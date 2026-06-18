#!/usr/bin/env python3
"""/dream 第十二梯队 — score=26 压至 ≥27。

- inbound<5：hub 互链（+1）
- 其余：trust_guard 可核 relations（+2）

用法: python scripts/patch_hlm_tier12_score27.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import parse_frontmatter  # noqa: E402
from lint_character_density import density_score  # noqa: E402
from patch_hlm_tier10_score22 import (  # noqa: E402
    BOOK,
    add_hub_link,
    add_relations,
    pick_hub_source,
    pick_relation,
    scan_pages,
    write_page,
)

TARGET = 27
THIN_SCORE = 26


def page_score(info: dict) -> int:
    return density_score({k: info[k] for k in ("rel", "plot", "main", "review", "inbound")})


def patch_one(
    cid: str,
    pages: dict,
    inbound: dict,
    all_fms: dict,
    chapter_cache: dict[int, str | None],
    dry_run: bool,
) -> str | None:
    info = pages[cid]
    if page_score(info) != THIN_SCORE:
        return None

    if info["inbound"] < 5:
        hub = pick_hub_source(cid, pages, inbound, chapter_cache)
        if hub:
            hub_path = pages[hub]["path"]
            hfm, hbody = parse_frontmatter(hub_path)
            new_body = add_hub_link(hbody, cid)
            if new_body != hbody:
                if not dry_run:
                    hfm_text = yaml.dump(hfm, allow_unicode=True, default_flow_style=False, sort_keys=False)
                    hub_path.write_text(f"---\n{hfm_text}---\n{new_body}", encoding="utf-8")
                inbound[cid].add(hub)
                info["inbound"] = len(inbound[cid])
                return f"{hub}→{cid}: hub"

    rel = pick_relation(cid, pages, all_fms, chapter_cache)
    if not rel:
        return None
    fm = dict(info["fm"])
    if not add_relations(fm, rel):
        return None
    write_page(info["path"], fm, info["body"], dry_run)
    info["fm"] = fm
    info["rel"] = len(fm.get("relations") or [])
    all_fms[cid] = (info["path"], fm, info["body"])
    return f"{cid}: +rel→{rel['target']}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pages, inbound = scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}
    changes: list[str] = []
    stuck: list[str] = []

    # 弱入链优先 hub
    order = sorted(
        pages,
        key=lambda c: (page_score(pages[c]) != THIN_SCORE, pages[c]["inbound"], c),
    )
    for cid in order:
        if page_score(pages[cid]) != THIN_SCORE:
            continue
        result = patch_one(cid, pages, inbound, all_fms, chapter_cache, args.dry_run)
        if result:
            changes.append(result)
        else:
            stuck.append(cid)

    print(f"patched {len(changes)} items")
    for c in changes:
        print(" ", c)

    if not args.dry_run:
        remaining = sum(1 for info in pages.values() if page_score(info) == THIN_SCORE)
        print(f"remaining score={THIN_SCORE}: {remaining}")
        if stuck:
            print(f"stuck: {len(stuck)}")
            for cid in stuck[:20]:
                d = pages[cid]
                print(f"  {cid} rel={d['rel']} plot={d['plot']} in={d['inbound']}")


if __name__ == "__main__":
    main()
