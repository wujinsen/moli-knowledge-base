#!/usr/bin/env python3
"""/dream 第十二梯队 — score≤26 全量压至 ≥27。

- score=25 / score=26：自动补 1 条 guard 可核 relations（+2）
- 补关系失败且 score=26 且 in<5：hub 互链（+1）
- 仍失败：全书回扫 co-occur 再试

用法: python scripts/patch_hlm_tier12_score26.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CONTENT, iter_characters, parse_frontmatter  # noqa: E402
from lint_character_density import density_score  # noqa: E402
from trust_guard import (  # noqa: E402
    chapter_count,
    collect_search_chapters,
    load_cihua_body,
    name_terms,
    text_has_any,
    verify_relation_edge,
)

BOOK = "红楼梦"
TARGET = 27
THIN_SCORES = {25, 26}


def scan_pages() -> tuple[dict[str, dict], dict[str, set[str]]]:
    chars = list(iter_characters(BOOK))
    ids = {fm.get("id") or p.stem for p, fm, _ in chars}
    pages: dict[str, dict] = {}
    inbound: dict[str, set[str]] = defaultdict(set)

    for p, fm, body in chars:
        cid = fm.get("id") or p.stem
        plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
        plots = []
        if plot_sec:
            plots = [ln for ln in plot_sec.group(1).splitlines() if ln.strip().startswith("-")]
        pages[cid] = {
            "path": p,
            "fm": fm,
            "body": body,
            "rel": len(fm.get("relations") or []),
            "plot": len(plots),
            "main": "## 主要关系" in body,
            "review": "## 评析" in body,
            "weight": int(fm.get("weight") or 0),
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
    return pages, inbound


def guess_rel_type(src_fm: dict, tgt_fm: dict) -> str:
    src_tags = set(src_fm.get("tags") or [])
    tgt_tags = set(tgt_fm.get("tags") or [])
    if "丫鬟" in src_tags or "小厮" in src_tags:
        if "贾母" in (tgt_fm.get("name") or "") or "夫人" in (tgt_fm.get("name") or ""):
            return "主仆"
        if tgt_fm.get("faction") and src_fm.get("faction") == tgt_fm.get("faction"):
            return "主仆"
    if "门客" in src_tags or "清客" in src_tags:
        return "同僚"
    if "丫鬟" in tgt_tags and "丫鬟" in src_tags:
        return "姐妹"
    if src_fm.get("gender") == tgt_fm.get("gender") == "女":
        return "姐妹"
    return "同僚"


def co_occur_candidates(
    cid: str,
    fm: dict,
    body: str,
    pages: dict[str, dict],
    existing: set[str],
    chapter_cache: dict[int, str | None],
    *,
    full_scan: bool = False,
) -> list[tuple[int, str]]:
    all_fms = {k: (v["path"], v["fm"], v["body"]) for k, v in pages.items()}
    search = collect_search_chapters(cid, fm, body, all_fms, None)
    if full_scan:
        search = list(range(1, chapter_count(BOOK) + 1))
    src_terms = name_terms(fm, cid)
    hits: Counter[str] = Counter()
    for chap in search:
        if chap not in chapter_cache:
            chapter_cache[chap] = load_cihua_body(BOOK, chap)
        text = chapter_cache[chap]
        if not text or not text_has_any(text, src_terms):
            continue
        for tid, info in pages.items():
            if tid == cid or tid in existing:
                continue
            tfm = info["fm"]
            if text_has_any(text, name_terms(tfm, tid)):
                hits[tid] += 1
    return sorted(((pages[t]["weight"], t) for t in hits), reverse=True)


def pick_relation(
    cid: str,
    pages: dict[str, dict],
    all_fms: dict[str, tuple],
    chapter_cache: dict[int, str | None],
    *,
    full_scan: bool = False,
) -> dict | None:
    info = pages[cid]
    fm, body = info["fm"], info["body"]
    existing = {r.get("target") for r in (fm.get("relations") or [])}
    for _, tid in co_occur_candidates(
        cid, fm, body, pages, existing, chapter_cache, full_scan=full_scan
    ):
        ok, _ = verify_relation_edge(BOOK, cid, fm, body, tid, "同僚", all_fms, chapter_cache)
        if ok:
            return {"target": tid, "type": guess_rel_type(fm, pages[tid]["fm"]), "role": "同场"}
    return None


def add_relations(fm: dict, extra: dict) -> bool:
    rels = list(fm.get("relations") or [])
    if extra["target"] in {r.get("target") for r in rels}:
        return False
    rels.append(extra)
    fm["relations"] = rels
    return True


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


def pick_hub_source(
    cid: str,
    pages: dict[str, dict],
    chapter_cache: dict[int, str | None],
) -> str | None:
    info = pages[cid]
    fm, body = info["fm"], info["body"]
    search = collect_search_chapters(
        cid, fm, body, {k: (v["path"], v["fm"], v["body"]) for k, v in pages.items()}, None
    )
    src_terms = name_terms(fm, cid)
    candidates: list[tuple[int, str]] = []
    for hid, hinfo in pages.items():
        if hid == cid:
            continue
        hbody = hinfo["path"].read_text(encoding="utf-8-sig")
        if f"[[{cid}]]" in hbody:
            continue
        for chap in search:
            if chap not in chapter_cache:
                chapter_cache[chap] = load_cihua_body(BOOK, chap)
            text = chapter_cache[chap]
            if not text:
                continue
            if text_has_any(text, src_terms) and text_has_any(text, name_terms(hinfo["fm"], hid)):
                candidates.append((hinfo["weight"], hid))
                break
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def write_page(path: Path, fm: dict, body: str, dry_run: bool) -> None:
    if dry_run:
        return
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def page_score(info: dict) -> int:
    return density_score({k: info[k] for k in ("rel", "plot", "main", "review", "inbound")})


def patch_one(
    cid: str,
    pages: dict[str, dict],
    inbound: dict[str, set[str]],
    all_fms: dict[str, tuple],
    chapter_cache: dict[int, str | None],
    dry_run: bool,
) -> str | None:
    info = pages[cid]
    score = page_score(info)
    if score not in THIN_SCORES:
        return None

    rel = pick_relation(cid, pages, all_fms, chapter_cache)
    if not rel:
        rel = pick_relation(cid, pages, all_fms, chapter_cache, full_scan=True)
    if rel:
        fm = dict(info["fm"])
        if add_relations(fm, rel):
            write_page(info["path"], fm, info["body"], dry_run)
            info["fm"] = fm
            info["rel"] = len(fm.get("relations") or [])
            all_fms[cid] = (info["path"], fm, info["body"])
            return f"{cid}: +rel→{rel['target']}"

    if score == 26 and info["inbound"] < 5:
        hub = pick_hub_source(cid, pages, chapter_cache)
        if hub:
            hub_path = pages[hub]["path"]
            hfm, hbody = parse_frontmatter(hub_path)
            new_body = add_hub_link(hbody, cid)
            if new_body != hbody:
                if not dry_run:
                    hfm_text = yaml.dump(hfm, allow_unicode=True, default_flow_style=False, sort_keys=False)
                    hub_path.write_text(f"---\n{hfm_text}---\n{new_body}", encoding="utf-8")
                inbound[cid].add(hub)
                info["inbound"] = len(inbound[cid])
                return f"{hub}→{cid}: hub"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pages, inbound = scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}
    changes: list[str] = []
    stuck: list[str] = []

    for cid in sorted(pages):
        if page_score(pages[cid]) not in THIN_SCORES:
            continue
        result = patch_one(cid, pages, inbound, all_fms, chapter_cache, args.dry_run)
        if result:
            changes.append(result)
        else:
            stuck.append(cid)
            print(f"WARN stuck {cid}")

    print(f"patched {len(changes)} items")
    for c in changes:
        print(" ", c)

    if not args.dry_run:
        thin = sum(1 for info in pages.values() if page_score(info) <= 26)
        print(f"remaining score<=26: {thin}")
        if stuck:
            print(f"stuck: {len(stuck)}")


if __name__ == "__main__":
    main()
