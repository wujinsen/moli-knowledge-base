"""Shared helpers: project paths + frontmatter parsing."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "src" / "content"
CHAR_DIR = CONTENT / "characters"
CHAPTER_DIR = CONTENT / "chapters"
DATA_DIR = ROOT / "src" / "data"

BOOKS = ["红楼梦", "金瓶梅", "西游记"]

try:
    import yaml  # type: ignore

    _HAS_YAML = True
except ImportError:  # pragma: no cover
    _HAS_YAML = False


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Requires PyYAML for nested fields."""
    text = path.read_text(encoding="utf-8-sig")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    if _HAS_YAML:
        data = yaml.safe_load(fm_raw) or {}
    else:
        raise SystemExit(
            "需要 PyYAML 解析 frontmatter，请先运行: pip install pyyaml"
        )
    return data, body


def count_plot_entries(body: str) -> int:
    """Count ## 关键情节 bullets and table rows (西游等常用表格梗概)。"""
    plot_sec = re.search(r"## 关键情节[^\n]*\n(.*?)(?=\n## |\Z)", body, re.S)
    if not plot_sec:
        return 0
    n = 0
    for ln in plot_sec.group(1).splitlines():
        s = ln.strip()
        if not s or re.match(r"^\|[-:\s|]+\|$", s):
            continue
        if s.startswith("-"):
            n += 1
        elif s.startswith("|"):
            if re.search(r"第\d+回?", s):
                n += 1
            elif re.match(r"^\|\s*\d", s):
                n += 1
    return n


def iter_characters(book: str):
    d = CHAR_DIR / book
    if not d.exists():
        return
    for p in sorted(d.glob("*.md")):
        fm, body = parse_frontmatter(p)
        yield p, fm, body


def resolve_books(arg: str | None) -> list[str]:
    if arg and arg in BOOKS:
        return [arg]
    return BOOKS
