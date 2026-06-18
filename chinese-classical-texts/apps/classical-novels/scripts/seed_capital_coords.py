#!/usr/bin/env python3
"""为《红楼梦》都外与王公地图注入 capital_zone + coord（A9）。

用法: python scripts/seed_capital_coords.py [--write]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC_DIR = ROOT / "src" / "content" / "locations" / "红楼梦"

# id, capital_zone, x, y — inference 布局（非测绘）
NODES: list[dict] = [
    dict(id="临敬殿", capital_zone="都城", coord=(400, 60)),
    dict(id="金陵城", capital_zone="都城", coord=(400, 180)),
    dict(id="贡院", capital_zone="都城", coord=(520, 160)),
    dict(id="宁荣街", capital_zone="连接", coord=(400, 320)),
    dict(id="北静王府", capital_zone="王府", coord=(280, 260)),
    dict(id="南安王府", capital_zone="王府", coord=(350, 260)),
    dict(id="乐善郡王府", capital_zone="王府", coord=(450, 260)),
    dict(id="忠顺王府", capital_zone="王府", coord=(520, 260)),
    dict(id="锦乡侯府", capital_zone="侯伯", coord=(200, 300)),
    dict(id="临安伯府", capital_zone="侯伯", coord=(250, 340)),
    dict(id="临昌伯府", capital_zone="侯伯", coord=(300, 380)),
    dict(id="永昌驸马府", capital_zone="侯伯", coord=(500, 340)),
    dict(id="甄家", capital_zone="市井", coord=(180, 200)),
    dict(id="孙家", capital_zone="市井", coord=(620, 200)),
    dict(id="小花枝巷", capital_zone="市井", coord=(160, 360)),
    dict(id="赖大家", capital_zone="市井", coord=(220, 420)),
    dict(id="清虚观", capital_zone="寺观", coord=(580, 280)),
    dict(id="铁槛寺", capital_zone="寺观", coord=(620, 360)),
    dict(id="水月庵", capital_zone="寺观", coord=(560, 420)),
    dict(id="姑子庙", capital_zone="寺观", coord=(140, 280)),
    dict(id="破寺", capital_zone="寺观", coord=(500, 480)),
    dict(id="地藏庵", capital_zone="寺观", coord=(480, 520)),
    dict(id="孝慈县", capital_zone="郊野", coord=(640, 480)),
    dict(id="十里屯", capital_zone="郊野", coord=(400, 480)),
    dict(id="急流津", capital_zone="郊野", coord=(320, 520)),
    dict(id="郝家庄", capital_zone="郊野", coord=(680, 400)),
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
    for anchor in ("capital_zone:", "manor_zone:", "garden_zone:", "summary:", "tags:", "appear_in:"):
        idx = raw.find(anchor)
        if idx >= 0:
            return raw[:idx] + block + raw[idx:]
    return raw.rstrip() + "\n" + block


def strip_body_orphans(body: str) -> str:
    body = re.sub(r"^coord:\n(?:  .+\n)+", "", body, count=1, flags=re.M)
    body = re.sub(r"^capital_zone:.*\n?", "", body, count=1, flags=re.M)
    return body.rstrip() + "\n"


def patch_file(path: Path, spec: dict, *, write: bool) -> bool:
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    fm = parts[1]
    body = strip_body_orphans(parts[2])
    cx, cy = spec["coord"]
    # 桥接节点（已有 manor/garden 坐标）仅补 capital_zone，不覆盖 coord
    has_inner_zone = re.search(r"^manor_zone:", fm, re.M) or re.search(r"^garden_zone:", fm, re.M)
    new_fm = upsert_scalar(
        fm, "capital_zone", spec["capital_zone"], before=("summary:", "tags:", "appear_in:")
    )
    if not has_inner_zone:
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
    print(f"seed_capital_coords [{mode}] · {len(NODES)} nodes\n")

    n = 0
    for spec in NODES:
        path = LOC_DIR / f"{spec['id']}.md"
        if not path.exists():
            print(f"  SKIP missing: {spec['id']}")
            continue
        if patch_file(path, spec, write=args.write):
            n += 1
            print(f"  {'patched' if args.write else 'would patch'}: {spec['id']} ({spec['capital_zone']})")

    print(f"\n{'Patched' if args.write else 'Would patch'}: {n}/{len(NODES)}")
    if not args.write:
        print("（加 --write 写回）")


if __name__ == "__main__":
    main()
