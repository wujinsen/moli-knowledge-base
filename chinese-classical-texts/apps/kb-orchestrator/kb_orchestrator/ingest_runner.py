from __future__ import annotations

import json
from datetime import datetime, timezone

from .config import NOVELS_ROOT, SLUG_BOOK
from .subprocess_util import run_shell


class IngestRunError(Exception):
    pass


def run_ingest_report(book_slug: str, chapter: int, edition_slug: str | None = None) -> dict:
    book = SLUG_BOOK.get(book_slug)
    if not book:
        raise ValueError(f"unknown book slug: {book_slug}")

    if chapter < 1:
        raise ValueError("chapter must be >= 1")

    ed = f' --edition {edition_slug}' if edition_slug else ""
    cmd = f'python -X utf8 scripts/ingest_report.py "{book}" {chapter}{ed} --json'
    proc = run_shell(cmd, cwd=NOVELS_ROOT, timeout=60)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-2000:]
        raise IngestRunError(err or f"ingest_report exited {proc.returncode}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise IngestRunError(f"invalid JSON from ingest_report: {e}") from e

    data.setdefault("bookSlug", book_slug)
    data.setdefault("generatedAt", datetime.now(timezone.utc).isoformat())
    return data
