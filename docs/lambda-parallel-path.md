# Lambda Parallel Path — Deploy Runbook (ADR-001, Option B)

Additive second backend on AWS Lambda, validated side-by-side with the live EC2
path. **EC2 and the CloudFront default behaviour stay untouched through Phase 1.**
Every step has an explicit rollback.

```
                   ┌──────────────── CloudFront E3D1THC6E0B6M2 ─────────────────┐
   Amplify frontend│  default behaviour (/api/*)  →  EC2 :8000   (PRIMARY, live) │
        │          │  /v2/* behaviour  (Phase 1.4) →  Lambda Fn URL (CANARY)     │
        └─────────►│                                                            │
                   └────────────────────────────────────────────────────────────┘
                                          ▲ direct invoke for validation (Step 3)
                            Lambda Fn URL (RESPONSE_STREAM) ← wealthseva-backend-lambda
                                          │ reads wealthseva/production (Secrets Manager)
                                          │ bedrock:InvokeModel(+WithResponseStream)
```

## Why this shape (grounding, not assumption)

- **No WebSocket.** `/api/chat` is FastAPI `StreamingResponse` (chunked HTTP), read
  by `AvatarChat.tsx` via `getReader()`. So 100% of traffic can move to Lambda.
- **Stateless.** Conversation history is sent per-request (`req.history`); account
  data comes from Supabase. No in-memory/EC2-disk session state to migrate.
- **Already containerised.** EC2 runs `backend/Dockerfile` → ECR → `docker run`,
  entrypoint `start.py` (pulls `wealthseva/production` from Secrets Manager, then
  `uvicorn main:app`). The Lambda image reuses that verbatim + the Web Adapter.
- **Streaming needs the Function URL, not API Gateway HTTP API.** API GW buffers
  the full response (reproduces the WEA-60 buffering bug). Function URL with
  `InvokeMode: RESPONSE_STREAM` preserves the chunked stream.

## Prerequisites

- AWS creds with rights to push to ECR, create IAM roles / Lambda / Function URL,
  and edit CloudFront (the same identity used by `.github/workflows/deploy.yml`).
- ECR repo `wealthseva-backend` already exists (EC2 path uses it).
- Region `ap-south-1`, account `408336116890`.

## Step 1 — Build & push the Lambda image

```bash
ACCOUNT=408336116890
REGION=ap-south-1
SHA=$(git rev-parse --short HEAD)

aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com

# Build context = repo root (so ai/ copies in), same as the EC2 image build.
docker build --platform linux/amd64 \
  --file backend/Dockerfile.lambda \
  -t ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-${SHA} \
  -t ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-latest .

docker push ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-${SHA}
docker push ${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-latest
```

## Step 2 — Deploy the stack

```bash
aws cloudformation deploy \
  --stack-name wealthseva-lambda-parallel \
  --template-file infra/lambda-parallel-path.cfn.yaml \
  --parameter-overrides \
      ImageUri=${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/wealthseva-backend:lambda-${SHA} \
      CorsOrigins="https://main.d13rdix674q29k.amplifyapp.com" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

aws cloudformation describe-stacks \
  --stack-name wealthseva-lambda-parallel \
  --query 'Stacks[0].Outputs' --region $REGION
```

Capture the `FunctionUrl` output.

## Step 3 — Validate the Lambda path directly (before touching CloudFront)

```bash
FN_URL="<FunctionUrl from Step 2>"

# Health
curl -sf ${FN_URL}/health

# Cold start, then warm — measure the delta (ADR Action Item #9)
curl -o /dev/null -s -w 'cold first call: %{time_total}s\n' \
  -X POST ${FN_URL}/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"DEMO_MODE_SIP_HINDI","language":"hi","history":[]}'
curl -o /dev/null -s -w 'warm follow-up: %{time_total}s\n' \
  -X POST ${FN_URL}/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"hello","language":"en","history":[]}'

# Verify the stream is progressive, not buffered — time-to-first-byte should be
# well under total time:
curl -N -X POST ${FN_URL}/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"explain SIP","language":"en","history":[]}' | head -c 80

# Non-streaming endpoints
curl -sf ${FN_URL}/api/goals/presets
curl -sf -X POST ${FN_URL}/api/risk-profile \
  -H 'Content-Type: application/json' \
  -d '{"answers":[{"question_id":1,"answer":"C"},{"question_id":2,"answer":"C"},{"question_id":3,"answer":"C"},{"question_id":4,"answer":"C"},{"question_id":5,"answer":"C"}],"language":"en"}'

# Logs (cold-start init time shows here)
aws logs tail /aws/lambda/wealthseva-backend-lambda --follow --region $REGION
```

**Pass criteria:** health 200; chat streams progressively (TTFB ≪ total); Bedrock
+ Secrets Manager loads (check `[start] Loaded N/N keys` in logs); cold start
noted. **Do not proceed to Step 4 if any fail.**

## Step 4 — Add the CloudFront canary route `/v2/*` (additive)

This mutates the live distribution — do it carefully. Get config + ETag, add a
second origin + a `/v2/*` behaviour pointing at it, keep the default behaviour on
EC2. Console or scripted; the shape is:

```bash
DIST=E3D1THC6E0B6M2
aws cloudfront get-distribution-config --id $DIST > /tmp/cf.json   # note ETag
# Edit /tmp/cf.json DistributionConfig:
#   Origins.Items: add { Id: wealthseva-lambda,
#                        DomainName: <function-url-host>,
#                        CustomOriginConfig: { OriginProtocolPolicy: https-only,
#                                              OriginReadTimeout: 60 } }
#   CacheBehaviors.Items: add { PathPattern: /v2/*,
#                               TargetOriginId: wealthseva-lambda,
#                               ViewerProtocolPolicy: redirect-to-https,
#                               AllowedMethods: [GET,HEAD,OPTIONS,PUT,POST,PATCH,DELETE],
#                               ForwardedValues: { QueryString: true,
#                                                  Headers: [Content-Type,Origin] },
#                               MinTTL:0, DefaultTTL:0, MaxTTL:0 }   # no caching — stream/RAG
# Then:
aws cloudfront update-distribution --id $DIST --if-match <ETag> \
  --distribution-config file://tmp/cf.json
```

> The frontend still hits `/api/*` (→ EC2). `/v2/*` is an **ops canary** for
> side-by-side comparison only. The user-facing cutover (Phase 2) flips the
> *default* behaviour to the Lambda origin — no frontend change needed then.

## Step 5 — Side-by-side validation

```bash
CF=https://d37mp3ng6xzrzd.cloudfront.net
for path in /health /api/goals/presets; do
  echo "EC2  $path : $(curl -o /dev/null -s -w '%{http_code} %{time_total}s' $CF$path)"
  echo "LAMB /v2$path : $(curl -o /dev/null -s -w '%{http_code} %{time_total}s' $CF/v2$path)"
done
# Streaming parity:
curl -N $CF/v2/api/chat -X POST -H 'Content-Type: application/json' \
  -d '{"message":"DEMO_MODE_SIP_HINDI","language":"hi","history":[]}'
```

Compare latency, status codes, and progressive streaming. ADR Action Item #10.

## Hardening (before cutover)

- **Function URL is currently `AuthType: NONE`** (public). Add a CloudFront origin
  custom header `x-origin-verify: <random>` to the Lambda origin and reject
  requests missing it (middleware or the adapter's built-in check) so the URL
  can't be invoked directly. Mirrors ADR Phase 0 item #1 (tighten EC2 SG).
- **Provisioned concurrency** if cold starts exceed your latency budget
  (provisioned concurrency costs money — decide after Step 3 numbers):
  ```bash
  aws lambda put-provisioned-concurrency-config \
    --function-name wealthseva-backend-lambda \
    --qualifier <published-version-arn> \
    --provisioned-concurrent-executions 2 --region ap-south-1
  ```

## Rollback

| Stage | Rollback |
|---|---|
| After Step 2/3 (Lambda only) | `aws cloudformation delete-stack --stack-name wealthseva-lambda-parallel`. EC2 path unaffected. |
| After Step 4 (CloudFront `/v2/*`) | Re-edit distribution: remove the `/v2/*` behaviour + Lambda origin. Default (EC2) was never changed. |
| After Phase 2 cutover | Flip CloudFront default behaviour back to the EC2 origin; `aws ec2 start-instances --instance-ids i-0c2877eae9f724ede` (EC2 was *stopped*, not terminated). |

## Open decisions (need your call before cutover)

1. **Cold-start budget** — is the measured cold start acceptable, or pay for
   provisioned concurrency? (Tune `MemoryMB` first — more memory = more CPU = faster init.)
2. **Function URL auth** — keep `NONE` + custom header, or switch to `AWS_IAM`?
3. **Memory / timeout** — CFN defaults are 2048 MB / 60 s; confirm or override.
4. **Canary shape** — `/v2/*` path (this runbook) vs header-based split.
5. **CI integration** — add a Lambda build/push job to `.github/workflows/deploy.yml`
   alongside the EC2 job, or keep Lambda deploys manual until after cutover?
