from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from app.models import MonitorConfig


DEFAULT_CONFIG_PATH = Path("/app/config/config.json")


def load_config() -> MonitorConfig:
    load_dotenv()
    config_path = Path(os.getenv("CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}. Provide CONFIG_PATH or mount config.json."
        )

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return MonitorConfig.model_validate(raw)
