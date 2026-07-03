FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

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
