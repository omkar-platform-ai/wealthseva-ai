# WealthSeva AI — Pre-Demo Checklist

Run this checklist top-to-bottom before every live demo. Each item must pass before presenting.

---

- [ ] **1. API keys set** — Open `backend/.env` and verify `ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` are all non-empty. The demo fails silently if any key is missing.

- [ ] **2. Backend running** — Run `cd backend && uvicorn main:app --reload --port 8000`. Confirm terminal shows `Application startup complete.` with no import errors.

- [ ] **3. Backend health check** — Open `http://localhost:8000/health` in the browser. Confirm JSON response `{"status":"ok"}` with HTTP 200.

- [ ] **4. Frontend running** — Run `cd frontend && npm run dev`. Confirm terminal shows `✓ Ready in <N>ms` with no build errors.

- [ ] **5. Browser open at /en/advisor** — Navigate to `http://localhost:3000/en/advisor`. Confirm Shreya's avatar frame loads and the text input is visible.

- [ ] **6. Sample CSV ready** — Verify `backend/tests/sample_portfolio.csv` exists and is non-empty. This file is required for the portfolio upload step.

- [ ] **7. Language switcher tested** — Click the language selector, switch from English to Hindi. Confirm the UI labels, chip suggestions, and avatar greeting all update within 2 seconds.

- [ ] **8. Demo mode verified** — Navigate to `http://localhost:3000/en/demo?demo=true`. Confirm it auto-runs all 5 advisory steps (greeting → risk quiz → portfolio → goals → market insights) without manual input.

- [ ] **9. Risk quiz flow** — On the advisor page, trigger the risk profiler by typing "what is my risk profile". Complete all 5 questions and confirm a risk category (Conservative / Moderate / Aggressive) is returned.

- [ ] **10. Portfolio upload tested** — Upload `backend/tests/sample_portfolio.csv` using the portfolio card. Confirm the allocation chart renders and rebalancing recommendations appear.

- [ ] **11. Goal planner tested** — Type "plan for my retirement" and confirm a SIP projection with monthly amount and timeline is returned.

- [ ] **12. Market insights tested** — Type "what are today's market insights" and confirm a language-appropriate market commentary is returned.

- [ ] **13. Hindi voice tested** — Switch to Hindi (`/hi/advisor`), type a greeting. Confirm the avatar speaks in Hindi voice (ElevenLabs audio plays).

- [ ] **14. Backup video ready** — Confirm `demo/backup_video_path.txt` contains the path or URL to a pre-recorded demo video. If live demo fails, this is the fallback.

- [ ] **15. Chrome DevTools closed** — Close DevTools panel (F12 / Cmd+Option+I). Open DevTools adds ~20% rendering overhead; keep it closed for performance during the live demo.

- [ ] **16. Battery / power** — Laptop is plugged in or battery is above 80%. Screen sleep is disabled. Presentation mode is on (notifications silenced).

- [ ] **17. Incognito check — repo is public** — Open an incognito window and navigate to `https://github.com/omkar-platform-ai/wealthseva-ai`. Confirm the repo is accessible without login.

- [ ] **18. No secrets in git log** — Run `git log --oneline -20` and confirm no commit messages reference API keys or secrets. Run the security scan: `grep -r "sk-ant-" --include="*.py" --include="*.ts" --include="*.json" .` — must return empty.

- [ ] **19. Clean commit history** — Confirm `git log --oneline -20` shows descriptive commit messages (no "fix fix fix" or "wip wip wip" noise). Judges may browse the commit history.

- [ ] **20. README live link confirmed** — Open `README.md` and confirm the repository URL, CI badge, and Quick Start commands are accurate. If a live deployed URL is available, confirm it returns HTTP 200.

---

*All 20 items checked? You are ready to demo. Good luck.*
