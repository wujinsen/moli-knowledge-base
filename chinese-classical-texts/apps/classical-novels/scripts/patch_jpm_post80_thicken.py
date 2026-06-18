#!/usr/bin/env python3
"""/dream — 后二十回（ch81–100）出场人物加厚：骨架 + relation + hub + topic 链。

用法: python scripts/patch_jpm_post80_thicken.py [--dry-run] [--thin-max 24]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CONTENT, parse_frontmatter  # noqa: E402
from dream_patch_common import (  # noqa: E402
    add_hub_link,
    add_relations,
    page_score,
    pick_hub_source,
    pick_relation,
    scan_pages,
    write_page,
)
from patch_dream_low_score import patch_rel_backlinks  # noqa: E402
from patch_hlm_character_skeleton import patch_body  # noqa: E402

BOOK = "金瓶梅"
CHAPTER_DIR = CONTENT / "chapters" / BOOK / "词话本"
TOPIC_HUB = "后二十回散场人物"
POST80_MIN = 81


def chars_in_post80() -> dict[str, set[int]]:
    out: dict[str, set[int]] = defaultdict(set)
    for p in sorted(CHAPTER_DIR.glob("*.md")):
        try:
            n = int(p.stem)
        except ValueError:
            continue
        if n < POST80_MIN:
            continue
        fm, _ = parse_frontmatter(p)
        for c in fm.get("characters") or []:
            out[str(c).strip()].add(n)
    return out


def run(*, thin_max: int, dry_run: bool) -> list[str]:
    post80 = chars_in_post80()
    pages, inbound = scan_pages(BOOK)
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}
    changes: list[str] = []

    topic_path = CONTENT / "topics" / BOOK / f"{TOPIC_HUB}.md"
    topic_fm, topic_body = parse_frontmatter(topic_path) if topic_path.exists() else ({}, "")
    topic_changed = False

    targets = sorted(
        (cid for cid in post80 if cid in pages and page_score(pages[cid]) <= thin_max),
        key=lambda c: (page_score(pages[c]), pages[c]["inbound"], c),
    )

    for cid in targets:
        info = pages[cid]
        chs = sorted(post80[cid])
        parts: list[str] = []

        new_body, sk = patch_body(info["fm"], info["body"])
        if sk:
            info["body"] = new_body
            parts.extend(sk)

        if info["rel"] <= 10:
            rel = pick_relation(BOOK, cid, pages, all_fms, chapter_cache)
            if rel:
                fm = dict(info["fm"])
                if add_relations(fm, rel):
                    info["fm"] = fm
                    info["rel"] = len(fm.get("relations") or [])
                    all_fms[cid] = (info["path"], fm, info["body"])
                    parts.append(f"+rel→{rel['target']}")

        if info["inbound"] <= 5:
            hub = pick_hub_source(BOOK, cid, pages, inbound, chapter_cache)
            if hub:
                hub_path = pages[hub]["path"]
                hfm, hbody = parse_frontmatter(hub_path)
                nb = add_hub_link(hbody, cid)
                if nb != hbody:
                    if not dry_run:
                        write_page(hub_path, hfm, nb, False)
                    inbound[cid].add(hub)
                    info["inbound"] = len(inbound[cid])
                    parts.append(f"hub←{hub}")

        if info["plot"] <= 1 and chs:
            ch = chs[0]
            line = f"- 第{ch}回：后二十回散场线出场（chapters/金瓶梅/词话本/{ch:03d}）。"
            if "## 关键情节" in info["body"] and line not in info["body"]:
                info["body"] = re.sub(
                    r"(## 关键情节\s*\n)",
                    rf"\1{line}\n",
                    info["body"],
                    count=1,
                )
                info["plot"] += 1
                parts.append("plot")

        if TOPIC_HUB not in info["body"]:
            if "## 相关" in info["body"]:
                info["body"] = info["body"].replace(
                    "## 相关\n",
                    f"## 相关\n\n- [[{TOPIC_HUB}]]\n",
                    1,
                )
            else:
                info["body"] = info["body"].rstrip() + (
                    f"\n\n## 相关\n\n- [[{TOPIC_HUB}]]\n"
                )
            parts.append("topic-link")

        if parts:
            if not dry_run:
                write_page(info["path"], info["fm"], info["body"], False)
            changes.append(f"{cid}: " + ", ".join(parts))

        if topic_path.exists() and f"[[{cid}]]" not in topic_body:
            topic_body = add_hub_link(topic_body, cid)
            topic_changed = True

        if page_score(info) <= thin_max:
            patch_rel_backlinks(cid, info, pages, inbound, dry_run=dry_run, changes=changes)

    if topic_path.exists() and topic_changed and not dry_run:
        write_page(topic_path, topic_fm, topic_body, False)
        changes.append(f"topic: hub links updated")

    return changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--thin-max", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    changes = run(thin_max=args.thin_max, dry_run=args.dry_run)
    pages, _ = scan_pages(BOOK)
    post80 = chars_in_post80()
    remaining = sum(
        1 for cid in post80 if cid in pages and page_score(pages[cid]) <= args.thin_max
    )
    print(f"[{BOOK}] post80 thickened {len(changes)} items")
    for c in changes[:60]:
        print(" ", c)
    if len(changes) > 60:
        print(f"  ... +{len(changes) - 60} more")
    print(f"remaining post80 score<={args.thin_max}: {remaining}")


if __name__ == "__main__":
    main()
