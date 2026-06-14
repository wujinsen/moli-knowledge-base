#!/usr/bin/env python3
"""金瓶梅 economic_event（financial subtype）首批样本。

重生成：python scripts/seed_jpm_financial.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "content" / "events" / "金瓶梅"

EVENTS: list[dict] = [
    dict(
        id="jpm-fe-001", title="西门庆生药铺经营", financial_kind="药铺",
        chapters=[1], characters=["西门庆"],
        amount_liang=500, transaction_refs=[],
        tags=["经营投资", "西门府"],
        summary="清河县五间门面生药铺，西门庆家业根基，后扩绒线铺、酒店。",
        body="## 出处\n\n第一回：西门庆父亲西门达「在清河县前开着一个大大的生药铺」。\n\n## 图谱\n\n关联 `location` 生药铺 · 白银流「经营投资」池。\n",
    ),
    dict(
        id="jpm-fe-002", title="蔡京寿礼行贿链", financial_kind="贿赂",
        chapters=[27], characters=["西门庆", "蔡京", "翟管家"],
        amount_liang=50, transaction_refs=["jpm-tx-003", "jpm-tx-011"],
        tags=["政商", "白银流"],
        summary="西门庆经翟管家向蔡太师进寿礼，换得官场庇护。",
    ),
    dict(
        id="jpm-fe-003", title="李智应伯爵转贷", financial_kind="放债",
        chapters=[14], characters=["西门庆", "李智", "应伯爵", "黄四"],
        amount_liang=50, transaction_refs=["jpm-tx-010"],
        tags=["帮闲圈", "借贷"],
        summary="帮闲圈典型放贷链：西门庆→李智→黄四，应伯爵居中撮合。",
    ),
    dict(
        id="jpm-fe-004", title="绒线铺本钱拨付", financial_kind="经营",
        chapters=[14], characters=["西门庆", "韩道国"],
        transaction_refs=["jpm-tx-004"],
        tags=["经营投资"],
        summary="西门庆付韩道国绒线铺本钱，扩大家业经营面。",
    ),
    dict(
        id="jpm-fe-005", title="李瓶儿私房物资变现", financial_kind="遗产",
        chapters=[16, 17], characters=["西门庆", "李瓶儿"],
        locations=["李瓶儿房"],
        amount_liang=380, transaction_refs=[],
        tags=["李瓶儿", "经营投资"],
        summary="李瓶儿箱藏香蜡水银等，经经纪变卖三百八十两，凑盖房与过门。",
    ),
    dict(
        id="jpm-fe-006", title="结拜十弟兄买办", financial_kind="经营",
        chapters=[1], characters=["西门庆", "应伯爵", "花子虚"],
        locations=["玉皇庙", "西门府"],
        amount_liang=4, transaction_refs=["jpm-tx-019", "jpm-tx-015"],
        tags=["结拜", "帮闲"],
        summary="初三玉皇庙结拜，猪羊酒礼与分资汇聚帮闲圈。",
        body="## 关联\n\n[[玉皇庙]] 结拜 · transaction [[jpm-tx-019]]、[[jpm-tx-015]]。\n",
    ),
    dict(
        id="jpm-fe-007", title="认翟管家干亲", financial_kind="贿赂",
        chapters=[23], characters=["西门庆", "翟管家"],
        locations=["清河县"],
        amount_liang=100, transaction_refs=["jpm-tx-018"],
        tags=["政商", "干亲"],
        summary="西门庆百两认干礼，打通蔡京府门路。",
        body="## 关联\n\n[[翟管家]] 政商中介 · transaction [[jpm-tx-018]]。\n",
    ),
]


def write(e: dict) -> None:
    amt = e.get("amount_liang")
    amt_line = f"amount_liang: {amt}\n" if amt is not None else ""
    refs = e.get("transaction_refs", [])
    locs = e.get("locations", [])
    loc_line = f"locations: [{', '.join(locs)}]" if locs else "locations: []"
    text = f"""---
id: {e['id']}
type: event
book: 金瓶梅
subtype: financial
financial_kind: {e['financial_kind']}
title: {e['title']}
chapters: [{', '.join(str(c) for c in e['chapters'])}]
characters: [{', '.join(e.get('characters', []))}]
{loc_line}
{amt_line}transaction_refs: [{', '.join(refs)}]
tags: [{', '.join(e.get('tags', []))}]
summary: {e['summary']}
source: chapters/金瓶梅/
---

{e.get('body', '')}
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{e['id']}.md").write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    for e in EVENTS:
        write(e)
    print(f"[金瓶梅] {len(EVENTS)} 经济事件 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
