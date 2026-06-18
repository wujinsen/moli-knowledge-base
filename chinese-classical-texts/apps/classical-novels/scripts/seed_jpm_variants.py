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
        id="jpm-v-009", chapter=7, category="情节",
        edition_a="词话本", edition_b="崇祯本",
        text_a="你老人家去年买春梅，许我几匹大布，还没与我",
        text_b="你老人家去年买春梅，许我几匹大布，还没与我",
        note="两本第7回同文；身价钱银未载。旧库误以同回「六锭三十两」（孟三儿亲事）作买春梅价，见 jpm-tx-012。",
        summary="买春梅——第7回薛嫂追述同文，银价误植已纠（jpm-tx-012）。",
        tags=["白银流", "纠错"],
    ),
    dict(
        id="jpm-v-010", chapter=1, category="批语",
        edition_a="词话本", edition_b="张竹坡评本",
        note="词话本纯说书正文；张竹坡评本（当前库为崇祯绣像+眉批旁批）含评点层。",
        summary="张评本批语层——非完整张竹坡全文评，但已具眉批/旁批结构。",
    ),
    dict(
        id="jpm-v-011", chapter=1, category="措辞",
        edition_a="词话本", edition_b="张竹坡评本",
        text_a="西门庆", text_b="西門慶",
        summary="人名用字简繁差异（全书通例）。",
        tags=["简繁"],
    ),
    dict(
        id="jpm-v-012", chapter=1, category="批语",
        edition_a="崇祯本", edition_b="张竹坡评本",
        note="崇祯本正文分段；张竹坡评本同底本但嵌 zhupi 眉批/旁批 span。",
        summary="绣像批评本 vs 张评批语 markup 层差异。",
        tags=["批语"],
    ),
    dict(
        id="jpm-v-013", chapter=1, category="措辞",
        edition_a="词话本", edition_b="张竹坡评本",
        text_a="怎能与人争气", text_b="怎能勾與人爭氣",
        summary="简繁 + 「怎的/怎勾」口语异写（张评本同崇祯系）。",
    ),
    dict(
        id="jpm-v-014", chapter=23, category="物价",
        edition_a="词话本", edition_b="崇祯本",
        note="认翟管家干礼百两；三版本金额一致，措辞或有微差。",
        summary="认干爹百两礼——政商链物价锚点。",
        tags=["白银流"],
    ),
    dict(
        id="jpm-v-015", chapter=1, category="情节",
        edition_a="词话本", edition_b="崇祯本",
        note="武松打虎赏五十两、散猎户；两本情节同，崇祯本分段更细。",
        summary="打虎赏银五十两——词话/崇祯同值异排。",
        tags=["白银流"],
    ),
    # 词话 ↔ 张竹坡评本 回目用字异文（竹坡本繁体，且个别用词不同；繁简差异之外的真异文）
    dict(
        id="jpm-v-016", chapter=3, category="回目",
        edition_a="词话本", edition_b="张竹坡评本",
        text_a="定挨光王婆受贿　　设圈套浪子私挑",
        text_b="定挨光虔婆受賄 設圈套浪子私挑",
        note="回目「王婆」↔「虔婆」：词话本作「王婆」，竹坡本作「虔婆」（贬称媒婆）。",
        summary="第3回回目「王婆」↔「虔婆」用字异文。",
    ),
    dict(
        id="jpm-v-017", chapter=25, category="回目",
        edition_a="词话本", edition_b="张竹坡评本",
        text_a="吴月娘春昼秋千　　来旺儿醉中谤仙",
        text_b="吳月娘春晝鞦韆 來旺兒醉中謗訕",
        note="回目「谤仙」↔「谤讪」：词话本作「谤仙」，竹坡本作「谤讪」（毁谤讥讪，于文义更通）。",
        summary="第25回回目「谤仙」↔「谤讪」异文（竹坡本于义为长）。",
    ),
    dict(
        id="jpm-v-018", chapter=32, category="回目",
        edition_a="词话本", edition_b="张竹坡评本",
        text_a="李桂姐趋炎认女　　潘金莲怀妒惊儿",
        text_b="李桂姐趨炎認女 潘金蓮懷嫉驚兒",
        note="回目「怀妒」↔「怀嫉」：妒/嫉近义异文。",
        summary="第32回回目「怀妒」↔「怀嫉」近义异文。",
    ),
    dict(
        id="jpm-v-019", chapter=44, category="回目",
        edition_a="词话本", edition_b="张竹坡评本",
        text_a="避马房侍女偷金　　下象棋佳人消夜",
        text_b="避馬房侍女偸金 下象棋佳人宵夜",
        note="回目「消夜」↔「宵夜」：词话本作「消夜」，竹坡本作「宵夜」。",
        summary="第44回回目「消夜」↔「宵夜」异文。",
    ),
    dict(
        id="jpm-v-020", chapter=99, category="回目",
        edition_a="词话本", edition_b="张竹坡评本",
        text_a="刘二醉骂王六儿张胜窃听张敬济",
        text_b="劉二醉罵王六兒 張勝竊聽陳敬濟",
        note="回目人名讹误：词话本误作「张敬济」，竹坡本正作「陈敬济」（即陈经济）。属版本校正一例。",
        summary="第99回回目「张敬济」↔「陈敬济」——词话本人名讹字，竹坡本校正。",
        tags=["校正"],
    ),
    # 词话 ↔ 崇祯 系统性异体字（全书通例，取第2回为代表）
    dict(
        id="jpm-v-021", chapter=2, category="措辞",
        edition_a="词话本", edition_b="崇祯本",
        text_a="吩咐", text_b="分付",
        note="词话本多作「吩咐」，崇祯本多作「分付」；为两本系统性异体/通假，全书反复出现。",
        summary="「吩咐」↔「分付」系统性异体（全书通例，第2回为代表）。",
        tags=["异体"],
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
