@README_AI.md

@AGENTS.md

# CLAUDE.md — Agent Watch Reference

This file provides quick-reference guidelines for Claude Code, Antigravity, OpenCode, Codex, Cursor, and 50+ Agent Skills hosts working in the **`agent-watch`** repository.

## Project Summary
`agent-watch` is the universal, open-source video engine for AI agents. It downloads video clips (`yt-dlp`), extracts scene-aware frames (`ffmpeg`), transcribes audio (captions, self-hosted Whisper, local Whisper, or Gemini API), sanitizes visual clutter, and surfaces structured Markdown & JSON intelligence (`agent_digest.json`).

## Quick CLI Reference
```bash
# Run basic watch on URL or file
python skills/watch/scripts/watch.py <url-or-path>

# Run in Autonomous Agentic Mode (Auto-detail, OCR, Chapters, Agent Digest)
python skills/watch/scripts/watch.py --agentic <url-or-path>

# Custom backend & flagship options
python skills/watch/scripts/watch.py <url> --ocr --diarize --chapters --whisper gemini --index --serve
```

## Developer Commands
- **Run Unit Tests**: `python -m pytest -v`
- **Install Editable Package**: `pip install -e .`
- **Build Web Skill Bundle**: `bash skills/watch/scripts/build-skill.sh`
- **Local Dev Sync**: `./agent-sync.sh`

## Architecture & Code Structure
- `skills/watch/scripts/watch.py`: Main CLI entry point & orchestrator.
- `skills/watch/scripts/frames.py`: Frame extraction, scene-change detection, blank-frame dropping, and OCR text sanitization.
- `skills/watch/scripts/transcribe.py`: Caption fetching & chapter segmentation.
- `skills/watch/scripts/whisper.py`: Multi-backend Whisper engine (Groq, OpenAI, self-hosted, local offline, Gemini 1.5).
- `skills/watch/scripts/index.py`: Local vector library search & indexing.
- `skills/watch/scripts/serve.py`: Zero-dependency HTML inspection dashboard (`http://localhost:8888`).
