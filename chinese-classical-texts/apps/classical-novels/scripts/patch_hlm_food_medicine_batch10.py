#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第十批：后段86–120 当槽酒案、南味小菜、元春通关、宝钗感邪、抄家茶器、妙玉闷香、祭礼扶正。"""
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
            "id": "薛蟠当槽酒案",
            "type": "custom",
            "name": "薛蟠当槽酒案",
            "book": BOOK,
            "category": "酒案",
            "eaters": ["薛蟠", "蒋玉菡"],
            "location": "城南酒铺",
            "first_appear": "第86回",
            "appear_in": ["第86回"],
            "tags": ["饮食", "酒案", "薛蟠", "误杀"],
            "summary": "第86回薛蟠南行，与蒋玉菡在铺子里吃饭喝酒；当槽张三迟换酒，酒碗误碰卤门致死。",
        },
        """## 出处

第86回：「大爷同他在个铺子里吃饭喝酒，因为这**当槽儿的**尽着拿眼瞟蒋玉菡……叫那当槽儿的换酒……大爷就拿起酒碗照他打去……酒碗误碰卤门身死。」

## 情节功能

- [[薛蟠]] **误杀** [[张三]] 线；[[吴良]] 当槽作证、买嘱撕掳
- 与 [[抄家席间]]、[[薛蟠生日宴]] 对照 **酒祸**

## 相关

- [[薛蟠]] · [[张三]] · [[吴良]] · [[蒋玉菡]] · 第86回
""",
    ),
    (
        "dishes",
        {
            "id": "南边糟东西",
            "type": "dish",
            "name": "南边糟东西",
            "book": BOOK,
            "category": "糟味",
            "eaters": ["王熙凤"],
            "location": "荣国府",
            "first_appear": "第88回",
            "appear_in": ["第88回"],
            "tags": ["饮食", "糟味", "凤姐", "南味"],
            "summary": "第88回凤姐备晚饭，命弄一两碟南边来的糟东西就粥。",
        },
        """## 出处

第88回：「你们熬了粥了没有？……你们把那**南边来的糟东西**弄一两碟来罢。」

## 情节功能

- **南味** 进府；同回 [[南小菜]]、水月庵讨物并读
- 与 [[风腌果子狸]]、[[椒油莼酱]] 地域 **口味** 纵切

## 相关

- [[王熙凤]] · [[南小菜]] · 第88回
""",
    ),
    (
        "dishes",
        {
            "id": "南小菜",
            "type": "dish",
            "name": "南小菜",
            "book": BOOK,
            "category": "小菜",
            "eaters": [],
            "location": "水月庵",
            "first_appear": "第88回",
            "appear_in": ["第88回"],
            "tags": ["饮食", "小菜", "水月庵", "南味"],
            "summary": "第88回水月庵师父向凤姐讨两瓶南小菜并支月银，平儿记挂。",
        },
        """## 出处

第88回：「水月庵的师父打发人来，要向奶奶讨**两瓶南小菜**，还要支用几个月的月银。」

## 情节功能

- 庵中 **日常给养**；伏笔 [[水月庵风月案]]
- 与 [[南边糟东西]] 同回 **南货** 线

## 相关

- [[王熙凤]] · [[水月庵]] · [[南边糟东西]] · 第88回
""",
    ),
    (
        "dishes",
        {
            "id": "水月庵风月案",
            "type": "custom",
            "name": "水月庵风月案",
            "book": BOOK,
            "category": "风月案",
            "eaters": [],
            "location": "水月庵",
            "first_appear": "第93回",
            "appear_in": ["第93回"],
            "tags": ["饮食", "风月案", "凤姐", "庵门"],
            "summary": "第93回回目「水月庵掀翻风月案」；平儿误说馒头庵，凤姐急火上攻吐出一口血。",
        },
        """## 出处

- 第93回回目：「水月庵掀翻**风月案**」
- 正文：平儿错说「**馒头庵**里的事情」——凤姐「急火上攻……哇的一声，吐出一口血来」；后辨明是「水月庵里不过是女沙弥女道士的事」

## 情节功能

- [[王熙凤]] **心虚** 旧案；与 [[弄权葬亲]]、[[抄检大观园]] 并轴
- 庵门 **给养**（[[南小菜]]）与 **风纪** 对照

## 相关

- [[王熙凤]] · [[平儿]] · [[水月庵]] · [[南小菜]] · 第93回
""",
    ),
    (
        "dishes",
        {
            "id": "抄家查茶器",
            "type": "custom",
            "name": "抄家查茶器",
            "book": BOOK,
            "category": "茶器",
            "eaters": [],
            "location": "荣禧堂",
            "first_appear": "第105回",
            "appear_in": ["第105回"],
            "tags": ["饮食", "茶器", "抄家", "查抄"],
            "summary": "第105回查抄登帐：三镶金象牙筋、镀金执壶、茶托、银碟、银酒杯等茶酒器列清单。",
        },
        """## 出处

第105回查抄清单：「**三镶金象牙筋**二把，镀金执壶四把，镀金折盂三对，**茶托**二件，银碟七十六件，银酒杯三十六个。」

## 情节功能

- [[抄家席间]] **物证** 层；宴饮未散即 **籍没**
- 与 [[黄杨根套杯]]、[[茶筅]]、[[宫制诗筒]] 器用纵切

## 相关

- [[抄家席间]] · [[贾政]] · 第105回
""",
    ),
    (
        "dishes",
        {
            "id": "甄应嘉祭礼",
            "type": "custom",
            "name": "甄应嘉祭礼",
            "book": BOOK,
            "category": "祭礼",
            "eaters": [],
            "location": "荣国府",
            "occasion": "奠祭",
            "first_appear": "第114回",
            "appear_in": ["第114回"],
            "tags": ["饮食", "祭礼", "甄应嘉", "贾母丧"],
            "summary": "第114回甄应嘉蒙恩还职来京，知贾母新丧，特备祭礼择日往寄灵处拜奠，先来拜望献茶。",
        },
        """## 出处

第114回：「知道贾母新丧，**特备祭礼**择日到寄灵的地方**拜奠**，所以先来拜望……分宾主坐下，**献了茶**。」

## 情节功能

- **甄贾** 对照余波；与 [[奠茶饭]]、[[贾母辞灵奠]] 丧仪链
- 与 [[路祭茶果]] 祭 **茶果** 并读

## 相关

- [[甄应嘉]] · [[贾政]] · [[奠茶饭]] · 第114回
""",
    ),
    (
        "dishes",
        {
            "id": "香菱扶正",
            "type": "custom",
            "name": "香菱扶正",
            "book": BOOK,
            "category": "扶正",
            "eaters": [],
            "location": "薛家",
            "first_appear": "第120回",
            "appear_in": ["第120回"],
            "tags": ["饮食", "扶正", "香菱", "薛家"],
            "summary": "第120回薛姨妈握薛蟠手，主张算香菱为媳妇、称大奶奶；众人称服，香菱急辩。",
        },
        """## 出处

第120回：薛姨妈「我便**算他是媳妇**了，你心里怎么样？」薛蟠点头；众人「便称起**大奶奶**来，无人不服。」香菱急道：「伏侍大爷一样的，何必如此。」

## 情节功能

- [[香菱]] **名分** 落定；与 [[情节-香菱之死]] 版本异文互参
- 薛家 **败落后** 人事收束

## 相关

- [[香菱]] · [[薛姨妈]] · [[薛蟠]] · [[夏金桂毒汤案]] · 第120回
""",
    ),
    (
        "medicines",
        {
            "id": "元春通关之剂",
            "type": "medicine",
            "name": "元春通关之剂",
            "book": BOOK,
            "category": "通关",
            "patient": "贾元春",
            "first_appear": "第95回",
            "appear_in": ["第95回"],
            "tags": ["医药", "通关", "元春", "宫闱"],
            "summary": "第95回元妃痰气壅塞、汤药不进，连用通关之剂不效，内官奏请预办后事。",
        },
        """## 出处

第95回：「竟至**痰气壅塞**，四肢厥冷……岂知**汤药不进**，连用**通关之剂**，并不见效。内官忧虑，奏请预办后事。」

## 情节功能

- **省亲—薨** 对称；贾府 **恩泽** 将尽
- 与 [[贾母参汤]] 临终、[[定心丸]] 宝玉 **医心** 并轴

## 相关

- [[贾元春]] · [[贾母]] · 第95回
""",
    ),
    (
        "medicines",
        {
            "id": "宝钗感邪发烧",
            "type": "medicine",
            "name": "宝钗感邪发烧",
            "book": BOOK,
            "category": "感邪",
            "patient": "薛宝钗",
            "first_appear": "第91回",
            "appear_in": ["第91回"],
            "tags": ["医药", "感邪", "宝钗", "金桂"],
            "summary": "第91回宝钗因金桂事苦劳至四更，次日发烧、汤水不进，满面通红身如燔灼，请医调治。",
        },
        """## 出处

第91回：「到底富家女子娇养惯的，心上又急，又苦劳了一会，**晚上就发烧**。到了明日，**汤水都吃不下**……只见宝钗**满面通红，身如燔灼**，话都不说。」

## 情节功能

- [[夏金桂]] 搅家 **连累**；荣宁两府惊动送 [[十香返魂丹]]
- 与 [[冷香丸]]「热毒」、[[宝钗散瘀丸]] 体质线

## 相关

- [[薛宝钗]] · [[夏金桂]] · [[十香返魂丹]] · 第91回
""",
    ),
    (
        "medicines",
        {
            "id": "十香返魂丹",
            "type": "medicine",
            "name": "十香返魂丹",
            "book": BOOK,
            "category": "丹剂",
            "patient": "薛宝钗",
            "first_appear": "第91回",
            "appear_in": ["第91回"],
            "tags": ["医药", "丹剂", "宝钗", "送药"],
            "summary": "第91回宝钗感邪发烧，凤姐打发人送十香返魂丹来，薛姨妈急用。",
        },
        """## 出处

第91回：「早惊动荣宁两府的人，先是**凤姐打发人送十香返魂丹**来，薛姨妈急用。」

## 情节功能

- [[宝钗感邪发烧]] **救急** 方；与 [[天王补心丹]]、[[真牛黄]] 名药并列
- 凤姐 **关切** 钗；金桂线 **外溢**

## 相关

- [[薛宝钗]] · [[王熙凤]] · [[宝钗感邪发烧]] · 第91回
""",
    ),
    (
        "medicines",
        {
            "id": "贾母消导发散",
            "type": "medicine",
            "name": "贾母消导发散",
            "book": BOOK,
            "category": "感冒",
            "patient": "贾母",
            "first_appear": "第109回",
            "appear_in": ["第109回"],
            "tags": ["医药", "感冒", "贾母", "消导"],
            "summary": "第109回贾母停饮食感风寒，大夫诊脉云略消导发散即可，开寻常药品；后渐不支。",
        },
        """## 出处

第109回：大夫诊脉——「有年纪的人停了些饮食，**感冒些风寒**，略**消导发散**些就好了。开了方子……知是**寻常药品**。」

## 情节功能

- [[贾母参汤]] **前奏**；与 [[食疗]]、[[净饿调养]] 食养对照 **末病**
- 宝玉 **欲梦黛玉** 同回 **神伤**

## 相关

- [[贾母]] · [[贾母参汤]] · [[食疗]] · 第109回 · 第110回
""",
    ),
    (
        "medicines",
        {
            "id": "妙玉闷香",
            "type": "medicine",
            "name": "妙玉闷香",
            "book": BOOK,
            "category": "迷香",
            "patient": "妙玉",
            "first_appear": "第112回",
            "appear_in": ["第112回"],
            "tags": ["医药", "迷香", "妙玉", "劫夺"],
            "summary": "第112回伙贼劫妙玉，带闷香熏住，轻薄后拖走；栊翠庵失玉。",
        },
        """## 出处

第112回：「伙贼……带了些**闷香**，跳上高墙……妙玉心中只是如醉如痴……被这强盗的**闷香熏住**，由着他掇弄了去了。」

## 情节功能

- [[妙玉]] **劫夺** 终局；与 [[玫瑰露]]、[[虎狼药]] 非常 **药物** 轴
- 园废 **盗匪** 与 [[抄家查茶器]] 末世并读

## 相关

- [[妙玉]] · [[栊翠庵]] · [[贾惜春]] · 第112回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    86: ["薛蟠当槽酒案"],
    88: ["南边糟东西", "南小菜"],
    91: ["宝钗感邪发烧", "十香返魂丹"],
    93: ["水月庵风月案"],
    95: ["元春通关之剂"],
    105: ["抄家查茶器"],
    109: ["贾母消导发散"],
    112: ["妙玉闷香"],
    114: ["甄应嘉祭礼"],
    120: ["香菱扶正"],
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
    print(f"[{BOOK}] patch food/medicine batch10 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
