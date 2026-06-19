#!/usr/bin/env python3
"""为红楼梦人物 frontmatter 注入 arc（一生轨迹节点）。

用法: python scripts/seed_hlm_character_arcs.py
"""
from __future__ import annotations

import yaml

from _common import CHAR_DIR, parse_frontmatter

BOOK = "红楼梦"

# 批次 A：十二钗余员 + 批次 B：家族轴
ARCS: dict[str, list[dict]] = {
    "贾元春": [
        {"chapter": 18, "stage": "出场", "title": "省亲赐名", "note": "回府省亲，大观园题匾赐名，家族盛极一时。", "fortune": 90, "event": "hlm-e-002"},
        {"chapter": 28, "stage": "转", "title": "端午赐礼", "note": "节礼宝玉与宝钗同份，引发「金玉」之疑，省亲恩宠渐成远忧。", "fortune": 40},
        {"chapter": 83, "stage": "低谷", "title": "宫闱染恙", "note": "元妃病重，亲丁入省，家族命运系于深宫。", "fortune": -30},
        {"chapter": 95, "stage": "结局", "title": "薨逝深宫", "note": "元妃薨逝（程高本），「虎兕相逢大梦归」，贾府失去最大靠山。", "fortune": -90},
    ],
    "贾探春": [
        {"chapter": 37, "stage": "起", "title": "海棠诗社", "note": "号「蕉下客」，与姊妹结社赋诗，才志初显。", "fortune": 45},
        {"chapter": 55, "stage": "高光", "title": "理家兴利", "note": "凤姐病，探春主理，削学里公费、定月例旧规。", "fortune": 75, "event": "hlm-e-012"},
        {"chapter": 74, "stage": "转", "title": "抄检心冷", "note": "大观园抄检，亲妹入画被逐，探春痛斥「自杀自灭」。", "fortune": 15, "event": "hlm-e-005"},
        {"chapter": 100, "stage": "结局", "title": "远嫁海疆", "note": "后四十回远嫁海疆（程高本），「清明涕送江边望」。", "fortune": -40},
    ],
    "贾迎春": [
        {"chapter": 23, "stage": "出场", "title": "入大观园", "note": "居紫菱洲，性格懦弱，「二木头」之称。", "fortune": 25},
        {"chapter": 73, "stage": "转", "title": "抄检受牵连", "note": "司棋事发，累丝金凤等风波，迎春无力自保。", "fortune": -10, "event": "hlm-e-005"},
        {"chapter": 80, "stage": "低谷", "title": "出嫁哭诉", "note": "许嫁孙绍祖，向王夫人哭诉夫家之恶，仍无力抗拒。", "fortune": -45},
        {"chapter": 109, "stage": "结局", "title": "被虐致死", "note": "婚后受孙绍祖虐待致死（程高本），「子系中山狼」。", "fortune": -100},
    ],
    "贾惜春": [
        {"chapter": 37, "stage": "出场", "title": "海棠社作画", "note": "号「藕榭」，与姊妹结社，性孤介清冷。", "fortune": 30},
        {"chapter": 74, "stage": "转", "title": "斥逐入画", "note": "抄检后坚拒「带累」，求逐入画，勘破亲缘。", "fortune": 10, "event": "hlm-e-005"},
        {"chapter": 115, "stage": "结局", "title": "剪发出家", "note": "大观园散后出家为尼（程高本），「独卧青灯古佛前」。", "fortune": 55},
    ],
    "史湘云": [
        {"chapter": 20, "stage": "出场", "title": "来府小住", "note": "贾母侄孙女，襟怀洒落，初显豪爽。", "fortune": 35},
        {"chapter": 38, "stage": "高光", "title": "螃蟹宴联诗", "note": "与宝钗助凤姐张罗，诗社联句夺魁。", "fortune": 70},
        {"chapter": 76, "stage": "高光", "title": "中秋联句", "note": "凹晶馆与黛玉联诗，「寒塘渡鹤影」。", "fortune": 55},
        {"chapter": 106, "stage": "结局", "title": "早寡飘零", "note": "后四十回夫婿病故，湘云早寡（程高本），「云散高唐」。", "fortune": -50},
    ],
    "李纨": [
        {"chapter": 3, "stage": "出场", "title": "寡居稻香村", "note": "贾珠遗孀，抚育贾兰，「如槁木死灰」守节。", "fortune": 20},
        {"chapter": 37, "stage": "起", "title": "诗社监察", "note": "海棠诗社任监察，号「稻香老农」。", "fortune": 45},
        {"chapter": 55, "stage": "高光", "title": "协理家务", "note": "与探春、宝钗共理，定月例赏银。", "fortune": 55, "event": "hlm-e-012"},
        {"chapter": 119, "stage": "结局", "title": "兰桂齐芳", "note": "后四十回贾兰科举显达，李纨得诰（程高本）。", "fortune": 70},
    ],
    "秦可卿": [
        {"chapter": 5, "stage": "出场", "title": "兼美幻境", "note": "宝玉游太虚幻境，见其卧室陈设，兼美两可。", "fortune": 40},
        {"chapter": 10, "stage": "转", "title": "病笃诊脉", "note": "张友士诊脉，病势沉重，家族隐忧渐显。", "fortune": -20},
        {"chapter": 13, "stage": "结局", "title": "薨逝极盛丧", "note": "早亡，凤姐协理极盛之丧，贾府权势巅峰亦衰败伏笔。", "fortune": -100, "event": "hlm-e-009"},
    ],
    "巧姐": [
        {"chapter": 42, "stage": "出场", "title": "刘姥姥起名", "note": "凤姐之女，刘姥姥取名「巧哥儿」，结下善缘。", "fortune": 40, "event": "hlm-e-011"},
        {"chapter": 84, "stage": "转", "title": "家势渐危", "note": "贾府败象已露，巧姐命运系于族中亲疏。", "fortune": -15},
        {"chapter": 118, "stage": "低谷", "title": "狠舅奸兄", "note": "王仁、贾环等欲卖与外藩，巧姐几陷险境。", "fortune": -80},
        {"chapter": 119, "stage": "结局", "title": "刘姥姥相救", "note": "刘姥姥、平儿救出送往乡村（程高本），「偶因济刘氏」。", "fortune": 50},
    ],
    "妙玉": [
        {"chapter": 41, "stage": "出场", "title": "栊翠庵品茶", "note": "以梅花雪水、成窑杯待客，才调高而性怪僻。", "fortune": 50},
        {"chapter": 76, "stage": "高光", "title": "中秋联诗", "note": "凹晶馆外续句收束，与钗黛同列诗坛。", "fortune": 45},
        {"chapter": 112, "stage": "结局", "title": "遭劫失踪", "note": "贾府被劫，妙玉被强盗掳走不知所终（程高本），「终陷淖泥中」。", "fortune": -90},
    ],
    "香菱": [
        {"chapter": 1, "stage": "出场", "title": "元宵被拐", "note": "甄士隐之女英莲，幼时被拐，命运从此改写。", "fortune": -60},
        {"chapter": 48, "stage": "高光", "title": "拜黛玉学诗", "note": "痴于诗词，苦学不辍，「根并荷花一茎香」。", "fortune": 55},
        {"chapter": 80, "stage": "低谷", "title": "受金桂凌虐", "note": "夏金桂悍妒，香菱备受折磨。", "fortune": -40},
        {"chapter": 120, "stage": "结局", "title": "魂归故乡", "note": "后四十回难产而亡、魂归（程高本），与甄士隐相认。", "fortune": -100},
    ],
    "贾母": [
        {"chapter": 3, "stage": "出场", "title": "荣府家长", "note": "史太君居尊，溺爱宝玉，主持家族日常。", "fortune": 50},
        {"chapter": 18, "stage": "高光", "title": "元妃省亲", "note": "省亲大典，贾府恩宠达于极盛。", "fortune": 85, "event": "hlm-e-002"},
        {"chapter": 71, "stage": "高光", "title": "八旬荣寿", "note": "嘉荫堂接驾，寿宴极盛，「享福到尽头」。", "fortune": 70},
        {"chapter": 105, "stage": "结局", "title": "寿终归西", "note": "后四十回贾母寿终，家族失去最高庇护（程高本）。", "fortune": -30},
    ],
    "贾政": [
        {"chapter": 3, "stage": "出场", "title": "严父当家", "note": "荣府二老爷，礼教端方，望子成龙。", "fortune": 30},
        {"chapter": 33, "stage": "低谷", "title": "笞打宝玉", "note": "因金钏、琪官等事重责宝玉，父子冲突达于顶点。", "fortune": -25, "event": "hlm-e-010"},
        {"chapter": 107, "stage": "转", "title": "蒙恩宽宥", "note": "抄家后蒙圣恩宽宥，贾政赴任。", "fortune": 40, "event": "hlm-e-007"},
        {"chapter": 120, "stage": "结局", "title": "送子出家", "note": "见宝玉悬崖撒手，贾政痛哭而返（程高本）。", "fortune": 15, "event": "hlm-e-008"},
    ],
    "贾珍": [
        {"chapter": 2, "stage": "出场", "title": "宁府族长", "note": "世袭威烈将军，族长身份，宁府实际掌权者。", "fortune": 40},
        {"chapter": 13, "stage": "高光", "title": "可卿极盛丧", "note": "秦可卿丧仪极盛，显宁府权势。", "fortune": 60, "event": "hlm-e-009"},
        {"chapter": 63, "stage": "低谷", "title": "服丹纵欲", "note": "贾敬服丹而亡，贾珍居丧仍宴饮，败象已露。", "fortune": -50},
        {"chapter": 107, "stage": "结局", "title": "革职发配", "note": "「爬灰」败露，被革职发往原籍（程高本）。", "fortune": -90, "event": "hlm-e-007"},
    ],
    "贾琏": [
        {"chapter": 3, "stage": "出场", "title": "琏二爷管家", "note": "捐同知，娶凤姐掌家，协理荣宁外事。", "fortune": 35},
        {"chapter": 64, "stage": "转", "title": "偷娶尤二姐", "note": "小花枝巷偷娶二房，埋下凤姐报复之线。", "fortune": 25},
        {"chapter": 69, "stage": "低谷", "title": "二姐之死", "note": "尤二姐被凤姐逼死，贾琏无力相护。", "fortune": -35},
        {"chapter": 96, "stage": "结局", "title": "偷梁换柱", "note": "后四十回操办「偷梁换柱」成婚，参与调包计。", "fortune": -45, "event": "hlm-e-006"},
    ],
    "晴雯": [
        {"chapter": 8, "stage": "出场", "title": "怡红院当差", "note": "贾母所赐大丫鬟，性情刚烈，心比天高。", "fortune": 35},
        {"chapter": 31, "stage": "高光", "title": "撕扇博笑", "note": "撕扇以博宝玉一笑，真率无伪。", "fortune": 65},
        {"chapter": 74, "stage": "转", "title": "抄检被诬", "note": "抄检大观园，被诬为「狐狸精」。", "fortune": -30, "event": "hlm-e-005"},
        {"chapter": 78, "stage": "结局", "title": "含冤夭亡", "note": "补裘后病倒，被撵出府，含冤而逝。", "fortune": -100},
    ],
    "袭人": [
        {"chapter": 3, "stage": "出场", "title": "服侍宝玉", "note": "贾母所赐，居怡红院，温柔尽职。", "fortune": 30},
        {"chapter": 19, "stage": "起", "title": "花解语订箴规", "note": "良宵以赎身试探，订读书、不毁僧道等三条箴规（非回目「箴宝玉」）。", "fortune": 45},
        {"chapter": 21, "stage": "高光", "title": "娇嗔箴宝玉", "note": "回目「贤袭人娇嗔箴宝玉」；因宝玉与姊妹厮闹、蘸胭脂等冷脸规劝。", "fortune": 50},
        {"chapter": 89, "stage": "转", "title": "侍疾晴雯", "note": "晴雯补雀金裘后，袭人悉心侍疾。", "fortune": 40},
        {"chapter": 97, "stage": "结局", "title": "配蒋玉菡", "note": "王夫人放出去配蒋玉菡（程高本），「花气袭人知昼暖」。", "fortune": 50},
    ],
    "尤二姐": [
        {"chapter": 64, "stage": "出场", "title": "被琏偷娶", "note": "尤家二姑娘，被贾琏偷娶于小花枝巷。", "fortune": 35},
        {"chapter": 65, "stage": "高光", "title": "暂安大观园", "note": "凤姐「赚」入府，暂居厢房，一度以为得所。", "fortune": 45},
        {"chapter": 69, "stage": "结局", "title": "吞金自逝", "note": "受凤姐、秋桐凌虐，吞金而死。", "fortune": -100},
    ],
    "尤三姐": [
        {"chapter": 64, "stage": "出场", "title": "拒轻薄", "note": "骂醒贾珍、贾琏，性情刚烈。", "fortune": 40},
        {"chapter": 65, "stage": "高光", "title": "订嫁柳湘莲", "note": "心属柳湘莲，非宝玉，以剑为聘。", "fortune": 55},
        {"chapter": 67, "stage": "结局", "title": "自刎殉情", "note": "柳湘莲退婚，三姐自刎于剑下，柳湘莲遂出家。", "fortune": -100},
    ],
    "薛蟠": [
        {"chapter": 4, "stage": "出场", "title": "葫芦案打死冯渊", "note": "争买香菱，打死冯渊，「护官符」案显薛家权势。", "fortune": 20},
        {"chapter": 21, "stage": "转", "title": "打死多官", "note": "再惹人命，呆霸王本色。", "fortune": -25},
        {"chapter": 48, "stage": "低谷", "title": "遭柳湘莲痛打", "note": "因轻薄柳湘莲，遭痛打，颜面尽失。", "fortune": -40},
        {"chapter": 86, "stage": "结局", "title": "发配流放", "note": "后四十回因人命等事发配（程高本），夏金桂事牵连香菱。", "fortune": -70},
    ],
}


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def main() -> None:
    char_dir = CHAR_DIR / BOOK
    updated = 0
    for cid, arc in ARCS.items():
        path = char_dir / f"{cid}.md"
        if not path.is_file():
            print(f"  skip: 无页 {cid}")
            continue
        fm, body = parse_frontmatter(path)
        if fm.get("arc"):
            print(f"  skip: {cid} 已有 arc")
            continue
        fm["arc"] = arc
        write_frontmatter(path, fm, body)
        print(f"  {cid}: +{len(arc)} 节点")
        updated += 1
    print(f"[{BOOK}] 注入 arc: {updated} 人")


if __name__ == "__main__":
    main()
