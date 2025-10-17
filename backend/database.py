"""Database utilities for the TestReportAnalyzer backend."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
SCHEMA_PATH = BASE_DIR / "models" / "schema.sql"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db_connection() -> sqlite3.Connection:
    """Return a new SQLite connection to the application database."""
    return _connect()


def init_db() -> None:
    """Initialise the database using the schema file if necessary."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect()) as conn:
        with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())
        conn.commit()


def insert_report(filename: str, pdf_path: str) -> int:
    """Insert a new report record and return its ID."""
    with closing(_connect()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (filename, pdf_path)
            VALUES (?, ?)
            """,
            (filename, pdf_path),
        )
        conn.commit()
        return int(cursor.lastrowid)


def update_report_stats(report_id: int, total: int, passed: int, failed: int) -> None:
    """Update aggregate statistics for a report."""
    with closing(_connect()) as conn:
        conn.execute(
            """
            UPDATE reports
            SET total_tests = ?, passed_tests = ?, failed_tests = ?
            WHERE id = ?
            """,
            (total, passed, failed, report_id),
        )
        conn.commit()


def insert_test_result(
    report_id: int,
    test_name: str,
    status: str,
    error_message: Optional[str],
    reason: Optional[str],
    fix: Optional[str],
) -> None:
    """Insert a single test result entry."""
    with closing(_connect()) as conn:
        conn.execute(
            """
            INSERT INTO test_results (report_id, test_name, status, error_message, failure_reason, suggested_fix)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (report_id, test_name, status, error_message, reason, fix),
        )
        conn.commit()


def get_all_reports(sort_by: str = "date", order: str = "desc") -> List[Dict]:
    """Return all reports ordered by the requested column."""
    column_map = {
        "date": "upload_date",
        "name": "filename",
        "total": "total_tests",
        "passed": "passed_tests",
        "failed": "failed_tests",
    }
    column = column_map.get(sort_by.lower(), "upload_date")
    direction = "ASC" if order.lower() == "asc" else "DESC"

    with closing(_connect()) as conn:
        cursor = conn.execute(
            f"""
            SELECT id, filename, upload_date, total_tests, passed_tests, failed_tests
            FROM reports
            ORDER BY {column} {direction}
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_report_by_id(report_id: int) -> Optional[Dict]:
    """Return a single report with aggregated statistics."""
    with closing(_connect()) as conn:
        cursor = conn.execute(
            """
            SELECT id, filename, upload_date, total_tests, passed_tests, failed_tests, pdf_path
            FROM reports
            WHERE id = ?
            """,
            (report_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_failed_tests(report_id: int) -> List[Dict]:
    """Return all failed tests for a given report."""
    with closing(_connect()) as conn:
        cursor = conn.execute(
            """
            SELECT id, test_name, status, error_message, failure_reason, suggested_fix
            FROM test_results
            WHERE report_id = ? AND status = 'FAIL'
            ORDER BY id ASC
            """,
            (report_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_test_results(report_id: int) -> List[Dict]:
    """Return all test results for a report."""
    with closing(_connect()) as conn:
        cursor = conn.execute(
            """
            SELECT id, test_name, status, error_message, failure_reason, suggested_fix
            FROM test_results
            WHERE report_id = ?
            ORDER BY id ASC
            """,
            (report_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def delete_report(report_id: int) -> Optional[str]:
    """Delete report and return stored PDF path if found."""
    with closing(_connect()) as conn:
        cursor = conn.execute(
            "SELECT pdf_path FROM reports WHERE id = ?",
            (report_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        pdf_path = row[0]
        conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
        return pdf_path
