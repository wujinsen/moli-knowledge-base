#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第二批：宝钗生辰、刘姥姥席面余项、群芳夜宴子项、丧仪供食、凤姐小月与尤二姐脉案。"""
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
            "id": "宝钗生辰宴",
            "type": "banquet",
            "name": "宝钗生辰宴",
            "book": BOOK,
            "category": "寿宴",
            "eaters": ["薛宝钗", "贾母", "史湘云", "贾宝玉", "林黛玉"],
            "location": "贾母上房",
            "occasion": "将笄之年",
            "first_appear": "第22回",
            "appear_in": ["第22回"],
            "tags": ["饮食", "宝钗", "贾母", "寿宴"],
            "summary": "第22回贾母蠲资二十两置酒戏，贾母内院搭戏台、排家宴酒席；宝钗点《鲁智深醉闹五台山》，与甜烂之食、灯谜谶语同回。",
        },
        """## 出处

第22回：薛宝钗十五岁将笄之年，贾母自蠲二十两交凤姐置酒戏；二十一日在贾母内院搭家常小巧戏台，排几席**家宴酒席**，并无外客。

## 情节功能

- 贾母特为宝钗作生日，与黛玉待遇对照（inference）
- 宝钗答贾母所好 [[甜烂之食]]；席后贾政悲谶语、宝玉悟禅机
- 与 [[群芳夜宴]]、后期简素寿席（第108回 inference）可纵切

## 相关

- [[薛宝钗]] · [[贾母]] · [[甜烂之食]] · [[元宵年例链]] · 第22回
""",
    ),
    (
        "dishes",
        {
            "id": "什锦攒心盒子",
            "type": "dish",
            "name": "什锦攒心盒子",
            "book": BOOK,
            "category": "席面器皿",
            "eaters": ["贾母", "刘姥姥", "薛宝钗", "林黛玉"],
            "location": "大观园",
            "occasion": "两宴大观园",
            "first_appear": "第40回",
            "appear_in": ["第40回", "第41回"],
            "tags": ["饮食", "刘姥姥", "贾母"],
            "summary": "第40回宝玉提议还席：每人跟前高几，爱吃的一两样，再一个什锦攒心盒子、自斟壶；贾母称「很是」。",
        },
        """## 出处

第40回：宝玉为史湘云还席献议——「每人跟前摆一张高几……再一个**什锦攒心盒子**，自斟壶，岂不别致。」贾母命厨房照办。

## 情节功能

- 与 [[两宴大观园]]、[[鸽子蛋]] 物价、[[茄鲞]] 同链
- 写贾府席面 **随意精致** 与刘姥姥见闻反差

## 相关

- [[贾宝玉]] · [[贾母]] · [[刘姥姥]] · [[两宴大观园]] · [[刘姥姥两宴饮食链]] · 第40回
""",
    ),
    (
        "dishes",
        {
            "id": "绍兴酒",
            "type": "dish",
            "name": "绍兴酒",
            "book": BOOK,
            "category": "酒",
            "eaters": ["贾宝玉", "晴雯", "袭人", "麝月"],
            "location": "怡红院",
            "occasion": "宝玉生日前夜",
            "first_appear": "第63回",
            "appear_in": ["第63回"],
            "tags": ["饮食", "群芳夜宴", "酒"],
            "summary": "第63回袭人等与柳嫂子备四十碟果子，平儿处抬一坛好绍兴酒藏怡红院边，供群芳夜宴。",
        },
        """## 出处

第63回：袭人等对宝玉说，银子已交柳嫂子预备 [[四十碟果子]]，「已经抬了一坛好**绍兴酒**藏在那边了」。

## 情节功能

- [[群芳夜宴]] 具体用酒；与同日贾敬服丹 **明暗对照**
- 丫鬟凑份子置酒，写怡红院 **女儿自治** 的短暂青春

## 相关

- [[群芳夜宴]] · [[四十碟果子]] · [[贾宝玉]] · [[晴雯]] · 第63回
""",
    ),
    (
        "dishes",
        {
            "id": "四十碟果子",
            "type": "dish",
            "name": "四十碟果子",
            "book": BOOK,
            "category": "果点",
            "eaters": ["贾宝玉", "晴雯", "袭人", "芳官"],
            "location": "怡红院",
            "occasion": "宝玉生日前夜",
            "first_appear": "第63回",
            "appear_in": ["第63回"],
            "tags": ["饮食", "群芳夜宴", "果点"],
            "summary": "第63回怡红院八丫鬟凑银交柳嫂子，预备四十碟果子，与绍兴酒同备群芳夜宴。",
        },
        """## 出处

第63回：袭人、晴雯等八人凑银「早已交给了柳嫂子，预备**四十碟果子**」。

## 相关

- [[群芳夜宴]] · [[绍兴酒]] · [[大观园厨房]] · 第63回
""",
    ),
    (
        "dishes",
        {
            "id": "供饭供茶",
            "type": "dish",
            "name": "供饭供茶",
            "book": BOOK,
            "category": "丧仪供食",
            "eaters": [],
            "location": "宁国府",
            "occasion": "秦可卿丧仪",
            "first_appear": "第14回",
            "appear_in": ["第14回"],
            "tags": ["饮食", "丧仪", "可卿", "凤姐"],
            "summary": "第14回凤姐协理宁府，分派四十人灵前守灵、供饭供茶；内茶房、酒饭器皿分责连坐。",
        },
        """## 出处

第14回凤姐点卯分派：「四十个人……单在灵前上香添油，挂幔守灵，**供饭供茶**，随起举哀」；又分茶房杯碟、酒饭器皿专责。

## 情节功能

- [[秦可卿丧仪饮食链]] 核心工序；病食（张方）与丧食排场对照
- 凤姐 **理家首秀**：时辰、连坐、描赔

## 相关

- [[秦可卿]] · [[王熙凤]] · [[秦可卿丧仪]] · [[秦可卿丧仪饮食链]] · 第14回
""",
    ),
    (
        "dishes",
        {
            "id": "奠茶饭",
            "type": "dish",
            "name": "奠茶饭",
            "book": BOOK,
            "category": "丧仪供食",
            "eaters": [],
            "location": "铁槛寺",
            "occasion": "可卿发殡",
            "first_appear": "第15回",
            "appear_in": ["第15回"],
            "tags": ["饮食", "丧仪", "路祭"],
            "summary": "第15回可卿殡至铁槛寺，和尚工课已完，奠过茶饭；与路祭祭棚、北静王祭并置。",
        },
        """## 出处

第15回：发殡至铁槛寺，「当下和尚工课已完，**奠过茶饭**」，贾珍命贾蓉请凤姐歇息。

## 情节功能

- [[秦可卿丧仪饮食链]] 发殡段；僧道水陆与 **奠茶饭** 写丧仪食礼
- 同回路祭、祭棚、凤姐弄权之引

## 相关

- [[秦可卿]] · [[铁槛寺]] · [[北静王]] · [[秦可卿丧仪饮食链]] · 第15回
""",
    ),
    (
        "dishes",
        {
            "id": "面茶",
            "type": "dish",
            "name": "面茶",
            "book": BOOK,
            "category": "晨食",
            "eaters": ["贾政", "贾环"],
            "location": "贾政上房",
            "occasion": "晨仪",
            "first_appear": "第77回",
            "appear_in": ["第77回"],
            "tags": ["饮食", "贾政", "家常"],
            "summary": "第77回王夫人催贾环速往上房，「老爷在上屋里还等他吃面茶呢」；写贾政晨间家礼。",
        },
        """## 出处

第77回：王夫人遣人催贾环往上房，道「老爷在上屋里还等他吃**面茶**呢。环哥儿已来了。」

## 情节功能

- **家常晨食**与后文抄检、晴雯被逐同回并置
- 贾政严父形象的一端（与宝玉避读对照）

## 相关

- [[贾政]] · [[贾环]] · [[王夫人]] · 第77回
""",
    ),
    (
        "medicines",
        {
            "id": "凤姐小月脉案",
            "type": "diagnosis",
            "name": "凤姐小月脉案",
            "book": BOOK,
            "category": "诊脉",
            "patient": "王熙凤",
            "first_appear": "第55回",
            "appear_in": ["第55回", "第77回"],
            "tags": ["诊脉", "凤姐", "小月"],
            "summary": "第55回元宵后凤姐小月，在家一月不能理事，天天两三个太医用药；禀赋气血不足、争强斗智致亏虚。",
        },
        """## 出处

第55回：「凤姐儿便**小月**了，在家一月，不能理事，**天天两三个太医用药**。」又云凤姐「禀赋气血不足，兼年幼不知保养，平生争强斗智，心力更亏，故虽系小月，竟着实亏虚下来。」

## 情节功能

- 凤姐 **失势** 起点：王夫人令李纨、探春协理，后请宝钗
- 与第77回 [[调经养荣丸]]、[[上等人参]] 前后呼应

## 相关

- [[王熙凤]] · [[下红之症]] · [[调经养荣丸]] · [[医药诊脉链]] · 第55回
""",
    ),
    (
        "medicines",
        {
            "id": "下红之症",
            "type": "diagnosis",
            "name": "下红之症",
            "book": BOOK,
            "category": "证候",
            "patient": "王熙凤",
            "first_appear": "第55回",
            "appear_in": ["第55回", "第77回"],
            "tags": ["证候", "凤姐", "小月"],
            "summary": "第55回凤姐小月亏虚后复添下红之症，不肯明言；众人见其面目黄瘦，王夫人命服药调养。",
        },
        """## 出处

第55回：小月后「一月之后，复添了**下红之症**。他虽不肯说出来，众人看他面目黄瘦，便知失于调养。王夫人只令他好生服药调养。」至八九月间方渐渐起复。

## 情节功能

- 妇科 **隐疾** 写法；凤姐好强讳病
- 与 [[凤姐小月脉案]]、[[调经养荣丸]] 同轴

## 相关

- [[王熙凤]] · [[凤姐小月脉案]] · [[王夫人]] · 第55回
""",
    ),
    (
        "medicines",
        {
            "id": "邢夫人火眼",
            "type": "diagnosis",
            "name": "邢夫人火眼",
            "book": BOOK,
            "category": "眼科",
            "patient": "邢夫人",
            "first_appear": "第53回",
            "appear_in": ["第53回"],
            "tags": ["火眼", "邢夫人", "侍药"],
            "summary": "第53回腊月诗社空几社，因李纨时气感冒、邢夫人正害火眼，迎春岫烟皆过去朝夕侍药。",
        },
        """## 出处

第53回：「李纨亦因时气感冒；**邢夫人又正害火眼**，迎春岫烟皆过去朝夕侍药。」

## 情节功能

- 与 [[净饿调养]]、晴雯未大愈等同回，写园中 **病气频仍**
- 脂批「妙在一人不落，事事皆到」

## 相关

- [[邢夫人]] · [[贾迎春]] · [[邢岫烟]] · [[净饿调养]] · 第53回
""",
    ),
    (
        "medicines",
        {
            "id": "尤二姐吞金",
            "type": "medicine",
            "name": "尤二姐吞金",
            "book": BOOK,
            "category": "自尽",
            "patient": "尤二姐",
            "first_appear": "第69回",
            "appear_in": ["第69回"],
            "tags": ["吞金", "尤二姐", "凤姐"],
            "summary": "第69回尤二姐受凤姐、秋桐凌虐，闻「生金子可以坠死」，取生金吞入口中自尽。",
        },
        """## 出处

第69回：尤二姐「常听见人说，**生金子可以坠死**，岂不比上吊自刎又干净。」遂「找出一块生金……便**吞入口中**」。

## 情节功能

- [[王熙凤]] 「借剑杀人」结局；与 [[胡君荣诊尤二姐]] 误治并读
- 吞金为明清笔记常见自尽方式（plausible_qing）

## 相关

- [[尤二姐]] · [[王熙凤]] · [[秋桐]] · [[胡君荣诊尤二姐]] · 第69回
""",
    ),
    (
        "medicines",
        {
            "id": "胡君荣诊尤二姐",
            "type": "diagnosis",
            "name": "胡君荣诊尤二姐",
            "book": BOOK,
            "category": "诊脉",
            "patient": "尤二姐",
            "physician": "胡君荣",
            "first_appear": "第69回",
            "appear_in": ["第69回"],
            "tags": ["诊脉", "尤二姐", "庸医"],
            "summary": "第69回王太医谋干军前，小厮另请胡太医君荣；诊为经水不调大补，贾琏言三月庚信不行疑胎气，胡君荣仍按不调治。",
        },
        """## 出处

第69回：「王太医亦谋干了军前效力……便请了个姓胡的太医，名叫**君荣**。进来诊脉看了，说是**经水不调，全要大补**。」贾琏道「已是三月庚信不行，又常作呕酸，恐是胎气」，胡君荣仍按经水不调开方。

## 情节功能

- 与 [[胡庸医诊晴雯]] 同属 **庸医误人** 线；误治加速尤二姐悲剧
- 王太医缺席（谋干）写太医 **趋利** 一面

## 相关

- [[尤二姐]] · [[贾琏]] · [[王太医]] · [[尤二姐吞金]] · [[医药诊脉链]] · 第69回
""",
    ),
    (
        "medicines",
        {
            "id": "参膏芦须",
            "type": "medicine",
            "name": "参膏芦须",
            "book": BOOK,
            "category": "药材",
            "patient": "王熙凤",
            "first_appear": "第77回",
            "appear_in": ["第77回"],
            "tags": ["药材", "人参", "凤姐"],
            "summary": "第77回配调经养荣丸寻参，凤姐称只有参膏芦须与几枝非上好人参，每日煎药里用。",
        },
        """## 出处

第77回：王夫人问凤姐有无人参，凤姐说「也只有些**参膏芦须**。虽有几枝，也不是上好的，每日还要煎药里用呢。」

## 情节功能

- 与 [[上等人参]] 告罄、贾母陈腐参 **同轴** 写物资枯竭
- 参膏、芦须（参须）为次等参品，仍不敷配丸之需

## 相关

- [[王熙凤]] · [[调经养荣丸]] · [[上等人参]] · [[王夫人]] · 第77回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    14: ["供饭供茶"],
    15: ["奠茶饭"],
    22: ["宝钗生辰宴"],
    40: ["什锦攒心盒子"],
    53: ["邢夫人火眼"],
    55: ["凤姐小月脉案", "下红之症"],
    63: ["绍兴酒", "四十碟果子"],
    69: ["尤二姐吞金", "胡君荣诊尤二姐"],
    77: ["参膏芦须", "面茶"],
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
    print(f"[{BOOK}] patch food/medicine batch2 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
