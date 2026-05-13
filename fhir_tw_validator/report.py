"""Render ValidationReport lists to text or JSON."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone

from .base import ValidationReport, Severity


def to_json(
    reports: list[ValidationReport],
    patient_id: str = "",
    min_severity: Severity = Severity.INFO,
) -> dict:
    """Return a JSON-serialisable validation report dict."""
    filtered = _filter_reports(reports, min_severity)
    total = len(reports)
    valid = sum(1 for r in reports if r.valid)
    errors = sum(r.error_count for r in reports)
    warnings = sum(r.warning_count for r in reports)
    infos = sum(r.info_count for r in reports)

    return {
        "patient_id": patient_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "min_severity": min_severity.value,
        "summary": {
            "total": total,
            "valid": valid,
            "with_errors": total - valid,
            "error_count": errors,
            "warning_count": warnings,
            "info_count": infos,
        },
        "reports": [
            {
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "valid": r.valid,
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "path": issue.path,
                        "rule": issue.rule,
                        "message": issue.message,
                    }
                    for issue in r.issues
                    if _meets_threshold(issue.severity, min_severity)
                ],
            }
            for r in filtered
            if any(_meets_threshold(i.severity, min_severity) for i in r.issues)
            or not r.valid  # always include resources with errors
        ],
    }


def to_text(
    reports: list[ValidationReport],
    patient_id: str = "",
    min_severity: Severity = Severity.WARNING,
) -> str:
    """Return a human-readable text report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    total = len(reports)
    valid = sum(1 for r in reports if r.valid)
    errors = sum(r.error_count for r in reports)
    warnings = sum(r.warning_count for r in reports)
    infos = sum(r.info_count for r in reports)

    lines.append("=" * 60)
    lines.append("FHIR R4 Validation Report")
    lines.append("=" * 60)
    if patient_id:
        lines.append(f"Patient  : {patient_id}")
    lines.append(f"Generated: {now}")
    lines.append(f"Resources: {total}  Valid: {valid}  "
                 f"Errors: {errors}  Warnings: {warnings}  Info: {infos}")
    lines.append("")

    # Group issues by severity
    error_items: list[tuple[ValidationReport, list]] = []
    warning_items: list[tuple[ValidationReport, list]] = []
    info_items: list[tuple[ValidationReport, list]] = []

    for r in reports:
        errs = [i for i in r.issues if i.severity == Severity.ERROR]
        warns = [i for i in r.issues if i.severity == Severity.WARNING]
        infos_list = [i for i in r.issues if i.severity == Severity.INFO]
        if errs:
            error_items.append((r, errs))
        if warns and _meets_threshold(Severity.WARNING, min_severity):
            warning_items.append((r, warns))
        if infos_list and _meets_threshold(Severity.INFO, min_severity):
            info_items.append((r, infos_list))

    if error_items:
        lines.append(f"── ERRORS ({sum(len(i) for _, i in error_items)}) " + "─" * 30)
        for r, issues in error_items:
            lines.append(f"  [{r.resource_type}/{r.resource_id}]")
            for issue in issues:
                lines.append(f"    [{issue.rule}] {issue.path}")
                lines.append(f"      {issue.message}")
        lines.append("")

    if warning_items:
        lines.append(f"── WARNINGS ({sum(len(i) for _, i in warning_items)}) " + "─" * 28)
        for r, issues in warning_items:
            lines.append(f"  [{r.resource_type}/{r.resource_id}]")
            for issue in issues:
                lines.append(f"    [{issue.rule}] {issue.path}")
                lines.append(f"      {issue.message}")
        lines.append("")

    if info_items:
        lines.append(f"── INFO ({sum(len(i) for _, i in info_items)}) " + "─" * 32)
        for r, issues in info_items:
            lines.append(f"  [{r.resource_type}/{r.resource_id}]")
            for issue in issues:
                lines.append(f"    [{issue.rule}] {issue.path}")
                lines.append(f"      {issue.message}")
        lines.append("")

    # Per-type summary table
    by_type: dict[str, dict] = defaultdict(lambda: {"count": 0, "errors": 0, "warnings": 0})
    for r in reports:
        by_type[r.resource_type]["count"] += 1
        by_type[r.resource_type]["errors"] += r.error_count
        by_type[r.resource_type]["warnings"] += r.warning_count

    lines.append("── Summary by resource type " + "─" * 33)
    for rtype, stats in sorted(by_type.items()):
        lines.append(
            f"  {rtype:<25} {stats['count']:>3} resources  "
            f"{stats['errors']:>2} errors  {stats['warnings']:>2} warnings"
        )

    lines.append("=" * 60)
    return "\n".join(lines)


def _meets_threshold(severity: Severity, min_severity: Severity) -> bool:
    order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
    return order[severity] <= order[min_severity]


def _filter_reports(
    reports: list[ValidationReport], min_severity: Severity
) -> list[ValidationReport]:
    return [r for r in reports if any(
        _meets_threshold(i.severity, min_severity) for i in r.issues
    ) or not r.valid]
