from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from azure.storage.blob import BlobClient


@dataclass
class StorageConfig:
    connection_string: Optional[str]
    container: str
    state_blob: str
    alerts_blob: str


class StorageBackend:
    def __init__(self, config: StorageConfig, local_dir: Path) -> None:
        self._config = config
        self._local_dir = local_dir
        self._local_dir.mkdir(parents=True, exist_ok=True)

    def _blob_client(self, blob_name: str) -> Optional[BlobClient]:
        if not self._config.connection_string:
            return None
        return BlobClient.from_connection_string(
            conn_str=self._config.connection_string,
            container_name=self._config.container,
            blob_name=blob_name,
        )

    def download_state(self) -> Optional[Path]:
        local_path = self._local_dir / "state.json"
        client = self._blob_client(self._config.state_blob)
        if client is None:
            return local_path if local_path.exists() else None

        if not client.exists():
            return None

        data = client.download_blob().readall()
        local_path.write_bytes(data)
        return local_path

    def upload_state(self, state_path: Path) -> None:
        client = self._blob_client(self._config.state_blob)
        if client is None:
            return
        client.upload_blob(state_path.read_bytes(), overwrite=True)

    def load_alerts(self) -> Dict[str, str]:
        local_path = self._local_dir / "sent_alerts.json"
        client = self._blob_client(self._config.alerts_blob)
        if client is None:
            return self._read_alerts(local_path)

        if client.exists():
            data = client.download_blob().readall()
            local_path.write_bytes(data)
        return self._read_alerts(local_path)

    def save_alerts(self, alerts: Dict[str, str]) -> None:
        local_path = self._local_dir / "sent_alerts.json"
        local_path.write_text(json.dumps(alerts, indent=2), encoding="utf-8")

        client = self._blob_client(self._config.alerts_blob)
        if client is None:
            return
        client.upload_blob(local_path.read_bytes(), overwrite=True)

    def prune_alerts(self, alerts: Dict[str, str], ttl_hours: int) -> Dict[str, str]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)
        return {
            key: timestamp
            for key, timestamp in alerts.items()
            if datetime.fromisoformat(timestamp) >= cutoff
        }

    @staticmethod
    def _read_alerts(path: Path) -> Dict[str, str]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))


def build_storage() -> StorageBackend:
    connection_string = os.getenv("STORAGE_CONNECTION_STRING")
    container = os.getenv("STORAGE_CONTAINER", "sas-monitor")
    state_blob = os.getenv("STATE_BLOB", "state.json")
    alerts_blob = os.getenv("ALERTS_BLOB", "sent_alerts.json")
    local_dir = Path(os.getenv("LOCAL_STATE_DIR", "/app/state"))

    config = StorageConfig(
        connection_string=connection_string,
        container=container,
        state_blob=state_blob,
        alerts_blob=alerts_blob,
    )
    return StorageBackend(config=config, local_dir=local_dir)
