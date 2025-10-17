"""Application factory for the TestReportAnalyzer backend."""
from __future__ import annotations

from pathlib import Path

from flask import Flask
from flask_cors import CORS

try:  # pragma: no cover - import resolution for script execution
    from .database import init_db
    from .routes import reports_bp
except ImportError:  # pragma: no cover
    from database import init_db  # type: ignore
    from routes import reports_bp  # type: ignore


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    base_dir = Path(__file__).resolve().parent
    upload_dir = base_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)

    init_db()
    app.register_blueprint(reports_bp, url_prefix="/api")
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=True)
