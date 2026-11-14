import httpx
from typing import List, Dict, Any

class CrtShConnector:
    """Keyless connector for Certificate Transparency logs via crt.sh."""

    BASE_URL = "https://crt.sh/"

    async def search_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Search for certificates related to a domain."""
        params = {"q": domain, "output": "json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            return resp.json()

    async def search(self, query: str) -> Dict[str, Any]:
        results = await self.search_domain(query)
        return {
            "source": "crt.sh",
            "query": query,
            "count": len(results),
            "results": results[:50],  # Limit for MVP
        }
