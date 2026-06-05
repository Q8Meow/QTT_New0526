"""Replay binding spine builders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dataset_contracts import common_binding_record
from .dataset_normalization_pipeline import receipt_for_task
from .source_acquisition_pipeline import source_candidate_for_task


REPLAY_SPINE_FAMILIES = (
    "SETTLEMENT_OUTCOME_LABELS",
    "MARKET_METADATA_AND_LIFECYCLE",
    "EVENT_STATE_TIMELINE",
    "HISTORICAL_PRICE_SERIES",
    "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES",
    "HISTORICAL_TRADE_SERIES",
    "VOLUME_DEPTH_LIQUIDITY_SERIES",
    "FEE_MODEL",
    "SLIPPAGE_MODEL",
    "LATENCY_OBSERVATION_SERIES",
    "PROBABILITY_MODEL_INPUTS",
    "COVARIANCE_CORRELATION_INPUTS",
    "CROSS_VENUE_DISAGREEMENT_INPUTS",
    "MARKET_CATEGORY_CALIBRATION",
    "STALENESS_AND_FRESHNESS_INPUTS",
)


def build_dataset_bindings(
    repo_root: Path,
    tasks: list[dict[str, Any]],
    source_candidates: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, task in enumerate(tasks, start=1):
        source = source_candidate_for_task(task, source_candidates)
        receipt = receipt_for_task(task, receipts)
        rows.append(
            common_binding_record(
                index=index,
                task=task,
                source_candidate_id=source["source_candidate_id"],
                normalization_receipt_id=receipt["normalization_receipt_id"],
                repo_root=repo_root,
            )
        )
    return rows


def build_replay_specific_bindings(dataset_bindings: list[dict[str, Any]], family: str, prefix: str) -> list[dict[str, Any]]:
    rows = []
    for binding in dataset_bindings:
        if binding["binding_family"] != family:
            continue
        rows.append(
            {
                **binding,
                "binding_id": f"{prefix}::{len(rows) + 1:04d}",
                "dataset_binding_ref": binding["binding_id"],
                "replay_binding_status": (
                    "REPLAY_SYNTHETIC_FIXTURE_BOUND"
                    if binding["source_class"] == "SYNTHETIC_TEST_FIXTURE"
                    else "REPLAY_REPO_LOCAL_FIXTURE_BOUND"
                ),
                "replay_result_packet_created": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_replay_historical_price_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_replay_specific_bindings(
        dataset_bindings,
        "HISTORICAL_PRICE_SERIES",
        "PR162R_B_REPLAY_PRICE_BINDING",
    )


def build_replay_orderbook_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_replay_specific_bindings(
        dataset_bindings,
        "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES",
        "PR162R_B_REPLAY_ORDERBOOK_BINDING",
    )


def build_replay_trade_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_replay_specific_bindings(
        dataset_bindings,
        "HISTORICAL_TRADE_SERIES",
        "PR162R_B_REPLAY_TRADE_BINDING",
    )


def build_replay_event_state_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_replay_specific_bindings(
        dataset_bindings,
        "EVENT_STATE_TIMELINE",
        "PR162R_B_REPLAY_EVENT_STATE_BINDING",
    )


def build_replay_settlement_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_replay_specific_bindings(
        dataset_bindings,
        "SETTLEMENT_OUTCOME_LABELS",
        "PR162R_B_REPLAY_SETTLEMENT_BINDING",
    )


def replay_binding_lookup(dataset_bindings: list[dict[str, Any]]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for binding in dataset_bindings:
        if not binding.get("replay_allowed"):
            continue
        for packet_id in binding.get("consumer_candidate_packet_ids", []):
            lookup.setdefault(packet_id, []).append(binding["binding_id"])
    return {key: sorted(value) for key, value in lookup.items()}
