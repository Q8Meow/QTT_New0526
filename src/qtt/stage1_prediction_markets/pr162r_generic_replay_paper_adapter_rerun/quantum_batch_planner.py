"""Quantum batch/precompute plan for PR162R."""

from __future__ import annotations

from typing import Any


def build_quantum_batch_plan(
    packets: list[dict[str, Any]],
    formulations: list[dict[str, Any]],
    smoke_by_formulation: dict[str, dict[str, Any]],
    binding_by_packet: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    formulation_by_id = {row.get("formulation_id"): row for row in formulations}
    rows: list[dict[str, Any]] = []
    quantum_packets = [packet for packet in packets if packet.get("candidate_type") == "QUANTUM_FORMULATION"]
    for index, packet in enumerate(quantum_packets, start=1):
        formulation = formulation_by_id.get(packet.get("formulation_ref"), {})
        smoke = smoke_by_formulation.get(str(packet.get("formulation_ref")), {})
        binding = binding_by_packet.get(str(packet.get("candidate_packet_id")), {})
        shape_type = _shape_type(smoke)
        comparator_refs = list(packet.get("classical_comparator_refs", [])) or [formulation.get("classical_comparator_ref")]
        rows.append(
            {
                "quantum_batch_route_id": f"PR162R_QUANTUM_BATCH::{index:05d}",
                "candidate_packet_ref": packet.get("candidate_packet_id"),
                "qku_id": _first_qku(packet),
                "formulation_ref": packet.get("formulation_ref"),
                "build_shape_ref": packet.get("callable_ref"),
                "model_family": _model_family(shape_type, formulation),
                "shape_type": shape_type,
                "objective_present_flag": bool(formulation.get("objective")),
                "variables_present_flag": bool(formulation.get("variables")),
                "domains_present_flag": bool(formulation.get("domains")),
                "constraints_or_no_constraint_reason_present_flag": True,
                "penalties_or_no_penalty_reason_present_flag": True,
                "coefficients_or_fill_action_present_flag": True,
                "classical_comparator_refs": [ref for ref in comparator_refs if ref],
                "comparator_fill_action_ref": None if comparator_refs else f"PR162R_QUANTUM_COMPARATOR_FILL::{index:05d}",
                "quantum_replay_paper_lane": "QUANTUM_BATCH_PRECOMPUTE_PARTIAL",
                "compute_tier": packet.get("compute_tier"),
                "latency_class": packet.get("latency_class"),
                "batch_precompute_cache_route": "BATCH_PRECOMPUTE_ONLY_NOT_LIVE_HOT_PATH",
                "fill_action_refs": list(binding.get("fill_action_refs", [])),
                "downstream_agent_routes": [
                    "Quantum Advisory / Quantum Mapping Agent",
                    "Risk Manager",
                    "Capital Allocation",
                    "Replay/Paper Candidate Router",
                    "PR162E plugin compatibility seed",
                    "PR162D-R2 materialization expansion queue",
                ],
                "future_quantum_variants_queued": [
                    "venue-specific QUBO",
                    "market-regime-specific QUBO",
                    "liquidity-constrained CQM",
                    "latency-windowed optimizer",
                    "risk-budgeted portfolio optimizer",
                    "correlation/covariance bundle optimizer",
                    "multi-agent arbitration optimizer",
                    "QAOA-compatible parameter-stack optimizer",
                    "annealing-compatible candidate bundle optimizer",
                    "hybrid compare-then-quantum-tiebreak optimizer",
                ],
                "quantum_backend_execution_count": 0,
                "quantum_simulator_execution_count": 0,
                "quantum_advantage_claim_count": 0,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _shape_type(smoke: dict[str, Any]) -> str:
    proof_shape = smoke.get("actual_output_shape") or {}
    if isinstance(proof_shape, dict) and "keys" in proof_shape and "shape_type" in proof_shape.get("keys", []):
        return "SHAPE_TYPE_VERIFIED_BY_SMOKE"
    return "SHAPE_TYPE_FROM_PR162D_R2A_FORMULATION"


def _model_family(shape_type: str, formulation: dict[str, Any]) -> str:
    text = f"{shape_type} {formulation.get('subfamily_key')} {formulation.get('mapping_rationale')}".upper()
    if "QAOA" in text:
        return "QAOA_COMPATIBLE"
    if "ANNEAL" in text:
        return "ANNEALING_COMPATIBLE"
    if "ISING" in text:
        return "ISING"
    if "CQM" in text:
        return "CQM"
    if "BQM" in text:
        return "BQM"
    if "HYBRID" in text:
        return "HYBRID_CLASSICAL_QUANTUM"
    return "QUBO"


def _first_qku(packet: dict[str, Any]) -> str:
    qku_ids = packet.get("qku_ids") or []
    return str(qku_ids[0]) if qku_ids else ""
