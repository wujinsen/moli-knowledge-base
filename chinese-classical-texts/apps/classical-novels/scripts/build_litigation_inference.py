#!/usr/bin/env python3
"""生成 jinpingmei.litigation-inference.json — 司法诉讼推演（inference 层）。"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import date
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
CHAPTER_COUNT = 100

TIERS = [
    {"id": "county", "label": "基层", "desc": "县衙·仵作·贿败"},
    {"id": "cross_region", "label": "跨区", "desc": "东京开封府·房族争产"},
    {"id": "capital", "label": "国家级", "desc": "巡按·蔡府·提刑千户"},
]

PHASES = [
    {"label": "武大命案前史", "from": 1, "to": 10},
    {"label": "西门得官·花案", "from": 11, "to": 39},
    {"label": "苗案·提刑巅峰", "from": 40, "to": 51},
    {"label": "庇护真空·后二十回", "from": 52, "to": 100},
]

# 手标 bribery（无 transaction 时保留）+ 案件匹配规则
CASES_TEMPLATE = [
    {
        "id": "jpm-lit-wusong",
        "tier": "county",
        "title": "武松告武大郎案",
        "chapters": [5, 6, 8, 9, 10, 87],
        "anchor_chapter": 10,
        "parties": {
            "plaintiff": ["武松"],
            "defendant": ["潘金莲", "西门庆", "王婆"],
            "officials": ["何九", "钱劳", "陈文昭", "李拱极"],
        },
        "locations": ["县衙", "狮子街", "东平府"],
        "manual_bribery": [
            {"chapter": 6, "amount_liang": 10, "party": "何九", "note": "瞒验尸"},
            {"chapter": 10, "amount_liang": 50, "party": "知县", "note": "金银酒器+吏典"},
        ],
        "tx_match": {
            "chapters": {5, 6, 8, 9, 10, 87},
            "keywords": ["武松", "知县", "何九", "县衙", "告状"],
            "subtypes": ["贿赂"],
            "tx_ids": [],
        },
        "outcome": "县衙刑讯诬告；府尹改判刺配；87回私刑祭兄",
        "inference": "体制内维权流产→血溅式私刑（推演）",
        "evidence": ["武松", "何九", "陈文昭", "第10回"],
        "links": {
            "saga": "jpm-rt-003",
            "chain_focus": "jpm-rt-003",
            "topic": "世情四横切面与社会推演",
        },
    },
    {
        "id": "jpm-lit-huazixu",
        "tier": "cross_region",
        "title": "花子虚房族争产",
        "chapters": [13, 14, 19],
        "anchor_chapter": 14,
        "parties": {
            "plaintiff": ["花子由", "花子光", "花子华"],
            "defendant": ["花子虚"],
            "beneficiary": ["西门庆", "李瓶儿"],
        },
        "locations": ["花家", "东京", "西门府"],
        "manual_bribery": [
            {"chapter": 14, "amount_liang": 3000, "party": "蔡京/杨提督", "note": "李瓶儿出银走分上（词话本 inference）"},
        ],
        "tx_match": {
            "chapters": {13, 14, 16, 17, 18, 19},
            "keywords": ["花子虚", "李瓶儿", "争产", "蔡", "杨"],
            "subtypes": ["贿赂"],
            "tx_ids": ["jpm-tx-011", "jpm-tx-021"],
        },
        "outcome": "子虚气死；财产经西门府洗入；李瓶儿改嫁",
        "inference": "诉讼=资产合法洗劫（推演）",
        "evidence": ["花子虚", "李瓶儿", "蔡京", "第14回"],
        "links": {
            "saga": "jpm-ms-002",
            "chain_focus": "jpm-ms-002",
            "chain_financial": "jpm-fe-005",
            "silver_tx": ["jpm-tx-021"],
            "topic": "世情四横切面与社会推演",
        },
    },
    {
        "id": "jpm-lit-tixing",
        "tier": "capital",
        "title": "提刑千户授官",
        "chapters": [30, 39],
        "anchor_chapter": 39,
        "parties": {
            "beneficiary": ["西门庆"],
            "patron": ["蔡京", "翟管家"],
        },
        "locations": ["提刑千户所", "东京", "蔡府"],
        "manual_bribery": [],
        "tx_match": {
            "chapters": {23, 27, 30, 39, 55, 75},
            "keywords": ["蔡", "翟", "提刑", "寿礼", "干亲"],
            "subtypes": ["贿赂"],
            "tx_ids": ["jpm-tx-003", "jpm-tx-018", "jpm-tx-022"],
        },
        "outcome": "理刑副千户→提刑千户；司法从买通到执掌",
        "inference": "资本终极增殖=政治庇护（推演）",
        "evidence": ["提刑千户所", "jpm-pe-001", "第39回"],
        "links": {
            "saga": "jpm-pe-001",
            "chain_focus": "jpm-pe-001",
            "chain_financial": "jpm-fe-007",
            "silver_tx": ["jpm-tx-003", "jpm-tx-018"],
            "topic": "世情四横切面与社会推演",
        },
    },
    {
        "id": "jpm-lit-miaotianxiu",
        "tier": "capital",
        "title": "苗员外命案",
        "chapters": [47, 48, 49, 51],
        "anchor_chapter": 48,
        "parties": {
            "victim": ["苗天秀"],
            "accused": ["苗青", "陈三", "翁八"],
            "officials": ["夏提刑", "西门庆", "曾孝序", "蔡御史"],
        },
        "locations": ["提刑千户所", "城西河边", "东昌府", "徐州洪"],
        "manual_bribery": [
            {"chapter": 48, "amount_liang": 500, "party": "西门庆", "note": "词话本枉法（无单独 transaction）"},
            {"chapter": 48, "amount_liang": 500, "party": "夏提刑", "note": "词话本枉法（无单独 transaction）"},
        ],
        "tx_match": {
            "chapters": {47, 48, 49, 51},
            "keywords": ["苗", "提刑", "买办", "夏提刑"],
            "subtypes": ["贿赂", "经营投资"],
            "tx_ids": ["jpm-tx-023"],
        },
        "outcome": "只斩船家；除苗青名；曾孝序参劾被蔡御史压下",
        "inference": "国家级枉法+巡按压案=律法商品化巅峰（推演）",
        "evidence": ["苗天秀", "苗青", "安童", "第48回"],
        "links": {
            "chain_focus": "jpm-fe-013",
            "silver_tx": ["jpm-tx-023"],
            "topic": "扬州经商线",
            "silver": True,
        },
    },
    {
        "id": "jpm-lit-chenjingji",
        "tier": "county",
        "title": "陈经济争产反被敲诈",
        "chapters": [92, 98],
        "anchor_chapter": 98,
        "parties": {
            "plaintiff": ["陈经济"],
            "officials": ["衙役"],
        },
        "locations": ["县衙", "提刑千户所"],
        "manual_bribery": [],
        "tx_match": {
            "chapters": {92, 98},
            "keywords": ["陈经济", "争产", "官司"],
            "subtypes": ["贿赂"],
            "tx_ids": [],
        },
        "outcome": "西门庆死后争产诉讼反被夹打敲诈",
        "inference": "司法特权随宿主消亡→后代成绞肉机新饲料（推演）",
        "evidence": ["陈经济", "后二十回散场人物"],
        "links": {"topic": "世情四横切面与社会推演"},
    },
]

CHAPTER_CORRUPTION: dict[int, int] = {
    5: 35,
    6: 55,
    8: 40,
    9: 45,
    10: 88,
    13: 50,
    14: 78,
    19: 45,
    30: 62,
    39: 72,
    47: 70,
    48: 96,
    49: 80,
    51: 65,
    58: 55,
    87: 82,
    92: 60,
    98: 68,
}

OFFICIALS = [
    {
        "id": "夏提刑",
        "role": "提刑正千户",
        "cases": ["jpm-lit-miaotianxiu"],
        "inference": "与西门庆各五百两合伙枉法（推演）",
    },
    {
        "id": "西门庆",
        "role": "理刑千户 / 司法操盘手",
        "cases": ["jpm-lit-wusong", "jpm-lit-huazixu", "jpm-lit-miaotianxiu", "jpm-lit-tixing"],
        "inference": "「太师府认得我字迹」— 从买通到执掌（推演）",
    },
    {
        "id": "武松",
        "role": "维权失败者→私刑者",
        "cases": ["jpm-lit-wusong"],
        "inference": "告状无门→血溅狮子楼（推演）",
    },
    {
        "id": "曾孝序",
        "role": "巡按参劾",
        "cases": ["jpm-lit-miaotianxiu"],
        "inference": "体制内清流无力对抗蔡党（推演）",
    },
    {
        "id": "陈经济",
        "role": "争产者",
        "cases": ["jpm-lit-chenjingji"],
        "inference": "失去西门庆庇护后反被司法敲诈（推演）",
    },
]

GLOBAL_INSIGHTS = [
    {
        "title": "三级司法通关",
        "body": "武松案基层贿败→花子虚跨区洗劫→苗案+提刑千户国家级枉法；详见 topics/世情四横切面与社会推演（推演）。",
        "evidence": ["武松", "花子虚", "苗天秀", "提刑千户所"],
    },
    {
        "title": "律法商品化",
        "body": "两千两改人命、五百两买官；当大理寺管不着我银子，民间国家信用归零（政治 inference）。",
        "evidence": ["蔡京", "西门庆", "县衙"],
    },
    {
        "title": "保护伞真空",
        "body": "西门庆死后提刑同僚翻脸；陈经济争产反被夹打——特权建在人身上非制度（推演）。",
        "evidence": ["陈经济", "后二十回散场人物"],
    },
    {
        "title": "与白银流/衰败链互证",
        "body": "诉讼 bribery 自动抽取自 transactions/；chain ?focus= 深链 saga 里程碑与 financial_event。",
        "evidence": ["药铺与放债链", "jpm-tx-023", "jpm-pe-001"],
    },
]

SOCIAL = {
    "title": "三级司法通关 · 全社会",
    "inference": "基层贿败→跨区洗劫→国家级买官；当司法成商品交易所，统治合法性在底层归零（推演）。",
    "insights": [
        {
            "title": "基层：有理无钱莫进来",
            "body": "县衙大门朝东开；武松人证物证仍被轰出——和平维权通道堵死（推演）。",
            "evidence": ["武松", "县衙", "何九"],
        },
        {
            "title": "跨区：诉讼洗劫资产",
            "body": "花子虚争产案=豪强借司法兼并寡妇财产；气死即完成收购（推演）。",
            "evidence": ["花子虚", "李瓶儿", "西门庆"],
        },
        {
            "title": "国家级：买法→掌法",
            "body": "苗案枉法+蔡御史压巡按参；西门庆从法外狂徒异化为法官（推演）。",
            "evidence": ["苗青", "夏提刑", "蔡京"],
        },
    ],
}


def load_transactions(book: str) -> list[dict]:
    d = CONTENT / "transactions" / book
    if not d.is_dir():
        return []
    rows: list[dict] = []
    for path in sorted(d.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        if fm.get("book") != book:
            continue
        rows.append(
            {
                "id": fm["id"],
                "chapter": int(fm.get("chapter") or 0),
                "subtype": fm.get("subtype", ""),
                "amount_liang": fm.get("amount_normalized"),
                "buyer": fm.get("buyer", ""),
                "payee": fm.get("payee", ""),
                "seller": fm.get("seller", ""),
                "summary": fm.get("summary", ""),
                "tags": fm.get("tags") or [],
                "source": fm.get("source", ""),
            }
        )
    return rows


def load_chain_event_ids() -> set[str]:
    path = DATA_DIR / "jinpingmei.chain.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {e["id"] for e in data.get("events", [])}


def _blob(tx: dict) -> str:
    return " ".join(
        [
            tx.get("summary") or "",
            tx.get("buyer") or "",
            tx.get("payee") or "",
            tx.get("seller") or "",
            " ".join(tx.get("tags") or []),
        ]
    )


def tx_matches_case(tx: dict, rules: dict) -> bool:
    if tx["id"] in rules.get("tx_ids") or []:
        return True
    ch = tx["chapter"]
    if ch not in rules.get("chapters", set()):
        return False
    if tx["subtype"] not in rules.get("subtypes", ["贿赂"]):
        return False
    blob = _blob(tx)
    keywords = rules.get("keywords") or []
    if keywords and not any(k in blob for k in keywords):
        return False
    return True


def bribery_from_tx(tx: dict) -> dict:
    party = tx.get("payee") or tx.get("seller") or tx.get("buyer") or "—"
    note = tx.get("summary") or tx.get("subtype")
    return {
        "chapter": tx["chapter"],
        "amount_liang": tx.get("amount_liang"),
        "party": party,
        "note": note,
        "tx_ref": tx["id"],
        "source": "transaction",
        "subtype": tx.get("subtype"),
    }


def merge_bribery(manual: list[dict], auto: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen_tx: set[str] = set()
    seen_manual: set[tuple] = set()

    for row in manual:
        key = (row["chapter"], row.get("party", ""), row.get("amount_liang"))
        if key in seen_manual:
            continue
        seen_manual.add(key)
        out.append({**row, "source": "manual"})

    for row in auto:
        tx_ref = row.get("tx_ref")
        if tx_ref:
            if tx_ref in seen_tx:
                continue
            seen_tx.add(tx_ref)
        out.append(row)

    out.sort(key=lambda r: (r["chapter"], r.get("party") or ""))
    return out


def validate_chain_focus(links: dict, chain_ids: set[str]) -> dict:
    focus = links.get("chain_focus")
    if focus and focus not in chain_ids:
        links = {**links, "chain_focus": None, "chain_focus_note": f"{focus} 不在 chain.json，请先 build_chain.py"}
    fin = links.get("chain_financial")
    if fin and fin not in chain_ids:
        links = {**links, "chain_financial": None}
    return links


def enrich_cases(txs: list[dict], chain_ids: set[str]) -> list[dict]:
    cases: list[dict] = []
    for tpl in CASES_TEMPLATE:
        case = copy.deepcopy(tpl)
        rules = case.pop("tx_match")
        manual = case.pop("manual_bribery")
        auto = [bribery_from_tx(tx) for tx in txs if tx_matches_case(tx, rules)]
        case["bribery"] = merge_bribery(manual, auto)
        case["links"] = validate_chain_focus(case["links"], chain_ids)
        case["transaction_refs"] = sorted({b["tx_ref"] for b in case["bribery"] if b.get("tx_ref")})
        cases.append(case)
    return cases


def smooth_series(values: list[float], window: int = 5) -> list[float]:
    out: list[float] = []
    half = window // 2
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        chunk = values[lo:hi]
        out.append(round(sum(chunk) / len(chunk), 1))
    return out


def case_ids_for_chapter(ch: int, cases: list[dict]) -> list[str]:
    return [c["id"] for c in cases if ch in c["chapters"]]


def build() -> dict:
    txs = load_transactions("金瓶梅")
    chain_ids = load_chain_event_ids()
    cases = enrich_cases(txs, chain_ids)

    raw = [float(CHAPTER_CORRUPTION.get(ch, 0)) for ch in range(1, CHAPTER_COUNT + 1)]
    smooth = smooth_series(raw, 5)
    by_chapter = []
    for ch in range(1, CHAPTER_COUNT + 1):
        ids = case_ids_for_chapter(ch, cases)
        by_chapter.append(
            {
                "chapter": ch,
                "corruption_index": CHAPTER_CORRUPTION.get(ch, 0),
                "corruption_smooth": smooth[ch - 1],
                "case_ids": ids,
                "petition_count": 1 if ids else 0,
                "phase": next((p["label"] for p in PHASES if p["from"] <= ch <= p["to"]), ""),
            }
        )

    peak_ch = max(by_chapter, key=lambda r: r["corruption_index"])["chapter"]
    lit_chapters = {ch for c in cases for ch in c["chapters"]}
    tx_linked = {b["tx_ref"] for c in cases for b in c["bribery"] if b.get("tx_ref")}

    milestones = []
    for c in cases:
        if c["id"] == "jpm-lit-chenjingji":
            continue
        links = c["links"]
        focus = links.get("chain_focus")
        milestones.append(
            {
                "id": c["id"],
                "title": c["title"],
                "chapter": c["anchor_chapter"],
                "tier": c["tier"],
                "href": f"/jinpingmei/read/cihua/{c['anchor_chapter']}",
                "saga": links.get("saga"),
                "chain_focus": focus,
                "chain_href": f"/jinpingmei/chain?focus={focus}" if focus else None,
            }
        )

    return {
        "book": "金瓶梅",
        "slug": "jinpingmei",
        "generated": date.today().isoformat(),
        "generated_by": "build_litigation_inference.py",
        "inference_note": "推演层：三级司法通关；bribery 含 transactions 自动抽取 + 手标 inference。",
        "tiers": TIERS,
        "phases": PHASES,
        "cases": cases,
        "milestones": milestones,
        "by_chapter": by_chapter,
        "officials": OFFICIALS,
        "social": SOCIAL,
        "global_insights": GLOBAL_INSIGHTS,
        "stats": {
            "case_count": len(cases),
            "chapters_with_litigation": len(lit_chapters),
            "peak_corruption_chapter": peak_ch,
            "peak_corruption": CHAPTER_CORRUPTION.get(peak_ch, 0),
            "bribery_from_transactions": len(tx_linked),
            "transaction_count": len(txs),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    payload = build()
    out = DATA_DIR / "jinpingmei.litigation-inference.json"
    if args.write:
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        s = payload["stats"]
        print(
            f"  jinpingmei.litigation: {s['case_count']} cases · "
            f"{s['chapters_with_litigation']} ch · peak ch{s['peak_corruption_chapter']} · "
            f"tx bribery {s['bribery_from_transactions']}"
        )
        print(f"written → {out.name}")
    else:
        print(json.dumps(payload["stats"], ensure_ascii=False))


if __name__ == "__main__":
    main()
