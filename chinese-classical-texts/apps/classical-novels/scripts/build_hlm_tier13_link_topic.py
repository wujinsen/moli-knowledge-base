#!/usr/bin/env python3
"""/dream 第十三梯队 — 生成 score=27 归档互链索引页。

用法: python scripts/build_hlm_tier13_link_topic.py
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, CONTENT, parse_frontmatter  # noqa: E402

BOOK = "红楼梦"
OUT = CONTENT / "topics" / BOOK / "第十三梯队score27互链.md"
IDS_FILE = Path(__file__).resolve().parent / "_tier13_ids.txt"

GROUPS: dict[str, list[str]] = {
    "赵房·抄检·露剂": [
        "马道婆", "周瑞家的", "喜儿", "佳蕙", "菂官", "小鹊", "赵亦华",
    ],
    "怡红·近侍": ["秋纹", "彩云", "素云", "绣鸾"],
    "管家·仆从": ["李贵", "焦大", "包勇", "善姐"],
    "学塾": ["玉爱"],
    "甄家·楔子·刑名": ["甄应嘉", "傅秋芳", "守备", "吴良", "胡庸医"],
    "姻亲·谱系": ["贾敏", "贾敷", "贾璜", "孙绍祖", "李婶"],
    "出场·名伶": ["妙玉", "珍珠", "蒋玉菡"],
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
        if s == 27:
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
        "title: 第十三梯队score27互链",
        f"derived_from: [{', '.join(sorted(all_ids)[:20])}, lint, score27]",
        "created: 2026-06-16",
        "tags: [lint, 互链, 配角, 索引, score27, 归档]",
        "summary: 2026-06-16 原 score=27 共 29 页归档索引；hub/rel 压平后 score 均已 ≥28。",
        "---",
        "",
        "## 结论",
        "",
    ]
    if archived and not rows:
        lines.append(
            f"本页归档 **{len(all_ids)}** 个原 score=27 配角（2026-06-16 `/dream` hub/rel 压平后，"
            f"`/lint` 该带 **0** 页）。按职能分组互链，便于从主题纵切回指人物 card。"
        )
    else:
        lines.append(f"本页索引 **{len(rows)}** 个 score=27 配角页，按职能分组互链。")
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
        "- [[第十二梯队score26互链]] · [[第七梯队低密度互链]] · [[零入链配角互链]] · "
        "[[赵姨娘房链]] · [[宝玉小厮链]] · [[图鉴名物信物链总览]]"
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
