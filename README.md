# webapp — renovation estimate calculator

Flask + Jinja + Tailwind app that turns a room size (and, optionally, a free-text
description like "tile my bathroom, 4 m²") into a structured renovation estimate.
Pricing and calculation logic is a deterministic Python engine (`app/calculator.py`,
no LLM, no live web lookups) reading from a local SQLite/PostgreSQL catalog. An
optional Gemini call only handles (a) parsing free text into structured fields and
(b) writing a short friendly summary — both skipped gracefully if no API key is set.

See `project.md` for architecture rationale and `DEVELOPMENT_PLAN.md` for the phased
roadmap and what's left to build.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run build:css
cp .env.example .env   # fill in GEMINI_API_KEY if you want the AI free-text input
```

## Run

```bash
source .venv/bin/activate
flask --app app run --debug
```

In another terminal, rebuild CSS as you edit templates:

```bash
npm run watch:css
```

## Test

```bash
pytest
```
