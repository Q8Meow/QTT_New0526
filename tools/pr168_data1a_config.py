#!/usr/bin/env python3
"""Central constants for PR168-DATA1A focused DATA1 audit."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"
AUDIT_DIR = GENERATED_ROOT / "pr168_data1a_audit"

TOOL_NAME = "tools/build_pr168_data1a_focused_audit.py"
REPORT_VERSION = "PR168-DATA1A-v3.0"
BRANCH_NAME = "pr168-data1a-focused-audit-gfp2r-readiness"
DATA1_MERGE_COMMIT = "5fd13f51ee125400f9bd9bffad760b2443c07d7b"

SNAPSHOT_ROOT = GENERATED_ROOT / "pr168_data1_snapshots"
FORWARD_L2_ROOT = GENERATED_ROOT / "pr168_data1_forward_l2"
HISTORICAL_CANDIDATE_ROOT = GENERATED_ROOT / "pr168_data1_historical_replay_candidates"

KALSHI_SNAPSHOT_JSONL = SNAPSHOT_ROOT / "kalshi" / "kalshi_snapshots.jsonl"
POLYMARKET_SNAPSHOT_JSONL = SNAPSHOT_ROOT / "polymarket" / "polymarket_snapshots.jsonl"
KALSHI_FORWARD_L2_JSONL = FORWARD_L2_ROOT / "kalshi" / "kalshi_forward_l2.jsonl"
POLYMARKET_FORWARD_L2_JSONL = FORWARD_L2_ROOT / "polymarket" / "polymarket_forward_l2.jsonl"
HISTORICAL_CANDIDATE_JSONL = (
    HISTORICAL_CANDIDATE_ROOT / "candidate_sources" / "historical_full_book_candidates.jsonl"
)
FORECASTEX_IBKR_MANIFEST = (
    SNAPSHOT_ROOT / "forecastex_ibkr" / "forecastex_ibkr_auth_required.manifest.json"
)

ROW_SHARDS = {
    "fetch_inventory": AUDIT_DIR / "fetch_inventory_rows.jsonl",
    "qku_unblock": AUDIT_DIR / "qku_unblock_rows.jsonl",
    "data_quality": AUDIT_DIR / "data_quality_rows.jsonl",
    "alpha_capture": AUDIT_DIR / "alpha_capture_readiness_rows.jsonl",
    "recovery": AUDIT_DIR / "recovery_readiness_rows.jsonl",
    "historical_full_book": AUDIT_DIR / "historical_full_book_truth_rows.jsonl",
    "gfp2r": AUDIT_DIR / "gfp2r_readiness_rows.jsonl",
    "quantum": AUDIT_DIR / "quantum_usability_rows.jsonl",
    "operator_actions": AUDIT_DIR / "operator_action_rows.jsonl",
}

REQUIRED_DATA1_REPORT_IDS = [
    "PR168_DATA1_FinalSummary",
    "PR168_DATA1_PublicFetchExecutionSummary",
    "PR168_DATA1_SourceEndpointDiscovery",
    "PR168_DATA1_KalshiSnapshotManifest",
    "PR168_DATA1_PolymarketSnapshotManifest",
    "PR168_DATA1_HistoricalFullBookAvailabilityAudit",
    "PR168_DATA1_HistoricalFullBookAcquisitionLedger",
    "PR168_DATA1_HistoricalL2GapRouteToFutureAcquisition",
    "PR168_DATA1_HistoricalPriceTradeCandleReplaySubstituteLedger",
    "PR168_DATA1_ForwardFullBookReplayCaptureBootstrap",
    "PR168_DATA1_ForwardL2CaptureShardManifest",
    "PR168_DATA1_NormalizedMarketDataFeatureRegistry",
    "PR168_DATA1_DataReadinessClassification",
    "PR168_DATA1_DataQualityFreshnessCoverageAudit",
    "PR168_DATA1_MinimumViableRealDataProofDatasetPlan",
    "PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse",
    "PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch",
    "PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch",
    "PR168_DATA1_QuantumForwardCoefficientFeatureSurface",
    "PR168_DATA1_AgentRoutingAndNoOrphanProof",
    "PR168_DATA1_DAGUpstreamDownstreamOrchestration",
    "PR168_DATA1_OperatorActionMatrix",
]

REQUIRED_REPORT_IDS = [
    "PR168_DATA1A_InputDiscovery",
    "PR168_DATA1A_FetchInventoryAudit",
    "PR168_DATA1A_DataProductIntegrityLedger",
    "PR168_DATA1A_CountConfidenceAndLineageLedger",
    "PR168_DATA1A_QKUFormulaDataRequirementBridge",
    "PR168_DATA1A_QKUUnblockDeltaAudit",
    "PR168_DATA1A_QKUComputabilityRouteLedger",
    "PR168_DATA1A_FormulaInputCoverageMatrix",
    "PR168_DATA1A_DataQualityCoverageAudit",
    "PR168_DATA1A_DataQualitySeverityActionQueue",
    "PR168_DATA1A_AlphaCaptureReadinessMatrix",
    "PR168_DATA1A_NegativeToPositiveRecoveryReadinessQueue",
    "PR168_DATA1A_HistoricalFullBookTruthLedger",
    "PR168_DATA1A_EndpointAssumptionDriftAudit",
    "PR168_DATA1A_GFP2RAllowedDataFamilyContract",
    "PR168_DATA1A_GFP2RReadinessDecision",
    "PR168_DATA1A_RP2RANK2BatchReadinessAudit",
    "PR168_DATA1A_QuantumForwardUsabilityAudit",
    "PR168_DATA1A_ReplayPaperLiveReadinessDelta",
    "PR168_DATA1A_AgentRoutingAndNoOrphanProof",
    "PR168_DATA1A_DAGUpstreamDownstreamOrchestration",
    "PR168_DATA1A_EveryValueUpstreamDownstreamCrosswalk",
    "PR168_DATA1A_AgentConsumableDataValueRoutingLedger",
    "PR168_DATA1A_OperatorActionMatrix",
    "PR168_DATA1A_ReportEssentialityAndDeduplicationAudit",
    "PR168_DATA1A_FinalSummary",
]

OPTIONAL_REPORT_IDS = [
    "PR168_DATA1A_MissingAgentCrosswalkBlocker",
    "PR168_DATA1A_MissingDATA1ArtifactsBlocker",
    "PR168_DATA1A_OnlineVerificationNetworkUnavailableReceipt",
]

AUTHORITY_FALSE_FLAGS = {
    "manual_edit_allowed_flag": False,
    "live_authority_created_flag": False,
    "profit_evidence_created_flag": False,
    "source_truth_acceptance_created_flag": False,
    "connector_semantic_binding_created_flag": False,
    "private_state_access_created_flag": False,
    "order_authority_created_flag": False,
    "quantum_backend_execution_flag": False,
    "quantum_advantage_claim_flag": False,
    "qtt_sha_or_atomicrows_hash_authority_flag": False,
}

VALIDATOR_REFS = [
    "tools/pr168_data1a_validator.py",
    "tools/validate_pr168_data1a_focused_audit.py",
]
TEST_REFS = ["tests/pr168_data1a"]
DOWNSTREAM_PRS = [
    "PR168-GFP2R",
    "PR168-RP2",
    "PR168-RANK2",
    "PR165-B",
    "PR167",
    "PR162E-Q",
    "PR166-Q",
    "PR166-QB",
    "PR166-QC",
]

ROUTES = {
    "market_data": {
        "owning_agent": "market_data_acquisition_agent",
        "consumer_agents": [
            "source_evidence_agent",
            "qku_formula_materialization_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
            "risk_tca_capacity_agent",
            "dashboard_operator_agent",
        ],
    },
    "source_evidence": {
        "owning_agent": "source_evidence_agent",
        "consumer_agents": [
            "market_data_acquisition_agent",
            "governance_validation_agent",
            "dashboard_operator_agent",
        ],
    },
    "formula": {
        "owning_agent": "qku_formula_materialization_agent",
        "consumer_agents": [
            "replay_paper_agent",
            "ranking_scoring_agent",
            "risk_tca_capacity_agent",
            "quantum_optimizer_agent",
            "dashboard_operator_agent",
        ],
    },
    "replay": {
        "owning_agent": "replay_paper_agent",
        "consumer_agents": [
            "risk_tca_capacity_agent",
            "ranking_scoring_agent",
            "dashboard_operator_agent",
        ],
    },
    "ranking": {
        "owning_agent": "ranking_scoring_agent",
        "consumer_agents": [
            "risk_tca_capacity_agent",
            "quantum_optimizer_agent",
            "dashboard_operator_agent",
        ],
    },
    "risk": {
        "owning_agent": "risk_tca_capacity_agent",
        "consumer_agents": [
            "replay_paper_agent",
            "ranking_scoring_agent",
            "dashboard_operator_agent",
        ],
    },
    "quantum": {
        "owning_agent": "quantum_optimizer_agent",
        "consumer_agents": [
            "ranking_scoring_agent",
            "governance_validation_agent",
            "dashboard_operator_agent",
        ],
    },
    "governance": {
        "owning_agent": "governance_validation_agent",
        "consumer_agents": [
            "dashboard_operator_agent",
            "source_evidence_agent",
            "market_data_acquisition_agent",
        ],
    },
}

OFFICIAL_DOC_URLS = [
    "https://docs.kalshi.com/getting_started/quick_start_market_data",
    "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
    "https://docs.kalshi.com/api-reference/market/get-trades",
    "https://docs.kalshi.com/getting_started/historical_data",
    "https://docs.kalshi.com/websockets/orderbook-updates",
    "https://docs.polymarket.com/market-data/overview",
    "https://docs.polymarket.com/api-reference/market-data/get-order-book",
    "https://docs.polymarket.com/api-reference/markets/get-prices-history",
    "https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets",
    "https://docs.polymarket.com/api-reference/wss/market",
    "https://www.interactivebrokers.com/campus/ibkr-api-page/event-contracts/",
    "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html",
    "https://docs.dwavequantum.com/en/latest/concepts/models.html",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def report_path(report_id: str) -> Path:
    return GENERATED_ROOT / f"{report_id}.report.json"


def generated_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def manifest_path(jsonl_path: Path) -> Path:
    return jsonl_path.with_suffix(".manifest.json")


def authority_flags() -> dict[str, bool]:
    return dict(AUTHORITY_FALSE_FLAGS)


def route_defaults(
    route_key: str = "governance",
    *,
    data1_refs: list[str] | None = None,
    upstream_refs: list[str] | None = None,
    row_shard_refs: list[str] | None = None,
    provenance_refs: list[str] | None = None,
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
    authority_class: str = "PR168_DATA1A_PUBLIC_READ_ONLY_AUDIT",
) -> dict[str, Any]:
    route = ROUTES[route_key]
    return {
        "upstream_input_refs": list(upstream_refs or []),
        "DATA1_artifact_refs": list(data1_refs or []),
        "row_shard_refs_if_any": list(row_shard_refs or []),
        "data_provenance_refs": list(provenance_refs or []),
        "owning_agent": route["owning_agent"],
        "consumer_agents": list(route["consumer_agents"]),
        "downstream_consumers": list(route["consumer_agents"]),
        "downstream_pr_refs": list(DOWNSTREAM_PRS),
        "validator_refs": list(VALIDATOR_REFS),
        "test_refs": list(TEST_REFS),
        "no_orphan_status": "NO_ORPHAN_ROUTED",
        "terminal_by_nature_flag": terminal_by_nature_flag,
        "terminal_reason_code": terminal_reason_code,
        "authority_class": authority_class,
        **authority_flags(),
    }


def count_confidence(
    name: str,
    value: int | float | None,
    authority_state: str,
    *,
    source_file_refs: list[str],
    row_selection_rule: str,
    join_key_used: str = "NOT_APPLICABLE",
    dedupe_key_used: str = "NOT_APPLICABLE",
    nested_array_expansion_rule: str = "NOT_APPLICABLE",
    missing_or_unknown_reason: str | None = None,
    confidence_level: str = "EXACT",
    gfp2r_allowed: bool = True,
) -> dict[str, Any]:
    return {
        "count_name": name,
        "count_value": value,
        "count_authority_state": authority_state,
        "source_file_refs": source_file_refs,
        "row_selection_rule": row_selection_rule,
        "join_key_used": join_key_used,
        "dedupe_key_used": dedupe_key_used,
        "nested_array_expansion_rule": nested_array_expansion_rule,
        "missing_or_unknown_reason": missing_or_unknown_reason,
        "confidence_level": confidence_level,
        "GFP2R_consumption_allowed_flag": gfp2r_allowed,
        **route_defaults("governance", data1_refs=source_file_refs),
    }


def parse_iso(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value)
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None
