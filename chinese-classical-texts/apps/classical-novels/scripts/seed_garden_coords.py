#!/usr/bin/env python3
"""为《红楼梦》大观园 M0 游线节点注入 coord / garden_zone / tour_order。

坐标与分区属 inference（南北中轴说），页内须标注非定稿地图。
可重复运行：覆盖已有同名字段。

用法: python scripts/seed_garden_coords.py [--write]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC_DIR = ROOT / "src" / "content" / "locations" / "红楼梦"

# id, garden_zone, (x, y), tour_order（第17回贾政游园 fact 序）
NODES: list[dict] = [
    dict(id="曲径通幽", garden_zone="路径", coord=(400, 540), tour_order=2),
    dict(id="沁芳亭", garden_zone="水系", coord=(400, 220), tour_order=3),
    dict(id="潇湘馆", garden_zone="居所", coord=(160, 280), tour_order=4),
    dict(id="稻香村", garden_zone="居所", coord=(260, 130), tour_order=5),
    dict(id="蓼溆", garden_zone="水系", coord=(560, 260), tour_order=7),
    dict(id="蘅芜苑", garden_zone="居所", coord=(640, 300), tour_order=8),
    dict(id="省亲别墅", garden_zone="仪典", coord=(400, 90), tour_order=9),
    dict(id="沁芳闸", garden_zone="水系", coord=(400, 340), tour_order=10),
    dict(id="怡红院", garden_zone="居所", coord=(400, 460), tour_order=11),
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
    if re.search(r"^coord:", raw, re.M):
        return re.sub(
            r"^coord:\n(?:  .+\n)+",
            f"coord:\n  x: {x}\n  y: {y}\n",
            raw,
            count=1,
            flags=re.M,
        )
    block = f"coord:\n  x: {x}\n  y: {y}\n"
    for anchor in ("garden_zone:", "map_zone:", "summary:", "tags:", "appear_in:"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + block + raw[idx:]
    return raw.rstrip() + "\n" + block


def patch_file(path: Path, spec: dict, *, write: bool) -> bool:
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    fm = parts[1]
    cx, cy = spec["coord"]
    new_fm = upsert_scalar(fm, "garden_zone", spec["garden_zone"], before=("summary:", "tags:", "appear_in:"))
    new_fm = upsert_scalar(
        new_fm,
        "tour_order",
        str(spec["tour_order"]),
        before=("summary:", "tags:", "appear_in:", "garden_zone:"),
    )
    new_fm = upsert_coord(new_fm, cx, cy)
    if new_fm == fm:
        return False
    if write:
        path.write_text(f"---{new_fm}---{parts[2]}", encoding="utf-8")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"seed_garden_coords [{mode}]\n")

    n = 0
    for spec in NODES:
        path = LOC_DIR / f"{spec['id']}.md"
        if not path.exists():
            print(f"  SKIP missing: {spec['id']}")
            continue
        if patch_file(path, spec, write=args.write):
            n += 1
            print(f"  {'patched' if args.write else 'would patch'}: {spec['id']}")

    print(f"\n{'Patched' if args.write else 'Would patch'}: {n}/{len(NODES)}")
    if not args.write:
        print("（加 --write 写回）")


if __name__ == "__main__":
    main()
