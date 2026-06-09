"""Central PR165-B condition-scope vocabulary."""

from __future__ import annotations


CONDITION_FINGERPRINT_FIELDS = (
    "venue",
    "market_type",
    "event_type",
    "market_id_or_candidate_market_ref",
    "side",
    "order_type_candidate",
    "entry_price_bucket",
    "spread_bucket",
    "liquidity_bucket",
    "depth_bucket",
    "latency_bucket",
    "time_to_resolution_bucket",
    "market_maturity_bucket",
    "volatility_bucket",
    "fee_bucket",
    "slippage_bucket",
    "yes_no_complement_consistency_bucket",
    "source_provenance_tier",
    "model_risk_tier",
    "repair_confidence_tier",
    "rank_confidence_tier",
    "quantum_formulation_class",
    "hot_path_lane",
    "portfolio_cluster",
    "duplicate_edge_cluster",
    "event_concentration_group",
    "formula_family",
    "algorithm_family",
    "parameter_stack_family",
)

SIMILARITY_DISTANCE_METRIC = "DETERMINISTIC_BUCKET_OVERLAP_DISTANCE"
SIMILARITY_ACTION_DOWNGRADES = (
    "WATCH_ONLY_UNTIL_MORE_EVIDENCE",
    "REPLAY_PAPER_RETEST_REQUIRED",
    "DEMOTE_WITHIN_MATCHING_CONDITION",
    "DASHBOARD_REVIEW_REQUIRED",
)
