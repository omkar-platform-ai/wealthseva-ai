FROM python:3.12-slim
WORKDIR /app

# Build context is the repo root (see .github/workflows/deploy.yml) so that
# ai/system_prompts/ can be copied in — services/language_service.py resolves
# prompts via `../../ai/system_prompts` from /app/services/, which lands at /ai/.
COPY backend/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY backend/ .
COPY ai /ai

# ── Prototype note ────────────────────────────────────────────────────────────
# TLS terminates at CloudFront + ACM.  EC2 only needs plain HTTP on port 8000.
# Self-signed cert generation removed — openssl no longer required.
# Phase 2: switch to ECS + ALB with ACM cert on the listener.
# ─────────────────────────────────────────────────────────────────────────────

EXPOSE 8000

# Default to production so start.py pulls secrets from AWS Secrets Manager.
# Override with `docker run -e ENVIRONMENT=development ...` for local dev.
ENV ENVIRONMENT=production

# start.py fetches secrets from AWS Secrets Manager (when ENVIRONMENT=production)
# then starts uvicorn — boto3 is already in requirements.txt
CMD ["python", "start.py"]
