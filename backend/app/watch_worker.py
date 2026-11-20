"""Database-backed worker for explicitly configured public filing and news watches."""

import asyncio
import logging

from fastapi import HTTPException

from . import watch_store as watches
from .config import settings
from .routers.research import lookup_filings, lookup_news

log = logging.getLogger("corenews.watch_worker")


async def run_once() -> bool:
    if not settings.research_watches_enabled:
        return False
    watch = watches.claim_due(watches.epoch())
    if watch is None:
        return False
    records = []
    error = None
    try:
        lookup = {"edgar": lookup_filings, "gdelt": lookup_news}[watch["source"]]
        result = await asyncio.wait_for(lookup(watch["query"]), timeout=70)
        records = result.records
    except HTTPException as exc:
        error = str(exc.detail)
    except TimeoutError:
        error = "The source check timed out."
    except Exception:
        error = "The source check failed."
        log.exception("Unexpected source failure while processing a watch")
    watches.finish_check(watch, watches.epoch(), records, error)
    return True


async def loop():
    if not settings.research_watches_enabled:
        raise SystemExit("Set RESEARCH_WATCHES_ENABLED=true to start the watch worker.")
    while True:
        try:
            processed = await run_once()
        except Exception:
            log.exception("Watch worker failed to persist a check")
            processed = False
        await asyncio.sleep(1 if processed else 15)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(loop())
