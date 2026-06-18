from __future__ import annotations

import json
import re
import uuid

from .config import NOVELS_ROOT


EXAMPLES_DIR = NOVELS_ROOT / "schemas" / "studio" / "examples"


def _load_example(name: str) -> dict:
    path = EXAMPLES_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def _clone_proposal(template: dict, session_id: str) -> dict:
    p = json.loads(json.dumps(template))
    p["proposalId"] = f"prop_{uuid.uuid4().hex[:12]}"
    p["sessionId"] = session_id
    p["status"] = "pending"
    return p


def pick_proposal(context: dict, text: str, intent_hint: dict | None) -> dict | None:
    entity = context["page"]["entityId"]
    page_kind = context["page"].get("kind") or "character"
    intent = (intent_hint or {}).get("type")
    lower = (text or "").lower()

    if page_kind == "chapter" or intent == "ingest_chapter" or "摄取" in text or "ingest" in lower:
        chapter = int(entity) if page_kind == "chapter" else None
        if chapter is None:
            m = re.search(r"第?\s*(\d+)\s*回", text or "")
            chapter = int(m.group(1)) if m else None
        book_slug = context.get("bookSlug")
        if book_slug == "honglou" and (chapter == 73 or entity == "73"):
            return _clone_proposal(
                _load_example("honglou-ch73-ingest.proposal.json"), context["sessionId"]
            )
        if page_kind == "chapter":
            return _generic_ingest_proposal(context)

    if intent == "fix_costume" or "服饰" in text:
        if entity == "林黛玉":
            return _clone_proposal(_load_example("daiyu-fix-costume.proposal.json"), context["sessionId"])
        return _generic_proposal(context, "fix_costume", "调整服饰字段", "请在名物页与 frontmatter 服饰[] 间对齐。")

    if intent == "fix_key_item" or "信物" in text or "关键物品" in text:
        if entity == "贾迎春":
            return _clone_proposal(_load_example("yingchun-fix-key-item.proposal.json"), context["sessionId"])
        return _generic_proposal(context, "fix_key_item", "补全信物链", "对照建议回目，补 crosslinks 与名物页。")

    if intent == "run_lint":
        return None

    # 启发：迎春上下文有 missing crosslinks
    missing = context.get("items", {}).get("missingFromCrosslinks") or []
    if missing and ("补" in text or "crosslinks" in lower or "链" in text):
        if entity == "贾迎春":
            return _clone_proposal(_load_example("yingchun-fix-key-item.proposal.json"), context["sessionId"])

    return None


def _generic_ingest_proposal(context: dict) -> dict:
    ingest = context.get("ingest") or {}
    ch = ingest.get("chapter") or context["page"]["entityId"]
    title = ingest.get("title") or context["page"].get("name") or f"第{ch}回"
    read_url = ingest.get("readUrl") or f"/{context['bookSlug']}/read/{ch}"
    return {
        "proposalId": f"prop_{uuid.uuid4().hex[:12]}",
        "sessionId": context["sessionId"],
        "status": "pending",
        "intent": "ingest_chapter",
        "title": f"第{ch}回 · {title} · 摄取清单",
        "summary": "MVP 占位：后续接 LLM 生成 frontmatter / 人物页 patch（原文 body 只读）。",
        "sources": [
            {
                "chapter": int(ch),
                "path": context["entity"]["path"],
                "edition": ingest.get("editionSlug"),
                "readUrl": read_url,
            }
        ],
        "patches": [],
        "postApply": {
            "scripts": ["python scripts/build_content_snapshots.py --write"],
            "logEntry": f"## [2026-06-16] ingest | {context['book']} 第{ch}回 studio (mvp stub)",
        },
        "guardPreview": {"status": "skipped", "checked": 0, "unverified": []},
        "actions": {
            "canApply": False,
            "canApplyPartial": False,
            "canEdit": True,
            "canDiscard": True,
        },
    }


def _generic_proposal(context: dict, intent: str, title: str, summary: str) -> dict:
    entity = context["page"]["entityId"]
    name = context["page"].get("name") or entity
    ch = (context.get("chapters") or {}).get("suggested") or [1]
    return {
        "proposalId": f"prop_{uuid.uuid4().hex[:12]}",
        "sessionId": context["sessionId"],
        "status": "pending",
        "intent": intent,
        "title": f"{name} · {title}",
        "summary": summary + "（MVP 占位 proposal，后续接 LLM 生成 diff）",
        "sources": [
            {
                "chapter": ch[0],
                "path": f"src/content/chapters/{context['book']}/{ch[0]:03d}.md",
                "edition": "zhiben" if context["bookSlug"] == "honglou" else "1",
                "readUrl": f"/{context['bookSlug']}/read/zhiben/{ch[0]}"
                if context["bookSlug"] == "honglou"
                else f"/{context['bookSlug']}/read/{ch[0]}",
            }
        ],
        "patches": [],
        "postApply": {
            "scripts": ["python scripts/build_content_snapshots.py --write"],
            "logEntry": f"## [2026-06-16] studio | {entity} {intent} (mvp stub)",
        },
        "guardPreview": {"status": "skipped", "checked": 0, "unverified": []},
        "actions": {
            "canApply": False,
            "canApplyPartial": False,
            "canEdit": True,
            "canDiscard": True,
        },
    }


def assistant_reply(context: dict, text: str, proposal: dict | None) -> str:
    name = context["page"].get("name") or context["page"]["entityId"]
    hints = context.get("lintHints") or []
    hint_txt = hints[0]["message"] if hints else "未发现结构性告警"
    page_kind = context["page"].get("kind") or "character"

    if proposal:
        return (
            f"已对照 **{name}** 当前数据（{hint_txt}）。"
            f"下方卡片为 **{proposal['title']}** 变更预览；确认后点「应用全部」将写盘并跑 postApply。"
        )

    if page_kind == "chapter":
        ingest = context.get("ingest") or {}
        missing = len(ingest.get("charactersMissingPage") or [])
        body_only = ingest.get("bodyOnlyCharacters") or []
        extra = f"缺页人物 {missing} 个。"
        if body_only:
            extra += f" 正文未列入：{', '.join(body_only)}。"
        return (
            f"收到。当前为 **第{ingest.get('chapter', context['page']['entityId'])}回** 摄取上下文。"
            f"{extra}{hint_txt}。"
            f"可试：「摄取本回 frontmatter 与登场人物」，或使用下方快捷按钮。"
        )

    return (
        f"收到。当前上下文：**信物 {len(context.get('items', {}).get('keyItems') or [])} 项**，"
        f"**服饰 {len(context.get('items', {}).get('costumes') or [])} 项**。"
        f"{hint_txt}。"
        f"可试：「补信物链」「改服饰」，或使用下方快捷按钮。"
    )
