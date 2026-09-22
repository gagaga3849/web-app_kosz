"""Single source of truth for Polish regional pricing granularity.

Why voivodeship + capital, not powiat (district):
Real Polish kosztorys sources (Sekocenbud included) differentiate regional
labor rates at the voivodeship level, usually split into "duże miasto"
(the voivodeship's main city) vs. the rest of the voivodeship — not at the
powiat level (~380 districts nationwide). Going to powiat granularity would
mean inventing precise numbers for hundreds of districts with no reliable
source behind them, which is worse than useful for a tool people build real
quotes from. This mirrors how professional PL estimating tools actually
work.

Coefficients below are a calibrated STARTING approximation (relative to a
1.00 national baseline), grounded in publicly reported regional spreads for
finishing/construction labor (typically ~10-15% voivodeship-to-voivodeship,
with an extra premium in the largest agglomerations, Warsaw highest).
They are placeholders in the same sense as the rest of this project's
pricing (see data/README.md) — replace with real Sekocenbud regional data
before relying on this for real client quotes.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Voivodeship:
    voivodeship_code: str
    name_pl: str
    name_en: str
    name_ru: str
    capital_region_code: str
    capital_name_pl: str
    capital_name_en: str
    capital_name_ru: str
    capital_coefficient: Decimal
    avg_region_code: str
    avg_coefficient: Decimal


# Sorted alphabetically by Polish name — stable, predictable dropdown order
# for the primary market.
VOIVODESHIPS: tuple[Voivodeship, ...] = (
    Voivodeship("dolnoslaskie", "Dolnośląskie", "Lower Silesia", "Нижнесилезское воеводство",
                "dolnoslaskie_wroclaw", "Wrocław", "Wrocław", "Вроцлав", Decimal("1.18"),
                "dolnoslaskie_avg", Decimal("1.00")),
    Voivodeship("kujawsko_pomorskie", "Kujawsko-pomorskie", "Kuyavia-Pomerania", "Куявско-Поморское воеводство",
                "kujawsko_pomorskie_bydgoszcz", "Bydgoszcz", "Bydgoszcz", "Быдгощ", Decimal("1.00"),
                "kujawsko_pomorskie_avg", Decimal("0.88")),
    Voivodeship("lubelskie", "Lubelskie", "Lublin Voivodeship", "Люблинское воеводство",
                "lubelskie_lublin", "Lublin", "Lublin", "Люблин", Decimal("0.95"),
                "lubelskie_avg", Decimal("0.82")),
    Voivodeship("lubuskie", "Lubuskie", "Lubusz Voivodeship", "Любушское воеводство",
                "lubuskie_zielona_gora", "Zielona Góra", "Zielona Góra", "Зелёна-Гура", Decimal("0.95"),
                "lubuskie_avg", Decimal("0.88")),
    Voivodeship("lodzkie", "Łódzkie", "Łódź Voivodeship", "Лодзинское воеводство",
                "lodzkie_lodz", "Łódź", "Łódź", "Лодзь", Decimal("1.05"),
                "lodzkie_avg", Decimal("0.90")),
    Voivodeship("malopolskie", "Małopolskie", "Lesser Poland", "Малопольское воеводство",
                "malopolskie_krakow", "Kraków", "Kraków", "Краков", Decimal("1.20"),
                "malopolskie_avg", Decimal("0.95")),
    Voivodeship("mazowieckie", "Mazowieckie", "Masovia", "Мазовецкое воеводство",
                "mazowieckie_warszawa", "Warszawa", "Warsaw", "Варшава", Decimal("1.40"),
                "mazowieckie_avg", Decimal("1.05")),
    Voivodeship("opolskie", "Opolskie", "Opole Voivodeship", "Опольское воеводство",
                "opolskie_opole", "Opole", "Opole", "Ополе", Decimal("0.93"),
                "opolskie_avg", Decimal("0.85")),
    Voivodeship("podkarpackie", "Podkarpackie", "Subcarpathia", "Подкарпатское воеводство",
                "podkarpackie_rzeszow", "Rzeszów", "Rzeszów", "Жешув", Decimal("0.93"),
                "podkarpackie_avg", Decimal("0.80")),
    Voivodeship("podlaskie", "Podlaskie", "Podlasie", "Подляское воеводство",
                "podlaskie_bialystok", "Białystok", "Białystok", "Белосток", Decimal("0.95"),
                "podlaskie_avg", Decimal("0.85")),
    Voivodeship("pomorskie", "Pomorskie", "Pomerania", "Поморское воеводство",
                "pomorskie_gdansk", "Gdańsk", "Gdańsk", "Гданьск", Decimal("1.18"),
                "pomorskie_avg", Decimal("0.95")),
    Voivodeship("slaskie", "Śląskie", "Silesia", "Силезское воеводство",
                "slaskie_katowice", "Katowice", "Katowice", "Катовице", Decimal("1.10"),
                "slaskie_avg", Decimal("0.95")),
    Voivodeship("swietokrzyskie", "Świętokrzyskie", "Świętokrzyskie Voivodeship", "Свентокшиское воеводство",
                "swietokrzyskie_kielce", "Kielce", "Kielce", "Кельце", Decimal("0.92"),
                "swietokrzyskie_avg", Decimal("0.82")),
    Voivodeship("warminsko_mazurskie", "Warmińsko-mazurskie", "Warmia-Masuria", "Варминьско-Мазурское воеводство",
                "warminsko_mazurskie_olsztyn", "Olsztyn", "Olsztyn", "Ольштын", Decimal("0.93"),
                "warminsko_mazurskie_avg", Decimal("0.83")),
    Voivodeship("wielkopolskie", "Wielkopolskie", "Greater Poland", "Великопольское воеводство",
                "wielkopolskie_poznan", "Poznań", "Poznań", "Познань", Decimal("1.15"),
                "wielkopolskie_avg", Decimal("0.95")),
    Voivodeship("zachodniopomorskie", "Zachodniopomorskie", "West Pomerania", "Западно-Поморское воеводство",
                "zachodniopomorskie_szczecin", "Szczecin", "Szczecin", "Щецин", Decimal("1.08"),
                "zachodniopomorskie_avg", Decimal("0.92")),
)

NATIONAL_FALLBACK_CODE = "pl"

_SUFFIX = {
    "pl": {"capital": "stolica województwa", "avg": "średnio w województwie", "national": "Polska — średnia krajowa"},
    "en": {"capital": "voivodeship capital", "avg": "voivodeship average", "national": "Poland — national average"},
    "ru": {"capital": "столица воеводства", "avg": "в среднем по воеводству", "national": "Польша — среднее по стране"},
}


def _suffix(locale: str, key: str) -> str:
    bundle = _SUFFIX.get(locale) or _SUFFIX["pl"]
    return bundle[key]


def voivodeship_label(v: Voivodeship, locale: str) -> str:
    return {"pl": v.name_pl, "en": v.name_en, "ru": v.name_ru}.get(locale, v.name_pl)


def capital_label(v: Voivodeship, locale: str) -> str:
    name = {"pl": v.capital_name_pl, "en": v.capital_name_en, "ru": v.capital_name_ru}.get(locale, v.capital_name_pl)
    return name


def avg_label(v: Voivodeship, locale: str) -> str:
    return f"{voivodeship_label(v, locale)} — {_suffix(locale, 'avg')}"


def national_fallback_label(locale: str) -> str:
    return _suffix(locale, "national")


def find_voivodeship(voivodeship_code: str) -> Optional[Voivodeship]:
    return next((v for v in VOIVODESHIPS if v.voivodeship_code == voivodeship_code), None)
