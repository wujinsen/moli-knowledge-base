#!/usr/bin/env python3
"""红楼梦饮食·医药 ingest 第六批：年例锞子、中秋酒月、甄席、厨房馊豆腐、抄家席间与后段方药。"""
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
            "id": "风腌果子狸",
            "type": "dish",
            "name": "风腌果子狸",
            "book": BOOK,
            "category": "腌味",
            "eaters": ["林黛玉", "贾宝玉"],
            "location": "贾母上房",
            "first_appear": "第75回",
            "appear_in": ["第75回"],
            "tags": ["饮食", "野味", "贾母"],
            "summary": "第75回贾母用膳，吩咐将风腌果子狸与笋送黛玉、宝玉；同红稻米粥、甄家阴影同席。",
        },
        """## 出处

第75回：贾母吃 [[红稻米粥]] 后，「又指着这一碗笋和这一盘**风腌果子狸**给颦儿宝玉两个吃去」。

## 情节功能

- 第75回 **家宴分派** 写贾母疼黛玉宝玉
- 与 [[风腌笋]] 并提；野味 plausible_qing

## 相关

- [[贾母]] · [[林黛玉]] · [[贾宝玉]] · [[红稻米粥]] · 第75回
""",
    ),
    (
        "dishes",
        {
            "id": "风腌笋",
            "type": "dish",
            "name": "风腌笋",
            "book": BOOK,
            "category": "腌味",
            "eaters": ["林黛玉", "贾宝玉"],
            "location": "贾母上房",
            "first_appear": "第75回",
            "appear_in": ["第75回"],
            "tags": ["饮食", "笋", "贾母"],
            "summary": "第75回贾母分膳：这一碗笋与风腌果子狸一并送黛玉、宝玉。",
        },
        """## 出处

第75回：同 [[风腌果子狸]]——「这一碗**笋**和这一盘风腌果子狸给颦儿宝玉两个吃去」。

## 相关

- [[风腌果子狸]] · [[红稻米粥]] · [[贾母]] · 第75回
""",
    ),
    (
        "dishes",
        {
            "id": "押岁锞子",
            "type": "dish",
            "name": "押岁锞子",
            "book": BOOK,
            "category": "年例",
            "eaters": ["尤氏", "贾珍"],
            "location": "宁国府",
            "occasion": "腊月年例",
            "first_appear": "第53回",
            "appear_in": ["第53回"],
            "tags": ["饮食", "年例", "恩赏"],
            "summary": "第53回腊月，尤氏收押岁锞子，碎金倾成梅花、海棠、笔锭如意、八宝联春等式样。",
        },
        """## 出处

第53回：「丫头捧了一茶盘**押岁锞子**进来……碎金子共是一百五十三两六钱七分……也有梅花式的，也有海棠式的，也有笔锭如意的，也有八宝联春的。」

## 情节功能

- [[元宵年例链]] / [[年例]] 经济—礼仪节点
- 与 [[宗祠祭祖]]、[[乌进孝]] 交租同回

## 相关

- [[尤氏]] · [[贾珍]] · [[年例]] · [[元宵年例链]] · 第53回
""",
    ),
    (
        "dishes",
        {
            "id": "枣儿粳米粥",
            "type": "dish",
            "name": "枣儿粳米粥",
            "book": BOOK,
            "category": "粥",
            "eaters": ["贾母", "王夫人"],
            "location": "宁荣两府",
            "occasion": "元宵夜宴",
            "first_appear": "第54回",
            "appear_in": ["第54回"],
            "tags": ["饮食", "粥", "元宵"],
            "summary": "第54回元宵夜，凤姐预备鸭子肉粥，贾母要清淡，另有枣儿熬的粳米粥给太太们吃斋。",
        },
        """## 出处

第54回：凤姐预备 [[鸭子肉粥]]，贾母要清淡；凤姐道：「也有**枣儿熬的粳米粥**，预备太太们吃斋的。」

## 相关

- [[鸭子肉粥]] · [[杏仁茶]] · [[元宵夜宴]] · 第54回
""",
    ),
    (
        "dishes",
        {
            "id": "中秋热酒",
            "type": "dish",
            "name": "中秋热酒",
            "book": BOOK,
            "category": "酒",
            "eaters": ["贾母", "王夫人", "邢夫人", "尤氏"],
            "location": "凸碧堂",
            "occasion": "中秋赏月",
            "first_appear": "第76回",
            "appear_in": ["第76回"],
            "tags": ["饮食", "中秋", "酒"],
            "summary": "第76回凸碧堂中秋，贾母命拿大杯斟热酒，邢夫人等换大杯陪饮；后换暖酒、笛声佐月。",
        },
        """## 出处

第76回：贾母「不觉长叹一声，遂命拿大杯来**斟热酒**」；「你们也换大杯才是」；后又「入席换**暖酒**来」。

## 情节功能

- [[凸碧堂赏月]] 盛时将尽之感；凤姐、李纨病缺
- 与 [[凸碧堂月饼]] 同场

## 相关

- [[贾母]] · [[尤氏]] · [[凸碧堂月饼]] · 第76回
""",
    ),
    (
        "dishes",
        {
            "id": "凸碧堂月饼",
            "type": "dish",
            "name": "凸碧堂月饼",
            "book": BOOK,
            "category": "节令",
            "eaters": ["贾母", "邢夫人", "尤氏"],
            "location": "凸碧堂",
            "occasion": "中秋赏月",
            "first_appear": "第76回",
            "appear_in": ["第76回"],
            "tags": ["饮食", "中秋", "月饼"],
            "summary": "第76回中秋，贾母命将月饼、西瓜果品搬至阶上，丫头媳妇围坐赏月。",
        },
        """## 出处

第76回：「命将**月饼**西瓜果品等类都叫搬下去，令丫头媳妇们也都团团围坐赏月。」

## 情节功能

- 与 [[中秋热酒]]、笛声、贾赦绊腿并置
- 后文 [[凸碧堂联诗]] 悲音

## 相关

- [[中秋热酒]] · [[贾母]] · 第76回
""",
    ),
    (
        "dishes",
        {
            "id": "甄夫人席",
            "type": "banquet",
            "name": "甄夫人席",
            "book": BOOK,
            "category": "宴请",
            "eaters": ["贾宝玉", "王夫人", "甄夫人"],
            "location": "甄家",
            "first_appear": "第57回",
            "appear_in": ["第57回"],
            "tags": ["饮食", "甄家", "宝玉"],
            "summary": "第57回王夫人带宝玉拜甄夫人，甄夫人留席竟日；晚间王夫人又预备上等席面、名班大戏请甄夫人母女。",
        },
        """## 出处

第57回：「甄夫人**留席**，竟日方回」；「王夫人又吩咐预备**上等的席面**，定名班大戏，请过甄夫人母女。」

## 情节功能

- **甄宝玉** 对照真玉；后文抄家伏笔（inference）
- 同回紫鹃拒宝玉、雪雁取人参

## 相关

- [[贾宝玉]] · [[王夫人]] · [[甄宝玉]] · 第57回
""",
    ),
    (
        "dishes",
        {
            "id": "馊豆腐",
            "type": "dish",
            "name": "馊豆腐",
            "book": BOOK,
            "category": "膳",
            "eaters": ["贾迎春", "司棋"],
            "location": "大观园厨房",
            "first_appear": "第61回",
            "appear_in": ["第61回"],
            "tags": ["饮食", "厨房", "司棋"],
            "summary": "第61回司棋要炖嫩鸡蛋，柳家言鸡蛋短；莲花儿记前儿豆腐弄馊了被说一顿。",
        },
        """## 出处

第61回：莲花儿道：「前儿要吃豆腐，你弄了些**馊的**，叫他说了我一顿。今儿要鸡蛋又没有了。」

## 情节功能

- [[投鼠忌器链]] / 小厨房 **权力与质量** 冲突
- 与 [[炖嫩鸡蛋]]、[[茯苓霜]] 同链

## 相关

- [[司棋]] · [[贾迎春]] · [[炖嫩鸡蛋]] · [[投鼠忌器链]] · 第61回
""",
    ),
    (
        "dishes",
        {
            "id": "抄家席间",
            "type": "banquet",
            "name": "抄家席间",
            "book": BOOK,
            "category": "宴席",
            "eaters": ["贾政", "贾赦", "亲友"],
            "location": "荣禧堂",
            "occasion": "查抄",
            "first_appear": "第105回",
            "appear_in": ["第105回"],
            "tags": ["饮食", "抄家", "败落"],
            "summary": "第105回贾政设宴请酒，锦衣府赵堂官、西平郡王至，「满堂中筵席未散」即奉旨查抄。",
        },
        """## 出处

第105回：「贾政正在那里**设宴请酒**」；西平王：「如今**满堂中筵席未散**，想有亲友在此未便，且请众位府上亲友各散。」

## 情节功能

- [[末世看园链]] **盛—败** 临界点；宴饮与查抄并置
- 后文封园、[[包勇]] 看园

## 相关

- [[贾政]] · [[贾赦]] · [[末世看园链]] · 第105回
""",
    ),
    (
        "medicines",
        {
            "id": "归肺固金汤",
            "type": "prescription",
            "name": "归肺固金汤",
            "book": BOOK,
            "category": "汤剂",
            "patient": "林黛玉",
            "physician": "王太医",
            "first_appear": "第83回",
            "appear_in": ["第83回"],
            "tags": ["方剂", "黛玉", "积郁"],
            "summary": "第83回王太医诊黛玉积郁，方意黑逍遥开其先，复用归肺固金继其后；忌骤施补剂。",
        },
        """## 出处

第83回：「姑拟 [[黑逍遥方]] 以开其先，复用**归肺固金**以继其后。」

## 情节功能

- [[黛玉积郁脉案]] 方药后半；与第97回急变链
- 后段详脉、医理

## 相关

- [[林黛玉]] · [[黛玉积郁脉案]] · [[黑逍遥方]] · [[鳖血拌柴胡]] · 第83回
""",
    ),
    (
        "medicines",
        {
            "id": "鳖血拌柴胡",
            "type": "prescription",
            "name": "鳖血拌柴胡",
            "book": BOOK,
            "category": "炮制法",
            "patient": "林黛玉",
            "physician": "王太医",
            "first_appear": "第83回",
            "appear_in": ["第83回"],
            "tags": ["医药", "黛玉", "柴胡"],
            "summary": "第83回贾琏问血势上冲柴胡是否使得，王太医释须用鳖血拌炒，制其升性。",
        },
        """## 出处

第83回：贾琏问「血势上冲，**柴胡**使得么？」王太医道：「柴胡升散，恐助血势。必用**鳖血拌炒**，制其升性。」

## 情节功能

- [[黛玉积郁脉案]] **医理细节**；写王太医非混饭
- 与 [[归肺固金汤]] 同方

## 相关

- [[林黛玉]] · [[黛玉积郁脉案]] · [[王太医诊晴雯]] · 第83回
""",
    ),
    (
        "medicines",
        {
            "id": "伤后薄汤",
            "type": "prescription",
            "name": "伤后薄汤",
            "book": BOOK,
            "category": "病养",
            "patient": "贾宝玉",
            "first_appear": "第34回",
            "appear_in": ["第34回"],
            "tags": ["病养", "宝玉", "打板"],
            "summary": "第34回宝玉挨贾政板子后，至掌灯时分只喝了两口汤，便昏昏睡去；同回宝钗送散瘀丸。",
        },
        """## 出处

第34回：「至掌灯时分，宝玉**只喝了两口汤**，便昏昏沉沉的睡去。」（同回 [[宝钗散瘀丸]] 外敷。）

## 情节功能

- 打板后 **饮食锐减** 与 [[宝钗散瘀丸]] 并写
- 周瑞媳妇等探视同段

## 相关

- [[贾宝玉]] · [[宝钗散瘀丸]] · [[薛宝钗]] · 第34回
""",
    ),
]

CHAPTER_ITEMS_ADD: dict[int, list[str]] = {
    34: ["伤后薄汤"],
    53: ["押岁锞子"],
    54: ["枣儿粳米粥"],
    57: ["甄夫人席"],
    61: ["馊豆腐"],
    75: ["风腌果子狸", "风腌笋"],
    76: ["中秋热酒", "凸碧堂月饼"],
    83: ["归肺固金汤", "鳖血拌柴胡"],
    105: ["抄家席间"],
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
    print(f"[{BOOK}] patch food/medicine batch6 …")
    created = sum(1 for kind, fm, body in NEW_ITEMS if write_item(kind, fm, body))
    ch = merge_chapter_items()
    print(f"  新建 {created} 页 · 回目回填 {ch}")


if __name__ == "__main__":
    main()
