from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone

from .config import NOVELS_ROOT


class DreamRunError(Exception):
    pass


UNSUPPORTED = {"jinpingmei", "xiyouji"}


def _run_dream(args: str) -> dict:
    cmd = f"python scripts/dream_report.py {args} --json"
    proc = subprocess.run(
        cmd,
        cwd=NOVELS_ROOT,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=360,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-2500:]
        raise DreamRunError(err or f"dream_report exited {proc.returncode}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise DreamRunError(f"invalid JSON from dream_report: {e}") from e

    data.setdefault("generatedAt", datetime.now(timezone.utc).isoformat())
    return data


def dream_catalog(book_slug: str) -> dict:
    if book_slug in UNSUPPORTED:
        return {
            "bookSlug": book_slug,
            "supported": False,
            "message": "当前仅红楼梦 honglou 支持 /dream tier 压平批次",
            "tiers": [],
        }
    if book_slug != "honglou":
        raise ValueError(f"unknown book slug: {book_slug}")

    data = _run_dream("")
    data["supported"] = True
    data.setdefault("bookSlug", book_slug)
    return data


def preview_dream_tier(book_slug: str, tier_id: str) -> dict:
    if book_slug != "honglou":
        raise ValueError("dream tier preview only available for honglou")
    data = _run_dream(f'--tier "{tier_id}"')
    data.setdefault("bookSlug", book_slug)
    return data


def apply_dream_tier(book_slug: str, tier_id: str) -> dict:
    if book_slug != "honglou":
        raise ValueError("dream tier apply only available for honglou")
    data = _run_dream(f'--tier "{tier_id}" --apply')
    data.setdefault("bookSlug", book_slug)
    return data
