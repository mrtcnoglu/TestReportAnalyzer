"""Flask routes for the TestReportAnalyzer backend."""
from __future__ import annotations

import os
import difflib
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.utils import secure_filename

try:  # pragma: no cover - import flexibility
    from . import database
    from .pdf_analyzer import (
        REPORT_TYPE_LABELS,
        extract_text_from_pdf,
        infer_report_type,
        parse_test_results,
    )
except ImportError:  # pragma: no cover
    import database  # type: ignore
    from pdf_analyzer import (  # type: ignore
        REPORT_TYPE_LABELS,
        extract_text_from_pdf,
        infer_report_type,
        parse_test_results,
    )

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
    },
}


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
        text = extract_text_from_pdf(saved_path)
        parsed_results = parse_test_results(text)
        report_type_key, report_type_label = infer_report_type(text, filename)
    except Exception as exc:  # pragma: no cover - defensive
        saved_path.unlink(missing_ok=True)
        return _json_error(f"Failed to analyse PDF: {exc}", 500)

    report_id = database.insert_report(filename, str(saved_path), report_type_key)

    total_tests = len(parsed_results)
    passed_tests = sum(1 for result in parsed_results if result["status"] == "PASS")
    failed_tests = total_tests - passed_tests

    for result in parsed_results:
        database.insert_test_result(
            report_id,
            result["test_name"],
            result["status"],
            result.get("error_message", ""),
            result.get("failure_reason"),
            result.get("suggested_fix"),
            result.get("ai_provider", "rule-based"),
        )

    database.update_report_stats(report_id, total_tests, passed_tests, failed_tests)

    report = database.get_report_by_id(report_id)
    if report is not None:
        report["test_type_label"] = report_type_label

    return (
        jsonify(
            {
                "report": report,
                "totals": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                },
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
    report = database.get_report_by_id(report_id)
    if not report:
        return _json_error("Report not found.", 404)

    results = database.get_test_results(report_id)
    report["test_type_label"] = _resolve_report_type_label(report.get("test_type"))
    return jsonify({"report": report, "results": results})


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
        first_text = extract_text_from_pdf(first_path)
        second_text = extract_text_from_pdf(second_path)
    except FileNotFoundError:
        return _json_error("Karşılaştırma için PDF dosyalarından biri bulunamadı.", 404)
    except Exception as exc:  # pragma: no cover - defensive
        return _json_error(f"PDF karşılaştırması yapılamadı: {exc}", 500)

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
    }

    return jsonify(response_payload)


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
            text = extract_text_from_pdf(temp_path)
            parsed_results = parse_test_results(text)
        except Exception as exc:  # pragma: no cover - defensive logging
            temp_path.unlink(missing_ok=True)
            return _json_error(f"PDF analizi başarısız oldu: {exc}", 500)
        finally:
            temp_path.unlink(missing_ok=True)

        report_type_key, report_type_label = infer_report_type(text, filename)
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

        localized_summaries = _build_multilingual_summary(
            engine_label,
            filename,
            report_type_label,
            total_tests,
            passed_tests,
            failed_tests,
            failure_details,
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
