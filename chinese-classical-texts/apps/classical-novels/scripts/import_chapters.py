#!/usr/bin/env python3
"""把 raw 原文导入 Astro content/chapters/<书>/，供阅读器使用。

源（chinese-classical-texts/raw）:
  红楼梦: daizhige/集藏/小说/红楼梦.txt（程高本 120 回）
  红楼梦脂砚斋本: daizhige/集藏/小说/脂砚斋全评石头记.txt（脂砚斋本 80 回，含批语）
  金瓶梅词话本: daizhige/集藏/小说/金瓶梅.txt（词话本，100 回）
  金瓶梅崇祯本: editions/jinpingmei/JingPingMei-ZhCN/chapters/JPM*.tex（100 回）
  金瓶梅张竹坡评本: editions/jinpingmei/JPM_Congzhen/html_ori/part*.html（100 回，含眉批旁批）
  西游记: editions/xiyouji/明代金陵世德堂本 简体版/*.txt（100 回）
  西游记通本: daizhige/集藏/小说/西游记.txt（殆知阁通本 100 回，与世德堂对勘）

用法: python scripts/import_chapters.py [红楼梦|…|西游记通本|all|金瓶梅全部]
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from _common import CHAPTER_DIR, ROOT

CCT_ROOT = ROOT.parent.parent

# type: txt_dir | daizhige_txt
SOURCES: dict[str, dict] = {
    "红楼梦": {
        "path": CCT_ROOT / "raw" / "daizhige" / "集藏" / "小说" / "红楼梦.txt",
        "edition": "程高本",
        "kind": "daizhige_txt",
        "book": "红楼梦",
    },
    "红楼梦脂砚斋本": {
        "path": CCT_ROOT / "raw" / "daizhige" / "集藏" / "小说" / "脂砚斋全评石头记.txt",
        "edition": "脂砚斋本",
        "kind": "zhiben_txt",
        "book": "红楼梦",
        "out_subdir": "脂砚斋本",
    },
    "金瓶梅": {
        "path": CCT_ROOT / "raw" / "daizhige" / "集藏" / "小说" / "金瓶梅.txt",
        "edition": "词话本",
        "kind": "daizhige_txt",
        "book": "金瓶梅",
        "out_subdir": "词话本",
    },
    "金瓶梅崇祯本": {
        "path": CCT_ROOT / "raw" / "editions" / "jinpingmei" / "JingPingMei-ZhCN" / "chapters",
        "edition": "崇祯本",
        "kind": "jpm_latex_dir",
        "book": "金瓶梅",
        "out_subdir": "崇祯本",
    },
    "金瓶梅张竹坡评本": {
        "path": CCT_ROOT / "raw" / "editions" / "jinpingmei" / "JPM_Congzhen" / "html_ori",
        "edition": "张竹坡评本",
        "kind": "jpm_congzhen_html",
        "book": "金瓶梅",
        "out_subdir": "张竹坡评本",
    },
    "西游记": {
        "path": CCT_ROOT / "raw" / "editions" / "xiyouji" / "明代金陵世德堂本 简体版",
        "edition": "世德堂本",
        "kind": "txt_dir",
        "book": "西游记",
    },
    "西游记通本": {
        "path": CCT_ROOT / "raw" / "daizhige" / "集藏" / "小说" / "西游记.txt",
        "edition": "通本",
        "kind": "daizhige_txt",
        "book": "西游记",
        "out_subdir": "通本",
    },
}

ZIPI = re.compile(r"【([^】]+)】")

# 正文回目标题在同 line，或仅「第X回」且下一行是回目
CHAPTER_HEAD = re.compile(
    r"^第\s*([一二三四五六七八九十百零〇两\d]+)\s*回[　\s]+(.{2,})$"
)
CHAPTER_ONLY = re.compile(
    r"^第\s*([一二三四五六七八九十百零〇两\d]+)\s*回\s*$"
)
CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "两": 2}
XYJ_FNAME = re.compile(r"^(\d+)\s+(.+)\.txt$", re.I)
JPM_TEX = re.compile(r"^JPM(\d+)\.tex$", re.I)
JPM_HTML_TITLE = re.compile(
    r"^第\s*([一二三四五六七八九十百零〇两\d]+)\s*[回囘]\s*(.+)$"
)
LATEX_CHAPTER = re.compile(r"\\chapter\{([^}]+)\}")
TEXTUNI = re.compile(r"\\textuni\{([0-9A-Fa-f]+)\}")
PZ_SPAN = re.compile(r'<span class="pz">(.*?)</span>', re.S)
TAG_RE = re.compile(r"<[^>]+>")


def cn_numeral_to_int(s: str) -> int | None:
    """中文数字 → int；兼容殆知阁「第一一三」「第一零六」逐位写法。"""
    s = re.sub(r"\s+", "", s)
    if s.isdigit():
        return int(s)
    digit = CN_DIGIT
    if len(s) >= 2 and all(c in digit for c in s):
        return int("".join(str(digit[c]) for c in s))
    if s == "十":
        return 10
    if "百" in s:
        parts = s.split("百", 1)
        hi = cn_numeral_to_int(parts[0]) if parts[0] else 1
        lo = cn_numeral_to_int(parts[1]) if len(parts) > 1 and parts[1] else 0
        return hi * 100 + lo
    if "十" in s:
        parts = s.split("十", 1)
        hi = cn_numeral_to_int(parts[0]) if parts[0] else 1
        lo = cn_numeral_to_int(parts[1]) if len(parts) > 1 and parts[1] else 0
        return hi * 10 + lo
    if len(s) == 1 and s in digit:
        return digit[s]
    return None


def find_body_start(lines: list[str]) -> int:
    """跳过文件头目录：正文第一回下一行通常是「　　」起首段落。"""
    for i, line in enumerate(lines):
        if CHAPTER_HEAD.match(line.strip()):
            if i + 1 < len(lines) and lines[i + 1].startswith("　　"):
                return i
    for i, line in enumerate(lines):
        if CHAPTER_HEAD.match(line.strip()) or CHAPTER_ONLY.match(line.strip()):
            return i
    return 0


def peek_chapter_title(lines: list[str], idx: int) -> str:
    for j in range(idx + 1, min(idx + 4, len(lines))):
        t = lines[j].strip().lstrip("　 ")
        if not t:
            continue
        if t.startswith("　"):
            break
        if len(t) <= 80 and not CHAPTER_ONLY.match(t) and not CHAPTER_HEAD.match(t):
            return t
        break
    return ""


def parse_chapter_line(lines: list[str], idx: int) -> tuple[int, str] | None:
    line = lines[idx].strip()
    m = CHAPTER_HEAD.match(line)
    if m:
        n = cn_numeral_to_int(m.group(1))
        if n is None:
            return None
        return n, m.group(2).strip() or f"第{n}回"
    m = CHAPTER_ONLY.match(line)
    if m:
        n = cn_numeral_to_int(m.group(1))
        if n is None:
            return None
        title = peek_chapter_title(lines, idx) or f"第{n}回"
        return n, title
    return None


def inline_with_zhipi(text: str) -> str:
    """正文内嵌脂批 → span.zhipi。"""
    parts = ZIPI.split(text)
    out: list[str] = []
    for i, part in enumerate(parts):
        if not part:
            continue
        if i % 2 == 0:
            out.append(html.escape(part))
        else:
            out.append(f'<span class="zhipi">{html.escape(part)}</span>')
    return "".join(out)


def plain_to_html(text: str, *, zhiben: bool = False) -> str:
    """Plain text → HTML 段落（阅读器 prose-cn 用）。"""
    lines = text.splitlines()
    blocks: list[str] = []
    buf: list[str] = []

    def flush():
        if not buf:
            return
        para = "".join(buf).strip()
        if para:
            inner = inline_with_zhipi(para) if zhiben else html.escape(para)
            blocks.append(f"<p>{inner}</p>")
        buf.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        # 全角缩进开头的新段
        if stripped.startswith("　") and buf:
            flush()
        buf.append(stripped.lstrip("　"))
    flush()
    return "\n\n".join(blocks)


def split_daizhige_txt(text: str) -> list[tuple[int, str, str]]:
    """Split 殆知阁整本书 txt into (number, title, body)."""
    lines = text.splitlines()
    start = find_body_start(lines)

    chapters: list[tuple[int, str, str]] = []
    by_num: dict[int, int] = {}
    current_num = 0
    current_title = ""
    body_lines: list[str] = []
    skip_title_line = False

    def flush_ch():
        nonlocal current_num, current_title, body_lines
        if current_num:
            body = "\n".join(body_lines).strip()
            if current_num in by_num:
                chapters[by_num[current_num]] = (current_num, current_title, body)
            else:
                by_num[current_num] = len(chapters)
                chapters.append((current_num, current_title, body))
        body_lines = []

    i = start
    while i < len(lines):
        parsed = parse_chapter_line(lines, i)
        if parsed:
            flush_ch()
            current_num, current_title = parsed
            skip_title_line = bool(CHAPTER_ONLY.match(lines[i].strip()))
            i += 1
            if skip_title_line:
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    t = lines[i].strip().lstrip("　 ")
                    if t and not parse_chapter_line(lines, i):
                        i += 1
            continue
        if current_num:
            body_lines.append(lines[i])
        i += 1
    flush_ch()
    chapters.sort(key=lambda x: x[0])
    return chapters


def write_chapter(
    book: str,
    n: int,
    title: str,
    body: str,
    edition: str,
    source: str,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fm = (
        "---\n"
        "type: chapter\n"
        f"book: {book}\n"
        f"number: {n}\n"
        f"title: {title}\n"
        f"edition: {edition}\n"
        f"source: {source}\n"
        "characters: []\n"
        "locations: []\n"
        "---\n\n"
    )
    (out_dir / f"{n:03d}.md").write_text(fm + body + "\n", encoding="utf-8")


def import_txt_dir(book: str, src: Path, edition: str, out_subdir: str | None = None) -> int:
    out_dir = CHAPTER_DIR / book / out_subdir if out_subdir else CHAPTER_DIR / book
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in sorted(src.glob("*.txt")):
        m = XYJ_FNAME.match(p.name)
        if not m:
            continue
        n = int(m.group(1))
        title = m.group(2).strip()
        raw = p.read_text(encoding="utf-8")
        lines = raw.splitlines()
        if lines and CHAPTER_HEAD.match(lines[0].strip()):
            body_text = "\n".join(lines[1:])
            hm = CHAPTER_HEAD.match(lines[0].strip())
            if hm and hm.group(2).strip():
                title = hm.group(2).strip()
        else:
            body_text = raw
        body = plain_to_html(body_text)
        rel = p.relative_to(CCT_ROOT).as_posix()
        write_chapter(book, n, title, body, edition, rel, out_dir)
        count += 1
    return count


def clean_jpm_latex(text: str) -> str:
    """JingPingMei-ZhCN LaTeX 片段 → 纯文本。"""
    text = TEXTUNI.sub(lambda m: chr(int(m.group(1), 16)), text)
    text = text.replace(r"\textShan ", "搧")
    text = text.replace(r"\textShan{", "搧")
    text = text.replace(r"\textMaoJi ", "毬")
    text = text.replace(r"\textMaoBa ", "巴")
    text = text.replace(r"\KG", "　　")
    text = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})*", "", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def latex_to_html(body: str) -> str:
    """LaTeX 章正文 → HTML 段落。"""
    blocks: list[str] = []
    buf: list[str] = []
    in_quote = False
    quote_buf: list[str] = []

    def flush_para():
        nonlocal buf
        if not buf:
            return
        para = clean_jpm_latex("\n".join(buf))
        if para:
            blocks.append(f"<p>{html.escape(para)}</p>")
        buf = []

    def flush_quote():
        nonlocal quote_buf, in_quote
        if not quote_buf:
            in_quote = False
            return
        para = clean_jpm_latex("\n".join(quote_buf))
        if para:
            blocks.append(f"<p>{html.escape(para)}</p>")
        quote_buf = []
        in_quote = False

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            if in_quote:
                flush_quote()
            else:
                flush_para()
            continue
        if stripped.startswith(r"\["):
            flush_para()
            in_quote = True
            rest = stripped.lstrip(r"\[").rstrip("\\").rstrip("]")
            if rest:
                quote_buf.append(rest)
            continue
        if in_quote:
            if stripped.endswith(r"\]"):
                quote_buf.append(stripped.rstrip(r"\]").rstrip("\\"))
                flush_quote()
            else:
                quote_buf.append(stripped)
            continue
        if stripped.startswith("\\") and not stripped.startswith("\\["):
            continue
        buf.append(stripped)

    if in_quote:
        flush_quote()
    flush_para()
    return "\n\n".join(blocks)


def parse_jpm_tex(path: Path) -> tuple[int, str, str]:
    raw = path.read_text(encoding="utf-8")
    m = JPM_TEX.match(path.name)
    if not m:
        raise ValueError(path.name)
    n = int(m.group(1))
    cm = LATEX_CHAPTER.search(raw)
    if not cm:
        raise ValueError(f"无 \\chapter: {path}")
    title = cm.group(1).replace(r"\KG", "　　").strip()
    start = cm.end()
    body = raw[start:]
    return n, title, latex_to_html(body)


def import_jpm_latex_dir(
    book: str, src: Path, edition: str, out_subdir: str | None = None
) -> int:
    out_dir = CHAPTER_DIR / book / out_subdir if out_subdir else CHAPTER_DIR / book
    count = 0
    for p in sorted(src.glob("JPM*.tex")):
        n, title, body = parse_jpm_tex(p)
        rel = p.relative_to(CCT_ROOT).as_posix()
        write_chapter(book, n, title, body, edition, rel, out_dir)
        count += 1
    return count


def pz_to_zhupi(fragment: str) -> str:
    """html_ori 内 span.pz → span.zhupi。"""
    kind = "批"
    if "眉" in fragment[:40] and "批" in fragment[:40]:
        kind = "眉批"
    elif "旁" in fragment[:40] and "批" in fragment[:40]:
        kind = "旁批"
    text = TAG_RE.sub("", fragment)
    text = text.replace("眉批", "").replace("旁批", "").replace("眉", "").replace("旁", "").replace("批", "")
    text = re.sub(r"\s+", "", text)
    if not text:
        return ""
    return f'<span class="zhupi" title="{html.escape(kind)}">{html.escape(text)}</span>'


def html_para_to_inline(para_html: str) -> str:
    """段落 HTML：批语 span.pz → zhupi，其余转义。"""
    out: list[str] = []
    pos = 0
    needle = '<span class="pz">'
    while True:
        start = para_html.find(needle, pos)
        if start < 0:
            break
        if start > pos:
            out.append(html.escape(TAG_RE.sub("", para_html[pos:start])))
        depth = 1
        i = start + len(needle)
        while i < len(para_html) and depth:
            next_open = para_html.find("<span", i)
            next_close = para_html.find("</span>", i)
            if next_close < 0:
                break
            if next_open >= 0 and next_open < next_close:
                depth += 1
                i = next_open + 5
            else:
                depth -= 1
                if depth == 0:
                    inner = para_html[start + len(needle) : next_close]
                    zh = pz_to_zhupi(inner)
                    if zh:
                        out.append(zh)
                    pos = next_close + len("</span>")
                    break
                i = next_close + len("</span>")
        else:
            break
    tail = para_html[pos:]
    if tail:
        out.append(html.escape(TAG_RE.sub("", tail)))
    return "".join(out)


def parse_jpm_html(path: Path) -> tuple[int, str, str]:
    raw = path.read_text(encoding="utf-8")
    tm = re.search(r"<title>([^<]+)</title>", raw)
    if not tm:
        raise ValueError(f"无 title: {path}")
    title_line = tm.group(1).strip()
    hm = JPM_HTML_TITLE.match(title_line)
    if not hm:
        raise ValueError(f"无法解析回目: {title_line}")
    n = cn_numeral_to_int(hm.group(1))
    if n is None:
        raise ValueError(f"无法解析回数: {title_line}")
    title = hm.group(2).strip()

    blocks: list[str] = []
    for cls in ("calibre6", "poetry", "poem", "poemi"):
        for m in re.finditer(
            rf'<p class="{cls}">(.*?)</p>', raw, re.S
        ):
            inner = m.group(1).strip()
            if not inner:
                continue
            inline = html_para_to_inline(inner)
            if inline:
                blocks.append(f"<p>{inline}</p>")
    return n, title, "\n\n".join(blocks)


def import_jpm_congzhen_html(
    book: str, src: Path, edition: str, out_subdir: str | None = None
) -> int:
    out_dir = CHAPTER_DIR / book / out_subdir if out_subdir else CHAPTER_DIR / book
    count = 0
    for p in sorted(src.glob("part*.html")):
        try:
            n, title, body = parse_jpm_html(p)
        except ValueError:
            continue
        if not body.strip():
            continue
        rel = p.relative_to(CCT_ROOT).as_posix()
        write_chapter(book, n, title, body, edition, rel, out_dir)
        count += 1
    return count


def import_daizhige_txt(
    book: str, src: Path, edition: str, out_subdir: str | None = None, *, zhiben: bool = False
) -> int:
    out_dir = CHAPTER_DIR / book / out_subdir if out_subdir else CHAPTER_DIR / book
    text = src.read_text(encoding="utf-8")
    rel = src.relative_to(CCT_ROOT).as_posix()
    count = 0
    for n, title, body_text in split_daizhige_txt(text):
        body = plain_to_html(body_text, zhiben=zhiben)
        write_chapter(book, n, title, body, edition, rel, out_dir)
        count += 1
    return count


def import_book(key: str) -> int:
    cfg = SOURCES[key]
    src = cfg["path"]
    edition = cfg["edition"]
    kind = cfg["kind"]
    book = cfg.get("book", key)
    out_subdir = cfg.get("out_subdir")
    if not src.exists():
        raise SystemExit(f"源不存在: {src}")
    if kind == "txt_dir":
        n = import_txt_dir(book, src, edition, out_subdir)
    elif kind == "daizhige_txt":
        n = import_daizhige_txt(book, src, edition, out_subdir)
    elif kind == "zhiben_txt":
        n = import_daizhige_txt(book, src, edition, out_subdir, zhiben=True)
    elif kind == "jpm_latex_dir":
        n = import_jpm_latex_dir(book, src, edition, out_subdir)
    elif kind == "jpm_congzhen_html":
        n = import_jpm_congzhen_html(book, src, edition, out_subdir)
    else:
        raise SystemExit(f"未知 kind: {kind}")
    dest = CHAPTER_DIR / book / out_subdir if out_subdir else CHAPTER_DIR / book
    print(f"[{book}/{edition}] 导入 {n} 回 → {dest}")
    return n


JPM_ALL = ["金瓶梅", "金瓶梅崇祯本", "金瓶梅张竹坡评本"]


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(
            f"用法: python scripts/import_chapters.py <{'|'.join(SOURCES)}|all|金瓶梅全部>"
        )
    arg = sys.argv[1]
    if arg == "all":
        books = list(SOURCES)
    elif arg == "金瓶梅全部":
        books = JPM_ALL
    else:
        books = [arg]
    for key in books:
        if key not in SOURCES:
            raise SystemExit(f"未知书目: {key}")
        import_book(key)


if __name__ == "__main__":
    main()
