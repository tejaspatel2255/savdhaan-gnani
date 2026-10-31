# Deployment Guide: Savdhaan

Savdhaan supports two deployment targets:
1. **Hosted Static Demo (Vercel)**: Zero backend, zero API credits, plays bundled recorded sessions and warning audio for evaluators.
2. **Full Live Service (Render)**: Full FastAPI backend with live WebSocket streaming to Gnani Prisma v2.5.

---

## 1. Deploying the Static Demo to Vercel (Recommended for Judges)

The static frontend runs without any Python server or environment variables:

1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository (`savdhaan-gnani`).
4. In the **Project Configuration** panel:
   - **Framework Preset**: Select `Other` (or leave default detected by `vercel.json`).
   - **Root Directory**: Leave `./` (the root containing `vercel.json`).
   - **Build Command**: Leave empty / disabled.
   - **Output Directory**: Ensure it uses `frontend` (as defined in `vercel.json`).
   - **Install Command**: Leave empty / disabled.
5. Click **Deploy**.
6. Deployment completes in under 15 seconds. Verify that `/` opens the Nazar Control Room and `/report.html` displays the Khata ledger.

---

## 2. Deploying Full Live Backend to Render

1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Select your repository `savdhaan-gnani`.
4. Configure service settings:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `./start.sh`
5. Under **Environment Variables**, add:
   - `GNANI_API_KEY`: Your confidential Gnani AI API key.
   - `MAX_TTS_CHARS_PER_RUN`: `600`
   - `MAX_STT_SECONDS_PER_RUN`: `180`
   - `PYTHONUNBUFFERED`: `1`
6. Click **Create Web Service**. Once live, open the Render URL to use live microphone streaming.
