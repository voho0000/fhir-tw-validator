"""Standalone CLI: validate a FHIR JSON file against R4 + Taiwan NHI rules.

Usage:
    python scripts/validate_file.py path/to/bundle.json
    python scripts/validate_file.py path/to/bundle.json --severity error
    python scripts/validate_file.py path/to/bundle.json --severity info --format json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root without installing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fhir_tw_validator import validate_bundle, Severity
from fhir_tw_validator.report import to_text, to_json as to_json_report


_SEVERITY_MAP = {"error": Severity.ERROR, "warning": Severity.WARNING, "info": Severity.INFO}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a FHIR R4 JSON file against Taiwan NHI rules.",
    )
    parser.add_argument("file", help="Path to a FHIR Bundle, single resource, or array JSON file")
    parser.add_argument("--severity", choices=["error", "warning", "info"], default="warning")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1

    if isinstance(body, list):
        resources = body
    elif isinstance(body, dict):
        rtype = body.get("resourceType", "")
        if rtype == "Bundle":
            resources = [e.get("resource", e) for e in body.get("entry", []) if isinstance(e, dict)]
        else:
            resources = [body]
    else:
        print("Expected JSON object or array.", file=sys.stderr)
        return 1

    min_sev = _SEVERITY_MAP[args.severity]
    reports = validate_bundle(resources)

    patient_label = next(
        (r.get("id", "") for r in resources if isinstance(r, dict) and r.get("resourceType") == "Patient"),
        path.stem,
    )

    if args.format == "json":
        print(json.dumps(to_json_report(reports, patient_id=patient_label, min_severity=min_sev),
                         ensure_ascii=False, indent=2))
    else:
        print(to_text(reports, patient_id=patient_label, min_severity=min_sev))

    error_count = sum(r.error_count for r in reports)
    return 1 if error_count else 0


if __name__ == "__main__":
    sys.exit(main())
