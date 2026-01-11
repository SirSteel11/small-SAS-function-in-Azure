from __future__ import annotations

import os
from typing import Optional

import requests


class TelegramClient:
    def __init__(self, token: Optional[str], chat_id: Optional[str]) -> None:
        self._token = token
        self._chat_id = chat_id

    def send_message(self, message: str) -> None:
        if not self._token or not self._chat_id:
            print("Telegram credentials missing; skipping alert.")
            return

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {"chat_id": self._chat_id, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()


def build_telegram_client() -> TelegramClient:
    return TelegramClient(
        token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
    )
