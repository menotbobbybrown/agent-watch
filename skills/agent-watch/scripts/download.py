#!/usr/bin/env python3
"""Download a video via yt-dlp, or resolve a local file path.

Also fetches subtitles (manual first, then auto-generated) in VTT format so
transcribe.py can parse them without needing Whisper.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi", ".flv", ".wmv"}

# YouTube tags spoken-language auto-captions "<lang>-orig" (e.g. "tr-orig").
SUB_LANGS = ".*-orig,en.*"


def is_url(source: str) -> bool:
    if source.startswith("-"):
        return False
    parsed = urlparse(source)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _is_youtube(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def resolve_local(path: str) -> dict:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise SystemExit(f"File not found: {p}")
    if p.suffix.lower() not in VIDEO_EXTS:
        print(
            f"[agent-watch] warning: {p.suffix} is not a known video extension, proceeding anyway",
            file=sys.stderr,
        )
    return {
        "video_path": str(p),
        "subtitle_path": None,
        "info": {"title": p.name, "url": str(p)},
        "downloaded": False,
    }


def _pick_subtitle(out_dir: Path) -> Path | None:
    candidates = sorted(out_dir.glob("video*.vtt"))
    if not candidates:
        return None
    for markers in (("-orig.",), (".en.", ".en-US.", ".en-GB.")):
        for c in candidates:
            if any(m in c.name for m in markers):
                return c
    return candidates[0]


def _pick_video(out_dir: Path) -> Path | None:
    for ext in (".mp4", ".mkv", ".webm", ".mov", ".m4a", ".mp3", ".opus"):
        for candidate in out_dir.glob(f"video*{ext}"):
            return candidate
    for candidate in out_dir.glob("video.*"):
        if candidate.suffix.lower() in VIDEO_EXTS:
            return candidate
    return None


def fetch_captions(url: str, out_dir: Path, sub_lang_override: str | None = None) -> dict:
    """Fetch metadata and best available VTT captions without downloading video."""
    if shutil.which("yt-dlp") is None:
        raise SystemExit("yt-dlp is not installed. Install with: brew install yt-dlp or pip install yt-dlp")

    out_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(out_dir / "video.%(ext)s")
    sub_pattern = sub_lang_override or SUB_LANGS
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-info-json",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", sub_pattern,
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        "--no-playlist",
        "--ignore-errors",
        "-o", output_template,
        "--",
        url,
    ]
    subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
    subtitle = _pick_subtitle(out_dir)
    info = _read_info(out_dir / "video.info.json", url)
    return {
        "video_path": None,
        "subtitle_path": str(subtitle) if subtitle else None,
        "info": info or {"url": url},
        "downloaded": False,
    }


def _read_info(info_path: Path, url: str) -> dict:
    info: dict = {}
    if info_path.exists():
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return info


def download_url(
    url: str,
    out_dir: Path,
    audio_only: bool = False,
    browser_cookies: str | None = None,
    sub_lang_override: str | None = None,
) -> dict:
    if shutil.which("yt-dlp") is None:
        raise SystemExit("yt-dlp is not installed. Install with: brew install yt-dlp or pip install yt-dlp")

    out_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(out_dir / "video.%(ext)s")
    sub_pattern = sub_lang_override or SUB_LANGS
    fmt = "ba/bestaudio" if audio_only else "bv*[height<=720]+ba/b[height<=720]/bv+ba/b"

    common = [
        "-N", "8",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", sub_pattern,
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        "--no-playlist",
        "--ignore-errors",
        "-o", output_template,
    ]

    cmd = ["yt-dlp", *common, "-f", fmt, "--", url]
    subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
    video = _pick_video(out_dir)

    # Fallback for YouTube 403 HTTP stream errors
    if video is None and _is_youtube(url):
        print(
            "[agent-watch] media download failed (likely YouTube 403). Retrying via android/mweb player clients...",
            file=sys.stderr,
        )
        fallback_fmt = fmt if audio_only else "18/bv*[height<=720]+ba/b[height<=720]/b"
        fallback_cmd = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android,mweb,tv,ios",
            *common,
            "-f", fallback_fmt,
            "--",
            url,
        ]
        subprocess.run(fallback_cmd, stdout=sys.stderr, stderr=sys.stderr)
        video = _pick_video(out_dir)

    # Fallback for login-gated downloads with browser cookies
    if video is None:
        browsers_to_try = [browser_cookies] if browser_cookies else ["chrome", "brave", "firefox", "edge", "safari"]
        for b in browsers_to_try:
            if not b:
                continue
            print(f"[agent-watch] Retrying download with browser cookies from {b}...", file=sys.stderr)
            cookie_cmd = ["yt-dlp", "--cookies-from-browser", b, *common, "-f", fmt, "--", url]
            subprocess.run(cookie_cmd, stdout=sys.stderr, stderr=sys.stderr)
            video = _pick_video(out_dir)
            if video is not None:
                break

    if video is None:
        raise SystemExit(
            f"yt-dlp could not download video from {url}. Check that the URL is valid and accessible."
        )

    subtitle = _pick_subtitle(out_dir)
    info = _read_info(out_dir / "video.info.json", url)

    return {
        "video_path": str(video),
        "subtitle_path": str(subtitle) if subtitle else None,
        "info": info or {"url": url},
        "downloaded": True,
    }


def download(
    source: str,
    out_dir: Path,
    audio_only: bool = False,
    browser_cookies: str | None = None,
    sub_lang_override: str | None = None,
) -> dict:
    if is_url(source):
        return download_url(source, out_dir, audio_only=audio_only, browser_cookies=browser_cookies, sub_lang_override=sub_lang_override)
    return resolve_local(source)
