#!/usr/bin/env python3
"""/dream 第十九梯队 — score=33 压至 ≥34（+1 verified rel 或 +1 plot）。

用法: python scripts/patch_hlm_tier19_score33.py [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_hlm_tier18_score32 import patch_one_33  # noqa: E402, F401
from patch_hlm_tier17_score31 import page_score, scan_pages  # noqa: E402

SOURCE_SCORE = 33
TARGET = 34


def patch_one_34(cid, pages, inbound, all_fms, chapter_cache, dry_run):
    info = pages[cid]
    if page_score(info) != SOURCE_SCORE:
        return None
    from patch_hlm_tier17_score31 import (  # noqa: E402
        add_plot_line,
        pick_extra_plot,
        write_page,
    )
    from patch_hlm_tier10_score22 import add_relations, pick_hub_source, add_hub_link  # noqa: E402
    from patch_hlm_tier12_score26 import pick_relation  # noqa: E402
    from _common import parse_frontmatter  # noqa: E402
    import yaml  # noqa: E402

    parts: list[str] = []
    for attempt in range(4):
        if page_score(info) >= TARGET:
            break
        rel = pick_relation(cid, pages, all_fms, chapter_cache, full_scan=attempt >= 1)
        if rel:
            fm = dict(info["fm"])
            if add_relations(fm, rel):
                write_page(info["path"], fm, info["body"], dry_run)
                info["fm"] = fm
                info["rel"] = len(fm.get("relations") or [])
                all_fms[cid] = (info["path"], fm, info["body"])
                parts.append(f"+rel→{rel['target']}")
                if page_score(info) >= TARGET:
                    break
        if page_score(info) < TARGET and info["plot"] <= 4:
            line = pick_extra_plot(cid, info["fm"], info["body"], pages, chapter_cache)
            if line:
                new_body = add_plot_line(info["body"], line)
                if new_body != info["body"]:
                    write_page(info["path"], info["fm"], new_body, dry_run)
                    info["body"] = new_body
                    info["plot"] += 1
                    all_fms[cid] = (info["path"], info["fm"], new_body)
                    parts.append("+plot")
                    if page_score(info) >= TARGET:
                        break
        if page_score(info) < TARGET and info["inbound"] < 5:
            hub = pick_hub_source(cid, pages, inbound, chapter_cache)
            if hub:
                hub_path = pages[hub]["path"]
                hfm, hbody = parse_frontmatter(hub_path)
                nb = add_hub_link(hbody, cid)
                if nb != hbody and not dry_run:
                    hfm_text = yaml.dump(hfm, allow_unicode=True, default_flow_style=False, sort_keys=False)
                    hub_path.write_text(f"---\n{hfm_text}---\n{nb}", encoding="utf-8")
                if nb != hbody:
                    inbound[cid].add(hub)
                    info["inbound"] = len(inbound[cid])
                    parts.append(f"hub←{hub}")
                    if page_score(info) >= TARGET:
                        break
    if not parts:
        return None
    return f"{cid}: " + ", ".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    pages, inbound = scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}
    changes: list[str] = []

    targets = sorted(
        (cid for cid, info in pages.items() if page_score(info) == SOURCE_SCORE),
        key=lambda c: (pages[c]["inbound"], c),
    )
    if args.limit > 0:
        targets = targets[: args.limit]

    for cid in targets:
        result = patch_one_34(cid, pages, inbound, all_fms, chapter_cache, args.dry_run)
        if result:
            changes.append(result)

    remaining = sum(1 for info in pages.values() if page_score(info) == SOURCE_SCORE)
    print(f"patched {len(changes)} items (limit={args.limit or 'all'})")
    for c in changes[:60]:
        print(" ", c)
    if len(changes) > 60:
        print(f"  ... +{len(changes) - 60} more")
    print(f"remaining score={SOURCE_SCORE}: {remaining}")
    print(f"min score: {min(page_score(i) for i in pages.values())}")


if __name__ == "__main__":
    main()
