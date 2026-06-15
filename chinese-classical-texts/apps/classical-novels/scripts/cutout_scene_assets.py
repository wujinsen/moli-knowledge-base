"""把 AI 生成图里「假透明棋盘格 / 浅灰白底」从边缘 flood-fill 抠成真透明。

仅处理与图像边缘连通的近中性亮色背景；建筑内部白墙、彩色主体因不与边缘连通而保留。
用法: python scripts/cutout_scene_assets.py
"""
from PIL import Image, ImageDraw
from pathlib import Path

SCENE_DIR = Path(__file__).resolve().parent.parent / "public" / "honglou" / "scene"
TARGETS = [
    "xiaoxiangguan.png",
    "yihongyuan.png",
    "qinfangting.png",
    "npc-daiyu.png",
    "npc-baoyu.png",
]
# flood 容差（PIL 用各通道绝对差之和；白253 vs 灰227 ≈ 78，主体彩色 > 120）
THRESH = 105
STEP = 24  # 沿边缘布种间距，覆盖被主体切断的边缘段


def border_seeds(w, h):
    pts = []
    for x in range(0, w, STEP):
        pts.append((x, 0))
        pts.append((x, h - 1))
    for y in range(0, h, STEP):
        pts.append((0, y))
        pts.append((w - 1, y))
    return pts


def cutout(path: Path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    for seed in border_seeds(w, h):
        px = im.getpixel(seed)
        if px[3] == 0:  # 已透明，跳过
            continue
        # 仅对近中性亮色（背景棋盘格）布种，避免误吃彩色主体
        r, g, b = px[0], px[1], px[2]
        if min(r, g, b) < 150 or (max(r, g, b) - min(r, g, b)) > 40:
            continue
        ImageDraw.floodfill(im, seed, (0, 0, 0, 0), thresh=THRESH)
    im.save(path)
    # 统计透明占比
    alpha = im.getchannel("A")
    transparent = sum(1 for a in alpha.getdata() if a == 0)
    pct = transparent / (w * h) * 100
    print(f"{path.name}: {w}x{h}  透明 {pct:.1f}%")


def main():
    for name in TARGETS:
        cutout(SCENE_DIR / name)


if __name__ == "__main__":
    main()
