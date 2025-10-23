# -*- coding: utf-8 -*-
"""Provider selection and fallback logic for AI analysis."""
from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - support execution without package context
    from .claude_client import analyze_with_claude
    from .config import AI_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY
    from .openai_client import analyze_with_openai
except ImportError:  # pragma: no cover
    from claude_client import analyze_with_claude  # type: ignore
    from config import AI_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY  # type: ignore
    from openai_client import analyze_with_openai  # type: ignore


def analyze_with_ai(text: str) -> Dict[str, Any]:
    """Analyze the supplied text using the configured AI provider(s)."""
    provider = AI_PROVIDER or "none"
    if provider == "none":
        raise RuntimeError("AI provider is 'none'")

    if provider in {"claude", "both"} and ANTHROPIC_API_KEY:
        try:
            return analyze_with_claude(text)
        except Exception:
            if provider != "both":
                raise

    if provider in {"chatgpt", "both"} and OPENAI_API_KEY:
        return analyze_with_openai(text)

    raise RuntimeError("AI configured but no working provider/key available.")
