from __future__ import annotations

from typing import Any, Mapping

from .validator import build_acceptance_artifacts, validate_ledger_record


def build_ledger_record(candidate: Mapping[str, Any]) -> dict[str, Any]:
    result = build_acceptance_artifacts(candidate)
    if result.accepted_ledger_record is None:
        raise ValueError(
            "candidate cannot produce accepted ledger record: "
            + ", ".join(result.decision_receipt["validation_failure_messages"])
        )
    return result.accepted_ledger_record


__all__ = ["build_ledger_record", "validate_ledger_record"]
