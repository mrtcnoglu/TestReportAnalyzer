# -*- coding: utf-8 -*-
"""Configuration helpers for AI integrations."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env file if present without leaking secrets into repo
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

AI_PROVIDER = os.getenv("AI_PROVIDER", "none").strip().lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

AI_OPENAI_MODEL = os.getenv("AI_OPENAI_MODEL", "gpt-4o-mini").strip()
AI_ANTHROPIC_MODEL = os.getenv(
    "AI_ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620"
).strip()

def _int_from_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


AI_MAX_TOKENS = _int_from_env("AI_MAX_TOKENS", 1200)
AI_TIMEOUT_S = _int_from_env("AI_TIMEOUT_S", 60)


def ai_config_status() -> dict[str, object]:
    """Return a sanitized snapshot of the AI configuration state."""
    return {
        "provider": AI_PROVIDER,
        "has_openai": bool(OPENAI_API_KEY),
        "has_claude": bool(ANTHROPIC_API_KEY),
        "openai_model": AI_OPENAI_MODEL,
        "anthropic_model": AI_ANTHROPIC_MODEL,
        "max_tokens": AI_MAX_TOKENS,
        "timeout_s": AI_TIMEOUT_S,
    }
