#!/usr/bin/env python3
"""生成 variants/红楼梦/*.md — 脂砚斋本 ↔ 程高本对勘锚点。"""
from __future__ import annotations

import json
from pathlib import Path

from _common import CONTENT, DATA_DIR, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
VARIANTS_DIR = CONTENT / "variants" / "红楼梦"
CHAPTERS = CONTENT / "chapters" / "红楼梦"
TOPICS_JSON = DATA_DIR / "honglou.variant-topics.json"
EDITION_A = "脂砚斋本"
EDITION_B = "程高本"


def yaml_quote(s: str) -> str:
    if not s:
        return '""'
    if any(c in s for c in ':"\'\n#'):
        return json.dumps(s, ensure_ascii=False)
    return s


def write_variant(
    vid: str,
    chapter: int,
    category: str,
    summary: str,
    *,
    text_a: str | None = None,
    text_b: str | None = None,
    note: str | None = None,
    topic_id: str | None = None,
    tags: list[str] | None = None,
) -> None:
    lines = [
        "---",
        f"id: {vid}",
        "type: variant",
        "book: 红楼梦",
        f"chapter: {chapter}",
        f"category: {category}",
        f"edition_a: {EDITION_A}",
        f"edition_b: {EDITION_B}",
    ]
    if text_a is not None:
        lines.append(f"text_a: {yaml_quote(text_a)}")
    if text_b is not None:
        lines.append(f"text_b: {yaml_quote(text_b)}")
    if note:
        lines.append(f"note: {yaml_quote(note)}")
    if topic_id:
        lines.append(f"topic_id: {topic_id}")
    lines.append(f"tags: {tags or []}")
    lines.append(f"summary: {yaml_quote(summary)}")
    lines.append("---")
    lines.append("")
    (VARIANTS_DIR / f"{vid}.md").write_text("\n".join(lines), encoding="utf-8")


def scan_title_diffs() -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    for n in range(1, 81):
        z_path = CHAPTERS / "脂砚斋本" / f"{n:03d}.md"
        c_path = CHAPTERS / f"{n:03d}.md"
        if not z_path.exists() or not c_path.exists():
            continue
        fz, _ = parse_frontmatter(z_path)
        fc, _ = parse_frontmatter(c_path)
        tz = (fz.get("title") or "").strip()
        tc = (fc.get("title") or "").strip()
        if tz and tc and tz != tc:
            rows.append((n, tz, tc))
    return rows


def main() -> None:
    VARIANTS_DIR.mkdir(parents=True, exist_ok=True)
    for old in VARIANTS_DIR.glob("hlm-v-*.md"):
        old.unlink()

    seq = 1
    variants: list[str] = []

    write_variant(
        f"hlm-v-{seq:03d}",
        1,
        "批语",
        "脂本含戚蓼生序、甲戌凡例与侧批/眉批；程高本删净批语，开篇直入作者自云。",
        text_a="甲戌侧批",
        note="双栏对勘时左栏可见 zhipi 批语层，右栏为净文。",
        tags=["脂批"],
    )
    variants.append(f"hlm-v-{seq:03d}")
    seq += 1

    for n, tz, tc in scan_title_diffs():
        write_variant(
            f"hlm-v-{seq:03d}",
            n,
            "回目",
            f"第{n}回回目异字（脂↔程）。",
            text_a=tz,
            text_b=tc,
        )
        variants.append(f"hlm-v-{seq:03d}")
        seq += 1

    topics = json.loads(TOPICS_JSON.read_text(encoding="utf-8")).get("topics") or []
    for t in topics:
        tid = t["id"]
        ch = int(t["chapter"])
        write_variant(
            f"hlm-v-{seq:03d}",
            ch,
            "情节",
            t.get("summary", tid),
            topic_id=tid,
            tags=["续书", "探佚"] if ch > 80 else ["版本议题"],
        )
        variants.append(f"hlm-v-{seq:03d}")
        seq += 1

    print(f"seed_honglou_compare: {len(variants)} variants → {VARIANTS_DIR}")


if __name__ == "__main__":
    main()
