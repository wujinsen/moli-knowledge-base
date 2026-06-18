#!/usr/bin/env python3
"""/dream tier 批次 — JSON 预览 / 应用（红楼梦密度压平）。

用法:
  python scripts/dream_report.py --json                    # 梯队目录 + 当前分带
  python scripts/dream_report.py --json --tier tier14      # tier14 dry-run 预览
  python scripts/dream_report.py --json --tier tier14 --apply  # 写盘 + postApply
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lint_character_density import collect_density, density_score
from patch_hlm_tier10_score22 import scan_pages

BOOK = "红楼梦"
BOOK_SLUG = "honglou"

# 从新到旧；Studio 默认推荐 candidateCount>0 的第一项
HLM_TIERS: list[dict] = [
    {
        "id": "tier14",
        "label": "第十四梯队",
        "module": "patch_hlm_tier14_score29",
        "script": "patch_hlm_tier14_score29.py",
        "thinLabel": "score=28",
        "goal": "≥29",
        "postApply": [
            "python scripts/build_relations.py 红楼梦",
            "python scripts/build_hlm_tier14_link_topic.py",
        ],
    },
    {
        "id": "tier13",
        "label": "第十三梯队",
        "module": "patch_hlm_tier13_score28",
        "script": "patch_hlm_tier13_score28.py",
        "thinLabel": "score=27",
        "goal": "≥28",
        "postApply": [
            "python scripts/build_relations.py 红楼梦",
            "python scripts/build_hlm_tier13_link_topic.py",
        ],
    },
    {
        "id": "tier12b",
        "label": "第十二梯队 · score27",
        "module": "patch_hlm_tier12_score27",
        "script": "patch_hlm_tier12_score27.py",
        "thinLabel": "score=26",
        "goal": "≥27",
        "postApply": [
            "python scripts/build_relations.py 红楼梦",
            "python scripts/build_hlm_tier12_link_topic.py",
        ],
    },
    {
        "id": "tier12a",
        "label": "第十二梯队 · score26",
        "module": "patch_hlm_tier12_score26",
        "script": "patch_hlm_tier12_score26.py",
        "thinLabel": "score=25–26",
        "goal": "抬升",
        "postApply": ["python scripts/build_relations.py 红楼梦"],
    },
    {
        "id": "tier11",
        "label": "第十一梯队",
        "module": "patch_hlm_tier11_score25",
        "script": "patch_hlm_tier11_score25.py",
        "thinLabel": "score=24–25",
        "goal": "≥26",
        "postApply": ["python scripts/build_relations.py 红楼梦"],
    },
    {
        "id": "tier10",
        "label": "第十梯队",
        "module": "patch_hlm_tier10_score22",
        "script": "patch_hlm_tier10_score22.py",
        "thinLabel": "score≤22",
        "goal": "≥23",
        "postApply": ["python scripts/build_relations.py 红楼梦"],
        "subprocessOnly": True,
    },
]


def _page_score(info: dict) -> int:
    return density_score({k: info[k] for k in ("rel", "plot", "main", "review", "inbound")})


def _thin_match(mod, score: int) -> bool:
    if hasattr(mod, "THIN_SCORE"):
        return score == mod.THIN_SCORE
    if hasattr(mod, "THIN_SCORES"):
        return score in mod.THIN_SCORES
    return False


def _tier_candidate_count(tier: dict) -> int:
    pages, _inbound = scan_pages()
    if tier.get("subprocessOnly"):
        c = Counter(_page_score(info) for info in pages.values())
        return c.get(21, 0) + c.get(22, 0)
    mod = importlib.import_module(tier["module"])
    return sum(1 for info in pages.values() if _thin_match(mod, _page_score(info)))


def build_catalog() -> dict:
    density = collect_density(BOOK)
    tiers = []
    recommended: str | None = None
    for t in HLM_TIERS:
        count = _tier_candidate_count(t)
        entry = {
            "id": t["id"],
            "label": t["label"],
            "thinLabel": t["thinLabel"],
            "goal": t["goal"],
            "candidateCount": count,
            "script": t["script"],
            "postApply": t.get("postApply", []),
        }
        tiers.append(entry)
        if recommended is None and count > 0:
            recommended = t["id"]

    return {
        "book": BOOK,
        "bookSlug": BOOK_SLUG,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scoreDistribution": density["scoreDistribution"],
        "totalCharacters": density["totalCharacters"],
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


def preview_tier(tier_id: str) -> dict:
    tier = next((t for t in HLM_TIERS if t["id"] == tier_id), None)
    if not tier:
        raise ValueError(f"unknown tier: {tier_id}")

    if tier.get("subprocessOnly"):
        return _preview_subprocess_tier(tier)

    mod = importlib.import_module(tier["module"])
    pages, inbound = mod.scan_pages()
    all_fms = {cid: (info["path"], info["fm"], info["body"]) for cid, info in pages.items()}
    chapter_cache: dict[int, str | None] = {}

    candidates = [cid for cid, info in pages.items() if _thin_match(mod, _page_score(info))]
    order = sorted(
        candidates,
        key=lambda c: (_page_score(pages[c]), pages[c]["inbound"], c),
    )

    changes: list[dict] = []
    stuck: list[dict] = []
    for cid in order:
        if not _thin_match(mod, _page_score(pages[cid])):
            continue
        result = mod.patch_one(cid, pages, inbound, all_fms, chapter_cache, True)
        if result:
            changes.append(
                {
                    "summary": result,
                    "characterId": _extract_character_id(result),
                }
            )
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
        "book": BOOK,
        "bookSlug": BOOK_SLUG,
        "tierId": tier_id,
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


def _preview_subprocess_tier(tier: dict) -> dict:
    cmd = f'python scripts/{tier["script"]} --dry-run'
    proc = subprocess.run(
        cmd,
        cwd=Path(__file__).resolve().parents[1],
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "")[-2000:])

    changes: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("patched ") or line.startswith("WARN"):
            continue
        if line:
            changes.append({"summary": line, "characterId": _extract_character_id(line)})

    pages, _ = scan_pages()
    c = Counter(_page_score(info) for info in pages.values())
    candidates = c.get(21, 0) + c.get(22, 0)

    return {
        "book": BOOK,
        "bookSlug": BOOK_SLUG,
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


def apply_tier(tier_id: str, *, novels_root: Path | None = None) -> dict:
    tier = next((t for t in HLM_TIERS if t["id"] == tier_id), None)
    if not tier:
        raise ValueError(f"unknown tier: {tier_id}")

    root = novels_root or Path(__file__).resolve().parents[1]
    cmd = f'python scripts/{tier["script"]}'
    proc = subprocess.run(
        cmd,
        cwd=root,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
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
            errors="replace",
            timeout=300,
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

    preview = preview_tier(tier_id)
    preview["preview"] = False
    preview["applied"] = True
    preview["patchCount"] = patch_count
    preview["stdoutTail"] = proc.stdout[-3000:]
    preview["postApplyResults"] = post_results
    return preview


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tier", default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if args.tier:
        data = apply_tier(args.tier) if args.apply else preview_tier(args.tier)
    else:
        data = build_catalog()

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if args.tier:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"tiers: {len(data['tiers'])} recommended={data['recommendedTierId']}")


if __name__ == "__main__":
    main()
