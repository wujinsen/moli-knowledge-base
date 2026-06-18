"""Dream tier catalog — 三书配置。"""
from __future__ import annotations

BOOK_SLUG = {
    "honglou": "红楼梦",
    "xiyouji": "西游记",
    "jinpingmei": "金瓶梅",
}

# 红楼梦：沿用历史 patch_hlm 梯队
HLM_TIERS: list[dict] = [
    {
        "id": "tier17",
        "label": "第十七梯队",
        "module": "patch_hlm_tier17_score31",
        "script": "patch_hlm_tier17_score31.py",
        "thinLabel": "score≤31",
        "goal": "≥32",
        "candidateMode": "module",
        "postApply": [
            "python scripts/reciprocate_relations.py 红楼梦",
            "python scripts/build_relations.py 红楼梦",
        ],
    },
    {
        "id": "tier14",
        "label": "第十四梯队",
        "module": "patch_hlm_tier14_score29",
        "script": "patch_hlm_tier14_score29.py",
        "thinLabel": "score=28",
        "goal": "≥29",
        "candidateMode": "module",
        "postApply": [
            "python scripts/build_relations.py 红楼梦",
            "python scripts/build_hlm_tier14_link_topic.py",
        ],
    },
    {
        "id": "tier10",
        "label": "第十梯队",
        "module": "patch_hlm_tier10_score22",
        "script": "patch_hlm_tier10_score22.py",
        "thinLabel": "score≤22",
        "goal": "≥23",
        "candidateMode": "subprocess_score",
        "subprocessOnly": True,
        "postApply": ["python scripts/build_relations.py 红楼梦"],
    },
    {
        "id": "weak_inbound",
        "label": "弱入链巩固",
        "script": "patch_dream_weak_inbound.py",
        "thinLabel": "入链≤1",
        "goal": "hub 回链",
        "candidateMode": "weak_inbound",
        "candidateParams": {"maxInbound": 1},
        "subprocessOnly": True,
        "postApply": [
            "python scripts/reciprocate_relations.py 红楼梦",
            "python scripts/build_relations.py 红楼梦",
        ],
    },
]

XYJ_TIERS: list[dict] = [
    {
        "id": "weak_inbound",
        "label": "弱入链巩固",
        "script": "patch_dream_weak_inbound.py",
        "thinLabel": "入链≤1",
        "goal": "hub 回链",
        "candidateMode": "weak_inbound",
        "candidateParams": {"maxInbound": 1},
        "subprocessOnly": True,
        "postApply": [
            "python scripts/reciprocate_relations.py 西游记",
            "python scripts/build_relations.py 西游记",
        ],
    },
    {
        "id": "skeleton",
        "label": "结构骨架补全",
        "script": "patch_hlm_character_skeleton.py",
        "thinLabel": "缺主要关系/评析",
        "goal": "补章节骨架",
        "candidateMode": "skeleton",
        "subprocessOnly": True,
        "postApply": ["python scripts/build_relations.py 西游记"],
    },
    {
        "id": "low_score_15",
        "label": "低密度压平 · score≤15",
        "script": "patch_dream_low_score.py",
        "scriptArgs": ["--thin-max", "15", "--limit", "60"],
        "thinLabel": "score≤15",
        "goal": "rel + hub",
        "candidateMode": "low_score",
        "candidateParams": {"thinMax": 15},
        "subprocessOnly": True,
        "postApply": [
            "python scripts/reciprocate_relations.py 西游记",
            "python scripts/build_relations.py 西游记",
        ],
    },
]

JPM_TIERS: list[dict] = [
    {
        "id": "weak_inbound",
        "label": "弱入链巩固",
        "script": "patch_dream_weak_inbound.py",
        "thinLabel": "入链≤1",
        "goal": "hub 回链",
        "candidateMode": "weak_inbound",
        "candidateParams": {"maxInbound": 1},
        "subprocessOnly": True,
        "postApply": [
            "python scripts/reciprocate_relations.py 金瓶梅",
            "python scripts/build_relations.py 金瓶梅",
        ],
    },
    {
        "id": "low_score_16",
        "label": "低密度压平 · score≤16",
        "script": "patch_dream_low_score.py",
        "scriptArgs": ["--thin-max", "16", "--limit", "80"],
        "thinLabel": "score≤16",
        "goal": "rel + hub",
        "candidateMode": "low_score",
        "candidateParams": {"thinMax": 16},
        "subprocessOnly": True,
        "postApply": [
            "python scripts/reciprocate_relations.py 金瓶梅",
            "python scripts/build_relations.py 金瓶梅",
        ],
    },
    {
        "id": "skeleton",
        "label": "结构骨架补全",
        "script": "patch_hlm_character_skeleton.py",
        "thinLabel": "缺主要关系/评析",
        "goal": "补章节骨架",
        "candidateMode": "skeleton",
        "subprocessOnly": True,
        "postApply": ["python scripts/build_relations.py 金瓶梅"],
    },
]

TIERS_BY_SLUG: dict[str, list[dict]] = {
    "honglou": HLM_TIERS,
    "xiyouji": XYJ_TIERS,
    "jinpingmei": JPM_TIERS,
}


def resolve_book(slug: str) -> tuple[str, list[dict]]:
    book = BOOK_SLUG.get(slug)
    if not book:
        raise ValueError(f"unknown book slug: {slug}")
    return book, TIERS_BY_SLUG[slug]
