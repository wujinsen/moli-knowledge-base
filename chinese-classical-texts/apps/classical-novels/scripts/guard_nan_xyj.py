#!/usr/bin/env python3
"""D1–D2 守卫：校验《西游记》八十一难索引与靠山统计。

- 81 难齐备、难序 1–81 连续无缺
- xiyouji.nan.json 存在，phases 计数与 tribulations 一致
- 妖怪关联：至少 N 难挂上妖怪、收服者阵营分类非空
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

EVENT_DIR = CONTENT / "events" / "西游记"

MIN_WITH_MONSTER = 45


def main() -> int:
    errors: list[str] = []
    warns: list[str] = []

    nos = []
    for p in sorted(EVENT_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("subtype") == "tribulation":
            nos.append(fm.get("tribulation_no") or 0)
    nos.sort()
    if len(nos) != 81:
        errors.append(f"难数 {len(nos)} ≠ 81")
    missing = [i for i in range(1, 82) if i not in set(nos)]
    if missing:
        errors.append(f"难序缺号：{missing}")

    path = DATA_DIR / "xiyouji.nan.json"
    if not path.exists():
        errors.append("缺 xiyouji.nan.json（先跑 build_nan.py --write）")
        print_errs(errors, warns)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("total") != 81:
        errors.append(f"nan.json total {data.get('total')} ≠ 81")
    psum = sum(ph["count"] for ph in data.get("phases") or [])
    if psum != data.get("total"):
        errors.append(f"phases 计数之和 {psum} ≠ total {data.get('total')}")

    with_monster = sum(1 for r in data["tribulations"] if r["monsters"])
    if with_monster < MIN_WITH_MONSTER:
        warns.append(f"挂妖怪的难 {with_monster} < {MIN_WITH_MONSTER}（建议补全 monsters）")

    by_camp = data.get("stats", {}).get("by_camp", {})
    if not by_camp:
        errors.append("收服者阵营统计为空")
    backed = sum(by_camp.get(c, 0) for c in ("佛门", "道门", "天庭"))
    if backed < 1:
        warns.append("无任何有靠山妖怪——检查妖怪页收服者字段")

    print_errs(errors, warns)
    if errors:
        return 1
    print(
        f"guard_nan_xyj 通过：81 难连续 · 挂妖怪 {with_monster} 难 · "
        f"有靠山 {backed} · 打杀 {by_camp.get('打杀自死', 0)}"
    )
    return 0


def print_errs(errors: list[str], warns: list[str]) -> None:
    for w in warns:
        print(f"  [warn] {w}")
    if errors:
        print("guard_nan_xyj 失败：")
        for e in errors:
            print(f"  [err] {e}")


if __name__ == "__main__":
    sys.exit(main())
