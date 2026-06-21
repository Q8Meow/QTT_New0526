#!/usr/bin/env python3
"""External candidate source acquisition lanes for PR168-GFP2."""

from __future__ import annotations

from typing import Any


SOURCE_SURFACES = (
    ("KALSHI", "market_event_orderbook_trade_fee_settlement", "OFFICIAL_SOURCE_CANDIDATE", "https://kalshi.com/docs"),
    ("KALSHI", "public_probability_and_fee_explainers", "OFFICIAL_SOURCE_CANDIDATE", "https://help.kalshi.com"),
    ("POLYMARKET", "gamma_data_clob_orderbook_prices_history_trade_fee_settlement", "OFFICIAL_SOURCE_CANDIDATE", "https://docs.polymarket.com"),
    ("POLYMARKET", "institutional_orderbook_concepts", "OFFICIAL_SOURCE_CANDIDATE", "https://docs.polymarket.us"),
    ("FORECASTEX_IBKR", "event_contract_market_data_daily_intraday_settlement_cost", "OFFICIAL_SOURCE_CANDIDATE", "https://www.interactivebrokers.com"),
    ("QISKIT", "quadraticprogram_qubo_conversion", "OFFICIAL_SOURCE_CANDIDATE", "https://qiskit-community.github.io/qiskit-optimization"),
    ("DWAVE", "bqm_qubo_cqm_ising_models", "OFFICIAL_SOURCE_CANDIDATE", "https://docs.dwavequantum.com"),
    ("INSTITUTIONAL_RESEARCH", "tca_fdr_calibration_capacity_portfolio_governance", "INSTITUTIONAL_RESEARCH_CANDIDATE", "PUBLIC_RESEARCH_REFS"),
)


def external_candidate_source_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (venue, surface, tier, source_ref) in enumerate(SOURCE_SURFACES, start=1):
        rows.append(
            {
                "candidate_source_id": f"PR168_GFP2_SOURCE::{index:03d}",
                "venue_or_domain": venue,
                "candidate_surface": surface,
                "source_ref": source_ref,
                "source_tier": tier,
                "accepted_truth_flag": False,
                "candidate_only_flag": True,
                "official_source_flag": tier == "OFFICIAL_SOURCE_CANDIDATE",
                "non_official_source_flag": tier != "OFFICIAL_SOURCE_CANDIDATE",
                "source_conflict_state": "PENDING_ACCEPTED_SOURCE_EVIDENCE_REVIEW",
                "staleness_state": "PENDING_REVALIDATION",
                "may_seed_replay_paper_queue_flag": True,
                "may_prove_profit_or_source_truth_flag": False,
                "repair_route_if_missing": "PR162D-R3",
                "downstream_pr_refs": ["PR162D-R3", "PR168-RP2"],
                "agent_owner": "Source Evidence Agent",
                "agent_consumers": ["Replay Paper Recompute Agent", "Governance Agent"],
                "validator_refs": ["tools/pr168_gfp2_validator.py"],
                "test_refs": ["tests/pr168_gfp2"],
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows


def venue_binding_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in external_candidate_source_rows():
        for binding_family in (
            "market_venue_payoff",
            "orderbook_trade_resolution",
            "fee_slippage_fill_latency_tca",
            "current_market_data",
            "historical_replay_data",
        ):
            rows.append(
                {
                    "binding_queue_id": f"{source['candidate_source_id']}::{binding_family}",
                    "venue_or_domain": source["venue_or_domain"],
                    "binding_family": binding_family,
                    "source_ref": source["source_ref"],
                    "source_tier": source["source_tier"],
                    "accepted_truth_flag": False,
                    "candidate_only_flag": True,
                    "required_before_real_positive_negative_flag": True,
                    "downstream_pr_refs": ["PR162D-R3", "PR168-RP2"],
                    "agent_owner": "Source Evidence Agent",
                    "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
                }
            )
    return rows
