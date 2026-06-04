"""Quantum replay/paper eligibility records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def quantum_replay_paper_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if candidate_type(record) != "QUANTUM":
            continue
        mapping_ready = bool(
            record.get("mathematical_objective")
            and record.get("variable_definitions")
            and record.get("coefficient_definitions")
            and (
                record.get("qubo_mapping")
                or record.get("ising_mapping")
                or record.get("bqm_cqm_mapping")
                or record.get("qaoa_vqe_samplingvqe_annealing_mapping")
            )
        )
        rows.append(
            {
                "candidate_id": candidate_id(record),
                "quantum_specific_mapping_ready_flag": mapping_ready,
                "classical_comparator_ready_flag": bool(record.get("strongest_classical_comparator_mapping")),
                "replay_paper_quantum_eligible_flag": mapping_ready,
                "latency_class": "QUANTUM_BATCH_ONLY",
                "remote_quantum_hot_path_flag": False,
                "live_order_authority": False,
            }
        )
    return rows
