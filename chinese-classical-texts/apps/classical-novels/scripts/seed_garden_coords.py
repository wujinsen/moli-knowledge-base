#!/usr/bin/env python3
"""为《红楼梦》大观园地图注入 coord / garden_zone / tour_order。

M0：第17回游线 9 节点（含 tour_order）
M2：全园 33 子地点（inference 坐标，南北中轴说）

用法: python scripts/seed_garden_coords.py [--write]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC_DIR = ROOT / "src" / "content" / "locations" / "红楼梦"

# id, garden_zone, x, y, tour_order（仅第17回游线节点）
NODES: list[dict] = [
    # —— 仪典 / 北 ——
    dict(id="省亲别墅", garden_zone="仪典", coord=(400, 85), tour_order=9),
    dict(id="稻香村", garden_zone="居所", coord=(255, 125), tour_order=5),
    dict(id="议事厅", garden_zone="亭榭", coord=(455, 155)),
    dict(id="大观园厨房", garden_zone="服务", coord=(335, 165)),
    dict(id="茶房", garden_zone="服务", coord=(295, 185)),
    dict(id="芦雪庵", garden_zone="亭榭", coord=(175, 105)),
    dict(id="栊翠庵", garden_zone="寺观", coord=(515, 105)),
    dict(id="达摩庵", garden_zone="寺观", coord=(555, 135)),
    dict(id="玉皇庙", garden_zone="寺观", coord=(595, 95)),
    # —— 水系中轴 ——
    dict(id="沁芳亭", garden_zone="水系", coord=(400, 215), tour_order=3),
    dict(id="缀锦阁", garden_zone="亭榭", coord=(675, 175)),
    dict(id="嘉荫堂", garden_zone="亭榭", coord=(535, 185)),
    dict(id="船坞", garden_zone="水系", coord=(615, 235)),
    dict(id="凸碧堂", garden_zone="亭榭", coord=(425, 275)),
    dict(id="蓼溆", garden_zone="水系", coord=(565, 255), tour_order=7),
    dict(id="滴翠亭", garden_zone="亭榭", coord=(485, 295)),
    dict(id="藕香榭", garden_zone="亭榭", coord=(315, 305)),
    dict(id="沁芳闸", garden_zone="水系", coord=(400, 335), tour_order=10),
    dict(id="凹晶馆", garden_zone="亭榭", coord=(375, 355)),
    dict(id="回廊", garden_zone="服务", coord=(245, 325)),
    # —— 西 / 东 居所 ——
    dict(id="潇湘馆", garden_zone="居所", coord=(155, 275), tour_order=4),
    dict(id="紫菱洲", garden_zone="亭榭", coord=(115, 355)),
    dict(id="柳叶渚", garden_zone="水系", coord=(195, 415)),
    dict(id="蘅芜苑", garden_zone="居所", coord=(645, 295), tour_order=8),
    dict(id="秋爽斋", garden_zone="居所", coord=(725, 245)),
    dict(id="缀锦楼", garden_zone="居所", coord=(705, 315)),
    dict(id="蓼风轩", garden_zone="居所", coord=(685, 375)),
    # —— 桥 / 南 ——
    dict(id="翠烟桥", garden_zone="路径", coord=(295, 395)),
    dict(id="蜂腰桥", garden_zone="路径", coord=(505, 405)),
    dict(id="怡红院", garden_zone="居所", coord=(400, 455), tour_order=11),
    dict(id="红香圃", garden_zone="亭榭", coord=(460, 430)),
    dict(id="暖香坞", garden_zone="居所", coord=(700, 395)),
    dict(id="晓翠堂", garden_zone="亭榭", coord=(740, 265)),
    dict(id="后门", garden_zone="服务", coord=(545, 475)),
    dict(id="云步石梯", garden_zone="路径", coord=(345, 505)),
    dict(id="曲径通幽", garden_zone="路径", coord=(400, 535), tour_order=2),
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


def remove_scalar(raw: str, key: str) -> str:
    return re.sub(rf"^{re.escape(key)}:.*\n?", "", raw, count=1, flags=re.M)


def upsert_coord(raw: str, x: int, y: int) -> str:
    block = f"coord:\n  x: {x}\n  y: {y}\n"
    if re.search(r"^coord:", raw, re.M):
        return re.sub(r"^coord:\n(?:  .+\n)+", block, raw, count=1, flags=re.M)
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
    if "tour_order" in spec:
        new_fm = upsert_scalar(
            new_fm, "tour_order", str(spec["tour_order"]),
            before=("summary:", "tags:", "appear_in:", "garden_zone:"),
        )
    else:
        new_fm = remove_scalar(new_fm, "tour_order")
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
    print(f"seed_garden_coords [{mode}] · {len(NODES)} nodes\n")

    n = 0
    for spec in NODES:
        path = LOC_DIR / f"{spec['id']}.md"
        if not path.exists():
            print(f"  SKIP missing: {spec['id']}")
            continue
        if patch_file(path, spec, write=args.write):
            n += 1
            tag = f" · 游线{spec['tour_order']}" if "tour_order" in spec else ""
            print(f"  {'patched' if args.write else 'would patch'}: {spec['id']} ({spec['garden_zone']}){tag}")

    print(f"\n{'Patched' if args.write else 'Would patch'}: {n}/{len(NODES)}")
    if not args.write:
        print("（加 --write 写回）")


if __name__ == "__main__":
    main()
