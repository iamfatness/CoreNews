from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from . import evidence_store
from .config import settings
from .routers import case_reports, geo, investigations, monitoring, research, screening, search, workbench

app = FastAPI(
    title="CoreNews",
    description="Modular self-hosted OSINT / intelligence platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(research.router)
app.include_router(case_reports.router)
app.include_router(monitoring.router)
app.include_router(geo.router)
app.include_router(screening.router)
app.include_router(workbench.router)
app.include_router(investigations.router)
app.mount(
    "/research",
    StaticFiles(directory=Path(__file__).with_name("research"), html=True),
    name="research",
)

@app.get("/")
async def root():
    return {
        "name": "CoreNews",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        with evidence_store.database(settings.database_url).connect() as conn:
            for table in evidence_store.metadata.sorted_tables:
                conn.execute(select(table).limit(0))
    except SQLAlchemyError:
        raise HTTPException(503, "Research storage is not ready.") from None
    return {"status": "ready"}
