"""QKU mapping for every external candidate."""

from __future__ import annotations

from typing import Any


def qku_external_candidate_mapping_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "mapping_id": f"PR162D_R1_QKU_MAP_{index:04d}",
            "candidate_id": record["candidate_id"],
            "qku_refs": record.get("qku_refs", []),
            "qku_formula_compute_engine_route": "QKU_FORMULA_COMPUTE_ENGINE",
            "feature_or_quantum_input_route": (
                "QUANTUM_OPTIMIZER_CANDIDATE_INPUT"
                if "quantum_candidate_id" in record
                else "FEATURE_BUILDER_CANDIDATE_INPUT"
            ),
            "live_order_authority": False,
        }
        for index, record in enumerate(candidates, start=1)
    ]
