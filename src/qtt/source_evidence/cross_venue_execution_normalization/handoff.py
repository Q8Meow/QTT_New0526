from __future__ import annotations

from typing import Any, Mapping, Sequence

from .taxonomy import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    FUTURE_PR_MAPPING,
)


def build_downstream_handoff(
    *,
    phase_bindings: Sequence[Mapping[str, Any]],
    transition_bindings: Sequence[Mapping[str, Any]],
    placeholder_records: Sequence[Mapping[str, Any]],
    arbitrage_preconditions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "cross_venue_execution_downstream_handoff_id": (
            "PR128_CROSS_VENUE_EXECUTION_DOWNSTREAM_HANDOFF_FIXTURE_V1"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "source_repo_pr_label": "PR128",
        "venue_ids_in_scope": list(ACTIVE_STAGE1_VENUES),
        "normalized_phase_binding_ids": [
            str(record["cross_venue_phase_binding_id"]) for record in phase_bindings
        ],
        "normalized_transition_binding_ids": [
            str(record["cross_venue_transition_binding_id"])
            for record in transition_bindings
        ],
        "placeholder_normalization_record_ids": [
            str(record["placeholder_normalization_id"]) for record in placeholder_records
        ],
        "arbitrage_comparability_precondition_ids": [
            str(record["arbitrage_comparability_precondition_id"])
            for record in arbitrage_preconditions
        ],
        "future_runtime_cash_component_field_map_pr": "PR111",
        "future_private_state_read_receipt_pr": "PR112",
        "future_credential_alias_secret_no_capture_pr": "PR113",
        "future_market_data_ingest_pr": "PR114",
        "future_orderbook_event_snapshot_pr": "PR115",
        "future_runtime_resolver_snapshot_pr": "PR116",
        "production_downstream_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "future_production_launch_path_preserved": True,
        **FUTURE_PR_MAPPING,
    }
