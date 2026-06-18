#!/usr/bin/env python3
"""/dream 第七梯队 — score 15–18 中 plot=1 页补第二条情节。

用法: python scripts/patch_hlm_tier7_score18.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, parse_frontmatter  # noqa: E402

BOOK = "红楼梦"

PLOT_ADD: dict[str, str] = {
    "东平郡王": "第11回：贾敬寿辰，东平郡王等与北静、南安诸客来贺宁府。",
    "小鹊": "第73回：小鹊直进怡红院找宝玉，晴雯等在场；宝玉如闻紧箍咒，连夜温书。",
    "来升": "第14回：次日凤姐与来升媳妇分派花名册，定卯正点卯等规制。",
    "钱华": "第8回：与詹光、单聘仁清客同索宝玉斗方字画。",
    "双寿": "第28回：冯紫英家射猎，双寿与焙茗、锄药、双瑞随侍。",
    "双瑞": "第28回：冯紫英家射猎，双瑞与焙茗、锄药、双寿随侍。",
    "引泉": "第24回：贾芸来访绮霰斋，引泉等与伴鹤等收束行礼。",
    "扫花": "第24回：与锄药下象棋，又与引泉、挑云等在檐上掏雀儿。",
    "挑云": "第24回：与引泉、扫花、伴鹤等在檐上掏雀儿。",
}


def count_plots(body: str) -> int:
    import re

    plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    if not plot_sec:
        return 0
    return sum(1 for ln in plot_sec.group(1).splitlines() if ln.strip().startswith("-"))


def add_plot(body: str, line: str) -> str:
    import re

    plot_match = re.search(r"(## 关键情节\s*\n.*?)(\n## )", body, re.S)
    if not plot_match:
        return body
    block = plot_match.group(1)
    if line.strip() in block:
        return body
    new_block = block.rstrip() + f"\n- {line}\n"
    return body[: plot_match.start(1)] + new_block + body[plot_match.end(1) :]


def patch_file(path: Path, dry_run: bool) -> list[str]:
    fm, body = parse_frontmatter(path)
    cid = str(fm.get("id") or path.stem)
    plot_line = PLOT_ADD.get(cid)
    if not plot_line or count_plots(body) != 1:
        return []

    new_body = add_plot(body, plot_line)
    if new_body == body:
        return []

    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    text = f"---\n{fm_text}---\n{new_body}"
    if not dry_run:
        path.write_text(text, encoding="utf-8")
    return [f"{cid}: +1 plot"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    char_dir = CHAR_DIR / BOOK
    changes: list[str] = []
    for cid in sorted(PLOT_ADD):
        path = char_dir / f"{cid}.md"
        if not path.exists():
            print(f"WARN missing {path}")
            continue
        changes.extend(patch_file(path, args.dry_run))

    print(f"patched {len(changes)}")
    for c in changes:
        print(" ", c)


if __name__ == "__main__":
    main()
