"""Unit tests for the DevFlow application and its JSON API."""

from __future__ import annotations

import json
import platform

import pytest

from app import APP_NAME, APP_VERSION, create_app, get_build_info, resolve_environment

EXPECTED_STAGE_IDS = {"quality", "test", "build", "publish", "deploy", "verify"}


def test_index_returns_html_dashboard(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    body = response.get_data(as_text=True)
    assert "DevFlow" in body
    assert f"v{APP_VERSION}" in body


def test_health_returns_json(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    payload = json.loads(response.get_data(as_text=True))
    assert isinstance(payload, dict)


def test_health_reports_expected_status_and_service(client):
    payload = client.get("/health").get_json()

    assert payload == {"status": "healthy", "service": APP_NAME, "version": APP_VERSION}


def test_info_endpoint_returns_metadata(client):
    response = client.get("/api/info")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["name"] == APP_NAME
    assert payload["version"] == APP_VERSION
    assert payload["environment"] == "development"
    assert payload["python_version"] == platform.python_version()
    assert set(payload["build"]) == {"commit", "build_number", "branch", "collected_at"}


def test_info_endpoint_reports_missing_build_metadata_as_null(client):
    build = client.get("/api/info").get_json()["build"]

    assert build["commit"] is None
    assert build["build_number"] is None
    assert build["branch"] is None
    assert build["collected_at"]


def test_info_endpoint_does_not_leak_environment_or_secrets(clean_env, client):
    clean_env.setenv("SECRET_TOKEN", "super-secret-value")
    clean_env.setenv("DATABASE_URL", "postgres://user:password@db/app")

    body = client.get("/api/info").get_data(as_text=True)

    assert "super-secret-value" not in body
    assert "postgres://" not in body
    assert "SECRET_TOKEN" not in body


def test_pipeline_endpoint_lists_expected_stages(client):
    response = client.get("/api/pipeline")

    assert response.status_code == 200
    payload = response.get_json()
    stages = payload["configured_stages"]
    assert {stage["id"] for stage in stages} == EXPECTED_STAGE_IDS
    assert [stage["order"] for stage in stages] == list(range(1, len(stages) + 1))
    assert all(stage["name"] and stage["workflow"] for stage in stages)


def test_pipeline_endpoint_distinguishes_configuration_from_results(client):
    payload = client.get("/api/pipeline").get_json()

    assert payload["execution"]["collected"] is False
    assert payload["execution"]["status"] == "not-collected"
    assert payload["execution"]["detail"]
    for stage in payload["configured_stages"]:
        assert "status" not in stage


def test_unknown_route_returns_404(client):
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404


def test_security_headers_are_present(client):
    headers = client.get("/").headers

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'self'" in headers["Content-Security-Policy"]


def test_build_metadata_is_read_from_ci_environment(clean_env):
    clean_env.setenv("GITHUB_SHA", "0123456789abcdef0123")
    clean_env.setenv("GITHUB_RUN_NUMBER", "42")
    clean_env.setenv("GITHUB_REF_NAME", "main")

    build = get_build_info()

    assert build["commit"] == "0123456789ab"
    assert build["build_number"] == "42"
    assert build["branch"] == "main"


def test_environment_is_normalised_and_validated(clean_env):
    assert resolve_environment() == "development"

    clean_env.setenv("APP_ENV", "Production")
    assert resolve_environment() == "production"

    clean_env.setenv("APP_ENV", "not-a-real-env")
    assert resolve_environment() == "unknown"


@pytest.mark.parametrize("app_env", ["production", "staging", "test"])
def test_info_reflects_configured_environment(clean_env, app_env):
    clean_env.setenv("APP_ENV", app_env)
    test_app = create_app({"TESTING": True})

    assert test_app.test_client().get("/api/info").get_json()["environment"] == app_env


def test_version_can_be_overridden_at_build_time(clean_env):
    clean_env.setenv("APP_VERSION", "2.5.0")
    test_app = create_app({"TESTING": True})

    payload = test_app.test_client().get("/health").get_json()
    assert payload["version"] == "2.5.0"
