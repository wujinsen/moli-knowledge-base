#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第四批：路祭茶果、蟹宴姜醋、建莲汤、元春赐器、鲍太医与后段丸药。"""
from __future__ import annotations

import re

import yaml

from _common import CHAPTER_DIR, CONTENT
from lint_modules import list_known_item_ids
from tag_chapter_meta import find_ids, format_list, load_item_pairs, parse_list_field, split_body, strip_html

BOOK = "红楼梦"

NEW_ITEMS: list[tuple[str, dict, str]] = [
    (
        "dishes",
        {
            "id": "路祭茶果",
            "type": "dish",
            "name": "路祭茶果",
            "book": BOOK,
            "category": "丧仪茶点",
            "eaters": ["王熙凤", "贾宝玉", "秦钟"],
            "location": "水月庵",
            "occasion": "可卿发殡",
            "first_appear": "第15回",
            "appear_in": ["第15回"],
            "tags": ["饮食", "丧仪", "可卿"],
            "summary": "第15回可卿殡至铁槛寺途中，水月庵智善摆茶碟，请凤姐、宝玉、秦钟吃茶果点心；与奠茶饭、路祭祭棚同链。",
        },
        """## 出处

第15回：殡至水月庵，「智善来叫智能去摆茶碟子，一时来请他两个去吃**茶果点心**。」

## 情节功能

- [[秦可卿丧仪饮食链]] 发殡段；僧庵 **茶点** 与 [[奠茶饭]] 并置
- 同回馒头庵、凤姐弄权之引

## 相关

- [[秦可卿]] · [[王熙凤]] · [[奠茶饭]] · [[秦可卿丧仪饮食链]] · 第15回
""",
    ),
    (
        "dishes",
        {
            "id": "姜醋蘸蟹",
            "type": "dish",
            "name": "姜醋蘸蟹",
            "book": BOOK,
            "category": "蘸料",
            "eaters": ["贾母", "王熙凤", "平儿", "史湘云"],
            "location": "藕香榭",
            "occasion": "螃蟹宴",
            "first_appear": "第38回",
            "appear_in": ["第38回"],
            "tags": ["饮食", "蟹", "螃蟹宴"],
            "summary": "第38回藕香榭螃蟹宴，凤姐剥蟹「多倒些姜醋」；与烫酒、绿豆洗面同场。",
        },
        """## 出处

第38回：螃蟹宴上平儿剔蟹黄送凤姐，凤姐道「**多倒些姜醋**」；贾母怕蟹积冷，凤姐以笑话劝多食。

## 情节功能

- [[螃蟹宴]] 食蟹 **礼法与细节**；蟹寒用姜醋温中（plausible_qing）
- 与 [[合欢酒]]、[[绿豆洗面]] 同回

## 相关

- [[螃蟹宴]] · [[合欢酒]] · [[螃蟹宴重阳链]] · 第38回
""",
    ),
    (
        "dishes",
        {
            "id": "绿豆洗面",
            "type": "dish",
            "name": "绿豆洗面",
            "book": BOOK,
            "category": "盥洗",
            "eaters": ["贾母", "史湘云", "薛宝钗"],
            "location": "藕香榭",
            "occasion": "螃蟹宴",
            "first_appear": "第38回",
            "appear_in": ["第38回"],
            "tags": ["饮食", "蟹", "盥洗"],
            "summary": "第38回食蟹后，丫头取菊花叶儿桂花蕊熏的绿豆面子预备洗手；藕香榭螃蟹宴细目。",
        },
        """## 出处

第38回：「又命小丫头们去取**菊花叶儿桂花蕊熏的绿豆面子**来，预备洗手。」

## 情节功能

- [[螃蟹宴]] **阶层与精致**；食蟹后盥洗礼
- 与 [[姜醋蘸蟹]] 同链

## 相关

- [[螃蟹宴]] · [[姜醋蘸蟹]] · 第38回
""",
    ),
    (
        "dishes",
        {
            "id": "建莲红枣汤",
            "type": "dish",
            "name": "建莲红枣汤",
            "book": BOOK,
            "category": "汤",
            "eaters": ["贾宝玉"],
            "location": "怡红院",
            "first_appear": "第52回",
            "appear_in": ["第52回"],
            "tags": ["饮食", "汤", "宝玉"],
            "summary": "第52回宝玉出门前，小丫头捧盖碗建莲红枣儿汤，宝玉喝了两口；又噙法制紫姜一块。",
        },
        """## 出处

第52回：宝玉「即时换了衣裳。小丫头便用小茶盘捧了一盖碗**建莲红枣儿汤**来，宝玉喝了两口。」

## 情节功能

- 日常 **晨起汤饮**；同回贾母论凤姐、晴雯病
- 与 [[法制紫姜]] 并提

## 相关

- [[贾宝玉]] · [[法制紫姜]] · 第52回
""",
    ),
    (
        "dishes",
        {
            "id": "宫制诗筒",
            "type": "dish",
            "name": "宫制诗筒",
            "book": BOOK,
            "category": "赐器",
            "eaters": [],
            "location": "贾母上房",
            "occasion": "元宵灯谜",
            "first_appear": "第22回",
            "appear_in": ["第22回"],
            "tags": ["饮食", "元春", "灯谜", "赐物"],
            "summary": "第22回元春灯谜赐物：猜中者各得宫制诗筒一、茶筅一；贾环、迎春未得。",
        },
        """## 出处

第22回：「太监又将颁赐之物送与猜着之人，每人一个**宫制诗筒**，一柄茶筅，独迎春、贾环二人未得。」

## 情节功能

- 与 [[香茶细果]]、[[宝钗生辰宴]] 灯谜同回
- 链 [[元春赐物链]]

## 相关

- [[贾元春]] · [[茶筅]] · [[香茶细果]] · [[元春赐物链]] · 第22回
""",
    ),
    (
        "dishes",
        {
            "id": "茶筅",
            "type": "tea",
            "name": "茶筅",
            "book": BOOK,
            "category": "茶具",
            "eaters": [],
            "location": "藕香榭",
            "first_appear": "第22回",
            "appear_in": ["第22回", "第38回"],
            "tags": ["饮食", "茶", "元春", "螃蟹宴"],
            "summary": "第22回元春赐茶筅；第38回藕香榭竹案设茶筅茶盂，丫头煽风炉煮茶。",
        },
        """## 出处

- 第22回：元春灯谜赐 **茶筅**（同 [[宫制诗筒]]）
- 第38回：藕香榭「一个上头设着**茶筅**茶盂各色茶具」

## 相关

- [[宫制诗筒]] · [[螃蟹宴]] · [[栊翠庵品茶链]] · 第38回
""",
    ),
    (
        "dishes",
        {
            "id": "门杯",
            "type": "dish",
            "name": "门杯",
            "book": BOOK,
            "category": "酒令",
            "eaters": ["贾宝玉", "冯紫英", "薛蟠", "蒋玉菡"],
            "location": "冯紫英家",
            "occasion": "冯紫英寿宴",
            "first_appear": "第28回",
            "appear_in": ["第28回"],
            "tags": ["饮食", "酒令", "宝玉"],
            "summary": "第28回冯紫英家酒令：说毕女儿四字原故，「饮门杯」；宝玉、蒋玉菡等依次行令。",
        },
        """## 出处

第28回：宝玉立令「说完了，**饮门杯**。酒面要唱一个新鲜时样曲子……」冯紫英、云儿、薛蟠、蒋玉菡次第行令。

## 情节功能

- 同回 **茜香罗** 换汗巾；女儿酒令与《红豆词》
- 宴饮 **雅俗对照**（薛蟠哼哼韵）

## 相关

- [[贾宝玉]] · [[蒋玉菡]] · [[冯紫英]] · 第28回
""",
    ),
    (
        "dishes",
        {
            "id": "法制紫姜",
            "type": "dish",
            "name": "法制紫姜",
            "book": BOOK,
            "category": "小食",
            "eaters": ["贾宝玉"],
            "location": "怡红院",
            "first_appear": "第52回",
            "appear_in": ["第52回"],
            "tags": ["饮食", "姜", "宝玉"],
            "summary": "第52回宝玉出门前，麝月捧一小碟法制紫姜，宝玉噙了一块；同建莲红枣汤。",
        },
        """## 出处

第52回：「麝月又捧过一小碟**法制紫姜**来，宝玉噙了一块。」

## 情节功能

- 与 [[建莲红枣汤]] 写宝玉 **晨起饮食**
- 紫姜制法则 plausible_qing

## 相关

- [[贾宝玉]] · [[建莲红枣汤]] · 第52回
""",
    ),
    (
        "medicines",
        {
            "id": "鲍太医诊黛玉",
            "type": "diagnosis",
            "name": "鲍太医诊黛玉",
            "book": BOOK,
            "category": "诊脉",
            "patient": "林黛玉",
            "physician": "鲍太医",
            "first_appear": "第28回",
            "appear_in": ["第28回"],
            "tags": ["诊脉", "黛玉", "鲍太医"],
            "summary": "第28回王夫人问黛玉吃鲍太医的药可好些；黛玉言「不过这么着」，仍吃王大夫的药。",
        },
        """## 出处

第28回：王夫人问「大姑娘，你吃那**鲍太医**的药可好些？」黛玉道「也不过这么着。老太太还叫我吃**王大夫**的药呢。」

## 情节功能

- **多医并治** 写黛玉弱症；与 [[黛玉嗽疾]]、[[人参养荣丸]] 同轴
- 宝玉论内症、丸药 vs 煎药

## 相关

- [[林黛玉]] · [[王太医诊晴雯]] · [[黛玉嗽疾]] · [[医药诊脉链]] · 第28回
""",
    ),
    (
        "medicines",
        {
            "id": "天王补心丹",
            "type": "prescription",
            "name": "天王补心丹",
            "book": BOOK,
            "category": "丸",
            "patient": "林黛玉",
            "first_appear": "第28回",
            "appear_in": ["第28回"],
            "tags": ["方剂", "黛玉", "王夫人"],
            "summary": "第28回王夫人记大夫所开丸药名，误说「金刚」；宝钗笑指是天王补心丹，宝玉戏言金刚丸菩萨散。",
        },
        """## 出处

第28回：王夫人问丸药名，宝玉猜人参养荣丸等皆不是；王夫人只记得有「**金刚**」二字。宝钗抿嘴：「想是**天王补心丹**。」

## 情节功能

- **谐趣**中写黛玉常服丸药；与 [[人参养荣丸]] 并提
- 后文黛玉药养线（inference）

## 相关

- [[林黛玉]] · [[薛宝钗]] · [[人参养荣丸]] · 第28回
""",
    ),
    (
        "medicines",
        {
            "id": "疏气安神丸",
            "type": "prescription",
            "name": "疏气安神丸",
            "book": BOOK,
            "category": "丸",
            "patient": "贾母",
            "first_appear": "第106回",
            "appear_in": ["第106回"],
            "tags": ["方剂", "贾母", "抄家"],
            "summary": "第106回贾母因抄家惊吓气逆，王夫人等唤醒后「用疏气安神的丸药服了，渐渐的好些」。",
        },
        """## 出处

第106回：「见贾母惊吓气逆……即用**疏气安神的丸药**服了，渐渐的好些。」

## 情节功能

- **败落信号** 与贾政赦宥、家产查抄同回
- 后段贾母 **受惊调治** 线

## 相关

- [[贾母]] · [[王夫人]] · 第106回
""",
    ),
    (
        "dishes",
        {
            "id": "八旬寿点",
            "type": "dish",
            "name": "八旬寿点",
            "book": BOOK,
            "category": "寿宴点心",
            "eaters": ["尤氏", "贾母"],
            "location": "大观园",
            "occasion": "贾母八旬",
            "first_appear": "第71回",
            "appear_in": ["第71回"],
            "tags": ["饮食", "贾母八旬", "寿宴"],
            "summary": "第71回八旬寿期，平儿请尤氏「这里有点心，且点补一点儿」；七日分席筵宴中茶点不断。",
        },
        """## 出处

第71回：尤氏欲往园中，平儿笑道「奶奶请回来。这里**有点心**，且点补一点儿，回来再吃饭。」同回议定七月二十八至八月初五荣宁齐开筵。

## 情节功能

- [[贾母八旬宴]] / [[贾母八旬宴链]] 细目；排场犹盛而嫌隙已生
- 与 [[金寿星]] 等元春寿礼对照

## 相关

- [[贾母]] · [[尤氏]] · [[贾母八旬宴]] · [[贾母八旬宴链]] · 第71回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    15: ["路祭茶果"],
    22: ["宫制诗筒", "茶筅"],
    28: ["门杯", "鲍太医诊黛玉", "天王补心丹"],
    38: ["姜醋蘸蟹", "绿豆洗面", "茶筅"],
    52: ["建莲红枣汤", "法制紫姜"],
    71: ["八旬寿点"],
    106: ["疏气安神丸"],
}


def write_item(kind: str, fm: dict, body: str) -> bool:
    iid = fm["id"]
    path = CONTENT / kind / BOOK / f"{iid}.md"
    if path.exists():
        return False
    text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{text}---\n{body}", encoding="utf-8")
    print(f"  + {kind}/{iid}.md")
    return True


def merge_chapter_items() -> int:
    pairs = load_item_pairs(BOOK)
    known = list_known_item_ids(BOOK)
    n = 0
    bases = [
        CHAPTER_DIR / BOOK,
        CHAPTER_DIR / BOOK / "脂砚斋本",
    ]
    for base in bases:
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if base == CHAPTER_DIR / BOOK and p.parent != base:
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
            label = "脂砚斋本" if "脂砚斋本" in str(p) else "程高本"
            print(f"  {label} 第{ch}回 +{len(merged) - len(cur)} → {len(merged)}")
            n += 1
    return n


def main() -> None:
    print(f"[{BOOK}] patch food/medicine batch4 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
