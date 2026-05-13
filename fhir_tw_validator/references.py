"""Reference integrity validation.

Single-resource: check reference format is non-empty after the '/'.
Cross-resource (batch): check that subject references resolve to a Patient
in the same batch, and DiagnosticReport.result[] refs resolve to Observations.
"""
from __future__ import annotations
import re

from .base import ValidationReport, Severity, ValidationIssue

_PATIENT_REF_RE = re.compile(r"^Patient/\S+$")
_OBS_REF_RE = re.compile(r"^Observation/\S+$")


def validate_references(
    resources: list[dict],
    reports_by_id: dict[str, ValidationReport],
) -> None:
    """Check cross-resource reference integrity.

    Appends issues directly to the matching ValidationReport in reports_by_id.
    reports_by_id key format: "<resourceType>/<id>"
    """
    patient_ids: set[str] = {
        r["id"] for r in resources
        if r.get("resourceType") == "Patient" and r.get("id")
    }
    obs_ids: set[str] = {
        r["id"] for r in resources
        if r.get("resourceType") == "Observation" and r.get("id")
    }

    for resource in resources:
        rtype = resource.get("resourceType", "")
        rid = resource.get("id", "")
        key = f"{rtype}/{rid}"
        report = reports_by_id.get(key)
        if report is None:
            continue

        # Check subject/patient reference resolves
        for field in ("subject", "patient"):
            ref_obj = resource.get(field) or {}
            ref = ref_obj.get("reference", "")
            if not ref:
                continue
            if _PATIENT_REF_RE.match(ref):
                pid = ref.split("/", 1)[1]
                if patient_ids and pid not in patient_ids:
                    report.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        resource_type=rtype,
                        resource_id=rid,
                        path=f"{field}.reference",
                        rule="ref-patient-dangling",
                        message=(
                            f"{rtype}.{field}.reference 'Patient/{pid}' does not resolve "
                            "to any Patient in this batch."
                        ),
                    ))

        # DiagnosticReport.result[] must resolve to Observations
        if rtype == "DiagnosticReport":
            for i, result_ref in enumerate(resource.get("result") or []):
                ref = result_ref.get("reference", "")
                if _OBS_REF_RE.match(ref):
                    obs_id = ref.split("/", 1)[1]
                    if obs_ids and obs_id not in obs_ids:
                        report.issues.append(ValidationIssue(
                            severity=Severity.WARNING,
                            resource_type=rtype,
                            resource_id=rid,
                            path=f"result[{i}].reference",
                            rule="ref-obs-dangling",
                            message=(
                                f"DiagnosticReport.result[{i}].reference 'Observation/{obs_id}' "
                                "does not resolve to any Observation in this batch. "
                                "It may have been upserted separately."
                            ),
                        ))
