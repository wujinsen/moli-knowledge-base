#!/usr/bin/env python3
"""C6 guard: 名物谶纬 P1–P3 — 金瓶梅 imagery inference / phase / karma / chains。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
IMG = CONTENT / "imagery" / "金瓶梅"
OMEN = {"name_omen", "object_omen", "tune_omen"}
PHASES = {"欲起", "聚敛", "极盛", "反噬", "散尽"}
TEMPS = {"冷", "热"}


def main() -> int:
    errors: list[str] = []

    items = []
    for p in sorted(IMG.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") == "金瓶梅":
            items.append(fm)

    if len(items) < 40:
        errors.append(f"imagery 过少: {len(items)}")

    for fm in items:
        st = fm.get("subtype")
        if st not in OMEN:
            continue
        links = fm.get("links") or []
        inf = [l for l in links if l.get("inference")]
        if not inf:
            errors.append(f"P1 {fm['id']}: 无 inference 边")
        for l in inf:
            if not l.get("phase") or l.get("phase") not in PHASES:
                errors.append(f"P2 {fm['id']}: inference 缺 phase")
            if l.get("temperature") not in TEMPS:
                errors.append(f"P2 {fm['id']}: inference 缺 temperature")

    karma_path = DATA_DIR / "jinpingmei.shi-karma.json"
    if not karma_path.exists():
        errors.append("missing jinpingmei.shi-karma.json")
    else:
        karma = json.loads(karma_path.read_text(encoding="utf-8"))
        for p in PHASES:
            if not karma.get("by_phase", {}).get(p):
                errors.append(f"P3 karma 阶段 {p} 为空")
        if len(karma.get("chains") or []) < 5:
            errors.append(f"P3 chains 过少: {len(karma.get('chains') or [])}")

    chain_path = DATA_DIR / "金瓶梅.imagery-chains.json"
    if not chain_path.exists():
        errors.append("missing 金瓶梅.imagery-chains.json")

    shi_path = DATA_DIR / "shi_index.json"
    if shi_path.exists():
        shi = json.loads(shi_path.read_text(encoding="utf-8"))
        jpm = (shi.get("books") or {}).get("jinpingmei", {})
        if jpm.get("count", 0) < 40:
            errors.append(f"shi_index jpm 过少: {jpm.get('count')}")

    if errors:
        print("guard_shi_jpm FAILED:")
        for e in errors[:25]:
            print(f"  - {e}")
        return 1

    karma = json.loads(karma_path.read_text(encoding="utf-8"))
    print(
        f"guard_shi_jpm OK: {len(items)} imagery · "
        f"karma {sum(karma['counts'].values())} slots · "
        f"{len(karma['chains'])} chains"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
