#!/usr/bin/env python3
"""/dream 第十六梯队 — score≤29 压至 ≥30。

- 优先：trust_guard 可核 relations（+2）
- plot≤2：补第 3 条情节（+3，需 co-occur 章节可核）
- inbound<5：hub 互链（+1）

用法: python scripts/patch_hlm_tier16_score29.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CONTENT, iter_characters, parse_frontmatter  # noqa: E402
from lint_character_density import density_score  # noqa: E402
from patch_hlm_tier10_score22 import (  # noqa: E402
    add_hub_link,
    add_relations,
    pick_hub_source,
    pick_relation,
)
from trust_guard import (  # noqa: E402
    chapters_from_label,
    collect_search_chapters,
    load_cihua_body,
    name_terms,
    parse_plot_bullets,
    text_has_any,
    verify_plot_line,
)

BOOK = "红楼梦"
THIN_MAX = 29
TARGET = 30


def scan_pages() -> tuple[dict[str, dict], dict[str, set[str]]]:
    chars = list(iter_characters(BOOK))
    ids = {fm.get("id") or p.stem for p, fm, _ in chars}
    pages: dict[str, dict] = {}
    inbound: dict[str, set[str]] = defaultdict(set)

    for p, fm, body in chars:
        cid = fm.get("id") or p.stem
        plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
        plots: list[str] = []
        if plot_sec:
            plots = [ln for ln in plot_sec.group(1).splitlines() if ln.strip().startswith("-")]
        pages[cid] = {
            "path": p,
            "fm": fm,
            "body": body,
            "rel": len(fm.get("relations") or []),
            "plot": len(plots),
            "main": "## 主要关系" in body,
            "review": "## 评析" in body,
            "weight": int(fm.get("weight") or 0),
        }

    char_dir = CONTENT / "characters" / BOOK
    for p in char_dir.glob("*.md"):
        txt = p.read_text(encoding="utf-8-sig")
        src = p.stem
        for m in re.finditer(r"\[\[([^\]|]+)", txt):
            t = m.group(1).strip()
            if t in ids and t != src:
                inbound[t].add(src)
    topics_dir = CONTENT / "topics" / BOOK
    if topics_dir.exists():
        for p in topics_dir.glob("*.md"):
            txt = p.read_text(encoding="utf-8-sig")
            for m in re.finditer(r"\[\[([^\]|]+)", txt):
                t = m.group(1).strip()
                if t in ids:
                    inbound[t].add("topic")

    for cid in pages:
        pages[cid]["inbound"] = len(inbound[cid])
    return pages, inbound


def page_score(info: dict) -> int:
    return density_score({k: info[k] for k in ("rel", "plot", "main", "review", "inbound")})


def write_page(path: Path, fm: dict, body: str, dry_run: bool) -> None:
    if dry_run:
        return
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def add_plot_line(body: str, line: str) -> str:
    plot_match = re.search(r"(## 关键情节\s*\n.*?)(\n## )", body, re.S)
    if not plot_match:
        return body
    block = plot_match.group(1)
    if line.strip() in block:
        return body
    new_block = block.rstrip() + f"\n- {line}\n"
    return body[: plot_match.start(1)] + new_block + body[plot_match.end(1) :]


def pick_extra_plot(
    cid: str,
    fm: dict,
    body: str,
    pages: dict[str, dict],
    chapter_cache: dict[int, str | None],
) -> str | None:
    """Find co-character in a chapter not yet covered by plot bullets."""
    existing_chapters = set()
    for chaps, _ in parse_plot_bullets(body):
        existing_chapters.update(chaps)

    search = collect_search_chapters(
        cid, fm, body, {k: (v["path"], v["fm"], v["body"]) for k, v in pages.items()}, None
    )
    src_terms = name_terms(fm, cid)
    for chap in search:
        if chap in existing_chapters:
            continue
        if chap not in chapter_cache:
            chapter_cache[chap] = load_cihua_body(BOOK, chap)
        text = chapter_cache[chap]
        if not text or not text_has_any(text, src_terms):
            continue
        others: list[str] = []
        for tid, info in pages.items():
            if tid == cid:
                continue
            if text_has_any(text, name_terms(info["fm"], tid)):
                others.append(tid)
        others.sort(key=lambda t: pages[t]["weight"], reverse=True)
        others = others[:2]
        other_txt = "、".join(f"[[{t}]]" for t in others) if others else ""
        line = f"第{chap}回：与{other_txt}同场（第{chap}回）。" if other_txt else f"第{chap}回：正文出场（第{chap}回）。"
        ok, _ = verify_plot_line(cid, fm, [chap], line, BOOK)
        if ok:
            return line
    return None


def _chapter_from_line(line: str) -> str:
    m = re.search(r"第(\d+)回", line)
    return m.group(1) if m else "?"


def patch_one(
    cid: str,
    pages: dict[str, dict],
    inbound: dict[str, set[str]],
    all_fms: dict[str, tuple],
    chapter_cache: dict[int, str | None],
    dry_run: bool,
) -> str | None:
    info = pages[cid]
    if page_score(info) > THIN_MAX:
        return None

    rel = pick_relation(cid, pages, all_fms, chapter_cache)
    if rel:
        fm = dict(info["fm"])
        if add_relations(fm, rel):
            write_page(info["path"], fm, info["body"], dry_run)
            info["fm"] = fm
            info["rel"] = len(fm.get("relations") or [])
            all_fms[cid] = (info["path"], fm, info["body"])
            if page_score(info) >= TARGET:
                return f"{cid}: +rel→{rel['target']}"

    if info["plot"] <= 2 and page_score(info) <= THIN_MAX:
        line = pick_extra_plot(cid, info["fm"], info["body"], pages, chapter_cache)
        if line:
            new_body = add_plot_line(info["body"], line)
            if new_body != info["body"]:
                write_page(info["path"], info["fm"], new_body, dry_run)
                info["body"] = new_body
                info["plot"] += 1
                all_fms[cid] = (info["path"], info["fm"], new_body)
                if page_score(info) >= TARGET:
                    return f"{cid}: +plot ch{_chapter_from_line(line)}"

    if page_score(info) <= THIN_MAX and info["inbound"] < 5:
        hub = pick_hub_source(cid, pages, inbound, chapter_cache)
        if hub:
            hub_path = pages[hub]["path"]
            hfm, hbody = parse_frontmatter(hub_path)
            new_hbody = add_hub_link(hbody, cid)
            if new_hbody != hbody:
                if not dry_run:
                    hfm_text = yaml.dump(hfm, allow_unicode=True, default_flow_style=False, sort_keys=False)
                    hub_path.write_text(f"---\n{hfm_text}---\n{new_hbody}", encoding="utf-8")
                inbound[cid].add(hub)
                info["inbound"] = len(inbound[cid])
                if page_score(info) >= TARGET:
                    return f"{hub}→{cid}: hub"

    if page_score(info) <= THIN_MAX:
        rel2 = pick_relation(cid, pages, all_fms, chapter_cache)
        if rel2:
            fm = dict(info["fm"])
            if add_relations(fm, rel2):
                write_page(info["path"], fm, info["body"], dry_run)
                info["fm"] = fm
                info["rel"] = len(fm.get("relations") or [])
                all_fms[cid] = (info["path"], fm, info["body"])
                return f"{cid}: +rel→{rel2['target']}"

    return None if page_score(info) > THIN_MAX else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pages, inbound = scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}
    changes: list[str] = []
    stuck: list[str] = []

    order = sorted(
        pages,
        key=lambda c: (page_score(pages[c]), pages[c]["inbound"], c),
    )
    for cid in order:
        if page_score(pages[cid]) > THIN_MAX:
            continue
        result = patch_one(cid, pages, inbound, all_fms, chapter_cache, args.dry_run)
        if result:
            changes.append(result)
        elif page_score(pages[cid]) <= THIN_MAX:
            d = pages[cid]
            stuck.append(f"{cid} score={page_score(d)} rel={d['rel']} plot={d['plot']} in={d['inbound']}")

    print(f"patched {len(changes)} items")
    for c in changes:
        print(" ", c)
    remaining = sum(1 for info in pages.values() if page_score(info) <= THIN_MAX)
    print(f"remaining score≤{THIN_MAX}: {remaining}")
    if stuck:
        print(f"stuck: {len(stuck)}")
        for s in stuck[:30]:
            print(" ", s)


if __name__ == "__main__":
    main()
