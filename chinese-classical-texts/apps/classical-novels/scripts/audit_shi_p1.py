#!/usr/bin/env python3
"""Audit 诗词意象 P1: judgment/tune → character inference edges."""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "src/content/imagery/红楼梦"
LINKS = ROOT / "src/data/红楼梦.imagery-links.json"
CHAR_DIR = ROOT / "src/content/characters/红楼梦"

INF_PRED = {"隐喻", "预示", "象征", "影射"}
# 总收/开篇母题曲：人物边分散在 imagery-links.json 互文链，frontmatter 不要求逐人 inference
EXEMPT_POEMS = {"hl-p-07"}


def parse_fm(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    return yaml.safe_load(m.group(1)) if m else {}


def main() -> None:
    items = [parse_fm(p.read_text(encoding="utf-8")) for p in sorted(IMG_DIR.glob("*.md"))]
    items = [i for i in items if i.get("id")]
    char_names = {
        parse_fm(p.read_text(encoding="utf-8")).get("name")
        for p in CHAR_DIR.glob("*.md")
    }
    char_names.discard(None)
    extra = json.loads(LINKS.read_text(encoding="utf-8"))["links"]

    judgments = [i for i in items if i.get("subtype") == "judgment"]
    poems = [i for i in items if i.get("subtype") == "poem"]

    print("=== Judgments without inference char link (frontmatter) ===")
    for j in judgments:
        inf = [
            l
            for l in j.get("links", [])
            if l.get("inference")
            and l.get("target_kind", "character") == "character"
            and l.get("predicate") in INF_PRED
        ]
        if not inf:
            preds = [l.get("predicate") for l in j.get("links", [])]
            print(f"  {j['id']} {j['title']}: {preds}")

    print("\n=== Poems without inference char link (frontmatter) ===")
    skip = {"hl-p-02"} | EXEMPT_POEMS
    missing = []
    for p in poems:
        if p["id"] in skip:
            continue
        inf = [
            l
            for l in p.get("links", [])
            if l.get("inference") and l.get("target_kind", "character") == "character"
        ]
        if not inf:
            preds = [l.get("predicate") for l in p.get("links", [])]
            missing.append(f"  {p['id']} {p['title']}: {preds}")
            print(f"  {p['id']} {p['title']}: {preds}")

    if missing:
        raise SystemExit(f"P1 audit failed: {len(missing)} poem(s) missing inference char links")
    print("P1 audit OK")

    print("\n=== hl-p/hl-j in extra JSON → char without inference ===")
    for l in extra:
        src, tgt = l["source"], l["target"]
        if (src.startswith("hl-j-") or src.startswith("hl-p-")) and tgt in char_names:
            if not l.get("inference") and l.get("predicate") not in ("作", "对应判词"):
                print(f"  {src} → {tgt} ({l.get('predicate')})")

    print("\n=== hl-p/hl-j in extra JSON missing any char edge ===")
    poem_ids = {p["id"] for p in poems}
    judge_ids = {j["id"] for j in judgments}
    for pid in sorted(poem_ids | judge_ids):
        fm = next(i for i in items if i["id"] == pid)
        chars = set(fm.get("characters", []))
        extra_chars = {
            l["target"]
            for l in extra
            if l["source"] == pid
            and l["target"] in char_names
            and l.get("predicate") in INF_PRED | {"作", "对应判词", "互文"}
        }
        fm_inf = {
            l["target"]
            for l in fm.get("links", [])
            if l.get("target_kind", "character") == "character"
        }
        if not chars and not extra_chars and not fm_inf:
            print(f"  {pid} NO CHAR LINKS")


if __name__ == "__main__":
    main()
