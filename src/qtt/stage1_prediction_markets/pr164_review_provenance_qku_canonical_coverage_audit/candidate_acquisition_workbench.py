"""Deterministic candidate source acquisition workbench."""

from __future__ import annotations

from typing import Any

from .candidate_source_policy import ensure_policy_disposition, policy_for
from .deterministic_ids import plain_ref


OBSERVED_AT_UTC = "2026-06-06T00:00:00Z"


SOURCE_SEEDS: tuple[dict[str, str], ...] = (
    {
        "source_class": "OFFICIAL_VENUE_OR_REGULATORY",
        "source_locator": "CFTC prediction-market and event-contract regulatory research target",
        "extracted_candidate_value": "regulatory event-contract constraint candidates for replay/paper review",
        "qku_mapping": "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
        "confidence_hint": "HIGH_FOR_SOURCE_EXISTENCE_CANDIDATE_VALUES_REQUIRE_REPLAY_PAPER_VERIFICATION",
    },
    {
        "source_class": "OFFICIAL_API_DOC",
        "source_locator": "Kalshi, Polymarket, and other venue API documentation source target",
        "extracted_candidate_value": "fee, orderbook, tick, payout, and settlement semantic candidates only",
        "qku_mapping": "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
        "confidence_hint": "HIGH_FOR_LOCATOR_LOW_FOR_UNBOUND_LIVE_SEMANTICS",
    },
    {
        "source_class": "ACADEMIC_RESEARCH",
        "source_locator": "academic prediction-market efficiency and market microstructure literature target",
        "extracted_candidate_value": "probability calibration, divergence, and liquidity formula candidates",
        "qku_mapping": "probability_calibration_edge",
        "confidence_hint": "MEDIUM_RESEARCH_CANDIDATE",
    },
    {
        "source_class": "INSTITUTIONAL_RESEARCH",
        "source_locator": "institutional execution-cost and model-risk governance research target",
        "extracted_candidate_value": "TCA, latency, and model-risk monitoring metric candidates",
        "qku_mapping": "market_microstructure_liquidity",
        "confidence_hint": "MEDIUM_RESEARCH_CANDIDATE",
    },
    {
        "source_class": "OPEN_SOURCE_REPO_RESEARCH_ONLY",
        "source_locator": "open-source optimizer and QUBO formulation repositories as research-only locators",
        "extracted_candidate_value": "QUBO/CQM constraint-shape candidates; no external code execution",
        "qku_mapping": "quantum_bundle_selection_optimizer",
        "confidence_hint": "LOW_UNTIL_LOCAL_REIMPLEMENTATION_AND_TEST_VECTOR_VERIFIED",
    },
    {
        "source_class": "SOCIAL_SIGNAL_RESEARCH_ONLY",
        "source_locator": "social discussion signals about event-market liquidity and stale pricing",
        "extracted_candidate_value": "candidate signal families for source-scout queue only",
        "qku_mapping": "source_uncertainty_penalty",
        "confidence_hint": "LOW_RESEARCH_ONLY",
    },
    {
        "source_class": "NEWS_RESEARCH_ONLY",
        "source_locator": "news/event calendars for exogenous event timing research",
        "extracted_candidate_value": "event timing and lifecycle penalty candidates",
        "qku_mapping": "market_lifecycle_penalty",
        "confidence_hint": "LOW_RESEARCH_ONLY",
    },
    {
        "source_class": "OWNER_PROVIDED",
        "source_locator": "PR164 owner prompt",
        "extracted_candidate_value": "accept useful official, non-official, research, social, owner, classical, hybrid, and quantum candidate information in provisional lanes",
        "qku_mapping": "candidate_source_policy",
        "confidence_hint": "HIGH_OWNER_POLICY",
    },
    {
        "source_class": "LOCAL_REPO_DERIVED",
        "source_locator": "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json",
        "extracted_candidate_value": "6502 current CandidatePacketV1 rows and formula/test-vector refs",
        "qku_mapping": "CandidatePacketV1",
        "confidence_hint": "HIGH_REPO_LOCAL_DETERMINISTIC",
    },
    {
        "source_class": "SYNTHETIC_REPLAY_PAPER_DERIVED",
        "source_locator": "docs/master_plan/generated/PR163_B_TransactionCostAnalysisCandidateRegistry.report.json",
        "extracted_candidate_value": "synthetic replay/paper TCA candidate components, not profit evidence",
        "qku_mapping": "execution_cost_components",
        "confidence_hint": "MEDIUM_SYNTHETIC_FIXTURE",
    },
    {
        "source_class": "UNSAFE_REJECTED",
        "source_locator": "external package install or credential-seeking execution request",
        "extracted_candidate_value": "blocked unsafe source action",
        "qku_mapping": "UNSAFE_REJECTED",
        "confidence_hint": "REJECTED_UNSAFE",
        "rejection_reason": "UNSAFE",
    },
    {
        "source_class": "OPEN_SOURCE_REPO_RESEARCH_ONLY",
        "source_locator": "duplicate open-source optimizer research locator",
        "extracted_candidate_value": "duplicate source target",
        "qku_mapping": "quantum_bundle_selection_optimizer",
        "confidence_hint": "REJECTED_DUPLICATE",
        "rejection_reason": "DUPLICATE",
    },
    {
        "source_class": "NEWS_RESEARCH_ONLY",
        "source_locator": "irrelevant entertainment news candidate source",
        "extracted_candidate_value": "irrelevant to QKU or prediction-market materialization",
        "qku_mapping": "IRRELEVANT",
        "confidence_hint": "REJECTED_IRRELEVANT",
        "rejection_reason": "IRRELEVANT",
    },
    {
        "source_class": "SOCIAL_SIGNAL_RESEARCH_ONLY",
        "source_locator": "unmapped social rumor with no event, market, formula, or source-policy target",
        "extracted_candidate_value": "impossible to map safely",
        "qku_mapping": "IMPOSSIBLE_TO_MAP",
        "confidence_hint": "REJECTED_IMPOSSIBLE_TO_MAP",
        "rejection_reason": "IMPOSSIBLE_TO_MAP",
    },
)


def build_candidate_source_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, seed in enumerate(SOURCE_SEEDS, 1):
        disposition = ensure_policy_disposition(policy_for(seed["source_class"], seed.get("rejection_reason", "")))
        rows.append(
            {
                "candidate_source_record_ref": plain_ref("SOURCE", index),
                "source_class": seed["source_class"],
                "source_locator": seed["source_locator"],
                "observed_at_utc": OBSERVED_AT_UTC,
                "extraction_method": "PR164_DETERMINISTIC_SOURCE_TARGET_MATERIALIZATION_NO_EXTERNAL_CODE_EXECUTION",
                "confidence_hint": seed["confidence_hint"],
                "extracted_candidate_value": seed["extracted_candidate_value"],
                "qku_mapping": seed["qku_mapping"],
                "intended_consumer": "candidate_research_provisional_replay_paper_lane",
                "source_policy_disposition": disposition,
                "nonofficial_rejected_merely_because_nonofficial": False,
                "source_truth_created": False,
                "connector_semantics_created": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_source_to_qku_mapping(source_rows: list[dict[str, Any]], identity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted = [row for row in source_rows if not row["source_policy_disposition"].startswith("REJECT_")]
    rows = []
    for index, identity in enumerate(identity_rows, 1):
        source = accepted[(index - 1) % len(accepted)]
        rows.append(
            {
                "candidate_source_to_qku_mapping_ref": plain_ref("SOURCE_QKU_MAP", index),
                "qku_id": identity["qku_id"],
                "candidate_id": identity["candidate_id"],
                "source_record_ref": source["candidate_source_record_ref"],
                "source_class": source["source_class"],
                "source_policy_disposition": source["source_policy_disposition"],
                "qku_mapping_reason": "Deterministic round-robin candidate source enrichment lane; value remains provisional until downstream replay/paper verification.",
                "intended_consumer": "source_scout_agent",
                "validation_status": "PASS",
            }
        )
    return rows
