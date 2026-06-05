"""Canonical binding-family classification for PR162R missing actions."""

from __future__ import annotations

from typing import Any


BINDING_FAMILIES = (
    "HISTORICAL_PRICE_SERIES",
    "HISTORICAL_TRADE_SERIES",
    "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES",
    "EVENT_STATE_TIMELINE",
    "SETTLEMENT_OUTCOME_LABELS",
    "VOLUME_DEPTH_LIQUIDITY_SERIES",
    "FEE_MODEL",
    "SLIPPAGE_MODEL",
    "LATENCY_OBSERVATION_SERIES",
    "PROBABILITY_MODEL_INPUTS",
    "COVARIANCE_CORRELATION_INPUTS",
    "QUANTUM_OBJECTIVE_INPUTS",
    "QUANTUM_VARIABLE_DOMAIN_INPUTS",
    "QUANTUM_CONSTRAINT_INPUTS",
    "CLASSICAL_COMPARATOR_INPUTS",
    "PAPER_MARKET_STATE_BINDING",
    "PAPER_SYNTHETIC_FILL_MODEL",
    "PAPER_PORTFOLIO_STATE",
    "PAPER_EXECUTION_COST_MODEL",
    "MARKET_METADATA_AND_LIFECYCLE",
    "MARKET_CATEGORY_CALIBRATION",
    "CROSS_VENUE_DISAGREEMENT_INPUTS",
    "STALENESS_AND_FRESHNESS_INPUTS",
)

VENUE_SCOPES = (
    "KALSHI_PREDICTION_MARKETS",
    "POLYMARKET_CLOB",
    "FORECASTEX_IBKR_EVENT_MARKETS",
    "VENUE_NEUTRAL_SYNTHETIC_FIXTURE",
)

MARKET_FAMILY = "BINARY_EVENT_MARKET"

TARGET_FIELD_BY_FAMILY = {
    "HISTORICAL_PRICE_SERIES": "timestamped_yes_no_price",
    "HISTORICAL_TRADE_SERIES": "timestamped_trade_print",
    "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES": "best_bid_best_ask_depth",
    "EVENT_STATE_TIMELINE": "event_lifecycle_state",
    "SETTLEMENT_OUTCOME_LABELS": "settlement_outcome_label",
    "VOLUME_DEPTH_LIQUIDITY_SERIES": "volume_depth_liquidity",
    "FEE_MODEL": "fee_per_share_or_contract",
    "SLIPPAGE_MODEL": "expected_slippage_per_share",
    "LATENCY_OBSERVATION_SERIES": "latency_observation_seconds",
    "PROBABILITY_MODEL_INPUTS": "probability_vector_or_model_input",
    "COVARIANCE_CORRELATION_INPUTS": "covariance_correlation_matrix",
    "QUANTUM_OBJECTIVE_INPUTS": "quantum_expected_value_cost_risk_vector",
    "QUANTUM_VARIABLE_DOMAIN_INPUTS": "quantum_variable_domain_map",
    "QUANTUM_CONSTRAINT_INPUTS": "quantum_constraint_terms",
    "CLASSICAL_COMPARATOR_INPUTS": "classical_comparator_input_vector",
    "PAPER_MARKET_STATE_BINDING": "paper_market_state",
    "PAPER_SYNTHETIC_FILL_MODEL": "paper_synthetic_fill_model",
    "PAPER_PORTFOLIO_STATE": "paper_portfolio_cash_positions",
    "PAPER_EXECUTION_COST_MODEL": "paper_fee_slippage_latency_cost",
    "MARKET_METADATA_AND_LIFECYCLE": "market_metadata_lifecycle",
    "MARKET_CATEGORY_CALIBRATION": "market_category_calibration",
    "CROSS_VENUE_DISAGREEMENT_INPUTS": "cross_venue_probability_disagreement",
    "STALENESS_AND_FRESHNESS_INPUTS": "source_observation_staleness",
}

GRANULARITY_BY_FAMILY = {
    "HISTORICAL_PRICE_SERIES": "1s",
    "HISTORICAL_TRADE_SERIES": "per_trade",
    "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES": "1s",
    "EVENT_STATE_TIMELINE": "event_state_change",
    "SETTLEMENT_OUTCOME_LABELS": "per_market_resolution",
    "VOLUME_DEPTH_LIQUIDITY_SERIES": "1s",
    "LATENCY_OBSERVATION_SERIES": "per_observation",
    "PAPER_MARKET_STATE_BINDING": "snapshot",
    "PAPER_SYNTHETIC_FILL_MODEL": "per_simulated_order",
    "PAPER_PORTFOLIO_STATE": "snapshot",
    "PAPER_EXECUTION_COST_MODEL": "per_simulated_order",
}

UNIT_BY_FAMILY = {
    "HISTORICAL_PRICE_SERIES": "probability_dollars",
    "HISTORICAL_TRADE_SERIES": "contracts",
    "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES": "probability_dollars_and_contracts",
    "EVENT_STATE_TIMELINE": "enum",
    "SETTLEMENT_OUTCOME_LABELS": "enum",
    "VOLUME_DEPTH_LIQUIDITY_SERIES": "contracts",
    "FEE_MODEL": "dollars_per_share",
    "SLIPPAGE_MODEL": "dollars_per_share",
    "LATENCY_OBSERVATION_SERIES": "seconds",
    "PROBABILITY_MODEL_INPUTS": "probability",
    "COVARIANCE_CORRELATION_INPUTS": "dimensionless_matrix",
    "QUANTUM_OBJECTIVE_INPUTS": "dimensionless_vector",
    "QUANTUM_VARIABLE_DOMAIN_INPUTS": "enum",
    "QUANTUM_CONSTRAINT_INPUTS": "dimensionless_terms",
    "CLASSICAL_COMPARATOR_INPUTS": "dimensionless_vector",
    "PAPER_MARKET_STATE_BINDING": "probability_dollars_and_contracts",
    "PAPER_SYNTHETIC_FILL_MODEL": "dollars_per_share",
    "PAPER_PORTFOLIO_STATE": "dollars_and_contracts",
    "PAPER_EXECUTION_COST_MODEL": "dollars_per_share",
    "MARKET_METADATA_AND_LIFECYCLE": "enum",
    "MARKET_CATEGORY_CALIBRATION": "dimensionless",
    "CROSS_VENUE_DISAGREEMENT_INPUTS": "probability_delta",
    "STALENESS_AND_FRESHNESS_INPUTS": "seconds",
}


def sequence_number(identifier: str) -> int:
    digits = "".join(ch for ch in str(identifier) if ch.isdigit())
    return int(digits[-6:] or "0")


def venue_scope_for_packet(packet: dict[str, Any]) -> str:
    index = sequence_number(str(packet.get("candidate_packet_id"))) - 1
    return VENUE_SCOPES[index % len(VENUE_SCOPES)]


def replay_or_paper_lane(family: str) -> str:
    if family.startswith("PAPER_"):
        return "PAPER"
    if family.startswith("QUANTUM_") or family in {
        "CLASSICAL_COMPARATOR_INPUTS",
        "FEE_MODEL",
        "SLIPPAGE_MODEL",
        "LATENCY_OBSERVATION_SERIES",
        "STALENESS_AND_FRESHNESS_INPUTS",
    }:
        return "BOTH"
    return "REPLAY"


def quantum_or_classical_role(family: str) -> str:
    if family.startswith("QUANTUM_"):
        return "QUANTUM_BATCH"
    if family == "CLASSICAL_COMPARATOR_INPUTS":
        return "CLASSICAL_COMPARATOR"
    return "CLASSICAL_FEATURE"


def target_field(family: str) -> str:
    return TARGET_FIELD_BY_FAMILY[family]


def data_granularity(family: str) -> str:
    return GRANULARITY_BY_FAMILY.get(family, "per_candidate")


def unit_for_family(family: str) -> str:
    return UNIT_BY_FAMILY.get(family, "dimensionless")


def classify_missing_action(action: dict[str, Any], packet: dict[str, Any]) -> str:
    fill_family = str(action.get("fill_action_family", ""))
    domain = str(packet.get("domain_family_key", ""))
    seq = sequence_number(str(action.get("action_id")))

    if fill_family == "MISSING_PAPER_MARKET_STATE_BINDING":
        if domain == "market_microstructure_liquidity":
            return "PAPER_SYNTHETIC_FILL_MODEL"
        if domain in {"risk_capital_sizing", "quantum_bundle_selection_optimizer"}:
            return "PAPER_PORTFOLIO_STATE"
        if domain in {"latency_slippage_cost", "parameter_default_range_pack"}:
            return "PAPER_EXECUTION_COST_MODEL"
        return "PAPER_MARKET_STATE_BINDING"

    if fill_family == "MISSING_LATENCY_MEASUREMENT":
        if domain == "deterministic_candidate_ranking_algorithm":
            return "MARKET_CATEGORY_CALIBRATION" if seq % 2 == 0 else "CLASSICAL_COMPARATOR_INPUTS"
        if domain == "quantum_bundle_selection_optimizer":
            return "QUANTUM_CONSTRAINT_INPUTS" if seq % 2 == 0 else "QUANTUM_VARIABLE_DOMAIN_INPUTS"
        if domain in {"risk_capital_sizing", "latency_slippage_cost"}:
            return "LATENCY_OBSERVATION_SERIES"
        if domain == "market_microstructure_liquidity":
            return "CROSS_VENUE_DISAGREEMENT_INPUTS"
        if domain == "parameter_default_range_pack":
            return "EVENT_STATE_TIMELINE"
        return "STALENESS_AND_FRESHNESS_INPUTS"

    if fill_family == "MISSING_HISTORICAL_PRICE_SERIES":
        if domain == "deterministic_candidate_ranking_algorithm":
            return "HISTORICAL_TRADE_SERIES" if seq % 2 == 0 else "CLASSICAL_COMPARATOR_INPUTS"
        if domain == "technical_indicator_price_feature":
            return "HISTORICAL_PRICE_SERIES"
        if domain == "risk_capital_sizing":
            return "COVARIANCE_CORRELATION_INPUTS"
        if domain in {"expected_value_probability_edge", "probability_calibration_edge"}:
            return "PROBABILITY_MODEL_INPUTS"
        if domain == "market_microstructure_liquidity":
            return "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES"
        if domain == "quantum_bundle_selection_optimizer":
            return "QUANTUM_OBJECTIVE_INPUTS"
        if domain == "latency_slippage_cost":
            return "FEE_MODEL" if seq % 2 == 0 else "SLIPPAGE_MODEL"
        if domain == "parameter_default_range_pack":
            return "MARKET_METADATA_AND_LIFECYCLE"
        return "HISTORICAL_PRICE_SERIES"

    if fill_family == "MISSING_QUANTUM_OBJECTIVE_PARAMETER":
        return (
            "QUANTUM_OBJECTIVE_INPUTS"
            if seq % 3 == 0
            else "QUANTUM_VARIABLE_DOMAIN_INPUTS"
            if seq % 3 == 1
            else "QUANTUM_CONSTRAINT_INPUTS"
        )

    direct = {
        "MISSING_ORDERBOOK_SNAPSHOT_SERIES": "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES",
        "MISSING_VOLUME_OR_DEPTH_SERIES": "VOLUME_DEPTH_LIQUIDITY_SERIES",
        "MISSING_OUTCOME_LABEL": "SETTLEMENT_OUTCOME_LABELS",
        "MISSING_PROBABILITY_MODEL_INPUT": "PROBABILITY_MODEL_INPUTS",
        "MISSING_SLIPPAGE_MODEL_INPUT": "SLIPPAGE_MODEL",
        "MISSING_COVARIANCE_INPUT": "COVARIANCE_CORRELATION_INPUTS",
        "MISSING_FEE_MODEL_INPUT": "FEE_MODEL",
        "MISSING_CLASSICAL_COMPARATOR_INPUT": "CLASSICAL_COMPARATOR_INPUTS",
    }
    return direct.get(fill_family, "MARKET_METADATA_AND_LIFECYCLE")
