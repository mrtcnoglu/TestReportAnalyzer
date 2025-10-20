"""Utilities for extracting and interpreting test results from PDF reports."""
from __future__ import annotations

"""Utilities for extracting and interpreting test results from PDF reports."""

import re
from pathlib import Path
from typing import Dict, List

import pdfplumber
from PyPDF2 import PdfReader

from ai_analyzer import ai_analyzer


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract plain text content from a PDF file using pdfplumber/PyPDF2."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        reader = PdfReader(str(pdf_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)


TEST_RESULT_PATTERN = re.compile(
    r"^(?P<name>[^\n]+?)[\s:-]+(?P<status>PASS|FAIL)(?:[\s:-]+(?P<message>.*))?$",
    re.IGNORECASE,
)


def parse_test_results(text: str) -> List[Dict[str, str]]:
    """Parse raw text into structured test result dictionaries."""
    results: List[Dict[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = TEST_RESULT_PATTERN.match(line)
        if not match:
            continue
        data = match.groupdict()
        status = data.get("status", "").upper()
        error_message = data.get("message") or ""

        result: Dict[str, str] = {
            "test_name": data.get("name", "Unknown Test").strip(),
            "status": status,
            "error_message": error_message,
        }

        if status == "FAIL":
            failure_reason, suggested_fix, ai_provider = analyze_failure(
                result["test_name"],
                error_message,
                text,
            )
            result.update(
                {
                    "failure_reason": failure_reason,
                    "suggested_fix": suggested_fix,
                    "ai_provider": ai_provider,
                }
            )
        else:
            result.update(
                {
                    "failure_reason": "",
                    "suggested_fix": "",
                    "ai_provider": "rule-based",
                }
            )

        results.append(result)

    return results


def analyze_failure(test_name: str, error_message: str, test_context: str = ""):
    """AI veya rule-based analiz"""
    result = ai_analyzer.analyze_failure_with_ai(test_name, error_message, test_context)
    return (
        result["failure_reason"],
        result["suggested_fix"],
        result.get("ai_provider", "rule-based"),
    )
