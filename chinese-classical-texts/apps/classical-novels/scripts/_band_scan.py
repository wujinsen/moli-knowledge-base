#!/usr/bin/env python3
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CONTENT, CHAR_DIR, parse_frontmatter
from lint_character_density import density_score

book = "红楼梦"
char_dir = CHAR_DIR / book
ids = {p.stem for p in char_dir.glob("*.md")}
inbound: dict[str, set[str]] = defaultdict(set)
for p in char_dir.glob("*.md"):
    for m in re.finditer(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8-sig")):
        t = m.group(1).strip()
        if t in ids and t != p.stem:
            inbound[t].add(p.stem)
for p in (CONTENT / "topics" / book).glob("*.md"):
    for m in re.finditer(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8-sig")):
        t = m.group(1).strip()
        if t in ids:
            inbound[t].add("topic")

rows = []
for p in char_dir.glob("*.md"):
    fm, body = parse_frontmatter(p)
    cid = fm.get("id") or p.stem
    if cid == "西门庆":
        continue
    m = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    plots = sum(
        1 for ln in (m.group(1).splitlines() if m else []) if ln.strip().startswith("-")
    )
    d = {
        "rel": len(fm.get("relations") or []),
        "plot": plots,
        "main": "## 主要关系" in body,
        "review": "## 评析" in body,
        "inbound": len(inbound[cid]),
    }
    sc = density_score(d)
    if 21 <= sc <= 24:
        rows.append((sc, cid, d))

lines = [
    f"band 21-24: {len(rows)}",
    f"by score: {dict(Counter(sc for sc, _, _ in rows))}",
    f"plot: {dict(Counter(d['plot'] for _, _, d in rows))}",
    f"rel: {dict(Counter(d['rel'] for _, _, d in rows))}",
    "",
]
for sc, cid, d in sorted(rows):
    lines.append(
        f"{cid}\tsc={sc}\trel={d['rel']}\tplot={d['plot']}\tin={d['inbound']}\tneed+{25-sc}"
    )

out = Path(__file__).resolve().parent / "_band_scan.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {len(rows)} rows")
