#!/usr/bin/env python3
"""/dream 第六梯队 — score≤14 中薄页加固。

用法: python scripts/patch_hlm_tier6_medium_thin.py [--dry-run]
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

# 在「## 关键情节」末追加第二条（仅当现有 plot 条数为 1 时）
PLOT_ADD: dict[str, str] = {
    "林四娘": "第78回：贾政与詹光等清客论恒王、林四娘统辖诸姬及殉国事，考较宝玉才思作《姽婳词》。",
    "赵亦华": "第52回：同场另有王荣、钱启、周瑞等清客扈从，赵亦华、张若锦「两边紧贴宝玉后身」。",
    "戴权": "第13回：贾珍因可卿不得建上，戴权传旨，内侍昭儿往锦乡侯等府送领凭牌、代求天恩义冢。",
    "小吉祥儿": "第57回：赵姨娘唤雪雁，雪雁向王夫人房玉钏儿借月白缎子袄儿与青缎子背心，给小吉祥儿送殡。",
    "菂官": "第58回：梨香院散班议遣，藕官于园外烧纸祭之；芳官道破「假凤泣虚凰」，宝玉悟诚心之祭。",
    "钱槐": "第60回：钱槐为赵姨娘内侄，觊觎柳家五儿不成，与赵姨娘、贾环一党，后文争蔷薇硝作歹。",
    "锦乡侯": "第13回：可卿丧仪，内侍昭儿往锦乡侯府等处送领凭牌（与第71回寿宴诰命并见）。",
    "乌进孝": "第53回：贾珍叹「你比不得你爹，你怎的没有本事？堆山积海的，太不容易了」，乌进孝战兢兢连声答应。",
    "卜世仁": "第24回：世仁推托赊账，贾芸转求街坊倪二，得银十五两三钱，后谋凤姐差事。",
    "吴良": "第86回：薛蟠误伤张三案，薛蝌呈子称须拉扯同喝酒的吴良作保人、买嘱尸亲，方得撕掳。",
    "彩鸾": "第23回：贾政在王夫人房中议事，彩鸾与绣鸾、绣凤、金钏儿等在廊檐下随侍。",
    "王尔调": "第84回：贾母与贾政议为宝玉定亲；王尔调于外书房与詹光闲谈，提南韶道张小姐说亲。",
    "王成": "第6回：刘姥姥一进荣国府，王狗儿之岳丈王成，昔年曾作小京官，与金陵王家连宗。",
    "甄应嘉": "第99回：甄应嘉遣家仆送书，报甄家被抄、甄宝玉随母进京；贾政读罢，与贾母等商议。",
    "霍启": "第2回：封肃回禀，霍启元宵失英莲后不敢回主，逃往他乡（与第1回看灯失女连缀）。",
    "张三": "第86回：薛蟠酒碗误碰张三卤门致死；薛蝌代兄呈子，称与张姓素不相认、并无仇隙。",
    "玉爱": "第9回：金荣等闹学，玉爱与香怜等同在塾中，被金荣诬为「小妇人之子」。",
    "胡庸医": "第51回：胡庸医诊晴雯，误用虎狼药；王夫人闻知，即命逐出，不许再进。",
    "贾敷": "第2回：冷子兴演说宁荣谱系，贾代善长子贾敷早亡，贾敬袭爵。",
    "贾璜": "第9回：金荣母告贾璜，璜说情于贾珍，金荣方敢进园闹学。",
    "镇国公": "第14回：秦可卿出殡，镇国公等世交诸王、公侯祭棚接祭于城门前。",
    "香怜": "第9回：金荣诬香怜、玉爱为「小妇人之子」，秦钟与之扭打，引发学堂大乱。",
    "净虚": "第16回：智能私逃进城看秦钟，秦业知觉逐之；水月庵与净虚、张金哥案相连。",
    "娇杏": "第1回：甄士隐养病，窗外闻女子对镜悲叹，即娇杏；后第2回封肃将其送作雨村二房。",
    "守备": "第16回：守备之子闻张金哥自缢，亦投河而死，不负妻义；张李两家人财两空。",
    "绣凤": "第62回：宝玉生日，绣凤与彩鸾、绣鸾等至怡红院拜寿，嚷着要面吃。",
}

# 已有两条情节仍偏薄时追加
PLOT_ADD_EXTRA: dict[str, str] = {
    "雪雁": "第3回：随黛玉自扬州入贾府，与紫鹃同侍潇湘馆。",
}

# frontmatter relations 追加（去重 target）
REL_ADD: dict[str, list[dict]] = {
    "多官": [{"target": "贾琏", "type": "朋友", "role": "多姑娘之夫"}],
    "傅秋芳": [{"target": "贾宝玉", "type": "恋慕", "role": "兄欲说亲"}],
    "傻大姐": [{"target": "林黛玉", "type": "主仆", "role": "误传婚讯"}],
    "素云": [{"target": "碧月", "type": "姐妹", "role": "李纨房"}],
    "倪二": [{"target": "卜世仁", "type": "朋友", "role": "义借对照"}],
    "小蝉": [{"target": "柳家的", "type": "同僚", "role": "厨房口角"}],
    "玉官": [{"target": "宝官", "type": "姐妹", "role": "同班"}],
    "马道婆": [{"target": "王熙凤", "type": "仇敌", "role": "魇镇"}],
}

# 整页替换（纠错）
BODY_REPLACE: dict[str, str] = {
    "多官": """---
id: 多官
type: character
name: 多官
aliases:
- 多浑虫
gender: 男
book: 红楼梦
faction: 村野
first_appear: 第21回
status: 配角
tags:
- 酒肆
relations:
- target: 贾琏
  type: 朋友
  role: 多姑娘之夫
summary: 皇庄多总管之侄，外号多浑虫；第21回懦弱卖酒，妻貌美，贾琏与之私通。
weight: 28
性格: 卖酒、懦弱
喜好:
- 酒
关键物品:
- 荣国府
结局: 多浑虫醉卧，贾琏与多姑娘私会；凤姐后审平儿得知。（第21回）
---
## 身份

都统制多总管之侄，外号「多浑虫」，在门首卖酒；妻貌美而性轻浮，人称「多姑娘」。

## 主要关系

- [[贾琏]]：多浑虫醉卧，琏与多姑娘私会（第21回）。
- [[王熙凤]]：平儿撞破，凤姐审问（第21回）。

## 关键情节

- 第21回：人称「多浑虫」，懦弱卖酒；妻貌美而性轻浮，「最喜拈花惹草，多浑虫又不理论」。
- 第21回：贾琏挪在外书房，多姑娘有意；多浑虫醉昏在炕，琏溜来相会，为凤姐「软语救贾琏」伏线。

## 评析

程高本第21回写 **琏偷情** 而非薛蟠人命；「多浑虫」名与懦弱对照，连缀凤姐、平儿线。

## 相关

- [[贾琏]] · [[王熙凤]] · 第21回
""",
}


def write_page(path: Path, text: str, dry_run: bool) -> bool:
    if dry_run:
        print(f"[dry-run] would write {path.name}")
        return True
    path.write_text(text, encoding="utf-8")
    return True


def count_plots(body: str) -> int:
    plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    if not plot_sec:
        return 0
    return sum(1 for ln in plot_sec.group(1).splitlines() if ln.strip().startswith("-"))


def add_plot(body: str, line: str) -> str:
    marker = "## 评析"
    plot_match = re.search(r"(## 关键情节\s*\n.*?)(\n## )", body, re.S)
    if not plot_match:
        return body
    block = plot_match.group(1)
    if line.strip() in block:
        return body
    new_block = block.rstrip() + f"\n- {line}\n"
    return body[: plot_match.start(1)] + new_block + body[plot_match.end(1) :]


def add_relations(fm: dict, extra: list[dict]) -> dict:
    rels = list(fm.get("relations") or [])
    existing = {r.get("target") for r in rels}
    for r in extra:
        if r["target"] not in existing:
            rels.append(r)
            existing.add(r["target"])
    fm["relations"] = rels
    return fm


def patch_file(path: Path, dry_run: bool) -> list[str]:
    changes: list[str] = []
    cid = path.stem

    if cid in BODY_REPLACE:
        write_page(path, BODY_REPLACE[cid], dry_run)
        return [f"{cid}: full replace (多官程高本纠错)"]

    fm, body = parse_frontmatter(path)
    orig = body
    rel_extra = REL_ADD.get(cid, [])

    if rel_extra:
        fm = add_relations(fm, rel_extra)
        changes.append(f"{cid}: +{len(rel_extra)} rel")

    plot_line = PLOT_ADD.get(cid)
    if plot_line and count_plots(body) == 1:
        body = add_plot(body, plot_line)
        if body != orig:
            changes.append(f"{cid}: +1 plot")

    extra_plot = PLOT_ADD_EXTRA.get(cid)
    if extra_plot and count_plots(body) == 2:
        body2 = add_plot(body, extra_plot)
        if body2 != body:
            body = body2
            changes.append(f"{cid}: +1 plot (extra)")

    if body != orig or rel_extra:
        fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        text = f"---\n{fm_text}---\n{body}"
        write_page(path, text, dry_run)

    return changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    char_dir = CHAR_DIR / BOOK
    targets = set(PLOT_ADD) | set(PLOT_ADD_EXTRA) | set(REL_ADD) | set(BODY_REPLACE)
    all_changes: list[str] = []

    for cid in sorted(targets):
        path = char_dir / f"{cid}.md"
        if not path.exists():
            print(f"WARN missing {path}")
            continue
        all_changes.extend(patch_file(path, args.dry_run))

    print(f"patched {len(all_changes)} items")
    for c in all_changes:
        print(" ", c)


if __name__ == "__main__":
    main()
