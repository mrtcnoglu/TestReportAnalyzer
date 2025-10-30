# -*- coding: utf-8 -*-
"""Utility script to inspect PDF contents for debugging purposes."""
import os
import sys

import pdfplumber


def debug_pdf(pdf_path: str) -> None:
    """Print a detailed analysis of the PDF content to stdout."""
    print("=" * 70)
    print(f"PDF DOSYASI: {pdf_path}")
    print("=" * 70)

    if not os.path.exists(pdf_path):
        print(f"HATA: Dosya bulunamadı - {pdf_path}")
        return

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"\nToplam Sayfa: {len(pdf.pages)}")
            print("\n" + "=" * 70)

            for index, page in enumerate(pdf.pages, 1):
                print(f"\n{'=' * 70}")
                print(f"SAYFA {index}")
                print(f"{'=' * 70}\n")

                text = page.extract_text()
                if text:
                    print("TEXT İÇERİĞİ:")
                    print("-" * 70)
                    print(text)
                    print("-" * 70)

                    print("\nANAHTAR KELİME ANALİZİ:")
                    keywords = {
                        "Pass İngilizce": ["pass", "passed", "success", "ok"],
                        "Fail İngilizce": ["fail", "failed", "error", "exception"],
                        "Pass Türkçe": ["başarılı", "geçti", "başarili", "gecti"],
                        "Fail Türkçe": ["başarısız", "kaldı", "hata", "basarisiz"],
                        "Test": ["test", "case", "suite", "scenario"],
                    }

                    text_lower = text.lower()
                    for category, words in keywords.items():
                        found = [word for word in words if word in text_lower]
                        if found:
                            print(f"  {category}: {', '.join(found)}")
                else:
                    print("TEXT İÇERİK YOK (Grafik/Image olabilir)")

                tables = page.extract_tables()
                if tables:
                    print(f"\n{len(tables)} ADET TABLO BULUNDU:")
                    for table_index, table in enumerate(tables, 1):
                        print(f"\nTablo {table_index}:")
                        print("-" * 70)
                        for row in table[:5]:
                            print(row)
                        if len(table) > 5:
                            print(f"... ({len(table) - 5} satır daha)")
                        print("-" * 70)
                else:
                    print("\nTABLO YOK")

                if index == 1:
                    print("\n(İlk sayfa analizi tamamlandı, diğer sayfalar atlandı)")
                    break

    except Exception as exc:  # pragma: no cover - diagnostic tool
        print(f"\nHATA: {exc}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        uploads_dir = "uploads"
        if os.path.exists(uploads_dir):
            pdf_files = [file for file in os.listdir(uploads_dir) if file.endswith(".pdf")]
            if pdf_files:
                pdf_path = os.path.join(uploads_dir, pdf_files[0])
                print(f"Varsayılan PDF kullanılıyor: {pdf_files[0]}\n")
            else:
                print("HATA: uploads/ klasöründe PDF bulunamadı")
                sys.exit(1)
        else:
            print("HATA: uploads/ klasörü bulunamadı")
            sys.exit(1)

    debug_pdf(pdf_path)
