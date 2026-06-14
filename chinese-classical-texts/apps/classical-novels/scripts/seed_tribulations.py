#!/usr/bin/env python3
"""从第99回「圣僧历难簿」生成 81 条 event 实体（含第81难：通天河湿经）。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "content" / "events" / "西游记"

# 难目 ↔ 主要回目（可逐步对勘修订）
CHAPTERS: dict[int, list[int]] = {
    1: [1],
    2: [1],
    3: [1],
    4: [1],
    5: [13],
    6: [13],
    7: [13],
    8: [14],
    9: [15],
    10: [16],
    11: [17],
    12: [19],
    13: [20],
    14: [21],
    15: [22],
    16: [22, 23],
    17: [23],
    18: [24, 25],
    19: [25, 26],
    20: [27],
    21: [28],
    22: [29, 30],
    23: [30, 31],
    24: [32],
    25: [33, 34],
    26: [36, 37],
    27: [37],
    28: [40, 41],
    29: [41],
    30: [41, 42],
    31: [42],
    32: [43],
    33: [44, 45],
    34: [45, 46],
    35: [46],
    36: [47],
    37: [47, 48],
    38: [49],
    39: [50, 51],
    40: [51, 52],
    41: [52, 53],
    42: [53],
    43: [54],
    44: [55],
    45: [56, 57],
    46: [57, 58],
    47: [59],
    48: [59, 60],
    49: [61],
    50: [62, 63],
    51: [63],
    52: [64],
    53: [65, 66],
    54: [66],
    55: [67],
    56: [68, 69],
    57: [69, 70],
    58: [70, 71],
    59: [72],
    60: [73],
    61: [74, 75],
    62: [75, 76],
    63: [76],
    64: [77],
    65: [78, 79],
    66: [79],
    67: [80, 81],
    68: [81],
    69: [81],
    70: [82],
    71: [83],
    72: [84],
    73: [85],
    74: [86],
    75: [87, 88],
    76: [89, 90],
    77: [91, 92],
    78: [93, 94, 95],
    79: [96],
    80: [98],
    81: [99],
}

ALIASES: dict[int, list[str]] = {
    20: ["三打白骨精"],
    17: ["四圣试禅心"],
    48: ["三借芭蕉扇"],
    53: ["小雷音寺"],
    61: ["狮驼岭"],
    69: ["无底洞"],
}

EXTRA: dict[int, dict] = {
    11: {
        "characters": ["唐僧", "孙悟空", "黑熊精", "观音菩萨"],
        "monsters": ["黑熊精"],
        "locations": ["黑风山", "观音院"],
        "summary": "观音院失火，黑熊精盗锦襕袈裟；观音收为守山大神。",
    },
    13: {
        "characters": ["唐僧", "孙悟空", "黄风怪", "灵吉菩萨"],
        "locations": ["黄风岭"],
        "summary": "黄风岭黄风怪三昧神风伤悟空眼，灵吉菩萨降伏。",
    },
    17: {
        "characters": ["唐僧", "孙悟空", "猪八戒", "沙僧"],
        "locations": ["五庄观"],
        "summary": "四圣试禅心；五庄观留宿，为后人参果难埋伏笔。",
    },
    18: {
        "characters": ["唐僧", "孙悟空", "猪八戒", "沙僧", "镇元子", "观音菩萨"],
        "locations": ["五庄观"],
        "summary": "悟空偷人参果、推树；观音甘露救树，镇元与悟空结拜。",
    },
    20: {
        "characters": ["唐僧", "孙悟空", "猪八戒", "沙僧"],
        "monsters": ["白骨精"],
        "locations": ["白虎岭"],
        "summary": "白虎岭三打白骨精，唐僧肉眼凡胎怒贬悟空（贬退心猿）。",
    },
    30: {
        "characters": ["唐僧", "孙悟空", "猪八戒", "沙僧", "红孩儿", "观音菩萨"],
        "locations": ["火云洞"],
        "summary": "红孩儿三昧真火擒唐僧，观音收为善财童子。",
    },
    45: {
        "characters": ["孙悟空", "六耳猕猴", "如来佛祖", "唐僧"],
        "locations": ["灵山"],
        "summary": "真假悟空乱乾坤，如来辨六耳猕猴，悟空打死假身。",
    },
    48: {
        "characters": ["孙悟空", "铁扇公主", "牛魔王", "唐僧", "猪八戒", "沙僧"],
        "locations": ["火焰山"],
        "monsters": [],
        "artifacts": ["芭蕉扇"],
        "summary": "火焰山阻路，悟空三借芭蕉扇，天兵降伏牛魔王。",
    },
    81: {
        "title": "通天河湿经",
        "characters": ["唐僧", "孙悟空", "猪八戒", "沙僧"],
        "locations": ["通天河"],
        "summary": "菩萨令揭谛还生一难；老鼋淬水，经书落水，晒经石上留痕。",
    },
}

# 第99回难簿（80难，逐条列出）
TRIBULATION_TITLES = [
    "金蝉遭贬", "出胎几杀", "满月抛江", "寻亲报冤", "出城逢虎",
    "折从落坑", "双叉岭上", "两界山头", "陡涧换马", "夜被火烧",
    "失却袈裟", "收降八戒", "黄风怪阻", "请求灵吉", "流沙难渡",
    "收得沙僧", "四圣显化", "五庄观中", "难活人参", "贬退心猿",
    "黑松林失散", "宝象国捎书", "金銮殿变虎", "平顶山逢魔", "莲花洞高悬",
    "乌鸡国救主", "被魔化身", "号山逢怪", "风摄圣僧", "心猿遭害",
    "请圣降妖", "黑河沉没", "搬运车迟", "大赌输赢", "祛道兴僧",
    "路逢大水", "身落天河", "鱼篮现身", "山遇怪", "普天神难伏",
    "问佛根源", "吃水遭毒", "西梁国留婚", "琵琶洞受苦", "再贬心猿",
    "难辨猕猴", "路阻火焰山", "求取芭蕉扇", "收缚魔王", "赛城扫塔",
    "取宝救僧", "棘林吟咏", "小雷音遇难", "诸天神遭困", "稀柿同秽阻",
    "朱紫国行医", "拯救疲癃", "降妖取后", "七情迷没", "多目遭伤",
    "路阻狮驼", "怪分三色", "城里遇灾", "请佛收魔", "比丘救子",
    "辨认真邪", "松林救怪", "僧房卧病", "无底洞遭困", "灭法国难行",
    "隐雾山遇魔", "凤仙郡求雨", "失落兵器", "会庆钉钯", "竹节山遭难",
    "玄英洞受苦", "赶捉犀牛", "天竺招婚", "铜台府监禁", "凌云渡脱胎",
]


def parse_canonical(_text: str) -> list[tuple[int, str]]:
    return [(i + 1, t) for i, t in enumerate(TRIBULATION_TITLES)]


def yaml_list(key: str, vals: list) -> str:
    if not vals:
        return f"{key}: []"
    lines = [f"{key}:"] + [f"  - {v}" for v in vals]
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    parsed = parse_canonical("")
    if len(parsed) != 80:
        raise SystemExit(f"expected 80 tribulations, got {len(parsed)}")

    # 第81难（难簿外补计）
    parsed.append((81, EXTRA[81]["title"]))

    for no, title in parsed:
        eid = f"xy-e-{no:03d}"
        extra = EXTRA.get(no, {})
        title = extra.get("title", title)
        summary = extra.get("summary", f"第{no}难：{title}。")
        chapters = CHAPTERS.get(no, [])
        aliases = ALIASES.get(no, [])
        prev_id = f"xy-e-{no - 1:03d}" if no > 1 else None
        next_id = f"xy-e-{no + 1:03d}" if no < 81 else None

        lines = [
            "---",
            f"id: {eid}",
            "type: event",
            "book: 西游记",
            "subtype: tribulation",
            f"tribulation_no: {no}",
            f"title: {title}",
        ]
        if aliases:
            lines.append(yaml_list("aliases", aliases))
        lines.append(yaml_list("chapters", chapters))
        for field in ("locations", "characters", "monsters", "artifacts"):
            lines.append(yaml_list(field, extra.get(field, [])))
        if prev_id:
            lines.append(f"prev: {prev_id}")
        if next_id:
            lines.append(f"next: {next_id}")
        lines += [
            "tags: [八十一难]",
            f'summary: "{summary}"',
            "source: chapters/西游记/099.md",
            "---",
            "",
            f"## 第{no}难 · {title}",
            "",
            summary,
            "",
            "出处：第九十九回「九九数完魔灭尽」历难簿；回目锚点待持续对勘。",
        ]
        (OUT / f"{eid}.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {len(parsed)} events to {OUT}")


if __name__ == "__main__":
    main()
