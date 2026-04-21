#!/usr/bin/env python3
"""Serve UI + API together.

This wraps backend/mvp_server.py so POST /api/* works.
"""

from http.server import ThreadingHTTPServer
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.mvp_server import Handler  # noqa: E402

PORT = int(os.environ.get("PORT", "8080"))

print(f"[INFO] Serving Event CRM MVP at http://localhost:{PORT}/ui/")
print(f"[INFO] API enabled at http://localhost:{PORT}/api/health")

ThreadingHTTPServer(("", PORT), Handler).serve_forever()
