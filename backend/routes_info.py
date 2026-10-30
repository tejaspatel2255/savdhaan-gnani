"""Information, calls catalog, audio files, and usage routes."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from backend.config import settings
from backend import usage

router = APIRouter()


@router.get("/api/calls")
async def get_calls():
    """List available mock and real calls."""
    calls = []
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


@router.get("/api/audio/{name}.wav")
async def get_audio(name: str):
    if "/" in name or "\\" in name or ".." in name or "." in name:
        raise HTTPException(status_code=400, detail="Invalid audio filename")

    audio_path = Path("data/cache/warnings") / f"{name}.wav"
    if not audio_path.exists():
        audio_path = Path("frontend/assets/audio") / f"{name}.wav"
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path, media_type="audio/wav")


@router.get("/api/usage")
async def get_usage():
    data = usage.read()
    data["caps"] = {
        "max_tts_chars_per_run": settings.max_tts_chars_per_run,
        "max_stt_seconds_per_run": settings.max_stt_seconds_per_run,
    }
    return data


@router.get("/api/eval")
async def get_eval():
    eval_file = Path("data/eval/results.json")
    if not eval_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "no_results"},
        )
    with open(eval_file, "r", encoding="utf-8") as f:
        return json.load(f)
