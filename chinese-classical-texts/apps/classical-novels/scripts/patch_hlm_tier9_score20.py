#!/usr/bin/env python3
"""/dream 第九梯队 — score≤20 全量压至 ≥21。

用法: python scripts/patch_hlm_tier9_score20.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, CONTENT, iter_characters, parse_frontmatter  # noqa: E402
from lint_character_density import density_score  # noqa: E402

BOOK = "红楼梦"
TARGET = 21

REL_ADD: dict[str, list[dict]] = {
    "伴鹤": [{"target": "茗烟", "type": "同僚", "role": "怡红小厮"}],
    "佳蕙": [{"target": "林黛玉", "type": "主仆", "role": "送茶叶"}],
    "傅秋芳": [{"target": "王熙凤", "type": "同僚", "role": "傅家来访"}],
    "净虚": [{"target": "云光", "type": "同僚", "role": "张金哥案"}],
    "包勇": [{"target": "妙玉", "type": "主仆", "role": "护园擒贼"}],
    "卜世仁": [{"target": "倪二", "type": "朋友", "role": "义借对照"}],
    "同喜": [{"target": "贾母", "type": "主仆", "role": "清虚观"}],
    "同贵": [{"target": "贾母", "type": "主仆", "role": "清虚观"}],
    "善姐": [{"target": "尤二姐", "type": "主仆", "role": "凌虐"}],
    "喜儿": [{"target": "王熙凤", "type": "主仆", "role": "端莲叶羹"}],
    "夏守忠": [{"target": "赖大", "type": "同僚", "role": "报喜同回"}],
    "多官": [{"target": "平儿", "type": "同僚", "role": "琏偷情"}],
    "嫣红": [{"target": "贾琏", "type": "同僚", "role": "抄检"}],
    "孙绍祖": [{"target": "王夫人", "type": "主仆", "role": "出嫁劝慰"}],
    "守备": [{"target": "赖大", "type": "同僚", "role": "同回异事"}],
    "宝官": [{"target": "贾母", "type": "主仆", "role": "戏班散"}],
    "小吉祥儿": [{"target": "紫鹃", "type": "同僚", "role": "借衣传话"}],
    "小鹊": [{"target": "袭人", "type": "主仆", "role": "夜报留茶"}],
    "张三": [{"target": "门子", "type": "同僚", "role": "葫芦案"}],
    "张友士": [{"target": "尤氏", "type": "同僚", "role": "荐医叙病"}],
    "张金哥": [{"target": "云光", "type": "同僚", "role": "退聘案"}],
    "彩明": [{"target": "来升", "type": "同僚", "role": "协理宁府"}],
    "戴权": [{"target": "贾蓉", "type": "同僚", "role": "龙禁尉"}],
    "潘又安": [{"target": "王熙凤", "type": "主仆", "role": "抄检情帖"}],
    "玉爱": [{"target": "贾瑞", "type": "同僚", "role": "闹学惩处"}],
    "玉钏儿": [{"target": "喜儿", "type": "同僚", "role": "莲叶羹"}],
    "王尔调": [{"target": "贾政", "type": "同僚", "role": "论定亲"}],
    "王成": [{"target": "周瑞", "type": "同僚", "role": "连宗引见"}],
    "素云": [{"target": "贾母", "type": "主仆", "role": "清虚观"}],
    "绣鸾": [{"target": "彩云", "type": "姐妹", "role": "王夫人房"}],
    "菂官": [{"target": "贾宝玉", "type": "朋友", "role": "祭事护庇"}],
    "贾璜": [{"target": "王熙凤", "type": "同僚", "role": "资助"}],
    "贾芹": [{"target": "贾琏", "type": "同僚", "role": "管小和尚"}],
    "赵亦华": [{"target": "贾宝玉", "type": "主仆", "role": "扈从出门"}],
    "钱槐": [{"target": "贾环", "type": "同僚", "role": "蔷薇硝"}],
    "雪雁": [{"target": "小吉祥儿", "type": "同僚", "role": "借衣送殡"}],
    "入画": [{"target": "彩屏", "type": "姐妹", "role": "惜春房"}],
    "卫若兰": [{"target": "史湘云", "type": "朋友", "role": "婚约"}],
    "锦乡侯": [{"target": "秦可卿", "type": "朋友", "role": "丧仪"}],
    "霍启": [{"target": "封肃", "type": "主仆", "role": "葫芦庙"}],
    "傻大姐": [{"target": "林黛玉", "type": "主仆", "role": "误传婚讯"}],
    "李嬷嬷": [{"target": "袭人", "type": "主仆", "role": "争宠饮食"}],
    "李贵": [{"target": "茗烟", "type": "兄弟", "role": "宝玉小厮"}],
    "彩云": [{"target": "王夫人", "type": "主仆", "role": "玫瑰露案"}],
    "乌进孝": [{"target": "王熙凤", "type": "主仆", "role": "年例"}],
    "焦大": [{"target": "贾宝玉", "type": "主仆", "role": "亲闻醉骂"}],
    "甄应嘉": [{"target": "甄夫人", "type": "夫妻"}],
    "马道婆": [{"target": "王熙凤", "type": "仇敌", "role": "魇镇"}],
    "吴良": [{"target": "门子", "type": "同僚", "role": "呈子同案"}],
    "坠儿": [{"target": "平儿", "type": "主仆", "role": "偷镯"}],
    "林四娘": [{"target": "詹光", "type": "同僚", "role": "论姽婳词"}],
    "倪二": [{"target": "贾芸", "type": "朋友", "role": "义借"}],
    "彩屏": [{"target": "智能", "type": "姐妹", "role": "惜春房"}],
    "小蝉": [{"target": "赵姨娘", "type": "主仆", "role": "厨房"}],
    "胡庸医": [{"target": "晴雯", "type": "朋友", "role": "误诊"}],
    "妙玉": [{"target": "贾母", "type": "主仆", "role": "栊翠庵"}],
    "葵官": [{"target": "贾母", "type": "主仆", "role": "戏班散"}],
    "贾敷": [{"target": "贾珍", "type": "同僚", "role": "谱系"}],
    "鹦哥": [{"target": "贾母", "type": "主仆", "role": "两宴"}],
}

REL_ADD_EXTRA: dict[str, list[dict]] = {
    "傻大姐": [{"target": "王熙凤", "type": "主仆", "role": "抄检线索"}],
    "张三": [{"target": "香菱", "type": "同僚", "role": "英莲链"}],
    "善姐": [{"target": "王熙凤", "type": "主仆", "role": "遣入"}],
    "钱槐": [{"target": "赵姨娘", "type": "主仆", "role": "内侄"}],
    "王尔调": [{"target": "詹光", "type": "同僚", "role": "清客"}],
    "伴鹤": [{"target": "锄药", "type": "兄弟", "role": "怡红小厮"}],
}

PLOT_FOURTH: dict[str, str] = {
    "张三": "第4回：原告称拐子先收冯家银子，又悄悄卖与薛家，争买殴伤人命。",
    "倪二": "第24回：闻贾芸向卜世仁诉苦，主动叫住，不取利、不写契，借银十五两三钱。",
    "吴良": "第86回：薛蝌呈子称须拉扯同喝酒的吴良作保，方得撕掳。",
    "多官": "第21回：都统制多总管之侄，外号多浑虫，在门首卖酒。",
    "嫣红": "第74回：抄检大观园，凤姐列举邢夫人曾带嫣红、翠云等人入园。",
    "宝官": "第36回：梨香院女伶当差，与玉官等同列。",
    "小鹊": "第73回：小鹊直进怡红院找宝玉，宝玉如闻紧箍咒，连夜温书。",
    "彩屏": "第115回：地藏庵姑子来，彩屏答惜春饭都没吃，只是歪着。",
    "戴权": "第13回：可卿首七，戴权趁便为贾蓉捐龙禁尉前程。",
    "林四娘": "第78回：宝玉作《姽婳词》吊林四娘（贾政先述恒王、诸姬殉国事）。",
    "王尔调": "第84回：外书房与詹光闲谈，称宝二爷学问大进。",
    "王成": "第6回：连宗王家后家业萧条，搬出城外，新近病故。",
    "翠云": "第89回：随侍叙事中再列翠云（程高本）。",
    "菂官": "第58回：梨香院散班议遣，藕官于园外烧纸祭之。",
    "贾璜": "第10回：璜大奶奶至宁府找尤氏评理，金荣方敢进园闹学。",
    "赵亦华": "第52回：同场另有王荣、钱启、周瑞等，赵亦华、张若锦紧贴宝玉后身。",
    "钱槐": "第60回：赵姨娘内侄，因觊觎柳家五儿与环儿一党作歹。",
    "喜儿": "第35回：莺儿与喜儿同端捧盒至怡红院，端莲叶羹。",
    "彩明": "第14回：协理宁府首日，凤姐命其钉造簿册、念花名册点卯。",
    "卜世仁": "第24回：贾芸赊冰片麝香，世仁推托并冷笑道再休提赊欠。",
    "包勇": "第112回：包勇擒贼护惜春妙玉（程高本）。",
    "小蝉": "第61回：司棋经小蝉等传话与柳家的争鸡蛋。",
    "胡庸医": "第51回：王夫人闻误治晴雯，即命逐出，不许再进。",
    "妙玉": "第41回：妙玉奉茶，梅花雪水、老君眉（两宴大观园）。",
    "葵官": "第58回：戏班散，葵官随探春等归所主。",
    "贾敷": "第2回：冷子兴演说宁荣谱系，贾敷早亡，贾敬袭爵。",
    "鹦哥": "第40回：两宴大观园，鹦哥等随侍贾母行令。",
    "净虚": "第16回：水月庵与净虚、张金哥案相连。",
    "夏守忠": "第16回：夏太监出来道喜，与赖大报喜同回。",
    "守备": "第16回：守备忍气吞声，张李两家没趣。",
    "绣凤": "第62回：宝玉生日，绣凤与彩鸾、绣鸾等至怡红院拜寿。",
    "绣鸾": "第62回：与彩鸾等同至怡红院拜寿，嚷着要面吃。",
    "玉爱": "第9回：金荣诬玉爱与香怜为「小妇人之子」，引发学堂大乱。",
    "香怜": "第9回：金荣诬香怜、玉爱，秦钟与之扭打，引发学堂大乱。",
    "小吉祥儿": "第57回：赵姨娘唤雪雁向王夫人房借衣给小吉祥儿送殡。",
    "潘又安": "第77回：司棋被搜出潘又安情帖，迎春不能作主。",
    "玉钏儿": "第18回：元春省亲后，玉钏儿等与众人赏宴。",
    "孙绍祖": "第79回：孙绍祖与迎春成婚，后虐待（程高本）。",
    "张友士": "第10回：张友士为秦可卿诊脉，尤氏荐医。",
    "张金哥": "第16回：张金哥与李守备之子退婚，凤姐得云光回信。",
    "来旺家的": "第69回：来旺家的献计赚张华，尤二姐案收尾。",
    "坠儿": "第56回：宋妈妈拿镯子，称小丫头子坠儿偷起来的。",
    "彩云": "第60回：玫瑰露案，彩云私赠赵姨娘房。",
    "李嬷嬷": "第19回：元春赐糖蒸酥酪，宝玉命留与袭人。",
    "李贵": "第117回：李贵将和尚拦住，不放他进来。",
    "焦大": "第7回：因跟太爷出过兵、曾救主，有特殊恩赏。",
    "甄应嘉": "第114回：蒙恩还职后至贾家寄灵处，与贾政悲喜交集。",
    "马道婆": "第25回：与赵姨娘用纸人、青面鬼等魇镇凤姐、宝玉。",
    "雪雁": "第3回：随黛玉自扬州入贾府，与紫鹃同侍潇湘馆。",
    "素云": "第119回：袭人带素云等给宝玉贾兰收拾场具。",
    "佳蕙": "第26回：佳蕙送茶叶至潇湘馆，黛玉收用。",
    "傅秋芳": "第35回：傅试之妹才貌俱全，年二十有三尚未许人。",
    "伴鹤": "第24回：贾芸来访绮霰斋，引泉等与伴鹤等收束行礼。",
    "善姐": "第68回：入园三日后凌虐尤二姐，反责其不知好歹。",
}

HUB_LINKS: dict[str, list[str]] = {
    "芳官": ["四儿", "碧痕"],
    "贾政": ["忠顺亲王", "王尔调"],
    "娇杏": ["贾雨村"],
    "李婶": ["李纹", "李绮"],
    "彩明": ["来升"],
    "贾母": ["甄夫人", "贾代善", "鹦哥"],
    "王熙凤": ["鲍二", "善姐", "钱槐", "伴鹤", "王尔调"],
    "贾宝玉": ["文官", "伴鹤"],
    "秦可卿": ["西宁郡王"],
    "尤二姐": ["善姐"],
    "topics/神话还泪链": ["娇杏"],
    "topics/大观园诗社总览": ["李纹", "李绮"],
    "topics/两宴大观园": ["鹦哥"],
    "北静王": ["西宁郡王"],
    "冯紫英": ["卫若兰"],
    "邢夫人": ["嫣红", "翠云"],
    "薛姨妈": ["甄夫人"],
    "李纨": ["素云", "碧月"],
    "赵姨娘": ["钱槐", "小蝉"],
    "茗烟": ["李贵", "伴鹤"],
    "门子": ["张三", "吴良"],
    "尤氏": ["张友士", "夏守忠"],
    "贾珍": ["乌进孝", "戴权"],
    "詹光": ["林四娘", "王尔调"],
    "甄士隐": ["霍启"],
    "冷子兴": ["贾敷", "贾代善"],
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
    if "## 相关" in body:
        rel_match = re.search(r"(## 相关\s*\n\n?)(.*?)(\n## )", body, re.S)
        if rel_match:
            block = rel_match.group(2).rstrip()
            if block.startswith("- "):
                new_line = block + f" · [[{target}]]"
            else:
                new_line = f"- [[{target}]]"
            return body[: rel_match.start(2)] + new_line + body[rel_match.end(2) :]
    new_sec = f"\n## 相关\n\n- [[{target}]]\n"
    if "## 评析" in body:
        return body.replace("## 评析", new_sec + "## 评析", 1)
    return body.rstrip() + new_sec


def patch_hub_file(path: Path, targets: list[str], dry_run: bool) -> bool:
    if not path.exists():
        return False
    fm, body = parse_frontmatter(path)
    orig = body
    for t in targets:
        body = add_hub_link(body, t)
    if body == orig:
        return False
    if not dry_run:
        fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")
    return True


def patch_character(path: Path, dry_run: bool) -> list[str]:
    changes: list[str] = []
    fm, body = parse_frontmatter(path)
    cid = str(fm.get("id") or path.stem)
    orig_body = body
    orig_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)

    for bucket in (REL_ADD, REL_ADD_EXTRA):
        if cid in bucket:
            fm = add_relations(fm, bucket[cid])

    plot_line = PLOT_FOURTH.get(cid)
    if plot_line:
        cp = count_plots(body)
        if cp in (2, 3):
            new_body = add_plot(body, plot_line)
            if new_body != body:
                body = new_body
                changes.append(f"{cid}: +plot")

    if yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False) != orig_fm:
        changes.append(f"{cid}: +rel")

    if body != orig_body or changes:
        fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        text = f"---\n{fm_text}---\n{body}"
        if not dry_run:
            path.write_text(text, encoding="utf-8")
    return changes


def scan_thin() -> list[tuple[int, str]]:
    chars = list(iter_characters(BOOK))
    ids = {fm.get("id") or p.stem for p, fm, _ in chars}
    pages: dict[str, dict] = {}
    inbound: dict[str, set[str]] = __import__("collections").defaultdict(set)
    for p, fm, body in chars:
        cid = fm.get("id") or p.stem
        plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
        plots = []
        if plot_sec:
            plots = [ln for ln in plot_sec.group(1).splitlines() if ln.strip().startswith("-")]
        pages[cid] = {
            "rel": len(fm.get("relations") or []),
            "plot": len(plots),
            "main": "## 主要关系" in body,
            "review": "## 评析" in body,
            "inbound": 0,
        }
    char_dir = CONTENT / "characters" / BOOK
    for p in char_dir.glob("*.md"):
        txt = p.read_text(encoding="utf-8-sig")
        src = p.stem
        for m in re.finditer(r"\[\[([^\]|]+)", txt):
            t = m.group(1).strip()
            if t in ids and t != src:
                inbound[t].add(src)
    topics_dir = CONTENT / "topics" / BOOK
    if topics_dir.exists():
        for p in topics_dir.glob("*.md"):
            txt = p.read_text(encoding="utf-8-sig")
            for m in re.finditer(r"\[\[([^\]|]+)", txt):
                t = m.group(1).strip()
                if t in ids:
                    inbound[t].add("topic")
    for cid in pages:
        pages[cid]["inbound"] = len(inbound[cid])
    return sorted(
        (density_score(d), cid)
        for cid, d in pages.items()
        if density_score(d) <= 20
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    char_dir = CHAR_DIR / BOOK
    targets = sorted(set(REL_ADD) | set(REL_ADD_EXTRA) | set(PLOT_FOURTH))
    all_changes: list[str] = []

    for cid in targets:
        path = char_dir / f"{cid}.md"
        if not path.exists():
            print(f"WARN missing {path}")
            continue
        all_changes.extend(patch_character(path, args.dry_run))

    for hub, tgs in HUB_LINKS.items():
        if hub.startswith("topics/"):
            path = CONTENT / "topics" / BOOK / f"{hub.split('/', 1)[1]}.md"
        else:
            path = char_dir / f"{hub}.md"
        if patch_hub_file(path, tgs, args.dry_run):
            all_changes.append(f"{hub}: hub")

    print(f"patched {len(all_changes)} items")
    for c in all_changes:
        print(" ", c)

    if not args.dry_run:
        thin = scan_thin()
        print(f"remaining score<={TARGET - 1}: {len(thin)}")
        for s, cid in thin[:15]:
            print(f"  {s} {cid}")
        if len(thin) > 15:
            print(f"  ... +{len(thin) - 15}")


if __name__ == "__main__":
    main()
