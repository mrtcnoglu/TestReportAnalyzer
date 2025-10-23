# -*- coding: utf-8 -*-
"""Basic sanity checks for AI configuration loading."""
from __future__ import annotations

import importlib
import os
import sys


def _reload_config():
    module_name = "backend.config"
    if module_name in sys.modules:
        del sys.modules[module_name]
    return importlib.import_module(module_name)


def test_ai_provider_none(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg = _reload_config()
    assert cfg.AI_PROVIDER == "none"
    assert cfg.ai_config_status()["provider"] == "none"


def test_ai_provider_openai(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "chatgpt")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg = _reload_config()
    assert cfg.AI_PROVIDER == "chatgpt"
    assert cfg.OPENAI_API_KEY == "sk-test"
    assert cfg.ai_config_status()["has_openai"] is True
    assert cfg.ai_config_status()["has_claude"] is False


def test_ai_provider_claude(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = _reload_config()
    assert cfg.AI_PROVIDER == "claude"
    assert cfg.ANTHROPIC_API_KEY == "sk-ant-test"
    status = cfg.ai_config_status()
    assert status["has_claude"] is True
    assert status["has_openai"] is False
