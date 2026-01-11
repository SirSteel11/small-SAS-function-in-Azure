from __future__ import annotations

import asyncio
import json

from app.config import load_config
from app.monitor import run_monitor
from app.storage import build_storage
from app.telegram import build_telegram_client


def format_alert(payload: dict) -> str:
    if payload.get("type") == "sas":
        return (
            "✈️ <b>SAS övervakning</b>\n"
            f"{payload['origin']} → {payload['destination']} ({payload['date']})\n"
            f"Kabin: {payload['cabin']}\n"
            f"Status: {payload['status']}"
        )
    if payload.get("type") == "booking":
        return (
            "🏨 <b>Booking.com övervakning</b>\n"
            f"{payload['hotel']} — {payload['city']}\n"
            f"{payload['check_in']} → {payload['check_out']}\n"
            f"Status: {payload['status']}"
        )
    return f"Ny observation: {json.dumps(payload, ensure_ascii=False)}"


async def main() -> None:
    config = load_config()
    storage = build_storage()
    telegram = build_telegram_client()

    alerts = await run_monitor(config, storage)
    if not alerts:
        print("No new alerts.")
        return

    for alert in alerts:
        telegram.send_message(format_alert(alert))


if __name__ == "__main__":
    asyncio.run(main())
