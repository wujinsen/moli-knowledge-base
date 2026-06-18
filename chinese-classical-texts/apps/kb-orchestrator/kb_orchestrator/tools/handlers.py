from __future__ import annotations

import json
import sys
import uuid
from datetime import date
from typing import Any, Callable

from ..config import ITEM_DIRS, NOVELS_ROOT
from ..log_util import default_log_entry
from ..parse_md import parse_frontmatter
from ..patch import PatchError, preview_file_patch

_SCRIPTS = NOVELS_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from ingest_common import analyze_chapter_ingest, chapter_file, parse_chapter, strip_html  # noqa: E402

EventCallback = Callable[[str, dict], None]

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "read_chapter",
            "description": "Read chapter YAML frontmatter and a plain-text excerpt. chapters/ HTML body is read-only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chapter": {"type": "integer", "minimum": 1},
                    "edition_slug": {"type": "string", "description": "e.g. chenggao, zhiben"},
                    "max_body_chars": {"type": "integer", "default": 2500},
                },
                "required": ["chapter"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_entity",
            "description": "Read a character/monster wiki page (frontmatter + markdown body preview).",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                    "max_body_chars": {"type": "integer", "default": 5000},
                },
                "required": ["entity_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_item",
            "description": "Read a costume/dish/medicine/custom/artifact wiki page by id.",
            "parameters": {
                "type": "object",
                "properties": {"item_id": {"type": "string"}},
                "required": ["item_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_chapter_ingest",
            "description": "Ingest checklist for a chapter: missing pages, body-only characters, tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chapter": {"type": "integer", "minimum": 1},
                    "edition_slug": {"type": "string"},
                },
                "required": ["chapter"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_patch",
            "description": (
                "Submit a PatchProposal (unified diffs). Does NOT write to disk until user clicks Apply. "
                "Each patch diff must match current file content exactly. "
                "Never patch chapters/ HTML body — frontmatter only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": [
                            "fix_key_item",
                            "fix_costume",
                            "add_plot_bullet",
                            "ingest_chapter",
                            "query",
                            "topic_fill",
                        ],
                    },
                    "title": {"type": "string", "maxLength": 120},
                    "summary": {"type": "string", "maxLength": 500},
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "chapter": {"type": "integer"},
                                "path": {"type": "string"},
                                "edition": {"type": "string"},
                                "excerpt": {"type": "string"},
                                "readUrl": {"type": "string"},
                            },
                            "required": ["chapter", "path"],
                        },
                        "minItems": 1,
                    },
                    "patches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "operation": {"type": "string", "enum": ["create", "update"]},
                                "hunkSummary": {"type": "string"},
                                "diff": {"type": "string"},
                            },
                            "required": ["path", "operation", "diff"],
                        },
                    },
                    "postApply": {
                        "type": "object",
                        "properties": {
                            "scripts": {"type": "array", "items": {"type": "string"}},
                            "logEntry": {"type": "string"},
                            "refreshHints": {"type": "object"},
                        },
                    },
                },
                "required": ["intent", "title", "summary", "sources", "patches"],
            },
        },
    },
]


def _rel(path) -> str:
    return str(path.relative_to(NOVELS_ROOT)).replace("\\", "/")


def _tool_read_chapter(book: str, args: dict) -> dict:
    ch = int(args["chapter"])
    edition = args.get("edition_slug")
    max_chars = int(args.get("max_body_chars") or 2500)
    path = chapter_file(book, ch, edition, NOVELS_ROOT)
    if not path.exists():
        return {"error": f"chapter not found: {ch}"}
    fm, body = parse_chapter(path)
    plain = strip_html(body)
    return {
        "path": _rel(path),
        "frontmatter": fm,
        "excerpt": plain[:max_chars] + ("…" if len(plain) > max_chars else ""),
    }


def _tool_read_entity(book: str, args: dict) -> dict:
    eid = args["entity_id"]
    max_chars = int(args.get("max_body_chars") or 5000)
    for sub in ("characters",):
        p = NOVELS_ROOT / "src/content" / sub / book / f"{eid}.md"
        if p.exists():
            fm, body = parse_frontmatter(p)
            return {"path": _rel(p), "frontmatter": fm, "bodyMarkdown": body[:max_chars]}
    return {"error": f"entity not found: {eid}"}


def _tool_read_item(book: str, args: dict) -> dict:
    iid = args["item_id"]
    for kind in ITEM_DIRS:
        p = NOVELS_ROOT / "src/content" / kind / book / f"{iid}.md"
        if p.exists():
            fm, body = parse_frontmatter(p)
            return {"kind": kind, "path": _rel(p), "frontmatter": fm, "bodyMarkdown": body[:3000]}
    return {"error": f"item not found: {iid}"}


def _tool_read_chapter_ingest(book: str, args: dict) -> dict:
    ch = int(args["chapter"])
    data = analyze_chapter_ingest(
        book, ch, novels_root=NOVELS_ROOT, edition_slug=args.get("edition_slug")
    )
    # trim heavy fields for token budget
    slim = {k: data[k] for k in data if k not in ("entityFrontmatter", "excerpt")}
    slim["excerpt"] = (data.get("excerpt") or "")[:800]
    return slim


def _default_post_apply(book: str, intent: str, title: str) -> dict:
    scripts: list[str] = ["python scripts/build_content_snapshots.py --write"]
    refresh: dict[str, bool] = {"snapshots": True}
    prefix = "ingest" if intent == "ingest_chapter" else "studio"
    log = f"## [{date.today().isoformat()}] {prefix} | {title}"

    if intent in ("fix_key_item", "fix_costume"):
        scripts = [
            f'python scripts/build_crosslinks.py "{book}"',
            "python scripts/build_content_snapshots.py --write",
        ]
        refresh["bestiary"] = book == "红楼梦"
    elif intent == "ingest_chapter":
        scripts = [
            f'python scripts/build_relations.py "{book}"',
            f'python scripts/trust_guard.py "{book}"',
            "python scripts/build_content_snapshots.py --write",
        ]
        refresh["relations"] = True
    elif intent == "add_plot_bullet":
        scripts = [
            f'python scripts/build_relations.py "{book}"',
            "python scripts/build_content_snapshots.py --write",
        ]
        refresh["relations"] = True

    return {"scripts": scripts, "logEntry": log, "refreshHints": refresh}


def _validate_proposal_patches(patches: list[dict]) -> tuple[list[dict], list[dict]]:
    ok: list[dict] = []
    errors: list[dict] = []
    for p in patches:
        path = p.get("path") or ""
        op = p.get("operation") or "update"
        diff = p.get("diff") or ""
        try:
            preview_file_patch(NOVELS_ROOT, path, op, diff)
            ok.append(p)
        except PatchError as e:
            errors.append({"path": path, "error": str(e)})
    return ok, errors


def _tool_propose_patch(
    book: str,
    session_id: str,
    args: dict,
    *,
    proposal_sink: list[dict],
) -> dict:
    patches = list(args.get("patches") or [])
    valid, errors = _validate_proposal_patches(patches)
    intent = args.get("intent") or "query"
    title = (args.get("title") or "变更提案")[:120]
    summary = (args.get("summary") or "")[:500]
    post = args.get("postApply") or _default_post_apply(book, intent, title)
    if not post.get("logEntry"):
        post["logEntry"] = default_log_entry(title)

    proposal = {
        "proposalId": f"prop_{uuid.uuid4().hex[:12]}",
        "sessionId": session_id,
        "status": "pending",
        "intent": intent,
        "title": title,
        "summary": summary,
        "sources": args.get("sources") or [],
        "patches": valid,
        "postApply": post,
        "guardPreview": {"status": "skipped", "checked": 0, "unverified": []},
        "actions": {
            "canApply": len(valid) > 0,
            "canApplyPartial": len(valid) > 0 and len(errors) > 0,
            "canEdit": True,
            "canDiscard": True,
        },
    }
    if errors:
        proposal["_validationErrors"] = errors  # stripped before SSE

    proposal_sink.clear()
    proposal_sink.append(proposal)

    return {
        "accepted": len(valid),
        "rejected": len(errors),
        "errors": errors,
        "canApply": len(valid) > 0,
        "proposalId": proposal["proposalId"],
    }


def execute_tool(
    name: str,
    args: dict,
    *,
    book: str,
    session_id: str,
    proposal_sink: list[dict],
) -> str:
    if name == "read_chapter":
        result = _tool_read_chapter(book, args)
    elif name == "read_entity":
        result = _tool_read_entity(book, args)
    elif name == "read_item":
        result = _tool_read_item(book, args)
    elif name == "read_chapter_ingest":
        result = _tool_read_chapter_ingest(book, args)
    elif name == "propose_patch":
        result = _tool_propose_patch(book, session_id, args, proposal_sink=proposal_sink)
    else:
        result = {"error": f"unknown tool: {name}"}
    return json.dumps(result, ensure_ascii=False)


def tool_summary(name: str, args: dict, result_json: str) -> str:
    try:
        data = json.loads(result_json)
    except json.JSONDecodeError:
        return f"{name}: done"
    if data.get("error"):
        return f"{name}: {data['error']}"
    if name == "propose_patch":
        return f"proposal {data.get('proposalId')} · {data.get('accepted')} patch(es)"
    if name == "read_chapter":
        return f"第{args.get('chapter')}回 · {data.get('path', '')}"
    if name == "read_entity":
        return args.get("entity_id") or "entity"
    if name == "read_item":
        return args.get("item_id") or "item"
    if name == "read_chapter_ingest":
        return f"ingest ch{args.get('chapter')}"
    return name
