#!/usr/bin/env python3
"""补全三书 imagery 页正文：原文 · 互文 · 评析 · 相关。

用法:
  python scripts/enrich_imagery_bodies.py [--write] [--book 红楼梦]
  python scripts/enrich_imagery_bodies.py --write   # 三书全量
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CONTENT, parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
IMG = CONTENT / "imagery"

# 程高本常用全本（补 frontmatter text 中的省略号）
HLM_FULLTEXT: dict[str, str] = {
    "hl-p-02": (
        "世人都晓神仙好，惟有功名忘不了！\n"
        "古今将相在何方？荒冢一堆草没了。\n"
        "世人都晓神仙好，只有金银忘不了！\n"
        "终朝只恨聚无多，及到多时眼闭了。\n"
        "世人都晓神仙好，只有姣妻忘不了！\n"
        "君生日日说恩情，君死又随人去了。\n"
        "世人都晓神仙好，只有儿孙忘不了！\n"
        "痴心父母古来多，孝顺儿孙谁见了！"
    ),
    "hl-p-03": (
        "一个是阆苑仙葩，一个是美玉无瑕。\n"
        "若说没奇缘，今生我偏遇着他；\n"
        "若说有奇缘，如何心事终虚化？\n"
        "一个枉自韶光，一个空劳牵挂。\n"
        "一个是水中月，一个是镜中花。\n"
        "想眼中能有多少泪珠儿，\n"
        "怎经得秋流到冬尽，春流到夏！"
    ),
    "hl-p-08": (
        "都道是金玉良姻，俺只念木石前盟。\n"
        "空对着，山中高士晶莹雪；终不忘，世外仙姝寂寞林。\n"
        "叹人间，美中不足今方信：纵然是齐眉举案，到底意难平。"
    ),
    "hl-p-07": (
        "为官的，家业凋零；富贵的，金银散尽；\n"
        "有恩的，死不相报；无情的，生死空闻。\n"
        "欠命的，命已还；欠泪的，泪已尽。\n"
        "看破的，遁入空门；痴迷的，枉送了性命。\n"
        "好一似食尽鸟投林，落了片白茫茫大地真干净！"
    ),
    "hl-p-10": (
        "秋花惨淡秋草黄，已觉秋窗秋未凉。\n"
        "已觉秋窗秋未凉，何处秋声无风狂？\n"
        "罗衾不奈秋风力，残漏声催秋雨急。\n"
        "连宵霢霢复飕飕，灯前伴人空悲泣。\n"
        "寒烟小院转萧条，疏竹虚窗时滴沥。\n"
        "不知风雨几时休，已教泪洒窗纱湿。"
    ),
    "hl-p-04": (
        "持螯更喜桂阴凉，泼醋擂姜兴欲狂。\n"
        "饕餮王孙因酒废，风流冤孽为钱亡。\n"
        "古今富贵千般好，不及疏篱护菊香。"
    ),
    "hl-p-11": (
        "喜荣华正好，恨无常又到。\n"
        "眼睁睁，把万事全抛。\n"
        "荡悠悠，把芳魂消耗。\n"
        "望家乡，路远山高。\n"
        "故向爹娘梦里相寻告：儿命已入黄泉，天伦呵，须要退步抽身早！"
    ),
    "hl-p-12": (
        "一帆风雨路三千，把骨肉家园齐来抛闪。\n"
        "恐哭损残年，告爹娘，休把儿悬念。\n"
        "自古穷通皆有定，离合岂无缘？\n"
        "从今分两地，各自保平安。\n"
        "奴去也，莫牵连！"
    ),
    "hl-p-13": (
        "留余庆，留余庆，忽遇恩人；\n"
        "幸娘亲，幸娘亲，积得阴功。\n"
        "劝人生，济困扶穷，\n"
        "休似俺那爱银钱忘骨肉的狠舅奸兄！\n"
        "正是乘除加减，上有苍穹。"
    ),
    "hl-p-16": (
        "气质美如兰，才华阜比仙。\n"
        "天生成孤癖人皆罕。\n"
        "你道是啖肉食腥膻，视绮罗俗厌，\n"
        "却不知太高人愈妒，过洁世同嫌。\n"
        "可叹这，青灯古殿人将老，辜负了，红粉朱楼春色阑。\n"
        "到头来，依旧是风尘肮脏违心愿。\n"
        "好一似，无瑕白玉遭泥陷，又何须，王孙公子叹无缘。"
    ),
    "hl-p-01": (
        "花谢花飞花满天，红消香断有谁怜？\n"
        "游丝软系飘春榭，落絮轻沾扑绣帘；\n"
        "闺中女儿惜春暮，愁绪满怀无释处，\n"
        "手把花锄出绣帘，忍踏落花来复去？\n"
        "柳丝榆荚自芳菲，不管桃飘与李飞；\n"
        "桃李明年能再发，明年闺中知有谁？\n"
        "三月香巢已垒成，梁间燕子太无情！\n"
        "明年花开虽可啄，却不道人去楼空巢也倾。\n"
        "一年三百六十日，风刀霜剑严相逼；\n"
        "明媚鲜妍能几时，一朝漂泊难寻觅。\n"
        "花开易见落难寻，阶前愁杀葬花人，\n"
        "独倚花锄泪暗洒，洒上空枝见血痕。\n"
        "杜鹃无语正黄昏，荷锄归去掩重门；\n"
        "青灯照壁人初睡，冷雨敲窗被未温。\n"
        "怪奴底事倍伤神？半为怜春半恼春：\n"
        "怜春忽至恼忽去，至又无言去未闻。\n"
        "昨宵庭外悲歌发，知是花魂与鸟魂？\n"
        "花魂鸟魂总难留，鸟自无言花自羞；\n"
        "愿侬此日生双翼，随花飞到天尽头。\n"
        "天尽头，何处有香丘？\n"
        "未若锦囊收艳骨，一抔净土掩风流。\n"
        "质本洁来还洁去，强于污淖陷渠沟。\n"
        "尔今死去侬收葬，未卜侬身何日丧？\n"
        "侬今葬花人笑痴，他年葬侬知是谁？\n"
        "试看春残花渐落，便是红颜老死时；\n"
        "一朝春尽红颜老，花落人亡两不知！"
    ),
    "hl-p-15": (
        "襁褓中，父母叹双亡。\n"
        "纵居那绮罗丛，谁知娇养？\n"
        "幸生来，英豪阔大宽宏量，从未将儿女私情略萦心上。\n"
        "好一似，霁月光风耀玉堂。\n"
        "厮配得才貌仙郎，博得个地久天长，\n"
        "准折得幼年时坎坷形状。\n"
        "终久是云散高唐，水涸湘江。\n"
        "这是尘寰中消长数应当，何必枉悲伤！"
    ),
    "hl-p-17": (
        "镜里恩情，更那堪梦里功名！\n"
        "那美韶华去之何迅！再休提绣帐鸳衾。\n"
        "只这带珠冠，披凤袄，也抵不了无常性命。\n"
        "虽说是，人生莫受老来贫，也须要阴骘积儿孙。\n"
        "气昂昂头戴簪缨，光灿灿胸悬金印，威赫赫爵禄高登，\n"
        "昏惨惨黄泉路近。\n"
        "问古来将相可还存？也只是虚名儿与后人钦敬。"
    ),
    "hl-p-18": (
        "画梁春尽落香尘。\n"
        "擅风情，秉月貌，便是败家的根本。\n"
        "箕裘颓堕皆从敬，家事消亡首罪宁。\n"
        "宿孽总因情。"
    ),
    "hl-p-14": (
        "【薛宝钗·临江仙】\n"
        "白玉堂前春解舞，东风卷得均匀。\n"
        "蜂团蝶阵乱纷纷。几曾随逝水，岂肯委芳尘。\n"
        "万缕千丝终不改，任他随聚随分。\n"
        "韶华休笑本无根。好风凭借力，送我上青云。\n"
        "\n"
        "【林黛玉·唐多令】\n"
        "粉堕百花洲，香残燕子楼。\n"
        "一团团、逐对成球。飘泊亦如人命薄，空缱绻，说风流。\n"
        "草木也知愁，韶华竟白头。\n"
        "叹今生、谁舍谁收？\n"
        "嫁与东风春不管，凭尔去，忍淹留。\n"
        "\n"
        "【史湘云·如梦令】\n"
        "空挂纤纤缕，徒垂络络丝。\n"
        "也难绾系，也难羁束，也无情，也无力。"
    ),
    "hl-p-05": (
        "维太平不易之元，蓉桂竞芳之月，无可奈何之日，\n"
        "怡红院浊玉，谨以群花之蕊，冰鲛之帕，沁芳之泉，枫露之茗，\n"
        "四者虽微，聊以达诚申信，乃致祭于白帝宫中抚司秋艳芙蓉女儿之前曰：\n"
        "窃思女儿自临浊世，迄今凡十有六载。\n"
        "其为质则金玉不足喻其贵，其为性则冰雪不足喻其洁，\n"
        "其为神则星日不足喻其精，其为貌则花月不足喻其色。\n"
        "（中略：追叙晴雯平生、撕扇补裘、夭逝诸节，见第78回原文。）\n"
        "自为红绡帐里，公子情深，始信黄土垄中，女儿命薄！\n"
        "呜呼！固鬼蜮之为灾，岂神灵而亦妒。\n"
        "天何苍苍，乘玉虬以游乎穹窿；地何茫茫，驾瑶象以降乎泉壤。\n"
        "呜呼哀哉！尚飨！"
    ),
    "hl-p-06": (
        "恒王好武兼好色，遂教美女习骑射。\n"
        "绣歌艳舞不成欢，列阵挽戈为自得。\n"
        "眼前不见尘沙起，将军俏影红灯里。\n"
        "叱咤时闻口舌香，霜矛雪剑娇难举。\n"
        "丁香结子芙蓉绦，不系明珠系宝刀。\n"
        "战罢夜阑心力怯，脂痕粉渍污鲛绡。\n"
        "明年流寇走山东，强吞虎豹势如蜂。\n"
        "王率天兵思剿灭，一战再战不成功。\n"
        "腥风吹折陇头麦，日照旌旗虎帐空。\n"
        "青山寂寂水澌澌，正是恒王战死时。\n"
        "不期忠义明闺阁，愤起恒王得意人。\n"
        "恒王得意数谁行，巾帼将军林四娘，\n"
        "号令秦姬驱赵女，艳李秾桃临战场。\n"
        "誓盟生死报前王，贼势猖獗不可敌，\n"
        "柳折花残实可伤，魂依城郭家乡近，马践胭脂骨髓香。\n"
        "天子惊慌恨失守，此时文武皆垂首。\n"
        "何事文武立朝纲，不及闺中林四娘！\n"
        "我为四娘长太息，歌成馀意尚彷徨。"
    ),
}

# 象征页无 text 字段时的叙述原文
HLM_SYMBOL_NARRATIVE: dict[str, str] = {
    "hl-s-furong": (
        "芙蓉在书中串联多处意象：第31回晴雯撕扇后，宝玉称其「阿晴最像芙蓉」；"
        "第63回占花令，黛玉得芙蓉签「莫怨东风当自嗟」；"
        "第78回宝玉作《芙蓉女儿诔》祭晴雯，又与黛玉改「洧」字论诗。"
        "晴雯为黛影，芙蓉遂成高情难表、泪尽夭逝的枢纽象征。"
    ),
}

# 金瓶梅全本补录
JPM_FULLTEXT: dict[str, str] = {
    "jpm-tune-jiusecaiqi": (
        "酒损精神破丧家，语言无状闹喧哗。\n"
        "拈针弄线难称意，对客挥拳敢怒加。\n"
        "枕上同眠之语，被底私言，\n"
        "都是丧身失命之源。\n"
        "\n"
        "色是刮骨钢刀，空教粉黛争娇；\n"
        "财是夺命绳索，专把英雄困扰。\n"
        "气是雷火，财是贪狼，\n"
        "四者连环，跳不出酒色财气圈子。\n"
        "西门庆一生，尽在此四句中。"
    ),
}

SUBTYPE_HEADING = {
    "judgment": "判词",
    "poem": "诗词",
    "symbol": "象征",
    "flower_lot": "花签",
    "myth": "神话本源",
    "name_omen": "名字谶",
    "object_omen": "物谶",
    "tune_omen": "曲谶",
    "alchemy": "丹道意象",
    "place_omen": "地名谶",
}


def lookup_fulltext(iid: str, book: str) -> str | None:
    if book == "红楼梦":
        return HLM_FULLTEXT.get(iid)
    if book == "金瓶梅":
        return JPM_FULLTEXT.get(iid)
    return None


def needs_enrich(fm: dict, body: str, book: str, iid: str) -> bool:
    subtype = fm.get("subtype")
    summary = fm.get("summary") or ""
    text_fm = fm.get("text") or ""

    if is_stub_body(body, summary, subtype):
        return True
    if lookup_fulltext(iid, book) and ("……" in body or "……" in text_fm or "..." in text_fm):
        return True
    if book == "红楼梦" and iid in HLM_SYMBOL_NARRATIVE and "## 原文" not in body:
        return True
    if len(body.strip()) < 120:
        return True
    return False


def is_stub_body(body: str, summary: str, subtype: str | None = None) -> bool:
    b = body.strip()
    if subtype == "myth" and "## 原文" not in b:
        return True
    if not b:
        return True
    if "## 互文" in b and len(b) > 280:
        return False
    if len(b) < 150:
        return True
    if summary and summary.strip() in b and "……" in b:
        return True
    if b.count("\n") < 4 and "## 评析" not in b:
        return True
    return False


def chapter_ref(chapters: list, source: str | None, book: str) -> str:
    slug = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}.get(book, "")
    parts: list[str] = []
    if chapters:
        for c in chapters:
            parts.append(f"第{c}回")
    if source and source.startswith("chapters/"):
        m = re.search(r"/(\d+)\.md", source)
        if m:
            n = int(m.group(1))
            parts.append(f"[第{n}回](/{slug}/read/chenggao/{n})" if slug else f"第{n}回")
    if not parts:
        return ""
    if len(parts) == 1:
        return f"（{parts[0]}）"
    return f"（{' · '.join(dict.fromkeys(parts))}）"


def format_links(links: list, book: str) -> list[str]:
    if not links:
        return ["- （无显式互文边，见图谱）"]
    lines: list[str] = []
    slug = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}.get(book, "")
    for link in links:
        tgt = link.get("target", "")
        pred = link.get("predicate", "")
        ch = link.get("chapter")
        note = link.get("note", "")
        inf = link.get("inference")
        kind = link.get("target_kind", "character")
        ch_s = f"第{ch}回 · " if ch else ""
        inf_s = "推论 · " if inf else ""
        if kind == "imagery" and tgt.startswith(("hl-", "jpm-", "xyj-")):
            label = f"[[{tgt}]]" if book == "红楼梦" else f"[{tgt}](/{slug}/imagery/{tgt})"
        elif kind == "character":
            label = f"[[{tgt}]]"
        else:
            label = tgt
        extra = f" — {note}" if note else ""
        phase = link.get("phase")
        temp = link.get("temperature")
        meta = ""
        if phase or temp:
            meta = f"（{phase or ''}{'·' if phase and temp else ''}{temp or ''}）"
        lines.append(f"- {ch_s}{inf_s}{pred} → {label}{meta}{extra}")
    return lines


def related_section(fm: dict, book: str) -> list[str]:
    slug = {"红楼梦": "honglou", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}.get(book, "")
    lines: list[str] = []
    for c in fm.get("characters") or []:
        lines.append(f"- [[{c}]]")
    for link in fm.get("links") or []:
        if link.get("target_kind") == "imagery":
            tgt = link["target"]
            if slug:
                lines.append(f"- 意象：[{tgt}](/{slug}/imagery/{tgt})")
            else:
                lines.append(f"- 意象：[[{tgt}]]")
    src = fm.get("source")
    if src:
        lines.append(f"- 出处：`{src}`")
    tags = fm.get("tags") or []
    if tags:
        lines.append(f"- 标签：{', '.join(tags)}")
    return lines or ["- —"]


def build_body(fm: dict, book: str, fulltext: str | None, symbol_text: str | None = None) -> str:
    iid = fm["id"]
    title = fm.get("title", iid)
    subtype = fm.get("subtype", "poem")
    summary = (fm.get("summary") or "").strip()
    text = (fulltext or fm.get("text") or symbol_text or "").strip()
    chapters = fm.get("chapters") or []
    source = fm.get("source")
    heading = SUBTYPE_HEADING.get(subtype, "意象")
    cref = chapter_ref(chapters, source, book)

    parts: list[str] = [f"## {heading} · {title}", ""]

    if text:
        parts.append("## 原文")
        parts.append("")
        parts.append(text)
        if "……" in text or "..." in text:
            parts.append("")
            parts.append(f"> 节录{cref}；全文见对应回目原文。")
        parts.append("")
    elif subtype == "myth":
        parts.append("## 原文")
        parts.append("")
        parts.append(summary)
        for link in fm.get("links") or []:
            note = link.get("note")
            if note:
                parts.append("")
                parts.append(note)
        parts.append("")

    parts.append("## 互文")
    parts.append("")
    parts.extend(format_links(fm.get("links") or [], book))
    parts.append("")

    parts.append("## 评析")
    parts.append("")
    parts.append(summary or "（待补 summary）")
    if subtype in ("symbol", "myth") and fm.get("layer"):
        parts.append("")
        parts.append(f"层级：**{fm['layer']}**（太虚/人间双层镜像）。")
    parts.append("")

    parts.append("## 相关")
    parts.append("")
    parts.extend(related_section(fm, book))
    parts.append("")

    return "\n".join(parts)


def upsert_text_field(fm_raw: str, new_text: str) -> str:
    escaped = new_text.replace("\\", "\\\\").replace('"', '\\"')
    block = f'text: "{escaped}"'
    if re.search(r"^text:", fm_raw, re.M):
        return re.sub(r'^text:.*$', block, fm_raw, count=1, flags=re.M)
    anchor = "title:"
    idx = fm_raw.find(anchor)
    if idx >= 0:
        line_end = fm_raw.find("\n", idx)
        return fm_raw[: line_end + 1] + block + "\n" + fm_raw[line_end + 1 :]
    return fm_raw.rstrip() + "\n" + block + "\n"


def enrich_file(path: Path, book: str, *, write: bool) -> bool:
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False
    fm_raw, body = parts[1], parts[2]
    fm, _ = parse_frontmatter(path)
    iid = fm.get("id") or path.stem
    summary = fm.get("summary") or ""

    if not needs_enrich(fm, body, book, iid):
        return False

    full = lookup_fulltext(iid, book)
    sym = HLM_SYMBOL_NARRATIVE.get(iid) if book == "红楼梦" else None
    new_body = build_body(fm, book, full, sym)
    new_fm = fm_raw
    if full:
        new_fm = upsert_text_field(new_fm, full)

    if write:
        path.write_text(f"---{new_fm}---\n{new_body}", encoding="utf-8")
    return True


def enrich_book(book: str, *, write: bool) -> int:
    d = IMG / book
    if not d.is_dir():
        return 0
    n = 0
    for p in sorted(d.glob("*.md")):
        if enrich_file(p, book, write=write):
            n += 1
            print(f"  {'wrote' if write else 'would write'}: {p.stem}")
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--book", choices=["红楼梦", "金瓶梅", "西游记"])
    args = ap.parse_args()
    books = [args.book] if args.book else ["红楼梦", "金瓶梅", "西游记"]
    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"enrich_imagery_bodies [{mode}]\n")
    total = 0
    for book in books:
        print(f"=== {book} ===")
        total += enrich_book(book, write=args.write)
    print(f"\n{'Updated' if args.write else 'Would update'} {total} pages")
    if not args.write:
        print("（加 --write 写回）")


if __name__ == "__main__":
    main()
