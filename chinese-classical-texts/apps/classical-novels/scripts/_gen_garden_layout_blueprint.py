#!/usr/bin/env python3
"""从 红楼梦.garden_scene_full.json 生成项目坐标方位蓝图（供 AI 重绘 Archviz 对照）。"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "src" / "data" / "红楼梦.garden_scene_full.json"
OUT = ROOT / "public" / "honglou" / "scene" / "layout-blueprint-project.png"

W, H = 2400, 1500
PADDING = (100, 80)
BOUNDS = dict(minX=115, maxX=740, minY=85, maxY=535)

ZONE_COLOR = {
    "仪典": (180, 140, 60),
    "居所": (200, 90, 90),
    "亭榭": (90, 140, 200),
    "水系": (40, 120, 140),
    "寺观": (120, 100, 180),
    "路径": (110, 110, 110),
    "服务": (130, 130, 130),
}

STREAM_SEGS = [
    ("沁芳亭", "沁芳闸"),
    ("沁芳闸", "柳叶渚"),
    ("沁芳亭", "蓼溆"),
    ("蓼溆", "船坞"),
]

MAJOR = {
    "省亲别墅",
    "稻香村",
    "潇湘馆",
    "蘅芜苑",
    "秋爽斋",
    "缀锦楼",
    "怡红院",
    "沁芳亭",
    "沁芳闸",
    "藕香榭",
    "凸碧堂",
    "凹晶馆",
    "蓼溆",
    "栊翠庵",
    "曲径通幽",
}


def logical_to_px(x: float, y: float) -> tuple[float, float]:
    ux = W - PADDING[0] * 2
    uy = H - PADDING[1] * 2
    px = PADDING[0] + (x - BOUNDS["minX"]) / (BOUNDS["maxX"] - BOUNDS["minX"]) * ux
    py = PADDING[1] + (y - BOUNDS["minY"]) / (BOUNDS["maxY"] - BOUNDS["minY"]) * uy
    return px, py


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    buildings = {b["id"]: b for b in data["buildings"]}

    im = Image.new("RGBA", (W, H), (18, 28, 22, 255))
    d = ImageDraw.Draw(im)

    try:
        font = ImageFont.truetype("msyh.ttc", 22)
        font_sm = ImageFont.truetype("msyh.ttc", 16)
        font_lg = ImageFont.truetype("msyh.ttc", 28)
    except OSError:
        font = font_sm = font_lg = ImageFont.load_default()

    # 园界
    wall = [
        logical_to_px(115, 85),
        logical_to_px(740, 85),
        logical_to_px(740, 535),
        logical_to_px(115, 535),
    ]
    d.polygon(wall, outline=(200, 180, 120, 220), fill=(30, 48, 36, 255), width=4)

    # 中轴虚线（北→南）
    cx, _ = logical_to_px(400, 0)
    d.line([(cx, PADDING[1]), (cx, H - PADDING[1])], fill=(255, 220, 120, 80), width=2)

    # 水系（窄溪，非中心大湖）
    for a_id, b_id in STREAM_SEGS:
        a = logical_to_px(*buildings[a_id]["logical"].values())
        b = logical_to_px(*buildings[b_id]["logical"].values())
        d.line([a, b], fill=(60, 160, 170, 200), width=28)

    for pool_id in ("沁芳亭", "沁芳闸"):
        p = logical_to_px(*buildings[pool_id]["logical"].values())
        d.ellipse((p[0] - 46, p[1] - 46, p[0] + 46, p[1] + 46), fill=(50, 140, 150, 180))

    # 建筑块
    for b in data["buildings"]:
        lx, ly = b["logical"]["x"], b["logical"]["y"]
        px, py = logical_to_px(lx, ly)
        bw = max(36, b.get("w", 120) * 0.22)
        bh = max(28, b.get("h", 90) * 0.22)
        col = ZONE_COLOR.get(b["zone"], (150, 150, 150))
        d.rectangle((px - bw / 2, py - bh / 2, px + bw / 2, py + bh / 2), fill=(*col, 210), outline=(255, 255, 255, 180), width=2)
        label = b["name"]
        if b["id"] in MAJOR:
            d.text((px - bw / 2, py - bh / 2 - 24), label, fill=(255, 240, 200, 255), font=font)
        else:
            d.text((px - bw / 2, py + bh / 2 + 2), label, fill=(200, 200, 200, 200), font=font_sm)

    # 第17回游线
    tour = [
        "曲径通幽",
        "沁芳亭",
        "潇湘馆",
        "稻香村",
        "蓼溆",
        "蘅芜苑",
        "省亲别墅",
        "沁芳闸",
        "怡红院",
    ]
    pts = [logical_to_px(*buildings[i]["logical"].values()) for i in tour if i in buildings]
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i + 1]], fill=(255, 210, 80, 160), width=3)

    d.text((PADDING[0], 24), "大观园 · 项目坐标方位蓝图（南北中轴说 inference）", fill=(255, 240, 210, 255), font=font_lg)
    d.text((PADDING[0], 62), "北↑ · 无中心大湖 · 沁芳溪为窄流 · scan/复原图不参与落位", fill=(180, 200, 180, 255), font=font_sm)
    d.text((W - 120, PADDING[1] - 10), "北", fill=(255, 220, 120, 255), font=font_lg)
    d.text((W - 120, H - PADDING[1] - 30), "南", fill=(255, 220, 120, 255), font=font_lg)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, optimize=True)
    print(f"Wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
