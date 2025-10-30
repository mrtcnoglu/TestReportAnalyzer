"""Utilities for extracting and interpreting test results from PDF reports."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber
from PyPDF2 import PdfReader

try:  # pragma: no cover - allow execution both as package and script
    from .ai_analyzer import (
        ai_analyzer,
        analyze_detailed_data,
        analyze_graphs,
        analyze_results,
        analyze_test_conditions,
        generate_comprehensive_report,
    )
    from .pdf_section_analyzer import (
        detect_sections,
        detect_subsections,
        identify_section_language,
    )
    from .structured_data_parser import parse_test_conditions_structured
except ImportError:  # pragma: no cover
    from ai_analyzer import (  # type: ignore
        ai_analyzer,
        analyze_detailed_data,
        analyze_graphs,
        analyze_results,
        analyze_test_conditions,
        generate_comprehensive_report,
    )
    from pdf_section_analyzer import (  # type: ignore
        detect_sections,
        detect_subsections,
        identify_section_language,
    )
    from structured_data_parser import parse_test_conditions_structured  # type: ignore

PASS_PATTERN = r"(PASS|PASSED|SUCCESS|OK|✓|SUCCESSFUL|Başarılı|Geçti|BAŞARILI|GEÇTİ|Basarili|Gecti)"
FAIL_PATTERN = r"(FAIL|FAILED|ERROR|EXCEPTION|✗|FAILURE|Başarısız|Kaldı|Hata|BAŞARISIZ|KALDI|HATA|Basarisiz|Kaldi)"
TEST_NAME_PATTERN = r"(?:Test[:\s]+|test_|TEST[:\s-]+|Senaryo[:\s]+|SENARYO[:\s]+)([^\n\r]+)"

logger = logging.getLogger(__name__)

_PASS_KEYWORDS = {
    "pass",
    "passed",
    "success",
    "successful",
    "ok",
    "✓",
    "başarılı",
    "başarili",
    "geçti",
    "basarili",
    "gecti",
}

_FAIL_KEYWORDS = {
    "fail",
    "failed",
    "error",
    "exception",
    "✗",
    "failure",
    "başarısız",
    "başarisiz",
    "kaldı",
    "hata",
    "basarisiz",
    "kaldi",
}

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

_STATUS_TOKEN_PATTERN = re.compile(rf"{PASS_PATTERN}|{FAIL_PATTERN}", re.IGNORECASE)
_SUMMARY_SKIP_PATTERN = re.compile(
    r"\b(summary|özet|toplam|overall|istatistik|general report)\b", re.IGNORECASE
)


def _ensure_text_string(text_or_dict: object) -> str:
    """Return a string representation for extracted text results."""

    if isinstance(text_or_dict, dict):
        structured = text_or_dict.get("structured_text")
        if structured:
            return str(structured)
        fallback = text_or_dict.get("text")
        if fallback:
            return str(fallback)
        return ""
    return str(text_or_dict or "")


def extract_text_from_pdf(pdf_path: Path | str) -> Dict[str, object]:
    """Extract text and table contents from a PDF file."""

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    text_segments: List[str] = []
    structured_segments: List[str] = []
    tables: List[Dict[str, object]] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    header = f"\n=== SAYFA {page_number} - METİN ===\n"
                    structured_segments.append(f"{header}{page_text}")
                    text_segments.append(page_text)

                extracted_tables = page.extract_tables() or []
                for table_index, table in enumerate(extracted_tables, 1):
                    table_info = {
                        "page": page_number,
                        "table_num": table_index,
                        "data": table,
                    }
                    tables.append(table_info)

                    table_lines = [f"\n=== SAYFA {page_number} - TABLO {table_index} ==="]
                    for row in table:
                        if not row:
                            continue
                        row_text = " | ".join(str(cell) if cell else "" for cell in row)
                        table_lines.append(row_text)
                    structured_segments.append("\n".join(table_lines))
    except Exception:
        # pdfplumber may fail on certain PDFs; fall back below.
        text_segments = []
        structured_segments = []
        tables = []

    if not structured_segments:
        try:
            reader = PdfReader(str(pdf_path))
            text_pages = [page.extract_text() or "" for page in reader.pages]
            text_segments = [segment for segment in text_pages if segment]
            structured_segments = text_segments.copy()
        except Exception:
            text_segments = []
            structured_segments = []

    joined_text = "\n".join(text_segments).strip()
    joined_structured = "\n".join(structured_segments).strip()

    return {
        "text": joined_text,
        "tables": tables,
        "structured_text": joined_structured or joined_text,
    }


def _normalise_status(token: str) -> Optional[str]:
    token_normalized = (token or "").strip().lower()
    if token_normalized in _PASS_KEYWORDS:
        return "PASS"
    if token_normalized in _FAIL_KEYWORDS:
        return "FAIL"
    return None


def _clean_fragment(fragment: str) -> str:
    cleaned = (fragment or "").strip()
    if not cleaned:
        return ""
    cleaned = re.sub(r"^[\s\-–—:|•*·▪‣‧·•○●◦►»›]+", "", cleaned)
    cleaned = re.sub(r"^\d+\s*[.)-]+\s*", "", cleaned)
    cleaned = re.sub(r"[\s\-–—:|•*·▪‣‧·•○●◦►»›]+$", "", cleaned)
    return cleaned.strip()


def _extract_test_entry(line: str) -> Optional[dict]:
    if not line:
        return None

    matches = list(_STATUS_TOKEN_PATTERN.finditer(line))
    if not matches:
        return None

    status_match = matches[-1]
    status_at_line_start = status_match.start() == 0
    status = _normalise_status(status_match.group(0))
    if status is None:
        return None

    name_part = line[: status_match.start()]
    message_part = line[status_match.end() :]

    if not name_part.strip() and message_part.strip():
        name_part, message_part = message_part, ""

    test_name = _clean_fragment(name_part)
    error_message = _clean_fragment(message_part)

    if not error_message:
        split_match = re.split(r"\s[-–—:|]+\s", test_name, maxsplit=1)
        if len(split_match) > 1:
            test_name = _clean_fragment(split_match[0])
            error_message = _clean_fragment(split_match[1])
        else:
            colon_index = test_name.find(":")
            if colon_index != -1:
                potential_name = _clean_fragment(test_name[:colon_index])
                potential_message = _clean_fragment(test_name[colon_index + 1 :])
                if potential_message:
                    test_name = potential_name
                    error_message = potential_message

    if not error_message and status_at_line_start:
        dash_index = test_name.find(" - ")
        if dash_index != -1:
            potential_name = _clean_fragment(test_name[:dash_index])
            potential_message = _clean_fragment(test_name[dash_index + 3 :])
            if potential_message:
                test_name = potential_name
                error_message = potential_message

    if not test_name:
        test_pattern = re.compile(TEST_NAME_PATTERN, re.IGNORECASE)
        match = test_pattern.search(line)
        if match:
            test_name = _clean_fragment(match.group(1))

    if _SUMMARY_SKIP_PATTERN.search(line) or _SUMMARY_SKIP_PATTERN.search(test_name):
        return None

    if len(test_name) < 2:
        return None

    return {
        "test_name": test_name,
        "status": status,
        "error_message": error_message,
    }


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


def _finalize_entry(entry: dict, context: str) -> Dict[str, str]:
    test_name = entry.get("test_name", "Unknown Test") or "Unknown Test"
    status = entry.get("status", "PASS") or "PASS"
    error_message = (entry.get("error_message") or "").strip()

    result: Dict[str, str] = {
        "test_name": test_name.strip() or "Unknown Test",
        "status": status.upper(),
        "error_message": error_message,
    }

    if result["status"] == "FAIL":
        failure_reason, suggested_fix, ai_provider = analyze_failure(
            result["test_name"],
            error_message,
            context,
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

    result["name"] = result["test_name"]
    return result


def parse_test_results(text: str | dict) -> List[Dict[str, str]]:
    """Parse raw text (or extraction dict) into structured test result dictionaries."""

    text = _ensure_text_string(text)
    if not text:
        return []

    pass_pattern = re.compile(PASS_PATTERN, re.IGNORECASE)
    fail_pattern = re.compile(FAIL_PATTERN, re.IGNORECASE)
    test_pattern = re.compile(TEST_NAME_PATTERN, re.IGNORECASE)

    results: List[Dict[str, str]] = []
    current_entry: Optional[dict] = None
    current_test_hint: Optional[str] = None
    lines = text.splitlines()
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()

        if not line:
            if current_entry is not None:
                if current_test_hint and not current_entry.get("test_name"):
                    current_entry["test_name"] = current_test_hint
                results.append(_finalize_entry(current_entry, text))
                current_entry = None
            index += 1
            continue

        if _SUMMARY_SKIP_PATTERN.search(line):
            index += 1
            continue

        test_match = test_pattern.search(line)
        if test_match:
            current_test_hint = _clean_fragment(test_match.group(1)) or current_test_hint
            if current_entry is not None and not current_entry.get("test_name"):
                current_entry["test_name"] = current_test_hint

        entry = _extract_test_entry(line)
        if entry is not None:
            if current_test_hint and not entry.get("test_name"):
                entry["test_name"] = current_test_hint
            if current_entry is not None:
                results.append(_finalize_entry(current_entry, text))
            current_entry = entry
            current_test_hint = entry.get("test_name") or current_test_hint
            index += 1
            continue

        if current_entry is not None:
            appended = raw_line.strip()
            if appended:
                existing_message = current_entry.get("error_message", "")
                if existing_message:
                    current_entry["error_message"] = f"{existing_message} {appended}".strip()
                else:
                    current_entry["error_message"] = appended
            index += 1
            continue

        if current_test_hint:
            if pass_pattern.search(line):
                entry = {
                    "test_name": current_test_hint,
                    "status": "PASS",
                    "error_message": "",
                }
                results.append(_finalize_entry(entry, text))
                current_test_hint = None
                current_entry = None
                index += 1
                continue

            if fail_pattern.search(line):
                error_lines: List[str] = []
                lookahead = index + 1
                while lookahead < len(lines):
                    follow_line = lines[lookahead].strip()
                    if not follow_line:
                        break
                    if pass_pattern.search(follow_line) or fail_pattern.search(follow_line):
                        break
                    error_lines.append(follow_line)
                    lookahead += 1
                error_message = " ".join(error_lines).strip() or "Detay yok"
                entry = {
                    "test_name": current_test_hint,
                    "status": "FAIL",
                    "error_message": error_message,
                }
                results.append(_finalize_entry(entry, text))
                current_test_hint = None
                current_entry = None
                index = lookahead
                continue

        index += 1

    if current_entry is not None:
        if current_test_hint and not current_entry.get("test_name"):
            current_entry["test_name"] = current_test_hint
        results.append(_finalize_entry(current_entry, text))

    if not results:
        results = _parse_table_format(text)

    return results


def analyze_pdf_comprehensive(pdf_path: Path | str) -> Dict[str, object]:
    """Run a comprehensive analysis for a PDF by examining its sections individually."""

    logger.info("\n%s", "=" * 70)
    logger.info("KAPSAMLI PDF ANALİZİ BAŞLADI")
    logger.info("Dosya: %s", pdf_path)
    logger.info("%s\n", "=" * 70)

    try:
        logger.info("ADIM 1: Text ve Tablo Extraction")
        extraction_result = extract_text_from_pdf(pdf_path)
        text = extraction_result.get("structured_text") or _ensure_text_string(extraction_result)
        tables = extraction_result.get("tables") or []

        logger.info("  ✓ Text uzunluğu: %s karakter", len(text or ""))
        logger.info("  ✓ Tablo sayısı: %s", len(tables))
        if text:
            logger.info("  ✓ İlk 200 karakter: %s", text[:200])

        logger.info("\nADIM 2: Temel Test Parse")
        basic_results = parse_test_results(text)
        logger.info("  ✓ Bulunan test sayısı: %s", len(basic_results))

        logger.info("\nADIM 3: Bölüm Tanıma")
        sections = detect_sections(text)
        logger.info("  ✓ Tespit edilen bölüm sayısı: %s", len([v for v in sections.values() if v]))
        for section_name, section_content in sections.items():
            if section_content:
                logger.info("    - %s: %s karakter", section_name, len(section_content))

        if not sections or all(not value for value in sections.values()):
            logger.warning("  ⚠ UYARI: Hiçbir bölüm tespit edilemedi!")
            logger.info("  Text örneği (ilk 500 karakter):\n%s", (text or "")[:500])

        language = identify_section_language(text)

        logger.info("\nADIM 4: Yapılandırılmış Veri Parse")
        structured_test_conditions: Optional[Dict[str, object]] = None
        test_conditions_text = sections.get("test_conditions", "")
        if test_conditions_text:
            logger.info("  Test koşulları bölümü bulundu, parse ediliyor...")
            structured_test_conditions = parse_test_conditions_structured(test_conditions_text) or {}
            structured_test_conditions["tables"] = tables
            logger.info("  ✓ Yapılandırılmış veri parse edildi")
        else:
            logger.warning("  ⚠ Test koşulları bölümü bulunamadı")

        logger.info("\nADIM 5: Alt Bölüm Tanıma")
        if test_conditions_text:
            subsections = detect_subsections(test_conditions_text)
            logger.info("  ✓ Alt bölüm sayısı: %s", len(subsections))
            for sub_name, sub_content in subsections.items():
                logger.info("    - %s: %s karakter", sub_name, len(sub_content or ""))
                if sub_content:
                    sections[sub_name] = sub_content
        else:
            logger.warning("  ⚠ Alt bölüm tanıma atlandı (test_conditions yok)")

        logger.info("\nADIM 6: AI Analizi")
        section_analyses: Dict[str, str] = {}

        logger.info("  6.1 Test Koşulları Analizi...")
        if structured_test_conditions:
            try:
                section_analyses["test_conditions"] = analyze_test_conditions(
                    test_conditions_text,
                    structured_data=structured_test_conditions,
                    language=language,
                )
                logger.info(
                    "  ✓ Test koşulları analiz edildi: %s karakter",
                    len(section_analyses["test_conditions"] or ""),
                )
            except Exception as exc:
                logger.error("  ✗ Test koşulları analiz hatası: %s", exc, exc_info=True)
                section_analyses["test_conditions"] = f"Analiz hatası: {exc}"
        else:
            logger.warning("  ⚠ Test koşulları analizi atlandı (yapılandırılmış veri yok)")
            section_analyses["test_conditions"] = "Test koşulları bölümü bulunamadı veya parse edilemedi."

        logger.info("  6.2 Grafik/Tablo Analizi...")
        graph_section = "\n".join(filter(None, [sections.get("graphs", ""), sections.get("load_values", "")]))
        if graph_section.strip() or tables:
            try:
                section_analyses["graphs"] = analyze_graphs(
                    graph_section or sections.get("graphs", ""),
                    tables=tables,
                    language=language,
                )
                logger.info(
                    "  ✓ Grafikler analiz edildi: %s karakter",
                    len(section_analyses["graphs"] or ""),
                )
            except Exception as exc:
                logger.error("  ✗ Grafik analiz hatası: %s", exc, exc_info=True)
                section_analyses["graphs"] = f"Analiz hatası: {exc}"
        else:
            logger.warning("  ⚠ Grafik bölümü bulunamadı")
            section_analyses["graphs"] = "Grafik veya tablo verisi bulunamadı."

        logger.info("  6.3 Sonuç Analizi...")
        results_text = sections.get("results", "")
        if results_text:
            try:
                section_analyses["results"] = analyze_results(results_text, language=language)
                logger.info(
                    "  ✓ Sonuçlar analiz edildi: %s karakter",
                    len(section_analyses["results"] or ""),
                )
            except Exception as exc:
                logger.error("  ✗ Sonuç analiz hatası: %s", exc, exc_info=True)
                section_analyses["results"] = f"Analiz hatası: {exc}"
        else:
            logger.warning("  ⚠ Sonuç bölümü bulunamadı")
            section_analyses["results"] = "Sonuç bölümü bulunamadı."

        section_analyses.setdefault("summary", sections.get("summary", ""))
        section_analyses.setdefault(
            "detailed_data",
            analyze_detailed_data(sections.get("detailed_data", ""), language=language),
        )

        logger.info("\nADIM 7: Kapsamlı Rapor Oluşturma")
        comprehensive_report = generate_comprehensive_report(
            section_analyses,
            language=language,
            header=sections.get("header", ""),
        )
        logger.info("  ✓ Rapor oluşturuldu")

        total_tests = len(basic_results)
        passed_tests = sum(1 for result in basic_results if result.get("status") == "PASS")
        failed_tests = sum(1 for result in basic_results if result.get("status") == "FAIL")

        metadata = {
            "analysis_language": language,
            "text_length": len(text or ""),
            "table_count": len(tables),
        }

        logger.info("\n%s", "=" * 70)
        logger.info("ANALİZ BAŞARIYLA TAMAMLANDI")
        logger.info("%s\n", "=" * 70)

        return {
            "basic_stats": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "tests": basic_results,
            },
            "sections": sections,
            "section_analyses": section_analyses,
            "comprehensive_analysis": comprehensive_report,
            "metadata": metadata,
            "raw_text": text,
            "structured_data": structured_test_conditions,
            "tables": tables,
        }

    except Exception as exc:  # pragma: no cover - defensive logging wrapper
        logger.error("\n%s", "=" * 70)
        logger.error("ANALİZ HATASI: %s", exc, exc_info=True)
        logger.error("%s\n", "=" * 70)
        raise


def _parse_table_format(text: str | dict) -> List[Dict[str, str]]:
    """Parse table-like test result structures."""

    text = _ensure_text_string(text)
    pass_pattern = re.compile(PASS_PATTERN, re.IGNORECASE)
    fail_pattern = re.compile(FAIL_PATTERN, re.IGNORECASE)

    results: List[Dict[str, str]] = []

    for line in text.splitlines():
        if "|" not in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2:
            continue

        test_name, status_cell = parts[0], parts[1]
        error_cell = parts[2] if len(parts) > 2 else ""

        if pass_pattern.search(status_cell):
            entry = {
                "test_name": _clean_fragment(test_name) or "Unknown Test",
                "status": "PASS",
                "error_message": "",
            }
            results.append(_finalize_entry(entry, text))
        elif fail_pattern.search(status_cell):
            entry = {
                "test_name": _clean_fragment(test_name) or "Unknown Test",
                "status": "FAIL",
                "error_message": _clean_fragment(error_cell) or "Detay yok",
            }
            results.append(_finalize_entry(entry, text))

    return results


def analyze_failure(test_name: str, error_message: str, test_context: str = ""):
    """AI veya rule-based analiz"""
    result = ai_analyzer.analyze_failure_with_ai(test_name, error_message, test_context)
    return (
        result["failure_reason"],
        result["suggested_fix"],
        result.get("ai_provider", "rule-based"),
    )
