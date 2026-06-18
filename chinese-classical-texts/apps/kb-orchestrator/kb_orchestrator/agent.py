from __future__ import annotations

import json
from typing import Any, Callable

from openai import OpenAI

from .config import (
    NOVELS_ROOT,
    STUDIO_LLM_BASE_URL,
    STUDIO_LLM_API_KEY,
    STUDIO_LLM_MAX_TOOL_ROUNDS,
    STUDIO_LLM_MODEL,
    agent_mode,
    llm_configured,
)
from .mock_agent import assistant_reply, pick_proposal
from .tools import TOOL_DEFINITIONS, execute_tool
from .tools.handlers import tool_summary

EventCallback = Callable[[str, dict], None]

AGENTS_PATH = NOVELS_ROOT / "AGENTS.md"


def _system_prompt(context: dict, intent_hint: dict | None) -> str:
    rules_excerpt = ""
    if AGENTS_PATH.exists():
        text = AGENTS_PATH.read_text(encoding="utf-8")
        rules_excerpt = text[:6000]

    intent_line = ""
    if intent_hint:
        intent_line = f"\nUser intent hint: {json.dumps(intent_hint, ensure_ascii=False)}"

    ctx_json = json.dumps(
        {
            k: context.get(k)
            for k in (
                "book",
                "bookSlug",
                "page",
                "entity",
                "items",
                "ingest",
                "chapters",
                "lintHints",
                "allowedIntents",
            )
            if context.get(k) is not None
        },
        ensure_ascii=False,
    )

    return f"""你是古典小说知识库维护者（Studio Agent）。遵守 AGENTS.md 铁律：

- `src/content/chapters/` 原文 HTML **只读**；ingest 仅可改回目 frontmatter（YAML），不可改正文。
- 情节性结论必须带 `sources[].chapter` 与 chapters 路径。
- 关系 `type` 仅用 AGENTS.md 受控词表。
- 名物 id 与文件名一致；路径必须在 `src/content/` 或 `src/data/` 下。
- **禁止**声称已写入磁盘；变更必须通过 `propose_patch` 工具提交 unified diff。
- patch diff 必须与当前文件逐行匹配（context 行以空格开头）；先 `read_entity` / `read_chapter` 再写 diff。
- `postApply.logEntry` 格式：`## [YYYY-MM-DD] studio | …` 或 ingest 用 `ingest |`。
- crosslinks / 信物改动后 postApply 应含 `build_crosslinks.py`；ingest 后含 `build_relations.py` + `trust_guard.py`。

AGENTS.md 摘录：
{rules_excerpt}

当前 MaintenanceContext JSON：
{ctx_json}
{intent_line}
"""


def _history_messages(session_messages: list[dict], user_text: str) -> list[dict]:
    msgs: list[dict] = []
    for m in session_messages[-12:]:
        role = m.get("role")
        if role in ("user", "assistant") and m.get("text"):
            msgs.append({"role": role, "content": m["text"]})
    msgs.append({"role": "user", "content": user_text})
    return msgs


def run_agent_turn(
    context: dict,
    user_text: str,
    intent_hint: dict | None,
    session_messages: list[dict],
    on_event: EventCallback | None = None,
) -> tuple[str, dict | None]:
    """Run one assistant turn. Returns (reply_text, proposal_or_none)."""
    if agent_mode() == "mock" or not llm_configured():
        proposal = pick_proposal(context, user_text, intent_hint)
        reply = assistant_reply(context, user_text, proposal)
        return reply, proposal

    def emit(event: str, data: dict) -> None:
        if on_event:
            on_event(event, data)

    client = OpenAI(api_key=STUDIO_LLM_API_KEY, base_url=STUDIO_LLM_BASE_URL)
    book = context.get("book") or "红楼梦"
    session_id = context["sessionId"]
    proposal_sink: list[dict] = []

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _system_prompt(context, intent_hint)},
        *_history_messages(session_messages, user_text),
    ]

    reply_text = ""

    for _ in range(STUDIO_LLM_MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=STUDIO_LLM_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.2,
        )
        choice = response.choices[0]
        msg = choice.message

        if msg.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                emit("tool.start", {"tool": name, "args": args})
                result = execute_tool(
                    name,
                    args,
                    book=book,
                    session_id=session_id,
                    proposal_sink=proposal_sink,
                )
                summary = tool_summary(name, args, result)
                emit("tool.done", {"tool": name, "summary": summary})
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result}
                )
            continue

        reply_text = (msg.content or "").strip()
        break

    if not reply_text and proposal_sink:
        reply_text = (
            f"已生成变更提案 **{proposal_sink[0].get('title')}**。"
            "请查看下方卡片，确认后点「应用全部」。"
        )
    elif not reply_text:
        reply_text = assistant_reply(context, user_text, None)

    proposal = proposal_sink[0] if proposal_sink else None
    if proposal and "_validationErrors" in proposal:
        proposal = {k: v for k, v in proposal.items() if not k.startswith("_")}
    return reply_text, proposal
