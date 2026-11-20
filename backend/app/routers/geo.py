from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..connectors.usgs import UsgsConnector, Window
from ..workspace_access import issue_proof
from .research import RecordSelection, Workspace

router = APIRouter(prefix="/api/research/geo", tags=["geospatial research"])
usgs = UsgsConnector()
REGIONS = {
    "world": None,
    "americas": (-170, -60, -25, 85),
    "europe-africa": (-30, -40, 70, 85),
    "asia-pacific": (65, -60, -165, 85),
}


class EarthquakeResults(BaseModel):
    available: int
    records: list[RecordSelection]


def inside(latitude: float, longitude: float, bounds: tuple[int, int, int, int] | None) -> bool:
    if bounds is None:
        return True
    west, south, east, north = bounds
    if not south <= latitude <= north:
        return False
    return west <= longitude <= east if west <= east else longitude >= west or longitude <= east


@router.get("/earthquakes", response_model=EarthquakeResults)
async def earthquake_map(
    workspace_id: Workspace, window: Window = "day",
    min_magnitude: Annotated[float, Query(ge=2.5, le=10)] = 2.5,
    region: str = "world",
):
    if region not in REGIONS:
        raise HTTPException(422, "Choose a supported earthquake region.")
    try:
        rows = await usgs.events(window)
    except httpx.TimeoutException as exc:
        raise HTTPException(504, "USGS earthquake feed timed out.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "USGS earthquake records are temporarily unavailable.") from exc
    selected = [row for row in rows if row.magnitude >= min_magnitude
                and inside(row.latitude, row.longitude, REGIONS[region])]
    return EarthquakeResults(available=len(selected), records=[
        RecordSelection(record=row, proof=issue_proof(workspace_id, row)) for row in selected[:250]
    ])
