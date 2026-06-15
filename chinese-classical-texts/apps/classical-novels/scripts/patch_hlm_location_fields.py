#!/usr/bin/env python3
"""One-shot: 红楼梦 location nearby + plaque/couplet 补全。

用法: python scripts/patch_hlm_location_fields.py [--write]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CONTENT, parse_frontmatter

BOOK = "红楼梦"
LOC_DIR = CONTENT / "locations" / BOOK

NEARBY: dict[str, list[str]] = {
    "临安伯府": ["锦乡侯府", "南安王府", "乐善郡王府", "宁荣街"],
    "临昌伯府": ["锦乡侯府", "临安伯府", "乐善郡王府", "宁荣街"],
    "乐善郡王府": ["南安王府", "北静王府", "临昌伯府", "永昌驸马府", "宁荣街"],
    "北静王府": ["南安王府", "乐善郡王府", "忠顺王府", "永昌驸马府", "宁荣街"],
    "十里屯": ["孝慈县", "郝家庄", "急流津"],
    "南安王府": ["北静王府", "乐善郡王府", "锦乡侯府", "宁荣街"],
    "姑子庙": ["铁槛寺", "地藏庵", "小花枝巷"],
    "孙家": ["宁荣街", "甄家", "金陵城"],
    "小花枝巷": ["赖大家", "宁荣街", "姑子庙"],
    "忠顺王府": ["北静王府", "南安王府", "宁荣街"],
    "永昌驸马府": ["北静王府", "乐善郡王府", "临昌伯府", "南安王府"],
    "清虚观": ["铁槛寺", "水月庵", "孝慈县"],
    "甄家": ["宁荣街", "金陵城", "孙家"],
    "破寺": ["金陵城", "铁槛寺", "地藏庵"],
    "郝家庄": ["十里屯", "孝慈县", "金陵城"],
    "锦乡侯府": ["临昌伯府", "临安伯府", "宁荣街", "南安王府"],
}

PLAQUE: dict[str, dict] = {
    "蓼溆": {"plaque": "蓼汀花溆"},
    "秋爽斋": {"plaque": "风清玉爽"},
    "凸碧堂": {"plaque": "凸碧"},
    "凹晶馆": {"plaque": "凹晶"},
    "藕香榭": {"plaque": "藕香榭"},
    "栊翠庵": {"plaque": "栊翠庵"},
    "芦雪庵": {"plaque": "荻芦夜雪", "aliases_add": ["荻芦夜雪"]},
    "滴翠亭": {"plaque": "滴翠亭"},
    "晓翠堂": {"plaque": "晓翠堂"},
    "缀锦阁": {"plaque": "缀锦阁"},
    "缀锦楼": {"plaque": "缀锦楼"},
    "嘉荫堂": {"plaque": "嘉荫堂"},
    "蓼风轩": {"plaque": "蓼风轩", "aliases_add": ["桐剪秋风"]},
    "暖香坞": {"plaque": "暖香坞"},
    "紫菱洲": {"plaque": "荇叶渚", "aliases_add": ["荇叶渚"]},
    "曲径通幽": {
        "couplet": {"upper": "曲径通幽处", "lower": "禅房花木深"},
    },
    "省亲别墅": {
        "plaque": "顾恩思义",
        "aliases_add": ["天仙宝境"],
        "couplet": {
            "upper": "天地启宏慈，赤子苍头同感戴",
            "lower": "古今垂旷典，九州万国被恩荣",
        },
    },
    "大观园": {"plaque": "大观园"},
    "沁芳闸": {"plaque": "沁芳闸"},
}


def format_nearby(items: list[str]) -> str:
    return f"nearby: [{', '.join(items)}]"


def format_couplet(c: dict[str, str]) -> str:
    return f"couplet:\n  upper: {c['upper']}\n  lower: {c['lower']}"


def upsert_nearby(raw: str, items: list[str]) -> str:
    line = format_nearby(items)
    if re.search(r"^nearby:", raw, re.M):
        return re.sub(r"^nearby:.*$", line, raw, count=1, flags=re.M)
    for anchor in ("first_appear:", "appear_in:", "summary:", "tags:", "features:"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + line + "\n" + raw[idx:]
    return raw.rstrip() + "\n" + line + "\n"


def upsert_plaque(raw: str, plaque: str) -> str:
    if re.search(r"^plaque:", raw, re.M):
        return re.sub(r"^plaque:.*$", f"plaque: {plaque}", raw, count=1, flags=re.M)
    for anchor in ("couplet:", "features:", "occupants:", "nearby:", "first_appear:"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + f"plaque: {plaque}\n" + raw[idx:]
    return raw.rstrip() + f"\nplaque: {plaque}\n"


def upsert_couplet(raw: str, couplet: dict[str, str]) -> str:
    block = format_couplet(couplet)
    if re.search(r"^couplet:", raw, re.M):
        return re.sub(
            r"^couplet:\n(?:  .+\n)+",
            block + "\n",
            raw,
            count=1,
            flags=re.M,
        )
    for anchor in ("features:", "occupants:", "nearby:", "first_appear:", "summary:"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + block + "\n" + raw[idx:]
    if re.search(r"^plaque:", raw, re.M):
        return re.sub(
            r"^(plaque:.*\n)",
            r"\1" + block + "\n",
            raw,
            count=1,
            flags=re.M,
        )
    return raw.rstrip() + "\n" + block + "\n"


def upsert_aliases(raw: str, add: list[str]) -> str:
    m = re.search(r"^aliases:\s*\[(.*?)\]", raw, re.M)
    if m:
        existing = [x.strip() for x in m.group(1).split(",") if x.strip()]
        merged = list(dict.fromkeys(existing + add))
        return re.sub(
            r"^aliases:\s*\[.*?\]",
            f"aliases: [{', '.join(merged)}]",
            raw,
            count=1,
            flags=re.M,
        )
    line = f"aliases: [{', '.join(add)}]"
    for anchor in ("book:", "category:", "parent:"):
        idx = raw.find(anchor)
        if idx >= 0:
            end = raw.find("\n", idx)
            return raw[: end + 1] + line + "\n" + raw[end + 1 :]
    return raw


def patch_file(path: Path, *, write: bool) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return []
    lid = path.stem
    fm_raw, body = parts[1], parts[2]
    changed: list[str] = []

    if lid in NEARBY:
        new_fm = upsert_nearby(fm_raw, NEARBY[lid])
        if new_fm != fm_raw:
            fm_raw = new_fm
            changed.append("nearby")

    spec = PLAQUE.get(lid)
    if spec:
        if "plaque" in spec:
            new_fm = upsert_plaque(fm_raw, spec["plaque"])
            if new_fm != fm_raw:
                fm_raw = new_fm
                changed.append("plaque")
        if "couplet" in spec:
            new_fm = upsert_couplet(fm_raw, spec["couplet"])
            if new_fm != fm_raw:
                fm_raw = new_fm
                changed.append("couplet")
        if spec.get("aliases_add"):
            new_fm = upsert_aliases(fm_raw, spec["aliases_add"])
            if new_fm != fm_raw:
                fm_raw = new_fm
                changed.append("aliases")

    if changed and write:
        path.write_text(f"---{fm_raw}---{body}", encoding="utf-8")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"patch_hlm_location_fields [{mode}]\n")

    stats: dict[str, int] = {}
    for p in sorted(LOC_DIR.glob("*.md")):
        for c in patch_file(p, write=args.write):
            stats[c] = stats.get(c, 0) + 1
            print(f"  {p.stem}: {c}")

    print(f"\n{'Would patch' if not args.write else 'Patched'}: {stats}")
    if not args.write:
        print("（加 --write 写回）")


if __name__ == "__main__":
    main()
