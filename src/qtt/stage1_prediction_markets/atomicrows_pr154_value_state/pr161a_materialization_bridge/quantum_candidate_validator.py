"""In-memory quantum candidate validator."""

from __future__ import annotations

from typing import Mapping


def validate_quantum_candidate_records(records: list[Mapping[str, object]]) -> list[str]:
    failures: list[str] = []
    for record in records:
        candidate_id = str(record.get("quantum_candidate_id"))
        if not record.get("classical_baseline_formula_id"):
            failures.append(f"PR161A_QUANTUM_BASELINE_MISSING:{candidate_id}")
        if record.get("quantum_backend_execution_evidence_created_flag") is not False:
            failures.append(f"PR161A_QUANTUM_BACKEND_EVIDENCE_CREATED:{candidate_id}")
        if record.get("optimizer_execution_evidence_created_flag") is not False:
            failures.append(f"PR161A_OPTIMIZER_EVIDENCE_CREATED:{candidate_id}")
        if record.get("profit_validation_tag") != "PROFIT_NOT_TESTED":
            failures.append(f"PR161A_QUANTUM_PROFIT_TAG_BAD:{candidate_id}")
    return failures

