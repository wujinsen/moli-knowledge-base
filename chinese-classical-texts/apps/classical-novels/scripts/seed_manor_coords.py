#!/usr/bin/env python3
"""为《红楼梦》宁荣两府地图注入 manor_zone + coord（M3/M4）。

用法: python scripts/seed_manor_coords.py [--write]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC_DIR = ROOT / "src" / "content" / "locations" / "红楼梦"

# id, manor_zone, x, y
NODES: list[dict] = [
    dict(id="宁荣街", manor_zone="连接", coord=(400, 420)),
    dict(id="荣国府", manor_zone="荣府轴", coord=(280, 340)),
    dict(id="宁国府", manor_zone="宁府轴", coord=(520, 340)),
    dict(id="荣禧堂", manor_zone="荣府轴", coord=(260, 260)),
    dict(id="贾母上房", manor_zone="荣府轴", coord=(300, 200)),
    dict(id="贾政上房", manor_zone="荣府轴", coord=(220, 200)),
    dict(id="王夫人上房", manor_zone="荣府轴", coord=(340, 200)),
    dict(id="凤姐院", manor_zone="荣府侧", coord=(180, 300)),
    dict(id="梨香院", manor_zone="荣府侧", coord=(360, 300)),
    dict(id="赵姨娘房", manor_zone="荣府侧", coord=(200, 380)),
    dict(id="大观园", manor_zone="荣府侧", coord=(280, 480)),
    dict(id="夹道", manor_zone="连接", coord=(320, 460)),
    dict(id="角门", manor_zone="连接", coord=(300, 500)),
    dict(id="二门", manor_zone="连接", coord=(260, 320)),
    dict(id="仪门", manor_zone="连接", coord=(240, 280)),
    dict(id="门上", manor_zone="连接", coord=(380, 400)),
    dict(id="贾氏宗祠", manor_zone="外联", coord=(160, 180)),
    dict(id="会芳园", manor_zone="宁府园", coord=(540, 260)),
    dict(id="天香楼", manor_zone="宁府园", coord=(560, 200)),
    dict(id="尤氏上房", manor_zone="宁府轴", coord=(500, 200)),
    dict(id="可卿上房", manor_zone="宁府轴", coord=(540, 300)),
    dict(id="家塾", manor_zone="外联", coord=(140, 300)),
    dict(id="荣庆堂", manor_zone="荣府轴", coord=(280, 240)),
    dict(id="穿堂", manor_zone="连接", coord=(270, 220)),
    dict(id="邢夫人上房", manor_zone="宁府轴", coord=(480, 240)),
    dict(id="东角门", manor_zone="连接", coord=(400, 320)),
]


def upsert_scalar(raw: str, key: str, value: str, *, before: tuple[str, ...] = ()) -> str:
    line = f"{key}: {value}"
    if re.search(rf"^{re.escape(key)}:", raw, re.M):
        return re.sub(rf"^{re.escape(key)}:.*$", line, raw, count=1, flags=re.M)
    for anchor in before:
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + line + "\n" + raw[idx:]
    return raw.rstrip() + "\n" + line + "\n"


def upsert_coord(raw: str, x: int, y: int) -> str:
    block = f"coord:\n  x: {x}\n  y: {y}\n"
    if re.search(r"^coord:", raw, re.M):
        return re.sub(r"^coord:\n(?:  .+\n)+", block, raw, count=1, flags=re.M)
    for anchor in ("manor_zone:", "garden_zone:", "summary:", "tags:", "appear_in:"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + block + raw[idx:]
    return raw.rstrip() + "\n" + block


def strip_body_orphans(body: str) -> str:
    """Remove coord/manor_zone blocks mistakenly appended after frontmatter."""
    body = re.sub(r"^coord:\n(?:  .+\n)+", "", body, count=1, flags=re.M)
    body = re.sub(r"^manor_zone:.*\n?", "", body, count=1, flags=re.M)
    return body.rstrip() + "\n"


def patch_file(path: Path, spec: dict, *, write: bool) -> bool:
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    fm = parts[1]
    body = strip_body_orphans(parts[2])
    cx, cy = spec["coord"]
    new_fm = upsert_scalar(
        fm, "manor_zone", spec["manor_zone"], before=("summary:", "tags:", "appear_in:")
    )
    new_fm = upsert_coord(new_fm, cx, cy)
    if new_fm == fm and body == parts[2]:
        return False
    if write:
        path.write_text(f"---{new_fm}---\n\n{body.lstrip()}", encoding="utf-8")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"seed_manor_coords [{mode}] · {len(NODES)} nodes\n")

    n = 0
    for spec in NODES:
        path = LOC_DIR / f"{spec['id']}.md"
        if not path.exists():
            print(f"  SKIP missing: {spec['id']}")
            continue
        if patch_file(path, spec, write=args.write):
            n += 1
            print(f"  {'patched' if args.write else 'would patch'}: {spec['id']} ({spec['manor_zone']})")

    print(f"\n{'Patched' if args.write else 'Would patch'}: {n}/{len(NODES)}")
    if not args.write:
        print("（加 --write 写回）")


if __name__ == "__main__":
    main()
