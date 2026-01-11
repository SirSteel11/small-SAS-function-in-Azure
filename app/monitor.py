from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.models import BookingHotel, MonitorConfig, SasRoute
from app.storage import StorageBackend


def _make_alert_id(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _record_alert(alerts: Dict[str, str], payload: Dict[str, Any]) -> bool:
    alert_id = _make_alert_id(payload)
    if alert_id in alerts:
        return False
    alerts[alert_id] = datetime.now(timezone.utc).isoformat()
    return True


async def _prepare_page(context: BrowserContext, block_resources: bool) -> Page:
    page = await context.new_page()
    if block_resources:
        await page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in {"image", "media", "font"}
            else route.continue_(),
        )
    return page


async def check_sas_routes(
    browser: Browser,
    routes: List[SasRoute],
    config: MonitorConfig,
    state_path: str | None,
) -> List[Dict[str, Any]]:
    if not routes:
        return []

    context = await browser.new_context(storage_state=state_path) if state_path else await browser.new_context()
    page = await _prepare_page(context, config.settings.block_resources)

    results: List[Dict[str, Any]] = []
    for route in routes:
        await page.goto(config.settings.sas_base_url, wait_until="domcontentloaded")
        # TODO: implement SAS SkyTeam search using locators or network interception.
        results.append(
            {
                "type": "sas",
                "origin": route.origin,
                "destination": route.destination,
                "date": route.date.isoformat(),
                "cabin": route.cabin,
                "status": "not_implemented",
            }
        )

    await context.close()
    return results


async def check_booking_hotels(
    browser: Browser,
    hotels: List[BookingHotel],
    config: MonitorConfig,
) -> List[Dict[str, Any]]:
    if not hotels:
        return []

    context = await browser.new_context()
    page = await _prepare_page(context, config.settings.block_resources)

    results: List[Dict[str, Any]] = []
    for hotel in hotels:
        await page.goto(config.settings.booking_base_url, wait_until="domcontentloaded")
        # TODO: implement Booking.com search and extraction.
        results.append(
            {
                "type": "booking",
                "hotel": hotel.name,
                "city": hotel.city,
                "check_in": hotel.check_in.isoformat(),
                "check_out": hotel.check_out.isoformat(),
                "status": "not_implemented",
            }
        )

    await context.close()
    return results


async def run_monitor(config: MonitorConfig, storage: StorageBackend) -> List[Dict[str, Any]]:
    alerts = storage.load_alerts()
    alerts = storage.prune_alerts(alerts, config.settings.alert_ttl_hours)

    state_path = storage.download_state()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=config.settings.headless)
        sas_results = await check_sas_routes(browser, config.sas_routes, config, str(state_path) if state_path else None)
        booking_results = await check_booking_hotels(browser, config.booking_hotels, config)
        await browser.close()

    new_alerts: List[Dict[str, Any]] = []
    for result in sas_results + booking_results:
        if _record_alert(alerts, result):
            new_alerts.append(result)

    storage.save_alerts(alerts)
    if state_path:
        storage.upload_state(state_path)

    return new_alerts
