#!/usr/bin/env python3
"""从 hongloumeng.bestiary.json 同步人物 frontmatter 的 性格/喜好/服饰/关键物品/结局。

编辑 scripts/hlm_bestiary_fields.py 后先运行:
  python scripts/build_hlm_bestiary_json.py
再运行:
  python scripts/seed_hlm_bestiary.py
"""
from __future__ import annotations

import json

import yaml

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter

BOOK = "红楼梦"
DATA_PATH = DATA_DIR / "hongloumeng.bestiary.json"
FIELDS = ("性格", "喜好", "服饰", "关键物品", "结局")
ARRAY_FIELDS = frozenset({"喜好", "服饰", "关键物品"})


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    field_map: dict[str, dict] = data.get("fields", {})
    char_dir = CHAR_DIR / BOOK
    updated = 0

    for path in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        cid = fm.get("id", path.stem)
        expected = field_map.get(cid, {})
        changed = False
        for key in FIELDS:
            val = expected.get(key)
            if key in ARRAY_FIELDS:
                val = val if val else []
            if val:
                if fm.get(key) != val:
                    fm[key] = val
                    changed = True
            elif key in fm:
                del fm[key]
                changed = True
        if not changed:
            continue
        write_frontmatter(path, fm, body)
        likes = fm.get("喜好") or []
        costumes = fm.get("服饰") or []
        keys = fm.get("关键物品") or []
        print(
            f"  {cid}: 性格={'有' if fm.get('性格') else '—'}"
            f" · 喜好 {len(likes)} · 服饰 {len(costumes)} · 关键物品 {len(keys)}"
        )
        updated += 1

    missing = sorted(set(field_map) - {p.stem for p in char_dir.glob("*.md")})
    if missing:
        print(f"  warn: JSON 有但无人物页: {', '.join(missing)}")
    print(f"[{BOOK}] 更新 {updated} 个人物图鉴字段（共 {len(field_map)} 条定义）")


if __name__ == "__main__":
    main()
