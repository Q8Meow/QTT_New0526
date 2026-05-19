from __future__ import annotations

from typing import Any


GENERIC_FIXTURE_PHASE_FAMILIES: tuple[str, ...] = (
    "ORDER_INTENT_DECLARED_FIXTURE",
    "CONNECTOR_SEMANTIC_IMPLEMENTATION_CONFIRMED_FIXTURE",
    "ORDER_SUBMISSION_PREPARED_FIXTURE",
    "VENUE_ACKNOWLEDGEMENT_PENDING_FIXTURE",
    "VENUE_STATE_UPDATE_PENDING_FIXTURE",
    "FILL_INTEGRITY_EVALUATION_PENDING_FIXTURE",
    "CASHFLOW_PNL_MAPPING_PENDING_FIXTURE",
    "SETTLEMENT_FINALITY_PENDING_FIXTURE",
    "RECONCILIATION_PENDING_FIXTURE",
    "LIFECYCLE_TERMINAL_STATE_PENDING_FIXTURE",
)


def build_phase_records(
    *,
    model_id: str,
    venue_id: str,
    deterministic_fixture_time: str,
    fixture_authority_class: str,
) -> list[dict[str, Any]]:
    return [
        {
            "execution_lifecycle_phase_record_id": (
                f"{model_id}__PHASE_{ordinal:02d}_{phase_family}"
            ),
            "per_venue_execution_lifecycle_model_id": model_id,
            "venue_id": venue_id,
            "phase_ordinal": ordinal,
            "phase_family": phase_family,
            "execution_phase_state": "PR127_GENERIC_FIXTURE_PHASE_PENDING",
            "phase_authority_note": "QTT generic fixture modeling phase, not a venue fact",
            "fixture_authority_class": fixture_authority_class,
            "production_execution_lifecycle_authority": False,
            "deterministic_fixture_time": deterministic_fixture_time,
        }
        for ordinal, phase_family in enumerate(GENERIC_FIXTURE_PHASE_FAMILIES, start=1)
    ]
