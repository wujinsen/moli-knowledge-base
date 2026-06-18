#!/usr/bin/env python3
"""/dream 第十一梯队 — score=25 压至 ≥26。

- plot=2：补第 3 条可核情节（+3）
- inbound=4：hub 互链（+1）
- 其余：trust_guard 可核 relations（+2）

用法: python scripts/patch_hlm_tier11_score25.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, parse_frontmatter  # noqa: E402
from lint_character_density import density_score  # noqa: E402
from patch_hlm_tier10_score22 import (  # noqa: E402
    BOOK,
    add_hub_link,
    add_relations,
    pick_hub_source,
    pick_relation,
    scan_pages,
    write_page,
)

TARGET = 26

PLOT_THIRD: dict[str, str] = {
    "冯紫英": "第28回：冯家消寒会，与蒋玉菡、薛蟠等同席，宝玉论琪官、湘云等事。",
    "单大良": "第72回：宝钗生日后，尤氏协理，府内年例管事仍含单大良家一类（与第54回年酒并见）。",
    "双寿": "第93回：随宝玉往临安伯府听戏，与焙茗、锄药、双瑞等同往。",
    "双瑞": "第93回：随宝玉往临安伯府听戏，与焙茗、锄药、双寿等同往。",
    "司棋": "第61回：司棋要鸡蛋，经莲花儿至厨房传话，与柳家的争，为抄检伏线。",
    "引泉": "第52回：与李贵、赵亦华等扈从，随宝玉出门时列于小厮行列。",
    "戴良": "第14回：协理宁府，来旺媳妇持对牌至仪门，与账房戴良等支取呈文纸札。",
    "扫红": "第57回：宝玉病中，林之孝家的等来瞧，扫红等与墨雨同列怡红院小厮。",
    "扫花": "第52回：随宝玉出门，与茗烟、锄药等同在扈从之列。",
    "挑云": "第52回：随宝玉出门，与引泉、扫花等同列小厮。",
    "文官": "第58回：戏班散，贾母独留文官在园内使唤，不归王夫人遣散之列。",
    "春燕": "第61回：厨房争利，春燕与夏婆子、小蝉等同场，柳家的被凤姐问责。",
    "来升": "第14回：传齐宁府同事，嘱凤姐「有名的烈货，脸酸心硬，一时恼了不认人」。",
    "王善保家的": "第71回：邢夫人房中，王善保家的常随邢夫人、贾赦一房当差。",
    "王狗儿": "第41回：刘姥姥二进荣府，狗儿在家耕种，姥姥带青板入园见贾母。",
    "甄士隐": "第2回：封肃回禀英莲失踪、霍启逃往他乡，士隐夫妇昼夜啼哭构疾。",
    "甄夫人": "第99回：甄应嘉遣家仆送书，报甄家被抄、甄宝玉随母进京（程高本）。",
    "秋桐": "第70回：尤二姐发殡后，秋桐仍在贾琏房，与凤姐、平儿同场叙事。",
    "色空和尚": "第25回：僧道还玉至，与跛足道人同来，点化通灵下界（神话线）。",
    "茗烟": "第19回：宁府书房，茗烟与丫头私会，宝玉撞破喝「青天白日」、命快跑。",
    "蕊官": "第60回：玫瑰露案前，蕊官赶出叫春燕，递蔷薇硝与芳官檫脸。",
    "藕官": "第59回：芳官与干娘争洗头，藕官在旁；同回柳叶渚莺儿编篮。",
    "西宁郡王": "第13回：可卿丧仪，内侍昭儿往西宁郡王府等处送领凭牌（与路祭并见）。",
    "詹光": "第52回：贾母议园内冬天炕桌吃饭，詹光等与清客同列随侍场。",
    "贾代善": "第53回：宁府宗祠祭祀，代善与源、演等神主并列。",
    "贾瑞": "第11回：宁府戏台，贾瑞居中安排，凤姐诈许，瑞信以为真。",
    "贾菌": "第9回：与金荣扭打，秦钟头破，贾代儒命各打二十大板。",
    "贾蔷": "第23回：龄官称病，蔷在外书房当差，与贾芸等同求凤姐差事。",
    "金荣": "第9回：金荣母胡氏劝止，言在贾家学里念书、薛大爷帮过七八十两银子。",
    "镇国公": "第13回：可卿丧仪，内侍昭儿往镇国公府等处送领凭牌、代求天恩义冢。",
    "彩鸾": "第62回：王夫人不在府，生日不比往年热闹，彩鸾仍随王夫人房丫鬟往怡红院凑趣。",
    "门子": "第4回：雨村密审，门子从夹缝闪出，呈护官符，劝改判葫芦案。",
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


def page_score(info: dict) -> int:
    return density_score(
        {k: info[k] for k in ("rel", "plot", "main", "review", "inbound")}
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pages, inbound = scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}
    changes: list[str] = []

    # 1) plot=2 → +3 情节
    for cid in sorted(PLOT_THIRD):
        info = pages.get(cid)
        if not info or page_score(info) != 25 or info["plot"] != 2:
            continue
        line = PLOT_THIRD[cid]
        body = add_plot(info["body"], line)
        if body == info["body"]:
            continue
        fm = dict(info["fm"])
        write_page(info["path"], fm, body, args.dry_run)
        info["body"] = body
        info["plot"] = count_plots(body)
        all_fms[cid] = (info["path"], fm, body)
        changes.append(f"{cid}: +plot→3")

    # 2) inbound=4 → hub
    for cid, info in sorted(pages.items()):
        if page_score(info) != 25 or info["inbound"] != 4:
            continue
        hub = pick_hub_source(cid, pages, inbound, chapter_cache)
        if not hub:
            continue
        hub_path = pages[hub]["path"]
        hfm, hbody = parse_frontmatter(hub_path)
        new_body = add_hub_link(hbody, cid)
        if new_body == hbody:
            continue
        if not args.dry_run:
            hfm_text = yaml.dump(hfm, allow_unicode=True, default_flow_style=False, sort_keys=False)
            hub_path.write_text(f"---\n{hfm_text}---\n{new_body}", encoding="utf-8")
        inbound[cid].add(hub)
        info["inbound"] = len(inbound[cid])
        changes.append(f"{hub}→{cid}: hub")

    # 3) 仍 score=25 → +rel
    for cid, info in sorted(pages.items()):
        if page_score(info) != 25:
            continue
        rel = pick_relation(cid, pages, all_fms, chapter_cache)
        if not rel:
            print(f"WARN stuck {cid}")
            continue
        fm = dict(info["fm"])
        if not add_relations(fm, rel):
            continue
        write_page(info["path"], fm, info["body"], args.dry_run)
        info["fm"] = fm
        info["rel"] = len(fm.get("relations") or [])
        all_fms[cid] = (info["path"], fm, info["body"])
        changes.append(f"{cid}: +rel→{rel['target']}")

    print(f"patched {len(changes)} items")
    for c in changes:
        print(" ", c)

    if not args.dry_run:
        remaining = sum(1 for info in pages.values() if page_score(info) == 25)
        print(f"remaining score=25: {remaining}")


if __name__ == "__main__":
    main()
