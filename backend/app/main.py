from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import search

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
