# DESIGN.md — agent-watch Design System

> **Design Source of Truth.** Every UI decision for agent-watch flows from this file.
> Last updated: August 2026

---

## Memorable Thing

> **"This is how an AI agent finally sees."**

Every design decision serves this. The visual language must feel like precision instrumentation — a viewfinder locking onto a target frame — not a generic SaaS dashboard.

---

## Aesthetic Direction

**Retro-Futuristic / Industrial Cyber-Minimalist**

CRT viewport precision meets modern engineering austerity. The product is a machine that sees — so the design should feel like looking through a camera lens or a terminal monitor. High-contrast dark canvas, monospace timestamp accents, viewfinder crosshairs, and signal-green/cyan precision marks.

**Not:** purple gradients, bubbly border-radius everywhere, centered hero + 3-column feature grid, glassy translucent cards.

**Is:** tight grid discipline, scanline texture, explicit timestamp markers [t=00:32], frame-counter badges, deliberate negative space, every decoration tied to function.

---

## Color Palette

| Token | Hex | Role |
|-------|-----|------|
| --bg-void | #070A0F | Page background — near-black slate |
| --bg-deep | #0D131F | Viewport panels, section backgrounds |
| --bg-surface | #141C2E | Cards, code blocks, inputs |
| --border | #1E293B | Subtle 1px structural borders |
| --border-lit | #2D4A6B | Hovered / focused border state |
| --cyan | #00F0FF | Primary accent — viewfinder cyan |
| --emerald | #10B981 | Success, active, install confirmation |
| --amber | #FFB800 | Warning, CRT highlight, beta labels |
| --text-primary | #F8FAFC | Headlines, primary content |
| --text-secondary | #CBD5E1 | Body copy, descriptions |
| --text-muted | #64748B | Metadata, secondary labels |

---

## Typography

| Role | Font | Weight |
|------|------|--------|
| Display / Hero | Syne | 700–800 |
| Heading / Body | Plus Jakarta Sans | 400–700 |
| Code / Timestamps | JetBrains Mono | 400–600 |

---

## Motion

Intentional-functional. Motion communicates state change and system activity.

- Copy button success: scale 0.95→1.0, flash emerald — 150ms
- Terminal typing: character-by-character — 40ms per char
- Frame extraction demo: sequential pop-in — 80ms stagger
- Tab switch: fade + 4px slide — 180ms

Never: scroll-triggered wipe-ins on everything, bounce physics, confetti.

---

## Voice

- Lead with the action. "Give Any AI Agent Eyes & Ears." Not descriptions.
- Frame numbers and time codes are identity. [t=00:32], Frame 0042, 50 frames · 9.8k tokens.
- No enterprise hype. No "seamless", "powerful", "robust".
- Monospace for every command, path, and number. It signals precision.
