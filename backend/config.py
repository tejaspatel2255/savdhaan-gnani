"""Configuration and environment settings for Savdhaan."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application settings read from environment variables."""

    api_key: str = field(
        default_factory=lambda: os.getenv("GNANI_API_KEY", "").strip().strip('"').strip("'"),
        repr=False,
    )
    max_tts_chars_per_run: int = field(
        default_factory=lambda: int(os.getenv("MAX_TTS_CHARS_PER_RUN", "600"))
    )
    max_stt_seconds_per_run: int = field(
        default_factory=lambda: int(os.getenv("MAX_STT_SECONDS_PER_RUN", "180"))
    )
    thresh_careful: int = field(
        default_factory=lambda: int(os.getenv("THRESH_CAREFUL", "30"))
    )
    thresh_danger: int = field(
        default_factory=lambda: int(os.getenv("THRESH_DANGER", "60"))
    )
    save_live_runs: bool = field(
        default_factory=lambda: os.getenv("SAVE_LIVE_RUNS", "false").lower() in ("true", "1", "yes")
    )
    warning_voice: str = field(
        default_factory=lambda: os.getenv("WARNING_VOICE", "Shivani")
    )
    warning_model: str = field(
        default_factory=lambda: os.getenv("WARNING_MODEL", "timbre-v3.0")
    )
    scorer_packs: str = field(
        default_factory=lambda: os.getenv("SCORER_PACKS", "hi_en")
    )
    tts_credits_per_1k_chars: Optional[float] = field(
        default_factory=lambda: float(os.getenv("TTS_CREDITS_PER_1K_CHARS"))
        if os.getenv("TTS_CREDITS_PER_1K_CHARS") and os.getenv("TTS_CREDITS_PER_1K_CHARS").strip()
        else None
    )
    stt_credits_per_minute: Optional[float] = field(
        default_factory=lambda: float(os.getenv("STT_CREDITS_PER_MINUTE"))
        if os.getenv("STT_CREDITS_PER_MINUTE") and os.getenv("STT_CREDITS_PER_MINUTE").strip()
        else None
    )
    demo: bool = field(
        default_factory=lambda: os.getenv("DEMO", "0").lower() in ("1", "true", "yes")
    )
    allowed_origins: str = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "").strip()
    )
    allow_remote_live: bool = field(
        default_factory=lambda: os.getenv("ALLOW_REMOTE_LIVE", "0").lower() in ("1", "true", "yes")
    )

    @property
    def key_present(self) -> bool:
        """True if GNANI_API_KEY is non-empty."""
        return bool(self.api_key and self.api_key.strip())


# Default settings singleton
settings = Settings()
