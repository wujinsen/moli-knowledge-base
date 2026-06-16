#!/usr/bin/env python3
"""生成大观园水面荷叶 / 驳岸山石 sprite（RGBA 透明底，直接可用）。"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[1] / "public" / "honglou" / "scene"


def _save(name: str, im: Image.Image) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / f"{name}.png"
    im.save(dst, optimize=True)
    print(f"{name}: {im.size[0]}x{im.size[1]} -> {dst}")


def lotus_pad() -> None:
    w, h = 96, 72
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, h // 2 + 4
    # 叶影
    d.ellipse((cx - 38, cy - 22, cx + 38, cy + 24), fill=(20, 48, 32, 70))
    # 主叶（心形偏椭圆）
    d.ellipse((cx - 36, cy - 26, cx + 36, cy + 20), fill=(58, 108, 62, 245))
    d.ellipse((cx - 28, cy - 22, cx + 10, cy + 8), fill=(88, 142, 72, 120))
    # 叶脉
    d.line((cx, cy - 18, cx, cy + 14), fill=(42, 82, 48, 180), width=2)
    for ang in (-0.55, 0.55, -1.05, 1.05):
        ex = cx + math.cos(ang) * 30
        ey = cy + math.sin(ang) * 16
        d.line((cx, cy, ex, ey), fill=(42, 82, 48, 140), width=1)
    # 缺口（典型荷叶）
    d.polygon([(cx, cy - 20), (cx + 6, cy - 8), (cx - 2, cy - 6)], fill=(0, 0, 0, 0))
    im = im.filter(ImageFilter.GaussianBlur(radius=0.4))
    _save("lotus-pad", im)


def lotus_bloom() -> None:
    w, h = 96, 88
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = w // 2, h // 2 + 10
    d.ellipse((cx - 34, cy - 20, cx + 34, cy + 18), fill=(58, 108, 62, 230))
    # 花瓣
    for i in range(8):
        ang = i * math.tau / 8 - math.pi / 2
        px = cx + math.cos(ang) * 14
        py = cy - 22 + math.sin(ang) * 8
        d.ellipse((px - 10, py - 8, px + 10, py + 8), fill=(240, 170, 196, 240))
    d.ellipse((cx - 8, cy - 26, cx + 8, cy - 10), fill=(255, 228, 238, 250))
    d.ellipse((cx - 4, cy - 22, cx + 4, cy - 14), fill=(255, 248, 252, 255))
    _save("lotus-bloom", im)


def rock(name: str, seed: int) -> None:
    rng = np.random.default_rng(seed)
    w, h = 80, 64
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    n = 3 + int(rng.integers(0, 3))
    for i in range(n):
        cx = int(w * (0.35 + rng.random() * 0.3))
        cy = int(h * (0.55 + rng.random() * 0.25) - i * 4)
        rx = int(14 + rng.random() * 16)
        ry = int(rx * (0.55 + rng.random() * 0.25))
        shade = int(118 + rng.random() * 38)
        d.ellipse(
            (cx - rx, cy - ry, cx + rx, cy + ry),
            fill=(shade - 18, shade - 12, shade - 22, 255),
        )
        d.ellipse(
            (cx - rx * 0.7, cy - ry * 0.85, cx + rx * 0.35, cy + ry * 0.2),
            fill=(shade + 28, shade + 32, shade + 24, 200),
        )
        # 苔点
        if rng.random() > 0.4:
            tx = cx - rx // 3
            ty = cy + ry // 4
            d.ellipse((tx - 4, ty - 3, tx + 4, ty + 3), fill=(72, 98, 58, 160))
    im = im.filter(ImageFilter.GaussianBlur(radius=0.35))
    _save(name, im)


def main() -> None:
    lotus_pad()
    lotus_bloom()
    rock("rock-a", 0xA1)
    rock("rock-b", 0xB2)
    rock("rock-c", 0xC3)


if __name__ == "__main__":
    main()
