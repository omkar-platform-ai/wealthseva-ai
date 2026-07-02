# WealthSeva AI 🏦

> AI-powered multilingual wealth advisor avatar for IDBI Bank — IDBI Innovate 2026, Track 01

[![Live Demo](https://img.shields.io/badge/Live%20Demo-WealthSeva-brightgreen)](https://github.com/omkar-platform-ai/wealthseva-ai)
[![CI](https://github.com/omkar-platform-ai/wealthseva-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/omkar-platform-ai/wealthseva-ai/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

**WealthSeva AI** is an avatar-based, conversational wealth management assistant that integrates into IDBI Bank's mobile banking app. It delivers personalized, AI-powered financial guidance to 500M+ Indian bank customers — in their preferred language.

**Supported Languages:** English &nbsp;|&nbsp; हिंदी &nbsp;|&nbsp; मराठी &nbsp;|&nbsp; தமிழ் &nbsp;|&nbsp; বাংলা

---

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Data Flow](#data-flow)
- [Multilingual Architecture](#multilingual-architecture)
- [RAG Pipeline](#rag-pipeline)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)

---

## Features

| Feature | Description |
|---|---|
| 🤖 **AI Avatar Advisor** | Real-time talking avatar (ElevenLabs) powered by Claude API — Shreya, your IDBI wealth advisor |
| 🌐 **Multilingual** | Full UI + avatar voice in 5 Indian languages; auto-detects language from user input |
| 📊 **Risk Profiler** | 5-question onboarding quiz → Conservative / Moderate / Aggressive profile + recommended allocation |
| 💼 **Portfolio Analyzer** | Upload CSV → Claude analysis → actionable rebalancing recommendations |
| 🎯 **Goal Planner** | Set goals (retirement, house, education) → AI-generated SIP + savings plan |
| 📈 **Market Insights** | Daily personalized market commentary in the user's language |
| 🏦 **IDBI Sandbox APIs** | Transaction data, UPI patterns, MSME financials — grounded advisory, not guesswork |
| 🧠 **RAG-Grounded Responses** | Retrieves relevant IDBI dataset context before every Claude call — factual, hallucination-resistant |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Next.js 14 Frontend                            │   │
│  │                                                                   │   │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────┐  │   │
│  │  │  Avatar UI   │  │  Dashboard       │  │  Language Switcher │  │   │
│  │  │ (ElevenLabs) │  │  (Portfolio,     │  │  EN|HI|MR|TA|BN   │  │   │
│  │  │  streaming   │  │   Goals, Risk)   │  │  (next-intl)       │  │   │
│  │  └──────┬───────┘  └────────┬─────────┘  └────────┬───────────┘  │   │
│  │         └───────────────────┴──────────────────────┘              │   │
│  │                             │  HTTP / SSE                          │   │
│  └─────────────────────────────┼──────────────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                          API LAYER (FastAPI)                             │
│                                                                          │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌───────┐  │
│  │  /chat   │  │/portfolio │  │/risk-     │  │ /goals   │  │/idbi  │  │
│  │ (stream) │  │ (upload)  │  │ profile   │  │ (plan)   │  │(txns) │  │
│  └────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────┬─────┘  └───┬───┘  │
└───────┼──────────────┼───────────────┼──────────────┼────────────┼──────┘
        │              │               │              │            │
┌───────▼──────────────▼───────────────▼──────────────▼────────────▼──────┐
│                        SERVICE LAYER                                      │
│                                                                           │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌────────────────┐  │
│  │   claude_service    │  │   language_service   │  │  risk_service  │  │
│  │                     │  │                      │  │                │  │
│  │  • stream_chat()    │  │  • detect_language() │  │  • score_quiz()│  │
│  │  • analyze_        │  │  • get_system_       │  │  • ALLOCATIONS │  │
│  │    portfolio()      │  │    prompt(lang)      │  │    map         │  │
│  │  • generate_        │  │  • get_voice_id()    │  │                │  │
│  │    goal_plan()      │  │                      │  │                │  │
│  └──────────┬──────────┘  └──────────────────────┘  └────────────────┘  │
│             │                                                             │
│  ┌──────────▼──────────┐                                                 │
│  │    rag_service      │                                                 │
│  │                     │                                                 │
│  │  • retrieve_        │                                                 │
│  │    context(query,   │                                                 │
│  │    language)        │                                                 │
│  └──────────┬──────────┘                                                 │
└─────────────┼───────────────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────────────┐
│                        EXTERNAL SERVICES                                  │
│                                                                           │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐ │
│  │  Anthropic    │  │  ElevenLabs  │  │  Pinecone  │  │   Supabase   │ │
│  │  Claude API   │  │  (Avatar     │  │  (Vector   │  │  (PostgreSQL │ │
│  │  claude-      │  │   Voice)     │  │   Store /  │  │   + Auth)    │ │
│  │  sonnet-4-6   │  │  Multilingual│  │   RAG)     │  │              │ │
│  └───────────────┘  └──────────────┘  └────────────┘  └──────────────┘ │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    IDBI Sandbox APIs                              │   │
│  │     Transactions  |  UPI Patterns  |  MSME Financials            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE (AWS — IDBI provided)                 │
│                                                                           │
│          EC2 / Lambda          S3 (assets)          CloudFront           │
│          ap-south-1            (portfolio files)    (CDN)                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Conversational Chat (Core Flow)

```
User types message
       │
       ▼
Frontend detects locale → sends { message, language, history } to POST /api/chat
       │
       ▼
language_service.detect_language(message)
  → auto-detects language from text (e.g. "हिंदी" detected as 'hi')
  → falls back to user.preferred_language if detection fails
       │
       ▼
rag_service.retrieve_context(message, language)
  → embeds query with Anthropic embeddings
  → queries Pinecone namespace: idbi-data-{lang}
  → returns top-3 relevant IDBI dataset chunks
       │
       ▼
language_service.get_system_prompt(language)
  → loads ai/system_prompts/wealth_advisor_{lang}.md
  → appends RAG context to system prompt
       │
       ▼
claude_service.stream_chat(message, history, language, context)
  → calls Claude API (claude-sonnet-4-6) with streaming
  → streams tokens back via SSE to frontend
       │
       ▼
Frontend renders streaming text
  → simultaneously sends text chunks to ElevenLabs
  → avatar speaks in the correct regional voice
       │
       ▼
Response complete → stored in conversation history
```

### 2. Language Switch Flow

```
User taps [हिंदी] in LanguageSwitcher
       │
       ▼
next-intl router: navigates /en/advisor → /hi/advisor
  → reloads messages/hi.json (all UI strings in Hindi)
  → locale stored in URL + localStorage
       │
       ▼
Next API call to /api/chat includes language: "hi"
  → language_service routes to wealth_advisor_hi.md prompt
  → Pinecone queries idbi-data-hi namespace
  → Claude responds in Hindi
  → ElevenLabs uses VOICE_MAP["hi"] voice ID
       │
       ▼
Avatar continues same conversation — new language, same context
```

### 3. Portfolio Analysis Flow

```
User uploads portfolio.csv
       │
       ▼
POST /api/portfolio (multipart form)
  → pandas reads CSV → converts to dict
       │
       ▼
claude_service.analyze_portfolio(portfolio_data, language)
  → Claude API called with portfolio data + system prompt
  → Returns structured analysis: allocation gaps, recommendations, risk alignment
       │
       ▼
Frontend renders analysis text + charts (Recharts)
```

---

## Multilingual Architecture

### Language Support Matrix

| Language | Code | UI Strings | Avatar Voice | System Prompt | RAG Namespace |
|---|---|---|---|---|---|
| English | `en` | ✅ | ✅ | ✅ | `idbi-data-en` |
| Hindi (हिंदी) | `hi` | ✅ | ✅ | ✅ Devanagari | `idbi-data-hi` |
| Marathi (मराठी) | `mr` | ✅ | ✅ | ✅ Devanagari | `idbi-data-mr` |
| Tamil (தமிழ்) | `ta` | ✅ | ✅ | ✅ Tamil script | `idbi-data-ta` |
| Bengali (বাংলা) | `bn` | ✅ | ✅ | ✅ Bengali script | `idbi-data-bn` |

### Why No Translation API?

Claude API (claude-sonnet-4-6) natively reads and writes all Indian languages at zero extra cost. Rather than translating English responses, we load language-specific system prompts that instruct Claude to respond in that language from the start — resulting in more natural, culturally appropriate phrasing.

### Language Detection Pipeline

```python
# backend/services/language_service.py

User input: "मेरे लिए SIP plan बनाओ"
      │
      ▼
langdetect.detect() → "hi"
      │
      ▼
LANGDETECT_MAP["hi"] → Language.HI
      │
      ├─→ get_system_prompt(Language.HI) → loads wealth_advisor_hi.md
      ├─→ get_voice_id(Language.HI)      → VOICE_MAP["hi"] → ElevenLabs voice ID
      └─→ RAG namespace                  → "idbi-data-hi"
```

### next-intl Route Structure

```
/en/advisor    → English UI, English avatar
/hi/advisor    → Hindi UI, Hindi avatar
/mr/dashboard  → Marathi UI, Marathi avatar
/ta/goals      → Tamil UI, Tamil avatar
/bn/insights   → Bengali UI, Bengali avatar
```

---

## RAG Pipeline

WealthSeva AI uses Retrieval-Augmented Generation to ground Claude's responses in actual IDBI banking data — preventing hallucinations on financial figures, product terms, and rates.

```
INDEXING (run once, ai/rag/index_datasets.py)
────────────────────────────────────────────
IDBI Synthetic Datasets (CSV/JSON)
  ├── transaction_patterns.csv
  ├── msme_financials.csv
  └── upi_patterns.csv
         │
         ▼
Chunking (500 tokens, 50 overlap)
         │
         ▼
Anthropic Embeddings (voyage-3)
         │
         ▼
Pinecone Upsert
  ├── namespace: idbi-data-en
  ├── namespace: idbi-data-hi  (translated chunks)
  ├── namespace: idbi-data-mr
  ├── namespace: idbi-data-ta
  └── namespace: idbi-data-bn


RETRIEVAL (every chat request)
────────────────────────────────────────────
User query
  │
  ▼
Embed query (voyage-3)
  │
  ▼
Pinecone query → namespace: idbi-data-{lang}
  │
  ▼
Top-3 chunks returned
  │
  ▼
Injected into Claude system prompt as context
  │
  ▼
Claude generates grounded response
```

---

## API Reference

### `POST /api/chat`
Stream a conversational response from Shreya (the AI wealth advisor).

**Request**
```json
{
  "message": "What SIP should I start for retirement?",
  "session_id": "user-123",
  "language": "hi",
  "history": [
    { "role": "user", "content": "My monthly income is ₹80,000" },
    { "role": "assistant", "content": "Great! Let me help you plan..." }
  ]
}
```

**Response** — `text/plain` stream (SSE)
```
रिटायरमेंट के लिए, मैं आपको ₹5,000/माह का SIP...
```
**Headers:** `X-Detected-Language: hi`

---

### `POST /api/risk-profile`
Score a completed risk quiz and return profile + allocation.

**Request**
```json
{
  "answers": [
    { "question_id": 1, "answer": "D" },
    { "question_id": 2, "answer": "C" },
    { "question_id": 3, "answer": "D" },
    { "question_id": 4, "answer": "B" },
    { "question_id": 5, "answer": "C" }
  ],
  "language": "en"
}
```

**Response**
```json
{
  "profile": "moderate",
  "score": 14,
  "explanation": "You seek balanced growth. A mix of equity and debt suits your profile.",
  "recommended_allocation": {
    "FD/Bonds": 30,
    "Debt MF": 30,
    "Equity MF": 40
  }
}
```

---

### `POST /api/portfolio`
Upload a portfolio CSV and receive AI analysis.

**Request** — `multipart/form-data`
```
file: portfolio.csv
language: hi
```

**Response**
```json
{
  "analysis": "आपका पोर्टफोलियो equity-heavy है (75%)...",
  "language": "hi"
}
```

---

### `GET /api/insights?language=ta`
Get today's market insights in the specified language.

**Response**
```json
{
  "insights": "இன்றைய சந்தை தகவல்கள்: 1. நிஃப்டி...",
  "language": "ta"
}
```

---

### `POST /api/goals`
Generate a savings and investment plan for financial goals.

**Request**
```json
{
  "goals": [
    {
      "name": "Retirement",
      "target_amount": 5000000,
      "target_date": "2045-01-01",
      "current_savings": 200000,
      "monthly_contribution": 5000
    }
  ],
  "language": "en"
}
```

---

### `GET /api/idbi/transactions?account_id=demo`
Fetch transaction data from IDBI sandbox (mock until sandbox access).

---

## Project Structure

```
wealthseva-ai/
│
├── .github/
│   └── workflows/
│       ├── ci.yml              # Lint + type-check + test on every PR
│       └── deploy.yml          # Deploy backend (AWS) + frontend (Vercel) on main push
│
├── frontend/                   # Next.js 14 App Router
│   ├── app/
│   │   └── [locale]/           # next-intl locale routing
│   │       ├── layout.tsx      # Root layout with NextIntlClientProvider
│   │       ├── page.tsx        # Redirects to /dashboard
│   │       ├── advisor/        # Avatar chat page
│   │       ├── dashboard/      # Portfolio + risk overview
│   │       └── goals/          # Goal planner page
│   ├── components/
│   │   ├── AvatarChat.tsx      # Streaming chat UI + ElevenLabs integration
│   │   ├── LanguageSwitcher.tsx# EN|HI|MR|TA|BN dropdown (key demo component)
│   │   ├── Navbar.tsx          # Top nav with language switcher
│   │   ├── PortfolioCard.tsx   # CSV upload + analysis display
│   │   ├── GoalPlanner.tsx     # Goal input form
│   │   └── RiskProfileBadge.tsx# Profile display chip
│   ├── messages/               # i18n translation files
│   │   ├── en.json
│   │   ├── hi.json             # Hindi
│   │   ├── mr.json             # Marathi
│   │   ├── ta.json             # Tamil
│   │   └── bn.json             # Bengali
│   ├── i18n.ts                 # next-intl config + locale list
│   ├── middleware.ts            # Locale routing middleware
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   └── package.json
│
├── backend/                    # FastAPI application
│   ├── main.py                 # App factory + CORS + router mounting
│   ├── routers/
│   │   ├── chat.py             # POST /api/chat (streaming)
│   │   ├── portfolio.py        # POST /api/portfolio
│   │   ├── risk.py             # POST /api/risk-profile
│   │   ├── insights.py         # GET /api/insights
│   │   ├── goals.py            # POST /api/goals
│   │   └── idbi.py             # GET /api/idbi/* (sandbox wrapper + mock)
│   ├── services/
│   │   ├── claude_service.py   # Claude API: streaming, portfolio analysis, goal planning
│   │   ├── language_service.py # Language detection, prompt routing, voice mapping
│   │   └── rag_service.py      # Pinecone retrieval (per-language namespaces)
│   ├── models/
│   │   └── schemas.py          # Pydantic models for all request/response types
│   └── requirements.txt
│
├── ai/
│   ├── system_prompts/         # Per-language Shreya persona prompts
│   │   ├── wealth_advisor_en.md
│   │   ├── wealth_advisor_hi.md    # Full Devanagari
│   │   ├── wealth_advisor_mr.md    # Full Devanagari (Marathi)
│   │   ├── wealth_advisor_ta.md    # Tamil script
│   │   └── wealth_advisor_bn.md    # Bengali script
│   └── rag/
│       └── index_datasets.py   # Index IDBI datasets into Pinecone namespaces
│
├── infra/                      # AWS infrastructure (CloudFormation/CDK)
├── docs/
│   └── demo_script.md          # August 13 Demo Day script (5 min)
├── demo/                       # Demo assets, backup video
├── scripts/
│   ├── setup.sh                # One-command local setup
│   └── create_github_repo.sh  # Creates GitHub repo + pushes (requires gh CLI)
│
├── CLAUDE.md                   # Claude Code context (read by claude automatically)
├── .env.example                # All required environment variables
├── .gitignore
└── README.md
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **AI/LLM** | Claude API `claude-sonnet-4-6` | Natively multilingual, streaming, tool use — zero translation cost |
| **Avatar** | ElevenLabs Conversational AI | Real-time lip sync + multilingual Indian voices |
| **Frontend** | Next.js 14 (App Router) | Fast, mobile-first, server components |
| **Styling** | TailwindCSS | Rapid UI — IDBI brand colours baked in |
| **i18n** | next-intl | Native App Router support, locale routing, SSR-safe |
| **Backend** | FastAPI + Python 3.12 | Async, streaming-native, clean for AI pipelines |
| **Language Detection** | langdetect | Lightweight, offline, 55 languages |
| **RAG** | LangChain + Pinecone | Per-language namespaces, semantic search over IDBI data |
| **Database** | Supabase (PostgreSQL) | Auth + user profiles + `preferred_language` field |
| **Cloud** | AWS (EC2/Lambda + S3) | Provided by IDBI Bank — production-grade |
| **CDN/Frontend** | Vercel (fallback) | Instant global deploys for frontend |
| **CI/CD** | GitHub Actions | Lint + test on PR; deploy on merge to `main` |
| **Dev Tool** | Claude Code | Primary coding assistant — reads `CLAUDE.md` for full context |

---

## Quick Start

```bash
# Clone
git clone https://github.com/omkar-platform-ai/wealthseva-ai.git
cd wealthseva-ai

# One-command setup (installs both frontend and backend)
bash scripts/setup.sh

# Add your API keys
nano .env                # Backend keys
nano frontend/.env.local # Frontend keys (NEXT_PUBLIC_BACKEND_URL, etc.)

# Start backend (Terminal 1)
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Start frontend (Terminal 2)
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — defaults to English, switch language top-right.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `ELEVENLABS_API_KEY` | ✅ | ElevenLabs API key |
| `ELEVENLABS_VOICE_EN/HI/MR/TA/BN` | ✅ | Voice IDs per language |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anon key |
| `PINECONE_API_KEY` | ✅ | Pinecone API key |
| `PINECONE_INDEX` | ✅ | Index name (e.g. `wealthseva-idbi`) |
| `IDBI_SANDBOX_BASE_URL` | After shortlist | IDBI Bank sandbox base URL |
| `IDBI_SANDBOX_API_KEY` | After shortlist | IDBI sandbox API key |
| `AWS_ACCESS_KEY_ID` | For deploy | AWS credentials (provided by IDBI) |
| `DEFAULT_LOCALE` | ✅ | Default app language (`en`) |
| `SUPPORTED_LOCALES` | ✅ | `en,hi,mr,ta,bn` |

See `.env.example` for the full list.

---

## Deployment

### Backend (AWS EC2)
```bash
# SSH into your IDBI-provided EC2 instance
ssh -i key.pem ec2-user@<EC2_IP>  # update with IDBI-provided IP after WEA-22 deployment

# Clone and run
git clone https://github.com/omkar-platform-ai/wealthseva-ai.git
cd wealthseva-ai/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend (Vercel)
```bash
cd frontend
npx vercel --prod
```

### Index IDBI Datasets into Pinecone
```bash
# After receiving datasets at orientation / shortlist phase
python ai/rag/index_datasets.py --dataset-dir ./data --languages en,hi,mr,ta,bn
```

---

## Branch Strategy

```
main  ← protected; only stable, demo-ready code
  └── dev  ← integration; merge features here first
        ├── feature/avatar-ui
        ├── feature/risk-profiler
        ├── feature/rag-pipeline
        ├── feature/multilingual-i18n
        ├── feature/multilingual-prompts
        └── feature/idbi-api-integration
```

Every feature → PR to `dev` → review → merge. Only `dev` → `main` when demo-ready.

---

## Hackathon

**Event:** IDBI Innovate 2026 &nbsp;|&nbsp; **Track:** 01 — Digital Wealth Management &nbsp;|&nbsp; **Team:** Omkar

**Timeline:**
- Jun 23 — Orientation (today)
- Jul 9 — Initial submission deadline
- Jul 21 — Shortlist announced; sandbox API access granted
- Jul 31 — Final submission
- Aug 13 — Demo Day & winner announcement

---

## License

MIT