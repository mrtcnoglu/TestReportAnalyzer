# -*- coding: utf-8 -*-
"""Utility script to inspect the return type of ``extract_text_from_pdf``."""

from __future__ import annotations

import sys

from pdf_analyzer import extract_text_from_pdf


def main() -> None:
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "uploads/kielt22_86.pdf"
    print(f"Testing: {pdf_path}\n")

    result = extract_text_from_pdf(pdf_path)

    print(f"Type: {type(result)}")
    if isinstance(result, dict):
        print(f"Keys: {list(result.keys())}")
        print(f"\nText length: {len(result.get('text', ''))}")
        print(f"Structured text length: {len(result.get('structured_text', ''))}")
        print(f"Table count: {len(result.get('tables', []))}")

        print("\n=== First 200 chars of structured_text ===")
        print((result.get('structured_text') or "")[:200])
    else:
        print("ERROR: Result is not a dict!")


if __name__ == "__main__":
    main()
