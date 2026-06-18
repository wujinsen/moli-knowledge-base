"""Shared /dream patch helpers — any book."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from _common import CONTENT, iter_characters, parse_frontmatter
from lint_character_density import density_score
from trust_guard import (
    collect_search_chapters,
    load_cihua_body,
    name_terms,
    text_has_any,
    verify_relation_edge,
)

REL_TYPES = {
    "夫妻", "父子", "母子", "兄弟", "姐妹", "祖孙", "妯娌", "主仆", "师徒", "师兄弟",
    "同僚", "朋友", "结拜", "君臣", "情人", "恋慕", "仇敌", "敌对",
}


def scan_pages(book: str) -> tuple[dict[str, dict], dict[str, set[str]]]:
    chars = list(iter_characters(book))
    ids = {fm.get("id") or p.stem for p, fm, _ in chars}
    pages: dict[str, dict] = {}
    inbound: dict[str, set[str]] = defaultdict(set)

    for p, fm, body in chars:
        cid = fm.get("id") or p.stem
        plot_sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
        plots: list[str] = []
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
            "identity": "## 身份" in body,
            "weight": int(fm.get("weight") or 0),
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
                    inbound[t].add("topic")

    for cid in pages:
        pages[cid]["inbound"] = len(inbound[cid])
    return pages, inbound


def page_score(info: dict) -> int:
    return density_score({k: info[k] for k in ("rel", "plot", "main", "review", "inbound")})


def guess_rel_type(src_fm: dict, tgt_fm: dict) -> str:
    src_tags = set(src_fm.get("tags") or [])
    tgt_tags = set(tgt_fm.get("tags") or [])
    if "妖怪" in src_tags or "monster" in (src_fm.get("type") or ""):
        return "仇敌" if "主角" in (tgt_fm.get("tags") or []) else "同僚"
    if "丫鬟" in src_tags or "小厮" in src_tags:
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
    book: str,
    cid: str,
    fm: dict,
    body: str,
    pages: dict[str, dict],
    existing: set[str],
    chapter_cache: dict[int, str | None],
) -> list[tuple[int, str]]:
    search = collect_search_chapters(
        cid, fm, body, {k: (v["path"], v["fm"], v["body"]) for k, v in pages.items()}, None
    )
    src_terms = name_terms(fm, cid)
    hits: Counter[str] = Counter()
    for chap in search:
        if chap not in chapter_cache:
            chapter_cache[chap] = load_cihua_body(book, chap)
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
    book: str,
    cid: str,
    pages: dict[str, dict],
    all_fms: dict[str, tuple],
    chapter_cache: dict[int, str | None],
) -> dict | None:
    info = pages[cid]
    fm, body = info["fm"], info["body"]
    existing = {r.get("target") for r in (fm.get("relations") or [])}
    for _, tid in co_occur_candidates(book, cid, fm, body, pages, existing, chapter_cache):
        ok, _ = verify_relation_edge(book, cid, fm, body, tid, "同僚", all_fms, chapter_cache)
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
    book: str,
    cid: str,
    pages: dict[str, dict],
    inbound: dict[str, set[str]],
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
        hpath = hinfo["path"]
        hbody = hpath.read_text(encoding="utf-8-sig")
        if f"[[{cid}]]" in hbody:
            continue
        for chap in search:
            if chap not in chapter_cache:
                chapter_cache[chap] = load_cihua_body(book, chap)
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
