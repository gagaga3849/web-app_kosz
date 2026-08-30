"""Offline price sync — Phase 5.

Reads a Sekocenbud-style CSV (kind, code, base_price) plus a retail markup
config (JSON), and upserts base_price / markup_multiplier / unit_price (or
labor_rate for works) into the database.

This script is meant to be run manually or on a schedule (cron), NEVER on the
user-request path — see project.md's non-negotiable rule about no live
research/search during a request. It touches no network at all; both inputs
are local files you (or a future, separate scheduled job) prepare in advance.

Usage:
    python scripts/sync_prices.py --sekocenbud data/sekocenbud_sample.csv --markup data/retail_markup.json
    python scripts/sync_prices.py --sekocenbud data/sekocenbud_sample.csv --markup data/retail_markup.json --dry-run

Unknown codes (present in the CSV but not in the DB) are reported and skipped,
not auto-created — new materials/works are a deliberate seed.py/migration
decision, not something a price sync should improvise.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Material, Work  # noqa: E402


def load_markup_config(path: Path) -> tuple[Decimal, dict[str, Decimal]]:
    raw = json.loads(path.read_text())
    default = Decimal(str(raw["default"]))
    overrides = {code: Decimal(str(mult)) for code, mult in raw.get("overrides", {}).items()}
    return default, overrides


def load_sekocenbud_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def quantize_base(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def sync_prices(
    sekocenbud_path: Path,
    markup_path: Path,
    dry_run: bool = False,
) -> dict[str, int]:
    """Runs the sync inside an existing app context. Returns a summary dict."""
    default_markup, overrides = load_markup_config(markup_path)
    rows = load_sekocenbud_csv(sekocenbud_path)

    updated = 0
    unknown: list[str] = []

    for row in rows:
        kind = row["kind"].strip()
        code = row["code"].strip()
        base_price = quantize_base(Decimal(row["base_price"]))
        markup = overrides.get(code, default_markup)
        final_price = quantize_currency(base_price * markup)

        if kind == "material":
            record = Material.query.filter_by(code=code).first()
        elif kind == "work":
            record = Work.query.filter_by(code=code).first()
        else:
            print(f"  ! unknown kind '{kind}' for code '{code}', skipping", file=sys.stderr)
            continue

        if record is None:
            unknown.append(f"{kind}:{code}")
            continue

        record.base_price = base_price
        record.markup_multiplier = markup
        if kind == "material":
            record.unit_price = final_price
        else:
            record.labor_rate = final_price
        updated += 1
        print(f"  {kind:8s} {code:24s} base={base_price:>8} x{markup} -> {final_price}")

    if unknown:
        print(f"\nSkipped {len(unknown)} code(s) not found in the database:", file=sys.stderr)
        for code in unknown:
            print(f"  - {code}", file=sys.stderr)

    if dry_run:
        db.session.rollback()
        print("\nDry run — no changes written.")
    else:
        db.session.commit()
        print(f"\nCommitted. {updated} record(s) updated, {len(unknown)} skipped.")

    return {"updated": updated, "skipped": len(unknown)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sekocenbud", required=True, type=Path, help="Path to the Sekocenbud-style CSV")
    parser.add_argument("--markup", required=True, type=Path, help="Path to the retail markup JSON config")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to the database")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        sync_prices(args.sekocenbud, args.markup, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
