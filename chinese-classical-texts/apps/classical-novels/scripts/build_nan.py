#!/usr/bin/env python3
"""D1–D2 X3：生成 xiyouji.nan.json（八十一难索引 + 靠山/难度统计）。

把 81 难事件与妖怪页（原型 / 收服者 / 法宝）连接，按五阶段排列，
统计「收服者阵营」分布（道门 / 佛门 / 天庭 / 打杀自死），以及妖怪、法宝、
地点频次。揭示「有靠山的妖怪被收走、无背景的被打杀」这一讽喻结构。
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

EVENT_DIR = CONTENT / "events" / "西游记"
CHAR_DIR = CONTENT / "characters" / "西游记"

PHASES = [
    {"key": "origin", "label": "前世因缘", "range": [1, 4]},
    {"key": "start", "label": "初出长安", "range": [5, 16]},
    {"key": "mid", "label": "中途魔障", "range": [17, 55]},
    {"key": "late", "label": "后期险途", "range": [56, 79]},
    {"key": "finish", "label": "功果圆满", "range": [80, 81]},
]

# 收服者 / 原型 → 阵营。命中关键词即归类。
CAMP_KEYS = {
    "佛门": ["如来", "佛祖", "观音", "菩萨", "弥勒", "灵吉", "毗蓝", "罗汉", "揭谛", "佛"],
    "道门": ["老君", "太上", "镇元", "真仙", "寿星", "南极", "天尊", "真人", "道祖"],
    "天庭": [
        "玉帝", "玉皇", "天王", "李靖", "哪吒", "二郎", "星官", "金星", "太白",
        "星君", "天蓬", "卷帘", "二十八宿", "昴日", "奎木", "土地", "山神", "龙王",
    ],
}


def classify_backer(subduer: str, prototype: str) -> str:
    text = f"{subduer or ''} {prototype or ''}"
    if not (subduer or prototype):
        return "未知"
    # 打杀 / 自死优先（无靠山）
    if re.search(r"打死|打杀|杀|斩|自死|烧死|现形|亡", subduer or ""):
        # 但若同时点名某神佛，说明仍有靠山——以神佛归类
        for camp, keys in CAMP_KEYS.items():
            if any(k in (subduer or "") for k in keys):
                return camp
        return "打杀自死"
    for camp, keys in CAMP_KEYS.items():
        if any(k in text for k in keys):
            return camp
    # 孙悟空 / 师徒亲手收伏且无背景
    if re.search(r"悟空|行者|八戒|沙僧|唐僧", subduer or ""):
        return "打杀自死"
    return "未知"


def clean_subduer(raw: str) -> str:
    return re.sub(r"[（(].*?[)）]", "", raw or "").strip()


def phase_for(no: int) -> dict:
    for p in PHASES:
        if p["range"][0] <= no <= p["range"][1]:
            return p
    return PHASES[2]


def load_monsters() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(CHAR_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("type") != "monster":
            continue
        subduer = str(fm.get("收服者") or "")
        prototype = str(fm.get("原型") or "")
        artifacts = fm.get("法宝") or []
        if isinstance(artifacts, str):
            artifacts = [artifacts]
        out[fm["id"]] = {
            "name": fm["id"],
            "aliases": fm.get("aliases") or [],
            "原型": prototype,
            "收服者": clean_subduer(subduer),
            "收服者_raw": subduer,
            "法宝": [a for a in artifacts if a],
            "洞府": str(fm.get("洞府") or ""),
            "camp": classify_backer(subduer, prototype),
        }
    # 别名索引
    alias_idx: dict[str, dict] = {}
    for m in out.values():
        for a in m["aliases"]:
            alias_idx[a] = m
    return {**alias_idx, **out}


def build() -> dict:
    monsters = load_monsters()
    rows: list[dict] = []
    camp_counter: Counter = Counter()
    monster_counter: Counter = Counter()
    artifact_counter: Counter = Counter()
    location_counter: Counter = Counter()

    for p in sorted(EVENT_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("subtype") != "tribulation":
            continue
        no = fm.get("tribulation_no") or 0
        ph = phase_for(no)
        ms = []
        for mname in fm.get("monsters") or []:
            monster_counter[mname] += 1
            m = monsters.get(mname)
            if m:
                ms.append(
                    {
                        "name": mname,
                        "原型": m["原型"],
                        "收服者": m["收服者"],
                        "camp": m["camp"],
                        "法宝": m["法宝"],
                    }
                )
                camp_counter[m["camp"]] += 1
            else:
                ms.append({"name": mname, "原型": "", "收服者": "", "camp": "未知", "法宝": []})
                camp_counter["未知"] += 1
        arts = fm.get("artifacts") or []
        for a in arts:
            artifact_counter[a] += 1
        for loc in fm.get("locations") or []:
            location_counter[loc] += 1
        rows.append(
            {
                "no": no,
                "id": fm["id"],
                "title": fm.get("title", fm["id"]),
                "aliases": fm.get("aliases") or [],
                "chapters": fm.get("chapters") or [],
                "phase": ph["key"],
                "phaseLabel": ph["label"],
                "summary": fm.get("summary", ""),
                "monsters": ms,
                "locations": fm.get("locations") or [],
                "artifacts": arts,
            }
        )

    rows.sort(key=lambda r: r["no"])

    phase_meta = []
    for ph in PHASES:
        cnt = sum(1 for r in rows if r["phase"] == ph["key"])
        phase_meta.append({**ph, "count": cnt})

    return {
        "book": "西游记",
        "slug": "xiyouji",
        "generated_by": "build_nan.py",
        "total": len(rows),
        "phases": phase_meta,
        "tribulations": rows,
        "stats": {
            "by_camp": dict(camp_counter.most_common()),
            "top_monsters": monster_counter.most_common(12),
            "top_artifacts": artifact_counter.most_common(12),
            "top_locations": location_counter.most_common(12),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    payload = build()
    if args.write:
        out = DATA_DIR / "xiyouji.nan.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  xiyouji nan: {payload['total']} 难")
        for ph in payload["phases"]:
            print(f"    {ph['label']}（难{ph['range'][0]}-{ph['range'][1]}）: {ph['count']}")
        print("  收服者阵营：", payload["stats"]["by_camp"])
        print(f"written → {out.name}")
    else:
        print(json.dumps(payload["stats"]["by_camp"], ensure_ascii=False))


if __name__ == "__main__":
    main()
