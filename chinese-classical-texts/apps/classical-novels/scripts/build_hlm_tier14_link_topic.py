#!/usr/bin/env python3
"""/dream 第十四梯队 — 生成 score=28 归档互链索引页。

用法: python scripts/build_hlm_tier14_link_topic.py
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, CONTENT, parse_frontmatter  # noqa: E402

BOOK = "红楼梦"
OUT = CONTENT / "topics" / BOOK / "第十四梯队score28互链.md"
IDS_FILE = Path(__file__).resolve().parent / "_tier14_ids.txt"

GROUPS: dict[str, list[str]] = {
    "王府·国公·钦差": [
        "东平郡王", "南安郡王", "西宁郡王", "北静王", "锦乡侯", "镇国公",
        "戴权", "夏守忠", "乌进孝",
    ],
    "管家·买办·仆从": [
        "钱华", "戴良", "吴新登", "林之孝", "赖大", "旺儿", "兴儿", "来旺家的",
        "周瑞", "周瑞家的", "王善保家的", "善姐", "包勇", "焦大", "李贵",
    ],
    "小厮·跟班": [
        "引泉", "挑云", "扫花", "扫红", "伴鹤", "茗烟", "锄药", "墨雨",
        "四儿", "同喜", "同贵", "焙茗",
    ],
    "怡红·蘅芜·近侍": [
        "秋纹", "彩云", "素云", "绣鸾", "碧痕", "五儿", "莺儿", "琥珀",
        "傻大姐", "佳蕙", "喜儿", "彩鸾", "彩屏",
    ],
    "戏伶·梨香": [
        "芳官", "龄官", "茜官", "菂官", "藕官", "宝官", "玉官",
        "艾官", "茄官", "葵官", "豆官",
    ],
    "学塾·赵房": [
        "金荣", "玉爱", "香怜", "钱槐", "小蝉", "马道婆", "秦业", "贾代儒",
    ],
    "刑名·穷亲·楔子": [
        "多官", "张三", "吴良", "王成", "霍启", "守备", "冯渊", "张华",
        "张金哥", "云光", "卜世仁", "石呆子",
    ],
    "甄家·方外·诗典": [
        "甄应嘉", "甄宝玉", "傅秋芳", "傅试", "林四娘", "净虚", "胡庸医",
        "渺渺真人", "茫茫大士",
    ],
    "姻亲·远房·寡妇": [
        "李婶", "李纹", "李绮", "王仁", "邢岫烟", "柳湘莲", "尤三姐",
        "嫣红", "翠云", "鲍二", "周姨娘", "夏婆子",
    ],
    "清客·门客·医": ["单聘仁", "王太医", "詹光", "张友士", "娇杏", "封肃"],
    "宁荣谱系·早亡": ["贾敷", "贾菌", "贾璜", "贾源", "贾演", "贾敬", "贾珠", "贾代善"],
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
        if s == 28:
            summary = (fm.get("summary") or "").split("；")[0][:48]
            rows.append((s, cid, summary))
    return sorted(rows)


def build(rows: list[tuple[int, str, str]], archived: list[str]) -> str:
    all_ids = set(archived) if archived else {cid for _, cid, _ in rows}
    assigned: set[str] = set()
    n = len(all_ids)
    lines = [
        "---",
        "type: topic",
        f"book: {BOOK}",
        "title: 第十四梯队score28互链",
        f"derived_from: [lint, score28, 归档{n}人]",
        "created: 2026-06-16",
        "tags: [lint, 互链, 配角, 索引, score28, 归档]",
        f"summary: 2026-06-16 原 score=28 共 {n} 页归档索引；hub/rel 压平后 score 均已 ≥29。",
        "---",
        "",
        "## 结论",
        "",
        f"本页归档 **{n}** 个原 score=28 配角（`/dream` hub/rel 压平后，`/lint` 该带 **0** 页）。"
        "按职能分组互链，便于从主题纵切回指人物 card。",
        "",
    ]

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
        "- [[第十三梯队score27互链]] · [[第十二梯队score26互链]] · [[零入链配角互链]] · "
        "[[宝玉小厮链]] · [[四王八公王府链]] · [[图鉴名物信物链总览]]"
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
