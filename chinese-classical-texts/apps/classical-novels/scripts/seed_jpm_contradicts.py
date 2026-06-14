#!/usr/bin/env python3
"""从 jinpingmei.variant-topics.json 同步人物 frontmatter 的 contradicts[]。

用法: python scripts/seed_jpm_contradicts.py
"""
from __future__ import annotations

import json

import yaml

from _common import CHAR_DIR, DATA_DIR, parse_frontmatter

BOOK = "金瓶梅"
TOPICS_PATH = DATA_DIR / "jinpingmei.variant-topics.json"


def write_frontmatter(path, fm: dict, body: str) -> None:
    fm_text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{fm_text}---\n{body}", encoding="utf-8")


def main() -> None:
    data = json.loads(TOPICS_PATH.read_text(encoding="utf-8"))
    char_topics: dict[str, set[str]] = {}
    for topic in data.get("topics", []):
        tid = topic["id"]
        for cid in topic.get("characters", []):
            char_topics.setdefault(cid, set()).add(tid)

    char_dir = CHAR_DIR / BOOK
    updated = 0
    for path in sorted(char_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        cid = fm.get("id", path.stem)
        expected = sorted(char_topics.get(cid, []))
        current = sorted(fm.get("contradicts") or [])
        if expected == current:
            continue
        if expected:
            fm["contradicts"] = expected
        else:
            fm.pop("contradicts", None)
        write_frontmatter(path, fm, body)
        print(f"  {cid}: {current or '—'} → {expected or '—'}")
        updated += 1

    print(f"[{BOOK}] 更新 {updated} 个人物 contradicts（共 {len(char_topics)} 人涉议题）")


if __name__ == "__main__":
    main()
