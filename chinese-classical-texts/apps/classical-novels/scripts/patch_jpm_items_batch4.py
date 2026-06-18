#!/usr/bin/env python3
"""金瓶梅名物 ingest 第四批：政商盐引/官服员领 + 宴饮猜枚 + 零覆盖诊脉补链。"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from _common import CHAPTER_DIR, CONTENT
from lint_modules import list_known_item_ids
from tag_chapter_meta import find_ids, format_list, load_item_pairs, parse_list_field, split_body, strip_html

BOOK = "金瓶梅"

NEW_ITEMS: list[tuple[str, dict, str]] = [
    (
        "customs",
        {
            "id": "盐引",
            "type": "institution",
            "name": "盐引",
            "book": BOOK,
            "participants": ["西门庆", "来保", "崔本", "蔡御史", "乔大户"],
            "procedure": ["旧派淮盐仓钞", "户部坐派", "巡盐早掣"],
            "location": "新河口 / 扬州",
            "economic": "乔亲家高阳关旧仓钞三万引",
            "first_appear": "第48回",
            "appear_in": ["第48回", "第49回"],
            "tags": ["政商", "盐政", "放债链"],
            "summary": "西门庆借乔亲家旧仓钞派三万盐引，蔡御史许早掣（第49回）；政商链与南货扩张交汇。",
        },
        """## 出处

- 第48回：来保抄邸报，韩爷开引种盐例，旧仓钞派三万盐引。
- 第49回：揭帖列「商人来保、崔本，旧派淮盐三万引，乞到日早掣」，蔡御史许早掣一个月。

## 情节功能

- **政商贿赂轨**与 **南货扩张** 衔接：盐引特权换巡按庇护
- 与 [[蔡御史]]、[[来保]]、[[崔本]]、[[白银]] 互证

## 相关

- [[西门庆]] · [[乔大户]] · [药铺与放债链](/jinpingmei/topics/药铺与放债链) · 第48–49回
""",
    ),
    (
        "customs",
        {
            "id": "揭帖",
            "type": "institution",
            "name": "揭帖",
            "book": BOOK,
            "holders": ["来保", "崔本", "陈敬济"],
            "procedure": ["盐引申领", "官场呈递", "回帖答谢"],
            "first_appear": "第49回",
            "appear_in": ["第49回", "第70回"],
            "tags": ["文书", "政商"],
            "summary": "来保、崔本持揭帖请蔡御史早掣盐引（第49回）；赴京谢恩亦以揭帖呈礼（第70回）。",
        },
        """## 出处

第49回：「上面写着：商人来保、崔本，旧派淮盐三万引，乞到日早掣。」蔡御史袖帖，许早放。

## 情节功能

- 官商往来的 **文书接口**，与 [[盐引]]、[[员领]] 馈礼并置

## 相关

- [[来保]] · [[崔本]] · [[盐引]] · 第49回
""",
    ),
    (
        "customs",
        {
            "id": "帅府分资",
            "type": "ritual",
            "name": "帅府分资",
            "book": BOOK,
            "participants": ["周守备", "荆都监", "张团练", "西门庆"],
            "procedure": ["帅府差人送贺礼", "每人五星", "粗帕二方"],
            "location": "西门府",
            "first_appear": "第73回",
            "appear_in": ["第73回"],
            "tags": ["官场", "往来", "分资"],
            "summary": "孟玉楼生日，帅府周爷差人送五封分资（周守备、荆都监、张团练、刘薛二内相各五星），写清河武官与西门府礼法往来（第73回）。",
        },
        """## 出处

第73回：「帅府周爷差人送分资来了。盒内封着五封分资……每人五星，粗帕二方，奉引贺敬。」

## 情节功能

- 与 [[结拜分资]]、[[帮闲凑分]] 对照：官场 **引贺** 型分资
- [[周守备]] 线节点，后文春梅、守备府并读

## 相关

- [[周守备]] · [[孟玉楼]] · [[结拜分资]] · 第73回
""",
    ),
    (
        "customs",
        {
            "id": "猜枚",
            "type": "ritual",
            "name": "猜枚",
            "book": BOOK,
            "participants": ["西门庆", "应伯爵", "韩道国", "来保"],
            "procedure": ["宴饮行令", "行酒令", "弹唱佐酒"],
            "location": "西门府 / 扬州院中",
            "first_appear": "第1回",
            "appear_in": ["第1回", "第81回"],
            "tags": ["宴饮", "帮闲", "酒令"],
            "summary": "结拜酒席与南货线宴饮中的猜枚行令（第1、81回），是 [[宴饮纵酒]] 的具体程式之一。",
        },
        """## 出处

- 第1回：结拜酒席，帮闲凑分、宴饮纵酒。
- 第81回：韩道国扬州院中「行令猜枚，吃至三更方散」。

## 情节功能

- 宴饮 **酒令** 细写，与 [[象牙牌]] 抹牌、[[红牙象板]] 并置

## 相关

- [[宴饮纵酒]] · [[应伯爵]] · [[金华酒]] · 第1回 · 第81回
""",
    ),
    (
        "customs",
        {
            "id": "妆奁",
            "type": "ritual",
            "name": "妆奁",
            "book": BOOK,
            "participants": ["西门庆", "韩爱姐", "冯妈妈"],
            "procedure": ["半副嫁妆", "衣服首饰箱柜", "送东京蔡府"],
            "location": "西门府 / 东京",
            "first_appear": "第37回",
            "appear_in": ["第37回", "第97回"],
            "tags": ["婚嫁", "财礼"],
            "summary": "西门庆为韩爱姐备半副妆奁送翟府（第37回）；后二十回陈敬济言「床帐妆奁都搬的去了」（第97回）。",
        },
        """## 出处

- 第37回：「凡一应衣服首饰、妆奁箱柜等件，都是我这里替他办备。」
- 第97回：陈敬济诉大姐案后「床帐妆奁，都搬的去了」。

## 情节功能

- **临清韩爱姐线** 起点财物；与 [[认干亲礼]] 政商链并置

## 相关

- [[韩爱姐]] · [[冯妈妈]] · [[西门庆]] · [临清韩爱姐线](/jinpingmei/topics/临清韩爱姐线) · 第37回
""",
    ),
    (
        "costumes",
        {
            "id": "员领",
            "type": "costume",
            "name": "员领",
            "book": BOOK,
            "wearers": ["西门庆", "陈敬济", "宋乔年"],
            "material": "绸缎",
            "occasion": "官服补子、年节谢官",
            "rank_signal": "武职捐官、巡按馈礼",
            "description": "大红绒金豸员领、妆花纻丝员领、五彩洒线狮子补子员领等，标志官阶与官场往来",
            "tags": ["服饰", "官场"],
            "summary": "捐官上任穿狮子补子员领（第31回）；谢宋御史、赴京谢恩、陈敬济冠带荣身皆以此为核心礼服（第31、70、78、98回）。",
            "first_appear": "第31回",
            "appear_in": ["第31回", "第70回", "第78回", "第98回"],
        },
        """## 出处

- 第31回：「五彩洒线揉头狮子补子员领，四指大宽萌金茄楠香带。」
- 第78回：谢宋御史「一匹大红绒金豸员领，一匹黑青妆花纻丝员领」。
- 第98回：陈敬济「穿大红员领，头戴冠帽……和新妇葛氏拜见」。

## 情节功能

- **官服等级** 与 [[犀角带]]、[[蟒衣]] 并置，写西门庆捐官与后二十回冠带荣身

## 相关

- [[西门庆]] · [[陈敬济]] · [[果馅金饼]] · [[浙江酒]] · 第31回
""",
    ),
    (
        "costumes",
        {
            "id": "蟒衣",
            "type": "costume",
            "name": "蟒衣",
            "book": BOOK,
            "wearers": ["西门庆", "何太监"],
            "material": "绿绒 / 青绒",
            "occasion": "赴京谢恩、内侍赐服",
            "rank_signal": "武职升迁、恩宠",
            "description": "大红绒彩蟒、青绒妆花斗牛补子员领、飞鱼绿绒氅衣等，区别于妻妾 [[织金莲五彩蟒衣]]",
            "tags": ["服饰", "官场", "恩宠"],
            "summary": "西门庆赴京贺蔡府、何太监赐飞鱼绿绒氅衣（第70–71回）；写武职捐官后的恩宠服饰，与内廷赏赐互文。",
            "first_appear": "第70回",
            "appear_in": ["第70回", "第71回"],
        },
        """## 出处

- 第70回：「一匹大红绒彩蟒、一匹玄色妆花斗牛补子员领」谢翟管家。
- 第71回：何太监「穿着绿绒蟒衣」；赐西门庆「飞鱼绿绒氅衣」。

## 情节功能

- 与 [[员领]]、[[犀角带]] 构成 **赴京谢恩** 礼服组合
- 对照 [[织金莲五彩蟒衣]]（李瓶儿婚嫁，非官服）

## 相关

- [[西门庆]] · [[蔡府寿礼]] · [[员领]] · 第70–71回
""",
    ),
    (
        "costumes",
        {
            "id": "头面",
            "type": "accessory",
            "name": "头面",
            "book": BOOK,
            "holders": ["吴月娘", "李瓶儿", "潘金莲", "孟玉楼", "葛翠屏", "陈敬济"],
            "material": "金珠首饰",
            "occasion": "节令盛装、婚嫁、赏赉",
            "description": "簪环、首饰、打头面，六房年节与后二十回赏赉的核心饰物",
            "tags": ["首饰", "服饰"],
            "summary": "全书高频「头面」指首饰整装；守备赏葛氏「十两银子打头面」（第98回），与 [[簪环]] 并置而更广。",
            "first_appear": "第1回",
            "appear_in": ["第98回"],
        },
        """## 出处

- 第98回：守备「赏了一套衣服、十两银子打头面」予葛翠屏。
- 全书屡言「头面首饰」「打头面」，为婚嫁、节令、赏赉的固定用语。

## 情节功能

- 物质 **等级与恩赏** 的细目，对照 [[白银]]、[[妆奁]]

## 相关

- [[簪环]] · [[葛翠屏]] · [[周守备]] · 第98回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    1: ["猜枚"],
    31: ["员领", "蟒衣"],
    37: ["妆奁"],
    48: ["盐引"],
    49: ["盐引", "揭帖"],
    61: ["任医官诊血崩"],
    62: ["任医官诊血崩"],
    70: ["员领", "蟒衣", "揭帖"],
    71: ["员领", "蟒衣"],
    73: ["帅府分资"],
    78: ["员领"],
    79: ["西门庆脱阳之症"],
    81: ["猜枚"],
    98: ["员领", "头面"],
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
    base = CHAPTER_DIR / BOOK
    for p in sorted(base.rglob("*.md")):
        if "词话本" not in str(p):
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
        print(f"  词话本 第{ch}回 +{len(merged) - len(cur)} → {len(merged)}")
        n += 1
    return n


def main() -> None:
    print(f"[{BOOK}] patch batch4 …")
    created = 0
    for kind, fm, body in NEW_ITEMS:
        if write_item(kind, fm, body):
            created += 1
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
