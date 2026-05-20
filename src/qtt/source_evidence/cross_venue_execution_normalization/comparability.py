from __future__ import annotations

from itertools import combinations
from typing import Any, Mapping, Sequence

from .taxonomy import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    NOT_ARBITRAGE_AUTHORITY,
    REQUIRED_FUTURE_PRS,
    REQUIRED_PLACEHOLDER_DIMENSIONS,
    READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
)


REQUIRED_FUTURE_RECEIPTS: tuple[str, ...] = (
    "PR111_RUNTIME_CASH_COMPONENT_FIELD_MAP_RECEIPT",
    "PR112_PRIVATE_STATE_READ_RECEIPT",
    "PR113_CREDENTIAL_ALIAS_SECRET_NO_CAPTURE_RECEIPT",
    "PR114_MARKET_DATA_INGEST_RECEIPT",
    "PR115_ORDERBOOK_EVENT_STATE_SNAPSHOT_RECEIPT",
    "PR116_RUNTIME_RESOLVER_SNAPSHOT_RECEIPT",
)


def build_arbitrage_comparability_preconditions(
    *,
    phase_bindings: Sequence[Mapping[str, Any]],
    transition_bindings: Sequence[Mapping[str, Any]],
    venue_ids: Sequence[str] = ACTIVE_STAGE1_VENUES,
) -> list[dict[str, Any]]:
    phase_ids_by_venue = _ids_by_venue(phase_bindings, "cross_venue_phase_binding_id")
    transition_ids_by_venue = _ids_by_venue(
        transition_bindings,
        "cross_venue_transition_binding_id",
    )
    records: list[dict[str, Any]] = []
    for left, right in combinations(venue_ids, 2):
        compared = [left, right]
        records.append(
            {
                "arbitrage_comparability_precondition_id": (
                    f"PR128_ARBITRAGE_COMPARABILITY_PRECONDITION_{left}_{right}_FIXTURE"
                ),
                "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
                "precondition_authority_class": NOT_ARBITRAGE_AUTHORITY,
                "arbitrage_comparability_precondition_state": (
                    READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION
                ),
                "production_arbitrage_comparability_authority": False,
                "production_cross_venue_normalization_authority": False,
                "venue_ids_compared": compared,
                "normalized_phase_binding_ids": [
                    binding_id
                    for venue_id in compared
                    for binding_id in phase_ids_by_venue[venue_id]
                ],
                "normalized_transition_binding_ids": [
                    binding_id
                    for venue_id in compared
                    for binding_id in transition_ids_by_venue[venue_id]
                ],
                "unresolved_placeholder_dimensions": list(
                    REQUIRED_PLACEHOLDER_DIMENSIONS
                ),
                "required_future_receipts": list(REQUIRED_FUTURE_RECEIPTS),
                "required_future_prs": list(REQUIRED_FUTURE_PRS),
                "apparent_price_gap_arbitrage_claim_allowed": False,
                "production_order_authority_allowed": False,
                "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
                "future_production_launch_path_preserved": True,
            }
        )
    return records


def _ids_by_venue(
    records: Sequence[Mapping[str, Any]],
    id_field: str,
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {venue_id: [] for venue_id in ACTIVE_STAGE1_VENUES}
    for record in records:
        venue_id = str(record["venue_id"])
        grouped.setdefault(venue_id, []).append(str(record[id_field]))
    return {venue_id: sorted(ids) for venue_id, ids in grouped.items()}
