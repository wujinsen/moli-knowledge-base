#!/usr/bin/env python3
"""从世德堂 raw 与殆知阁通本 raw 自动抽取措辞异文，写入 variants/西游记/。

人工锚点（回目重排、卷首作者署等）在 CURATED 中固定；其余由字符级 diff 生成。

用法:
  python scripts/seed_xiyouji_variants.py          # 写入全部
  python scripts/seed_xiyouji_variants.py --dry-run  # 仅统计
  python scripts/seed_xiyouji_variants.py --max-total 60 --max-per-chapter 5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

from _common import ROOT
from import_chapters import CHAPTER_HEAD, SOURCES, XYJ_FNAME, split_daizhige_txt

OUT = ROOT / "src" / "content" / "variants" / "西游记"

EDITION_A = "世德堂本"
EDITION_B = "通本"

# 第 9–12 回为情节/结构重排，正文 diff 无意义，仅保留 CURATED 回目锚点
SKIP_BODY_CHAPTERS = frozenset({9, 10, 11, 12})

RARE_CHAR = re.compile(r"□【[^】]*】")
WHITESPACE = re.compile(r"[\s　]+")
TITLE_SPACE = re.compile(r"[　\s]+")
PUNCT_ONLY = re.compile(
    r"^[\s　，。、；：！？「」『』（）…—·\.\,\!\?\;\:\"\'\-\[\]《》]+$"
)

# 人工标杆：回目重排、结构差异、已知讹字（不被 auto 覆盖）
CURATED: list[dict] = [
    dict(
        id="xyj-v-000", chapter=1, category="删润",
        text_a="（卷首不署作者）", text_b="《西游记》 明 吴承恩",
        note="通本卷首署作者；世德堂本不署。作者归属见考证台「作者公案」，非正文事实。",
        summary="卷首作者署：世德堂无署 vs 通本署吴承恩。",
        tags=["卷首"],
    ),
    dict(
        id="xyj-v-001", chapter=1, category="措辞",
        text_a="扑蜡", text_b="扑八蜡",
        note="第1回群猴顽耍，世德堂作「扑蜡」，通本作「扑八蜡」（扑蜻蜓的一种游戏名）。",
        summary="第1回「扑蜡」↔「扑八蜡」措辞异文。",
    ),
    dict(
        id="xyj-v-002", chapter=1, category="措辞",
        text_a="灵霄宝殿", text_b="灵霄宝店",
        note="第1回玉帝所居，世德堂作「宝殿」，通本作「宝店」（疑为刻本讹字）。",
        summary="第1回「灵霄宝殿」↔「灵霄宝店」。",
    ),
    dict(
        id="xyj-v-003", chapter=1, category="措辞",
        text_a="编草", text_b="编草帓",
        note="第1回猴群游戏「编草帓」，世德堂省作「编草」。",
        summary="第1回「编草」↔「编草帓」。",
    ),
    dict(
        id="xyj-v-009", chapter=9, category="回目",
        text_a="陈光蕊赴任逢灾　江流僧复雠报本",
        text_b="袁守诚妙算无私曲　老龙王拙计犯天条",
        note="结构重排：世德堂第9回为陈光蕊/江流儿身世，通本第9回为袁守诚/老龙王。",
        summary="第9回回目完全不同（陈光蕊段 vs 袁守诚/龙王段）。",
        tags=["结构重排"],
    ),
    dict(
        id="xyj-v-010", chapter=10, category="回目",
        text_a="老龙王拙计犯天条　魏丞相遗书托冥吏",
        text_b="二将军宫门镇鬼　唐太宗地府还魂",
        summary="第10回回目异文（龙王冥吏 vs 镇鬼还魂）。",
        tags=["结构重排"],
    ),
    dict(
        id="xyj-v-011", chapter=11, category="回目",
        text_a="游地府太宗还魂　进瓜果刘全续配",
        text_b="还受生唐王遵善果　度孤魂萧瑀正空门",
        summary="第11回回目异文（刘全续配 vs 萧瑀空门）。",
        tags=["结构重排"],
    ),
    dict(
        id="xyj-v-012", chapter=12, category="回目",
        text_a="唐王秉诚修大会　观音显圣化金蝉",
        text_b="玄奘秉诚建大会　观音显象化金蝉",
        note="世德堂作「唐王」「显圣」，通本作「玄奘」「显象」。",
        summary="第12回回目：唐王/玄奘、显圣/显象异文。",
        tags=["结构重排"],
    ),
    dict(
        id="xyj-v-013", chapter=13, category="措辞",
        text_a="陷虎穴金星解厄　　双叉岭伯钦留僧",
        text_b="陷虎穴金星解厄　双叉岭伯钦留僧",
        note="世德堂回目「解厄」与「双叉岭」间有双全角空格，通本合并为单空格。",
        summary="第13回回目标点/空格删润。",
        tags=["版式"],
    ),
    dict(
        id="xyj-v-018", chapter=18, category="回目",
        text_a="观音院唐僧脱难　高老庄大圣除魔",
        text_b="观音院唐僧脱难　高老庄行者降魔",
        note="世德堂作「大圣除魔」，通本作「行者降魔」。",
        summary="第18回「大圣除魔」↔「行者降魔」。",
    ),
]


def normalize_body(text: str) -> str:
    """去空白、去殆知阁缺字占位，供字符级 diff。"""
    text = RARE_CHAR.sub("", text)
    return WHITESPACE.sub("", text)


def normalize_title(title: str) -> str:
    return TITLE_SPACE.sub("　", title.strip())


def load_shide() -> dict[int, tuple[str, str]]:
    out: dict[int, tuple[str, str]] = {}
    src = SOURCES["西游记"]["path"]
    for p in sorted(src.glob("*.txt")):
        m = XYJ_FNAME.match(p.name)
        if not m:
            continue
        n = int(m.group(1))
        title = m.group(2).strip()
        raw = p.read_text(encoding="utf-8")
        lines = raw.splitlines()
        if lines and CHAPTER_HEAD.match(lines[0].strip()):
            body = "\n".join(lines[1:])
            hm = CHAPTER_HEAD.match(lines[0].strip())
            if hm and hm.group(2).strip():
                title = hm.group(2).strip()
        else:
            body = raw
        out[n] = (title, body)
    return out


def load_tongben() -> dict[int, tuple[str, str]]:
    text = SOURCES["西游记通本"]["path"].read_text(encoding="utf-8")
    return {n: (title, body) for n, title, body in split_daizhige_txt(text)}


def is_meaningful_pair(a: str, b: str, *, max_len: int, min_ratio: float) -> bool:
    if not a or not b or a == b:
        return False
    if len(a) < 2 or len(b) < 2:
        return False
    if max(len(a), len(b)) > max_len:
        return False
    if PUNCT_ONLY.match(a) or PUNCT_ONLY.match(b):
        return False
    ratio = min(len(a), len(b)) / max(len(a), len(b))
    if ratio < min_ratio:
        return False
    # 纯数字/标点微差
    if re.fullmatch(r"[\d〇零一二三四五六七八九十百两]+", a) and re.fullmatch(
        r"[\d〇零一二三四五六七八九十百两]+", b
    ):
        return False
    return True


def extract_title_variants(
    shide: dict[int, tuple[str, str]],
    tongben: dict[int, tuple[str, str]],
    *,
    curated_keys: set[tuple[int, str, str]],
) -> list[dict]:
    found: list[dict] = []
    seen: set[tuple[int, str, str]] = set()
    for n in sorted(set(shide) & set(tongben)):
        ta = normalize_title(shide[n][0])
        tb = normalize_title(tongben[n][0])
        if ta == tb:
            continue
        key = (n, ta, tb)
        if key in curated_keys or key in seen:
            continue
        seen.add(key)
        found.append(
            dict(
                chapter=n,
                category="回目",
                text_a=ta,
                text_b=tb,
                summary=f"第{n}回回目异文（自动抽取）。",
                tags=["auto", "回目"],
            )
        )
    return found


def extract_body_variants(
    shide: dict[int, tuple[str, str]],
    tongben: dict[int, tuple[str, str]],
    *,
    curated_keys: set[tuple[int, str, str]],
    max_len: int,
    min_ratio: float,
    max_per_chapter: int,
) -> list[dict]:
    found: list[dict] = []
    global_seen: set[tuple[int, str, str]] = set()

    for n in sorted(set(shide) & set(tongben)):
        if n in SKIP_BODY_CHAPTERS:
            continue
        na = normalize_body(shide[n][1])
        nb = normalize_body(tongben[n][1])
        if na == nb:
            continue

        chapter_hits: list[tuple[str, str]] = []
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, na, nb).get_opcodes():
            if tag != "replace":
                continue
            a, b = na[i1:i2], nb[j1:j2]
            if not is_meaningful_pair(a, b, max_len=max_len, min_ratio=min_ratio):
                continue
            key = (n, a, b)
            if key in curated_keys or key in global_seen:
                continue
            global_seen.add(key)
            chapter_hits.append((a, b))

        # 每回优先短片段（更可能是措辞而非大段删润）
        chapter_hits.sort(key=lambda p: max(len(p[0]), len(p[1])))
        for a, b in chapter_hits[:max_per_chapter]:
            found.append(
                dict(
                    chapter=n,
                    category="措辞",
                    text_a=a,
                    text_b=b,
                    summary=f"第{n}回「{a}」↔「{b}」（自动抽取）。",
                    tags=["auto"],
                )
            )
    return found


def assign_ids(curated: list[dict], auto: list[dict]) -> list[dict]:
    """CURATED 保留固定 id；auto 从 xyj-v-019 起递增。"""
    used = {v["id"] for v in curated}
    next_num = max(int(i.split("-")[-1]) for i in used) + 1
    out = [dict(v) for v in curated]
    for v in auto:
        while f"xyj-v-{next_num:03d}" in used:
            next_num += 1
        vid = f"xyj-v-{next_num:03d}"
        used.add(vid)
        row = dict(v)
        row["id"] = vid
        row.setdefault("edition_a", EDITION_A)
        row.setdefault("edition_b", EDITION_B)
        out.append(row)
        next_num += 1
    for v in out:
        v.setdefault("edition_a", EDITION_A)
        v.setdefault("edition_b", EDITION_B)
        v.setdefault("tags", [])
    return out


def yaml_quote(value: str) -> str:
    """安全嵌入 YAML 标量。"""
    return json.dumps(value, ensure_ascii=False)


def write_variant(v: dict) -> None:
    tags = v.get("tags", [])
    lines = [
        "---",
        f"id: {v['id']}",
        "type: variant",
        "book: 西游记",
        f"chapter: {v['chapter']}",
        f"category: {v['category']}",
        f"edition_a: {v['edition_a']}",
        f"edition_b: {v['edition_b']}",
    ]
    if v.get("text_a") is not None:
        lines.append(f"text_a: {yaml_quote(v['text_a'])}")
    if v.get("text_b") is not None:
        lines.append(f"text_b: {yaml_quote(v['text_b'])}")
    if v.get("note"):
        lines.append(f"note: {yaml_quote(v['note'])}")
    tag_str = ", ".join(tags)
    lines.append(f"tags: [{tag_str}]")
    lines.append(f"summary: {yaml_quote(v['summary'])}")
    lines.append("---")
    lines.append("")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{v['id']}.md").write_text("\n".join(lines), encoding="utf-8")


def curated_keys() -> set[tuple[int, str, str]]:
    keys: set[tuple[int, str, str]] = set()
    for v in CURATED:
        if v.get("text_a") and v.get("text_b"):
            keys.add((v["chapter"], v["text_a"], v["text_b"]))
    return keys


def main() -> None:
    parser = argparse.ArgumentParser(description="世德堂 vs 通本异文种子")
    parser.add_argument("--dry-run", action="store_true", help="只打印统计，不写文件")
    parser.add_argument("--max-total", type=int, default=70, help="auto 异文上限（不含 CURATED）")
    parser.add_argument("--max-per-chapter", type=int, default=4, help="每回 auto 措辞上限")
    parser.add_argument("--max-len", type=int, default=12, help="单段异文最大字数")
    parser.add_argument("--min-ratio", type=float, default=0.4, help="两段长度比下限")
    args = parser.parse_args()

    shide = load_shide()
    tongben = load_tongben()
    if len(shide) != 100 or len(tongben) != 100:
        print(f"[warn] 世德堂 {len(shide)} 回 / 通本 {len(tongben)} 回", file=sys.stderr)

    keys = curated_keys()
    title_auto = extract_title_variants(shide, tongben, curated_keys=keys)
    body_auto = extract_body_variants(
        shide,
        tongben,
        curated_keys=keys,
        max_len=args.max_len,
        min_ratio=args.min_ratio,
        max_per_chapter=args.max_per_chapter,
    )

    # 回目 auto 不与 CURATED 重复后，限量并入
    auto = title_auto + body_auto
    if len(auto) > args.max_total:
        # 回目优先，其余按回次+片段长度
        title_part = [a for a in auto if a["category"] == "回目"]
        body_part = [a for a in auto if a["category"] != "回目"]
        body_part.sort(
            key=lambda v: (v["chapter"], max(len(v.get("text_a", "")), len(v.get("text_b", ""))))
        )
        budget = max(0, args.max_total - len(title_part))
        auto = title_part + body_part[:budget]

    variants = assign_ids(CURATED, auto)
    auto_n = len(variants) - len(CURATED)

    print(
        f"[西游记] CURATED {len(CURATED)} + auto {auto_n} = {len(variants)} 异文"
        f"（跳过正文 diff 回次 {sorted(SKIP_BODY_CHAPTERS)}）"
    )
    if args.dry_run:
        from collections import Counter

        by_cat = Counter(v["category"] for v in variants)
        by_ch = Counter(v["chapter"] for v in variants if "auto" in v.get("tags", []))
        print("  分类:", dict(by_cat))
        print("  auto 分布 Top10:", by_ch.most_common(10))
        return

    # 清空旧 auto 文件后全量写入（避免残留过期 id）
    if OUT.exists():
        for p in OUT.glob("xyj-v-*.md"):
            p.unlink()

    for v in variants:
        write_variant(v)

    rel = OUT.relative_to(ROOT)
    print(f"→ {rel}/ ({len(variants)} 文件)")


if __name__ == "__main__":
    main()
