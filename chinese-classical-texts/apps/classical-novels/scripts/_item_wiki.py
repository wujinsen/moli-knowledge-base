"""名物百科 ↔ 人物 frontmatter 的服饰/关键物品映射。

图鉴卡片字段语义（三书共用，build/prune/lint/audit 均须走此模块）：

| 书 | 卡片字段 | 允许 | 禁止 |
|----|----------|------|------|
| 红楼梦 | 喜好 | 性情/技艺/人名/具体饮食 | 地点、宴事、诊脉、主仆部属 |
| 红楼梦 | 关键物品（信物） | 佩饰/首饰/物证（costumes·accessory 等） | 地点、情节/宴链、机构（义学等）、人物 id、customs 礼仪链 |
| 金瓶梅 | 喜好 | 饮食/情欲/具体人物 | 帮闲差事、店铺、主仆部属 |
| 金瓶梅 | 服饰 | 原文可分的个人衣饰（比甲/皮袄/蟒衣等） | 六房齐整共用（锦裙绣袄/大红妆花袍等 wearers≥4） |
| 金瓶梅 | 关键物品 | 物证/乐器/毒物/名场面饮食 | 地点、情节链、人物 id、customs 凑分/结拜/宴饮 |
| 西游记 | 喜好 | 饮食/人物/名物；地点仅绑定人物白名单 | 洞府职责、主仆部属、**驻地=faction 勿填**、情节词（助战/叙旧） |
| 西游记 | 关键物品 | 主兵器/取经三宝（人物） | 地点、情节/职责链、人物 id；妖怪用 `法宝[]` |

清理脚本：prune_hlm_likes · prune_hlm_keepsakes · prune_jpm_likes · prune_jpm_keepsakes · prune_jpm_costumes · prune_xyj_likes · prune_xyj_keepsakes
全局审计：python scripts/audit_bestiary_semantics.py
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from _common import CHAR_DIR, CONTENT, DATA_DIR, parse_frontmatter

ITEM_DIRS = ("artifacts", "dishes", "medicines", "costumes", "customs")
PERSON_LIST_FIELDS = ("eaters", "wearers", "holders", "owners", "participants")
PERSON_SINGLE_FIELDS = ("wearer", "patient", "owner", "prescriber", "holder", "physician")
WIKI_LINK = re.compile(r"\[\[([^\]|]+)")

# 红楼梦图鉴「信物」：少量、可触可指的情物/佩饰/物证；非饮食宴饮/诊脉/地点链
HLM_KEEPSAKE_TAGS = frozenset({"信物", "佩饰", "情物"})
HLM_KEEPSAKE_OVERRIDES = frozenset(
    {
        "通灵宝玉",
        "金锁",
        "金麒麟",
        "冷香丸",
        "累丝金凤",
        "成窑杯",
        "折扇",
        "虾须镯",
        "求愿金镯",
        "护官符",
        "玫瑰露",
        "茯苓霜",
        "蔷薇硝",
        "风月宝鉴",
        "贾珠遗砚",
        "金寿星",
        "沉香拐",
        "伽南珠",
        "福寿香",
        "寿宴玉杯",
        "鸽子蛋",
    }
)
HLM_KEEPSAKE_BLOCK_MARKERS = (
    "起名", "扮", "送祟", "魇胜", "剪发", "抗婚", "省亲", "出嫁", "丧仪", "成婚",
    "夜宴", "宴席", "诊脉", "抄检",
)
HLM_KEEPSAKE_BLOCK_IDS = frozenset({"义学", "家塾"})


def _book_location_ids(book: str) -> set[str]:
    loc_dir = CONTENT / "locations" / book
    if not loc_dir.is_dir():
        return set()
    return {p.stem for p in loc_dir.glob("*.md")}


def is_hlm_keepsake(
    meta: dict,
    iid: str = "",
    *,
    book: str = "红楼梦",
    char_ids: set[str] | None = None,
) -> bool:
    """红楼梦 frontmatter「关键物品」= 图鉴「信物」，须为名物 id 且符合信物语义。"""
    if not iid:
        return False
    if char_ids and iid in char_ids:
        return False
    if iid in HLM_KEEPSAKE_BLOCK_IDS:
        return False
    if iid in _book_location_ids(book):
        return False
    if iid in HLM_KEEPSAKE_OVERRIDES:
        return True
    if any(m in iid for m in HLM_KEEPSAKE_BLOCK_MARKERS):
        return False
    kind = meta.get("kind", "")
    typ = meta.get("type", "")
    if kind in ("dishes", "medicines", "locations", "customs"):
        return False
    tags = set(meta.get("tags") or [])
    if kind == "costumes" and typ in ("accessory", "costume", "fabric", "jewelry"):
        if tags & HLM_KEEPSAKE_TAGS:
            return True
        return typ == "accessory" and ("首饰" in tags or "佩饰" in tags)
    if tags & HLM_KEEPSAKE_TAGS:
        return True
    if kind == "artifacts" and (tags & HLM_KEEPSAKE_TAGS or typ in ("accessory", "jewelry")):
        return True
    return False


def filter_hlm_keepsake_ids(
    ids: list[str],
    catalog: dict[str, dict],
    char_ids: set[str] | None = None,
    *,
    book: str = "红楼梦",
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        if is_hlm_keepsake(
            catalog.get(iid, {}), iid, book=book, char_ids=char_ids
        ):
            seen.add(iid)
            out.append(iid)
    return out


# 红楼梦图鉴「喜好」：性情/技艺/人名/具体饮食；非地点/宴事/诊脉/制度名物 id
HLM_LIKE_PLOT_MARKERS = ("省亲", "出嫁", "丧仪", "诊", "抄检", "成婚", "郁气", "夜宴", "宴")
HLM_LIKE_DUTY_MARKERS = ("佛事", "管家", "月例", "当差", "执事", "差事")

# 金瓶梅图鉴「喜好」：性情/情欲/饮食/具体人物；非帮闲差事/店铺/权势链
JPM_LIKE_DUTY_MARKERS = (
    "差事", "帮闲", "奉承", "贿赂", "认干亲", "认干娘", "争宠", "报仇", "权势",
    "财产", "结拜", "风月", "排场", "管家", "佛事", "月例", "打扮", "说嘴",
    "烟花", "缠头", "唱曲", "娘家", "赏赐", "说媒", "体面", "军功", "官位",
    "财礼", "款待", "声妓", "买卖", "使女", "奶母",
)
JPM_LIKE_LOCATION_EXTRA = frozenset(
    {
        "绒线铺", "厨房", "酒店", "酒楼", "东京", "南京", "清河县", "狮子街",
        "丽春院", "茶坊", "勾栏", "西门府", "王茶坊",
    }
)

LIKE_RELATION_BLOCK = frozenset({"主仆", "师徒", "同僚", "君臣"})
LIKE_RELATION_EMOTION = frozenset(
    {"情人", "恋慕", "夫妻", "兄弟", "姐妹", "父子", "母子", "祖孙", "妯娌"}
)
LIKE_PET_ALLOW = frozenset({"哮天犬"})


def is_char_like_ok(iid: str, char_ids: set[str], relations: list | None) -> bool:
    """人物 id 作喜好：排除组织边，保留情人/亲属等情感边。"""
    if iid not in char_ids:
        return True
    if iid in LIKE_PET_ALLOW:
        return True
    rel_types = {
        r.get("type")
        for r in (relations or [])
        if r.get("target") == iid and r.get("type")
    }
    if rel_types & LIKE_RELATION_EMOTION:
        return True
    if rel_types & LIKE_RELATION_BLOCK:
        return False
    return True


def is_hlm_valid_like(
    meta: dict,
    iid: str,
    char_ids: set[str],
    *,
    book: str = "红楼梦",
    relations: list | None = None,
) -> bool:
    """红楼梦 frontmatter「喜好」须为性情/技艺/人名/具体饮食，勿填地点/情节链 id。"""
    if not iid:
        return False
    if any(m in iid for m in HLM_LIKE_DUTY_MARKERS):
        return False
    if iid in char_ids:
        return is_char_like_ok(iid, char_ids, relations)
    loc_dir = CONTENT / "locations" / book
    if loc_dir.is_dir() and (loc_dir / f"{iid}.md").is_file():
        return False
    kind = meta.get("kind")
    if not kind:
        if any(m in iid for m in HLM_LIKE_PLOT_MARKERS):
            return False
        return True
    if kind in ("locations", "customs"):
        return False
    typ = meta.get("type") or ""
    tags = set(meta.get("tags") or [])
    if kind == "medicines":
        return typ not in ("diagnosis", "prescription", "pulse_case") and "诊脉" not in tags
    if kind == "dishes":
        return typ not in ("banquet", "feast") and "宴席" not in tags
    if kind in ("costumes", "artifacts"):
        return False
    return True


def filter_hlm_like_ids(
    ids: list[str],
    catalog: dict[str, dict],
    char_ids: set[str],
    *,
    book: str = "红楼梦",
    relations: list | None = None,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        meta = catalog.get(iid, {})
        if is_hlm_valid_like(
            meta if meta else {}, iid, char_ids, book=book, relations=relations
        ):
            seen.add(iid)
            out.append(iid)
    return out


def is_jpm_valid_like(
    meta: dict,
    iid: str,
    char_ids: set[str],
    *,
    book: str = "金瓶梅",
    relations: list | None = None,
) -> bool:
    if not iid:
        return False
    if any(m in iid for m in JPM_LIKE_DUTY_MARKERS):
        return False
    if iid in char_ids:
        return is_char_like_ok(iid, char_ids, relations)
    loc_dir = CONTENT / "locations" / book
    if loc_dir.is_dir() and (loc_dir / f"{iid}.md").is_file():
        return False
    if iid in JPM_LIKE_LOCATION_EXTRA:
        return False
    kind = meta.get("kind")
    if kind in ("locations", "customs"):
        return False
    if kind in ("artifacts", "dishes", "costumes"):
        return True
    if not kind:
        return True
    return True


def filter_jpm_like_ids(
    ids: list[str],
    catalog: dict[str, dict],
    char_ids: set[str],
    *,
    relations: list | None = None,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        meta = catalog.get(iid, {})
        if is_jpm_valid_like(meta if meta else {}, iid, char_ids, relations=relations):
            seen.add(iid)
            out.append(iid)
    return out


# 金瓶梅图鉴「关键物品」：可触可指的物证/乐器/毒物/名场面饮食；非礼仪制度/帮闲凑分/节令席面
JPM_KEEPSAKE_BLOCK_MARKERS = (
    "帮闲", "结拜", "分资", "凑分", "宴饮", "佛事", "月例", "帅府", "官钱粮",
    "历日", "冠带", "四贪", "吴典恩借银", "帮闲凑分", "结拜分资",
)
JPM_KEEPSAKE_OVERRIDES = frozenset(
    {
        "雪狮子",
        "红睡鞋",
        "砒霜",
        "胡僧药",
        "销金裙带",
        "药五香酒",
    }
)
JPM_FEAST_DISH_TAGS = frozenset({"宴席", "节令食", "元宵"})


def is_jpm_keepsake(
    meta: dict,
    iid: str = "",
    *,
    book: str = "金瓶梅",
    char_ids: set[str] | None = None,
) -> bool:
    """金瓶梅 frontmatter「关键物品」：物证/乐器/毒物/名场面饮食；勿填 custom 礼仪链。"""
    if not iid:
        return False
    if char_ids and iid in char_ids:
        return False
    if iid in JPM_LIKE_LOCATION_EXTRA or iid in _book_location_ids(book):
        return False
    if iid in JPM_KEEPSAKE_OVERRIDES:
        return True
    if any(m in iid for m in JPM_KEEPSAKE_BLOCK_MARKERS):
        return False
    kind = meta.get("kind", "")
    typ = meta.get("type", "")
    tags = set(meta.get("tags") or [])
    if kind in ("locations",):
        return False
    if kind == "medicines":
        typ = meta.get("type", "")
        tags = set(meta.get("tags") or [])
        if typ in ("diagnosis", "pulse_case"):
            return False
        if "诊脉" in tags:
            return False
        return True
    if kind == "customs":
        return bool(tags & {"物象谶", "命案", "转折"})
    if kind == "costumes":
        return typ in ("accessory", "weapon", "jewelry", "fabric")
    if kind == "dishes":
        if tags & JPM_FEAST_DISH_TAGS and "名场面" not in tags:
            return False
        return bool(tags & {"名场面", "命案"}) or (
            typ == "dish" and "饮食" in tags and "宴席" not in tags
        )
    if kind == "artifacts":
        return True
    return False


def filter_jpm_keepsake_ids(
    ids: list[str],
    catalog: dict[str, dict],
    char_ids: set[str] | None = None,
    *,
    book: str = "金瓶梅",
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        if is_jpm_keepsake(
            catalog.get(iid, {}), iid, book=book, char_ids=char_ids
        ):
            seen.add(iid)
            out.append(iid)
    return out


# 金瓶梅图鉴「服饰」：个人可辨衣饰；非六房齐整共用（名物 wearers 多人同挂）
JPM_GROUP_COSTUME_IDS = frozenset({"锦裙绣袄", "大红妆花袍"})
JPM_COSTUME_MULTI_WEARER_ALLOW: dict[str, frozenset[str]] = {
    "遍地金比甲": frozenset({"孟玉楼", "潘金莲"}),
}
JPM_GROUP_WEARER_THRESHOLD = 4


def is_jpm_costume_for_char(meta: dict, iid: str, char_id: str) -> bool:
    """金瓶梅 frontmatter「服饰」= 图鉴个人衣饰，非六房节令齐整共用项。"""
    if not iid or not char_id:
        return False
    kind = meta.get("kind", "")
    typ = meta.get("type", "")
    if kind != "costumes" and typ not in ("costume", "fabric", "accessory", "jewelry", "weapon"):
        return False
    if iid in JPM_GROUP_COSTUME_IDS:
        return False
    allowed = JPM_COSTUME_MULTI_WEARER_ALLOW.get(iid)
    if allowed is not None:
        return char_id in allowed
    if char_id in iid:
        return True
    wearers = meta.get("wearers") or []
    if isinstance(wearers, list) and len(wearers) >= JPM_GROUP_WEARER_THRESHOLD:
        return False
    owner = meta.get("wearer") or meta.get("owner") or ""
    if owner:
        return owner == char_id
    if char_id in wearers:
        return len(wearers) <= 3
    return not wearers


def filter_jpm_costume_ids(
    ids: list[str],
    catalog: dict[str, dict],
    char_id: str,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        if is_jpm_costume_for_char(catalog.get(iid, {}), iid, char_id):
            seen.add(iid)
            out.append(iid)
    return out


def validate_card_field_semantics(
    book: str,
    cid: str,
    fields: dict,
    catalog: dict[str, dict],
    char_ids: set[str],
) -> list[str]:
    """单人物图鉴 frontmatter / bestiary.json fields 语义校验。返回 issue 文案列表。"""
    issues: list[str] = []
    rel = fields.get("relations") or []
    ctype = fields.get("type") or "character"
    likes = fields.get("喜好") or []

    if book == "红楼梦":
        bad_likes = [x for x in likes if x not in filter_hlm_like_ids([x], catalog, char_ids, relations=rel)]
        if bad_likes:
            issues.append(f"喜好语义非法: {cid} · {bad_likes}")
        bad_keys = [
            x
            for x in (fields.get("关键物品") or [])
            if x
            not in filter_hlm_keepsake_ids([x], catalog, char_ids, book=book)
        ]
        if bad_keys:
            issues.append(f"关键物品非信物: {cid} · {bad_keys}")
    elif book == "金瓶梅":
        bad_likes = [x for x in likes if x not in filter_jpm_like_ids([x], catalog, char_ids, relations=rel)]
        if bad_likes:
            issues.append(f"喜好语义非法: {cid} · {bad_likes}")
        bad_keys = [
            x
            for x in (fields.get("关键物品") or [])
            if x not in filter_jpm_keepsake_ids([x], catalog, char_ids, book=book)
        ]
        if bad_keys:
            issues.append(f"关键物品非法: {cid} · {bad_keys}")
        bad_costumes = [
            x
            for x in (fields.get("服饰") or [])
            if x not in filter_jpm_costume_ids([x], catalog, cid)
        ]
        if bad_costumes:
            issues.append(f"服饰非个人: {cid} · {bad_costumes}")
    elif book == "西游记":
        rel = fields.get("relations") or []
        bad_likes = [
            x
            for x in likes
            if x
            not in filter_xyj_like_ids(
                [x],
                catalog,
                char_ids,
                char_id=cid,
                faction=fields.get("faction") or "",
                relations=rel,
            )
        ]
        if bad_likes:
            issues.append(f"喜好语义非法: {cid} · {bad_likes}")
        keys = fields.get("关键物品") or []
        if keys:
            filtered = filter_xyj_keepsake_ids(
                keys, catalog, cid, char_type=ctype, char_ids=char_ids, book=book
            )
            if ctype == "monster":
                issues.append(f"妖怪误填关键物品: {cid} · {keys}")
            elif filtered != keys:
                issues.append(f"关键物品非法: {cid} · {keys} → 应 {filtered}")
    return issues


def audit_bestiary_json_fields(book: str) -> list[str]:
    """校验 <slug>.bestiary.json 的 fields 段（源数据层）。"""
    import json

    slug = {"红楼梦": "hongloumeng", "金瓶梅": "jinpingmei", "西游记": "xiyouji"}.get(book)
    if not slug:
        return []
    path = DATA_DIR / f"{slug}.bestiary.json"
    if not path.is_file():
        return [f"缺少 {path.name}"]
    data = json.loads(path.read_text(encoding="utf-8"))
    catalog = list_item_catalog(book)
    char_ids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
    issues: list[str] = []
    for cid, entry in sorted((data.get("fields") or {}).items()):
        issues.extend(validate_card_field_semantics(book, cid, entry, catalog, char_ids))
    return issues


def hlm_keepsake_for_char(meta: dict, iid: str, char_id: str) -> bool:
    """crosslinks/回填：该名物是否应写入此人物 frontmatter「关键物品」。"""
    if not is_hlm_keepsake(meta, iid):
        return False
    kind = meta.get("kind", "")
    owner = meta.get("owner") or meta.get("wearer") or meta.get("holder") or ""
    if kind == "customs":
        return bool(owner and owner == char_id)
    if owner and owner != char_id:
        return False
    return True


def hlm_frontmatter_from_occ(
    items: list[str], catalog: dict[str, dict], char_id: str
) -> tuple[list[str], list[str]]:
    """从 crosslinks occupant 筛出可写入 frontmatter 的服饰/信物（红楼梦）。"""
    costumes: list[str] = []
    keys: list[str] = []
    seen_c: set[str] = set()
    seen_k: set[str] = set()
    for iid in items:
        if not iid:
            continue
        meta = catalog.get(iid, {})
        field = item_target_field(meta, "红楼梦")
        if field == "服饰" and iid not in seen_c:
            wear = meta.get("wearer") or meta.get("owner") or ""
            if wear and wear != char_id:
                continue
            seen_c.add(iid)
            costumes.append(iid)
        elif field == "关键物品" and hlm_keepsake_for_char(meta, iid, char_id) and iid not in seen_k:
            seen_k.add(iid)
            keys.append(iid)
    char_ids = {p.stem for p in (CHAR_DIR / "红楼梦").glob("*.md")}
    return costumes, filter_hlm_keepsake_ids(keys, catalog, char_ids, book="红楼梦")


# 西游记图鉴「关键物品」
XYJ_TANGSANBAO = frozenset({"九环锡杖", "锦襴袈裟", "紧箍"})


def is_xyj_keepsake(
    meta: dict,
    iid: str = "",
    char_id: str = "",
    *,
    book: str = "西游记",
    char_ids: set[str] | None = None,
) -> bool:
    """西游记 frontmatter「关键物品」= 主兵器或唐僧三宝；非符咒微器/地点/饮食链。"""
    if not iid:
        return False
    if char_ids and iid in char_ids:
        return False
    if iid in _book_location_ids(book):
        return False
    if meta.get("kind") == "artifacts":
        if char_id == "唐僧" and iid in XYJ_TANGSANBAO:
            return True
        if not char_id and iid in XYJ_TANGSANBAO:
            return True
        tags = set(meta.get("tags") or [])
        typ = meta.get("type", "")
        owner = meta.get("owner") or ""
        if char_id and owner and owner != char_id:
            return False
        if "五众兵器" in tags:
            return True
        if typ == "weapon":
            return True
    if any(m in iid for m in XYJ_DUTY_MARKERS):
        return False
    return False


def filter_xyj_keepsake_ids(
    ids: list[str],
    catalog: dict[str, dict],
    char_id: str = "",
    *,
    char_type: str = "",
    char_ids: set[str] | None = None,
    book: str = "西游记",
) -> list[str]:
    if char_type == "monster":
        return []
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        if is_xyj_keepsake(
            catalog.get(iid, {}),
            iid,
            char_id,
            book=book,
            char_ids=char_ids,
        ):
            seen.add(iid)
            out.append(iid)
    return out


# 西游记图鉴「喜好」：性情/人名/具体物；非地点/洞府/职责/情节链
XYJ_DUTY_MARKERS = (
    "护行",
    "传信",
    "报信",
    "当值",
    "听观音",
    "暗护",
    "护唐僧",
    "差遣",
    "敲锣",
    "验身",
    "执幢",
    "传帖",
    "买办",
    "点化",
    "调度",
    "缴旨",
    "记功",
    "请天兵",
    "奏请",
    "听候",
    "听揭谛",
    "云端报",
    "收伏坐骑",
    "随真君降妖",
    "敬僧",
    "忠义",
    "取经",
    "降妖",
    "挑担",
    "守戒",
    "钉钯会",
    "钉钯宴",
    "三打",
    "护国",
    "护教",
    "行刑",
    "传令",
    "巡逻",
    "看守",
    "当班",
    "兵器",
    "助战",
    "合围",
    "叙旧",
)
# 地点作喜好：须绑定特定人物（勿因 faction=灌江口 给全班底填灌江口）
XYJ_LIKE_LOCATION_FOR_CHAR: dict[str, frozenset[str]] = {
    "灌江口": frozenset({"二郎神"}),
    "高老庄": frozenset({"猪八戒"}),
    "五庄观": frozenset({"镇元子"}),
    "花果山": frozenset({"孙悟空"}),
    "长安": frozenset({"唐太宗"}),
}
XYJ_LIKE_GROUP_BLOCK = frozenset({"梅山兄弟", "梅山六兄弟", "一千二百草头神"})
XYJ_LIKE_PET_ALLOW = frozenset({"哮天犬"})
XYJ_LIKE_RELATION_BLOCK = frozenset({"主仆", "师徒", "同僚", "君臣"})
XYJ_LIKE_LOCATION_SUFFIX = ("国", "岭", "洞", "山", "河", "潭", "府", "州", "寺", "观", "园", "涧", "港", "口", "坡", "岸", "城")
CHIP_ITEM_KINDS = frozenset({"artifacts", "dishes", "costumes"})


def _xyj_location_like_ok(iid: str, char_id: str) -> bool:
    allowed = XYJ_LIKE_LOCATION_FOR_CHAR.get(iid)
    if allowed is not None:
        return char_id in allowed
    return False


def is_xyj_valid_like(
    meta: dict,
    iid: str,
    char_ids: set[str],
    *,
    char_id: str = "",
    faction: str = "",
    book: str = "西游记",
    relations: list | None = None,
) -> bool:
    if not iid:
        return False
    if faction and iid == faction:
        return False
    if any(m in iid for m in XYJ_DUTY_MARKERS):
        return False
    if iid in XYJ_LIKE_GROUP_BLOCK:
        return False
    if iid in char_ids:
        return is_char_like_ok(iid, char_ids, relations)
    loc_dir = CONTENT / "locations" / book
    is_loc_page = loc_dir.is_dir() and (loc_dir / f"{iid}.md").is_file()
    if is_loc_page or iid in XYJ_LIKE_LOCATION_FOR_CHAR or iid.endswith(XYJ_LIKE_LOCATION_SUFFIX):
        return _xyj_location_like_ok(iid, char_id)
    kind = meta.get("kind")
    if kind in ("artifacts", "dishes", "costumes"):
        return True
    if kind in ("locations", "customs", "medicines"):
        return False
    if not kind:
        return True
    return False


def filter_xyj_like_ids(
    ids: list[str],
    catalog: dict[str, dict],
    char_ids: set[str],
    *,
    char_id: str = "",
    faction: str = "",
    book: str = "西游记",
    relations: list | None = None,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for iid in ids:
        if not iid or iid in seen:
            continue
        meta = catalog.get(iid, {})
        if is_xyj_valid_like(
            meta if meta else {},
            iid,
            char_ids,
            char_id=char_id,
            faction=faction,
            book=book,
            relations=relations,
        ):
            seen.add(iid)
            out.append(iid)
    return out


def build_chip_item_ids(
    book: str,
    catalog: dict[str, dict],
    char_ids: set[str],
    *,
    extra_ids: set[str] | None = None,
) -> set[str]:
    """图鉴 chip 可链 `/i/` 的 id：真实名物页，不含人物名。"""
    out: set[str] = set()
    for iid, meta in catalog.items():
        if iid in char_ids:
            continue
        kind = meta.get("kind")
        if book == "西游记" and kind == "artifacts":
            out.add(iid)
        elif book == "红楼梦" and kind in CHIP_ITEM_KINDS | {"customs", "medicines"}:
            out.add(iid)
        elif book == "金瓶梅" and kind in CHIP_ITEM_KINDS | {"customs"}:
            out.add(iid)
    if extra_ids:
        for iid in extra_ids:
            if iid in char_ids:
                continue
            meta = catalog.get(iid, {})
            if meta.get("kind") in CHIP_ITEM_KINDS | {"customs", "medicines", "artifacts"}:
                out.add(iid)
    return out


def audit_item_ids_pollution(book: str, item_ids: set[str], char_ids: set[str]) -> list[str]:
    """item_ids.json 中误含人物 id → 图鉴 chip 会链向空白 `/i/` 页。"""
    return sorted(iid for iid in item_ids if iid in char_ids)


def list_item_catalog(book: str) -> dict[str, dict]:
    """item_id → {kind, type, ...frontmatter}"""
    catalog: dict[str, dict] = {}
    for kind in ITEM_DIRS:
        d = CONTENT / kind / book
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            fm, _ = parse_frontmatter(p)
            if fm.get("book") != book:
                continue
            iid = fm.get("id") or p.stem
            catalog[iid] = {"kind": kind, **fm}
    return catalog


def list_known_item_ids(book: str) -> set[str]:
    return set(list_item_catalog(book))


def item_target_field(meta: dict, book: str | None = None) -> str | None:
    """costume/fabric → 服饰；红楼梦信物 / 西游记主兵器 → 关键物品；金瓶梅等非服饰 → 关键物品。"""
    book = book or meta.get("book") or ""
    kind = meta.get("kind", "")
    typ = meta.get("type", "")
    iid = meta.get("id", "")
    if kind == "costumes" and typ in ("costume", "fabric"):
        return "服饰"
    if book == "红楼梦":
        return "关键物品" if is_hlm_keepsake(meta, iid) else None
    if book == "西游记":
        return "关键物品" if is_xyj_keepsake(meta, iid) else None
    if book == "金瓶梅":
        return "关键物品" if is_jpm_keepsake(meta, iid) else None
    return "关键物品"


def parse_person_refs(raw: str, char_ids: set[str]) -> list[str]:
    if not raw or not isinstance(raw, str):
        return []
    text = raw.strip()
    if text in char_ids:
        return [text]
    refs: list[str] = []
    for part in re.split(r"[；;、,]", text):
        name = re.sub(r"[（(].*?[）)]", "", part.strip()).strip()
        if not name:
            continue
        if name in char_ids:
            refs.append(name)
            continue
        for cid in sorted(char_ids, key=len, reverse=True):
            if cid in name:
                refs.append(cid)
                break
    return refs


def merge_item_lists(*lists: list[str] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for lst in lists:
        for x in lst or []:
            if not x or x in seen:
                continue
            seen.add(x)
            out.append(x)
    return out


def build_char_item_map(book: str) -> dict[str, dict[str, list[str]]]:
    """从名物页 wearer 等字段 + 人物正文 [[名物]] 链接汇总。"""
    char_ids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
    catalog = list_item_catalog(book)
    item_ids = set(catalog)
    buckets: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"服饰": set(), "关键物品": set()}
    )
    strict_keys = book in ("红楼梦", "西游记", "金瓶梅")
    list_fields = ("wearers",) if strict_keys else PERSON_LIST_FIELDS
    single_fields = ("wearer", "holder", "owner") if strict_keys else PERSON_SINGLE_FIELDS

    for iid, meta in catalog.items():
        field = item_target_field(meta, book)
        if not field:
            continue
        persons: set[str] = set()
        for key in list_fields:
            for raw in meta.get(key) or []:
                if isinstance(raw, str):
                    persons.update(parse_person_refs(raw, char_ids))
        for key in single_fields:
            raw = meta.get(key)
            if isinstance(raw, str):
                persons.update(parse_person_refs(raw, char_ids))
        if not strict_keys:
            for key in PERSON_LIST_FIELDS:
                if key in list_fields:
                    continue
                for raw in meta.get(key) or []:
                    if isinstance(raw, str):
                        persons.update(parse_person_refs(raw, char_ids))
            for key in PERSON_SINGLE_FIELDS:
                if key in single_fields:
                    continue
                raw = meta.get(key)
                if isinstance(raw, str):
                    persons.update(parse_person_refs(raw, char_ids))
        for pid in persons:
            if (
                book == "金瓶梅"
                and field == "服饰"
                and not is_jpm_costume_for_char(meta, iid, pid)
            ):
                continue
            buckets[pid][field].add(iid)

    if not strict_keys:
        char_dir = CHAR_DIR / book
        if char_dir.is_dir():
            for p in char_dir.glob("*.md"):
                cid = p.stem
                text = p.read_text(encoding="utf-8-sig")
                for m in WIKI_LINK.finditer(text):
                    iid = m.group(1).strip()
                    if iid not in item_ids:
                        continue
                    field = item_target_field(catalog[iid], book)
                    if not field:
                        continue
                    if (
                        book == "金瓶梅"
                        and field == "服饰"
                        and not is_jpm_costume_for_char(catalog[iid], iid, cid)
                    ):
                        continue
                    buckets[cid][field].add(iid)

    return {
        cid: {k: sorted(v) for k, v in fields.items() if v}
        for cid, fields in buckets.items()
        if any(fields.values())
    }


def merge_fields_with_wiki(
    entry: dict,
    wiki: dict[str, list[str]] | None,
    item_ids: set[str],
    *,
    book: str | None = None,
    catalog: dict[str, dict] | None = None,
) -> dict:
    out = dict(entry)
    wiki = wiki or {}
    book = book or out.get("book") or ""
    strict_key_items = book in ("红楼梦", "西游记", "金瓶梅")
    for field in ("服饰", "关键物品"):
        wiki_part = [] if (strict_key_items and field == "关键物品") else (wiki.get(field) or [])
        out[field] = merge_item_lists(out.get(field), wiki_part)
    if book == "金瓶梅" and catalog is not None:
        char_ids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
        cid = out.get("id") or ""
        costumes = filter_jpm_costume_ids(out.get("服饰") or [], catalog, cid)
        if costumes:
            out["服饰"] = costumes
        else:
            out.pop("服饰", None)
        keys = filter_jpm_keepsake_ids(
            out.get("关键物品") or [], catalog, char_ids, book=book
        )
        if keys:
            out["关键物品"] = keys
        else:
            out.pop("关键物品", None)
    if book == "红楼梦" and catalog is not None:
        char_ids = {p.stem for p in (CHAR_DIR / book).glob("*.md")} if book else set()
        keys = filter_hlm_keepsake_ids(
            out.get("关键物品") or [], catalog, char_ids, book=book
        )
        if keys:
            out["关键物品"] = keys
        else:
            out.pop("关键物品", None)
    elif book == "西游记" and catalog is not None:
        char_ids = {p.stem for p in (CHAR_DIR / book).glob("*.md")}
        char_id = out.get("id") or ""
        char_type = out.get("type") or ""
        keys = filter_xyj_keepsake_ids(
            out.get("关键物品") or [],
            catalog,
            char_id,
            char_type=char_type,
            char_ids=char_ids,
            book=book,
        )
        if keys:
            out["关键物品"] = keys
        else:
            out.pop("关键物品", None)
    for field in ("服饰", "关键物品"):
        if not out.get(field):
            out.pop(field, None)
    return out
