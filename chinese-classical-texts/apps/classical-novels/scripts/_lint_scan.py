import re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CONTENT, iter_characters
from lint_character_density import density_score

BOOK = "红楼梦"
chars = list(iter_characters(BOOK))
ids = {fm.get("id") or p.stem for p, fm, _ in chars}
from collections import defaultdict
inbound = defaultdict(set)
pages = {}
for p, fm, body in chars:
    cid = fm.get("id") or p.stem
    m = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    plots = sum(1 for ln in (m.group(1).splitlines() if m else []) if ln.strip().startswith("-"))
    pages[cid] = {
        "rel": len(fm.get("relations") or []),
        "plot": plots,
        "main": "## 主要关系" in body,
        "review": "## 评析" in body,
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

scores = Counter()
plot2 = []
for cid, d in pages.items():
    if cid == "西门庆":
        continue
    sc = density_score(d)
    scores[sc] += 1
    if d["plot"] <= 2:
        plot2.append((sc, cid, d["plot"], d["rel"]))

lines = ["score distribution:"]
for sc in sorted(scores):
    lines.append(f"  {sc}: {scores[sc]}")
lines.append(f"\nplot<=2: {len(plot2)}")
for row in sorted(plot2)[:30]:
    lines.append(f"  {row}")
Path("scripts/_lint_scan.txt").write_text("\n".join(lines), encoding="utf-8")
print("min", min(scores), "max", max(scores))
