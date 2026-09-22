import asyncio

from bot.telegram_bot import TelegramApiClient, format_estimate


def run(coro):
    return asyncio.run(coro)


def test_bot_parses_text_then_requests_estimate():
    calls = []

    async def request(path, payload):
        calls.append((path, payload))
        if path == "/api/parse_text":
            return {"job_type": "bathroom_tiling", "area_m2": 4, "region": "pl"}
        return {"job_name": "Układanie płytek", "area_m2": "4", "total_price": "5392.40", "currency": "PLN", "estimated_duration_days": 3}

    estimate = run(TelegramApiClient("http://backend", request).estimate_from_text("kafelki 4 m²"))

    assert estimate["total_price"] == "5392.40"
    assert calls == [
        ("/api/parse_text", {"text": "kafelki 4 m²"}),
        ("/api/estimate", {"job_type": "bathroom_tiling", "area_m2": 4, "region": "pl"}),
    ]


def test_bot_requests_missing_fields():
    async def request(path, payload):
        return {"job_type": None, "area_m2": None}

    try:
        run(TelegramApiClient("http://backend", request).estimate_from_text("remont"))
    except ValueError as exc:
        assert str(exc) == "Podaj jeszcze: rodzaj prac, powierzchnię w m²."
    else:
        raise AssertionError("missing fields should stop the estimate request")


def test_bot_formats_fallback_estimate():
    text = format_estimate({
        "job_name": "Układanie płytek",
        "area_m2": "4",
        "total_price": "5392.40",
        "currency": "PLN",
        "estimated_duration_days": 3,
    })
    assert "5392.40 PLN" in text