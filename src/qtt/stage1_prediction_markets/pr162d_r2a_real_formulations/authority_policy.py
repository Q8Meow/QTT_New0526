"""Central authority boundary policy for PR162D-R2A.

All validators and generated audit reports consume this module so no-live,
no-result, no-profit, no-QTT-SHA, and no-AtomicRows boundaries are not
redefined independently across the implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PR_ID = "PR162D_R2A"
AUTHORITY_CLASS = (
    "PR162D_R2A_REAL_EXECUTABLE_CANDIDATE_FORMULATIONS_NO_LIVE_ORDER_NO_REPLAY_PAPER_EXECUTION"
)
EXPECTED_BRANCH = "pr162d-r2a-real-computable-formulations-redo"
POLICY_MODULE_REF = (
    "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.authority_policy"
)

SOURCE_TRUTH_STATUSES = (
    "OWNER_TEMPLATE",
    "OFFICIAL_SOURCE_CANDIDATE",
    "NON_OFFICIAL_RESEARCH_CANDIDATE",
    "SOCIAL_SIGNAL_CANDIDATE",
    "GITHUB_RESEARCH_CANDIDATE",
    "INSTITUTIONAL_RESEARCH_CANDIDATE",
    "OWNER_SUBMITTED_CANDIDATE",
    "AGENT_DISCOVERED_CANDIDATE",
    "WEB_SCOUTED_CANDIDATE",
    "QUANTUM_PROVIDER_RESEARCH_CANDIDATE",
    "NOT_MATERIALIZED_FIELD_FILL_REQUIRED",
)

CANDIDATE_TRUTH_STATUSES = (
    "CANDIDATE",
    "PROVISIONAL",
    "REPLAY_PAPER_CANDIDATE",
    "OWNER_TEMPLATE_CANDIDATE",
    "NEEDS_REPLAY_PAPER_EVIDENCE",
    "NEEDS_OWNER_REVIEW",
    "PROMOTED_BY_FUTURE_RECEIPT_ONLY",
)

FORMULATION_OUTCOMES = (
    "FORMULATION_FULLY_MATERIALIZED",
    "FORMULATION_PARTIALLY_MATERIALIZED",
    "REPLAY_PAPER_ROUTE_READY",
    "EXACT_FIELD_FILL_ACTION_CREATED",
    "DUPLICATE_OR_EQUIVALENT_MAPPED",
    "DORMANT_NON_STAGE1_CLASSIFIED",
    "OWNER_REVIEW_REQUIRED_WITH_REASON",
    "LIVE_MATERIALIZATION_NOT_IN_SCOPE",
)

FORMULATION_TYPES = (
    "FORMULA",
    "ALGORITHM",
    "PARAMETER_PACK",
    "FEATURE",
    "OBJECTIVE_CONSTRAINT_SOLVER",
    "QUANTUM_FORMULATION",
)

COMPUTE_TIERS = (
    "TIER_0_CONSTANT_OR_CACHED_PARAMETER",
    "TIER_1_SIMPLE_ARITHMETIC_FORMULA",
    "TIER_2_VECTORIZED_FEATURE_FORMULA",
    "TIER_3_CLASSICAL_OPTIMIZER_FORMULA",
    "TIER_4_QUANTUM_OR_HYBRID_BATCH_OPTIMIZER",
    "TIER_5_REPLAY_PAPER_RESEARCH_ONLY",
)

LATENCY_CLASSES = (
    "HOT_PATH_ELIGIBLE_CANDIDATE",
    "PRECOMPUTE_REQUIRED",
    "CACHE_READ_ELIGIBLE",
    "INCREMENTAL_UPDATE_ELIGIBLE",
    "BATCH_ONLY",
    "REPLAY_PAPER_ONLY",
    "QUANTUM_BATCH_ONLY",
)

INTAKE_LANES = (
    "FAST_REPLAY_PAPER_CANDIDATE",
    "FORMULATION_ONLY_ROUTE_FILL_REQUIRED",
    "FIELD_FILL_REQUIRED",
    "EXECUTABLE_WITH_ENHANCEMENT_BACKLOG",
)

NO_AUTHORITY_FLAGS: dict[str, bool] = {
    "creates_live_authority": False,
    "creates_order_authority": False,
    "creates_connector_semantics": False,
    "creates_private_state": False,
    "creates_source_truth_authority": False,
    "executes_replay_adapter": False,
    "executes_paper_adapter": False,
    "emits_replay_paper_results": False,
    "emits_result_packets": False,
    "creates_profit_evidence": False,
    "creates_quantum_advantage_evidence": False,
    "creates_live_reachability_claim": False,
    "creates_live_promotion_ready_claim": False,
    "creates_order_ready_claim": False,
    "creates_qtt_sha_authority": False,
    "creates_qtt_generated_sha": False,
    "creates_qtt_freeze_authority": False,
    "creates_qtt_global_digest_checksum_authority": False,
    "mutates_atomicrows_bundle_jsonl": False,
    "creates_atomicrows_bundle_hash_sha_artifact": False,
    "references_protected_atomicrows_hash_sha_artifact_path": False,
    "quantum_backend_execution_required": False,
    "ci_requires_network": False,
}

BOUNDARY_COUNT_FIELDS: dict[str, int] = {
    "live_order_authority_count": 0,
    "order_ready_count": 0,
    "live_promotion_ready_count": 0,
    "live_reachability_claim_count": 0,
    "profit_evidence_count": 0,
    "private_state_fetch_count": 0,
    "replay_execution_count": 0,
    "paper_execution_count": 0,
    "result_packet_created_count": 0,
    "qtt_sha_freeze_checksum_authority_count": 0,
    "qtt_generated_sha_count": 0,
    "atomicrows_bundle_mutation_count": 0,
    "protected_atomicrows_hash_sha_artifact_count": 0,
    "quantum_backend_execution_count": 0,
    "quantum_advantage_claim_count": 0,
}

PROTECTED_FILES_NOT_TOUCHED = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "AtomicRows bundle JSONL artifacts",
    "AtomicRows bundle hash/SHA artifacts",
)

SOURCE_SCOUT_LOCATORS = (
    {
        "source_locator_id": "PR162D_R2A_SOURCE_KALSHI_MARKET_CANDLESTICKS",
        "source_truth_status": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://docs.kalshi.com/api-reference/market/get-market-candlesticks",
        "confidence_reason": "Official Kalshi API reference locator for market candlestick candidate data fields.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
    {
        "source_locator_id": "PR162D_R2A_SOURCE_KALSHI_HISTORICAL_CANDLESTICKS",
        "source_truth_status": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://docs.kalshi.com/api-reference/historical/get-historical-market-candlesticks",
        "confidence_reason": "Official Kalshi historical candlestick locator for replay/paper data binding candidates.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
    {
        "source_locator_id": "PR162D_R2A_SOURCE_POLYMARKET_API_OVERVIEW",
        "source_truth_status": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://docs.polymarket.com/api-reference",
        "confidence_reason": "Official Polymarket API overview locator for public Gamma, Data, and CLOB candidate lanes.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
    {
        "source_locator_id": "PR162D_R2A_SOURCE_POLYMARKET_PRICE_HISTORY",
        "source_truth_status": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://docs.polymarket.com/api-reference/markets/get-prices-history",
        "confidence_reason": "Official Polymarket CLOB price-history locator for historical price feature candidates.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
    {
        "source_locator_id": "PR162D_R2A_SOURCE_FORECASTEX_DATA",
        "source_truth_status": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://www.forecastex.com/data/",
        "confidence_reason": "ForecastEx public data locator for daily and intraday CSV candidate files.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
    {
        "source_locator_id": "PR162D_R2A_SOURCE_DWAVE_MODELS",
        "source_truth_status": "QUANTUM_PROVIDER_RESEARCH_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "confidence_reason": "D-Wave model documentation locator for BQM, CQM, QUBO, and Ising shape candidates.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
    {
        "source_locator_id": "PR162D_R2A_SOURCE_QISKIT_QAOA",
        "source_truth_status": "QUANTUM_PROVIDER_RESEARCH_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://qiskit-community.github.io/qiskit-algorithms/stubs/qiskit_algorithms.QAOA.html",
        "confidence_reason": "Qiskit algorithm documentation locator for QAOA/SamplingVQE suitability candidates.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
    {
        "source_locator_id": "PR162D_R2A_SOURCE_SKLEARN_BRIER",
        "source_truth_status": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://sklearn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html",
        "confidence_reason": "scikit-learn metric documentation locator for Brier score candidate formulation.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
    {
        "source_locator_id": "PR162D_R2A_SOURCE_TALIB",
        "source_truth_status": "NON_OFFICIAL_RESEARCH_CANDIDATE",
        "candidate_truth_status": "REPLAY_PAPER_CANDIDATE",
        "source_locator": "https://ta-lib.org/index.html",
        "confidence_reason": "TA-Lib public technical-analysis locator for RSI, MACD, and Bollinger candidate formulas.",
        "replay_paper_candidate_flag": True,
        "official_truth_flag": False,
        "live_order_authority": False,
    },
)


@dataclass(frozen=True)
class AuthorityCheck:
    ok: bool
    failures: tuple[str, ...]


def boundary_payload() -> dict[str, Any]:
    return {
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "authority_class": AUTHORITY_CLASS,
        "central_policy_consumed_flag": True,
        "source_truth_statuses": list(SOURCE_TRUTH_STATUSES),
        "candidate_truth_statuses": list(CANDIDATE_TRUTH_STATUSES),
        "no_authority_flags": dict(NO_AUTHORITY_FLAGS),
        "boundary_count_fields": dict(BOUNDARY_COUNT_FIELDS),
        "protected_files_not_touched": list(PROTECTED_FILES_NOT_TOUCHED),
        "official_truth_flag": False,
        "live_order_authority": False,
    }


def no_authority_record(record_id: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "central_policy_consumed_flag": True,
        "live_order_authority": False,
        "official_truth_flag": False,
        "replay_execution_count": 0,
        "paper_execution_count": 0,
        "result_packet_created_count": 0,
        "profit_evidence_count": 0,
        "private_state_fetch_count": 0,
        "qtt_sha_freeze_checksum_authority_count": 0,
        "qtt_generated_sha_count": 0,
        "atomicrows_bundle_mutation_count": 0,
        "protected_atomicrows_hash_sha_artifact_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "validation_status": "PASS",
    }


def validate_record_authority(record: dict[str, Any]) -> AuthorityCheck:
    failures: list[str] = []
    if record.get("live_order_authority") is not False:
        failures.append(f"{record.get('formulation_id') or record.get('record_id')} live_order_authority drift")
    if record.get("official_truth_flag") is True:
        failures.append(f"{record.get('formulation_id') or record.get('record_id')} official truth drift")
    for key in (
        "result_packet_created_flag",
        "profit_evidence_claim_flag",
        "quantum_advantage_claim_flag",
        "quantum_backend_execution_flag",
    ):
        if record.get(key) is True:
            failures.append(f"{record.get('formulation_id') or record.get('record_id')} boundary flag drift: {key}")
    return AuthorityCheck(not failures, tuple(failures))
