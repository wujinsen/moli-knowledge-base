#!/usr/bin/env python3
"""红楼梦建筑 enrichment：第17–18回匾联、植物矩阵、红香圃、嵌套节点地图坐标。

用法: python scripts/patch_hlm_garden_enrich.py [--write]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CONTENT, parse_frontmatter
from patch_hlm_location_fields import format_couplet, upsert_couplet, upsert_plaque

BOOK = "红楼梦"
LOC_DIR = CONTENT / "locations" / BOOK

# 第18回元春赐匾（fact）
CH18_PLAQUE: dict[str, str] = {
    "缀锦楼": "崇光泛彩",
    "蓼风轩": "桐剪秋风",
    "缀锦阁": "含芳阁",
}

# 第18回元春另赐匾额名（作 alias / 补充）
CH18_PLAQUE_ALIAS: dict[str, list[str]] = {
    "潇湘馆": ["梨花春雨"],
    "芦雪庵": ["荻芦夜雪"],
}

# 第18回宝玉奉诏补诗可作文联（fact，非第17回题额）
CH18_COUPLETS: dict[str, dict[str, str]] = {
    "怡红院": {
        "upper": "绿蜡春犹卷",
        "lower": "红妆夜未眠",
    },
}

# 植物矩阵（对齐 garden-scholarship plant_matrix + 方位考证表）
PLANTS: dict[str, list[str]] = {
    "潇湘馆": ["翠竹", "梨花", "芭蕉"],
    "怡红院": ["芭蕉", "西府海棠", "蔷薇", "宝相花"],
    "蘅芜苑": ["杜若", "蘅芜", "茝兰", "清葛", "紫芸", "青芷"],
    "稻香村": ["杏花", "桑", "榆", "槿", "柘", "蔬菜"],
    "秋爽斋": ["梧桐", "芭蕉", "白菊", "佛手"],
    "缀锦楼": ["紫菱", "荇叶"],
    "蓼风轩": ["梧桐", "蓼", "荇叶"],
    "栊翠庵": ["红梅", "梅花"],
}

FURNISHINGS_ADD: dict[str, list[str]] = {
    "缀锦楼": ["围屏", "花灯", "戏具", "帐幔"],
    "蓼风轩": ["画具", "棋枰"],
}

# 红香圃 appear_in 同步到怡红院 nearby
NEARBY_ADD: dict[str, list[str]] = {
    "怡红院": ["红香圃"],
    "红香圃": ["怡红院", "蜂腰桥", "翠烟桥", "后门"],
    "暖香坞": ["蓼风轩", "栊翠庵"],
    "晓翠堂": ["秋爽斋", "藕香榭"],
}

APPEAR_IN_ADD: dict[str, list[str]] = {
    "蓼溆": ["第17回"],
    "红香圃": ["第62回", "第63回"],
}

# 地图：嵌套节点 + 红香圃（inference 坐标）
GARDEN_COORD: dict[str, dict] = {
    "红香圃": {
        "garden_zone": "亭榭",
        "coord": (460, 430),
    },
    "暖香坞": {
        "garden_zone": "居所",
        "coord": (700, 395),
    },
    "晓翠堂": {
        "garden_zone": "亭榭",
        "coord": (740, 265),
    },
}

ALIASES_ADD: dict[str, list[str]] = {
    "缀锦楼": ["崇光泛彩"],
    "缀锦阁": ["含芳阁"],
    "凸碧堂": ["凸碧山庄"],
    "凹晶馆": ["凹晶溪馆"],
    "蓼风轩": ["桐剪秋风"],
}


def upsert_plants(raw: str, plants: list[str]) -> str:
    line = f"plants: [{', '.join(plants)}]"
    if re.search(r"^plants:", raw, re.M):
        return re.sub(r"^plants:.*$", line, raw, count=1, flags=re.M)
    for anchor in ("furnishings:", "features:", "first_appear:"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + line + "\n" + raw[idx:]
    return raw.rstrip() + "\n" + line + "\n"


def upsert_list_field(raw: str, key: str, items: list[str]) -> str:
    line = f"{key}: [{', '.join(items)}]"
    if re.search(rf"^{re.escape(key)}:", raw, re.M):
        return re.sub(rf"^{re.escape(key)}:.*$", line, raw, count=1, flags=re.M)
    return raw.rstrip() + "\n" + line + "\n"


def merge_list(existing: list | None, add: list[str]) -> list[str]:
    out: list[str] = []
    for x in (existing or []) + add:
        if x not in out:
            out.append(x)
    return out


def upsert_aliases(raw: str, add: list[str]) -> str:
    fm, _ = parse_frontmatter_from_raw(raw)
    merged = merge_list(fm.get("aliases"), add)
    line = f"aliases: [{', '.join(merged)}]"
    if re.search(r"^aliases:", raw, re.M):
        return re.sub(r"^aliases:.*$", line, raw, count=1, flags=re.M)
    return raw


def parse_frontmatter_from_raw(raw: str) -> tuple[dict, str]:
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    import yaml

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except Exception:
        fm = {}
    return fm, parts[2]


def upsert_coord_block(raw: str, x: int, y: int) -> str:
    block = f"coord:\n  x: {x}\n  y: {y}\n"
    if re.search(r"^coord:", raw, re.M):
        return re.sub(r"^coord:\n(?:  .+\n)+", block, raw, count=1, flags=re.M)
    for anchor in ("garden_zone:", "summary:", "tags:", "appear_in:"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + block + raw[idx:]
    return raw.rstrip() + "\n" + block


def upsert_scalar(raw: str, key: str, value: str) -> str:
    line = f"{key}: {value}"
    if re.search(rf"^{re.escape(key)}:", raw, re.M):
        return re.sub(rf"^{re.escape(key)}:.*$", line, raw, count=1, flags=re.M)
    return raw.rstrip() + "\n" + line + "\n"


def patch_file(path: Path, write: bool) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    lid = path.stem
    changes: list[str] = []
    fm, _ = parse_frontmatter(path)

    if lid in CH18_PLAQUE:
        raw = upsert_plaque(raw, CH18_PLAQUE[lid])
        changes.append(f"plaque→{CH18_PLAQUE[lid]}")

    if lid in CH18_COUPLETS and not fm.get("couplet"):
        raw = upsert_couplet(raw, CH18_COUPLETS[lid])
        changes.append("couplet(ch18)")

    if lid in CH18_PLAQUE_ALIAS:
        raw = upsert_aliases(raw, CH18_PLAQUE_ALIAS[lid])
        changes.append("aliases(ch18)")

    if lid in PLANTS:
        raw = upsert_plants(raw, PLANTS[lid])
        changes.append("plants")

    if lid in ALIASES_ADD:
        raw = upsert_aliases(raw, ALIASES_ADD[lid])
        changes.append("aliases")

    if lid in NEARBY_ADD:
        merged = merge_list(fm.get("nearby"), NEARBY_ADD[lid])
        raw = upsert_list_field(raw, "nearby", merged)
        changes.append("nearby")

    if lid in APPEAR_IN_ADD:
        merged = merge_list(fm.get("appear_in"), APPEAR_IN_ADD[lid])
        raw = upsert_list_field(raw, "appear_in", merged)
        changes.append("appear_in")

    if lid in GARDEN_COORD:
        g = GARDEN_COORD[lid]
        raw = upsert_scalar(raw, "garden_zone", g["garden_zone"])
        raw = upsert_coord_block(raw, g["coord"][0], g["coord"][1])
        changes.append("garden coord")

    if changes and write:
        path.write_text(raw, encoding="utf-8")
    return changes


def create_hongxiangpu(write: bool) -> bool:
    path = LOC_DIR / "红香圃.md"
    if path.exists():
        return False
    body = """---
id: 红香圃
type: building
name: 红香圃
aliases: []
book: 红楼梦
category: 其他
parent: 大观园
occupants: []
nearby: [怡红院, 蜂腰桥, 翠烟桥, 后门]
plaque: 红香圃
features:
  - 怡红院外花圃，宝玉生日夜宴处
  - 第62–63回群芳夜宴、芳官改男装、查夜
  - 与怡红院「红香绿玉」名脉相承
plants: [海棠, 蔷薇, 宝相花]
first_appear: 第62回
appear_in: [第62回, 第63回]
tags: [夜宴, 怡红院, 群芳]
coord:
  x: 460
  y: 430
garden_zone: 亭榭
summary: 大观园怡红院外花圃，第62–63回宝玉生日群芳夜宴于此。
---

## 位置与格局

[[大观园]]内，[[怡红院]]外之圃。第62回宝玉生日，袭人、晴雯等凑份子，晚间于怡红院、红香圃一带群芳夜宴。

## 关联人物

- [[贾宝玉]]、[[袭人]]、[[晴雯]]、[[芳官]]、[[麝月]]等

## 关键情节

- 宝玉生日夜宴、芳官改扮（第62–63回）。
- 林之孝家的查夜（第63回）。

## 评析

「红香」承怡红院旧名，夜宴于此而事端亦由此生，是盛极将散之小高潮。
"""
    if write:
        path.write_text(body, encoding="utf-8")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    n = 0
    if create_hongxiangpu(args.write):
        print("created 红香圃.md")
        n += 1
    for p in sorted(LOC_DIR.glob("*.md")):
        ch = patch_file(p, args.write)
        if ch:
            print(f"{'W' if args.write else 'D'} {p.stem}: {', '.join(ch)}")
            n += 1
    print(f"{'Updated' if args.write else 'Dry-run'} {n} file(s)")


if __name__ == "__main__":
    main()
