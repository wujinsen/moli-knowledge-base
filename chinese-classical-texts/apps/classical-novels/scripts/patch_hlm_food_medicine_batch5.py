#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第五批：元宵粥茶、尤氏素斋、露剂误认、后段简素寿席与黛玉后段方药。"""
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
            "id": "杏仁茶",
            "type": "dish",
            "name": "杏仁茶",
            "book": BOOK,
            "category": "茶点",
            "eaters": ["贾母", "王熙凤"],
            "location": "宁荣两府",
            "occasion": "元宵夜宴",
            "first_appear": "第54回",
            "appear_in": ["第54回"],
            "tags": ["饮食", "元宵", "甜"],
            "summary": "第54回元宵夜宴，凤姐虑贾母嫌甜，另备杏仁茶；与鸭子肉粥同回。",
        },
        """## 出处

第54回：贾母夜长觉饿，凤姐预备鸭子肉粥；又道「还有**杏仁茶**，只怕也甜」，贾母道「倒是我的意思」。

## 情节功能

- [[元宵夜宴]] 细目；贾母择 **清淡甜饮**
- 与 [[鸭子肉粥]] 并写凤姐体贴

## 相关

- [[贾母]] · [[王熙凤]] · [[元宵夜宴]] · [[元宵年例链]] · 第54回
""",
    ),
    (
        "dishes",
        {
            "id": "鸭子肉粥",
            "type": "dish",
            "name": "鸭子肉粥",
            "book": BOOK,
            "category": "粥",
            "eaters": ["贾母"],
            "location": "宁荣两府",
            "occasion": "元宵夜宴",
            "first_appear": "第54回",
            "appear_in": ["第54回"],
            "tags": ["饮食", "元宵", "粥"],
            "summary": "第54回元宵夜，贾母觉饿，凤姐回「有预备的鸭子肉粥」；贾母改要清淡，另有枣儿粳米粥。",
        },
        """## 出处

第54回：「夜长，觉的有些饿了。」凤姐儿忙回说：「有预备的**鸭子肉粥**。」贾母道：「我吃些清淡的罢。」

## 情节功能

- [[元宵夜宴]] **备膳** 层次；后改清淡
- 与 [[杏仁茶]] 同链

## 相关

- [[贾母]] · [[王熙凤]] · [[元宵夜宴]] · 第54回
""",
    ),
    (
        "dishes",
        {
            "id": "红稻米粥",
            "type": "dish",
            "name": "红稻米粥",
            "book": BOOK,
            "category": "粥",
            "eaters": ["贾母", "王熙凤", "林黛玉"],
            "location": "贾母上房",
            "first_appear": "第75回",
            "appear_in": ["第75回"],
            "tags": ["饮食", "粥", "贾母"],
            "summary": "第75回尤氏捧红稻米粥与贾母，又吩咐送凤姐、笋与风腌果子狸给黛玉；甄家阴影同席。",
        },
        """## 出处

第75回：「有稀饭吃些罢了。」尤氏早捧过一碗来，说是**红稻米粥**。贾母接来吃了半碗，便吩咐：「将这粥送给凤哥儿吃去。」

## 情节功能

- 第75回 **家宴** 与甄家抄没阴影并置
- 与 [[椒油莼酱]]、[[茶面子]] 同段

## 相关

- [[尤氏]] · [[贾母]] · [[王熙凤]] · [[林黛玉]] · 第75回
""",
    ),
    (
        "dishes",
        {
            "id": "椒油莼酱",
            "type": "dish",
            "name": "椒油莼酱",
            "book": BOOK,
            "category": "斋菜",
            "eaters": ["贾母", "王夫人", "薛宝琴"],
            "location": "贾母上房",
            "occasion": "王夫人吃斋",
            "first_appear": "第75回",
            "appear_in": ["第75回"],
            "tags": ["饮食", "斋", "贾母"],
            "summary": "第75回王夫人吃斋，面筋豆腐贾母不大爱，只拣椒油莼酱；贾母道「正想这个吃」。",
        },
        """## 出处

第75回：王夫人笑道：「今日我吃斋没有别的。那些面筋豆腐老太太又不大甚爱吃，只拣了一样**椒油莼酱**来。」贾母笑道：「这样正好，正想这个吃。」

## 情节功能

- **斋食** 与贾母口味对照
- 同回 [[红稻米粥]] 家宴

## 相关

- [[王夫人]] · [[贾母]] · [[红稻米粥]] · 第75回
""",
    ),
    (
        "dishes",
        {
            "id": "蘅芜庆生宴",
            "type": "banquet",
            "name": "蘅芜庆生宴",
            "book": BOOK,
            "category": "寿宴",
            "eaters": ["薛宝钗", "贾母", "史湘云", "贾宝玉", "王熙凤"],
            "location": "蘅芜苑",
            "occasion": "宝钗生日",
            "first_appear": "第108回",
            "appear_in": ["第108回"],
            "tags": ["饮食", "宝钗", "败落", "强欢笑"],
            "summary": "第108回抄家后贾母出一百银子办两日酒饭为宝钗过生日；强欢笑、曲牌骰令，宝玉闻潇湘鬼哭。",
        },
        """## 出处

第108回：湘云提议为宝钗拜寿，贾母「叫鸳鸯拿出一百银子来交给外头，叫他明日起预备两天的酒饭」；席间掷曲牌骰令，「强欢笑」而众人无精打采。

## 情节功能

- [[饮食纵切总览]] **奢侈曲线** 后段简素中的最后一次「热闹」
- 与 [[宝钗生辰宴]]（第22回）、[[贾母八旬宴]] 对照
- 宝玉离席闻潇湘鬼哭

## 相关

- [[薛宝钗]] · [[贾母]] · [[史湘云]] · [[宝玉宝钗成婚]] · [[宝钗生辰宴]] · 第108回
""",
    ),
    (
        "dishes",
        {
            "id": "西洋葡萄酒",
            "type": "wine",
            "name": "西洋葡萄酒",
            "book": BOOK,
            "category": "酒",
            "eaters": ["芳官", "柳五儿"],
            "location": "厨房",
            "first_appear": "第60回",
            "appear_in": ["第60回"],
            "tags": ["饮食", "露剂", "五儿"],
            "summary": "第60回五儿见小瓶胭脂汁，误道是宝玉吃的西洋葡萄酒；方知是玫瑰露，引露剂案。",
        },
        """## 出处

第60回：五儿「拿了一个五寸来高的小玻璃瓶来，迎亮照看，里面小半瓶胭脂一般的汁子，还道是宝玉吃的**西洋葡萄酒**」——后芳官说是 [[玫瑰露]]。

## 情节功能

- [[露剂与家法链]] **误认** 入口；五儿、芳官线
- 写洋货与露剂在宅中 **管控** 之难

## 相关

- [[玫瑰露]] · [[柳五儿]] · [[芳官]] · [[露剂与家法链]] · 第60回
""",
    ),
    (
        "dishes",
        {
            "id": "薛蟠生日宴",
            "type": "banquet",
            "name": "薛蟠生日宴",
            "book": BOOK,
            "category": "寿宴",
            "eaters": ["薛蟠", "薛宝钗", "贾宝玉", "林黛玉"],
            "location": "薛家",
            "first_appear": "第29回",
            "appear_in": ["第29回"],
            "tags": ["饮食", "薛蟠", "生日"],
            "summary": "第29回初三薛蟠生日，家里摆酒唱戏请贾府；宝玉因与黛玉别扭推病不去，黛玉闻香薷饮后吐。",
        },
        """## 出处

第29回：「至初三日，乃是**薛蟠生日**，家里摆酒唱戏，来请贾府诸人。」宝玉推病不去；黛玉因宝玉不来，吃 [[香薷解暑汤]] 后呕吐。

## 情节功能

- 薛家 **宴饮** 与宝黛冷战同回
- 接清虚观前后情节

## 相关

- [[薛蟠]] · [[贾宝玉]] · [[林黛玉]] · [[香薷解暑汤]] · 第29回
""",
    ),
    (
        "dishes",
        {
            "id": "香薷解暑汤",
            "type": "dish",
            "name": "香薷解暑汤",
            "book": BOOK,
            "category": "汤",
            "eaters": ["林黛玉"],
            "location": "潇湘馆",
            "first_appear": "第29回",
            "appear_in": ["第29回"],
            "tags": ["饮食", "汤", "黛玉", "暑"],
            "summary": "第29回黛玉因宝玉不来烦恼，方才吃的香薷饮解暑汤承受不住，吐湿手帕。",
        },
        """## 出处

第29回：黛玉「心里一烦恼，方才吃的**香薷饮解暑汤**便承受不住，"哇"的一声都吐了出来。」

## 情节功能

- **情志** 触发躯体反应；与 [[薛蟠生日宴]] 同链
- 暑饮 plausible_qing

## 相关

- [[林黛玉]] · [[贾宝玉]] · [[薛蟠生日宴]] · 第29回
""",
    ),
    (
        "medicines",
        {
            "id": "宝钗散瘀丸",
            "type": "prescription",
            "name": "宝钗散瘀丸",
            "book": BOOK,
            "category": "外敷",
            "patient": "贾宝玉",
            "first_appear": "第34回",
            "appear_in": ["第34回"],
            "tags": ["方剂", "宝钗", "打板"],
            "summary": "第34回宝玉挨贾政板子后，宝钗托一丸药来，嘱袭人用酒研开敷上，散淤血热毒。",
        },
        """## 出处

第34回：「只见宝钗手里托着**一丸药**走进来，向袭人说道：晚上把这药用酒研开，替他敷上，把那淤血的热毒散开，可以就好了。」

## 情节功能

- 宝钗 **细心** 与「羞笼红麝串」情感线并置
- 打板后 **外治** 与内情

## 相关

- [[薛宝钗]] · [[贾宝玉]] · [[袭人]] · 第34回
""",
    ),
    (
        "medicines",
        {
            "id": "湘云时气",
            "type": "diagnosis",
            "name": "湘云时气",
            "book": BOOK,
            "category": "证候",
            "patient": "史湘云",
            "first_appear": "第55回",
            "appear_in": ["第55回"],
            "tags": ["证候", "湘云", "时气"],
            "summary": "第55回孟春黛玉嗽疾，湘云亦因时气所感卧病蘅芜苑，一天医药不断；诗社暂停。",
        },
        """## 出处

第55回：「时届孟春，黛玉又犯了嗽疾。湘云亦因**时气**所感，亦卧病于蘅芜苑，一天医药不断。」

## 情节功能

- 与 [[李纨时气]]、[[黛玉嗽疾]] 并写 **春令时病**
- 探春、李纨理家期间园事

## 相关

- [[史湘云]] · [[林黛玉]] · [[李纨时气]] · [[黛玉嗽疾]] · 第55回
""",
    ),
    (
        "medicines",
        {
            "id": "黑逍遥方",
            "type": "prescription",
            "name": "黑逍遥方",
            "book": BOOK,
            "category": "汤剂",
            "patient": "林黛玉",
            "physician": "王太医",
            "first_appear": "第83回",
            "appear_in": ["第83回"],
            "tags": ["方剂", "黛玉", "积郁"],
            "summary": "第83回王太医诊黛玉积郁，方意先以黑逍遥开其先，归肺固金继其后；忌骤用补剂。",
        },
        """## 出处

第83回：王太医论黛玉脉案，治法「须得**疏肝保肺，涵养心脾**」；方意「**黑逍遥**开其先，**归肺固金**继其后」，并释柴胡须鳖血拌炒。

## 情节功能

- [[黛玉积郁脉案]] 之 **方名** 拆页；后段详脉
- 与第97回 [[黛玉郁气吐血]] 慢性—急变链

## 相关

- [[林黛玉]] · [[黛玉积郁脉案]] · [[王太医诊晴雯]] · 第83回
""",
    ),
    (
        "medicines",
        {
            "id": "敛阴止血药",
            "type": "prescription",
            "name": "敛阴止血药",
            "book": BOOK,
            "category": "汤剂",
            "patient": "林黛玉",
            "physician": "王大夫",
            "first_appear": "第97回",
            "appear_in": ["第97回"],
            "tags": ["方剂", "黛玉", "吐血"],
            "summary": "第97回王大夫诊黛玉郁气伤肝、肝不藏血，言「要用敛阴止血的药，方可望好」。",
        },
        """## 出处

第97回：王大夫诊脉后道：「这是郁气伤肝，肝不藏血……如今要用**敛阴止血的药**，方可望好。」

## 情节功能

- [[黛玉郁气吐血]] 之 **治法** 实体；闻婚讯急变
- 后文焚稿、绝粒

## 相关

- [[林黛玉]] · [[黛玉郁气吐血]] · [[王大夫]] · [[宝玉宝钗成婚]] · 第97回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    29: ["薛蟠生日宴", "香薷解暑汤"],
    34: ["宝钗散瘀丸"],
    54: ["杏仁茶", "鸭子肉粥"],
    55: ["湘云时气"],
    60: ["西洋葡萄酒"],
    75: ["红稻米粥", "椒油莼酱"],
    83: ["黑逍遥方"],
    97: ["敛阴止血药"],
    108: ["蘅芜庆生宴"],
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
    print(f"[{BOOK}] patch food/medicine batch5 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
