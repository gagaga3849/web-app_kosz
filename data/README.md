# Price data files

These files feed `scripts/sync_prices.py`. Nothing here is fetched live —
everything is a file you (or a scheduled job) drop in manually, then run the
sync script against it.

## `sekocenbud_sample.csv`

**This is a placeholder, not a real Sekocenbud export.** We don't have a
Sekocenbud subscription yet. This file exists so the sync pipeline is testable
end-to-end today: its `base_price` values were back-calculated from the current
seed prices in `app/seed.py` (base_price × markup from `retail_markup.json` ==
today's `unit_price`/`labor_rate`), so running the sync now reproduces the exact
numbers already in the database — a safe way to verify the pipeline before real
data is involved.

**When a real Sekocenbud subscription exists:** replace this file's contents with
the actual quarterly export (same `kind,code,base_price` shape — remap Sekocenbud's
own item codes to our internal `code` values, e.g. `plytki_podlogowe`, in a small
mapping step before writing this CSV). Cadence: refresh **quarterly**, matching
Sekocenbud's own publication schedule.

## `retail_markup.json`

Multiplier applied on top of each `base_price` to get the retail-facing
`unit_price`/`labor_rate` actually shown to users. `default` applies unless a
`overrides` entry exists for that code. Edit by hand. Cadence: review **monthly**
— retail margins move faster than the underlying Sekocenbud baseline.

## Running the sync

```bash
python scripts/sync_prices.py --sekocenbud data/sekocenbud_sample.csv --markup data/retail_markup.json
```

Add `--dry-run` to preview changes without writing to the database.
