#!/usr/bin/env python3
"""One-off scan helper for 红楼梦 density."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CONTENT, iter_characters  # noqa: E402
from lint_character_density import density_score  # noqa: E402

BOOK = "红楼梦"


def main() -> None:
    max_score = int(sys.argv[1]) if len(sys.argv) > 1 else 18
    chars = list(iter_characters(BOOK))
    ids = {fm.get("id") or p.stem for p, fm, _ in chars}
    pages: dict[str, dict] = {}
    inbound: dict[str, set[str]] = defaultdict(set)

    for p, fm, body in chars:
        cid = fm.get("id") or p.stem
        rels = fm.get("relations") or []
        plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
        plots = []
        if plot_sec:
            plots = [ln for ln in plot_sec.group(1).splitlines() if ln.strip().startswith("-")]
        pages[cid] = {
            "rel": len(rels),
            "plot": len(plots),
            "main": "## 主要关系" in body,
            "review": "## 评析" in body,
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
                    inbound[t].add("topic:" + p.stem)

    for cid in pages:
        pages[cid]["inbound"] = len(inbound[cid])

    rows = sorted((density_score(d), cid, d) for cid, d in pages.items() if density_score(d) <= max_score)
    print(f"score<={max_score}: {len(rows)} pages")
    for s, cid, d in rows:
        need = 19 - s
    print(f"{s:2d} {cid:12s} rel={d['rel']} plot={d['plot']} in={d['inbound']} need+{need}")


if __name__ == "__main__":
    main()
