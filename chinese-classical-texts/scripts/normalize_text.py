#!/usr/bin/env python3
"""古籍检索语料归一化（坑2：异体字/占位符/繁简混排污染 BM25 与向量召回）。

铁律：**raw 永不修改**。本工具只读 raw，输出到独立的语料副本目录，
供全文索引 / 向量库使用；展示用的原文仍按原书字体保留（见 AGENTS）。

归一化内容（默认全开，繁→简需 opt-in）：
  - 去数字化占位符：［…］〔…〕（殆知阁用于无法数字化的字符）
  - 全角字母数字 → 半角
  - 折叠多余空白
  - 繁 → 简：--to-simplified（需 `pip install opencc-python-reimplemented`）

用法:
  python scripts/normalize_text.py raw/daizhige/集藏/小说/金瓶梅.txt -o build/corpus/jinpingmei
  python scripts/normalize_text.py 某文件.txt --to-simplified
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # chinese-classical-texts

# 占位符：成对的全角/方头括号内含内容，整体视为非正文噪声
PLACEHOLDER_RE = re.compile(r"[［〔][^］〕]*[］〕]")
WS_RE = re.compile(r"[ \t\u3000]+")
MULTINL_RE = re.compile(r"\n{3,}")


def _to_halfwidth_alnum(s: str) -> str:
    out = []
    for ch in s:
        code = ord(ch)
        # 全角数字/大小写字母 → 半角
        if 0xFF10 <= code <= 0xFF19 or 0xFF21 <= code <= 0xFF3A or 0xFF41 <= code <= 0xFF5A:
            out.append(chr(code - 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)


_OPENCC = None


def _get_opencc():
    global _OPENCC
    if _OPENCC is None:
        try:
            from opencc import OpenCC  # type: ignore

            _OPENCC = OpenCC("t2s")
        except Exception:
            raise SystemExit(
                "繁→简需要 opencc：pip install opencc-python-reimplemented"
            )
    return _OPENCC


def normalize(text: str, *, to_simplified: bool = False) -> str:
    """归一化一段文本（用于索引/向量，不用于展示）。"""
    # 占位符清理必须在 NFKC 之前：NFKC 会把全角［］转半角，导致匹配失效
    text = PLACEHOLDER_RE.sub("", text)
    # NFKC：全角字母数字/标点 → 半角，统一兼容字符
    text = unicodedata.normalize("NFKC", text)
    text = _to_halfwidth_alnum(text)
    if to_simplified:
        text = _get_opencc().convert(text)
    # 折叠空白
    lines = [WS_RE.sub(" ", ln).strip() for ln in text.splitlines()]
    text = "\n".join(lines)
    text = MULTINL_RE.sub("\n\n", text)
    return text.strip() + "\n"


def _resolve_out(out: Path | None, src: Path) -> Path:
    if out:
        return out
    return ROOT / "build" / "corpus" / src.name


def main() -> int:
    ap = argparse.ArgumentParser(description="古籍检索语料归一化（raw 只读）")
    ap.add_argument("src", help="raw 下的文件或目录")
    ap.add_argument("-o", "--out", help="输出目录（默认 build/corpus/<名>）")
    ap.add_argument("--to-simplified", action="store_true", help="繁→简（需 opencc）")
    ap.add_argument("--ext", default=".txt,.md", help="处理的扩展名，逗号分隔")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_absolute():
        src = ROOT / src
    if not src.exists():
        print(f"不存在: {src}", file=sys.stderr)
        return 1

    exts = {e if e.startswith(".") else f".{e}" for e in args.ext.split(",")}

    if src.is_file():
        files = [src]
        base = src.parent
    else:
        files = [p for p in sorted(src.rglob("*")) if p.suffix in exts]
        base = src

    out_dir = _resolve_out(Path(args.out) if args.out else None, src)
    out_dir.mkdir(parents=True, exist_ok=True)

    n = 0
    for p in files:
        rel = p.relative_to(base) if src.is_dir() else p.name
        text = p.read_text(encoding="utf-8", errors="replace")
        norm = normalize(text, to_simplified=args.to_simplified)
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(norm, encoding="utf-8")
        n += 1
    print(f"归一化 {n} 个文件 → {out_dir}（raw 未改动）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
