from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone

from .config import NOVELS_ROOT, SLUG_BOOK


class LintRunError(Exception):
    pass


def run_lint_report(book_slug: str) -> dict:
    book = SLUG_BOOK.get(book_slug)
    if not book:
        raise ValueError(f"unknown book slug: {book_slug}")

    cmd = f'python scripts/lint_report.py "{book}" --json'
    proc = subprocess.run(
        cmd,
        cwd=NOVELS_ROOT,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-2000:]
        raise LintRunError(err or f"lint_report exited {proc.returncode}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise LintRunError(f"invalid JSON from lint_report: {e}") from e

    data.setdefault("bookSlug", book_slug)
    data.setdefault("generatedAt", datetime.now(timezone.utc).isoformat())
    return data
