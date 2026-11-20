import httpx
from fastapi import APIRouter, HTTPException, Query

from ..connectors.crtsh import RESULT_LIMIT, CrtShConnector
from ..records import CertificateSearchResults, normalize_certificates, normalize_domain

router = APIRouter(prefix="/search", tags=["search"])

crtsh = CrtShConnector()

@router.get("/crtsh")
async def search_crtsh(q: str = Query(..., description="Domain or query to search on crt.sh")):
    """Search Certificate Transparency logs via crt.sh (keyless)."""
    return await crtsh.search(q)


@router.get("/records", response_model=CertificateSearchResults)
async def search_records(q: str = Query(..., max_length=512)):
    """Look up a domain and return normalized public certificate records."""
    return await lookup_certificates(q)


async def lookup_certificates(q: str) -> CertificateSearchResults:
    try:
        domain = normalize_domain(q)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    try:
        rows = await crtsh.search_domain(domain)
    except httpx.TimeoutException as exc:
        raise HTTPException(504, "crt.sh timed out. Try your search again.") from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise HTTPException(503, "crt.sh is limiting requests. Try again in a moment.") from exc
        raise HTTPException(502, "crt.sh is temporarily unavailable. Try again.") from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(502, "crt.sh did not return usable results. Try again.") from exc

    if not isinstance(rows, list) or (rows and not any(isinstance(row, dict) for row in rows)):
        raise HTTPException(502, "crt.sh did not return usable results. Try again.")
    results = normalize_certificates(domain, rows, RESULT_LIMIT)
    if rows and not results.records:
        raise HTTPException(502, "crt.sh did not return usable records. Try again.")
    return results
