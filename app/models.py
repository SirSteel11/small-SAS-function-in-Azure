from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class SasRoute(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    date: date
    cabin: str = Field(default="Economy")
    max_points: Optional[int] = None


class BookingHotel(BaseModel):
    name: str
    city: str
    check_in: date
    check_out: date
    max_price_sek: Optional[int] = None


class Settings(BaseModel):
    sas_base_url: str
    booking_base_url: str
    headless: bool = True
    alert_ttl_hours: int = 24
    block_resources: bool = True


class MonitorConfig(BaseModel):
    sas_routes: List[SasRoute] = Field(default_factory=list)
    booking_hotels: List[BookingHotel] = Field(default_factory=list)
    settings: Settings
