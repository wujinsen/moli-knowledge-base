#!/usr/bin/env python3
"""从人物页 frontmatter / arc / 关键情节 / summary 提取图鉴「结局」。"""
from __future__ import annotations

import re

OUTCOME_KW = (
    "死", "逝", "亡", "殁", "卒", "夭", "出家", "为僧", "为尼", "剃度", "逐", "撵", "赶",
    "嫁", "配", "婚", "和", "散", "败", "抄", "疯", "空", "流放", "伏法", "自尽", "自缢",
    "遣", "放", "归", "返", "复位", "夺", "收", "成佛", "封", "证", "正果", "圆寂",
    "贬", "囚", "陷", "殒", "绝", "覆", "灭", "败亡", "含冤", "冤死", "早夭", "夭折",
    "殉情", "吐血", "病发", "病亡", "病故", "而亡", "而死", "被逐", "被撵", "被卖", "发配",
    "显达", "复兴", "救", "后文", "后四十",
)

CHAPTER_RE = re.compile(r"第\s*(\d+)\s*回")
CHAPTER_RANGE_RE = re.compile(r"第\s*(\d+)\s*[–—-]\s*(\d+)\s*回")


def _format_chapter(ch: int | None, ch_end: int | None = None) -> str:
    if ch is None:
        return ""
    if ch_end and ch_end != ch:
        return f"（第{ch}–{ch_end}回）"
    return f"（第{ch}回）"


def _from_arc(arc: list) -> str | None:
    if not arc:
        return None
    for node in reversed(arc):
        if node.get("stage") == "结局":
            title = (node.get("title") or "").strip()
            note = (node.get("note") or "").strip()
            ch = node.get("chapter")
            suffix = _format_chapter(int(ch) if ch is not None else None)
            if title:
                return f"{title}{suffix}" if suffix else title
            if note:
                return note[:48] + ("…" if len(note) > 48 else "")
    return None


def _has_outcome_signal(text: str) -> bool:
    return any(k in text for k in OUTCOME_KW)


def _from_summary(summary: str) -> str | None:
    if not summary or not _has_outcome_signal(summary):
        return None
    # 优先取含结局关键词的末句
    parts = re.split(r"[；;。]", summary)
    for part in reversed(parts):
        part = part.strip()
        if part and _has_outcome_signal(part):
            part = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", part)
            return part[:56] + ("…" if len(part) > 56 else "")
    cleaned = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", summary.strip())
    return cleaned[:56] + ("…" if len(cleaned) > 56 else "")


def _from_key_plots(body: str) -> str | None:
    m = re.search(r"##\s*关键情节\s*\n([\s\S]*?)(?=\n##\s|\Z)", body)
    if not m:
        return None
    block = m.group(1)
    bullets: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.startswith("|") and "回" in line and _has_outcome_signal(line):
            bullets.append(line)
    if not bullets:
        return None
    for raw in reversed(bullets):
        text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", raw)
        text = re.sub(r"\*\*", "", text)
        if not _has_outcome_signal(text):
            continue
        rm = CHAPTER_RANGE_RE.search(text)
        cm = CHAPTER_RE.search(text)
        if rm:
            suffix = _format_chapter(int(rm.group(1)), int(rm.group(2)))
            core = CHAPTER_RANGE_RE.sub("", text).strip(" ：:，,")
            core = re.sub(r"^第\s*\d+\s*[–—-]\s*\d+\s*回\s*[:：]?", "", core).strip()
        elif cm:
            suffix = _format_chapter(int(cm.group(1)))
            core = CHAPTER_RE.sub("", text).strip(" ：:，,")
            core = re.sub(r"^第\s*\d+\s*回\s*[:：]?", "", core).strip()
        else:
            suffix = ""
            core = text.strip(" ：:，,")
        core = core.lstrip("-| ").strip()
        if not core:
            continue
        return f"{core}{suffix}" if suffix else core[:56]
    # 无明确结局词时，取末条情节作收束（配角常见）
    raw = bullets[-1]
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", raw)
    text = re.sub(r"\*\*", "", text).strip()
    if _has_outcome_signal(text) or text.startswith("后文") or text.startswith("后四十"):
        core = text.lstrip("-| ").strip()
        if core:
            return core[:56] + ("…" if len(core) > 56 else "")
    if CHAPTER_RE.search(text) or CHAPTER_RANGE_RE.search(text):
        rm = CHAPTER_RANGE_RE.search(text)
        cm = CHAPTER_RE.search(text)
        if rm:
            suffix = _format_chapter(int(rm.group(1)), int(rm.group(2)))
            core = CHAPTER_RANGE_RE.sub("", text).strip(" ：:，,")
        elif cm:
            suffix = _format_chapter(int(cm.group(1)))
            core = re.sub(r"第\s*\d+\s*回\s*[:：]?", "", text).strip(" ：:，,")
        else:
            suffix = ""
            core = text
        core = core.lstrip("-| ").strip()
        if core:
            return f"{core}{suffix}" if suffix else core[:56]
    return None


# 图鉴字段未覆盖时的手工补全（须可核原文）
MANUAL: dict[str, str] = {
    # 西游记 · 取经五众
    "唐僧": "取经功成，封旃檀功德佛（第100回）",
    "孙悟空": "取经功成，封斗战胜佛（第100回）",
    "猪八戒": "取经功成，封净坛使者（第100回）",
    "沙僧": "取经功成，封金身罗汉（第100回）",
    "白龙马": "化龙复命，盘绕华表（第100回）",
    "玉皇大帝": "天庭至尊，取经后加封五圣（第100回）",
    "观音菩萨": "取经总调度，五圣朝真（第100回）",
    "如来佛祖": "灵山授经，收伏群魔（第100回）",
    "唐太宗": "还阳续命，发起取经（第13回）",
    "女儿国国王": "痴情挽留不成，目送唐僧西行",
    "镇元子": "与悟空结拜，五庄观地仙之祖",
    "铁扇公主": "借扇熄火，后随牛魔王败散",
    "混世魔王": "被孙悟空剿灭（第2回）",
    # 红楼梦 · 终局难核或程高本补叙
    "刘姥姥": "后文救巧姐（程高本）",
    "贾兰": "后四十回科举显达，兰桂齐芳（程高本）",
    "冯紫英": "射猎荐医后淡出叙事（第10回后少出）",
    "詹光": "清客随贾政，抄家后随府流散",
    "茗烟": "随宝玉读书外出，后四十回随出家流散",
    "李贵": "宝玉跟班，随家塾与宝玉行事",
    "扫红": "宝玉小厮，随怡红院当差",
    "素云": "李纨大丫鬟，随稻香村守节",
    "王狗儿": "刘姥姥女婿，乡野务农",
    "宝蟾": "第91回设计勾引薛蝌，后随夏金桂事败",
    "贾蔷": "管戏班，后赴外任（第92回）",
    "锄药": "宝玉小厮，随怡红院当差",
    # 红楼梦 · 主支终局（程高本为主，须可核原文）
    "贾元春": "宫中薨逝，享年四十三（第95回）",
    "贾探春": "远嫁海疆（程高本）",
    "贾迎春": "被孙绍祖虐待致死（第109回）",
    "贾惜春": "大观园散后剪发出家（第115–116回）",
    "史湘云": "夫婿病故，早寡飘零（第106回）",
    "李纨": "贾兰科举显达，兰桂齐芳（程高本）",
    "秦可卿": "病亡，凤姐协理极盛之丧（第13回）",
    "巧姐": "刘姥姥救出，避祸乡村（第119回）",
    "妙玉": "贾府遭劫，被强盗掳走不知所终（第112回）",
    "香菱": "难产而亡，魂归甄家（第120回）",
    "贾母": "寿终归西（程高本）",
    "贾政": "送子出家，痛哭而返（第120回）",
    "贾珍": "革职发往原籍（第107回）",
    "贾琏": "参与偷梁换柱成婚（第96–97回）",
    "晴雯": "补裘后被撵，含冤夭亡（第77–78回）",
    "袭人": "王夫人放出去配蒋玉菡（第97回）",
    "尤二姐": "受凤姐凌虐，吞金自逝（第69回）",
    "尤三姐": "柳湘莲退婚，自刎于剑下（第67回）",
    "薛蟠": "人命案发配（程高本）",
    "王熙凤": "病中托孤，狱神庙后病逝（程高本）",
    "贾宝玉": "悬崖撒手，出家为僧（第120回）",
    "林黛玉": "焚稿泪尽而逝（第97–98回）",
    "薛宝钗": "与宝玉成婚，守寡度日（程高本）",
}


def personality_from_summary(summary: str) -> str | None:
    """图鉴「性格」：从 summary 首句截取（无则不回填）。"""
    if not summary:
        return None
    s = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", summary)
    s = re.sub(r"（[^）]*）", "", s)
    s = re.split(r"[；;，,]", s)[0].strip()
    if len(s) < 4:
        return None
    return s[:28] + ("…" if len(s) > 28 else "")


def extract_outcome(fm: dict, body: str = "") -> str | None:
    cid = fm.get("id") or fm.get("name") or ""
    if cid in MANUAL:
        return MANUAL[cid]
    if fm.get("结局"):
        return str(fm["结局"]).strip()
    from_arc = _from_arc(fm.get("arc") or [])
    if from_arc:
        return from_arc
    from_plot = _from_key_plots(body)
    if from_plot:
        return from_plot
    from_summary = _from_summary(fm.get("summary") or "")
    if from_summary:
        return from_summary
    return None
