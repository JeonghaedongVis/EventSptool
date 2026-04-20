#!/usr/bin/env python3
"""Serve repository root so /ui/ works reliably."""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os

PORT = int(os.environ.get("PORT", "8080"))
ROOT = Path(__file__).resolve().parents[1]

os.chdir(ROOT)
print(f"[INFO] Serving repo root: {ROOT}")
print(f"[INFO] Open: http://localhost:{PORT}/ui/")

httpd = ThreadingHTTPServer(("", PORT), SimpleHTTPRequestHandler)
httpd.serve_forever()
