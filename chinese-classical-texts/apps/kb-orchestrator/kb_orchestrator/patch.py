from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


class PatchError(Exception):
    pass


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str]


def _parse_hunks(diff: str) -> list[Hunk]:
    hunks: list[Hunk] = []
    current: Hunk | None = None
    for raw in diff.splitlines():
        if raw.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", raw)
            if not m:
                raise PatchError(f"bad hunk header: {raw}")
            current = Hunk(
                old_start=int(m.group(1)),
                old_count=int(m.group(2) or 1),
                new_start=int(m.group(3)),
                new_count=int(m.group(4) or 1),
                lines=[],
            )
            hunks.append(current)
            continue
        if current is not None and (raw.startswith(" ") or raw.startswith("+") or raw.startswith("-")):
            current.lines.append(raw)
    return hunks


def _apply_hunks(lines: list[str], hunks: list[Hunk]) -> list[str]:
    out = lines[:]
    offset = 0
    for hunk in hunks:
        idx = hunk.old_start - 1 + offset
        if idx < 0 or idx > len(out):
            raise PatchError(f"hunk out of range at line {hunk.old_start}")

        pos = idx
        new_segment: list[str] = []
        for hl in hunk.lines:
            tag, content = hl[0], hl[1:]
            if tag == " ":
                if pos >= len(out) or out[pos] != content:
                    got = out[pos] if pos < len(out) else "<eof>"
                    raise PatchError(
                        f"context mismatch at line {pos + 1}: expected {content!r}, got {got!r}"
                    )
                new_segment.append(content)
                pos += 1
            elif tag == "-":
                if pos >= len(out) or out[pos] != content:
                    got = out[pos] if pos < len(out) else "<eof>"
                    raise PatchError(
                        f"delete mismatch at line {pos + 1}: expected {content!r}, got {got!r}"
                    )
                pos += 1
            elif tag == "+":
                new_segment.append(content)
            else:
                raise PatchError(f"bad hunk line: {hl!r}")

        consumed = pos - idx
        expected = sum(1 for hl in hunk.lines if hl[0] in " -")
        if consumed != expected:
            raise PatchError(f"hunk consumed {consumed} lines, expected {expected}")

        out[idx:pos] = new_segment
        offset += len(new_segment) - consumed
    return out


def validate_rel_path(rel_path: str) -> None:
    if ".." in rel_path.replace("\\", "/"):
        raise PatchError(f"path traversal blocked: {rel_path}")
    norm = rel_path.replace("\\", "/")
    if not (norm.startswith("src/content/") or norm.startswith("src/data/")):
        raise PatchError(f"path not allowed: {rel_path}")


def apply_file_patch(root: Path, rel_path: str, operation: str, diff: str) -> None:
    validate_rel_path(rel_path)
    _assert_chapter_body_safe(rel_path, diff)
    target = root / rel_path.replace("/", "\\") if "\\" in str(root) else root / rel_path

    if operation == "create":
        # create: diff should be full content after +++ only lines starting with +
        lines = [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return

    if not target.exists():
        raise PatchError(f"file not found: {rel_path}")

    text = target.read_text(encoding="utf-8-sig")
    had_trailing_nl = text.endswith("\n")
    lines = text.splitlines()

    hunks = _parse_hunks(diff)
    if not hunks:
        raise PatchError("empty diff")

    # Try git apply first (more tolerant on some platforms)
    if _try_git_apply(root, diff):
        return

    new_lines = _apply_hunks(lines, hunks)
    new_text = "\n".join(new_lines)
    if had_trailing_nl or text.endswith("\n"):
        new_text += "\n"
    target.write_text(new_text, encoding="utf-8")


def _try_git_apply(root: Path, diff: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "apply", "--unsafe-paths", "-"],
            cwd=root,
            input=diff.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def apply_proposal_patches(
    root: Path,
    patches: list[dict],
    only_paths: set[str] | None = None,
) -> tuple[list[str], list[dict]]:
    applied: list[str] = []
    errors: list[dict] = []
    for p in patches:
        path = p.get("path") or ""
        if only_paths is not None and path not in only_paths:
            continue
        try:
            apply_file_patch(root, path, p.get("operation") or "update", p.get("diff") or "")
            applied.append(path)
        except PatchError as e:
            errors.append({"path": path, "error": str(e)})
    return applied, errors


def _assert_chapter_body_safe(rel_path: str, diff: str) -> None:
    norm = rel_path.replace("\\", "/")
    if "/chapters/" not in norm:
        return
    for raw in diff.splitlines():
        if not raw or raw.startswith("@@") or raw.startswith("---") or raw.startswith("+++"):
            continue
        if raw[0] not in "+-":
            continue
        content = raw[1:].strip()
        if content.startswith("<") or content.startswith("</"):
            raise PatchError("chapters/ body is read-only (HTML); only edit YAML frontmatter")


def preview_file_patch(root: Path, rel_path: str, operation: str, diff: str) -> None:
    """Validate patch applies without writing."""
    validate_rel_path(rel_path)
    _assert_chapter_body_safe(rel_path, diff)
    target = root / rel_path.replace("/", "\\") if "\\" in str(root) else root / rel_path

    if operation == "create":
        lines = [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
        if not lines:
            raise PatchError("create diff has no + lines")
        return

    if not target.exists():
        raise PatchError(f"file not found: {rel_path}")

    text = target.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    hunks = _parse_hunks(diff)
    if not hunks:
        raise PatchError("empty diff")
    _apply_hunks(lines, hunks)
