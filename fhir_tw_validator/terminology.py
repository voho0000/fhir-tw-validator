"""Embedded terminology lookups for offline FHIR R4 validation.

No external API calls — all value sets are inlined here.
"""

# LOINC codes known to this bridge (from observation.py _LOINC_MAP).
# Additional codes encountered in the wild are only flagged as INFO.
KNOWN_LOINC_CODES: frozenset[str] = frozenset({
    "2345-7",   # glucose
    "718-7",    # hemoglobin
    "6690-2",   # WBC
    "777-3",    # platelet
    "2160-0",   # creatinine
    "3094-0",   # BUN
    "1920-8",   # AST
    "1742-6",   # ALT
    "2276-4",   # ferritin
    # Common additional lab LOINC codes
    "2823-3",   # potassium
    "2951-2",   # sodium
    "2075-0",   # chloride
    "1963-8",   # bicarbonate
    "2000-8",   # calcium
    "2777-1",   # phosphate
    "1975-2",   # bilirubin total
    "1742-6",   # ALT (duplicate guard)
    "6768-6",   # alkaline phosphatase
    "2532-0",   # LDH
    "13457-7",  # LDL
    "2093-3",   # cholesterol
    "2085-9",   # HDL
    "2571-8",   # triglycerides
    "4548-4",   # HbA1c
    "2339-0",   # glucose (plasma)
    "718-7",    # hemoglobin
    "789-8",    # RBC
    "20570-8",  # hematocrit
    "6690-2",   # WBC
    "26515-7",  # platelet
    "33959-8",  # procalcitonin
    "1988-5",   # CRP
    "2276-4",   # ferritin
    "2498-4",   # iron
    "2132-9",   # TIBC
    "14682-9",  # creatinine urine
    "2161-8",   # creatinine urine
    "57369-1",  # eGFR
    "33914-3",  # eGFR CKD-EPI
})

# HL7 observation status value set
OBS_STATUS_VALUES: frozenset[str] = frozenset({
    "registered", "preliminary", "final", "amended",
    "corrected", "cancelled", "entered-in-error", "unknown",
})

# HL7 diagnostic report status value set
DR_STATUS_VALUES: frozenset[str] = frozenset({
    "registered", "partial", "preliminary", "final",
    "amended", "corrected", "appended", "cancelled",
    "entered-in-error", "unknown",
})

# HL7 medication request status value set
MED_STATUS_VALUES: frozenset[str] = frozenset({
    "active", "on-hold", "cancelled", "completed",
    "entered-in-error", "stopped", "draft", "unknown",
})

# HL7 medication request intent value set
MED_INTENT_VALUES: frozenset[str] = frozenset({
    "proposal", "plan", "order", "original-order",
    "reflex-order", "filler-order", "instance-order", "option",
})

# HL7 condition clinical status
CONDITION_CLINICAL_STATUS_VALUES: frozenset[str] = frozenset({
    "active", "recurrence", "relapse", "inactive", "remission", "resolved",
})

# HL7 allergy intolerance category
ALLERGY_CATEGORY_VALUES: frozenset[str] = frozenset({
    "food", "medication", "environment", "biologic",
})

# HL7 allergy criticality
ALLERGY_CRITICALITY_VALUES: frozenset[str] = frozenset({
    "high", "low", "unable-to-assess",
})

# HL7 encounter status
ENCOUNTER_STATUS_VALUES: frozenset[str] = frozenset({
    "planned", "arrived", "triaged", "in-progress", "onleave",
    "finished", "cancelled", "entered-in-error", "unknown",
})

# HL7 procedure status
PROCEDURE_STATUS_VALUES: frozenset[str] = frozenset({
    "preparation", "in-progress", "not-done", "on-hold",
    "stopped", "completed", "entered-in-error", "unknown",
})

# Patient name use
NAME_USE_VALUES: frozenset[str] = frozenset({
    "usual", "official", "temp", "nickname", "anonymous", "old", "maiden",
})

# Patient gender
GENDER_VALUES: frozenset[str] = frozenset({
    "male", "female", "other", "unknown",
})

# valueQuantity comparator
QUANTITY_COMPARATOR_VALUES: frozenset[str] = frozenset({
    "<", "<=", ">=", ">",
})

# v3 observation interpretation system
OBS_INTERPRETATION_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"

# UCUM units system
UCUM_SYSTEM = "http://unitsofmeasure.org"

# Standard LOINC system URI
LOINC_SYSTEM = "http://loinc.org"

# NHI lab code OID
NHI_LAB_OID = "urn:oid:nhi.lab.code"
HIS_LAB_OID = "urn:oid:his.lab.code"

# NHI medication code OID
NHI_MED_OID = "urn:oid:nhi.medication.code"

# Encounter class system
ENCOUNTER_CLASS_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ActCode"

# Encounter class codes (common v3-ActCode values)
ENCOUNTER_CLASS_CODES: frozenset[str] = frozenset({
    "AMB", "IMP", "EMER", "VR", "HH", "OBSENC", "SS", "PRENC",
})

# Known code systems used by this bridge (custom OIDs are valid here)
KNOWN_OBSERVATION_SYSTEMS: frozenset[str] = frozenset({
    LOINC_SYSTEM,
    NHI_LAB_OID,
    HIS_LAB_OID,
    "urn:oid:his.lab.code",
    "http://snomed.info/sct",
})

KNOWN_CONDITION_SYSTEMS: frozenset[str] = frozenset({
    "http://snomed.info/sct",
    "http://hl7.org/fhir/sid/icd-10",
    "http://hl7.org/fhir/sid/icd-10-cm",
    "urn:oid:his.condition.code",
    "urn:oid:nhi.condition.code",
})
