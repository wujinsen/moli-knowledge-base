#!/usr/bin/env python3
"""/lint 辅助 — 人物页低密度扫描（只报告）。

用法: python scripts/lint_character_density.py 金瓶梅
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from _common import CONTENT, DATA_DIR, count_plot_entries, iter_characters

VARIANT_TOPICS_SLUG = {"金瓶梅": "jinpingmei", "红楼梦": "honglou"}


def load_variant_topic_ids(book: str) -> set[str]:
    slug = VARIANT_TOPICS_SLUG.get(book)
    if not slug:
        return set()
    path = DATA_DIR / f"{slug}.variant-topics.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return {t["id"] for t in data.get("topics", [])}

SYMMETRIC = {
    "夫妻", "兄弟", "姐妹", "妯娌", "师兄弟", "同僚", "朋友", "结拜", "情人", "仇敌", "敌对",
}


def density_score(d: dict) -> int:
    return (
        d["rel"] * 2
        + d["plot"] * 3
        + (1 if d["main"] else 0)
        + (1 if d["review"] else 0)
        + min(d["inbound"], 5)
    )


def _scan_pages(book: str) -> tuple[dict[str, dict], set[str], dict, list[str], list[str]]:
    """Build per-character metrics used by scan() and collect_density()."""
    chars = list(iter_characters(book))
    ids = {fm.get("id") or p.stem for p, fm, _ in chars}
    pages: dict[str, dict] = {}
    inbound: dict[str, set[str]] = defaultdict(set)

    for p, fm, body in chars:
        cid = fm.get("id") or p.stem
        rels = fm.get("relations") or []
        plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
        plots: list[str] = []
        if plot_sec:
            plots = [ln for ln in plot_sec.group(1).splitlines() if ln.strip().startswith("-")]
        plot_count = count_plot_entries(body)
        pages[cid] = {
            "rel": len(rels),
            "plot": plot_count,
            "body_len": len(re.sub(r"\[\[[^\]]+\]\]", "", body).strip()),
            "main": "## 主要关系" in body,
            "identity": "## 身份" in body,
            "review": "## 评析" in body,
            "weight": fm.get("weight") or 0,
            "status": fm.get("status") or "",
            "first": fm.get("first_appear") or "",
        }

    char_dir = CONTENT / "characters" / book
    for p in char_dir.glob("*.md"):
        txt = p.read_text(encoding="utf-8-sig")
        src = p.stem
        for m in re.finditer(r"\[\[([^\]|]+)", txt):
            t = m.group(1).strip()
            if t in ids and t != src:
                inbound[t].add(src)
    topics_dir = CONTENT / "topics" / book
    if topics_dir.exists():
        for p in topics_dir.glob("*.md"):
            txt = p.read_text(encoding="utf-8-sig")
            for m in re.finditer(r"\[\[([^\]|]+)", txt):
                t = m.group(1).strip()
                if t in ids:
                    inbound[t].add("topic:" + p.stem)

    for cid in pages:
        pages[cid]["inbound"] = len(inbound[cid])

    rel_path = DATA_DIR / f"{book}.relations.json"
    rel_json = json.loads(rel_path.read_text(encoding="utf-8-sig"))
    variant_ids = load_variant_topic_ids(book)
    missing_targets = sorted(
        {
            e["target"]
            for e in rel_json["edges"]
            if e["target"] not in ids
            and not str(e["target"]).startswith("版本-")
            and e["target"] not in variant_ids
        }
    )

    rel_map: dict[str, set[str]] = defaultdict(set)
    for p, fm, _ in chars:
        cid = fm.get("id") or p.stem
        for r in fm.get("relations") or []:
            rel_map[cid].add(r["target"])
    one_way: list[str] = []
    for p, fm, _ in chars:
        cid = fm.get("id") or p.stem
        for r in fm.get("relations") or []:
            t = r["target"]
            if t not in ids:
                continue
            rt = r.get("type", "")
            if rt in SYMMETRIC:
                continue
            if cid not in rel_map[t]:
                one_way.append(f"{cid}→{t} ({rt})")

    return pages, ids, rel_json, missing_targets, one_way


def collect_density(book: str) -> dict:
    """Structured density scan for Studio / JSON API."""
    pages, ids, rel_json, missing_targets, one_way = _scan_pages(book)
    rows = sorted((density_score(d), cid, d) for cid, d in pages.items())
    score_dist: dict[str, int] = defaultdict(int)
    for score, _cid, _d in rows:
        score_dist[str(score)] += 1

    def flags_for(d: dict) -> list[str]:
        out: list[str] = []
        if d["plot"] <= 2:
            out.append(f"plot={d['plot']}")
        if d["rel"] <= 3:
            out.append(f"rel={d['rel']}")
        if not d["main"]:
            out.append("缺主要关系")
        if d["inbound"] <= 1:
            out.append(f"入链={d['inbound']}")
        return out

    priority = []
    for score, cid, d in rows:
        if cid == "西门庆":
            continue
        if score > 8:
            continue
        priority.append(
            {
                "id": cid,
                "score": score,
                "rel": d["rel"],
                "plot": d["plot"],
                "inbound": d["inbound"],
                "flags": flags_for(d),
            }
        )
        if len(priority) >= 30:
            break

    struct_missing = []
    for cid, d in sorted(pages.items()):
        miss = []
        if not d["identity"]:
            miss.append("缺身份")
        if not d["main"]:
            miss.append("缺主要关系")
        if d["plot"] == 0:
            miss.append("无关键情节")
        if not d["review"]:
            miss.append("缺评析")
        if miss:
            struct_missing.append({"id": cid, "missing": miss})

    weak_inbound = sorted(
        ({"id": cid, "inbound": d["inbound"]} for cid, d in pages.items() if d["inbound"] <= 1),
        key=lambda x: (x["inbound"], x["id"]),
    )

    return {
        "totalCharacters": len(rows),
        "graphNodes": len(rel_json["nodes"]),
        "graphEdges": len(rel_json["edges"]),
        "scoreDistribution": dict(sorted(score_dist.items(), key=lambda x: int(x[0]))),
        "priorityBatch": priority,
        "structMissing": struct_missing[:50],
        "structMissingTotal": len(struct_missing),
        "weakInbound": weak_inbound[:40],
        "weakInboundTotal": len(weak_inbound),
        "missingRelTargets": missing_targets,
        "oneWayRels": sorted(set(one_way))[:30],
        "oneWayRelsTotal": len(set(one_way)),
    }


def scan(book: str) -> None:
    pages, ids, rel_json, missing_targets, one_way = _scan_pages(book)
    rows = sorted((density_score(d), cid, d) for cid, d in pages.items())

    print(f"=== {book} /lint 低密度人物 ===")
    print(
        f"全库 {len(rows)} 页 · 图谱 {len(rel_json['nodes'])} 节点 / {len(rel_json['edges'])} 边"
    )
    print("score = rel×2 + plot×3 + 主要关系 + 评析 + min(入链,5)\n")

    print("--- 下一批优先 (score≤8, 排除西门庆) ---")
    batch = [r for r in rows if r[1] != "西门庆" and r[0] <= 8][:22]
    for score, cid, d in batch:
        flags = []
        if d["plot"] <= 2:
            flags.append(f"plot={d['plot']}")
        if d["rel"] <= 3:
            flags.append(f"rel={d['rel']}")
        if not d["main"]:
            flags.append("缺主要关系")
        if d["inbound"] <= 1:
            flags.append(f"入链={d['inbound']}")
        flag_s = " ".join(flags) if flags else "—"
        print(f"{cid}\tscore={score}\t{flag_s}")

    print("\n--- 结构缺漏 ---")
    struct_miss = []
    for cid, d in sorted(pages.items()):
        miss = []
        if not d["identity"]:
            miss.append("缺身份")
        if not d["main"]:
            miss.append("缺主要关系")
        if d["plot"] == 0:
            miss.append("无关键情节")
        if not d["review"]:
            miss.append("缺评析")
        if miss:
            struct_miss.append(f"{cid}: {', '.join(miss)}")
    if struct_miss:
        for line in struct_miss[:25]:
            print(line)
        if len(struct_miss) > 25:
            print(f"... +{len(struct_miss) - 25}")
    else:
        print("(无)")

    print("\n--- 弱入链 (入链≤1) ---")
    weak = sorted((d["inbound"], cid) for cid, d in pages.items() if d["inbound"] <= 1)
    for n, c in weak[:30]:
        print(f"入链={n}\t{c}")
    if len(weak) > 30:
        print(f"... +{len(weak) - 30}")

    print("\n--- relations 指向缺页 ---")
    if missing_targets:
        for t in missing_targets:
            print(t)
    else:
        print("(无)")

    print("\n--- 非对称单边 (前20) ---")
    uniq = sorted(set(one_way))
    for x in uniq[:20]:
        print(x)
    if len(uniq) > 20:
        print(f"... +{len(uniq) - 20}")

    print("\n--- 按线分组 · 建议 /dream 批次 ---")
    groups = {
        "方外/刑名": ["王和尚", "何九", "陈洪", "安童", "胡僧", "吴神仙"],
        "勾栏/唱": [
            "郑爱香", "秦玉芝", "向三", "保儿", "周肖儿", "妙凤", "妙趣", "荣娇儿",
            "段绵纱", "消愁儿", "郑娇儿", "齐香儿", "吕赛儿", "樊百奴儿", "聂钺儿",
        ],
        "帮闲/市井": ["白秃子", "罗回子", "白回子", "白赉光", "于宽", "祝实念", "孙天化", "文嫂", "老虔婆", "桂卿"],
        "府内配角": ["如意儿", "洪四儿", "大师父", "周肖儿"],
        "后二十回次要": ["云理守", "陆秉义", "僧宝儿", "来兴儿"],
    }
    for gname, members in groups.items():
        hits = []
        for cid in members:
            if cid not in pages:
                hits.append(f"{cid}(缺页)")
                continue
            d = pages[cid]
            sc = d["rel"] * 2 + d["plot"] * 3
            if sc <= 14:
                hits.append(f"{cid}(rel={d['rel']},plot={d['plot']})")
        if hits:
            print(f"{gname}: {', '.join(hits)}")


def main() -> None:
    book = sys.argv[1] if len(sys.argv) > 1 else "金瓶梅"
    scan(book)


if __name__ == "__main__":
    main()
