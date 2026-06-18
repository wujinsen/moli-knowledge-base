#!/usr/bin/env python3
from pathlib import Path
from _common import parse_frontmatter

CONTENT = Path(__file__).resolve().parents[1] / "src" / "content" / "imagery"
for book in ["红楼梦", "金瓶梅", "西游记"]:
    d = CONTENT / book
    if not d.exists():
        continue
    files = list(d.glob("*.md"))
    thin = []
    no_layer = []
    for p in sorted(files):
        fm, body = parse_frontmatter(p)
        b = body.strip()
        if len(b) < 120 or "……" in b or "..." in fm.get("text", ""):
            thin.append(p.stem)
        if book == "红楼梦" and not fm.get("layer"):
            no_layer.append(p.stem)
    print(f"=== {book} ({len(files)}) ===")
    print(f"thin/stub: {len(thin)}")
    print(f"no layer: {len(no_layer)}")
    if thin:
        print(" ", ", ".join(thin[:15]), ("..." if len(thin) > 15 else ""))
