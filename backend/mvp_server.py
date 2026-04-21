#!/usr/bin/env python3
from __future__ import annotations

import json
import uuid
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "mvp_db.json"
SHEET_ROWS_PATH = ROOT / "data" / "sheet_rows.json"


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def normalize_phone(value: str, prefix_to_strip: str = "p:") -> str:
    # Example raw: "p:+77475789240"
    if not value:
        return ""
    value = value.strip()
    if prefix_to_strip and value.startswith(prefix_to_strip):
        value = value[len(prefix_to_strip):]
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


def load_sheet_rows() -> list:
    if SHEET_ROWS_PATH.exists():
        return json.loads(SHEET_ROWS_PATH.read_text(encoding="utf-8"))
    return []


def save_sheet_rows(rows: list) -> None:
    SHEET_ROWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SHEET_ROWS_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def create_lead_from_instagram_row(db: dict, event: dict, body: dict) -> dict:
    created_time = body.get("created_time") or now_iso()
    cfg = event.get("config", {})
    status_cfg = cfg.get("statusConfig", {})
    phone_prefix = cfg.get("phonePrefixToStrip", "p:")
    created_status = status_cfg.get("created", "CREATED")
    consulting_values = status_cfg.get("consulting", ["IN_PROGRESS", "상담 중"])
    phone = normalize_phone(body.get("phone_number", ""), phone_prefix)
    platform = normalize_platform(body.get("platform", ""))
    lead_status = (body.get("lead_status") or "CREATED").strip()
    stage = (
        "new_lead"
        if lead_status.upper() == str(created_status).upper()
        else ("consulting" if lead_status in consulting_values else "consulting")
    )
    lead = {
        "id": str(uuid.uuid4()),
        "eventId": event["id"],
        "name": body.get("full_name", "").strip() or f"리드{len(db['leads']) + 1}",
        "phone": phone or "+82-10-0000-0000",
        "service": event.get("defaultService", "checkup"),
        "stage": stage,
        "createdAt": created_time,
        "platform": platform,
        "lead_status": lead_status,
        "log": f"Instagram New 인입({platform}) status={lead_status}",
    }
    db["leads"].append(lead)
    return lead


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
                "sheetWebhookUrl": "",
                "config": {
                    "phonePrefixToStrip": "p:",
                    "statusConfig": {"created": "CREATED", "consulting": ["IN_PROGRESS", "상담 중"]},
                    "replyTemplates": {
                        "ko": "안녕하세요 {{name}}님, 문의 감사합니다.",
                        "en": "Hi {{name}}, thanks for your inquiry.",
                        "ru": "Здравствуйте, {{name}}. Спасибо за обращение.",
                    },
                },
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

        if path.startswith("/api/events/") and path.endswith("/sheet-webhook"):
            event_id = path.split("/")[3]
            body = self._read_json()
            for e in db["events"]:
                if e["id"] == event_id:
                    e["sheetWebhookUrl"] = body.get("sheetWebhookUrl", "")
                    save_db(db)
                    self._send_json(200, e)
                    return
            self._not_found()
            return

        if path.startswith("/api/events/") and path.endswith("/config"):
            event_id = path.split("/")[3]
            body = self._read_json()
            for e in db["events"]:
                if e["id"] == event_id:
                    current = e.get("config", {})
                    merged = {**current, **body}
                    # nested merge for known objects
                    if "statusConfig" in body:
                        merged["statusConfig"] = {**current.get("statusConfig", {}), **body["statusConfig"]}
                    if "replyTemplates" in body:
                        merged["replyTemplates"] = {**current.get("replyTemplates", {}), **body["replyTemplates"]}
                    e["config"] = merged
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
            lead = create_lead_from_instagram_row(db, event, body)
            save_db(db)
            self._send_json(201, lead)
            return

        if path.startswith("/api/events/") and path.endswith("/append-instagram-row"):
            event_id = path.split("/")[3]
            body = self._read_json()
            event = next((e for e in db["events"] if e["id"] == event_id), None)
            if not event:
                self._not_found()
                return

            # 1) 신규행 저장(시트 모의 저장소)
            row = {
                "eventId": event_id,
                "source_tab": "Instagram New",
                "created_time": body.get("created_time") or now_iso(),
                "platform": body.get("platform", ""),
                "phone_number": body.get("phone_number", ""),
                "full_name": body.get("full_name", ""),
                "lead_status": body.get("lead_status", "CREATED"),
                "savedAt": now_iso(),
            }
            rows = load_sheet_rows()
            rows.append(row)
            save_sheet_rows(rows)

            # 2) webhook 설정 시 외부 Apps Script로 전달(옵션)
            webhook_url = event.get("sheetWebhookUrl", "").strip()
            webhook_result = "skipped"
            if webhook_url:
                try:
                    req = Request(
                        webhook_url,
                        data=json.dumps(row, ensure_ascii=False).encode("utf-8"),
                        headers={"Content-Type": "application/json; charset=utf-8"},
                        method="POST",
                    )
                    with urlopen(req, timeout=5) as resp:  # nosec B310
                        webhook_result = f"sent:{resp.status}"
                except Exception as e:  # noqa: BLE001
                    webhook_result = f"failed:{e}"

            # 3) CRM 리드에도 즉시 인입
            ingest_body = {"eventId": event_id, **row}
            lead = create_lead_from_instagram_row(db, event, ingest_body)
            lead["log"] += f" · sheet_append={webhook_result}"
            save_db(db)

            self._send_json(201, {"sheet_row": row, "webhook": webhook_result, "lead": lead})
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
