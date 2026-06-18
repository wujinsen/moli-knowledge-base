#!/usr/bin/env python3
"""在 target-visual-mockup 上绘制校准点，便于肉眼验收。输出 debug PNG，勿提交 dist。"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "src" / "data" / "红楼梦.garden_digital_tour_pins.json"
IMG = ROOT / "public" / "honglou" / "target-visual-mockup.png"
OUT = ROOT / "public" / "honglou" / "scene" / "digital-tour-pins-debug.png"


def main() -> None:
    doc = json.loads(PINS.read_text(encoding="utf-8"))
    im = Image.open(IMG).convert("RGBA")
    w, h = im.size
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("msyh.ttc", 14)
    except OSError:
        font = ImageFont.load_default()

    wall = doc.get("gardenWall")
    if wall:
        x0 = wall["xMin"] / 100 * w
        y0 = wall["yMin"] / 100 * h
        x1 = wall["xMax"] / 100 * w
        y1 = wall["yMax"] / 100 * h
        d.rectangle((x0, y0, x1, y1), outline=(251, 191, 36, 180), width=3)

    for lab in doc.get("exteriorLabels", []):
        x = lab["xPct"] / 100 * w
        y = lab["yPct"] / 100 * h
        d.rectangle((x - 36, y - 10, x + 36, y + 10), fill=(60, 40, 10, 200), outline=(251, 191, 36, 220))
        d.text((x - 28, y - 7), lab["id"], fill=(255, 230, 180, 255), font=font)

    for name, pin in doc["pins"].items():
        x = pin["xPct"] / 100 * w
        y = pin["yPct"] / 100 * h
        tier = pin.get("tier", "secondary")
        r = 10 if tier == "primary" else 7 if tier == "secondary" else 5
        col = (224, 176, 89, 230) if tier == "primary" else (120, 180, 220, 200)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col, outline=(255, 255, 255, 240), width=2)
        d.text((x + r + 2, y - 8), name, fill=(255, 255, 255, 240), font=font)

    out = Image.alpha_composite(im, overlay).convert("RGB")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT, optimize=True)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
