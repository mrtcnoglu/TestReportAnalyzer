"""Utilities for extracting and interpreting test results from PDF reports."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

import pdfplumber
from PyPDF2 import PdfReader


FAILURE_PATTERNS: Dict[str, Tuple[str, str]] = {
    r"timeout": (
        "Execution timed out",
        "Increase timeout thresholds or investigate performance bottlenecks.",
    ),
    r"nullpointer": (
        "Null reference encountered",
        "Add null checks and ensure dependent services return valid data.",
    ),
    r"connection refused": (
        "Service connection failed",
        "Verify service availability and network connectivity.",
    ),
    r"assertion": (
        "Assertion failed",
        "Review the expected conditions and update the test or implementation.",
    ),
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
        results.append(
            {
                "test_name": data.get("name", "Unknown Test").strip(),
                "status": status,
                "error_message": data.get("message") or "",
            }
        )
    return results


def analyze_failure(error_message: str) -> Dict[str, str]:
    """Return inferred failure reason and suggested fix based on message patterns."""
    message = (error_message or "").lower()
    for pattern, (reason, fix) in FAILURE_PATTERNS.items():
        if re.search(pattern, message):
            return {"failure_reason": reason, "suggested_fix": fix}
    return {
        "failure_reason": "Review the error details for root cause analysis.",
        "suggested_fix": "Consult the logs or stack trace for further investigation.",
    }
