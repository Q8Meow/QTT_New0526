"""Quantum advisory passthrough for PR166-S without backend execution."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract
from .selected_batch_loader import LoadedSelection


def build_quantum_advisory_passthrough_rows(
    selection: LoadedSelection,
    attribution_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    attr_by_candidate = {str(row["candidate_packet_id"]): row for row in attribution_rows}
    selected_ids = {context.candidate_packet_id for context in selection.contexts}
    rows: list[dict[str, Any]] = []
    for index, quantum in enumerate(selection.quantum_rows, start=1):
        cid = str(quantum["candidate_packet_id"])
        attr = attr_by_candidate.get(cid)
        priority_delta = _priority_delta(attr, quantum)
        row_id = f"PR166_S_QUANTUM_ADVISORY::{index:06d}"
        rows.append(
            {
                "quantum_advisory_passthrough_id": row_id,
                "candidate_packet_id": cid,
                "qku_id": quantum.get("qku_id", ""),
                "source_quantum_selection_route_ref": quantum.get("quantum_selection_route_id", ""),
                "quantum_model_class": quantum.get("quantum_model_class_candidate", "CLASSICAL_ONLY"),
                "variable_domain": quantum.get("variable_domain", ""),
                "constraint_handling": quantum.get("constraint_handling", ""),
                "objective_order": quantum.get("objective_order", ""),
                "qiskit_route_candidate": quantum.get("qiskit_route_candidate", ""),
                "dwave_route_candidate": quantum.get("dwave_route_candidate", ""),
                "quantum_repair_route": quantum.get("quantum_repair_route", "PR166-Q_OPTIONAL_COMPARATOR_REVIEW"),
                "execution_result_interaction": _interaction(attr, cid in selected_ids),
                "future_quantum_comparator_priority_delta": priority_delta,
                "route_to_PR166_Q": priority_delta >= 0 and quantum.get("quantum_model_class_candidate") != "CLASSICAL_ONLY",
                "no_backend_execution": True,
                "no_quantum_advantage_claim": True,
                "backend_execution_created_by_PR166_S": False,
                "advantage_claim_created_by_PR166_S": False,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_D_QuantumSelectionRouter.report.json",
                    source_row_ref=quantum.get("quantum_selection_route_id", cid),
                    computed_by_module="quantum_advisory_passthrough",
                    owning_agent="quantum_mapper_advisory_agent",
                    consuming_agent="quantum_mapper_advisory_agent",
                    downstream_action_type="PR166-Q advisory comparator input",
                    downstream_pr_route="PR166-Q",
                    downstream_artifact_route="PR166-Q",
                    no_orphan_status="CONNECTED_TO_PR166_Q_ROUTE",
                ),
            }
        )
    return rows


def _interaction(attr: dict[str, Any] | None, selected: bool) -> str:
    if attr is None:
        return "NO_EXECUTION_REQUIRED_WITH_REASON" if not selected else "REPAIR_REQUIRED_BEFORE_EXECUTION"
    if attr.get("net_return_proxy", 0.0) > 0:
        return "REPLAY_PAPER_RESULT_INCREASES_COMPARATOR_PRIORITY"
    return "REPLAY_PAPER_RESULT_DECREASES_COMPARATOR_PRIORITY"


def _priority_delta(attr: dict[str, Any] | None, quantum: dict[str, Any]) -> float:
    if attr is None:
        return 0.0
    base = float(quantum.get("quantum_candidate_selection_score", 0.0) or 0.0)
    return round((0.08 if attr.get("net_return_proxy", 0.0) > 0 else -0.08) + base * 0.02, 6)
