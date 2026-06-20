#!/usr/bin/env python3
"""全局膳食推演：dishes（含 diet_axes 手标）+ 回目 items[] + medicine + saga 里程碑。"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter
from _material_inference_common import build_social_block

DISHES_DIR = CONTENT / "dishes"
MEDICINES_DIR = CONTENT / "medicines"
EVENTS_DIR = CONTENT / "events"
CHAPTERS_DIR = CONTENT / "chapters"

AXES = [
    ("fine_tonic", "大补药膳", "燕窝、人参、露剂、胡僧药等"),
    ("fat_sweet", "肥甘甜烂", "糟味、奶酥、甜烂、禽脂"),
    ("refined_grain", "细米精面", "粳稻、红稻、细面（非粗粮）"),
    ("coarse_balance", "粗淡平衡", "小菜、消导、清淡粥汤"),
    ("feast_luxury", "宴享排场", "省亲、寿宴、茄鲞等"),
    ("alcohol", "酒茶", "绍兴酒、金华酒等"),
]
AXIS_IDS = [a[0] for a in AXES]

TEMPERATURE_BIAS: dict[str, dict[str, int]] = {
    "热": {"fat_sweet": 1},
    "温": {"fine_tonic": 1},
    "平": {},
    "凉": {"coarse_balance": 1},
    "寒": {"coarse_balance": 2},
}

KEYWORD_RULES: list[tuple[str, str, int]] = [
    ("fine_tonic", "燕窝", 3),
    ("fine_tonic", "人参", 3),
    ("fine_tonic", "参汤", 3),
    ("fine_tonic", "露", 2),
    ("fine_tonic", "茯苓", 2),
    ("fine_tonic", "药膳", 3),
    ("fine_tonic", "胡僧", 2),
    ("fine_tonic", "春药", 2),
    ("fat_sweet", "甜", 2),
    ("fat_sweet", "烂", 2),
    ("fat_sweet", "糟", 2),
    ("fat_sweet", "鹅", 2),
    ("fat_sweet", "鸭", 2),
    ("fat_sweet", "猪", 2),
    ("fat_sweet", "羊", 2),
    ("fat_sweet", "奶", 2),
    ("fat_sweet", "酥", 2),
    ("fat_sweet", "脂", 2),
    ("fat_sweet", "奶油", 3),
    ("refined_grain", "粳", 2),
    ("refined_grain", "稻", 2),
    ("refined_grain", "红稻", 2),
    ("refined_grain", "面", 1),
    ("refined_grain", "饽饽", 2),
    ("refined_grain", "鸽子蛋", 3),
    ("coarse_balance", "南小菜", 2),
    ("coarse_balance", "斋", 2),
    ("coarse_balance", "绿豆", 2),
    ("coarse_balance", "消导", 3),
    ("coarse_balance", "发散", 2),
    ("coarse_balance", "香薷", 2),
    ("coarse_balance", "梅汤", 2),
    ("feast_luxury", "宴", 2),
    ("feast_luxury", "席", 2),
    ("feast_luxury", "寿", 2),
    ("feast_luxury", "省亲", 3),
    ("feast_luxury", "螃蟹", 2),
    ("feast_luxury", "茄鲞", 3),
    ("feast_luxury", "八旬", 3),
    ("feast_luxury", "抄家", 2),
    ("alcohol", "酒", 2),
    ("alcohol", "茶", 1),
]

CATEGORY_BIAS: dict[str, dict[str, int]] = {
    "药膳": {"fine_tonic": 3},
    "露剂": {"fine_tonic": 2, "fat_sweet": 1},
    "饭": {"refined_grain": 2},
    "粥": {"coarse_balance": 1, "refined_grain": 1},
    "寿宴": {"feast_luxury": 3, "fat_sweet": 1},
    "大礼宴": {"feast_luxury": 3},
    "宴席": {"feast_luxury": 2},
    "闲食": {"fat_sweet": 2},
    "腌味": {"fat_sweet": 2},
    "糟味": {"fat_sweet": 2},
    "主菜": {"fat_sweet": 2},
    "膳食偏好": {"fat_sweet": 2},
    "丧仪供食": {"feast_luxury": 1, "coarse_balance": 1},
}

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
        "focus": [
            "贾母", "贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "秦可卿",
            "史湘云", "贾元春", "刘姥姥", "晴雯", "香菱", "尤二姐",
        ],
        "character_notes": {
            "贾母": "甜烂之食、牛乳蒸羊羔、糟鸭信；茄鲞鸽蛋宴后「闹肚子」（刘姥姥线）。推演：老年高脂高胆+不规律，与屡次暴病互参（inference）。",
            "林黛玉": "长期少食，第45回自认「连燕窝粥也吃不惯」；饭后即茶（第3回随贾府习惯）。推演：低热量+单宁阻铁吸收，精补不能代高蛋白，与「郁气伤肝」并读（inference）。",
            "薛宝钗": "邢岫烟言其嗜甜食（第11回）；螃蟹宴极爱此物；「热毒」赖冷香丸。推演：丰腴+高糖高热，或过敏性哮喘/代谢内热（inference）。",
            "贾宝玉": "糖蒸酥酪、豆腐皮包子、火腿鲜笋；病中「净饿」只喝清米汤。推演：精制碳水+饮食剧烈波动伤脾胃（inference）。",
            "王熙凤": "「刚吃了一口，又有人来回话」；小产后饮食不节→崩漏。推演：高压+饱饥无常致内分泌/溃疡风险（inference）。",
            "刘姥姥": "两宴见精工（茄鲞、鸽蛋），日常粗淡；与主子层饮食不可比，是全社会对照切片。",
            "秦可卿": "张友士「水亏木旺」；贾府肥甘环境为背景。",
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
        "focus": ["西门庆", "潘金莲", "李瓶儿", "孟玉楼", "庞春梅", "吴月娘", "应伯爵", "陈经济", "武松", "孙雪娥"],
        "character_notes": {
            "西门庆": "四步金融经：婚姻兼并→三分利→产业矩阵→买官理刑千户；资本宿主纵欲+胡僧药透支，死后帮闲/韩道国清算（推演）。",
            "李瓶儿": "太监遗产=资本三级跳；新盖三层楼=特权空间亦成母子坟墓（推演）。",
            "孟玉楼": "改嫁携数千两+货，婚姻作资产重组工具（推演）。",
            "潘金莲": "西厢边缘空间→偷听争位；分不到核心席面，酸梅汤/酸辣对抗瓶儿蹄子（空间+胃囊 inference）。",
            "吴月娘": "正房上房=宗法合法性神坛；暴卒危机时秩序锚点（空间 inference）。",
            "孙雪娥": "锁死厨房=最卑微食物制造者；西门庆死后卖厨娘上吊（胃囊阶级 inference）。",
            "应伯爵": "帮闲胃囊寄生；死即投张二官收铺娶李娇儿——喂养反噬（推演）。",
            "陈经济": "西门庆死后二门失守，管账穿梭后院；争产诉讼反被衙役敲诈（空间+司法 inference）。",
            "武松": "知县受贿驳回→血溅狮子楼；司法商品化逼出私刑（推演）。",
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


def merge_scores(base: dict[str, int], manual: dict | None, temperature: str | None) -> dict[str, int]:
    scores = dict(base)
    if manual:
        for axis, w in manual.items():
            if axis in AXIS_IDS and w is not None:
                scores[axis] = int(w)
    if temperature:
        for axis, w in TEMPERATURE_BIAS.get(str(temperature), {}).items():
            scores[axis] += w
    return scores


def score_from_blob(blob: str, category: str = "") -> dict[str, int]:
    scores = {a: 0 for a in AXIS_IDS}
    for axis, kw, w in KEYWORD_RULES:
        if kw in blob:
            scores[axis] += w
    for prefix, bias in CATEGORY_BIAS.items():
        if prefix in category:
            for axis, w in bias.items():
                scores[axis] += w
    return scores


def luxury_index(scores: dict[str, int]) -> int:
    heavy = scores["feast_luxury"] * 8 + scores["refined_grain"] * 4 + scores["fat_sweet"] * 3
    heavy += scores["fine_tonic"] * 5 + scores["alcohol"] * 2
    light = scores["coarse_balance"] * 4
    return max(0, min(100, 20 + heavy * 3 - light * 2))


def balance_score(scores: dict[str, int]) -> float:
    plus = scores["coarse_balance"] * 1.2
    minus = (
        scores["fine_tonic"] * 1.0
        + scores["fat_sweet"] * 1.1
        + scores["refined_grain"] * 0.8
        + scores["feast_luxury"] * 0.6
    )
    return round(plus - minus, 2)


def normalize_eaters(raw: list | str | None) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    out: list[str] = []
    for e in raw:
        name = re.sub(r"等$", "", str(e).strip())
        if name and name not in out:
            out.append(name)
    return out


def load_food_index(book: str) -> dict[str, dict]:
    path = DATA_DIR / f"{book}.food.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {r["id"]: r for r in data.get("dishes") or []}


def ensure_jinpingmei_food_json() -> None:
    book = "金瓶梅"
    out = DATA_DIR / "jinpingmei.food.json"
    dishes = []
    for p in sorted((DISHES_DIR / book).glob("*.md")):
        fm, _ = parse_frontmatter(p)
        ch = chapter_num(fm.get("first_appear"))
        dishes.append(
            {
                "id": fm["id"],
                "name": fm.get("name", fm["id"]),
                "type": fm.get("type", "dish"),
                "chapter": ch,
                "eaters": fm.get("eaters") or [],
                "literary_function": fm.get("summary", ""),
            }
        )
    payload = {"book": book, "generated_by": "build_diet_inference.py", "dishes": dishes}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dish_record_from_fm(fm: dict, food_row: dict | None, source: str = "entity") -> dict:
    chs: set[int] = set()
    c0 = chapter_num(fm.get("first_appear"))
    if c0:
        chs.add(c0)
    for ap in fm.get("appear_in") or []:
        c = chapter_num(ap)
        if c:
            chs.add(c)
    if food_row and food_row.get("chapter"):
        chs.add(int(food_row["chapter"]))

    blob = " ".join(str(fm.get(k, "") or "") for k in ("name", "category", "summary", "occasion", "process"))
    if food_row:
        blob += " " + str(food_row.get("literary_function", "")) + str(food_row.get("cost_signal", ""))

    base = score_from_blob(blob, str(fm.get("category") or ""))
    if food_row and food_row.get("cost_signal"):
        base["feast_luxury"] += 2

    manual = fm.get("diet_axes")
    scores = merge_scores(base, manual, fm.get("temperature"))
    return {
        "id": fm["id"],
        "name": fm.get("name", fm["id"]),
        "category": fm.get("category", ""),
        "chapters": sorted(chs),
        "eaters": normalize_eaters(fm.get("eaters") or (food_row or {}).get("eaters")),
        "scores": scores,
        "luxury": luxury_index(scores),
        "balance": balance_score(scores),
        "source": source,
        "temperature": fm.get("temperature"),
        "has_manual_axes": bool(manual),
    }


def load_dish_catalog(book: str) -> dict[str, dict]:
    d = DISHES_DIR / book
    if not d.is_dir():
        return {}
    food_idx = load_food_index(book)
    catalog: dict[str, dict] = {}
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != book:
            continue
        if fm.get("type") not in ("dish", "banquet", "tea", "wine", "ingredient"):
            continue
        catalog[fm["id"]] = dish_record_from_fm(fm, food_idx.get(fm["id"]))
    return catalog


def load_medicine_catalog(book: str) -> dict[str, dict]:
    d = MEDICINES_DIR / book
    if not d.is_dir():
        return {}
    catalog: dict[str, dict] = {}
    for p in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != book:
            continue
        chs: set[int] = set()
        c0 = chapter_num(fm.get("first_appear"))
        if c0:
            chs.add(c0)
        for ap in fm.get("appear_in") or []:
            c = chapter_num(ap)
            if c:
                chs.add(c)
        blob = " ".join(str(fm.get(k, "") or "") for k in ("name", "summary", "category"))
        base = score_from_blob(blob, str(fm.get("category") or ""))
        if "砒霜" in fm.get("id", "") or "砒霜" in blob:
            base = {a: 0 for a in AXIS_IDS}
        else:
            base["fine_tonic"] = max(base["fine_tonic"], 2)
        manual = fm.get("diet_axes")
        scores = merge_scores(base, manual, fm.get("temperature"))
        catalog[fm["id"]] = {
            "id": fm["id"],
            "name": fm.get("name", fm["id"]),
            "category": fm.get("category", ""),
            "chapters": sorted(chs),
            "eaters": normalize_eaters(fm.get("patients") or fm.get("eaters")),
            "scores": scores,
            "luxury": luxury_index(scores),
            "balance": balance_score(scores),
            "source": "medicine",
            "temperature": fm.get("temperature"),
            "has_manual_axes": bool(manual),
        }
    return catalog


def load_chapter_item_refs(book: str, catalog: dict[str, dict]) -> list[tuple[int, str, str]]:
    """(chapter, item_id, source) — 回目 items[] 补链。"""
    refs: list[tuple[int, str, str]] = []
    book_dir = CHAPTERS_DIR / book
    if not book_dir.is_dir():
        return refs

    seen: set[tuple[int, str]] = set()
    paths: list[Path] = list(book_dir.glob("*.md"))
    sub = book_dir / "脂砚斋本"
    if sub.is_dir():
        paths.extend(sub.glob("*.md"))

    for p in paths:
        fm, _ = parse_frontmatter(p)
        if fm.get("book") != book:
            continue
        ch = fm.get("number") or chapter_num(fm.get("first_appear"))
        if not ch:
            continue
        ch = int(ch)
        for item in fm.get("items") or []:
            iid = str(item).strip()
            if not iid or (ch, iid) in seen:
                continue
            seen.add((ch, iid))
            refs.append((ch, iid, "chapter_item"))

    return refs


def expand_occurrences(catalog: dict[str, dict], chapter_refs: list[tuple[int, str, str]]) -> list[dict]:
    rows: list[dict] = []
    for rec in catalog.values():
        for ch in rec.get("chapters") or []:
            rows.append({**rec, "chapter": ch})

    for ch, iid, src in chapter_refs:
        if any(r["id"] == iid and r["chapter"] == ch for r in rows):
            continue
        if iid in catalog:
            rec = catalog[iid]
            rows.append({**rec, "chapter": ch, "source": "chapter_item"})
            continue
        base = score_from_blob(iid, "")
        scores = merge_scores(base, None, None)
        rows.append(
            {
                "id": iid,
                "name": iid,
                "category": "",
                "chapter": ch,
                "eaters": [],
                "scores": scores,
                "luxury": luxury_index(scores),
                "balance": balance_score(scores),
                "source": "chapter_item",
                "temperature": None,
                "has_manual_axes": False,
            }
        )
    return [r for r in rows if r.get("chapter")]


def load_medicine_echo(book: str) -> dict[str, list[str]]:
    path = DATA_DIR / f"{book}.medicine.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = defaultdict(list)
    for p in data.get("prescriptions") or []:
        for patient in p.get("patients") or []:
            note = p.get("diagnosis") or p.get("note") or p.get("name", "")
            ch = p.get("chapter") or p.get("first_appear") or ""
            out[patient].append(f"{p.get('name', p.get('id', ''))}（{ch} {note}）".strip())
    for ph in data.get("physicians") or []:
        for patient in ph.get("patients") or []:
            if ph.get("diagnosis"):
                out[patient].append(f"{ph['name']}：{ph['diagnosis']}")
    for p in data.get("prescriptions") or []:
        pass
    # 金瓶梅 medicine 实体页
    for rec in load_medicine_catalog(book).values():
        for eater in rec.get("eaters") or []:
            out[eater].append(f"{rec['name']}（饮食/药线索）")
    return dict(out)


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


def build_book(book: str) -> dict | None:
    cfg = BOOK_CONFIG.get(book)
    if not cfg:
        return None
    slug = cfg["slug"]
    chapter_count = cfg["chapters"]
    phases = cfg["phases"]

    if book == "金瓶梅":
        ensure_jinpingmei_food_json()

    catalog: dict[str, dict] = {}
    catalog.update(load_dish_catalog(book))
    catalog.update(load_medicine_catalog(book))
    chapter_refs = load_chapter_item_refs(book, catalog)
    dishes = expand_occurrences(catalog, chapter_refs)

    def phase_for(ch: int) -> str:
        for label, lo, hi in phases:
            if lo <= ch <= hi:
                return label
        return "其他"

    by_ch: dict[int, list[dict]] = defaultdict(list)
    for d in dishes:
        by_ch[int(d["chapter"])].append(d)

    chapter_rows = []
    for ch in range(1, chapter_count + 1):
        ds = by_ch.get(ch, [])
        agg = {a: 0 for a in AXIS_IDS}
        for d in ds:
            for a in AXIS_IDS:
                agg[a] += d["scores"][a]
        lux = round(sum(d["luxury"] for d in ds) / len(ds), 1) if ds else 0
        bal = round(sum(d["balance"] for d in ds) / len(ds), 2) if ds else 0
        sources = list({d.get("source", "entity") for d in ds})
        chapter_rows.append(
            {
                "chapter": ch,
                "dish_count": len(ds),
                "luxury": lux,
                "balance": bal,
                "axes": agg,
                "phase": phase_for(ch),
                "dishes": [x["id"] for x in ds],
                "sources": sources,
            }
        )

    for i, row in enumerate(chapter_rows):
        window = chapter_rows[max(0, i - 2) : min(chapter_count, i + 3)]
        active = [w for w in window if w["dish_count"] > 0]
        if active:
            row["luxury_smooth"] = round(sum(w["luxury"] for w in active) / len(active), 1)
            row["balance_smooth"] = round(sum(w["balance"] for w in active) / len(active), 2)
        else:
            row["luxury_smooth"] = chapter_rows[i - 1]["luxury_smooth"] if i else 0
            row["balance_smooth"] = chapter_rows[i - 1]["balance_smooth"] if i else 0

    char_axes: dict[str, dict[str, int]] = defaultdict(lambda: {a: 0 for a in AXIS_IDS})
    char_dishes: dict[str, list[str]] = defaultdict(list)
    for d in dishes:
        for eater in d["eaters"]:
            for a in AXIS_IDS:
                char_axes[eater][a] += d["scores"][a]
            if d["id"] not in char_dishes[eater]:
                char_dishes[eater].append(d["id"])

    med_echo = load_medicine_echo(book)
    notes = cfg.get("character_notes") or {}
    char_rows = []
    for cid in cfg["focus"]:
        ax = char_axes.get(cid, {a: 0 for a in AXIS_IDS})
        if sum(ax.values()) == 0 and cid not in med_echo:
            continue
        bal = balance_score(ax)
        risks: list[str] = []
        if ax["fine_tonic"] >= 4 and ax["coarse_balance"] <= 2:
            risks.append("长期偏温补药膳，粗淡杂粮不足")
        if ax["fat_sweet"] >= 5 and ax["coarse_balance"] <= 3:
            risks.append("肥甘甜烂偏多，易滞中助湿（推演）")
        if ax["refined_grain"] >= 4 and ax["coarse_balance"] <= 2:
            risks.append("精米细面为主，缺粗粮平衡")
        if ax["feast_luxury"] >= 6:
            risks.append("宴享排场密集，饮食失时风险")
        if ax["alcohol"] >= 4:
            risks.append("酒肉频繁")

        parts: list[str] = []
        if risks:
            parts.append("；".join(risks) + "。")
        else:
            parts.append("饮食轴相对均衡，或文本着墨较少。")
        if cid in notes:
            parts.append(notes[cid])
        if med_echo.get(cid):
            parts.append("医药互证：" + "；".join(med_echo[cid][:2]))

        char_rows.append(
            {
                "id": cid,
                "name": cid,
                "dish_count": len(char_dishes.get(cid, [])),
                "axes": ax,
                "balance_score": bal,
                "risk_tags": risks,
                "inference": "".join(parts),
                "medicine_echo": med_echo.get(cid, [])[:4],
                "sample_dishes": char_dishes.get(cid, [])[:8],
            }
        )
    char_rows.sort(key=lambda x: x["balance_score"])

    saga = load_saga_milestones(book, slug)
    peak = max(chapter_rows, key=lambda r: r["luxury_smooth"])
    manual_count = sum(1 for r in catalog.values() if r.get("has_manual_axes"))
    social = build_social_block(book, dishes, AXIS_IDS, "eaters", "饮食水平")

    return {
        "book": book,
        "slug": slug,
        "generated_by": "build_diet_inference.py",
        "inference_note": "推演层：dish 手标 diet_axes + 回目 items[] + medicine + saga 互参；非医学诊断。",
        "axes": [{"id": a, "label": b, "desc": c} for a, b, c in AXES],
        "phases": [{"label": l, "from": lo, "to": hi} for l, lo, hi in phases],
        "saga_milestones": saga,
        "by_chapter": chapter_rows,
        "characters": char_rows,
        "global_insights": build_global_insights(book, chapter_rows, char_rows, dishes, social),
        "social": social,
        "stats": {
            "dish_entities": len(catalog),
            "occurrence_rows": len(dishes),
            "manual_axis_entities": manual_count,
            "chapter_item_refs": len(chapter_refs),
            "chapters_with_food": sum(1 for r in chapter_rows if r["dish_count"] > 0),
            "peak_luxury_chapter": peak["chapter"],
            "peak_luxury": peak["luxury_smooth"],
            "saga_milestones": len(saga),
            "social_segments": len(social["segments"]),
        },
    }


def build_global_insights(book: str, chapters: list, chars: list, dishes: list, social: dict | None = None) -> list[dict]:
    total_axes = {a: 0 for a in AXIS_IDS}
    for d in dishes:
        for a in AXIS_IDS:
            total_axes[a] += d["scores"][a]

    ch_item_count = sum(1 for d in dishes if d.get("source") == "chapter_item")
    insights = [
        {
            "title": "精细有余、粗粮平衡不足",
            "body": "聚合轴上细米精面+肥甘+大补显著高于粗淡项；绿畦香稻/红稻粥手标为精米非杂粮。",
            "evidence": ["茄鲞", "鸽子蛋", "燕窝粥", "甜烂之食", "绿畦香稻饭"] if book == "红楼梦" else ["烧鹅", "金华酒", "酥酥", "寿面"],
        },
        {
            "title": "奢侈曲线与大事记同向",
            "body": "rolling 奢侈度与 saga 里程碑（省亲/园宴/查抄/散府）可对照；曲线峰谷不等于因果。",
            "evidence": [m["title"] for m in load_saga_milestones(book, BOOK_CONFIG[book]["slug"])[:4]],
        },
        {
            "title": "健康推演：补而不衡",
            "body": "焦点人物普遍「大补/精细 ≥ 粗淡」；脉案作互证，非医学定论。",
            "evidence": [c["id"] for c in chars if c["balance_score"] < -2][:5],
        },
    ]
    if ch_item_count:
        insights.append(
            {
                "title": "回目 items[] 补链",
                "body": f"另有 {ch_item_count} 条由回目 frontmatter items[] 补入曲线（无独立 dish 页者按名关键词估轴）。",
                "evidence": [],
            }
        )
    insights[0]["axis_ratio"] = {
        "heavy": total_axes["fine_tonic"] + total_axes["fat_sweet"] + total_axes["refined_grain"],
        "light": total_axes["coarse_balance"],
    }
    if social and social.get("inference"):
        insights.insert(
            1,
            {
                "title": social.get("title", "全社会饮食水平"),
                "body": social["inference"],
                "evidence": [s["label"] for s in social.get("segments", [])[:3]],
            },
        )
    if book == "红楼梦":
        insights.extend(
            [
                {
                    "title": "茄鲞：炫耀性消费与阶级壁垒",
                    "body": "十几只鸡配一茄，烹饪冗余把底层生存物资转化为身份游戏；刘姥姥「倒得十来只鸡」点破阶层绝对隔离（社会学推演）。",
                    "evidence": ["茄鲞", "刘姥姥", "王熙凤"],
                },
                {
                    "title": "乌进孝进贡：生态红线与财政枯竭",
                    "body": "第53回野味清单与「地都冻了」「年成一年不如一年」并读——人口压力、生态萎缩与小农供养断绝，上层餐桌失去底层现金流（经济史推演）。",
                    "evidence": ["乌进孝", "第53回", "祭宗祠"],
                },
                {
                    "title": "从极奢到寒酸：帝国气压计",
                    "body": "前部夜宴绍兴酒、反季鲜果；抄家后粥不可得。饮食曲线峰谷映射阶层雪崩，非仅贾府私事（全社会推演）。",
                    "evidence": ["群芳夜宴", "查抄", "刘姥姥"],
                },
            ]
        )
    elif book == "金瓶梅":
        insights.extend(build_jinpingmei_diet_insights())
    return insights


def build_jinpingmei_diet_insights() -> list[dict]:
    """金瓶梅：胃囊社会学 + 帮闲食物链（inference）。"""
    return [
        {
            "title": "胃囊社会学：油腻与吞噬",
            "body": "全书二百多种肴馔，人物不在床就在席；相对红楼意境饮食，金书写纯胃口与阶级剥削（推演）。",
            "evidence": ["烧鹅", "金华酒", "酥酥"],
        },
        {
            "title": "厨房阶级：孙雪娥",
            "body": "掌全家灶火却是最卑微「高级厨工」；油烟失性、死后卖厨娘——困死灶台（推演）。",
            "evidence": ["孙雪娥", "厨房"],
        },
        {
            "title": "蹄子 vs 酸梅：受宠显影",
            "body": "瓶儿炖蹄子烧鸭=核心权力；金莲酸梅汤/酸辣=分不到核心席面的饥渴外化（推演）。",
            "evidence": ["李瓶儿", "潘金莲", "炖蹄子"],
        },
        {
            "title": "应伯爵：喂养与反噬",
            "body": "帮闲靠酒席换吹捧情报；西门庆死即投张二官收铺说媒李娇儿——寄生虫只爱残渣（推演）。",
            "evidence": ["应伯爵", "西门庆", "张二官", "李娇儿"],
        },
        {
            "title": "鲥鱼：物流暴政",
            "body": "第34回江南鲜鲥鱼抵清河需急递漕运；一口鱼肉成本=纤夫性命（经济—社会 inference）。",
            "evidence": ["鲥鱼", "第34回", "大运河"],
        },
        {
            "title": "特权胃囊与饥饿黑洞",
            "body": "墙内葡萄酒乳猪 vs 墙外武大郎炊饼；生产力塞满权贵胃、底层缺粥——系统溃疡（推演）。",
            "evidence": ["武大郎", "葡萄酒", "清河"],
        },
        {
            "title": "富贵病：精尽与高脂",
            "body": "常年高脂高酒+胡僧药=血管寿命崩漏；床榻秽物=统治阶层消化不了不公的镜像（医学 inference）。",
            "evidence": ["西门庆", "胡僧药"],
        },
        {
            "title": "与红楼对照：意境 vs 胃口",
            "body": "红楼茄鲞=审美标尺；金瓶=资本与肉欲消耗直写（跨书 inference）。",
            "evidence": ["世情与贵族衰败对比", "茄鲞", "烧鹅"],
        },
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book", nargs="?", default="红楼梦")
    ap.add_argument("--all", action="store_true", help="重建全部 supported 书")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    targets = list(BOOK_CONFIG.keys()) if args.all else [args.book]
    for book in targets:
        payload = build_book(book)
        if not payload:
            print(f"skip: {book}")
            continue
        slug = payload["slug"]
        out = DATA_DIR / f"{slug}.diet-inference.json"
        if args.write:
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            s = payload["stats"]
            print(
                f"  {slug}: {s['occurrence_rows']} occ · {s['chapters_with_food']} ch · "
                f"manual {s['manual_axis_entities']} · items+ {s['chapter_item_refs']} · saga {s['saga_milestones']}"
            )
            print(f"written → {out.name}")
        else:
            print(json.dumps(payload["stats"], ensure_ascii=False))


if __name__ == "__main__":
    main()
