"""FastAPI main application entrypoint and REST/WebSocket API endpoints."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import settings
from backend.orchestrator import SessionBusy, SessionManager, StartSessionRequest
from backend import usage

app = FastAPI(title="Savdhaan Backend", version="0.1")
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


@app.get("/api/calls")
async def get_calls():
    """List available mock and real calls."""
    calls = []
    # Always include mock call
    mock_file = Path("data/mock/mock_call.json")
    if mock_file.exists():
        try:
            with open(mock_file, "r", encoding="utf-8") as f:
                mock_data = json.load(f)
            calls.append({
                "id": "mock",
                "title": mock_data.get("title", "Digital arrest call (synthetic mock)"),
                "label": "scam",
                "lang": mock_data.get("lang", "hi-IN"),
                "duration_s": 48.6,
                "modes": ["mock"],
            })
        except Exception:
            calls.append({"id": "mock", "title": "Mock call", "label": "scam", "lang": "hi-IN", "duration_s": 48.6, "modes": ["mock"]})

    # Read manifest if present
    manifest_path = Path("data/calls/manifest.json")
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            for item in manifest_data:
                cid = item.get("id")
                modes = []
                wav_path = Path("data/calls") / f"{cid}.wav"
                if wav_path.exists() or Path(item.get("audio_path", "")).exists():
                    modes.append("file")
                rep_path = Path("data/transcripts") / f"{cid}.jsonl"
                if rep_path.exists():
                    modes.append("replay")
                if modes:
                    calls.append({
                        "id": cid,
                        "title": item.get("title", cid),
                        "label": item.get("label", "scam"),
                        "lang": item.get("lang", "hi-IN"),
                        "duration_s": item.get("duration_s", 0.0),
                        "modes": modes,
                    })
        except Exception:
            pass

    return {"calls": calls}


@app.post("/api/session/start")
async def start_session(body: SessionStartBody):
    if not (0 < body.careful < body.danger <= 100):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Thresholds must satisfy 0 < careful < danger <= 100",
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


@app.get("/api/audio/{name}.wav")
async def get_audio(name: str):
    # Reject path traversal (slashes or dots)
    if "/" in name or "\\" in name or ".." in name or "." in name:
        raise HTTPException(status_code=400, detail="Invalid audio filename")

    audio_path = Path("data/cache/warnings") / f"{name}.wav"
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path, media_type="audio/wav")


@app.get("/api/usage")
async def get_usage():
    data = usage.read()
    data["caps"] = {
        "max_tts_chars_per_run": settings.max_tts_chars_per_run,
        "max_stt_seconds_per_run": settings.max_stt_seconds_per_run,
    }
    return data


@app.get("/api/eval")
async def get_eval():
    eval_file = Path("data/eval/results.json")
    if not eval_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "no_results"},
        )
    with open(eval_file, "r", encoding="utf-8") as f:
        return json.load(f)


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
    allowed = {"http://localhost:8000", "http://127.0.0.1:8000"}
    origin = websocket.headers.get("origin", "")
    if (origin and origin not in allowed) or not session_id:
        await websocket.close(code=1008)
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
