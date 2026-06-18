#!/usr/bin/env python3
"""Match chapter bodies against known character ids/aliases; fill empty characters[]."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _common import CHAPTER_DIR, iter_characters

# Common narrative forms not always listed in entity aliases (alias -> id)
BOOK_EXTRA_ALIASES: dict[str, dict[str, str]] = {
    "红楼梦": {
    "凤姐儿": "王熙凤",
    "凤姐": "王熙凤",
    "凤丫头": "王熙凤",
    "凤哥儿": "王熙凤",
    "琏二奶奶": "王熙凤",
    "黛玉": "林黛玉",
    "林妹妹": "林黛玉",
    "林姑娘": "林黛玉",
    "宝姑娘": "薛宝钗",
    "宝钗": "薛宝钗",
    "宝玉": "贾宝玉",
    "宝二爷": "贾宝玉",
    "薛大哥": "薛蟠",
    "呆霸王": "薛蟠",
    "可卿": "秦可卿",
    "湘云": "史湘云",
    "探春": "贾探春",
    "三姑娘": "贾探春",
    "迎春": "贾迎春",
    "二姑娘": "贾迎春",
    "惜春": "贾惜春",
    "四姑娘": "贾惜春",
    "元春": "贾元春",
    "环哥儿": "贾环",
    "环儿": "贾环",
    "兰哥儿": "贾兰",
    "岫烟": "邢岫烟",
    "智能儿": "智能",
    "来旺媳妇": "来旺家的",
    "来旺妇": "来旺家的",
    "周瑞媳妇": "周瑞家的",
    "周嫂子": "周瑞家的",
    "鲍二媳妇": "鲍二家的",
    "鲍二老婆": "鲍二家的",
    "芸哥儿": "贾芸",
    "芸二爷": "贾芸",
    "琏二爷": "贾琏",
    "琏哥": "贾琏",
    "珍大爷": "贾珍",
    "蓉哥儿": "贾蓉",
    "大老爷": "贾赦",
    "二老爷": "贾政",
    "老祖宗": "贾母",
    "史太君": "贾母",
    "太太": "王夫人",
    "大太太": "邢夫人",
    "薛姨妈": "薛姨妈",
    "姨太太": "薛姨妈",
    "醉金刚": "倪二",
    "冷二郎": "柳湘莲",
    "琪官": "蒋玉菡",
    "鲸卿": "秦钟",
    "秦鲸卿": "秦钟",
    "红玉": "小红",
    "林红玉": "小红",
    "黄金莺": "莺儿",
    "来旺儿": "旺儿",
    "来旺": "旺儿",
    "赖总管": "赖大",
    "林之孝家": "林之孝",
    "狗儿": "王狗儿",
    "詹子亮": "詹光",
    "大姐儿": "巧姐",
    "巧哥儿": "巧姐",
    "焙茗": "茗烟",
    "瑞大爷": "贾瑞",
    "金钏": "金钏儿",
        "多浑虫": "多官",
        "北静郡王": "北静王",
        "水溶": "北静王",
        "冯公子": "冯渊",
        "金相公": "金荣",
        "南安王": "南安郡王",
        "夏太监": "夏守忠",
        "夏老爷": "夏守忠",
        "西宁王": "西宁郡王",
    },
    "西游记": {
        "悟空": "孙悟空",
        "行者": "孙悟空",
        "孙行者": "孙悟空",
        "齐天大圣": "孙悟空",
        "美猴王": "孙悟空",
        "猴王": "孙悟空",
        "三藏": "唐僧",
        "玄奘": "唐僧",
        "唐三藏": "唐僧",
        "陈玄奘": "唐僧",
        "八戒": "猪八戒",
        "悟能": "猪八戒",
        "天蓬元帅": "猪八戒",
        "沙和尚": "沙僧",
        "悟净": "沙僧",
        "卷帘大将": "沙僧",
        "观音": "观音菩萨",
        "观世音": "观音菩萨",
        "玉帝": "玉皇大帝",
        "如来": "如来佛祖",
        "世尊": "如来佛祖",
        "太宗": "唐太宗",
        "李世民": "唐太宗",
        "唐王": "唐太宗",
        "龙王": "东海龙王",
        "敖广": "东海龙王",
        "二郎": "二郎神",
        "杨戬": "二郎神",
        "显圣真君": "二郎神",
        "李天王": "李靖",
        "托塔天王": "李靖",
        "三太子": "哪吒",
        "哪吒三太子": "哪吒",
        "镇元子": "镇元子",
        "地仙之祖": "镇元子",
        "牛魔王": "牛魔王",
        "平天大圣": "牛魔王",
        "铁扇仙": "铁扇公主",
        "罗刹女": "铁扇公主",
        "铁扇公主": "铁扇公主",
        "圣婴大王": "红孩儿",
        "红孩儿": "红孩儿",
        "尸魔": "白骨精",
        "白骨夫人": "白骨精",
        "黄风怪": "黄风怪",
        "黄风大圣": "黄风怪",
        "熊罴怪": "黑熊精",
        "黑熊精": "黑熊精",
        "金角大王": "金角大王",
        "银角大王": "银角大王",
        "混世魔王": "混世魔王",
        "狮猁怪": "狮猁怪",
        "灵感大王": "灵感大王",
        "独角兕大王": "青牛精",
        "青牛精": "青牛精",
        "兕大王": "青牛精",
        "黄眉怪": "黄眉怪",
        "黄眉童儿": "黄眉怪",
        "赛太岁": "赛太岁",
        "青狮精": "青狮精",
        "白象精": "白象精",
        "大鹏精": "大鹏精",
        "大鹏金翅雕": "大鹏精",
        "蜘蛛精": "蜘蛛精",
        "百眼魔君": "百眼魔君",
        "蜈蚣精": "百眼魔君",
        "如意真仙": "如意真仙",
        "老君": "太上老君",
        "太上老君": "太上老君",
        "灵吉菩萨": "灵吉菩萨",
        "六耳猕猴": "六耳猕猴",
        "假悟空": "六耳猕猴",
        "黄袍怪": "奎木狼",
        "黄袍": "奎木狼",
        "黄袍郎": "奎木狼",
        "奎木狼": "奎木狼",
        "奎星": "奎木狼",
        "蝎子精": "蝎子精",
        "女儿国国王": "女儿国国王",
        "西梁女王": "女儿国国王",
        "女王陛下": "女儿国国王",
        "女王": "女儿国国王",
        "鼍龙": "鼍龙",
        "鼍怪": "鼍龙",
        "虎力大仙": "虎力大仙",
        "鹿力大仙": "鹿力大仙",
        "羊力大仙": "羊力大仙",
        "虎力": "虎力大仙",
        "鹿力": "鹿力大仙",
        "羊力": "羊力大仙",
        "玉面公主": "玉面公主",
        "玉面狐狸": "玉面公主",
        "九头虫": "九头虫",
        "九头驸马": "九头虫",
        "万圣龙王": "万圣龙王",
        "万圣老龙": "万圣龙王",
        "白鹿精": "白鹿精",
        "国丈": "白鹿精",
        "地涌夫人": "地涌夫人",
        "金鼻白毛老鼠精": "地涌夫人",
        "半截观音": "地涌夫人",
        "玉兔精": "玉兔精",
        "假公主": "玉兔精",
        "九灵元圣": "九灵元圣",
        "九头狮子": "九灵元圣",
        "黄狮精": "黄狮精",
        "孙黄狮": "黄狮精",
        "辟寒大王": "辟寒大王",
        "辟暑大王": "辟暑大王",
        "辟尘大王": "辟尘大王",
    },
    "金瓶梅": {
        "西门大官人": "西门庆",
        "大官人": "西门庆",
        "月娘": "吴月娘",
        "月姐": "吴月娘",
        "吴氏": "吴月娘",
        "五娘": "潘金莲",
        "潘氏": "潘金莲",
        "六娘": "李瓶儿",
        "瓶儿": "李瓶儿",
        "三娘": "孟玉楼",
        "二娘": "孙雪娥",
        "春梅": "庞春梅",
        "应二哥": "应伯爵",
        "花二哥": "花子虚",
        "花子虚": "花子虚",
        "玳安儿": "玳安",
        "玳安": "玳安",
        "来兴儿": "来旺",
        "韩道国": "韩道国",
        "陈敬济": "陈经济",
        "敬济": "陈经济",
        "蔡太师": "蔡京",
        "翟管家": "翟管家",
        "李智": "李智",
        "谢希大": "谢希大",
        "子纯": "谢希大",
        "应花子": "应伯爵",
        "应伯爵": "应伯爵",
        # 张竹坡评本繁体
        "西門慶": "西门庆",
        "西門大官人": "西门庆",
        "吳月娘": "吴月娘",
        "月姐": "吴月娘",
        "應伯爵": "应伯爵",
        "應二哥": "应伯爵",
        "應花子": "应伯爵",
        "謝希大": "谢希大",
        "玳安兒": "玳安",
        "花子虛": "花子虚",
        "花二哥": "花子虚",
        "李瓶兒": "李瓶儿",
        "六娘": "李瓶儿",
        "陳敬濟": "陈经济",
        "敬濟": "陈经济",
        "武二郎": "武松",
        "武大郎": "武大郎",
        "李嬌兒": "李娇儿",
        "潘金蓮": "潘金莲",
        "龐春梅": "庞春梅",
        "孟玉樓": "孟玉楼",
        "孫雪娥": "孙雪娥",
        "韓道國": "韩道国",
    },
}

# backward compat
EXTRA_ALIASES = BOOK_EXTRA_ALIASES["红楼梦"]

# Skip overly short / ambiguous aliases when scanning
MIN_ALIAS_LEN = 2
# Too ambiguous for substring auto-tag (keep on entity pages for manual use)
SKIP_ALIASES = frozenset({"老爷", "太太", "姑娘", "奶奶"})


def build_alias_map(book: str) -> list[tuple[str, str]]:
    """Return (alias, id) pairs sorted by alias length descending."""
    pairs: dict[str, str] = {}
    for _, fm, _ in iter_characters(book):
        cid = fm.get("id") or fm.get("name")
        if not cid:
            continue
        names = [cid, fm.get("name", "")]
        names.extend(fm.get("aliases") or [])
        for n in names:
            n = (n or "").strip()
            if len(n) >= MIN_ALIAS_LEN and n not in SKIP_ALIASES:
                pairs.setdefault(n, cid)
    for alias, cid in BOOK_EXTRA_ALIASES.get(book, {}).items():
        if len(alias) >= MIN_ALIAS_LEN and alias not in SKIP_ALIASES:
            pairs.setdefault(alias, cid)
    return sorted(pairs.items(), key=lambda x: (-len(x[0]), x[0]))


def split_body(raw: str) -> str:
    """Return markdown body without parsing YAML (tolerates bad frontmatter)."""
    m = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)$", raw, re.S)
    return m.group(1) if m else raw


def strip_html(body: str) -> str:
    # Drop side/head comments before matching (not story text)
    text = re.sub(r'<span class="zhipi">.*?</span>', "", body, flags=re.S)
    text = re.sub(r'<span class="zhupi"[^>]*>.*?</span>', "", body, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&quot;", '"').replace("&#x27;", "'")
    return text


# alias -> compound phrases where the alias must not match as substring
ALIAS_BLOCK: dict[str, list[str]] = {
    "宝玉": ["通灵宝玉"],
    "鸳鸯": ["卧鸳鸯"],
    "黄袍": ["赭黄袍", "飞龙舞凤赭黄袍", "淡黄袍"],
}


def alias_in_text(text: str, alias: str) -> int:
    """Return first valid start index of alias in text, or -1."""
    start = 0
    blocks = ALIAS_BLOCK.get(alias, [])
    while True:
        idx = text.find(alias, start)
        if idx < 0:
            return -1
        blocked = False
        for compound in blocks:
            cidx = text.find(compound)
            while cidx >= 0:
                if cidx <= idx < cidx + len(compound):
                    blocked = True
                    break
                cidx = text.find(compound, cidx + 1)
        if not blocked:
            return idx
        start = idx + 1


def find_characters(text: str, alias_pairs: list[tuple[str, str]]) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    positions: dict[str, int] = {}
    for alias, cid in alias_pairs:
        if cid in seen:
            continue
        idx = alias_in_text(text, alias)
        if idx >= 0:
            seen.add(cid)
            positions[cid] = idx
            found.append(cid)
    found.sort(key=lambda c: positions[c])
    return found


def format_characters_line(chars: list[str]) -> str:
    if not chars:
        return "characters: []"
    return f"characters: [{', '.join(chars)}]"


def merge_char_lists(existing: list[str], detected: list[str]) -> list[str]:
    """Union: body appearance order first, then any frontmatter-only ids."""
    out = list(detected)
    for cid in existing:
        if cid not in out:
            out.append(cid)
    return out


def patch_frontmatter(raw: str, chars: list[str], *, force: bool = False, merge: bool = False) -> str | None:
    if merge:
        existing: list[str] = []
        m = re.search(r"^characters:\s*\[(.*?)\]\s*$", raw, re.M | re.S)
        block = re.search(r"^characters:\s*\n((?:[ \t]*-[ \t].+\n?)+)", raw, re.M)
        if m:
            inner = m.group(1).strip()
            if inner:
                existing = re.findall(r"[\u4e00-\u9fff]+", inner)
        elif block:
            for line in block.group(1).splitlines():
                line = line.strip()
                if line.startswith("- "):
                    item = line[2:].strip().strip('"').strip("'")
                    if item:
                        existing.append(item)
        chars = merge_char_lists(existing, chars)
        line = format_characters_line(chars)
        if m:
            return re.sub(r"^characters:\s*\[.*\]\s*$", line, raw, count=1, flags=re.M)
        if block:
            return re.sub(
                r"^characters:\s*\n((?:[ \t]*-[ \t].+\n?)+)",
                line + "\n",
                raw,
                count=1,
                flags=re.M,
            )
        return None
    if force:
        if not re.search(r"^characters:\s*\[.*\]\s*$", raw, re.M):
            return None
        line = format_characters_line(chars)
        return re.sub(r"^characters:\s*\[.*\]\s*$", line, raw, count=1, flags=re.M)
    if not re.search(r"^characters:\s*\[\]\s*$", raw, re.M):
        return None
    line = format_characters_line(chars)
    return re.sub(r"^characters:\s*\[\]\s*$", line, raw, count=1, flags=re.M)


def iter_chapter_files(book: str, subdir: str | None) -> list[Path]:
    base = CHAPTER_DIR / book
    if subdir:
        base = base / subdir
    return sorted(base.glob("[0-9]*.md"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Fill empty chapter characters[] from body text")
    ap.add_argument("book", nargs="?", default="红楼梦")
    ap.add_argument("--subdir", default="", help='e.g. "脂砚斋本"; default = 程高本 root')
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Overwrite existing non-empty characters[]")
    ap.add_argument("--merge", action="store_true", help="Merge detected ids into existing characters[]")
    ap.add_argument("--files", nargs="*", help="Only process these basenames (e.g. 001.md)")
    ap.add_argument("--to-chapter", type=int, default=0, help="Only process NNN.md where number <= this")
    ap.add_argument("--from-chapter", type=int, default=0, help="Only process NNN.md where number >= this")
    ap.add_argument("--min-chars", type=int, default=1, help="Min matches to write (default 1)")
    args = ap.parse_args()

    alias_pairs = build_alias_map(args.book)
    paths = iter_chapter_files(args.book, args.subdir or None)
    updated = skipped = empty_still = 0

    for path in paths:
        if args.files and path.name not in args.files:
            continue
        if args.to_chapter:
            try:
                if int(path.stem) > args.to_chapter:
                    continue
            except ValueError:
                pass
        if args.from_chapter:
            try:
                if int(path.stem) < args.from_chapter:
                    continue
            except ValueError:
                pass
        raw = path.read_text(encoding="utf-8")
        is_empty = bool(re.search(r"^characters:\s*\[\]\s*$", raw, re.M))
        if not is_empty and not args.force and not args.merge:
            skipped += 1
            continue
        body = split_body(raw)
        text = strip_html(body)
        chars = find_characters(text, alias_pairs)
        if len(chars) < args.min_chars:
            if args.force and not is_empty:
                new_raw = patch_frontmatter(raw, [], force=True)
                if new_raw and not args.dry_run:
                    path.write_text(new_raw, encoding="utf-8")
                if new_raw:
                    updated += 1
                    if args.dry_run:
                        print(f"  {path.name}: (cleared, no KB match)")
            else:
                empty_still += 1
                if args.dry_run:
                    print(f"  {path.name}: (no match)")
            continue
        new_raw = patch_frontmatter(
            raw, chars, force=args.force and not args.merge, merge=args.merge
        )
        if not new_raw:
            continue
        if args.dry_run:
            print(f"  {path.name}: {len(chars)} -> {chars[:8]}{'...' if len(chars) > 8 else ''}")
        else:
            path.write_text(new_raw, encoding="utf-8")
        updated += 1

    label = args.subdir or "程高本"
    print(f"[{args.book}/{label}] updated {updated}, skipped {skipped}, still empty {empty_still}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
