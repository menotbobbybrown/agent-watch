# `agent-watch` Product & Architecture Roadmap

This document outlines the strategic product vision, architectural milestones, and upcoming feature releases for **`agent-watch`**.

---

## 🟢 v1.0.0 — Production Release (Current)

- [x] **Universal Agent Integration**: Native plugin manifests for Antigravity, OpenCode, Claude Code, Codex, Cursor, Copilot, and Gemini CLI.
- [x] **100+ Community PR Fixes**: Windows UTF-8 encoding stability, NTFS permissions checks, modern FFmpeg `-fps_mode vfr` flags, and short-clip fps overrides.
- [x] **Self-Hosted & Offline Whisper**: Custom OpenAI-compatible endpoints (`WATCH_WHISPER_ENDPOINT`), local offline `openai-whisper` / `faster-whisper`, and Google Gemini 1.5 Flash/Pro integration.
- [x] **Anti-Bot & Cookie Auth**: `--cookies-from-browser` fallback loop (Chrome, Brave, Firefox, Edge, Safari) and YouTube 403 player client retries (`mweb`, `android`).
- [x] **Flagship Feature Suite**:
  - 🔤 **On-Screen OCR Text Extraction & Junk Sanitizer**: Strips subscriber prompts and lower-thirds to isolate code/slides.
  - 👥 **Speaker Diarization**: Multi-speaker attribution (`[Speaker 0]`, `[Speaker 1]`).
  - 🔖 **Automated Topic Chapters**: Scene-aware & speech-pause chapter generation.
  - 🤖 **Autonomous Agentic Mode (`--agentic`)**: Auto-tunes resolution/detail and generates `agent_digest.json`.
  - 🔍 **Library Indexing & Search (`--index`)**: Local JSON/SQLite transcript search.
  - 🌐 **HTML Web Inspection Dashboard (`--serve`)**: Synced video player, transcript sidebar, and clickable frame gallery.
- [x] **Infrastructure**: Multi-OS (Ubuntu, macOS, Windows) & Multi-Python (3.9–3.12) GitHub Actions CI/CD pipeline and PyPI `pyproject.toml` packaging.

---

## 🟡 v1.1.0 — Multimodal Intelligence & Live Streams (Q3 2026)

- [ ] **Real-Time WebRTC & Live Stream Ingestion (`--live`)**: Support live YouTube, Twitch, and RTMP stream tapping with sliding-window transcript buffers.
- [ ] **Local Multimodal Frame Embeddings**: Integrate CLIP / SigLIP embeddings to enable sub-second visual similarity frame search across indexed video libraries.
- [ ] **Object & UI Element Bounding Boxes**: Integrate Segment Anything 2 (SAM-2) or YOLOv10 for visual UI component tracking (buttons, dialogs, error popups).
- [ ] **Native MCP Server Mode (`agent-watch mcp`)**: Expose stdio/HTTP Model Context Protocol endpoints for direct agent tool calling without CLI invocation.

---

## 🔵 v1.2.0 — Multi-Video Synthesis & Cloud API (Q4 2026)

- [ ] **Multi-Video Comparative Analysis**: Query across entire playlists or folders of recordings (`agent-watch compare video1.mp4 video2.mp4`).
- [ ] **Cloud REST Microservice (`agent-watch-api`)**: Containerized Docker microservice with REST & WebSocket endpoints for enterprise agent fleets.
- [ ] **Automated Video Bug Repro Generator**: Convert screen recording videos directly into Playwright / Cypress test scripts.

---

## 🤝 Contributing

We welcome community contributions! Please read [AGENTS.md](AGENTS.md) and submit pull requests or feature requests on GitHub:  
👉 [https://github.com/menotbobbybrown/agent-watch](https://github.com/menotbobbybrown/agent-watch)
