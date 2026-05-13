# fhir-tw-validator

**FHIR R4 Validator for Taiwan NHI Health Data（台灣健保 FHIR R4 驗證器）**

A lightweight, zero-dependency Python library that validates FHIR R4 resources generated from Taiwan's National Health Insurance (NHI) 健康存摺 (health booklet) system. Designed to work with [EHR-FHIR-BRIDGE](https://github.com/voho0000/EHR-FHIR-BRIDGE) but usable standalone.

---

## Features

| 功能 | 說明 |
|------|------|
| **Structural validation** | 驗證每種資源的必填欄位、cardinality、值域綁定 |
| **Terminology validation** | 離線檢查 LOINC、HL7 value sets、UCUM 單位 |
| **Taiwan NHI rules** | 身分證格式、醫令代碼（`^\d{4,6}[A-Z]$`）、健保藥品代碼（含舊式 `G0` 結尾）|
| **Reference integrity** | 跨資源 `subject.reference` 完整性、DR→Obs 參照 |
| **Three severity levels** | `error` / `warning` / `info` 分層報告 |
| **Zero dependencies** | 純 Python stdlib，Python ≥ 3.10 |

---

## Supported FHIR Resources

`Patient` · `Observation` · `DiagnosticReport` · `MedicationRequest` · `Condition` · `AllergyIntolerance` · `Encounter` · `Procedure`

---

## Quick Start

### Install

```bash
# From source (no PyPI release yet)
git clone https://github.com/voho0000/fhir-tw-validator.git
cd fhir-tw-validator
```

### CLI — validate a JSON file

```bash
# Default: show warnings and above (text report)
python scripts/validate_file.py examples/sample_bundle.json

# Errors only
python scripts/validate_file.py my_bundle.json --severity error

# Full detail including info, JSON output
python scripts/validate_file.py my_bundle.json --severity info --format json
```

**Sample output:**

```
============================================================
FHIR R4 Validation Report
============================================================
Patient  : P001
Generated: 2026-05-13 08:00 UTC
Resources: 3  Valid: 3  Errors: 0  Warnings: 0  Info: 1

── INFO (1) ────────────────────────────────────────────────
  [Observation/obs-gluc-001]
    [obs-loinc-unknown] code.coding[0].code
      LOINC code '2345-7' is not in the bridge's known LOINC set.

── Summary by resource type ────────────────────────────────
  MedicationRequest         1 resources   0 errors   0 warnings
  Observation               1 resources   0 errors   0 warnings
  Patient                   1 resources   0 errors   0 warnings
============================================================
```

### Python API

```python
import json
from fhir_tw_validator import validate_bundle, bundle_summary
from fhir_tw_validator.report import to_text, to_json

# Load resources
with open("my_bundle.json") as f:
    bundle = json.load(f)

if bundle.get("resourceType") == "Bundle":
    resources = [e["resource"] for e in bundle.get("entry", [])]
else:
    resources = bundle  # already a list

# Validate
reports = validate_bundle(resources)

# Summary
print(bundle_summary(reports))
# {'total': 3, 'valid': 3, 'with_errors': 0, 'error_count': 0, 'warning_count': 0, 'info_count': 1}

# Text report
print(to_text(reports, patient_id="P001"))

# JSON report (for APIs / frontend)
result = to_json(reports, patient_id="P001")
```

---

## Input Formats

The validator accepts:

| Format | Example |
|--------|---------|
| FHIR Bundle (`resourceType: "Bundle"`) | `{"resourceType":"Bundle","entry":[{"resource":{...}},...]}` |
| Single FHIR resource | `{"resourceType":"Patient","id":"P001",...}` |
| Array of resources | `[{"resourceType":"Patient",...}, {"resourceType":"Observation",...}]` |

---

## Validation Rules

### Structural Rules (per resource type)

#### Patient
| Rule ID | Check | Severity |
|---------|-------|----------|
| `pat-identifier-required` | `identifier` non-empty | ERROR |
| `pat-name-required` | `name` non-empty | ERROR |
| `pat-gender-invalid` | `gender` ∈ `{male,female,other,unknown}` | ERROR |
| `pat-name-use-invalid` | `name[*].use` in HL7 value set | WARNING |
| `pat-birthdate-format` | `birthDate` matches YYYY-MM-DD | WARNING |

#### Observation
| Rule ID | Check | Severity |
|---------|-------|----------|
| `obs-status-required` | `status` present & valid | ERROR |
| `obs-code-required` | `code.coding` non-empty | ERROR |
| `obs-subject-required` | `subject.reference` = `Patient/<id>` | ERROR |
| `obs-comparator-invalid` | `valueQuantity.comparator` ∈ `{<,<=,>=,>}` | ERROR |
| `obs-refrange-numeric` | `referenceRange[*].low/high.value` numeric | ERROR |
| `obs-category-missing` | `category` present | WARNING |
| `obs-value-missing` | at least one `value[x]` or `dataAbsentReason` | WARNING |
| `obs-ucum-system` | `valueQuantity.system` = UCUM URI | WARNING |
| `obs-loinc-unknown` | LOINC code recognized | INFO |

#### DiagnosticReport
| Rule ID | Check | Severity |
|---------|-------|----------|
| `dr-status-required` | `status` present & valid | ERROR |
| `dr-code-required` | `code` present | ERROR |
| `dr-subject-required` | `subject.reference` valid | ERROR |
| `dr-issued-missing` | `issued` present when `status=final` | WARNING |
| `dr-result-ref-invalid` | `result[*].reference` = `Observation/<id>` | WARNING |

#### MedicationRequest
| Rule ID | Check | Severity |
|---------|-------|----------|
| `med-status-required` | `status` present & valid | ERROR |
| `med-intent-required` | `intent` present & valid | ERROR |
| `med-medication-required` | `medicationCodeableConcept` with coding | ERROR |
| `med-subject-required` | `subject.reference` valid | ERROR |
| `med-dosage-text-missing` | `dosageInstruction[*].text` present | WARNING |

#### AllergyIntolerance
| Rule ID | Check | Severity |
|---------|-------|----------|
| `ai-patient-required` | `patient.reference` valid | ERROR |
| `ai-code-required` | `code` present | ERROR |
| `ai-category-invalid` | `category[*]` ∈ `{food,medication,environment,biologic}` | ERROR |
| `ai-criticality-invalid` | `criticality` ∈ `{high,low,unable-to-assess}` | ERROR |

#### Encounter
| Rule ID | Check | Severity |
|---------|-------|----------|
| `enc-status-required` | `status` present & valid | ERROR |
| `enc-class-required` | `class.code` present | ERROR |
| `enc-subject-required` | `subject.reference` valid | ERROR |
| `enc-period-start-missing` | `period.start` present | WARNING |

#### Condition / Procedure
> `code` present (ERROR), `status` valid (ERROR), `subject.reference` valid (ERROR)

---

### Taiwan NHI Rules

| Rule ID | Check | Severity |
|---------|-------|----------|
| `tw-nhi-id-format` | 10-char Patient identifier matches 身分證/ARC format | WARNING |
| `tw-nhi-lab-code-format` | `urn:oid:nhi.lab.code` matches `^\d{4,6}[A-Z]$` | WARNING |
| `tw-nhi-med-code-format` | `urn:oid:nhi.medication.code` matches `^[A-Z]{1,3}[0-9A-Z]{7,9}$` (including `G0` suffix format) | INFO |
| `tw-timezone-missing` | datetime fields include `+08:00` offset | WARNING |
| `tw-meta-source` | `meta.source` = `"ehr-fhir-bridge/scraper"` | INFO |

---

### Reference Integrity (batch validation only)

| Rule ID | Check | Severity |
|---------|-------|----------|
| `ref-patient-dangling` | `subject.reference = Patient/X` → X exists in batch | ERROR |
| `ref-obs-dangling` | `DiagnosticReport.result[*].reference` → Observation exists in batch | WARNING |

---

## Module Structure

```
fhir_tw_validator/
  __init__.py      # Public API: validate_resource, validate_bundle
  base.py          # Severity, ValidationIssue, ValidationReport
  terminology.py   # Embedded code-system lookups (offline)
  taiwan.py        # Taiwan NHI-specific rules
  structural.py    # Per-resource field checks
  references.py    # Cross-resource reference integrity
  bundle.py        # Batch validator
  report.py        # Text + JSON report renderers
scripts/
  validate_file.py # CLI entrypoint
examples/
  sample_bundle.json  # Valid sample FHIR Bundle for testing
```

---

## Integration with EHR-FHIR-BRIDGE

This validator is embedded in [EHR-FHIR-BRIDGE](https://github.com/voho0000/EHR-FHIR-BRIDGE) as `backend/app/validator/`. It exposes two HTTP endpoints:

```
GET  /fhir/validate?patient=P001&severity=warning&format=json
POST /fhir/validate                          ← accepts FHIR JSON body
```

The web UI at `/validate` provides drag-and-drop file upload with an interactive results viewer.

---

## Real-World Results (VGH dataset)

Validated against a real patient record (1,528 FHIR R4 resources from 健康存摺):

| Resource | Count | ERRORs | WARNINGs |
|----------|-------|--------|----------|
| Patient | 1 | 0 | 0 |
| Observation | 594 | 0 | 0 |
| DiagnosticReport | 445 | 0 | 386* |
| MedicationRequest | 448 | 0 | 0 |
| Encounter | 38 | 0 | 0 |
| Procedure | 2 | 0 | 0 |

> \* `dr-issued-missing`: LAB DiagnosticReports generated by an older mapper version that omitted the `issued` field. Fixed in mapper v0.2 — will be resolved upon next resync.

**Conclusion: 0 FHIR R4 structural errors across 1,528 resources.**

---

## Requirements

- Python ≥ 3.10
- No external dependencies (pure stdlib)

---

## License

MIT © 2026 [voho0000](https://github.com/voho0000)

---

## Related Projects

- [EHR-FHIR-BRIDGE](https://github.com/voho0000/EHR-FHIR-BRIDGE) — AI-powered HIS → FHIR R4 bridge with SMART on FHIR support
- [HL7 FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [Taiwan NHI 健康存摺](https://myhealthbank.nhi.gov.tw)
