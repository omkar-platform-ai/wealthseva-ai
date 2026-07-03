"""
WealthSeva AI — container entrypoint

Startup order:
  1. Load .env  (local dev only — ignored in production if file absent)
  2. Fetch wealthseva/production from AWS Secrets Manager  (production)
  3. Start uvicorn

Secrets Manager values never override explicit environment variables,
so you can always override a single key by passing --env KEY=value to
docker run without touching the secret.
"""

import json
import os
import sys


# ── 1. Load .env for local development ───────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — fine in prod


# ── 2. Pull secrets from AWS Secrets Manager (production only) ───────────────
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
SECRET_NAME = os.environ.get("SECRET_NAME", "wealthseva/production")
AWS_REGION  = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")

if ENVIRONMENT == "production":
    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        response = client.get_secret_value(SecretId=SECRET_NAME)
        secrets: dict = json.loads(response["SecretString"])

        injected = 0
        for key, value in secrets.items():
            if key not in os.environ:          # explicit env vars always win
                os.environ[key] = str(value)
                injected += 1

        print(
            f"[start] Loaded {injected}/{len(secrets)} keys from "
            f"Secrets Manager ({SECRET_NAME})",
            flush=True,
        )

    except ClientError as e:
        code = e.response["Error"]["Code"]
        print(f"[start] ERROR fetching secrets ({code}): {e}", file=sys.stderr, flush=True)
        print("[start] Check the EC2 IAM role has secretsmanager:GetSecretValue permission.", file=sys.stderr)
        sys.exit(1)   # hard-fail — running without secrets is worse than not starting

    except Exception as e:
        print(f"[start] ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

else:
    print(f"[start] ENVIRONMENT={ENVIRONMENT} — skipping Secrets Manager (using .env)", flush=True)


# ── 3. Start uvicorn ──────────────────────────────────────────────────────────
# Import after env vars are set so any module-level reads (e.g. settings)
# see the correct values.
import uvicorn  # noqa: E402

# NOTE: uvicorn spawns worker processes via multiprocessing when workers>1.
# Each child re-imports this module, so uvicorn.run() MUST be guarded by
# `if __name__ == "__main__":` or the children will recursively try to
# start their own workers and crash with a RuntimeError.
if __name__ == "__main__":
    WORKERS = int(os.environ.get("UVICORN_WORKERS", "2"))
    PORT    = int(os.environ.get("PORT", "8000"))

    print(f"[start] Starting uvicorn on 0.0.0.0:{PORT} with {WORKERS} worker(s)", flush=True)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        workers=WORKERS,
        # Reload only in dev; workers>1 + reload together raises an error
        reload=False,
    )
