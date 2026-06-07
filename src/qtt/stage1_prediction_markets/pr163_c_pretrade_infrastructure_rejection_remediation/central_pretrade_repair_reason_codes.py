"""Central PR163-C reason codes and allowed dispositions."""

from __future__ import annotations

ALLOWED_DISPOSITIONS = frozenset(
    {
        "REPAIRED_REPLAY_PAPER_READY",
        "REPAIRED_REPLAY_READY_PAPER_PENDING",
        "REPAIRED_PAPER_READY_REPLAY_PENDING",
        "REPAIRED_PRETRADE_READY_NEEDS_REPLAY_RERUN",
        "REPAIRED_PRETRADE_READY_NEEDS_PAPER_RERUN",
        "REPAIRED_SYNTHETIC_FILL_READY_NEEDS_REPLAY_PAPER_RERUN",
        "REPAIRED_TCA_READY_NEEDS_PR165_SCORING",
        "RECLASSIFIED_VALID_REJECTION_NOT_REPAIRABLE",
        "ROUTED_TO_PR162D_R3_MISSING_VALUE_FILL_NOT_PR163C",
        "ROUTED_TO_PR165_SCORING_AFTER_REPAIR",
        "ROUTED_TO_PR165B_NEGATIVE_MEMORY_AFTER_REPAIR",
        "ROUTED_TO_PR162E_PLUGIN_INTAKE_AFTER_EVIDENCE_RANKING",
        "ROUTED_TO_LATER_RUNTIME_OR_LIVE_PR_NOT_REPAIRABLE_HERE",
        "BLOCKED_BY_EXACT_NON_REPAIRABLE_REASON",
    }
)

PROHIBITED_DISPOSITIONS = frozenset(
    {
        "UNKNOWN",
        "GENERIC_BLOCKED",
        "METADATA_ONLY",
        "PLACEHOLDER_ONLY",
        "FUTURE_CONSUMER_ONLY",
        "REPAIR_TODO_WITHOUT_AGENT",
        "REPAIR_TODO_WITHOUT_DOWNSTREAM_PR",
        "REPAIR_TODO_WITHOUT_EXACT_FIELD",
        "FORMULA_TEXT_WITHOUT_EXECUTABLE_FUNCTION",
        "TEST_VECTOR_MISSING",
        "SOURCE_CANDIDATE_WITHOUT_POINT_IN_TIME_TAG",
        "REPLAY_PAPER_ELIGIBLE_WITHOUT_CONSUMER_ROUTE",
    }
)

FAMILY_TO_REPAIR = {
    "MARKET_STATE_REPAIR": {
        "repair_family": "MARKET_STATE_FRESHNESS_REPAIR",
        "repair_action_id": "PR163C_ACTION::MARKET_STATE_FRESHNESS",
        "formula_ref": "PR163C_FORMULA::LATENCY_STALE_DATA_COST",
        "test_vector_ref": "PR163C_TEST_VECTOR::LATENCY_STALE_DATA_COST",
        "causal_defect_code": "STALE_QUOTE_FIXTURE_FRESHNESS_DEFECT",
        "exact_defect_fields": [
            "market_open_candidate",
            "event_active_candidate",
            "signal_timestamp",
            "pretrade_timestamp",
            "stale_data_penalty",
        ],
        "final_disposition": "REPAIRED_PRETRADE_READY_NEEDS_REPLAY_RERUN",
    },
    "TICK_SIZE_REPAIR": {
        "repair_family": "TICK_SIZE_QUANTIZATION_REPAIR",
        "repair_action_id": "PR163C_ACTION::TICK_SIZE_QUANTIZATION",
        "formula_ref": "PR163C_FORMULA::TICK_SIZE_QUANTIZE",
        "test_vector_ref": "PR163C_TEST_VECTOR::TICK_SIZE_QUANTIZE",
        "causal_defect_code": "TICK_SIZE_PRICE_GRID_DEFECT",
        "exact_defect_fields": [
            "tick_size_candidate",
            "price_scale",
            "limit_price_candidate",
            "simulated_execution_price",
        ],
        "final_disposition": "REPAIRED_PRETRADE_READY_NEEDS_REPLAY_RERUN",
    },
    "VENUE_NORMALIZATION_REPAIR": {
        "repair_family": "VENUE_PRICE_DOMAIN_NORMALIZATION_REPAIR",
        "repair_action_id": "PR163C_ACTION::VENUE_NORMALIZATION",
        "formula_ref": "PR163C_FORMULA::VENUE_PRICE_NORMALIZE",
        "test_vector_ref": "PR163C_TEST_VECTOR::VENUE_PRICE_NORMALIZE",
        "causal_defect_code": "VENUE_PRICE_DOMAIN_NORMALIZATION_DEFECT",
        "exact_defect_fields": [
            "canonical_venue_id",
            "canonical_market_id",
            "price_scale",
            "quantity_scale",
            "payout_unit_candidate",
        ],
        "final_disposition": "REPAIRED_PRETRADE_READY_NEEDS_REPLAY_RERUN",
    },
    "REPLAY_ADAPTER_REPAIR": {
        "repair_family": "REPLAY_PAPER_ADAPTER_ALIGNMENT_REPAIR",
        "repair_action_id": "PR163C_ACTION::REPLAY_ADAPTER_ALIGNMENT",
        "formula_ref": "PR163C_FORMULA::FILL_PROBABILITY",
        "test_vector_ref": "PR163C_TEST_VECTOR::FILL_PROBABILITY",
        "causal_defect_code": "REPLAY_ONLY_ADAPTER_TRACE_ALIGNMENT_DEFECT",
        "exact_defect_fields": [
            "replay_order_type",
            "paper_order_type",
            "order_lifecycle_trace",
            "fill_integrity_receipt_ref",
        ],
        "final_disposition": "REPAIRED_REPLAY_PAPER_READY",
    },
}


def family_policy(remediation_family: str) -> dict[str, object]:
    return FAMILY_TO_REPAIR.get(
        remediation_family,
        {
            "repair_family": "VALID_OR_NON_PR163C_REJECTION",
            "repair_action_id": "",
            "formula_ref": "",
            "test_vector_ref": "",
            "causal_defect_code": "NON_PR163C_DEFECT",
            "exact_defect_fields": [],
            "final_disposition": "RECLASSIFIED_VALID_REJECTION_NOT_REPAIRABLE",
        },
    )
