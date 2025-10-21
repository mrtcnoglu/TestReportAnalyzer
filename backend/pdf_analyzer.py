"""Utilities for extracting and interpreting test results from PDF reports."""
from __future__ import annotations

"""Utilities for extracting and interpreting test results from PDF reports."""

import re
from pathlib import Path
from typing import Dict, List, Tuple

import pdfplumber
from PyPDF2 import PdfReader

from ai_analyzer import ai_analyzer


REPORT_TYPE_LABELS = {
    "r80": "R80 Darbe Testi",
    "r10": "R10 EMC Testi",
    "unknown": "Bilinmeyen",
}

_REPORT_TYPE_KEYWORDS = {
    "r80": [
        "ece r80",
        "r80",
        "darbe",
        "impact",
        "collision",
        "crash",
        "seat strength",
        "aufprall",
        "stoß",
    ],
    "r10": [
        "ece r10",
        "r10",
        "emc",
        "electromagnetic",
        "elektromanyetik",
        "elektromagnetische",
        "störfestigkeit",
        "radiated",
        "conducted",
    ],
}


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


def infer_report_type(text: str, filename: str = "") -> Tuple[str, str]:
    """Infer whether a report belongs to R80 or R10 based on its contents."""

    haystack = f"{filename}\n{text}".lower()
    scores = {key: 0 for key in _REPORT_TYPE_KEYWORDS}

    for key, keywords in _REPORT_TYPE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            occurrences = haystack.count(keyword)
            if occurrences <= 0:
                continue
            weight = 2 if keyword.startswith("ece") or " " in keyword else 1
            score += occurrences * weight
        scores[key] = score

    filename_lower = (filename or "").lower()
    if "r80" in filename_lower or "darbe" in filename_lower:
        scores["r80"] += 2
    if "r10" in filename_lower or "emc" in filename_lower:
        scores["r10"] += 2

    if scores["r80"] == scores["r10"]:
        if scores["r80"] == 0:
            return "unknown", REPORT_TYPE_LABELS["unknown"]

        r80_index = haystack.find("ece r80")
        if r80_index == -1:
            r80_index = haystack.find("r80")
        r10_index = haystack.find("ece r10")
        if r10_index == -1:
            r10_index = haystack.find("r10")

        if r80_index != -1 and (r10_index == -1 or r80_index < r10_index):
            inferred_type = "r80"
        elif r10_index != -1:
            inferred_type = "r10"
        elif "darbe" in haystack:
            inferred_type = "r80"
        elif "emc" in haystack:
            inferred_type = "r10"
        else:
            inferred_type = "unknown"
    else:
        inferred_type = "r80" if scores["r80"] > scores["r10"] else "r10"

    label = REPORT_TYPE_LABELS.get(inferred_type, REPORT_TYPE_LABELS["unknown"])
    return inferred_type, label


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
