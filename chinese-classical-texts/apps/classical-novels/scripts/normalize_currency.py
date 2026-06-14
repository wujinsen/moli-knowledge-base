#!/usr/bin/env python3
"""金瓶梅 transaction 货币换算校验 / 补全辅助。

读取 scripts/jinpingmei_currency.yaml 规则，扫描 transactions/金瓶梅/*.md：
- 报告 amount_normalized 缺失
- 可选 --fix 写入换算字段（仅当缺失时）

用法:
  python scripts/normalize_currency.py           # 仅报告
  python scripts/normalize_currency.py --fix     # 补全缺失 normalized
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TX_DIR = ROOT / "src" / "content" / "transactions" / "金瓶梅"
YAML_PATH = ROOT / "scripts" / "jinpingmei_currency.yaml"

try:
    import yaml  # type: ignore
except ImportError:
    sys.exit("需要 PyYAML: pip install pyyaml")

from _common import parse_frontmatter


def load_rules() -> dict:
    return yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))


def normalize(amount: float, currency: str, rules: dict) -> tuple[float | None, str, bool]:
    units = rules.get("units", {})
    cfg = units.get(currency)
    if not cfg:
        return None, "未知单位", False
    strategy = cfg.get("strategy", "direct")
    factor = cfg.get("factor", 1)
    note = cfg.get("note", "")
    disputed = bool(cfg.get("disputed"))
    if strategy == "direct":
        val = amount
        conv_note = note or f"{currency}，直接计"
    else:
        val = amount / factor if factor else None
        conv_note = f"{amount}{currency} ÷ {factor} ≈ {val:.3f} 两" + (f"（{note}）" if note else "")
        if currency in ("钱", "文") and amount >= rules.get("disputed_threshold_qian", 500):
            disputed = True
    return val, conv_note, disputed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    args = parser.parse_args()
    rules = load_rules()
    issues = 0
    fixed = 0

    for path in sorted(TX_DIR.glob("*.md")):
        fm, body = parse_frontmatter(path)
        amount = fm.get("amount")
        currency = fm.get("currency")
        if amount is None or not currency:
            print(f"[skip] {path.name}: 无 amount/currency")
            continue
        norm = fm.get("amount_normalized")
        val, note, disputed = normalize(float(amount), currency, rules)
        if norm is None and val is not None:
            issues += 1
            print(f"[missing] {path.name}: {amount}{currency} → 应 {val:.3f} 两")
            if args.fix:
                text = path.read_text(encoding="utf-8")
                insert = f"amount_normalized: {val}\nconversion_note: {note}\n"
                if disputed:
                    insert += "conversion_disputed: true\n"
                text = re.sub(
                    r"(currency: \S+\n)",
                    rf"\1{insert}",
                    text,
                    count=1,
                )
                path.write_text(text, encoding="utf-8")
                fixed += 1
        elif norm is not None and val is not None and abs(norm - val) > 0.01:
            issues += 1
            print(f"[drift] {path.name}: normalized={norm} vs 规则={val:.3f}")

    if issues == 0:
        print("[金瓶梅] 全部 transaction 换算 OK")
    elif args.fix:
        print(f"[金瓶梅] 补全 {fixed} 条")
    else:
        print(f"[金瓶梅] {issues} 条待处理（加 --fix 补全）")


if __name__ == "__main__":
    main()
