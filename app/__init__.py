"""DevFlow — CI/CD Demonstration Platform.

This module contains the application factory plus a few small helpers that
describe the running application (environment, build metadata). Everything the
UI and API expose about the runtime is derived here so there is a single source
of truth.
"""

from __future__ import annotations

import os
import platform
from datetime import UTC, datetime

from flask import Flask

APP_NAME = "devflow"
APP_VERSION = "1.0.0"

# Environments the application understands. Anything else is reported as
# "unknown" instead of being echoed back verbatim.
VALID_ENVIRONMENTS = ("development", "staging", "production", "test")

# CI/CD providers set different commit variables. We read the first one that is
# present instead of dumping the environment.
COMMIT_ENV_VARS = ("GIT_COMMIT", "GITHUB_SHA", "RENDER_GIT_COMMIT", "SOURCE_VERSION")
BUILD_NUMBER_ENV_VARS = ("BUILD_NUMBER", "GITHUB_RUN_NUMBER", "RENDER_BUILD_ID")
BRANCH_ENV_VARS = ("GIT_BRANCH", "GITHUB_REF_NAME", "RENDER_GIT_BRANCH")


def _first_env(names: tuple[str, ...]) -> str | None:
    """Return the first non-empty environment variable, else ``None``."""
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def resolve_environment(default: str = "development") -> str:
    """Resolve the deployment environment from ``APP_ENV``.

    Unknown values are reported as ``"unknown"`` so a typo in configuration is
    visible in the UI rather than silently treated as production.
    """
    value = (os.environ.get("APP_ENV") or default).strip().lower()
    return value if value in VALID_ENVIRONMENTS else "unknown"


def resolve_version() -> str:
    """Application version, overridable at build time via ``APP_VERSION``."""
    return os.environ.get("APP_VERSION", "").strip() or APP_VERSION


def get_build_info() -> dict[str, str | None]:
    """Describe the build that is currently running.

    Every field is optional: a local checkout has no CI metadata, and in that
    case the values are ``None``. Nothing here is invented.
    """
    commit = _first_env(COMMIT_ENV_VARS)
    return {
        "commit": commit[:12] if commit else None,
        "build_number": _first_env(BUILD_NUMBER_ENV_VARS),
        "branch": _first_env(BRANCH_ENV_VARS),
        "collected_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def get_runtime_info() -> dict[str, str | None]:
    """Safe runtime details (no secrets, no environment dump)."""
    server_software = os.environ.get("SERVER_SOFTWARE", "")
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "server": "gunicorn" if server_software.startswith("gunicorn") else None,
    }


def create_app(config: dict | None = None) -> Flask:
    """Create and configure a Flask application instance."""
    app = Flask(__name__)

    app.config.from_mapping(
        APP_NAME=APP_NAME,
        APP_VERSION=resolve_version(),
        ENVIRONMENT=resolve_environment(),
        BUILD_INFO=get_build_info(),
        RUNTIME_INFO=get_runtime_info(),
    )
    if config:
        app.config.update(config)

    from .routes import bp

    app.register_blueprint(bp)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'"
        )
        return response

    return app
