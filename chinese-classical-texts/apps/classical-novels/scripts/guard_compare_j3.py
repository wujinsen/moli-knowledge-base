#!/usr/bin/env python3
"""C5 guard: 版本对勘 J3 — compare.json 与三版本对完整性。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import DATA_DIR

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PAIRS = {
    "jinpingmei": ["cihua-chongzhen", "cihua-zhupo", "chongzhen-zhupo"],
    "xiyouji": ["shide-tongben"],
}


def check_slug(slug: str) -> list[str]:
    errors: list[str] = []
    path = DATA_DIR / f"{slug}.compare.json"
    if not path.exists():
        return [f"missing {slug}.compare.json — run build_compare.py --write"]
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("pairs", "by_chapter", "variant_total", "topics"):
        if key not in data:
            errors.append(f"{slug}: 缺字段 {key}")

    for ps in REQUIRED_PAIRS.get(slug, []):
        if ps not in (data.get("pairs") or {}):
            errors.append(f"{slug}: 缺对勘对 {ps}")

    if slug == "jinpingmei":
        if data.get("variant_total", 0) < 10:
            errors.append(f"jinpingmei variants 过少: {data.get('variant_total')}")
        cc = data.get("chapter_count_with_variants", 0)
        if cc < 5:
            errors.append(f"jinpingmei 异文回过少: {cc}")
        topics = data.get("topics") or []
        if len(topics) < 5:
            errors.append(f"jinpingmei variant topics 过少: {len(topics)}")

    return errors


def main() -> int:
    errors: list[str] = []
    for slug in REQUIRED_PAIRS:
        errors.extend(check_slug(slug))

    if errors:
        print("guard_compare_j3 FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    jpm = json.loads((DATA_DIR / "jinpingmei.compare.json").read_text(encoding="utf-8"))
    print(
        f"guard_compare_j3 OK: jpm {jpm['variant_total']} variants · "
        f"{len(jpm['pairs'])} pairs · {len(jpm['topics'])} graph topics"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
