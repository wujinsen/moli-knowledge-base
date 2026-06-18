from __future__ import annotations

import json
from datetime import datetime, timezone

from .config import NOVELS_ROOT, SLUG_BOOK
from .subprocess_util import run_shell


class GraphRunError(Exception):
    pass


def _run_graph_report(book_slug: str, *, apply: bool) -> dict:
    book = SLUG_BOOK.get(book_slug)
    if not book:
        raise ValueError(f"unknown book slug: {book_slug}")

    flags = f'"{book}" --json'
    if apply:
        flags += " --apply"
    cmd = f"python -X utf8 scripts/graph_report.py {flags}"
    proc = run_shell(cmd, cwd=NOVELS_ROOT, timeout=180)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-2000:]
        raise GraphRunError(err or f"graph_report exited {proc.returncode}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise GraphRunError(f"invalid JSON from graph_report: {e}") from e

    data.setdefault("bookSlug", book_slug)
    data.setdefault("generatedAt", datetime.now(timezone.utc).isoformat())
    return data


def preview_graph(book_slug: str) -> dict:
    return _run_graph_report(book_slug, apply=False)


def apply_graph(book_slug: str) -> dict:
    return _run_graph_report(book_slug, apply=True)
