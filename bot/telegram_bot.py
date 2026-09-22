from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message


JsonRequest = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


class TelegramApiClient:
    """HTTP client for the existing parse-and-estimate API endpoints."""

    def __init__(self, base_url: str, request: JsonRequest | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._request = request or self._request_json

    async def _request_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            response = await client.post(path, json=payload)
            data = response.json()
            if response.is_error:
                raise RuntimeError(data.get("error", "Backend request failed."))
            return data

    async def estimate_from_text(self, text: str) -> dict[str, Any]:
        parsed = await self._request("/api/parse_text", {"text": text})
        if not parsed.get("job_type") or parsed.get("area_m2") is None:
            missing = []
            if not parsed.get("job_type"):
                missing.append("rodzaj prac")
            if parsed.get("area_m2") is None:
                missing.append("powierzchnię w m²")
            raise ValueError(f"Podaj jeszcze: {', '.join(missing)}.")

        return await self._request(
            "/api/estimate",
            {
                "job_type": parsed["job_type"],
                "area_m2": parsed["area_m2"],
                "region": parsed.get("region") or "pl",
            },
        )


def format_estimate(estimate: dict[str, Any]) -> str:
    summary = estimate.get("summary")
    if summary:
        return summary
    return (
        f"Kosztorys: {estimate['job_name']}\n"
        f"Powierzchnia: {estimate['area_m2']} m²\n"
        f"Suma: {estimate['total_price']} {estimate['currency']}\n"
        f"Czas: {estimate['estimated_duration_days']} dni"
    )


def create_router(api_client: TelegramApiClient) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await message.answer("Opisz prace remontowe i podaj powierzchnię, np. kafelki w łazience, 4 m².")

    @router.message()
    async def estimate_handler(message: Message) -> None:
        if not message.text:
            await message.answer("Wyślij opis prac tekstem. Wiadomości głosowe będą dostępne później.")
            return
        try:
            estimate = await api_client.estimate_from_text(message.text)
            await message.answer(format_estimate(estimate))
        except (RuntimeError, ValueError) as exc:
            await message.answer(str(exc))

    return router


async def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN before starting the bot.")
    api_url = os.environ.get("ESTIMATE_API_URL", "http://127.0.0.1:5000")
    bot = Bot(token=token)
    dispatcher = Dispatcher()
    dispatcher.include_router(create_router(TelegramApiClient(api_url)))
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())