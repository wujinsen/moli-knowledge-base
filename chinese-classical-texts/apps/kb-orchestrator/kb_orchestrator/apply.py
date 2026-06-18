from __future__ import annotations

import os
import uuid
from pathlib import Path

from .config import NOVELS_ROOT
from .jobs import run_post_apply
from .log_util import append_studio_log
from .patch import PatchError, apply_proposal_patches


def _dry_run() -> bool:
    return os.environ.get("STUDIO_DRY_RUN", "").lower() in ("1", "true", "yes")


def execute_apply(
    *,
    book: str,
    proposal: dict,
    patch_paths: list[str] | None,
    skip_post_apply: bool,
) -> dict:
    patches = proposal.get("patches") or []
    if not patches:
        raise PatchError("proposal has no patches")

    only = set(patch_paths) if patch_paths else None
    dry = _dry_run()

    if dry:
        paths = [p["path"] for p in patches if not only or p["path"] in only]
        return {
            "jobId": f"job_{uuid.uuid4().hex[:12]}",
            "status": "completed",
            "dryRun": True,
            "appliedPaths": paths,
            "logAppended": False,
            "postApply": {"ok": True, "skipped": skip_post_apply},
            "message": "STUDIO_DRY_RUN=1：未写盘",
        }

    applied, errors = apply_proposal_patches(NOVELS_ROOT, patches, only)
    if errors:
        raise PatchError(
            "; ".join(f"{e['path']}: {e['error']}" for e in errors)
        )

    log_appended = False
    post = proposal.get("postApply") or {}
    log_entry = post.get("logEntry")

    if log_entry:
        append_studio_log(NOVELS_ROOT, book, log_entry)
        log_appended = True

    post_result = {"ok": True, "skipped": skip_post_apply, "scripts": []}
    if not skip_post_apply:
        scripts = post.get("scripts") or []
        pa = run_post_apply(NOVELS_ROOT, scripts)
        post_result = {
            "ok": pa.ok,
            "skipped": False,
            "error": pa.error,
            "scripts": [
                {
                    "command": r.command,
                    "returncode": r.returncode,
                    "stdoutTail": r.stdout[-800:] if r.stdout else "",
                    "stderrTail": r.stderr[-800:] if r.stderr else "",
                }
                for r in pa.results
            ],
        }
        if not pa.ok:
            return {
                "jobId": f"job_{uuid.uuid4().hex[:12]}",
                "status": "failed",
                "appliedPaths": applied,
                "logAppended": log_appended,
                "postApply": post_result,
                "message": f"补丁已写入，但 postApply 失败：{pa.error}",
            }

    status = "partially_applied" if only and len(applied) < len(patches) else "applied"
    return {
        "jobId": f"job_{uuid.uuid4().hex[:12]}",
        "status": status,
        "appliedPaths": applied,
        "logAppended": log_appended,
        "postApply": post_result,
        "refreshHints": post.get("refreshHints"),
        "message": "已写盘并完成 postApply" if post_result.get("ok") else "已写盘",
    }
