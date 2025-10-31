# -*- coding: utf-8 -*-
"""Manual test script for the Kielt/TÜV PDF parser."""

from pdf_format_detector import (
    detect_pdf_format,
    extract_measurement_params,
    parse_kielt_format,
)

pdf_text = """
Test Conditions: UN-R80
Date: 11.02.2022
Test vehicle: MAN LE

Schlittenverzögerung: Examiner: IMW Test conditions: UN-R80

Belastungswerte:
SAYFA 3 - TABLO 2
HAC, [162.45, 174.5 ms] | 308.00 a Kopf über 3 ms [g]
Kopfbeschl. a [g] 45.2
Brustbeschl. a [g] 38.7
Oberschenkelkraft F [kN] 3.89

TABLO 3
HAC, [162.45, 174.5 ms] | 308.00 a Kopf über 3 ms [g]
"""

print("=== FORMAT TESPİTİ ===")
format_type = detect_pdf_format(pdf_text)
print(f"Format: {format_type}")

print("\n=== PARSE TEST ===")
sections = parse_kielt_format(pdf_text)
for key, value in sections.items():
    print(f"\n{key}:")
    print(value[:200])

print("\n=== MEASUREMENT PARAMS ===")
params = extract_measurement_params(pdf_text)
for param in params:
    print(f"{param['name']} [{param['unit']}]: {param['values']}")
