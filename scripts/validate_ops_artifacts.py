#!/usr/bin/env python3
"""Validate Event CRM docs/config artifacts.

Checks:
1) Required files exist.
2) JSON files are valid JSON.
3) module-field-mapping.csv has required headers and non-empty rows.
4) Mapping target fields appear in I/O spec standard field list (best-effort text check).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/event-crm-blueprint-ko.md",
    "docs/event-crm-implementation-playbook-ko.md",
    "ops/README.md",
    "ops/config/hubspot-properties.json",
    "ops/config/pipeline-stages.json",
    "ops/config/response-buttons.json",
    "ops/templates/message-templates.json",
    "ops/samples/google-sheet-mapping.csv",
    "ops/samples/instagram-new-mapping.csv",
    "ops/samples/incoming-webhook-payload.json",
    "ops/make/make-scenario-io-spec-ko.md",
    "ops/make/module-field-mapping.csv",
    "backend/mvp_server.py",
]

JSON_FILES = [
    "ops/config/hubspot-properties.json",
    "ops/config/pipeline-stages.json",
    "ops/config/response-buttons.json",
    "ops/templates/message-templates.json",
    "ops/samples/incoming-webhook-payload.json",
]

CSV_FILE = "ops/make/module-field-mapping.csv"
CSV_REQUIRED_HEADERS = {
    "module",
    "input_field",
    "output_field",
    "rule_or_formula",
    "destination",
}


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)


def main() -> int:
    print("[INFO] Validating required files...")
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.exists():
            fail(f"Missing required file: {rel}")
    print(f"[PASS] Required files exist: {len(REQUIRED_FILES)}")

    print("[INFO] Validating JSON syntax...")
    for rel in JSON_FILES:
        path = ROOT / rel
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            fail(f"Invalid JSON in {rel}: {e}")
    print(f"[PASS] JSON syntax valid: {len(JSON_FILES)} files")

    print("[INFO] Validating module-field-mapping CSV...")
    csv_path = ROOT / CSV_FILE
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
        if not CSV_REQUIRED_HEADERS.issubset(headers):
            fail(
                f"CSV headers missing. required={sorted(CSV_REQUIRED_HEADERS)} got={sorted(headers)}"
            )
        rows = list(reader)
        if not rows:
            fail("module-field-mapping.csv has no rows")
        for idx, row in enumerate(rows, start=2):
            for h in CSV_REQUIRED_HEADERS:
                if row.get(h, "").strip() == "":
                    fail(f"CSV empty field at line {idx}: {h}")
    print(f"[PASS] CSV structure valid: {len(rows)} rows")

    print("[INFO] Cross-check target fields against I/O spec (best effort)...")
    spec_text = (ROOT / "ops/make/make-scenario-io-spec-ko.md").read_text(encoding="utf-8")
    target_fields = set()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out = row["output_field"].strip()
            if out and out not in {"validation_ok", "run_log", "retry_at", "is_duplicate", "dealname", "message_status", "provider_message_id", "mapping_rows", "raw_payload"}:
                target_fields.add(out)

    missing = [f for f in sorted(target_fields) if f not in spec_text]
    if missing:
        fail(f"Fields not found in I/O spec text: {missing}")
    print(f"[PASS] Cross-check success: {len(target_fields)} mapped fields found in spec")

    print("[DONE] All validations passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
