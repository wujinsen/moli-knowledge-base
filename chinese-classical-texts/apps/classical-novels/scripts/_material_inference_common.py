"""物质推演共用：书目阶段、saga、社会分层、曲线平滑。"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

EVENTS_DIR = CONTENT / "events"

BOOK_CONFIG: dict[str, dict] = {
    "红楼梦": {
        "slug": "honglou",
        "chapters": 120,
        "phases": [
            ("楔子·入府", 1, 16),
            ("省亲极盛", 17, 41),
            ("园宴精工", 42, 52),
            ("露剂·园规", 53, 71),
            ("晚景简素", 72, 100),
            ("末世崩散", 101, 120),
        ],
        "elite": {
            "贾母", "贾政", "王夫人", "贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾珍", "尤氏",
            "贾元春", "史湘云", "贾赦", "邢夫人", "薛姨妈", "薛蟠", "北静王", "贾蓉", "秦可卿",
            "李纨", "探春", "迎春", "惜春", "妙玉",
        },
        "folk": {
            "刘姥姥", "张道士", "马道婆", "胡庸医", "毛半仙", "王短腿", "村妇", "板儿",
        },
    },
    "金瓶梅": {
        "slug": "jinpingmei",
        "chapters": 100,
        "phases": [
            ("发迹根基", 1, 20),
            ("得官攀升", 21, 49),
            ("鼎盛极奢", 50, 79),
            ("衰败散府", 80, 100),
        ],
        "elite": {
            "西门庆", "吴月娘", "潘金莲", "李瓶儿", "孟玉楼", "庞春梅", "蔡京", "蔡御史",
            "应伯爵", "陈经济", "王六儿",
        },
        "folk": {
            "来旺儿", "宋德", "胡僧", "任医官", "薛姑子", "玳安", "傅伙计", "韩道国",
        },
    },
}


def chapter_num(raw: str | int | None) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    m = re.search(r"(\d+)", str(raw))
    return int(m.group(1)) if m else None


def phase_for(book: str, ch: int) -> str:
    for label, lo, hi in BOOK_CONFIG[book]["phases"]:
        if lo <= ch <= hi:
            return label
    return "其他"


def load_saga_milestones(book: str, slug: str) -> list[dict]:
    d = EVENTS_DIR / book
    if not d.is_dir():
        return []
    rows: list[dict] = []
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("subtype") != "milestone":
            continue
        chs = [int(c) for c in (fm.get("chapters") or []) if c]
        if not chs:
            continue
        rows.append(
            {
                "id": fm["id"],
                "title": fm.get("title", fm["id"]),
                "chapters": chs,
                "chapter": chs[0],
                "href": f"/{slug}/e/{fm['id']}",
            }
        )
    rows.sort(key=lambda r: r["chapter"])
    return rows


def smooth_chapter_rows(rows: list[dict], chapter_count: int, count_key: str, primary_key: str, secondary_key: str) -> None:
    for i, row in enumerate(rows):
        window = rows[max(0, i - 2) : min(chapter_count, i + 3)]
        active = [w for w in window if w[count_key] > 0]
        if active:
            row[f"{primary_key}_smooth"] = round(sum(w[primary_key] for w in active) / len(active), 1)
            row[f"{secondary_key}_smooth"] = round(sum(w[secondary_key] for w in active) / len(active), 2)
        else:
            row[f"{primary_key}_smooth"] = rows[i - 1].get(f"{primary_key}_smooth", 0) if i else 0
            row[f"{secondary_key}_smooth"] = rows[i - 1].get(f"{secondary_key}_smooth", 0) if i else 0


def social_tier(book: str, name: str) -> str:
    cfg = BOOK_CONFIG.get(book, {})
    n = str(name).strip()
    if not n:
        return "general"
    if n in cfg.get("elite", set()):
        return "elite"
    if n in cfg.get("folk", set()):
        return "folk"
    folk_kw = ("刘姥姥", "村", "僧", "道", "巫", "医官", "帮闲", "玳安", "来旺")
    if any(k in n for k in folk_kw):
        return "folk"
    servant_kw = ("婆", "妈", "丫头", "小厮", "仆", "役", "丫鬟", "晴雯", "袭人", "平儿", "紫鹃")
    if any(k in n for k in servant_kw):
        return "middling"
    return "general"


def build_social_block(
    book: str,
    occurrences: list[dict],
    axes: list[str],
    link_field: str,
    domain_label: str,
    axis_labels: dict[str, str] | None = None,
) -> dict:
    """全书实体按社会层聚合 → 全社会推演。"""
    tier_labels = {
        "elite": "权贵/主子层",
        "middling": "中层（体面仆婢·客商）",
        "folk": "市井/民间",
        "general": "未分层/制度性",
    }
    tier_agg: dict[str, dict[str, int]] = {t: {a: 0 for a in axes} for t in tier_labels}
    tier_entities: dict[str, list[str]] = defaultdict(list)
    tier_count: dict[str, int] = defaultdict(int)

    for occ in occurrences:
        links = occ.get(link_field) or []
        if not links:
            tier = "general"
            for a in axes:
                tier_agg[tier][a] += occ["scores"][a]
            tier_count[tier] += 1
            if occ["id"] not in tier_entities[tier]:
                tier_entities[tier].append(occ["id"])
            continue
        for link in links:
            tier = social_tier(book, link)
            for a in axes:
                tier_agg[tier][a] += occ["scores"][a]
            tier_count[tier] += 1
            if occ["id"] not in tier_entities[tier]:
                tier_entities[tier].append(occ["id"])

    segments = []
    for tid, label in tier_labels.items():
        if tier_count[tid] == 0 and not tier_entities[tid]:
            continue
        ax = tier_agg[tid]
        segments.append(
            {
                "id": tid,
                "label": label,
                "entity_count": len(tier_entities[tid]),
                "occurrence_weight": tier_count[tid],
                "axes": ax,
                "sample_entities": tier_entities[tid][:6],
            }
        )

    global_axes = {a: 0 for a in axes}
    for occ in occurrences:
        for a in axes:
            global_axes[a] += occ["scores"][a]

    insights = _social_insights(book, domain_label, segments, global_axes, axes, axis_labels)
    return {
        "title": f"全社会{domain_label}",
        "segments": segments,
        "global_axes": global_axes,
        "inference": insights[0]["body"] if insights else "",
        "insights": insights,
    }


def _social_insights(book: str, label: str, segments: list, global_axes: dict, axes: list[str], axis_labels: dict[str, str] | None = None) -> list[dict]:
    by_id = {s["id"]: s for s in segments}
    elite = by_id.get("elite")
    folk = by_id.get("folk")
    rows: list[dict] = []

    if elite and folk and axes:
        rows.append(
            {
                "title": f"阶层差：{label}不对称",
                "body": f"权贵层与市井层在文本中的{label}着墨密度悬殊；上层偏精细/排场，民间偏简易或求神问卜（推演）。",
                "evidence": (elite.get("sample_entities") or [])[:3] + (folk.get("sample_entities") or [])[:2],
            }
        )

    if book == "红楼梦":
        if label == "饮食水平":
            rows.extend(
                [
                    {
                        "title": "贾府餐桌 vs 全社会",
                        "body": "茄鲞、鸽蛋、乌进孝野味清单标示炫耀性消费；刘姥姥线提供底层对照——从舌尖可见阶级隔离与生态-财政红线（推演）。",
                        "evidence": ["茄鲞", "刘姥姥", "乌进孝", "祭宗祠"],
                    },
                    {
                        "title": "钟鸣鼎食与生理衰亡",
                        "body": "主子层精补肥甘、仆婢粗淡；同一社会内营养结构极化。饮食曲线与 saga 崩散同向，是「从胃到骨髓」的衰败写实（推演）。",
                        "evidence": ["林黛玉", "贾母", "查抄"],
                    },
                ]
            )
        elif label == "药疗水平":
            rows.extend(
                [
                    {
                        "title": "太医 vs 走方郎中",
                        "body": "御医随叫随到 vs 丫鬟只能后门请胡大夫开虎狼药——医疗资源极端垄断，是阶级矛盾的隐形导火索（推演）。",
                        "evidence": ["胡庸医诊晴雯", "王太医诊晴雯", "贾母参汤"],
                    },
                    {
                        "title": "人参泡沫与巫医蒙昧",
                        "body": "参茸温补轴高；第77回上参难求。马道婆、痘疹娘娘与脉案并置——进补金融化 + 半医学半神棍（推演）。",
                        "evidence": ["上等人参", "毛半仙占卦", "刘姥姥求神"],
                    },
                    {
                        "title": "死亡花名册：高夭折率",
                        "body": "贾珠、可卿、黛玉、晴雯皆青年暴卒；贾府尚如此，底层更残酷——还原古代人口周期（推演）。",
                        "evidence": ["黛玉绝粒", "秦可卿", "晴雯"],
                    },
                ]
            )
        elif label == "服饰精神面貌":
            rows.extend(
                [
                    {
                        "title": "洋货风潮与皮毛特权",
                        "body": "雀金呢、洋缎、貂狐猩毡——买办奢侈品+满族皮毛政治符号在温室冗余展示（推演）。",
                        "evidence": ["雀金裘", "软烟罗", "省亲礼服"],
                    },
                    {
                        "title": "舆服等级与奴才之衣",
                        "body": "律例限丝绸颜色；晴雯绫罗成罪、换小袄为反抗——衣服是阶级监狱之墙（推演）。",
                        "evidence": ["晴雯", "旧衣", "雀金裘"],
                    },
                    {
                        "title": "织造财政与抄家充公",
                        "body": "江宁织造、内务府料子连接南巡亏空；华服充公=经济泡沫破裂（推演）。",
                        "evidence": ["大红妆缎", "查抄"],
                    },
                ]
            )
        elif label == "民俗状态":
            rows.extend(
                [
                    {
                        "title": "节令倒计时：盛→毒→散→祭",
                        "body": "元宵极盛、端午争斗、中秋无月、除夕祭祖——四节循环如家族死亡倒计时（推演）。",
                        "evidence": ["元宵夜宴", "端午", "中秋", "宗祠祭祖"],
                    },
                    {
                        "title": "祭祖泡沫与巫术焦虑",
                        "body": "宗祠庄严与乌进孝账单并置；马道婆魇法、求神还愿——仪式维持等级，精神靠巫术自救（推演）。",
                        "evidence": ["魇魔法", "宗祠祭祖", "刘姥姥求神"],
                    },
                    {
                        "title": "底层民俗的续命力",
                        "body": "巧姐七夕名、刘姥姥取名还愿——上层失效后农家逻辑延续血脉（推演）。",
                        "evidence": ["巧姐托姥姥", "巧哥儿名"],
                    },
                ]
            )
        else:
            rows.append(
                {
                    "title": "贾府 vs 全社会",
                    "body": "以贾府为轴的贵族书写构成可见面主体；刘姥姥等线提供对照切片。",
                    "evidence": ["刘姥姥", "贾母"],
                }
            )
    elif book == "金瓶梅":
        rows.extend(
            [
                {
                    "title": "四步金融经与金融空心化",
                    "body": "婚姻兼并→三分利→产业矩阵→买官；白银未转实业而回流官僚洞（推演）。",
                    "evidence": ["药铺与放债链", "孟玉楼", "李瓶儿", "蔡京"],
                },
                {
                    "title": "空间政治学：高墙内外",
                    "body": "正房/西厢/新楼=后院地缘政治；扩园兼并 vs 武大郎式墙外矮民（推演）。",
                    "evidence": ["西门府建筑名录", "潘金莲", "吴月娘", "武大郎"],
                },
                {
                    "title": "胃囊社会学：特权与饥饿",
                    "body": "帮闲酒席喂养链；鲥鱼急递 vs 底层炊饼——资源虹吸式「吃人」（推演）。",
                    "evidence": ["应伯爵", "鲥鱼", "孙雪娥"],
                },
                {
                    "title": "司法商品化与信用归零",
                    "body": "武松案贿败、花子虚洗劫、理刑千户——律法变价目表（推演）。",
                    "evidence": ["武松", "花子虚", "提刑千户所"],
                },
            ]
        )
        rows.append(
            {
                "title": "西门府 vs 清河市井",
                "body": "晚明城市世情：西门府纵欲奢靡与县城市井帮闲礼俗并置，构成全书社会剖面。",
                "evidence": ["西门庆", "应伯爵", "帮闲凑分", "蔡府寿礼"],
            }
        )

    top_axis = max(global_axes.items(), key=lambda x: x[1]) if global_axes else ("", 0)
    if top_axis[1] > 0:
        lbl = (axis_labels or {}).get(top_axis[0], top_axis[0])
        rows.append(
            {
                "title": "主导轴",
                "body": f"聚合后「{lbl}」权重最高，可视为本书{label}的结构性偏向（inference）。",
                "evidence": [],
            }
        )
    return rows[:5]
