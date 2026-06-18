#!/usr/bin/env python3
"""第十二梯队 trust_guard 扫尾 — 删/改 tier12 误补情节与关系。

用法: python scripts/patch_hlm_tier12_guard_fix.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import parse_frontmatter  # noqa: E402
from lint_character_density import density_score  # noqa: E402
from patch_hlm_tier10_score22 import (  # noqa: E402
    BOOK,
    add_relations,
    pick_relation,
    scan_pages,
    write_page,
)

# 精确删除的情节行（整行匹配，去首尾空白）
DROP_PLOTS: dict[str, list[str]] = {
    "净虚": ["第16回：水月庵与净虚、张金哥案相连。"],
    "单大良": [
        "第72回：宝钗生日后，尤氏协理，府内年例管事仍含单大良家一类（与第54回年酒并见）。"
    ],
    "坠儿": ["第56回：宋妈妈拿镯子，称小丫头子坠儿偷起来的。"],
    "引泉": ["第52回：与李贵、赵亦华等扈从，随宝玉出门时列于小厮行列。"],
    "张三": ["第4回：原告称拐子先收冯家银子，又悄悄卖与薛家，争买殴伤人命。"],
    "张友士": ["第10回：张友士为秦可卿诊脉，尤氏荐医。"],
    "戴良": ["第14回：协理宁府，来旺媳妇持对牌至仪门，与账房戴良等支取呈文纸札。"],
    "扫红": ["第57回：宝玉病中，林之孝家的等来瞧，扫红等与墨雨同列怡红院小厮。"],
    "扫花": ["第52回：随宝玉出门，与茗烟、锄药等同在扈从之列。"],
    "挑云": ["第52回：随宝玉出门，与引泉、扫花等同列小厮。"],
    "来旺家的": ["第69回：来旺家的献计赚张华，尤二姐案收尾。"],
    "潘又安": ["第77回：司棋被搜出潘又安情帖，迎春不能作主。"],
    "玉钏儿": ["第18回：元春省亲后，玉钏儿等与众人赏宴。"],
    "王善保家的": ["第71回：邢夫人房中，王善保家的常随邢夫人、贾赦一房当差。"],
    "王狗儿": ["第41回：刘姥姥二进荣府，狗儿在家耕种，姥姥带青板入园见贾母。"],
    "秋桐": ["第70回：尤二姐发殡后，秋桐仍在贾琏房，与凤姐、平儿同场叙事。"],
    "西宁郡王": ["第13回：可卿丧仪，内侍昭儿往西宁郡王府等处送领凭牌（与路祭并见）。"],
    "詹光": ["第52回：贾母议园内冬天炕桌吃饭，詹光等与清客同列随侍场。"],
    "贾代善": ["第53回：宁府宗祠祭祀，代善与源、演等神主并列。"],
    "镇国公": ["第13回：可卿丧仪，内侍昭儿往镇国公府等处送领凭牌、代求天恩义冢。"],
    "鹦哥": ["第40回：两宴大观园，鹦哥等随侍贾母行令。"],
}

# guard-safe 替换情节（删后 plot<3 或 score<27 时追加）
ADD_PLOTS: dict[str, list[str]] = {
    "玉钏儿": ["第57回：雪雁与玉钏儿姐姐坐在下房里说话儿。"],
}

# 删除的关系 target
DROP_REL_TARGETS: dict[str, list[str]] = {
    "卫若兰": ["史湘云"],
    "张三": ["香菱"],
    "彩屏": ["智能"],
    "林四娘": ["詹光"],
    "甄应嘉": ["甄夫人"],
}

TARGET_SCORE = 27


def drop_plot_lines(body: str, drops: list[str]) -> str:
    if not drops:
        return body
    drop_set = {d.strip() for d in drops}
    out: list[str] = []
    in_plots = False
    for line in body.splitlines():
        if line.strip() == "## 关键情节":
            in_plots = True
            out.append(line)
            continue
        if in_plots and line.startswith("## "):
            in_plots = False
        if in_plots and line.strip().startswith("- "):
            text = line.strip()[2:].strip()
            if text in drop_set:
                continue
        out.append(line)
    return "\n".join(out) + ("\n" if body.endswith("\n") else "")


def add_plot_lines(body: str, adds: list[str]) -> str:
    if not adds:
        return body
    existing = set()
    in_plots = False
    for line in body.splitlines():
        if line.strip() == "## 关键情节":
            in_plots = True
            continue
        if in_plots and line.startswith("## "):
            break
        if in_plots and line.strip().startswith("- "):
            existing.add(line.strip()[2:].strip())
    to_add = [a for a in adds if a not in existing]
    if not to_add:
        return body
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if line.strip() != "## 关键情节":
            continue
        j = i + 1
        while j < len(lines) and not (lines[j].startswith("## ") and lines[j].strip() != "## 关键情节"):
            if lines[j].strip().startswith("- "):
                j += 1
                continue
            if lines[j].strip() == "":
                j += 1
                continue
            break
        for add in reversed(to_add):
            lines.insert(j, f"- {add}")
        break
    return "\n".join(lines) + ("\n" if body.endswith("\n") else "")


def drop_relations(fm: dict, targets: list[str]) -> bool:
    rels = fm.get("relations") or []
    drop = set(targets)
    new = [r for r in rels if r.get("target") not in drop]
    if len(new) == len(rels):
        return False
    fm["relations"] = new
    return True


def count_plots(body: str) -> int:
    m = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    if not m:
        return 0
    return sum(1 for ln in m.group(1).splitlines() if ln.strip().startswith("-"))


def page_score(fm: dict, body: str, inbound: int) -> int:
    return density_score(
        {
            "rel": len(fm.get("relations") or []),
            "plot": count_plots(body),
            "main": "## 主要关系" in body,
            "review": "## 评析" in body,
            "inbound": inbound,
        }
    )


def patch_file(
    cid: str,
    path: Path,
    pages: dict,
    inbound: dict,
    all_fms: dict,
    chapter_cache: dict,
    dry_run: bool,
) -> list[str]:
    fm, body = parse_frontmatter(path)
    changes: list[str] = []

    new_body = drop_plot_lines(body, DROP_PLOTS.get(cid, []))
    if new_body != body:
        n = len(DROP_PLOTS[cid])
        changes.append(f"drop {n} plot(s)")
        body = new_body

    new_body = add_plot_lines(body, ADD_PLOTS.get(cid, []))
    if new_body != body:
        changes.append(f"add plot(s)")
        body = new_body

    if drop_relations(fm, DROP_REL_TARGETS.get(cid, [])):
        changes.append(f"drop rel→{DROP_REL_TARGETS[cid]}")

    if not changes:
        return []

    inb = len(inbound.get(cid, set()))
    score = page_score(fm, body, inb)
    if score < TARGET_SCORE:
        rel = pick_relation(cid, pages, all_fms, chapter_cache)
        if rel and add_relations(fm, rel):
            changes.append(f"+rel→{rel['target']} (score {score}→{page_score(fm, body, inb)})")

    if not dry_run:
        fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")

    return changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pages, inbound = scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}
    touched: list[str] = []

    for cid in sorted(set(DROP_PLOTS) | set(DROP_REL_TARGETS) | set(ADD_PLOTS)):
        info = pages.get(cid)
        if not info:
            print(f"skip missing {cid}")
            continue
        ch = patch_file(cid, info["path"], pages, inbound, all_fms, chapter_cache, args.dry_run)
        if ch:
            touched.append(f"{cid}: {', '.join(ch)}")
            if not args.dry_run:
                fm, body = parse_frontmatter(info["path"])
                info["fm"] = fm
                info["body"] = body
                info["rel"] = len(fm.get("relations") or [])
                info["plot"] = count_plots(body)
                all_fms[cid] = (info["path"], fm, body)

    print(f"patched {len(touched)} pages")
    for t in touched:
        print(" ", t)

    if not args.dry_run and touched:
        mins = min(
            page_score(info["fm"], info["body"], len(inbound.get(cid, set())))
            for cid, info in pages.items()
        )
        print(f"min score after patch: {mins}")


if __name__ == "__main__":
    main()
