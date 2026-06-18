#!/usr/bin/env python3
"""金瓶梅名物 ingest 第三批：物象谶实体化 + 回目 items[] 正文扫描回填。"""
from __future__ import annotations

import re

from _common import CHAPTER_DIR
from lint_modules import list_known_item_ids
from tag_chapter_meta import find_ids, format_list, load_item_pairs, parse_list_field, split_body, strip_html

BOOK = "金瓶梅"

# 情节锚点回目 → 追加 items（与自动扫描合并）
CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    1: ["宴饮纵酒", "金华酒", "琵琶"],
    2: ["梅汤"],
    5: ["砒霜"],
    6: ["骨殖", "琵琶"],
    7: ["月琴", "销金裙带"],
    12: ["琵琶", "簪环"],
    14: ["犀角带", "李瓶儿之财"],
    15: ["元宵灯", "白绫袄儿", "遍地金比甲", "貂鼠皮袄", "琵琶", "簪环", "寿面"],
    16: ["蔡府寿礼", "香蜡批文", "琵琶", "象牙牌", "寿面", "李瓶儿之财"],
    18: ["琵琶"],
    20: ["满池娇分心", "簪环", "琵琶"],
    21: ["满池娇分心", "月琴", "金华酒", "琵琶"],
    22: ["簪环", "汗巾"],
    23: ["金华酒", "烧猪头"],
    28: ["药五香酒", "红睡鞋"],
    29: ["梅汤", "红睡鞋"],
    34: ["糟鲥鱼", "桂花饼"],
    46: ["遍地金比甲", "貂鼠皮袄", "琵琶"],
    52: ["药五香酒", "烧猪头"],
    60: ["汗巾"],
    62: ["棺木"],
    63: ["大红妆花袍"],
    66: ["拣金挑牙"],
    67: ["香蜡批文", "拣金挑牙"],
    68: ["衣梅"],
    70: ["红牙象板"],
    77: ["貂鼠皮袄"],
    95: ["锦裙绣袄"],
    61: ["葡萄酒"],
    100: ["月琴"],
}


def merge_chapter_items() -> int:
    pairs = load_item_pairs(BOOK)
    known = list_known_item_ids(BOOK)
    n = 0
    base = CHAPTER_DIR / BOOK
    for p in sorted(base.rglob("*.md")):
        if "词话本" not in str(p):
            continue
        m = re.search(r"(\d+)\.md$", p.name)
        if not m:
            continue
        ch = int(m.group(1))
        raw = p.read_text(encoding="utf-8-sig")
        cur = set(parse_list_field(raw, "items") or [])
        body = strip_html(split_body(raw))
        found = set(find_ids(body, pairs, {})) & known
        found |= set(CHAPTER_ITEMS_ADD.get(ch, []))
        merged = sorted(cur | found)
        if merged == sorted(cur):
            continue
        new_fm = format_list("items", merged)
        if re.search(r"^items:\s*\[", raw, re.M):
            raw = re.sub(r"^items:\s*\[[^\]]*\]", new_fm.strip(), raw, count=1, flags=re.M)
        else:
            raw = re.sub(r"(^summary:.*\n)", rf"\1{new_fm}\n", raw, count=1, flags=re.M)
        p.write_text(raw, encoding="utf-8")
        print(f"  词话本 第{ch}回 +{len(merged) - len(cur)} → {len(merged)}")
        n += 1
    return n


def main() -> None:
    print(f"[{BOOK}] patch batch3 …")
    ch = merge_chapter_items()
    print(f"  回目回填 {ch}")


if __name__ == "__main__":
    main()
