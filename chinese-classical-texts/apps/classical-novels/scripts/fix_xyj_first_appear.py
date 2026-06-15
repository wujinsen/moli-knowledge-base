#!/usr/bin/env python3
"""P2: 校正西游记人物 first_appear / aliases 以通过 trust_guard。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CHAPTER_DIR, iter_characters, parse_frontmatter  # noqa: E402

BOOK = "西游记"

# 世德堂原文用简称/异体字，需补 alias
EXTRA_ALIASES: dict[str, list[str]] = {
    "乌鸡国太子": ["太子"],
    "乌鸡国娘娘": ["娘娘", "正宫娘娘"],
    "宝林寺方丈": ["宝林寺僧人", "宝林寺"],
    "宝象国国王": ["国王"],
    "比丘国国王": ["国王"],
    "祭赛国国王": ["国王"],
    "慈云寺院主": ["院主"],
    "金光寺方丈": ["金光寺", "和尚"],
    "镇海寺方丈": ["院主"],
    "金平府刺史": ["刺史"],
    "赛太岁先锋": ["先锋"],
    "陈家庄老妪": ["老者", "陈老"],
    "黑水河渔翁": ["棹船的", "棹船人"],
    "关元帅": ["关"],
    "刘元帅": ["刘"],
    "庞元帅": ["庞"],
    "毕元帅": ["毕"],
    "苟元帅": ["苟"],
    "马元帅": ["马"],
    "赵元帅": ["赵"],
    "温元帅": ["温"],
    "崩将军": ["崩"],
    "芭将军": ["芭"],
    "康太尉": ["康"],
    "李太尉": ["李"],
    "姚公麟": ["姚"],
    "壁水貐": ["壁水㺄"],
    "魏征": ["魏徵"],
    "袁守诚": ["守诚"],
    "殷温娇": ["温娇"],
    "泾河龙王": ["泾河", "龙王"],
    "薛仁贵": ["薛"],
    "高翠兰": ["翠兰"],
    "金圣宫娘娘": ["金圣宫", "娘娘"],
    "精细鬼": ["精细"],
    "伶俐虫": ["伶俐"],
}

# 叙事首现回与 trust_guard 校验回不一致时强制指定
FIRST_APPEAR_OVERRIDE: dict[str, int] = {
    "魏征": 10,
    "袁守诚": 10,
    "薛仁贵": 11,
    "乌鸡国太子": 38,
    "乌鸡国娘娘": 38,
    "宝林寺方丈": 40,
    "精细鬼": 33,
    "伶俐虫": 33,
    "金圣宫娘娘": 69,
}

# 世德堂无具名，仅通本有；去掉 first_appear 让 trust_guard 跳过
REMOVE_FIRST_APPEAR: set[str] = {"虞世南"}


def load_chapter_text(ch: int) -> str:
    p = CHAPTER_DIR / BOOK / f"{ch:03d}.md"
    if not p.is_file():
        return ""
    _, body = parse_frontmatter(p)
    return body


def chapter_hit(text: str, names: list[str]) -> bool:
    return any(n and n in text for n in names)


def find_first_chapter(names: list[str]) -> int | None:
    for ch in range(1, 101):
        text = load_chapter_text(ch)
        if text and chapter_hit(text, names):
            return ch
    return None


def pick_aliases(cid: str, text: str, existing: list[str]) -> list[str]:
    out = list(existing)
    for a in EXTRA_ALIASES.get(cid, []):
        if a in text and a not in out and a != cid:
            out.append(a)
    return out


def update_file(
    path: Path,
    fm: dict,
    body: str,
    *,
    first: int | None,
    aliases: list[str],
    drop_first: bool = False,
) -> bool:
    changed = False
    if drop_first:
        if "first_appear" in fm:
            del fm["first_appear"]
            changed = True
    elif first and fm.get("first_appear") != f"第{first}回":
        fm["first_appear"] = f"第{first}回"
        changed = True
    old_aliases = fm.get("aliases") or []
    if aliases != old_aliases:
        fm["aliases"] = aliases
        changed = True
    if not changed:
        return False
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
    return True


def main() -> int:
    n = 0
    for path, fm, body in iter_characters(BOOK):
        cid = fm.get("id") or path.stem
        if cid in REMOVE_FIRST_APPEAR:
            aliases = fm.get("aliases") or []
            if update_file(path, fm, body, first=None, aliases=aliases, drop_first=True):
                print(f"  fix {cid} -> (no first_appear, 世德堂无具名)")
                n += 1
            continue

        names = [cid, fm.get("name", ""), *(fm.get("aliases") or [])]
        names += EXTRA_ALIASES.get(cid, [])
        names = [x for x in names if x]

        no = FIRST_APPEAR_OVERRIDE.get(cid)
        if no is None:
            m = re.search(r"\d+", fm.get("first_appear") or "")
            no = int(m.group()) if m else None

        text = load_chapter_text(no) if no else ""
        if not text or not chapter_hit(text, names):
            hit = find_first_chapter(names)
            if hit:
                no = hit
                text = load_chapter_text(hit)
            elif no:
                text = load_chapter_text(no)

        aliases = pick_aliases(cid, text, fm.get("aliases") or [])
        all_names = names + [a for a in aliases if a not in names]
        if no and not chapter_hit(text, all_names):
            hit = find_first_chapter(all_names)
            if hit:
                no = hit
                text = load_chapter_text(hit)
                aliases = pick_aliases(cid, text, aliases)

        if cid in FIRST_APPEAR_OVERRIDE:
            no = FIRST_APPEAR_OVERRIDE[cid]
            text = load_chapter_text(no)
            aliases = pick_aliases(cid, text, aliases)

        if update_file(path, fm, body, first=no, aliases=aliases):
            print(f"  fix {cid} -> ch{no} aliases={len(aliases)}")
            n += 1
    print(f"updated {n} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
