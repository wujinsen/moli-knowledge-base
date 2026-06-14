#!/usr/bin/env python3
"""生成《金瓶梅》深度图谱首批数据：西门府社会网人物 + 物质百科名物。

重生成：python scripts/seed_jinpingmei.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAR_OUT = ROOT / "src" / "content" / "characters" / "金瓶梅"
DISH_OUT = ROOT / "src" / "content" / "dishes" / "金瓶梅"
COSTUME_OUT = ROOT / "src" / "content" / "costumes" / "金瓶梅"
MED_OUT = ROOT / "src" / "content" / "medicines" / "金瓶梅"

# id, name, status, faction, ximen_proximity, tags, summary, relations[{target,type,role?}]
CHARACTERS: list[dict] = [
    dict(
        id="西门庆", name="西门庆", status="主角", faction="西门府", ximen_proximity="亲缘",
        tags=["官员", "商贾"], first_appear="第1回",
        summary="清河县提刑千户，西门府当家人；政商勾结、放贷经营、妻妾成群。",
        relations=[
            {"target": "吴月娘", "type": "夫妻"},
            {"target": "潘金莲", "type": "情人", "role": "五房"},
            {"target": "李瓶儿", "type": "情人", "role": "六房"},
            {"target": "孟玉楼", "type": "情人", "role": "三房"},
            {"target": "孙雪娥", "type": "情人", "role": "二房"},
            {"target": "庞春梅", "type": "主仆", "role": "房主"},
            {"target": "应伯爵", "type": "帮闲"},
            {"target": "谢希大", "type": "帮闲"},
            {"target": "韩道国", "type": "朋友", "role": "绒线铺伙计"},
            {"target": "蔡京", "type": "贿赂", "role": "行贿方"},
            {"target": "玳安", "type": "主仆", "role": "心腹小厮"},
            {"target": "来旺", "type": "主仆", "role": "酒店管事"},
            {"target": "陈经济", "type": "主仆", "role": "继子"},
            {"target": "花子虚", "type": "朋友", "role": "结拜兄弟"},
            {"target": "翟管家", "type": "朋友", "role": "蔡府中介"},
        ],
        body="## 身份\n\n清河县提刑千户，生药铺、绒线铺、酒店等多处产业当家人。\n\n## 经济枢纽\n\n- [[犀角带]]、[[蔡太师寿礼银人]] 等高价流转\n- 白银经 [[应伯爵]] 帮闲圈、[[蔡京]] 官场链外溢\n",
    ),
    dict(
        id="吴月娘", name="吴月娘", status="重要", faction="西门府", ximen_proximity="亲缘",
        tags=["妻妾", "正室"], first_appear="第1回",
        summary="西门庆正室，吴千户之女；持家宽厚，府内名分枢纽。",
        relations=[
            {"target": "西门庆", "type": "夫妻"},
            {"target": "庞春梅", "type": "主仆", "role": "房婢"},
            {"target": "潘金莲", "type": "妯娌"},
            {"target": "李瓶儿", "type": "妯娌"},
            {"target": "陈经济", "type": "母子", "role": "继母"},
        ],
    ),
    dict(
        id="潘金莲", name="潘金莲", status="重要", faction="西门府", ximen_proximity="亲缘",
        tags=["妻妾"], first_appear="第1回",
        summary="西门庆五房；与李瓶儿争宠，后害死李瓶儿，晚明妻妾斗争典型。",
        relations=[
            {"target": "西门庆", "type": "情人"},
            {"target": "李瓶儿", "type": "嫉妒"},
            {"target": "庞春梅", "type": "主仆", "role": "房主"},
            {"target": "陈经济", "type": "情人"},
        ],
    ),
    dict(
        id="李瓶儿", name="李瓶儿", status="重要", faction="西门府", ximen_proximity="亲缘",
        tags=["妻妾"], first_appear="第10回",
        summary="花子虚遗孀，携巨资入西门府为六房；被潘金莲嫉妒陷害，早亡。",
        relations=[
            {"target": "西门庆", "type": "情人"},
            {"target": "花子虚", "type": "夫妻"},
            {"target": "潘金莲", "type": "敌对"},
            {"target": "庞春梅", "type": "主仆", "role": "赠婢"},
        ],
    ),
    dict(
        id="庞春梅", name="庞春梅", status="重要", faction="西门府", ximen_proximity="雇佣",
        tags=["仆佣", "妻妾"], first_appear="第8回",
        summary="李瓶儿所赠丫鬟，后属潘金莲房；聪明能干，后嫁守备为夫人。",
        relations=[
            {"target": "西门庆", "type": "主仆"},
            {"target": "潘金莲", "type": "主仆", "role": "房婢"},
            {"target": "吴月娘", "type": "主仆"},
            {"target": "李瓶儿", "type": "主仆", "role": "旧主"},
        ],
    ),
    dict(
        id="孟玉楼", name="孟玉楼", status="配角", faction="西门府", ximen_proximity="亲缘",
        tags=["妻妾"], first_appear="第7回",
        summary="西门庆三房，朱提刑之女；较持重，少涉府内纷争。",
        relations=[{"target": "西门庆", "type": "情人"}],
    ),
    dict(
        id="孙雪娥", name="孙雪娥", status="配角", faction="西门府", ximen_proximity="亲缘",
        tags=["妻妾"], first_appear="第1回",
        summary="西门庆二房，原在厨房；地位较低，常与潘金莲冲突。",
        relations=[
            {"target": "西门庆", "type": "情人"},
            {"target": "潘金莲", "type": "敌对"},
        ],
    ),
    dict(
        id="应伯爵", name="应伯爵", status="重要", faction="帮闲圈", ximen_proximity="利益交换",
        tags=["帮闲"], first_appear="第1回",
        summary="「十弟兄」之一，西门庆头号帮闲；吃花酒、通消息、牵线借贷。",
        relations=[
            {"target": "西门庆", "type": "帮闲"},
            {"target": "谢希大", "type": "朋友"},
            {"target": "李智", "type": "朋友"},
            {"target": "韩道国", "type": "朋友"},
        ],
        body="## SNA 枢纽\n\n帮闲圈中**度中心性最高**的节点之一：连接西门庆、李智、黄四借贷链与韩道国等外围人物。\n",
    ),
    dict(
        id="谢希大", name="谢希大", status="配角", faction="帮闲圈", ximen_proximity="利益交换",
        tags=["帮闲"], first_appear="第1回",
        summary="应伯爵同党帮闲，常伴西门庆花天酒地。",
        relations=[
            {"target": "西门庆", "type": "帮闲"},
            {"target": "应伯爵", "type": "朋友"},
        ],
    ),
    dict(
        id="翟管家", name="翟管家", status="配角", faction="帮闲圈", ximen_proximity="利益交换",
        tags=["帮闲", "中介"], first_appear="第23回",
        summary="蔡京府上管家，西门庆认干爹、行贿的关键掮客。",
        relations=[
            {"target": "西门庆", "type": "朋友", "role": "政商中介"},
            {"target": "蔡京", "type": "主仆", "role": "管家"},
        ],
        body="## 介数中心性\n\n政商链路的**隐形枢纽**：西门庆—翟管家—蔡京，白银与庇护双向流动。\n",
    ),
    dict(
        id="蔡京", name="蔡京", status="配角", faction="朝廷", ximen_proximity="外人",
        tags=["官员"], first_appear="第27回",
        summary="当朝太师，西门庆认干爹、寿礼行贿对象；庇护西门庆官场。",
        relations=[
            {"target": "西门庆", "type": "庇护"},
            {"target": "翟管家", "type": "主仆", "role": "太师"},
        ],
    ),
    dict(
        id="花子虚", name="花子虚", status="配角", faction="清河县", ximen_proximity="利益交换",
        tags=["商贾"], first_appear="第1回",
        summary="西门庆结拜兄弟，李瓶儿前夫；家财被西门庆等算计。",
        relations=[
            {"target": "李瓶儿", "type": "夫妻"},
            {"target": "西门庆", "type": "朋友", "role": "结拜"},
        ],
    ),
    dict(
        id="陈经济", name="陈经济", status="配角", faction="西门府", ximen_proximity="亲缘",
        tags=["商贾"], first_appear="第1回",
        summary="吴月娘继子，后与潘金莲私通，败家流荡。",
        relations=[
            {"target": "西门庆", "type": "主仆", "role": "继子"},
            {"target": "吴月娘", "type": "母子", "role": "继子"},
            {"target": "潘金莲", "type": "情人"},
        ],
    ),
    dict(
        id="玳安", name="玳安", status="配角", faction="西门府", ximen_proximity="雇佣",
        tags=["仆佣"], first_appear="第1回",
        summary="西门庆贴身小厮，通外差、送银、跑腿。",
        relations=[{"target": "西门庆", "type": "主仆", "role": "小厮"}],
    ),
    dict(
        id="来旺", name="来旺", status="配角", faction="西门府", ximen_proximity="雇佣",
        tags=["仆佣"], first_appear="第14回",
        summary="西门庆心腹，酒店管事；后因与潘金莲私通被逐。",
        relations=[{"target": "西门庆", "type": "主仆", "role": "酒店管事"}],
    ),
    dict(
        id="韩道国", name="韩道国", status="配角", faction="帮闲圈", ximen_proximity="利益交换",
        tags=["帮闲", "商贾"], first_appear="第14回",
        summary="绒线铺伙计，应伯爵一党；后随蔡京家奴逃亡。",
        relations=[
            {"target": "西门庆", "type": "朋友", "role": "伙计"},
            {"target": "应伯爵", "type": "朋友"},
        ],
    ),
    dict(
        id="李智", name="李智", status="配角", faction="帮闲圈", ximen_proximity="利益交换",
        tags=["帮闲"], first_appear="第14回",
        summary="帮闲弟兄，向西门庆借银经营。",
        relations=[
            {"target": "西门庆", "type": "借贷", "role": "借方"},
            {"target": "应伯爵", "type": "朋友"},
        ],
    ),
    dict(
        id="武松", name="武松", status="重要", faction="清河县", ximen_proximity="外人",
        tags=["官员"], first_appear="第1回",
        summary="打虎都头，武大嫡亲兄弟；后杀西门庆为兄报仇。",
        relations=[
            {"target": "武大郎", "type": "兄弟"},
            {"target": "潘金莲", "type": "敌对"},
            {"target": "西门庆", "type": "仇敌"},
        ],
    ),
    dict(
        id="武大郎", name="武大郎", status="配角", faction="清河县", ximen_proximity="外人",
        tags=["商贾"], first_appear="第1回",
        summary="武松之兄，卖炊饼为生；潘金莲之夫，被西门庆害死。",
        relations=[
            {"target": "武松", "type": "兄弟"},
            {"target": "潘金莲", "type": "夫妻"},
            {"target": "西门庆", "type": "敌对"},
        ],
    ),
    dict(
        id="李娇儿", name="李娇儿", status="配角", faction="清河县", ximen_proximity="利益交换",
        tags=["妻妾"], first_appear="第1回",
        summary="勾栏妓女，后入西门府；与吴月娘争房。",
        relations=[
            {"target": "西门庆", "type": "情人"},
            {"target": "吴月娘", "type": "妯娌"},
        ],
    ),
]

DISHES = [
    dict(id="酥酥", name="酥酥", category="点心", first_appear="第1回", appear_in=["第1回"],
         ingredients=["面", "油"], eaters=["西门庆", "应伯爵"], tags=["饮食", "帮闲"],
         summary="应伯爵等帮闲陪西门庆所吃小点，见帮闲圈日常消费。"),
    dict(id="烧羊", name="烧羊", category="主菜", first_appear="第1回", appear_in=["第1回"],
         ingredients=["羊肉"], eaters=["西门庆", "应伯爵", "谢希大"], location="西门府",
         tags=["饮食", "宴席"], summary="西门庆宴帮闲弟兄，烧羊为常见硬菜。"),
    dict(id="金华酒", name="金华酒", category="wine", type="wine", first_appear="第1回",
         appear_in=["第1回"], eaters=["西门庆"], tags=["饮食", "酒类"],
         summary="浙江名酒，西门庆府宴饮常备，体现晚明商品流通。"),
    dict(id="面汤", name="面汤", category="主食", first_appear="第8回", appear_in=["第8回"],
         ingredients=["面", "汤"], eaters=["庞春梅"], tags=["饮食"],
         summary="庞春梅等婢仆日常饮食，与主子宴席形成阶层对照。"),
]

COSTUMES = [
    dict(id="犀角带", name="犀角带", type="accessory", wearer="西门庆", first_appear="第27回",
         appear_in=["第27回"], material="犀角", rank_signal="官员身份",
         tags=["服饰", "高价"], summary="王昭宣所售犀角带，西门庆购以装点官仪。"),
    dict(id="销金裙带", name="销金裙带", type="accessory", wearer="潘金莲", first_appear="第12回",
         appear_in=["第12回"], material="销金", color="大红",
         tags=["服饰"], summary="潘金莲所着，晚明销金工艺与妾室装扮。"),
    dict(id="大红段子袄", name="大红段子袄", type="costume", wearer="潘金莲", first_appear="第12回",
         appear_in=["第12回"], material="刻丝段子", color="大红",
         tags=["服饰", "奢侈"], summary="刻丝段子对衿圆领，名物描写极细。"),
    dict(id="貂鼠里皮袄", name="貂鼠里皮袄", type="costume", wearer="西门庆", first_appear="第15回",
         appear_in=["第15回"], material="貂鼠", tags=["服饰", "冬装"],
         summary="西门庆冬日外出所穿，体现商贾显贵。"),
]

MEDICINES = [
    dict(id="胡僧药", name="胡僧春药", type="medicine", category="春药", first_appear="第49回",
         appear_in=["第49回"], patient="西门庆", prescriber="胡僧",
         tags=["药材", "纵欲"], summary="胡僧所赠，西门庆纵欲之由，晚明纵欲心理切片。"),
    dict(id="五灵脂", name="五灵脂", type="prescription", category="方剂", first_appear="第52回",
         appear_in=["第52回"], ingredients=["五灵脂"], patient="李瓶儿",
         tags=["药材"], summary="李瓶儿病中所用，与府内医药描写相关。"),
]


def yaml_list(items: list) -> str:
    if not items:
        return "[]"
    lines = []
    for it in items:
        if isinstance(it, dict):
            inner = ", ".join(f'{k}: {v}' if not isinstance(v, str) or " " in v else f"{k}: {v}" for k, v in it.items())
            lines.append(f"  - {{ {inner} }}")
        else:
            lines.append(f"  - {it}")
    return "\n".join(lines)


def write_char(c: dict) -> None:
    rel_yaml = "\n".join(
        f"  - {{ target: {r['target']}, type: {r['type']}" + (f", role: {r['role']}" if r.get('role') else "") + " }"
        for r in c.get("relations", [])
    )
    text = f"""---
id: {c['id']}
type: character
name: {c['name']}
book: 金瓶梅
faction: {c['faction']}
ximen_proximity: {c['ximen_proximity']}
first_appear: {c.get('first_appear', '')}
status: {c['status']}
tags: [{', '.join(c.get('tags', []))}]
relations:
{rel_yaml}
summary: {c['summary']}
---

{c.get('body', '')}
"""
    (CHAR_OUT / f"{c['id']}.md").write_text(text.strip() + "\n", encoding="utf-8")


def write_item(kind: str, d: dict) -> None:
    if kind == "dish":
        out = DISH_OUT / f"{d['id']}.md"
        typ = d.get("type", "dish")
        text = f"""---
id: {d['id']}
type: {typ}
name: {d['name']}
book: 金瓶梅
category: {d.get('category', '')}
ingredients: [{', '.join(d.get('ingredients', []))}]
eaters: [{', '.join(d.get('eaters', []))}]
{('location: ' + d['location'] + chr(10)) if d.get('location') else ''}first_appear: {d.get('first_appear', '')}
appear_in: [{', '.join(d.get('appear_in', []))}]
tags: [{', '.join(d.get('tags', []))}]
summary: {d['summary']}
---
"""
    elif kind == "costume":
        out = COSTUME_OUT / f"{d['id']}.md"
        opt = []
        for key in ("wearer", "material", "color", "rank_signal"):
            if d.get(key):
                opt.append(f"{key}: {d[key]}")
        opt_block = ("\n".join(opt) + "\n") if opt else ""
        text = f"""---
id: {d['id']}
type: {d.get('type', 'costume')}
name: {d['name']}
book: 金瓶梅
{opt_block}first_appear: {d.get('first_appear', '')}
appear_in: [{', '.join(d.get('appear_in', []))}]
tags: [{', '.join(d.get('tags', []))}]
summary: {d['summary']}
---
"""
    else:
        out = MED_OUT / f"{d['id']}.md"
        optional = []
        if d.get("patient"):
            optional.append(f"patient: {d['patient']}")
        if d.get("prescriber"):
            optional.append(f"prescriber: {d['prescriber']}")
        opt_block = ("\n".join(optional) + "\n") if optional else ""
        text = f"""---
id: {d['id']}
type: {d.get('type', 'medicine')}
name: {d['name']}
book: 金瓶梅
category: {d.get('category', '')}
{opt_block}ingredients: [{', '.join(d.get('ingredients', []))}]
first_appear: {d.get('first_appear', '')}
appear_in: [{', '.join(d.get('appear_in', []))}]
tags: [{', '.join(d.get('tags', []))}]
summary: {d['summary']}
---
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    CHAR_OUT.mkdir(parents=True, exist_ok=True)
    for c in CHARACTERS:
        write_char(c)
    for d in DISHES:
        write_item("dish", d)
    for c in COSTUMES:
        write_item("costume", c)
    for m in MEDICINES:
        write_item("medicine", m)
    print(f"[金瓶梅] {len(CHARACTERS)} 人物 → {CHAR_OUT.relative_to(ROOT)}")
    print(f"[金瓶梅] {len(DISHES)} 饮食 + {len(COSTUMES)} 服饰 + {len(MEDICINES)} 药材")


if __name__ == "__main__":
    main()
