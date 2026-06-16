"""品红绿幕色键：把 mag-*.png（纯品红背景的等距渲染）抠成透明 PNG。

原理：品红 = 高 R、高 B、低 G。令 d = min(R,B) - G，
  d 越大越是背景 → alpha 越低；d<=LOW 全不透明，d>=HIGH 全透明，中间线性羽化。
红柱(低 B)、灰瓦(中性)、绿树/粉花(低 d) 均不会被误伤。
顺带去品红溢色(despill) + 降采样到 720px 压缩。
"""
from pathlib import Path

import numpy as np
from PIL import Image

ASSETS = Path(r"C:\Users\123\.cursor\projects\d-work-moli-project-moli-knowledge-base\assets")
OUT = Path("public/honglou/scene")
NAMES = [
    "grandhall", "courtyard", "farmstead", "temple",
    "xie", "pavilion", "bridge", "cottage", "trees",
]
TARGET_W = 720
LOW, HIGH = 45.0, 130.0   # d 的羽化区间


def key_one(name: str):
    src = ASSETS / f"mag-{name}.png"
    im = Image.open(src).convert("RGB")
    arr = np.asarray(im).astype(np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    d = np.minimum(r, b) - g
    alpha = np.clip((HIGH - d) / (HIGH - LOW), 0.0, 1.0)
    # 去溢色：对偏品红的像素，把 R/B 拉回接近 G，消除粉紫描边
    spill = d > 0
    r2 = np.where(spill, np.minimum(r, g + 55), r)
    b2 = np.where(spill, np.minimum(b, g + 55), b)
    rgba = np.dstack([r2, g, b2, alpha * 255.0]).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    if out.width > TARGET_W:
        h = round(out.height * TARGET_W / out.width)
        out = out.resize((TARGET_W, h), Image.LANCZOS)
    # 裁掉全透明边距，减小尺寸
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    dst = OUT / f"{name}.png"
    out.save(dst, optimize=True)
    op = (np.asarray(out)[..., 3] == 0).mean() * 100
    print(f"{name}: {out.size[0]}x{out.size[1]}  透明 {op:.0f}%  -> {dst.stat().st_size // 1024}KB")


def main():
    for n in NAMES:
        key_one(n)


if __name__ == "__main__":
    main()
