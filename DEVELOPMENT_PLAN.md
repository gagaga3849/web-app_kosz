# Development Plan — Renovation Estimate Calculator

Companion file to `project.md` (master prompt). Drop this in the repo root or `.cursor/rules/` as `DEVELOPMENT_PLAN.md`. Work through phases in order — do not start a phase until the previous one's "Definition of done" is met. Each phase should be a small, reviewable set of commits, not one giant dump.

**Stack:** Python, Flask, Jinja2, Tailwind CSS (standalone CLI), PostgreSQL (SQLite for local dev), aiogram (bot, later phase).

**Non-negotiable rule across all phases:** no live web search or agentic research on the user-request path. Price data is always read from the local DB, populated offline. See `project.md` for the full rationale.

---

## Phase 0 — Project scaffolding

**Goal:** empty but runnable skeleton, nothing functional yet.

- [ ] Flask app factory pattern (`app/__init__.py`, `create_app()`)
- [ ] `.env` handling (python-dotenv), `.env.example` committed, real `.env` gitignored
- [ ] SQLite for local dev, config flag to switch to PostgreSQL later
- [ ] Tailwind standalone CLI wired up: `input.css` → watch → `static/output.css`, base Jinja layout (`base.html`) linking it
- [ ] One dummy route (`/`) rendering a "hello" page through the Tailwind-styled layout, to confirm the whole chain works
- [ ] `requirements.txt`, `README.md` with setup steps (clone, venv, install, run)

**Definition of done:** `flask run` serves a styled page locally with zero manual steps beyond what's in the README.

---

## Phase 1 — Core calculation engine (no web, no LLM, no bot)

**Goal:** prove the domain logic works, in isolation, before touching any interface.

- [ ] DB schema: `materials`, `works`, `work_norms` (consumption per m², labor time per unit), `regional_coefficients` (stub, PL only for now)
- [ ] Seed data: hardcoded PL price data for **one job type only** — bathroom tile installation (floor + walls). 10–15 materials, 3–5 work items.
- [ ] Pure Python calculation function: given `{job_type, area_m2, region}` → returns structured estimate `{materials: [...], works: [...], total_price, estimated_duration_days, sequence: [...]}`. No LLM involved anywhere in this function.
- [ ] Unit tests covering the 4 m² bathroom tile case with known expected output
- [ ] `flask shell` or a small script to call the function directly and print the result — no HTTP layer needed yet to validate this phase

**Definition of done:** running the calculation function against the 4 m² tile test case produces a correct, sane estimate, verified by a passing test — entirely without a browser or API call.

---

## Phase 2 — HTTP API + web form

**Goal:** expose Phase 1's engine through a form a human can actually use.

- [ ] `POST /api/estimate` — accepts structured JSON (`job_type`, `area_m2`, `region`), calls the Phase 1 function, returns JSON
- [ ] Web form (Jinja + Tailwind) on `/` or `/estimate` — dropdown for job type (just tile for now), number input for area, submits to the API, renders the returned estimate as a readable table
- [ ] i18n scaffolding: wrap all user-facing strings (Flask-Babel or a simple dict-based approach), default locale `pl`, structure ready for `uk` later even though only `pl` strings exist yet
- [ ] Basic error handling: invalid area, unknown job type → clear message, not a stack trace

**Definition of done:** a person can open the site, fill the form for a 4 m² bathroom tile job, and see a readable estimate in PLN — full round trip through the browser.

---

## Phase 3 — Free-text input (still no live search, first LLM touchpoint)

**Goal:** accept natural language ("tile my bathroom, 4 square meters") instead of a rigid form.

- [ ] One cheap LLM call: free text → structured JSON (`job_type`, `area_m2`, region if mentioned). Validate/clamp the output before passing it to the Phase 1 engine — never trust the LLM's numbers directly for anything the calculation engine should own.
- [ ] Fallback to the Phase 2 form if parsing fails or confidence is low — always give the user a way to correct fields manually
- [ ] Second cheap LLM call (optional at this stage): turn the structured estimate into a short natural-language summary alongside the table — table stays the source of truth, LLM text is a friendly wrapper

**Definition of done:** typing the example sentence in a text box produces the same correct estimate as the Phase 2 form, with the option to review/edit the parsed fields before confirming.

---

## Phase 4 — Expand job catalog

**Goal:** go beyond the single tile use case, still PL-only.

- [ ] Add 2–3 more common job types (e.g. painting walls, laying laminate flooring, drywall partition)
- [ ] Extend `work_norms` and seed data accordingly
- [ ] Confirm the calculation engine and form/API scale to multiple job types without rewrites (if they don't, refactor before adding more data)

**Definition of done:** at least 3 distinct job types produce correct estimates through the same pipeline.

---

## Phase 5 — Offline price sync job

**Goal:** replace hardcoded seed prices with a maintained pipeline, still entirely offline from the user's perspective.

- [ ] Scripted import from Sekocenbud data (manual quarterly download → parser → DB upsert) — start manual/semi-automated, not a live agent
- [ ] Manual retail markup table layered on top of base Sekocenbud prices (config file or admin-editable DB table)
- [ ] Document the update cadence (quarterly for Sekocenbud, monthly for retail markup) in `README.md`
- [ ] (Only if genuinely needed later) evaluate a scheduled CrewAI job for supplementary retail price checks — runs on a cron, never on the request path

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

## What Cursor should NOT do without being asked

- Do not add a JS framework (React/Vue/etc.) — this is a server-rendered Flask+Jinja app by design
- Do not implement live web search, scraping, or agentic price lookup on the request path, at any phase
- Do not start Phase 3+ work before Phase 1's tests pass
- Do not add payment processing, user accounts, or the Telegram bot before Phase 4 is done
- Do not switch to PostgreSQL, add Docker, or add CI/CD unless explicitly asked — keep the dev loop lightweight until there's a reason not to
