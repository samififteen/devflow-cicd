"""Local development entry point.

Production uses Gunicorn (see the Dockerfile / render.yaml):
    gunicorn --bind 0.0.0.0:${PORT} "app:create_app()"

Run locally with:
    python run.py
"""

from __future__ import annotations

import os

from app import create_app

app = create_app()


def _int_env(name: str, default: int) -> int:
    """Read an integer environment variable, falling back safely."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


if __name__ == "__main__":
    port = _int_env("PORT", 5000)
    host = os.environ.get("HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes"}
    if debug and app.config["ENVIRONMENT"] == "production":
        raise SystemExit("Refusing to start with FLASK_DEBUG=1 in a production environment.")
    app.run(host=host, port=port, debug=debug)
