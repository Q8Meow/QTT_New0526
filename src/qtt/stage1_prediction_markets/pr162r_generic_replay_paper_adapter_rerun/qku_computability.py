"""QKU computability route classification for PR162R."""

from __future__ import annotations

from typing import Any


def build_qku_computability_rows(
    packets: list[dict[str, Any]],
    formulations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    formulations_by_id = {row.get("formulation_id"): row for row in formulations}
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        formulation = formulations_by_id.get(packet.get("formulation_ref"), {})
        route, reason, fill_action = _route_for(packet, formulation)
        upstream = list(packet.get("upstream_pr_refs", []))
        downstream = list(packet.get("downstream_pr_refs", []))
        if not upstream:
            upstream = ["PR162D_R2A_CandidatePacketV1Registry.report.json"]
        if not downstream:
            downstream = ["PR162R", "PR163", "PR164", "PR165", "PR162E"]
        rows.append(
            {
                "classification_id": f"PR162R_QKU_COMPUTABILITY::{index:05d}",
                "candidate_packet_ref": packet.get("candidate_packet_id"),
                "qku_id": _first_qku(packet),
                "qku_ids": list(packet.get("qku_ids", [])),
                "formulation_ref": packet.get("formulation_ref"),
                "callable_ref": packet.get("callable_ref"),
                "candidate_type": packet.get("candidate_type"),
                "computability_route": route,
                "computability_reason": reason,
                "exact_fill_action_ref": fill_action,
                "formula_callable_present_flag": bool(packet.get("callable_ref")) if packet.get("candidate_type") in {"FORMULA", "FEATURE"} else None,
                "algorithm_callable_present_flag": bool(packet.get("callable_ref")) if packet.get("candidate_type") == "ALGORITHM" else None,
                "quantum_shape_payload_required_flag": packet.get("candidate_type") == "QUANTUM_FORMULATION",
                "quantum_shape_payload_present_flag": bool(
                    formulation.get("objective") and formulation.get("variables") and formulation.get("domains")
                )
                if packet.get("candidate_type") == "QUANTUM_FORMULATION"
                else None,
                "classical_comparator_refs": list(packet.get("classical_comparator_refs", [])),
                "upstream_route_refs": upstream,
                "downstream_route_refs": downstream,
                "metadata_only_ready_flag": False,
                "solver_compatible_label_only_flag": False,
                "quantum_compatible_label_only_flag": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _route_for(packet: dict[str, Any], formulation: dict[str, Any]) -> tuple[str, str, str | None]:
    candidate_type = packet.get("candidate_type")
    if candidate_type in {"FORMULA", "FEATURE"}:
        if packet.get("callable_ref"):
            return "FORMULA_EXECUTABLE", "Formula/feature callable ref present in PR162D-R2A formulation registry.", None
        return "DATA_BINDING_FILL_REQUIRED_WITH_EXACT_ACTION", "Formula callable missing; exact fill action required.", "PR162R_FILL_CALLABLE_REF_REQUIRED"
    if candidate_type == "ALGORITHM":
        if packet.get("callable_ref"):
            return "ALGORITHM_CALLABLE", "Algorithm callable ref present in PR162D-R2A formulation registry.", None
        return "DATA_BINDING_FILL_REQUIRED_WITH_EXACT_ACTION", "Algorithm callable missing; exact fill action required.", "PR162R_FILL_ALGORITHM_CALLABLE_REF_REQUIRED"
    if candidate_type == "PARAMETER_PACK":
        if packet.get("callable_ref"):
            return "PARAMETER_VALUE_COMPUTABLE_FROM_INPUTS", "Parameter pack callable returns deterministic defaults/ranges from input packet.", None
        return "DATA_BINDING_FILL_REQUIRED_WITH_EXACT_ACTION", "Parameter pack callable missing; exact fill action required.", "PR162R_FILL_PARAMETER_PACK_CALLABLE_REF_REQUIRED"
    if candidate_type == "QUANTUM_FORMULATION":
        if packet.get("callable_ref") and formulation.get("objective") and formulation.get("variables") and formulation.get("domains"):
            return "QUANTUM_SHAPE_BUILDABLE", "Quantum shape builder and objective/variables/domains present; no backend execution.", None
        return "DATA_BINDING_FILL_REQUIRED_WITH_EXACT_ACTION", "Quantum shape missing objective/variables/domains or callable; exact fill action required.", "PR162R_FILL_QUANTUM_SHAPE_REQUIRED"
    if packet.get("classical_comparator_refs"):
        return "CLASSICAL_COMPARATOR_EXECUTABLE", "Classical comparator refs present.", None
    return "OWNER_REVIEW_REQUIRED_WITH_EXACT_REASON", "Candidate type could not be mapped to a PR162R computability route.", "PR162R_OWNER_REVIEW_UNKNOWN_COMPUTABILITY_ROUTE"


def _first_qku(packet: dict[str, Any]) -> str:
    qku_ids = packet.get("qku_ids") or []
    return str(qku_ids[0]) if qku_ids else ""
