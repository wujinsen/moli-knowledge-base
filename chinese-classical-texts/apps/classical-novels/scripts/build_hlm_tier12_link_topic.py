#!/usr/bin/env python3
"""/dream 第十二梯队 — 生成 score=26 归档互链索引页。

用法: python scripts/build_hlm_tier12_link_topic.py
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, CONTENT, parse_frontmatter  # noqa: E402

BOOK = "红楼梦"
OUT = CONTENT / "topics" / BOOK / "第十二梯队score26互链.md"
IDS_FILE = Path(__file__).resolve().parent / "_tier12_ids.txt"

GROUPS: dict[str, list[str]] = {
    "小厮·跟班": [
        "引泉", "挑云", "扫花", "伴鹤", "四儿", "同喜", "同贵", "坠儿", "小鹊",
        "墨雨", "玻璃", "翡翠",
    ],
    "买办·管事·王府": [
        "钱华", "戴权", "镇国公", "乌进孝", "锦乡侯", "赵亦华", "王尔调",
        "东平郡王", "南安郡王", "夏守忠", "赖大", "旺儿", "兴儿",
    ],
    "学塾·赵房·露剂": [
        "金荣", "玉爱", "香怜", "钱槐", "小蝉", "小吉祥儿", "马道婆",
        "秦业", "秦钟", "贾代儒", "贾芹",
    ],
    "戏伶·梨香": [
        "芳官", "龄官", "茜官", "菂官", "藕官", "宝官", "玉官",
        "艾官", "茄官", "葵官", "豆官",
    ],
    "刑名·穷亲·楔子": [
        "多官", "张三", "吴良", "王成", "霍启", "守备", "卜世仁",
        "冯渊", "张华", "张金哥", "石呆子", "冷子兴", "云光",
    ],
    "甄家·诗典·方外": [
        "甄应嘉", "甄宝玉", "傅秋芳", "傅试", "林四娘", "净虚", "胡庸医",
        "神瑛侍者", "绛珠仙子", "渺渺真人", "茫茫大士", "葫芦僧",
    ],
    "怡红·蘅芜·近侍": [
        "喜儿", "彩鸾", "彩屏", "傻大姐", "坠儿", "碧痕", "入画",
        "晴雯", "麝月", "小红", "五儿", "莺儿", "琥珀", "碧月",
        "紫鹃", "雪雁", "佳蕙",
    ],
    "宁荣谱系·早亡": ["贾敷", "贾菌", "贾璜", "贾源", "贾演", "贾敬", "贾珠"],
    "姻亲·寡妇·远房": [
        "李婶", "李纹", "李绮", "王仁", "邢岫烟", "柳湘莲", "尤三姐",
        "嫣红", "翠云", "鲍二", "鲍二家的", "周姨娘", "夏婆子", "夏金桂",
    ],
    "清客·门客": ["单聘仁", "王太医", "詹光", "娇杏", "封肃", "板儿", "青儿"],
}


def load_archived() -> list[str]:
    if IDS_FILE.exists():
        return [ln.strip() for ln in IDS_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return []


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
        if s == 26:
            summary = (fm.get("summary") or "").split("；")[0][:48]
            rows.append((s, cid, summary))
    return sorted(rows)


def build(rows: list[tuple[int, str, str]], archived: list[str]) -> str:
    all_ids = set(archived) if archived else {cid for _, cid, _ in rows}
    assigned: set[str] = set()
    lines = [
        "---",
        "type: topic",
        f"book: {BOOK}",
        "title: 第十二梯队score26互链",
        f"derived_from: [{', '.join(sorted(all_ids)[:20])}, lint, score26]",
        "created: 2026-06-16",
        "tags: [lint, 互链, 配角, 索引, score26, 归档]",
        "summary: 2026-06-16 原 score=26 共 108 页归档索引；hub/rel 压平后 score 均已 ≥27。",
        "---",
        "",
        "## 结论",
        "",
    ]
    if archived and not rows:
        lines.append(
            f"本页归档 **{len(all_ids)}** 个原 score=26 配角（2026-06-16 `/dream` hub/rel 压平后，"
            f"`/lint` 该带 **0** 页）。按职能分组互链，便于从主题纵切回指人物 card。"
        )
    else:
        lines.append(
            f"本页索引 **{len(rows)}** 个 score=26 配角页，按职能分组互链。"
        )
    lines.append("")

    char_dir = CHAR_DIR / BOOK

    def line_for(cid: str) -> str:
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
        "- [[第七梯队低密度互链]] · [[零入链配角互链]] · [[清客门客链]] · "
        "[[宝玉小厮链]] · [[图鉴名物信物链总览]]"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows = scan()
    archived = load_archived()
    text = build(rows, archived)
    OUT.write_text(text, encoding="utf-8")
    label = "archived" if not rows else "active"
    print(f"wrote {OUT.name}: {len(rows) or len(archived)} characters ({label})")


if __name__ == "__main__":
    main()
