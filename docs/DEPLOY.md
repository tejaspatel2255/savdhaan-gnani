# Deploying Savdhaan (Static Demo on Vercel)

This deployment hosts a **STATIC recorded demo** of Savdhaan for public evaluation, with **no backend and no Gnani API keys**.

## Why Static Deployment?

1. **Security & Zero Credit Leakage**: The live mode connects directly to Gnani Prisma and Timbre using your `GNANI_API_KEY`. Deploying the live backend publicly would allow unauthorized visitors to exhaust your programme credits.
2. **In-Memory Concurrency**: The live backend manages real-time session state in memory (designed for local defense on a citizen's personal device).
3. **Zero Configuration**: Vercel serves the deterministic, explainable playback interface directly with zero secrets.

## How to Deploy on Vercel

1. **Push to GitHub**:
   Ensure all changes are pushed to your repository branch:
   ```bash
   git push origin main
   ```

2. **Import Project into Vercel**:
   - Go to your Vercel Dashboard -> **Add New Project**.
   - Select your Savdhaan GitHub repository and click **Import**.

3. **Configure Project Settings**:
   - **Framework Preset**: Select `Other`.
   - **Root Directory**: Leave as `./` (the root).
   - **Build Command**: Leave empty (override toggled on).
   - **Install Command**: Leave empty (override toggled on).
   - **Output Directory**: `frontend`.

4. **Environment Variables**:
   - **DO NOT add `GNANI_API_KEY` to Vercel**.
   - No database or backend environment variables are needed. Nothing is stored.

5. **Deploy**:
   Click **Deploy**. Your static demo will be live at `https://<your-project>.vercel.app`.

## What Works on the Deployed Demo

- **Sample Scam Call**: Full real-time playback with Eye, Tape, Stamp, Why signals, and Phone warning.
- **Sample Normal Call**: Bank EMI reminder playback demonstrating zero false alarms (calm state).
- **Evaluation Khata**: `/report.html` renders all benchmark metrics directly from `frontend/assets/results.json`.
- **Language Switcher**: Hindi and Gujarati labels.
