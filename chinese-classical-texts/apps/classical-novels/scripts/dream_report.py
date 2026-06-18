#!/usr/bin/env python3
"""/dream tier 批次 — JSON 预览 / 应用（三书）。

用法:
  python scripts/dream_report.py --book-slug honglou --json
  python scripts/dream_report.py --book-slug xiyouji --json --tier weak_inbound
  python scripts/dream_report.py --book-slug jinpingmei --json --tier weak_inbound --apply
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dream_patch_common import page_score, scan_pages  # noqa: E402
from dream_tiers import resolve_book  # noqa: E402
from lint_character_density import collect_density, density_score  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _page_score(info: dict) -> int:
    return density_score({k: info[k] for k in ("rel", "plot", "main", "review", "inbound")})


def _thin_match(mod, score: int) -> bool:
    if hasattr(mod, "THIN_SCORE"):
        return score == mod.THIN_SCORE
    if hasattr(mod, "THIN_SCORES"):
        return score in mod.THIN_SCORES
    if hasattr(mod, "THIN_MAX"):
        return score <= mod.THIN_MAX
    return False


def _tier_candidate_count(book: str, tier: dict) -> int:
    mode = tier.get("candidateMode", "module")
    params = tier.get("candidateParams") or {}

    if mode == "weak_inbound":
        max_in = int(params.get("maxInbound", 1))
        pages, _ = scan_pages(book)
        return sum(1 for info in pages.values() if info["inbound"] <= max_in)

    if mode == "skeleton":
        pages, _ = scan_pages(book)
        return sum(1 for info in pages.values() if not info["main"] or not info["review"])

    if mode == "low_score":
        thin = int(params.get("thinMax", 16))
        pages, _ = scan_pages(book)
        return sum(1 for info in pages.values() if page_score(info) <= thin)

    if mode == "subprocess_score":
        from patch_hlm_tier10_score22 import scan_pages as hlm_scan

        pages, _ = hlm_scan()
        c = Counter(_page_score(info) for info in pages.values())
        return c.get(21, 0) + c.get(22, 0)

    if tier.get("module"):
        mod = importlib.import_module(tier["module"])
        pages, _inbound = mod.scan_pages()
        return sum(1 for info in pages.values() if _thin_match(mod, _page_score(info)))

    return 0


def build_catalog(book_slug: str) -> dict:
    book, tiers_cfg = resolve_book(book_slug)
    density = collect_density(book)
    tiers = []
    recommended: str | None = None
    for t in tiers_cfg:
        count = _tier_candidate_count(book, t)
        entry = {
            "id": t["id"],
            "label": t["label"],
            "thinLabel": t["thinLabel"],
            "goal": t["goal"],
            "candidateCount": count,
            "script": t.get("script", ""),
            "postApply": t.get("postApply", []),
        }
        tiers.append(entry)
        if recommended is None and count > 0:
            recommended = t["id"]

    return {
        "book": book,
        "bookSlug": book_slug,
        "supported": True,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scoreDistribution": density["scoreDistribution"],
        "totalCharacters": density["totalCharacters"],
        "weakInboundTotal": density["weakInboundTotal"],
        "tiers": tiers,
        "recommendedTierId": recommended,
    }


def _extract_character_id(summary: str) -> str | None:
    if "→" in summary and summary.endswith(": hub"):
        return summary.split("→", 1)[1].split(":", 1)[0].strip()
    if summary.startswith(":"):
        return None
    if ": +rel" in summary:
        return summary.split(":", 1)[0].strip()
    if "→" in summary:
        return summary.split("→", 1)[0].strip()
    return summary.split(":", 1)[0].strip() or None


def _script_needs_book(tier: dict) -> bool:
    script = tier.get("script") or ""
    return script.startswith("patch_dream_") or "character_skeleton" in script


def _script_cmd(book: str, tier: dict, *, dry_run: bool) -> str:
    parts = [f'python -u -X utf8 scripts/{tier["script"]}']
    if _script_needs_book(tier):
        parts.append(f'"{book}"')
    parts.extend(tier.get("scriptArgs") or [])
    if dry_run:
        parts.append("--dry-run")
    return " ".join(parts)


def preview_tier(book_slug: str, tier_id: str) -> dict:
    book, tiers_cfg = resolve_book(book_slug)
    tier = next((t for t in tiers_cfg if t["id"] == tier_id), None)
    if not tier:
        raise ValueError(f"unknown tier: {tier_id}")

    if tier.get("subprocessOnly") or (tier.get("script") and not tier.get("module")):
        return _preview_script_tier(book, book_slug, tier)

    return _preview_module_tier(book, book_slug, tier)


def _preview_script_tier(book: str, book_slug: str, tier: dict) -> dict:
    cmd = _script_cmd(book, tier, dry_run=True)
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        timeout=360,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "")[-2000:])

    changes: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("patched ") or line.startswith("WARN") or line.startswith("remaining"):
            continue
        if line.startswith("[") and "]" in line:
            continue
        if line:
            changes.append({"summary": line, "characterId": _extract_character_id(line)})

    candidates = _tier_candidate_count(book, tier)
    return {
        "book": book,
        "bookSlug": book_slug,
        "tierId": tier["id"],
        "label": tier["label"],
        "thinLabel": tier["thinLabel"],
        "goal": tier["goal"],
        "preview": True,
        "applied": False,
        "candidateCount": candidates,
        "patchCount": len(changes),
        "stuckCount": max(0, candidates - len(changes)),
        "changes": changes[:120],
        "truncatedChanges": max(0, len(changes) - 120),
        "stuck": [],
        "truncatedStuck": 0,
        "postApply": tier.get("postApply", []),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "stdoutTail": proc.stdout[-3000:],
    }


def _preview_module_tier(book: str, book_slug: str, tier: dict) -> dict:
    mod = importlib.import_module(tier["module"])
    pages, inbound = mod.scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}

    candidates = [cid for cid, info in pages.items() if _thin_match(mod, _page_score(info))]
    order = sorted(candidates, key=lambda c: (_page_score(pages[c]), pages[c]["inbound"], c))

    changes: list[dict] = []
    stuck: list[dict] = []
    for cid in order:
        if not _thin_match(mod, _page_score(pages[cid])):
            continue
        result = mod.patch_one(cid, pages, inbound, all_fms, chapter_cache, True)
        if result:
            changes.append({"summary": result, "characterId": _extract_character_id(result)})
        else:
            d = pages[cid]
            stuck.append(
                {
                    "id": cid,
                    "score": _page_score(d),
                    "rel": d["rel"],
                    "plot": d["plot"],
                    "inbound": d["inbound"],
                }
            )

    return {
        "book": book,
        "bookSlug": book_slug,
        "tierId": tier["id"],
        "label": tier["label"],
        "thinLabel": tier["thinLabel"],
        "goal": tier["goal"],
        "preview": True,
        "applied": False,
        "candidateCount": len(candidates),
        "patchCount": len(changes),
        "stuckCount": len(stuck),
        "changes": changes[:120],
        "truncatedChanges": max(0, len(changes) - 120),
        "stuck": stuck[:60],
        "truncatedStuck": max(0, len(stuck) - 60),
        "postApply": tier.get("postApply", []),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


def apply_tier(book_slug: str, tier_id: str, *, novels_root: Path | None = None) -> dict:
    book, tiers_cfg = resolve_book(book_slug)
    tier = next((t for t in tiers_cfg if t["id"] == tier_id), None)
    if not tier:
        raise ValueError(f"unknown tier: {tier_id}")

    root = novels_root or ROOT
    if _script_needs_book(tier) or tier.get("subprocessOnly"):
        cmd = _script_cmd(book, tier, dry_run=False)
    else:
        cmd = f'python -X utf8 scripts/{tier["script"]}'

    proc = subprocess.run(
        cmd,
        cwd=root,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "")[-2000:])

    patch_match = re.search(r"patched (\d+) items", proc.stdout or "")
    patch_count = int(patch_match.group(1)) if patch_match else 0

    post_results: list[dict] = []
    for script_cmd in tier.get("postApply", []):
        p2 = subprocess.run(
            script_cmd,
            cwd=root,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
            timeout=600,
        )
        post_results.append(
            {
                "command": script_cmd,
                "returncode": p2.returncode,
                "stdoutTail": (p2.stdout or "")[-1500:],
                "stderrTail": (p2.stderr or "")[-800:],
            }
        )
        if p2.returncode != 0:
            raise RuntimeError(f"postApply failed: {script_cmd}\n{(p2.stderr or p2.stdout)[-1500:]}")

    preview = preview_tier(book_slug, tier_id)
    preview["preview"] = False
    preview["applied"] = True
    preview["patchCount"] = patch_count or preview["patchCount"]
    preview["stdoutTail"] = proc.stdout[-3000:]
    preview["postApplyResults"] = post_results
    return preview


def _utf8_env() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
    }


def _iter_shell(cmd: str, *, cwd: Path, timeout: int = 600) -> Iterator[str]:
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_utf8_env(),
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


def _is_script_noise(line: str) -> bool:
    if not line:
        return True
    if line.startswith("patched ") or line.startswith("WARN") or line.startswith("remaining"):
        return True
    return line.startswith("[") and "]" in line


def _is_change_line(line: str) -> bool:
    if _is_script_noise(line):
        return False
    if line.startswith(" "):
        return True
    return "→" in line or ": +rel" in line or ": hub" in line


def _build_preview_result(
    book: str,
    book_slug: str,
    tier: dict,
    *,
    changes: list[dict],
    stuck: list[dict],
    candidate_count: int,
    stdout_tail: str = "",
    applied: bool = False,
) -> dict:
    return {
        "book": book,
        "bookSlug": book_slug,
        "tierId": tier["id"],
        "label": tier["label"],
        "thinLabel": tier["thinLabel"],
        "goal": tier["goal"],
        "preview": not applied,
        "applied": applied,
        "candidateCount": candidate_count,
        "patchCount": len(changes),
        "stuckCount": len(stuck) if stuck else max(0, candidate_count - len(changes)),
        "changes": changes[:120],
        "truncatedChanges": max(0, len(changes) - 120),
        "stuck": stuck[:60],
        "truncatedStuck": max(0, len(stuck) - 60),
        "postApply": tier.get("postApply", []),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "stdoutTail": stdout_tail[-3000:] if stdout_tail else "",
    }


def iter_preview_tier_events(book_slug: str, tier_id: str) -> Iterator[dict]:
    book, tiers_cfg = resolve_book(book_slug)
    tier = next((t for t in tiers_cfg if t["id"] == tier_id), None)
    if not tier:
        yield {"event": "error", "message": f"unknown tier: {tier_id}"}
        return

    if tier.get("subprocessOnly") or (tier.get("script") and not tier.get("module")):
        yield from _iter_preview_script_events(book, book_slug, tier)
    else:
        yield from _iter_preview_module_events(book, book_slug, tier)


def _iter_preview_script_events(book: str, book_slug: str, tier: dict) -> Iterator[dict]:
    cmd = _script_cmd(book, tier, dry_run=True)
    candidates = _tier_candidate_count(book, tier)
    changes: list[dict] = []
    stdout_parts: list[str] = []
    line_index = 0

    yield {
        "event": "stage",
        "stage": "preview",
        "label": "dry-run 扫描",
        "step": 1,
        "total": 1,
        "command": cmd,
    }

    for raw in _iter_shell(cmd, cwd=ROOT):
        stdout_parts.append(raw)
        line = raw.strip()
        if line.startswith("patched "):
            yield {"event": "milestone", "stage": "preview", "text": line}
            continue
        if _is_script_noise(line):
            continue
        if not line:
            continue
        line_index += 1
        changes.append({"summary": line, "characterId": _extract_character_id(line)})
        yield {
            "event": "line",
            "stage": "preview",
            "index": line_index,
            "total": candidates,
            "text": line,
            "characterId": _extract_character_id(line),
        }

    result = _build_preview_result(
        book,
        book_slug,
        tier,
        changes=changes,
        stuck=[],
        candidate_count=candidates,
        stdout_tail="\n".join(stdout_parts),
    )
    yield {"event": "done", "result": result}


def _iter_preview_module_events(book: str, book_slug: str, tier: dict) -> Iterator[dict]:
    mod = importlib.import_module(tier["module"])
    pages, inbound = mod.scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}

    candidates = [cid for cid, info in pages.items() if _thin_match(mod, _page_score(info))]
    order = sorted(candidates, key=lambda c: (_page_score(pages[c]), pages[c]["inbound"], c))
    total = len(order)
    changes: list[dict] = []
    stuck: list[dict] = []

    yield {
        "event": "stage",
        "stage": "preview",
        "label": "逐页 dry-run",
        "step": 0,
        "total": total,
    }

    for step, cid in enumerate(order, 1):
        if not _thin_match(mod, _page_score(pages[cid])):
            continue
        yield {
            "event": "stage",
            "stage": "preview",
            "step": step,
            "total": total,
            "text": cid,
        }
        result = mod.patch_one(cid, pages, inbound, all_fms, chapter_cache, True)
        if result:
            changes.append({"summary": result, "characterId": _extract_character_id(result)})
            yield {
                "event": "line",
                "stage": "preview",
                "index": len(changes),
                "total": total,
                "text": result,
                "characterId": _extract_character_id(result),
            }
        else:
            d = pages[cid]
            stuck.append(
                {
                    "id": cid,
                    "score": _page_score(d),
                    "rel": d["rel"],
                    "plot": d["plot"],
                    "inbound": d["inbound"],
                }
            )

    result = _build_preview_result(
        book,
        book_slug,
        tier,
        changes=changes,
        stuck=stuck,
        candidate_count=len(candidates),
    )
    yield {"event": "done", "result": result}


def iter_apply_tier_events(
    book_slug: str,
    tier_id: str,
    *,
    novels_root: Path | None = None,
) -> Iterator[dict]:
    book, tiers_cfg = resolve_book(book_slug)
    tier = next((t for t in tiers_cfg if t["id"] == tier_id), None)
    if not tier:
        yield {"event": "error", "message": f"unknown tier: {tier_id}"}
        return

    root = novels_root or ROOT
    if _script_needs_book(tier) or tier.get("subprocessOnly"):
        cmd = _script_cmd(book, tier, dry_run=False)
    else:
        cmd = f'python -u -X utf8 scripts/{tier["script"]}'

    post_apply_cmds = tier.get("postApply", [])
    total_steps = 1 + len(post_apply_cmds) + 1
    patch_count = 0
    stdout_parts: list[str] = []
    post_results: list[dict] = []
    line_index = 0

    yield {
        "event": "stage",
        "stage": "patch",
        "label": "写盘补丁",
        "step": 1,
        "total": total_steps,
        "command": cmd,
    }

    for raw in _iter_shell(cmd, cwd=root):
        stdout_parts.append(raw)
        line = raw.strip()
        if line.startswith("patched "):
            patch_match = re.search(r"patched (\d+) items", line)
            if patch_match:
                patch_count = int(patch_match.group(1))
            yield {"event": "milestone", "stage": "patch", "text": line, "patchCount": patch_count}
            continue
        if _is_change_line(line):
            line_index += 1
            text = line.lstrip()
            yield {
                "event": "line",
                "stage": "patch",
                "index": line_index,
                "text": text,
                "characterId": _extract_character_id(text),
            }
        elif line and not _is_script_noise(line):
            yield {"event": "log", "stage": "patch", "text": line}

    for i, script_cmd in enumerate(post_apply_cmds, 1):
        yield {
            "event": "stage",
            "stage": "postApply",
            "label": f"postApply {i}/{len(post_apply_cmds)}",
            "step": 1 + i,
            "total": total_steps,
            "command": script_cmd,
        }
        step_lines: list[str] = []
        try:
            for raw in _iter_shell(script_cmd, cwd=root):
                step_lines.append(raw)
                if raw.strip():
                    yield {"event": "log", "stage": "postApply", "text": raw.strip()}
        except RuntimeError as e:
            post_results.append(
                {
                    "command": script_cmd,
                    "returncode": 1,
                    "stdoutTail": "\n".join(step_lines)[-1500:],
                    "stderrTail": str(e)[-800:],
                }
            )
            yield {"event": "error", "message": f"postApply failed: {script_cmd}\n{e}"}
            return

        post_results.append(
            {
                "command": script_cmd,
                "returncode": 0,
                "stdoutTail": "\n".join(step_lines)[-1500:],
                "stderrTail": "",
            }
        )

    yield {
        "event": "stage",
        "stage": "refresh",
        "label": "重新生成预览",
        "step": total_steps,
        "total": total_steps,
    }

    preview_result: dict | None = None
    for ev in iter_preview_tier_events(book_slug, tier_id):
        if ev.get("event") == "done":
            preview_result = ev["result"]
        elif ev.get("event") != "stage" or ev.get("step", 0) != 0:
            yield ev

    if not preview_result:
        yield {"event": "error", "message": "preview refresh produced no result"}
        return

    preview_result["preview"] = False
    preview_result["applied"] = True
    preview_result["patchCount"] = patch_count or preview_result["patchCount"]
    preview_result["stdoutTail"] = "\n".join(stdout_parts)[-3000:]
    preview_result["postApplyResults"] = post_results
    yield {"event": "done", "result": preview_result}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-slug", default="honglou")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tier", default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.tier:
        data = apply_tier(args.book_slug, args.tier) if args.apply else preview_tier(args.book_slug, args.tier)
    else:
        data = build_catalog(args.book_slug)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if args.tier:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"tiers: {len(data['tiers'])} recommended={data['recommendedTierId']}")


if __name__ == "__main__":
    main()
