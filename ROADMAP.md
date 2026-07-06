# WealthSeva AI — Product Roadmap

> What we've shipped for the demo — and where WealthSeva goes next.
> Timeline follows our IDBI Innovate 2026 build plan (Jul 9 → Jul 31 → Aug 13) and may evolve.
> A live, localized version of this roadmap is in the app at **`/roadmap`** (all 5 languages).

---

## ✅ Shipped — Demo (Jul 9)

The initial submission demonstrates the three differentiators end-to-end.

| Feature | What it does |
|---|---|
| **Voice-first vernacular advisor** | Shreya speaks and listens in all 5 languages (ElevenLabs TTS + Web Speech STT, browser fallback). |
| **"Why this advice?" transparency** | Every recommendation exposes its data → rule → deterministic calculation. Server-side math, never LLM arithmetic. RBI FREE-AI aligned (consent gate, AI disclosure, human-escalation CTA). |
| **Money Moments nudges** | Proactive behavioral alerts — idle-cash detection and goal-drift, each with a collapsible "why" trace and a deep-link into chat. |
| **Personalized, grounded answers** | Advice grounded in the customer's IDBI account snapshot plus a multilingual RAG knowledge base — factual, hallucination-resistant. |
| **Switch language mid-chat** | Change language at any point; the conversation continues without losing context, and Shreya replies (and speaks) in the detected language. |

## 🚧 In progress — Final (Jul 31)

| Feature | What it does | Ref |
|---|---|---|
| **CAS statement analysis** | Upload a real Consolidated Account Statement (CDSL/NSDL demat + CAMS/KFintech mutual-fund SOA) for instant AI analysis — password-protected PDFs, PII-safe. | [WEA-72](https://github.com/omkar-platform-ai/wealthseva-ai) · demo slice [WEA-73] |
| **Saved history & goals** | Conversations and goals persist across sessions (Supabase). | — |
| **Deeper multilingual search** | Semantic retrieval (Titan embeddings) tuned per language, with per-language namespaces. | — |
| **More proactive guards** | Panic-selling guards and SIP-shortfall alerts added to the Money Moments feed. | — |

## 🔭 Planned — Vision (Aug 13 & beyond)

| Feature | What it does |
|---|---|
| **Live IDBI accounts** | Real account data through a live / mock toggle (IDBI sandbox access expected ~Jul 22). |
| **Works in low connectivity** | Pre-cached audio and offline fallbacks for branch and rural use. |
| **In-app & WhatsApp** | Embedded inside IDBI mobile banking and delivered over WhatsApp. |
| **More Indian languages** | Telugu, Gujarati, Kannada and beyond. |

---

*The three differentiators — voice-first vernacular advisory, explainable compliance-native recommendations, and proactive "Money Moments" — are the throughline across every phase.*
