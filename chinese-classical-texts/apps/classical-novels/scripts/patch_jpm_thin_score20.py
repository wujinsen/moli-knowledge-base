#!/usr/bin/env python3
"""/dream — 金瓶梅 score≤20 薄页补第 2 条情节（带出处）。

用法: python scripts/patch_jpm_thin_score20.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAR_DIR, parse_frontmatter  # noqa: E402
from dream_patch_common import page_score, scan_pages  # noqa: E402

BOOK = "金瓶梅"
THIN_MAX = 20

PLOT_SECOND: dict[str, str] = {
    "六黄太尉": "第65回：钦差太尉至西门庆门首，山东巡抚、巡按率两司八府接筵，搬演《裴晋公还带记》；胡师文等八府官行厅参礼（chapters/金瓶梅/词话本/065）。",
    "胡师文": "第65回：筵散后，胡师文与守御周秀亲送桌面、羊酒至皇船交付，回厅拜谢西门庆（chapters/金瓶梅/词话本/065）。",
    "方轸": "第64回：薛内相、刘内相在西门庆席评方轸奏本，讥科道「酸子弄坏江山」，与蔡京割地议并读（chapters/金瓶梅/词话本/064）。",
    "杜中书": "第63回：西门庆亲递三杯酒，要写「诏封锦衣西门恭人李氏柩」，杜子春号云野与应伯爵、温秀才议去「恭」字改「室人」（chapters/金瓶梅/词话本/063）。",
    "杜二娘": "第75回：月娘回府述应二嫂满月席，西门庆评春花儿「成精奴才」；杜二娘与马家娘子等同席，两个女儿弹唱（chapters/金瓶梅/词话本/075）。",
    "潘道士": "第62回：祭灯灭后嘱西门庆「切忌不可往病人房里去，恐祸及汝身」，只收布一疋、白金三两作衬，拂袖而去（chapters/金瓶梅/词话本/062）。",
    "郑纪": "第63回：瓶儿丧筵正搬《抱妆盒》，郑纪厅内打茶过帘，春梅取盏、小玉推玉箫泼茶，西门庆闻喧嚷使来安问（chapters/金瓶梅/词话本/063）。",
    "陈文昭": "第48回：后文苗青案由东平府尹胡师文承转，与陈文昭并记为府尹异文；钱劳僚属两案并见（chapters/金瓶梅/词话本/048）。",
}

REL_ADD: dict[str, list[dict]] = {
    "方轸": [{"target": "蔡京", "type": "同僚", "role": "灾异本牵连"}],
    "六黄太尉": [{"target": "胡师文", "type": "同僚", "role": "接筵八府"}],
    "杜中书": [{"target": "潘金莲", "type": "同僚", "role": "瓶儿丧筵"}],
    "陈文昭": [{"target": "潘金莲", "type": "同僚", "role": "同场"}],
}


def count_plots(body: str) -> int:
    m = re.search(r"## 关键情节\s*\n(.*?)(?=\n## |\Z)", body, re.S)
    if not m:
        return 0
    return sum(1 for ln in m.group(1).splitlines() if ln.strip().startswith("-"))


def add_plot(body: str, line: str) -> str:
    m = re.search(r"(## 关键情节\s*\n.*?)(\n## )", body, re.S)
    if not m:
        return body
    block = m.group(1)
    if line.strip() in block:
        return body
    new_block = block.rstrip() + f"\n- {line}\n"
    return body[: m.start(1)] + new_block + body[m.end(1) :]


def dedupe_related(body: str) -> str:
    """合并重复 ## 相关 块为一块。"""
    parts = re.split(r"(## 相关\s*\n)", body)
    if len(parts) < 3:
        return body
    head = parts[0]
    blocks: list[str] = []
    i = 1
    while i < len(parts):
        if parts[i].startswith("## 相关"):
            if i + 1 < len(parts):
                blocks.append(parts[i + 1])
            i += 2
        else:
            break
    if len(blocks) <= 1:
        return body
    lines: list[str] = []
    for b in blocks:
        for ln in b.splitlines():
            s = ln.strip()
            if s.startswith("- "):
                lines.append(s)
    merged = "\n".join(dict.fromkeys(lines)) + "\n"
    tail = "".join(parts[i:])
    return head + "## 相关\n\n" + merged + tail


def patch_file(path: Path, dry_run: bool) -> list[str]:
    cid = path.stem
    fm, body = parse_frontmatter(path)
    changes: list[str] = []

    new_body = dedupe_related(body)
    if new_body != body:
        body = new_body
        changes.append("dedupe-相关")

    line = PLOT_SECOND.get(cid)
    if line and count_plots(body) < 2:
        nb = add_plot(body, line)
        if nb != body:
            body = nb
            changes.append("+plot2")

    for rel in REL_ADD.get(cid, []):
        rels = list(fm.get("relations") or [])
        if rel["target"] not in {r.get("target") for r in rels}:
            rels.append(rel)
            fm["relations"] = rels
            changes.append(f"+rel→{rel['target']}")

    if not changes:
        return []
    if not dry_run:
        text = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        path.write_text(f"---\n{text}---\n{body}", encoding="utf-8")
    return changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pages, _ = scan_pages(BOOK)
    targets = sorted(
        cid for cid, info in pages.items() if page_score(info) <= THIN_MAX
    )
    n = 0
    for cid in targets:
        path = CHAR_DIR / BOOK / f"{cid}.md"
        if not path.exists():
            continue
        ch = patch_file(path, args.dry_run)
        if ch:
            print(f"  {cid}: {', '.join(ch)}")
            n += 1
    remaining = sum(1 for _, info in scan_pages(BOOK)[0].items() if page_score(info) <= THIN_MAX)
    print(f"patched {n} · remaining score<={THIN_MAX}: {remaining}")


if __name__ == "__main__":
    main()
