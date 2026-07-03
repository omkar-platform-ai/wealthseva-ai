# WealthSeva AI

> WealthSeva AI — Avatar-based multilingual wealth advisor for IDBI Bank customers

[![Live Demo](https://img.shields.io/badge/Live%20Demo-WealthSeva-brightgreen)](https://github.com/omkar-platform-ai/wealthseva-ai)
[![CI](https://github.com/omkar-platform-ai/wealthseva-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/omkar-platform-ai/wealthseva-ai/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

**Supported Languages:** English &nbsp;|&nbsp; हिंदी &nbsp;|&nbsp; मराठी &nbsp;|&nbsp; தமிழ் &nbsp;|&nbsp; বাংলা

---

## What Is WealthSeva

India's banking sector serves 500M+ customers, yet 70% prefer to engage with financial services in their vernacular language. Wealth advisory — SIP planning, portfolio analysis, goal setting — remains practically inaccessible for most retail customers because it is delivered in English through branch appointments or generic templated tools. The result is a nation of savers who lack the personalized guidance needed to become investors.

WealthSeva AI closes this gap with **Shreya**, an AI-powered avatar advisor who speaks fluently in English, Hindi, Marathi, Tamil, and Bengali. Embedded inside IDBI Bank's existing mobile app, Shreya delivers personalized financial guidance grounded in the customer's actual transaction history, portfolio composition, and declared goals — in the language they think in. Every response is retrieved from a RAG pipeline seeded with IDBI's own datasets, not generated from memory, so figures and recommendations stay factual and hallucination-resistant.

The key differentiator is the combination that has never been delivered together in Indian banking: real-time avatar voice synthesis (ElevenLabs) in five vernacular Indian languages, retrieval-augmented generation over IDBI's own data, and RBI FREE-AI compliant AI disclosure — all without a single incremental headcount. The system scales from one customer to 500 million through the existing mobile banking surface.

---

## Table of Contents

- [What Is WealthSeva](#what-is-wealthseva)
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Local Development Setup](#local-development-setup)
- [Demo Mode](#demo-mode)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [RBI Compliance Note](#rbi-compliance-note)
- [Project Structure](#project-structure)
- [Hackathon Context](#hackathon-context)

---

## Features

| Feature | Description |
|---|---|
| **AI Avatar Advisor** | Real-time talking avatar (ElevenLabs) powered by Claude via Amazon Bedrock — Shreya, your IDBI wealth advisor |
| **Multilingual** | Full UI + avatar voice in 5 Indian languages; auto-detects language from user input |
| **Risk Profiler** | 5-question onboarding quiz → Conservative / Moderate / Aggressive profile + recommended allocation |
| **Portfolio Analyzer** | Upload CSV → Claude analysis → actionable rebalancing recommendations |
| **Goal Planner** | Set goals (retirement, house, education) → AI-generated SIP + savings plan |
| **Market Insights** | Daily personalized market commentary in the user's language |
| **RAG-Grounded Responses** | Retrieves relevant IDBI dataset context before every Claude call — factual, hallucination-resistant |
| **RBI FREE-AI Compliant** | Mandatory AI disclosure, DPDP consent gate, human escalation CTA on distress signals |

---

## Architecture Overview

WealthSeva is a decoupled two-service architecture: a **Next.js 14** frontend and a **FastAPI** backend communicating over a well-defined REST/SSE API. Claude inference runs through **Amazon Bedrock** (Mumbai region, `ap-south-1`; IAM role auth on EC2 — no API key needed). The RAG pipeline retrieves context from **Pinecone** per-language namespaces before every Claude call. User sessions and profiles are stored in **Supabase**. Avatar voice synthesis runs through **ElevenLabs**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Next.js 14 Frontend                                  │
│   Avatar UI (ElevenLabs)  ·  Dashboard  ·  Language Switcher EN|HI|MR|TA|BN │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │  HTTP / SSE
┌──────────────────────────────────▼──────────────────────────────────────┐
│                  FastAPI Backend (Python 3.12, ap-south-1)               │
│  /api/chat  ·  /api/portfolio  ·  /api/risk-profile  ·  /api/goals      │
│  claude_service  ·  language_service  ·  rag_service  ·  risk_service   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
        Amazon Bedrock (Claude)  ·  ElevenLabs  ·  Pinecone  ·  Supabase
```

---

## Local Development Setup

Judges and reviewers should be able to run the full stack locally in under 15 minutes.

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Node.js | 20+ | https://nodejs.org |
| Python | 3.12 | https://python.org |
| npm | bundled with Node | — |

**API keys needed:**

| Service | Purpose | Where to get it |
|---|---|---|
| AWS (Bedrock) | Claude inference | IAM user with `bedrock:InvokeModel` permission on `ap-south-1`; on EC2 use IAM role (no key needed) |
| ElevenLabs | Avatar voice | https://elevenlabs.io — create 5 voices (EN/HI/MR/TA/BN), copy their voice IDs |
| Supabase | User profiles | https://supabase.com — new project → Settings > API |
| Pinecone | RAG vector store | https://pinecone.io — optional; mock fallback used if key is absent |

---

### Step 1 — Clone and scaffold

```bash
git clone https://github.com/omkar-platform-ai/wealthseva-ai.git
cd wealthseva-ai

# Creates backend venv, installs deps, copies .env.example → .env and frontend/.env.local
bash scripts/setup.sh
```

---

### Step 2 — Fill in backend `.env`

Open `.env` and set the values below. Everything else can stay at its default.

```bash
# Amazon Bedrock — Claude (ap-south-1)
BEDROCK_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-6

# ElevenLabs — paste voice IDs from your ElevenLabs project
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_EN=your_english_voice_id
ELEVENLABS_VOICE_HI=your_hindi_voice_id
ELEVENLABS_VOICE_MR=your_marathi_voice_id
ELEVENLABS_VOICE_TA=your_tamil_voice_id
ELEVENLABS_VOICE_BN=your_bengali_voice_id

# Supabase — Project Settings > API
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Pinecone — optional (app mocks context if key is absent)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
PINECONE_INDEX=wealthseva-idbi

# AWS credentials for local Bedrock access (not needed on EC2 with IAM role)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=ap-south-1

# App config — defaults work for local dev
APP_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
DEFAULT_LOCALE=en
SUPPORTED_LOCALES=en,hi,mr,ta,bn
```

---

### Step 3 — Start the backend

```bash
cd backend
source venv/bin/activate       # Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Confirm it is running:

```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"wealthseva-ai-backend"}
```

---

### Step 4 — Configure frontend

Edit `frontend/.env.local` (created by `setup.sh`) and set:

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

### Step 5 — Start the frontend

Open a second terminal:

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000/en/advisor](http://localhost:3000/en/advisor). Use the language switcher (top-right) to switch to हिंदी, मराठी, தமிழ், or বাংলা.

> **Note:** The backend must be running before the frontend makes API calls. If you see CORS errors, confirm `NEXT_PUBLIC_BACKEND_URL` matches the backend's listen address.

---

## Demo Mode

A fully scripted 5-step walkthrough that requires no backend API keys — ideal for judges evaluating the prototype.

**URL:** [http://localhost:3000/en/demo](http://localhost:3000/en/demo)

| Step | What you see |
|---|---|
| **1 — Meet Ramesh** | Introduction to a sample IDBI customer profile |
| **2 — Risk Quiz** | The 5-question risk profiling quiz, answered interactively |
| **3 — Portfolio** | Ramesh's sample portfolio with live Recharts visualization |
| **4 — Goal Plan** | AI-generated retirement savings plan |
| **5 — Hindi SIP** | Shreya responds in Hindi: ₹5,000/month SIP recommendation for HDFC Flexi Cap Fund |

A step progress bar tracks completion (Step N of 5). No API keys or backend connection is required for the scripted demo steps.

---

## Running Tests

### Backend

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Covers: `test_health`, `test_chat`, `test_risk`, `test_portfolio`, `test_goals`, `test_idbi`, `test_rag_insights`.

### Frontend

```bash
cd frontend
npm run type-check    # TypeScript — zero errors expected
npm run lint          # ESLint
npm run build         # Production build (catches missing env vars and import errors)
```

---

## Deployment

The live demo runs on **AWS EC2** (backend, `ap-south-1`) + **Vercel** (frontend). See `docs/solution_document.md` for the full architecture write-up.

### Backend (AWS EC2)

```bash
ssh -i key.pem ec2-user@<EC2_IP>

git clone https://github.com/omkar-platform-ai/wealthseva-ai.git
cd wealthseva-ai/backend
pip install -r requirements.txt
# On EC2, Bedrock auth uses the instance IAM role — no AWS_ACCESS_KEY_ID needed
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend (Vercel)

```bash
cd frontend
npx vercel --prod
# Set NEXT_PUBLIC_BACKEND_URL to your EC2 backend URL in the Vercel dashboard
```

### Index IDBI Datasets (post-shortlist)

```bash
# After receiving IDBI sandbox datasets at shortlist phase
python ai/rag/index_datasets.py --dataset-dir ./data --languages en,hi,mr,ta,bn
```

---

## RBI Compliance Note

WealthSeva is designed with awareness of the **RBI FREE-AI Framework** and the **DPDP Act 2023**. Every system prompt opens with a mandatory AI disclosure identifying Shreya as an AI assistant. A FINANCIAL FIGURES RULE blocks memory-based NAV, return percentage, or price claims — grounded retrieval from the RAG pipeline is required for any specific figure. A DPDP-compliant consent gate is presented on first use, and human escalation CTAs surface automatically on financial distress signals (loan defaults, credit limit breaches).

See `docs/rbi-ai-compliance-analysis.md` for the full compliance mapping across all seven RBI FREE-AI requirements.

---

## Project Structure

```
wealthseva-ai/
├── .github/workflows/
│   ├── ci.yml              # Lint + type-check + test on every PR
│   └── deploy.yml          # Deploy on main push
├── frontend/               # Next.js 14 App Router
│   ├── app/[locale]/       # next-intl locale routing (en/hi/mr/ta/bn)
│   │   ├── advisor/        # Avatar chat page
│   │   ├── dashboard/      # Portfolio + risk overview
│   │   ├── demo/           # Scripted 5-step judge demo (no API keys needed)
│   │   └── goals/          # Goal planner
│   ├── components/         # AvatarChat, LanguageSwitcher, PortfolioCard, GoalPlanner...
│   ├── messages/           # i18n strings: en.json hi.json mr.json ta.json bn.json
│   ├── i18n.ts
│   ├── middleware.ts        # Locale routing
│   └── package.json
├── backend/                # FastAPI + Python 3.12
│   ├── main.py             # App factory, CORS, rate limiting
│   ├── routers/            # chat, portfolio, risk, insights, goals, idbi
│   ├── services/
│   │   ├── claude_service.py    # Bedrock streaming, portfolio analysis, goal planning
│   │   ├── language_service.py  # Language detection, prompt routing, voice mapping
│   │   └── rag_service.py       # Pinecone retrieval (per-language namespaces)
│   ├── models/schemas.py        # Pydantic models
│   ├── tests/                   # pytest suite (7 files)
│   └── requirements.txt
├── ai/
│   ├── system_prompts/     # wealth_advisor_{en,hi,mr,ta,bn}.md — RBI-compliant prompts
│   └── rag/
│       └── index_datasets.py
├── docs/
│   ├── rbi-ai-compliance-analysis.md
│   ├── solution_document.md
│   └── demo_script.md
├── scripts/
│   └── setup.sh            # One-command local setup
├── .env.example            # All required env vars (copy to .env)
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI/LLM | Amazon Bedrock — `claude-sonnet-4-6` (ap-south-1) |
| Avatar | ElevenLabs Conversational AI — multilingual Indian voices |
| Frontend | Next.js 14 (App Router), TailwindCSS, Recharts |
| i18n | next-intl — 5 locale routes, SSR-safe |
| Backend | FastAPI, Python 3.12, uvicorn |
| Language detection | langdetect (offline, 55 languages) |
| RAG | LangChain + Pinecone (per-language namespaces) |
| Database | Supabase (PostgreSQL + Auth) |
| Cloud | AWS EC2 ap-south-1 (backend) + Vercel (frontend) |
| CI/CD | GitHub Actions — lint + test on PR; deploy on main |

---

## Hackathon Context

**Event:** IDBI Innovate 2026 &nbsp;|&nbsp; **Track:** 01 — Digital Wealth Management

**Team:** Omkar Sonawane

**Timeline:**
- Jun 23 — Orientation
- **Jul 9 — Initial submission deadline (Hack2skill)**
- Jul 21 — Shortlist announced; sandbox API access granted
- Jul 31 — Final submission
- **Aug 13 — Demo Day & winner announcement**

---

## License

MIT
