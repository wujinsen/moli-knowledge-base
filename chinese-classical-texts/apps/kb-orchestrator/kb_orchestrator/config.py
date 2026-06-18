from __future__ import annotations

import os
from pathlib import Path

# apps/kb-orchestrator/kb_orchestrator/config.py → apps/
APPS_DIR = Path(__file__).resolve().parents[2]
NOVELS_ROOT = Path(os.environ.get("NOVELS_ROOT", APPS_DIR / "classical-novels")).resolve()

BOOK_SLUG: dict[str, str] = {
    "红楼梦": "honglou",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}
SLUG_BOOK = {v: k for k, v in BOOK_SLUG.items()}

CROSSLINKS_SLUG: dict[str, str] = {
    "红楼梦": "hongloumeng",
    "金瓶梅": "jinpingmei",
    "西游记": "xiyouji",
}

ITEM_DIRS = ("artifacts", "dishes", "medicines", "costumes", "customs")

# --- LLM agent (OpenAI-compatible) ---
# STUDIO_AGENT_MODE: auto | llm | mock  (default auto = llm if key present)
STUDIO_AGENT_MODE = os.environ.get("STUDIO_AGENT_MODE", "auto").strip().lower()
STUDIO_LLM_API_KEY = os.environ.get("STUDIO_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
STUDIO_LLM_BASE_URL = os.environ.get("STUDIO_LLM_BASE_URL") or None
STUDIO_LLM_MODEL = os.environ.get("STUDIO_LLM_MODEL", "gpt-4o-mini")
STUDIO_LLM_MAX_TOOL_ROUNDS = int(os.environ.get("STUDIO_LLM_MAX_TOOL_ROUNDS", "8"))


def agent_mode() -> str:
    mode = STUDIO_AGENT_MODE
    if mode == "auto":
        return "llm" if STUDIO_LLM_API_KEY else "mock"
    if mode in ("llm", "mock"):
        return mode
    return "mock"


def llm_configured() -> bool:
    return bool(STUDIO_LLM_API_KEY)
