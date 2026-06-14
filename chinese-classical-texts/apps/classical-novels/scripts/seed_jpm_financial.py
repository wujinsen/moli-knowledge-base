#!/usr/bin/env python3
"""金瓶梅 economic_event（financial subtype）样本与专题链（J6）。

重生成：python scripts/seed_jpm_financial.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "content" / "events" / "金瓶梅"

EVENTS: list[dict] = [
    dict(
        id="jpm-fe-001", title="西门庆生药铺经营", financial_kind="药铺",
        chapters=[1], characters=["西门庆"], locations=["西门庆生药铺"],
        amount_liang=500, transaction_refs=[],
        prev=None, next="jpm-fe-006",
        tags=["经营投资", "西门府"],
        summary="清河县五间门面生药铺，西门庆家业根基，后扩绒线铺、酒店。",
        body="## 出处\n\n第一回：西门庆父亲西门达「在清河县前开着一个大大的生药铺」。\n\n## 图谱\n\n关联 [[西门庆生药铺]] · 白银流「经营投资」池。\n",
    ),
    dict(
        id="jpm-fe-006", title="结拜十弟兄买办", financial_kind="经营",
        chapters=[1], characters=["西门庆", "应伯爵", "花子虚"],
        locations=["玉皇庙", "西门府"],
        amount_liang=4, transaction_refs=["jpm-tx-019", "jpm-tx-015"],
        prev="jpm-fe-001", next="jpm-fe-005",
        tags=["结拜", "帮闲"],
        summary="初三玉皇庙结拜，猪羊酒礼与分资汇聚帮闲圈。",
        body="## 关联\n\n[[玉皇庙]] 结拜 · transaction [[jpm-tx-019]]、[[jpm-tx-015]]。\n",
    ),
    dict(
        id="jpm-fe-005", title="李瓶儿私房物资变现", financial_kind="遗产",
        chapters=[16, 17], characters=["西门庆", "李瓶儿"],
        locations=["李瓶儿房"],
        amount_liang=380, transaction_refs=["jpm-tx-021"],
        prev="jpm-fe-006", next="jpm-fe-007",
        tags=["李瓶儿", "经营投资"],
        summary="李瓶儿箱藏香蜡水银等，经经纪变卖三百八十两，凑盖房与过门。",
        body="## 关联\n\ntransaction [[jpm-tx-021]] · 注入经营投资池。\n",
    ),
    dict(
        id="jpm-fe-007", title="认翟管家干亲", financial_kind="贿赂",
        chapters=[23], characters=["西门庆", "翟管家"],
        locations=["清河县"],
        amount_liang=100, transaction_refs=["jpm-tx-018"],
        prev="jpm-fe-005", next="jpm-fe-009",
        tags=["政商", "干亲"],
        summary="西门庆百两认干礼，打通蔡京府门路。",
        body="## 关联\n\n[[翟管家]] 政商中介 · transaction [[jpm-tx-018]]。\n",
    ),
    dict(
        id="jpm-fe-009", title="来旺酒店本钱拨付", financial_kind="经营",
        chapters=[26], characters=["西门庆", "来旺"],
        locations=["西门府"],
        amount_liang=300, transaction_refs=["jpm-tx-002"],
        prev="jpm-fe-007", next="jpm-fe-002",
        tags=["经营投资", "酒店"],
        summary="付来旺三百两作酒店本钱，由生药铺向多业扩张。",
        body="## 出处\n\n第二十六回，西门庆付来旺三百两银子作酒店本钱。\n",
    ),
    dict(
        id="jpm-fe-002", title="蔡京寿礼行贿链", financial_kind="贿赂",
        chapters=[27], characters=["西门庆", "蔡京", "翟管家"],
        locations=["蔡太师府"],
        amount_liang=300, transaction_refs=["jpm-tx-003", "jpm-tx-011"],
        prev="jpm-fe-009", next="jpm-fe-008",
        tags=["政商", "白银流"],
        summary="西门庆经翟管家向蔡太师进寿礼三百两，换得官场庇护。",
        body="## 出处\n\n第二十七回，蔡太师寿辰，西门庆差人送三百两寿礼。\n",
    ),
    dict(
        id="jpm-fe-008", title="吴典恩借债", financial_kind="放债",
        chapters=[31], characters=["西门庆", "吴典恩"],
        locations=["西门府"],
        amount_liang=100, transaction_refs=["jpm-tx-006"],
        prev="jpm-fe-002", next="jpm-fe-004",
        tags=["帮闲圈", "借贷"],
        summary="吴典恩借西门庆一百两银子，约期归还，府内放债典型。",
        body="## 出处\n\n第三十一回，吴典恩借西门庆一百两。\n",
    ),
    dict(
        id="jpm-fe-004", title="绒线铺本钱拨付", financial_kind="经营",
        chapters=[33], characters=["西门庆", "韩道国"],
        locations=["绒线铺"],
        amount_liang=450, transaction_refs=["jpm-tx-004"],
        prev="jpm-fe-008", next="jpm-fe-003",
        tags=["经营投资"],
        summary="西门庆付韩道国绒线铺本钱四百五十两，扩大家业经营面。",
        body="## 出处\n\n第三十三回，绒线铺开张，本钱四百五十两。\n",
    ),
    dict(
        id="jpm-fe-003", title="李智应伯爵转贷", financial_kind="放债",
        chapters=[38], characters=["西门庆", "李智", "应伯爵", "黄四"],
        locations=["西门府"],
        amount_liang=1000, transaction_refs=["jpm-tx-010"],
        prev="jpm-fe-004", next="jpm-pe-001",
        tags=["帮闲圈", "借贷"],
        summary="应伯爵牵线，西门庆借出一千两与李智、黄四，帮闲圈核心放贷链。",
        body="## 出处\n\n第三十八回，应伯爵说合，西门庆借李智、黄四一千两。\n",
    ),
    dict(
        id="jpm-fe-011", title="蔡府二次寿礼", financial_kind="贿赂",
        chapters=[75], characters=["西门庆", "蔡京"],
        locations=["蔡太师府"],
        amount_liang=500, transaction_refs=["jpm-tx-022"],
        prev="jpm-pe-002", next="jpm-pe-003",
        tags=["政商", "寿礼"],
        summary="蔡京寿辰，西门庆再送五百两寿礼银，巩固政商关系。",
        body="## 出处\n\n第七十五回，西门庆再进蔡府寿礼五百两。\n",
    ),
    dict(
        id="jpm-fe-012", title="西门庆丧礼耗银", financial_kind="经营",
        chapters=[79], characters=["吴月娘", "应伯爵"],
        locations=["西门府"],
        amount_liang=200, transaction_refs=["jpm-tx-024"],
        prev="jpm-pe-003", next="jpm-pe-004",
        tags=["丧礼", "衰败"],
        summary="西门庆亡故，吴月娘治丧，帮闲张罗，耗费甚巨（摘记一笔）。",
        body="## 出处\n\n第七十九回，西门庆暴亡，丧礼开销。\n",
    ),
]

PLOT_EVENTS: list[dict] = [
    dict(
        id="jpm-pe-001", title="西门庆赴京得官", subtype="plot",
        chapters=[39], characters=["西门庆", "蔡京", "翟管家"],
        locations=["清河县"],
        prev="jpm-fe-003", next="jpm-pe-002",
        tags=["情节", "官场"],
        summary="西门庆进京贺寿后授提刑千户，政商合流达于顶点。",
        body="## 出处\n\n第三十九回前后，西门庆因蔡府关系得授山东提刑千户，清河县官商地位确立。\n\n## 图谱\n\n衔接 [[jpm-fe-003]] 转贷链 · 后接 [[jpm-pe-002]] 李瓶儿丧。\n",
    ),
    dict(
        id="jpm-pe-002", title="李瓶儿丧礼", subtype="plot",
        chapters=[60], characters=["西门庆", "李瓶儿", "吴月娘", "潘金莲"],
        locations=["西门府", "李瓶儿房"],
        prev="jpm-pe-001", next="jpm-fe-011",
        tags=["情节", "丧礼"],
        summary="李瓶儿病亡，西门庆大办丧仪，府内权力格局再洗牌。",
        body="## 出处\n\n第六十回，李瓶儿因产难而亡，西门庆耗银办丧，是「由盛转衰」的重要节点。\n\n## 图谱\n\n紧接 [[jpm-fe-005]] 私房变现线 · 后接 [[jpm-fe-011]] 二次寿礼。\n",
    ),
    dict(
        id="jpm-pe-003", title="西门庆暴亡", subtype="plot",
        chapters=[79], characters=["西门庆", "潘金莲", "吴月娘"],
        locations=["西门府"],
        prev="jpm-fe-011", next="jpm-fe-012",
        tags=["情节", "结局"],
        summary="西门庆纵欲而亡，西门府权力真空，家业急转直下。",
        body="## 出处\n\n第七十九回，西门庆宴后暴亡，词话本写「家主已亡，妇妾无主」。\n\n## 图谱\n\n与 [[胡僧药]] 纵欲线呼应 · 后接 [[jpm-fe-012]] 丧礼耗银。\n",
    ),
    dict(
        id="jpm-pe-004", title="西门府散", subtype="plot",
        chapters=[100], characters=["吴月娘", "陈经济", "庞春梅", "潘金莲"],
        locations=["西门府", "清河县"],
        prev="jpm-fe-012", next=None,
        tags=["情节", "结局"],
        summary="蔡京倒台牵连、家仆离散、妻妾各奔，西门庆一世荣华终归于尽。",
        body="## 出处\n\n第一百回，陈经济落魄、春梅改嫁、吴月娘持家守节，西门府叙事收束。\n\n## 图谱\n\n时间轴末节点 · 对照开篇 [[jpm-fe-001]] 药铺发家。\n",
    ),
]


def write_financial(e: dict) -> None:
    amt = e.get("amount_liang")
    amt_line = f"amount_liang: {amt}\n" if amt is not None else ""
    refs = e.get("transaction_refs", [])
    locs = e.get("locations", [])
    loc_line = f"locations: [{', '.join(locs)}]" if locs else "locations: []"
    prev = e.get("prev")
    next_ = e.get("next")
    prev_line = f"prev: {prev}\n" if prev else ""
    next_line = f"next: {next_}\n" if next_ else ""
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
{prev_line}{next_line}tags: [{', '.join(e.get('tags', []))}]
summary: {e['summary']}
source: chapters/金瓶梅/
---

{e.get('body', '')}
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{e['id']}.md").write_text(text.strip() + "\n", encoding="utf-8")


def write_plot(e: dict) -> None:
    locs = e.get("locations", [])
    loc_line = f"locations: [{', '.join(locs)}]" if locs else "locations: []"
    prev = e.get("prev")
    next_ = e.get("next")
    prev_line = f"prev: {prev}\n" if prev else ""
    next_line = f"next: {next_}\n" if next_ else ""
    text = f"""---
id: {e['id']}
type: event
book: 金瓶梅
subtype: plot
title: {e['title']}
chapters: [{', '.join(str(c) for c in e['chapters'])}]
characters: [{', '.join(e.get('characters', []))}]
{loc_line}
{prev_line}{next_line}tags: [{', '.join(e.get('tags', []))}]
summary: {e['summary']}
source: chapters/金瓶梅/词话本/{e['chapters'][0]:03d}.md
---

{e.get('body', '')}
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{e['id']}.md").write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    for e in EVENTS:
        write_financial(e)
    for e in PLOT_EVENTS:
        write_plot(e)
    print(f"[金瓶梅] {len(EVENTS)} 经济 + {len(PLOT_EVENTS)} 情节事件 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
