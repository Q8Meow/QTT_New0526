"""Combination fingerprint records for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref


def build_combination_fingerprint_record(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    score = ctx["score"]
    quantum = ctx["quantum"]
    maker = ctx["maker_taker"]
    combination_payload = {
        "qku_refs": [score["qku_id"]],
        "formula_refs": [score["score_formula_ref"], ctx["formula_family"]],
        "algorithm_refs": [ctx["algorithm_family"], "PR165_B_CONDITION_MEMORY_CLASSIFIER_V1"],
        "parameter_stack_refs": [ctx["parameter_stack_family"], score.get("deterministic_score_component_record", "")],
        "feature_family_refs": [
            "TCA",
            "LATENCY",
            "LIQUIDITY",
            "MODEL_RISK",
            "SOURCE_PROVENANCE",
            "PORTFOLIO_CROWDING",
            "QUANTUM_FORMULATION",
        ],
        "score_formula_refs": [score["score_formula_ref"]],
        "test_vector_refs": [score["score_test_vector_ref"]],
        "quantum_formulation_refs": [quantum.get("quantum_formulation_materialization_ref", "")],
        "classical_comparator_refs": [quantum.get("classical_comparator_ref", "PR165_CLASSICAL_COMPARATOR::LOCAL")],
        "maker_taker_route_decision": maker.get("maker_taker_route_decision", "MAKER_ROUTE_PREFERRED_FOR_REPLAY_PAPER"),
        "latency_lane": ctx["latency_lane"].get("hot_path_lane", "REPLAY_PAPER_ONLY"),
        "repair_route_refs": [ctx["repair_route"].get("repair_event_id", score.get("repair_routing_ref", ""))],
        "source_candidate_refs": score.get("source_candidate_refs", []),
        "upstream_pr_refs": score.get("upstream_pr_refs", []),
        "upstream_report_refs": score.get("upstream_report_refs", []),
    }
    return {
        "combination_fingerprint_id": ordinal_ref("PR165_B_COMBINATION_FINGERPRINT", index),
        "candidate_packet_id": score["candidate_packet_id"],
        "qku_id": score["qku_id"],
        "combination_scope": combination_payload,
        **combination_payload,
        "deterministic_materialization_policy": "FIELD_ORDERED_COMBINATION_REFS_NO_HASH_AUTHORITY",
        "validation_status": "PASS",
    }
