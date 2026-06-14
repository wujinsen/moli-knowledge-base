#!/usr/bin/env python3
"""生成《金瓶梅》西门府 / 清河县 location 实体（含市井地图坐标）。

重生成：python scripts/seed_jpm_locations.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "content" / "locations" / "金瓶梅"

# id, name, type, category, parent, aliases, occupants, nearby, chapters, tags, summary, map_zone, coord
NODES: list[dict] = [
    dict(
        id="西门府", name="西门府", type="building", category="府邸",
        parent=None, aliases=["西门大官人家", "五间门面七进房"],
        occupants=["西门庆", "吴月娘", "潘金莲", "李瓶儿", "孟玉楼", "孙雪娥"],
        nearby=["清河县", "狮子街"],
        chapters=[1, 2, 3, 6, 14, 20, 27, 62, 79],
        tags=["主场景", "七进深宅"],
        map_zone="府内", coord=(520, 300),
        summary="西门庆在清河县的七进深宅，门面五间到底七进；妻妾分院、帮闲出入、白银流转的核心场域。",
        body="## 格局\n\n词话本第1回：「门面五间到底七进」；正室吴月娘、二房孙雪娥、三房孟玉楼、五房潘金莲、六房李瓶儿各据院落。\n\n## 经济枢纽\n\n府内银钱、礼物、借贷与 [[应伯爵]] 帮闲圈、[[蔡京]] 官场链在此交汇。\n",
    ),
    dict(
        id="清河县", name="清河县", type="location", category="市街",
        parent=None, aliases=["东平府清河县", "山东清河县"],
        occupants=[], nearby=["狮子街", "西门府", "永福寺", "玉皇庙"],
        chapters=[1, 5, 12, 23, 48],
        tags=["县城", "政商"],
        map_zone="市井", coord=(240, 300),
        summary="故事主要发生的县级空间；西门庆任提刑千户，生药铺、勾栏、寺观皆在此。",
    ),
    dict(
        id="狮子街", name="狮子街", type="location", category="市街",
        parent="清河县", aliases=[],
        occupants=["花子虚"], nearby=["西门府", "李娇儿院"],
        chapters=[1, 10, 14, 19],
        tags=["商业街", "帮闲"],
        map_zone="市井", coord=(300, 300),
        summary="清河县繁华市街；花子虚宅与西门府仅隔一壁，李娇儿勾栏亦在此。",
    ),
    dict(
        id="吴月娘房", name="吴月娘房", type="building", category="院落",
        parent="西门府", aliases=["大房", "月娘房"],
        occupants=["吴月娘", "庞春梅"], nearby=["潘金莲房", "李瓶儿房"],
        chapters=[1, 6, 14, 27],
        tags=["正室"],
        map_zone="府内", coord=(460, 240),
        summary="西门庆正室吴月娘所居；持家宽厚，府内名分与银钱出入多经此房。",
    ),
    dict(
        id="潘金莲房", name="潘金莲房", type="building", category="院落",
        parent="西门府", aliases=["五娘房"],
        occupants=["潘金莲", "庞春梅"], nearby=["吴月娘房", "李瓶儿房"],
        chapters=[8, 12, 27, 44, 62],
        tags=["争宠", "五房"],
        map_zone="府内", coord=(460, 360),
        summary="潘金莲所居；与李瓶儿争宠，后害死李瓶儿，晚明妻妾斗争典型空间。",
    ),
    dict(
        id="李瓶儿房", name="李瓶儿房", type="building", category="院落",
        parent="西门府", aliases=["六娘房", "瓶儿房"],
        occupants=["李瓶儿", "庞春梅"], nearby=["潘金莲房"],
        chapters=[19, 27, 39, 62],
        tags=["六房", "巨资入府"],
        map_zone="府内", coord=(580, 360),
        summary="花子虚遗孀李瓶儿携巨资入府后所居；被潘金莲嫉妒陷害，早亡于此。",
    ),
    dict(
        id="孟玉楼房", name="孟玉楼房", type="building", category="院落",
        parent="西门府", aliases=["三房", "三娘房"],
        occupants=["孟玉楼"], nearby=["吴月娘房"],
        chapters=[7, 14, 62],
        tags=["三房"],
        map_zone="府内", coord=(580, 240),
        summary="朱提刑之女孟玉楼所居；较持重，少涉府内纷争。",
    ),
    dict(
        id="孙雪娥房", name="孙雪娥房", type="building", category="院落",
        parent="西门府", aliases=["二房", "厨房"],
        occupants=["孙雪娥"], nearby=[],
        chapters=[1, 25, 62],
        tags=["二房", "厨房"],
        map_zone="府内", coord=(520, 420),
        summary="西门庆二房孙雪娥所居，原在厨房；地位较低，常与潘金莲冲突。",
    ),
    dict(
        id="西门庆生药铺", name="西门庆生药铺", type="building", category="市街",
        parent="清河县", aliases=["生药铺", "药铺"],
        occupants=["西门庆"], nearby=["西门府", "绒线铺"],
        chapters=[1, 5, 48],
        tags=["产业", "药材"],
        map_zone="市井", coord=(160, 220),
        summary="西门庆祖业；门面五间，清河县城前大街，与府宅相连，是府内经济起点。",
    ),
    dict(
        id="绒线铺", name="韩道国绒线铺", type="building", category="市街",
        parent="清河县", aliases=["绒线铺"],
        occupants=["韩道国"], nearby=["西门庆生药铺"],
        chapters=[23, 48, 74],
        tags=["产业", "伙计"],
        map_zone="市井", coord=(160, 340),
        summary="西门庆出资、韩道国经营的绒线铺；后卷入拐逃、销赃等风波。",
    ),
    dict(
        id="玉皇庙", name="玉皇庙", type="temple", category="寺观",
        parent="清河县", aliases=[],
        occupants=[], nearby=["永福寺"],
        chapters=[1, 3],
        tags=["结拜", "吴道官"],
        map_zone="寺观", coord=(320, 100),
        summary="西门庆与「十弟兄」结拜处；吴道官主持，初五上庙散福。",
    ),
    dict(
        id="永福寺", name="永福寺", type="temple", category="寺观",
        parent="清河县", aliases=[],
        occupants=[], nearby=["玉皇庙"],
        chapters=[1, 39, 48],
        tags=["僧家"],
        map_zone="寺观", coord=(440, 100),
        summary="清河县僧家；李瓶儿荐官、西门庆做佛事等多与此寺相关。",
    ),
    dict(
        id="李娇儿院", name="李娇儿院", type="building", category="馆",
        parent="狮子街", aliases=["勾栏", "院中"],
        occupants=["李娇儿"], nearby=["狮子街", "西门府"],
        chapters=[1, 12, 19],
        tags=["勾栏", "帮闲"],
        map_zone="市井", coord=(320, 420),
        summary="清河县勾栏；李娇儿所居，西门庆、应伯爵等常在此吃花酒。",
    ),
    dict(
        id="花家", name="花子虚宅", type="building", category="府邸",
        parent="狮子街", aliases=["花二哥家"],
        occupants=["花子虚", "李瓶儿"], nearby=["西门府"],
        chapters=[1, 10, 14],
        tags=["结拜兄弟", "隔壁"],
        map_zone="市井", coord=(360, 260),
        summary="花子虚宅，与西门府仅隔一壁；李瓶儿携财入西门府前，巨产多出于此。",
    ),
    dict(
        id="潘家", name="潘金莲旧居", type="building", category="府邸",
        parent="清河县", aliases=["武大郎家", "紫石街"],
        occupants=["潘金莲", "武大郎"], nearby=[],
        chapters=[1, 5],
        tags=["紫石街"],
        map_zone="市井", coord=(120, 460),
        summary="清河县紫石街武大郎家；潘金莲嫁西门庆前的居所，武松打虎后故事起点之一。",
    ),
    dict(
        id="东京", name="东京", type="location", category="城关",
        parent=None, aliases=["东京汴梁", "汴京"],
        occupants=["蔡京"], nearby=[],
        chapters=[18, 23, 27, 48],
        tags=["政商", "蔡京"],
        map_zone="城外", coord=(720, 260),
        summary="西门庆行贿蔡京、认干爹、得官的政商链远端；与清河本地网络以白银与书信相连。",
    ),
]


def yaml_list(key: str, vals: list) -> str:
    if not vals:
        return f"{key}: []"
    return "\n".join([f"{key}:"] + [f"  - {v}" for v in vals])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for n in NODES:
        appear_in = [f"第{c}回" for c in n["chapters"]]
        first = appear_in[0] if appear_in else None
        cx, cy = n["coord"]
        lines = [
            "---",
            f"id: {n['id']}",
            f"type: {n['type']}",
            f"name: {n['name']}",
            yaml_list("aliases", n["aliases"]),
            "book: 金瓶梅",
            f"category: {n['category']}",
        ]
        if n.get("parent"):
            lines.append(f"parent: {n['parent']}")
        lines.extend([
            yaml_list("occupants", n["occupants"]),
            yaml_list("nearby", n["nearby"]),
        ])
        if first:
            lines.append(f"first_appear: {first}")
        lines.append(yaml_list("appear_in", appear_in))
        lines.append(yaml_list("tags", n["tags"]))
        lines.append(f"map_zone: {n['map_zone']}")
        lines.append("coord:")
        lines.append(f"  x: {cx}")
        lines.append(f"  y: {cy}")
        lines.append(f"summary: {n['summary']}")
        lines.append("---")
        lines.append("")
        if n.get("body"):
            lines.append(n["body"].strip())
            lines.append("")
        path = OUT / f"{n['id']}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"done: {len(NODES)} locations")


if __name__ == "__main__":
    main()
