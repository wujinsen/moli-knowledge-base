from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .subprocess_util import run_shell


@dataclass
class ScriptResult:
    command: str
    returncode: int
    stdout: str
    stderr: str


@dataclass
class PostApplyResult:
    ok: bool
    results: list[ScriptResult] = field(default_factory=list)
    error: str | None = None


def run_post_apply(root: Path, scripts: list[str], *, dry_run: bool = False) -> PostApplyResult:
    if not scripts:
        return PostApplyResult(ok=True)

    results: list[ScriptResult] = []
    for cmd in scripts:
        if dry_run:
            results.append(ScriptResult(command=cmd, returncode=0, stdout="(dry-run)", stderr=""))
            continue

        # Windows: use shell for `python scripts/...`
        proc = run_shell(cmd, cwd=root, timeout=300)
        sr = ScriptResult(
            command=cmd,
            returncode=proc.returncode,
            stdout=(proc.stdout or "")[-4000:],
            stderr=(proc.stderr or "")[-4000:],
        )
        results.append(sr)
        if proc.returncode != 0:
            return PostApplyResult(
                ok=False,
                results=results,
                error=f"script failed ({proc.returncode}): {cmd}",
            )
    return PostApplyResult(ok=True, results=results)
