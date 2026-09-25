# Plain Downloader

A minimal, stress-free personal video downloader. No signup, no accounts,
no history — paste a URL, pick a format, get the file. Built as a thin UI
around [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense / public domain).
All credit for the actual extraction/download engine goes to the yt-dlp
project and its contributors.

## Structure
- `backend/` — FastAPI service that wraps yt-dlp (`/formats`, `/download`)
- `frontend/` — single static `index.html`, no build step

## Deploy (free)

### 1. Backend → Render.com (free web service)
1. Push the `backend/` folder to a GitHub repo (or the whole project — Render
   lets you set a root directory).
2. On [render.com](https://render.com): **New → Web Service** → connect the repo.
3. Render will detect the `Dockerfile` automatically. Leave build/start
   commands blank (the Dockerfile handles it).
4. Deploy. Copy the resulting URL, e.g. `https://plain-downloader.onrender.com`.

Note: free tier sleeps after ~15 min idle and wakes on the next request
(a few seconds' delay) — fine for personal, occasional use.

### 2. Frontend → Cloudflare Pages (free)
1. Open `frontend/index.html` and replace:
   ```js
   const API_BASE = "https://your-backend.onrender.com";
   ```
   with your actual Render URL from step 1.
2. On [pages.cloudflare.com](https://pages.cloudflare.com): **Create project**
   → connect the repo → set build output directory to `frontend`
   (no build command needed, it's static).
3. Deploy. You'll get a `https://your-project.pages.dev` URL.

### 3. Tighten CORS (optional but recommended)
In `backend/main.py`, change:
```python
allow_origins=["*"]
```
to your actual Pages URL, e.g. `["https://your-project.pages.dev"]`.
Redeploy the backend.

## Local testing
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
Then open `frontend/index.html` directly in a browser with
`API_BASE = "http://localhost:8000"`.
