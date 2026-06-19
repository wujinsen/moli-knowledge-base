#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第七批：芳官盒膳、北静拜寿茶宴、巧姐惊风方药与黛玉后段病养。"""
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
            "id": "酒酿蒸鸭",
            "type": "dish",
            "name": "酒酿蒸鸭",
            "book": BOOK,
            "category": "蒸菜",
            "eaters": ["芳官", "柳五儿"],
            "location": "怡红院",
            "first_appear": "第62回",
            "appear_in": ["第62回"],
            "tags": ["饮食", "芳官", "柳家"],
            "summary": "第62回柳家遣人送盒：一碗酒酿清蒸鸭子，与虾丸汤、绿畦饭等同盒，芳官生日简席。",
        },
        """## 出处

第62回：柳家的遣人送了一个盒子来——「里面是一碗虾丸鸡皮汤，又是一碗**酒酿清蒸鸭子**」。

## 情节功能

- [[群芳夜宴]] 前后 **厨房温情**；柳五儿与芳官线
- 同回 [[供尖儿]] 僧尼寿礼、宝玉宝琴同生日

## 相关

- [[芳官]] · [[柳五儿]] · [[露剂与家法链]] · 第62回
""",
    ),
    (
        "dishes",
        {
            "id": "虾丸鸡皮汤",
            "type": "dish",
            "name": "虾丸鸡皮汤",
            "book": BOOK,
            "category": "汤",
            "eaters": ["芳官"],
            "location": "怡红院",
            "first_appear": "第62回",
            "appear_in": ["第62回"],
            "tags": ["饮食", "汤", "芳官"],
            "summary": "第62回柳家送盒首碗：虾丸鸡皮汤，与酒酿蒸鸭、绿畦香稻饭等同送芳官。",
        },
        """## 出处

第62回：柳家盒子「里面是一碗**虾丸鸡皮汤**，又是一碗酒酿清蒸鸭子」。

## 相关

- [[酒酿蒸鸭]] · [[绿畦香稻饭]] · [[芳官]] · 第62回
""",
    ),
    (
        "dishes",
        {
            "id": "绿畦香稻饭",
            "type": "dish",
            "name": "绿畦香稻饭",
            "book": BOOK,
            "category": "饭",
            "eaters": ["芳官"],
            "location": "怡红院",
            "first_appear": "第62回",
            "appear_in": ["第62回"],
            "tags": ["饮食", "饭", "芳官"],
            "summary": "第62回柳家盒膳：一大碗热腾腾碧荧荧蒸的绿畦香稻粳米饭，与酒酿蒸鸭等同盒。",
        },
        """## 出处

第62回：盒内「一碟……奶油松瓤卷酥，并一大碗热腾腾碧荧荧蒸的**绿畦香稻粳米饭**」。

## 情节功能

- **色香** 细写；与 [[红稻米粥]] 同属精米饭类名物

## 相关

- [[酒酿蒸鸭]] · [[芳官]] · 第62回
""",
    ),
    (
        "dishes",
        {
            "id": "醒酒酸汤",
            "type": "dish",
            "name": "醒酒酸汤",
            "book": BOOK,
            "category": "汤",
            "eaters": ["王熙凤"],
            "location": "藕香榭",
            "occasion": "群芳夜宴",
            "first_appear": "第62回",
            "appear_in": ["第62回"],
            "tags": ["饮食", "醒酒", "凤姐"],
            "summary": "第62回红香圃群芳夜宴后，探春命衔醒酒石并喝些酸汤，凤姐方觉好些。",
        },
        """## 出处

第62回：凤姐在红香圃「用了水，又吃了两盏酽茶。探春忙命将醒酒石拿来给他衔在口内，一时又命他喝了一些**酸汤**，方才觉得好了些」。

## 情节功能

- [[群芳夜宴]] **宿醉** 余波；与 [[合欢酒]]、[[普洱茶]] 同链

## 相关

- [[王熙凤]] · [[群芳夜宴]] · 第62回
""",
    ),
    (
        "dishes",
        {
            "id": "北静王赏茶",
            "type": "tea",
            "name": "北静王赏茶",
            "book": BOOK,
            "category": "茶",
            "eaters": ["贾宝玉"],
            "location": "北静王府",
            "first_appear": "第85回",
            "appear_in": ["第85回"],
            "tags": ["饮食", "茶", "北静王"],
            "summary": "第85回宝玉北静王府拜寿，单留说话，北静王甚加爱惜又赏茶，并论贾政学政。",
        },
        """## 出处

第85回：北静王单留宝玉说话，「北静王甚加爱惜，又**赏了茶**」，并谈巡抚保举贾政。

## 情节功能

- **王府恩赏** 与第15回 [[路祭茶果]]、省亲恩宠并置
- 同回 [[北静王赏宴]] 外席

## 相关

- [[北静王]] · [[贾宝玉]] · [[北静王赏宴]] · 第85回
""",
    ),
    (
        "dishes",
        {
            "id": "北静王赏宴",
            "type": "banquet",
            "name": "北静王赏宴",
            "book": BOOK,
            "category": "寿宴",
            "eaters": ["贾赦", "贾政", "贾珍", "贾琏", "贾宝玉"],
            "location": "北静王府",
            "occasion": "北静王寿",
            "first_appear": "第85回",
            "appear_in": ["第85回"],
            "tags": ["饮食", "宴", "北静王"],
            "summary": "第85回北静郡王生日，贾赦等拜寿；外殿诸公谢宴，宝玉单赏饭，呈上谢宴帖。",
        },
        """## 出处

第85回：「外面诸位大人老爷都在前殿**谢王爷赏宴**」——呈上谢宴并请午安帖子；又「这贾宝玉王爷单赏的饭预备了」。

## 情节功能

- 后段 **王府往来** 仍盛；与抄家前后对照
- 同回赵姨娘、贾环弄药余波

## 相关

- [[北静王]] · [[北静王赏茶]] · [[贾宝玉]] · 第85回
""",
    ),
    (
        "medicines",
        {
            "id": "发散风痰药",
            "type": "medicine",
            "name": "发散风痰药",
            "book": BOOK,
            "category": "汤剂",
            "patient": "巧姐",
            "physician": "大夫",
            "first_appear": "第84回",
            "appear_in": ["第84回"],
            "tags": ["医药", "巧姐", "惊风"],
            "summary": "第84回巧姐内热惊风，大夫言须先用一剂发散风痰药，并四神散、真牛黄。",
        },
        """## 出处

第84回：大夫诊巧姐后回贾母——「须先用一剂**发散风痰药**，还要用四神散才好……如今的牛黄都是假的，要找**真牛黄**方用得」。

## 情节功能

- **巧姐惊风** 与 [[贾环]] 弄泼药铞并写
- 凤姐寻 [[真牛黄]]、王夫人遣人往薛家

## 相关

- [[四神散]] · [[真牛黄]] · [[贾母]] · [[王熙凤]] · 第84回
""",
    ),
    (
        "medicines",
        {
            "id": "四神散",
            "type": "medicine",
            "name": "四神散",
            "book": BOOK,
            "category": "散剂",
            "patient": "巧姐",
            "first_appear": "第84回",
            "appear_in": ["第84回"],
            "tags": ["医药", "巧姐", "惊风"],
            "summary": "第84回巧姐惊风方：大夫言发散风痰药后须用四神散，病势不轻。",
        },
        """## 出处

第84回：同 [[发散风痰药]]——「还要用**四神散**才好，因病势来得不轻」。

## 相关

- [[发散风痰药]] · [[真牛黄]] · 巧姐 · 第84回
""",
    ),
    (
        "medicines",
        {
            "id": "真牛黄",
            "type": "medicine",
            "name": "真牛黄",
            "book": BOOK,
            "category": "药材",
            "patient": "巧姐",
            "first_appear": "第84回",
            "appear_in": ["第84回"],
            "tags": ["医药", "药材", "巧姐"],
            "summary": "第84回大夫言如今牛黄多假，巧姐惊风须找真牛黄方用；幸府中还有一点配药。",
        },
        """## 出处

第84回：「如今的牛黄都是假的，要找**真牛黄**方用得。」凤姐道外头买须真的；平儿配药时云「幸亏牛黄还有一点」。

## 情节功能

- **药材真伪** 信号；与 [[上等人参]] 陈腐参对照

## 相关

- [[发散风痰药]] · [[四神散]] · [[王熙凤]] · [[平儿]] · 第84回
""",
    ),
    (
        "medicines",
        {
            "id": "钩藤煎",
            "type": "medicine",
            "name": "钩藤煎",
            "book": BOOK,
            "category": "汤剂",
            "patient": "薛姨妈",
            "first_appear": "第84回",
            "appear_in": ["第84回"],
            "tags": ["医药", "钩藤", "理气"],
            "summary": "第84回薛姨妈被金桂气怄得肝气上逆，宝钗叫人买钩藤浓浓煎一碗与母亲。",
        },
        """## 出处

第84回：「宝钗……先叫人去买了几钱**钩藤**来，浓浓的煎了一碗，给他母亲吃了。」

## 情节功能

- 金桂撒泼 **家宅医药** 侧写；与巧姐惊风同回

## 相关

- [[薛宝钗]] · [[薛姨妈]] · [[夏金桂]] · 第84回
""",
    ),
    (
        "medicines",
        {
            "id": "王大夫诊黛玉",
            "type": "medicine",
            "name": "王大夫诊黛玉",
            "book": BOOK,
            "category": "诊脉",
            "patient": "林黛玉",
            "physician": "王大夫",
            "first_appear": "第97回",
            "appear_in": ["第97回"],
            "tags": ["医药", "诊脉", "黛玉"],
            "summary": "第97回黛玉闻宝玉宝钗事吐血，王大夫诊为郁气伤肝、肝不藏血，言须敛阴止血药。",
        },
        """## 出处

第97回：「**王大夫**同着贾琏进来，诊了脉，说道：『尚不妨事。这是郁气伤肝，肝不藏血……如今要用 [[敛阴止血药]]，方可望好。』」

## 情节功能

- 后段 **黛玉脉案** 与 [[宝玉宝钗成婚]] 同轴
- 王大夫区别于 [[王太医诊晴雯]]（和剂）

## 相关

- [[林黛玉]] · [[敛阴止血药]] · [[黛玉郁气吐血]] · [[宝玉宝钗成婚]] · 第97回
""",
    ),
    (
        "medicines",
        {
            "id": "黛玉绝粒",
            "type": "medicine",
            "name": "黛玉绝粒",
            "book": BOOK,
            "category": "病养",
            "patient": "林黛玉",
            "first_appear": "第90回",
            "appear_in": ["第90回"],
            "tags": ["医药", "黛玉", "绝食"],
            "summary": "第90回黛玉闻说宝玉亲事后自戕，渐渐不支，一日竟至绝粒；紫鹃雪雁不敢声张。",
        },
        """## 出处

第90回：「黛玉自立意自戕之后，渐渐不支，一日竟至**绝粒**。」紫鹃料无指望，雪雁与侍书私语亲事，愈促其病。

## 情节功能

- **焚稿泪尽** 前段；与 [[敛阴止血药]]、[[王大夫诊黛玉]] 相接
- 傻大姐走风 → 第97回吐血

## 相关

- [[林黛玉]] · [[宝玉宝钗成婚]] · [[紫鹃]] · 第90回 · 第97回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    62: ["酒酿蒸鸭", "虾丸鸡皮汤", "绿畦香稻饭", "醒酒酸汤"],
    84: ["发散风痰药", "四神散", "真牛黄", "钩藤煎"],
    85: ["北静王赏茶", "北静王赏宴"],
    90: ["黛玉绝粒"],
    97: ["王大夫诊黛玉"],
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
    print(f"[{BOOK}] patch food/medicine batch7 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
