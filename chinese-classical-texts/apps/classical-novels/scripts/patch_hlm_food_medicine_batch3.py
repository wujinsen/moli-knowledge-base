#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第三批：刘姥姥席面细目、协理丧宴、灯谜茶果、螃蟹宴佐酒、晴雯补方与嗽疾。"""
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
            "id": "黄杨根套杯",
            "type": "dish",
            "name": "黄杨根套杯",
            "book": BOOK,
            "category": "酒器",
            "eaters": ["刘姥姥", "贾母"],
            "location": "大观园",
            "occasion": "刘姥姥宴",
            "first_appear": "第41回",
            "appear_in": ["第41回"],
            "tags": ["饮食", "刘姥姥", "鸳鸯", "奢侈"],
            "summary": "第41回鸳鸯取黄杨根整抠十个大套杯戏刘姥姥，连饮十杯；与竹根套杯、门杯同场。",
        },
        """## 出处

第41回：刘姥姥怕摔瓷杯，凤姐先命取竹根套杯；鸳鸯改取「黄杨根整抠的十个大套杯」，挨次大小，「定要吃遍一套方使得」。

## 情节功能

- [[刘姥姥两宴饮食链]] 名场面；阶层戏谑与器物精工并置
- 刘姥姥「这要吃我们的家去才使得」式反应，对照 [[茄鲞]]

## 相关

- [[刘姥姥]] · [[鸳鸯]] · [[两宴大观园]] · [[刘姥姥两宴饮食链]] · 第41回
""",
    ),
    (
        "dishes",
        {
            "id": "螃蟹小饺",
            "type": "dish",
            "name": "螃蟹小饺",
            "book": BOOK,
            "category": "点心",
            "eaters": ["贾母", "薛姨妈"],
            "location": "大观园",
            "occasion": "刘姥姥宴",
            "first_appear": "第41回",
            "appear_in": ["第41回"],
            "tags": ["饮食", "蟹", "贾母"],
            "summary": "第41回盒内一寸来大小饺，馅儿是螃蟹；贾母皱眉嫌「油腻腻的，谁吃这个」。",
        },
        """## 出处

第41回：盒内「一寸来大的小饺儿」，婆子回是**螃蟹**馅；贾母皱眉不吃，与 [[奶油小面果]] 同席。

## 情节功能

- 与 [[螃蟹宴]] 同用蟹而 **贾母择食** 写口味与礼数
- 精致点心与刘姥姥见识反差

## 相关

- [[贾母]] · [[螃蟹宴]] · [[两宴大观园]] · 第41回
""",
    ),
    (
        "dishes",
        {
            "id": "奶油小面果",
            "type": "dish",
            "name": "奶油小面果",
            "book": BOOK,
            "category": "点心",
            "eaters": ["刘姥姥", "贾母"],
            "location": "大观园",
            "first_appear": "第41回",
            "appear_in": ["第41回"],
            "tags": ["饮食", "刘姥姥", "点心"],
            "summary": "第41回「奶油炸的各色小面果」，玲珑剔透；刘姥姥拣牡丹花样，贾母亦不喜油腻。",
        },
        """## 出处

第41回：席上「一样是奶油炸的各色**小面果**」，刘姥姥见玲珑剔透，拣了一朵牡丹花样的。

## 相关

- [[刘姥姥]] · [[螃蟹小饺]] · [[两宴大观园]] · 第41回
""",
    ),
    (
        "dishes",
        {
            "id": "奶子糖粳粥",
            "type": "dish",
            "name": "奶子糖粳粥",
            "book": BOOK,
            "category": "粥",
            "eaters": ["王熙凤"],
            "location": "宁国府",
            "occasion": "协理丧仪",
            "first_appear": "第14回",
            "appear_in": ["第14回"],
            "tags": ["饮食", "凤姐", "丧仪"],
            "summary": "第14回凤姐协理可卿丧，五七正日寅正梳洗后「吃了两口奶子糖粳米粥」即赴宁府点卯。",
        },
        """## 出处

第14回：凤姐五七正五日夜歇宁府，寅正平儿请起梳洗，「吃了两口**奶子糖粳米粥**」，卯正二刻至宁府点卯。

## 情节功能

- [[秦可卿丧仪饮食链]] 协理段：凤姐 **勤苦** 与精粥对照
- 与 [[劝食细粥]]（送尤氏贾珍）同回

## 相关

- [[王熙凤]] · [[劝食细粥]] · [[秦可卿丧仪饮食链]] · 第14回
""",
    ),
    (
        "dishes",
        {
            "id": "劝食细粥",
            "type": "dish",
            "name": "劝食细粥",
            "book": BOOK,
            "category": "粥",
            "eaters": ["尤氏", "贾珍"],
            "location": "宁国府",
            "occasion": "协理丧仪",
            "first_appear": "第14回",
            "appear_in": ["第14回"],
            "tags": ["饮食", "凤姐", "丧仪"],
            "summary": "第14回凤姐见尤氏病、贾珍悲哀不大进饮食，每日从荣府煎各样细粥、精致小菜送来劝食。",
        },
        """## 出处

第14回：「因见尤氏犯病，贾珍又过于悲哀，不大进饮食，自己每日从那府中煎了**各样细粥，精致小菜**，命人送来劝食。」

## 情节功能

- 丧仪中 **病食关怀**；凤姐理家细处
- 与 [[供饭供茶]]、[[奶子糖粳粥]] 并读

## 相关

- [[王熙凤]] · [[尤氏]] · [[贾珍]] · [[秦可卿丧仪饮食链]] · 第14回
""",
    ),
    (
        "dishes",
        {
            "id": "香茶细果",
            "type": "dish",
            "name": "香茶细果",
            "book": BOOK,
            "category": "茶点",
            "eaters": ["贾母", "贾政", "薛宝钗", "林黛玉"],
            "location": "贾母上房",
            "occasion": "元宵灯谜",
            "first_appear": "第22回",
            "appear_in": ["第22回"],
            "tags": ["饮食", "元宵", "灯谜"],
            "summary": "第22回宝钗生辰后设围屏灯谜，预备香茶细果及各色玩物为猜着之贺；贾政悲谶语同回。",
        },
        """## 出处

第22回：元春送灯谜，贾母命设围屏灯，「预备下**香茶细果**以及各色玩物，为猜着之贺」；贾政赴宴猜谜。

## 情节功能

- 与 [[宝钗生辰宴]]、[[甜烂之食]] 同回；灯谜 **谶语** 与茶果并置

## 相关

- [[贾母]] · [[贾政]] · [[宝钗生辰宴]] · [[元宵年例链]] · 第22回
""",
    ),
    (
        "dishes",
        {
            "id": "合欢酒",
            "type": "dish",
            "name": "合欢酒",
            "book": BOOK,
            "category": "酒",
            "eaters": ["林黛玉", "薛宝钗"],
            "location": "藕香榭",
            "occasion": "螃蟹宴",
            "first_appear": "第38回",
            "appear_in": ["第38回"],
            "tags": ["饮食", "蟹", "诗社"],
            "summary": "第38回黛玉食蟹后心口微疼，令烫「合欢花浸的酒」；与螃蟹宴、咏菊同场。",
        },
        """## 出处

第38回：黛玉「吃了一点子螃蟹，觉得心口微微的疼，须得热热的喝口烧酒」；宝玉命将**合欢花浸的酒**烫来，黛玉、宝钗各饮一口。

## 情节功能

- [[螃蟹宴]] 佐酒细节；合欢名与 **情喻**（inference）
- 蟹寒用酒温中， plausible_qing

## 相关

- [[林黛玉]] · [[螃蟹宴]] · [[螃蟹宴重阳链]] · 第38回
""",
    ),
    (
        "dishes",
        {
            "id": "普洱茶",
            "type": "tea",
            "name": "普洱茶",
            "book": BOOK,
            "category": "茶",
            "eaters": ["贾宝玉", "袭人", "晴雯"],
            "location": "怡红院",
            "occasion": "群芳夜宴",
            "first_appear": "第63回",
            "appear_in": ["第63回"],
            "tags": ["饮食", "茶", "怡红院"],
            "summary": "第63回林之孝家的查夜，建议沏普洱茶；袭人晴雯已吃面，以女儿茶应对。",
        },
        """## 出处

第63回：宝玉因吃面怕停食多顽，林之孝家的笑说「该沏些个**普洱茶**吃」；袭人晴雯答已沏女儿茶吃过两碗。

## 情节功能

- [[群芳夜宴]] 前后 **消食茶**；管家查夜与夜宴对照
- 与 [[绍兴酒]] 同回

## 相关

- [[贾宝玉]] · [[群芳夜宴]] · [[绍兴酒]] · 第63回
""",
    ),
    (
        "dishes",
        {
            "id": "炖嫩鸡蛋",
            "type": "dish",
            "name": "炖嫩鸡蛋",
            "book": BOOK,
            "category": "膳",
            "eaters": ["司棋"],
            "location": "大观园厨房",
            "first_appear": "第61回",
            "appear_in": ["第61回"],
            "tags": ["饮食", "厨房", "司棋", "鸡蛋"],
            "summary": "第61回司棋要「碗鸡蛋炖的嫩嫩的」；柳家的言鸡蛋短贵、难凑，引发小厨房冲突。",
        },
        """## 出处

第61回：莲花儿传司棋话「要碗**鸡蛋，炖的嫩嫩的**」；柳家的道今年鸡蛋短，「十个钱一个还找不出来」。

## 情节功能

- **小厨房权力** 与 [[露剂与家法链]] 前后；鸡蛋物价信号
- 与 [[玫瑰露]]、[[茯苓霜]] 案同轴

## 相关

- [[司棋]] · [[柳家的]] · [[大观园厨房]] · [[露剂与家法链]] · 第61回
""",
    ),
    (
        "medicines",
        {
            "id": "益神养血之剂",
            "type": "prescription",
            "name": "益神养血之剂",
            "book": BOOK,
            "category": "汤剂",
            "patient": "晴雯",
            "physician": "王太医",
            "first_appear": "第53回",
            "appear_in": ["第53回"],
            "tags": ["方剂", "晴雯", "王太医"],
            "summary": "第53回晴雯补雀裘后虚耗，王太医减疏散驱邪药，添茯苓、地黄、当归等益神养血之剂。",
        },
        """## 出处

第53回：王太医诊晴雯，「已将疏散驱邪诸药减去了，倒添了**茯苓、地黄、当归等益神养血之剂**。」

## 情节功能

- 与 [[王太医诊晴雯]]（第51回和剂）、[[胡庸医诊晴雯]]（虎狼药）形成 **方药递进**
- 补 [[雀金裘]] 后汗后失养

## 相关

- [[晴雯]] · [[王太医]] · [[王太医诊晴雯]] · [[雀金裘]] · 第53回
""",
    ),
    (
        "medicines",
        {
            "id": "虎狼药",
            "type": "medicine",
            "name": "虎狼药",
            "book": BOOK,
            "category": "禁药",
            "patient": "晴雯",
            "physician": "胡庸医",
            "first_appear": "第51回",
            "appear_in": ["第51回"],
            "tags": ["禁药", "枳实", "麻黄", "晴雯"],
            "summary": "第51回胡庸医方中枳实、麻黄等，宝玉斥为「狼虎药」，女孩儿禁不起。",
        },
        """## 出处

第51回：胡庸医方有枳实、麻黄；宝玉道「拿着女孩儿们也象我们一样的治，如何使得」「**枳实、麻黄如何禁得**」，又称「狼虎药」。

## 情节功能

- 与 [[胡庸医诊晴雯]] 同案；**体质—用药** 对照
- 海棠 vs 杨树之喻

## 相关

- [[晴雯]] · [[胡庸医诊晴雯]] · [[王太医诊晴雯]] · [[医药诊脉链]] · 第51回
""",
    ),
    (
        "medicines",
        {
            "id": "黛玉嗽疾",
            "type": "diagnosis",
            "name": "黛玉嗽疾",
            "book": BOOK,
            "category": "证候",
            "patient": "林黛玉",
            "first_appear": "第45回",
            "appear_in": ["第45回", "第55回"],
            "tags": ["嗽疾", "黛玉", "肺弱"],
            "summary": "第45回黛玉每至春分秋分后必犯嗽疾；第55回探春协理时仍嗽，与燕窝供给线并置。",
        },
        """## 出处

- 第45回：「黛玉每岁至春分秋分之后，必犯**嗽疾**……近日又复嗽起来，比往常又重。」
- 第55回：探春协理时「黛玉又犯了嗽疾」

## 情节功能

- 与 [[燕窝粥]]、[[人参养荣丸]] 食养链衔接
- 节令 **反复** 写肺弱体质

## 相关

- [[林黛玉]] · [[燕窝粥]] · [[医药诊脉链]] · 第45回
""",
    ),
    (
        "medicines",
        {
            "id": "李纨时气",
            "type": "diagnosis",
            "name": "李纨时气",
            "book": BOOK,
            "category": "证候",
            "patient": "李纨",
            "first_appear": "第53回",
            "appear_in": ["第53回", "第55回"],
            "tags": ["时气", "李纨", "病养"],
            "summary": "第53回李纨因时气感冒；第55回与邢夫人火眼、黛玉嗽疾等同回，诗社空几社。",
        },
        """## 出处

第53回：「李纨亦因**时气**感冒；邢夫人又正害火眼……」诗社无人作兴。
第55回：园中姊妹病气频仍，与凤姐小月并提。

## 情节功能

- 与 [[净饿调养]]、[[邢夫人火眼]] 写腊月 **病气**
- 诗社暂停的背景

## 相关

- [[李纨]] · [[邢夫人火眼]] · [[净饿调养]] · 第53回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    14: ["奶子糖粳粥", "劝食细粥"],
    22: ["香茶细果"],
    38: ["合欢酒"],
    41: ["黄杨根套杯", "螃蟹小饺", "奶油小面果"],
    45: ["黛玉嗽疾"],
    51: ["虎狼药"],
    53: ["益神养血之剂", "李纨时气"],
    55: ["黛玉嗽疾"],
    61: ["炖嫩鸡蛋"],
    63: ["普洱茶"],
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
    print(f"[{BOOK}] patch food/medicine batch3 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
