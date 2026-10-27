# Deploying Savdhaan

Two deployment paths are available depending on what you need.

---

## Option A — Static Demo on Vercel (no backend, no API key)

This hosts a **recorded playback demo** only. No Gnani API calls are made.
Live mic mode, file mode and real scam detection are **not available**.

### Why use this?

- Zero credit leakage — no `GNANI_API_KEY` is required or exposed.
- Works on Vercel's serverless platform (no persistent WebSocket needed).
- Good for public evaluation links and the challenge submission demo video.

### Steps

1. **Push to GitHub**:
   ```bash
   git push origin main
   ```

2. **Import Project into Vercel**:
   - Go to your Vercel Dashboard → **Add New Project**.
   - Select your Savdhaan GitHub repository and click **Import**.

3. **Configure Project Settings**:
   - **Framework Preset**: `Other`
   - **Root Directory**: `./`
   - **Build Command**: *(leave empty, toggle override on)*
   - **Install Command**: *(leave empty, toggle override on)*
   - **Output Directory**: `frontend`

4. **Environment Variables**:
   - **Do NOT add `GNANI_API_KEY`** to Vercel.
   - No other secrets are needed.

5. **Deploy**: Click **Deploy**. Your demo will be live at `https://<your-project>.vercel.app`.

### What works on the static demo

| Feature | Status |
|---|---|
| Sample Scam Call playback (Eye, Tape, Stamp, Why, Phone warning) | ✅ |
| Sample Normal Call (bank EMI reminder, zero false alarm) | ✅ |
| Evaluation Khata (`/report.html`) | ✅ |
| Language switcher (Hindi / Gujarati) | ✅ |
| Live microphone mode | ❌ (backend required) |
| File upload mode | ❌ (backend required) |

---

## Option B — Full Stack on Render.com (live mic + real Gnani calls)

This runs the **complete FastAPI backend** alongside the frontend.
Real-time mic capture, Gnani Prisma STT, scam scoring and Gnani Timbre TTS
warnings all work. **Requires your `GNANI_API_KEY`.**

> [!IMPORTANT]
> Keep `GNANI_API_KEY` in Render's dashboard as a **Secret** environment variable.
> Never commit it to git or paste it into `render.yaml`.

### Steps

1. **Push to GitHub** (Procfile and render.yaml must be committed):
   ```bash
   git add Procfile render.yaml
   git push origin main
   ```

2. **Create a Render Web Service**:
   - Go to [render.com](https://render.com) → **New** → **Web Service**.
   - Connect your GitHub repository.
   - Render will detect `render.yaml` automatically (Blueprint deploy).
   - If not, set manually:
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables in the Render Dashboard**:

   | Variable | Value | Note |
   |---|---|---|
   | `GNANI_API_KEY` | `<your key>` | Mark as **Secret** |
   | `DEMO` | `0` | Enables live modes |
   | `ALLOWED_ORIGINS` | `https://<your-app>.onrender.com` | Set after first deploy |
   | `MAX_TTS_CHARS_PER_RUN` | `600` | Credit guard |
   | `MAX_STT_SECONDS_PER_RUN` | `180` | Credit guard |
   | `SAVE_LIVE_RUNS` | `false` | Privacy |

4. **First Deploy**:
   - Click **Deploy**. Wait for the build to finish (≈ 2 min).
   - Note your public URL: `https://<your-app>.onrender.com`.

5. **Update `ALLOWED_ORIGINS`**:
   - In Render Dashboard → your service → **Environment** tab.
   - Set `ALLOWED_ORIGINS` = `https://<your-app>.onrender.com`.
   - Click **Save Changes** — Render will redeploy automatically.

6. **Verify**:
   - Open `https://<your-app>.onrender.com` in the browser.
   - The source badge should show **LIVE MIC** (not STATIC DEMO).
   - Start a session in FILE mode with one of the sample scripts to confirm
     Gnani Prisma responds.

### Free tier note

Render's free tier **sleeps after 15 minutes of inactivity**.
The first request after a sleep takes ≈ 30 s to wake up.
For the demo video, open the page once, wait for the wake-up spinner to clear,
then start recording.

---

## Choosing between A and B

| Need | Use |
|---|---|
| Public demo link, no API key required | Option A (Vercel) |
| Full live experience for judging | Option B (Render) |
| Local development | `uvicorn backend.main:app --reload --port 8000` |
