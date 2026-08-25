# webapp

Empty Flask + Jinja + Tailwind CLI starter.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run build:css
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
