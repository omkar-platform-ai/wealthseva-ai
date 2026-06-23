# WealthSeva AI — Claude Code Context

## Project
AI-powered multilingual wealth management avatar for IDBI Bank.
Built for IDBI Innovate 2026 hackathon — Track 01: Digital Wealth Management.

## Stack
- Frontend: Next.js 14, TailwindCSS, TypeScript, next-intl (i18n)
- Backend: FastAPI, Python 3.12, LangChain, langdetect
- AI: Claude API (claude-sonnet-4-6) — natively multilingual
- Avatar: ElevenLabs Conversational AI (multilingual voices)
- DB: Supabase (PostgreSQL), Pinecone (vector store)
- Cloud: AWS (EC2/Lambda + S3), provided by IDBI Bank

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

## Architecture Notes
- Language detection: langdetect on incoming message, fallback to user.preferred_language
- Claude prompt routing: load ai/system_prompts/wealth_advisor_{lang}.md per request
- ElevenLabs voice: VOICE_MAP in language_service.py maps lang_code → voice_id
- Pinecone namespaces: idbi-data-{lang} — separate namespace per language
- RAG: index IDBI synthetic datasets; retrieve top-3 chunks per query for Claude context

## Demo Priorities (for judges)
1. Language switch mid-conversation (English → Hindi live demo)
2. Avatar speaking in correct regional language
3. Personalized SIP recommendation with real numbers
4. Risk profiler → portfolio recommendation flow
