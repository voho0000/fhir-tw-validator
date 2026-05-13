"""Per-resource FHIR R4 structural validation.

Each validate_<type> function checks required fields, cardinality,
and value-set bindings for one resource type.
"""
from __future__ import annotations
import re

from .base import ValidationReport
from . import terminology as T

# Matches a valid FHIR resource reference: "ResourceType/id"
_REFERENCE_RE = re.compile(r"^[A-Za-z]+/.+")
# Valid Patient reference specifically
_PATIENT_REF_RE = re.compile(r"^Patient/\S+")
# Valid Observation reference
_OBS_REF_RE = re.compile(r"^Observation/\S+")
# Valid YYYY-MM-DD date
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_resource(resource: dict) -> ValidationReport:
    """Dispatch to the correct per-type validator and return a ValidationReport."""
    rtype = resource.get("resourceType", "Unknown")
    rid = resource.get("id", "")
    report = ValidationReport(resource_type=rtype, resource_id=rid)

    if not rid:
        report.error("id", "fhir-id-required", "Resource must have an 'id' field.")

    _VALIDATORS.get(rtype, _validate_unknown)(resource, report)
    return report


# ── Patient ──────────────────────────────────────────────────────────────────

def _validate_patient(resource: dict, report: ValidationReport) -> None:
    if not (resource.get("identifier") or []):
        report.error(
            "identifier", "pat-identifier-required",
            "Patient.identifier must contain at least one entry.",
        )
    if not (resource.get("name") or []):
        report.error(
            "name", "pat-name-required",
            "Patient.name must contain at least one entry.",
        )
    for i, n in enumerate(resource.get("name") or []):
        use = n.get("use")
        if use and use not in T.NAME_USE_VALUES:
            report.warning(
                f"name[{i}].use", "pat-name-use-invalid",
                f"name[{i}].use '{use}' is not in the FHIR R4 name-use value set. "
                f"Expected one of: {sorted(T.NAME_USE_VALUES)}",
            )

    gender = resource.get("gender")
    if gender is not None and gender not in T.GENDER_VALUES:
        report.error(
            "gender", "pat-gender-invalid",
            f"Patient.gender '{gender}' is not valid. "
            f"Expected one of: {sorted(T.GENDER_VALUES)}",
        )

    birth = resource.get("birthDate")
    if birth is not None and not _DATE_RE.match(str(birth)):
        report.warning(
            "birthDate", "pat-birthdate-format",
            f"Patient.birthDate '{birth}' does not match YYYY-MM-DD.",
        )


# ── Observation ──────────────────────────────────────────────────────────────

def _validate_observation(resource: dict, report: ValidationReport) -> None:
    status = resource.get("status")
    if not status:
        report.error(
            "status", "obs-status-required",
            "Observation.status is required.",
        )
    elif status not in T.OBS_STATUS_VALUES:
        report.error(
            "status", "obs-status-invalid",
            f"Observation.status '{status}' is not in the FHIR R4 value set. "
            f"Expected one of: {sorted(T.OBS_STATUS_VALUES)}",
        )

    code = resource.get("code") or {}
    codings = code.get("coding") or []
    if not codings:
        report.error(
            "code.coding", "obs-code-required",
            "Observation.code must have at least one coding.",
        )
    else:
        for i, c in enumerate(codings):
            sys = c.get("system", "")
            if sys == T.LOINC_SYSTEM:
                code_val = c.get("code", "")
                if code_val and code_val not in T.KNOWN_LOINC_CODES:
                    report.info(
                        f"code.coding[{i}].code", "obs-loinc-unknown",
                        f"LOINC code '{code_val}' is not in the bridge's known LOINC set. "
                        "Verify this is the correct LOINC code.",
                    )

    _check_patient_reference(resource, "subject", "obs-subject-required", report)

    category = resource.get("category")
    if not category:
        report.warning(
            "category", "obs-category-missing",
            "Observation.category is recommended (e.g. 'laboratory').",
        )

    # Check value[x] presence
    value_keys = {k for k in resource if k.startswith("value")}
    if not value_keys and not resource.get("dataAbsentReason") and not resource.get("component"):
        report.warning(
            "value[x]", "obs-value-missing",
            "Observation has no value[x] or dataAbsentReason. "
            "Consider using dataAbsentReason if value is genuinely unknown.",
        )

    # valueQuantity checks
    vq = resource.get("valueQuantity")
    if isinstance(vq, dict):
        if vq.get("system") and vq.get("system") != T.UCUM_SYSTEM:
            report.warning(
                "valueQuantity.system", "obs-ucum-system",
                f"valueQuantity.system should be '{T.UCUM_SYSTEM}' (UCUM). Got: '{vq.get('system')}'",
            )
        if vq.get("system") == T.UCUM_SYSTEM and not vq.get("code"):
            report.warning(
                "valueQuantity.code", "obs-ucum-code-empty",
                "valueQuantity.code (UCUM unit code) is empty.",
            )
        cmp = vq.get("comparator")
        if cmp and cmp not in T.QUANTITY_COMPARATOR_VALUES:
            report.error(
                "valueQuantity.comparator", "obs-comparator-invalid",
                f"valueQuantity.comparator '{cmp}' is not valid. "
                f"Expected one of: {sorted(T.QUANTITY_COMPARATOR_VALUES)}",
            )

    # referenceRange numeric check
    for i, rr in enumerate(resource.get("referenceRange") or []):
        for bound in ("low", "high"):
            b = rr.get(bound)
            if b is not None:
                v = b.get("value")
                if v is not None and not isinstance(v, (int, float)):
                    report.error(
                        f"referenceRange[{i}].{bound}.value",
                        "obs-refrange-numeric",
                        f"referenceRange[{i}].{bound}.value must be numeric. Got: {v!r}",
                    )

    # interpretation system check
    for i, interp in enumerate(resource.get("interpretation") or []):
        for j, c in enumerate(interp.get("coding") or []):
            sys = c.get("system", "")
            if sys and sys != T.OBS_INTERPRETATION_SYSTEM:
                report.warning(
                    f"interpretation[{i}].coding[{j}].system",
                    "obs-interp-system",
                    f"Unexpected interpretation system '{sys}'. "
                    f"Expected '{T.OBS_INTERPRETATION_SYSTEM}'.",
                )


# ── DiagnosticReport ─────────────────────────────────────────────────────────

def _validate_diagnostic_report(resource: dict, report: ValidationReport) -> None:
    status = resource.get("status")
    if not status:
        report.error("status", "dr-status-required", "DiagnosticReport.status is required.")
    elif status not in T.DR_STATUS_VALUES:
        report.error(
            "status", "dr-status-invalid",
            f"DiagnosticReport.status '{status}' is not valid. "
            f"Expected one of: {sorted(T.DR_STATUS_VALUES)}",
        )

    if not (resource.get("code") or {}).get("coding") and not (resource.get("code") or {}).get("text"):
        report.error("code", "dr-code-required", "DiagnosticReport.code is required.")

    _check_patient_reference(resource, "subject", "dr-subject-required", report)

    if status == "final" and not resource.get("issued"):
        report.warning(
            "issued", "dr-issued-missing",
            "DiagnosticReport.issued should be present when status is 'final'.",
        )

    for i, result_ref in enumerate(resource.get("result") or []):
        ref = result_ref.get("reference", "")
        if not _OBS_REF_RE.match(ref):
            report.warning(
                f"result[{i}].reference", "dr-result-ref-invalid",
                f"result[{i}].reference '{ref}' should match 'Observation/<id>'.",
            )


# ── MedicationRequest ────────────────────────────────────────────────────────

def _validate_medication_request(resource: dict, report: ValidationReport) -> None:
    status = resource.get("status")
    if not status:
        report.error("status", "med-status-required", "MedicationRequest.status is required.")
    elif status not in T.MED_STATUS_VALUES:
        report.error(
            "status", "med-status-invalid",
            f"MedicationRequest.status '{status}' is not valid. "
            f"Expected one of: {sorted(T.MED_STATUS_VALUES)}",
        )

    intent = resource.get("intent")
    if not intent:
        report.error("intent", "med-intent-required", "MedicationRequest.intent is required.")
    elif intent not in T.MED_INTENT_VALUES:
        report.error(
            "intent", "med-intent-invalid",
            f"MedicationRequest.intent '{intent}' is not valid. "
            f"Expected one of: {sorted(T.MED_INTENT_VALUES)}",
        )

    med_cc = resource.get("medicationCodeableConcept")
    if not med_cc or not (med_cc.get("coding") or med_cc.get("text")):
        report.error(
            "medicationCodeableConcept", "med-medication-required",
            "MedicationRequest must have medicationCodeableConcept with at least one coding or text.",
        )

    _check_patient_reference(resource, "subject", "med-subject-required", report)

    for i, di in enumerate(resource.get("dosageInstruction") or []):
        if not di.get("text"):
            report.warning(
                f"dosageInstruction[{i}].text", "med-dosage-text-missing",
                f"dosageInstruction[{i}].text is recommended for human-readable dosage.",
            )


# ── Condition ────────────────────────────────────────────────────────────────

def _validate_condition(resource: dict, report: ValidationReport) -> None:
    cs = resource.get("clinicalStatus") or {}
    cs_codings = cs.get("coding") or []
    if not cs_codings:
        report.error(
            "clinicalStatus", "con-clinical-status-required",
            "Condition.clinicalStatus is required and must have at least one coding.",
        )
    else:
        for i, c in enumerate(cs_codings):
            code_val = (c.get("code") or "").lower()
            if code_val and code_val not in T.CONDITION_CLINICAL_STATUS_VALUES:
                report.warning(
                    f"clinicalStatus.coding[{i}].code", "con-clinical-status-invalid",
                    f"clinicalStatus code '{code_val}' not in expected value set. "
                    f"Expected: {sorted(T.CONDITION_CLINICAL_STATUS_VALUES)}",
                )

    code = resource.get("code") or {}
    if not code.get("coding") and not code.get("text"):
        report.error("code", "con-code-required", "Condition.code is required.")

    _check_patient_reference(resource, "subject", "con-subject-required", report)

    for i, c in enumerate((resource.get("code") or {}).get("coding") or []):
        sys = c.get("system", "")
        if sys and sys not in T.KNOWN_CONDITION_SYSTEMS:
            report.info(
                f"code.coding[{i}].system", "con-code-system-unknown",
                f"Condition code system '{sys}' is not a standard system. "
                f"Expected one of: ICD-10, SNOMED-CT.",
            )


# ── AllergyIntolerance ───────────────────────────────────────────────────────

def _validate_allergy_intolerance(resource: dict, report: ValidationReport) -> None:
    # AllergyIntolerance uses "patient" not "subject"
    pat_ref = (resource.get("patient") or {}).get("reference", "")
    if not _PATIENT_REF_RE.match(pat_ref):
        report.error(
            "patient.reference", "ai-patient-required",
            f"AllergyIntolerance.patient.reference must match 'Patient/<id>'. Got: '{pat_ref}'",
        )

    code = resource.get("code") or {}
    if not code.get("coding") and not code.get("text"):
        report.error("code", "ai-code-required", "AllergyIntolerance.code is required.")

    for i, cat in enumerate(resource.get("category") or []):
        if cat not in T.ALLERGY_CATEGORY_VALUES:
            report.error(
                f"category[{i}]", "ai-category-invalid",
                f"AllergyIntolerance.category[{i}] '{cat}' is not valid. "
                f"Expected one of: {sorted(T.ALLERGY_CATEGORY_VALUES)}",
            )

    criticality = resource.get("criticality")
    if criticality and criticality not in T.ALLERGY_CRITICALITY_VALUES:
        report.error(
            "criticality", "ai-criticality-invalid",
            f"AllergyIntolerance.criticality '{criticality}' is not valid. "
            f"Expected one of: {sorted(T.ALLERGY_CRITICALITY_VALUES)}",
        )


# ── Encounter ────────────────────────────────────────────────────────────────

def _validate_encounter(resource: dict, report: ValidationReport) -> None:
    status = resource.get("status")
    if not status:
        report.error("status", "enc-status-required", "Encounter.status is required.")
    elif status not in T.ENCOUNTER_STATUS_VALUES:
        report.error(
            "status", "enc-status-invalid",
            f"Encounter.status '{status}' is not valid. "
            f"Expected one of: {sorted(T.ENCOUNTER_STATUS_VALUES)}",
        )

    cls = resource.get("class") or {}
    if not cls.get("code"):
        report.error(
            "class", "enc-class-required",
            "Encounter.class is required and must have a 'code' (e.g. AMB, IMP, EMER).",
        )
    else:
        cls_code = cls.get("code", "")
        if cls_code and cls_code not in T.ENCOUNTER_CLASS_CODES:
            report.warning(
                "class.code", "enc-class-code-unknown",
                f"Encounter.class.code '{cls_code}' is not a standard v3-ActCode value. "
                f"Common values: {sorted(T.ENCOUNTER_CLASS_CODES)}",
            )

    _check_patient_reference(resource, "subject", "enc-subject-required", report)

    period = resource.get("period") or {}
    if not period.get("start"):
        report.warning(
            "period.start", "enc-period-start-missing",
            "Encounter.period.start is recommended.",
        )


# ── Procedure ────────────────────────────────────────────────────────────────

def _validate_procedure(resource: dict, report: ValidationReport) -> None:
    status = resource.get("status")
    if not status:
        report.error("status", "proc-status-required", "Procedure.status is required.")
    elif status not in T.PROCEDURE_STATUS_VALUES:
        report.error(
            "status", "proc-status-invalid",
            f"Procedure.status '{status}' is not valid. "
            f"Expected one of: {sorted(T.PROCEDURE_STATUS_VALUES)}",
        )

    code = resource.get("code") or {}
    if not code.get("coding") and not code.get("text"):
        report.error("code", "proc-code-required", "Procedure.code is required.")

    _check_patient_reference(resource, "subject", "proc-subject-required", report)


# ── Unknown resource type ────────────────────────────────────────────────────

def _validate_unknown(resource: dict, report: ValidationReport) -> None:
    rtype = resource.get("resourceType", "Unknown")
    report.info(
        "resourceType", "fhir-unknown-type",
        f"Resource type '{rtype}' is not validated by this bridge validator. "
        "Only Patient, Observation, DiagnosticReport, MedicationRequest, "
        "Condition, AllergyIntolerance, Encounter, Procedure are supported.",
    )


# ── Shared helper ────────────────────────────────────────────────────────────

def _check_patient_reference(
    resource: dict, field: str, rule: str, report: ValidationReport
) -> None:
    ref_obj = resource.get(field) or {}
    ref = ref_obj.get("reference", "")
    if not _PATIENT_REF_RE.match(ref):
        report.error(
            f"{field}.reference", rule,
            f"{resource.get('resourceType', '')}.{field}.reference must match "
            f"'Patient/<id>'. Got: '{ref}'",
        )


# ── Dispatch table ───────────────────────────────────────────────────────────

_VALIDATORS = {
    "Patient":              _validate_patient,
    "Observation":          _validate_observation,
    "DiagnosticReport":     _validate_diagnostic_report,
    "MedicationRequest":    _validate_medication_request,
    "Condition":            _validate_condition,
    "AllergyIntolerance":   _validate_allergy_intolerance,
    "Encounter":            _validate_encounter,
    "Procedure":            _validate_procedure,
}
