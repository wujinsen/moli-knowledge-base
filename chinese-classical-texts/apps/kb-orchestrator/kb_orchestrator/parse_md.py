from __future__ import annotations

import re
from pathlib import Path

import yaml


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def count_plot_bullets(body: str) -> int:
    sec = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    if not sec:
        return 0
    return sum(1 for ln in sec.group(1).splitlines() if ln.strip().startswith("-"))


def parse_chapter_num(text: str) -> int | None:
    m = re.search(r"第(\d+)回", text or "")
    return int(m.group(1)) if m else None
