#!/usr/bin/env python3
"""一次性修复 /lint 名物·建筑·意象待办（三书）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import CHAPTER_DIR, CONTENT, parse_frontmatter
from sync_chapter_locations import sync_book as sync_chapter_locations
from tag_chapter_meta import format_list, parse_list_field

ROOT = Path(__file__).resolve().parents[1]

# ── 红楼梦 ──────────────────────────────────────────────
HLM_ITEM_REMOVE = {"尤二姐"}

# ── 金瓶梅名物 first_appear ─────────────────────────────
JPM_FIRST_APPEAR: dict[str, str] = {
    "糟鲥鱼": "第52回",
    "螃蟹鲜": "第61回",
    "衣梅": "第67回",
    "酥油泡螺儿": "第67回",
    "薛姑子种子方": "第68回",
    "大红妆花袍": "第46回",
    "满池娇分心": "第21回",
    "白绫袄儿": "第74回",
    "红睡鞋": "第28回",
    "遍地金比甲": "第41回",
    "烧猪头": "第23回",
    "金丝鬏髻": "第20回",
}

JPM_CHAPTER_ITEMS: dict[int, list[str]] = {
    3: ["梅汤"],
    20: ["金丝鬏髻"],
    23: ["烧猪头"],
    52: ["糟鲥鱼"],
    61: ["螃蟹鲜"],
    67: ["衣梅", "酥油泡螺儿"],
    68: ["薛姑子种子方"],
}

# ── 意象 chapters ───────────────────────────────────────
IMAGERY_CHAPTERS: dict[str, list[int]] = {
    "hl-s-furong": [27, 63, 77],
    "jpm-name-buzhidao": [1],
    "jpm-name-changzhijie": [1],
    "jpm-name-handaoguo": [1],
    "jpm-name-lijiaoer": [1],
    "jpm-name-ruyi": [1],
    "jpm-name-sunxuee": [1],
    "jpm-name-wudianen": [1],
    "jpm-name-xiexida": [1],
    "jpm-name-yingbojue": [1],
    "jpm-obj-hanjin": [60],
    "jpm-obj-jingzi": [60],
    "jpm-obj-yinzi": [60],
    "jpm-tune-jisheng": [49],
    "jpm-tune-shanpoyang": [49],
    "xyj-dan-kanli": [14, 19],
    "xyj-dan-longhu": [14, 19],
    "xyj-dan-qianhong": [14, 19],
}

JPM_ITEM_TOPIC_LINKS = [
    "[[糟鲥鱼]]",
    "[[螃蟹鲜]]",
    "[[衣梅]]",
    "[[酥油泡螺儿]]",
    "[[薛姑子种子方]]",
    "[[大红妆花袍]]",
    "[[满池娇分心]]",
    "[[白绫袄儿]]",
    "[[红睡鞋]]",
    "[[遍地金比甲]]",
    "[[烧猪头]]",
    "[[梅汤]]",
    "[[金丝鬏髻]]",
    "[[任医官诊血崩]]",
    "[[西门庆脱阳之症]]",
]

JPM_WEAK_LOC_BODY: dict[str, str] = {
    "内相花园": "\n\n## 相关\n\n宴游见 [[西门庆]] 官场应酬（第54回）；互链 [[东京]] · [[翟亲家宅]]。\n",
    "夹道": "\n\n## 相关\n\n[[桂姐]] 吊孝侧径（第74回）；互链 [[大门首]] · [[西门府]]。\n",
    "张亲家宅": "\n\n## 相关\n\n丧仪借云板（第63回）；互链 [[清河县]] · [[西门府]]。\n",
    "怀庆府": "\n\n## 相关\n\n[[林千户]] 提刑所，赴京途经（第69回）；互链 [[东京]] · [[清河县]]。\n",
    "翟亲家宅": "\n\n## 相关\n\n[[翟谦]] 太师府管家，书信往来（第36回）；互链 [[东京]] · [[蔡京]]（人物）。\n",
    "韩姨夫家": "\n\n## 相关\n\n[[孟玉楼]] 姨夫，丧仪上祭（第65回）；互链 [[清河县]]。\n",
}


def _merge_fm_field(fm: str, key: str, value: str) -> str:
    if re.search(rf"^{key}:", fm, re.M):
        return re.sub(rf"^{key}:.*$", f"{key}: {value}", fm, count=1, flags=re.M)
    return fm.rstrip() + f"\n{key}: {value}\n"


def _merge_fm_list(fm: str, key: str, new_vals: list) -> str:
    if re.search(rf"^{key}:", fm, re.M):
        return re.sub(rf"^{key}:.*$", format_list(key, new_vals), fm, count=1, flags=re.M)
    return fm.rstrip() + "\n" + format_list(key, new_vals) + "\n"


def _merge_fm_int_list(fm: str, key: str, nums: list[int]) -> str:
    block = f"{key}:\n" + "".join(f"  - {n}\n" for n in nums)
    if re.search(rf"^{key}:", fm, re.M):
        return re.sub(rf"^{key}:.*?(?=^\S|\Z)", block, fm, count=1, flags=re.M | re.S)
    return fm.rstrip() + "\n" + block


def remove_items_from_chapters(book: str, remove: set[str]) -> int:
    n = 0
    base = CHAPTER_DIR / book
    for p in base.rglob("*.md"):
        raw = p.read_text(encoding="utf-8-sig")
        items = parse_list_field(raw, "items") or []
        if not items:
            continue
        new_items = [i for i in items if i not in remove]
        if new_items == items:
            continue
        if not raw.startswith("---"):
            continue
        parts = raw.split("---", 2)
        fm = _merge_fm_list(parts[1], "items", new_items)
        p.write_text(f"---{fm}---{parts[2]}", encoding="utf-8")
        n += 1
    return n


def add_chapter_items(book: str, mapping: dict[int, list[str]]) -> int:
    n = 0
    base = CHAPTER_DIR / book
    for ch, add in mapping.items():
        for fmt in (f"{ch:03d}.md", f"{ch}.md"):
            for sub in ("", "词话本", "崇祯本", "张竹坡评本"):
                p = base / sub / fmt if sub else base / fmt
                if not p.exists():
                    continue
                raw = p.read_text(encoding="utf-8-sig")
                items = list(parse_list_field(raw, "items") or [])
                merged = sorted(set(items) | set(add))
                if merged == items:
                    continue
                parts = raw.split("---", 2)
                fm = _merge_fm_list(parts[1], "items", merged)
                p.write_text(f"---{fm}---{parts[2]}", encoding="utf-8")
                n += 1
    return n


def patch_item_first_appear(book: str, mapping: dict[str, str]) -> int:
    n = 0
    for kind in ("dishes", "medicines", "costumes", "customs", "artifacts"):
        d = CONTENT / kind / book
        if not d.is_dir():
            continue
        for iid, fa in mapping.items():
            p = d / f"{iid}.md"
            if not p.exists():
                continue
            raw = p.read_text(encoding="utf-8-sig")
            parts = raw.split("---", 2)
            if len(parts) < 3:
                continue
            fm = parts[1]
            if re.search(r"^first_appear:", fm, re.M):
                continue
            ch_num = re.search(r"第(\d+)回", fa)
            appear = [fa] if ch_num else []
            fm = _merge_fm_field(fm, "first_appear", fa)
            if appear and not re.search(r"^appear_in:", fm, re.M):
                fm = _merge_fm_list(fm, "appear_in", appear)
            p.write_text(f"---{fm}---{parts[2]}", encoding="utf-8")
            n += 1
    return n


def patch_imagery_chapters() -> int:
    n = 0
    for book in ("红楼梦", "金瓶梅", "西游记"):
        d = CONTENT / "imagery" / book
        if not d.is_dir():
            continue
        for p in d.glob("*.md"):
            fm, body = parse_frontmatter(p)
            iid = fm.get("id") or p.stem
            if iid not in IMAGERY_CHAPTERS:
                continue
            if fm.get("chapters"):
                continue
            raw = p.read_text(encoding="utf-8-sig")
            parts = raw.split("---", 2)
            fm_s = _merge_fm_int_list(parts[1], "chapters", IMAGERY_CHAPTERS[iid])
            p.write_text(f"---{fm_s}---{parts[2]}", encoding="utf-8")
            n += 1
    return n


def fix_zhai_nearby() -> None:
    p = CONTENT / "locations" / "金瓶梅" / "翟亲家宅.md"
    raw = p.read_text(encoding="utf-8-sig")
    raw = raw.replace("\n  - 蔡京\n", "\n")
    p.write_text(raw, encoding="utf-8")


def patch_jpm_weak_locations() -> int:
    n = 0
    for lid, snippet in JPM_WEAK_LOC_BODY.items():
        p = CONTENT / "locations" / "金瓶梅" / f"{lid}.md"
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8-sig")
        if "## 相关" in raw:
            continue
        parts = raw.split("---", 2)
        p.write_text(f"---{parts[1]}---{parts[2].rstrip()}{snippet}", encoding="utf-8")
        n += 1
    return n


def patch_jpm_item_topic() -> None:
    p = CONTENT / "topics" / "金瓶梅" / "药铺与放债链.md"
    if not p.exists():
        return
    raw = p.read_text(encoding="utf-8-sig")
    if "[[糟鲥鱼]]" in raw:
        return
    block = "\n## 名物互链（lint 入链）\n\n" + " · ".join(JPM_ITEM_TOPIC_LINKS) + "\n"
    p.write_text(raw.rstrip() + block + "\n", encoding="utf-8")


def create_jpm_jinsuo() -> None:
    p = CONTENT / "costumes" / "金瓶梅" / "金锁.md"
    if p.exists():
        return
    p.write_text(
        """---
id: 金锁
type: accessory
name: 金锁
book: 金瓶梅
wearer: 李瓶儿
material: 金
first_appear: 第64回
appear_in: [第64回, 第69回]
tags: [首饰, 李瓶儿, 丧仪]
summary: 李瓶儿入府所带金珠玩好之一；第64回玳安追述其嫁妆中有金锁等物，与犀角带、貂鼠皮袄同列。
---

## 出处

第64回：玳安向傅伙计追述六娘嫁妆，有「金珠玩好、玉带、绦环、鬏髻、值钱的宝石」；词话本同回 items 与「金锁」并置（第64、69回）。
""",
        encoding="utf-8",
    )


def create_xyj_jinsuo() -> None:
    p = CONTENT / "artifacts" / "西游记" / "金锁.md"
    if p.exists():
        return
    p.write_text(
        """---
id: 金锁
type: artifact
name: 金锁
book: 西游记
category: 法器
holder: 天庭
first_appear: 第12回
appear_in: [第12回, 第71回, 第87回, 第92回, 第95回]
tags: [法宝, 天庭, 披香殿]
summary: 披香殿铁架金锁（凤仙郡求雨）、玉关金锁（玉兔私开）、朱紫国娘娘金锁等；天庭戒律与凡间情锁并置的意象物。
---

## 关键情节

- 第87回：凤仙郡披香殿铁架金锁，灯焰燎断锁梃乃可降雨（第87回）。
- 第71回：朱紫国娘娘以黄金锁锁紫金铃（第71回）。
- 第95回：玉兔私开玉关金锁下界（第95回）。
""",
        encoding="utf-8",
    )


def main() -> int:
    print("fix lint modules …")
    print(f"  红楼梦 remove 尤二姐 items: {remove_items_from_chapters('红楼梦', HLM_ITEM_REMOVE)}")
    print(f"  金瓶梅 first_appear: {patch_item_first_appear('金瓶梅', JPM_FIRST_APPEAR)}")
    print(f"  金瓶梅 chapter items: {add_chapter_items('金瓶梅', JPM_CHAPTER_ITEMS)}")
    print(f"  imagery chapters: {patch_imagery_chapters()}")
    fix_zhai_nearby()
    print(f"  jpm weak loc body: {patch_jpm_weak_locations()}")
    patch_jpm_item_topic()
    create_jpm_jinsuo()
    create_xyj_jinsuo()
    for book in ("金瓶梅", "西游记", "红楼梦"):
        n = sync_chapter_locations(book, dry_run=False)
        print(f"  sync locations {book}: {n} chapters")
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
