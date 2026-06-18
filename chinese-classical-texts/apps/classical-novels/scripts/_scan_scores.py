import re, sys
from collections import defaultdict, Counter
sys.path.insert(0, "scripts")
from _common import CONTENT, iter_characters
from lint_character_density import density_score

book = "红楼梦"
chars = list(iter_characters(book))
ids = {fm.get("id") or p.stem for p, fm, _ in chars}
inbound = defaultdict(set)
for p in (CONTENT / "characters" / book).glob("*.md"):
    src = p.stem
    for m in re.finditer(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8-sig")):
        t = m.group(1).strip()
        if t in ids and t != src:
            inbound[t].add(src)
for p in (CONTENT / "topics" / book).glob("*.md"):
    for m in re.finditer(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8-sig")):
        t = m.group(1).strip()
        if t in ids:
            inbound[t].add("topic")

rows = []
for p, fm, body in chars:
    cid = fm.get("id") or p.stem
    if cid == "西门庆":
        continue
    m = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    plots = sum(1 for ln in (m.group(1).splitlines() if m else []) if ln.strip().startswith("-"))
    d = {
        "rel": len(fm.get("relations") or []),
        "plot": plots,
        "main": "## 主要关系" in body,
        "review": "## 评析" in body,
        "inbound": len(inbound[cid]),
    }
    rows.append((density_score(d), cid, d))

c = Counter(s for s, _, _ in rows)
print("score 17-25:", {k: c[k] for k in sorted(c) if 17 <= k <= 25})
weak = [(d["inbound"], s, cid) for s, cid, d in rows if d["inbound"] <= 1]
print("weak inbound<=1:", len(weak))
for n, s, cid in sorted(weak)[:20]:
    print(f"  in={n} score={s} {cid}")
dup = [(cid, d["plot"]) for s, cid, d in rows if d["plot"] >= 3]
print("all min score", min(s for s, _, _ in rows))
