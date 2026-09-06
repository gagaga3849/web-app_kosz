"""Deterministic, dependency-free fallback for guessing a typical room size
from common Polish keywords in the user's free-text description.

This is intentionally NOT an LLM call and NOT a web search. It's a plain
lookup table so it's instant, free, offline-safe, and 100% reproducible —
consistent with keeping calculate_estimate() the only source of truth for
money math. This only ever fills in a *starting point* for area_m2 when the
model couldn't find one; the value is always shown to the user as an
assumption they can override, never silently used.
"""

from __future__ import annotations

import re
import unicodedata

# code: (typical_area_m2, human label shown to the user, list of keywords/aliases)
SPACE_DEFAULTS: list[tuple[float, str, list[str]]] = [
    (15.0, "typowy garaż (1 samochód)", ["garaz", "garazu", "garazem"]),
    (5.0, "typowa łazienka", ["lazienka", "lazience", "lazienke", "lazienki"]),
    (2.0, "typowa toaleta/WC", ["toaleta", "toalecie", "wc"]),
    (20.0, "typowy salon", ["salon", "salonie", "salonu"]),
    (10.0, "typowa kuchnia", ["kuchnia", "kuchni"]),
    (12.0, "typowa sypialnia", ["sypialnia", "sypialni"]),
    (6.0, "typowy przedpokój/korytarz", ["przedpokoj", "korytarz", "korytarza", "korytarzu"]),
    (4.0, "typowy balkon", ["balkon", "balkonu", "balkonie"]),
    (14.0, "typowy pokój", ["pokoj", "pokoju", "pokoje"]),
]


def _normalize(text: str) -> str:
    # "ł"/"Ł" aren't combining-diacritic forms, so NFKD alone won't fold them
    # to "l" the way it does for ą/ę/ć/ń/ś/ź/ż — needs an explicit swap first.
    text = text.replace("ł", "l").replace("Ł", "L")
    decomposed = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9\s]", " ", stripped)


def guess_area_from_text(text: str) -> dict | None:
    """Return {"area_m2": float, "label": str} for the first matching space
    keyword found in the text, or None if nothing matched.
    Word-boundary matching only, so 'salonik' style substrings inside longer
    unrelated words won't cause a false positive.
    """
    normalized = _normalize(text)
    words = set(normalized.split())
    for area, label, keywords in SPACE_DEFAULTS:
        if words & set(keywords):
            return {"area_m2": area, "label": label}
    return None
