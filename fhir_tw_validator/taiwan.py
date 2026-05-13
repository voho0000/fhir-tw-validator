"""Taiwan NHI-specific validation rules.

Validates NHI ID formats, 醫令代碼 patterns, ROC timezone presence,
and bridge-specific meta.source tagging.
"""
from __future__ import annotations
import re

from .base import ValidationReport

# Taiwan ROC 身分證號 (citizens)
_NHI_ID_RE = re.compile(r"^[A-Z][12]\d{8}$")
# Taiwan ARC (居留證) for foreign residents
_ARC_ID_RE = re.compile(r"^[A-Z][89]\d{8}$")

# NHI 醫令代碼: 4-6 digits + one uppercase letter
_NHI_LAB_CODE_RE = re.compile(r"^\d{4,6}[A-Z]$")

# NHI 健保藥品代碼: 1-3 uppercase letters + 7-9 alphanumeric chars.
# Old-format codes end in 'G0' (generic substitution indicator), e.g. AC346701G0.
_NHI_MED_CODE_RE = re.compile(r"^[A-Z]{1,3}[0-9A-Z]{7,9}$")

# Datetime fields expected to carry timezone
_DATETIME_FIELDS = (
    "effectiveDateTime", "effectivePeriod", "authoredOn",
    "issued", "recordedDate", "onsetDateTime", "performedDateTime",
    "start", "end",
)

BRIDGE_META_SOURCE = "ehr-fhir-bridge/scraper"


def validate_taiwan(resource: dict, report: ValidationReport) -> None:
    """Append Taiwan-specific issues to an existing ValidationReport."""
    _check_meta_source(resource, report)
    _check_timezone(resource, report)

    rtype = resource.get("resourceType", "")
    if rtype == "Patient":
        _check_patient_nhi(resource, report)
    elif rtype == "Observation":
        _check_obs_nhi_lab_code(resource, report)
    elif rtype == "MedicationRequest":
        _check_med_nhi_code(resource, report)


# ── internal helpers ─────────────────────────────────────────────────────────

def _check_meta_source(resource: dict, report: ValidationReport) -> None:
    meta = resource.get("meta") or {}
    source = meta.get("source", "")
    if source != BRIDGE_META_SOURCE:
        report.info(
            "meta.source",
            "tw-meta-source",
            f"meta.source should be '{BRIDGE_META_SOURCE}' for bridge-generated resources. "
            f"Got: '{source}'",
        )


def _check_timezone(resource: dict, report: ValidationReport) -> None:
    """Datetime literals without a timezone offset lose clinical meaning."""
    for field in _DATETIME_FIELDS:
        value = resource.get(field)
        if isinstance(value, str) and "T" in value:
            if not (value.endswith("+08:00") or value.endswith("Z") or
                    re.search(r"[+-]\d{2}:\d{2}$", value)):
                report.warning(
                    field,
                    "tw-timezone-missing",
                    f"{field} datetime '{value}' has no timezone offset. "
                    "Taiwan resources should use +08:00.",
                )


def _check_patient_nhi(resource: dict, report: ValidationReport) -> None:
    for i, ident in enumerate(resource.get("identifier") or []):
        value = ident.get("value") or ""
        if len(value) == 10:
            if not (_NHI_ID_RE.match(value) or _ARC_ID_RE.match(value)):
                report.warning(
                    f"identifier[{i}].value",
                    "tw-nhi-id-format",
                    f"10-character identifier '{value}' does not match Taiwan NHI ID format "
                    "(^[A-Z][12]\\d{{8}}$) or ARC format (^[A-Z][89]\\d{{8}}$). "
                    "May be a hospital MRN.",
                )


def _check_obs_nhi_lab_code(resource: dict, report: ValidationReport) -> None:
    for i, coding in enumerate((resource.get("code") or {}).get("coding") or []):
        if coding.get("system") in ("urn:oid:nhi.lab.code", "urn:oid:his.lab.code"):
            code = coding.get("code") or ""
            if code and not _NHI_LAB_CODE_RE.match(code):
                report.warning(
                    f"code.coding[{i}].code",
                    "tw-nhi-lab-code-format",
                    f"NHI 醫令代碼 '{code}' does not match expected pattern ^\\d{{4,6}}[A-Z]$.",
                )


def _check_med_nhi_code(resource: dict, report: ValidationReport) -> None:
    med_cc = resource.get("medicationCodeableConcept") or {}
    for i, coding in enumerate(med_cc.get("coding") or []):
        if coding.get("system") == "urn:oid:nhi.medication.code":
            code = coding.get("code") or ""
            if code and not _NHI_MED_CODE_RE.match(code):
                report.info(
                    f"medicationCodeableConcept.coding[{i}].code",
                    "tw-nhi-med-code-format",
                    f"NHI 健保藥品代碼 '{code}' does not match expected pattern "
                    "^[A-Z]{{1,3}}\\d{{7,9}}$.",
                )
