"""Shared dataset binding contract builders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .authority_policy import BOUNDARY_COUNT_FIELDS
from .binding_family_classifier import target_field, unit_for_family


def quality_tier_for(source_class: str, lane: str) -> str:
    if source_class == "SYNTHETIC_TEST_FIXTURE":
        return "DQ0_SYNTHETIC_TEST_ONLY"
    if source_class == "REPO_LOCAL_ARTIFACT_CANDIDATE":
        return "DQ2_REPO_LOCAL_HISTORICAL"
    if source_class == "RESEARCH_SOURCE_CANDIDATE":
        return "DQ1_RESEARCH_CANDIDATE"
    if lane == "PAPER":
        return "DQ5_PAPER_READY_VALIDATED"
    return "DQ4_REPLAY_READY_VALIDATED"


def source_class_for_task(task: dict[str, Any]) -> str:
    if task["venue_scope"] == "VENUE_NEUTRAL_SYNTHETIC_FIXTURE":
        return "SYNTHETIC_TEST_FIXTURE"
    if task["binding_family"].startswith("PAPER_"):
        return "SYNTHETIC_TEST_FIXTURE"
    if task["binding_family"].startswith("QUANTUM_"):
        return "SYNTHETIC_TEST_FIXTURE"
    return "REPO_LOCAL_ARTIFACT_CANDIDATE"


def fixture_path_for_family(family: str) -> str:
    mapping = {
        "HISTORICAL_PRICE_SERIES": "synthetic_binary_market_orderbook_1s.fixture.jsonl",
        "HISTORICAL_TRADE_SERIES": "synthetic_binary_market_trade_prints.fixture.jsonl",
        "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES": "synthetic_binary_market_orderbook_1s.fixture.jsonl",
        "EVENT_STATE_TIMELINE": "synthetic_event_state_timeline.fixture.jsonl",
        "SETTLEMENT_OUTCOME_LABELS": "synthetic_settlement_labels.fixture.jsonl",
        "VOLUME_DEPTH_LIQUIDITY_SERIES": "synthetic_binary_market_orderbook_1s.fixture.jsonl",
        "FEE_MODEL": "synthetic_fee_slippage_model.fixture.json",
        "SLIPPAGE_MODEL": "synthetic_fee_slippage_model.fixture.json",
        "LATENCY_OBSERVATION_SERIES": "synthetic_latency_observations.fixture.jsonl",
        "PROBABILITY_MODEL_INPUTS": "synthetic_quantum_objective_inputs.fixture.json",
        "COVARIANCE_CORRELATION_INPUTS": "synthetic_quantum_objective_inputs.fixture.json",
        "QUANTUM_OBJECTIVE_INPUTS": "synthetic_quantum_objective_inputs.fixture.json",
        "QUANTUM_VARIABLE_DOMAIN_INPUTS": "synthetic_quantum_constraints.fixture.json",
        "QUANTUM_CONSTRAINT_INPUTS": "synthetic_quantum_constraints.fixture.json",
        "CLASSICAL_COMPARATOR_INPUTS": "synthetic_classical_comparator_inputs.fixture.json",
        "PAPER_MARKET_STATE_BINDING": "synthetic_paper_market_state.fixture.json",
        "PAPER_SYNTHETIC_FILL_MODEL": "synthetic_paper_fill_events.fixture.jsonl",
        "PAPER_PORTFOLIO_STATE": "synthetic_paper_portfolio_state.fixture.json",
        "PAPER_EXECUTION_COST_MODEL": "synthetic_fee_slippage_model.fixture.json",
        "MARKET_METADATA_AND_LIFECYCLE": "synthetic_event_state_timeline.fixture.jsonl",
        "MARKET_CATEGORY_CALIBRATION": "synthetic_classical_comparator_inputs.fixture.json",
        "CROSS_VENUE_DISAGREEMENT_INPUTS": "synthetic_binary_market_orderbook_1s.fixture.jsonl",
        "STALENESS_AND_FRESHNESS_INPUTS": "synthetic_latency_observations.fixture.jsonl",
    }
    return (
        "tests/fixtures/stage1_prediction_markets/"
        "pr162r_b_replay_paper_data_binding_completion/"
        f"{mapping[family]}"
    )


def field_map_for_family(family: str) -> dict[str, str]:
    return {
        "market_id": "market_id",
        "event_id": "event_id",
        "outcome_id": "outcome_id",
        "source_timestamp": "source_timestamp_utc",
        "observation_timestamp": "observation_timestamp_utc",
        target_field(family): target_field(family),
    }


def common_binding_record(
    *,
    index: int,
    task: dict[str, Any],
    source_candidate_id: str,
    normalization_receipt_id: str,
    repo_root: Path,
    status: str | None = None,
) -> dict[str, Any]:
    family = task["binding_family"]
    source_class = source_class_for_task(task)
    lane = task["replay_or_paper_lane"]
    binding_status = status or (
        "SYNTHETIC_FIXTURE_BOUND"
        if source_class == "SYNTHETIC_TEST_FIXTURE"
        else "REPO_LOCAL_FIXTURE_BOUND"
    )
    fixture_path = fixture_path_for_family(family)
    packet_ids = list(task.get("impacted_candidate_packet_ids", []))
    qku_ids = list(task.get("impacted_qku_ids", []))
    return {
        "binding_id": f"PR162R_B_DATASET_BINDING::{index:04d}",
        "binding_task_id": task["binding_task_id"],
        "binding_family": family,
        "binding_status": binding_status,
        "venue_scope": task["venue_scope"],
        "market_scope": "BINARY_EVENT_MARKET_SYNTHETIC_REPRESENTATIVE",
        "market_family": task["market_family"],
        "event_or_contract_scope": task["event_or_contract_scope_class"],
        "time_range": {
            "start_utc": "2026-01-01T00:00:00Z",
            "end_utc": "2026-01-01T00:00:05Z",
            "deterministic_fixture_window": True,
        },
        "data_granularity": task["data_granularity"],
        "source_class": source_class,
        "source_locator": source_locator_for(task["venue_scope"], family),
        "repo_local_path": fixture_path,
        "field_map": field_map_for_family(family),
        "unit_map": {target_field(family): unit_for_family(family)},
        "timestamp_policy": "UTC_ISO8601_EVENT_AND_OBSERVATION_TIME_REQUIRED",
        "normalization_policy": "PR162R_B_DATASET_NORMALIZATION_PIPELINE_V1",
        "missingness_policy": "DROP_INVALID_FIXTURE_ROW_OR_DEFER_FAMILY_WITH_EXACT_REASON",
        "freshness_policy": "REPLAY_FIXED_WINDOW_PAPER_SYNTHETIC_SNAPSHOT_NO_RUNTIME_RETRIEVAL",
        "replay_allowed": lane in {"REPLAY", "BOTH"},
        "paper_allowed": lane in {"PAPER", "BOTH"},
        "live_allowed": False,
        "candidate_truth_status": (
            "SYNTHETIC_TEST_FIXTURE"
            if source_class == "SYNTHETIC_TEST_FIXTURE"
            else "REPO_LOCAL_ARTIFACT_CANDIDATE"
        ),
        "data_quality_tier": quality_tier_for(source_class, lane),
        "promotion_requirements": [
            "later source acceptance PR required for external truth promotion",
            "later replay/paper execution evidence required for result status",
            "later owner approval required before any live or order authority",
        ],
        "consumer_qku_ids": qku_ids,
        "consumer_candidate_packet_ids": packet_ids,
        "consumer_agent_ids": list(task.get("impacted_agent_ids", [])),
        "rows_resolved_count": len(packet_ids),
        "upstream_refs": [
            task["binding_task_id"],
            source_candidate_id,
            normalization_receipt_id,
            "PR162R_MissingDataBindingActionQueue.report.json",
            "PR162R_ReplayPaperDataBindingRequirementMatrix.report.json",
            "PR162D_R2A_CandidatePacketV1Registry.report.json",
        ],
        "downstream_refs": list(task.get("downstream_refs", [])),
        "determinism_receipt": {
            "deterministic_fixture": True,
            "runtime_source_retrieval": False,
            "repo_local_path_exists_after_build": (repo_root / fixture_path).exists(),
        },
        "normalization_receipt_refs": [normalization_receipt_id],
        "source_candidate_refs": [source_candidate_id],
        "no_source_acceptance": True,
        "no_connector_binding": True,
        "no_live_order_authority": True,
        "no_profit_evidence": True,
        "live_order_authority": False,
        "validation_status": "PASS",
        **BOUNDARY_COUNT_FIELDS,
    }


def source_locator_for(venue_scope: str, family: str) -> str:
    if venue_scope == "KALSHI_PREDICTION_MARKETS":
        return "https://docs.kalshi.com/welcome"
    if venue_scope == "POLYMARKET_CLOB":
        if family in {"HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES", "CROSS_VENUE_DISAGREEMENT_INPUTS"}:
            return "https://docs.polymarket.com/resources/blockchain-data"
        return "https://docs.polymarket.com/trading/overview"
    if venue_scope == "FORECASTEX_IBKR_EVENT_MARKETS":
        return "https://www.interactivebrokers.com/en/pricing/commissions-events.php"
    return "repo-local synthetic fixture"
