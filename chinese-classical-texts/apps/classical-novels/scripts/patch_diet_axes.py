#!/usr/bin/env python3
"""为 dish 实体写入 diet_axes / temperature（手标营养轴，覆盖关键词误判）。"""
from __future__ import annotations

import re
from pathlib import Path

from _common import CONTENT, parse_frontmatter

DISHES = CONTENT / "dishes"

# id → { diet_axes?, temperature? }
PATCHES: dict[str, dict[str, dict]] = {
    "红楼梦": {
        "绿畦香稻饭": {"diet_axes": {"refined_grain": 4, "feast_luxury": 1}, "temperature": "平"},
        "红稻米粥": {"diet_axes": {"refined_grain": 3, "feast_luxury": 1}, "temperature": "温"},
        "甜烂之食": {"diet_axes": {"fat_sweet": 4}, "temperature": "温"},
        "燕窝粥": {"diet_axes": {"fine_tonic": 4}, "temperature": "温"},
        "燕窝汤": {"diet_axes": {"fine_tonic": 4}, "temperature": "温"},
        "茄鲞": {"diet_axes": {"feast_luxury": 4, "fat_sweet": 2}, "temperature": "温"},
        "鸽子蛋": {"diet_axes": {"refined_grain": 3, "feast_luxury": 3}},
        "南小菜": {"diet_axes": {"coarse_balance": 4}, "temperature": "凉"},
        "劝食细粥": {"diet_axes": {"coarse_balance": 3}, "temperature": "温"},
        "面茶": {"diet_axes": {"coarse_balance": 3}, "temperature": "温"},
        "枣儿粳米粥": {"diet_axes": {"coarse_balance": 2, "refined_grain": 2}, "temperature": "温"},
        "香薷解暑汤": {"diet_axes": {"coarse_balance": 3}, "temperature": "凉"},
        "绿豆洗面": {"diet_axes": {"coarse_balance": 2}, "temperature": "凉"},
        "风腌果子狸": {"diet_axes": {"fat_sweet": 3, "feast_luxury": 1}, "temperature": "温"},
        "胭脂鹅脯": {"diet_axes": {"fat_sweet": 2, "feast_luxury": 1}},
        "奶油松瓤卷酥": {"diet_axes": {"fat_sweet": 3, "refined_grain": 1}},
        "酒酿蒸鸭": {"diet_axes": {"fat_sweet": 2, "feast_luxury": 1}},
        "螃蟹宴": {"diet_axes": {"feast_luxury": 3, "fat_sweet": 1, "alcohol": 1}},
        "省亲宴": {"diet_axes": {"feast_luxury": 4, "refined_grain": 1}},
        "贾母八旬宴": {"diet_axes": {"feast_luxury": 4, "fat_sweet": 2}},
        "抄家席间": {"diet_axes": {"feast_luxury": 2, "fat_sweet": 1}},
        "贾母丧仪供饭": {"diet_axes": {"coarse_balance": 2, "feast_luxury": 1}},
        "宝玉复生粥": {"diet_axes": {"coarse_balance": 3}, "temperature": "温"},
        "桂圆汤": {"diet_axes": {"fine_tonic": 1, "coarse_balance": 2}, "temperature": "温"},
        "玫瑰露": {"diet_axes": {"fine_tonic": 2, "fat_sweet": 1}},
        "茯苓霜": {"diet_axes": {"fine_tonic": 2, "fat_sweet": 1}},
    },
    "金瓶梅": {
        "烧鹅": {"diet_axes": {"fat_sweet": 3, "feast_luxury": 1}, "temperature": "温"},
        "烧猪头": {"diet_axes": {"fat_sweet": 3, "feast_luxury": 1}},
        "鲜猪": {"diet_axes": {"fat_sweet": 2}},
        "糟鲥鱼": {"diet_axes": {"fat_sweet": 2, "alcohol": 1}},
        "酥酥": {"diet_axes": {"fat_sweet": 3}},
        "酥油泡螺儿": {"diet_axes": {"fat_sweet": 3}},
        "桂花饼": {"diet_axes": {"fat_sweet": 2, "refined_grain": 1}},
        "果馅金饼": {"diet_axes": {"fat_sweet": 2, "refined_grain": 1}},
        "荷花细饼": {"diet_axes": {"fat_sweet": 2}},
        "元宵圆子": {"diet_axes": {"fat_sweet": 2, "feast_luxury": 1}},
        "寿面": {"diet_axes": {"refined_grain": 2, "feast_luxury": 2}},
        "面汤": {"diet_axes": {"coarse_balance": 2, "refined_grain": 1}, "temperature": "温"},
        "梅汤": {"diet_axes": {"coarse_balance": 2}, "temperature": "凉"},
        "衣梅": {"diet_axes": {"coarse_balance": 1, "fat_sweet": 1}},
        "螃蟹鲜": {"diet_axes": {"feast_luxury": 2, "fat_sweet": 1}},
        "烧羊": {"diet_axes": {"fat_sweet": 3, "feast_luxury": 2}},
        "浙江酒": {"diet_axes": {"alcohol": 3}},
        "金华酒": {"diet_axes": {"alcohol": 3}},
        "葡萄酒": {"diet_axes": {"alcohol": 3}},
        "药五香酒": {"diet_axes": {"alcohol": 2, "fine_tonic": 1}},
        "历日": {"diet_axes": {"feast_luxury": 1}},
    },
}


def format_axes_block(axes: dict[str, int]) -> str:
    lines = ["diet_axes:"]
    for k, v in sorted(axes.items()):
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def patch_file(path: Path, patch: dict) -> bool:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(path)
    changed = False

    if "diet_axes" in patch:
        block = format_axes_block(patch["diet_axes"])
        if re.search(r"^diet_axes:", text, re.M):
            text = re.sub(r"^diet_axes:\n(?:  \w+: \d+\n)+", block + "\n", text, count=1, flags=re.M)
        else:
            text = text.replace("---\n", f"---\n{block}\n", 1)
        changed = True

    if "temperature" in patch:
        temp = patch["temperature"]
        if re.search(r"^temperature:", text, re.M):
            text = re.sub(r"^temperature:.*$", f"temperature: {temp}", text, count=1, flags=re.M)
        else:
            # insert after category or book
            if re.search(r"^category:", text, re.M):
                text = re.sub(r"^(category:.*)$", rf"\1\ntemperature: {temp}", text, count=1, flags=re.M)
            else:
                text = text.replace("---\n", f"---\ntemperature: {temp}\n", 1)
        changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main() -> None:
    n = 0
    for book, patches in PATCHES.items():
        d = DISHES / book
        for dish_id, patch in patches.items():
            p = d / f"{dish_id}.md"
            if p.exists() and patch_file(p, patch):
                n += 1
                print(f"  patched {book}/{dish_id}")
            elif not p.exists():
                print(f"  skip missing {book}/{dish_id}")
    print(f"patch_diet_axes: {n} files")


if __name__ == "__main__":
    main()
