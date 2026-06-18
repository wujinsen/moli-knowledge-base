#!/usr/bin/env python3
"""Studio 待办清单 — lint / crosslinks / ingest 聚合。"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import DATA_DIR, iter_characters
from ingest_common import analyze_chapter_ingest
from lint_character_density import collect_density

BOOK_SLUG = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

CROSSLINKS_SLUG = {
    "红楼梦": "hongloumeng",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

NOVELS_ROOT = Path(__file__).resolve().parents[1]

CHAPTER_SCAN_LIMIT = {
    "红楼梦": 120,
    "金瓶梅": 100,
    "西游记": 100,
}

# 待办 ingest 抽样：每 5 回 + 关键回（非全量扫描）
INGEST_SAMPLE_EXTRA = {
    "红楼梦": [17, 49, 73, 74, 80],
    "金瓶梅": [1, 27, 49],
    "西游记": [1, 27, 50],
}


def chapters_for_ingest_scan(book: str) -> list[int]:
    max_ch = CHAPTER_SCAN_LIMIT.get(book, 100)
    sampled = list(range(1, max_ch + 1, 5))
    extras = [c for c in INGEST_SAMPLE_EXTRA.get(book, []) if c <= max_ch]
    return sorted(set(sampled + extras))


def _load_crosslinks(book: str) -> dict:
    slug = CROSSLINKS_SLUG.get(book, book)
    path = DATA_DIR / f"{slug}.crosslinks.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_crosslink_todos(book: str, *, limit: int = 15) -> list[dict]:
    occupant = (_load_crosslinks(book).get("occupant_items") or {})
    todos: list[dict] = []
    for _path, fm, _body in iter_characters(book):
        cid = fm.get("id") or fm.get("name")
        if not cid:
            continue
        items = list(fm.get("关键物品") or []) + list(fm.get("服饰") or [])
        if not items:
            continue
        occ = set(occupant.get(cid) or [])
        for item in items:
            if item in occ:
                continue
            todos.append(
                {
                    "id": f"todo_crosslinks_{cid}_{item}",
                    "kind": "fix_key_item",
                    "entityId": cid,
                    "message": f"{cid} 已列「{item}」，crosslinks 未链",
                    "suggestedPrompt": f"补全 {cid} 与 {item} 的 crosslinks 与名物页论据",
                    "severity": "warn",
                }
            )
            if len(todos) >= limit:
                return todos
    return todos


def collect_density_todos(book: str, *, limit: int = 8) -> list[dict]:
    density = collect_density(book)
    todos: list[dict] = []
    for row in density.get("priorityBatch") or []:
        flags = row.get("flags") or []
        if not flags:
            continue
        todos.append(
            {
                "id": f"todo_density_{row['id']}",
                "kind": "add_plot_bullet",
                "entityId": row["id"],
                "message": f"低密度 score={row['score']}：{', '.join(flags[:3])}",
                "suggestedPrompt": f"为 {row['id']} 补关键情节与关系（lint 低密度）",
                "severity": "info",
            }
        )
        if len(todos) >= limit:
            break
    return todos


def collect_ingest_todos(book: str, *, limit: int = 6) -> list[dict]:
    chapters = chapters_for_ingest_scan(book)

    def scan(ch: int) -> dict | None:
        try:
            return analyze_chapter_ingest(book, ch, novels_root=NOVELS_ROOT)
        except FileNotFoundError:
            return None

    candidates: list[tuple[int, dict]] = []
    workers = min(8, max(2, len(chapters) // 4))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(scan, ch) for ch in chapters]
        for fut in as_completed(futures):
            data = fut.result()
            if not data:
                continue
            body_only = data.get("bodyOnlyCharacters") or []
            missing = data.get("charactersMissingPage") or []
            if not body_only and not missing:
                continue
            score = len(body_only) * 2 + len(missing)
            candidates.append((score, data))

    candidates.sort(key=lambda x: -x[0])
    todos: list[dict] = []
    for _score, data in candidates[:limit]:
        ch = data["chapter"]
        body_only = data.get("bodyOnlyCharacters") or []
        missing = data.get("charactersMissingPage") or []
        parts = []
        if body_only:
            parts.append(f"frontmatter 未列 {len(body_only)} 人")
        if missing:
            parts.append(f"缺页 {len(missing)}")
        todos.append(
            {
                "id": f"todo_ingest_ch{ch:03d}",
                "kind": "ingest_chapter",
                "chapter": ch,
                "editionSlug": data.get("editionSlug"),
                "readUrl": data.get("readUrl"),
                "message": f"第{ch}回：{' · '.join(parts)}",
                "suggestedPrompt": f"摄取第{ch}回：补 frontmatter 与登场人物关键情节",
                "severity": "warn" if body_only else "info",
            }
        )
    return todos


def collect_module_todos(book: str, *, limit: int = 15) -> list[dict]:
    """名物 / 建筑 / 意象 lint 优先待办。"""
    from lint_modules import (
        _has_places_module,
        book_features,
        lint_items_body_unlisted,
        lint_items_character_gaps,
        lint_items_crosslinks_gap,
        lint_items_field_gaps,
        lint_items_imagery_unmaterialized,
        lint_items_missing_pages,
        lint_items_orphans,
        lint_places_field_gaps,
        lint_places_graph,
        lint_shi_field_gaps,
        lint_shi_inference_gaps,
    )

    feats = book_features(book)
    todos: list[dict] = []

    if "items" in feats:
        for line in lint_items_character_gaps(book)[:5]:
            if "人物缺 frontmatter 名物: " in line:
                cid = line.split("人物缺 frontmatter 名物: ", 1)[1].split(" ·")[0]
            elif "人物缺名物链: " in line:
                cid = line.split("人物缺名物链: ", 1)[1].split(" ·")[0]
            else:
                cid = line.split(": ", 1)[-1].split(" ·")[0]
            todos.append(
                {
                    "id": f"todo_item_char_{cid}",
                    "kind": "fix_key_item",
                    "entityId": cid,
                    "message": line,
                    "suggestedPrompt": f"为 {cid} 补 服饰/关键物品（或运行 sync_character_items_from_wiki.py）",
                    "severity": "warn",
                }
            )
        for line in lint_items_body_unlisted(book)[:4]:
            iid = line.split(": ", 1)[-1].split(" @")[0].replace("正文有名物未入 items[]: ", "")
            ch_m = re.search(r"第(\d+)回", line)
            todos.append(
                {
                    "id": f"todo_item_body_{iid}_{ch_m.group(1) if ch_m else len(todos)}",
                    "kind": "fix_key_item",
                    "entityId": iid,
                    "message": line,
                    "suggestedPrompt": f"第{ch_m.group(1) if ch_m else '?'}回 items[] 补 {iid}，或核对正文误匹配",
                    "severity": "info",
                }
            )
        for line in lint_items_imagery_unmaterialized(book)[:3]:
            todos.append(
                {
                    "id": f"todo_item_omen_{len(todos)}",
                    "kind": "fix_key_item",
                    "message": line,
                    "suggestedPrompt": f"为物象谶建名物页并互链：{line}",
                    "severity": "info",
                }
            )
        for line in lint_items_missing_pages(book)[:3]:
            iid = line.split(": ", 1)[-1].split(" @")[0].replace("缺实体页: ", "")
            todos.append(
                {
                    "id": f"todo_item_page_{iid}",
                    "kind": "fix_key_item",
                    "entityId": iid,
                    "message": line,
                    "suggestedPrompt": f"为名物 {iid} 建实体页并补回目 items[] 互链",
                    "severity": "warn",
                }
            )
        for line in lint_items_orphans(book)[:2]:
            iid = line.split(":", 1)[-1].split(" ·")[0].replace("名物孤儿: ", "").strip()
            todos.append(
                {
                    "id": f"todo_item_orphan_{iid}",
                    "kind": "fix_key_item",
                    "entityId": iid,
                    "message": line,
                    "suggestedPrompt": f"为孤儿名物 {iid} 补回目 items[]、wearer 或 topic 入链",
                    "severity": "info",
                }
            )
        for line in lint_items_crosslinks_gap(book)[:2]:
            todos.append(
                {
                    "id": f"todo_item_xlink_{len(todos)}",
                    "kind": "fix_key_item",
                    "message": line,
                    "suggestedPrompt": f"补全 crosslinks：{line}",
                    "severity": "info",
                }
            )
        for line in lint_items_field_gaps(book)[:2]:
            iid = line.split(": ", 1)[-1].split(" ·")[0].replace("字段缺漏: ", "")
            todos.append(
                {
                    "id": f"todo_item_field_{iid}",
                    "kind": "fix_key_item",
                    "entityId": iid,
                    "message": line,
                    "suggestedPrompt": f"补全名物页 {iid} 的 summary / first_appear",
                    "severity": "info",
                }
            )

    if "places" in feats or _has_places_module(book):
        for line in lint_places_graph(book)[:2]:
            todos.append(
                {
                    "id": f"todo_place_graph_{len(todos)}",
                    "kind": "query",
                    "message": line,
                    "suggestedPrompt": f"补建筑入链或回目 locations[]：{line}",
                    "severity": "warn",
                }
            )
        for line in lint_places_field_gaps(book)[:2]:
            lid = line.split(": ", 1)[-1].split(" ·")[0].replace("字段缺漏: ", "")
            todos.append(
                {
                    "id": f"todo_place_field_{lid}",
                    "kind": "query",
                    "entityId": lid,
                    "message": line,
                    "suggestedPrompt": f"补全地点页 {lid} 的 summary / first_appear",
                    "severity": "info",
                }
            )

    if "poems" in feats:
        for line in lint_shi_inference_gaps(book)[:3]:
            todos.append(
                {
                    "id": f"todo_shi_inf_{len(todos)}",
                    "kind": "topic_fill",
                    "message": line,
                    "suggestedPrompt": f"补意象 inference 边：{line}",
                    "severity": "warn",
                }
            )
        for line in lint_shi_field_gaps(book)[:2]:
            iid = line.split(": ", 1)[-1].split(" ·")[0].replace("字段缺漏: ", "")
            todos.append(
                {
                    "id": f"todo_shi_field_{iid}",
                    "kind": "topic_fill",
                    "entityId": iid,
                    "message": line,
                    "suggestedPrompt": f"补全意象页 {iid} 的 summary / chapters",
                    "severity": "info",
                }
            )

    return todos[:limit]


def collect_studio_todos(book: str) -> dict:
    book_slug = BOOK_SLUG.get(book, book)
    cross = collect_crosslink_todos(book)
    density = collect_density_todos(book)
    ingest = collect_ingest_todos(book)
    modules = collect_module_todos(book)

    seen: set[str] = set()
    merged: list[dict] = []
    for group in (modules, cross, ingest, density):
        for t in group:
            if t["id"] in seen:
                continue
            seen.add(t["id"])
            merged.append(t)

    return {
        "book": book,
        "bookSlug": book_slug,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalTodos": len(merged),
        "todos": merged[:25],
        "sources": {
            "modules": len(modules),
            "crosslinks": len(cross),
            "ingest": len(ingest),
            "density": len(density),
        },
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Studio todo aggregator")
    ap.add_argument("book", help="书名")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    data = collect_studio_todos(args.book)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"{data['book']} · {data['totalTodos']} todos")
        for t in data["todos"]:
            print(f"  [{t['severity']}] {t['kind']}: {t['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
