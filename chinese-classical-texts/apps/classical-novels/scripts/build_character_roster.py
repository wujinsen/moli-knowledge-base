#!/usr/bin/env python3
"""从回目原文抽取「提及但未建页」人物，写入 src/data/<slug>.character_roster.json。

策略：
  1. 读取 seed 名单（data/<slug>.pending_characters.seed.json，可人工增补）
  2. 从全书正文按叙事句式自动发现（打死/名唤/又称…）并去重
  3. 在程高本/主版本回目中检索出现回次

用法: python scripts/build_character_roster.py [书名...]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from _common import BOOKS, CHAPTER_DIR, CONTENT, DATA_DIR, iter_characters
from tag_chapter_characters import BOOK_EXTRA_ALIASES, split_body, strip_html

BOOK_SLUG = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}

# 严格叙事句式（自动发现）；宽句式噪声大，不启用
DISCOVER_PATTERNS = [
    re.compile(r"打死([\u4e00-\u9fff]{2,4})"),
    re.compile(r"杀了([\u4e00-\u9fff]{2,4})"),
    re.compile(r"名唤([\u4e00-\u9fff]{2,4})"),
    re.compile(r"名叫([\u4e00-\u9fff]{2,4})"),
    re.compile(r"小名([\u4e00-\u9fff]{2,4})"),
]

STOP_NAMES = frozenset(
    {
        "今日", "明日", "昨日", "此时", "彼时", "这里", "那里", "什么", "怎么", "为何",
        "因此", "于是", "原来", "果然", "只见", "听说", "众人", "大家", "老爷", "太太",
        "奶奶", "姑娘", "丫头", "哥儿", "姐儿", "小子", "婆子", "媳妇", "母亲", "父亲",
        "兄弟", "姐妹", "一面", "一时", "一句", "一声", "一回", "一头", "一阵", "一起",
        "一边", "一个", "一位", "一名", "自己", "他们", "她们", "我们", "你们", "人家",
        "别人", "如此", "这般", "那样", "这样", "不可", "不能", "不敢", "不觉", "不知",
        "太爷", "太君", "一体", "一头", "一句", "一声", "一回", "一头", "一阵", "一起",
        "一边", "如今", "彼时", "先前", "后来", "方才", "正在", "已是", "已是", "却是",
        "却是", "只是", "不过", "便是", "就是", "却是", "却是", "通灵宝玉", "大观园",
        "荣国府", "宁国府", "护官符", "葫芦庙", "太虚幻境", "西门庆", "潘金莲",
        "孙悟空", "猪八戒", "唐僧", "沙僧", "观音菩萨", "怎么", "什么", "这样", "那样",
        "这边", "那边", "一体", "一体", "知道", "不知", "听见", "听说", "说道", "笑道",
        "答应", "忙道", "便道", "又道", "只道", "因道", "且道", "如何", "为何", "多少",
        "若干", "多少", "几个", "这些", "那些", "这个", "那个", "每人", "各人", "各自",
        "大家", "众人", "众位", "各位", "二位", "三位", "四位", "五位", "六位", "一位",
        "两位", "三位", "四位", "五位", "六位", "一位", "两位", "三位", "四位", "五位",
    }
)


def known_ids(book: str) -> set[str]:
    ids: set[str] = set()
    for _, fm, _ in iter_characters(book):
        cid = fm.get("id") or fm.get("name") or ""
        if cid:
            ids.add(cid)
        name = fm.get("name") or ""
        if name:
            ids.add(name)
        for a in fm.get("aliases") or []:
            if a:
                ids.add(a)
    for alias, cid in BOOK_EXTRA_ALIASES.get(book, {}).items():
        ids.add(alias)
        ids.add(cid)
    return ids


def load_seed(book: str) -> list[dict]:
    slug = BOOK_SLUG.get(book, book)
    path = DATA_DIR / f"{slug}.pending_characters.seed.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return [x if isinstance(x, dict) else {"name": x} for x in data]
    return data.get("names", [])


def iter_main_chapters(book: str) -> list[tuple[int, Path]]:
    base = CHAPTER_DIR / book
    if book == "金瓶梅":
        sub = base / "崇祯本"
        if sub.is_dir():
            base = sub
    out: list[tuple[int, Path]] = []
    for p in sorted(base.glob("[0-9]*.md")):
        try:
            out.append((int(p.stem), p))
        except ValueError:
            pass
    return out


def _is_candidate(name: str, known: set[str]) -> bool:
    if not name or len(name) < 2 or len(name) > 4:
        return False
    if name in known or name in STOP_NAMES:
        return False
    if any(name in k or k in name for k in known if 2 <= len(k) <= 4 and k != name):
        return False
    return True


def discover_from_prose(book: str, known: set[str]) -> set[str]:
    """从人物页 / 回目 / 事件正文按叙事句式发现未建页专名。"""
    found: set[str] = set()
    roots = [
        CONTENT / "characters" / book,
        CONTENT / "events" / book,
        CONTENT / "topics" / book,
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.glob("*.md"):
            text = p.read_text(encoding="utf-8-sig")
            body = split_body(text)
            _collect_names(body, known, found)

    for _, path in iter_main_chapters(book):
        text = strip_html(split_body(path.read_text(encoding="utf-8-sig")))
        _collect_names(text, known, found)
    surnames = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴鬱胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东殴殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公"
    return {n for n in found if n[0] in surnames or len(n) >= 3}


def _collect_names(text: str, known: set[str], found: set[str]) -> None:
    for pat in DISCOVER_PATTERNS:
        for m in pat.finditer(text):
            name = m.group(1)
            if _is_candidate(name, known):
                found.add(name)


def scan_name_in_chapters(book: str, name: str) -> set[int]:
    hits: set[int] = set()
    for ch, path in iter_main_chapters(book):
        text = strip_html(split_body(path.read_text(encoding="utf-8-sig")))
        if name in text:
            hits.add(ch)
    return hits


def chapter_labels(chapters: list[int]) -> list[str]:
    return [f"第{n}回" for n in sorted(chapters)]


def build_roster(book: str, *, discover: bool = False) -> dict:
    known = known_ids(book)
    paged_count = len({fm.get("id") for _, fm, _ in iter_characters(book) if fm.get("id")})

    seeds = load_seed(book)
    seed_map = {s["name"]: s for s in seeds if s.get("name")}

    discovered: set[str] = discover_from_prose(book, known) if discover else set()
    all_names = set(seed_map) | discovered

    pending_map: dict[str, dict] = {}
    for name in sorted(all_names):
        if name in known:
            continue
        chapters = sorted(scan_name_in_chapters(book, name))
        is_seed = name in seed_map
        if not chapters and not is_seed:
            continue
        entry: dict = {
            "name": name,
            "mentions": len(chapters),
            "chapters": chapters,
            "appear_in": chapter_labels(chapters),
            "source": "seed" if is_seed else "extracted",
        }
        seed = seed_map.get(name, {})
        if seed.get("note"):
            entry["note"] = seed["note"]
        if seed.get("aliases"):
            entry["aliases"] = seed["aliases"]
        pending_map[name] = entry

    pending = sorted(pending_map.values(), key=lambda x: (-x["mentions"], x["name"]))
    return {
        "book": book,
        "generated": date.today().isoformat(),
        "paged_count": paged_count,
        "pending_count": len(pending),
        "pending": pending,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("books", nargs="*", default=BOOKS)
    ap.add_argument("--discover", action="store_true", help="合并叙事句式自动发现（噪声较多，供审阅）")
    args = ap.parse_args()
    for book in args.books:
        if book not in BOOKS:
            print(f"skip unknown book: {book}", file=sys.stderr)
            continue
        slug = BOOK_SLUG[book]
        payload = build_roster(book, discover=args.discover)
        out = DATA_DIR / f"{slug}.character_roster.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[{book}] paged={payload['paged_count']} pending={payload['pending_count']} -> {out.name}")
        for p in payload["pending"][:8]:
            ch = ",".join(p["appear_in"][:3])
            print(f"  · {p['name']} ({p['mentions']}回) {ch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
