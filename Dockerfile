# syntax=docker/dockerfile:1
# Production image for DevFlow: slim Python, non-root user, Gunicorn WSGI server.

FROM python:3.12-slim

# Do not write .pyc files and stream logs straight to stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    APP_ENV=production \
    WEB_CONCURRENCY=2

WORKDIR /app

# Create an unprivileged user before copying application code.
RUN groupadd --system devflow \
    && useradd --system --gid devflow --create-home --home-dir /home/devflow devflow

# Runtime dependencies only: the lockstep pin lives in requirements.txt.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code only (see .dockerignore for what is excluded).
COPY --chown=devflow:devflow app ./app
COPY --chown=devflow:devflow run.py ./

USER devflow

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; port = os.environ.get('PORT', '8000'); urllib.request.urlopen('http://127.0.0.1:' + port + '/health', timeout=3)"

# Gunicorn (not the Flask dev server). The port comes from $PORT so the same
# image works locally, on Render and on any container host.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY:-2} --access-logfile - --error-logfile - 'app:create_app()'"]
