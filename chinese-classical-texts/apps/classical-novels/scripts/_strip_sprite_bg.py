"""临时脚本：给等距 sprite 抠掉纯色背景（GenerateImage 输出为浅灰底 RGB）。

策略：从四边向内做「邻接梯度漫水」——只吞掉平滑、低饱和的背景色，
遇到物体轮廓 / 接地投影的明显落差即停，从而保住白墙与浅色石台基。
处理后顺带降采样压缩（展示宽度仅 ~100-280px，720px 足够）。
"""
import sys
from collections import deque
from pathlib import Path

from PIL import Image

SCENE = Path("public/honglou/scene")
SPRITES = [
    "grandhall.png", "courtyard.png", "farmstead.png", "temple.png",
    "xie.png", "pavilion.png", "bridge.png", "cottage.png", "trees.png",
]
TARGET_W = 720
TOL = 20          # 邻接像素色差阈值（梯度爬升容差）
SAT_MAX = 42      # 仅在低饱和（接近灰）区域允许吞噬，保护彩色屋顶/红柱


def sat(r, g, b):
    return max(r, g, b) - min(r, g, b)


def strip(path: Path):
    im = Image.open(path).convert("RGB")
    if im.width > TARGET_W:
        h = round(im.height * TARGET_W / im.width)
        im = im.resize((TARGET_W, h), Image.LANCZOS)
    W, H = im.size
    px = im.load()
    arr = [[px[x, y] for x in range(W)] for y in range(H)]
    removed = [[False] * W for _ in range(H)]
    dq = deque()

    def seed(x, y):
        if not removed[y][x]:
            removed[y][x] = True
            dq.append((x, y))

    for x in range(W):
        seed(x, 0); seed(x, H - 1)
    for y in range(H):
        seed(0, y); seed(W - 1, y)

    while dq:
        x, y = dq.popleft()
        cr, cg, cb = arr[y][x]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not removed[ny][nx]:
                nr, ng, nb = arr[ny][nx]
                if (abs(nr - cr) <= TOL and abs(ng - cg) <= TOL and abs(nb - cb) <= TOL
                        and sat(nr, ng, nb) <= SAT_MAX):
                    removed[ny][nx] = True
                    dq.append((nx, ny))

    out = Image.new("RGBA", (W, H))
    op = out.load()
    cut = 0
    for y in range(H):
        row = arr[y]
        rm = removed[y]
        for x in range(W):
            if rm[x]:
                op[x, y] = (0, 0, 0, 0)
                cut += 1
            else:
                r, g, b = row[x]
                op[x, y] = (r, g, b, 255)
    out.save(path, optimize=True)
    print(f"{path.name}: {W}x{H}  removed {cut*100//(W*H)}%  -> {path.stat().st_size//1024}KB")


def main():
    for name in SPRITES:
        p = SCENE / name
        if p.exists():
            strip(p)
        else:
            print("missing", name)


if __name__ == "__main__":
    main()
