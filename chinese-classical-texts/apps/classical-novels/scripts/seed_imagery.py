#!/usr/bin/env python3
"""生成红楼梦诗词意象实体（判词 / 诗词 / 象征 / 花签）及互文推论边 JSON。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "content" / "imagery" / "红楼梦"
LINKS_OUT = ROOT / "src" / "data" / "红楼梦.imagery-links.json"

# 正册十二钗判词（第五回），节选核心句
JUDGMENTS = [
    ("hl-j-01", "林黛玉判词", 5, "林黛玉",
     "可叹停机德，堪怜咏絮才。玉带林中挂，金簪雪里埋。",
     "咏絮才、玉带林暗示黛玉才名与姓名；与宝钗判合成钗黛对照。"),
    ("hl-j-02", "薛宝钗判词", 5, "薛宝钗",
     "空对着，山中高士晶莹雪；终不忘，世外仙姝寂寞林。",
     "晶莹雪、金簪雪里埋诸说；与黛玉判词互文，金玉木石之谶。"),
    ("hl-j-03", "贾元春判词", 5, "贾元春",
     "二十年来辨是非，榴花深处照宫闱。三春争及初春景，虎兕相逢大梦归。",
     "宫闱、虎兕相逢预示元春薨逝与家族盛极而衰。"),
    ("hl-j-04", "贾探春判词", 5, "贾探春",
     "才自精明志自高，生于末世运偏消。清明涕送江边望，千里东风一梦遥。",
     "远嫁海疆/和番，清明涕送为经典诠释。"),
    ("hl-j-05", "史湘云判词", 5, "史湘云",
     "富贵又何为，襁褓之间父母违。展眼吊斜晖，湘江水逝楚云飞。",
     "楚云飞、水逝与湘云名、命运漂泊相合。"),
    ("hl-j-06", "妙玉判词", 5, "妙玉",
     "欲洁何曾洁，云空未必空。可怜金玉地，终陷污泥中。",
     "洁癖与终被污，栊翠庵与败局互照。"),
    ("hl-j-07", "贾迎春判词", 5, "贾迎春",
     "子系中山狼，得志便猖狂。金闺花柳质，一载赴黄粱。",
     "中山狼指孙绍祖，一载赴黄粱言短命。"),
    ("hl-j-08", "贾惜春判词", 5, "贾惜春",
     "勘破三春景不长，缁衣顿改昔年装。可怜绣户侯门女，独卧青灯古佛旁。",
     "出家为尼，三春景不长扣三春姊妹。"),
    ("hl-j-09", "王熙凤判词", 5, "王熙凤",
     "凡鸟偏从末世来，都知爱慕此生才。一从二令三人木，哭向金陵事更哀。",
     "凡鸟合「凤」字；一从二令三人木拆「休」字谶。"),
    ("hl-j-10", "巧姐判词", 5, "巧姐",
     "势败休云尊贵，家亡莫论亲疏。幸有贤妻，留得余生，巧傍贵人。",
     "刘姥姥相救，败落后得安。"),
    ("hl-j-11", "李纨判词", 5, "李纨",
     "偶因济刘氏，巧得苟安食。春光忽已尽，命薄偏不遇。",
     "稻香村、课子守寡，与贾兰成器对照。"),
    ("hl-j-12", "秦可卿判词", 5, "秦可卿",
     "情天情海幻情身，情既相逢必主淫。漫言不肖皆荣出，造衅开端实在宁。",
     "太虚幻境警幻，宁府败局之始。"),
    ("hl-j-13", "晴雯判词", 5, "晴雯",
     "霁月难逢，彩云易散。心比天高，身为下贱。风流灵巧招人怨，寿夭多因毁谤生。",
     "副册；与芙蓉、撕扇、夭逝互文。"),
    ("hl-j-14", "香菱判词", 5, "香菱",
     "根并荷花一体香，平生遭际实堪伤。自从两地生孤木，致使香魂返故乡。",
     "副册；甄英莲身世，荷花意象。"),
]

POEMS = [
    ("hl-p-01", "葬花吟", 27, "林黛玉",
     "花谢花飞飞满天，红消香断有谁怜？……",
     "黛玉葬花核心诗章，以花自喻，泪尽前身。"),
    ("hl-p-02", "好了歌", 1, None,
     "世人都晓神仙好，惟有功名忘不了！……",
     "跛道人唱，盛衰无常总纲。"),
    ("hl-p-03", "枉凝眉", 5, None,
     "一个是阆苑仙葩，一个是美玉无瑕。……",
     "《红楼梦曲》第三支，宝黛「木石前盟」。"),
    ("hl-p-04", "螃蟹咏", 38, "贾宝玉",
     "持螯更喜桂阴凉，泼醋擂姜兴欲狂。……",
     "诗社讽喻，暗写贾府败象（后文续貂争议）。"),
]

SYMBOLS = [
    ("hl-s-furong", "芙蓉", [], None, "晴雯撕扇、花签、葬花互文的枢纽意象。"),
    ("hl-s-zhu", "竹", [17], "林黛玉", "潇湘馆竹、黛玉气节与愁绪。"),
    ("hl-s-yu", "玉", [3], "贾宝玉", "通灵宝玉、金玉木石之「玉」。"),
    ("hl-s-jin", "金", [3], "薛宝钗", "金锁、金玉良缘之「金」。"),
    ("hl-s-bing", "冰", [5], "薛宝钗", "冷香、晶莹雪与宝钗性情。"),
    ("hl-s-meihua", "梅花", [50], "李纨", "稻香村、李纨寡居清寒。"),
]

FLOWER_LOTS = [
    ("hl-f-01", "芙蓉花签", 63, "林黛玉", "莫怨东风当自嗟", "占得芙蓉，预示黛玉孤高夭逝。"),
    ("hl-f-02", "牡丹花签", 63, "薛宝钗", "任是无情也动人", "占得牡丹，与宝钗富贵冷艳相应。"),
    ("hl-f-03", "梅花花签", 63, "李纨", "竹篱茅舍自甘心", "占得梅花，合稻香村。"),
    ("hl-f-04", "杏花花签", 63, "贾探春", "日边红杏倚云栽", "占得杏花，暗合远嫁。"),
]

# 跨实体互文推论边（inference 边集中于此 JSON）
EXTRA_LINKS = [
    {"source": "晴雯", "target": "林黛玉", "predicate": "影射", "inference": True,
     "note": "晴为黛影；撕扇、补裘、性情与黛玉镜像", "chapter": 31},
    {"source": "hl-s-furong", "target": "晴雯", "predicate": "象征", "inference": True,
     "note": "晴雯撕扇、死后芙蓉女儿诔", "chapter": 78},
    {"source": "hl-s-furong", "target": "林黛玉", "predicate": "隐喻", "inference": True,
     "note": "芙蓉花签、葬花、泪尽", "chapter": 63},
    {"source": "hl-f-01", "target": "林黛玉", "predicate": "预示", "inference": True,
     "note": "莫怨东风当自嗟", "chapter": 63},
    {"source": "hl-s-zhu", "target": "林黛玉", "predicate": "象征", "inference": True,
     "note": "潇湘馆、湘妃竹", "chapter": 17},
    {"source": "hl-s-yu", "target": "贾宝玉", "predicate": "象征", "inference": False,
     "note": "通灵玉", "chapter": 3},
    {"source": "hl-s-jin", "target": "薛宝钗", "predicate": "象征", "inference": False,
     "note": "金锁、冷香丸", "chapter": 3},
    {"source": "hl-p-01", "target": "林黛玉", "predicate": "作", "inference": False,
     "note": "葬花吟", "chapter": 27},
    {"source": "hl-p-03", "target": "贾宝玉", "predicate": "预示", "inference": True,
     "note": "阆苑仙葩/美玉无瑕", "chapter": 5},
    {"source": "hl-p-03", "target": "林黛玉", "predicate": "预示", "inference": True,
     "note": "阆苑仙葩", "chapter": 5},
    {"source": "hl-j-01", "target": "hl-j-02", "predicate": "互文", "inference": True,
     "note": "钗黛合判对照", "chapter": 5},
    {"source": "hl-s-bing", "target": "hl-s-jin", "predicate": "互文", "inference": True,
     "note": "冷香/晶莹雪与金锁", "chapter": 5},
]


def yaml_list(key: str, vals: list) -> str:
    if not vals:
        return f"{key}: []"
    return f"{key}:\n" + "\n".join(f"  - {v}" for v in vals)


def link_block(target: str, predicate: str, inference: bool, chapter: int | None, note: str,
               target_kind: str = "character") -> list[str]:
    lines = [
        "  - target: " + target,
        f"    target_kind: {target_kind}",
        f"    predicate: {predicate}",
        f"    inference: {'true' if inference else 'false'}",
    ]
    if chapter is not None:
        lines.append(f"    chapter: {chapter}")
    if note:
        lines.append(f'    note: "{note}"')
    return lines


def write_judgment(item: tuple) -> None:
    eid, title, ch, char, text, summary = item
    links = []
    if char:
        links.extend(link_block(char, "对应判词", False, ch, summary[:40]))
        links.extend(link_block(char, "预示", True, ch, "判词谶语"))
    body = [
        "---",
        f"id: {eid}",
        "type: imagery",
        "book: 红楼梦",
        "subtype: judgment",
        f"title: {title}",
        f"text: \"{text}\"",
        yaml_list("chapters", [ch]),
        yaml_list("characters", [char] if char else []),
        "links:",
        *links,
        "tags: [判词, 金陵十二钗]",
        f'summary: "{summary}"',
        "source: chapters/红楼梦/005.md",
        "---",
        "",
        f"## {title}",
        "",
        text,
        "",
        summary,
    ]
    (OUT / f"{eid}.md").write_text("\n".join(body), encoding="utf-8")


def write_poem(item: tuple) -> None:
    eid, title, ch, char, text, summary = item
    links = []
    if char:
        links.extend(link_block(char, "作", False, ch, title))
    body = [
        "---",
        f"id: {eid}",
        "type: imagery",
        "book: 红楼梦",
        "subtype: poem",
        f"title: {title}",
        f"text: \"{text}\"",
        yaml_list("chapters", [ch]),
        yaml_list("characters", [char] if char else []),
        yaml_list("links", []) if not links else "links:\n" + "\n".join(links),
        "tags: [诗词]",
        f'summary: "{summary}"',
        f"source: chapters/红楼梦/{ch:03d}.md",
        "---",
        "",
        f"## {title}",
        "",
        text,
        "",
        summary,
    ]
    (OUT / f"{eid}.md").write_text("\n".join(body), encoding="utf-8")


def write_symbol(item: tuple) -> None:
    eid, title, chapters, char, summary = item
    links = []
    if char:
        ch = chapters[0] if chapters else None
        links.extend(link_block(char, "象征", True, ch, summary[:40]))
    body = [
        "---",
        f"id: {eid}",
        "type: imagery",
        "book: 红楼梦",
        "subtype: symbol",
        f"title: {title}",
        yaml_list("chapters", chapters),
        yaml_list("characters", [char] if char else []),
        yaml_list("links", []) if not links else "links:\n" + "\n".join(links),
        "tags: [象征物]",
        f'summary: "{summary}"',
        "---",
        "",
        f"## 象征 · {title}",
        "",
        summary,
    ]
    (OUT / f"{eid}.md").write_text("\n".join(body), encoding="utf-8")


def write_flower_lot(item: tuple) -> None:
    eid, title, ch, char, lot_text, summary = item
    links = link_block(char, "隐喻", True, ch, lot_text)
    body = [
        "---",
        f"id: {eid}",
        "type: imagery",
        "book: 红楼梦",
        "subtype: flower_lot",
        f"title: {title}",
        f"text: \"{lot_text}\"",
        yaml_list("chapters", [ch]),
        yaml_list("characters", [char]),
        "links:",
        *links,
        "tags: [花签, 酒令]",
        f'summary: "{summary}"',
        "source: chapters/红楼梦/063.md",
        "---",
        "",
        f"## {title} · {char}",
        "",
        f"签文：{lot_text}",
        "",
        summary,
    ]
    (OUT / f"{eid}.md").write_text("\n".join(body), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for j in JUDGMENTS:
        write_judgment(j)
    for p in POEMS:
        write_poem(p)
    for s in SYMBOLS:
        write_symbol(s)
    for f in FLOWER_LOTS:
        write_flower_lot(f)

    payload = {"book": "红楼梦", "links": EXTRA_LINKS}
    LINKS_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    n = len(JUDGMENTS) + len(POEMS) + len(SYMBOLS) + len(FLOWER_LOTS)
    print(f"Wrote {n} imagery entities to {OUT}")
    print(f"Wrote {len(EXTRA_LINKS)} extra links to {LINKS_OUT}")


if __name__ == "__main__":
    main()
