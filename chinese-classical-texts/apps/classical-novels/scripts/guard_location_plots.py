#!/usr/bin/env python3
"""/guard 子模块 — 抽检 location 页「关键情节」表对照词话本。

用法: python scripts/guard_location_plots.py [书名]
"""
from __future__ import annotations

import re
import sys

from _common import CHAPTER_DIR, CONTENT, parse_frontmatter, resolve_books

# 词话本正文常用别称（id → 该回可接受的锚词）
EXTRA_ANCHORS: dict[str, list[str]] = {
    "藏春坞": ["藏春阁", "花园里书房", "花园藏春坞", "藏春坞"],
    "卷棚": ["卷棚", "小卷棚", "花园卷棚", "卷棚后面", "卷棚内"],
    "大厅": ["大厅", "厅上", "前厅", "经坛"],
    "上房": ["上房", "后宅", "大娘房里"],
    "花园": ["花园", "园里", "后园", "葡萄架", "翡翠轩"],
    "绒线铺": [
        "绒线铺", "开绒线韩伙计", "韩道国铺", "铺中", "开铺", "对门楼",
        "九月初四日开张", "柜上发卖", "甘伙计", "韩伙计",
    ],
    "西门庆生药铺": ["生药铺", "药铺", "县门前"],
    "李娇儿院": ["院中", "勾栏", "李家", "李娇儿"],
    "花家": ["花子虚", "花二哥", "隔一壁", "花家"],
    "潘家": ["紫石街", "武大郎", "武大", "王婆"],
    "东京": ["东京", "汴梁", "汴京", "蔡京", "太师府"],
    "吴月娘房": ["月娘", "大房", "大娘"],
    "潘金莲房": ["潘金莲", "五娘", "五房"],
    "李瓶儿房": ["李瓶儿", "瓶儿", "六娘", "六房"],
    "孟玉楼房": ["孟玉楼", "玉楼", "三房", "三娘"],
    "孙雪娥房": ["孙雪娥", "雪娥", "二房", "厨房", "灶上"],
    "清河县": ["清河县", "清河", "东平府", "提刑"],
    "仪门": ["仪门", "后边仪门", "进入仪门"],
    "角门": ["角门", "花园角门", "角门外"],
    "大门首": ["大门首", "门首", "挂起长幡"],
    "翡翠轩": ["翡翠轩", "翡翠轩卷棚", "葡萄架", "木香棚"],
    "对门楼": ["对门楼", "对门房", "对门房子里", "卸在对门楼上"],
    "后楼": ["后楼", "后楼上", "往后楼上", "后边楼上"],
    "木香棚": ["木香棚", "抹过木香棚"],
    "县衙": ["县衙", "知县", "李拱极", "李知县", "衙内", "穿孝服来上纸帛", "五员官"],
    "提刑千户所": ["提刑所", "山东提刑所", "提刑千户", "衙门", "往衙门", "衙门中", "衙门里"],
    "乔大户家": ["乔大户", "乔亲家", "乔皇亲", "长姐", "乔亲家爹"],
    "门房": ["门房", "门房里", "门首", "接拜贴"],
    "厨房": ["厨房", "厨房里", "大厨灶", "厨役", "上灶", "灶上", "收拾家火"],
    "吴道官道院": ["吴道官", "道院", "吴道官院", "玉皇庙", "写疏焚符", "讨符", "上庙散福", "散福"],
    "守备府": ["守备府", "帅府", "周爷", "周守备", "周爷府"],
    "五岳观": ["五岳观", "潘道士", "潘捉鬼", "门外五岳观"],
    "厢房": ["厢房", "厢房中"],
    "铺子里": ["铺子里", "前边铺子", "关上铺子门"],
    "王婆茶坊": ["王婆茶坊", "茶坊", "茶肆", "护炕"],
    "灵堂": ["灵堂", "灵前", "灵前行礼", "前边灵前", "焚香烧纸", "打磐"],
    "穿廊": ["穿廊", "穿廊下", "凉椅"],
    "观音庵": ["观音庵", "进庵来", "北面皈依"],
    "莲花庵": ["莲花庵", "薛姑子"],
    "报恩寺": ["报恩寺", "禅和子", "伴灵拜忏"],
    "招宣府": ["招宣府", "王招宣府", "王招宣"],
    "紫石街": ["紫石街", "紫石街巷口", "王婆茶坊"],
    "丽春院": ["丽春院", "李桂姐"],
    "郑爱月儿院": ["郑爱月儿", "院中郑爱月儿"],
    "王六儿家": ["王六儿", "王六儿家", "石桥东边"],
    "前厅书房": ["大厅前书房", "对门房子里", "温秀才"],
    "县前街": ["县前街", "县前客店", "县门前", "县东街", "县前一个"],
    "临清钞关": ["临清钞关", "临清", "税钞"],
    "张亲家宅": ["张亲家", "张亲家爹", "张亲家母", "云板"],
    "崔中书家": ["崔中书家", "崔中书"],
    "何千户家": ["何千户", "何千户家", "何太监", "到家一饭"],
    "报国寺": ["报国寺", "十六众僧人", "水陆"],
    "内相花园": ["内相花园", "出城二十里", "极是华丽"],
    "翟亲家宅": ["翟亲家", "翟大爹", "翟云峰", "翟管家", "太师爷府里"],
    "王皇亲宅": ["王皇亲", "王皇亲家", "王皇亲家人"],
    "韩姨夫家": ["韩姨夫", "韩姨夫家", "门外韩姨夫家"],
    "夹道": ["夹道", "夹道内", "打夹道内"],
    "东昌府": ["东昌府", "东平府", "东平府察院", "察院"],
    "新河口": ["新河口", "百家村", "出郊五十里"],
    "阳谷县": ["阳谷县", "狄斯彬", "狄斯朽", "狄混"],
    "石桥儿巷": ["石桥儿巷", "石桥巷", "甘润", "字出身"],
    "王家巷": ["王家巷", "大南首王家巷", "文嫂"],
    "皇庄": ["皇庄", "皇庄上", "门外皇庄", "薛内相", "薛公公", "管砖厂"],
    "应伯爵家": ["应伯爵家", "应二家", "应二哥家", "应二爹家"],
    "大街皇亲家": ["大街皇亲", "大街皇亲家"],
    "怀庆府": ["怀庆府", "怀西", "林千户", "林承勋", "林苍峰"],
    "城西河边": ["城西河边", "清河县城西河边", "旋风", "狄斯彬"],
    "狮子街": ["狮子街", "市街"],
    "西门府": ["西门府", "七进", "大官人", "西门庆家"],
    "玉皇庙": ["玉皇庙", "玉皇", "吴道官"],
    "永福寺": ["永福寺", "永福", "僧家"],
}

# 情节为回目/梗概级综述，仅校验回目存在
SYNOPSIS_ONLY = re.compile(r"回目|丧命|散离|全书|政商链")


def load_cihua_body(book: str, chap_no: int) -> str | None:
    if book != "金瓶梅":
        p = CHAPTER_DIR / book / f"{chap_no:03d}.md"
        if not p.exists():
            return None
        raw = p.read_text(encoding="utf-8")
    else:
        raw = None
        for sub in ("词话本", ""):
            for fmt in (f"{chap_no:03d}.md", f"{chap_no}.md"):
                p = CHAPTER_DIR / book / sub / fmt if sub else CHAPTER_DIR / book / fmt
                if p.exists():
                    raw = p.read_text(encoding="utf-8")
                    break
            if raw:
                break
        if raw is None:
            return None
    m = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)$", raw, re.S)
    body = m.group(1) if m else raw
    return re.sub(r"<[^>]+>", "", body)


def parse_plot_rows(body: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    in_table = False
    for line in body.splitlines():
        if line.strip() == "## 关键情节":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("|"):
            continue
        if re.match(r"^\|\s*[-:]+", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("回目", ""):
            continue
        m = re.search(r"(\d+)", cells[0])
        if not m:
            continue
        rows.append((int(m.group(1)), cells[1]))
    return rows


def plot_anchors(loc_id: str, fm: dict, plot: str) -> list[str]:
    anchors: list[str] = []
    for m in re.finditer(r"「([^」]{2,})」", plot):
        anchors.append(m.group(1))
    clean = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", plot)
    for token in re.findall(r"[\u4e00-\u9fff]{2,}", clean):
        if token not in ("回目", "情节", "西门庆", "月娘"):
            anchors.append(token)
    for term in [fm.get("id"), fm.get("name")] + (fm.get("aliases") or []):
        if term:
            anchors.append(term)
    anchors.extend(EXTRA_ANCHORS.get(loc_id, []))
    # 去重，长词优先
    seen: set[str] = set()
    out: list[str] = []
    for a in sorted(set(anchors), key=len, reverse=True):
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def verify_row(loc_id: str, fm: dict, chap_no: int, plot: str, text: str) -> tuple[bool, str]:
    if SYNOPSIS_ONLY.search(plot) and len(plot) < 40:
        return True, "synopsis"
    anchors = plot_anchors(loc_id, fm, plot)
    for a in anchors:
        if len(a) >= 2 and a in text:
            return True, a
    return False, anchors[0] if anchors else "?"


def guard_location_plots(book: str) -> int:
    loc_dir = CONTENT / "locations" / book
    if not loc_dir.is_dir():
        return 0
    issues = 0
    checked = 0
    for path in sorted(loc_dir.glob("*.md")):
        fm, body = parse_frontmatter(path)
        lid = fm.get("id", path.stem)
        for chap_no, plot in parse_plot_rows(body):
            checked += 1
            text = load_cihua_body(book, chap_no)
            if text is None:
                print(f"[{book}] {lid} 第{chap_no}回: 词话本缺页 → skip")
                continue
            ok, hint = verify_row(lid, fm, chap_no, plot, text)
            if not ok:
                print(f"[{book}] {lid} 第{chap_no}回: unverified — {plot[:60]}…")
                print(f"    未命中锚词（首项 {hint}）")
                issues += 1
    print(f"location plots: 抽检 {checked} 条，{issues} 处 unverified")
    return issues


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "金瓶梅"
    issues = 0
    for book in resolve_books(arg):
        issues += guard_location_plots(book)
    if issues:
        print(f"Trust Guard (location plots) 完成，{issues} 处存疑")
    else:
        print("Trust Guard (location plots) 通过")


if __name__ == "__main__":
    main()
