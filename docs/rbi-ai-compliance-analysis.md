# RBI AI Compliance Analysis — WealthSeva
**Prepared:** 2026-07-02
**For:** IDBI Innovate 2026 — Track 01: Digital Wealth Management
**Status:** Awaiting agent action — see [Actionable Tasks](#actionable-tasks) below

---

## Overview

India's AI regulation for the financial sector is advisory but tightening fast.
Three instruments are directly relevant to WealthSeva:

| Instrument | Status | Relevance |
|---|---|---|
| RBI FREE-AI Framework (Aug 2025) | Advisory — binding conversion expected via Master Directions | Primary governance framework for AI in Indian banking |
| RBI Draft Model Risk Management Guidance 2026 (Jun 2026) | Draft — binding soon | AI/ML model lifecycle, validation, third-party model risk |
| DPDP Act 2023 + Rules 2025 | Phase 1 live (Nov 2025); full compliance from May 2027 | Personal financial data processing, consent, cross-border flows |

FREE-AI is not yet law but IDBI Bank is an RBI-regulated entity running this
hackathon. Judges will evaluate WealthSeva against these principles. The RBI
has explicitly proposed a "tolerant supervisory stance" for first-time AI errors
in a sandboxed/innovation context — but only where firms demonstrate good
governance awareness. The goal for Demo Day (Aug 13) is not full production
compliance; it is demonstrable awareness + a credible production gap narrative.

---

## FREE-AI Framework: 7 Sutras

The FREE-AI framework is anchored in seven guiding principles every AI system
in the Indian financial sector is expected to express:

1. **Trust** — AI must not erode trust in the financial system
2. **People First** — customers must know when AI is involved in decisions;
   individuals retain the right to override AI determinations
3. **Innovation over Restraint** — responsible innovation is explicitly favoured
4. **Fairness and Equity** — no discriminatory outcomes by demographic or profile
5. **Accountability** — boards/management remain accountable for AI and third-party AI
6. **Understandable by Design (Explainability)** — AI decisions must be explainable
7. **Safety, Resilience and Sustainability** — robustness against failures and misuse

---

## Risk & Compliance Issues Mapped to WealthSeva Architecture

### 1. Third-Party LLM / Vendor Concentration Risk
**Severity for Demo Day:** Medium — expect the question, not a disqualifier
**Regulatory basis:** FREE-AI recommends indigenous sector-specific AI models
over global LLMs; flags data sovereignty and vendor concentration risks from
excessive reliance on external providers.

**WealthSeva exposure:** Core model is Claude (Anthropic, US). ElevenLabs
(US) handles avatar voice. Both are non-Indian providers.

**Production gap to acknowledge:** A production system would evaluate
indigenization — Sarvam AI, Krutrim, or IndiaAI Mission models — aligned with
the RBI's preference. For the hackathon, Claude was selected for multilingual
capability, API stability, and Anthropic's responsible AI commitments.

**No code change needed.** Prepare a talking point or deck slide.

---

### 2. Data Localisation & Cross-Border Data Flows
**Severity for Demo Day:** Medium — judges will likely probe; not a blocking issue
**Regulatory basis:** RBI mandates payment system data stored exclusively in
India. DPDP Act permits cross-border transfers subject to government notification
but RBI's localisation rules impose stricter constraints on financial data.
The decision rule: the strictest applicable regulation wins.

**WealthSeva exposure:** Portfolio holdings, risk profiles, goals, and
conversation history all flow to:
- Claude API (Anthropic — US-hosted by default)
- ElevenLabs (US)
- Pinecone (configurable; default US)

**Production mitigation story:**
- Claude → Vertex AI on Google Cloud Mumbai region (already partially in place
  via `shreya-backend-engineer`'s Vertex AI routing)
- Pinecone → deploy to `ap-south-1` (Mumbai) namespace
- ElevenLabs → assess Indian-region availability; flag as known gap

**No code change needed for hackathon.** Prepare a talking point.

---

### 3. AI Disclosure to Users — "You are talking to AI"
**Severity for Demo Day:** HIGH — directly tests FREE-AI Sutra 2; judges will check
**Regulatory basis:** FREE-AI Sutra 2 (People First): customers must know when
AI is involved in decisions. Customers must know when AI materially affects
outcomes. This is a named obligation even in the advisory framework.

**WealthSeva exposure:** Shreya presents as an avatar advisor with no current
on-screen or in-conversation disclosure that she is an AI system, not a licensed
human financial planner.

**Fix required (frontend + system prompt):**

**A. Opening system prompt addition** — add to all `ai/system_prompts/wealth_advisor_*.md`:
```
Always introduce yourself as: "I'm Shreya, an AI-powered wealth advisor.
My guidance is for informational purposes only and does not constitute
licensed financial advice. For significant investment decisions, please
consult a SEBI-registered financial advisor."
```

**B. UI disclaimer** — add a static one-line disclaimer below the chat input
in `frontend/app/[locale]/advisor/page.tsx`:
```
Shreya is an AI assistant. Responses are for guidance only, not licensed financial advice.
```

**Files to change:**
- `ai/system_prompts/wealth_advisor_en.md`
- `ai/system_prompts/wealth_advisor_hi.md`
- `ai/system_prompts/wealth_advisor_mr.md`
- `ai/system_prompts/wealth_advisor_ta.md`
- `ai/system_prompts/wealth_advisor_bn.md`
- `frontend/app/[locale]/advisor/page.tsx`
- `frontend/messages/en.json` (+ hi, mr, ta, bn) — add `"ai_disclaimer"` key

---

### 4. Human Override / Escalation Path
**Severity for Demo Day:** HIGH — FREE-AI requires human oversight for high-risk
AI applications; SIP recommendations and risk profiling qualify as high-risk
**Regulatory basis:** FREE-AI mandates comprehensive AI system governance
including human oversight for autonomous and high-risk applications. All
AI-enabled financial products must include AI-specific risk evaluations.

**WealthSeva exposure:** No "escalate to human advisor" or "talk to an IDBI
relationship manager" path exists anywhere in the current UI or API. Shreya
makes SIP recommendations and risk profile assessments autonomously with no
override mechanism.

**Fix required (frontend):**

Add an "Escalate / Talk to an Advisor" CTA in the chat UI — can be a mock
button for Demo Day but must be present. Suggested placement: below the
avatar panel, visible at all times during an active conversation.

```tsx
// In frontend/app/[locale]/advisor/page.tsx or a new component
<button className="text-idbi-blue border border-idbi-blue px-4 py-2 rounded-lg text-sm">
  {t('advisor.escalate_cta')}
</button>
```

Add i18n key `"advisor.escalate_cta"` to all five `messages/*.json`:
- EN: "Talk to an IDBI Advisor"
- HI: "IDBI सलाहकार से बात करें"
- MR: "IDBI सल्लागाराशी बोला"
- TA: "IDBI ஆலோசகரிடம் பேசுங்கள்"
- BN: "IDBI উপদেষ্টার সাথে কথা বলুন"

The button can open a modal with mock contact details for Demo Day. Flag
as "connect to live CRM/RM routing in production" in the pitch deck.

**Files to change:**
- `frontend/app/[locale]/advisor/page.tsx`
- `frontend/messages/en.json` (+ hi, mr, ta, bn)
- New component: `frontend/components/EscalateAdvisorModal.tsx` (optional)

---

### 5. User Consent Screen for Financial Data Processing
**Severity for Demo Day:** Medium — DPDP awareness signal; judges will notice absence
**Regulatory basis:** DPDP Act 2023 — WealthSeva is a Data Fiduciary processing
personal financial data (portfolio, goals, risk profile, conversation history).
Even though substantive DPDP compliance doesn't go live until May 2027,
judges from IDBI Bank — itself a Data Fiduciary — will recognise the gap.

**WealthSeva exposure:** No consent screen or consent acknowledgement exists
at onboarding. Users share portfolio data and risk quiz answers with no
explicit consent capture.

**Fix required (frontend):**

Add a consent gate at first-use / onboarding — a single checkbox modal before
the advisor chat becomes active:

```
"I consent to WealthSeva processing my financial information
(portfolio holdings, risk profile, financial goals, and conversation
history) to provide personalised wealth guidance. Data is used solely
for this purpose and is not shared with third parties."
[ ] I agree    [Continue]
```

Can be stored in `localStorage` for the hackathon demo (no backend needed).
Flag in the pitch as "production system would store consent with timestamp in
Supabase against user ID."

**Files to change:**
- New component: `frontend/components/ConsentGate.tsx`
- `frontend/app/[locale]/advisor/page.tsx` — gate the advisor UI behind consent
- `frontend/messages/en.json` (+ hi, mr, ta, bn) — add consent string keys

---

### 6. LLM Hallucination in Financial Figures
**Severity for Demo Day:** HIGH — IDBI judges will specifically test this
**Regulatory basis:** FREE-AI mandates AI models be regularly tested for bias,
model degradation, and unexplained behavior. "AI did it" is not a valid defence
for a discriminatory or incorrect financial outcome. Draft Model Risk Management
Guidance 2026 requires documented validation of AI model outputs.

**WealthSeva exposure:** Shreya can generate specific financial figures (SIP
returns, NAV numbers, expected yield) from Claude's parametric memory, which
is ungrounded in current Indian market data and prone to confident hallucination.
A fabricated "this fund returned 34% last year" statement in front of IDBI judges
is a critical failure point.

**Fix required (backend + system prompt):**

**A. System prompt guardrail** — add to all `ai/system_prompts/wealth_advisor_*.md`:
```
FINANCIAL FIGURES RULE: Never state specific past return percentages, NAV
values, or current prices from memory. Always retrieve these from the
knowledge base. If no grounded data is available, say: "I don't have
current figures for this — please check your fund's factsheet or AMFI
data." Specific ₹ SIP projections are allowed only using the calculator
endpoint, not from memory.
```

**B. RAG enforcement** — WEA-5 (Pinecone RAG pipeline) must be completed
and all financial figure retrieval must go through `rag_service.py`, not
direct Claude generation. This is the primary technical fix for this risk.

**C. SIP figures via calculator** — WEA-4 (SIP calculator endpoint) provides
formula-based projections. Route all SIP ₹ figure generation through this
endpoint. Shreya should call `/api/sip-calculator` and present the result,
never generate the number from parametric memory.

**Files to change:**
- `ai/system_prompts/wealth_advisor_en.md` (+ hi, mr, ta, bn)
- `backend/services/claude_service.py` — enforce RAG retrieval before
  generating financial responses (WEA-5 dependency)
- WEA-4 and WEA-5 tickets are the underlying blockers — prioritise these

---

### 7. Model Risk Documentation (Production Roadmap)
**Severity for Demo Day:** Low — not a blocker, but worth a pitch deck slide
**Regulatory basis:** RBI Draft Model Risk Management Guidance 2026 requires
risk-based model tiering, lifecycle management, validation evidence, and
continuous oversight for AI/ML models — including specific principles for
third-party models.

**No code change needed for hackathon.** Add one slide to the pitch deck
under "Production Readiness" covering:
- Model card for Claude (version pinned: `claude-sonnet-4-6`, known limitations,
  validation approach)
- Risk tier: HIGH (financial advice, direct customer impact)
- Monitoring plan: response logging, hallucination detection, periodic human audit
- Change management: version pinning, no silent model updates in production

---

## Actionable Tasks

The following tasks are scoped for agent pickup. Assign based on the file
paths involved — frontend tasks to `shreya-frontend-engineer`, system prompt
tasks to `shreya-utility-engineer`.

### TASK A — AI Disclosure (Utility + Frontend)
**Owner:** shreya-utility-engineer (system prompts) + shreya-frontend-engineer (UI)
**Effort:** ~2 hours combined
**Priority:** HIGH — do before any other compliance fix

1. Add opening AI disclosure to all five `ai/system_prompts/wealth_advisor_*.md`
   (see exact wording in Issue 3 above — translate appropriately for hi/mr/ta/bn)
2. Add `"ai_disclaimer"` i18n key to all five `frontend/messages/*.json`
3. Add one-line static disclaimer below chat input in
   `frontend/app/[locale]/advisor/page.tsx`

---

### TASK B — Human Escalation CTA (Frontend)
**Owner:** shreya-frontend-engineer
**Effort:** ~3 hours
**Priority:** HIGH

1. Add "Talk to an IDBI Advisor" button to the advisor page (see exact
   placement and i18n strings for all 5 languages in Issue 4 above)
2. Button opens a simple modal — mock contact details acceptable for Demo Day
3. Add `frontend/components/EscalateAdvisorModal.tsx`
4. Add i18n keys to all five `messages/*.json`

---

### TASK C — Consent Gate (Frontend)
**Owner:** shreya-frontend-engineer
**Effort:** ~2 hours
**Priority:** Medium

1. Create `frontend/components/ConsentGate.tsx` — checkbox modal
   (see exact copy in Issue 5 above; translate for all 5 languages)
2. Gate `frontend/app/[locale]/advisor/page.tsx` behind consent check
3. Store consent state in `localStorage` (key: `wealthseva_consent_v1`)
4. Add consent string i18n keys to all five `messages/*.json`

---

### TASK D — Hallucination Guardrails (Utility)
**Owner:** shreya-utility-engineer
**Effort:** ~1 hour (prompt update only; RAG/calculator integration is WEA-4/WEA-5)
**Priority:** HIGH

1. Add FINANCIAL FIGURES RULE to all five `ai/system_prompts/wealth_advisor_*.md`
   (see exact wording in Issue 6 above — translate for hi/mr/ta/bn)
2. Verify the rule is reflected in the existing `backend/services/claude_service.py`
   system prompt loading logic — no structural change needed, just confirm the
   prompt file is loaded correctly

---

## Production Gap Summary (for Pitch Deck)

Use this table in the "Responsible AI & Compliance" slide:

| Gap | Hackathon Status | Production Fix |
|---|---|---|
| Third-party LLM (Claude/ElevenLabs) | Acknowledged; Claude chosen for multilingual capability | Evaluate Sarvam AI / Krutrim; Claude on Vertex AI Mumbai |
| Data localisation | US-hosted services in prototype | Vertex AI Mumbai + Pinecone ap-south-1 |
| AI disclosure | ✅ Implemented (Task A) | Full DPDP-compliant notice |
| Human override | ✅ Mock escalation button (Task B) | Live RM routing via IDBI CRM |
| User consent | ✅ Consent gate (Task C) | Timestamped consent in Supabase |
| Hallucination guardrails | ✅ Prompt guardrails (Task D) + RAG (WEA-5) | Model monitoring + audit log |
| Model risk documentation | Pitch deck slide | Full model card + risk tier + validation |

---

## References

- RBI FREE-AI Committee Report: https://rbidocs.rbi.org.in/rdocs/PublicationReport/Pdfs/FREEAIR130820250A24FF2D4578453F824C72ED9F5D5851.PDF
- RBI Draft Model Risk Management Guidance 2026 (Jun 2026): https://www.indiancooperative.com/banks/rbi-proposes-ai-and-model-risk-management-norms-for-co-op-banks/
- DPDP Act 2023 + Rules 2025: https://www.dlapiperdataprotection.com/?t=law&c=IN
- KPMG FREE-AI Analysis: https://kpmg.com/in/en/insights/2025/09/rbis-free-ai-committee-report-in-the-financial-sector.html
- Chambers & Partners FREE-AI Overview: https://chambers.com/articles/a-framework-for-using-ai-in-the-indian-financial-sector