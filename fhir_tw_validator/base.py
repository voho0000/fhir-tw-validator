from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    ERROR   = "error"    # FHIR-invalid; consumer will likely fail
    WARNING = "warning"  # non-conformant but parseable
    INFO    = "info"     # advisory / Taiwan-specific guidance


@dataclass
class ValidationIssue:
    severity: Severity
    resource_type: str
    resource_id: str
    path: str    # dotted FHIR path, e.g. "Observation.code.coding[0].system"
    rule: str    # machine-readable id, e.g. "obs-status-required"
    message: str # human-readable


@dataclass
class ValidationReport:
    resource_type: str
    resource_id: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)

    def add(self, severity: Severity, path: str, rule: str, message: str) -> None:
        self.issues.append(ValidationIssue(
            severity=severity,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            path=path,
            rule=rule,
            message=message,
        ))

    def error(self, path: str, rule: str, message: str) -> None:
        self.add(Severity.ERROR, path, rule, message)

    def warning(self, path: str, rule: str, message: str) -> None:
        self.add(Severity.WARNING, path, rule, message)

    def info(self, path: str, rule: str, message: str) -> None:
        self.add(Severity.INFO, path, rule, message)
