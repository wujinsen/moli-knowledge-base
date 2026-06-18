from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone

from .config import NOVELS_ROOT, SLUG_BOOK

_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL_SEC = 300


class TodosRunError(Exception):
    pass


def run_studio_todos(book_slug: str) -> dict:
    book = SLUG_BOOK.get(book_slug)
    if not book:
        raise ValueError(f"unknown book slug: {book_slug}")

    now = time.time()
    cached = _CACHE.get(book_slug)
    if cached and now - cached[0] < _CACHE_TTL_SEC:
        return cached[1]

    cmd = f'python scripts/studio_todos.py "{book}" --json'
    proc = subprocess.run(
        cmd,
        cwd=NOVELS_ROOT,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-2500:]
        raise TodosRunError(err or f"studio_todos exited {proc.returncode}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise TodosRunError(f"invalid JSON from studio_todos: {e}") from e

    data.setdefault("bookSlug", book_slug)
    data.setdefault("generatedAt", datetime.now(timezone.utc).isoformat())
    _CACHE[book_slug] = (now, data)
    return data
