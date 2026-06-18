from __future__ import annotations

from datetime import date
from pathlib import Path


def default_log_entry(summary: str) -> str:
    return f"## [{date.today().isoformat()}] studio | {summary}"


def append_studio_log(root: Path, book: str, entry: str, *, dry_run: bool = False) -> Path:
    if not entry.startswith("## ["):
        entry = default_log_entry(entry)

    log_path = root / "src" / "content" / f"{book}.log.md"
    if not log_path.exists():
        raise FileNotFoundError(f"log not found: {log_path}")

    text = log_path.read_text(encoding="utf-8-sig")
    if entry.strip() in text:
        return log_path

    # Prepend after optional title line (# 金瓶梅 · 维护日志)
    lines = text.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("# "):
        insert_at = 1
        if len(lines) > 1 and lines[1].strip() == "":
            insert_at = 2

    block = entry.rstrip() + "\n\n"
    if dry_run:
        return log_path

    new_text = "".join(lines[:insert_at]) + block + "".join(lines[insert_at:])
    log_path.write_text(new_text, encoding="utf-8")
    return log_path
