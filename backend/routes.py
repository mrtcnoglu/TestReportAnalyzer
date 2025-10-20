"""Flask routes for the TestReportAnalyzer backend."""
from __future__ import annotations

import os
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

try:  # pragma: no cover - import flexibility
    from . import database
    from .pdf_analyzer import extract_text_from_pdf, parse_test_results
except ImportError:  # pragma: no cover
    import database  # type: ignore
    from pdf_analyzer import extract_text_from_pdf, parse_test_results  # type: ignore

reports_bp = Blueprint("reports", __name__)


def _json_error(message: str, status_code: int = 400):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


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
    except Exception as exc:  # pragma: no cover - defensive
        saved_path.unlink(missing_ok=True)
        return _json_error(f"Failed to analyse PDF: {exc}", 500)

    report_id = database.insert_report(filename, str(saved_path))

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
    return jsonify({"report": report, "totals": {"total": total_tests, "passed": passed_tests, "failed": failed_tests}}), 201


@reports_bp.route("/reports", methods=["GET"])
def list_reports():
    sort_by = request.args.get("sortBy", "date")
    order = request.args.get("order", "desc")
    reports = database.get_all_reports(sort_by=sort_by, order=order)
    return jsonify({"reports": reports})


@reports_bp.route("/reports/<int:report_id>", methods=["GET"])
def get_report(report_id: int):
    report = database.get_report_by_id(report_id)
    if not report:
        return _json_error("Report not found.", 404)

    results = database.get_test_results(report_id)
    return jsonify({"report": report, "results": results})


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
