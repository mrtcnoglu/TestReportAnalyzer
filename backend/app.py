"""Application factory for the TestReportAnalyzer backend."""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

try:  # pragma: no cover - import resolution for script execution
    from .database import init_db
    from .routes import reports_bp
    from .routes.ai import bp as ai_bp
except ImportError:  # pragma: no cover
    from database import init_db  # type: ignore
    from routes import reports_bp  # type: ignore
    from routes.ai import bp as ai_bp  # type: ignore


def _resolve_host(default: str = "0.0.0.0") -> str:
    """Return the host address the development server should bind to."""

    for env_name in ("FLASK_RUN_HOST", "FLASK_HOST", "HOST"):
        host = os.getenv(env_name)
        if host:
            return host
    return default


def _resolve_port(default: int = 5000) -> int:
    """Return the TCP port as an integer, validating environment overrides."""

    for env_name in ("FLASK_RUN_PORT", "FLASK_PORT", "PORT"):
        port_value = os.getenv(env_name)
        if port_value:
            try:
                return int(port_value)
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError(f"Invalid port value for {env_name}: {port_value!r}") from exc
    return default


def _resolve_debug(default: bool = True) -> bool:
    """Return whether the Flask dev server should run in debug mode."""

    flag = os.getenv("FLASK_DEBUG")
    if flag is None:
        return default
    return flag.strip().lower() in {"1", "true", "yes", "on"}


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    base_dir = Path(__file__).resolve().parent
    upload_dir = base_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)

    init_db()
    app.register_blueprint(reports_bp, url_prefix="/api")
    app.register_blueprint(ai_bp)
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host=_resolve_host(),
        port=_resolve_port(),
        debug=_resolve_debug(),
    )
