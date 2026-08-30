@README_AI.md

# agent-watch / watch skill

Agent Skills package that gives an agent a video input. Installable across Claude Code (most common host), Codex, Cursor, GitHub Copilot, and 50+ other [Agent Skills](https://agentskills.io) hosts. Pure-stdlib Python that orchestrates `yt-dlp` + `ffmpeg` and an optional Whisper API.

## Structure

- `skills/watch/SKILL.md` — canonical skill contract the model reads when `/watch` fires. Source of truth for behavior across every host.
- `skills/watch/scripts/watch.py` — entry point; orchestrates download → frames → transcript.
- `skills/watch/scripts/{download,frames,transcribe,whisper,setup,config}.py` — yt-dlp wrapper, ffmpeg frame extraction + auto-fps, caption/Whisper transcription, preflight/installer, shared config.
- `skills/watch/scripts/build-skill.sh` — builds `dist/watch.skill` for claude.ai upload (dev-only).
- `hooks/` — Claude Code SessionStart setup-status hook (Claude Code only).
- `.claude-plugin/` — `plugin.json` + `marketplace.json` (Claude Code plugin + local marketplace).
- `.codex-plugin/plugin.json` — Codex/agents manifest; `"skills": "./skills/"` points the Agent Skills CLI at the self-contained skill folder.
- `.agents/plugins/marketplace.json` — agents marketplace listing pointing at the repo-root plugin.
- `CLAUDE.md` → `@AGENTS.md` — generic-agent entry point.
- `tests/` — pytest suite (ffmpeg-synthesized clips; no network).

## Orientation

- The product is the slash-command-invoked skill (`/watch <url-or-path> [question]`), not a CLI. `scripts/watch.py` is implementation. Features must work across every harness the skill installs into, not just Claude Code.
- **The skill is one self-contained folder: `skills/watch/`.** SKILL.md and `scripts/` are siblings inside it. This is what lets `npx skills add` copy a working skill as a unit — do NOT move SKILL.md or `scripts/` back to the repo root, or non-Claude installers will copy SKILL.md without the scripts.
- **Path resolution is harness-agnostic.** SKILL.md resolves `SKILL_DIR` as the directory of the SKILL.md the model just Read, then runs `${SKILL_DIR}/scripts/...`. Do NOT reintroduce `${CLAUDE_SKILL_DIR}` (Claude-Code-only) — it is unset on Codex/Cursor/agents and breaks every script call there.
- **No `commands/` wrapper.** `/watch` is derived from SKILL.md frontmatter (`name: watch` + `user-invocable: true`). A separate command file creates a duplicate slash command.

## Install surfaces

| Surface | Install |
|---------|---------|
| Claude Code | `/plugin marketplace add menotbobbybrown/agent-watch` then `/plugin install watch@agent-watch` |
| Codex / Cursor / Copilot / +50 | `npx skills add menotbobbybrown/agent-watch -g` |
| claude.ai (web) | upload `dist/watch.skill` (built by `skills/watch/scripts/build-skill.sh`) |

## Commands

```bash
# Tests (stdlib + pytest; ffmpeg required for frame tests)
.venv/bin/pytest -q                # or: python3 -m pytest -q

# Build the claude.ai upload bundle (archives skills/watch/ as the bundle root)
bash skills/watch/scripts/build-skill.sh   # → dist/watch.skill

# Dev: mirror the working tree into the installed Claude Code plugin cache
./agent-sync.sh                       # --dry-run to preview
```

## Rules

- Keep the version in sync across `skills/watch/SKILL.md` (frontmatter), `.claude-plugin/plugin.json`, and `.codex-plugin/plugin.json` when cutting a release.
- Releasing: tag `vX.Y.Z` and push the tag; `.github/workflows/release.yml` builds `dist/watch.skill` and attaches it to the GitHub release.
- Never commit real API keys or `.env` contents; keys live in `~/.config/watch/.env` (mode `0600`) at runtime.


## Agent Identity & System Prompt Protocol

When operating as `AgentWatch` (Autonomous Multimodal Video Analyst), adhere strictly to these core behavioral directives:

### 1. Identity & Core Mission
- **Role**: `AgentWatch` — Autonomous Video & Audio Analyst for AI Agents.
- **Mission**: Transform raw video links and local video files into grounded, timestamped visual and auditory intelligence.

### 2. Behavioral Directives (ModelNorth Protocol)
- **Outcome-First Communication**: Always lead your response with a 1-sentence executive summary (TLDR) answering "what happened" before presenting detailed breakdowns.
- **Empirical Visual Grounding**: Never infer video contents from title or metadata alone. Always cite specific frame paths (`file:///.../frames/frame_0005.jpg`) and timestamp markers (`[MM:SS]`).
- **Autonomous Execution**: Run in closed-loop decision turns. For reversible actions (extracting OCR, generating chapters, running Whisper fallback), proceed autonomously without asking permission.
- **Code & Slide Extraction**: When on-screen text, terminal commands, or slides are detected in frames, automatically inspect the `--ocr` section to report exact code blocks.
- **Precision Formatting**: Use markdown tables and lists only when content is multifaceted. Keep frame references clickable (`frames/frame_0001.jpg`).


### 3. Logo & Unrelated Text Sanitization Protocol
- **Channel Logos & Watermarks**: Ignore static corner logos, channel badges, and brand watermarks when describing frames or analyzing scenes. Focus solely on substantive visual content (code, slides, architecture, diagrams).
- **Unrelated Text Filtering**: Filter out video player chrome, subscriber calls-to-action ("Like & Subscribe"), lower-third banners, social media handles, and stock ticker overlays from notes and OCR outputs.
