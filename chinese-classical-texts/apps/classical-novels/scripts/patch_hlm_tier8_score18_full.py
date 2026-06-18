#!/usr/bin/env python3
"""/dream 第八梯队 — score≤18 全量压至 ≥19。

用法: python scripts/patch_hlm_tier8_score18_full.py [--dry-run]
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

# 第三条情节（仅当 plot 条数 == 2 时追加）
PLOT_THIRD: dict[str, str] = {
    "傅秋芳": "第35回：傅试之妹才貌俱全，年二十有三尚未许人，宝玉闻而遐思遥爱。",
    "卜世仁": "第24回：贾芸赊冰片麝香，世仁推托并冷笑道再休提赊欠。",
    "卫若兰": "第14回：可卿路祭，与冯紫英、陈也俊同列诸王孙。",
    "善姐": "第68回：入园三日后凌虐尤二姐，反责其不知好歹、饭亦不肯端。",
    "乌进孝": "第53回：因大雪路难行，自言走了一个月零两日方到；交租折银二千五百两并土物。",
    "倪二": "第24回：闻贾芸向卜世仁诉苦，主动叫住，不取利、不写契，借银十五两三钱。",
    "吴良": "第86回：薛蝌呈子称须拉扯同喝酒的吴良作保、买嘱尸亲，方得撕掳。",
    "彩屏": "第115回：地藏庵姑子来，彩屏答惜春「饭都没吃，只是歪着」。",
    "彩明": "第14回：协理宁府首日，凤姐命其钉造簿册、念花名册点卯。",
    "彩鸾": "第62回：宝玉生日，与绣鸾等随王夫人房丫鬟至怡红院拜寿。",
    "戴权": "第13回：可卿首七，戴权趁便为贾蓉捐龙禁尉前程。",
    "李嬷嬷": "第19回：元春赐糖蒸酥酪，宝玉命留与袭人。",
    "林四娘": "第78回：宝玉作《姽婳词》吊林四娘（贾政先述恒王、诸姬殉国事）。",
    "王尔调": "第84回：外书房与詹光闲谈，称宝二爷学问大进。",
    "王成": "第6回：连宗王家后家业萧条，搬出城外，新近病故。",
    "甄应嘉": "第114回：蒙恩还职后至贾家寄灵处，与贾政悲喜交集。",
    "素云": "第119回：宝玉贾兰进场前夜，袭人带素云等收拾场具。",
    "钱槐": "第60回：赵姨娘内侄，因觊觎柳家五儿与环儿一党作歹。",
    "锦乡侯": "第13回：可卿丧仪，与川宁侯、寿山伯并迎入上房。",
    "霍启": "第1回：元宵看灯小解，英莲失踪，不敢回主逃往他乡。",
    "入画": "第7回：周瑞送宫花至惜春处，入画、智能同侍；惜春论出家。",
    "坠儿": "第52回：宋妈妈拿镯子，称小丫头子坠儿偷起来的。",
    "李贵": "第117回：门外拦阻送玉僧，李贵将和尚拦住，不放他进来。",
    "焦大": "第7回：因跟太爷出过兵、曾救主，有特殊恩赏；后醉骂被塞马粪。",
    "玉官": "第36回：梨香院女伶当差，与宝官等同列，戏班散前。",
    "马道婆": "第25回：与赵姨娘用纸人、青面鬼等魇镇凤姐、宝玉。",
    "傅试": "第94回：贾芹、女尼进宫案，傅试在场（后四十回）。",
    "娇杏": "第2回：封肃门前，雨村见娇杏那丫头买线，后索为二房、扶正。",
    "王太医": "第53回：晴雯雀裘病后，王太医复诊，减疏散药、添养血方。",
    "石呆子": "第107回：朝审复述倚势强索石呆子古扇，石呆子自尽。",
    "碧痕": "第24回：忽见碧痕来催小红洗脸。",
    "东平郡王": "第11回：贾敬寿辰，东平郡王等与诸客来贺宁府。",
    "云光": "第16回：凤姐已得云光回信，守备退聘（张金哥案）。",
    "周姨娘": "第25回：在王夫人房，与贾环抄《金刚咒》同场。",
    "封肃": "第2回：雨村密书托封肃，将娇杏送作二房。",
    "张华": "第64回：凤姐假意周全，令状告贾琏（退婚线起）。",
    "来升": "第14回：次日凤姐与来升媳妇分派花名册，定卯正点卯等规制。",
    "秦业": "第8回：秦钟入塾，秦业老迈，与贾代儒同管学事。",
    "艾官": "第60回：玫瑰露案前后，与诸伶同在园内。",
    "豆官": "第60回：玫瑰露案，与蕊官等同在园内。",
    "贾源": "第53回：宁府宗祠祭祀，源、演与代善等并列神主。",
    "贾演": "第53回：宁国公贾演与荣国公并祭。",
    "钱华": "第8回：宝玉往梨香院，账房七总管钱华多日未见，打千儿请安。",
    "多官": "第21回：都统制多总管之侄，外号多浑虫，在门首卖酒。",
}

REL_ADD: dict[str, list[dict]] = {
    "多官": [
        {"target": "王熙凤", "type": "同僚", "role": "琏偷情"},
    ],
    "菂官": [{"target": "蕊官", "type": "姐妹", "role": "补其小旦位"}],
    "赵亦华": [{"target": "张若锦", "type": "同僚", "role": "扈从出门"}],
    "喜儿": [{"target": "玉钏儿", "type": "同僚", "role": "端莲叶羹"}],
    "张三": [{"target": "薛蝌", "type": "同僚", "role": "呈子同案"}],
    "同喜": [{"target": "香菱", "type": "同僚", "role": "清虚观"}],
    "同贵": [{"target": "香菱", "type": "同僚", "role": "清虚观"}],
    "小蝉": [{"target": "司棋", "type": "主仆", "role": "传话要鸡蛋"}],
    "小鹊": [{"target": "贾政", "type": "主仆", "role": "第73回报"}],
    "彩鸾": [{"target": "金钏儿", "type": "同僚", "role": "王夫人房"}],
    "翠云": [{"target": "贾赦", "type": "主仆", "role": "妾室"}],
    "胡庸医": [{"target": "王夫人", "type": "主仆", "role": "误治逐出"}],
    "茄官": [{"target": "贾母", "type": "主仆", "role": "戏班散"}],
    "贾敷": [{"target": "贾敬", "type": "兄弟"}],
    "贾璜": [{"target": "尤氏", "type": "同僚", "role": "评理"}],
    "镇国公": [{"target": "理国公", "type": "同僚", "role": "四王八公"}],
    "净虚": [{"target": "守备", "type": "敌对", "role": "张金哥案"}],
    "守备": [{"target": "净虚", "type": "敌对", "role": "张金哥案"}],
    "宝官": [{"target": "薛宝钗", "type": "主仆", "role": "戏班散"}],
    "小吉祥儿": [{"target": "王夫人", "type": "主仆", "role": "借衣送殡"}],
    "忠顺亲王": [{"target": "北静王", "type": "同僚", "role": "王府对照"}],
    "玉爱": [{"target": "秦钟", "type": "朋友", "role": "闹学"}],
    "绣凤": [{"target": "彩鸾", "type": "姐妹", "role": "王夫人房"}],
    "绣鸾": [{"target": "金钏儿", "type": "同僚", "role": "王夫人房"}],
    "香怜": [{"target": "秦钟", "type": "朋友", "role": "闹学"}],
    "嫣红": [{"target": "翠云", "type": "姐妹", "role": "贾赦妾"}],
    "来升": [{"target": "赖大", "type": "同僚", "role": "宁荣总管"}],
    "潘又安": [{"target": "贾迎春", "type": "主仆", "role": "司棋房"}],
    "秦业": [{"target": "贾蓉", "type": "同僚", "role": "可卿养父"}],
    "佳蕙": [{"target": "袭人", "type": "主仆", "role": "怡红院"}],
    "傻大姐": [{"target": "邢夫人", "type": "主仆", "role": "呈绣春囊"}],
    "雪雁": [{"target": "王夫人", "type": "主仆", "role": "取人参"}],
    "贾芹": [{"target": "贾珍", "type": "同僚", "role": "管小和尚"}],
    "包勇": [{"target": "贾政", "type": "主仆", "role": "护园"}],
    "碧月": [{"target": "素云", "type": "姐妹", "role": "李纨房"}],
}

# hub 页 ## 相关 追加 [[target]]（为 score 仍 ≤18 且缺入链者 +1）
HUB_LINKS: dict[str, list[str]] = {
    "王熙凤": ["乌进孝", "彩明", "善姐", "来升", "张华"],
    "贾珍": ["戴权", "镇国公", "东平郡王", "乌进孝", "贾芹"],
    "贾宝玉": ["卫若兰", "钱华", "碧痕", "坠儿"],
    "赵姨娘": ["钱槐", "小蝉", "玉官", "马道婆", "小吉祥儿", "胡庸医"],
    "李纨": ["素云", "碧月", "同喜", "同贵"],
    "芳官": ["玉官", "茄官", "宝官", "菂官"],
    "金荣": ["贾璜", "香怜", "玉爱"],
    "薛蟠": ["张三", "吴良", "石呆子"],
    "门子": ["云光", "石呆子", "冯渊"],
    "尤二姐": ["善姐", "张华", "潘又安"],
    "贾政": ["林四娘", "王尔调", "甄应嘉", "小鹊", "包勇"],
    "刘姥姥": ["王成", "霍启"],
    "甄士隐": ["霍启", "封肃", "娇杏"],
    "贾雨村": ["娇杏", "封肃"],
    "蒋玉菡": ["忠顺亲王"],
    "北静王": ["东平郡王", "卫若兰", "镇国公", "锦乡侯"],
    "尤氏": ["茄官", "来升", "喜儿"],
    "王夫人": ["彩鸾", "绣凤", "绣鸾", "李嬷嬷", "王太医"],
    "秦可卿": ["戴权", "锦乡侯", "镇国公"],
    "智能": ["入画", "净虚"],
    "司棋": ["潘又安", "小蝉"],
    "贾赦": ["嫣红", "翠云", "周姨娘"],
    "冷子兴": ["贾源", "贾演", "贾敷"],
    "詹光": ["王尔调", "赵亦华", "钱华"],
    "倪二": ["卜世仁"],
    "傅试": ["傅秋芳"],
    "薛宝钗": ["喜儿", "宝官", "豆官", "艾官"],
    "贾惜春": ["彩屏", "入画", "包勇"],
    "贾母": ["锦乡侯", "茄官"],
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


def add_relations(fm: dict, extra: list[dict]) -> dict:
    rels = list(fm.get("relations") or [])
    existing = {r.get("target") for r in rels}
    for r in extra:
        if r["target"] not in existing:
            rels.append(r)
            existing.add(r["target"])
    fm["relations"] = rels
    return fm


def add_hub_link(body: str, target: str) -> str:
    if f"[[{target}]]" in body:
        return body
    rel_match = re.search(r"(## 相关\s*\n\n?)(.*?)(\n## |\Z)", body, re.S)
    if not rel_match:
        new_sec = f"\n## 相关\n\n- [[{target}]]\n"
        if "## 评析" in body:
            return body.replace("## 评析", new_sec + "## 评析", 1)
        return body.rstrip() + new_sec
    block = rel_match.group(2).rstrip()
    if block.startswith("- "):
        new_line = block + f" · [[{target}]]"
    else:
        new_line = f"- [[{target}]]"
    return (
        body[: rel_match.start(2)]
        + new_line
        + body[rel_match.end(2) :]
    )


def patch_character(path: Path, dry_run: bool) -> list[str]:
    changes: list[str] = []
    fm, body = parse_frontmatter(path)
    cid = str(fm.get("id") or path.stem)
    orig_body = body
    orig_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)

    if cid in REL_ADD:
        fm = add_relations(fm, REL_ADD[cid])
        if yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False) != orig_fm:
            changes.append(f"{cid}: +rel")

    plot_line = PLOT_THIRD.get(cid)
    if plot_line and count_plots(body) == 2:
        new_body = add_plot(body, plot_line)
        if new_body != body:
            body = new_body
            changes.append(f"{cid}: +plot")

    if body != orig_body or changes:
        fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        text = f"---\n{fm_text}---\n{body}"
        if not dry_run:
            path.write_text(text, encoding="utf-8")
    return changes


def patch_hubs(char_dir: Path, dry_run: bool) -> list[str]:
    changes: list[str] = []
    for hub, targets in HUB_LINKS.items():
        path = char_dir / f"{hub}.md"
        if not path.exists():
            continue
        fm, body = parse_frontmatter(path)
        orig = body
        for t in targets:
            body = add_hub_link(body, t)
        if body != orig:
            if not dry_run:
                fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
                path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")
            changes.append(f"{hub}: hub→{len(targets)}")
    return changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    char_dir = CHAR_DIR / BOOK
    targets = sorted(set(PLOT_THIRD) | set(REL_ADD))
    all_changes: list[str] = []

    for cid in targets:
        path = char_dir / f"{cid}.md"
        if not path.exists():
            print(f"WARN missing {path}")
            continue
        all_changes.extend(patch_character(path, args.dry_run))

    all_changes.extend(patch_hubs(char_dir, args.dry_run))

    print(f"patched {len(all_changes)} items")
    for c in all_changes:
        print(" ", c)


if __name__ == "__main__":
    main()
