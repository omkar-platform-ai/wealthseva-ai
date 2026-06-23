# WealthSeva AI 🏦

> AI-powered multilingual wealth advisor avatar for IDBI Bank — built for IDBI Innovate 2026

[![CI](https://github.com/your-username/wealthseva-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/wealthseva-ai/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What is WealthSeva AI?

WealthSeva AI is an **avatar-based, conversational wealth management assistant** that integrates into IDBI Bank's mobile banking app. It delivers personalized, AI-powered financial guidance to every customer — in their preferred language.

**Supported Languages:** English | हिंदी | मराठी | தமிழ் | বাংলা

---

## Features

- 🤖 **AI Avatar Advisor** — Real-time talking avatar powered by ElevenLabs + Claude API
- 📊 **Risk Profiler** — 5-question onboarding → Conservative / Moderate / Aggressive
- 💼 **Portfolio Analyzer** — Upload portfolio → AI analysis + recommendations
- 🎯 **Goal Planner** — Retirement, house, education — AI-generated savings plans
- 🌐 **Multilingual** — Full UI + avatar voice in 5 Indian languages
- 📈 **Market Insights** — Daily personalized commentary via Claude
- 🏦 **IDBI Sandbox APIs** — Real transaction + UPI + MSME data integration

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TailwindCSS, TypeScript, next-intl |
| Backend | FastAPI, Python 3.12, LangChain |
| AI/LLM | Claude API (claude-sonnet-4-6) |
| Avatar | ElevenLabs Conversational AI |
| Vector DB | Pinecone |
| Database | Supabase (PostgreSQL) |
| Cloud | AWS (EC2/Lambda + S3) |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-username/wealthseva-ai.git
cd wealthseva-ai

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload

# 3. Frontend (new terminal)
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
```

Open http://localhost:3000

---

## Environment Variables

Copy `.env.example` to `.env` (backend) and `.env.local` (frontend) and fill in values.

---

## Project Structure

```
wealthseva-ai/
├── frontend/          # Next.js 14 app (multilingual)
├── backend/           # FastAPI backend + Claude API
├── ai/                # System prompts + RAG indexing
├── infra/             # AWS CloudFormation templates
├── docs/              # Architecture, API reference, demo script
├── scripts/           # Setup and utility scripts
└── demo/              # Demo assets and backup video
```

---

## Hackathon

**IDBI Innovate 2026** | Track 01: Digital Wealth Management | Team: Omkar

---

## License

MIT
