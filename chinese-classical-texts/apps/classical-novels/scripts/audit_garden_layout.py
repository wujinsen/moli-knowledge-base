#!/usr/bin/env python3
"""巡检大观园地图坐标：方位 inference 校验、游线、距离、nearby 一致性。"""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOC = ROOT / "src" / "content" / "locations" / "红楼梦"
PX_PER_STEP = 6


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm: dict = {}
    cur: str | None = None
    for line in m.group(1).splitlines():
        if line.startswith("  ") and cur and isinstance(fm.get(cur), dict):
            k, _, v = line.strip().partition(":")
            fm[cur][k.strip()] = v.strip()
        elif ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if v == "":
                cur = k
                fm[k] = {}
            else:
                fm[k] = v
                cur = None
    return fm


def load_nodes() -> dict[str, dict]:
    nodes: dict[str, dict] = {}
    for p in LOC.glob("*.md"):
        fm = parse_frontmatter(p.read_text(encoding="utf-8"))
        if "garden_zone" not in fm:
            continue
        coord = fm.get("coord")
        if not isinstance(coord, dict):
            continue
        nodes[str(fm.get("id", p.stem))] = {
            "x": int(coord["x"]),
            "y": int(coord["y"]),
            "zone": fm.get("garden_zone"),
            "tour": int(fm["tour_order"]) if "tour_order" in fm else None,
            "nearby": fm.get("nearby") if isinstance(fm.get("nearby"), list) else [],
        }
    return nodes


def steps(a: dict, b: dict) -> int:
    return round(math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / PX_PER_STEP)


def bearing(from_n: dict, to_n: dict) -> str:
    dx = to_n["x"] - from_n["x"]
    dy = to_n["y"] - from_n["y"]
    deg = math.degrees(math.atan2(dx, dy))
    dirs = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
    return dirs[round(deg / 45) % 8]


def dir_ok(actual: str, expected: str) -> bool:
    if expected == "北偏":
        return actual in ("北", "东北", "西北")
    return expected in actual


def main() -> None:
    nodes = load_nodes()
    print(f"地图节点: {len(nodes)}\n")

    print("=== 一、inference 方位（对照 garden-scholarship direction_hint）===\n")
    checks = [
        ("潇湘馆", "沁芳亭", "西"),
        ("蘅芜苑", "沁芳亭", "东"),
        ("秋爽斋", "蘅芜苑", "东"),  # 同在东区
        ("省亲别墅", "怡红院", "北"),
        ("稻香村", "沁芳亭", "北偏"),
        ("怡红院", "沁芳闸", "南"),
    ]
    issues = 0
    for id1, anchor, expected in checks:
        a, b = nodes.get(id1), nodes.get(anchor)
        if not a or not b:
            print(f"  SKIP {id1}/{anchor}")
            continue
        if id1 == "省亲别墅":
            br = bearing(a, b)  # 省亲在怡红之北
        elif id1 == "怡红院":
            br = bearing(b, a)  # 怡红在闸之南
        else:
            br = bearing(b, a)  # id1 相对 anchor
        ok = dir_ok(br, expected)
        if not ok:
            issues += 1
        mark = "OK" if ok else "WARN"
        print(f"  {mark} {id1} 在 {anchor} 之 {br}（期望 {expected}）")

    print("\n=== 二、第17回 tour_order 游线（相邻段）===\n")
    tour = sorted(
        [(v["tour"], k, v) for k, v in nodes.items() if v["tour"]],
        key=lambda x: x[0],
    )
    entry = nodes.get("曲径通幽")
    for o, name, v in tour:
        dist = steps(entry, v) if entry else 0
        print(f"  {o:2}. {name:8} ({v['x']},{v['y']}) 距南入口 {dist} 步")
    print()
    for i in range(len(tour) - 1):
        _, n1, v1 = tour[i]
        _, n2, v2 = tour[i + 1]
        print(f"  {n1} → {n2}: {bearing(v1, v2)} · {steps(v1, v2)} 步")

    print("\n=== 三、关键距离（逻辑步，非正文步数）===\n")
    pairs = [
        ("曲径通幽", "省亲别墅"),
        ("潇湘馆", "怡红院"),
        ("潇湘馆", "蘅芜苑"),
        ("稻香村", "省亲别墅"),
        ("沁芳亭", "怡红院"),
        ("蘅芜苑", "秋爽斋"),
        ("沁芳闸", "怡红院"),
    ]
    for a, b in pairs:
        if a in nodes and b in nodes:
            print(f"  {a} — {b}: {steps(nodes[a], nodes[b])} 步 · {bearing(nodes[a], nodes[b])}")

    print("\n=== 四、nearby 边 vs 坐标近邻（前8）===\n")
    near_issues = 0
    for name, v in sorted(nodes.items()):
        nb = [n for n in v.get("nearby", []) if isinstance(n, str) and n in nodes]
        if not nb:
            continue
        dists = sorted(
            ((k, steps(v, nodes[k])) for k in nodes if k != name),
            key=lambda x: x[1],
        )
        top8 = {k for k, _ in dists[:8]}
        for n in nb:
            rank = next(i for i, (k, _) in enumerate(dists, 1) if k == n)
            if n not in top8:
                near_issues += 1
                print(f"  WARN {name}.nearby「{n}」距 {steps(v, nodes[n])} 步，排名第 {rank}")

    if near_issues == 0:
        print("  全部 nearby 边落在坐标前 8 近邻内")

    print(f"\n=== 汇总 ===")
    print(f"  方位 issue: {issues}")
    print(f"  nearby issue: {near_issues}")
    print("  距离单位: inference（px_per_step=6），正文无定量步数，不可称「准确」")


if __name__ == "__main__":
    main()
