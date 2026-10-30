"""FastAPI main application entrypoint and REST/WebSocket API endpoints."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.analyze import router as analyze_router
from backend.routes_info import router as info_router
from backend.config import settings
from backend.orchestrator import SessionBusy, SessionManager, StartSessionRequest

app = FastAPI(title="Savdhaan Backend", version="0.1")
app.include_router(analyze_router)
app.include_router(info_router)
session_manager = SessionManager(settings)


class SessionStartBody(BaseModel):
    mode: str = Field(..., description="mock, replay, file, or mic")
    call_id: Optional[str] = None
    lang: str = "hi-IN"
    sample_rate: int = 8000
    danger: int = 60
    careful: int = 30
    speak_warning: bool = True
    speed: float = 1.0


class SessionStopBody(BaseModel):
    session_id: str


@app.get("/api/health")
async def health():
    """Health check endpoint indicating service status and Gnani API key presence."""
    return {
        "ok": True,
        "gnani_key_present": settings.key_present,
        "version": "0.1",
        "demo": settings.demo,
    }


@app.post("/api/session/start")
async def start_session(body: SessionStartBody, request: Request):
    if not (0 < body.careful < body.danger <= 100):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Thresholds must satisfy 0 < careful < danger <= 100",
        )

    if body.mode == "mic" and not settings.allow_remote_live:
        client_host = request.client.host if request.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "live_local_only", "detail": "live_local_only"},
            )

    if settings.demo and body.mode in ("file", "mic"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "demo_mode"},
        )

    if body.mode == "mic" and not settings.key_present:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GNANI_API_KEY is required for mic mode",
        )

    req = StartSessionRequest(
        mode=body.mode,
        call_id=body.call_id,
        lang=body.lang,
        sample_rate=body.sample_rate,
        danger=body.danger,
        careful=body.careful,
        speak_warning=body.speak_warning,
        speed=body.speed,
    )

    try:
        session_id = await session_manager.start(req)
        return {"session_id": session_id}
    except SessionBusy:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another session is already active",
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )


@app.post("/api/session/stop")
async def stop_session(body: SessionStopBody):
    stopped = await session_manager.stop(body.session_id)
    return {"ok": stopped}


@app.websocket("/ws/ui")
async def websocket_ui(websocket: WebSocket):
    await websocket.accept()
    q = session_manager.subscribe()
    sent_seqs = set()
    try:
        # First send existing history
        for msg in session_manager.history():
            sent_seqs.add(msg["seq"])
            await websocket.send_text(json.dumps(msg, ensure_ascii=False))

        # Stream live messages
        while True:
            msg = await q.get()
            if msg.get("seq") not in sent_seqs:
                sent_seqs.add(msg.get("seq"))
                await websocket.send_text(json.dumps(msg, ensure_ascii=False))
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        session_manager.unsubscribe(q)


@app.websocket("/ws/mic")
async def websocket_mic(websocket: WebSocket, session_id: str = ""):
    """Receive browser microphone audio and route to the active mic session."""
    origin = websocket.headers.get("origin", "")
    host = websocket.headers.get("host", "")
    allowed = {"http://localhost:8000", "http://127.0.0.1:8000"}
    if settings.allowed_origins:
        for o in settings.allowed_origins.split(","):
            if o.strip():
                allowed.add(o.strip())

    origin_ok = True
    if origin:
        parsed_origin = urlparse(origin)
        origin_netloc = parsed_origin.netloc or parsed_origin.path
        if origin_netloc != host and origin not in allowed:
            origin_ok = False

    if not origin_ok or not session_id:
        await websocket.close(code=1008)
        return

    if not settings.allow_remote_live:
        client_host = websocket.client.host if websocket.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            await websocket.close(code=4003)
            return

    await websocket.accept()
    if not session_manager.attach_mic(session_id, websocket):
        await websocket.close(code=1008)
        return
    try:
        while True:
            msg = await websocket.receive()
            data = msg.get("bytes")
            text = msg.get("text")
            if data:
                await session_manager.push_mic(session_id, data)
            elif text == "stop" or msg.get("type") == "websocket.disconnect":
                break
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        await session_manager.stop_mic(session_id)


# Mount frontend static directory LAST
frontend_dir = Path("frontend")
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
