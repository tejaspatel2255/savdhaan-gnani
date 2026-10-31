# Third-Party Dependencies and Licensing

Savdhaan incorporates carefully selected open-source libraries, runtimes, and external assets to ensure determinism, accessibility, and zero-leakage security.

## Python Runtime Dependencies

| Library / Package | Version Range | License | Purpose in Savdhaan |
| :--- | :--- | :--- | :--- |
| `fastapi` | `>=0.115.0` | MIT | Asynchronous REST and WebSocket API endpoints |
| `uvicorn` | `>=0.30.0` | BSD-3-Clause | ASGI server implementation |
| `websockets` | `>=13.0` | BSD-3-Clause | Gnani Prisma v2.5 streaming WebSocket client |
| `httpx` | `>=0.27.0` | BSD-3-Clause | HTTP client for Gnani Timbre TTS & REST STT |
| `pydantic` | `>=2.8.0` | MIT | Strongly typed event schemas and data validation |
| `soundfile` | `>=0.12.0` | BSD-3-Clause | Audio file I/O for 24kHz mono PCM generation |
| `numpy` | `>=1.26.0` | BSD-3-Clause | Telephony bandpass filtering & audio signal processing |
| `python-dotenv` | `>=1.0.0` | BSD-3-Clause | Local environment variable management (`.env`) |
| `pyyaml` | `>=6.0` | MIT | Structured configuration and test fixture parsing |
| `jiwer` | `>=3.0.0` | Apache-2.0 | Word Error Rate (WER) & Character Error Rate (CER) calculation |
| `pytest` | `>=8.0.0` | MIT | Unit and integration test framework |

## Frontend Assets

| Asset | Source / Author | License | Description |
| :--- | :--- | :--- | :--- |
| **Google Fonts** (`Cinzel`, `JetBrains Mono`, `Noto Sans Devanagari`, `Noto Sans Gujarati`) | Google Fonts / Open Font Contributors | [SIL Open Font License 1.1](https://scripts.sil.org/OFL) | High-legibility typography for English and Indic scripts. System fallbacks ensure graceful rendering offline. |
| Handcrafted Inline SVGs | Savdhaan Project | MIT | Nazar eye, receipt tape textures, stamps, and shield icons (zero external CDN or icon libraries). |

## System Tools & Optional Runtimes

| Tool | Minimum Version | License | Usage |
| :--- | :--- | :--- | :--- |
| **FFmpeg** | `4.x+` (tested 8.1.1) | LGPL v2.1+ / GPL v2+ | Audio resynthesis, telephony filtering, and benchmark noise injection. |
| **Playwright** | `>=1.40.0` | Apache-2.0 | Optional headless browser verification for automated DOM snapshots. |
