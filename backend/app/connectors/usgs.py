"""Normalize public USGS earthquake summary features."""

import asyncio
import math
import re
from datetime import datetime, timezone
from time import monotonic
from typing import Literal

import httpx

from ..records import ResearchRecord, source_text

Window = Literal["day", "week"]
URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_{}.geojson"


class EarthquakeRecord(ResearchRecord):
    record_type: Literal["earthquake"] = "earthquake"
    latitude: float
    longitude: float
    depth_km: float
    magnitude: float
    occurred_at: datetime | None
    source_updated_at: datetime | None


def event_time(value: object) -> datetime | None:
    if not isinstance(value, int):
        return None
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def normalize_earthquakes(payload: object) -> list[EarthquakeRecord]:
    features = payload.get("features") if isinstance(payload, dict) else None
    if not isinstance(features, list):
        raise ValueError("USGS did not return an earthquake collection.")
    collected = datetime.now(timezone.utc).replace(microsecond=0)
    records = {}
    for feature in features:
        if not isinstance(feature, dict):
            continue
        identifier = feature.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", identifier):
            continue
        point, properties = feature.get("geometry"), feature.get("properties")
        if not isinstance(point, dict) or point.get("type") != "Point" or not isinstance(properties, dict):
            continue
        position = point.get("coordinates")
        if not isinstance(position, list) or len(position) < 3:
            continue
        lon, lat, depth = position[:3]
        magnitude = properties.get("mag")
        if any(not isinstance(n, (float, int)) or isinstance(n, bool) or not math.isfinite(n)
               for n in (lat, lon, depth, magnitude)):
            continue
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            continue
        records[identifier] = EarthquakeRecord(
            id=f"usgs:{identifier}",
            title=source_text(properties.get("title")) or source_text(properties.get("place")) or identifier,
            source="USGS Earthquakes",
            source_url=f"https://earthquake.usgs.gov/earthquakes/eventpage/{identifier}",
            collected_at=collected, latitude=lat, longitude=lon, depth_km=depth, magnitude=magnitude,
            occurred_at=event_time(properties.get("time")),
            source_updated_at=event_time(properties.get("updated")),
        )
    if features and not records:
        raise ValueError("USGS returned no usable earthquake coordinates.")
    return list(records.values())


class UsgsConnector:
    def __init__(self):
        self.cache: dict[Window, tuple[float, list[EarthquakeRecord]]] = {}
        self.lock = asyncio.Lock()

    async def events(self, window: Window) -> list[EarthquakeRecord]:
        async with self.lock:
            cached = self.cache.get(window)
            if cached and monotonic() < cached[0]:
                return cached[1]
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(URL.format(window))
                response.raise_for_status()
                records = normalize_earthquakes(response.json())
            self.cache[window] = (monotonic() + 60, records)
            return records
