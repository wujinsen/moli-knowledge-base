"""一次性迁移：为红楼梦现有 imagery 补 layer（太虚 / 人间）。

分层规则：
- judgment（判词）→ 太虚（第5回薄命司预录）
- flower_lot（花签）→ 人间（第63回怡红夜宴占花名）
- symbol（象征）→ 人间（除已显式标注者，如风月宝鉴=太虚）
- poem（诗词）→ 太虚 if 第5回仙曲 或 好了歌(hl-p-02)，否则人间（人物所作）

幂等：已含 `layer:` 的文件跳过（含本次新建的 7 条神话/结构意象）。
用法：python scripts/add_hlm_imagery_layer.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "src" / "content" / "imagery" / "红楼梦"

POEM_TAIXU_IDS = {
    "hl-p-02",  # 好了歌（出世警偈）
    "hl-p-03", "hl-p-07", "hl-p-08", "hl-p-09", "hl-p-11", "hl-p-12",
    "hl-p-13", "hl-p-15", "hl-p-16", "hl-p-17", "hl-p-18", "hl-p-19", "hl-p-20",
}


def classify(entry_id: str, subtype: str) -> str:
    if subtype == "judgment":
        return "太虚"
    if subtype == "poem":
        return "太虚" if entry_id in POEM_TAIXU_IDS else "人间"
    # symbol / flower_lot
    return "人间"


def main() -> None:
    changed = []
    skipped = []
    for path in sorted(IMG_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        if any(re.match(r"^layer:", ln) for ln in lines):
            skipped.append(path.stem)
            continue
        meta = {}
        for ln in lines[:30]:
            m = re.match(r"^(id|subtype):\s*(\S+)", ln)
            if m:
                meta[m.group(1)] = m.group(2)
        entry_id = meta.get("id", path.stem)
        subtype = meta.get("subtype", "")
        layer = classify(entry_id, subtype)
        # 在 title 行之后插入 layer
        out = []
        inserted = False
        for ln in lines:
            out.append(ln)
            if not inserted and ln.startswith("title:"):
                out.append(f"layer: {layer}\n")
                inserted = True
        if not inserted:
            print(f"[warn] no title line in {path.name}, skipped")
            continue
        path.write_text("".join(out), encoding="utf-8")
        changed.append((path.stem, subtype, layer))

    print(f"updated {len(changed)} files, skipped {len(skipped)} (already layered)")
    for sid, st, ly in changed:
        print(f"  {sid:12} {st:11} -> {ly}")
    if skipped:
        print("skipped:", ", ".join(skipped))


if __name__ == "__main__":
    main()
