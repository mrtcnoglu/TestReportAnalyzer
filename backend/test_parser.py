# -*- coding: utf-8 -*-
"""Simple smoke test for the PDF parser."""
from pdf_analyzer import parse_test_results


test_text = """
Test Raporu

Test 1: Login Test
Sonuç: Başarılı

Test 2: API Test  
Sonuç: Başarısız
Hata: Connection timeout

Test 3: Database Test
Sonuç: PASS
"""

print("Test Text Parse Ediliyor...\n")
results = parse_test_results(test_text)

print(f"Bulunan Test Sayısı: {len(results)}\n")
for index, result in enumerate(results, 1):
    print(f"{index}. {result['name']} - {result['status']}")
    if result['status'] == 'FAIL':
        print(f"   Hata: {result.get('error_message')}")
        print(f"   Neden: {result.get('failure_reason')}")
        print(f"   Öneri: {result.get('suggested_fix')}")
    print()
