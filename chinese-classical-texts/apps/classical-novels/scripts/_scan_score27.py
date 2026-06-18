#!/usr/bin/env python3
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CONTENT, iter_characters
from lint_character_density import density_score

BOOK = "红楼梦"
chars = list(iter_characters(BOOK))
ids = {fm.get("id") or p.stem for p, fm, _ in chars}
inbound: dict[str, set[str]] = defaultdict(set)
pages: dict[str, dict] = {}

for p, fm, body in chars:
    cid = fm.get("id") or p.stem
    m = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    plots = sum(
        1 for ln in (m.group(1).splitlines() if m else []) if ln.strip().startswith("-")
    )
    pages[cid] = {
        "rel": len(fm.get("relations") or []),
        "plot": plots,
        "main": "## 主要关系" in body,
        "review": "## 评析" in body,
        "weight": int(fm.get("weight") or 0),
    }

char_dir = CONTENT / "characters" / BOOK
for p in char_dir.glob("*.md"):
    src = p.stem
    for m in re.finditer(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8-sig")):
        t = m.group(1).strip()
        if t in ids and t != src:
            inbound[t].add(src)
for p in (CONTENT / "topics" / BOOK).glob("*.md"):
    for m in re.finditer(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8-sig")):
        t = m.group(1).strip()
        if t in ids:
            inbound[t].add("topic")

for cid in pages:
    pages[cid]["inbound"] = len(inbound[cid])

rows = []
for cid, d in pages.items():
    if cid == "西门庆":
        continue
    sc = density_score(d)
    if sc == 27:
        rows.append((cid, d))

lines = [f"score=27: {len(rows)} pages\n"]
for flag in ("inbound", "plot", "rel"):
    buckets: dict[int, list[str]] = defaultdict(list)
    for cid, d in rows:
        buckets[d[flag]].append(cid)
    lines.append(f"--- by {flag} ---")
    for k in sorted(buckets):
        lines.append(f"  {flag}={k}: {len(buckets[k])}")
    lines.append("")

lines.append("--- detail ---")
for cid, d in sorted(rows, key=lambda x: (x[1]["inbound"], x[1]["rel"], x[0])):
    lines.append(
        f"{cid}\tplot={d['plot']}\trel={d['rel']}\tin={d['inbound']}\tw={d['weight']}"
    )

out = Path(__file__).resolve().parent / "_score27_scan.txt"
ids_out = Path(__file__).resolve().parent / "_tier13_ids.txt"
out.write_text("\n".join(lines), encoding="utf-8")
if rows:
    ids_out.write_text("\n".join(cid for cid, _ in sorted(rows)), encoding="utf-8")
print(f"wrote {out.name}: {len(rows)} pages")
