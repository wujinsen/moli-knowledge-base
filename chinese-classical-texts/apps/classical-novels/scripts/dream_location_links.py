#!/usr/bin/env python3
"""/dream — 地点弱入链自动挂链（红楼梦 location graph）。

修复 lint_kb `location 弱入链仅名录`：入链仅来自「大观园建筑名录」且总数 ≤2。

策略（多轮直至 weak 清空或达上限）：
  1. reciprocate nearby[]（YAML 互指）
  2. 父级 nearby[] 纳入子地点
  3. 父级正文 ## 下辖 补 [[子地点]]
  4. 子地点正文中的 [[人物]] → 人物页 ## 关联地点 回链
  5. 子地点正文中的 [[地点]] → 对端 ## 邻近 回链
  6. occupants → 人物页回链
  7. appear_in → 回目 locations[]

用法:
  python scripts/dream_location_links.py 红楼梦           # 预览
  python scripts/dream_location_links.py 红楼梦 --write   # 写回
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from _common import CHAR_DIR, CONTENT, parse_frontmatter
from reciprocate_location_nearby import reciprocate, set_nearby
from sync_chapter_locations import sync_book as sync_chapter_locations

WIKI_LINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
INDEX_TOPIC = "大观园建筑名录"


def load_location_pages(book: str) -> dict[str, tuple[Path, dict, str]]:
    loc_dir = CONTENT / "locations" / book
    out: dict[str, tuple[Path, dict, str]] = {}
    for p in sorted(loc_dir.glob("*.md")):
        fm, body = parse_frontmatter(p)
        lid = fm.get("id") or p.stem
        out[lid] = (p, fm, body)
    return out


def build_inbound(book: str, pages: dict[str, tuple[Path, dict, str]]) -> dict[str, set[str]]:
    loc_ids = set(pages)
    inbound: dict[str, set[str]] = defaultdict(set)

    def scan(text: str, source: str) -> None:
        for m in WIKI_LINK.finditer(text):
            t = m.group(1).strip()
            if t in loc_ids:
                inbound[t].add(source)

    for lid, (_, fm, body) in pages.items():
        for other in loc_ids:
            if other != lid and f"[[{other}]]" in body:
                inbound[other].add(f"wiki:{lid}")
        for n in fm.get("nearby") or []:
            if isinstance(n, str) and n in loc_ids and n != lid:
                inbound[n].add(f"nearby:{lid}")

    for sub in ("characters", "topics", "events"):
        d = CONTENT / sub / book
        if not d.exists():
            continue
        for p in d.rglob("*.md"):
            scan(p.read_text(encoding="utf-8"), f"{sub}:{p.stem}")

    idx = CONTENT / "topics" / book / f"{INDEX_TOPIC}.md"
    if idx.exists():
        txt = idx.read_text(encoding="utf-8")
        for lid in loc_ids:
            if f"/l/{lid}" in txt:
                inbound[lid].add("index")

    return inbound


def weak_locations(inbound: dict[str, set[str]]) -> list[str]:
    return sorted(
        lid
        for lid, sources in inbound.items()
        if 0 < len(sources) <= 2 and "index" in sources
    )


def has_wiki(body: str, target: str) -> bool:
    return f"[[{target}]]" in body


def insert_before_heading(body: str, heading_prefix: str, block: str) -> str:
    pat = re.compile(rf"^## {re.escape(heading_prefix)}", re.M)
    m = pat.search(body)
    if m:
        return body[: m.start()] + block + body[m.start() :]
    return body.rstrip() + "\n\n" + block


def append_bullet_to_section(body: str, heading: str, bullet: str) -> str:
    target = re.search(r"\[\[([^\]|]+)", bullet)
    if target and has_wiki(body, target.group(1)):
        return body

    section_pat = re.compile(
        rf"(^## {re.escape(heading)}[^\n]*\n)(.*?)(?=^## |\Z)",
        re.M | re.S,
    )
    m = section_pat.search(body)
    if m:
        section = m.group(2)
        if target and has_wiki(section, target.group(1)):
            return body
        new_section = section.rstrip() + "\n" + bullet + "\n"
        return body[: m.start(2)] + new_section + body[m.end(2) :]

    block = f"## {heading}\n\n{bullet}\n"
    return insert_before_heading(body, "评析", block)


def write_page(path: Path, fm_raw: str, body: str, *, dry_run: bool) -> None:
    text = f"---{fm_raw}---{body}"
    if not dry_run:
        path.write_text(text, encoding="utf-8")


def link_parent_child(
    book: str,
    pages: dict[str, tuple[Path, dict, str]],
    lid: str,
    *,
    dry_run: bool,
) -> bool:
    _, fm, _ = pages[lid]
    parent = fm.get("parent")
    if not isinstance(parent, str) or parent not in pages or parent == lid:
        return False
    p_path, _, p_body = pages[parent]
    if has_wiki(p_body, lid):
        return False
    bullet = f"- [[{lid}]]"
    new_body = append_bullet_to_section(p_body, "下辖", bullet)
    if new_body == p_body:
        new_body = append_bullet_to_section(p_body, "关联人物 / 建筑", bullet)
    if new_body == p_body:
        return False
    raw = p_path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    write_page(p_path, parts[1], new_body, dry_run=dry_run)
    pages[parent] = (p_path, pages[parent][1], new_body)
    print(f"  parent {parent}: +[[{lid}]]")
    return True


def link_occupants(
    book: str,
    lid: str,
    fm: dict,
    *,
    dry_run: bool,
) -> int:
    changed = 0
    char_dir = CHAR_DIR / book
    for occ in fm.get("occupants") or []:
        if not isinstance(occ, str) or not occ:
            continue
        c_path = char_dir / f"{occ}.md"
        if not c_path.exists():
            continue
        raw = c_path.read_text(encoding="utf-8")
        parts = raw.split("---", 2)
        if len(parts) < 3:
            continue
        body = parts[2]
        if has_wiki(body, lid):
            continue
        bullet = f"- [[{lid}]]"
        new_body = append_bullet_to_section(body, "关联地点", bullet)
        if new_body == body:
            continue
        write_page(c_path, parts[1], new_body, dry_run=dry_run)
        print(f"  character {occ}: +[[{lid}]]")
        changed += 1
    return changed


def char_exists(book: str, cid: str) -> bool:
    return (CHAR_DIR / book / f"{cid}.md").exists()


def wiki_targets(body: str) -> list[str]:
    return [m.group(1).strip() for m in WIKI_LINK.finditer(body)]


def add_wiki_to_character(
    book: str,
    cid: str,
    lid: str,
    *,
    dry_run: bool,
) -> bool:
    c_path = CHAR_DIR / book / f"{cid}.md"
    raw = c_path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    body = parts[2]
    if has_wiki(body, lid):
        return False
    new_body = append_bullet_to_section(body, "关联地点", f"- [[{lid}]]")
    if new_body == body:
        return False
    write_page(c_path, parts[1], new_body, dry_run=dry_run)
    print(f"  character {cid}: +[[{lid}]]")
    return True


def add_wiki_to_location_body(
    pages: dict[str, tuple[Path, dict, str]],
    peer: str,
    lid: str,
    *,
    dry_run: bool,
) -> bool:
    if peer not in pages or peer == lid:
        return False
    p_path, _, body = pages[peer]
    if has_wiki(body, lid):
        return False
    new_body = append_bullet_to_section(body, "邻近", f"- [[{lid}]]")
    if new_body == body:
        new_body = append_bullet_to_section(body, "下辖", f"- [[{lid}]]")
    if new_body == body:
        return False
    raw = p_path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    write_page(p_path, parts[1], new_body, dry_run=dry_run)
    pages[peer] = (p_path, pages[peer][1], new_body)
    print(f"  location {peer}: +[[{lid}]]")
    return True


def add_parent_nearby(
    pages: dict[str, tuple[Path, dict, str]],
    lid: str,
    fm: dict,
    *,
    dry_run: bool,
) -> bool:
    parent = fm.get("parent")
    if not isinstance(parent, str) or parent not in pages or parent == lid:
        return False
    p_path, p_fm, p_body = pages[parent]
    nearby = [n for n in (p_fm.get("nearby") or []) if isinstance(n, str)]
    if lid in nearby:
        return False
    new_nearby = sorted(set(nearby) | {lid})
    raw = p_path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    new_fm = set_nearby(parts[1], new_nearby)
    if new_fm == parts[1]:
        return False
    if not dry_run:
        p_path.write_text(f"---{new_fm}---{parts[2]}", encoding="utf-8")
    p_fm = parse_frontmatter(p_path)[0] if not dry_run else {**p_fm, "nearby": new_nearby}
    pages[parent] = (p_path, p_fm, p_body)
    print(f"  parent {parent} nearby: +{lid}")
    return True


def link_body_characters(
    book: str,
    lid: str,
    body: str,
    loc_ids: set[str],
    *,
    dry_run: bool,
) -> int:
    changed = 0
    for target in wiki_targets(body):
        if target in loc_ids or not char_exists(book, target):
            continue
        if add_wiki_to_character(book, target, lid, dry_run=dry_run):
            changed += 1
    return changed


def link_body_peers(
    pages: dict[str, tuple[Path, dict, str]],
    lid: str,
    body: str,
    fm: dict,
    loc_ids: set[str],
    *,
    dry_run: bool,
) -> int:
    parent = fm.get("parent")
    changed = 0
    for target in wiki_targets(body):
        if target not in loc_ids or target == lid or target == parent:
            continue
        if add_wiki_to_location_body(pages, target, lid, dry_run=dry_run):
            changed += 1
    return changed


def fix_weak_batch(
    book: str,
    pages: dict[str, tuple[Path, dict, str]],
    weak: list[str],
    *,
    dry_run: bool,
) -> dict[str, int]:
    loc_ids = set(pages)
    batch = {"parent_nearby": 0, "parent": 0, "character": 0, "peer": 0, "occupant": 0}
    for lid in weak:
        path, fm, body = pages[lid]
        if add_parent_nearby(pages, lid, fm, dry_run=dry_run):
            batch["parent_nearby"] += 1
        if link_parent_child(book, pages, lid, dry_run=dry_run):
            batch["parent"] += 1
        batch["character"] += link_body_characters(
            book, lid, body, loc_ids, dry_run=dry_run
        )
        batch["peer"] += link_body_peers(pages, lid, body, fm, loc_ids, dry_run=dry_run)
        batch["occupant"] += link_occupants(book, lid, fm, dry_run=dry_run)
    return batch


def dream_book(book: str, *, write: bool) -> dict[str, int]:
    if book != "红楼梦":
        print(f"skip {book}: location weak-link dream 当前仅支持红楼梦", file=sys.stderr)
        return {}

    dry_run = not write
    stats = {
        "rounds": 0,
        "nearby": 0,
        "parent_nearby": 0,
        "parent": 0,
        "character": 0,
        "peer": 0,
        "occupant": 0,
        "chapters": 0,
    }

    pages = load_location_pages(book)
    inbound = build_inbound(book, pages)
    initial_weak = weak_locations(inbound)
    print(f"initial weak: {len(initial_weak)}")

    for round_no in range(1, 5):
        weak = weak_locations(build_inbound(book, load_location_pages(book)))
        if not weak:
            break
        stats["rounds"] = round_no
        print(f"\n--- round {round_no} · weak {len(weak)} ---")
        print("== reciprocate nearby[] ==")
        stats["nearby"] += reciprocate(book, dry_run=dry_run)

        pages = load_location_pages(book)
        batch = fix_weak_batch(book, pages, weak, dry_run=dry_run)
        for k in ("parent_nearby", "parent", "character", "peer", "occupant"):
            stats[k] += batch[k]

    print("\n== sync appear_in → chapter locations[] ==")
    stats["chapters"] = sync_chapter_locations(book, dry_run=dry_run)

    pages = load_location_pages(book)
    remaining = weak_locations(build_inbound(book, pages))
    print(f"\nweak {len(initial_weak)} → {len(remaining)}")
    if remaining:
        print("  still weak:", ", ".join(remaining))
    else:
        print("  location graph weak links cleared")

    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description="/dream location weak-link auto wiring")
    ap.add_argument("book", nargs="?", default="红楼梦")
    ap.add_argument("--write", action="store_true", help="写回文件（默认仅预览 reciprocate 外的变更）")
    args = ap.parse_args()

    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"dream_location_links [{mode}] · {args.book}\n")
    stats = dream_book(args.book, write=args.write)
    if stats:
        print(
            f"\n{'Would change' if not args.write else 'Changed'}: "
            f"rounds={stats['rounds']}, nearby={stats['nearby']}, "
            f"parent_nearby={stats['parent_nearby']}, parent_wiki={stats['parent']}, "
            f"character={stats['character']}, peer={stats['peer']}, "
            f"occupant={stats['occupant']}, chapters={stats['chapters']}"
        )
    if not args.write:
        print("\n（预览模式；加 --write 写回）")


if __name__ == "__main__":
    main()
