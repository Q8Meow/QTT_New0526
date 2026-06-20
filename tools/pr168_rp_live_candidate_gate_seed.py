#!/usr/bin/env python3
"""Future-only live pretrade decision gate seed for PR168-RP."""

from __future__ import annotations


def live_gate_seed() -> dict[str, object]:
    return {
        "gate_id": "PR168_RP_LIVE_PRETRADE_DECISION_GATE_V1_SEED",
        "packet_type": "LivePreTradeDecisionGateV1",
        "allowed_formula_stack_ref": "PR168_RP_To_RuntimeFormulaAllowlistHotPathCacheSeed.report.json",
        "allowed_qku_combination_ref": "PR168_RP_QKUCombinationCandidateResults.report.json",
        "allowed_order_policy_ref": "PR168_RP_OrderPolicyCandidateRanking.report.json",
        "max_latency_ms_budget": "MISSING_DEFAULT_THRESHOLD",
        "max_stale_book_ms": "MISSING_DEFAULT_THRESHOLD",
        "max_spread_bps": "MISSING_DEFAULT_THRESHOLD",
        "min_visible_depth": "MISSING_DEFAULT_THRESHOLD",
        "min_fill_probability": "MISSING_DEFAULT_THRESHOLD",
        "max_capacity_usage": "MISSING_DEFAULT_THRESHOLD",
        "max_event_exposure": "MISSING_DEFAULT_THRESHOLD",
        "max_common_driver_exposure": "MISSING_DEFAULT_THRESHOLD",
        "min_lcb_edge": "MISSING_DEFAULT_THRESHOLD",
        "min_fill_adjusted_expected_pnl": "MISSING_DEFAULT_THRESHOLD",
        "no_unresolved_agent_gap": True,
        "no_source_truth_violation": True,
        "no_connector_binding_violation": True,
        "execution_router_required": True,
        "live_authority_created_by_pr168_rp": False,
        "source_truth_authority": False,
        "connector_truth_authority": False,
        "producer": "PR168_RP_LIVE_CANDIDATE_GATE_SEED",
        "consumer": "Future Execution Router Live Gate PR",
        "upstream_source": "PR168_RP_PreTradeSimulationCandidates.report.json",
        "downstream_route": "PR168_RP_To_ExecutionRouterLiveGateFutureHandoff.report.json",
        "owning_agent": "Governance Agent",
        "no_orphan_status": "CONNECTED_TO_FUTURE_LIVE_GATE_CONSUMER",
    }
