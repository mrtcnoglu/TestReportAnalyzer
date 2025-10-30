# -*- coding: utf-8 -*-
"""Utility script to inspect table extraction results for a PDF file."""
from __future__ import annotations

import sys

import pdfplumber


def main() -> None:
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "uploads/kielt22_86.pdf"

    print(f"PDF: {pdf_path}\n")
    print("=" * 70)

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            print(f"\nSAYFA {page_number}")
            print("-" * 70)

            tables = page.extract_tables() or []
            print(f"Tablo sayısı: {len(tables)}")

            for table_index, table in enumerate(tables, 1):
                print(f"\nTablo {table_index}:")
                print(f"Satır sayısı: {len(table)}")
                print("İlk 3 satır:")
                for row in table[:3]:
                    row_values = [str(cell)[:20] if cell else "-" for cell in row]
                    print("  |  ".join(row_values))

            if page_number >= 3:
                break


if __name__ == "__main__":
    main()
