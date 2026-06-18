#!/usr/bin/env python3
"""金瓶梅 roster 审阅：建真实缺页 · 扩充 known · 重建 roster（无 discover 噪声）。

用法: python scripts/triage_jpm_roster.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parent
BOOK = "金瓶梅"

# discover 误抽片段，永久忽略
DISMISS = frozenset(
    {
        "他女儿", "我罢了", "叫甚么", "了小人", "奴罢了", "全家老小", "大虫的",
        "一龙戏二", "了皂隶李", "了这个大", "了这个猛", "了那大虫", "人是大事",
        "做三寸丁", "做勉铃", "做吴应元", "做桃花洞", "做爱姐", "做衣梅", "做郑观音",
        "做金莲", "做陶扒灰", "儿叫玉楼", "叫做爱姐", "叫做郑观", "叫做金莲",
        "大虫的武", "才是好汉", "汉子才好", "爹爹跟前", "的老虎", "罗万象那",
        "者多埋在", "金弹打银", "雪里送炭", "两个公人", "怀胎母羊", "山中虎",
        "西门氏",  # 称谓非独立人物
    }
)


def location_ids() -> set[str]:
    ids: set[str] = set()
    d = CONTENT / "locations" / BOOK
    for p in d.glob("*.md"):
        fm, _ = parse_frontmatter(p)
        iid = fm.get("id") or p.stem
        ids.add(iid)
        for a in fm.get("aliases") or []:
            ids.add(a)
    return ids


def write_location(path: Path, fm: dict, body: str) -> None:
    if path.exists():
        return
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for x in v:
                lines.append(f"  - {x}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append(body)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  + location {fm['id']}")


def write_character(path: Path, fm: dict, body: str) -> None:
    if path.exists():
        return
    import yaml

    text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{text}---\n{body}\n", encoding="utf-8")
    print(f"  + character {fm['id']}")


def seed_locations() -> None:
    loc_dir = CONTENT / "locations" / BOOK
    write_location(
        loc_dir / "卧云亭.md",
        {
            "id": "卧云亭",
            "type": "building",
            "name": "卧云亭",
            "book": BOOK,
            "category": "亭",
            "parent": "花园",
            "first_appear": "第27回",
            "appear_in": ["第27回", "第52回", "第96回"],
            "summary": "花园假山顶棋亭；第27回春梅在此，潘金莲醉闹葡萄架近旁。",
        },
        "## 出处\n\n第27回：春梅在 **卧云亭** 搭伏棋桌，西门庆与潘金莲葡萄架事在其下。\n",
    )
    write_location(
        loc_dir / "谢家酒楼.md",
        {
            "id": "谢家酒楼",
            "type": "building",
            "name": "谢家酒楼",
            "book": BOOK,
            "category": "酒楼",
            "parent": "临清",
            "first_appear": "第93回",
            "appear_in": ["第93回", "第94回"],
            "summary": "临清第一座酒楼，百十阁儿临官河；陈敬济与冯金宝于此勾搭（第93–94回）。",
        },
        "## 出处\n\n第93回：临清 **谢家酒楼**，陈敬济见冯金宝；第94回续有往来。\n",
    )
    write_location(
        loc_dir / "永福禅林.md",
        {
            "id": "永福禅林",
            "type": "temple",
            "name": "永福禅林",
            "book": BOOK,
            "category": "禅林",
            "parent": "清河县",
            "first_appear": "第89回",
            "appear_in": ["第89回"],
            "summary": "周秀香火院；吴月娘祭扫遇周小奶奶，僧道坚接待（第89回）。",
        },
        "## 出处\n\n第89回：[[吴月娘]] 随 [[吴大舅]] 至 **永福禅林** 随喜，遇周府小奶奶祭祀。\n",
    )
    write_location(
        loc_dir / "雪涧洞.md",
        {
            "id": "雪涧洞",
            "type": "realm",
            "name": "雪涧洞",
            "aliases": ["雪洞"],
            "book": BOOK,
            "category": "洞府",
            "first_appear": "第84回",
            "appear_in": ["第84回"],
            "summary": "岱岳东峰石洞，雪洞禅师普静修行；吴月娘进香归途遇险得救（第84回）。",
        },
        "## 出处\n\n第84回：[[吴月娘]] 一行迷途，遇 **雪涧洞** 普静禅师指路回清河县。\n",
    )


def seed_characters() -> None:
    char_dir = CONTENT / "characters" / BOOK
    write_character(
        char_dir / "徐崶.md",
        {
            "id": "徐崶",
            "type": "character",
            "name": "徐崶",
            "book": BOOK,
            "faction": "严州府",
            "first_appear": "第92回",
            "status": "配角",
            "summary": "严州府知府，庚戌进士，清廉刚正；审陈敬济盗库案留疑停刑（第92回）。",
            "weight": 12,
        },
        "## 关键情节\n\n- 第92回：闻陈敬济骂「孟三儿陷我」，停板收监，明日再审。\n",
    )


def save_dismissed() -> None:
    p = DATA_DIR / "jinpingmei.roster_dismissed.json"
    payload = {
        "book": BOOK,
        "updated": date.today().isoformat(),
        "dismissed": sorted(DISMISS),
        "note": "discover 误抽片段/称谓，不参与 pending",
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    print("[金瓶梅] roster triage …")
    seed_locations()
    seed_characters()
    save_dismissed()

    # 重建 roster（仅 seed，不用 discover）
    subprocess.run(
        [sys.executable, str(ROOT / "build_character_roster.py"), BOOK],
        cwd=ROOT.parent,
        check=True,
    )

    roster = json.loads((DATA_DIR / "jinpingmei.character_roster.json").read_text(encoding="utf-8"))
    still = [p["name"] for p in roster.get("pending", []) if p["name"] not in DISMISS]
    print(f"  pending after triage: {roster.get('pending_count')} (real seed gaps: {len(still)})")
    for n in still[:12]:
        print(f"    · {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
