#!/usr/bin/env python3
"""金瓶梅名物 ingest 第二批：六房服饰 / 饮食宴席 / 帮闲银两 + 回目 items[] 回填。"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from _common import CHAR_DIR, CHAPTER_DIR, parse_frontmatter
from tag_chapter_meta import format_list, parse_list_field

BOOK = "金瓶梅"

# 回目 → 追加 items（与 frontmatter 合并去重）
CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    1: ["结拜分资"],
    11: ["银丝鬏髻", "银红比甲"],
    23: ["认干亲礼"],
    27: ["织金莲五彩蟒衣"],
    31: ["吴典恩借银"],
    41: ["遍地金比甲", "满池娇分心"],
    74: ["貂鼠皮袄", "大红遍地金鹤袖", "李娇儿皮袄"],
    78: ["果馅金饼", "浙江酒", "锦裙绣袄"],
    79: ["元宵圆子"],
    80: ["帮闲凑分"],
}

SIX_WIVES_ITEMS: dict[str, dict[str, list[str]]] = {
    "吴月娘": {"服饰": ["锦裙绣袄", "貂鼠皮袄"], "关键物品": ["薛姑子种子方"]},
    "李娇儿": {"服饰": ["李娇儿皮袄"], "关键物品": []},
    "孟玉楼": {
        "服饰": ["银丝鬏髻", "银红比甲", "遍地金比甲"],
        "关键物品": ["月琴", "簪环", "满池娇分心"],
    },
    "孙雪娥": {"服饰": ["李娇儿皮袄"], "关键物品": []},
    "潘金莲": {
        "服饰": ["大红段子袄", "白绫袄儿", "大红遍地金鹤袖", "遍地金比甲"],
        "关键物品": ["烧猪头", "红睡鞋", "销金裙带", "琵琶", "药五香酒", "雪狮子"],
    },
    "李瓶儿": {
        "服饰": ["织金莲五彩蟒衣", "貂鼠皮袄", "金丝鬏髻"],
        "关键物品": [
            "五灵脂",
            "任医官诊血崩",
            "螃蟹鲜",
            "酥油泡螺儿",
            "金锁",
            "红牙象板",
            "雪狮子",
        ],
    },
}

SIX_WIVES_COSTUMES_FOR_SIEMEN = [
    "吴月娘",
    "李娇儿",
    "孟玉楼",
    "孙雪娥",
    "潘金莲",
    "李瓶儿",
]


def merge_list_field(fm: dict, key: str, vals: list[str]) -> bool:
    cur = list(fm.get(key) or [])
    merged = sorted(set(cur) | set(vals))
    if merged == cur:
        return False
    fm[key] = merged
    return True


def patch_characters() -> int:
    n = 0
    for cid, fields in SIX_WIVES_ITEMS.items():
        path = CHAR_DIR / BOOK / f"{cid}.md"
        if not path.is_file():
            continue
        fm, body = parse_frontmatter(path)
        changed = False
        for key in ("服饰", "关键物品"):
            if key in fields and merge_list_field(fm, key, fields[key]):
                changed = True
        if not changed:
            continue
        text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        path.write_text(f"---\n{text}---\n{body}", encoding="utf-8")
        print(f"  人物 {cid}")
        n += 1
    return n


def patch_chapters() -> int:
    n = 0
    base = CHAPTER_DIR / BOOK
    for ch, add in CHAPTER_ITEMS_ADD.items():
        for p in base.rglob(f"{ch:03d}.md"):
            raw = p.read_text(encoding="utf-8-sig")
            cur = list(parse_list_field(raw, "items") or [])
            merged = sorted(set(cur) | set(add))
            if merged == cur:
                continue
            new_fm = format_list("items", merged)
            if re.search(r"^items:\s*\[", raw, re.M):
                raw = re.sub(r"^items:\s*\[[^\]]*\]", new_fm.strip(), raw, count=1, flags=re.M)
            else:
                raw = re.sub(r"(^summary:.*\n)", rf"\1{new_fm}\n", raw, count=1, flags=re.M)
            p.write_text(raw, encoding="utf-8")
            print(f"  回目 第{ch}回 +{len(merged)-len(cur)}")
            n += 1
    return n


def patch_shared_costumes() -> int:
    """妻妾共用服饰补 wearers 列表。"""
    from _common import CONTENT

    updates = {
        "遍地金比甲": {"wearers": SIX_WIVES_COSTUMES_FOR_SIEMEN},
        "满池娇分心": {"wearers": SIX_WIVES_COSTUMES_FOR_SIEMEN},
        "大红妆花袍": {"wearers": SIX_WIVES_COSTUMES_FOR_SIEMEN},
    }
    n = 0
    d = CONTENT / "costumes" / BOOK
    for iid, extra in updates.items():
        path = d / f"{iid}.md"
        if not path.is_file():
            continue
        fm, body = parse_frontmatter(path)
        if fm.get("wearers") == extra["wearers"]:
            continue
        fm["wearers"] = extra["wearers"]
        fm.pop("wearer", None)
        text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        path.write_text(f"---\n{text}---\n{body}", encoding="utf-8")
        print(f"  服饰 {iid} wearers")
        n += 1
    return n


def main() -> None:
    print(f"[{BOOK}] patch batch2 …")
    c = patch_characters()
    ch = patch_chapters()
    co = patch_shared_costumes()
    print(f"  人物 {c} · 回目 {ch} · 共用服饰 {co}")


if __name__ == "__main__":
    main()
