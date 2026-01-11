# SAS + Booking Monitor (Azure Container Apps Job)

This repository provides a container-ready Python application for monitoring SAS EuroBonus award availability and Booking.com hotel prices using Playwright. It is designed to run as an **Azure Container Apps Job** on a schedule and send alerts via Telegram.

## What you run
The container executes:

```bash
python -m app.main
```

It reads configuration from a JSON file (mounted or baked into the image) and uses Azure Blob Storage to persist session state and sent-alert history.

## Required configuration

### 1) Config file
Provide a config file (JSON) with routes and hotels. A sample is included at `config/config.sample.json`.

Set the path with `CONFIG_PATH` (defaults to `/app/config/config.json`).

### 2) Environment variables

| Variable | Description |
| --- | --- |
| `CONFIG_PATH` | Path to the config JSON inside the container. |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather. |
| `TELEGRAM_CHAT_ID` | Telegram chat ID to receive alerts. |
| `STORAGE_CONNECTION_STRING` | Azure Storage connection string for state/alerts. |
| `STORAGE_CONTAINER` | Blob container name (default: `sas-monitor`). |
| `STATE_BLOB` | Blob name for Playwright storage state (default: `state.json`). |
| `ALERTS_BLOB` | Blob name for sent-alerts tracking (default: `sent_alerts.json`). |
| `LOCAL_STATE_DIR` | Local fallback dir (default: `/app/state`). |

## Cookies / session state (SAS login)
The SAS SkyTeam portal requires authentication. This app expects a **Playwright storage state** JSON file named `state.json`.

### How to create `state.json`
1. Run a local Playwright script (or `playwright codegen`) to log in to SAS interactively.
2. Save storage state:

```python
await context.storage_state(path="state.json")
```

3. Upload `state.json` to the Azure Blob container referenced by `STORAGE_CONNECTION_STRING`.

At runtime, the job downloads `state.json`, loads it into the Playwright context, and re-uploads any updated state.

> If you do **not** provide a storage state, the job will run unauthenticated and SAS scraping will not work.

## Docker

```bash
docker build -t sas-monitor .
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=... \
  -e TELEGRAM_CHAT_ID=... \
  -e STORAGE_CONNECTION_STRING=... \
  -v $(pwd)/config/config.sample.json:/app/config/config.json \
  sas-monitor
```

## Azure Container Apps Job (example)

```bash
az containerapp job create \
  --name sas-monitor-job \
  --resource-group travel-watcher-rg \
  --image <registry>.azurecr.io/sas-monitor:v1 \
  --trigger-type Schedule \
  --cron-expression "0 */4 * * *" \
  --cpu 0.5 --memory 1.0Gi \
  --env-vars \
    TELEGRAM_BOT_TOKEN=... \
    TELEGRAM_CHAT_ID=... \
    STORAGE_CONNECTION_STRING=... \
    CONFIG_PATH=/app/config/config.json
```

## Implementation notes
- SAS and Booking.com scraping flows are stubbed with TODO markers in `app/monitor.py`. Replace those sections with your Playwright locators or network interception logic.
- Alert de-duplication uses a SHA-256 hash stored in Blob Storage or the local state directory.
