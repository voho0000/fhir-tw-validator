"""FHIR R4 Validator for Taiwan NHI health data.

Public API:
    validate_resource(resource: dict) -> ValidationReport
    validate_bundle(resources: list[dict]) -> list[ValidationReport]
    ValidationReport, ValidationIssue, Severity
"""
from .base import ValidationIssue, ValidationReport, Severity
from .structural import validate_resource
from .bundle import validate_bundle, summary as bundle_summary

__all__ = [
    "validate_resource",
    "validate_bundle",
    "bundle_summary",
    "ValidationReport",
    "ValidationIssue",
    "Severity",
]
