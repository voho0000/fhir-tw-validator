"""Batch FHIR R4 validator.

Validates a list of resources (e.g. a patient's full record) by:
1. Running per-resource structural + Taiwan checks on each resource.
2. Running cross-resource reference integrity checks across the batch.
"""
from __future__ import annotations

from .base import ValidationReport
from .structural import validate_resource
from .taiwan import validate_taiwan
from .references import validate_references


def validate_bundle(resources: list[dict]) -> list[ValidationReport]:
    """Validate a list of FHIR resources and return one report per resource.

    Filters out None values (mappers return None for skipped rows).
    """
    clean = [r for r in resources if r is not None and isinstance(r, dict)]

    # Per-resource checks
    reports: list[ValidationReport] = []
    reports_by_key: dict[str, ValidationReport] = {}
    for resource in clean:
        report = validate_resource(resource)
        validate_taiwan(resource, report)
        reports.append(report)
        key = f"{resource.get('resourceType', '')}/{resource.get('id', '')}"
        reports_by_key[key] = report

    # Cross-resource reference checks
    if len(clean) > 1:
        validate_references(clean, reports_by_key)

    return reports


def summary(reports: list[ValidationReport]) -> dict:
    """Return an aggregate summary dict."""
    total = len(reports)
    valid = sum(1 for r in reports if r.valid)
    errors = sum(r.error_count for r in reports)
    warnings = sum(r.warning_count for r in reports)
    infos = sum(r.info_count for r in reports)
    return {
        "total": total,
        "valid": valid,
        "with_errors": total - valid,
        "error_count": errors,
        "warning_count": warnings,
        "info_count": infos,
    }
