"""Unit tests for the 6 flagship features of agent-watch."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "watch" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import frames
import transcribe
import index
import serve

def test_chapter_generation():
    segs = [
        {"start": 0.0, "end": 2.0, "text": "Intro segment"},
        {"start": 6.0, "end": 10.0, "text": "Topic gap section"},
    ]
    chaps = transcribe.generate_chapters(segs, min_gap_seconds=3.0)
    assert len(chaps) == 2
    assert chaps[0]["title"] == "Introduction"
    assert "Topic Section 2" in chaps[1]["title"]

def test_library_indexing(tmp_path, monkeypatch):
    monkeypatch.setattr(index, "INDEX_DIR", tmp_path)
    monkeypatch.setattr(index, "INDEX_FILE", tmp_path / "index.json")

    entry = {
        "source": "https://example.com/video.mp4",
        "title": "Agent Watch Demo Video",
        "transcript_segments": [{"start": 1.0, "end": 3.0, "text": "Testing index search"}]
    }
    index.add_to_index(entry)

    res = index.search_index("Demo")
    assert len(res) == 1
    assert res[0]["item"]["title"] == "Agent Watch Demo Video"

def test_serve_dashboard_html():
    assert "agent-watch Dashboard" in serve.HTML_TEMPLATE
