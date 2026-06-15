#!/usr/bin/env python3
"""One-off audit: 红楼梦全书人物 vs 现有人物页，含版本对比。"""
from __future__ import annotations

import json
import re
import yaml
from collections import defaultdict
from pathlib import Path

from _common import CHAPTER_DIR, DATA_DIR, iter_characters
from tag_chapter_characters import (
    BOOK_EXTRA_ALIASES,
    build_alias_map,
    find_characters,
    split_body,
    strip_html,
)
from tag_chapter_meta import parse_list_field

BOOK = "红楼梦"

# 红学常见待建人物 seed（无 seed 文件时用）
MANUAL_SEED = [
    {"name": "金荣", "note": "第9回家塾争闹"},
    {"name": "菂官", "note": "第58回藕官祭友，已故小旦"},
    {"name": "冯渊", "note": "第4回争买英莲被薛蟠打死"},
    {"name": "甄宝玉", "note": "第56/57/115/116回，程高本后四十回"},
    {"name": "甄夫人", "note": "第57回甄家来访"},
    {"name": "香怜", "note": "第9回家塾，与金荣争闹"},
    {"name": "玉爱", "note": "第9回家塾"},
    {"name": "扫红", "note": "宝玉小厮"},
    {"name": "锄药", "note": "宝玉小厮"},
    {"name": "墨雨", "note": "宝玉小厮"},
    {"name": "双瑞", "note": "宝玉小厮"},
    {"name": "双寿", "note": "宝玉小厮"},
    {"name": "伴鹤", "note": "宝玉小厮"},
    {"name": "扫花", "note": "宝玉小厮"},
    {"name": "吴新登", "note": "已有页"},
    {"name": "吴嬷嬷", "note": "脂本/异本，程高120回正文无此用名"},
    {"name": "守备", "note": "张金哥案，第15回"},
    {"name": "张门", "note": "张金哥案"},
    {"name": "李守忠", "note": "第4回护官符"},
    {"name": "王成", "note": "第6回刘姥姥连宗"},
    {"name": "王成之子", "note": "第6回"},
    {"name": "卜世仁", "note": "第24回贾芸舅"},
    {"name": "卜银姐", "note": "第24回"},
    {"name": "卜世仁妻", "note": "第24回"},
    {"name": "林四娘", "note": "第78回诗"},
    {"name": "忠顺亲王", "note": "第28回索琪官"},
    {"name": "北静王", "note": "第14/15/71/108回"},
    {"name": "南安郡王", "note": "第71/108回"},
    {"name": "西宁郡王", "note": "第71回"},
    {"name": "东平郡王", "note": "第71回"},
    {"name": "镇国公", "note": "第71回"},
    {"name": "锦乡侯", "note": "第71回"},
    {"name": "宁国公", "note": "第71回"},
    {"name": "荣国公", "note": "第71回"},
    {"name": "贾代善", "note": "贾母夫，已故"},
    {"name": "贾源", "note": "荣国公，已故"},
    {"name": "贾演", "note": "宁国公，已故"},
    {"name": "贾敬", "note": "第11/13/63回，惜春父"},
    {"name": "贾敷", "note": "贾敬长子，早亡"},
    {"name": "贾珠", "note": "贾政长子，李纨夫，早亡"},
    {"name": "贾敏", "note": "黛玉母，已故"},
    {"name": "王仁", "note": "第95/117/120回，王夫人侄"},
    {"name": "孙绍祖", "note": "已有页"},
    {"name": "孙天球", "note": "第79回"},
    {"name": "夏太监", "note": "第16/18/102回"},
    {"name": "戴权", "note": "第13/16/71/102回"},
    {"name": "单大良", "note": "第71回"},
    {"name": "钱槐", "note": "第94/95/103回"},
    {"name": "赵亦华", "note": "第71回"},
    {"name": "彩鸾", "note": "第71回"},
    {"name": "彩凤", "note": "第71回"},
    {"name": "绣鸾", "note": "第71回"},
    {"name": "绣凤", "note": "第71回"},
    {"name": "同喜", "note": "第71回"},
    {"name": "同贵", "note": "第71回"},
    {"name": "琥珀", "note": "贾母丫鬟"},
    {"name": "珍珠", "note": "贾母丫鬟"},
    {"name": "翡翠", "note": "贾母丫鬟"},
    {"name": "玻璃", "note": "贾母丫鬟"},
    {"name": "鹦哥", "note": "贾母丫鬟"},
    {"name": "文官", "note": "第36/58/70回，戏伶"},
    {"name": "药官", "note": "第58回，戏伶"},
    {"name": "玉官", "note": "第58回，戏伶"},
    {"name": "宝官", "note": "第58回，戏伶"},
    {"name": "艾官", "note": "第58回，戏伶"},
    {"name": "豆官", "note": "第58/70回，戏伶"},
    {"name": "葵官", "note": "第58/70回，戏伶"},
    {"name": "茄官", "note": "第58回，戏伶"},
    {"name": "菂官", "note": "第58回，已故"},
    {"name": "四儿", "note": "第44回"},
    {"name": "小蝉", "note": "第44/60/69回"},
    {"name": "小吉祥", "note": "已有小吉祥儿"},
    {"name": "佳蕙", "note": "第26/57/58回"},
    {"name": "碧月", "note": "第26/57/58回"},
    {"name": "碧痕", "note": "第26/57/58回"},
    {"name": "碧霞", "note": "第26/57/58回"},
    {"name": "碧云", "note": "第26/57/58回"},
    {"name": "碧桃", "note": "第26/57/58回"},
    {"name": "碧秋", "note": "第26/57/58回"},
    {"name": "碧春", "note": "第26/57/58回"},
    {"name": "碧夏", "note": "第26/57/58回"},
    {"name": "碧冬", "note": "第26/57/58回"},
]


def known_set() -> set[str]:
    s: set[str] = set()
    for _, fm, _ in iter_characters(BOOK):
        cid = fm.get("id") or ""
        if cid:
            s.add(cid)
        for a in [fm.get("name")] + (fm.get("aliases") or []):
            if a:
                s.add(a)
    for alias, cid in BOOK_EXTRA_ALIASES.get(BOOK, {}).items():
        s.add(alias)
        s.add(cid)
    return s


def scan_edition(subdir: str | None) -> tuple[dict[str, set[int]], dict[str, set[int]]]:
    alias_pairs = build_alias_map(BOOK)
    base = CHAPTER_DIR / BOOK
    d = base / subdir if subdir else base
    text_hits: dict[str, set[int]] = defaultdict(set)
    fm_hits: dict[str, set[int]] = defaultdict(set)
    for p in sorted(d.glob("[0-9]*.md")):
        try:
            ch = int(p.stem)
        except ValueError:
            continue
        raw = p.read_text(encoding="utf-8-sig")
        text = strip_html(split_body(raw))
        for cid in find_characters(text, alias_pairs):
            text_hits[cid].add(ch)
        for c in parse_list_field(raw, "characters") or []:
            fm_hits[c].add(ch)
    return dict(text_hits), dict(fm_hits)


def scan_seed_names(names: list[str], known: set[str]) -> dict[str, set[int]]:
    hits: dict[str, set[int]] = defaultdict(set)
    base = CHAPTER_DIR / BOOK
    for p in sorted(base.glob("[0-9]*.md")):
        ch = int(p.stem)
        raw = p.read_text(encoding="utf-8-sig")
        text = strip_html(split_body(raw))
        for name in names:
            if name in known or name not in text:
                continue
            hits[name].add(ch)
    return dict(hits)


def main() -> None:
    known = known_set()
    paged = sorted({fm.get("id") for _, fm, _ in iter_characters(BOOK) if fm.get("id")})

    cheng_text, cheng_fm = scan_edition(None)
    zhi_text, zhi_fm = scan_edition("脂砚斋本")

    with open(DATA_DIR / "honglou.character_roster.json", encoding="utf-8") as f:
        roster = json.load(f)

    seed_names = [s["name"] for s in MANUAL_SEED]
    seed_hits = scan_seed_names(seed_names, known)

    # Edition diff for known chars
    only_cheng = sorted(set(cheng_text) - set(zhi_text))
    only_zhi = sorted(set(zhi_text) - set(cheng_text))

    # Seed not in wiki
    seed_pending = []
    for s in MANUAL_SEED:
        name = s["name"]
        if name in known:
            continue
        chs = sorted(seed_hits.get(name, set()))
        seed_pending.append({**s, "chapters": chs, "mentions": len(chs)})

    seed_pending.sort(key=lambda x: (-x["mentions"], x["name"]))

    # Roster top real (mentions >= 2, filter obvious noise)
    NOISE = re.compile(r"(笑|知|道|说|问|答|忙|便|又|只|怒|叹|嚷|喝|应|回|接|因|且)$")
    roster_real = [
        p
        for p in roster["pending"]
        if p["mentions"] >= 2 and not NOISE.search(p["name"])
    ]

    bestiary_path = DATA_DIR / "hongloumeng.bestiary.json"
    if bestiary_path.is_file():
        bdata = json.loads(bestiary_path.read_text(encoding="utf-8"))
        ids = set()
        for members in (bdata.get("groups") or {}).values():
            ids.update(members)
        bestiary_count = len(ids) or len(paged)
    else:
        bestiary_count = len(paged)

    report = {
        "generated": roster["generated"],
        "paged_count": len(paged),
        "bestiary_count": bestiary_count,
        "edition": {
            "程高本_chapters": len(list((CHAPTER_DIR / BOOK).glob("[0-9]*.md"))),
            "脂砚斋本_chapters": len(list((CHAPTER_DIR / BOOK / "脂砚斋本").glob("[0-9]*.md"))),
            "程高本_detected_known": len(cheng_text),
            "脂砚斋本_detected_known": len(zhi_text),
            "only_in_程高本_120回": only_cheng,
            "only_in_脂砚斋本_80回": only_zhi,
        },
        "frontmatter": {
            "程高本_fm_unique": len(cheng_fm),
            "脂砚斋本_fm_unique": len(zhi_fm),
        },
        "roster_extracted_pending": roster["pending_count"],
        "roster_real_candidates": len(roster_real),
        "seed_pending": seed_pending,
        "roster_top20": roster_real[:20],
    }

    out = DATA_DIR / "honglou.character_audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wiki pages: {len(paged)}")
    print(f"程高本 detected (known alias map): {len(cheng_text)}")
    print(f"脂砚斋本 detected: {len(zhi_text)}")
    print(f"Only 程高120: {only_cheng}")
    print(f"Only 脂本80: {only_zhi}")
    print(f"\nSeed pending ({len(seed_pending)} names with text hits):")
    for s in seed_pending[:35]:
        chs = s["chapters"][:5]
        extra = f" +{len(s['chapters'])-5}" if len(s["chapters"]) > 5 else ""
        print(f"  {s['name']:10s} {s['mentions']:2d}回  {chs}{extra}  | {s.get('note','')}")
    print(f"\nRoster top (>=2 mentions, filtered):")
    for p in roster_real[:15]:
        print(f"  {p['name']:10s} {p['mentions']:3d}回")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
