#!/usr/bin/env python3
"""agent-watch entry point: download video, extract frames, parse transcript.

Universal video watching engine for any AI agent in the world (Antigravity, OpenCode, Claude Code, Codex, Cursor, etc.).
Prints a markdown report to stdout listing frame paths + transcript.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# Force UTF-8 encoding on Windows consoles
for _stream in (sys.stdout, sys.stderr):
    reconfigure = getattr(_stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from config import frame_cap, get_config, cookies_from_browser, sub_langs  # noqa: E402
from download import download, fetch_captions, is_url  # noqa: E402
from frames import (  # noqa: E402
    MAX_FPS,
    auto_fps,
    auto_fps_focus,
    extract_at_timestamps,
    extract_keyframes,
    extract_scene_or_uniform,
    format_time,
    get_metadata,
    merge_frames,
    parse_time,
    parse_timestamps,
    resolve_fps_override,
)
from transcribe import filter_range, format_transcript, parse_vtt  # noqa: E402
from whisper import load_api_key, local_whisper_available, transcribe_local, transcribe_video, custom_endpoint  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="agent-watch",
        description="Universal video engine for any AI agent: download video, extract frames, and surface transcripts.",
    )
    ap.add_argument("source", help="Video URL or local file path")
    ap.add_argument("--max-frames", type=int, default=None, help="Override frame cap")
    ap.add_argument("--resolution", type=int, default=512, help="Frame width in pixels (default 512)")
    ap.add_argument("--fps", type=float, default=None, help="Override auto-fps")
    ap.add_argument(
        "--detail",
        choices=["transcript", "efficient", "balanced", "token-burner"],
        default=None,
        help="Fidelity/speed dial: transcript (no frames), efficient (fast keyframes, cap 50), "
             "balanced (scene, cap 100), token-burner (scene, uncapped).",
    )
    ap.add_argument(
        "--timestamps",
        type=str,
        default=None,
        help="Comma-separated absolute timestamps (SS, MM:SS, HH:MM:SS) to grab a frame at.",
    )
    ap.add_argument("--start", type=str, default=None, help="Range start (SS, MM:SS, or HH:MM:SS)")
    ap.add_argument("--end", type=str, default=None, help="Range end (SS, MM:SS, or HH:MM:SS)")
    ap.add_argument("--out-dir", type=str, default=None, help="Working directory (default: tmp)")
    ap.add_argument(
        "--no-whisper",
        action="store_true",
        help="Disable Whisper fallback. Report frames-only if no captions available.",
    )
    ap.add_argument(
        "--whisper",
        choices=["custom", "groq", "openai", "local", "gemini"],
        default=None,
        help="Force a specific Whisper backend (custom self-hosted, groq, openai, or local offline).",
    )
    ap.add_argument(
        "--cookies-from-browser",
        type=str,
        default=None,
        help="Browser to pull cookies from for login-gated hosts (chrome, brave, firefox, edge, safari).",
    )
    ap.add_argument(
        "--sub-lang",
        type=str,
        default=None,
        help="Preferred subtitle language pattern (default: .*-orig,en.*).",
    )
    ap.add_argument("--ocr", action="store_true", help="Run OCR text extraction on extracted frames (slides, terminal, code).")
    ap.add_argument("--diarize", action="store_true", help="Enable speaker diarization attribution.")
    ap.add_argument("--chapters", action="store_true", help="Generate automated topic chapter breakpoints.")
    ap.add_argument("--index", action="store_true", help="Index video and transcript into local searchable library.")
    ap.add_argument("--serve", action="store_true", help="Launch local web inspection dashboard (http://localhost:8888).")
    ap.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable near-duplicate frame removal.",
    )
    args = ap.parse_args()

    config = get_config()
    detail = args.detail or str(config["detail"])
    configured_cap = frame_cap(detail)
    max_frames = args.max_frames if args.max_frames is not None else configured_cap
    if max_frames is not None and max_frames < 1:
        raise SystemExit("--max-frames must be greater than zero")
    budget_cap = max_frames if max_frames is not None else 100
    cue_timestamps = parse_timestamps(args.timestamps)

    browser_cookies = args.cookies_from-browser if hasattr(args, "cookies_from-browser") and getattr(args, "cookies_from-browser") else (args.cookies_from_browser or cookies_from_browser())
    sub_lang_pattern = args.sub_lang or sub_langs()

    if args.out_dir:
        work = Path(args.out_dir).expanduser().resolve()
    else:
        work = Path(tempfile.mkdtemp(prefix="agent-watch-"))
    work.mkdir(parents=True, exist_ok=True)
    print(f"[agent-watch] working dir: {work}", file=sys.stderr)

    url_source = is_url(args.source)
    dl: dict = {"subtitle_path": None, "info": {}, "downloaded": False}
    transcript_segments: list[dict] = []
    transcript_text: str | None = None
    transcript_source: str | None = None
    video_path: str | None = None

    if url_source:
        print("[agent-watch] checking metadata/captions via yt-dlp...", file=sys.stderr)
        dl = fetch_captions(args.source, work / "download", sub_lang_override=sub_lang_pattern)
        if dl.get("subtitle_path"):
            try:
                transcript_segments = parse_vtt(dl["subtitle_path"])
                transcript_source = "captions"
            except Exception as exc:
                print(f"[agent-watch] caption parse failed: {exc}", file=sys.stderr)

    if not url_source or detail != "transcript" or cue_timestamps or (not transcript_segments and not args.no_whisper):
        if not dl.get("downloaded"):
            print("[agent-watch] downloading video...", file=sys.stderr)
            dl = download(args.source, work / "download", browser_cookies=browser_cookies, sub_lang_override=sub_lang_pattern)
        video_path = dl.get("video_path")

    if not video_path and not transcript_segments:
        raise SystemExit("Could not resolve video file or captions.")

    meta: dict = {}
    if video_path:
        meta = get_metadata(video_path)

    full_duration = float(meta.get("duration", 0.0))
    start_sec = parse_time(args.start)
    end_sec = parse_time(args.end)
    focused = start_sec is not None or end_sec is not None

    effective_start = start_sec if start_sec is not None else 0.0
    effective_end = end_sec if end_sec is not None else full_duration
    effective_duration = max(0.0, effective_end - effective_start)

    frames: list[dict] = []
    frame_meta: dict = {}
    cue_frames: list[dict] = []

    if video_path and cue_timestamps:
        cue_frames, _ = extract_at_timestamps(video_path, work / "frames", cue_timestamps, resolution=args.resolution)

    if video_path and detail != "transcript":
        if focused:
            fps, target = auto_fps_focus(effective_duration, max_frames=budget_cap)
            scope = f"focus range {format_time(effective_start)} -> {format_time(effective_end)}"
        else:
            fps, target = auto_fps(full_duration, max_frames=budget_cap)
            scope = f"full video ({format_time(full_duration)})"

        if args.fps is not None:
            fps = resolve_fps_override(args.fps, effective_duration if focused else full_duration)

        detail_budget = max_frames
        engine_label = "keyframes" if detail == "efficient" else "scene-change frames"
        cap_label = "unlimited" if detail_budget is None else str(detail_budget)
        print(f"[agent-watch] extracting {engine_label} over {scope} (target {target}, cap {cap_label})...", file=sys.stderr)

        if detail == "efficient":
            frames, frame_meta = extract_keyframes(
                video_path,
                work / "frames",
                resolution=args.resolution,
                max_frames=detail_budget,
                start_seconds=start_sec,
                end_seconds=end_sec,
                dedup=not args.no_dedup,
            )
        else:
            frames, frame_meta = extract_scene_or_uniform(
                video_path,
                work / "frames",
                fps=fps,
                target_frames=target,
                resolution=args.resolution,
                max_frames=detail_budget,
                start_seconds=start_sec,
                end_seconds=end_sec,
                dedup=not args.no_dedup,
            )

    if cue_frames:
        frames = merge_frames(frames, cue_frames)

    if not transcript_segments and dl.get("subtitle_path"):
        try:
            all_segments = parse_vtt(dl["subtitle_path"])
            transcript_segments = filter_range(all_segments, start_sec, end_sec) if focused else all_segments
            transcript_text = format_transcript(transcript_segments)
            transcript_source = "captions"
        except Exception as exc:
            print(f"[agent-watch] subtitle parse failed: {exc}", file=sys.stderr)

    if not transcript_segments and not args.no_whisper and video_path and meta.get("has_audio"):
        forced_local = args.whisper == "local"
        backend, api_key = (None, None) if forced_local else load_api_key(args.whisper)

        def _run_local() -> bool:
            nonlocal transcript_segments, transcript_text, transcript_source
            try:
                all_segments, used_backend = transcribe_local(video_path, work / "stt")
                transcript_segments = filter_range(all_segments, start_sec, end_sec) if focused else all_segments
                transcript_text = format_transcript(transcript_segments)
                transcript_source = f"whisper ({used_backend})"
                return True
            except Exception as exc:
                print(f"[agent-watch] local whisper failed: {exc}", file=sys.stderr)
                return False

        if backend and (api_key is not None or backend == "custom"):
            try:
                all_segments, used_backend = transcribe_video(
                    video_path,
                    work / "audio.mp3",
                    backend=backend,
                    api_key=api_key or "",
                )
                transcript_segments = filter_range(all_segments, start_sec, end_sec) if focused else all_segments
                transcript_text = format_transcript(transcript_segments)
                transcript_source = f"whisper ({used_backend})"
            except SystemExit as exc:
                print(f"[agent-watch] whisper API failed: {exc} - trying local fallback", file=sys.stderr)
                _run_local()
        elif forced_local or (args.whisper is None and local_whisper_available()):
            _run_local()
        else:
            hint = f"--whisper {args.whisper} was set but API key or endpoint missing" if args.whisper else "no subtitles, no API key, and local whisper not installed"
            print(f"[agent-watch] {hint} - run `python3 setup.py` to configure Whisper fallback", file=sys.stderr)

    elif not transcript_segments and video_path and not meta.get("has_audio"):
        print("[agent-watch] no audio stream found - proceeding without transcript", file=sys.stderr)

    
    # Flagship Feature 1: OCR Text Extraction
    if args.ocr and frames:
        from frames import extract_ocr_for_frames
        print("[agent-watch] running OCR text extraction on frames...", file=sys.stderr)
        frames = extract_ocr_for_frames(frames)

    # Flagship Feature 3: Chapter Segmentation
    chapters: list[dict] = []
    if (args.chapters or len(transcript_segments) > 10) and transcript_segments:
        from transcribe import generate_chapters
        chapters = generate_chapters(transcript_segments)

    info = dl.get("info") or {}

    print()
    print("# agent-watch: video report")
    print()
    print(f"- **Source:** {args.source}")
    if info.get("title"):
        print(f"- **Title:** {info['title']}")
    if info.get("uploader"):
        print(f"- **Uploader:** {info['uploader']}")
    print(f"- **Duration:** {format_time(full_duration)} ({full_duration:.1f}s)")
    if focused:
        print(f"- **Focus range:** {format_time(effective_start)} -> {format_time(effective_end)} ({effective_duration:.1f}s)")
    if meta.get("width") and meta.get("height"):
        print(f"- **Resolution:** {meta['width']}x{meta['height']} ({meta.get('codec') or 'unknown codec'})")
    range_mode = "focused" if focused else "full"
    print(f"- **Detail:** {detail}")
    detail_count = frame_meta.get("selected_count", 0)
    if detail != "transcript":
        cap_label = "unlimited" if detail_budget is None else str(detail_budget)
        engine = frame_meta.get("engine", "scene")
        fallback = " with uniform fallback" if frame_meta.get("fallback") else ""
        deduped = frame_meta.get("deduped_count", 0)
        dedup_note = f", {deduped} near-duplicate{'s' if deduped != 1 else ''} dropped" if deduped else ""
        print(f"- **Frames:** {detail_count} selected ({engine}{fallback}{dedup_note}, {range_mode} range, budget {target}, cap {cap_label})")
    elif not cue_frames:
        print("- **Frames:** skipped (transcript detail)")

    if cue_frames:
        print(f"- **Transcript-cue frames:** {len(cue_frames)} extracted at requested timestamps")

    if transcript_source:
        print(f"- **Transcript:** available ({transcript_source})")
    else:
        print("- **Transcript:** none available")

    print()
    if frames:
        print("## Frames")
        print()
        for f in frames:
            timestamp_str = f.get("timestamp_str", format_time(f.get("timestamp", f.get("timestamp_seconds", 0.0))))
            reason = f.get("reason")
            reason_str = f", reason={reason}" if reason else ""
            posix_path = Path(f['path']).as_posix()
            print(f"- `frame_{f.get('index', 0):04d}` (t={timestamp_str}{reason_str}) -> `{posix_path}`")
        print()

    
    if chapters:
        from transcribe import format_chapters
        print(format_chapters(chapters))
        print()

    ocr_frames = [f for f in frames if f.get("ocr_text")]
    if ocr_frames:
        print("## On-Screen Text (OCR)")
        print()
        for f in ocr_frames:
            ts_str = f.get("timestamp_str", format_time(f.get("timestamp", 0.0)))
            print(f"### `t={ts_str}`")
            print(f"```\n{f['ocr_text']}\n```")
            print()

    if transcript_segments:
        if transcript_text is None:
            transcript_text = format_transcript(transcript_segments)
        print("## Transcript")
        print()
        print(transcript_text)
        print()

        # Write TRANSCRIPT.md
        try:
            (work / "TRANSCRIPT.md").write_text(transcript_text, encoding="utf-8")
        except OSError:
            pass

    
    # Flagship Feature 5: Library Indexing
    if args.index:
        from index import add_to_index
        add_to_index({
            "source": args.source,
            "title": info.get("title") or args.source,
            "duration": full_duration,
            "transcript_segments": transcript_segments,
            "chapters": chapters,
        })

    # Flagship Feature 6: Local Inspection Dashboard
    if args.serve:
        from serve import serve_dashboard
        serve_dashboard(work)

    print(f"Working directory: `{work}`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
