# Development Plan — Renovation Estimate Calculator

Companion file to `project.md` (master prompt). Drop this in the repo root or `.cursor/rules/` as `DEVELOPMENT_PLAN.md`. Work through phases in order — do not start a phase until the previous one's "Definition of done" is met. Each phase should be a small, reviewable set of commits, not one giant dump.

**Stack:** Python, Flask, Jinja2, Tailwind CSS (standalone CLI), PostgreSQL (SQLite for local dev), aiogram (bot, later phase).

**Non-negotiable rule across all phases:** no live web search or agentic research on the user-request path. Price data is always read from the local DB, populated offline. See `project.md` for the full rationale.

---

## Phase 0 — Project scaffolding

**Goal:** empty but runnable skeleton, nothing functional yet.

- [x] Flask app factory pattern (`app/__init__.py`, `create_app()`)
- [x] `.env` handling (python-dotenv), `.env.example` committed, real `.env` gitignored
- [x] SQLite for local dev (`DATABASE_URL` config flag; Postgres swap is a URL change, no code change needed)
- [x] Tailwind wired up via `@tailwindcss/cli` (npx-based, not a standalone binary — deviates slightly from the original "no Node pipeline" plan, but works and is low-friction; revisit only if npm becomes a real pain point), `input.css` → `static/output.css`, `base.html` layout linking it
- [x] Real route (`/`) — went straight to the actual estimate form rather than a throwaway hello-page, which is fine since Phase 1's engine already existed to back it
- [x] `requirements.txt`, `README.md` with setup steps

**Definition of done:** `flask run` serves a styled page locally with zero manual steps beyond what's in the README.

---

## Phase 1 — Core calculation engine (no web, no LLM, no bot)

**Goal:** prove the domain logic works, in isolation, before touching any interface.

- [x] DB schema: `JobType`, `Material`, `Work`, `WorkNorm`, `RegionalCoefficient` (PL only seeded so far)
- [x] Seed data: bathroom tile installation, fully priced (floor + walls + prep/hydro/grout sequence)
- [x] Pure Python calculation function (`app/calculator.py::calculate_estimate`) — deterministic, no LLM, no network; returns materials, works, totals, duration, sequence
- [x] Unit tests for the 4 m² bathroom tile case (`tests/test_calculator.py`) — passing, including an invalid-area/unknown-job/unknown-region error-path test (one stale assertion fixed 2026-08-25: test referenced `job_type="painting"` as an "unknown" example, but painting was seeded as part of Phase 4 — swapped to a genuinely nonexistent code)
- [x] `flask estimate` CLI command (`app.cli.command`) prints the fixture without going through HTTP

**Definition of done:** running the calculation function against the 4 m² tile test case produces a correct, sane estimate, verified by a passing test — entirely without a browser or API call.

---

## Phase 2 — HTTP API + web form

**Goal:** expose Phase 1's engine through a form a human can actually use.

- [x] `POST /api/estimate` — verified manually: valid input returns full JSON estimate, unknown job type returns `400` with a clear Polish error message, not a stack trace
- [x] Web form (Jinja + Tailwind) on `/`, posts to `/estimate`, renders the estimate as a readable table
- [x] i18n scaffolding (`app/i18n.py`, simple dict-based `t(key, locale)`) — only `pl` strings exist, falls back to `uk` then `pl` by design, ready for Phase 7
- [x] Error handling confirmed end-to-end via curl (see verification log below)

**Definition of done:** a person can open the site, fill the form for a 4 m² bathroom tile job, and see a readable estimate in PLN — full round trip through the browser.

---

## Phase 3 — Free-text input (still no live search, first LLM touchpoint)

**Goal:** accept natural language ("tile my bathroom, 4 square meters") instead of a rigid form.

- [x] `POST /api/parse_text` (`app/llm.py::parse_free_text`) — Gemini 2.5 Flash with a Pydantic-validated response schema (`ParseResult`), `confidence` flag, `temperature=0.0`. Confirmed the calculation engine never receives raw LLM numbers unvalidated — `job_type`/`region` are matched strictly against DB-sourced valid codes passed into the prompt.
- [x] Graceful fallback: no `GEMINI_API_KEY` set → returns `confidence: false` with nulls instead of crashing (verified via curl); UI still has the manual form as a fallback
- [x] `generate_estimate_summary` — second cheap LLM call, friendly PL summary appended to the estimate response; table/JSON stays the source of truth

**Definition of done:** typing the example sentence in a text box produces the same correct estimate as the Phase 2 form, with the option to review/edit the parsed fields before confirming.

---

## Phase 4 — Expand job catalog

**Goal:** go beyond the single tile use case, still PL-only.

- [x] Added `painting` and `laminate_flooring` alongside `bathroom_tiling` (3 job types total)
- [x] `work_norms` extended per job type (each with its own materials/works/sequence)
- [x] Confirmed the calculation engine scales without changes — `calculate_estimate` is fully data-driven off `JobType`/`WorkNorm`, no per-job-type branching in code

**Definition of done:** at least 3 distinct job types produce correct estimates through the same pipeline.

---

## Phase 5 — Offline price sync job

**Goal:** replace hardcoded seed prices with a maintained pipeline, still entirely offline from the user's perspective.

- [x] Scripted import (`scripts/sync_prices.py`) — reads a Sekocenbud-style CSV + a JSON markup config, upserts `base_price`/`markup_multiplier`/`unit_price`(or `labor_rate`) by code. Idempotent, `--dry-run` supported, unknown codes reported and skipped (never auto-created).
- [x] Manual retail markup layered on top of base price (`data/retail_markup.json` — `default` + per-code `overrides`), separate columns on `Material`/`Work` (`base_price`, `markup_multiplier`) so the calculation engine still just reads `unit_price`/`labor_rate` — no change to `app/calculator.py`.
- [x] Update cadence documented in `data/README.md`: Sekocenbud quarterly, retail markup monthly.
- [ ] (Deferred, not needed yet) scheduled CrewAI job for supplementary retail price checks — no real Sekocenbud subscription exists yet, so there's nothing to supplement. Revisit once Phase 5's manual pipeline is actually in use with real data.

**Definition of done:** prices in the DB can be refreshed by running one documented command/script, without touching application code.

---

## Phase 6 — Telegram bot (thin client)

**Goal:** second interface, zero duplicated logic.

- [ ] aiogram bot that accepts text (and later voice) messages
- [ ] Bot calls the same `/api/estimate` — no separate calculation logic in the bot codebase
- [ ] Voice messages: Whisper API transcription → same text pipeline as Phase 3
- [ ] Bot replies with a formatted estimate (text or a simple PDF/image if easy; don't over-invest here yet)

**Definition of done:** the bot and the website produce identical estimates for the same input, because they hit the same endpoint.

---

## Phase 7 — Ukrainian locale

**Goal:** second market, reusing Phase 0–6 infrastructure.

- [ ] `uk` translation strings filled in (i18n scaffolding from Phase 2 pays off here)
- [ ] Separate price table/region config for UA market (new data source TBD — not blocking, use placeholder/manual figures if needed)
- [ ] Language switcher on the site; bot detects or asks for language

**Definition of done:** the same flows (form, free text, bot) work end-to-end in Ukrainian with UA pricing, without any changes to the calculation engine's code — only data and translation files.

---

## Phase 8 — Lead-gen / B2B groundwork (do not start before Phase 1–4 are solid)

**Goal:** first monetization hook, kept deliberately minimal until the calculator itself is proven.

- [ ] "Get matched with a contractor" CTA after an estimate is shown — simple lead capture form (name, contact, estimate reference), stored in DB, no automated matching logic yet
- [ ] Admin view (even a bare Flask-protected page) to see submitted leads
- [ ] Everything past this point (payments, contractor accounts, subscriptions) is deliberately out of scope until there's real user traffic to justify it

**Definition of done:** a lead submitted through the site is retrievable and reviewable by the project owner — nothing more elaborate yet.

---

## Status log

**2026-08-25 — audit of existing code against this plan.** Repo already had Phases 0–4 substantially implemented before this session. Findings:

- All 8 tests passed except one: `tests/test_calculator.py::test_invalid_area_and_unknown_job` used `job_type="painting"` as a stand-in for "unknown job type," but Phase 4 had since made `painting` a real seeded job — the test no longer exercised the branch it claimed to. Fixed by swapping to a genuinely nonexistent code (`nonexistent_job`). This was a stale-test issue, not a calculator bug — the actual unknown-job-type validation in `calculate_estimate` was correct.
- `.gitignore` referenced `static/css/output.css`, but the real Tailwind build output is `static/output.css` (see `package.json`). The mismatch meant the generated CSS file was untracked-but-not-ignored — annoying, not breaking. Fixed the path and added `instance/` and `*.db`.
- `.env.example` didn't mention `GEMINI_API_KEY`, even though `app/llm.py` reads it. Added it as an optional var with a one-line note on the free tier.
- `README.md` still described the project as an "empty starter." Updated to reflect the actual current functionality and added a `pytest` section.
- Manually verified end-to-end: `GET /`, `POST /api/estimate` (valid input, and a 400 with a clear message for an unknown job type), `POST /api/parse_text` (graceful `confidence: false` fallback with no API key set).

Net result: Phases 0–4 are genuinely done, not just checked off. Next open item is **Phase 5 (offline price sync)** — currently all prices are hardcoded in `app/seed.py`, which is fine for continued development but is the next real gap before this could hold real Sekocenbud-sourced pricing.

**2026-08-25 (later) — Phase 5 built and verified.** Added `Material.base_price`/`markup_multiplier` and `Work.base_price`/`markup_multiplier` columns, `scripts/sync_prices.py`, `data/sekocenbud_sample.csv` (placeholder — see `data/README.md`, no real Sekocenbud subscription yet), `data/retail_markup.json`, and `tests/test_price_sync.py`. Two real bugs surfaced and were fixed during verification, not just left as TODOs:

- `base_price` was originally 2 decimal places, which lost precision on the divide-then-multiply round trip (e.g. dividing 12.00 by 1.15, rounding to 2dp, then multiplying back didn't reliably return 12.00). Widened to 4 decimal places on both models and regenerated the sample CSV — verified zero round-trip mismatches across all 29 seeded codes.
- Running `python scripts/sync_prices.py` directly failed with `ModuleNotFoundError: No module named 'app'` — Python only adds the script's own directory to `sys.path`, not the repo root. Fixed by inserting the repo root into `sys.path` at the top of the script.

Manually verified via CLI (not just pytest): `--dry-run` writes nothing, a real run commits and updates 29 records, and a CSV with an unrecognized code is skipped and reported rather than crashing or silently creating a new row.

---

## What Cursor should NOT do without being asked

- Do not add a JS framework (React/Vue/etc.) — this is a server-rendered Flask+Jinja app by design
- Do not implement live web search, scraping, or agentic price lookup on the request path, at any phase
- Do not start Phase 3+ work before Phase 1's tests pass
- Do not add payment processing, user accounts, or the Telegram bot before Phase 4 is done
- Do not switch to PostgreSQL, add Docker, or add CI/CD unless explicitly asked — keep the dev loop lightweight until there's a reason not to
