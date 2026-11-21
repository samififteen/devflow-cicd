"""HTTP routes for the DevFlow dashboard and its JSON API."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template

bp = Blueprint("main", __name__)

# The pipeline that the repository's GitHub Actions workflows implement. This
# is *configuration* metadata: it describes what CI/CD is set up to do. Real
# execution results are never fabricated here.
PIPELINE_STAGES: tuple[dict[str, object], ...] = (
    {
        "id": "quality",
        "name": "Code quality",
        "tool": "Ruff",
        "workflow": ".github/workflows/ci.yml",
        "description": "Lint the codebase and verify formatting with Ruff.",
    },
    {
        "id": "test",
        "name": "Automated tests",
        "tool": "pytest",
        "workflow": ".github/workflows/ci.yml",
        "description": "Run the full pytest suite against Flask's test client.",
    },
    {
        "id": "build",
        "name": "Docker build",
        "tool": "Docker",
        "workflow": ".github/workflows/ci.yml",
        "description": "Build the production image to validate the Dockerfile.",
    },
    {
        "id": "publish",
        "name": "Image publish",
        "tool": "GHCR",
        "workflow": ".github/workflows/cd.yml",
        "description": "Push the image tagged with the commit SHA to GitHub Container Registry.",
    },
    {
        "id": "deploy",
        "name": "Deployment",
        "tool": "Render",
        "workflow": ".github/workflows/cd.yml",
        "description": "Trigger the hosting platform deploy hook for the main branch.",
    },
    {
        "id": "verify",
        "name": "Verification",
        "tool": "curl",
        "workflow": ".github/workflows/cd.yml",
        "description": "Poll /health on the deployed URL and fail if it does not answer.",
    },
)


def _pipeline_payload() -> dict[str, object]:
    """Shared representation of the configured pipeline."""
    return {
        "service": current_app.config["APP_NAME"],
        "version": current_app.config["APP_VERSION"],
        "configured_stages": [
            {"order": index, **stage} for index, stage in enumerate(PIPELINE_STAGES, start=1)
        ],
        "execution": {
            "collected": False,
            "status": "not-collected",
            "detail": (
                "This endpoint describes pipeline configuration only. "
                "Live run results are available in the GitHub Actions tab of the repository."
            ),
        },
    }


@bp.get("/")
def index():
    """Render the DevFlow dashboard."""
    return render_template(
        "index.html",
        app_name=current_app.config["APP_NAME"],
        version=current_app.config["APP_VERSION"],
        environment=current_app.config["ENVIRONMENT"],
        stages=PIPELINE_STAGES,
        build=current_app.config["BUILD_INFO"],
        runtime=current_app.config["RUNTIME_INFO"],
    )


@bp.get("/health")
def health():
    """Liveness probe used by Docker, CI and the hosting platform."""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": current_app.config["APP_NAME"],
                "version": current_app.config["APP_VERSION"],
            }
        ),
        200,
    )


@bp.get("/api/info")
def info():
    """Non-sensitive application metadata."""
    runtime = current_app.config["RUNTIME_INFO"]
    return jsonify(
        {
            "name": current_app.config["APP_NAME"],
            "version": current_app.config["APP_VERSION"],
            "environment": current_app.config["ENVIRONMENT"],
            "python_version": runtime["python_version"],
            "python_implementation": runtime["python_implementation"],
            "build": current_app.config["BUILD_INFO"],
        }
    )


@bp.get("/api/pipeline")
def pipeline():
    """Describe the configured CI/CD pipeline stages."""
    return jsonify(_pipeline_payload())
