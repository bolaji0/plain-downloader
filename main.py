"""
Plain Downloader — a minimal personal video downloader.

Built as a thin, personal-use wrapper around yt-dlp:
https://github.com/yt-dlp/yt-dlp (Unlicense — public domain)

All credit for the actual extraction/download engine goes to the
yt-dlp project and its contributors. This file just exposes two
small HTTP endpoints around it for a personal web UI.
"""

import os
import re
import shutil
import tempfile

import yt_dlp
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

app = FastAPI(
    title="Plain Downloader",
    description="Personal video downloader UI powered by yt-dlp (https://github.com/yt-dlp/yt-dlp).",
)

# Tighten this to your actual frontend domain once deployed
# (e.g. "https://your-project.pages.dev") instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
MAX_URL_LENGTH = 2048


def validate_url(url: str) -> None:
    if not url or len(url) > MAX_URL_LENGTH or not URL_PATTERN.match(url):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid http(s) URL.",
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/formats")
def list_formats(url: str = Query(..., description="Video page URL")):
    """Return the title and a clean list of downloadable formats for a URL."""
    validate_url(url)

    ydl_opts = {"quiet": True, "skip_download": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=422, detail=f"Couldn't read that URL: {e}")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error reading that URL.")

    formats = []
    for f in info.get("formats", []):
        # Skip entries with no usable audio or video stream
        if f.get("vcodec") in (None, "none") and f.get("acodec") in (None, "none"):
            continue
        is_audio_only = f.get("vcodec") in (None, "none")
        formats.append(
            {
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": "audio only" if is_audio_only else (f.get("resolution") or "unknown"),
                "note": f.get("format_note") or "",
                "filesize": f.get("filesize") or f.get("filesize_approx"),
            }
        )

    if not formats:
        raise HTTPException(status_code=422, detail="No downloadable formats found for that URL.")

    return {"title": info.get("title", "video"), "formats": formats}


@app.get("/download")
def download(
    url: str = Query(...),
    format_id: str = Query(..., description="format_id from /formats"),
):
    """Download the chosen format to a temp dir, stream it back, then delete it."""
    validate_url(url)

    tmpdir = tempfile.mkdtemp(prefix="plaindl_")
    outtmpl = os.path.join(tmpdir, "%(title).80s.%(ext)s")

    ydl_opts = {
        "quiet": True,
        "format": format_id,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # merge_output_format can change the final extension,
            # so fall back to scanning the temp dir if needed.
            if not os.path.exists(filename):
                candidates = os.listdir(tmpdir)
                if not candidates:
                    raise FileNotFoundError("No file produced.")
                filename = os.path.join(tmpdir, candidates[0])
    except yt_dlp.utils.DownloadError as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=422, detail=f"Download failed: {e}")
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="Unexpected error during download.")

    return FileResponse(
        path=filename,
        filename=os.path.basename(filename),
        media_type="application/octet-stream",
        background=BackgroundTask(shutil.rmtree, tmpdir, ignore_errors=True),
    )
