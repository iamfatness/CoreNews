from fastapi import APIRouter, Query
from ..connectors.crtsh import CrtShConnector

router = APIRouter(prefix="/search", tags=["search"])

crtsh = CrtShConnector()

@router.get("/crtsh")
async def search_crtsh(q: str = Query(..., description="Domain or query to search on crt.sh")):
    """Search Certificate Transparency logs via crt.sh (keyless)."""
    return await crtsh.search(q)
