#!/usr/bin/env python3
"""/dream 第七梯队 — 生成 score 9–16 互链索引页。

用法: python scripts/build_hlm_tier7_link_topic.py
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, CONTENT, parse_frontmatter  # noqa: E402

BOOK = "红楼梦"
OUT = CONTENT / "topics" / BOOK / "第七梯队低密度互链.md"

# 2026-06-16 末批 consolidation 后 score 均已 >16；scan 为空时仍保留归档索引
ARCHIVED_TIER7: list[str] = [
    "同喜", "同贵", "坠儿", "小鹊",
    "戴权", "镇国公", "乌进孝", "锦乡侯", "赵亦华", "王尔调",
    "钱槐", "小蝉", "马道婆",
    "菂官", "玉官",
    "多官", "张三", "吴良", "王成", "霍启", "卜世仁",
    "甄应嘉", "傅秋芳", "林四娘", "胡庸医",
    "喜儿", "彩鸾", "彩屏", "入画",
    "贾敷", "贾璜",
    "倪二", "卫若兰", "善姐", "彩明", "李嬷嬷", "李贵", "焦大", "素云", "翠云", "茄官",
]

GROUPS: dict[str, list[str]] = {
    "小厮·跟班": [
        "引泉", "挑云", "扫花", "伴鹤", "四儿", "同喜", "同贵", "坠儿", "小鹊",
    ],
    "买办·管事·王府": [
        "钱华", "戴权", "镇国公", "乌进孝", "锦乡侯", "赵亦华", "王尔调",
    ],
    "学塾·赵房·露剂": [
        "金荣", "玉爱", "香怜", "钱槐", "小蝉", "小吉祥儿", "马道婆",
    ],
    "戏伶·梨香": [
        "芳官", "龄官", "茜官", "菂官", "藕官", "宝官", "玉官",
    ],
    "刑名·穷亲·楔子": [
        "多官", "张三", "吴良", "王成", "霍启", "守备", "卜世仁",
    ],
    "甄家·诗典·方外": [
        "甄应嘉", "甄宝玉", "傅秋芳", "林四娘", "净虚", "胡庸医",
    ],
    "怡红·蘅芜·近侍": [
        "喜儿", "彩鸾", "彩屏", "傻大姐", "坠儿", "碧痕", "入画",
    ],
    "宁荣谱系·早亡": ["贾敷", "贾菌", "贾璜"],
}


def density(d: dict) -> int:
    return (
        d["rel"] * 2
        + d["plot"] * 3
        + (1 if d["main"] else 0)
        + (1 if d["review"] else 0)
        + min(d["inbound"], 5)
    )


def scan() -> list[tuple[int, str, str]]:
    char_dir = CHAR_DIR / BOOK
    ids = {p.stem for p in char_dir.glob("*.md")}
    inbound: dict[str, set[str]] = defaultdict(set)
    for p in char_dir.glob("*.md"):
        txt = p.read_text(encoding="utf-8-sig")
        src = p.stem
        for m in re.finditer(r"\[\[([^\]|]+)", txt):
            t = m.group(1).strip()
            if t in ids and t != src:
                inbound[t].add(src)
    for p in (CONTENT / "topics" / BOOK).glob("*.md"):
        if p.name == OUT.name:
            continue
        for m in re.finditer(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8-sig")):
            t = m.group(1).strip()
            if t in ids:
                inbound[t].add("topic")

    rows: list[tuple[int, str, str]] = []
    for p in char_dir.glob("*.md"):
        fm, body = parse_frontmatter(p)
        cid = fm.get("id") or p.stem
        if cid == "西门庆":
            continue
        m = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
        plots = sum(
            1
            for ln in (m.group(1).splitlines() if m else [])
            if ln.strip().startswith("-")
        )
        d = {
            "rel": len(fm.get("relations") or []),
            "plot": plots,
            "main": "## 主要关系" in body,
            "review": "## 评析" in body,
            "inbound": len(inbound[cid]),
        }
        s = density(d)
        if 9 <= s <= 16:
            summary = (fm.get("summary") or "").split("；")[0][:48]
            rows.append((s, cid, summary))
    return sorted(rows)


def build(rows: list[tuple[int, str, str]], archived: bool = False) -> str:
    row_map = {cid: (sc, sm) for sc, cid, sm in rows}
    all_ids = set(row_map) if rows else set(ARCHIVED_TIER7)
    assigned: set[str] = set()
    lines = [
        "---",
        "type: topic",
        f"book: {BOOK}",
        "title: 第七梯队低密度互链",
        f"derived_from: [{', '.join(sorted(all_ids)[:20])}, lint, score9-16]",
        "created: 2026-06-16",
        "tags: [lint, 互链, 配角, 索引, score9-16, 归档]",
        "summary: 2026-06-16 末批 41 页低密度配角归档索引；各补第 3 情节后 score 均已 >16。",
        "---",
        "",
        "## 结论",
        "",
    ]
    if archived:
        lines.append(
            f"本页归档 **{len(all_ids)}** 个原 score∈[9,16] 配角（2026-06-16 `/dream` 各补第 3 条可核情节后，"
            f"`/lint` 该带 **0** 页）。按职能分组互链，便于从主题纵切回指人物 card。"
        )
    else:
        lines.append(
            f"本页索引 **{len(rows)}** 个 score∈[9,16] 配角页，按职能分组互链，便于从主题纵切回指人物 card。"
        )
    lines.append("")

    char_dir = CHAR_DIR / BOOK

    def line_for(cid: str) -> str:
        if cid in row_map:
            sc, sm = row_map[cid]
            return f"- [[{cid}]]（score={sc}）：{sm}"
        path = char_dir / f"{cid}.md"
        if path.exists():
            fm, _ = parse_frontmatter(path)
            sm = (fm.get("summary") or "").split("；")[0][:48]
            return f"- [[{cid}]]（已出境）：{sm}"
        return f"- [[{cid}]]（已出境）"

    for gname, members in GROUPS.items():
        hits = [m for m in members if m in all_ids]
        if not hits:
            continue
        assigned.update(hits)
        lines.append(f"## {gname}")
        lines.append("")
        for cid in hits:
            lines.append(line_for(cid))
        lines.append("")

    rest = sorted(all_ids - assigned)
    if rest:
        lines.append("## 其余")
        lines.append("")
        for cid in rest:
            lines.append(line_for(cid))
        lines.append("")

    lines.append("## 相关链接")
    lines.append("")
    lines.append(
        "- [[零入链配角互链]] · [[宝玉小厮链]] · [[淘气小厮链]] · [[账房三头目链]] · "
        "[[赵姨娘房链]] · [[家塾闹学链]] · [[图鉴名物信物链总览]]"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows = scan()
    archived = len(rows) == 0
    text = build(rows, archived=archived)
    OUT.write_text(text, encoding="utf-8")
    label = "archived" if archived else "active"
    print(f"wrote {OUT.name}: {len(rows) or len(ARCHIVED_TIER7)} characters ({label})")


if __name__ == "__main__":
    main()
