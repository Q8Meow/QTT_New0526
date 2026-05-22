"""Small value objects for PR137R validation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BundleAudit:
    status: str
    bundle_exists: bool
    row_count_value: int | None
    row_count_proven: bool
    schema_validated: bool
    validation_errors: tuple[str, ...]
    supported_row_contract_fields: tuple[str, ...]
    missing_row_contract_fields: tuple[str, ...]
    quantum_metadata_support: dict[str, bool]

    def as_report(self) -> dict[str, Any]:
        return {
            "functional_bundle_status": self.status,
            "row_count_proven": self.row_count_proven,
            "row_count_value": self.row_count_value,
            "schema_validated": self.schema_validated,
            "validation_error_count": len(self.validation_errors),
            "validation_errors": list(self.validation_errors),
            "row_contract_field_audit": {
                "supported_fields": list(self.supported_row_contract_fields),
                "missing_fields": list(self.missing_row_contract_fields),
            },
        }


@dataclass(frozen=True)
class ValidationOutcome:
    ok: bool
    failures: tuple[str, ...]
    receipts: tuple[str, ...]
