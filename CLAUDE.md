# WealthSeva AI — Claude Code Context

## Project
AI-powered multilingual wealth management avatar for IDBI Bank.
Built for IDBI Innovate 2026 hackathon — Track 01: Digital Wealth Management.

## Stack
- Frontend: Next.js 14, TailwindCSS, TypeScript, next-intl (i18n)
- Backend: FastAPI, Python 3.12, LangChain, langdetect
- AI: Claude API via Amazon Bedrock (global.anthropic.claude-sonnet-4-6) — natively multilingual
- Embeddings: Amazon Titan Text Embeddings V2 via Bedrock (amazon.titan-embed-text-v2:0)
- Avatar: ElevenLabs Conversational AI (multilingual voices)
- DB: Supabase (PostgreSQL), Pinecone (vector store)
- Cloud: AWS (EC2/Lambda + S3), provided by IDBI Bank
- Region: ap-south-1 (Mumbai) — compute and Bedrock inference run in India
- Authentication: IAM role for Bedrock (no API keys when running on EC2/Lambda)

## Supported Languages
EN (English), HI (Hindi/हिंदी), MR (Marathi/मराठी), TA (Tamil/தமிழ்), BN (Bengali/বাংলা)
User preferred_language is stored in Supabase and passed to every Claude API call.

## Coding Conventions
- All API calls use async/await
- Error responses follow { "error": string, "code": string } format
- All Claude system prompts live in /ai/system_prompts/
- Environment variables via .env (backend) and .env.local (frontend) — never hardcode
- Use Pydantic models for all FastAPI request/response schemas
- TypeScript strict mode enabled

## Key Files
- backend/services/claude_service.py   — Core Claude API logic + streaming
- backend/services/language_service.py — Language detection + prompt/voice routing
- backend/routers/chat.py              — Main chat endpoint
- frontend/app/[locale]/advisor/page.tsx — Avatar chat UI
- frontend/components/LanguageSwitcher.tsx — Language switcher (EN|HI|MR|TA|BN)
- ai/system_prompts/wealth_advisor_*.md — Per-language system prompts

## API Endpoints
- POST /api/chat          — Main conversational endpoint (streams Claude response)
- POST /api/risk-profile  — Submit risk quiz answers → get risk score
- POST /api/portfolio     — Upload/analyze portfolio
- GET  /api/insights      — Daily market insights in user's language
- POST /api/goals         — Create/update financial goals

## Current Sprint Focus
[Update this daily]
Phase 1 (Jun 23–26): Scaffold + avatar integration + language switcher working end-to-end

## Agent Review & Triage Workflow
Agents commit directly to `dev` (no PR gate — Option B). shreya-reviewer
reviews commits after the fact and posts APPROVED / CHANGES_REQUESTED verdicts.

### Engineer agents — on TASK_COMPLETE

When all TASK_COMPLETE criteria in your issue description are met:

1. Commit and push your changes to `dev`.
2. Set your issue status to **`in_review`** — NOT `done`. Use:
   `mcp__paperclip__update_issue(issueId="WEA-XX", status="in_review")`
3. Post a comment: "TASK_COMPLETE — committed [short hash]. Setting to
   in_review for code review."

Do NOT mark your own issue as `done`. The reviewer is the one that closes
the loop to `done` after approving. This is enforced on all code tasks:
backend, frontend, and utility.

### shreya-reviewer — on APPROVED verdict

1. Post a comment on the reviewed issue: "APPROVED — code meets standards."
2. Update the ORIGINAL work issue to `done`:
   `mcp__paperclip__update_issue(issueId="WEA-XX", status="done")`
3. Mark this review issue as `done`.

### shreya-reviewer — on CHANGES_REQUESTED verdict

1. Create a new fix issue in this project:
   - Title: "Fix: <short description>" referencing the original commit hash
   - Body: specific file/line locations and the exact fix needed
   - Status: `backlog`, **unassigned** — do NOT assign to any engineer agent.
2. Post a comment on the ORIGINAL work issue (not just the new fix issue):
   "CHANGES_REQUESTED — Fix issue [WEA-X] created in backlog, awaiting board
   triage. Original issue remains `in_review` pending resolution."
   This comment is the primary notification mechanism — watch the original
   issue thread, not just the backlog list.
3. Leave the original work issue in **`in_review`** status. Do NOT change it
   to `done` or `blocked`.
4. Mark this review issue as `done`.

### Human board operator (triage)

- Watch for `in_review` issues: engineer agent has finished, review pending.
- Dispatch the corresponding WEA-2X review ticket to shreya-reviewer.
- When CHANGES_REQUESTED fix issues appear in backlog (unassigned), triage
  and assign to the appropriate engineer agent before dispatching.

Reviewer confidence is not sufficient grounds for auto-dispatching fixes —
board review is the gate. This is a deliberate human-in-the-loop checkpoint
on a no-PR-gate workflow.

If this convention changes (e.g. notifications get wired up via a plugin,
or auto-dispatch is approved after Jul 9), update this section.

## Architecture Notes
- Language detection: langdetect on incoming message, fallback to user.preferred_language
- Claude prompt routing: load ai/system_prompts/wealth_advisor_{lang}.md per request
- Bedrock integration: AsyncAnthropicBedrock for Claude, BedrockEmbeddings for Titan
- Region: All Bedrock calls use ap-south-1; IAM authentication via boto3 credential chain
- ElevenLabs voice: VOICE_MAP in language_service.py maps lang_code → voice_id
- Pinecone namespaces: idbi-data-{lang} — separate namespace per language
- RAG: index IDBI synthetic datasets; retrieve top-3 chunks per query using Titan embeddings
- Graceful degradation: Missing AWS credentials return mock responses, never 500 errors
- Deployment (prod, post-2026-07-11 cutover): serverless — backend on a Lambda Function URL (RESPONSE_STREAM). The Amplify `main` frontend calls it directly for streaming `/api/chat` and via its SSR proxy (`frontend/app/api/[...path]/route.ts`, injects `x-origin-verify`) for the other endpoints. The public FURL is gated by `backend/origin_verify.py` plus chat rate-limit / input-caps / `CHAT_PUBLIC_ENABLED` kill-switch. EC2 is a stopped rollback; CloudFront is NOT in the Lambda path (CF→Function-URL is unsupported in this account/region). Stack: `infra/lambda-parallel-path.cfn.yaml`; runbook: `docs/lambda-parallel-path.md`

## Demo Priorities (for judges)
1. Language switch mid-conversation (English → Hindi live demo)
2. Avatar speaking in correct regional language
3. Personalized SIP recommendation with real numbers
4. Risk profiler → portfolio recommendation flow