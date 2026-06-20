#!/usr/bin/env python3
"""医药 / 服饰 / 民俗 物质推演：全书曲线 + 社会分层 + saga 互参。"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter
from _material_inference_common import (
    BOOK_CONFIG,
    build_social_block,
    chapter_num,
    load_saga_milestones,
    phase_for,
    smooth_chapter_rows,
    social_tier,
)

MEDICINES_DIR = CONTENT / "medicines"
COSTUMES_DIR = CONTENT / "costumes"
CUSTOMS_DIR = CONTENT / "customs"

DOMAINS: dict[str, dict] = {
    "medicine": {
        "dir": MEDICINES_DIR,
        "out_suffix": "medicine-inference",
        "entity_types": ("medicine", "prescription", "diagnosis"),
        "link_field": "patients",
        "domain_label": "药疗水平",
        "curve_primary": "精细度",
        "curve_secondary": "危机度",
        "inference_note": "推演层：脉案/方剂/庸医/求神关键词 + 社会分层 + 人物病理档案（inference）；非医学史定论。",
        "axes": [
            ("pulse_refined", "脉案精细", "张友士级详脉、证候辨析"),
            ("tonic_luxury", "参茸温补", "人参、阿胶、上等人参"),
            ("prescription_norm", "方剂规范", "汤丸膏散、益神养荣"),
            ("folk_belief", "求神符咒", "还愿、求神、毛半仙"),
            ("quack_risk", "庸医虎狼", "胡庸医、虎狼药、误治"),
            ("acute_crisis", "时气急症", "时气、吐血、血崩、脱阳"),
        ],
        "keywords": [
            ("pulse_refined", "脉", 2), ("pulse_refined", "诊脉", 3), ("pulse_refined", "脉案", 3),
            ("pulse_refined", "张友士", 3), ("pulse_refined", "王太医", 2), ("pulse_refined", "鲍太医", 2),
            ("tonic_luxury", "人参", 3), ("tonic_luxury", "阿胶", 2), ("tonic_luxury", "参", 2),
            ("tonic_luxury", "养荣", 2), ("tonic_luxury", "补心", 2), ("tonic_luxury", "胡僧", 2),
            ("prescription_norm", "汤", 1), ("prescription_norm", "丸", 2), ("prescription_norm", "方", 1),
            ("prescription_norm", "益神", 2), ("prescription_norm", "疏肝", 2), ("prescription_norm", "固金", 2),
            ("folk_belief", "求神", 3), ("folk_belief", "还愿", 3), ("folk_belief", "半仙", 2),
            ("folk_belief", "占卦", 2), ("folk_belief", "薛姑子", 2), ("folk_belief", "马道婆", 3),
            ("folk_belief", "痘疹", 2), ("folk_belief", "符", 2),
            ("quack_risk", "庸医", 3), ("quack_risk", "胡庸", 3), ("quack_risk", "虎狼", 3),
            ("quack_risk", "误", 1), ("quack_risk", "胡君荣", 2), ("quack_risk", "枳实", 2),
            ("quack_risk", "黄芩", 2),
            ("acute_crisis", "时气", 2), ("acute_crisis", "吐血", 2), ("acute_crisis", "血崩", 3),
            ("acute_crisis", "脱阳", 3), ("acute_crisis", "绝粒", 2), ("acute_crisis", "砒霜", 3),
            ("acute_crisis", "崩漏", 3),
            ("tonic_luxury", "养荣丸", 3), ("tonic_luxury", "冷香丸", 2), ("tonic_luxury", "鹿茸", 2),
        ],
        "category_bias": {
            "诊脉": {"pulse_refined": 3},
            "丸散": {"prescription_norm": 2},
            "病症": {"acute_crisis": 2},
        },
        "focus_hlm": ["林黛玉", "贾母", "秦可卿", "晴雯", "王熙凤", "薛宝钗", "尤二姐", "贾宝玉"],
        "focus_jpm": ["西门庆", "李瓶儿", "潘金莲", "吴月娘", "庞春梅"],
        "char_notes_hlm": {
            "林黛玉": "人参养荣丸自幼服用，体质阴虚火旺却长期温补（推演：火上浇油）。高焦虑寄居→忧肺思脾；痨病叠加免疫崩盘，是精神高压在生理上的排异（inference）。",
            "贾宝玉": "嗜食女儿唇上胭脂；明清上等胭脂多含朱砂（硫化汞）。推演：长期微量汞摄入→情绪不稳、神志恍惚，与后期「疯癫」并读（inference）。",
            "王熙凤": "小产后强撑管家→「下元亏损、便溺带血」（崩漏/功血）；第77回配药难求上好人参。推演：职场过劳+慢性失血+抄家打击（inference）。",
            "薛宝钗": "胎里「热毒」、怕热喘嗽；嗜甜食，常年冷香丸（花蕊霜雪+冰片）。推演：代谢偏旺/过敏性哮喘，丸药多为清凉剂与精神安慰剂（inference）。",
            "晴雯": "第51回风寒后只能后门请走方郎中；胡庸医开枳实、黄芩虎狼药，宝玉斥「内虚怎受得住」。推演：阶级医疗缺失+误治→急症恶化（inference）。",
            "秦可卿": "病中「今日张说明日李说」；张友士脉案为全书医笔高峰。推演：多医试验+心力衰竭型过劳，与贾府 CEO 宿命互文（inference）。",
            "贾母": "不适即召王太医等太医院一脉；参汤、消导并见。与晴雯/刘姥姥线对照，标示御医资源私有化（inference）。",
            "尤二姐": "胡君荣误治、吞金；庶出女性医疗与礼法双重弱势（inference）。",
        },
        "char_notes_jpm": {
            "西门庆": "胡僧药+脱阳；司法座右铭「太师府认得我字迹」；空间扩张+资本轴（推演）。",
            "李瓶儿": "血崩、滋补与财富引来迫害；新花园空间特权（推演）。",
            "潘金莲": "前边花园边缘空间；司法/恩宠争夺（推演）。",
            "应伯爵": "帮闲凑分、结拜、蔡府寿礼；酒肉与信息交换（推演）。",
        },
    },
    "costume": {
        "dir": COSTUMES_DIR,
        "out_suffix": "costume-inference",
        "entity_types": ("costume",),
        "link_field": "wearers",
        "domain_label": "服饰精神面貌",
        "curve_primary": "炫耀度",
        "curve_secondary": "信物性",
        "inference_note": "推演层：织品/首饰/礼服/信物/洋货关键词 + 社会分层 + 人物服饰档案（inference）；非法制史定论。",
        "axes": [
            ("silk_brocade", "绸缎绣", "妆缎、刻丝、织锦"),
            ("jewelry_rank", "首饰等级", "金、珠、凤、麒麟"),
            ("ceremonial", "礼仪礼服", "省亲、蟒、大红妆"),
            ("daily_plain", "日常简素", "旧衣、粗布、简装"),
            ("symbolic_token", "信物隐喻", "玉、帕、锁、剑、汗巾"),
            ("foreign_rare", "异域稀有", "雀金、俄罗斯、洋"),
        ],
        "keywords": [
            ("silk_brocade", "缎", 2), ("silk_brocade", "绣", 2), ("silk_brocade", "罗", 2),
            ("silk_brocade", "绸", 2), ("silk_brocade", "锦", 2), ("silk_brocade", "刻丝", 3),
            ("jewelry_rank", "金", 1), ("jewelry_rank", "珠", 2), ("jewelry_rank", "凤", 2),
            ("jewelry_rank", "麒麟", 2), ("jewelry_rank", "累丝", 3), ("jewelry_rank", "头面", 2),
            ("ceremonial", "省亲", 3), ("ceremonial", "蟒", 3), ("ceremonial", "大红", 2),
            ("ceremonial", "礼服", 3), ("ceremonial", "寿", 1),
            ("daily_plain", "旧", 2), ("daily_plain", "粗", 2), ("daily_plain", "简", 1),
            ("symbolic_token", "玉", 2), ("symbolic_token", "帕", 2), ("symbolic_token", "锁", 2),
            ("symbolic_token", "剑", 2), ("symbolic_token", "汗巾", 2), ("symbolic_token", "荷包", 1),
            ("foreign_rare", "雀金", 3), ("foreign_rare", "俄罗斯", 3), ("foreign_rare", "洋", 2),
            ("foreign_rare", "境外", 2), ("foreign_rare", "呢", 2), ("foreign_rare", "哆啰", 3),
            ("foreign_rare", "貂", 2), ("foreign_rare", "狐", 2), ("foreign_rare", "猩", 2),
            ("foreign_rare", "凫", 2), ("foreign_rare", "羽纱", 2),
            ("silk_brocade", "洋缎", 3), ("ceremonial", "箭袖", 2), ("ceremonial", "窄裉", 2),
            ("daily_plain", "半新", 2), ("daily_plain", "蜜合", 2), ("daily_plain", "衲", 2),
            ("symbolic_token", "小袄", 2),
        ],
        "category_bias": {},
        "focus_hlm": ["贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母", "晴雯", "史湘云", "贾元春"],
        "focus_jpm": ["西门庆", "潘金莲", "李瓶儿", "孟玉楼", "庞春梅", "吴月娘"],
        "char_notes_hlm": {
            "王熙凤": "第3回金丝八宝、刻丝银鼠褂、大红洋缎窄裉袄——金珠刻丝堆叠如「权力甲胄」（inference）。败落后「破席裹尸」与前期洋缎五彩形成阶级跌落对照。",
            "林黛玉": "第49回雪天「大红羽纱剪绒里猩猩毡斗篷」——孤傲文人审美，雪中一抹纯猩红（inference）。与「冷月葬花魂」并读。",
            "薛宝钗": "常年半新不旧、蜜合色棉袄——低调顺从礼法，甘做背景板（inference）；[[金锁]]与省亲礼服是正统归宿。",
            "贾宝玉": "大红箭袖、雀金呢、拒穿补服——女红化富贵色对抗仕途男装（inference）；抄家后粗布衲衣、赤足拜别。",
            "晴雯": "[[雀金裘]]补裘与奴婢身份矛盾；临终与宝玉交换小袄——对「衣服剥夺人格」的阶级反抗（inference）。",
            "史湘云": "第49回貂鼠脑袋面子大袄——雪地诗社皮草秀一环；豪爽与特权符号并置。",
            "贾母": "库房软烟罗、赐晴雯雀金裘——顶级织品分配权在族长手中。",
            "贾元春": "[[省亲礼服]]；皇权礼仪与家族荣耀的服饰峰值，僭越与合规的边界。",
        },
        "char_notes_jpm": {
            "西门庆": "貂鼠蟒衣销金=暴发户炫耀；与买办洋货、空间扩张并读（推演）。",
            "潘金莲": "红睡鞋、汗巾；前边旧宅空间边缘→服饰情欲互证（推演）。",
            "李瓶儿": "新花园三层洋房=财富峰值空间；引发金莲阶级仇恨（推演）。",
            "吴月娘": "正房礼服特权；宗法空间不可动摇（推演）。",
        },
    },
    "custom": {
        "dir": CUSTOMS_DIR,
        "out_suffix": "custom-inference",
        "entity_types": ("custom", "funeral", "festival", "ritual", "institution"),
        "link_field": "participants",
        "domain_label": "民俗状态",
        "curve_primary": "礼制密度",
        "curve_secondary": "逾制/异端",
        "inference_note": "推演层：节令/丧祭/婚嫁/制度/魇魅关键词 + 社会分层 + 人物民俗档案（inference）；非礼制史定论。",
        "axes": [
            ("festival", "节令年例", "元宵、端午、中秋、年例"),
            ("funeral_rite", "丧祭礼仪", "丧仪、停灵、水陆、路祭"),
            ("marriage", "婚嫁", "出嫁、成婚、财礼"),
            ("clan_institution", "宗族制度", "宗祠、月例、义学、护官符"),
            ("folk_magic", "魇魅迷信", "魇法、求神、剪发"),
            ("state_norm", "逾制争议", "买官、诰命、尽用"),
        ],
        "keywords": [
            ("festival", "元宵", 3), ("festival", "端午", 3), ("festival", "中秋", 3),
            ("festival", "年例", 2), ("festival", "节", 1), ("festival", "芒种", 3),
            ("festival", "葬花", 3), ("festival", "夜宴", 2), ("festival", "省亲", 2),
            ("funeral_rite", "丧", 2), ("funeral_rite", "祭", 2), ("funeral_rite", "灵", 2),
            ("funeral_rite", "殡", 2), ("funeral_rite", "水陆", 2), ("funeral_rite", "宗祠", 2),
            ("marriage", "嫁", 2), ("marriage", "娶", 2), ("marriage", "婚", 2), ("marriage", "财礼", 2),
            ("marriage", "抓周", 3), ("marriage", "乞巧", 2),
            ("clan_institution", "宗祠", 3), ("clan_institution", "月例", 2), ("clan_institution", "义学", 2),
            ("clan_institution", "护官符", 3), ("clan_institution", "官钱", 2), ("clan_institution", "祭祖", 3),
            ("folk_magic", "魇", 3), ("folk_magic", "魔法", 3), ("folk_magic", "求神", 2),
            ("folk_magic", "剪发", 2), ("folk_magic", "誓", 1), ("folk_magic", "马道婆", 3),
            ("folk_magic", "纸人", 2), ("folk_magic", "还愿", 2),
            ("state_norm", "逾制", 3), ("state_norm", "买官", 3), ("state_norm", "诰命", 2),
            ("state_norm", "尽用", 2), ("state_norm", "龙禁尉", 2), ("state_norm", "红麝", 2),
        ],
        "category_bias": {
            "丧礼": {"funeral_rite": 3},
            "节令": {"festival": 3},
        },
        "focus_hlm": ["贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母", "贾珍", "贾元春", "刘姥姥"],
        "focus_jpm": ["西门庆", "吴月娘", "潘金莲", "李瓶儿", "应伯爵"],
        "char_notes_hlm": {
            "林黛玉": "第27回芒种葬花——送花神/饯春植物祭祀；把自己当花神，拒向「夏日」妥协（inference）。与端午赐礼线对照。",
            "薛宝钗": "第28回端午元春赐礼：与宝玉同款红麝串，黛玉不同——恶月祛毒民俗中的「镇邪求稳」（inference）；金玉良缘合法化。",
            "贾宝玉": "第2回冷子兴：周岁抓周只取脂粉钗环——对仕途继承最原始背叛（inference）；元宵省亲极盛 vs 最终僧袍。",
            "王熙凤": "第54回元宵夜宴讲「聋子放炮」「翻江子」——乐极生悲、抄家谶语（inference）；巧姐七夕生，刘姥姥「以毒攻毒」取名。",
            "贾珍": "可卿丧仪极尽+买官；第53回祭祖排场与乌进孝账单并置——宗族泡沫（inference）。",
            "贾母": "宗祠祭祖、元宵夜宴主持；中秋强撑笛声——家族团圆仪式最后的维持者。",
            "贾元春": "省亲大礼；端午赐礼定调——皇权节令介入贾府命运。",
            "刘姥姥": "巧姐取名、还愿求神；底层民俗经验在贾府庇护失效后救巧姐（inference）。",
        },
        "char_notes_jpm": {
            "西门庆": "玉皇庙结拜、蔡府寿礼、帮闲凑分——礼俗服务资本与司法庇护（推演）。",
            "吴月娘": "正室主持年例、丧祭；宗法礼制轴心（推演）。",
            "应伯爵": "酒席礼俗中的帮闲节点；人走茶凉（推演）。",
        },
    },
}


def score_from_blob(blob: str, category: str, domain_cfg: dict) -> dict[str, int]:
    axis_ids = [a[0] for a in domain_cfg["axes"]]
    scores = {a: 0 for a in axis_ids}
    for axis, kw, w in domain_cfg["keywords"]:
        if kw in blob:
            scores[axis] += w
    for prefix, bias in domain_cfg.get("category_bias", {}).items():
        if prefix in category:
            for axis, w in bias.items():
                scores[axis] += w
    manual = None  # future inference_axes in frontmatter
    return scores


def primary_index(domain: str, scores: dict[str, int]) -> float:
    if domain == "medicine":
        v = scores.get("pulse_refined", 0) * 8 + scores.get("prescription_norm", 0) * 6
        v += scores.get("tonic_luxury", 0) * 5
        v -= scores.get("quack_risk", 0) * 2
        return round(max(0, min(100, 15 + v * 2)), 1)
    if domain == "costume":
        v = scores.get("silk_brocade", 0) * 6 + scores.get("jewelry_rank", 0) * 5
        v += scores.get("ceremonial", 0) * 7 + scores.get("foreign_rare", 0) * 8
        v -= scores.get("daily_plain", 0) * 4
        return round(max(0, min(100, 10 + v * 2.5)), 1)
    # custom
    v = scores.get("festival", 0) * 5 + scores.get("funeral_rite", 0) * 6
    v += scores.get("marriage", 0) * 4
    v += scores.get("clan_institution", 0) * 5
    return round(max(0, min(100, 12 + v * 2)), 1)


def secondary_index(domain: str, scores: dict[str, int]) -> float:
    if domain == "medicine":
        return round(
            scores.get("acute_crisis", 0) * 1.2 + scores.get("quack_risk", 0) * 1.0 - scores.get("pulse_refined", 0) * 0.3,
            2,
        )
    if domain == "costume":
        return round(scores.get("symbolic_token", 0) * 1.1 - scores.get("daily_plain", 0) * 0.5, 2)
    return round(scores.get("folk_magic", 0) * 1.2 + scores.get("state_norm", 0) * 1.0, 2)


def normalize_links(raw, field: str) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    out: list[str] = []
    for e in raw:
        name = re.sub(r"等$", "", str(e).strip())
        if name and name not in out:
            out.append(name)
    if field == "wearers" and not out:
        return []
    return out


def load_catalog(book: str, domain: str, domain_cfg: dict) -> dict[str, dict]:
    d = domain_cfg["dir"] / book
    if not d.is_dir():
        return {}
    link_field = domain_cfg["link_field"]
    types = domain_cfg["entity_types"]
    catalog: dict[str, dict] = {}
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != book:
            continue
        if domain not in ("costume", "custom") and fm.get("type") not in types:
            continue
        chs: set[int] = set()
        c0 = chapter_num(fm.get("first_appear"))
        if c0:
            chs.add(c0)
        for ap in fm.get("appear_in") or []:
            c = chapter_num(ap)
            if c:
                chs.add(c)
        blob = " ".join(str(fm.get(k, "") or "") for k in ("name", "summary", "category", "material", "legal_norm", "economic", "syndrome", "pulse"))
        if domain == "costume":
            blob += " " + str(fm.get("material", "")) + " " + str(fm.get("color", ""))
        if domain == "custom":
            blob += " " + str(fm.get("procedure", "")) + " " + str(fm.get("economic", ""))

        scores = score_from_blob(blob, str(fm.get("category") or fm.get("type") or ""), domain_cfg)

        if domain == "medicine":
            links = normalize_links(fm.get("patient") or fm.get("patients"), "patients")
        elif domain == "costume":
            links = normalize_links(fm.get("wearer") or fm.get("wearers"), "wearers")
        else:
            links = normalize_links(fm.get("participants"), "participants")

        catalog[fm["id"]] = {
            "id": fm["id"],
            "name": fm.get("name", fm["id"]),
            "category": fm.get("category", fm.get("type", "")),
            "chapters": sorted(chs),
            link_field: links,
            "scores": scores,
            "primary": primary_index(domain, scores),
            "secondary": secondary_index(domain, scores),
            "source": "entity",
        }
    return catalog


def medicine_risk_tags(ax: dict[str, int], cid: str) -> list[str]:
    tags: list[str] = []
    if ax.get("tonic_luxury", 0) >= 3 and cid in ("林黛玉", "薛宝钗", "贾母"):
        tags.append("参茸温补轴高，或误于体质（推演）")
    if ax.get("quack_risk", 0) >= 2 or cid in ("晴雯", "尤二姐"):
        tags.append("庸医/虎狼药风险")
    if ax.get("folk_belief", 0) >= 2:
        tags.append("巫医求神线并置")
    if ax.get("acute_crisis", 0) >= 3 or cid in ("王熙凤", "林黛玉"):
        tags.append("血崩/时气/急症轴高")
    if ax.get("pulse_refined", 0) >= 6:
        tags.append("详脉着墨密集")
    return tags[:4]


def costume_risk_tags(ax: dict[str, int], cid: str) -> list[str]:
    tags: list[str] = []
    if ax.get("foreign_rare", 0) >= 3 or cid in ("贾宝玉", "晴雯"):
        tags.append("异域/皮草/洋货轴高（推演）")
    if ax.get("ceremonial", 0) >= 4 or cid in ("王熙凤", "贾元春"):
        tags.append("礼仪礼服/僭越符号密集")
    if ax.get("jewelry_rank", 0) >= 4:
        tags.append("首饰等级轴高")
    if ax.get("daily_plain", 0) >= 2 and cid == "薛宝钗":
        tags.append("简素低调，礼法顺从")
    if ax.get("symbolic_token", 0) >= 3:
        tags.append("信物隐喻轴高")
    return tags[:4]


def custom_risk_tags(ax: dict[str, int], cid: str) -> list[str]:
    tags: list[str] = []
    if ax.get("festival", 0) >= 4:
        tags.append("节令仪式轴高")
    if ax.get("folk_magic", 0) >= 3 or cid in ("王熙凤", "贾宝玉"):
        tags.append("魇魅/巫术线并置")
    if ax.get("clan_institution", 0) >= 4 or cid in ("贾珍", "贾母"):
        tags.append("宗族礼制密集")
    if ax.get("state_norm", 0) >= 3:
        tags.append("逾制/争议轴高")
    if ax.get("funeral_rite", 0) >= 3:
        tags.append("丧祭礼仪着墨")
    return tags[:4    ]


def build_jinpingmei_cross_insights(domain: str) -> list[dict]:
    """金瓶梅：四横切面总论（按 medicine/costume/custom 域侧重）。"""
    common = [
        {
            "title": "世情四横切面总论",
            "body": "金融四步经、空间政治学、胃囊社会学、司法三级通关——人物→府邸溃败→全社会三层推演（inference）。",
            "evidence": ["世情四横切面与社会推演", "药铺与放债链", "西门府建筑名录"],
        },
    ]
    finance = [
        {
            "title": "四步金融经：婚姻兼并",
            "body": "孟玉楼/李瓶儿携财=原始资本恶意收购；瓶儿财富引金莲害官哥儿——府内金融阶级斗争（推演）。",
            "evidence": ["孟玉楼", "李瓶儿", "潘金莲", "官哥儿"],
        },
        {
            "title": "三分利与产业矩阵",
            "body": "月息30%抽干清河；绸缎绒线铺+苏杭现款扫货=金融-物流-零售垄断（推演）。",
            "evidence": ["吴典恩", "常峙节", "韩道国"],
        },
        {
            "title": "买官庇护与金融空心化",
            "body": "贿蔡京得理刑千户；白银买官盖园非转工业→晚明资本非生产性异化（经济史 inference）。",
            "evidence": ["蔡京", "提刑千户", "苗员外"],
        },
        {
            "title": "胡僧药：身体的次贷杠杆",
            "body": "纵欲+胡僧药强行维持账面；杠杆断裂=猝然生理破产，与资本宿主命运同构（推演）。",
            "evidence": ["胡僧药", "西门庆"],
        },
        {
            "title": "死后清算：帮闲与韩道国",
            "body": "应伯爵投张二官、韩道国卷款——无核心现金流后婚姻友情团队互噬（推演）。",
            "evidence": ["应伯爵", "张二官", "韩道国"],
        },
    ]
    space = [
        {
            "title": "正房·西厢·新楼：后院地缘政治",
            "body": "月娘上房=宗法锚点；金莲西厢边缘窥视；瓶儿三层新楼=资本特权亦成坟墓（推演）。",
            "evidence": ["吴月娘", "潘金莲", "李瓶儿", "官哥儿"],
        },
        {
            "title": "二门失守与陈经济渗透",
            "body": "西门庆死后门禁失效；陈经济穿梭后院——空间守门人消失则府邸被瓜分（推演）。",
            "evidence": ["陈经济", "西门庆", "李娇儿"],
        },
        {
            "title": "兼并外环：花子虚与乔大户",
            "body": "扩园吞并邻居房产改街道→清河土地兼并、高墙内外阶层撕裂缩影（推演）。",
            "evidence": ["花子虚", "乔大户", "花园"],
        },
    ]
    legal = [
        {
            "title": "三级司法通关",
            "body": "武松案基层贿败→花子虚跨区洗劫→苗员外案买理刑千户；司法工具化（推演）。",
            "evidence": ["武松", "花子虚", "苗员外", "蔡京"],
        },
        {
            "title": "律法商品化与信用归零",
            "body": "两千两改人命；大理寺管不着我银子——基层司法溃烂则统治合法性归零（政治 inference）。",
            "evidence": ["西门庆", "县衙", "提刑千户所"],
        },
    ]
    by_domain = {
        "medicine": common + finance,
        "costume": common + [
            {
                "title": "锦衣与资本外化",
                "body": "绸缎绒线垄断+妻妾锦衣=资本峰值的空间—服饰显影；非红楼诗意衣饰（推演）。",
                "evidence": ["西门庆", "李瓶儿", "孟玉楼"],
            },
        ] + space[:1],
        "custom": common + space + legal[:1],
    }
    return by_domain.get(domain, common + finance[:2])


def build_custom_global_insights(book: str, social: dict, chars: list[dict]) -> list[dict]:
    """红楼梦民俗：人物民俗学 + 节日倒计时 + 全社会四横切面（inference）。"""
    if book != "红楼梦":
        return []
    return [
        {
            "title": "人物民俗：仪式固定的悲剧线",
            "body": "黛玉芒种葬花=植物祭祀；宝钗端午红麝=镇邪求稳；宝玉抓周背叛继承；凤姐元宵笑话成谶；巧姐七夕名=底层民俗救场（推演）。",
            "evidence": ["林黛玉", "薛宝钗", "贾宝玉", "王熙凤", "巧姐托姥姥"],
        },
        {
            "title": "节日倒计时：元宵→端午→中秋→祭祖",
            "body": "元宵极盛（省亲/夜宴）→端午五毒争斗（赐礼/提亲）→中秋无月散场（冷月葬花魂）→除夕祭祖+乌进孝缩水=终局祭坛（推演）。",
            "evidence": ["元宵夜宴", "端午", "中秋", "宗祠祭祖"],
        },
        {
            "title": "横切面一：除夕祭祖与宗族泡沫",
            "body": "第53回祭祖最庄严，同时乌进孝账单缩水——以孝治天下的仪式维持等级，经济根基已断（宗法 inference）。",
            "evidence": ["宗祠祭祖", "年例", "秦可卿丧仪"],
        },
        {
            "title": "横切面二：中秋无月与小农下行",
            "body": "第75–76回中秋宴颓败、无月凶兆——秋收节令成色挂钩年成；帝国下行周期缩影（经济—民俗 inference）。",
            "evidence": ["中秋", "凸碧堂"],
        },
        {
            "title": "横切面三：端午驱邪与巫术焦虑",
            "body": "红麝串、雄黄祛五毒；马道婆魇魔法、赵姨娘扎小人——各阶层精神不安全，转向巫术私刑（心理—社会 inference）。",
            "evidence": ["魇魔法", "端午", "刘姥姥求神"],
        },
        {
            "title": "横切面四：刘姥姥取名与底层续命",
            "body": "巧姐七夕生，凤姐求刘姥姥「以毒攻毒」取名——上层庇护失效后，底层农耕民俗延续血脉（阶级和解 inference）。",
            "evidence": ["巧姐托姥姥", "巧哥儿名", "刘姥姥"],
        },
        {
            "title": "终极：民俗天网与文化挽歌",
            "body": "每过一节=宗法引力拉回一步；仪式残缺变味时，封建文化根基风化——白茫茫大地是民俗丧钟（文学—社会 inference）。",
            "evidence": ["好了歌", "查抄", "冷月葬花魂"],
        },
    ]


def build_costume_global_insights(book: str, social: dict, chars: list[dict]) -> list[dict]:
    """红楼梦服饰：人物服饰学 + 全社会四横切面（inference）。"""
    if book != "红楼梦":
        return []
    return [
        {
            "title": "人物服饰：衣如其人的第二皮肤",
            "body": "凤姐刻丝银鼠如权力甲胄；黛玉猩猩毡孤傲；宝钗半新蜜合色顺从；宝玉大红箭袖拒补服；晴雯雀金裘+换小袄——性格与宿命写在丝绸上（推演）。",
            "evidence": ["王熙凤", "林黛玉", "薛宝钗", "贾宝玉", "晴雯", "雀金裘"],
        },
        {
            "title": "横切面一：奢侈洋货与买办经济",
            "body": "大红洋缎、雀金呢、哆啰呢等洋货轴高；十三行白银换奢侈品、非生产性消费——买办权贵享受全球化红利（经济史 inference）。",
            "evidence": ["雀金裘", "大红妆缎", "软烟罗"],
        },
        {
            "title": "横切面二：皮毛政治学与旗人退化",
            "body": "第49回雪地诗社：猩猩毡、狐腋箭袖、貂鼠大袄——满族皮毛特权在温室里冗余展示；强悍体魄已失（社会学 inference）。",
            "evidence": ["史湘云", "林黛玉", "贾宝玉"],
        },
        {
            "title": "横切面三：衣服等级与阶级毒性",
            "body": "《大清律例》舆服限制；奴才不得衣丝绸。晴雯「妖里妖气」因绫罗；死前换小袄是对人格剥夺的反抗（法制—阶级 inference）。",
            "evidence": ["晴雯", "旧衣", "雀金裘"],
        },
        {
            "title": "横切面四：江宁织造与财政雪崩",
            "body": "内务府料子、南巡垫付、织造亏空——华服背后是江南血汗被抽干；抄家充公华服=宏观泡沫破裂（曹学 inference）。",
            "evidence": ["省亲礼服", "查抄", "大红妆缎"],
        },
        {
            "title": "终极：从锦衣纨绔到捉襟见肘",
            "body": "前部织金缂丝孔雀羽堆砌；后部《好了歌解注》「昨怜破袄寒，今嫌紫蟒长」。凤姐衣不蔽体、宝玉衲衣雪行——阶级大网撕裂（文学—社会 inference）。",
            "evidence": ["好了歌", "王熙凤", "贾宝玉"],
        },
    ]


def build_medicine_global_insights(book: str, social: dict, chars: list[dict]) -> list[dict]:
    """红楼梦医药：人物病理 + 全社会四病灶（inference）。"""
    if book != "红楼梦":
        return []
    return [
        {
            "title": "人物病理：高级监护室里的贵族病",
            "body": "黛玉高敏感+误补→免疫崩盘；宝玉胭脂汞中毒→神志恍惚；凤姐/可卿 CEO 式过劳→崩漏与衰竭；宝钗以冷香丸压「热毒」；晴雯死于医疗阶级差+庸医催命（推演）。",
            "evidence": ["林黛玉", "贾宝玉", "王熙凤", "晴雯", "薛宝钗", "秦可卿"],
        },
        {
            "title": "病灶一：医疗资源阶级垄断",
            "body": "贾母宝玉随叫太医；晴雯只能后门请走方郎中，虎狼药几乎催命。顶级技术被圈养在权力顶层，底层赌庸医——医疗不对称是隐形阶级矛盾（推演）。",
            "evidence": ["王太医诊晴雯", "胡庸医诊晴雯", "贾母参汤"],
        },
        {
            "title": "病灶二：人参金融化与进补泡沫",
            "body": "全书参茸温补轴高；第77回凤姐配药翻府只找到碎参，需向薛家求助。推演：八旗权贵「全民进补」使人参成硬通货，资源枯竭与财政掏空同向（inference）。",
            "evidence": ["上等人参", "人参养荣丸", "凤姐小月脉案"],
        },
        {
            "title": "病灶三：巫医混杂与科学蒙昧",
            "body": "马道婆魇魔法、巧姐痘疹供娘娘、毛半仙占卦与太医脉案并置。精英阶层面对天花/邪病仍半在医学半在神棍——公共卫生与智力上的整体蒙昧（推演）。",
            "evidence": ["毛半仙占卦", "刘姥姥求神", "赵姨娘办理后事"],
        },
        {
            "title": "病灶四：高夭折率的人口周期",
            "body": "贾珠、可卿、黛玉、晴雯皆青年暴卒；贾府尚如此，底层农村婴幼儿与产妇死亡率更残酷。医药书写还原「高出生、高死亡、低均寿」古代人口真相（推演）。",
            "evidence": ["黛玉绝粒", "晴雯", "秦可卿", "贾珠"],
        },
        {
            "title": "终极隐喻：药罐子听见时代碎裂",
            "body": "荣国府如晚期凤姐——表面钟鸣鼎食，内里营养失衡、慢性中毒、伪科学依赖与参茸泡沫并存。靠过期人参与冷香丸维持体面时，「油尽灯枯」只是时间问题（社会学推演）。",
            "evidence": ["查抄", "冷香丸", "上等人参"],
        },
    ]


def expand_occurrences(catalog: dict[str, dict], link_field: str) -> list[dict]:
    rows: list[dict] = []
    for rec in catalog.values():
        for ch in rec.get("chapters") or []:
            rows.append({**rec, "chapter": ch})
    return [r for r in rows if r.get("chapter")]


def build_domain(book: str, domain: str) -> dict | None:
    if book not in BOOK_CONFIG:
        return None
    domain_cfg = DOMAINS[domain]
    cfg = BOOK_CONFIG[book]
    slug = cfg["slug"]
    chapter_count = cfg["chapters"]
    axis_ids = [a[0] for a in domain_cfg["axes"]]

    catalog = load_catalog(book, domain, domain_cfg)
    if not catalog:
        return None
    occurrences = expand_occurrences(catalog, domain_cfg["link_field"])
    link_field = domain_cfg["link_field"]

    by_ch: dict[int, list[dict]] = defaultdict(list)
    for row in occurrences:
        by_ch[int(row["chapter"])].append(row)

    chapter_rows = []
    for ch in range(1, chapter_count + 1):
        ds = by_ch.get(ch, [])
        agg = {a: 0 for a in axis_ids}
        for d in ds:
            for a in axis_ids:
                agg[a] += d["scores"][a]
        pri = round(sum(d["primary"] for d in ds) / len(ds), 1) if ds else 0
        sec = round(sum(d["secondary"] for d in ds) / len(ds), 2) if ds else 0
        chapter_rows.append(
            {
                "chapter": ch,
                "entity_count": len(ds),
                "luxury": pri,
                "balance": sec,
                "axes": agg,
                "phase": phase_for(book, ch),
                "entities": [x["id"] for x in ds],
            }
        )

    smooth_chapter_rows(chapter_rows, chapter_count, "entity_count", "luxury", "balance")

    char_axes: dict[str, dict[str, int]] = defaultdict(lambda: {a: 0 for a in axis_ids})
    char_entities: dict[str, list[str]] = defaultdict(list)
    for d in occurrences:
        for link in d.get(link_field) or ["__general__"]:
            cid = link if link != "__general__" else None
            if not cid:
                continue
            for a in axis_ids:
                char_axes[cid][a] += d["scores"][a]
            if d["id"] not in char_entities[cid]:
                char_entities[cid].append(d["id"])

    focus = domain_cfg["focus_hlm"] if book == "红楼梦" else domain_cfg["focus_jpm"]
    notes = domain_cfg["char_notes_hlm"] if book == "红楼梦" else domain_cfg["char_notes_jpm"]
    char_rows = []
    for cid in focus:
        ax = char_axes.get(cid, {a: 0 for a in axis_ids})
        has_note = cid in notes
        if sum(ax.values()) == 0 and not has_note:
            continue
        tier = social_tier(book, cid)
        risks: list[str] = []
        if domain == "medicine":
            risks = medicine_risk_tags(ax, cid)
        elif domain == "costume":
            risks = costume_risk_tags(ax, cid)
        elif domain == "custom":
            risks = custom_risk_tags(ax, cid)
        char_rows.append(
            {
                "id": cid,
                "name": cid,
                "social_tier": tier,
                "entity_count": len(char_entities.get(cid, [])),
                "axes": ax,
                "balance_score": round(sum(ax.values()) / max(len(char_entities.get(cid, [])), 1), 2),
                "risk_tags": risks,
                "inference": notes.get(cid, f"{cid} 相关{domain_cfg['domain_label']}实体 {len(char_entities.get(cid, []))} 条。"),
                "sample_entities": char_entities.get(cid, [])[:8],
            }
        )

    social = build_social_block(
        book,
        occurrences,
        axis_ids,
        link_field,
        domain_cfg["domain_label"],
        {a[0]: a[1] for a in domain_cfg["axes"]},
    )
    saga = load_saga_milestones(book, slug)
    peak = max(chapter_rows, key=lambda r: r.get("luxury_smooth", 0))

    global_insights = [
        {
            "title": f"全书{domain_cfg['curve_primary']}曲线",
            "body": f"按回聚合{domain_cfg['domain_label']}指数；峰回第{peak['chapter']}回（{peak['phase']}）。",
            "evidence": [str(peak["chapter"])],
        },
        {
            "title": social["title"],
            "body": social["inference"] or "见下方社会分层面板。",
            "evidence": [s["label"] for s in social["segments"][:3]],
        },
    ]
    if domain == "medicine":
        global_insights.extend(build_medicine_global_insights(book, social, char_rows))
    elif domain == "costume":
        global_insights.extend(build_costume_global_insights(book, social, char_rows))
    elif domain == "custom":
        global_insights.extend(build_custom_global_insights(book, social, char_rows))
    if book == "金瓶梅":
        global_insights.extend(build_jinpingmei_cross_insights(domain))

    return {
        "domain": domain,
        "book": book,
        "slug": slug,
        "generated_by": "build_material_inference.py",
        "inference_note": domain_cfg["inference_note"],
        "curve_labels": {
            "primary": domain_cfg["curve_primary"],
            "secondary": domain_cfg["curve_secondary"],
        },
        "axes": [{"id": a, "label": b, "desc": c} for a, b, c in domain_cfg["axes"]],
        "phases": [{"label": l, "from": lo, "to": hi} for l, lo, hi in cfg["phases"]],
        "saga_milestones": saga,
        "by_chapter": chapter_rows,
        "characters": char_rows,
        "social": social,
        "global_insights": global_insights,
        "stats": {
            "entity_count": len(catalog),
            "occurrence_rows": len(occurrences),
            "chapters_with_data": sum(1 for r in chapter_rows if r["entity_count"] > 0),
            "peak_chapter": peak["chapter"],
            "peak_primary": peak.get("luxury_smooth", 0),
            "saga_milestones": len(saga),
            "social_segments": len(social["segments"]),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("domain", nargs="?", choices=list(DOMAINS.keys()), default="medicine")
    ap.add_argument("book", nargs="?", default="红楼梦")
    ap.add_argument("--all-domains", action="store_true")
    ap.add_argument("--all-books", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    domains = list(DOMAINS.keys()) if args.all_domains else [args.domain]
    books = list(BOOK_CONFIG.keys()) if args.all_books else [args.book]

    for domain in domains:
        for book in books:
            payload = build_domain(book, domain)
            if not payload:
                print(f"skip: {domain} / {book}")
                continue
            slug = payload["slug"]
            out = DATA_DIR / f"{slug}.{DOMAINS[domain]['out_suffix']}.json"
            if args.write:
                out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                s = payload["stats"]
                print(f"  {slug}.{domain}: {s['occurrence_rows']} occ · {s['chapters_with_data']} ch · social {s['social_segments']}")
                print(f"written → {out.name}")
            else:
                print(json.dumps(payload["stats"], ensure_ascii=False))


if __name__ == "__main__":
    main()
