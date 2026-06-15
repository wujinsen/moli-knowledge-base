#!/usr/bin/env python3
"""P4: 正文 [[互链]] 与 frontmatter relations[] 对齐（西游记）。

扫描人物页正文中 wiki 链接，若 target 未在 relations 中则补边。
类型推断：反向边镜像 → 手工表 → 正文语境 → 启发式 → 默认「朋友」。

用法:
  python scripts/sync_xyj_body_relations.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import iter_characters  # noqa: E402

BOOK = "西游记"
VALID_TYPES = frozenset(
    {
        "夫妻",
        "父子",
        "母子",
        "兄弟",
        "姐妹",
        "祖孙",
        "妯娌",
        "主仆",
        "师徒",
        "师兄弟",
        "同僚",
        "朋友",
        "结拜",
        "君臣",
        "情人",
        "恋慕",
        "仇敌",
        "敌对",
    }
)

HEROES = frozenset({"孙悟空", "唐僧", "猪八戒", "沙僧"})
BUDDHA = frozenset(
    {
        "观音菩萨",
        "如来佛祖",
        "文殊菩萨",
        "普贤菩萨",
        "南极寿星",
        "太乙救苦天尊",
        "燃灯古佛",
        "乌巢禅师",
        "国师王菩萨",
        "弥勒佛",
        "灵吉菩萨",
        "毗蓝婆",
        "东华帝君",
    }
)
COURT_OFFICIALS = frozenset(
    {
        "太监",
        "侍官",
        "老军",
        "馆使",
        "宣召官",
        "内宫官",
        "当驾官",
        "黄门官",
        "司礼监",
        "光禄寺",
        "仪制司",
        "太医",
        "太医院正",
        "五城兵马官",
        "羽林军",
        "教坊司",
    }
)
RULER_SUFFIX = ("国王", "郡侯", "刺史", "太子", "娘娘")

# (source, target) -> (type, role?)
MANUAL: dict[tuple[str, str], tuple[str, str | None]] = {
    ("万圣公主", "祭赛国国王"): ("敌对", None),  # 盗舍利对立
    ("精细鬼", "小钻风"): ("朋友", None),  # 同类巡山小妖
    ("伶俐虫", "小钻风"): ("朋友", None),
    ("东华帝君", "白鹿精"): ("朋友", None),  # 寿星坐骑，同列上界
    ("土地", "日值功曹"): ("同僚", None),
    ("增长天王", "哪吒"): ("同僚", None),
    ("巨灵神", "哪吒"): ("同僚", None),
    ("巨灵神", "李靖"): ("同僚", None),
    ("推云童子", "雷公"): ("同僚", None),
    ("风伯", "雷公"): ("同僚", None),
    ("风伯", "电母"): ("同僚", None),
    ("雷公", "电母"): ("同僚", None),
    ("雷公", "虎力大仙"): ("敌对", None),
    ("辟寒", "辟暑"): ("兄弟", None),
    ("辟寒", "辟尘"): ("兄弟", None),
    ("辟暑", "辟尘"): ("兄弟", None),
    ("奔波儿灞", "祭赛国国王"): ("敌对", None),
    ("奔波儿灞", "万圣龙王"): ("主仆", None),
    ("奔波儿灞", "九头虫"): ("主仆", None),
    ("赛太岁先锋", "有来有去"): ("同僚", None),
    ("金平府刺史", "辟寒"): ("君臣", None),
    ("金平府刺史", "辟暑"): ("君臣", None),
    ("金平府刺史", "辟尘"): ("君臣", None),
    ("陈家庄老妪", "观音菩萨"): ("朋友", None),
    ("陈清", "观音菩萨"): ("朋友", None),
    ("高士廉", "魏征"): ("同僚", None),
    ("魏征", "唐太宗"): ("君臣", None),
    ("魏征", "秦琼"): ("同僚", None),
    ("魏征", "敬德"): ("同僚", None),
    ("魏征", "房玄龄"): ("同僚", None),
    ("薛仁贵", "程咬金"): ("同僚", None),
    ("殷温娇", "程咬金"): ("朋友", None),
    ("张稍", "泾河龙王"): ("朋友", None),
    ("徐兴", "泾河龙王"): ("朋友", None),
    ("张道士", "张士诚"): ("朋友", None),
    ("马元帅", "张道陵"): ("主仆", None),
    ("流元帅", "马元帅"): ("同僚", None),
    ("温元帅", "马元帅"): ("同僚", None),
    ("熊山君", "刘伯钦"): ("敌对", None),
    ("熊山君", "黑熊精"): ("敌对", None),
    ("广智", "黑熊精"): ("主仆", None),
    ("白衣秀士", "黑熊精"): ("朋友", None),
    ("白衣秀士", "凌虚子"): ("朋友", None),
    ("昴日星官", "增长天王"): ("同僚", None),
    ("昴日星官", "奎木狼"): ("同僚", None),
}


def link_context(body: str, target: str) -> str:
    needle = f"[[{target}]]"
    for line in body.splitlines():
        if needle in line:
            return line
    idx = body.find(needle)
    if idx < 0:
        return ""
    return body[max(0, idx - 30) : idx + len(needle) + 30]


def mirror_reverse(
    src: str, tgt: str, pages: dict[str, tuple]
) -> tuple[str, str | None] | None:
    t_fm = pages[tgt][0]
    for r in t_fm.get("relations") or []:
        if r.get("target") != src:
            continue
        rtype = r["type"]
        role = r.get("role")
        if rtype == "师徒":
            if role == "徒弟":
                return "师徒", "师父"
            if role == "师父":
                return "师徒", "徒弟"
        return rtype, role
    return None


def infer_from_context(ctx: str) -> tuple[str, str | None] | None:
    if re.search(r"其母[^。\n]{0,12}$", ctx) or "之母" in ctx or "母亲" in ctx:
        return "母子", None
    if re.search(r"其子[^。\n]{0,12}$", ctx) or "之父" in ctx or "父亲" in ctx:
        return "父子", None
    if "同类" in ctx or "并" in ctx and "成对" in ctx:
        return "朋友", None
    if any(w in ctx for w in ("收服", "降妖", "打死", "现本相叫", "鸡鸣收妖")):
        return "敌对", None
    if "克" in ctx and any(w in ctx for w in ("克蝎", "克蜈蚣", "物性相克", "破金光")):
        return "敌对", None
    if "奉" in ctx and "之命" in ctx:
        return "主仆", None
    return None


def infer_type(
    src: str, tgt: str, pages: dict[str, tuple]
) -> tuple[str, str | None]:
    key = (src, tgt)
    if key in MANUAL:
        return MANUAL[key]

    mirrored = mirror_reverse(src, tgt, pages)
    if mirrored:
        return mirrored

    s_fm, s_body = pages[src][0], pages[src][1]
    t_fm = pages[tgt][0]

    ctx = link_context(s_body, tgt)
    from_ctx = infer_from_context(ctx)
    if from_ctx:
        return from_ctx

    st, tt = s_fm.get("type"), t_fm.get("type")
    if (tt == "monster" and src in HEROES) or (st == "monster" and tgt in HEROES):
        return "敌对", None
    if tgt.endswith(RULER_SUFFIX) and not src.endswith(RULER_SUFFIX):
        return "君臣", None
    if src.endswith("国王") and not tgt.endswith(RULER_SUFFIX):
        return "君臣", None

    sf, tf = s_fm.get("faction"), t_fm.get("faction")
    if sf and sf == tf and sf in ("天庭", "佛界", "大唐", "灵山"):
        return "同僚", None

    stags = set(s_fm.get("tags") or [])
    ttags = set(t_fm.get("tags") or [])
    if "二十八宿" in stags and "二十八宿" in ttags:
        return "同僚", None
    if src in COURT_OFFICIALS and tgt in COURT_OFFICIALS:
        return "同僚", None
    if any(k in src or k in tgt for k in ("元帅", "太尉", "天君", "星官", "天王")):
        if sf == tf or (sf in ("天庭",) and tf in ("天庭",)):
            return "同僚", None

    if tgt in BUDDHA or src in BUDDHA:
        return "朋友", None
    if tt == "monster" or st == "monster":
        return "敌对", None
    return "朋友", None


def collect_missing(pages: dict[str, tuple]) -> list[tuple[str, str]]:
    ids = set(pages)
    missing: list[tuple[str, str]] = []
    for cid, (fm, body, _path) in pages.items():
        rel_targets = {r.get("target") for r in (fm.get("relations") or [])}
        for oid in sorted(ids):
            if oid != cid and f"[[{oid}]]" in body and oid not in rel_targets:
                missing.append((cid, oid))
    return missing


def write_frontmatter(path: Path, fm: dict, body: str) -> None:
    lines = ["---"]
    for k, v in fm.items():
        if k == "aliases":
            lines.append("aliases:")
            for a in v:
                lines.append(f"- {a}")
        elif isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                if isinstance(item, dict):
                    lines.append(f"- target: {item.get('target')}")
                    for sk, sv in item.items():
                        if sk != "target":
                            lines.append(f"  {sk}: {sv}")
                else:
                    lines.append(f"- {item}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    out = "\n".join(lines) + "\n"
    if body.startswith("\n"):
        out += body.lstrip("\n")
    else:
        out += body
    path.write_text(out, encoding="utf-8")


def add_relation(fm: dict, target: str, rtype: str, role: str | None) -> bool:
    rels = list(fm.get("relations") or [])
    if any(r.get("target") == target for r in rels):
        return False
    entry: dict = {"target": target, "type": rtype}
    if role:
        entry["role"] = role
    rels.append(entry)
    fm["relations"] = rels
    return True


def load_pages() -> dict[str, tuple]:
    pages: dict[str, tuple] = {}
    for path, fm, body in iter_characters(BOOK):
        cid = fm.get("id") or path.stem
        pages[cid] = (fm, body, path)
    return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pages = load_pages()
    missing = collect_missing(pages)
    if not missing:
        print("no missing body-link relations")
        return 0

    by_file: dict[Path, list[tuple[str, str, str, str | None]]] = {}
    for src, tgt in missing:
        rtype, role = infer_type(src, tgt, pages)
        if rtype not in VALID_TYPES:
            print(f"ERROR invalid type {rtype!r} for {src} -> {tgt}", file=sys.stderr)
            return 1
        path = pages[src][2]
        by_file.setdefault(path, []).append((src, tgt, rtype, role))
        role_s = f" role={role}" if role else ""
        print(f"  + {src} -> {tgt}: {rtype}{role_s}")

    if args.dry_run:
        print(f"dry-run: would add {len(missing)} edges on {len(by_file)} files")
        return 0

    n_files = 0
    for path, adds in sorted(by_file.items(), key=lambda x: str(x[0])):
        fm, body = None, None
        for _k, (f, b, p) in pages.items():
            if p == path:
                fm, body = dict(f), b
                break
        if fm is None:
            print(f"ERROR missing page {path}", file=sys.stderr)
            return 1
        changed = False
        for _src, tgt, rtype, role in adds:
            if add_relation(fm, tgt, rtype, role):
                changed = True
        if changed:
            write_frontmatter(path, fm, body)
            n_files += 1
            print(f"  wrote {path.name} (+{len(adds)})")

    remaining = collect_missing(load_pages())
    print(f"updated {n_files} files, added {len(missing)} edges, remaining={len(remaining)}")
    return 0 if not remaining else 1


if __name__ == "__main__":
    raise SystemExit(main())
