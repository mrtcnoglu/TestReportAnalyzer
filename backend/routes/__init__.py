"""Flask routes for the TestReportAnalyzer backend."""
from __future__ import annotations

import os
import logging
import difflib
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.utils import secure_filename

try:  # pragma: no cover - import flexibility
    from .. import database
    from ..ai_analyzer import ai_analyzer
    from ..translation_utils import fallback_translate_text
    from ..pdf_analyzer import (
        REPORT_TYPE_LABELS,
        analyze_pdf_comprehensive,
        extract_text_from_pdf,
        infer_report_type,
        parse_test_results,
    )
except ImportError:  # pragma: no cover
    import database  # type: ignore
    from ai_analyzer import ai_analyzer  # type: ignore
    from translation_utils import fallback_translate_text  # type: ignore
    from pdf_analyzer import (  # type: ignore
        REPORT_TYPE_LABELS,
        analyze_pdf_comprehensive,
        extract_text_from_pdf,
        infer_report_type,
        parse_test_results,
    )

logger = logging.getLogger(__name__)

reports_bp = Blueprint("reports", __name__)


def _json_error(message: str, status_code: int = 400):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


def _resolve_report_type_label(raw_type: str | None) -> str:
    key = (raw_type or "unknown").strip().lower()
    default_label = REPORT_TYPE_LABELS.get("unknown", "Bilinmeyen")
    return REPORT_TYPE_LABELS.get(key, default_label)


def _derive_alignment_key(total_tests: int, passed_tests: int, failed_tests: int) -> str:
    if total_tests <= 0:
        return "unknown"
    if failed_tests == 0 and passed_tests > 0:
        return "strong"
    if passed_tests == 0 and failed_tests > 0:
        return "critical"
    if passed_tests > 0 and failed_tests > 0:
        return "mixed"
    return "unknown"


SUMMARY_LABELS = {
    "tr": {
        "summary": "Genel Özet",
        "conditions": "Test Koşulları",
        "improvements": "İyileştirme Önerileri",
        "technical": "Teknik Analiz Detayları",
        "highlights": "Öne Çıkan Bulgular",
        "failures": "Kritik Testler",
    },
    "en": {
        "summary": "Summary",
        "conditions": "Test Conditions",
        "improvements": "Improvement Suggestions",
        "technical": "Technical Analysis Details",
        "highlights": "Key Highlights",
        "failures": "Critical Tests",
    },
    "de": {
        "summary": "Zusammenfassung",
        "conditions": "Testbedingungen",
        "improvements": "Verbesserungsvorschläge",
        "technical": "Technische Analyse",
        "highlights": "Wesentliche Erkenntnisse",
        "failures": "Kritische Tests",
    },
}

LANGUAGE_TEMPLATES = {
    "tr": {
        "summary": (
            "{engine}, {filename} raporunu {report_type} kapsamında değerlendirdi. "
            "Toplam {total} testin {passed}'i başarılı, {failed}'i başarısız. Başarı oranı %{success_rate}."
        ),
        "no_tests": (
            "{engine}, {filename} raporunda değerlendirilecek test kaydı bulamadı."
        ),
        "conditions": (
            "Grafik ve metin bulguları karşılaştırıldığında test koşulları ile sonuçlar {alignment} uyum gösteriyor."
        ),
        "no_tests_conditions": (
            "Grafik ve metin içerikleri sınırlı olduğu için koşul/sonuç kıyaslaması yapılamadı."
        ),
        "alignment_words": {
            "strong": "yüksek",
            "mixed": "kısmi",
            "critical": "düşük",
            "unknown": "belirsiz",
        },
        "improvements_intro": "Başarısız testlerin başarıya ulaşması için öneriler:",
        "failure_with_fix": "{test} -> {reason}. Öneri: {fix}.",
        "failure_without_fix": (
            "{test} -> {reason}. Ek veri gerekli, test parametrelerini gözden geçirin."
        ),
        "improvements_success": (
            "Tüm testler başarıyla tamamlandı; mevcut süreç korunmalıdır."
        ),
        "no_tests_improvements": (
            "Ölçümleri içeren güncel bir test raporu yükleyerek analizi yeniden başlatın."
        ),
        "unknown_test_name": "Bilinmeyen Test",
        "default_reason": "Başarısızlık nedeni belirtilmedi",
        "labels": SUMMARY_LABELS["tr"],
    },
    "en": {
        "summary": (
            "{engine} reviewed {filename} as part of the {report_type} scope. "
            "A total of {total} tests were evaluated: {passed} passed, {failed} failed. Overall success rate {success_rate}%."
        ),
        "no_tests": (
            "{engine} could not find evaluable test results in {filename}."
        ),
        "conditions": (
            "Comparing charts and textual findings indicates {alignment} alignment between test conditions and outcomes."
        ),
        "no_tests_conditions": (
            "No comparison of conditions versus outcomes was possible because the report lacks measurements."
        ),
        "alignment_words": {
            "strong": "strong",
            "mixed": "partial",
            "critical": "low",
            "unknown": "unclear",
        },
        "improvements_intro": "To recover the failing tests, consider the following actions:",
        "failure_with_fix": "{test} -> {reason}. Recommendation: {fix}.",
        "failure_without_fix": (
            "{test} -> {reason}. Provide additional diagnostics and review acceptance criteria."
        ),
        "improvements_success": (
            "All tests passed; maintain the current validation approach."
        ),
        "no_tests_improvements": (
            "Upload a version of the report that includes executed test steps to receive guidance."
        ),
        "unknown_test_name": "Unnamed Test",
        "default_reason": "Failure cause not specified",
        "labels": SUMMARY_LABELS["en"],
    },
    "de": {
        "summary": (
            "{engine} hat den Bericht {filename} im Rahmen des {report_type} geprüft. "
            "Insgesamt {total} Tests: {passed} bestanden, {failed} fehlgeschlagen. Erfolgsquote {success_rate}%."
        ),
        "no_tests": (
            "{engine} konnte im Bericht {filename} keine auswertbaren Testergebnisse finden."
        ),
        "conditions": (
            "Der Vergleich von Diagrammen und Text zeigt eine {alignment} Übereinstimmung zwischen Prüfbedingungen und Ergebnissen."
        ),
        "no_tests_conditions": (
            "Ohne Messdaten ist kein Vergleich zwischen Bedingungen und Ergebnissen möglich."
        ),
        "alignment_words": {
            "strong": "hohe",
            "mixed": "teilweise",
            "critical": "geringe",
            "unknown": "unklare",
        },
        "improvements_intro": (
            "Um fehlgeschlagene Tests zu verbessern, werden folgende Schritte empfohlen:"
        ),
        "failure_with_fix": "{test} -> {reason}. Empfehlung: {fix}.",
        "failure_without_fix": (
            "{test} -> {reason}. Zusätzliche Messdaten bereitstellen und Grenzwerte überprüfen."
        ),
        "improvements_success": (
            "Alle Tests waren erfolgreich; der bestehende Prüfablauf kann beibehalten werden."
        ),
        "no_tests_improvements": (
            "Bitte eine Version des Berichts mit durchgeführten Tests hochladen, um Analysen zu erhalten."
        ),
        "unknown_test_name": "Unbenannter Test",
        "default_reason": "Fehlerursache nicht angegeben",
        "labels": SUMMARY_LABELS["de"],
    },
}

COMPARISON_LABELS = {
    "tr": {"overview": "Karşılaştırma Özeti", "details": "Teknik Farklar"},
    "en": {"overview": "Comparison Overview", "details": "Technical Differences"},
    "de": {"overview": "Vergleichsübersicht", "details": "Technische Unterschiede"},
}

COMPARISON_ZERO_OVERVIEW = {
    "tr": "Seçilen raporların test sonuçları birebir aynı görünüyor; farklılık tespit edilmedi.",
    "en": "The selected reports share the same test outcomes; no differences were detected.",
    "de": "Die ausgewählten Berichte zeigen keine Abweichungen in den Testergebnissen.",
}

COMPARISON_EMPTY_DETAILS = {
    "tr": "Farklılık bulunamadı.",
    "en": "No differing points were identified.",
    "de": "Es wurden keine Unterschiede festgestellt.",
}


def _merge_localized_summaries(
    fallback: dict, overrides: dict | None, *, translator=None
) -> dict:
    languages = ("tr", "en", "de")
    overrides = overrides if isinstance(overrides, dict) else {}
    fallback = fallback if isinstance(fallback, dict) else {}

    def _collect_field(field: str) -> tuple[dict[str, str], str, str]:
        collected: dict[str, str] = {}
        source_language = ""
        source_text = ""

        for language in languages:
            entry = overrides.get(language, {}) if isinstance(overrides, dict) else {}
            value = str(entry.get(field) or "").strip()
            if not value:
                continue

            detected_language = _detect_language(value)
            target_language = detected_language or language
            collected[target_language] = value

            if not source_language:
                source_language = target_language
                source_text = value

        if not collected:
            for language in languages:
                entry = fallback.get(language, {}) if isinstance(fallback, dict) else {}
                value = str(entry.get(field) or "").strip()
                if value and language not in collected:
                    collected[language] = value
                    if not source_language:
                        source_language = language
                        source_text = value

        ensured = (
            _ensure_multilingual_entries(collected, translator=translator)
            if collected
            else {}
        )

        return ensured, source_language, source_text

    summary_entries, summary_source_lang, summary_source_text = _collect_field("summary")
    conditions_entries, conditions_source_lang, conditions_source_text = _collect_field(
        "conditions"
    )
    improvements_entries, improvements_source_lang, improvements_source_text = _collect_field(
        "improvements"
    )

    merged: dict[str, dict[str, str]] = {}

    for language in languages:
        default_entry = fallback.get(language, {}) if isinstance(fallback, dict) else {}
        override_entry = overrides.get(language, {}) if isinstance(overrides, dict) else {}

        labels = dict(SUMMARY_LABELS.get(language, {}))
        for candidate in (default_entry, override_entry):
            candidate_labels = candidate.get("labels") if isinstance(candidate, dict) else {}
            if isinstance(candidate_labels, dict):
                for key, value in candidate_labels.items():
                    value_str = str(value).strip()
                    if value_str:
                        labels[key] = value_str

        fallback_summary = str(default_entry.get("summary") or "").strip()
        summary_text = str(summary_entries.get(language, "")).strip()
        if not summary_text and fallback_summary:
            summary_text = fallback_summary
        elif (
            summary_source_lang
            and language != summary_source_lang
            and summary_text == summary_source_text
            and fallback_summary
            and fallback_summary != summary_source_text
        ):
            summary_text = fallback_summary

        fallback_conditions = str(default_entry.get("conditions") or "").strip()
        conditions_text = str(conditions_entries.get(language, "")).strip()
        if not conditions_text and fallback_conditions:
            conditions_text = fallback_conditions
        elif (
            conditions_source_lang
            and language != conditions_source_lang
            and conditions_text == conditions_source_text
            and fallback_conditions
            and fallback_conditions != conditions_source_text
        ):
            conditions_text = fallback_conditions

        fallback_improvements = str(default_entry.get("improvements") or "").strip()
        improvements_text = str(improvements_entries.get(language, "")).strip()
        if not improvements_text and fallback_improvements:
            improvements_text = fallback_improvements
        elif (
            improvements_source_lang
            and language != improvements_source_lang
            and improvements_text == improvements_source_text
            and fallback_improvements
            and fallback_improvements != improvements_source_text
        ):
            improvements_text = fallback_improvements

        merged[language] = {
            "summary": summary_text,
            "conditions": conditions_text,
            "improvements": improvements_text,
            "labels": labels,
        }

    return merged


def _ensure_multilingual_entries(
    values: dict[str, str], *, translator=None
) -> dict[str, str]:
    normalised: dict[str, str] = {}
    for language, text in values.items():
        language_key = str(language).strip().lower()
        cleaned = str(text or "").strip()
        if language_key and cleaned:
            normalised[language_key] = cleaned

    if not normalised:
        return {}

    required_languages = ("tr", "en", "de")
    missing = [lang for lang in required_languages if not normalised.get(lang)]
    if not missing:
        return normalised

    source_language = None
    for candidate in required_languages:
        if normalised.get(candidate):
            source_language = candidate
            break

    if not source_language:
        sample_text = next(iter(normalised.values()), "")
        detected_language = _detect_language(sample_text)
        if detected_language:
            source_language = detected_language
        else:
            source_language = next(iter(normalised.keys()), "en")

    source_text = normalised.get(source_language) or next(iter(normalised.values()))

    translations: dict[str, str] = {}
    if translator and source_text:
        try:
            translations = translator.translate_texts(
                source_text,
                source_language=source_language,
                target_languages=missing,
            )
        except Exception as exc:  # pragma: no cover - yalnızca tanılama
            print(f"[routes] Çeviri isteği başarısız: {exc}")
            translations = {}

    for language in missing:
        translated = (translations.get(language) or "").strip() if translations else ""
        if not translated and source_text:
            translated = fallback_translate_text(
                source_text, source_language=source_language, target_language=language
            )
        if not translated:
            translated = source_text
        normalised[language] = translated

    return normalised


_LANGUAGE_DIACRITIC_HINTS = {
    "tr": "çğıöşüâîûı",
    "de": "äöüß",
}

_LANGUAGE_KEYWORD_HINTS = {
    "tr": (
        " koşul",
        " değerlendirme",
        " uzman",
        " rapor",
        " başar",
        " ölçüm",
        " cihaz",
        " sonuç",
    ),
    "de": (
        " der ",
        " die ",
        " und ",
        " wurde ",
        " mit ",
        " kamer",
        " aufzeich",
        "prüfung",
        " messung",
        " gerät",
        " fehler",
        " erfolg",
    ),
    "en": (
        " the ",
        " and ",
        " with ",
        " recorded",
        " camera",
        " failure",
        " success",
        " analysis",
        " conditions",
        " results",
        " notes",
        " note ",
    ),
}


def _detect_language(text: str) -> str | None:
    if not text:
        return None

    lowered = text.lower()
    normalized = re.sub(r"[^a-z0-9äöüßçğıöşüâîûı]+", " ", lowered).strip()
    padded = f" {normalized} " if normalized else ""
    scores: dict[str, int] = {"tr": 0, "en": 0, "de": 0}

    for language, characters in _LANGUAGE_DIACRITIC_HINTS.items():
        diacritic_score = sum(lowered.count(char) for char in characters)
        if diacritic_score:
            scores[language] += diacritic_score * 3

    for language, keywords in _LANGUAGE_KEYWORD_HINTS.items():
        for keyword in keywords:
            target = keyword.strip()
            if not target:
                continue

            if keyword.startswith(" ") or keyword.endswith(" "):
                haystack = padded
                needle = f" {target} "
                if haystack and needle in haystack:
                    scores[language] += 2 if len(target) > 3 else 1
            else:
                if target in normalized:
                    scores[language] += 2 if len(target) > 3 else 1

    best_language, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score <= 0:
        return None

    if sum(1 for score in scores.values() if score == best_score) > 1:
        return None

    return best_language


def _wrap_multilingual_text(text: str) -> dict[str, str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return {}
    detected_language = _detect_language(cleaned)
    if detected_language:
        return {detected_language: cleaned}
    return {"en": cleaned}


def _normalize_structured_section_value(value: object) -> dict[str, str]:
    if isinstance(value, dict):
        normalized: dict[str, str] = {}
        for language, text in value.items():
            language_key = str(language).strip().lower()
            cleaned = str(text or "").strip()
            if language_key and cleaned:
                normalized[language_key] = cleaned
        return normalized

    if isinstance(value, list):
        joined = " ".join(str(item).strip() for item in value if str(item).strip())
        return _wrap_multilingual_text(joined)

    if value is None:
        return {}

    return _wrap_multilingual_text(str(value))


def _merge_structured_sections(
    fallback: dict, overrides: dict | None, *, translator=None
) -> dict:
    overrides = overrides or {}
    if not isinstance(overrides, dict):
        overrides = {}

    merged: dict[str, dict[str, str]] = {}
    for key in ("graphs", "conditions", "results", "comments"):
        base = _normalize_structured_section_value(fallback.get(key))
        override_value = _normalize_structured_section_value(overrides.get(key))
        combined: dict[str, str] = {}
        combined.update(base)
        combined.update(override_value)
        combined = {
            str(language).strip().lower(): str(text or "").strip()
            for language, text in combined.items()
            if str(language).strip() and str(text or "").strip()
        }
        if combined:
            merged[key] = _ensure_multilingual_entries(combined, translator=translator)
    return merged


def _merge_highlights(fallback: list[str], overrides: list[str] | None) -> list[str]:
    base = [item for item in fallback if item]
    if not isinstance(overrides, list):
        return base

    for item in overrides:
        text = str(item).strip()
        if text and text not in base:
            base.append(text)
    return base[:5]


def _split_into_sentences(text: str) -> list[str]:
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [sentence.strip() for sentence in sentences if sentence and sentence.strip()]


def _extract_keyword_sentences(text: str, keywords: tuple[str, ...], limit: int = 3) -> str:
    sentences = _split_into_sentences(text)
    matches: list[str] = []
    lowered = [keyword.lower() for keyword in keywords]
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in lowered):
            matches.append(sentence)
        if len(matches) >= limit:
            break
    return " ".join(matches)


def _build_structured_sections_from_text(
    text: str,
    total_tests: int,
    passed_tests: int,
    failed_tests: int,
    failure_details: list[dict],
    report_type_label: str,
) -> dict:
    graphs = _extract_keyword_sentences(
        text,
        ("graph", "grafik", "figure", "chart", "spektrum", "spectrum", "plot"),
    )
    conditions = _extract_keyword_sentences(
        text,
        ("condition", "koşul", "ambient", "environment", "temperature", "setup", "montaj"),
    )
    comments = _extract_keyword_sentences(
        text,
        ("comment", "yorum", "assessment", "değerl", "note", "gözlem"),
    )

    if graphs:
        graphs_value = _wrap_multilingual_text(graphs)
    else:
        graphs_value = {
            "tr": (
                "Rapor metninde grafiklere dair belirgin bir açıklama bulunamadı; PDF içeriği manuel olarak incelenmeli."
            ),
            "en": (
                "No specific chart description was found in the report; the PDF should be reviewed manually."
            ),
            "de": (
                "Im Berichtstext wurde keine eindeutige Beschreibung der Grafiken gefunden; bitte das PDF manuell prüfen."
            ),
        }

    if conditions:
        conditions_value = _wrap_multilingual_text(conditions)
    else:
        conditions_value = {
            "tr": (
                "Test koşulları bölümü metinde sınırlı yer alıyor. {report_type} için standart prosedürler esas alınmalıdır."
            ).format(report_type=report_type_label),
            "en": (
                "The section describing the test conditions is limited in the text. Standard procedures for {report_type} should be followed."
            ).format(report_type=report_type_label),
            "de": (
                "Der Abschnitt zu den Testbedingungen ist im Text nur begrenzt vorhanden. Es sollten die Standardverfahren für {report_type} beachtet werden."
            ).format(report_type=report_type_label),
        }
    success_rate = (passed_tests / total_tests * 100.0) if total_tests else 0.0
    results_tr = (
        f"Toplam {total_tests} testin {passed_tests}'i başarılı, {failed_tests}'i başarısız. "
        f"Başarı oranı %{success_rate:.1f}."
    )
    results_en = (
        f"{total_tests} tests in total: {passed_tests} passed, {failed_tests} failed. "
        f"Success rate {success_rate:.1f}%."
    )
    results_de = (
        f"Insgesamt {total_tests} Tests: {passed_tests} bestanden, {failed_tests} nicht bestanden. "
        f"Erfolgsquote {success_rate:.1f}%."
    )
    if failure_details:
        first_failure = failure_details[0]
        failure_reason = first_failure.get("failure_reason") or first_failure.get("error_message") or ""
        if failure_reason:
            highlight = first_failure.get("test_name", "Bilinmeyen Test")
            results_tr += f" Öne çıkan başarısızlık: {highlight} - {failure_reason}."
            results_en += f" Highlighted failure: {highlight} - {failure_reason}."
            results_de += f" Hervorgehobener Fehler: {highlight} - {failure_reason}."

    if comments:
        comments_value = _wrap_multilingual_text(comments)
    else:
        comments_value = {
            "tr": "Rapor genelinde ek yorum veya uzman görüşü bulunamadı; değerlendiricinin notları sınırlı.",
            "en": "No additional comments or expert opinions were found in the report; reviewer notes are limited.",
            "de": "Im Bericht wurden keine zusätzlichen Kommentare oder Expertenmeinungen gefunden; die Gutachternotizen sind begrenzt.",
        }

    return {
        "graphs": graphs_value,
        "conditions": conditions_value,
        "results": {"tr": results_tr, "en": results_en, "de": results_de},
        "comments": comments_value,
    }


def _build_highlights_from_data(
    total_tests: int,
    passed_tests: int,
    failed_tests: int,
    failure_details: list[dict],
    report_type_label: str,
) -> list[str]:
    highlights = [
        f"{report_type_label} kapsamında {total_tests} test incelendi.",
        f"Başarı/başarısızlık dağılımı: {passed_tests} PASS / {failed_tests} FAIL.",
    ]
    for failure in failure_details[:3]:
        reason = failure.get("failure_reason") or failure.get("error_message") or ""
        if reason:
            highlights.append(
                f"{failure.get('test_name', 'Bilinmeyen Test')}: {reason}"
            )
    return highlights


def _normalize_test_name_for_key(name: str | None) -> str:
    return re.sub(r"\s+", " ", (name or "").strip()).lower()


def _compose_result_detail(result: dict | None) -> str:
    if not result:
        return ""
    for key in ("failure_reason", "error_message", "suggested_fix"):
        value = (result.get(key) or "").strip()
        if value:
            return value
    return ""


def _collect_test_differences(
    first_results: list[dict],
    second_results: list[dict],
) -> list[dict]:
    first_map = {
        _normalize_test_name_for_key(result.get("test_name")): result for result in first_results
    }
    second_map = {
        _normalize_test_name_for_key(result.get("test_name")): result for result in second_results
    }

    differences: list[dict] = []
    all_keys = set(first_map) | set(second_map)
    for key in sorted(all_keys):
        first_result = first_map.get(key)
        second_result = second_map.get(key)
        first_status = (first_result.get("status") if first_result else "MISSING") or "MISSING"
        second_status = (second_result.get("status") if second_result else "MISSING") or "MISSING"

        if first_status == second_status and first_status != "MISSING":
            continue

        differences.append(
            {
                "test_name": first_result.get("test_name")
                if first_result and first_result.get("test_name")
                else (second_result.get("test_name") if second_result else "Bilinmeyen Test"),
                "first_status": first_status.upper(),
                "second_status": second_status.upper(),
                "first_detail": _compose_result_detail(first_result),
                "second_detail": _compose_result_detail(second_result),
            }
        )

    return differences


_STATUS_LABELS = {
    "tr": {"PASS": "test başarılı", "FAIL": "test başarısız", "MISSING": "raporda yer almıyor"},
    "en": {"PASS": "test passed", "FAIL": "test failed", "MISSING": "not present"},
    "de": {"PASS": "Test bestanden", "FAIL": "Test nicht bestanden", "MISSING": "nicht enthalten"},
}


def _format_difference_sentence(language: str, difference: dict) -> str:
    labels = _STATUS_LABELS.get(language, _STATUS_LABELS["tr"])
    test_name = difference.get("test_name") or "Test"
    first_status = labels.get(difference.get("first_status", "").upper(), labels["MISSING"])
    second_status = labels.get(difference.get("second_status", "").upper(), labels["MISSING"])
    first_detail = difference.get("first_detail") or ""
    second_detail = difference.get("second_detail") or ""

    first_sentence = first_status
    if first_detail:
        first_sentence += f" ({first_detail})"
    second_sentence = second_status
    if second_detail:
        second_sentence += f" ({second_detail})"

    if language == "en":
        template = (
            f"In the {test_name} test, the first report is {first_sentence}, while the second report is {second_sentence}."
        )
    elif language == "de":
        template = (
            f"Beim Test {test_name} ist der erste Bericht {first_sentence}, der zweite Bericht hingegen {second_sentence}."
        )
    else:
        template = (
            f"{test_name} testinde ilk rapor {first_sentence}, ikinci rapor ise {second_sentence}."
        )

    return template


def _build_localized_comparison_summary(
    first_report_label: str,
    second_report_label: str,
    differences: list[dict],
) -> dict:
    summaries = {}
    difference_count = len(differences)

    for language in ("tr", "en", "de"):
        labels = dict(COMPARISON_LABELS.get(language, {}))

        if difference_count == 0:
            overview = COMPARISON_ZERO_OVERVIEW.get(language, "")
            sentences: list[str] = []
        else:
            sentences = [_format_difference_sentence(language, diff) for diff in differences]
            if language == "en":
                overview = (
                    f"{difference_count} test differs between {first_report_label} and {second_report_label}."
                )
            elif language == "de":
                overview = (
                    f"Zwischen {first_report_label} und {second_report_label} unterscheiden sich {difference_count} Tests."
                )
            else:
                overview = (
                    f"{first_report_label} ile {second_report_label} arasında {difference_count} test sonucunda farklılık var."
                )

        entry = {"overview": overview, "details": sentences, "labels": labels}
        if not sentences:
            entry["empty_details"] = COMPARISON_EMPTY_DETAILS.get(language, "")

        summaries[language] = entry

    return summaries


def _build_multilingual_summary(
    engine_label: str,
    filename: str,
    report_type_label: str,
    total_tests: int,
    passed_tests: int,
    failed_tests: int,
    failure_details,
):
    total = int(total_tests or 0)
    passed = int(passed_tests or 0)
    failed = int(failed_tests or 0)
    success_rate = (passed / total * 100.0) if total else 0.0
    alignment_key = _derive_alignment_key(total, passed, failed)

    summaries = {}
    for language, config in LANGUAGE_TEMPLATES.items():
        labels = dict(config.get("labels", {}))
        if total == 0:
            summary_text = config["no_tests"].format(
                engine=engine_label,
                filename=filename,
                report_type=report_type_label,
            )
            conditions_text = config["no_tests_conditions"]
            improvements_text = config["no_tests_improvements"]
        else:
            summary_text = config["summary"].format(
                engine=engine_label,
                filename=filename,
                report_type=report_type_label,
                total=total,
                passed=passed,
                failed=failed,
                success_rate=f"{success_rate:.1f}",
            )
            alignment_word = config["alignment_words"].get(
                alignment_key, config["alignment_words"]["unknown"]
            )
            conditions_text = config["conditions"].format(alignment=alignment_word)

            if failure_details:
                improvement_lines = []
                for detail in failure_details:
                    test_name = detail.get("test_name") or config["unknown_test_name"]
                    suggested_fix = (detail.get("suggested_fix") or "").strip()
                    failure_reason = (detail.get("failure_reason") or "").strip()
                    if not failure_reason:
                        failure_reason = config["default_reason"]
                    if suggested_fix:
                        improvement_lines.append(
                            config["failure_with_fix"].format(
                                test=test_name,
                                fix=suggested_fix,
                                reason=failure_reason,
                            )
                        )
                    else:
                        improvement_lines.append(
                            config["failure_without_fix"].format(
                                test=test_name,
                                reason=failure_reason,
                            )
                        )
                improvements_text = (
                    config["improvements_intro"] + " " + " ".join(improvement_lines)
                )
            else:
                improvements_text = config["improvements_success"]

        summaries[language] = {
            "summary": summary_text,
            "conditions": conditions_text,
            "improvements": improvements_text,
            "labels": labels,
        }

    return summaries


@reports_bp.route("/upload", methods=["POST"])
def upload_report():
    if "file" not in request.files:
        return _json_error("No file part in the request.", 400)

    file = request.files["file"]
    if file.filename == "":
        return _json_error("No selected file.", 400)

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file.filename)
    saved_path = upload_folder / filename
    counter = 1
    while saved_path.exists():
        saved_path = upload_folder / f"{saved_path.stem}_{counter}{saved_path.suffix or '.pdf'}"
        counter += 1

    file.save(saved_path)

    try:
        logger.info(f"=== PDF ANALİZ BAŞLADI: {filename} ===")
        logger.info("Step 1: Text extraction")
        extraction_result = extract_text_from_pdf(saved_path)
        logger.info(
            "Text uzunluğu: %s",
            len((extraction_result.get("text") or "")),
        )
        logger.info(
            "Structured text uzunluğu: %s",
            len((extraction_result.get("structured_text") or "")),
        )
        logger.info(
            "Tablo sayısı: %s",
            len(extraction_result.get("tables") or []),
        )

        logger.info("Step 2: Comprehensive analysis")
        analysis_result = analyze_pdf_comprehensive(saved_path)
        logger.info("AI analizi tamamlandı")

        raw_text = analysis_result.pop("raw_text", "") or ""
        sections = analysis_result.get("sections", {}) or {}
        text_length = analysis_result.get("metadata", {}).get("text_length") or len(raw_text)
        logger.info(f"Text uzunluğu: {text_length} karakter")
        for section_name, section_content in sections.items():
            section_len = len(section_content or "")
            logger.info(f"Bölüm [{section_name}]: {section_len} karakter")

        basic_stats = analysis_result.get("basic_stats", {})
        parsed_results = basic_stats.get("tests", [])
        logger.info(f"Bulunan test sayısı: {len(parsed_results)}")
        if len(parsed_results) == 0:
            logger.warning(f"UYARI: PDF'de hiç test bulunamadı! Dosya: {filename}")
            preview = (raw_text or "")[:500]
            if preview:
                logger.debug(f"İlk 500 karakter: {preview}")

        combined_text_for_type = raw_text or "\n".join(
            value for value in sections.values() if isinstance(value, str)
        )
        report_type_key, report_type_label = infer_report_type(combined_text_for_type, filename)
        logger.info("Step 3: Database save hazırlığı")
    except AttributeError as exc:  # pragma: no cover - defensive
        saved_path.unlink(missing_ok=True)
        logger.error(f"AttributeError: {exc}", exc_info=True)
        if "splitlines" in str(exc):
            return (
                jsonify(
                    {
                        "error": "PDF parse hatası: Veri formatı uyumsuzluğu",
                        "detail": "extract_text_from_pdf dict döndürüyor ama kod string bekliyor",
                        "hint": "pdf_analyzer.py dosyasındaki fonksiyonları kontrol edin",
                    }
                ),
                500,
            )
        raise
    except Exception as exc:  # pragma: no cover - defensive
        saved_path.unlink(missing_ok=True)
        logger.error(f"PDF analiz hatası: {exc}", exc_info=True)
        return (
            jsonify(
                {
                    "error": "PDF analizi başarısız oldu",
                    "detail": str(exc),
                }
            ),
            500,
        )

    comprehensive_analysis = analysis_result.get("comprehensive_analysis", {})
    logger.info("Kapsamlı analiz database'e kaydediliyor...")
    logger.info(
        "  Test Koşulları: %s karakter",
        len((comprehensive_analysis.get("test_conditions") or "")),
    )
    logger.info(
        "  Grafikler: %s karakter",
        len((comprehensive_analysis.get("graphs") or "")),
    )
    logger.info(
        "  Sonuçlar: %s karakter",
        len((comprehensive_analysis.get("results") or "")),
    )

    report_id = database.insert_report(
        filename,
        str(saved_path),
        report_type_key,
        comprehensive_analysis,
    )

    total_tests = basic_stats.get("total_tests", 0)
    passed_tests = basic_stats.get("passed", 0)
    failed_tests = basic_stats.get("failed", 0)

    for result in parsed_results:
        database.insert_test_result(
            report_id,
            result.get("test_name", "Unknown Test"),
            result.get("status", "PASS"),
            result.get("error_message", ""),
            result.get("failure_reason"),
            result.get("suggested_fix"),
            result.get("ai_provider", "rule-based"),
        )

    database.update_report_stats(report_id, total_tests, passed_tests, failed_tests)
    database.update_report_comprehensive_analysis(
        report_id,
        comprehensive_analysis,
        structured_data=analysis_result.get("structured_data"),
        tables=analysis_result.get("tables"),
    )
    logger.info("Database kayıt tamamlandı")

    report = database.get_report_by_id(report_id)
    if report is not None:
        report["test_type_label"] = report_type_label

    logger.info(f"=== PDF ANALİZ BİTTİ: {filename} ===")

    return (
        jsonify(
            {
                "report": report,
                "totals": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                },
                "comprehensive_analysis": comprehensive_analysis,
            }
        ),
        201,
    )


@reports_bp.route("/reports", methods=["GET"])
def list_reports():
    sort_by = request.args.get("sortBy", "date")
    order = request.args.get("order", "desc")
    reports = database.get_all_reports(sort_by=sort_by, order=order)
    for report in reports:
        report["test_type_label"] = _resolve_report_type_label(report.get("test_type"))
    return jsonify({"reports": reports})


@reports_bp.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id: int):
    """Rapor detayını getir"""

    import logging

    logger = logging.getLogger(__name__)

    try:
        report = database.get_report_by_id(report_id)

        if not report:
            return _json_error("Report not found.", 404)

        tests = database.get_test_results(report_id) or []

        detailed_analysis = {
            "test_conditions": report.get("test_conditions_summary", ""),
            "graphs": report.get("graphs_description", ""),
            "results": report.get("detailed_results", ""),
            "improvements": report.get("improvement_suggestions", ""),
        }

        logger.info("Rapor %s getiriliyor:", report_id)
        logger.info("  Test conditions: %s karakter", len(detailed_analysis["test_conditions"]))
        logger.info("  Graphs: %s karakter", len(detailed_analysis["graphs"]))

        response = {
            "report": {
                "id": report.get("id"),
                "filename": report.get("filename"),
                "upload_date": report.get("upload_date"),
                "total_tests": report.get("total_tests", 0),
                "passed_tests": report.get("passed_tests", 0),
                "failed_tests": report.get("failed_tests", 0),
                "tests": tests,
            },
            "detailed_analysis": detailed_analysis,
        }

        return jsonify(response)

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Rapor getirme hatası: %s", exc, exc_info=True)
        return _json_error(str(exc), 500)


@reports_bp.route("/reports/<int:report_id>/detailed", methods=["GET"])
def get_detailed_report(report_id: int):
    """Return the comprehensive AI-backed analysis for a report."""

    report = database.get_report_by_id(report_id)
    if not report:
        return _json_error("Report not found.", 404)

    detailed_analysis = {
        "test_conditions": (report.get("test_conditions_summary") or ""),
        "graphs": (report.get("graphs_description") or ""),
        "results": (report.get("detailed_results") or ""),
        "improvements": (report.get("improvement_suggestions") or ""),
        "analysis_language": report.get("analysis_language", "tr"),
    }

    return jsonify(
        {
            "report_id": report_id,
            "filename": report.get("filename"),
            "upload_date": report.get("upload_date"),
            "basic_stats": {
                "total": report.get("total_tests", 0),
                "passed": report.get("passed_tests", 0),
                "failed": report.get("failed_tests", 0),
            },
            "detailed_analysis": detailed_analysis,
            "structured_data": report.get("structured_data"),
            "table_count": report.get("table_count", 0),
        }
    )


@reports_bp.route("/reports/<int:report_id>/download", methods=["GET"])
def download_report_file(report_id: int):
    report = database.get_report_by_id(report_id)
    if not report:
        return _json_error("Report not found.", 404)

    pdf_path = Path(report.get("pdf_path") or "")
    if not pdf_path.exists():
        return _json_error("PDF file is not available on the server.", 404)

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=report.get("filename") or pdf_path.name,
    )


@reports_bp.route("/reports/compare", methods=["POST"])
def compare_reports():
    payload = request.get_json(silent=True) or {}
    report_ids = payload.get("report_ids")

    if not isinstance(report_ids, list):
        return _json_error("Karşılaştırma için rapor kimliklerini içeren bir liste gönderin.", 400)

    if len(report_ids) != 2:
        return _json_error("Karşılaştırma işlemi için tam olarak iki rapor seçmelisiniz.", 400)

    try:
        first_id, second_id = (int(report_ids[0]), int(report_ids[1]))
    except (TypeError, ValueError):
        return _json_error("Geçersiz rapor kimliği gönderildi.", 400)

    if first_id == second_id:
        return _json_error("Karşılaştırma için farklı iki rapor seçmelisiniz.", 400)

    first_report = database.get_report_by_id(first_id)
    second_report = database.get_report_by_id(second_id)

    if not first_report or not second_report:
        return _json_error("Seçilen raporlardan biri bulunamadı.", 404)

    first_path = Path(first_report.get("pdf_path") or "")
    second_path = Path(second_report.get("pdf_path") or "")

    if not first_path.exists() or not second_path.exists():
        return _json_error("Karşılaştırma için PDF dosyalarından biri bulunamadı.", 404)

    try:
        first_extraction = extract_text_from_pdf(first_path)
        second_extraction = extract_text_from_pdf(second_path)
        first_text = (
            first_extraction.get("structured_text")
            or first_extraction.get("text")
            or ""
        )
        second_text = (
            second_extraction.get("structured_text")
            or second_extraction.get("text")
            or ""
        )
    except FileNotFoundError:
        return _json_error("Karşılaştırma için PDF dosyalarından biri bulunamadı.", 404)
    except Exception as exc:  # pragma: no cover - defensive
        return _json_error(f"PDF karşılaştırması yapılamadı: {exc}", 500)

    first_results = database.get_test_results(first_id)
    second_results = database.get_test_results(second_id)
    structured_differences = _collect_test_differences(first_results, second_results)
    localized_difference_summary = _build_localized_comparison_summary(
        first_report.get("filename") or f"report-{first_id}.pdf",
        second_report.get("filename") or f"report-{second_id}.pdf",
        structured_differences,
    )

    similarity_ratio = difflib.SequenceMatcher(None, first_text, second_text).ratio() * 100.0

    def _normalise_lines(raw_text: str):
        return [line.strip() for line in raw_text.splitlines() if line and line.strip()]

    first_lines = _normalise_lines(first_text)
    second_lines = _normalise_lines(second_text)

    def _collect_unique(source_lines, target_lines):
        target_set = set(target_lines)
        uniques = []
        seen = set()
        for line in source_lines:
            if line in target_set or line in seen or len(line) < 4:
                continue
            uniques.append(line)
            seen.add(line)
            if len(uniques) >= 5:
                break
        return uniques

    unique_first = _collect_unique(first_lines, second_lines)
    unique_second = _collect_unique(second_lines, first_lines)

    diff_lines = list(
        difflib.unified_diff(
            first_text.splitlines(),
            second_text.splitlines(),
            fromfile=first_report.get("filename") or f"report-{first_id}.pdf",
            tofile=second_report.get("filename") or f"report-{second_id}.pdf",
            lineterm="",
        )
    )

    max_diff_lines = 120
    if len(diff_lines) > max_diff_lines:
        remaining = len(diff_lines) - max_diff_lines
        diff_lines = diff_lines[:max_diff_lines]
        diff_lines.append(f"... ({remaining} satır daha)")

    if similarity_ratio >= 85:
        verdict = "Raporlar büyük ölçüde aynı içerikte."
    elif similarity_ratio >= 60:
        verdict = "Raporlar benzer ancak dikkate değer farklılıklar mevcut."
    else:
        verdict = "Raporlar arasında belirgin içerik farkı var."

    if structured_differences:
        verdict += f" Karşılaştırmada {len(structured_differences)} test sonucunda ayrışma bulundu."
    else:
        verdict += " Test sonuçları arasında fark tespit edilmedi."

    response_payload = {
        "summary": (
            f"{first_report.get('filename')} ile {second_report.get('filename')} arasındaki benzerlik oranı "
            f"%{similarity_ratio:.1f}. {verdict}"
        ),
        "similarity": round(similarity_ratio, 2),
        "first_report": {
            "id": first_id,
            "filename": first_report.get("filename"),
            "upload_date": first_report.get("upload_date"),
            "test_type": _resolve_report_type_label(first_report.get("test_type")),
        },
        "second_report": {
            "id": second_id,
            "filename": second_report.get("filename"),
            "upload_date": second_report.get("upload_date"),
            "test_type": _resolve_report_type_label(second_report.get("test_type")),
        },
        "difference_highlights": diff_lines,
        "unique_to_first": unique_first,
        "unique_to_second": unique_second,
        "test_differences": structured_differences,
        "difference_summary": localized_difference_summary,
    }

    return jsonify(response_payload)


@reports_bp.route("/reports/<int:report_id>/tables", methods=["GET"])
def get_report_tables(report_id: int):
    report = database.get_report_by_id(report_id)
    if not report:
        return _json_error("Report not found.", 404)

    pdf_path = Path(report.get("pdf_path") or "")
    if not pdf_path.exists():
        return _json_error("PDF file is not available on the server.", 404)

    try:
        extraction = extract_text_from_pdf(pdf_path)
    except Exception as exc:  # pragma: no cover - defensive
        return _json_error(f"Tablo verileri alınamadı: {exc}", 500)

    tables = extraction.get("tables") or []

    return jsonify(
        {
            "report_id": report_id,
            "table_count": len(tables),
            "tables": tables,
        }
    )


@reports_bp.route("/reports/<int:report_id>/failures", methods=["GET"])
def get_failures(report_id: int):
    report = database.get_report_by_id(report_id)
    if not report:
        return _json_error("Report not found.", 404)

    failures = database.get_failed_tests(report_id)
    return jsonify({"report": report, "failures": failures})


@reports_bp.route("/reports/<int:report_id>", methods=["DELETE"])
def delete_report(report_id: int):
    pdf_path = database.delete_report(report_id)
    if pdf_path is None:
        return _json_error("Report not found.", 404)

    try:
        Path(pdf_path).unlink(missing_ok=True)
    except OSError:
        pass

    return jsonify({"message": "Report deleted successfully."})


@reports_bp.route("/ai-status", methods=["GET"])
def get_ai_status():
    """AI provider durumunu döndür."""
    provider = (os.getenv("AI_PROVIDER", "none") or "none").strip().lower()
    if provider not in {"claude", "chatgpt", "both", "none"}:
        provider = "none"
    anthropic_key = (os.getenv("ANTHROPIC_API_KEY", "") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY", "") or "").strip()

    claude_available = bool(anthropic_key)
    chatgpt_available = bool(openai_key)

    active = False
    if provider == "claude":
        active = claude_available
    elif provider == "chatgpt":
        active = chatgpt_available
    elif provider == "both":
        active = claude_available or chatgpt_available

    status = "active" if active else "inactive"

    return jsonify(
        {
            "provider": provider or "none",
            "claude_available": claude_available,
            "chatgpt_available": chatgpt_available,
            "status": status,
        }
    )


@reports_bp.route("/reset", methods=["POST"])
def reset_all_data():
    """Delete all stored reports, analyses and uploaded PDF files."""

    pdf_paths = database.clear_all_data()
    removed_files = 0

    for pdf_path in pdf_paths:
        try:
            Path(pdf_path).unlink(missing_ok=True)
            removed_files += 1
        except OSError:
            pass

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    if upload_folder.exists():
        for orphan in upload_folder.glob("**/*"):
            if orphan.is_file():
                try:
                    orphan.unlink(missing_ok=True)
                except OSError:
                    pass

    return jsonify(
        {
            "message": "Tüm raporlar ve test sonuçları sıfırlandı.",
            "deleted_reports": len(pdf_paths),
            "deleted_files": removed_files,
        }
    )


@reports_bp.route("/analyze-files", methods=["POST"])
def analyze_files_with_ai():
    """Analyse uploaded PDF files and return AI flavoured summaries."""

    files = request.files.getlist("files")
    if not files:
        return _json_error("Analiz için en az bir PDF dosyası gönderin.", 400)

    engine = (request.form.get("engine") or "chatgpt").strip().lower()
    engine_label = "Claude" if engine == "claude" else "ChatGPT"

    summaries = []
    processed_files = 0

    for storage in files:
        if not storage or storage.filename == "":
            continue

        filename = storage.filename
        if not filename.lower().endswith(".pdf"):
            continue

        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            storage.save(temp_file.name)
            temp_path = Path(temp_file.name)

        try:
            extraction = extract_text_from_pdf(temp_path)
            raw_text = (
                extraction.get("structured_text")
                if isinstance(extraction, dict)
                else ""
            ) or (
                extraction.get("text")
                if isinstance(extraction, dict)
                else str(extraction)
            )
            raw_text = str(raw_text or "")
            parsed_results = parse_test_results(extraction)
        except Exception as exc:  # pragma: no cover - defensive logging
            temp_path.unlink(missing_ok=True)
            return _json_error(f"PDF analizi başarısız oldu: {exc}", 500)
        finally:
            temp_path.unlink(missing_ok=True)

        report_type_key, report_type_label = infer_report_type(raw_text, filename)
        processed_files += 1
        total_tests = len(parsed_results)
        passed_tests = sum(1 for result in parsed_results if result.get("status") == "PASS")
        failed_tests = total_tests - passed_tests
        alignment_key = _derive_alignment_key(total_tests, passed_tests, failed_tests)
        success_rate = (passed_tests / total_tests * 100.0) if total_tests else 0.0
        success_rate = round(success_rate, 2)

        failure_details = [
            {
                "test_name": result.get("test_name", "Bilinmeyen Test"),
                "failure_reason": result.get("failure_reason", ""),
                "suggested_fix": result.get("suggested_fix", ""),
            }
            for result in parsed_results
            if result.get("status") == "FAIL"
        ]

        fallback_localized = _build_multilingual_summary(
            engine_label,
            filename,
            report_type_label,
            total_tests,
            passed_tests,
            failed_tests,
            failure_details,
        )

        ai_summary_payload = ai_analyzer.generate_report_summary(
            filename=filename,
            report_type=report_type_label,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            raw_text=raw_text,
            failure_details=failure_details,
        )

        localized_summaries = _merge_localized_summaries(
            fallback_localized,
            (ai_summary_payload or {}).get("localized_summaries") if ai_summary_payload else None,
            translator=ai_analyzer,
        )

        fallback_sections = _build_structured_sections_from_text(
            raw_text,
            total_tests,
            passed_tests,
            failed_tests,
            failure_details,
            report_type_label,
        )
        structured_sections = _merge_structured_sections(
            fallback_sections,
            (ai_summary_payload or {}).get("sections") if ai_summary_payload else None,
            translator=ai_analyzer,
        )

        fallback_highlights = _build_highlights_from_data(
            total_tests,
            passed_tests,
            failed_tests,
            failure_details,
            report_type_label,
        )
        analysis_highlights = _merge_highlights(
            fallback_highlights,
            (ai_summary_payload or {}).get("highlights") if ai_summary_payload else None,
        )

        base_summary = localized_summaries["tr"]["summary"]
        conditions_text = localized_summaries["tr"].get("conditions", "")
        improvements_text = localized_summaries["tr"].get("improvements", "")

        summaries.append(
            {
                "filename": filename,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "engine": engine_label,
                "summary": base_summary,
                "condition_evaluation": conditions_text,
                "improvement_overview": improvements_text,
                "localized_summaries": localized_summaries,
                "report_type": report_type_key,
                "report_type_label": report_type_label,
                "alignment": alignment_key,
                "success_rate": success_rate,
                "failures": failure_details,
                "structured_sections": structured_sections,
                "highlights": analysis_highlights,
            }
        )

    if processed_files == 0:
        return _json_error("Analiz için geçerli PDF dosyası bulunamadı.", 400)

    return jsonify(
        {
            "engine": engine_label,
            "summaries": summaries,
            "message": (
                f"{processed_files} dosya {engine_label} ile analiz edildi. "
                "Türkçe, İngilizce ve Almanca özetler hazırlandı."
            ),
        }
    )
