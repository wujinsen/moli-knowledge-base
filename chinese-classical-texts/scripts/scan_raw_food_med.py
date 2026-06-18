#!/usr/bin/env python3
"""Scan raw/ for books related to food and medicine."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "raw"
OUT = Path(__file__).resolve().parents[1] / "_raw_food_med_scan.txt"

FOOD_KEYS = ["食", "饮", "膳", "馔", "菜", "酒", "茶", "谱", "糕", "粥", "厨"]
MED_KEYS = ["医", "药", "本草", "方", "疗", "养生", "脉", "伤寒", "千金", "诊"]


def main() -> None:
    lines: list[str] = []
    lines.append("# raw 目录概览\n")

    for p in sorted(ROOT.iterdir()):
        if p.is_dir():
            n = sum(1 for f in p.rglob("*") if f.is_file())
            lines.append(f"- `{p.name}/` — {n} 个文件")

    dz = ROOT / "daizhige"
    lines.append("\n## daizhige 十藏（.txt 数量）\n")
    cang_counts: dict[str, int] = {}
    for p in sorted(dz.iterdir()):
        if not p.is_dir():
            continue
        n = len(list(p.rglob("*.txt")))
        cang_counts[p.name] = n
        lines.append(f"- **{p.name}**：{n}")

    matched: list[tuple[str, str, str]] = []
    for f in sorted(dz.rglob("*.txt")):
        name = f.stem
        rel = str(f.relative_to(ROOT)).replace("\\", "/")
        cang = f.relative_to(dz).parts[0]
        if any(k in name for k in FOOD_KEYS + MED_KEYS):
            matched.append((name, rel, cang))

    food_books: list[tuple[str, str, str]] = []
    med_books: list[tuple[str, str, str]] = []
    both: list[tuple[str, str, str]] = []
    for name, rel, cang in matched:
        is_f = any(k in name for k in FOOD_KEYS)
        is_m = any(k in name for k in MED_KEYS)
        if is_f and is_m:
            both.append((name, rel, cang))
        elif is_f:
            food_books.append((name, rel, cang))
        elif is_m:
            med_books.append((name, rel, cang))

    yicang = cang_counts.get("医藏", 0)
    lines.append(f"\n## 书名含饮食/医学关键词（共 {len(matched)} 部；**医藏**整库另有 {yicang} 部）\n")
    lines.append(f"- 偏饮食：**{len(food_books)}**")
    lines.append(f"- 偏医学（十藏内、医藏目录外）：**{sum(1 for _, r, _ in med_books if '/医藏/' not in r)}**")
    lines.append(f"- 饮食+医学（食疗等）：**{len(both)}**")

    lines.append("\n### 饮食+医学\n")
    for name, rel, cang in both:
        lines.append(f"- [{cang}] {name} — `{rel}`")

    lines.append("\n### 偏饮食（书名匹配，全部）\n")
    for name, rel, cang in food_books:
        lines.append(f"- [{cang}] {name}")

    lines.append("\n### 偏医学 — 非医藏目录\n")
    for name, rel, cang in med_books:
        if "/医藏/" in rel:
            continue
        lines.append(f"- [{cang}] {name}")

    lines.append("\n## editions/\n")
    ed = ROOT / "editions"
    for book in sorted(ed.iterdir()):
        if not book.is_dir():
            continue
        subs = [s.name for s in sorted(book.iterdir()) if s.is_dir()]
        lines.append(f"- **{book.name}**：{', '.join(subs) if subs else '(无子目录)'}")

    lines.append("\n## 说明\n")
    lines.append("- **医藏/** 全部为医学文献（911 部），此处不逐条列出。")
    lines.append("- 小说中的宴饮、医药情节（如红楼梦、金瓶梅）见 **集藏/小说/** 与 **editions/**，书名通常不含「食/医」。")
    lines.append("- 集藏/小说 中含：`红楼梦.txt`、`金瓶梅.txt` 等，正文涉饮食医药但非专科。")

    # novels with food/med in 集藏
    lines.append("\n### 集藏/小说 — 正文涉饮食医药的章回小说\n")
    novel_dir = dz / "集藏" / "小说"
    if novel_dir.is_dir():
        for f in sorted(novel_dir.glob("*.txt")):
            n = f.stem
            if any(k in n for k in ["红楼", "金瓶", "水浒", "西游记", "儒林", "镜花"]):
                lines.append(f"- {n}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
