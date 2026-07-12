# Handoff: `/insights` disclaimer-in-first-card fix

## Task
Fix a GUI bug on the `/insights` page (live: https://main.d13rdix674q29k.amplifyapp.com/insights).
The first "market insight" card was displaying Shreya's self-introduction / disclaimer text instead of an actual market insight:

> "I'm Shreya, an AI-powered wealth advisor. My guidance is for informational purposes only and does not constitute licensed financial advice. For significant investment decisions, please consult a SEBI-registered financial advisor."

## Root Cause
- `ai/system_prompts/wealth_advisor_en.md` instructs the model: *"Always introduce yourself as: 'I'm Shreya, an AI-powered wealth advisor...'"*.
- The `/api/insights` endpoint (`backend/routers/insights.py` → `generate_market_insights` in `backend/services/claude_service.py`) reuses that same system prompt.
- Claude obediently prepended its self-introduction as the first element of the JSON insights array.
- The frontend (`frontend/app/[locale]/insights/page.tsx`) is innocent — it renders `data.insights` verbatim.

## Fix
Both changes are in `backend/services/claude_service.py`, function `generate_market_insights`:

1. **Root cause / cross-language fix** — strengthened the insights `user_prompt` to explicitly instruct: return exactly 3 standalone insights, and *"Do NOT introduce yourself, and do NOT include any disclaimer, preamble, or the 'I'm Shreya' self-introduction"*.
2. **Defensive net (EN)** — after JSON parsing, filter out any array element whose lowercased text contains one of `("i'm shreya", "informational purposes", "sebi-registered")`, with an `or insights` fallback so it never returns an empty list.

## Verification Done
- `python3 -c "import ast; ast.parse(...)"` — syntax OK.
- Unit-tested the filter against the exact 4-element array from the prod screenshot: disclaimer removed; 3 real insights (inflation, SEBI expense ratios, FPI inflows) remain.

## NOT Done / Next Steps
- **Uncommitted.** Changes are UNCOMMITTED on branch `main`, in `backend/services/claude_service.py`. Need to commit + deploy.
- **Deploy is serverless.** Prod runs on a Lambda Function URL (per `CLAUDE.md`). Deploy the new backend, then confirm.
- **Cache TTL.** Prod insights are cached with a 60s TTL (`_INSIGHTS_CACHE_TTL`), so the stale disclaimer will clear ~60s after the new backend is deployed.
- **No live re-verification.** No prod re-verification was done (would require redeploy) — verify on the live `/insights` page after deploy.
- **Commit message preference.** Commit messages must NOT include a `Co-Authored-By` line.
