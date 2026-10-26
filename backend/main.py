"""FastAPI main application entrypoint."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.config import settings

app = FastAPI(title="Savdhaan Backend", version="0.1")


@app.get("/api/health")
async def health():
    """Health check endpoint indicating service status and Gnani API key presence."""
    return {
        "ok": True,
        "gnani_key_present": settings.key_present,
        "version": "0.1",
    }


# Mount frontend static directory at root
frontend_dir = Path("frontend")
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
