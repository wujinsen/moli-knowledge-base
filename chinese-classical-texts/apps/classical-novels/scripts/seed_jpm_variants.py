#!/usr/bin/env python3
"""金瓶梅版本异文锚点（首批样本，供对勘双栏高亮）。

重生成：python scripts/seed_jpm_variants.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "content" / "variants" / "金瓶梅"

VARIANTS: list[dict] = [
    dict(
        id="jpm-v-001", chapter=1, category="回目",
        edition_a="词话本", edition_b="崇祯本",
        text_a="西门庆热结十弟兄　　武二郎冷遇亲哥嫂",
        text_b="西门庆热结十弟兄　　 武二郎冷遇亲哥嫂",
        summary="回目空格与全角空格差异（两本同回异排）。",
    ),
    dict(
        id="jpm-v-002", chapter=1, category="删润",
        edition_a="词话本", edition_b="崇祯本",
        note="词话本开篇诗与正文多连写为长段；崇祯本拆分为独立段落并加引诗分行。",
        summary="崇祯本对词话本大段连写做分段润色（全书通例）。",
        tags=["版式"],
    ),
    dict(
        id="jpm-v-003", chapter=1, category="措辞",
        edition_a="词话本", edition_b="崇祯本",
        text_a="怎能与人争气", text_b="怎能勾与人争气",
        summary="「怎的」↔「怎勾」类晚明口语异写。",
    ),
    dict(
        id="jpm-v-004", chapter=16, category="措辞",
        edition_a="词话本", edition_b="崇祯本",
        text_a="［入日］捣了一夜", text_b="肏捣了一夜",
        summary="词话本避讳符号 vs 崇祯本直写（删润/避讳策略差异）。",
        tags=["避讳"],
    ),
    dict(
        id="jpm-v-005", chapter=16, category="措辞",
        edition_a="词话本", edition_b="崇祯本",
        text_a="大钟饮酒", text_b="大锺饮酒",
        summary="「钟/锺」异体字。",
    ),
    dict(
        id="jpm-v-006", chapter=16, category="情节",
        edition_a="词话本", edition_b="崇祯本",
        note="李瓶儿箱藏沉香、白蜡、水银、胡椒等，两本金额与品种一致；崇祯本分段更细。",
        summary="李瓶儿私房物资清单（两本情节同，版式异）。",
    ),
    dict(
        id="jpm-v-007", chapter=27, category="物价",
        edition_a="词话本", edition_b="崇祯本",
        note="西门庆购犀角带；具体银两表述需逐句对勘，已关联 transaction jpm-tx-005。",
        summary="犀角带买卖——物价锚点（待持续补全异文金额）。",
        tags=["白银流"],
    ),
    dict(
        id="jpm-v-008", chapter=49, category="情节",
        edition_a="词话本", edition_b="崇祯本",
        note="胡僧赠药情节；张竹坡评本另增眉批阐释「纵欲」主题。",
        summary="胡僧春药——晚明纵欲心理切片，三版本批语层差异大。",
    ),
    dict(
        id="jpm-v-009", chapter=12, category="物价",
        edition_a="词话本", edition_b="崇祯本",
        text_a="三十两", text_b="三十两",
        note="买春梅身契；架构文档 §7.1 标杆 transaction，各本回目与措辞或有偏移。",
        summary="买庞春梅三十两——银价标杆（回目锚点存疑见 jpm-tx-012）。",
        tags=["白银流", "存疑"],
    ),
    dict(
        id="jpm-v-010", chapter=1, category="批语",
        edition_a="词话本", edition_b="张竹坡评本",
        note="词话本纯说书正文；张竹坡评本（当前库为崇祯绣像+眉批旁批）含评点层。",
        summary="张评本批语层——非完整张竹坡全文评，但已具眉批/旁批结构。",
    ),
]


def write(v: dict) -> None:
    tags = v.get("tags", [])
    opt = []
    if v.get("text_a"):
        opt.append(f"text_a: {v['text_a']}")
    if v.get("text_b"):
        opt.append(f"text_b: {v['text_b']}")
    if v.get("note"):
        opt.append(f"note: {v['note']}")
    opt_block = ("\n".join(opt) + "\n") if opt else ""
    text = f"""---
id: {v['id']}
type: variant
book: 金瓶梅
chapter: {v['chapter']}
category: {v['category']}
edition_a: {v['edition_a']}
edition_b: {v['edition_b']}
{opt_block}tags: [{', '.join(tags)}]
summary: {v['summary']}
---
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{v['id']}.md").write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    for v in VARIANTS:
        write(v)
    print(f"[金瓶梅] {len(VARIANTS)} 异文锚点 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
