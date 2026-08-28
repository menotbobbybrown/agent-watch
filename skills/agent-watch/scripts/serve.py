#!/usr/bin/env python3
"""Zero-dependency Local Inspection Dashboard for agent-watch."""
from __future__ import annotations

import http.server
import json
import socketserver
import sys
import webbrowser
from pathlib import Path

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>agent-watch Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 15px; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }
        .frame-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; max-height: 500px; overflow-y: auto; }
        .frame-item { background: #0f172a; border-radius: 6px; padding: 5px; text-align: center; border: 1px solid #334155; }
        .frame-item img { width: 100%; border-radius: 4px; }
        .transcript-box { max-height: 500px; overflow-y: auto; font-family: monospace; font-size: 13px; line-height: 1.6; }
        .stamp { color: #38bdf8; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📹 agent-watch Dashboard</h1>
        <span>Universal AI Agent Video Engine</span>
    </div>
    <div class="grid">
        <div class="card">
            <h2>Extracted Frames</h2>
            <div class="frame-grid" id="frames"></div>
        </div>
        <div class="card">
            <h2>Transcript</h2>
            <div class="transcript-box" id="transcript"></div>
        </div>
    </div>
    <script>
        fetch('/data.json').then(r => r.json()).then(data => {
            const fContainer = document.getElementById('frames');
            (data.frames || []).forEach(f => {
                const div = document.createElement('div');
                div.className = 'frame-item';
                div.innerHTML = `<img src="${f.url}"/><div class="stamp">${f.timestamp_str || ''}</div>`;
                fContainer.appendChild(div);
            });
            const tContainer = document.getElementById('transcript');
            (data.transcript_lines || []).forEach(l => {
                const div = document.createElement('div');
                div.innerHTML = `<span class="stamp">${l.stamp || ''}</span> ${l.text || ''}`;
                tContainer.appendChild(div);
            });
        });
    </script>
</body>
</html>
"""

def serve_dashboard(work_dir: Path, port: int = 8888) -> None:
    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
                return
            if self.path == "/data.json":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                data = {"frames": [], "transcript_lines": []}
                frames_dir = work_dir / "frames"
                if frames_dir.exists():
                    for img in sorted(frames_dir.glob("*.jpg")):
                        data["frames"].append({"url": f"/frames/{img.name}", "timestamp_str": img.stem})
                t_file = work_dir / "TRANSCRIPT.md"
                if t_file.exists():
                    for line in t_file.read_text(encoding="utf-8").splitlines():
                        if line.startswith("["):
                            stamp, _, txt = line.partition(" ")
                            data["transcript_lines"].append({"stamp": stamp, "text": txt})
                self.wfile.write(json.dumps(data).encode("utf-8"))
                return
            super().do_GET()

    os.chdir(work_dir)
    handler = DashboardHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"[agent-watch] Dashboard running at http://localhost:{port}", file=sys.stderr)
        webbrowser.open(f"http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("[agent-watch] Stopping dashboard...", file=sys.stderr)

if __name__ == "__main__":
    work = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    serve_dashboard(work)
