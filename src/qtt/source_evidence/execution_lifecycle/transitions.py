from __future__ import annotations

from typing import Any

from .phases import GENERIC_FIXTURE_PHASE_FAMILIES


GENERIC_FIXTURE_TRANSITION_FAMILIES: tuple[tuple[str, str, str], ...] = (
    (
        "INTENT_TO_PREPARED",
        "ORDER_INTENT_DECLARED_FIXTURE",
        "ORDER_SUBMISSION_PREPARED_FIXTURE",
    ),
    (
        "PREPARED_TO_ACK_PENDING",
        "ORDER_SUBMISSION_PREPARED_FIXTURE",
        "VENUE_ACKNOWLEDGEMENT_PENDING_FIXTURE",
    ),
    (
        "ACK_PENDING_TO_STATE_UPDATE_PENDING",
        "VENUE_ACKNOWLEDGEMENT_PENDING_FIXTURE",
        "VENUE_STATE_UPDATE_PENDING_FIXTURE",
    ),
    (
        "STATE_UPDATE_TO_FILL_INTEGRITY_PENDING",
        "VENUE_STATE_UPDATE_PENDING_FIXTURE",
        "FILL_INTEGRITY_EVALUATION_PENDING_FIXTURE",
    ),
    (
        "FILL_INTEGRITY_TO_CASHFLOW_PNL_PENDING",
        "FILL_INTEGRITY_EVALUATION_PENDING_FIXTURE",
        "CASHFLOW_PNL_MAPPING_PENDING_FIXTURE",
    ),
    (
        "CASHFLOW_PNL_TO_SETTLEMENT_FINALITY_PENDING",
        "CASHFLOW_PNL_MAPPING_PENDING_FIXTURE",
        "SETTLEMENT_FINALITY_PENDING_FIXTURE",
    ),
    (
        "SETTLEMENT_FINALITY_TO_RECONCILIATION_PENDING",
        "SETTLEMENT_FINALITY_PENDING_FIXTURE",
        "RECONCILIATION_PENDING_FIXTURE",
    ),
    (
        "RECONCILIATION_TO_TERMINAL_PENDING",
        "RECONCILIATION_PENDING_FIXTURE",
        "LIFECYCLE_TERMINAL_STATE_PENDING_FIXTURE",
    ),
)


def build_transition_records(
    *,
    model_id: str,
    venue_id: str,
    deterministic_fixture_time: str,
    fixture_authority_class: str,
) -> list[dict[str, Any]]:
    phase_set = set(GENERIC_FIXTURE_PHASE_FAMILIES)
    records: list[dict[str, Any]] = []
    for ordinal, (transition_family, from_phase, to_phase) in enumerate(
        GENERIC_FIXTURE_TRANSITION_FAMILIES,
        start=1,
    ):
        if from_phase not in phase_set or to_phase not in phase_set:
            raise ValueError(f"unknown fixture transition phases: {transition_family}")
        records.append(
            {
                "execution_lifecycle_transition_record_id": (
                    f"{model_id}__TRANSITION_{ordinal:02d}_{transition_family}"
                ),
                "per_venue_execution_lifecycle_model_id": model_id,
                "venue_id": venue_id,
                "transition_ordinal": ordinal,
                "transition_family": transition_family,
                "from_phase_family": from_phase,
                "to_phase_family": to_phase,
                "execution_transition_state": (
                    "PR127_GENERIC_FIXTURE_TRANSITION_PENDING"
                ),
                "transition_authority_note": (
                    "QTT generic fixture modeling transition, not a venue fact"
                ),
                "fixture_authority_class": fixture_authority_class,
                "production_execution_lifecycle_authority": False,
                "deterministic_fixture_time": deterministic_fixture_time,
            }
        )
    return records
