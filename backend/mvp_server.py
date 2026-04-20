#!/usr/bin/env python3
from __future__ import annotations

import json
import uuid
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "mvp_db.json"


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def normalize_phone(value: str) -> str:
    # Example raw: "p:+77475789240"
    if not value:
        return ""
    value = value.strip()
    if value.startswith("p:"):
        value = value[2:]
    return value


def normalize_platform(value: str) -> str:
    v = (value or "").strip().lower()
    if v in {"ig", "instagram", "인스타그램"}:
        return "instagram"
    if v in {"fb", "facebook"}:
        return "facebook"
    if v in {"m1"}:
        return "m1"
    return v or "unknown"


def load_db() -> dict:
    if DB_PATH.exists():
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    return {"events": [], "leads": []}


def save_db(db: dict) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, code: int, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _not_found(self):
        self._send_json(404, {"error": "not found"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._send_json(200, {"status": "ok", "time": now_iso()})
            return

        if path == "/api/events":
            db = load_db()
            self._send_json(200, db["events"])
            return

        if path.startswith("/api/events/") and path.endswith("/leads"):
            event_id = path.split("/")[3]
            db = load_db()
            leads = [l for l in db["leads"] if l["eventId"] == event_id]
            self._send_json(200, leads)
            return

        if path.startswith("/ui"):
            return super().do_GET()

        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/ui/")
            self.end_headers()
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        db = load_db()

        if path == "/api/events":
            body = self._read_json()
            event = {
                "id": str(uuid.uuid4()),
                "name": body.get("name", ""),
                "country": body.get("country", ""),
                "defaultService": body.get("defaultService", "checkup"),
                "sheetUrl": "",
                "createdAt": now_iso(),
            }
            db["events"].append(event)
            save_db(db)
            self._send_json(201, event)
            return

        if path.startswith("/api/events/") and path.endswith("/sheet"):
            event_id = path.split("/")[3]
            body = self._read_json()
            for e in db["events"]:
                if e["id"] == event_id:
                    e["sheetUrl"] = body.get("sheetUrl", "")
                    save_db(db)
                    self._send_json(200, e)
                    return
            self._not_found()
            return

        if path.startswith("/api/events/") and path.endswith("/leads"):
            event_id = path.split("/")[3]
            event = next((e for e in db["events"] if e["id"] == event_id), None)
            if not event:
                self._not_found()
                return
            lead = {
                "id": str(uuid.uuid4()),
                "eventId": event_id,
                "name": f"리드{len(db['leads']) + 1}",
                "phone": "+82-10-1234-5678",
                "service": event.get("defaultService", "checkup"),
                "stage": "new_lead",
                "createdAt": now_iso(),
                "log": "신규 리드 유입",
            }
            db["leads"].append(lead)
            save_db(db)
            self._send_json(201, lead)
            return

        if path == "/api/ingest/instagram-new":
            body = self._read_json()
            event_id = body.get("eventId", "")
            event = next((e for e in db["events"] if e["id"] == event_id), None)
            if not event:
                self._not_found()
                return

            created_time = body.get("created_time") or now_iso()
            phone = normalize_phone(body.get("phone_number", ""))
            platform = normalize_platform(body.get("platform", ""))
            lead_status = (body.get("lead_status") or "CREATED").strip()

            lead = {
                "id": str(uuid.uuid4()),
                "eventId": event_id,
                "name": body.get("full_name", "").strip() or f"리드{len(db['leads']) + 1}",
                "phone": phone or "+82-10-0000-0000",
                "service": event.get("defaultService", "checkup"),
                "stage": "new_lead" if lead_status.upper() == "CREATED" else "consulting",
                "createdAt": created_time,
                "platform": platform,
                "lead_status": lead_status,
                "log": f"Instagram New 인입({platform}) status={lead_status}",
            }
            db["leads"].append(lead)
            save_db(db)
            self._send_json(201, lead)
            return

        if path.startswith("/api/leads/") and path.endswith("/auto-reply"):
            lead_id = path.split("/")[3]
            for lead in db["leads"]:
                if lead["id"] == lead_id:
                    lead["stage"] = "auto_replied"
                    lead["log"] = "자동응답 실행 완료 (API)"
                    save_db(db)
                    self._send_json(200, lead)
                    return
            self._not_found()
            return

        if path.startswith("/api/leads/") and path.endswith("/quick-action"):
            lead_id = path.split("/")[3]
            body = self._read_json()
            action = body.get("action", "")
            for lead in db["leads"]:
                if lead["id"] == lead_id:
                    lead["stage"] = "booking_push" if action == "btn_booking_push" else "consulting"
                    lead["log"] = f"문의응답선택 실행(API): {action}"
                    save_db(db)
                    self._send_json(200, lead)
                    return
            self._not_found()
            return

        if path.startswith("/api/leads/") and path.endswith("/stage"):
            lead_id = path.split("/")[3]
            body = self._read_json()
            stage = body.get("stage", "new_lead")
            for lead in db["leads"]:
                if lead["id"] == lead_id:
                    lead["stage"] = stage
                    lead["log"] = f"상태 변경(API): {stage}"
                    save_db(db)
                    self._send_json(200, lead)
                    return
            self._not_found()
            return

        self._not_found()


if __name__ == "__main__":
    port = 8080
    print(f"[INFO] Event CRM MVP server running at http://localhost:{port}/ui/")
    print("[INFO] API health: /api/health")
    ThreadingHTTPServer(("", port), Handler).serve_forever()
