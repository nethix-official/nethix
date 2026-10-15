import io
import os
import re
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, request, send_file
import yt_dlp

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4096
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "").rstrip("/")
MAX_BYTES = 75 * 1024 * 1024
semaphore = threading.BoundedSemaphore(2)
DOMAINS = ("youtube.com", "youtu.be", "tiktok.com", "facebook.com", "fb.watch")

@app.after_request
def cors(response):
    if FRONTEND_ORIGIN and request.headers.get("Origin") == FRONTEND_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = FRONTEND_ORIGIN
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

@app.get("/")
def health():
    return jsonify(name="NETHIX 1.0", status="online")

@app.route("/api/download", methods=["POST", "OPTIONS"])
def download():
    if request.method == "OPTIONS":
        return ("", 204)
    data = request.get_json(silent=True) or {}
    url = data.get("url", "")
    if not isinstance(url, str) or len(url) > 2048:
        return jsonify(error="Invalid link."), 400
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        valid = (parsed.scheme == "https" and not parsed.username and not parsed.password
                 and parsed.port in (None, 443) and
                 any(host == d or host.endswith("." + d) for d in DOMAINS))
    except ValueError:
        valid = False
    if not valid:
        return jsonify(error="Use a supported HTTPS YouTube, TikTok or Facebook link."), 400
    if not semaphore.acquire(blocking=False):
        return jsonify(error="Server is busy. Please retry shortly."), 429
    try:
        with tempfile.TemporaryDirectory(prefix="nethix_") as directory:
            options = {
                "format": "best[ext=mp4][height<=720][filesize<75M]/best[ext=mp4][height<=720]/best[height<=720]",
                "outtmpl": str(Path(directory) / "video.%(ext)s"),
                "noplaylist": True, "quiet": True, "no_warnings": True,
                "socket_timeout": 15, "retries": 1, "fragment_retries": 1,
                "max_filesize": MAX_BYTES, "match_filter": yt_dlp.utils.match_filter_func("duration <= 600"),
                "ignoreerrors": False,
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("No downloadable video was found.")
            files = [p for p in Path(directory).iterdir() if p.is_file() and p.suffix.lower() in (".mp4", ".webm", ".mkv")]
            if len(files) != 1 or files[0].stat().st_size > MAX_BYTES:
                raise ValueError("Video is unavailable or exceeds the 75 MB limit.")
            path = files[0]
            payload = path.read_bytes()
            mime = {".mp4":"video/mp4", ".webm":"video/webm", ".mkv":"video/x-matroska"}[path.suffix.lower()]
            return send_file(io.BytesIO(payload), mimetype=mime, as_attachment=True,
                             download_name="NETHIX_video" + path.suffix)
    except Exception:
        app.logger.exception("Media download failed")
        return jsonify(error="This video could not be downloaded. It may be restricted, unavailable, too large, or unsupported."), 422
    finally:
        semaphore.release()
