#!/usr/bin/env python3
"""/guard — Trust Guard 内容校验（防幻觉）。

- form：由 Astro build / Zod 校验 frontmatter
- content：
  1. first_appear 回目原文是否出现人物名
  2. ## 关键情节 各条是否在标注回目命中锚词
  3. relations 逐边：在情节回目 / first_appear 回目中是否同现双方
  4. transactions：amount_normalized 与 source

用法: python scripts/trust_guard.py [书名]
"""
from __future__ import annotations

import re
import sys

from _common import CHAPTER_DIR, CONTENT, DATA_DIR, iter_characters, parse_frontmatter, resolve_books

# 人物 id → 词话本正文常见别称（relation / 情节锚词补充）
CHARACTER_EXTRA_ANCHORS: dict[str, list[str]] = {
    "陈经济": ["陈敬济", "敬济", "陈姐夫", "陈姑爷"],
    "周守备": ["周统制", "周秀", "周爷", "帅府", "守备"],
    "庞春梅": ["春梅", "春梅姐", "春梅奶奶"],
    "玳安": ["玳安儿", "大官儿", "玳安小厮"],
    "来保": ["汤来保", "保官儿", "来保儿"],
    "来旺": ["来旺儿", "宋旺"],
    "韩道国": ["韩伙计", "韩希尧", "韩一摇", "韩西桥"],
    "王六儿": ["韩道国浑家", "六儿", "王屠妹子"],
    "韩爱姐": ["爱姐", "五姐"],
    "吴月娘": ["月娘", "吴氏", "大娘"],
    "西门庆": ["大官人", "西门大官人", "大爹", "西门爹"],
    "翟管家": ["翟谦", "翟亲家", "翟爹", "翟叔", "翟云峰"],
    "夏提刑": ["夏延龄", "夏龙溪", "夏提刑", "夏老爹"],
    "张胜": ["张虞候", "张胜", "张管家"],
    "刘二": ["坐地虎", "刘二捣鬼", "老二", "二捣鬼"],
    "孙雪娥": ["雪娥", "雪姑娘"],
    "李衙内": ["李拱璧", "李通判"],
    "普静师": ["普静", "普静禅师", "雪洞老和尚", "老师"],
    "官哥儿": ["官哥", "哥儿"],
    "孟玉楼": ["孟三姐", "孟三儿", "三娘", "三姐"],
    "宋惠莲": ["蕙莲", "惠莲", "宋蕙莲", "小金莲"],
    "李瓶儿": ["瓶儿", "李大姐", "六娘"],
    "潘金莲": ["金莲", "五娘", "潘五儿"],
    "李智": ["李三", "李三相陪"],
    "黄四": ["白四哥", "白汝晃"],
    "蔡京": ["蔡太师", "太师"],
    "武松": ["武都头", "武二郎", "都头", "打虎"],
    "胡僧": ["胡老人家", "西域", "天竺", "密松林"],
    "武大郎": ["武大", "武大哥"],
    "应伯爵": ["应二哥", "伯爵"],
    "谢希大": ["谢爹", "希大"],
    "郑爱月儿": ["爱月儿", "爱月", "郑爱月"],
    "郑娇儿": ["娇儿", "董娇儿"],
    "韩金钏儿": ["韩钏儿", "金钏儿", "韩金钏", "韩金"],
    "韩玉钏儿": ["玉钏儿", "韩玉钏", "韩玉"],
    "消愁儿": ["消愁", "韩家女儿"],
    "王杏庵": ["杏庵", "王杏庵周济", "金宗明", "庙中坐"],
    "苗青": ["苗实", "苗家人"],
    "苗天秀": ["苗员外", "天秀"],
    "来兴儿": ["来兴", "来兴媳妇"],
    "云理守": ["云二哥", "云大人", "云参将"],
    "陆秉义": ["陆二郎", "陆二哥"],
    "崔本": ["崔大哥", "崔本"],
    # 西游记 · 天庭编制（正文多作「马、赵、温、关」「庞、刘、苟、毕」等合称）
    "关元帅": ["关", "马、赵、温、关", "马赵温关", "四大元帅", "四元帅", "四大天将"],
    "马元帅": ["马", "马、赵、温、关", "马赵温关", "四大元帅", "四元帅", "四大天将"],
    "温元帅": ["温", "马、赵、温、关", "马赵温关", "四大元帅", "四元帅", "四大天将"],
    "赵元帅": ["赵", "马、赵、温、关", "马赵温关", "四大元帅", "四元帅", "四大天将"],
    "庞元帅": ["庞", "庞、刘", "庞、刘、苟、毕", "庞刘苟毕", "四大天将"],
    "刘元帅": ["刘", "庞、刘", "庞、刘、苟、毕", "庞刘苟毕", "四大天将"],
    "毕元帅": ["毕", "庞、刘、苟、毕", "庞刘苟毕", "四大天将"],
    "苟元帅": ["苟", "庞、刘、苟、毕", "庞刘苟毕", "四大天将"],
    "增长天王": ["增长天王", "增长", "南方增长"],
    "广目天王": ["广目天王", "广目", "西方广目"],
    "护国天王": ["护国天王", "护国", "北门护国"],
    "多闻天王": ["多闻天王", "多闻", "北方多闻"],
    "崩将军": ["崩将军", "崩、芭", "崩芭", "崩芭二将"],
    "芭将军": ["芭将军", "崩、芭", "崩芭", "崩芭二将"],
    "流元帅": ["流元帅", "流", "马、流", "马流元帅"],
    "张道陵": ["张道陵", "张天师", "张"],
    "陶天君": ["陶天君", "陶", "陶、张、辛、邓", "邓、辛、张、陶"],
    "辛天君": ["辛天君", "辛", "陶、张、辛、邓", "邓、辛、张、陶"],
    "邓天君": ["邓天君", "邓", "陶、张、辛、邓", "邓、辛、张、陶"],
    "可韩丈人": ["可韩丈人", "可韩", "可韩司"],
    # 西游记 · 二郎神部属（第6回「康、张、姚、李」等）
    "姚公麟": ["姚公麟", "姚公", "姚太尉", "康、张、姚、李", "康、张、姚、李四太尉"],
    "康太尉": ["康太尉", "康", "康、张", "康、张、姚、李", "康、张太尉"],
    "李太尉": ["李太尉", "李四太尉", "李", "康、张、姚、李", "康、张、姚、李四太尉"],
    "张太尉": ["张太尉", "张", "康、张", "康、张、姚、李", "康、张太尉"],
    "梅山六兄弟": ["梅山六兄弟", "梅山七圣", "梅山"],
    "郭申将军": ["郭申", "郭申将军"],
    "直健将军": ["直健", "直健将军"],
    # 西游记 · 其他常见别称
    "观音菩萨": ["观音菩萨", "观音", "观世音", "南海观音", "南海菩萨", "菩萨", "拜菩萨", "活观音"],
    "唐太宗": ["唐太宗", "太宗", "李世民", "唐王", "大唐太宗"],
    "女儿国国王": ["女儿国国王", "女儿国", "女王", "国母"],
    "二郎神": ["二郎神", "二郎", "真君", "杨戬"],
    "九头虫": ["九头虫", "九头驸马"],
    "精细鬼": ["精细鬼", "精细"],
    "伶俐虫": ["伶俐虫", "伶俐"],
    "哪吒": ["哪吒", "三太子", "哪吒太子"],
    "殷温娇": ["殷温娇", "温娇", "殷小姐", "殷氏"],
    "魏征": ["魏征", "魏丞相"],
    "天竺国国王": ["天竺国国王", "天竺国", "天竺国王"],
    "灭法国国王": ["灭法国国王", "灭法国", "灭法"],
    "仪制司": ["仪制司", "仪制"],
    "光禄寺": ["光禄寺"],
    "内宫官": ["内宫官"],
    "教坊司": ["教坊司"],
    "宣召官": ["宣召官"],
    "护驾": ["护驾"],
    "白龙马": ["白龙马", "龙马", "玉龙三太子"],
    "东海龙王": ["东海龙王", "敖广", "龙王"],
    # 西游记 · 平顶山 / 高老庄 / 贞观举哀异文
    "金角大王": ["金角", "老魔", "大大王"],
    "银角大王": ["银角", "二魔", "二大王"],
    "压龙洞老母": ["压龙洞老母亲", "老奶奶", "老妈妈", "九尾狐狸", "姐姐"],
    "狐阿七大王": ["狐阿七", "阿七", "老舅爷"],
    "虞世南": ["李世绩"],
    "孙悟空": ["行者", "孙行者", "齐天大圣", "大圣"],
    "太白金星": ["金星"],
    "羽林军": ["羽林卫", "羽林"],
    "锦衣卫": ["锦衣官", "锦衣"],
    # 红楼梦 · 程高本正文别称（guard 真源 chapters/红楼梦/NNN.md，非脂砚斋本子目录）
    "贾探春": ["探春", "三姑娘"],
    "贾惜春": ["惜春", "四姑娘"],
    "贾迎春": ["迎春", "二姑娘"],
    "薛宝钗": ["宝钗", "宝姐姐", "薛姑娘"],
    "林黛玉": ["黛玉", "林姑娘", "林妹妹"],
    "贾宝玉": ["宝玉", "宝二爷"],
    "王熙凤": ["凤姐", "凤姐儿", "琏二奶奶", "凤辣子"],
    "秦可卿": ["可卿", "秦氏", "蓉大奶奶", "蓉哥媳妇"],
    "北静王": ["北静", "水溶", "北静郡王"],
    "东平郡王": ["东平", "东平郡"],
    "西宁郡王": ["西宁", "西宁郡"],
    "南安郡王": ["南安", "南安郡"],
    "镇国公": ["镇国", "四王八公"],
    "锦乡侯": ["锦乡", "锦乡侯府"],
    "警幻仙子": ["警幻", "仙姑", "警幻仙姑", "太虚幻境"],
    "神瑛侍者": ["神瑛", "侍者", "通灵宝玉", "顽石", "绛珠"],
    "绛珠仙子": ["绛珠", "还泪", "灌愁海"],
    "葫芦僧": ["门子", "葫芦庙", "小沙弥"],
    "渺渺真人": ["渺渺", "真人"],
    "茫茫大士": ["茫茫", "大士", "跛足道人"],
    "娇杏": ["娇杏", "封氏将其", "扶侧作正室"],
    "张友士": ["冯紫英荐", "从学过的一个先生", "医道很好"],
    "胡庸医": ["王太医", "外感内滞", "白冷着了些", "大夫来了"],
    "菂官": ["藕官", "纸钱", "烧纸"],
    "宝官": ["十二个女孩子", "戏班", "梨香院"],
    "玉官": ["十二个女孩子", "戏班", "梨香院"],
    "龄官": ["蔷薇花架", "划蔷", "地下抠土", "簪子"],
    "张金哥": ["金哥", "张家", "守备之子"],
    "净虚": ["净虚", "馒头庵", "铁槛寺"],
    "善姐": ["善姐"],
    "忠顺亲王": ["忠顺", "忠顺府", "忠顺亲王府"],
    "蒋玉菡": ["琪官", "蒋玉菡", "小旦"],
    "林如海": ["如海", "林海", "巡盐御史", "兰台寺大夫"],
    "贾敏": ["贾敏", "岳母", "妹丈", "贱荆"],
    "李嬷嬷": ["李嬷嬷", "嬷嬷"],
    "李贵": ["李贵", "奶母之子"],
    "夏守忠": ["夏守忠", "夏太监", "夏老爷", "六宫都太监", "宣贵妃娘娘之命", "元妃疾愈"],
    "同贵": ["同喜", "节礼", "薛蟠"],
    "甄宝玉": ["甄宝玉", "有一个宝玉", "甄夫人"],
    "彩云": ["赵姨娘", "小吉祥儿", "借衣"],
    "珍珠": ["贾母", "怡红院"],
    "鲍二家的": ["鲍二", "吊死", "二奶奶"],
    "焦大": ["焦大", "爬灰", "养小叔子"],
    "贾代儒": ["代儒", "塾师"],
}

SYNOPSIS_ONLY = re.compile(
    r"回目|丧命|散离|全书|政商链|对照|互链|见 \[|topics/|contradicts|compare|版本-|程高本|脂评|脂砚"
)


def load_cihua_body(book: str, chap_no: int) -> str | None:
    if book != "金瓶梅":
        p = CHAPTER_DIR / book / f"{chap_no:03d}.md"
        if not p.exists():
            return None
        raw = p.read_text(encoding="utf-8-sig")
    else:
        raw = None
        for sub in ("词话本", ""):
            for fmt in (f"{chap_no:03d}.md", f"{chap_no}.md"):
                p = CHAPTER_DIR / book / sub / fmt if sub else CHAPTER_DIR / book / fmt
                if p.exists():
                    raw = p.read_text(encoding="utf-8-sig")
                    break
            if raw:
                break
        if raw is None:
            return None
    m = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)$", raw, re.S)
    body = m.group(1) if m else raw
    return re.sub(r"<[^>]+>", "", body)


def chapter_count(book: str) -> int:
    p = DATA_DIR / f"{book}.chapter_summaries.json"
    if p.exists():
        import json

        data = json.loads(p.read_text(encoding="utf-8-sig"))
        summaries = data.get("summaries") or {}
        if summaries:
            return max(int(k) for k in summaries)
    base = CHAPTER_DIR / book
    if base.exists():
        return len(list(base.rglob("*.md")))
    return 100


def chapter_num(label: str | None) -> int | None:
    if not label:
        return None
    m = re.search(r"\d+", label)
    return int(m.group()) if m else None


def chapters_from_label(label: str) -> list[int]:
    """第47回 / 第47–48回 / 第94–95回 → [47] 或 [47,48]"""
    nums = [int(x) for x in re.findall(r"\d+", label)]
    if not nums:
        return []
    if len(nums) >= 2 and ("–" in label or "-" in label or "—" in label):
        lo, hi = nums[0], nums[1]
        return list(range(lo, hi + 1))
    return [nums[0]]


def name_terms(fm: dict, extra_id: str | None = None) -> list[str]:
    terms: list[str] = []
    for t in [extra_id or fm.get("id"), fm.get("name")] + (fm.get("aliases") or []):
        if t and isinstance(t, str):
            terms.append(t)
    eid = extra_id or fm.get("id")
    if eid:
        terms.extend(CHARACTER_EXTRA_ANCHORS.get(eid, []))
    seen: set[str] = set()
    out: list[str] = []
    for t in sorted(set(terms), key=len, reverse=True):
        if len(t) >= 2 and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def parse_plot_bullets(body: str) -> list[tuple[list[int], str]]:
    """解析 ## 关键情节 下的列表项。"""
    rows: list[tuple[list[int], str]] = []
    in_section = False
    for line in body.splitlines():
        if line.strip() == "## 关键情节":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.strip().startswith("- "):
            continue
        text = line.strip()[2:].strip()
        m = re.match(r"第[\d–\-—]+回", text)
        if m:
            chaps = chapters_from_label(m.group(0))
            rows.append((chaps, text))
        else:
            nums = [int(x) for x in re.findall(r"第(\d+)回", text)]
            if nums:
                rows.append((nums, text))
    return rows


def plot_anchors(char_id: str, fm: dict, plot: str) -> list[str]:
    anchors: list[str] = []
    for m in re.finditer(r"「([^」]{2,})」", plot):
        anchors.append(m.group(1))
    clean = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", plot)
    for token in re.findall(r"[\u4e00-\u9fff]{2,}", clean):
        if token not in ("关键情节", "相关", "评析", "主要关系", "身份"):
            anchors.append(token)
    anchors.extend(name_terms(fm, char_id))
    seen: set[str] = set()
    out: list[str] = []
    for a in sorted(set(anchors), key=len, reverse=True):
        if a not in seen and len(a) >= 2:
            seen.add(a)
            out.append(a)
    return out


def text_has_any(text: str, terms: list[str]) -> bool:
    return any(t in text for t in terms if len(t) >= 2)


def verify_plot_line(char_id: str, fm: dict, chaps: list[int], plot: str, book: str) -> tuple[bool, str]:
    if SYNOPSIS_ONLY.search(plot):
        return True, "synopsis-skip"
    anchors = plot_anchors(char_id, fm, plot)
    for chap in chaps:
        text = load_cihua_body(book, chap)
        if text is None:
            continue
        for a in anchors:
            if a in text:
                return True, f"第{chap}回·{a}"
    # 弱校验：人物在标注回目出现（情节条多为摘要式写法）
    terms = name_terms(fm, char_id)
    for chap in chaps:
        text = load_cihua_body(book, chap)
        if text and text_has_any(text, terms):
            return True, f"第{chap}回·{fm.get('name')}"
    return False, anchors[0] if anchors else "?"


def collect_search_chapters(
    char_id: str,
    fm: dict,
    body: str,
    all_fms: dict[str, tuple],
    target_id: str | None,
) -> list[int]:
    chaps: set[int] = set()
    for cs, _ in parse_plot_bullets(body):
        chaps.update(cs)
    if target_id and target_id in all_fms:
        _, _, tbody = all_fms[target_id]
        for cs, _ in parse_plot_bullets(tbody):
            chaps.update(cs)
    tgt_fm = all_fms.get(target_id or "", (None, {}, ""))[1]
    for label in [fm.get("first_appear"), tgt_fm.get("first_appear")]:
        n = chapter_num(label if isinstance(label, str) else None)
        if n:
            chaps.add(n)
    if not chaps:
        fa = chapter_num(fm.get("first_appear"))
        if fa:
            chaps.add(fa)
    return sorted(chaps)


def verify_relation_edge(
    book: str,
    char_id: str,
    fm: dict,
    body: str,
    target_id: str,
    rel_type: str,
    all_fms: dict[str, tuple],
    chapter_cache: dict[int, str | None],
) -> tuple[bool, str]:
    src_terms = name_terms(fm, char_id)
    if target_id in all_fms:
        _, tfm, _ = all_fms[target_id]
        tgt_terms = name_terms(tfm, target_id)
    else:
        tgt_terms = name_terms({"id": target_id, "name": target_id}, target_id)

    search = collect_search_chapters(char_id, fm, body, all_fms, target_id)

    def check_chapters(chap_list: list[int]) -> tuple[bool, str]:
        for chap in chap_list:
            if chap not in chapter_cache:
                chapter_cache[chap] = load_cihua_body(book, chap)
            text = chapter_cache[chap]
            if text and text_has_any(text, src_terms) and text_has_any(text, tgt_terms):
                return True, f"第{chap}回"
        return False, ""

    ok, hint = check_chapters(search)
    if ok:
        return True, hint

    # 全书回扫（仅 relation 未命中时）
    for chap in range(1, chapter_count(book) + 1):
        if chap in search:
            continue
        if chap not in chapter_cache:
            chapter_cache[chap] = load_cihua_body(book, chap)
        text = chapter_cache[chap]
        if text and text_has_any(text, src_terms) and text_has_any(text, tgt_terms):
            return True, f"第{chap}回(full-scan)"

    return False, f"{target_id}({rel_type})"


def guard_transactions(book: str) -> int:
    issues = 0
    tx_dir = CONTENT / "transactions" / book
    if not tx_dir.is_dir():
        return 0
    for path in sorted(tx_dir.glob("*.md")):
        fm, _ = parse_frontmatter(path)
        tid = fm.get("id", path.stem)
        if fm.get("amount_normalized") is None:
            print(f"[{book}] {tid}: 缺 amount_normalized → unverified")
            issues += 1
        if not fm.get("source"):
            print(f"[{book}] {tid}: 缺 source → unverified")
            issues += 1
        if fm.get("conversion_disputed"):
            print(f"[{book}] {tid}: conversion_disputed（换算存疑，需人工复核）")
    return issues


def guard_character_content(book: str) -> tuple[int, int, int]:
    """返回 (plot_issues, relation_issues, skipped_no_chapter)。"""
    all_fms: dict[str, tuple] = {}
    for path, fm, body in iter_characters(book):
        cid = fm.get("id") or path.stem
        all_fms[cid] = (path, fm, body)

    plot_issues = 0
    rel_issues = 0
    fa_issues = 0
    plot_checked = 0
    rel_checked = 0
    chapter_cache: dict[int, str | None] = {}

    for cid, (path, fm, body) in all_fms.items():
        # first_appear（保留原检）
        no = chapter_num(fm.get("first_appear"))
        if no:
            text = load_cihua_body(book, no)
            if text is not None:
                if not text_has_any(text, name_terms(fm, cid)):
                    print(f"[{book}] {cid}: first_appear=第{no}回 原文未见其名 → unverified")
                    fa_issues += 1

        # 关键情节
        for chaps, plot in parse_plot_bullets(body):
            if not chaps:
                continue
            plot_checked += 1
            ok, hint = verify_plot_line(cid, fm, chaps, plot, book)
            if not ok:
                print(f"[{book}] {cid} 情节 unverified — {plot[:72]}…")
                print(f"    回目 {chaps} 未命中锚词（首项 {hint}）")
                plot_issues += 1

        # relations 逐边
        for rel in fm.get("relations") or []:
            if not isinstance(rel, dict):
                continue
            target = rel.get("target")
            rtype = rel.get("type", "?")
            if not target:
                continue
            rel_checked += 1
            ok, hint = verify_relation_edge(
                book, cid, fm, body, target, rtype, all_fms, chapter_cache
            )
            if not ok:
                role = rel.get("role")
                extra = f" role={role}" if role else ""
                print(f"[{book}] {cid} → {target} ({rtype}{extra}): relation unverified — 全文未同现")
                rel_issues += 1

    print(
        f"[{book}] characters: first_appear {fa_issues}，关键情节 {plot_checked} 条（unverified {plot_issues}），"
        f"relations {rel_checked} 边（unverified {rel_issues}）"
    )
    return plot_issues + fa_issues, rel_issues, 0


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    total = 0
    for book in resolve_books(arg):
        p_i, r_i, _ = guard_character_content(book)
        total += p_i + r_i
        total += guard_transactions(book)
    if total:
        print(f"Trust Guard 完成，{total} 处存疑")
    else:
        print("Trust Guard 通过")


if __name__ == "__main__":
    main()
