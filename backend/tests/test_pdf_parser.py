"""Tests for PDF report parsing logic."""
from __future__ import annotations

from typing import List

import pytest


@pytest.fixture(autouse=True)
def stub_analyze_failure(monkeypatch):
    """Avoid external AI calls during tests by stubbing the analyzer."""

    def _fake_analyze(test_name: str, error_message: str, context: str):
        return (
            f"{test_name} failure analysis",
            f"Resolve issue in {test_name}",
            "chatgpt",
        )

    monkeypatch.setattr("backend.pdf_analyzer.analyze_failure", _fake_analyze)


def _parse(text: str) -> List[dict]:
    from backend.pdf_analyzer import parse_test_results

    return parse_test_results(text)


def test_parse_test_results_skips_summary_lines():
    sample_text = """
    Genel Özet: 6 test yürütüldü, 5 PASS, 1 FAIL
    Impact Test 01 ........ PASS
    Impact Test 02 ---- FAIL --- Gerilim sapması sınırı aştı
    Impact Test 03 - PASS
    Impact Test 04 FAIL  Voltaj toparlanmadı
      Ek bilgi: Ölçüm sırasında dalgalanma oluştu.
    Impact Test 05 : PASSED
    Impact Test 06 FAILED - Sensör bağlantısı koptu
    """

    results = _parse(sample_text)

    assert len(results) == 6

    failed = [result for result in results if result["status"] == "FAIL"]
    assert len(failed) == 3

    # Ensure follow-up lines are appended to the previous failure message
    failure_messages = {
        result["test_name"]: result["error_message"] for result in failed
    }
    assert (
        "Ek bilgi" in failure_messages.get("Impact Test 04", "")
    ), "Continuation lines should extend the failure description"

    # PASS entries should keep rule-based provider information
    pass_entries = [result for result in results if result["status"] == "PASS"]
    assert all(entry["ai_provider"] == "rule-based" for entry in pass_entries)

    # Failure entries should use stubbed AI provider output
    assert all(result["ai_provider"] == "chatgpt" for result in failed)


def test_parse_test_results_handles_status_prefix():
    sample_text = """
    FAIL - EMC Voltage Spike : Limit aşımı
    PASS : Ground Continuity
    FAILED – Harness Shielding : Isolation breakdown
    PASSED – Static Immunity
    """

    results = _parse(sample_text)

    assert len(results) == 4
    assert results[0]["test_name"] == "EMC Voltage Spike"
    assert results[0]["error_message"].startswith("Limit aşımı")
    assert results[0]["status"] == "FAIL"
    assert results[3]["status"] == "PASS"
