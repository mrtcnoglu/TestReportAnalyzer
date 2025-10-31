# -*- coding: utf-8 -*-
"""PDF format detection and specialized parsing utilities."""
from __future__ import annotations

import re
from typing import Dict, List


def detect_pdf_format(text: str) -> str:
    """Detect the PDF format based on textual cues."""
    text_lower = (text or "").lower()

    if any(
        keyword in text_lower
        for keyword in [
            "nosab 16140",
            "tuv rheinland",
            "tüv rheinland",
            "kielt",
            "prüfbericht",
            "testbedingungen",
            "belastungswerte",
            "schlittenverzögerung",
        ]
    ):
        return "kielt_format"

    if "junit" in text_lower or "<testsuite" in text_lower:
        return "junit_format"

    return "generic"


def parse_kielt_format(text: str) -> Dict[str, str]:
    """Parse sections for the Kielt/TÜV style PDF reports."""
    sections: Dict[str, str] = {}

    test_cond_match = re.search(
        r"(?:Test\s*Conditions?|Testbedingungen|Test\s*Koşulları)[:\s]+(.+?)(?=Schlittenverzögerung|Belastungswerte|===|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if test_cond_match:
        sections["test_conditions"] = test_cond_match.group(1).strip()[:1000]

    sled_match = re.search(
        r"Schlittenverzögerung[:\s]+(.+?)(?=Belastungswerte|===|\n\n|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if sled_match:
        sections["sled_deceleration"] = sled_match.group(1).strip()[:800]

    load_match = re.search(
        r"(?:Belastungswerte|Load\s*Values?|Yük\s*Değerleri)[:\s]*(.+?)(?=Fotodokumentation|===|Abb\.|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if load_match:
        sections["load_values"] = load_match.group(1).strip()[:1500]

    table_pattern = r"===\s*SAYFA\s*\d+\s*-\s*TABLO\s*\d+\s*===(.+?)(?====|$)"
    tables_text: List[str] = []
    for match in re.finditer(table_pattern, text, re.IGNORECASE | re.DOTALL):
        tables_text.append(match.group(1).strip()[:600])

    if tables_text:
        sections["tables_text"] = "\n\n".join(tables_text)

    photo_match = re.search(
        r"(?:Fotodokumentation|Photo\s*documentation|Fotoğraf)[:\s]*(.+?)(?=Abb\.|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if photo_match:
        sections["photo_docs"] = photo_match.group(1).strip()[:500]

    return sections


def extract_measurement_params(text: str) -> List[Dict[str, object]]:
    """Extract measurement parameters from the Kielt/TÜV report text."""
    params: List[Dict[str, object]] = []

    param_patterns = [
        (r"Kopfbeschl\.[^\n]*", "Kopfbeschl. (Baş ivmesi)", "g"),
        (r"Brustbeschl\.[^\n]*", "Brustbeschl. (Göğüs ivmesi)", "g"),
        (r"Oberschenkelkraft[^\n]*", "Oberschenkelkraft (Uyluk kuvveti)", "kN"),
        (r"FAC\s*right[^\n]*", "FAC right", "kN"),
        (r"FAC\s*left[^\n]*", "FAC left", "kN"),
    ]

    number_pattern = re.compile(r"[-+]?\d+[\d,.]*")

    for pattern, name, unit in param_patterns:
        values: List[str] = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            segment = match.group(0)
            numbers = number_pattern.findall(segment)
            cleaned_numbers = [num.strip() for num in numbers if num.strip()]
            values.extend(cleaned_numbers)
        if values:
            params.append({"name": name, "unit": unit, "values": values})

    return params


__all__ = [
    "detect_pdf_format",
    "parse_kielt_format",
    "extract_measurement_params",
]
