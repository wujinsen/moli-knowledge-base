#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第九批：后段神签许愿、夏金桂毒案、桂圆复生、刘姥姥还愿托巧姐、书房酒局、食疗与袭人脉案。"""
from __future__ import annotations

import re

import yaml

from _common import CHAPTER_DIR, CONTENT
from lint_modules import list_known_item_ids
from tag_chapter_meta import find_ids, format_list, load_item_pairs, parse_list_field, split_body, strip_html

BOOK = "红楼梦"

NEW_ITEMS: list[tuple[str, dict, str]] = [
    (
        "medicines",
        {
            "id": "定心丸",
            "type": "medicine",
            "name": "定心丸",
            "book": BOOK,
            "category": "丸剂",
            "patient": "贾宝玉",
            "first_appear": "第100回",
            "appear_in": ["第100回"],
            "tags": ["医药", "丸剂", "宝玉", "宝钗"],
            "summary": "第100回探春远嫁在即，宝玉心闹慌，宝钗暗叫袭人快给定心丸并慢慢开导。",
        },
        """## 出处

第100回：宝玉强说「心里闹的慌」——「宝钗也不理他，暗叫袭人快把**定心丸**给他吃了，慢慢的开导他。」

## 情节功能

- 探春 **远嫁** 与宝玉 **失恃** 并轴；宝钗持重 **医心**
- 与 [[疏气安神丸]]（抄家惊吓）、[[毕知庵诊宝玉]] 后段 **神伤** 线

## 相关

- [[贾宝玉]] · [[薛宝钗]] · [[袭人]] · [[贾探春]] · 第100回
""",
    ),
    (
        "dishes",
        {
            "id": "散花寺神签",
            "type": "custom",
            "name": "散花寺神签",
            "book": BOOK,
            "category": "求签",
            "eaters": [],
            "location": "散花寺",
            "first_appear": "第101回",
            "appear_in": ["第101回"],
            "tags": ["饮食", "求签", "凤姐", "异兆"],
            "summary": "第101回凤姐至散花寺求签，得第三十三签「上上大吉」，签文「王熙凤衣锦还乡」，惊异兆。",
        },
        """## 出处

第101回：大了查签簿——「第三十三签，上上大吉」；签上写着「**王熙凤衣锦还乡**」。凤姐吃一大惊。

## 情节功能

- 月夜感幽魂、秦可卿 **托梦** 余波；凤姐 **盛筵必散** 预谶
- 与 [[水陆道场许愿]] 同回 **民俗疗惧**

## 相关

- [[王熙凤]] · [[秦可卿]] · [[水陆道场许愿]] · 第101回
""",
    ),
    (
        "dishes",
        {
            "id": "水陆道场许愿",
            "type": "custom",
            "name": "水陆道场许愿",
            "book": BOOK,
            "category": "佛事",
            "eaters": [],
            "location": "散花寺",
            "occasion": "许愿",
            "first_appear": "第101回",
            "appear_in": ["第101回"],
            "tags": ["饮食", "佛事", "凤姐", "丧仪"],
            "summary": "第101回大了言凤姐要在散花菩萨前许愿烧香，做四十九天水陆道场，保佑家口、亡者升天。",
        },
        """## 出处

第101回：大了云——「要在散花菩萨跟前许愿烧香，做**四十九天的水陆道场**，保佑家口安宁，亡者升天，生者获福。」

## 情节功能

- 凤姐素恶 **迷信**，见鬼后方 **三分信意**
- 与 [[散花寺神签]]、[[刘姥姥求神]] 并读 **后段民俗**

## 相关

- [[王熙凤]] · [[散花寺神签]] · [[刘姥姥求神]] · 第101回
""",
    ),
    (
        "medicines",
        {
            "id": "夏金桂毒汤案",
            "type": "medicine",
            "name": "夏金桂毒汤案",
            "book": BOOK,
            "category": "毒案",
            "patient": "夏金桂",
            "first_appear": "第103回",
            "appear_in": ["第103回"],
            "tags": ["医药", "毒案", "夏金桂", "香菱", "宝蟾"],
            "summary": "第103回宝蟾做两碗汤，金桂服毒暴死；宝蟾供词、刑部相验，香菱释疑。",
        },
        """## 出处

第103回：「又叫**宝蟾去做了两碗汤**来，自己说同香菱一块儿喝」——金桂「鼻子眼睛里都流出血来……我瞧那光景是**服了毒**的。」宝钗云：「这汤是宝蟾做的，就该捆起宝蟾来问他。」

## 情节功能

- **施毒自焚** 回目；与 [[金桂案砒霜]]、[[虎狼药]] 并轴
- 香菱 **释疑**；薛家 **经官** 撕掳

## 相关

- [[夏金桂]] · [[香菱]] · [[宝蟾]] · [[金桂案砒霜]] · [[薛宝钗]] · 第103回
""",
    ),
    (
        "medicines",
        {
            "id": "金桂案砒霜",
            "type": "medicine",
            "name": "金桂案砒霜",
            "book": BOOK,
            "category": "毒药",
            "patient": "夏金桂",
            "first_appear": "第103回",
            "appear_in": ["第103回"],
            "tags": ["医药", "毒药", "夏金桂"],
            "summary": "第103回金桂暴死，薛姨妈言「这样子是砒霜药的」；宝蟾供词涉夏家儿子买砒霜。",
        },
        """## 出处

第103回：「这样子是**砒霜药**的，家里决无此物。」宝蟾又云：「问准了夏家的儿子买砒霜的话。」

## 情节功能

- [[夏金桂毒汤案]] **物证** 层；天理昭彰 **自害其身**（宝蟾供词）
- 与 [[虎狼药]]（赵姨娘线）对照 **府中毒物**

## 相关

- [[夏金桂毒汤案]] · [[夏金桂]] · [[宝蟾]] · 第103回
""",
    ),
    (
        "dishes",
        {
            "id": "桂圆汤",
            "type": "dish",
            "name": "桂圆汤",
            "book": BOOK,
            "category": "汤",
            "eaters": ["贾宝玉", "麝月"],
            "location": "荣国府",
            "first_appear": "第6回",
            "appear_in": ["第6回", "第116回"],
            "tags": ["饮食", "汤", "复生"],
            "summary": "第6回宝玉梦醒端上桂圆汤；第116回宝玉还魂后王夫人叫人端桂圆汤给麝月，定神复生。",
        },
        """## 出处

- 第6回：「众人忙端上**桂圆汤**来，呷了两口，遂起身整衣。」（梦醒）
- 第116回：「王夫人叫人端了**桂圆汤**叫他喝了几口，渐渐的定了神。」（麝月；宝玉魂魄复还）

## 情节功能

- **梦醒—还魂** 对称；与 [[净饿调养]]、[[益神养血之剂]] 后段 **调养** 并读

## 相关

- [[贾宝玉]] · [[麝月]] · [[净饿调养]] · 第6回 · 第116回
""",
    ),
    (
        "medicines",
        {
            "id": "刘姥姥还愿",
            "type": "medicine",
            "name": "刘姥姥还愿",
            "book": BOOK,
            "category": "病养",
            "patient": "王熙凤",
            "first_appear": "第113回",
            "appear_in": ["第113回"],
            "tags": ["医药", "还愿", "刘姥姥"],
            "summary": "第113回刘姥姥辞行，言姑奶奶好了再请还愿；接续求神许愿线。",
        },
        """## 出处

第113回：「明儿姑奶奶好了，**再请还愿**去。」

## 情节功能

- [[刘姥姥求神]] **后续**；村妪 **许诺—还愿** 闭环
- 与 [[巧姐托姥姥]] 同回 **托孤** 前奏

## 相关

- [[刘姥姥求神]] · [[刘姥姥]] · [[王熙凤]] · 第113回
""",
    ),
    (
        "dishes",
        {
            "id": "巧姐托姥姥",
            "type": "custom",
            "name": "巧姐托姥姥",
            "book": BOOK,
            "category": "托孤",
            "eaters": [],
            "location": "荣国府",
            "first_appear": "第113回",
            "appear_in": ["第113回"],
            "tags": ["饮食", "托孤", "巧姐", "刘姥姥"],
            "summary": "第113回凤姐病笃，将命与巧姐交刘姥姥：「我的命交给你了，巧姐儿也是千灾百病的，也交给你了。」",
        },
        """## 出处

第113回：「姥姥，**我的命交给你了。我的巧姐儿也是千灾百病的，也交给你了。**」

## 情节功能

- **托孤** 名场面；后接 [[刘姥姥还愿]]、第119–120回 **藏庄** 线（人物页互链）
- 与 [[刘姥姥求神]] 村妪 **恩情** 并置

## 相关

- [[巧姐]] · [[刘姥姥]] · [[王熙凤]] · [[刘姥姥求神]] · 第113回
""",
    ),
    (
        "dishes",
        {
            "id": "贾芸书房酒局",
            "type": "custom",
            "name": "贾芸书房酒局",
            "book": BOOK,
            "category": "酒局",
            "eaters": ["贾芸", "贾蔷", "邢大舅", "王仁"],
            "location": "外书房",
            "first_appear": "第117回",
            "appear_in": ["第117回"],
            "tags": ["饮食", "酒局", "末世", "聚赌"],
            "summary": "第117回贾芸贾蔷住外书房，邢大舅王仁借照看之名设局赌钱喝酒，荣府后段崩坏侧写。",
        },
        """## 出处

第117回：「邢大舅王仁……瞧见了贾芸贾蔷住在这里，知他热闹，也就借着照看的名儿时常在外书房**设局赌钱喝酒**。」又云陪酒、行「月字流觞」酒令。

## 情节功能

- **承家** 名义下的 **宿娼滥赌**；与 [[抄家席间]]、[[贾母丧仪供饭]] 末世轴
- 贾芸 **堕落** 对照前卷 [[红玉]] 手帕线

## 相关

- [[贾芸]] · [[贾蔷]] · [[邢大舅]] · [[王仁]] · 第117回
""",
    ),
    (
        "dishes",
        {
            "id": "食疗",
            "type": "dish",
            "name": "食疗",
            "book": BOOK,
            "category": "食养",
            "eaters": ["贾母"],
            "first_appear": "第22回",
            "appear_in": ["第22回"],
            "tags": ["饮食", "食养", "贾母", "inference"],
            "summary": "与第22回宝钗所答贾母所好及软烂菜、甜烂之食互参，为贾母长寿食养链之 inference 名物（见医药饮食名录）。",
        },
        """## 出处

- **互参**：第22回 [[甜烂之食]]；[[软烂菜]] 页与 [[医药饮食名录]] 贾母项「软烂菜、**食疗**」（inference）
- **制度背景**：第53回 [[净饿调养]] 贾府「一略伤风咳嗽，总以净饿为主，次则服药调养」

## 情节功能

- 与 [[软烂菜]]、[[甜烂之食]]、[[八旬寿点]] 构成 **贾母口腹** 纵切
- 食养 vs 药疗：对照 [[疏气安神丸]]、[[贾母参汤]]

## 相关

- [[软烂菜]] · [[甜烂之食]] · [[贾母]] · [[医药饮食名录]] · 第22回
""",
    ),
    (
        "dishes",
        {
            "id": "宝玉复生粥",
            "type": "dish",
            "name": "宝玉复生粥",
            "book": BOOK,
            "category": "粥",
            "eaters": ["贾宝玉"],
            "location": "荣国府",
            "first_appear": "第115回",
            "appear_in": ["第115回"],
            "tags": ["饮食", "粥", "宝玉", "复生"],
            "summary": "第115回宝玉失言后见贾政，嚷饿喝了一碗粥，又要饭，神气渐复，与后段还魂线衔接。",
        },
        """## 出处

第115回：「宝玉便嚷饿了，**喝了一碗粥**，还说要饭……便爬着吃了一碗，渐渐的神气果然好过来了。」

## 情节功能

- **失魂—复气** 日常食；与第116回 [[桂圆汤]] **还魂** 并轴
- 王夫人尚 **不敢给饭** → 渐信其愈

## 相关

- [[贾宝玉]] · [[桂圆汤]] · [[贾政]] · 第115回 · 第116回
""",
    ),
    (
        "medicines",
        {
            "id": "袭人急怒脉案",
            "type": "medicine",
            "name": "袭人急怒脉案",
            "book": BOOK,
            "category": "诊脉",
            "patient": "袭人",
            "first_appear": "第120回",
            "appear_in": ["第120回"],
            "tags": ["医药", "急怒", "袭人", "宝玉"],
            "summary": "第120回袭人因闻宝玉若不回来便要打发屋里人出去，急怒气厥；大夫诊为急怒所致。",
        },
        """## 出处

第120回：「大夫看了脉，说是**急怒所致**，开了方子去了。原来袭人模糊听见说宝玉若不回来，便要打发屋里的人都出去，一急越发不好了。」

## 情节功能

- 宝玉 **悟道出家** 后袭人 **去留** 两难；与 [[定心丸]]（宝玉侧）对照 **妾命**
- 终局 **蒋玉菡** 归宿之 **前奏**

## 相关

- [[袭人]] · [[贾宝玉]] · [[薛宝钗]] · 第120回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    6: ["桂圆汤"],
    22: ["食疗"],
    100: ["定心丸"],
    101: ["散花寺神签", "水陆道场许愿"],
    98: ["桂圆汤"],
    103: ["夏金桂毒汤案", "金桂案砒霜"],
    113: ["刘姥姥还愿", "巧姐托姥姥"],
    115: ["宝玉复生粥"],
    116: ["桂圆汤"],
    117: ["贾芸书房酒局"],
    120: ["袭人急怒脉案"],
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
            cur_items = parse_list_field(raw, "items") or []
            cur = set(cur_items)
            body = strip_html(split_body(raw))
            found = set(find_ids(body, pairs, {})) & known
            found |= set(CHAPTER_ITEMS_ADD.get(ch, []))
            merged = sorted(cur | found)
            if merged == sorted(cur):
                continue
            new_fm = format_list("items", merged)
            if re.search(r"^items:\s*\[", raw, re.M):
                raw = re.sub(r"^items:\s*\[[^\]]*\]", new_fm.strip(), raw, count=1, flags=re.M)
            elif re.search(r"^items:\s*\n", raw, re.M):
                raw = re.sub(
                    r"^items:\s*\n(?:  - .+\n)+",
                    new_fm,
                    raw,
                    count=1,
                    flags=re.M,
                )
            else:
                raw = re.sub(r"(^summary:.*\n)", rf"\1{new_fm}\n", raw, count=1, flags=re.M)
            if parse_list_field(raw, "items") != merged:
                print(f"  WARN merge verify failed ch{ch} {p.name}")
            p.write_text(raw, encoding="utf-8")
            label = "脂砚斋本" if "脂砚斋本" in str(p) else "程高本"
            print(f"  {label} 第{ch}回 +{len(merged) - len(cur)} → {len(merged)}")
            n += 1
    return n


def main() -> None:
    print(f"[{BOOK}] patch food/medicine batch9 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
