#!/usr/bin/env python3
"""生成《西游记》取经路线 GIS 的 location 实体（凡间路线 + 神话异界双层）。

坐标系：虚拟画布 1000 x 640，x 从左（长安）向右（灵山）递增，y 上小下大。
- layer=real 为凡间取经路线，按 route_order 串成时间轴折线；
- layer=myth 为天界/地府/龙宫等异界节点，俯瞰式叠加。
重生成：python scripts/seed_route.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "content" / "locations" / "西游记"

# id, name, type, category, realm, layer, x, y, route_order, aliases, chapters, tags, summary
NODES: list[dict] = [
    # —— 凡间取经路线（自东土长安向西天灵山）——
    dict(id="长安城", name="长安城", type="location", category="国度", realm="凡间", layer="real",
         x=70, y=360, order=1, aliases=["东土大唐"], chapters=[12, 13], tags=["起点", "大唐"],
         summary="取经起点。唐太宗于此为唐僧设坛拜送，赐紫金钵盂、通关文牒。"),
    dict(id="两界山", name="两界山", type="山岭", category="山岭", realm="凡间", layer="real",
         x=118, y=312, order=2, aliases=["五行山"], chapters=[13, 14], tags=["五行山", "收徒"],
         summary="原压孙悟空之五行山，唐僧揭帖救出悟空，收为大徒弟。"),
    dict(id="鹰愁涧", name="鹰愁涧", type="水域", category="水域", realm="凡间", layer="real",
         x=165, y=402, order=3, aliases=["蛇盘山"], chapters=[15], tags=["白龙马"],
         summary="西海龙王三太子吞马，经观音点化化为白龙马，成取经脚力。"),
    dict(id="高老庄", name="高老庄", type="location", category="国度", realm="凡间", layer="real",
         x=210, y=330, order=4, aliases=["乌斯藏"], chapters=[18, 19], tags=["收徒"],
         summary="悟空降伏入赘的猪刚鬣，收猪八戒为二徒弟。"),
    dict(id="黄风岭", name="黄风岭", type="山岭", category="山岭", realm="凡间", layer="real",
         x=255, y=408, order=5, aliases=[], chapters=[20, 21], tags=["黄风怪"],
         summary="黄风怪摄走唐僧，悟空请灵吉菩萨以飞龙杖收之（黄毛貂鼠）。"),
    dict(id="流沙河", name="流沙河", type="水域", category="水域", realm="凡间", layer="real",
         x=300, y=348, order=6, aliases=[], chapters=[22], tags=["收徒"],
         summary="收卷帘大将沙悟净为三徒弟，师徒四众至此凑齐。"),
    dict(id="五庄观", name="五庄观", type="temple", category="仙山", realm="凡间", layer="real",
         x=345, y=288, order=7, aliases=["万寿山"], chapters=[24, 25, 26], tags=["人参果", "镇元子"],
         summary="镇元大仙道场。八戒偷食人参果、悟空推倒仙树，后求观音净瓶甘露医活。"),
    dict(id="白虎岭", name="白虎岭", type="山岭", category="山岭", realm="凡间", layer="real",
         x=390, y=398, order=8, aliases=[], chapters=[27], tags=["白骨精", "三打"],
         summary="尸魔白骨精三化人形，悟空三打白骨精，唐僧肉眼凡胎怒贬悟空。"),
    dict(id="莲花洞", name="平顶山·莲花洞", type="洞府", category="洞府", realm="凡间", layer="real",
         x=435, y=330, order=9, aliases=["平顶山"], chapters=[32, 33, 34, 35], tags=["金角银角"],
         summary="金角银角大王（老君看炉童子），持紫金红葫芦等五件法宝，被悟空赚宝收服。"),
    dict(id="乌鸡国", name="乌鸡国", type="location", category="国度", realm="凡间", layer="real",
         x=480, y=410, order=10, aliases=[], chapters=[37, 38, 39], tags=["青毛狮子"],
         summary="青毛狮子精害国王、霸王位三年，悟空借太上老君还魂丹救活真王。"),
    dict(id="火云洞", name="号山·火云洞", type="洞府", category="洞府", realm="凡间", layer="real",
         x=525, y=352, order=11, aliases=["枯松涧"], chapters=[40, 41, 42], tags=["红孩儿", "三昧真火"],
         summary="牛魔王子红孩儿，三昧真火险伤悟空，观音以金箍咒收为善财童子。"),
    dict(id="车迟国", name="车迟国", type="location", category="国度", realm="凡间", layer="real",
         x=570, y=290, order=12, aliases=[], chapters=[44, 45, 46], tags=["虎力鹿力羊力"],
         summary="虎力、鹿力、羊力三大仙惑国压僧，斗法求雨、砍头剖腹，皆败露原形。"),
    dict(id="通天河", name="通天河", type="水域", category="水域", realm="凡间", layer="real",
         x=615, y=402, order=13, aliases=[], chapters=[47, 48, 49], tags=["灵感大王", "老鼋"],
         summary="灵感大王（观音莲池金鱼）食童男女，鱼篮观音收之；老鼋驮渡，约问寿数之事。"),
    dict(id="西梁女国", name="西梁女国", type="location", category="国度", realm="凡间", layer="real",
         x=660, y=332, order=14, aliases=["女儿国"], chapters=[53, 54], tags=["女儿国", "子母河"],
         summary="举国无男，女王欲招唐僧为夫；子母河误饮成胎，琵琶洞蝎子精摄僧。"),
    dict(id="火焰山", name="火焰山", type="山岭", category="山岭", realm="凡间", layer="real",
         x=705, y=412, order=15, aliases=[], chapters=[59, 60, 61], tags=["芭蕉扇", "牛魔王"],
         summary="八百里烈焰阻路。三借芭蕉扇，戏铁扇公主、斗牛魔王，终熄火西行。"),
    dict(id="祭赛国", name="祭赛国", type="location", category="国度", realm="凡间", layer="real",
         x=750, y=350, order=16, aliases=[], chapters=[62, 63], tags=["扫塔", "九头虫"],
         summary="金光寺宝塔失舍利，悟空扫塔辨冤；碧波潭九头虫盗宝，与二郎神协擒。"),
    dict(id="朱紫国", name="朱紫国", type="location", category="国度", realm="凡间", layer="real",
         x=795, y=290, order=17, aliases=[], chapters=[68, 69, 70, 71], tags=["行医", "赛太岁"],
         summary="悟空悬丝诊脉为国王治相思之疾，降观音坐骑金毛犼（赛太岁），救回金圣宫娘娘。"),
    dict(id="狮驼岭", name="狮驼岭", type="山岭", category="山岭", realm="凡间", layer="real",
         x=840, y=402, order=18, aliases=["狮驼国"], chapters=[74, 75, 76, 77], tags=["三魔", "最险一难"],
         summary="青狮、白象、大鹏三魔盘踞，吞城屠国。大鹏金翅雕最难制，终请如来现身收伏。"),
    dict(id="比丘国", name="比丘国", type="location", category="国度", realm="凡间", layer="real",
         x=885, y=335, order=19, aliases=["小子城"], chapters=[78, 79], tags=["白鹿精", "救小儿"],
         summary="国丈白鹿精进美后（白面狐狸），欲取小儿心肝作药引；寿星收鹿，救千百小儿。"),
    dict(id="灭法国", name="灭法国", type="location", category="国度", realm="凡间", layer="real",
         x=915, y=405, order=20, aliases=["钦法国"], chapters=[84, 85], tags=["杀僧愿"],
         summary="国王许愿杀一万和尚，仅差几众。悟空夜剃满朝须发，惊王悔过，改国号钦法。"),
    dict(id="天竺国", name="天竺国", type="location", category="国度", realm="凡间", layer="real",
         x=945, y=345, order=21, aliases=[], chapters=[93, 94, 95], tags=["玉兔精", "抛绣球"],
         summary="玉兔精冒充公主抛绣球招亲，欲害唐僧元阳；太阴星君携素娥收兔。"),
    dict(id="灵山", name="灵山·大雷音寺", type="temple", category="仙山", realm="灵山", layer="real",
         x=985, y=300, order=22, aliases=["雷音寺", "西天"], chapters=[98, 99, 100], tags=["终点", "取经成佛"],
         summary="取经终点。凌云渡脱胎，见如来传经，阿傩伽叶索人事；师徒四众与白马同证正果。"),
    # —— 神话异界（俯瞰叠加层）——
    dict(id="灵霄宝殿", name="灵霄宝殿", type="realm", category="天界", realm="天界", layer="myth",
         x=300, y=70, order=None, aliases=["天宫", "凌霄殿"], chapters=[4, 5, 6, 7], tags=["玉帝", "大闹天宫"],
         summary="玉皇大帝所居天庭中枢。悟空封弼马温、自称齐天大圣、大闹蟠桃会，终被压五行山。"),
    dict(id="兜率宫", name="兜率宫", type="realm", category="天界", realm="天界", layer="myth",
         x=470, y=92, order=None, aliases=["离恨天"], chapters=[5, 35, 50], tags=["太上老君", "炼丹"],
         summary="太上老君炼丹之所。悟空偷吃金丹炼成火眼金睛；金角银角、青牛精皆出其门下。"),
    dict(id="普陀山", name="南海·普陀落伽山", type="temple", category="仙山", realm="南海", layer="myth",
         x=700, y=98, order=None, aliases=["潮音洞", "紫竹林"], chapters=[8, 42, 49], tags=["观音", "求援"],
         summary="观世音菩萨道场。取经大业由此发起，多次危难悟空驾云至此求助（红孩儿、金鱼精等）。"),
    dict(id="东海龙宫", name="东海龙宫", type="realm", category="水域", realm="东海", layer="myth",
         x=150, y=560, order=None, aliases=["水晶宫"], chapters=[3], tags=["龙王", "金箍棒"],
         summary="东海龙王敖广居所。悟空索得定海神针如意金箍棒及一身披挂，闹得四海龙王上表。"),
    dict(id="幽冥地府", name="幽冥地府·森罗殿", type="realm", category="地府", realm="地府", layer="myth",
         x=385, y=575, order=None, aliases=["阴司", "森罗殿"], chapters=[3, 10, 11], tags=["十殿阎君", "生死簿"],
         summary="十殿阎君所辖。悟空强销猴属生死簿；唐太宗魂游地府还阳，乃有水陆大会、遣僧取经之缘起。"),
]


# content.config.ts 的 location.type 仅允许这 5 类；category 才承载西游细分
TYPE_BY_CATEGORY = {
    "仙山": "temple",
    "寺观": "temple",
    "洞府": "building",
    "天界": "realm",
    "地府": "realm",
}


def valid_type(n: dict) -> str:
    if n["layer"] == "myth" and n["category"] == "水域":
        return "realm"
    return TYPE_BY_CATEGORY.get(n["category"], "location")


def yaml_list(key: str, vals: list) -> str:
    if not vals:
        return f"{key}: []"
    return "\n".join([f"{key}:"] + [f"  - {v}" for v in vals])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written = 0
    for n in NODES:
        appear_in = [f"第{c}回" for c in n["chapters"]]
        first = appear_in[0] if appear_in else None
        lines = [
            "---",
            f"id: {n['id']}",
            f"type: {valid_type(n)}",
            f"name: {n['name']}",
            yaml_list("aliases", n["aliases"]),
            "book: 西游记",
            f"category: {n['category']}",
            f"realm: {n['realm']}",
            f"layer: {n['layer']}",
            f"coord: {{ x: {n['x']}, y: {n['y']} }}",
        ]
        if n["order"] is not None:
            lines.append(f"route_order: {n['order']}")
        lines.append(yaml_list("appear_in", appear_in))
        if first:
            lines.append(f"first_appear: {first}")
        lines.append(yaml_list("tags", n["tags"]))
        lines.append(f'summary: "{n["summary"]}"')
        lines.append("source: chapters/西游记/")
        lines.append("---")
        lines.append("")
        lines.append(f"## {n['name']}")
        lines.append("")
        lines.append(n["summary"])
        (OUT / f"{n['id']}.md").write_text("\n".join(lines), encoding="utf-8")
        written += 1

    print(f"Wrote {written} route locations to {OUT}")


if __name__ == "__main__":
    main()
