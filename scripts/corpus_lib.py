"""Corpus loading, turn validation, assembly, and audio generation library."""

import io
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import soundfile as sf

DEFAULT_CALLER_VOICE = "Avinash"
DEFAULT_LISTENER_VOICE = "Chetana"


@dataclass
class Call:
    id: str
    title: str
    label: str  # "scam" or "legit"
    lang: str
    split: str  # "dev" or "test"
    cue_turn: Optional[int]
    caller_voice: str
    listener_voice: str
    turns: List[Tuple[str, str]]  # list of (speaker, text)
    script_path: str = ""


@dataclass
class BuiltCall:
    clean_path: str
    duration_s: float
    first_cue_s: Optional[float]
    chars: int


def _validate_call(c: Dict[str, Any], split: str, script_path: str) -> Call:
    cid = c.get("id")
    if not cid or not isinstance(cid, str):
        raise ValueError(f"Call missing valid id: {c}")

    label = c.get("label")
    if label not in ("scam", "legit"):
        raise ValueError(f"Call {cid}: invalid label '{label}', must be 'scam' or 'legit'")

    turns_raw = c.get("turns")
    if not isinstance(turns_raw, list) or len(turns_raw) == 0:
        raise ValueError(f"Call {cid}: turns must be non-empty list")

    turns: List[Tuple[str, str]] = []
    for idx, t in enumerate(turns_raw):
        if not isinstance(t, list) or len(t) != 2 or t[0] not in ("C", "L") or not isinstance(t[1], str):
            raise ValueError(f"Call {cid}: turn {idx} must be ['C'|'L', text], got {t}")
        text = t[1]
        # Check no ASCII letters
        if re.search(r"[a-zA-Z]", text):
            raise ValueError(f"Call {cid}: turn {idx} contains ASCII letters: '{text}'")
        # Check no run of 7 or more digits
        if re.search(r"\d{7,}", text):
            raise ValueError(f"Call {cid}: turn {idx} contains run of >=7 digits: '{text}'")
        turns.append((t[0], text))

    cue = c.get("cue_turn")
    if label == "scam":
        if cue is None or not isinstance(cue, int) or cue < 0 or cue >= len(turns):
            raise ValueError(f"Call {cid}: scam call must have integer cue_turn in [0, {len(turns)-1}], got {cue}")
    else:
        if cue is not None:
            raise ValueError(f"Call {cid}: legit call must have cue_turn=null, got {cue}")

    caller_voice = c.get("caller_voice", DEFAULT_CALLER_VOICE)
    listener_voice = c.get("listener_voice", DEFAULT_LISTENER_VOICE)

    return Call(
        id=cid,
        title=c.get("title", cid),
        label=label,
        lang=c.get("lang", "hi-IN"),
        split=split,
        cue_turn=cue,
        caller_voice=caller_voice,
        listener_voice=listener_voice,
        turns=turns,
        script_path=script_path,
    )


def load_scripts(paths: List[Union[str, Path]]) -> List[Call]:
    """Load and validate call scripts from json files."""
    calls: List[Call] = []
    seen_ids: set[str] = set()

    for p in paths:
        path_obj = Path(p)
        with open(path_obj, "r", encoding="utf-8") as f:
            data = json.load(f)
        split = data.get("split", "dev")
        for item in data.get("calls", []):
            call = _validate_call(item, split, str(path_obj))
            if call.id in seen_ids:
                raise ValueError(f"Duplicate call id found: {call.id}")
            seen_ids.add(call.id)
            calls.append(call)

    return calls


def assemble(
    arrays: List[np.ndarray],
    rate: int,
    cue_turn: Optional[int] = None,
) -> Tuple[np.ndarray, List[Tuple[int, float, float]], Optional[float]]:
    """Assemble turn audio arrays with exact pacing.

    0.4 s silence at start, 0.7 s between turns, 1.0 s at end.
    Returns (assembled_audio, timeline, first_cue_s).
    """
    start_silence = np.zeros(int(0.4 * rate), dtype=np.float32)
    turn_silence = np.zeros(int(0.7 * rate), dtype=np.float32)
    end_silence = np.zeros(int(1.0 * rate), dtype=np.float32)

    pieces: List[np.ndarray] = [start_silence]
    current_sample = len(start_silence)
    timeline: List[Tuple[int, float, float]] = []
    first_cue_s: Optional[float] = None

    for idx, arr in enumerate(arrays):
        t_start = current_sample / float(rate)
        pieces.append(arr.astype(np.float32))
        current_sample += len(arr)
        t_end = current_sample / float(rate)
        timeline.append((idx, round(t_start, 3), round(t_end, 3)))

        if cue_turn is not None and idx == cue_turn:
            first_cue_s = round(t_start, 3)

        if idx < len(arrays) - 1:
            pieces.append(turn_silence)
            current_sample += len(turn_silence)

    pieces.append(end_silence)
    assembled = np.concatenate(pieces)
    return assembled, timeline, first_cue_s


async def build_call(
    call: Call,
    tts: Callable,
    out_dir: Union[str, Path],
    model: str = "timbre-v3.0",
    language: str = "hi-IN",
) -> BuiltCall:
    """Synthesize each turn of a call, assemble into a clean WAV, and return BuiltCall."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rate = 24000

    arrays: List[np.ndarray] = []
    total_chars = 0

    for speaker, text in call.turns:
        total_chars += len(text)
        voice = call.caller_voice if speaker == "C" else call.listener_voice
        res = await tts(
            text,
            voice=voice,
            model=model,
            language=language,
            sample_rate=rate,
        )
        wav_bytes = res.audio if isinstance(res.audio, bytes) else b""
        with io.BytesIO(wav_bytes) as buf:
            arr, sr = sf.read(buf, dtype="float32")
            if sr != rate:
                raise ValueError(f"Expected rate {rate}, got {sr}")
            arrays.append(arr)

    assembled, timeline, first_cue_s = assemble(arrays, rate=rate, cue_turn=call.cue_turn)
    clean_path = out_dir / f"{call.id}__clean.wav"
    sf.write(str(clean_path), assembled, rate, subtype="PCM_16")

    duration_s = round(len(assembled) / float(rate), 3)
    return BuiltCall(
        clean_path=str(clean_path),
        duration_s=duration_s,
        first_cue_s=first_cue_s,
        chars=total_chars,
    )
