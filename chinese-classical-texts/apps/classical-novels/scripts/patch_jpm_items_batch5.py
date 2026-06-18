#!/usr/bin/env python3
"""金瓶梅名物 ingest 第五批：饮食/帮闲银两/六房宴饮物象。"""
from __future__ import annotations

import re

import yaml

from _common import CHAPTER_DIR, CONTENT
from lint_modules import list_known_item_ids
from tag_chapter_meta import find_ids, format_list, load_item_pairs, parse_list_field, split_body, strip_html

BOOK = "金瓶梅"

NEW_ITEMS: list[tuple[str, dict, str]] = [
    (
        "dishes",
        {
            "id": "历日",
            "type": "dish",
            "name": "历日",
            "book": BOOK,
            "category": "馈礼",
            "eaters": [],
            "holders": ["西门庆", "宋乔年"],
            "first_appear": "第78回",
            "appear_in": ["第78回"],
            "tags": ["饮食", "年节", "馈礼"],
            "summary": "宋御史回礼「一百本历日、四万纸、一口猪」（第78回），与果馅金饼、员领等构成官场年节互惠。",
        },
        """## 出处

第78回：西门庆谢宋御史后，宋差人回礼「一百本历日，四万纸，一口猪」。

## 情节功能

- 与 [[果馅金饼]]、[[浙江酒]]、[[员领]] 并置，写巡按回礼规格
- 第73回潘金莲看历日择壬子日，同一物不同功能

## 相关

- [[西门庆]] · [[果馅金饼]] · [[员领]] · 第78回
""",
    ),
    (
        "dishes",
        {
            "id": "鲜猪",
            "type": "dish",
            "name": "鲜猪",
            "book": BOOK,
            "category": "主菜",
            "ingredients": ["猪"],
            "eaters": ["西门庆"],
            "first_appear": "第78回",
            "appear_in": ["第78回"],
            "tags": ["饮食", "馈礼"],
            "summary": "第78回西门庆「宰了一口鲜猪」与浙江酒、员领等谢宋御史；年节官场馈礼中的整猪规格。",
        },
        """## 出处

第78回：「西门庆宰了一口鲜猪，两坛浙江酒……谢宋御史。」

## 相关

- [[果馅金饼]] · [[浙江酒]] · [[员领]] · 第78回
""",
    ),
    (
        "dishes",
        {
            "id": "烧鹅",
            "type": "dish",
            "name": "烧鹅",
            "book": BOOK,
            "category": "主菜",
            "ingredients": ["鹅"],
            "eaters": ["西门庆", "黄四"],
            "first_appear": "第68回",
            "appear_in": ["第68回"],
            "tags": ["饮食", "谢礼"],
            "summary": "黄四谢恩送「两只烧鹅、四只烧鸡」（第68回），与香蜡批文帮闲线并读。",
        },
        """## 出处

第68回：黄四领孙文相，「宰了一口猪、一坛酒、两只烧鹅、四只烧鸡、两盒果子」谢西门庆。

## 情节功能

- **放债·帮闲轨**感恩礼，与 [[香蜡批文]] 连坐轨伏笔

## 相关

- [[黄四]] · [[西门庆]] · [[香蜡批文]] · 第68回
""",
    ),
    (
        "customs",
        {
            "id": "冠带荣身",
            "type": "ritual",
            "name": "冠带荣身",
            "book": BOOK,
            "participants": ["陈敬济", "周守备", "庞春梅"],
            "procedure": ["升参谋", "月给米二石", "大红员领冠帽"],
            "location": "守备府",
            "first_appear": "第98回",
            "appear_in": ["第98回"],
            "tags": ["后二十回", "官场", "散场"],
            "summary": "陈敬济随守备升「参谋之职，月给米二石，冠带荣身」（第98回）；后二十回败家线短暂翻身节点。",
        },
        """## 出处

第98回：周守备剿梁山回，「军门带得敬济名字，升为参谋之职，月给米二石，冠带荣身。」

## 情节功能

- 与 [[员领]]、[[头面]] 并置，写后二十回 **冠带** 与随后败家对照

## 相关

- [[陈敬济]] · [[周守备]] · [[员领]] · [后二十回散场人物](/jinpingmei/topics/后二十回散场人物) · 第98回
""",
    ),
    (
        "customs",
        {
            "id": "官钱粮",
            "type": "institution",
            "name": "官钱粮",
            "book": BOOK,
            "participants": ["黄四", "李智", "来保", "汤保", "西门庆"],
            "procedure": ["香蜡批文连坐", "追赃", "保官儿更名汤保"],
            "location": "西门府 / 临清",
            "first_appear": "第97回",
            "appear_in": ["第97回"],
            "tags": ["衰败", "连坐", "放债链"],
            "summary": "第97回黄四、李智与「保官儿」汤保官钱粮追赃；来保被逐后改名汤保，衰败连坐轨收束。",
        },
        """## 出处

第97回：黄四、李三（李智）与保官儿汤保 **官钱粮追赃**；来保欺主被逐后改名汤保。

## 情节功能

- [药铺与放债链](/jinpingmei/topics/药铺与放债链) **衰败连坐轨** 高潮
- 与 [[香蜡批文]]、[[白银]] 互证

## 相关

- [[黄四]] · [[李智]] · [[来保]] · [[香蜡批文]] · 第97回
""",
    ),
    (
        "customs",
        {
            "id": "花红",
            "type": "ritual",
            "name": "花红",
            "book": BOOK,
            "participants": ["西门庆", "吴大舅", "应伯爵"],
            "procedure": ["羊酒花红轴文", "迎贺上任", "节礼酬答"],
            "location": "西门府",
            "first_appear": "第78回",
            "appear_in": ["第78回"],
            "tags": ["礼仪", "官场", "节令"],
            "summary": "吴大舅上任，西门庆「备羊酒花红轴文，邀请亲朋迎贺」（第78回）；清河官场往来固定礼数。",
        },
        """## 出处

第78回：「封了印来家，又备羊酒花红轴文，邀请亲朋，等吴大舅从卫中上任回来，迎接到家，摆大酒席与他作贺。」

## 相关

- [[西门庆]] · [[吴大舅]] · [[烧羊]] · 第78回
""",
    ),
    (
        "customs",
        {
            "id": "财礼",
            "type": "ritual",
            "name": "财礼",
            "book": BOOK,
            "participants": ["西门庆", "韩爱姐", "冯妈妈", "翟管家"],
            "procedure": ["二十两财礼", "半副嫁妆", "送东京蔡府"],
            "location": "西门府",
            "economic": "二十两银（第37回）",
            "first_appear": "第37回",
            "appear_in": ["第37回"],
            "tags": ["婚嫁", "银两", "帮闲"],
            "summary": "冯妈妈说嫁韩爱姐，西门庆备妆奁并「二十两财礼」（第37回）；与 [[认干亲礼]] 百两对照的婚嫁银两节点。",
        },
        """## 出处

第37回：「凡一应衣服首饰、妆奁箱柜等件，都是我这里替他办备，还与他二十两财礼。」

## 情节功能

- **临清韩爱姐线** 起点；婚嫁 **财礼** 与政商 [[认干亲礼]] 并置

## 相关

- [[韩爱姐]] · [[冯妈妈]] · [[妆奁]] · [[认干亲礼]] · 第37回
""",
    ),
    (
        "costumes",
        {
            "id": "白绫带",
            "type": "costume",
            "name": "白绫带",
            "book": BOOK,
            "wearers": ["潘金莲", "西门庆"],
            "material": "白绫",
            "occasion": "私会云雨",
            "description": "潘金莲缝白绫带儿，内装颤声娇药末，倒口针细缝，预备与西门庆欢会",
            "tags": ["服饰", "六房", "私情"],
            "summary": "第73回回目「西门庆新试白绫带」：潘金莲缝白绫带藏 [[颤声娇]]，是六房争宠与胡僧药线的名场面。",
            "first_appear": "第73回",
            "appear_in": ["第73回"],
        },
        """## 出处

第73回：「拣一条白绫儿，将磁盒内颤声娇药末儿装在里面，周围用倒口针儿撩缝的甚是细法，预备晚夕要与西门庆云雨之欢。」

## 情节功能

- 与 [[胡僧药]]、[[药五香酒]] 并置，写 **色** 之器物延伸
- 对照 [[白绫袄儿]]（外衣，非同一物）

## 相关

- [[潘金莲]] · [[西门庆]] · [[颤声娇]] · 第73回
""",
    ),
    (
        "medicines",
        {
            "id": "颤声娇",
            "type": "medicine",
            "name": "颤声娇",
            "book": BOOK,
            "category": "春药",
            "patient": "潘金莲",
            "prescriber": "胡僧",
            "holder": "潘金莲",
            "first_appear": "第73回",
            "appear_in": ["第73回"],
            "tags": ["胡僧药", "六房"],
            "summary": "胡僧春药「颤声娇」药末，潘金莲缝入白绫带内（第73回）；与西门庆纵欲、脱阳之症链并读。",
        },
        """## 出处

第73回：潘金莲「将磁盒内颤声娇药末儿」装入 [[白绫带]]。

## 情节功能

- [[胡僧药]] 子类/别名，通向第79回 [[西门庆脱阳之症]]

## 相关

- [[潘金莲]] · [[西门庆]] · [[白绫带]] · [[胡僧药]] · 第73回
""",
    ),
    (
        "customs",
        {
            "id": "暖帘",
            "type": "ritual",
            "name": "暖帘",
            "book": BOOK,
            "participants": ["西门庆", "何太监"],
            "procedure": ["厅前油纸暖帘", "水磨细炭火盆", "冬日宴饮"],
            "location": "何太监府 / 西门府",
            "first_appear": "第69回",
            "appear_in": ["第69回", "第71回"],
            "tags": ["宴饮", "物象", "冬节"],
            "summary": "何太监家宴「厅前放下油纸暖帘」、火盆细炭（第71回）；西门庆书房亦设暖帘（第69回），写宴饮场域的冬令陈设。",
        },
        """## 出处

- 第69回：西门庆书房「暖帘」内与文嫂说话。
- 第71回：何太监府「厅前放下油纸暖帘来，日光掩映，十分明亮」；火盆水磨细炭。

## 情节功能

- 宴饮 **场域物象**，与 [[火盆]]、[[宴饮纵酒]] 互文

## 相关

- [[西门庆]] · [[宴饮纵酒]] · [[火盆]] · 第71回
""",
    ),
    (
        "customs",
        {
            "id": "火盆",
            "type": "ritual",
            "name": "火盆",
            "book": BOOK,
            "participants": ["西门庆", "吴月娘", "孟玉楼", "何太监"],
            "procedure": ["炕屋火盆", "水磨细炭", "寿席案酒"],
            "location": "西门府 / 何府",
            "first_appear": "第73回",
            "appear_in": ["第73回", "第71回"],
            "tags": ["宴饮", "冬节", "物象"],
            "summary": "孟玉楼寿席「铺着火盆摆下案酒」（第73回）；何府宴饮火池火叉、水磨细炭（第71回）。",
        },
        """## 出处

- 第73回：「又在明间内放八仙桌儿，铺着火盆摆下案酒，与孟玉楼上寿。」
- 第71回：「左右火池火叉，拿上一包水磨细炭，向火盆内只一倒。」

## 相关

- [[孟玉楼]] · [[暖帘]] · [[宴饮纵酒]] · 第73回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    37: ["财礼"],
    68: ["烧鹅"],
    69: ["暖帘"],
    71: ["暖帘", "火盆"],
    73: ["白绫带", "颤声娇", "火盆", "历日"],
    78: ["历日", "鲜猪", "花红"],
    97: ["官钱粮"],
    98: ["冠带荣身"],
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
    print(f"[{BOOK}] patch batch5 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
