#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第一批：栊翠庵茶、节令食养、露剂案、病养与后段方药。"""
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
            "id": "六安茶",
            "type": "tea",
            "name": "六安茶",
            "book": BOOK,
            "category": "茶",
            "eaters": ["贾母"],
            "location": "栊翠庵",
            "literary_vs_real": "fact",
            "first_appear": "第41回",
            "appear_in": ["第41回"],
            "tags": ["饮食", "妙玉", "贾母", "品茶"],
            "summary": "第41回妙玉奉茶，言贾母不服六安茶（「别人剩下的」），改以老君眉与旧年雨水；阶级与洁癖对照。",
        },
        """## 出处

第41回栊翠庵：妙玉向贾母说明所奉非六安茶，而是老君眉；又言泡茶之水为旧年蠲的雨水。

## 情节功能

- 与 [[老君眉]]、[[梅花雪水茶]] 并置，构成「栊翠庵品茶」三层（贾母 / 钗黛 / 刘姥姥）
- 妙玉以茶水分等，写 **洁癖与阶级**

## 相关

- [[妙玉]] · [[贾母]] · [[老君眉]] · [[栊翠庵品茶链]] · 第41回
""",
    ),
    (
        "dishes",
        {
            "id": "年茶",
            "type": "dish",
            "name": "年茶",
            "book": BOOK,
            "category": "节令",
            "eaters": ["袭人"],
            "occasion": "正月",
            "first_appear": "第19回",
            "appear_in": ["第19回"],
            "tags": ["饮食", "正月", "节令"],
            "summary": "第19回袭人母接其回家「吃年茶」，与元春赐 [[糖蒸酥酪]]、省亲后正月光景并置。",
        },
        """## 出处

第19回：袭人母亲来回贾母，接袭人家去吃年茶，晚间方回；宝玉留元春所赐糖蒸酥酪与袭人。

## 情节功能

- **正月光景**与后文「花解语」同回；下人年节归家食俗
- 与小厮们「吃年茶」并提，写贾府年节内外节奏

## 相关

- [[袭人]] · [[糖蒸酥酪]] · [[元宵年例链]] · 第19回
""",
    ),
    (
        "dishes",
        {
            "id": "茶面子",
            "type": "tea",
            "name": "茶面子",
            "book": BOOK,
            "category": "茶",
            "eaters": ["尤氏"],
            "location": "稻香村",
            "first_appear": "第75回",
            "appear_in": ["第75回"],
            "tags": ["饮食", "茶", "尤氏"],
            "summary": "第75回李纨以薛姨妈所送「好茶面子」对碗与尤氏，写夜宴前后园中消闲与甄家阴影。",
        },
        """## 出处

第75回：尤氏至李纨处，李纨道「昨日他姨娘家送来的好茶面子，倒是对碗来你喝罢。」

## 相关

- [[尤氏]] · [[李纨]] · [[薛姨妈]] · 第75回
""",
    ),
    (
        "dishes",
        {
            "id": "甜烂之食",
            "type": "dish",
            "name": "甜烂之食",
            "book": BOOK,
            "category": "膳食偏好",
            "eaters": ["贾母"],
            "occasion": "寿宴、日常",
            "literary_vs_real": "plausible_qing",
            "first_appear": "第22回",
            "appear_in": ["第22回"],
            "tags": ["饮食", "贾母", "养生"],
            "summary": "第22回宝钗答贾母所好：喜热闹戏文、爱吃甜烂之食；写贾母老年食养与宝钗会意。",
        },
        """## 出处

第22回：贾母问宝钗爱听何戏、爱吃何物，宝钗「深知贾母年老人，喜热闹戏文，爱吃甜烂之食，便总依贾母往日素喜者说了出来。」

## 情节功能

- **会意**写宝钗持重；与 [[医药饮食名录]] 中贾母「软烂菜、食疗」食养链互参（inference）
- 寿宴、年例排场常据此安排菜色

## 相关

- [[贾母]] · [[薛宝钗]] · [[贾母八旬宴]] · 第22回
""",
    ),
    (
        "dishes",
        {
            "id": "供尖儿",
            "type": "dish",
            "name": "供尖儿",
            "book": BOOK,
            "category": "节令供食",
            "eaters": [],
            "occasion": "生辰、寿诞",
            "first_appear": "第62回",
            "appear_in": ["第62回"],
            "tags": ["饮食", "僧尼", "寿礼"],
            "summary": "第62回宝玉生辰，僧尼庙送「供尖儿」并寿星纸马等；与 [[群芳夜宴]] 同回对照。",
        },
        """## 出处

第62回：宝玉、宝琴同生日，「几处僧尼庙的和尚姑子送了供尖儿，并寿星纸马疏头」。

## 情节功能

- 与同日 [[群芳夜宴]]、贾敬服丹 **明暗对照**
- 宗教供养食与府内寿宴并置

## 相关

- [[贾宝玉]] · [[群芳夜宴]] · 第62回
""",
    ),
    (
        "medicines",
        {
            "id": "蔷薇硝",
            "type": "medicine",
            "name": "蔷薇硝",
            "book": BOOK,
            "category": "外用药",
            "patient": "芳官",
            "first_appear": "第59回",
            "appear_in": ["第59回", "第60回", "第61回"],
            "tags": ["露剂", "芳官", "赵姨娘"],
            "summary": "第59–60回蕊官赠芳官蔷薇硝擦春癣；贾环索取引发冲突，牵出玫瑰露、茯苓霜案。",
        },
        """## 出处

- 第59回：湘云、宝钗论蔷薇硝治杏癍癣
- 第60回：蕊官赠芳官蔷薇硝；贾环强索，芳官以 [[茉莉粉]] 搪塞

## 情节功能

- [[露剂与家法链]] 引端；赵姨娘房与怡红院冲突
- 与 [[玫瑰露]]、[[茯苓霜]] 并案

## 相关

- [[芳官]] · [[贾环]] · [[茉莉粉]] · [[露剂与家法链]] · 第60回
""",
    ),
    (
        "medicines",
        {
            "id": "茉莉粉",
            "type": "medicine",
            "name": "茉莉粉",
            "book": BOOK,
            "category": "妆粉",
            "patient": "芳官",
            "first_appear": "第60回",
            "appear_in": ["第60回", "第61回"],
            "tags": ["露剂案", "芳官", "赵姨娘"],
            "summary": "第60回回目「茉莉粉替去蔷薇硝」：芳官以茉莉粉冒充蔷薇硝搪贾环，激化赵姨娘与怡红院冲突。",
        },
        """## 出处

第60回：芳官不肯将蕊官所赠 [[蔷薇硝]] 予贾环，「另拿些来」以茉莉粉冒充，贾环觉味不对，至赵姨娘处哭闹。

## 情节功能

- 回目明示 **替粉** 事件；后文搜检、平儿压事（第61回）

## 相关

- [[芳官]] · [[贾环]] · [[赵姨娘]] · [[蔷薇硝]] · 第60回
""",
    ),
    (
        "medicines",
        {
            "id": "净饿调养",
            "type": "medicine",
            "name": "净饿调养",
            "book": BOOK,
            "category": "病养",
            "first_appear": "第52回",
            "appear_in": ["第52回", "第53回"],
            "tags": ["病养", "贾府", "风俗"],
            "summary": "贾府伤风咳嗽时「总以净饿为主，次则服药调养」（第52–53回）；晴雯、雀裘补后调养皆用此法。",
        },
        """## 出处

第52–53回叙贾府风俗：「无论上下，只一略有些伤风咳嗽，总以净饿为主，次则服药调养。」晴雯补雀裘后亦净饿数日再服药。

## 学者评价（inference）

- 清代贵族府邸常见 **饿治** 与忌口，与今日「病时须补」观念不同
- 与 [[胡庸医诊晴雯]] 中宝玉重「女孩儿禁不起虎狼药」形成 **食养—用药** 对照

## 相关

- [[晴雯]] · [[王太医诊晴雯]] · [[医药诊脉链]] · 第53回
""",
    ),
    (
        "medicines",
        {
            "id": "调经养荣丸",
            "type": "prescription",
            "name": "调经养荣丸",
            "book": BOOK,
            "category": "丸",
            "patient": "王熙凤",
            "physician": "王太医",
            "first_appear": "第77回",
            "appear_in": ["第77回"],
            "tags": ["方剂", "凤姐", "人参"],
            "summary": "第77回凤姐小月后王太医开调经养荣丸，需上等人参二两；触发贾府人参告罄与宝钗代购。",
        },
        """## 出处

第77回：凤姐病减而未愈，「仍命大夫每日诊脉服药，又开了丸药方子来配调经养荣丸。因用上等人参二两」，王夫人翻寻不得，后由贾母处匀出并托宝钗购新参。

## 情节功能

- **人参线** 与盛衰、库存、人情（宝钗办参）并读
- 与 [[人参养荣丸]]（黛玉）同名类方、不同对象，可对照

## 相关

- [[王熙凤]] · [[王夫人]] · [[薛宝钗]] · [[人参养荣丸]] · 第77回
""",
    ),
    (
        "medicines",
        {
            "id": "上等人参",
            "type": "medicine",
            "name": "上等人参",
            "book": BOOK,
            "category": "药材",
            "patient": "王熙凤",
            "first_appear": "第77回",
            "appear_in": ["第77回"],
            "tags": ["药材", "人参", "盛衰"],
            "summary": "第77回配丸需上等人参二两，府中仅存陈腐之参；贾母所余亦「成了朽糟烂木」，写败落前资源枯竭。",
        },
        """## 出处

第77回：王太医方需上等人参二两；王夫人、凤姐、邢夫人皆无；贾母所出之参「年代太陈……成了朽糟烂木，也无性力的了。」

## 情节功能（literary）

- **物资信号**：与乌进孝欠租（第53回）、后文穷窘同轴
- 与黛玉 [[人参养荣丸]]、可卿 [[益气养荣补脾和肝汤]] 并读，人参贯穿全书医药线

## 相关

- [[王熙凤]] · [[贾母]] · [[薛宝钗]] · [[调经养荣丸]] · [[人参养荣丸]] · 第77回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    19: ["年茶"],
    22: ["甜烂之食"],
    41: ["六安茶"],
    52: ["净饿调养"],
    53: ["净饿调养"],
    59: ["蔷薇硝"],
    60: ["蔷薇硝", "茉莉粉"],
    61: ["茉莉粉"],
    62: ["供尖儿", "群芳夜宴"],
    63: ["群芳夜宴"],
    75: ["茶面子"],
    77: ["调经养荣丸", "上等人参"],
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
    print(f"[{BOOK}] patch food/medicine batch1 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
