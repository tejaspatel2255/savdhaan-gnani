"""Warning audio management, synthesis, and text mapping."""

import io
import os
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.config import settings as global_settings
from backend.gnani_tts import synthesize as default_synthesize

WARNINGS: Dict[str, Dict[str, str]] = {
    "hi-IN": {
        "generic": "सावधान! यह कॉल धोखाधड़ी हो सकती है। कोई ओटीपी या पैसे न दें। कॉल काट दें और अपने परिवार को बताएं।",
        "arrest": "सावधान! असली पुलिस या सीबीआई फोन पर गिरफ्तारी की धमकी नहीं देती। पैसे न भेजें। कॉल काट दें।",
        "otp": "सावधान! बैंक कभी फोन पर ओटीपी या पिन नहीं माँगता। इसे किसी को न बताएं। कॉल काट दें।",
        "money": "सावधान! सेफ अकाउंट जैसी कोई चीज़ नहीं होती। पैसे न भेजें। कॉल काट दें और किसी अपने से बात करें।",
        "remote": "सावधान! कोई ऐप डाउनलोड न करें और अपनी स्क्रीन शेयर न करें। कॉल काट दें।",
    },
    "en-IN": {
        "generic": "Be careful! This call may be a scam. Do not share any OTP or send money. Hang up and tell your family.",
        "arrest": "Be careful! Real police never threaten arrest over a phone call. Do not send money. Hang up now.",
        "otp": "Be careful! Banks never ask for your OTP or PIN on a call. Do not share it. Hang up now.",
        "money": "Be careful! There is no such thing as a safe account. Do not send money. Hang up and talk to someone you trust.",
        "remote": "Be careful! Do not install any app or share your screen. Hang up now.",
    },
    "gu-IN": {
        "generic": "સાવધાન રહો, આ ફોન કોલ છેતરપિંડી હોઈ શકે છે. તમારી અંગત માહિતી શેર કરશો નહીં અને ફોન કાપી નાખો.",
        "arrest": "ધ્યાન આપો, કોઈ સરકારી અધિકારી ફોન પર ધરપકડની ધમકી આપતા નથી. ગભરાશો નહીં અને તરત જ કોલ કાપો.",
        "otp": "ચેતવણી, બેંક ક્યારેય ઓટીપી અથવા પિન માંગતી નથી. કોઈને પણ ઓટીપી આપશો નહીં અને કોલ બંધ કરો.",
        "money": "સાવચેત રહો, વેરિફિકેશન માટે કોઈ સુરક્ષિત ખાતામાં પૈસા મોકલવા જરૂરી નથી. કોઈને પણ રૂપિયા ટ્રાન્સફર ન કરો.",
        "remote": "ચેતવણી, અજાણ્યા વ્યક્તિના કહેવાથી એનીડેસ્ક કે કોઈ એપ ડાઉનલોડ કરશો નહીં. સ્ક્રીન શેર ન કરો અને કોલ કાપો.",
    },
}

CACHE_DIR = Path("data/cache/warnings")


@dataclass
class WarningAudio:
    name: str
    url: str
    duration_s: float
    cached: bool
    text: str


def pick_key(reasons: List[Any]) -> str:
    """Look at categories of all reasons. Priority: remote_app -> remote, payment -> money,
    credentials -> otp, threat -> arrest, otherwise generic.
    """
    categories = [getattr(r, "category", "") if not isinstance(r, dict) else r.get("category", "") for r in reasons]
    if "remote_app" in categories:
        return "remote"
    if "payment" in categories:
        return "money"
    if "credentials" in categories:
        return "otp"
    if "threat" in categories:
        return "arrest"
    return "generic"


def family_message(lang: str, reasons: List[Any]) -> str:
    """Generate family alert message."""
    first_reason = reasons[0] if reasons else None
    if isinstance(first_reason, dict):
        label_hi = first_reason.get("label_hi", "संदिग्ध गतिविधि")
        label_en = first_reason.get("label_en", "suspicious activity")
    elif first_reason is not None:
        label_hi = getattr(first_reason, "label_hi", "संदिग्ध गतिविधि")
        label_en = getattr(first_reason, "label_en", "suspicious activity")
    else:
        label_hi = "संदिग्ध गतिविधि"
        label_en = "suspicious activity"

    if lang == "hi-IN":
        return f"सावधान: आपके परिवार के सदस्य को एक संदिग्ध कॉल आ रही है ({label_hi})। कृपया उन्हें अभी फोन करें।"
    return f"Savdhaan alert: your family member is on a suspected scam call ({label_en}). Please call them now."


async def get_warning(
    lang: str,
    key: str,
    *,
    voice: str,
    model: str,
    dry_run: bool = False,
    tts_func: Optional[Callable] = None,
) -> WarningAudio:
    """Retrieve or synthesize warning audio file.

    Atomically writes to data/cache/warnings/warn_<lang>_<key>_<voice>.wav (lowercase).
    """
    actual_lang = lang if lang in WARNINGS else "en-IN"
    lang_warnings = WARNINGS[actual_lang]
    actual_key = key if key in lang_warnings else "generic"
    text = lang_warnings[actual_key]

    clean_lang = actual_lang.lower().replace("-", "_")
    name = f"warn_{clean_lang}_{actual_key.lower()}_{voice.lower()}"
    file_path = CACHE_DIR / f"{name}.wav"
    url = f"/api/audio/{name}.wav"

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        # Read duration from WAV
        try:
            with wave.open(str(file_path), "rb") as wf:
                duration_s = round(wf.getnframes() / float(wf.getframerate()), 2)
        except Exception:
            duration_s = 3.0
        return WarningAudio(name=name, url=url, duration_s=duration_s, cached=True, text=text)

    # Synthesize
    tts = tts_func or default_synthesize
    res = await tts(
        text=text,
        voice=voice,
        model=model,
        language=actual_lang,
        dry_run=dry_run,
    )

    if dry_run:
        return WarningAudio(name=name, url=url, duration_s=3.0, cached=False, text=text)

    audio_bytes = res.audio if isinstance(res.audio, bytes) else b""

    # Write atomically
    temp_file = tempfile.NamedTemporaryFile("wb", dir=CACHE_DIR, delete=False)
    try:
        temp_file.write(audio_bytes)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        os.replace(temp_file.name, file_path)
    except Exception:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise

    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            duration_s = round(wf.getnframes() / float(wf.getframerate()), 2)
    except Exception:
        duration_s = 3.0

    return WarningAudio(name=name, url=url, duration_s=duration_s, cached=False, text=text)
