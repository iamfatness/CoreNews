from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import case_reports, research, search

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
