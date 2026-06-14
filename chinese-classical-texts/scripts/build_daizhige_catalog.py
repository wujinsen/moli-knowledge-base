#!/usr/bin/env python3
"""Scan raw/daizhige/*.txt and write catalog markdown under docs/daizhige-catalog/."""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAIZHIGE = ROOT / "raw" / "daizhige"
OUT_DIR = ROOT / "docs" / "daizhige-catalog"

# 殆知阁「藏」→ 逻辑实体家族 / 建议前端 app（藏级默认）
ZANG_META: dict[str, tuple[str, str]] = {
    "佛藏": ("义理思想", "classical-canon"),
    "道藏": ("义理思想", "classical-canon"),
    "儒藏": ("义理思想", "classical-canon"),
    "易藏": ("义理思想", "classical-canon"),
    "史藏": ("史籍", "classical-history"),
    "诗藏": ("诗文集", "classical-poetry"),  # 剧曲见下方子类覆盖
    "集藏": ("诗文集", "classical-poetry"),  # 小说/演义等见子类覆盖
    "医藏": ("工具博物", "classical-encyclopedia"),
    "子藏": ("工具博物", "classical-encyclopedia"),  # 诸子/法家见覆盖
    "艺藏": ("工具博物", "classical-encyclopedia"),
}

# 子类覆盖藏级默认（folder 级规则，零成本修正一刀切误差）
SUBCLASS_OVERRIDE: dict[tuple[str, str], tuple[str, str]] = {
    # 章回叙事
    ("集藏", "小说"): ("章回叙事", "classical-novels"),
    ("集藏", "演义"): ("章回叙事", "classical-novels"),
    ("集藏", "话本"): ("章回叙事", "classical-novels"),
    ("集藏", "宝卷"): ("章回叙事", "classical-novels"),
    ("诗藏", "剧曲"): ("章回叙事", "classical-novels"),  # 散曲为诗，待 ingest 文件级再分
    # 子藏中的思想类 → 义理思想（非工具博物）
    ("子藏", "诸子"): ("义理思想", "classical-canon"),
    ("子藏", "法家"): ("义理思想", "classical-canon"),
    # 儒藏中的工具/教育类 → 工具博物（非义理思想）
    ("儒藏", "小学"): ("工具博物", "classical-encyclopedia"),
    ("儒藏", "启蒙蒙学"): ("工具博物", "classical-encyclopedia"),
    # 易藏术数偏实用占卜 → 工具博物（易经留义理思想）
    ("易藏", "术数"): ("工具博物", "classical-encyclopedia"),
}


def classify(zang: str, subclass: str) -> tuple[str, str]:
    if (zang, subclass) in SUBCLASS_OVERRIDE:
        return SUBCLASS_OVERRIDE[(zang, subclass)]
    return ZANG_META.get(zang, ("未分类", "—"))


def parse_entry(path: Path) -> dict:
    rel = path.relative_to(DAIZHIGE)
    parts = rel.parts
    zang = parts[0]
    subclass = parts[1] if len(parts) > 2 else "—"
    title = path.stem
    family, app = classify(zang, subclass if subclass != "—" else "")
    return {
        "title": title,
        "zang": zang,
        "subclass": subclass,
        "path": rel.as_posix(),
        "family": family,
        "app": app,
    }


def esc_cell(s: str) -> str:
    return s.replace("|", "\\|")


def write_zang_file(zang: str, entries: list[dict]) -> None:
    by_sub: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_sub[e["subclass"]].append(e)

    lines = [
        f"# 殆知阁目录 · {zang}",
        "",
        f"共 **{len(entries)}** 种。",
        "",
        "| 子类 | 册数 | 实体家族 | 建议 app |",
        "|------|------|----------|----------|",
    ]
    for sub in sorted(by_sub, key=lambda x: (-len(by_sub[x]), x)):
        fam, app = classify(zang, sub)
        lines.append(f"| {sub} | {len(by_sub[sub])} | {fam} | `{app}` |")

    lines.extend(["", "---", ""])

    for sub in sorted(by_sub, key=lambda x: (-len(by_sub[x]), x)):
        fam, app = classify(zang, sub)
        lines.append(f"## {sub}（{len(by_sub[sub])}）")
        lines.append("")
        lines.append(f"实体家族：**{fam}** · app：`{app}`")
        lines.append("")
        lines.append("| 书名 | 相对路径 |")
        lines.append("|------|----------|")
        for e in sorted(by_sub[sub], key=lambda x: x["title"]):
            lines.append(f"| {esc_cell(e['title'])} | `{esc_cell(e['path'])}` |")
        lines.append("")

    out = OUT_DIR / f"{zang}.md"
    out.write_text("\n".join(lines), encoding="utf-8")


def write_index(all_entries: list[dict], zang_counts: Counter) -> None:
    family_counts: Counter = Counter()
    app_counts: Counter = Counter()
    for e in all_entries:
        family_counts[e["family"]] += 1
        app_counts[e["app"]] += 1

    lines = [
        "# 殆知阁全书目录（daizhige catalog）",
        "",
        f"> 生成日期：{date.today().isoformat()}",
        f"> 数据源：`raw/daizhige/`（只读，路径即分类）",
        f"> 总册数：**{len(all_entries)}**",
        "",
        "## 按「藏」统计",
        "",
        "| 藏 | 册数 | 实体家族（默认） | 建议 app | 明细 |",
        "|----|------|------------------|----------|------|",
    ]
    for zang in sorted(zang_counts, key=lambda z: -zang_counts[z]):
        fam, app = ZANG_META.get(zang, ("—", "—"))
        lines.append(
            f"| {zang} | {zang_counts[zang]} | {fam} | `{app}` | [{zang}.md](./{zang}.md) |"
        )

    lines.extend(
        [
            "",
            "## 按实体家族（逻辑分类）",
            "",
            "子类有特殊规则的见各藏明细（如集藏/小说 → 章回叙事）。",
            "",
            "| 实体家族 | 册数 | 建议 app |",
            "|----------|------|----------|",
        ]
    )
    for fam in sorted(family_counts, key=lambda x: -family_counts[x]):
        apps = sorted({e["app"] for e in all_entries if e["family"] == fam})
        app_str = ", ".join(f"`{a}`" for a in apps)
        lines.append(f"| {fam} | {family_counts[fam]} | {app_str} |")

    lines.extend(
        [
            "",
            "## 按建议前端 app",
            "",
            "| app | 册数 | 说明 |",
            "|-----|------|------|",
            (
                "| `classical-novels` | "
                f"{app_counts.get('classical-novels', 0)} | "
                "章回小说、演义、话本、宝卷、剧曲 |"
            ),
            (
                "| `classical-poetry` | "
                f"{app_counts.get('classical-poetry', 0)} | "
                "诗文集、别集、词话诗话等 |"
            ),
            (
                "| `classical-history` | "
                f"{app_counts.get('classical-history', 0)} | "
                "正史、编年、地理、职官等（含史记） |"
            ),
            (
                "| `classical-canon` | "
                f"{app_counts.get('classical-canon', 0)} | "
                "佛/道/儒经/易经 + 诸子/法家（内部按传统分子集） |"
            ),
            (
                "| `classical-encyclopedia` | "
                f"{app_counts.get('classical-encyclopedia', 0)} | "
                "医、子（类书/兵农算）、艺 + 小学/蒙学/术数 |"
            ),
            "",
            "## 子类覆盖规则（修正藏级一刀切）",
            "",
            "| 子类 | 藏级默认 | 覆盖为 | 理由 |",
            "|------|----------|--------|------|",
            "| 集藏/小说·演义·话本·宝卷 | 诗文集 | 章回叙事 | 人物·回目·关系 |",
            "| 诗藏/剧曲 | 诗文集 | 章回叙事 | 戏剧叙事（散曲属诗，待 ingest 细分） |",
            "| 子藏/诸子·法家 | 工具博物 | 义理思想 | 先秦诸子/法家思想，非工具 |",
            "| 儒藏/小学·启蒙蒙学 | 义理思想 | 工具博物 | 文字训诂/童蒙读物，非经义 |",
            "| 易藏/术数 | 义理思想 | 工具博物 | 占卜命理偏实用（易经留义理思想） |",
            "",
            "## 史藏子类说明（含史记）",
            "",
            "史藏按文献体裁分子类，**正史**（如《史记》）与**编年**、**地理**、**传记**等并列，",
            "均属 `classical-history`，UI 可按子类切换视图（纪传体 / 编年体 / 地志等）。",
            "",
            "## 分藏书目",
            "",
        ]
    )
    for zang in sorted(zang_counts, key=lambda z: -zang_counts[z]):
        lines.append(f"- [{zang}](./{zang}.md)（{zang_counts[zang]} 种）")

    lines.append("")
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not DAIZHIGE.is_dir():
        print(f"Missing: {DAIZHIGE}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    by_zang: dict[str, list[dict]] = defaultdict(list)

    for path in sorted(DAIZHIGE.rglob("*.txt")):
        e = parse_entry(path)
        entries.append(e)
        by_zang[e["zang"]].append(e)

    zang_counts = Counter(e["zang"] for e in entries)
    write_index(entries, zang_counts)
    for zang, z_entries in sorted(by_zang.items()):
        write_zang_file(zang, z_entries)

    print(f"Wrote {len(entries)} entries to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
