"""PR162C formula-to-dataset binding records."""

from __future__ import annotations

from typing import Any

from . import constants as c


def formula_to_dataset_binding_records(proofs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for proof in proofs:
        for formula_ref in proof.get("formula_refs") or []:
            records.append(
                {
                    "binding_id": f"PR162C-FORMULA-DATASET-BINDING-{proof['qku_id']}-{formula_ref}",
                    "qku_id": proof["qku_id"],
                    "formula_ref": formula_ref,
                    "dataset_ids": proof["dataset_ids"],
                    "required_input_fields": proof["required_input_fields"],
                    "provided_input_fields": proof["provided_input_fields"],
                    "missing_input_fields": proof["missing_input_fields"],
                    "binding_status": proof["strict_coverage_status"],
                    "blocker_code": proof["blocker_code"],
                    "created_by_pr": c.PR_ID,
                }
            )
    return records
