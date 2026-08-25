from __future__ import annotations

STRINGS = {
    "pl": {
        "site_title": "Kalkulator kosztorysu",
        "headline": "Wycena ułożenia płytek",
        "intro": "Podaj powierzchnię podłogi. Ściany liczymy automatycznie (×3) według norm katalogowych — bez wyszukiwania cen w internecie.",
        "job_type": "Rodzaj prac",
        "area": "Powierzchnia podłogi (m²)",
        "region": "Region",
        "submit": "Oblicz kosztorys",
        "materials": "Materiały",
        "works": "Robocizna",
        "sequence": "Kolejność prac",
        "total": "Razem",
        "duration": "Szacowany czas",
        "days": "dni roboczych",
        "item": "Pozycja",
        "qty": "Ilość",
        "unit": "J.m.",
        "unit_price": "Cena jedn.",
        "line_total": "Wartość",
        "materials_total": "Materiały razem",
        "works_total": "Robocizna razem",
        "dimensions": "Przyjęte wymiary",
        "floor": "podłoga",
        "wall": "ściany",
        "perimeter": "obwód",
        "error_generic": "Nie udało się obliczyć kosztorysu.",
        "lang_name": "Polski",
        "ai_input_title": "Zdefiniuj zlecenie własnymi słowami (AI)",
        "ai_input_placeholder": "np. Chcę położyć kafelki w łazience o powierzchni 4m²",
        "ai_button": "Dopasuj parametry",
        "ai_parsing": "Analizowanie...",
        "ai_success": "AI dopasowało rodzaj prac i powierzchnię! Sprawdź parametry poniżej i kliknij 'Oblicz kosztorys'.",
        "ai_error": "Nie udało się rozpoznać wszystkich szczegółów. Wybierz parametry ręcznie.",
    }
}

DEFAULT_LOCALE = "pl"


def t(key: str, locale: str = DEFAULT_LOCALE) -> str:
    bundle = STRINGS.get(locale) or STRINGS[DEFAULT_LOCALE]
    if key not in bundle:
        uk = STRINGS.get("uk")
        if uk and key in uk:
            return uk[key]
        return STRINGS[DEFAULT_LOCALE].get(key, key)
    return bundle[key]
