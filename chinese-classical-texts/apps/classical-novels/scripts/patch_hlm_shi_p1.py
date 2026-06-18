#!/usr/bin/env python3
"""B1 诗词意象 P1：为判词/曲子补全 → 人物「隐喻/预示」推论边（inference）。"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "src/content/imagery/红楼梦"

# 追加 links 块（YAML 列表项）；若已存在同 predicate+target 则跳过
PATCHES: dict[str, list[str]] = {
    "hl-p-01.md": [
        """  - target: 林黛玉
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 27
    note: "花谢花飞、红消香断，以花自喻泪尽前身"
""",
    ],
    "hl-p-02.md": [
        """characters:
  - 甄士隐
links:
  - target: 甄士隐
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 1
    note: "解注好了歌悟入空门，盛衰无常总纲"
""",
    ],
    "hl-p-03.md": [
        """characters:
  - 贾宝玉
  - 林黛玉
links:
  - target: 贾宝玉
    target_kind: character
    predicate: 预示
    inference: true
    chapter: 5
    note: "美玉无瑕"
  - target: 林黛玉
    target_kind: character
    predicate: 预示
    inference: true
    chapter: 5
    note: "阆苑仙葩"
  - target: hl-j-01
    target_kind: imagery
    predicate: 互文
    inference: true
    chapter: 5
    note: "黛玉判词与枉凝眉"
  - target: hl-p-08
    target_kind: imagery
    predicate: 互文
    inference: true
    chapter: 5
    note: "钗黛悲剧母题"
""",
    ],
    "hl-p-04.md": [
        """  - target: 贾宝玉
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 38
    note: "持螯狂态讽权贵，暗写贾府败象"
""",
    ],
    "hl-p-05.md": [
        """  - target: 晴雯
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 78
    note: "芙蓉女儿即晴雯，判词在祭文中兑现"
  - target: 林黛玉
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 78
    note: "改字论诗，与诔文主宾互文"
""",
    ],
    "hl-p-10.md": [
        """  - target: 林黛玉
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 45
    note: "秋窗孤灯自伤，与葬花一脉"
""",
    ],
    "hl-p-14.md": [
        """  - target: 林黛玉
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 70
    note: "唐多令：粉堕香残，春事将残"
  - target: 史湘云
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 70
    note: "空挂纤纤缕，漂泊无着"
  - target: 薛宝钗
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 70
    note: "好风凭借力，借势而上"
""",
    ],
    "hl-p-21.md": [
        """  - target: 香菱
    target_kind: character
    predicate: 隐喻
    inference: true
    chapter: 49
    note: "永团圆反扣判词，香魂难返故乡"
""",
    ],
}

# hl-p-05：影射边改为 inference
REPLACE = {
    "hl-p-05.md": (
        "    predicate: 影射\n    inference: false",
        "    predicate: 影射\n    inference: true",
    ),
}


def patch_file(name: str) -> bool:
    path = IMG / name
    text = path.read_text(encoding="utf-8")
    orig = text

    if name in REPLACE:
        old, new = REPLACE[name]
        text = text.replace(old, new, 1)

    if name not in PATCHES:
        return text != orig

    inserts = PATCHES[name]

    if name == "hl-p-02.md":
        text = re.sub(
            r"characters: \[\]\nlinks: \[\]",
            inserts[0].rstrip(),
            text,
            count=1,
        )
    elif name == "hl-p-03.md":
        text = re.sub(
            r"characters: \[\]\nlinks: \[\]",
            inserts[0].rstrip(),
            text,
            count=1,
        )
    else:
        for block in inserts:
            snippet = block.strip()
            if snippet.split("\n")[0].strip().startswith("- target:"):
                key = re.search(r"target: (\S+)", snippet)
                pred = re.search(r"predicate: (\S+)", snippet)
                if key and pred and f"target: {key.group(1)}" in text and f"predicate: {pred.group(1)}" in text:
                    continue
            if snippet in text:
                continue
            text = re.sub(
                r"(links:\n(?:  - .+\n)+)",
                lambda m: m.group(1) + block,
                text,
                count=1,
            )

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = [n for n in PATCHES | REPLACE if patch_file(n)]
    print(f"Patched {len(changed)} files: {', '.join(sorted(set(changed)))}")


if __name__ == "__main__":
    main()
