"""Shared pytest fixtures.

The tests never touch the network or a real deployment: each app instance is
created in-process and CI-related environment variables are cleared so results
do not depend on the machine running the suite.
"""

from __future__ import annotations

import pytest

from app import BRANCH_ENV_VARS, BUILD_NUMBER_ENV_VARS, COMMIT_ENV_VARS, create_app

BUILD_ENV_VARS = (
    *COMMIT_ENV_VARS,
    *BUILD_NUMBER_ENV_VARS,
    *BRANCH_ENV_VARS,
    "APP_VERSION",
    "APP_ENV",
)


@pytest.fixture
def clean_env(monkeypatch):
    """Remove every optional environment variable the app reads."""
    for name in BUILD_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture
def app(clean_env):
    """Application configured like a local development checkout."""
    return create_app({"TESTING": True})


@pytest.fixture
def client(app):
    """Flask test client bound to the app fixture."""
    return app.test_client()
