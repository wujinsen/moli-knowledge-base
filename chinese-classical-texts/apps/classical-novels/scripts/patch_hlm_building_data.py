#!/usr/bin/env python3
"""补全红楼梦 location：第17回间数、两府间数、features/plaque 缺口。

用法: python scripts/patch_hlm_building_data.py [--write]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CONTENT, parse_frontmatter

BOOK = "红楼梦"
LOC_DIR = CONTENT / "locations" / BOOK

# fact：第17回正文间数/格局（不换算现代尺寸）
CH17_SCALE: dict[str, list[str]] = {
    "大观园": ["第17回：园正门五间，桶瓦泥鳅脊，水磨群墙"],
    "曲径通幽": ["第17回：非主山障景，山口镜面白石留题"],
    "沁芳亭": ["第17回：石桥三港，桥上有亭；再进数步渐向北，飞楼插空"],
    "潇湘馆": [
        "第17回：小小两三间、一明两暗",
        "第17回：后院两间小小退步；引泉开沟仅尺许",
    ],
    "稻香村": ["第17回：数楹茅屋，黄泥矮墙"],
    "蓼溆": ["第17回：采莲船四只、座船一只尚未造成"],
    "蘅芜苑": ["第17回：五间清厦连着卷棚，四面出廊"],
    "省亲别墅": ["第17回：崇阁巍峨，层楼高起；玉石牌坊"],
    "沁芳闸": ["第17回：大桥引外河，水如晶帘"],
    "怡红院": [
        "第17回：几间房内，四面雕空玲珑隔扇",
        "第17回：未进两层便都迷了旧路",
    ],
}

# fact：两府及园外重要节点（非第17回）
FU_SCALE: dict[str, list[str]] = {
    "荣国府": ["第3回：荣禧堂五间大书，屏开鸾凤；角门、穿堂、上房规制"],
    "荣禧堂": ["第3回：五间大书，屏开鸾凤"],
    "贾母上房": ["第3回：正院五间上房"],
    "议事厅": ["第55回：园门南三间小花厅，匾辅仁谕德"],
    "梨香院": ["第4回：荣府角院，薛家寄居；第23回墙外听曲"],
    "宁国府": ["第11回：会芳园、天香楼在宁府内"],
    "天香楼": ["第13回：宁府内楼，可卿大丧设宴"],
    "贾氏宗祠": ["第53回：开宗祠，悬供遗像，祭祀大典"],
    "会芳园": ["第5回：宁府花园，贾母赏花"],
    "王夫人上房": ["第7回：荣府内院，王夫人理事"],
    "贾政上房": ["荣府正院，贾政日常起居"],
    "凤姐院": ["第3回：琏二奶奶院，理家枢纽"],
    "赵姨娘房": ["贾政妾室院落"],
    "周姨娘房": ["第35回：与赵姨娘并提"],
    "薛家": ["梨香院一带，薛姨妈宝钗初居"],
}

# 第18回及他回可考匾额（仅补缺；节点须已有 location 页）
PLAQUE_ADD: dict[str, str] = {}

# 无 features 页的最低 fact 补一句（仅当 features 为空时）
FEATURE_FALLBACK: dict[str, list[str]] = {
    "云步石梯": ["第6批：园中石阶景观节点"],
    "夹道": ["连接两府与园门的通道空间"],
    "后廊": ["荣府后部游廊，下人通行"],
    "腰门": ["内宅边门，礼仪层级低于仪门"],
    "下房": ["仆役下人起居处"],
    "厢房": ["第69回：尤二姐入府暂居"],
    "后门": ["园中后门，贾芸送花、宝玉窃听"],
    "外书房": ["第16回：宝玉约秦钟夜读处"],
    "孝幕": ["丧仪搭棚空间"],
    "抱厦": ["正厅两侧抱厦，待客起坐"],
    "孝慈县": ["都外县治，清虚观、铁槛寺所在"],
    "十里屯": ["京外屯庄"],
    "郝家庄": ["第93回：京外庄，租银被抢"],
    "孙家": ["第79回：孙绍祖府"],
    "甄家": ["第1回：甄士隐家；后甄家抄没"],
    "破寺": ["第98回：知庵，宝玉访散"],
    "姑子庙": ["都中尼庵"],
    "地藏庵": ["尼庵，与铁槛寺相近"],
    "清虚观": ["第29回：打醮、张道士说亲"],
    "铁槛寺": ["第15回：可卿停灵"],
    "水月庵": ["馒头庵，第71回后事"],
    "葫芦庙": ["第1回：甄士隐隔壁"],
    "急流津": ["第120回：觉迷渡口"],
    "小花枝巷": ["第63回：尤氏继母与二姐、三姐居此"],
    "赖大家": ["管家赖大宅"],
    "宁荣街": ["两府分列之街衢"],
    "金陵城": ["都中，贾府所在"],
    "离恨天": ["太虚幻境所在天界"],
    "贾母套间": ["第111回：贾母上房内室"],
    "家塾": ["贾府子弟读书处"],
    "穿堂": ["内外宅过渡空间"],
    "二门": ["内外院分界"],
    "仪门": ["第53回：主仆分界；国丧时关锁"],
    "角门": ["第59回：园中角门"],
    "回廊": ["游廊连接各院"],
    "翠烟桥": ["第25回：小红贾芸传帕"],
    "蜂腰桥": ["园中桥梁节点"],
    "柳叶渚": ["第59回：莺儿编篮、春燕冲突"],
    "船坞": ["第40回：存舟，刘姥姥游湖"],
    "大观园厨房": ["园中厨房后勤"],
    "洒泪亭": ["与黛玉葬花意象相关之亭"],
    "凸碧山庄": ["第76回：中秋，凸碧堂所在区"],
    "凹晶溪馆": ["第76回：中秋，凹晶馆所在区"],
    "东角门": ["第7回：周瑞家的往梨香院经东角门至东院"],
    "门上": ["府第大门门房，家人守门处"],
    "茶房": ["府内备茶之处"],
    "内茶房": ["内宅茶房"],
    "贡院": ["都中科举考场"],
    "登仙阁": ["宁府内楼阁节点"],
    "玉皇庙": ["第6批：都中道观"],
    "达摩庵": ["第6批：都中庵堂"],
    "临敬殿": ["第16回：皇宫陛见，元春封妃"],
    "北静王府": ["第14回：北静王水溶府；可卿路祭、贾母寿宴"],
    "南安王府": ["第71回：贾母八旬寿宴与北静王府并提"],
    "忠顺王府": ["第33回：索琪官，与北静府对照"],
    "乐善郡王府": ["第71回：寿宴世交王府"],
    "锦乡侯府": ["第71回：诰命陪席"],
    "临昌伯府": ["第71回：诰命陪席"],
    "临安伯府": ["第71回：与临昌伯诰命同席"],
    "永昌驸马府": ["都中驸马府第，与诸王府并列"],
}


def parse_features_block(fm_raw: str) -> tuple[list[str], str | None]:
    m = re.search(r"^features:\s*\n((?:  - .+\n)+)", fm_raw, re.M)
    if not m:
        if re.search(r"^features:\s*\[\s*\]", fm_raw, re.M):
            return [], "features: []"
        if re.search(r"^features:\s*$", fm_raw, re.M):
            return [], "features:"
        return [], None
    lines = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("- "):
            lines.append(line[2:].strip())
    return lines, m.group(0)


def merge_features(fm_raw: str, add: list[str]) -> tuple[str, bool]:
    existing, block = parse_features_block(fm_raw)
    if block is None:
        insert = "features:\n" + "".join(f"  - {x}\n" for x in add)
        for anchor in ("first_appear:", "appear_in:", "summary:", "tags:", "nearby:", "plaque:"):
            idx = fm_raw.find(anchor)
            if idx >= 0:
                return fm_raw[:idx] + insert + fm_raw[idx:], True
        return fm_raw.rstrip() + "\n" + insert, True
    merged = list(dict.fromkeys(existing + [x for x in add if x not in existing]))
    if merged == existing:
        return fm_raw, False
    new_block = "features:\n" + "".join(f"  - {x}\n" for x in merged)
    if block == "features: []":
        new_fm = re.sub(r"^features:\s*\[\s*\]", new_block.rstrip(), fm_raw, count=1, flags=re.M)
    else:
        new_fm = fm_raw.replace(block, new_block)
    return new_fm, True


def upsert_plaque(fm_raw: str, plaque: str) -> tuple[str, bool]:
    if re.search(r"^plaque:", fm_raw, re.M):
        return fm_raw, False
    line = f"plaque: {plaque}\n"
    for anchor in ("couplet:", "features:", "occupants:", "nearby:", "first_appear:"):
        idx = fm_raw.find(anchor)
        if idx >= 0:
            return fm_raw[:idx] + line + fm_raw[idx:], True
    return fm_raw.rstrip() + "\n" + line, True


def patch_file(path: Path, *, write: bool) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return []
    lid = path.stem
    fm_raw, body = parts[1], parts[2]
    changed: list[str] = []

    scale_add: list[str] = []
    scale_add.extend(CH17_SCALE.get(lid, []))
    scale_add.extend(FU_SCALE.get(lid, []))
    if not scale_add and lid in FEATURE_FALLBACK:
        _, block = parse_features_block(fm_raw)
        if block is None or block in ("features: []", "features:"):
            scale_add.extend(FEATURE_FALLBACK[lid])

    if scale_add:
        new_fm, ok = merge_features(fm_raw, scale_add)
        if ok:
            fm_raw = new_fm
            changed.append("features")

    if lid in PLAQUE_ADD:
        new_fm, ok = upsert_plaque(fm_raw, PLAQUE_ADD[lid])
        if ok:
            fm_raw = new_fm
            changed.append("plaque")

    if changed and write:
        path.write_text(f"---{fm_raw}---{body}", encoding="utf-8")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    mode = "WRITE" if args.write else "DRY-RUN"
    print(f"patch_hlm_building_data [{mode}]\n")

    stats: dict[str, int] = {}
    for p in sorted(LOC_DIR.glob("*.md")):
        for c in patch_file(p, write=args.write):
            stats[c] = stats.get(c, 0) + 1
            print(f"  {p.stem}: {c}")

    print(f"\n{'Would patch' if not args.write else 'Patched'}: {stats}")
    if not args.write:
        print("（加 --write 写回）")


if __name__ == "__main__":
    main()
