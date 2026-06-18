"""Run classical-novels Python scripts with UTF-8 stdout on Windows."""
from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path


def utf8_env() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
    }


def run_shell(
    cmd: str,
    *,
    cwd: Path,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command; decode child stdout/stderr as UTF-8."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=timeout,
        env=utf8_env(),
    )


def iter_shell(
    cmd: str,
    *,
    cwd: Path,
    timeout: int = 600,
) -> Iterator[str]:
    """Stream merged stdout/stderr lines until the process exits."""
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=utf8_env(),
    )
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            yield line.rstrip("\n\r")
    finally:
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise RuntimeError(f"command timed out after {timeout}s: {cmd}") from None
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {cmd}")
