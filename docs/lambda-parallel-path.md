# Serverless Backend — Deploy & Ops Runbook (ADR-001, Option B)

The WealthSeva backend runs **serverless on AWS Lambda** behind a Function URL
(response streaming). This became the **production** path in the 2026-07-11
cutover; the former EC2 instance is kept **stopped** as a rollback. The stack is
`wealthseva-lambda-parallel` (`infra/lambda-parallel-path.cfn.yaml`), function
`wealthseva-backend-lambda`, region `ap-south-1`, account `408336116890`.

> The name "parallel path" is historical — it started as an additive canary
> alongside EC2. Post-cutover it is the primary (and only running) backend.

## Architecture (as deployed)

```
        Amplify `main` frontend  (https://main.d13rdix674q29k.amplifyapp.com)
                 │
                 ├─ /api/chat ─────────────────► Lambda Function URL  (DIRECT, streamed)
                 │   NEXT_PUBLIC_CHAT_URL           AuthType NONE · InvokeMode RESPONSE_STREAM
                 │   (browser → FURL)               exempt from origin-verify; rate-limited
                 │
                 └─ /api/* (the other 9) ──► Amplify SSR proxy ──► Lambda Function URL
                     same-origin fetch        app/api/[...path]/route.ts
                                              injects x-origin-verify header
                                                                    │
                                     wealthseva-backend-lambda ◄────┘
                                       reads wealthseva/production (Secrets Manager)
                                       bedrock:InvokeModel(+WithResponseStream)

   EC2 i-0c2877eae9f724ede  →  STOPPED (rollback only). CloudFront E3D1THC6E0B6M2
   still fronts EC2 for the legacy origin but is NOT part of the Lambda path.
```

**Hybrid split — why chat is direct and everything else is proxied:**

- **Chat streams; Amplify SSR buffers.** `/api/chat` is a FastAPI
  `StreamingResponse` (chunked HTTP) read by `AvatarChat.tsx` via `getReader()`.
  Amplify Hosting's SSR runtime buffers responses, which would kill token
  streaming — so the browser calls the Function URL **directly**
  (`NEXT_PUBLIC_CHAT_URL`), bypassing Amplify.
- **The other endpoints go through the Amplify SSR proxy**
  (`frontend/app/api/[...path]/route.ts`), which runs server-side, injects the
  `x-origin-verify` secret, and forwards to the Function URL. This keeps the
  secret off the client and gives the browser a same-origin `/api/...` surface.
- **CloudFront is NOT used for the Lambda path.** CloudFront→Function-URL was
  proven unworkable in this account/region (see below), so the Function URL is
  public and protected at the app layer instead.

**Why not CloudFront in front of the Function URL?** Exhaustively tested
2026-07-10/11: OAC, `AuthType: AWS_IAM`, and every resource-policy shape return
`403 AccessDeniedException` at the Lambda service layer, while a direct curl to
the same URL reaches the app. It behaves like an account/region-level block on
`CloudFront → *.lambda-url.ap-south-1.on.aws`. Would need AWS Support to lift —
out of scope. The direct-FURL + app-gate design is the accepted end state.

## Security model (active, not future)

The Function URL is `AuthType: NONE` (public), so the app enforces access:

- **Origin-verify gate** (`backend/origin_verify.py`, middleware): if
  `ORIGIN_VERIFY_SECRET` is set, every request must carry a matching
  `x-origin-verify` header or it gets `403 ORIGIN_FORBIDDEN`. The Amplify SSR
  proxy injects it. `/health` and `/api/chat` are **exempt** (health probes and
  the direct-from-browser chat surface never carry the header).
- **Chat guardrails** (the exempt `/api/chat`): `@limiter.limit("10/minute")`
  keyed on the leftmost `X-Forwarded-For` (`backend/rate_limit.py`); input caps
  (`message`/`content` ≤ 2000 chars, `history` ≤ 10 → `422` pre-Bedrock,
  `backend/models/schemas.py`); and the `CHAT_PUBLIC_ENABLED` kill-switch
  (`false` → `503 CHAT_DISABLED`).
- **CORS**: `CORS_ORIGINS` allowlists the exact Amplify origin(s).

**Secret handling invariant:** `ORIGIN_VERIFY_SECRET` lives **only** as a Lambda
function-env var (CFN `OriginVerifySecret` parameter) and as the same-named
server-side env var on the Amplify `main` branch. It must **never** go in the
`wealthseva/production` Secrets Manager secret — `start.py` injects every key
from that secret into `os.environ` on **both** Lambda and EC2, and the EC2 path
sends no `x-origin-verify` header, so a shared value would 403 all EC2 traffic.

## Cold start / memory

At `MemoryMB: 3008` (this account's ceiling — pre-Nov-2023 cap) cold start is
~3.1 s (init completes inside Lambda's ~10 s budget; at 2048 MB it was ~21 s and
retry-inflated). Warm ~1 s. Provisioned concurrency is **not** used — 3.1 s is
demo-acceptable and cheaper per cold invoke.

## Prerequisites

- AWS creds with rights to ECR push, IAM role / Lambda / Function URL, and
  (for the frontend) Amplify — the identity used by `.github/workflows/deploy.yml`.
- ECR repo `wealthseva-backend` exists (shared with the EC2 image history).
- Region `ap-south-1`, account `408336116890`.

## Step 1 — Build & push the Lambda image

```bash
ACCOUNT=408336116890
REGION=ap-south-1
SHA=$(git rev-parse --short HEAD)

aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com

# Build context = repo root (so ai/ copies in), same as the EC2 image build.
# --provenance=false: buildx otherwise wraps the image in a manifest LIST, which
# Lambda rejects ("image manifest not supported").
docker build --platform linux/amd64 --provenance=false \
  --file backend/Dockerfile.lambda \
  -t ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-${SHA} \
  -t ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-latest .

docker push ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-${SHA}
docker push ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-latest
```

> `AWS_LWA_INVOKE_MODE=response_stream` is baked into `backend/Dockerfile.lambda`
> (and also declared in the CFN env) — required so the Web Adapter streams the
> response instead of buffering it into the Lambda JSON envelope.

## Step 2 — Deploy / update the stack

Generate the origin-verify secret **once** and reuse the same value on every
deploy (a fresh value would break the Amplify side until you update it there too):

```bash
# First time only — then store/reuse. Recover the live value with:
#   aws lambda get-function-configuration --function-name wealthseva-backend-lambda \
#     --region $REGION --query Environment.Variables.ORIGIN_VERIFY_SECRET
OVSECRET=$(openssl rand -hex 32)

aws cloudformation deploy \
  --stack-name wealthseva-lambda-parallel \
  --template-file infra/lambda-parallel-path.cfn.yaml \
  --parameter-overrides \
      ImageUri=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-${SHA} \
      CorsOrigins="https://main.d13rdix674q29k.amplifyapp.com" \
      OriginVerifySecret="$OVSECRET" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

aws cloudformation describe-stacks \
  --stack-name wealthseva-lambda-parallel \
  --query 'Stacks[0].Outputs' --region $REGION
```

Capture the `FunctionUrl` output (`FURL` below).

> **Fast image-only redeploy** (no infra change): the CI builds/pushes the image;
> to point the function at a new image without a full CFN deploy use
> `aws lambda update-function-code --function-name wealthseva-backend-lambda
> --image-uri <uri> --region $REGION && aws lambda wait function-updated ...`.

## Step 3 — Validate the Function URL directly

```bash
FURL="<FunctionUrl from Step 2>"

curl -sf ${FURL}/health                                   # 200
# Gate active: a non-chat call WITHOUT the header must 403.
curl -s -o /dev/null -w '%{http_code}\n' ${FURL}/api/insights?language=en   # 403
# With the header it passes (this is what the Amplify proxy does):
curl -s -H "x-origin-verify: $OVSECRET" ${FURL}/api/insights?language=en    # 200 real Claude
# Chat is exempt + streams (demo path needs no Bedrock; note X-Detected-Language: hi):
curl -N -X POST ${FURL}/api/chat -H 'Content-Type: application/json' \
  -d '{"message":"DEMO_MODE_SIP_HINDI","session_id":"smoke"}'

aws logs tail /aws/lambda/wealthseva-backend-lambda --follow --region $REGION
```

**Pass criteria:** health 200; unheadered non-chat → 403; headered non-chat →
200 with real (non-mock) content; chat streams progressively (TTFB ≪ total).
Success `path=bedrock` INFO lines are suppressed (logger defaults to WARNING) —
their absence is expected, not a failure.

## Step 4 — Wire the Amplify `main` frontend

Set these on the Amplify **main branch** (Console → App settings → Environment
variables, scoped to `main`), then trigger a build (a push to `main`, or
"Redeploy this version"). `NEXT_PUBLIC_*` bake in at build time.

| Variable | Value | Notes |
|---|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `https://main.d13rdix674q29k.amplifyapp.com` | Own origin → non-chat routes go same-origin through the SSR proxy. |
| `NEXT_PUBLIC_CHAT_URL` | `${FURL}/api/chat` | Browser calls chat directly (streaming). |
| `BACKEND_FURL_URL` | `${FURL}` (no trailing slash) | Server-side; SSR proxy target. |
| `ORIGIN_VERIFY_SECRET` | same value as the Lambda `OriginVerifySecret` | Server-side (NOT `NEXT_PUBLIC_`). |

> Amplify does **not** expose Console env vars to the Next.js SSR runtime by
> default — `amplify.yml` appends the server-side vars to `.env.production`
> during build (`env | grep -e '^BACKEND_FURL_URL=' -e '^ORIGIN_VERIFY_SECRET=' >>
> .env.production`) so `process.env.*` is populated at runtime. Leaving
> `NEXT_PUBLIC_BACKEND_URL` blank does **not** work (Amplify treats blank as
> unset → falls back to the app-level value); set it to the branch's own origin.

Verify in a **fresh tab** (stale bundles otherwise): chat streams; a non-chat
page (e.g. insights) returns real data via the proxy.

## Cost guardrails

Serverless scales to ~$0 idle; the guardrails cap runaway Bedrock spend:

- **AWS Budget** `wealthseva-monthly` — $20/mo cost, email at 80% actual /
  100% forecast (Budgets is global → `us-east-1`).
- **SNS topic** `wealthseva-cost-alerts` (ap-south-1) + email subscription
  (confirm the link once).
- **CloudWatch alarm** `wealthseva-bedrock-invocations-high` — `AWS/Bedrock`
  `Invocations` Sum over 1h > 500 → the SNS topic.

## Rollback

| From | Rollback |
|---|---|
| Bad image | `aws lambda update-function-code` to the previous `:lambda-<sha>`, or `cfn deploy` with the prior `ImageUri`. |
| Broken Amplify env | Restore the four env vars above and redeploy `main`. |
| Whole Lambda path down | Restart EC2 and repoint the frontend at the EC2/CloudFront origin: `aws ec2 start-instances --instance-ids i-0c2877eae9f724ede --region ap-south-1`. CloudFront's default behaviour still targets the EC2 origin; set the Amplify env back to the CloudFront backend URL. EC2 was *stopped*, not terminated. |

## Settled decisions (was "open")

1. **Cold start** — 3.1 s at 3008 MB accepted; no provisioned concurrency.
2. **Function URL auth** — `NONE` + app-level origin-verify gate (AWS_IAM/OAC via
   CloudFront is non-functional in this account/region).
3. **Memory / timeout** — 3008 MB / 60 s.
4. **Routing** — hybrid: direct FURL for streaming chat, Amplify SSR proxy for
   the rest. No CloudFront `/v2/*` canary (removed; CF→FURL unsupported here).
5. **CI** — `.github/workflows/deploy.yml` builds/pushes the Lambda image;
   `.github/workflows/preview-lambda.yml` is a manual `workflow_dispatch` preview.
