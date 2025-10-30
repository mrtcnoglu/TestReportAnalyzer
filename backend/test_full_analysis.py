# -*- coding: utf-8 -*-
"""End-to-end test script for comprehensive PDF analysis."""

import json
import sys

from pdf_analyzer import analyze_pdf_comprehensive


def main() -> None:
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "uploads/kielt22_86.pdf"

    print(f"Testing full analysis: {pdf_path}\n")
    print("=" * 70)

    try:
        result = analyze_pdf_comprehensive(pdf_path)

        print("\n=== TEMEL İSTATİSTİKLER ===")
        print(f"Toplam test: {result['basic_stats']['total_tests']}")
        print(f"Başarılı: {result['basic_stats']['passed']}")
        print(f"Başarısız: {result['basic_stats']['failed']}")

        print("\n=== KAPSAMLI ANALİZ ===")
        comp = result['comprehensive_analysis']

        print("\nTest Koşulları:")
        print("-" * 70)
        print(comp.get('test_conditions', 'YOK')[:300])

        print("\n\nGrafikler:")
        print("-" * 70)
        print(comp.get('graphs', 'YOK')[:300])

        print("\n\nSonuçlar:")
        print("-" * 70)
        print(comp.get('results', 'YOK')[:300])

        print("\n\n=== KONTROL ===")
        if not comp.get('test_conditions') or len(comp.get('test_conditions', '')) < 50:
            print("⚠️  UYARI: Test koşulları eksik veya çok kısa!")
        else:
            print("✓ Test koşulları OK")

        if not comp.get('graphs') or len(comp.get('graphs', '')) < 50:
            print("⚠️  UYARI: Grafik analizi eksik veya çok kısa!")
        else:
            print("✓ Grafik analizi OK")

    except Exception as exc:  # pragma: no cover - manual script
        print(f"\n✗ HATA: {exc}")
        raise


if __name__ == "__main__":
    main()
