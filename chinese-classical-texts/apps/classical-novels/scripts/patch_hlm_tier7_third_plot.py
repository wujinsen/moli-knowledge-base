#!/usr/bin/env python3
"""/dream 第七梯队 — 41 页各补第 3 条可核情节（plot<3 时追加）。

用法: python scripts/patch_hlm_tier7_third_plot.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, parse_frontmatter  # noqa: E402

BOOK = "红楼梦"

# 第七梯队低密度互链 41 页（固定名单，不依赖 scan 分数带）
TIER7_IDS: list[str] = [
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

# 仅 plot 条数 < 3 时写入
PLOT_THIRD: dict[str, str] = {
    "同喜": "第29回：端阳初一日，同喜、同贵列薛姨妈随侍丫鬟，与香菱及其丫头臻儿等同在清虚观车队。",
    "同贵": "第29回：贾母出游清虚观，薛姨妈丫头同喜、同贵与香菱等同往，始具名同列（与第67回节礼并读）。",
    "小鹊": "第73回：击院门入怡红院，袭人命留吃茶，小鹊因怕关门已闭，不答门外问话，回身即去。",
    "镇国公": "第13回：可卿丧仪，内侍昭儿往镇国公府等处送领凭牌、代求天恩义冢（与第14回路祭并见）。",
    "赵亦华": "第52回：贾母议冬天园内炕桌吃饭，宝玉记挂晴雯先回园；次日出门，赵亦华与王荣、钱启等六清客带小厮扈从。",
    "小蝉": "第60回：赵姨娘房小蝉以果掷雀儿，与春燕、柳家的口角，牵连后文蔷薇硝、厨房争利。",
    "菂官": "第58回：芳官向宝玉说明，藕官所祭菂官在戏中分饰夫妻（药官、菂官），「两个人原是一体」——点明菂官为小旦、早亡在祭前。",
    "张三": "第86回：刑部开审，尸叔张二、当槽李二并邻保作证；张王氏哭禀独子张三在李家店当槽，酒碗误碰卤门致死。",
    "胡庸医": "第51回：后门锁引入诊晴雯，开方含枳实、麻黄；宝玉闻而怒，命茗烟另请王太医，并以一两银打发胡庸医。",
    "喜儿": "第35回：莲叶羹至怡红院，宝玉欲把羹传与袭人，袭人推却；喜儿同莺儿在侧捧盒侍立。",
    "贾敷": "第2回：冷子兴演说，贾代善长子敷早亡无后，敬袭宁国公——宁府长房早亡、次房当家的谱系关键。",
    "贾璜": "第10回：璜大奶奶坐车上宁府欲评理，尤氏以「爷们的事你省得什么」劝止，只得含怒回家。",
    "翠云": "第74回：抄检前凤姐与贾琏论邢夫人挪当，并提邢夫人曾带嫣红、翠云等年轻侍妾入园，为长房秽乱伏线。",
    "茄官": "第58回：王夫人定议给银遣散十二女伶，称「当日老祖宗手里都是有这例的」；茄官等工老旦，尤氏独讨去。",
}


def count_plots(body: str) -> int:
    plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    if not plot_sec:
        return 0
    return sum(1 for ln in plot_sec.group(1).splitlines() if ln.strip().startswith("-"))


def add_plot(body: str, line: str) -> str:
    plot_match = re.search(r"(## 关键情节\s*\n.*?)(\n## )", body, re.S)
    if not plot_match:
        return body
    block = plot_match.group(1)
    if line.strip() in block:
        return body
    new_block = block.rstrip() + f"\n- {line}\n"
    return body[: plot_match.start(1)] + new_block + body[plot_match.end(1) :]


def patch_file(path: Path, dry_run: bool) -> str | None:
    cid = path.stem
    plot_line = PLOT_THIRD.get(cid)
    if not plot_line:
        return None

    fm, body = parse_frontmatter(path)
    n = count_plots(body)
    if n >= 3:
        return None

    new_body = add_plot(body, plot_line)
    if new_body == body:
        return None

    if dry_run:
        print(f"[dry-run] {cid}: plot {n} -> {count_plots(new_body)}")
        return f"{cid}: +1 plot ({n}->{count_plots(new_body)})"

    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{new_body}", encoding="utf-8")
    return f"{cid}: +1 plot ({n}->{count_plots(new_body)})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    char_dir = CHAR_DIR / BOOK
    changes: list[str] = []
    skipped_has3 = 0

    for cid in TIER7_IDS:
        path = char_dir / f"{cid}.md"
        if not path.exists():
            print(f"WARN missing {path}")
            continue
        fm, body = parse_frontmatter(path)
        if count_plots(body) >= 3:
            skipped_has3 += 1
            continue
        msg = patch_file(path, args.dry_run)
        if msg:
            changes.append(msg)

    print(f"tier7={len(TIER7_IDS)} already_3plot={skipped_has3} patched={len(changes)}")
    for c in changes:
        print(" ", c)


if __name__ == "__main__":
    main()
