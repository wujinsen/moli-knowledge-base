#!/usr/bin/env python3
"""生成 honglou.variant-topics.json 与 topics/红楼梦/情节-*.md 承接页。

用法: python scripts/seed_hlm_variant_topics.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from _common import CONTENT, DATA_DIR

BOOK = "红楼梦"
TOPICS_DIR = CONTENT / "topics" / BOOK
OUT_JSON = DATA_DIR / "honglou.variant-topics.json"

TOPICS = [
    {
        "id": "情节-黛玉结局",
        "chapter": 97,
        "summary": "焚稿泪尽（程高）vs 还泪沉湖诸说（脂评·探佚）",
        "characters": ["林黛玉"],
        "title": "黛玉结局",
        "derived_from": ["林黛玉", "第97回", "第98回", "hlm-e-006"],
        "cheng": "第97–98回焚稿断痴情、泪尽而逝",
        "zhi": "判词「玉带林中挂」「冷月葬花魂」——泪尽早夭乃至沉湖诸说",
    },
    {
        "id": "情节-宝黛钗姻缘",
        "chapter": 97,
        "summary": "调包计金玉成姻（程高）vs 木石前盟原构争议",
        "characters": ["林黛玉", "贾宝玉", "薛宝钗"],
        "title": "宝黛钗姻缘",
        "derived_from": ["林黛玉", "贾宝玉", "薛宝钗", "第97回"],
        "cheng": "第97回「调包计」令宝玉娶宝钗",
        "zhi": "〈终身误〉「调包」是否合曹公原意，争议甚大",
    },
    {
        "id": "情节-宝玉出家",
        "chapter": 120,
        "summary": "中举后出家、兰桂齐芳（程高）vs 悬崖撒手、败落沦贫（脂批）",
        "characters": ["贾宝玉"],
        "title": "宝玉出家",
        "derived_from": ["贾宝玉", "第119回", "第120回", "hlm-e-008"],
        "cheng": "第119–120回中乡魁后出家、兰桂齐芳",
        "zhi": "脂批「悬崖撒手」「寒冬噎酸齑，雪夜围破毡」——败落沦贫",
    },
    {
        "id": "情节-宝玉结局",
        "chapter": 120,
        "summary": "程高本出家路径与脂本「悬崖撒手」凄寒意趣的分歧",
        "characters": ["贾宝玉"],
        "title": "宝玉结局",
        "derived_from": ["贾宝玉", "第120回", "hlm-e-008"],
        "cheng": "中举后弃家随僧道而去，贾府家道复初",
        "zhi": "先历贫寒方出家，无「兰桂齐芳」式回暖",
    },
    {
        "id": "情节-湘云结局",
        "chapter": 31,
        "summary": "后四十回早寡 vs 白首双星、卫若兰诸说",
        "characters": ["史湘云", "卫若兰"],
        "title": "湘云结局",
        "derived_from": ["史湘云", "卫若兰", "第31回"],
        "cheng": "后四十回所嫁夫婿病重、归于早寡",
        "zhi": "「因麒麟伏白首双星」、〈乐中悲〉——与卫若兰偕老等说纷纭",
    },
    {
        "id": "情节-香菱之死",
        "chapter": 103,
        "summary": "难产而亡（程高）vs 为夏金桂折磨致死（判词）",
        "characters": ["香菱", "夏金桂"],
        "title": "香菱之死",
        "derived_from": ["香菱", "夏金桂", "第103回", "第120回"],
        "cheng": "第103回金桂误毒自害、香菱扶正、第120回难产亡",
        "zhi": "判词「致使香魂返故乡」——为夏金桂折磨致死",
    },
    {
        "id": "情节-妙玉结局",
        "chapter": 112,
        "summary": "遭劫不知所终（程高）vs 终陷淖泥、流落风尘（曲词）",
        "characters": ["妙玉"],
        "title": "妙玉结局",
        "derived_from": ["妙玉", "第112回"],
        "cheng": "第112回遭强盗劫掠、不知所终",
        "zhi": "「风尘肮脏违心愿」「终陷淖泥中」——流落风尘",
    },
    {
        "id": "情节-巧姐结局",
        "chapter": 118,
        "summary": "刘姥姥救出议嫁板儿（程高）vs 卖入烟花细节争议",
        "characters": ["巧姐"],
        "title": "巧姐结局",
        "derived_from": ["巧姐", "刘姥姥", "第118回", "第119回"],
        "cheng": "第118–119回遭狠舅奸兄欲卖，刘姥姥救出、议嫁板儿",
        "zhi": "〈留余庆〉细节是否真被卖入烟花，与续书有出入",
    },
    {
        "id": "情节-秦可卿之死",
        "chapter": 13,
        "summary": "病亡（通行本）vs 淫丧天香楼（脂批原稿）",
        "characters": ["秦可卿"],
        "title": "秦可卿之死",
        "derived_from": ["秦可卿", "第13回"],
        "cheng": "第13回因病亡故、丧仪极盛",
        "zhi": "脂批「淫丧天香楼」原稿、命芹溪删去「遗簪」「更衣」",
    },
    {
        "id": "情节-元春之死",
        "chapter": 95,
        "summary": "痰气壅塞病逝（程高）vs 虎兕相逢、宫廷政争（判词）",
        "characters": ["贾元春"],
        "title": "元春之死",
        "derived_from": ["贾元春", "第95回"],
        "cheng": "第95回发福、痰气壅塞病逝",
        "zhi": "「虎兕相逢大梦归」、〈恨无常〉——牵涉宫廷政争",
    },
    {
        "id": "情节-凤姐结局",
        "chapter": 114,
        "summary": "病亡托孤（程高）vs 狱神庙、休弃惨死（脂批探佚）",
        "characters": ["王熙凤"],
        "title": "凤姐结局",
        "derived_from": ["王熙凤", "第114回"],
        "cheng": "第114回失势成疾、病亡，托刘姥姥照看巧姐",
        "zhi": "判词「一从二令三人木」、〈聪明累〉、脂批「狱神庙」等，多解为休弃/获罪惨死",
    },
    {
        "id": "情节-探春结局",
        "chapter": 119,
        "summary": "远嫁归省（程高）vs 一去难返（判词·曲）",
        "characters": ["贾探春"],
        "title": "探春结局",
        "derived_from": ["贾探春", "第119回"],
        "cheng": "第99/119回远嫁海疆、随任归省",
        "zhi": "「清明涕送江边望，千里东风一梦遥」——远适不返",
    },
    {
        "id": "情节-李纨结局",
        "chapter": 119,
        "summary": "母凭子贵荣显（程高）vs 晚韶华含讽、荣华转瞬（脂评）",
        "characters": ["李纨"],
        "title": "李纨结局",
        "derived_from": ["李纨", "贾兰", "第119回"],
        "cheng": "贾兰中举，李纨得诰命荣显",
        "zhi": "〈晚韶华〉「枉与他人作笑谈」——荣华转瞬或子夭之讽",
    },
    {
        "id": "情节-惜春结局",
        "chapter": 118,
        "summary": "安顿出家（程高）vs 缁衣乞食、归宿更凄（脂评）",
        "characters": ["贾惜春"],
        "title": "惜春结局",
        "derived_from": ["贾惜春", "第118回"],
        "cheng": "第115/118回带发修行、紫鹃相伴，相对安顿",
        "zhi": "〈虚花悟〉「独卧青灯古佛旁」——缁衣凄境诸说",
    },
    {
        "id": "情节-雨村结局",
        "chapter": 120,
        "summary": "革职递籍、了悟尘缘（程高）vs 锁枷扛、身陷囹圄（脂批）",
        "characters": ["贾雨村"],
        "title": "雨村结局",
        "derived_from": ["贾雨村", "第120回", "甄士隐"],
        "cheng": "第120回革职递籍为民，急流津遇甄士隐点化",
        "zhi": "《好了歌注》「因嫌纱帽小，致使锁枷扛」——获罪更重",
    },
    {
        "id": "情节-甄宝玉后四十回",
        "chapter": 57,
        "summary": "程高续书甄宝玉主线 vs 脂本仅第57回伏笔",
        "characters": ["甄宝玉", "贾宝玉"],
        "title": "甄宝玉后四十回",
        "derived_from": ["甄宝玉", "贾宝玉", "第57回", "第114回"],
        "cheng": "第114–119回甄宝玉入京应接、劝宝玉举业",
        "zhi": "脂本第57回仅叙「有一宝玉」，后四十回主线为续书所增",
    },
    {
        "id": "情节-贾府结局",
        "chapter": 105,
        "summary": "查抄后沐皇恩复初（程高）vs 彻底败落、白茫茫大地真干净（脂批）",
        "characters": ["贾政", "贾赦", "贾珍"],
        "title": "贾府结局",
        "derived_from": ["第105回", "hlm-e-007"],
        "cheng": "第105回查抄后第106–107、119回复世职、家道复初",
        "zhi": "「家亡人散各奔腾」「落了片白茫茫大地真干净」——无回暖",
    },
]


def topic_body(t: dict) -> str:
    chars = " · ".join(f"[[{c}]]" for c in t["characters"])
    return f"""## 结论

本议题为 **程高本续书** 与 **脂评本·探佚** 在「{t["title"]}」上的分歧承接页；人物页 `variants` 并列异文，关系图谱以虚线「矛盾边」连接。详见 [[版本异文与探佚]]。

## 论据（带出处）

| 读法 | 要点 | 出处 |
|------|------|------|
| 程高本 | {t["cheng"]} | 后四十回 |
| 脂评·探佚 | {t["zhi"]} | 判词 / 曲 / 脂批 |

## 相关链接

- {chars}
- [[版本异文与探佚]] · [/honglou/graph](/honglou/graph)
"""


def main() -> None:
    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    json_topics = []
    written = 0
    for t in TOPICS:
        json_topics.append(
            {
                "id": t["id"],
                "chapter": t["chapter"],
                "summary": t["summary"],
                "characters": t["characters"],
            }
        )
        path = TOPICS_DIR / f"{t['id']}.md"
        if path.exists():
            continue
        fm = f"""---
type: 对比
book: {BOOK}
title: {t["title"]}
category: 考证
branch: 版本学
derived_from: {t["derived_from"]}
created: {today}
tags: [版本异文, 探佚, 矛盾]
summary: {t["summary"]}
---

"""
        path.write_text(fm + topic_body(t), encoding="utf-8")
        written += 1
        print(f"  + {path.name}")

    OUT_JSON.write_text(
        json.dumps({"book": BOOK, "topics": json_topics}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[{BOOK}] variant-topics.json: {len(json_topics)} 议题 · 新建 {written} 个 topic 页")


if __name__ == "__main__":
    main()
