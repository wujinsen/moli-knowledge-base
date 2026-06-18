from __future__ import annotations

import json
from datetime import datetime, timezone

from .config import NOVELS_ROOT, SLUG_BOOK
from .subprocess_util import run_shell


class GuardRunError(Exception):
    pass


def run_guard_report(book_slug: str) -> dict:
    book = SLUG_BOOK.get(book_slug)
    if not book:
        raise ValueError(f"unknown book slug: {book_slug}")

    cmd = f'python -X utf8 scripts/guard_report.py "{book}" --json'
    proc = run_shell(cmd, cwd=NOVELS_ROOT, timeout=600)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-2500:]
        raise GuardRunError(err or f"guard_report exited {proc.returncode}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise GuardRunError(f"invalid JSON from guard_report: {e}") from e

    data.setdefault("bookSlug", book_slug)
    data.setdefault("generatedAt", datetime.now(timezone.utc).isoformat())
    return data
