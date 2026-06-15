"""saga 大事记专项校验（只读，不改写文件）。

校验项：
  1. prev/next 链是否按回目顺序闭环（首无 prev、尾无 next、相邻互指）
  2. chapters 是否在该书回目范围内
  3. prev/next 指向的事件是否存在
  4. characters / locations 引用的 id 是否有对应实体页

用法：
  python scripts/lint_saga.py            # 校验三书
  python scripts/lint_saga.py 红楼梦      # 仅校验一书
退出码 0 = 无问题，1 = 有问题。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CONTENT, parse_frontmatter, resolve_books  # noqa: E402

EVENTS = CONTENT / "events"
CHAP_MAX = {"红楼梦": 120, "金瓶梅": 100, "西游记": 100}


def load_milestones(book: str) -> list[tuple[Path, dict]]:
    d = EVENTS / book
    out: list[tuple[Path, dict]] = []
    if d.exists():
        for p in sorted(d.glob("*.md")):
            fm, _ = parse_frontmatter(p)
            if fm.get("subtype") == "milestone":
                out.append((p, fm))
    return out


def entity_ids(book: str, kind: str) -> set[str]:
    base = CONTENT / kind / book
    if not base.exists():
        return set()
    return {p.stem for p in base.glob("*.md")}


def lint_book(book: str) -> list[str]:
    issues: list[str] = []
    ms = load_milestones(book)
    if not ms:
        return issues

    by_id = {fm["id"]: fm for _, fm in ms}
    chars = entity_ids(book, "characters")
    locs = entity_ids(book, "locations")
    cmax = CHAP_MAX.get(book, 200)

    ordered = sorted(ms, key=lambda t: ((t[1].get("chapters") or [999])[0], t[1]["id"]))

    for i, (_, fm) in enumerate(ordered):
        eid = fm["id"]
        for c in fm.get("chapters") or []:
            if c < 1 or c > cmax:
                issues.append(f"{eid}: 回目 {c} 越界（应在 1–{cmax}）")

        prev, nxt = fm.get("prev"), fm.get("next")
        if prev and prev not in by_id:
            issues.append(f"{eid}: prev={prev} 指向不存在的事件")
        if nxt and nxt not in by_id:
            issues.append(f"{eid}: next={nxt} 指向不存在的事件")

        exp_prev = ordered[i - 1][1]["id"] if i > 0 else None
        exp_next = ordered[i + 1][1]["id"] if i < len(ordered) - 1 else None
        if prev != exp_prev:
            issues.append(f"{eid}: prev={prev!r} 与回目顺序不符（期望 {exp_prev!r}）")
        if nxt != exp_next:
            issues.append(f"{eid}: next={nxt!r} 与回目顺序不符（期望 {exp_next!r}）")

        for c in fm.get("characters") or []:
            if c not in chars:
                issues.append(f"{eid}: 人物「{c}」无实体页")
        for l in fm.get("locations") or []:
            if l not in locs:
                issues.append(f"{eid}: 地点「{l}」无实体页")

    return issues


def main() -> None:
    books = resolve_books(sys.argv[1] if len(sys.argv) > 1 else None)
    total = 0
    for b in books:
        ms = load_milestones(b)
        issues = lint_book(b)
        status = "OK" if not issues else f"{len(issues)} 处问题"
        print(f"== {b}：{len(ms)} 个 milestone · {status} ==")
        for it in issues:
            print("  -", it)
        total += len(issues)
    print(f"\n合计 {total} 处问题")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
