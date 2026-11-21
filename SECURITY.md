# Security Policy

## Supported versions

DevFlow is a demonstration project. Security fixes are applied to the `main`
branch, which is the only supported version.

| Version | Supported |
| ------- | --------- |
| 1.0.x   | ✅        |

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Instead:

1. Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
   (“Report a vulnerability” on the **Security** tab of the repository), or
2. Contact the maintainer listed in the repository profile.

Include the affected version, reproduction steps, and the impact you expect.
You can expect an initial response within a few days. Please give a reasonable
amount of time for a fix before publishing details.

## Secrets handling

- **Never commit secrets.** `.env`, `.env.*`, credentials files and local IDE
  settings are listed in `.gitignore`; only `.env.example` with placeholders is
  tracked.
- **Keep runtime configuration out of the image.** The Dockerfile copies only
  `app/` and `run.py`; `.dockerignore` excludes `.git`, tests, caches and env files.
- **Use GitHub Actions secrets / repository variables** for `RENDER_DEPLOY_HOOK_URL`,
  `APP_BASE_URL` and `DEPLOY_ENABLED`. Reference them with `${{ secrets.* }}` and
  `${{ vars.* }}`; never inline their values in a workflow.
- **Use the platform secret store** (Render environment variables / secret files)
  for anything the running service needs.
- **Rotate immediately** if a secret leaks: revoke the deploy hook in Render, rotate
  any related API keys, and remove the value from history (for example with
  `git filter-repo`) before rewriting the branch.
- **Least privilege.** The CI workflow has `contents: read`. Only the image
  publishing job gets `packages: write`, and it uses the ephemeral
  `GITHUB_TOKEN`; no long-lived registry password is stored.
- **Do not expose configuration.** `/api/info` returns only version, environment,
  interpreter version and optional build identifiers. It never dumps environment
  variables or secrets.

## Application hardening in this project

- Production runs Gunicorn, not Flask's development server; debug mode is refused
  when `APP_ENV=production`.
- Responses set `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` and a
  restrictive `Content-Security-Policy`.
- The container runs as the unprivileged `devflow` user with no build tools or
  compilers installed.
- The base image (`python:3.12-slim`) and Python dependencies are pinned; Dependabot
  (or `pip list --outdated`) should be used to track updates.

## Out of scope

This project has no authentication, user accounts or database, and it is not
intended to store personal data. Reports about missing authentication features are
therefore not vulnerabilities.
