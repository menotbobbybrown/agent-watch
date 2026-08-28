#!/usr/bin/env python3
"""Semantic Indexing & Library Search for agent-watch."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

INDEX_DIR = Path.home() / ".config" / "agent-watch"
INDEX_FILE = INDEX_DIR / "library_index.json"


def load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        return []
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_index(index_data: list[dict]) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index_data, indent=2), encoding="utf-8")


def add_to_index(entry: dict) -> None:
    data = load_index()
    # Deduplicate by url/path
    data = [e for e in data if e.get("source") != entry.get("source")]
    data.append(entry)
    save_index(data)
    print(f"[agent-watch] Indexed video: {entry.get('title') or entry.get('source')}", file=sys.stderr)


def search_index(query: str) -> list[dict]:
    data = load_index()
    q = query.lower()
    results = []
    for item in data:
        score = 0
        matches = []
        if q in (item.get("title") or "").lower():
            score += 5
            matches.append("title match")
        for seg in item.get("transcript_segments", []):
            if q in seg.get("text", "").lower():
                score += 1
                matches.append(f"[{seg.get('start')}] {seg.get('text')}")
        if score > 0:
            results.append({"item": item, "score": score, "matches": matches[:5]})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        q = " ".join(sys.argv[2:])
        res = search_index(q)
        print(f"Found {len(res)} matches for '{q}':")
        for r in res:
            it = r["item"]
            print(f"- {it.get('title')} ({it.get('source')})")
            for m in r["matches"]:
                print(f"    {m}")
