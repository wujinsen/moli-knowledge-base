#!/usr/bin/env python3
"""金瓶梅 transaction 扩展（jpm-tx-015 起）。

重生成：python scripts/seed_jpm_transactions.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "content" / "transactions" / "金瓶梅"

# id, subtype, chapter, amount, currency, amount_normalized, conversion_note, parties..., item, pools, tags, summary, body
TXS: list[dict] = [
    dict(
        id="jpm-tx-015", subtype="财礼", chapter=1, amount=1, currency="银",
        amount_normalized=1, conversion_note="一两银子，直接计",
        buyer="花子虚", seller="西门庆", item_ref="结拜分资",
        pool_from="帮闲圈", pool_to="西门庆府", tags=["结拜", "帮闲"],
        summary="花子虚先送一两分资，结拜十弟兄预备。",
        body="第一回，花子虚遣小厮送分资一两，西门庆结拜弟兄会期用度之一。",
    ),
    dict(
        id="jpm-tx-016", subtype="馈赠", chapter=1, amount=50, currency="银",
        amount_normalized=50, conversion_note="五十两赏银，直接计",
        buyer="知县", payee="武松", item_ref="打虎赏银",
        pool_from="官府", pool_to="帮闲圈", tags=["武松", "打虎"],
        summary="知县赐武松打虎赏银五十两，散与众猎户。",
        body="第一回，武松景阳冈打虎，知县赏银五十两，武松尽散猎户。",
    ),
    dict(
        id="jpm-tx-017", subtype="买卖", chapter=1, amount=10, currency="银",
        amount_normalized=10, conversion_note="十数两典房，取整十两",
        buyer="武大郎", seller="王皇亲", item_ref="县前楼典房",
        pool_from="帮闲圈", pool_to="清河县", tags=["武大郎", "潘金莲"],
        summary="武大凑十数两银子，典县前楼上下两层四间。",
        body="第一回，武大与潘金莲典得清河县前楼房居住，卖炊饼度日。",
    ),
    dict(
        id="jpm-tx-018", subtype="贿赂", chapter=23, amount=100, currency="银",
        amount_normalized=100, conversion_note="百两认干礼，直接计",
        buyer="西门庆", payee="翟管家", item_ref="认干爹礼",
        pool_from="西门庆府", pool_to="蔡太师府", tags=["政商", "翟管家"],
        summary="西门庆认翟管家为干爹，初次进百两礼银。",
        body="第二十三回，西门庆经翟管家打通蔡京门路，认干亲送礼百两。",
    ),
    dict(
        id="jpm-tx-019", subtype="酒席宴请", chapter=1, amount=4, currency="银",
        amount_normalized=4, conversion_note="四两买办猪羊酒礼，直接计",
        buyer="西门庆", item_ref="结拜买办",
        pool_from="西门庆府", pool_to="玉皇庙", tags=["结拜", "宴席"],
        summary="初二买办猪羊金华酒等四两，预备初三结拜。",
        body="第一回，西门庆称四两银子买猪羊、金华酒、香烛等，送玉皇庙吴道官。",
    ),
    dict(
        id="jpm-tx-020", subtype="奴婢买卖", chapter=1, amount=30, currency="银",
        amount_normalized=30, conversion_note="三十两转卖，直接计",
        buyer="张大户", seller="潘妈妈", payee="潘金莲", item_ref="潘金莲身契",
        pool_from="帮闲圈", pool_to="妻妾奴婢", tags=["潘金莲", "身契"],
        summary="潘妈妈将潘金莲三十两转卖张大户家。",
        body="第一回，潘金莲十五岁由王招宣府转出，三十两卖与张大户。",
    ),
]


def opt(key: str, val) -> str:
    return f"{key}: {val}\n" if val else ""


def write(t: dict) -> None:
    disputed = "conversion_disputed: true\n" if t.get("conversion_disputed") else ""
    parties = "".join(opt(k, t.get(k)) for k in ("buyer", "seller", "payee"))
    text = f"""---
id: {t['id']}
type: transaction
book: 金瓶梅
subtype: {t['subtype']}
amount: {t['amount']}
currency: {t['currency']}
amount_normalized: {t['amount_normalized']}
conversion_note: {t['conversion_note']}
{disputed}{parties}item_ref: {t['item_ref']}
pool_from: {t['pool_from']}
pool_to: {t['pool_to']}
chapter: {t['chapter']}
source: chapters/金瓶梅/{t['chapter']:03d}.md
tags: [{', '.join(t['tags'])}]
summary: {t['summary']}
---

{t['body']}
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{t['id']}.md").write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    for t in TXS:
        write(t)
    print(f"[金瓶梅] {len(TXS)} transactions (015+) → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
