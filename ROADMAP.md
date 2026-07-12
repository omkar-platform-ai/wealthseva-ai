# WealthSeva AI — Product Roadmap

> What we've shipped for the demo — and where WealthSeva goes next.
> Timeline follows our IDBI Innovate 2026 build plan (Jul 9 → Jul 31 → Aug 13) and may evolve.
> A live, localized version of this roadmap is in the app at **`/roadmap`** (all 5 languages).

---

## ✅ Shipped — Demo (Jul 9)

The initial submission demonstrates the three differentiators end-to-end.

| Feature | What it does |
|---|---|
| **Voice-first vernacular advisor** | Shreya speaks and listens in all 5 languages (Sarvam Bulbul v3 TTS primary, ElevenLabs fallback + Web Speech STT, browser fallback). |
| **"Why this advice?" transparency** | Every recommendation exposes its data → rule → deterministic calculation. Server-side math, never LLM arithmetic. RBI FREE-AI aligned (consent gate, AI disclosure, human-escalation CTA). |
| **Money Moments nudges** | Proactive behavioral alerts — idle-cash detection and goal-drift, each with a collapsible "why" trace and a deep-link into chat. |
| **Personalized, grounded answers** | Advice grounded in the customer's IDBI account snapshot plus a multilingual RAG knowledge base — factual, hallucination-resistant. |
| **Switch language mid-chat** | Change language at any point; the conversation continues without losing context, and Shreya replies (and speaks) in the detected language. |

## 🚧 In progress — Final (Jul 31)

| Feature | What it does | Ref |
|---|---|---|
| **CAS statement analysis** | Upload a real Consolidated Account Statement (CDSL/NSDL demat + CAMS/KFintech mutual-fund SOA) for instant AI analysis — password-protected PDFs, PII-safe. | [WEA-72](https://github.com/omkar-platform-ai/wealthseva-ai) · demo slice [WEA-73] |
| **Saved history & goals** | Conversations and goals persist across sessions (Supabase). | — |
| **Deeper multilingual search** | Semantic retrieval tuned per language (multilingual embeddings), layered over today's keyword knowledge base. | — |
| **More proactive guards** | Panic-selling guards and SIP-shortfall alerts added to the Money Moments feed. | — |
| **Government scheme advisor** | Compare NPS, Sukanya Samriddhi, SCSS, PPF, NSC and RBI bonds against a customer's goals and eligibility. Advisory only — no execution; recommendations route to the existing IDBI scheme (branch / NPS POP / SSY-PPF counter), not a new transaction rail. Rate table is date-stamped and needs a quarterly refresh process (small-savings rates are revised by the Finance Ministry every quarter). | [WEA-79](https://github.com/omkar-platform-ai/wealthseva-ai) |
| **Capital gains & tax view** | LTCG/STCG estimate on the customer's mutual fund and digital gold holdings, computed with the same server-side deterministic pattern used for Risk and Goals ("Why this number?") — never LLM arithmetic. Deliberately scoped to the two asset classes already in MVP; explicitly not a general tax-filing or ITR tool, and does not model loss carry-forward or pre-2018 equity grandfathering. | [WEA-80](https://github.com/omkar-platform-ai/wealthseva-ai) |

## 🔭 Planned — Vision (Aug 13 & beyond)

| Feature | What it does |
|---|---|
| **Live IDBI accounts** | Real account data through a live / mock toggle (IDBI sandbox access expected ~Jul 22). |
| **Works in low connectivity** | Pre-cached audio and offline fallbacks for branch and rural use. |
| **In-app & WhatsApp** | Embedded inside IDBI mobile banking and delivered over WhatsApp. |
| **More Indian languages** | Telugu, Gujarati, Kannada and beyond. |
| **Foreign investment guide** | Explains LRS remittance limits, the 20% TCS above ₹7L, and US equity capital-gains taxation. Informational only — deliberately not a transactable asset class; IDBI has no existing overseas-broker relationship to execute against, and the target user (vernacular-first, advisor-scarce segment) is not primarily a foreign-equity investor. | [WEA-81](https://github.com/omkar-platform-ai/wealthseva-ai) |

---

*The three differentiators — voice-first vernacular advisory, explainable compliance-native recommendations, and proactive "Money Moments" — are the throughline across every phase.*
