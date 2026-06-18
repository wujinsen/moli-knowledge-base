from __future__ import annotations

import json
import sys
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from .config import NOVELS_ROOT
from .subprocess_util import run_shell


class DreamRunError(Exception):
    pass


def _dream_report_module():
    scripts = NOVELS_ROOT / "scripts"
    path = str(scripts)
    if path not in sys.path:
        sys.path.insert(0, path)
    import dream_report  # noqa: WPS433

    return dream_report


def _run_dream(book_slug: str, extra_args: str) -> dict:
    cmd = f'python -X utf8 scripts/dream_report.py --book-slug {book_slug} {extra_args} --json'
    proc = run_shell(cmd, cwd=NOVELS_ROOT, timeout=360)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-2500:]
        raise DreamRunError(err or f"dream_report exited {proc.returncode}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise DreamRunError(f"invalid JSON from dream_report: {e}") from e

    data.setdefault("generatedAt", datetime.now(timezone.utc).isoformat())
    return data


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _iter_dream_events(book_slug: str, tier_id: str | None, *, apply: bool):
    dream_report = _dream_report_module()
    if tier_id is None:
        yield _sse("dream.error", {"message": "tier_id required"})
        return

    try:
        events = (
            dream_report.iter_apply_tier_events(book_slug, tier_id, novels_root=NOVELS_ROOT)
            if apply
            else dream_report.iter_preview_tier_events(book_slug, tier_id)
        )
        for ev in events:
            kind = ev.get("event")
            if kind == "done":
                result = ev["result"]
                result.setdefault("bookSlug", book_slug)
                result.setdefault("generatedAt", datetime.now(timezone.utc).isoformat())
                yield _sse("dream.done", result)
            elif kind == "error":
                yield _sse("dream.error", {"message": ev.get("message", "unknown error")})
                return
            else:
                yield _sse("dream.progress", ev)
    except ValueError as e:
        yield _sse("dream.error", {"message": str(e)})
    except RuntimeError as e:
        yield _sse("dream.error", {"message": str(e)})
    except Exception as e:
        yield _sse("dream.error", {"message": f"dream stream failed: {e}"})


async def stream_dream_preview(book_slug: str, tier_id: str) -> AsyncIterator[str]:
    for chunk in _iter_dream_events(book_slug, tier_id, apply=False):
        yield chunk


async def stream_dream_apply(book_slug: str, tier_id: str) -> AsyncIterator[str]:
    for chunk in _iter_dream_events(book_slug, tier_id, apply=True):
        yield chunk


def dream_catalog(book_slug: str) -> dict:
    data = _run_dream(book_slug, "")
    data["supported"] = True
    data.setdefault("bookSlug", book_slug)
    return data


def preview_dream_tier(book_slug: str, tier_id: str) -> dict:
    data = _run_dream(book_slug, f'--tier "{tier_id}"')
    data.setdefault("bookSlug", book_slug)
    return data


def apply_dream_tier(book_slug: str, tier_id: str) -> dict:
    data = _run_dream(book_slug, f'--tier "{tier_id}" --apply')
    data.setdefault("bookSlug", book_slug)
    return data
