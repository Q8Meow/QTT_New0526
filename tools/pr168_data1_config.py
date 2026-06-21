#!/usr/bin/env python3
"""Central constants for PR168-DATA1 public market-data acquisition."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"

TOOL_NAME = "tools/build_pr168_data1_public_market_data_snapshots.py"
REPORT_VERSION = "PR168-DATA1-v3.0"
BRANCH_NAME = "pr168-data1-public-market-data-snapshots"

KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"
POLYMARKET_GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
POLYMARKET_DATA_BASE_URL = "https://data-api.polymarket.com"
POLYMARKET_CLOB_BASE_URL = "https://clob.polymarket.com"
POLYMARKET_MARKET_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

HTTP_USER_AGENT = "QTT-PR168-DATA1-public-readonly-snapshot"
TIMEOUT_SECONDS_DEFAULT = 20
RETRY_COUNT_DEFAULT = 2
BACKOFF_SECONDS_DEFAULT = 0.25

kalshi_market_fetch_target_default = 100
kalshi_orderbook_snapshot_target_default = 1
kalshi_forward_l2_capture_market_target_default = 1
kalshi_trade_page_target_default = 1
kalshi_candlestick_market_target_default = 1
kalshi_historical_candlestick_market_target_default = 1
kalshi_historical_trade_page_target_default = 1

polymarket_market_fetch_target_default = 25
polymarket_orderbook_snapshot_target_default = 1
polymarket_forward_l2_capture_token_target_default = 1
polymarket_price_history_market_target_default = 1
polymarket_price_history_lookback_days_default = 1
polymarket_price_history_interval_default = "1d"
polymarket_trade_or_activity_page_target_default = 1

historical_full_book_search_target_default = 12
third_party_dataset_candidate_target_default = 8
forecastex_ibkr_default = "manifest_only_auth_required"

SNAPSHOT_DIR = GENERATED_ROOT / "pr168_data1_snapshots"
FORWARD_L2_DIR = GENERATED_ROOT / "pr168_data1_forward_l2"
HISTORICAL_CANDIDATE_DIR = GENERATED_ROOT / "pr168_data1_historical_replay_candidates"

KALSHI_SNAPSHOT_JSONL = SNAPSHOT_DIR / "kalshi" / "kalshi_snapshots.jsonl"
POLYMARKET_SNAPSHOT_JSONL = SNAPSHOT_DIR / "polymarket" / "polymarket_snapshots.jsonl"
KALSHI_FORWARD_L2_JSONL = FORWARD_L2_DIR / "kalshi" / "kalshi_forward_l2.jsonl"
POLYMARKET_FORWARD_L2_JSONL = FORWARD_L2_DIR / "polymarket" / "polymarket_forward_l2.jsonl"
HISTORICAL_CANDIDATE_JSONL = (
    HISTORICAL_CANDIDATE_DIR / "candidate_sources" / "historical_full_book_candidates.jsonl"
)
FORECASTEX_IBKR_MANIFEST = (
    SNAPSHOT_DIR / "forecastex_ibkr" / "forecastex_ibkr_auth_required.manifest.json"
)


REQUIRED_REPORT_IDS = [
    "PR168_DATA1_SourceEndpointDiscovery",
    "PR168_DATA1_PublicFetchExecutionSummary",
    "PR168_DATA1_HistoricalFullBookAvailabilityAudit",
    "PR168_DATA1_HistoricalFullBookAcquisitionLedger",
    "PR168_DATA1_ForwardFullBookReplayCaptureBootstrap",
    "PR168_DATA1_ForwardL2CaptureShardManifest",
    "PR168_DATA1_HistoricalPriceTradeCandleReplaySubstituteLedger",
    "PR168_DATA1_HistoricalL2GapRouteToFutureAcquisition",
    "PR168_DATA1_KalshiSnapshotManifest",
    "PR168_DATA1_PolymarketSnapshotManifest",
    "PR168_DATA1_ForecastExIBKRAuthRequiredManifest",
    "PR168_DATA1_DataReadinessClassification",
    "PR168_DATA1_NormalizedMarketDataFeatureRegistry",
    "PR168_DATA1_DataQualityFreshnessCoverageAudit",
    "PR168_DATA1_DataBindingPriorityByVenue",
    "PR168_DATA1_MinimumViableRealDataProofDatasetPlan",
    "PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse",
    "PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch",
    "PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch",
    "PR168_DATA1_QuantumForwardCoefficientFeatureSurface",
    "PR168_DATA1_AgentRoutingAndNoOrphanProof",
    "PR168_DATA1_DAGUpstreamDownstreamOrchestration",
    "PR168_DATA1_OperatorActionMatrix",
    "PR168_DATA1_ReportEssentialityAndDeduplicationAudit",
    "PR168_DATA1_FinalSummary",
    "PR168_DATA1_WebSocketDependencyGapReceipt",
    "PR168_DATA1_ThirdPartyHistoricalFullBookCandidateDatasetRegistry",
    "PR168_DATA1_PublicDatasetLicenseAndAccessSafetyAudit",
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


VALID_READINESS_STATES = {
    "DATA_READY_PUBLIC_REAL_SNAPSHOT_CANDIDATE",
    "DATA_READY_PUBLIC_REAL_FORWARD_L2_CANDIDATE",
    "DATA_READY_PUBLIC_REAL_HISTORY_CANDIDATE",
    "DATA_READY_PUBLIC_REAL_ORDERBOOK_CANDIDATE",
    "DATA_READY_PUBLIC_REAL_HISTORICAL_FULL_BOOK_CANDIDATE",
    "DATA_READY_PUBLIC_REAL_PRICE_HISTORY_CANDIDATE",
    "DATA_READY_PUBLIC_REAL_TRADE_HISTORY_CANDIDATE",
    "ACCEPTANCE_PENDING_SOURCE_EVIDENCE",
    "AUTH_REQUIRED_PENDING_OWNER_SETUP",
    "MARKET_DATA_SUBSCRIPTION_REQUIRED",
    "NETWORK_UNAVAILABLE",
    "ENDPOINT_UNAVAILABLE",
    "RATE_LIMITED_RETRYABLE",
    "SCHEMA_CHANGED_REVIEW_REQUIRED",
    "EMPTY_BUT_VALID_RESPONSE",
    "UNSAFE_OR_FORBIDDEN_ENDPOINT",
    "DUPLICATE_DATA_SUPPRESSED",
    "IRRELEVANT_OR_IMPOSSIBLE_TO_MAP",
    "PUBLIC_HISTORICAL_FULL_BOOK_UNAVAILABLE_EXACT_REASON",
    "THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATE_ONLY",
}


DOWNSTREAM_PRS = ["PR168-GFP2R", "PR168-RP2", "PR168-RANK2"]
VALIDATOR_REFS = ["tools/pr168_data1_validator.py", "tools/validate_pr168_data1_public_market_data_snapshots.py"]
TEST_REFS = ["tests/pr168_data1"]


ROUTES = {
    "market_data": {
        "owning_agent": "market_data_acquisition_agent",
        "consumer_agents": [
            "source_evidence_agent",
            "qku_formula_materialization_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
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
        "consumer_agents": ["dashboard_operator_agent", "source_evidence_agent"],
    },
}


DOC_SOURCES = [
    {
        "source_id": "kalshi_quick_start_market_data",
        "venue": "kalshi",
        "url": "https://docs.kalshi.com/getting_started/quick_start_market_data",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "public unauthenticated base URL, markets and orderbook quick start, WebSocket auth caveat",
    },
    {
        "source_id": "kalshi_orderbook_responses",
        "venue": "kalshi",
        "url": "https://docs.kalshi.com/getting_started/orderbook_responses",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "orderbook dollars schema, bid-only book semantics, binary-market ask derivation",
    },
    {
        "source_id": "kalshi_market_orderbook_endpoint",
        "venue": "kalshi",
        "url": "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "GET /markets/{ticker}/orderbook public read-only contract",
    },
    {
        "source_id": "kalshi_trades_endpoint",
        "venue": "kalshi",
        "url": "https://docs.kalshi.com/api-reference/market/get-trades",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "GET /markets/trades public trade history contract",
    },
    {
        "source_id": "kalshi_historical_data",
        "venue": "kalshi",
        "url": "https://docs.kalshi.com/getting_started/historical_data",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "historical cutoff, markets, trades, fills, orders, candlesticks; no public historical full-book route",
    },
    {
        "source_id": "kalshi_historical_orders",
        "venue": "kalshi",
        "url": "https://docs.kalshi.com/api-reference/historical/get-historical-orders",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "auth-required user order history, blocked by DATA1 default",
    },
    {
        "source_id": "kalshi_orderbook_websocket",
        "venue": "kalshi",
        "url": "https://docs.kalshi.com/websockets/orderbook-updates",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "orderbook_delta forward feed requires API key authentication",
    },
    {
        "source_id": "polymarket_api_introduction",
        "venue": "polymarket",
        "url": "https://docs.polymarket.com/api-reference/introduction",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "public Gamma, Data, and CLOB read endpoints; auth only for trading/order management",
    },
    {
        "source_id": "polymarket_market_data_overview",
        "venue": "polymarket",
        "url": "https://docs.polymarket.com/market-data/overview",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "public REST market data overview, CLOB current book and price-history surfaces",
    },
    {
        "source_id": "polymarket_get_order_book",
        "venue": "polymarket",
        "url": "https://docs.polymarket.com/api-reference/market-data/get-order-book",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "GET /book current orderbook, bids, asks, min order size, tick size, raw venue book hash",
    },
    {
        "source_id": "polymarket_prices_history",
        "venue": "polymarket",
        "url": "https://docs.polymarket.com/api-reference/markets/get-prices-history",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "GET /prices-history public price history, not full historical book depth",
    },
    {
        "source_id": "polymarket_market_websocket",
        "venue": "polymarket",
        "url": "https://docs.polymarket.com/api-reference/wss/market",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "public market WebSocket event types for forward capture when dependency is available",
    },
    {
        "source_id": "polymarket_data_api_trades",
        "venue": "polymarket",
        "url": "https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "public Data API market/user trade activity; DATA1 uses only public market-safe access",
    },
    {
        "source_id": "ibkr_event_contracts",
        "venue": "forecastex_ibkr",
        "url": "https://www.interactivebrokers.com/campus/ibkr-api-page/event-contracts/",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "event-contract conid and market-data entitlement requirements",
    },
    {
        "source_id": "qiskit_qubo_converter",
        "venue": "quantum_forward",
        "url": "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "downstream QUBO conversion requires explicit penalty scaling discipline",
    },
    {
        "source_id": "dwave_ocean_models",
        "venue": "quantum_forward",
        "url": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
        "relevance": "BQM/CQM/Ising model readiness references for downstream mapping, no backend execution",
    },
]


ENDPOINT_CONTRACTS = [
    {
        "endpoint_id": "kalshi_markets",
        "venue": "kalshi",
        "method": "GET",
        "url": f"{KALSHI_BASE_URL}/markets",
        "params": ["limit", "status"],
        "auth_requirement": "PUBLIC_UNAUTHENTICATED",
        "data_families": ["market_metadata", "lifecycle", "fees_tick_size"],
        "historical_full_book_availability": "NOT_A_FULL_BOOK_ENDPOINT",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "kalshi_current_orderbook",
        "venue": "kalshi",
        "method": "GET",
        "url": f"{KALSHI_BASE_URL}/markets/{{ticker}}/orderbook",
        "params": ["ticker"],
        "auth_requirement": "PUBLIC_UNAUTHENTICATED",
        "data_families": ["current_full_orderbook_snapshot"],
        "historical_full_book_availability": "CURRENT_SNAPSHOT_ONLY",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "kalshi_live_trades",
        "venue": "kalshi",
        "method": "GET",
        "url": f"{KALSHI_BASE_URL}/markets/trades",
        "params": ["limit", "cursor", "ticker", "min_ts", "max_ts"],
        "auth_requirement": "PUBLIC_UNAUTHENTICATED",
        "data_families": ["trade_history"],
        "historical_full_book_availability": "TRADE_HISTORY_NOT_FULL_BOOK",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "kalshi_historical_trades",
        "venue": "kalshi",
        "method": "GET",
        "url": f"{KALSHI_BASE_URL}/historical/trades",
        "params": ["limit", "cursor", "ticker", "min_ts", "max_ts"],
        "auth_requirement": "PUBLIC_UNAUTHENTICATED",
        "data_families": ["historical_trade_history"],
        "historical_full_book_availability": "TRADE_HISTORY_NOT_FULL_BOOK",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "kalshi_historical_orders",
        "venue": "kalshi",
        "method": "GET",
        "url": f"{KALSHI_BASE_URL}/historical/orders",
        "params": ["ticker", "cursor", "limit"],
        "auth_requirement": "AUTH_REQUIRED_USER_SCOPED_NOT_USED",
        "data_families": ["historical_user_orders"],
        "historical_full_book_availability": "AUTH_REQUIRED_NOT_USED_BY_DATA1_DEFAULT",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "polymarket_gamma_markets",
        "venue": "polymarket",
        "method": "GET",
        "url": f"{POLYMARKET_GAMMA_BASE_URL}/markets",
        "params": ["active", "closed", "limit"],
        "auth_requirement": "PUBLIC_UNAUTHENTICATED",
        "data_families": ["market_metadata", "lifecycle", "liquidity_volume"],
        "historical_full_book_availability": "NOT_A_FULL_BOOK_ENDPOINT",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "polymarket_clob_book",
        "venue": "polymarket",
        "method": "GET",
        "url": f"{POLYMARKET_CLOB_BASE_URL}/book",
        "params": ["token_id"],
        "auth_requirement": "PUBLIC_UNAUTHENTICATED",
        "data_families": ["current_full_orderbook_snapshot"],
        "historical_full_book_availability": "CURRENT_SNAPSHOT_ONLY",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "polymarket_prices_history",
        "venue": "polymarket",
        "method": "GET",
        "url": f"{POLYMARKET_CLOB_BASE_URL}/prices-history",
        "params": ["market", "startTs", "endTs", "interval", "fidelity"],
        "auth_requirement": "PUBLIC_UNAUTHENTICATED",
        "data_families": ["price_history"],
        "historical_full_book_availability": "PRICE_HISTORY_NOT_FULL_BOOK",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "polymarket_data_trades",
        "venue": "polymarket",
        "method": "GET",
        "url": f"{POLYMARKET_DATA_BASE_URL}/trades",
        "params": ["market", "user", "limit"],
        "auth_requirement": "PUBLIC_MARKET_SAFE_WHEN_NOT_USER_PRIVATE",
        "data_families": ["trade_history", "activity"],
        "historical_full_book_availability": "TRADE_HISTORY_NOT_FULL_BOOK",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
    {
        "endpoint_id": "polymarket_public_market_websocket",
        "venue": "polymarket",
        "method": "WSS",
        "url": POLYMARKET_MARKET_WS_URL,
        "params": ["assets_ids", "type=market"],
        "auth_requirement": "PUBLIC_UNAUTHENTICATED_MARKET_CHANNEL",
        "data_families": ["forward_l2_stream", "price_change", "last_trade_price"],
        "historical_full_book_availability": "FORWARD_CAPTURE_ONLY",
        "source_tier": "OFFICIAL_PUBLIC_API",
    },
]


THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATES = [
    {
        "source_id": "predexon_kalshi_orderbooks",
        "venue": "kalshi",
        "url": "https://docs.predexon.com/api-reference/kalshi/orderbooks",
        "candidate_state": "AUTH_REQUIRED_PENDING_OWNER_SETUP",
        "reason": "non-official historical Kalshi orderbook API advertises x-api-key requirement",
        "source_tier": "PUBLIC_RESEARCH_DATASET_CANDIDATE",
    },
    {
        "source_id": "allium_kalshi_market_orderbook",
        "venue": "kalshi",
        "url": "https://docs.allium.so/historical-data/predictions/kalshi/market-orderbook",
        "candidate_state": "THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATE_ONLY",
        "reason": "non-official warehouse table route requires Allium access and source-evidence review",
        "source_tier": "PUBLIC_RESEARCH_DATASET_CANDIDATE",
    },
    {
        "source_id": "pmxt_polymarket_archive",
        "venue": "polymarket",
        "url": "https://archive.pmxt.dev/Polymarket",
        "candidate_state": "THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATE_ONLY",
        "reason": "public archive index needs manual dataset/license review before acquisition",
        "source_tier": "PUBLIC_RESEARCH_DATASET_CANDIDATE",
    },
    {
        "source_id": "polymarket_microstructure_research_archive",
        "venue": "polymarket",
        "url": "https://arxiv.org/html/2604.24366v1",
        "candidate_state": "THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATE_ONLY",
        "reason": "research describes tick-level order-book archive; no official source-truth acceptance route",
        "source_tier": "PUBLIC_RESEARCH_DATASET_CANDIDATE",
    },
    {
        "source_id": "prediction_market_analysis_repo",
        "venue": "multi_venue",
        "url": "https://github.com/jon-becker/prediction-market-analysis",
        "candidate_state": "THIRD_PARTY_HISTORICAL_FULL_BOOK_CANDIDATE_ONLY",
        "reason": "public research dataset appears market/trade centric; useful candidate, not accepted L2 source truth",
        "source_tier": "PUBLIC_RESEARCH_DATASET_CANDIDATE",
    },
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generated_ref(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def report_path(report_id: str) -> Path:
    return GENERATED_ROOT / f"{report_id}.report.json"


def manifest_path(jsonl_path: Path) -> Path:
    return jsonl_path.with_suffix(".manifest.json")


def route_defaults(route_key: str = "market_data") -> dict[str, object]:
    route = ROUTES[route_key]
    return {
        "owning_agent": route["owning_agent"],
        "consumer_agents": list(route["consumer_agents"]),
        "downstream_consumers": list(route["consumer_agents"]),
        "downstream_pr_refs": list(DOWNSTREAM_PRS),
        "validator_refs": list(VALIDATOR_REFS),
        "test_refs": list(TEST_REFS),
        "no_orphan_status": "NO_ORPHAN_ROUTED",
        "authority_class": "PUBLIC_READ_ONLY_DATA_ACQUISITION_CANDIDATE",
        "terminal_by_nature_flag": False,
        "terminal_reason_code": None,
    }


def authority_flags() -> dict[str, bool]:
    return dict(AUTHORITY_FALSE_FLAGS)
