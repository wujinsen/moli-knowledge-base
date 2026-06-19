#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第八批：芳官盒膳余项、后段燕窝汤、贾母丧仪与参汤、尤氏病养与刘姥姥求神。"""
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
            "id": "奶油松瓤卷酥",
            "type": "dish",
            "name": "奶油松瓤卷酥",
            "book": BOOK,
            "category": "点心",
            "eaters": ["芳官"],
            "location": "怡红院",
            "first_appear": "第62回",
            "appear_in": ["第62回"],
            "tags": ["饮食", "点心", "芳官"],
            "summary": "第62回柳家送盒：一碟四个奶油松瓤卷酥，与绿畦香稻饭等同盒送芳官。",
        },
        """## 出处

第62回：柳家盒子「还有一碟四个**奶油松瓤卷酥**，并一大碗热腾腾碧荧荧蒸的绿畦香稻粳米饭」。

## 情节功能

- 同 [[绿畦香稻饭]]、[[酒酿蒸鸭]] 构成芳官生日 **盒膳** 细目
- [[群芳夜宴]] 前后厨房线

## 相关

- [[芳官]] · [[柳五儿]] · 第62回
""",
    ),
    (
        "dishes",
        {
            "id": "胭脂鹅脯",
            "type": "dish",
            "name": "胭脂鹅脯",
            "book": BOOK,
            "category": "腌味",
            "eaters": ["芳官"],
            "location": "怡红院",
            "first_appear": "第62回",
            "appear_in": ["第62回"],
            "tags": ["饮食", "腌味", "芳官"],
            "summary": "第62回柳家盒膳：一碟腌的胭脂鹅脯，与虾丸汤、酒酿蒸鸭等同送。",
        },
        """## 出处

第62回：「一碟**腌的胭脂鹅脯**，还有一碟四个奶油松瓤卷酥……」

## 相关

- [[酒酿蒸鸭]] · [[芳官]] · 第62回
""",
    ),
    (
        "dishes",
        {
            "id": "燕窝汤",
            "type": "dish",
            "name": "燕窝汤",
            "book": BOOK,
            "category": "汤",
            "eaters": ["贾宝玉"],
            "location": "怡红院",
            "first_appear": "第89回",
            "appear_in": ["第89回"],
            "tags": ["饮食", "汤", "燕窝", "宝玉"],
            "summary": "第89回袭人因宝玉昨夜未睡，叫厨房作燕窝汤，麝月伺候宝玉早起空腹饮用。",
        },
        """## 出处

第89回：「却是一碗**燕窝汤**」——袭人云：「昨夜二爷没吃饭，又翻腾了一夜……所以叫小丫头们叫厨房里作了这个来的。」

## 情节功能

- 与 [[燕窝粥]]（黛玉弱症、第45回）并读：**同材异境**
- 晴雯雀裘、宝玉学房 **神伤** 余波

## 相关

- [[贾宝玉]] · [[袭人]] · [[燕窝粥]] · 第89回
""",
    ),
    (
        "dishes",
        {
            "id": "贾母丧仪供饭",
            "type": "banquet",
            "name": "贾母丧仪供饭",
            "book": BOOK,
            "category": "丧仪供食",
            "eaters": [],
            "location": "荣国府",
            "occasion": "贾母丧仪",
            "first_appear": "第110回",
            "appear_in": ["第110回"],
            "tags": ["饮食", "丧仪", "贾母"],
            "summary": "第110回贾母停灵第三日，供饭短缺、菜饭不齐，凤姐力诎难支，显末世丧仪拮据。",
        },
        """## 出处

第110回：「供了饭还叫亲戚们等着吗？叫了半天，来了菜，**短了饭**，这是什么办事的道理！」

## 情节功能

- [[宁戚丧仪]] 理念与邢夫人 **吝啬** 交织；对照 [[秦可卿丧仪]]、[[奠茶饭]]
- 凤姐吐血前 **家务崩坏** 信号

## 相关

- [[贾母]] · [[王熙凤]] · [[宁戚丧仪]] · [[秦可卿丧仪饮食链]] · 第110回
""",
    ),
    (
        "dishes",
        {
            "id": "贾母辞灵奠",
            "type": "dish",
            "name": "贾母辞灵奠",
            "book": BOOK,
            "category": "丧仪供食",
            "eaters": [],
            "location": "荣国府",
            "occasion": "辞灵",
            "first_appear": "第111回",
            "appear_in": ["第111回"],
            "tags": ["饮食", "丧仪", "辞灵"],
            "summary": "第111回远客去后预备辞灵，孝幕内女眷哭奠；琥珀等哭奠时鸳鸯不在，旋即殉主。",
        },
        """## 出处

第110–111回：停灵后「到二更多天远客去后，便预备**辞灵**」；「到了琥珀等一干的人**哭奠**之时，却不见鸳鸯」。

## 情节功能

- [[鸳鸯]] 殉主 **前奏**；与 [[奠茶饭]]（可卿路祭）对照
- 送殡夜 **盗入** 同轴（第111回）

## 相关

- [[贾母]] · [[鸳鸯]] · [[奠茶饭]] · 第111回
""",
    ),
    (
        "dishes",
        {
            "id": "宁戚丧仪",
            "type": "custom",
            "name": "宁戚丧仪",
            "book": BOOK,
            "category": "丧制",
            "eaters": [],
            "location": "荣国府",
            "occasion": "贾母丧仪",
            "first_appear": "第110回",
            "appear_in": ["第110回"],
            "tags": ["饮食", "丧仪", "礼制"],
            "summary": "第110回贾政引「丧与其易，宁戚」，主张悲切真孝、不必糜费，致供饭短缺与体面难兼。",
        },
        """## 出处

第110回：鸳鸯转宝玉语——「老爷的意思老太太的丧事只要悲切才是真孝，不必糜费图好看的念头。」又贾政云银子「用在老太太身上也是该当的」，邢夫人却 **吝银**。

## 情节功能

- **礼制话语** 与 [[贾母丧仪供饭]] 短缺并置
- 末世 **省俭** 与 [[抄家席间]] 对照

## 相关

- [[贾母丧仪供饭]] · [[贾政]] · [[邢夫人]] · 第110回
""",
    ),
    (
        "dishes",
        {
            "id": "软烂菜",
            "type": "dish",
            "name": "软烂菜",
            "book": BOOK,
            "category": "食养",
            "eaters": ["贾母"],
            "first_appear": "第22回",
            "appear_in": ["第22回"],
            "tags": ["饮食", "食养", "贾母", "inference"],
            "summary": "与第22回宝钗所答贾母「喜吃甜烂之食」互参，为贾母长寿食养链之 inference 名物（见医药饮食名录）。",
        },
        """## 出处

- **直接**：第22回宝钗答贾母所好——「喜热闹戏文，爱吃**甜烂之食**」（见 [[甜烂之食]]）
- **互参**：[[医药饮食名录]] 贾母项「软烂菜、食疗」食养链（inference）

## 情节功能

- 与 [[甜烂之食]]、[[八旬寿点]] 构成 **贾母口腹** 纵切
- 宝钗 **会意** 写其持重

## 相关

- [[甜烂之食]] · [[贾母]] · [[薛宝钗]] · [[医药饮食名录]] · 第22回
""",
    ),
    (
        "medicines",
        {
            "id": "贾母参汤",
            "type": "medicine",
            "name": "贾母参汤",
            "book": BOOK,
            "category": "汤剂",
            "patient": "贾母",
            "first_appear": "第109回",
            "appear_in": ["第109回", "第110回"],
            "tags": ["医药", "参汤", "贾母"],
            "summary": "第109回邢夫人进参汤，贾母却只要茶；第110回回光返照时贾政再进参汤。",
        },
        """## 出处

- 第109回：「贾母睁眼要茶喝，邢夫人便进了一杯**参汤**。贾母刚用嘴接着喝，便道：『不要这个，倒一钟茶来我喝。』」
- 第110回：「贾政知是回光返照，即忙进上**参汤**。」

## 情节功能

- **临终** 医药与 [[疏气安神丸]]（抄家惊吓）并轴
- 参汤 vs 茶：贾母 **最后口腹** 选择

## 相关

- [[贾母]] · [[邢夫人]] · [[贾政]] · 第109回 · 第110回
""",
    ),
    (
        "medicines",
        {
            "id": "尤氏足阳明谵语",
            "type": "medicine",
            "name": "尤氏足阳明谵语",
            "book": BOOK,
            "category": "诊脉",
            "patient": "尤氏",
            "physician": "大夫",
            "first_appear": "第102回",
            "appear_in": ["第102回"],
            "tags": ["医药", "谵语", "足阳明"],
            "summary": "第102回尤氏送探春后感邪发热，大夫言入足阳明胃经、谵语不清，有大秽即可身安，服剂不减反狂。",
        },
        """## 出处

第102回：大夫云「如今缠经，入了**足阳明胃经**，所以**谵语**不清，如有所见，有了**大秽**即可身安。」尤氏服了两剂，并不稍减，更加发起狂来。

## 情节功能

- 大观园 **荒凉** 感邪；贾蓉疑 **撞客** → [[毛半仙占卦]]
- 后段 **园废** 侧写

## 相关

- [[尤氏]] · [[毛半仙占卦]] · [[大观园]] · 第102回
""",
    ),
    (
        "medicines",
        {
            "id": "毛半仙占卦",
            "type": "medicine",
            "name": "毛半仙占卦",
            "book": BOOK,
            "category": "诊脉",
            "patient": "尤氏",
            "physician": "毛半仙",
            "first_appear": "第102回",
            "appear_in": ["第102回"],
            "tags": ["医药", "占卦", "撞客"],
            "summary": "第102回贾蓉请南方毛半仙为尤氏占卦，疑从园中走来撞客，与太医足阳明说并置。",
        },
        """## 出处

第102回：「外头有个**毛半仙**，是南方人，卦起的很灵，不如请他来**占卦**占卦。看有信儿呢……」

## 情节功能

- **医卜两途**：太医胃经说 vs 撞客占卦
- 与 [[刘姥姥求神]] 同属后段 **民俗疗疾**

## 相关

- [[尤氏足阳明谵语]] · [[尤氏]] · [[贾蓉]] · 第102回
""",
    ),
    (
        "medicines",
        {
            "id": "赵姨娘办理后事",
            "type": "medicine",
            "name": "赵姨娘办理后事",
            "book": BOOK,
            "category": "诊脉",
            "patient": "赵姨娘",
            "physician": "大夫",
            "first_appear": "第113回",
            "appear_in": ["第113回"],
            "tags": ["医药", "后事", "赵姨娘"],
            "summary": "第113回赵姨娘中毒暴病，大夫不敢诊，只嘱办理后事；摸脉已无脉息。",
        },
        """## 出处

第113回：「大夫来了，也不敢诊，只嘱咐『**办理后事**罢』……那大夫用手一摸，已无脉息。」

## 情节功能

- **服毒** 报应；与 [[虎狼药]]、贾环弄药线并读
- 周姨娘叹 **妾命** 侧写

## 相关

- [[赵姨娘]] · [[贾环]] · 第113回
""",
    ),
    (
        "medicines",
        {
            "id": "刘姥姥求神",
            "type": "medicine",
            "name": "刘姥姥求神",
            "book": BOOK,
            "category": "病养",
            "patient": "王熙凤",
            "first_appear": "第113回",
            "appear_in": ["第113回"],
            "tags": ["医药", "求神", "刘姥姥"],
            "summary": "第113回刘姥姥见凤姐病笃，言村庄人病则求神许愿、花几百钱即可，并愿替凤姐祷告。",
        },
        """## 出处

第113回：「我们屯乡里的人不会病的，若一病了就要求神许愿……我想姑奶奶的病不要撞着什么了罢？」又云：「求你替我**祷告**，要用供献的银钱我有。」

## 情节功能

- **村野疗疾** vs 府中医脉；凤姐托 **巧姐** 于刘姥姥
- 与 [[毛半仙占卦]] 并置

## 相关

- [[刘姥姥]] · [[王熙凤]] · [[巧姐]] · 第113回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    10: ["燕窝汤"],
    22: ["软烂菜"],
    62: ["奶油松瓤卷酥", "胭脂鹅脯"],
    83: ["燕窝汤"],
    89: ["燕窝汤"],
    102: ["尤氏足阳明谵语", "毛半仙占卦"],
    109: ["贾母参汤"],
    110: ["贾母参汤", "贾母丧仪供饭", "宁戚丧仪"],
    111: ["贾母辞灵奠"],
    113: ["赵姨娘办理后事", "刘姥姥求神"],
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
    print(f"[{BOOK}] patch food/medicine batch8 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
