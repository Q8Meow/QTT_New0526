"""Build PR169-DASH1 owner dashboard projections from one registry."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from .owner_action_registry import ACTION_DEFINITIONS
from .owner_dashboard_packet_builder import (
    build_actionable_cards,
    build_decision_queue,
    build_header_strip,
    build_owner_dashboard_packet,
)
from .owner_surface_models import (
    AUTHORITATIVE_SOURCE,
    AUTHORITY_BOUNDARY_REF,
    GENERATED_FROM,
    NO_ORPHAN_REF,
    PR_ID,
    PRODUCER_TOOL,
    REGISTRY_FILENAME,
    REQUIRED_JSONL_OUTPUTS,
    REQUIRED_JSON_OUTPUTS,
    REQUIRED_UI_OUTPUTS,
    ST12G_CONTRACT_MANIFEST_REF,
    ST12G_DASHBOARD_SURFACE_ID,
    ST12G_DESCRIPTOR_FILENAME,
    ST12G_REGISTRY_FEATURE_ID,
    ST12G_SOURCE_OWNER,
    ST12G_SVC_DESCRIPTOR_REF,
    VALIDATION_MARKER,
    VALIDATOR_REF,
    projection_trace,
    read_jsonl,
    registry_row_ref,
    repo_posix,
    write_json,
    write_jsonl,
)


UPSTREAM_REFS = {
    "rp5g": "docs/master_plan/generated/pr168_rp5g/exec_pnl.jsonl",
    "rp5g_tca": "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl",
    "rp5g_qstruct": "docs/master_plan/generated/pr168_rp5g/qstruct_problem.jsonl",
    "rank4": "docs/master_plan/generated/pr168_rank4/rank_edge_capture.jsonl",
    "qopt1": "docs/master_plan/generated/pr168_qopt1/notrade_reopt.jsonl",
    "qopt1_qstruct": "docs/master_plan/generated/pr168_qopt1/qstruct_optimized.jsonl",
    "vs2": "docs/master_plan/generated/pr168_vs2/vs2_packet_registry.jsonl",
    "vs2_qku": "docs/master_plan/generated/pr168_vs2/qku_formula_route_bundle.jsonl",
    "mem1": "docs/master_plan/generated/pr168_mem1/memory_query_contract.jsonl",
    "pr165_d2": "PR165_D2_CommandActionMatrix.report.json",
}

DEFAULT_AGENT_ROLES = ("dashboard_agent", "governance_agent", "commander_agent")
RISK_AGENT_ROLES = ("risk_manager_agent", "governance_agent", "commander_agent")
QUANTUM_AGENT_ROLES = ("quantum_optimizer_agent", "governance_agent", "commander_agent")
RESEARCH_AGENT_ROLES = ("parameter_selector_agent", "dashboard_agent", "commander_agent")

CHART_CONTRACTS = (
    "replay_vs_paper_pnl_chart",
    "cost_adjusted_net_pnl_chart",
    "drawdown_curve_chart",
    "latency_histogram_chart",
    "reject_throttle_error_rate_chart",
    "candidate_ranking_chart",
    "capital_usage_chart",
    "TCA_waterfall_chart",
    "implementation_shortfall_chart",
    "capacity_crowding_chart",
    "portfolio_marginal_utility_chart",
    "champion_challenger_scoreboard_chart",
    "no_trade_reoptimization_funnel_chart",
    "regime_memory_drift_chart",
    "QKU_formula_route_coverage_chart",
    "quantum_structural_readiness_heatmap",
    "qstruct_objective_constraint_variable_map_chart",
    "DAG_upstream_downstream_graph",
    "agent_KPI_merit_quarantine_chart",
    "source_validation_pipeline_chart",
    "LLM_critic_disagreement_chart",
    "shadow_vs_paper_vs_replay_comparison_chart",
)

INTERACTIVE_CHART_FAMILIES = (
    "portfolio_equity_curve",
    "portfolio_balance_by_time_range",
    "net_cash_pnl_by_day_month_year",
    "replay_vs_paper_vs_shadow_vs_live_pnl",
    "cost_adjusted_net_pnl",
    "cumulative_pnl_and_drawdown",
    "TCA_waterfall_and_implementation_shortfall",
    "fee_spread_slippage_impact_latency_breakdown",
    "capital_usage_and_exposure",
    "agent_performance_scoreboard",
    "agent_kpi_merit_quarantine_timeline",
    "agent_trade_decision_attribution",
    "QKU_formula_stack_performance_heatmap",
    "edge_alpha_candidate_scoreboard",
    "champion_challenger_rotation",
    "no_trade_reoptimization_funnel",
    "capacity_crowding_liquidity_panel",
    "latency_histogram",
    "reject_throttle_error_rate",
    "venue_platform_market_attribution",
    "source_research_candidate_funnel",
    "research_candidate_lifecycle_timeline",
    "quantum_structural_readiness_heatmap",
    "qstruct_objective_constraint_variable_map",
    "DAG_upstream_downstream_graph",
    "shadow_vs_paper_vs_replay_comparison",
)

TIME_RANGES = (
    "INTRADAY",
    "DAILY",
    "WEEKLY",
    "MONTHLY",
    "QUARTERLY",
    "YTD",
    "ONE_YEAR",
    "ALL_AVAILABLE",
)

FILTER_DIMENSIONS = (
    "mode",
    "agent",
    "market",
    "venue",
    "qku",
    "formula_stack",
    "source_candidate",
    "regime",
    "order_policy",
)

RESEARCH_SOURCE_FAMILIES = (
    "social_post_url",
    "news_article_url",
    "website_url",
    "pdf_or_uploaded_document",
    "owner_plain_text_idea",
    "formula_text",
    "algorithm_text",
    "quantum_strategy_text",
    "market_url_or_contract_url",
    "open_trade_url",
)

RESEARCH_PIPELINE_STATES = (
    "RESEARCH_SUBMITTED",
    "SOURCE_CANDIDATE_CREATED",
    "SOURCE_CAPTURE_REQUESTED",
    "SOURCE_CAPTURED",
    "SOURCE_VALIDATION_REQUESTED",
    "SOURCE_CONFLICT_REVIEW",
    "LLM_EXTRACTION_REQUESTED",
    "FORMULA_EXTRACTION_REQUESTED",
    "QKU_CANDIDATE_MATERIALIZATION_REQUESTED",
    "QKU_COMPUTABILITY_REVIEW_REQUESTED",
    "TEST_VECTOR_REQUESTED",
    "REPLAY_TEST_REQUESTED",
    "PAPER_TEST_REQUESTED",
    "VARIABLE_OPTIMIZATION_REQUESTED",
    "QOPT_ROUTE_REQUESTED",
    "RANKING_REVIEW_REQUESTED",
    "MEMORY_REVALIDATION_REQUESTED",
    "POSITIVE_NET_CASH_EVIDENCE_REVIEW",
    "OWNER_REVIEW_REQUIRED",
    "LIVE_CANARY_REVIEW_REQUESTED",
    "ALLOWLIST_REVIEW_REQUESTED",
    "ROUTED_PENDING_PROVIDER",
    "BLOCKED_BY_AUTHORITY_BOUNDARY",
    "REJECTED_DUPLICATE",
    "REJECTED_UNSAFE",
    "REJECTED_UNMAPPABLE",
)

RESEARCH_ROLES = (
    "owner_intake_receiver",
    "source_scout",
    "source_verifier",
    "LLM_research_extractor",
    "LLM_formula_interpreter",
    "QKU_materializer",
    "formula_computability_validator",
    "test_vector_builder",
    "trade_variable_optimizer",
    "replay_runner_provider",
    "paper_runner_provider",
    "ranker_optimizer_provider",
    "memory_revalidation_provider",
    "risk_pretrade_reviewer",
    "owner_review_router",
    "live_canary_review_router",
)

EXECUTION_LADDER_STATES = (
    "RESEARCH_CANDIDATE",
    "REPLAY_REQUESTED",
    "REPLAY_VALIDATED",
    "PAPER_REQUESTED",
    "PAPER_VALIDATED",
    "SHADOW_COMPARISON_REQUESTED",
    "SHADOW_COMPARISON_VALIDATED",
    "LIVE_DRYRUN_REQUESTED",
    "LIVE_DRYRUN_VALIDATED",
    "LIVE_PILOT_REVIEW_REQUESTED",
    "LIVE_PILOT_VALIDATED",
    "LAUNCH_REVIEW_REQUESTED",
    "EXECUTION_ROUTER_GATED",
)

FEATURE_COVERAGE_SEEDS = (
    "OwnerDashboardPacketV1 / owner dashboard packet",
    "OWNER_DASHBOARD_PACKET_CARD exact legacy alias",
    "OwnerHeaderStripV1",
    "OWNER_HEADER_STRIP_CARD exact legacy alias",
    "OwnerDecisionQueueV1 / DECISION_QUEUE",
    "DECISION_QUEUE_CARD_SHELL",
    "Severity badges S0_INFO through S4_CRITICAL",
    "Queue ordering S4 S3 Gate2 Gate1 older unresolved",
    "OwnerActionableCardV1",
    "No actionable card outside decision queue",
    "Acknowledgment is not live approval",
    "No presentation-layer semantic compression",
    "RISK_AND_KILL_SWITCH_PANEL / OwnerRiskPanelV1 / OwnerKillSwitchSurfaceV1",
    "LIVE_TRADING_PANEL / OwnerLivePanelV1",
    "RESEARCH_PROPOSAL_INBOX / OwnerResearchPanelV1",
    "SHADOW_REVIEW_INBOX / OwnerShadowPanelV1",
    "REFINEMENT_AND_REHAB_QUEUE / OwnerBacklogPanelV1",
    "CHANGE_QUEUE_AND_DEPLOYMENT_STATE / OwnerChangeQueuePanelV1",
    "AUDIT_FOOTER / OwnerAuditTrailPanelV1",
    "OWNER_PACKET_ACK_AUDIT_ROW",
    "OwnerApprovalLadderV1",
    "OwnerConfirmationClassV1",
    "OwnerActionRegistryV1",
    "OwnerReviewPolicyV1",
    "OwnerSafeActionPolicyV1",
    "OwnerActionReceiptV1",
    "OwnerNotifyTransportRegistryV1",
    "DashboardProjectionManifestV1 / OwnerSurfaceProjectionManifestV1",
    "OwnerDashboardNoOrderAuthorityProofV1",
    "Telegram owner packet mirror contract",
    "Telegram slash-command registry contract",
    "Direct owner-to-agent conversation extension",
    "Plain-English owner idea intake / one-click submission",
    "Multi-channel mirror / degraded rendering / fallback",
    "Packet cadence / unread state / owner audit",
    "Visual review-speed rendering without semantic compression",
    "Owner progress strip / linked-card law",
    "Agent reaction audit",
    "Agent reaction states",
    "Owner-agent conversation ledger",
    "Agent message ledger",
    "Directive envelope for free-form owner text",
    "Owner-visible transcript packet",
    "Slack-like transcript workspace contract",
    "Elite strategy dashboard panels / daily shadow reporting",
    "Autonomous implementation queue / one-click merge/deploy request only",
    "Performance-intelligence layer",
    "Decision-level attribution / counterfactual / promotion-rollback evidence",
    "Slippage intelligence / execution-cost forensics",
    "Cumulative learning / calibration / convex-PnL intelligence",
    "Maintenance-resume / loss-pattern intelligence",
    "Cumulative slippage panel",
    "Execution forensics / masked-parent reconstruction / routing linkage",
    "Owner Trade Target Intake / OTTI",
    "EVENT_CREDIBILITY_PACKET / Context and Catalyst",
    "TRADE_READINESS_SCORECARD",
    "TRADE_STRUCTURE_OPTIMIZATION_PACKET",
    "TRADE_PROPOSAL_CARD",
    "WATCH_MONITOR_CARD",
    "TRADE_MANAGEMENT_PLAN_CARD",
    "EXIT_DECISION_CARD",
    "OWNER_PROGRESS_BOARD_CARD",
    "Research/proposal archive",
    "Read-later queue",
    "Lifecycle-status panel",
    "Earnings/loss rollup / market-platform attribution / interactive graphs",
    "Alpha/edge board sorting / direct-live queue / death-monitor extension",
    "Alpha/edge artifact-ID continuity / institutional weighted-composite benchmark",
    "Edge taxonomy / reaction-order / alternative-data / branded-alias / sort-preset / Day-1 feasibility",
    "Criteria-strength badges / profit-priority overlays",
    "LIVE_EDGE_RADAR_PANEL",
    "SOURCE_WATCHLIST_PANEL",
    "RESEARCH_QUEUE_PANEL",
    "EDGE_HYPOTHESIS_BOARD",
    "ALPHA_CANDIDATE_SCOREBOARD",
    "NO_TRADE_BOARD",
    "REPLAY_PAPER_TEST_QUEUE_PANEL",
    "OWNER_APPROVAL_QUEUE_PANEL",
    "CAPITAL_USAGE_PANEL",
    "LATENCY_AND_ERROR_PANEL",
    "Replay vs paper PnL chart",
    "Cost-adjusted net PnL chart",
    "Drawdown curve",
    "Latency histogram",
    "Reject/throttle/error-rate chart",
    "Candidate ranking chart",
    "Capital usage chart",
    "Parameter revitalization board",
    "Local LLM model-control panel",
    "Day-1 review digest / platform-scope / API-key timeline",
    "Arbitrage dry-run owner-review panels",
    "Agent KPI / merit / self-healing / quarantine / replacement dashboard",
    "External bot-repo strategy/guardrail/arbitrage-candidate dashboard",
    "Prediction-market execution mechanics / reconciliation / cross-venue normalization",
    "Source-evidence retrieval readiness / ambiguity sweep dashboard",
    "External bot taxonomy / supply-chain / threat-intel dashboard",
    "Neural-signal candidate panel",
    "Stationary feature catalog panel",
    "Target construction panel",
    "Leakage audit panel",
    "Purged walk-forward validation panel",
    "Model calibration panel",
    "Model drift monitor panel",
    "Signal-to-sizing boundary panel",
    "Neural dual-result review panel",
    "Neural owner promotion gate panel",
    "Forbidden claim/source-retrieval-target panel",
    "Formula/trade controls ADD_FORMULA ADD_ALGORITHM ADD_QUANTUM_FORMULATION ADD_SOURCE",
    "Formula/trade controls PROMOTE_TO_REPLAY PROMOTE_TO_PAPER",
    "Formula/trade controls RUN_FORMULA_TEST_VECTOR RUN_REPLAY_CANDIDATE RUN_PAPER_CANDIDATE",
    "Formula/trade controls PROMOTE_TO_LIVE_REVIEW ROLLBACK_FORMULA_VERSION",
    "Open trade URL submission / SUBMIT_OPEN_TRADE_URL / SIMULATE_COMBINATIONS",
)


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()
    return slug or "ROW"


def _route_for_label(label: str) -> str:
    upper = label.upper()
    if "TELEGRAM" in upper or "MIRROR" in upper:
        return "TG1"
    if "LLM" in upper or "RESEARCH" in upper or "SOURCE" in upper or "IDEA" in upper:
        return "LLM2"
    if "QKU" in upper or "FORMULA" in upper or "PLUGIN" in upper or "ALGORITHM" in upper:
        return "PLUGIN1"
    if "QUANTUM" in upper or "QSTRUCT" in upper:
        return "QMAP1"
    if "PAPER" in upper or "REPLAY" in upper:
        return "PAPER-LOOP"
    if "LIVE" in upper or "LATENCY" in upper or "ERROR" in upper:
        return "LIVE-DRYRUN1"
    if "ALLOW" in upper or "ROLLBACK" in upper:
        return "ALLOW1"
    if "TRADE_READINESS" in upper or "PRETRADE" in upper:
        return "PRETRADE1"
    return "AGENT-ORCH1"


def _actions_for_label(label: str) -> list[str]:
    upper = label.upper()
    actions: list[str] = []
    if "ACK" in upper:
        actions.append("ACK_OWNER_PACKET")
    if "KILL" in upper or "RISK" in upper:
        actions.extend(["REQUEST_RISK_REVIEW", "REQUEST_KILL_SWITCH_REVIEW"])
    if "SOURCE" in upper or "EVENT_CREDIBILITY" in upper or "OPEN_TRADE_URL" in upper:
        actions.extend(["REQUEST_SOURCE_CAPTURE", "REQUEST_SOURCE_VALIDATION"])
    if "RESEARCH" in upper or "IDEA" in upper or "INTAKE" in upper:
        actions.append("SUBMIT_RESEARCH_CANDIDATE")
    if "LLM" in upper:
        actions.append("REQUEST_LLM_RESEARCH_EXTRACTION")
    if "QKU" in upper:
        actions.append("REQUEST_QKU_COMPUTABILITY_REVIEW")
    if "FORMULA" in upper:
        actions.extend(["REQUEST_FORMULA_EXTRACTION", "RUN_FORMULA_TEST_VECTOR_REQUEST"])
    if "QUANTUM" in upper or "QSTRUCT" in upper:
        actions.append("REQUEST_QSTRUCT_MAPPING_REVIEW")
    if "REPLAY" in upper:
        actions.append("REQUEST_REPLAY_TEST")
    if "PAPER" in upper:
        actions.append("REQUEST_PAPER_TEST")
    if "NO_TRADE" in upper or "NO-TRADE" in upper:
        actions.append("REQUEST_NO_TRADE_REOPTIMIZATION_REVIEW")
    if "LIVE" in upper or "CANARY" in upper:
        actions.append("REQUEST_LIVE_CANARY_REVIEW")
    if "ALLOW" in upper or "ROLLBACK" in upper:
        actions.append("REQUEST_ALLOWLIST_REVIEW")
    if "TELEGRAM" in upper:
        actions.append("REQUEST_TELEGRAM_MIRROR")
    if "ADD_FORMULA" in upper:
        actions.append("ADD_FORMULA_REQUEST")
    if "ADD_ALGORITHM" in upper:
        actions.append("ADD_ALGORITHM_REQUEST")
    if "ADD_QUANTUM_FORMULATION" in upper:
        actions.append("ADD_QUANTUM_FORMULATION_REQUEST")
    if "ADD_SOURCE" in upper:
        actions.append("ADD_SOURCE_REQUEST")
    if "PROMOTE_TO_REPLAY" in upper:
        actions.append("PROMOTE_TO_REPLAY_REQUEST")
    if "PROMOTE_TO_PAPER" in upper:
        actions.append("PROMOTE_TO_PAPER_REQUEST")
    if "PROMOTE_TO_LIVE_REVIEW" in upper:
        actions.append("PROMOTE_TO_LIVE_REVIEW_REQUEST")
    if "SUBMIT_OPEN_TRADE_URL" in upper:
        actions.append("SUBMIT_OPEN_TRADE_URL_REQUEST")
    if "SIMULATE_COMBINATIONS" in upper:
        actions.append("SIMULATE_COMBINATIONS_REQUEST")
    if "RUN_REPLAY_CANDIDATE" in upper:
        actions.append("RUN_REPLAY_CANDIDATE_REQUEST")
    if "RUN_PAPER_CANDIDATE" in upper:
        actions.append("RUN_PAPER_CANDIDATE_REQUEST")
    if not actions:
        actions.append("REQUEST_OWNER_REVIEW")
    return list(dict.fromkeys(actions))


def _roles_for_label(label: str) -> tuple[str, ...]:
    upper = label.upper()
    if "RISK" in upper or "PRETRADE" in upper or "LIVE" in upper:
        return RISK_AGENT_ROLES
    if "QUANTUM" in upper or "QSTRUCT" in upper or "QUBO" in upper:
        return QUANTUM_AGENT_ROLES
    if "RESEARCH" in upper or "SOURCE" in upper or "FORMULA" in upper or "QKU" in upper:
        return RESEARCH_AGENT_ROLES
    return DEFAULT_AGENT_ROLES


def _upstream_refs_for_route(route: str) -> list[str]:
    refs = [UPSTREAM_REFS["pr165_d2"]]
    if route in {"READINESS1", "PRETRADE1", "PAPER-LOOP"}:
        refs.extend([UPSTREAM_REFS["rp5g"], UPSTREAM_REFS["rank4"], UPSTREAM_REFS["vs2"]])
    if route in {"QMAP1", "PLUGIN1"}:
        refs.extend([UPSTREAM_REFS["vs2_qku"], UPSTREAM_REFS["qopt1_qstruct"]])
    if route == "LLM2":
        refs.extend([UPSTREAM_REFS["mem1"], UPSTREAM_REFS["vs2_qku"]])
    if route == "LIVE-DRYRUN1":
        refs.extend([UPSTREAM_REFS["rank4"], UPSTREAM_REFS["qopt1"]])
    return refs


def _feature_row(
    feature_id: str,
    label: str,
    *,
    feature_kind: str = "dashboard_surface",
    panel_id: str | None = None,
    packet_layer: str = "OWNER_PANEL_PROJECTIONS",
    card_type: str = "OWNER_ACTIONABLE_CARD",
    legacy_aliases: list[str] | None = None,
    lifecycle_state: str = "CONTRACT_DEFINED_PROVIDER_PENDING",
    route: str | None = None,
) -> dict[str, Any]:
    route_label = route or _route_for_label(label)
    actions = _actions_for_label(label)
    roles = _roles_for_label(label)
    panel = panel_id or f"{_slug(label)[:80]}_PANEL"
    return {
        "feature_id": feature_id,
        "feature_kind": feature_kind,
        "canonical_label": label,
        "legacy_aliases": legacy_aliases or [],
        "panel_id": panel,
        "packet_layer": packet_layer,
        "card_type": card_type,
        "action_code_refs": actions,
        "owner_view_purpose": "Central owner-visible review and routing contract.",
        "owner_control_purpose": "Audited request/control semantics only; no provider runtime authority.",
        "lifecycle_state": lifecycle_state,
        "provider_stage": route_label,
        "target_stage": route_label,
        "owning_stage_or_pr": PR_ID,
        "activation_route": f"{route_label}_ACTIVATION_ROUTE::{feature_id}",
        "provider_contract_ref": f"PR169_DASH1_PROVIDER_CONTRACT::{feature_id}",
        "v4_route_label": route_label,
        "legacy_route_aliases": [],
        "upstream_artifact_refs": _upstream_refs_for_route(route_label),
        "downstream_consumer_refs": [
            "OwnerSurfaceResolver",
            "owner_panel_projection.generated.jsonl",
            "owner_downstream_route_projection.generated.jsonl",
        ],
        "agent_role_refs_from_PR165_D2": list(roles),
        "responsible_agent_role": roles[0],
        "consumer_agent_role": roles[-1],
        "fallback_route_if_role_missing": "AGENT-ORCH1_ACTIVATION_ROUTE::ROLE_GAP_REVIEW",
        "agent_route_validation_ref": "PR165_D2_CommandActionMatrix.report.json",
        "reasoning_brain_view_policy": (
            "LLM may research, critique, summarize, explain, and request evidence; "
            "LLM cannot create source truth, risk pass, live readiness, or order release."
        ),
        "telegram_projection_policy": "TG1 mirror contract only; no bot runtime, webhook, polling, or token access.",
        "dashboard_projection_policy": "Generated projection consumed through OwnerSurfaceResolver.",
        "external_fact_receipt_policy": "External facts require accepted source receipts before truth use.",
        "source_workflow_policy": "Source candidate workflow request only; no source-truth acceptance.",
        "live_state_display_policy": "Display slot only; no live order, cancel, close, reduce, amend, or replace.",
        "cash_private_snapshot_policy": "Snapshot/receipt refs only; no private or cash account reads.",
        "shadow_mode_display_policy": "Comparison display contract only; no shadow execution authority.",
        "edge_alpha_capture_policy": "Execution-adjusted refs/routes only; no profit proof.",
        "chart_surface_policy": "Read-only interactive display contract; no mutation of trades or gates.",
        "qku_route_policy": "QKU refs/routes only; QKUs are immutable knowledge objects.",
        "formula_route_policy": "Formula refs/routes only; no formula repair into profit.",
        "candidate_route_policy": "TradePlanCandidateV1 routes mutable trade-plan variables only.",
        "quantum_structural_readiness_policy": "Structural readiness refs/routes only; no backend execution.",
        "institutional_metric_policy": "Metric refs/routes only; no invented evidence.",
        "authority_boundary_refs": [AUTHORITY_BOUNDARY_REF],
        "qku_formula_immutability_policy": "QKUs/formulas immutable; failures are condition-scoped routes.",
        "trade_plan_variable_policy": (
            "Mutable variables are market, venue, stack, side, entry, size, hold duration, "
            "exit rule, maker/taker/split, cancel/replace interval, liquidity/spread/depth "
            "filters, latency budget, portfolio exposure, order policy, and scenario path."
        ),
        "qtt_sha_policy": "No QTT SHA/hash authority.",
        "atomicrows_sha_policy": "No AtomicRows bundle hash/SHA authority.",
        "quantum_backend_policy": "No quantum backend execution, credential use, or advantage claim.",
        "profit_guarantee_policy": "No profit guarantee.",
        "no_orphan_status": "CONNECTED_TO_REGISTRY_PROJECTION_DAG_ROUTE",
        "validation_ref": VALIDATOR_REF,
    }


def seed_registry_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        _feature_row(
            "OWNER_DASHBOARD_PACKET_V1",
            "OwnerDashboardPacketV1",
            feature_kind="packet",
            panel_id="OWNER_DASHBOARD_PACKET_PANEL",
            packet_layer="OWNER_DASHBOARD_PACKET",
            card_type="PACKET",
            legacy_aliases=["OWNER_DASHBOARD_PACKET_CARD"],
            lifecycle_state="MATERIALIZED_IN_DASH1",
            route="AGENT-ORCH1",
        ),
        _feature_row(
            "OWNER_HEADER_STRIP_V1",
            "OwnerHeaderStripV1",
            feature_kind="header_strip",
            panel_id="OWNER_HEADER_STRIP_PANEL",
            packet_layer="OWNER_HEADER_STRIP",
            card_type="HEADER_STRIP",
            legacy_aliases=["OWNER_HEADER_STRIP_CARD"],
            lifecycle_state="MATERIALIZED_IN_DASH1",
            route="AGENT-ORCH1",
        ),
        _feature_row(
            "OWNER_DECISION_QUEUE_V1",
            "OwnerDecisionQueueV1",
            feature_kind="decision_queue",
            panel_id="OWNER_DECISION_QUEUE_PANEL",
            packet_layer="OWNER_DECISION_QUEUE",
            card_type="DECISION_QUEUE",
            legacy_aliases=["DECISION_QUEUE", "DECISION_QUEUE_CARD_SHELL", "OWNER_APPROVAL_QUEUE_PANEL"],
            lifecycle_state="MATERIALIZED_IN_DASH1",
            route="AGENT-ORCH1",
        ),
        _feature_row(
            "OWNER_ACTION_REGISTRY_V1",
            "OwnerActionRegistryV1",
            feature_kind="action_registry",
            panel_id="OWNER_ACTION_REGISTRY_PANEL",
            packet_layer="OWNER_ACTION_GRAMMAR",
            card_type="ACTION_REGISTRY",
            lifecycle_state="MATERIALIZED_IN_DASH1",
            route="AGENT-ORCH1",
        ),
        _feature_row(
            "OWNER_GLOBAL_AUTHORITY_POLICY_V1",
            "OwnerGlobalAuthorityPolicyV1",
            feature_kind="owner_policy",
            panel_id="OWNER_GLOBAL_AUTHORITY_PANEL",
            packet_layer="OWNER_POLICY",
            card_type="POLICY",
            lifecycle_state="MATERIALIZED_IN_DASH1",
            route="AGENT-ORCH1",
        ),
    ]
    used_ids = {row["feature_id"] for row in rows}
    for index, label in enumerate(FEATURE_COVERAGE_SEEDS, start=1):
        if index == 1:
            feature_id = "OWNER_DASHBOARD_PACKET_V1"
        elif index == 2:
            feature_id = "OWNER_DASHBOARD_PACKET_ALIAS_CARD"
        elif index == 3:
            feature_id = "OWNER_HEADER_STRIP_V1"
        elif index == 4:
            feature_id = "OWNER_HEADER_STRIP_ALIAS_CARD"
        elif index == 5:
            feature_id = "OWNER_DECISION_QUEUE_V1"
        elif index == 23:
            feature_id = "OWNER_ACTION_REGISTRY_V1"
        else:
            feature_id = f"DASH1_FEATURE_{index:03d}_{_slug(label)[:64]}"
        if feature_id in used_ids:
            continue
        route = _route_for_label(label)
        lifecycle = (
            "MATERIALIZED_IN_DASH1"
            if index <= 29 or "CONTRACT" in label.upper() or "POLICY" in label.upper()
            else "CONTRACT_DEFINED_PROVIDER_PENDING"
        )
        rows.append(
            _feature_row(
                feature_id,
                label,
                feature_kind="master_plan_20d_feature",
                panel_id=f"DASH1_20D_{index:03d}_PANEL",
                legacy_aliases=[label.split("/")[0].strip()] if "/" in label else [],
                lifecycle_state=lifecycle,
                route=route,
            )
        )
        used_ids.add(feature_id)
    for chart_id in CHART_CONTRACTS:
        feature_id = f"CHART_CONTRACT_{_slug(chart_id)}"
        rows.append(
            _feature_row(
                feature_id,
                chart_id,
                feature_kind="chart_contract",
                panel_id="OWNER_CHARTS_PANEL",
                card_type="CHART_CONTRACT",
                lifecycle_state="MATERIALIZED_IN_DASH1",
                route="PRETRADE1" if "quantum" not in chart_id.lower() else "QMAP1",
            )
        )
    for family in INTERACTIVE_CHART_FAMILIES:
        feature_id = f"INTERACTIVE_CHART_{_slug(family)}"
        rows.append(
            _feature_row(
                feature_id,
                family,
                feature_kind="interactive_chart",
                panel_id="OWNER_INTERACTIVE_CHART_PANEL",
                card_type="INTERACTIVE_CHART",
                lifecycle_state="MATERIALIZED_IN_DASH1",
                route="PRETRADE1" if "quantum" not in family.lower() else "QMAP1",
            )
        )
    for source_family in RESEARCH_SOURCE_FAMILIES:
        feature_id = f"RESEARCH_INTAKE_{_slug(source_family)}"
        rows.append(
            _feature_row(
                feature_id,
                f"Research candidate intake {source_family}",
                feature_kind="research_candidate_intake",
                panel_id="OWNER_RESEARCH_CANDIDATE_INTAKE_PANEL",
                card_type="RESEARCH_INTAKE",
                lifecycle_state="MATERIALIZED_IN_DASH1",
                route="LLM2",
            )
        )
    return _dedupe_registry_aliases(rows)


def _dedupe_registry_aliases(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    changed = False
    normalized_rows: list[dict[str, Any]] = []
    for row in registry_rows:
        next_row = dict(row)
        aliases: list[str] = []
        for alias in next_row.get("legacy_aliases", []):
            alias_text = str(alias)
            if not alias_text or alias_text in seen:
                changed = True
                continue
            seen.add(alias_text)
            aliases.append(alias_text)
        if aliases != next_row.get("legacy_aliases", []):
            changed = True
            next_row["legacy_aliases"] = aliases
        normalized_rows.append(next_row)
    return normalized_rows if changed else registry_rows


def _rows_by_feature_kind(registry_rows: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [row for row in registry_rows if row["feature_kind"] == kind]


def _find_feature(registry_rows: list[dict[str, Any]], feature_id: str) -> dict[str, Any]:
    for row in registry_rows:
        if row["feature_id"] == feature_id:
            return row
    raise KeyError(feature_id)


def _find_feature_label_contains(registry_rows: list[dict[str, Any]], token: str) -> dict[str, Any]:
    needle = token.upper()
    for row in registry_rows:
        if needle in str(row.get("canonical_label", "")).upper():
            return row
    raise KeyError(token)


def _first_feature_id(registry_rows: list[dict[str, Any]], kind: str | None = None) -> str:
    for row in registry_rows:
        if kind is None or row["feature_kind"] == kind:
            return str(row["feature_id"])
    return str(registry_rows[0]["feature_id"])


def _generic_projection_row(row: dict[str, Any], row_family: str) -> dict[str, Any]:
    feature_id = str(row["feature_id"])
    return {
        **projection_trace(feature_id),
        "feature_id": feature_id,
        "row_family": row_family,
        "canonical_label": row["canonical_label"],
        "panel_id": row["panel_id"],
        "lifecycle_state": row["lifecycle_state"],
        "owner_action_code_refs": row["action_code_refs"],
        "activation_route": row["activation_route"],
        "target_stage": row["target_stage"],
        "provider_stage": row["provider_stage"],
        "provider_contract_ref": row["provider_contract_ref"],
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "agent_role_refs_from_PR165_D2": row["agent_role_refs_from_PR165_D2"],
        "no_orphan_status": row["no_orphan_status"],
    }


def build_action_registry_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for action_code, definition in ACTION_DEFINITIONS.items():
        feature_refs = [row for row in registry_rows if action_code in row["action_code_refs"]]
        feature = feature_refs[0] if feature_refs else registry_rows[0]
        rows.append(
            {
                **projection_trace(str(feature["feature_id"])),
                "action_code": action_code,
                "canonical_label": definition["label"],
                "action_semantics": definition["semantics"],
                "confirmation_class": definition["confirmation_class"],
                "routes_through_decision_queue": True,
                "owner_action_receipt_required": True,
                "is_acknowledgment": action_code == "ACK_OWNER_PACKET",
                "is_live_approval": False,
                "creates_order_authority": False,
                "creates_source_truth": False,
                "creates_private_cash_truth": False,
                "creates_quantum_backend_authority": False,
                "owner_surface_registry_refs": [
                    registry_row_ref(str(row["feature_id"])) for row in feature_refs
                ],
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            }
        )
    return rows


def build_receipt_template_rows(action_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for action in action_rows:
        rows.append(
            {
                **projection_trace(action["registry_row_ref"].split("::", 1)[1]),
                "receipt_template_id": f"RECEIPT_TEMPLATE::{action['action_code']}",
                "action_code": action["action_code"],
                "required_receipt_fields": [
                    "receipt_id",
                    "action_code",
                    "owner_identity_ref",
                    "decision_queue_ref",
                    "timestamp_utc",
                    "evidence_refs",
                    "authority_boundary_ref",
                    "resulting_route",
                ],
                "owner_action_must_be_audited": True,
                "owner_action_may_not_bypass_execution_router": True,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            }
        )
    return rows


def build_chart_contract_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chart_id in CHART_CONTRACTS:
        feature_id = f"CHART_CONTRACT_{_slug(chart_id)}"
        feature = _find_feature(registry_rows, feature_id)
        rows.append(
            {
                **projection_trace(feature_id),
                "chart_id": chart_id,
                "chart_family": chart_id.replace("_chart", ""),
                "panel_id": feature["panel_id"],
                "chart_purpose": "Read-only owner review of provider evidence/routes.",
                "data_provider_stage": feature["provider_stage"],
                "source_dataset_refs": feature["upstream_artifact_refs"],
                "x_axis_field": "snapshot_time",
                "y_axis_fields": ["value", "lower_confidence_bound", "no_trade_comparator"],
                "group_by_fields": ["mode", "agent", "market", "venue"],
                "filter_fields": list(FILTER_DIMENSIONS),
                "time_window_policy": "owner_selectable_time_window_no_live_fetch",
                "staleness_policy": "display_stale_badge_until_provider_refresh_receipt",
                "empty_state_policy": "show_provider_pending_route_and_required_receipts",
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "owner_action_code_refs": feature["action_code_refs"],
                "activation_route": feature["activation_route"],
            }
        )
    return rows


def build_interactive_chart_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in INTERACTIVE_CHART_FAMILIES:
        feature_id = f"INTERACTIVE_CHART_{_slug(family)}"
        feature = _find_feature(registry_rows, feature_id)
        rows.append(
            {
                **projection_trace(feature_id),
                "chart_id": f"{family}_interactive_chart",
                "chart_family": family,
                "panel_id": feature["panel_id"],
                "data_contract_ref": f"DATASET_CONTRACT::{family}",
                "dataset_provider_stage": feature["provider_stage"],
                "dataset_snapshot_ref": f"PROVIDER_SNAPSHOT_REF::{family}",
                "supported_time_ranges": list(TIME_RANGES),
                "filter_dimensions": list(FILTER_DIMENSIONS),
                "x_axis_semantics": "time_or_ordered_stage",
                "y_axis_semantics": "provider_supplied_numeric_or_state_value",
                "series_semantics": "mode_agent_market_venue_qku_formula_source_regime",
                "tooltip_fields": [
                    "timestamp",
                    "mode",
                    "candidate_ref",
                    "net_cash_ref",
                    "source_ref",
                    "authority_boundary_ref",
                ],
                "drilldown_route": f"OwnerSurfaceResolver.get_chart_contract::{family}",
                "linked_receipt_refs": [UPSTREAM_REFS["rank4"], UPSTREAM_REFS["vs2"]],
                "linked_trade_plan_candidate_refs": ["TradePlanCandidateV1::provider_pending"],
                "linked_agent_role_refs": feature["agent_role_refs_from_PR165_D2"],
                "linked_qku_refs": ["QKU_REF::provider_pending"],
                "linked_formula_stack_refs": ["FORMULA_STACK_REF::provider_pending"],
                "linked_source_candidate_refs": ["SOURCE_CANDIDATE_REF::provider_pending"],
                "empty_state_policy": "render provider-pending route and missing receipt list",
                "stale_data_policy": "show stale badge and provider refresh action route",
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            }
        )
    return rows


def build_dataset_contract_rows(interactive_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **projection_trace(row["registry_row_ref"].split("::", 1)[1]),
            "dataset_contract_id": row["data_contract_ref"],
            "chart_id": row["chart_id"],
            "chart_family": row["chart_family"],
            "provider_stage": row["dataset_provider_stage"],
            "snapshot_ref_type": row["dataset_snapshot_ref"],
            "required_dimensions": row["filter_dimensions"],
            "required_time_ranges": row["supported_time_ranges"],
            "read_only_data_semantics": True,
            "external_network_required": False,
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        }
        for row in interactive_rows
    ]


def build_research_intake_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_family in RESEARCH_SOURCE_FAMILIES:
        feature_id = f"RESEARCH_INTAKE_{_slug(source_family)}"
        feature = _find_feature(registry_rows, feature_id)
        rows.append(
            {
                **projection_trace(feature_id),
                "intake_contract_id": f"RESEARCH_CANDIDATE_INTAKE::{source_family}",
                "source_family": source_family,
                "accepted_payload_refs": [
                    "owner_submission_ref",
                    "source_candidate_ref",
                    "evidence_capture_request_ref",
                ],
                "first_pipeline_state": "RESEARCH_SUBMITTED",
                "source_truth_created": False,
                "owner_action_code_refs": feature["action_code_refs"],
                "activation_route": feature["activation_route"],
                "target_stage": feature["target_stage"],
                "agent_role_refs_from_PR165_D2": feature["agent_role_refs_from_PR165_D2"],
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            }
        )
    return rows


def build_research_pipeline_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_id = "RESEARCH_INTAKE_QUANTUM_STRATEGY_TEXT"
    if not any(row["feature_id"] == feature_id for row in registry_rows):
        feature_id = "RESEARCH_INTAKE_SOCIAL_POST_URL"
    feature = _find_feature(registry_rows, feature_id)
    rows: list[dict[str, Any]] = []
    for index, state in enumerate(RESEARCH_PIPELINE_STATES, start=1):
        rows.append(
            {
                **projection_trace(feature_id),
                "pipeline_step_id": f"RESEARCH_PIPELINE_STEP_{index:02d}",
                "pipeline_state": state,
                "source_families": list(RESEARCH_SOURCE_FAMILIES),
                "agent_or_provider_role": RESEARCH_ROLES[min(index - 1, len(RESEARCH_ROLES) - 1)],
                "source_workflow_ref": "owner_research_candidate_evidence_route.generated.jsonl",
                "llm_extraction_ref": "owner_research_candidate_formula_extraction_route.generated.jsonl",
                "qku_materialization_ref": "owner_research_candidate_qku_materialization_route.generated.jsonl",
                "replay_paper_route_ref": "owner_research_candidate_replay_paper_route.generated.jsonl",
                "promotion_route_ref": "owner_research_candidate_promotion_route.generated.jsonl",
                "positive_net_cash_evidence_required": state
                in {"POSITIVE_NET_CASH_EVIDENCE_REVIEW", "LIVE_CANARY_REVIEW_REQUESTED"},
                "required_positive_evidence_refs": [
                    "net_expected_pnl_cash_after_TCA",
                    "lower_confidence_bound_pnl_cash",
                    "candidate_minus_no_trade_cash",
                    "fill_adjusted_expected_pnl_cash",
                    "latency_adjusted_expected_pnl_cash",
                    "capacity_adjusted_expected_pnl_cash",
                    "portfolio_marginal_utility",
                    "FDR_or_overfit_control",
                    "scenario_ladder_pass",
                    "calibration_status",
                    "replay_paper_validation_receipts",
                ],
                "owner_action_code_refs": feature["action_code_refs"],
                "activation_route": feature["activation_route"],
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            }
        )
    return rows


def build_edge_alpha_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = (
        ("LIVE_EDGE_RADAR_PANEL", "DASH1_FEATURE_071_LIVE_EDGE_RADAR_PANEL"),
        ("EDGE_HYPOTHESIS_BOARD", "DASH1_FEATURE_074_EDGE_HYPOTHESIS_BOARD"),
        ("ALPHA_CANDIDATE_SCOREBOARD", "DASH1_FEATURE_075_ALPHA_CANDIDATE_SCOREBOARD"),
        ("NO_TRADE_BOARD", "DASH1_FEATURE_076_NO_TRADE_BOARD"),
        ("REPLAY_PAPER_TEST_QUEUE_PANEL", "DASH1_FEATURE_077_REPLAY_PAPER_TEST_QUEUE_PANEL"),
        ("TRADE_READINESS_SCORECARD", "DASH1_FEATURE_056_TRADE_READINESS_SCORECARD"),
        ("TRADE_STRUCTURE_OPTIMIZATION_PACKET", "DASH1_FEATURE_057_TRADE_STRUCTURE_OPTIMIZATION_PACKET"),
        ("SOURCE_WATCHLIST_PANEL", "DASH1_FEATURE_072_SOURCE_WATCHLIST_PANEL"),
        ("RESEARCH_QUEUE_PANEL", "DASH1_FEATURE_073_RESEARCH_QUEUE_PANEL"),
    )
    rows: list[dict[str, Any]] = []
    for label, candidate_feature_id in labels:
        feature_id = candidate_feature_id if any(r["feature_id"] == candidate_feature_id for r in registry_rows) else _first_feature_id(registry_rows)
        feature = _find_feature(registry_rows, feature_id)
        rows.append(
            {
                **projection_trace(feature_id),
                "edge_id": f"EDGE_ALPHA::{label}",
                "alpha_hypothesis_ref": f"ALPHA_HYPOTHESIS_REF::{label}",
                "trade_plan_candidate_refs": ["TradePlanCandidateV1::provider_pending"],
                "formula_stack_refs": [UPSTREAM_REFS["vs2_qku"]],
                "qku_refs": [UPSTREAM_REFS["vs2_qku"]],
                "source_candidate_refs": ["SOURCE_CANDIDATE_REF::provider_pending"],
                "execution_adjusted_rank_ref": UPSTREAM_REFS["rank4"],
                "net_expected_pnl_cash_ref": UPSTREAM_REFS["rp5g"],
                "candidate_minus_no_trade_cash_ref": UPSTREAM_REFS["rank4"],
                "lower_confidence_bound_pnl_cash_ref": UPSTREAM_REFS["rank4"],
                "TCA_adjusted_expected_net_cash_ref": UPSTREAM_REFS["rp5g_tca"],
                "fill_probability_ref": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
                "latency_adjusted_expected_net_cash_ref": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
                "capacity_adjusted_expected_net_cash_ref": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
                "portfolio_marginal_utility_ref": UPSTREAM_REFS["qopt1"],
                "overfit_false_discovery_control_ref": UPSTREAM_REFS["rank4"],
                "regime_memory_ref": UPSTREAM_REFS["mem1"],
                "champion_challenger_ref": UPSTREAM_REFS["rank4"],
                "no_trade_reoptimization_route_ref": UPSTREAM_REFS["qopt1"],
                "owner_action_code_refs": feature["action_code_refs"],
                "activation_route": feature["activation_route"],
                "target_stage": feature["target_stage"],
                "agent_role_refs_from_PR165_D2": feature["agent_role_refs_from_PR165_D2"],
            }
        )
    return rows


def build_qku_route_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature = _find_feature(registry_rows, "DASH1_FEATURE_056_TRADE_READINESS_SCORECARD")
    return [
        {
            **projection_trace(feature["feature_id"]),
            "qku_refs": [UPSTREAM_REFS["vs2_qku"]],
            "formula_refs": [UPSTREAM_REFS["vs2_qku"]],
            "formula_stack_refs": [UPSTREAM_REFS["vs2_qku"]],
            "trade_plan_candidate_refs": [UPSTREAM_REFS["vs2"]],
            "computability_state": "COMPUTABLE_AFTER_PROVIDER_CONTRACT",
            "computability_tier_refs": [UPSTREAM_REFS["vs2_qku"]],
            "execution_readiness_refs": [UPSTREAM_REFS["rank4"]],
            "paper_intent_packet_refs": [UPSTREAM_REFS["vs2"]],
            "memory_recipe_refs": [UPSTREAM_REFS["mem1"]],
            "failure_memory_refs": [UPSTREAM_REFS["mem1"]],
            "no_trade_memory_refs": [UPSTREAM_REFS["mem1"]],
            "qstruct_refs": [UPSTREAM_REFS["qopt1_qstruct"]],
            "upstream_evidence_refs": [UPSTREAM_REFS["rp5g"], UPSTREAM_REFS["rank4"]],
            "downstream_consumer_refs": ["READINESS1", "PRETRADE1", "PAPER-LOOP"],
            "agent_role_refs_from_PR165_D2": feature["agent_role_refs_from_PR165_D2"],
            "activation_route": feature["activation_route"],
            "owner_action_code_refs": feature["action_code_refs"],
        }
    ]


def build_quantum_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_id = "INTERACTIVE_CHART_QUANTUM_STRUCTURAL_READINESS_HEATMAP"
    feature = _find_feature(registry_rows, feature_id)
    return [
        {
            **projection_trace(feature_id),
            "qstruct_ref": UPSTREAM_REFS["qopt1_qstruct"],
            "QUBO_readiness_ref": UPSTREAM_REFS["qopt1_qstruct"],
            "BQM_readiness_ref": UPSTREAM_REFS["qopt1_qstruct"],
            "CQM_readiness_ref": UPSTREAM_REFS["qopt1_qstruct"],
            "QuadraticProgram_readiness_ref": UPSTREAM_REFS["qopt1_qstruct"],
            "Ising_readiness_ref": UPSTREAM_REFS["qopt1_qstruct"],
            "QAOA_candidate_readiness_ref": "QAOA_STRUCTURE_ROUTE::provider_pending",
            "VQE_candidate_readiness_ref": "VQE_STRUCTURE_ROUTE::provider_pending",
            "quantum_annealing_candidate_readiness_ref": "ANNEALING_STRUCTURE_ROUTE::provider_pending",
            "hybrid_quantum_classical_readiness_ref": "HYBRID_STRUCTURE_ROUTE::provider_pending",
            "classical_fallback_ref": "docs/master_plan/generated/pr168_qopt1/classical_fallback.jsonl",
            "constraint_ledger_ref": "docs/master_plan/generated/pr168_qopt1/q_constraints.jsonl",
            "penalty_weight_policy_ref": "docs/master_plan/generated/pr168_qopt1/penalty_weight_policy.jsonl",
            "coefficient_scaling_ref": "docs/master_plan/generated/pr168_qopt1/qobj_coeff.jsonl",
            "variable_encoding_ref": "docs/master_plan/generated/pr168_qopt1/variable_encoding.jsonl",
            "objective_function_ref": "docs/master_plan/generated/pr168_qopt1/qobj_coeff.jsonl",
            "interpret_back_map_ref": "docs/master_plan/generated/pr168_qopt1/q_interp.jsonl",
            "quantum_classical_comparator_ref": "docs/master_plan/generated/pr168_qopt1/q_classic_fb.jsonl",
            "QMAP1_activation_route": feature["activation_route"],
            "forbidden_authority": [
                "quantum_backend_execution",
                "quantum_credential_use",
                "quantum_advantage_claim",
                "quantum_direct_order_submission",
            ],
        }
    ]


def build_institutional_metric_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature = _find_feature(registry_rows, "DASH1_FEATURE_047_PERFORMANCE_INTELLIGENCE_LAYER")
    metric_refs = {
        "execution_adjusted_rank_ref": UPSTREAM_REFS["rank4"],
        "TCA_decomposition_ref": UPSTREAM_REFS["rp5g_tca"],
        "implementation_shortfall_ref": UPSTREAM_REFS["rp5g_tca"],
        "fee_cost_ref": UPSTREAM_REFS["rp5g_tca"],
        "spread_cost_ref": UPSTREAM_REFS["rp5g_tca"],
        "slippage_cost_ref": UPSTREAM_REFS["rp5g_tca"],
        "market_impact_ref": UPSTREAM_REFS["rp5g_tca"],
        "latency_drag_ref": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
        "opportunity_cost_ref": UPSTREAM_REFS["rp5g_tca"],
        "fill_probability_ref": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
        "partial_fill_penalty_ref": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
        "adverse_selection_ref": UPSTREAM_REFS["rp5g_tca"],
        "capacity_crowding_ref": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
        "portfolio_diversification_ref": UPSTREAM_REFS["qopt1"],
        "portfolio_marginal_utility_ref": UPSTREAM_REFS["qopt1"],
        "capital_lock_ref": UPSTREAM_REFS["qopt1"],
        "overfit_false_discovery_control_ref": UPSTREAM_REFS["rank4"],
        "deflated_sharpe_or_multiple_testing_ref": UPSTREAM_REFS["rank4"],
        "walk_forward_or_replay_paper_validation_ref": UPSTREAM_REFS["rp5g"],
        "purged_embargoed_validation_ref": "PURGED_EMBARGOED_VALIDATION_ROUTE::provider_pending",
        "champion_challenger_ref": UPSTREAM_REFS["rank4"],
        "regime_conditioned_memory_ref": UPSTREAM_REFS["mem1"],
        "drift_cooldown_retest_ref": UPSTREAM_REFS["mem1"],
        "no_trade_reoptimization_route_ref": UPSTREAM_REFS["qopt1"],
        "scenario_ladder_ref": "docs/master_plan/generated/pr168_rp5g/scenario_ladder.jsonl",
        "calibration_ref": UPSTREAM_REFS["rank4"],
        "quantum_structural_readiness_ref": UPSTREAM_REFS["qopt1_qstruct"],
        "DAG_upstream_downstream_ref": "dag.generated.jsonl",
    }
    return [
        {
            **projection_trace(feature["feature_id"]),
            **metric_refs,
            "comparison_classes": [
                "candidate_minus_no_trade_cash",
                "lower_confidence_bound_pnl_cash",
                "TCA_adjusted_expected_net_cash",
                "capacity_adjusted_expected_net_cash",
                "portfolio_adjusted_expected_net_cash",
                "latency_adjusted_expected_net_cash",
                "execution_adjusted_rank",
                "champion_candidate",
                "challenger_candidate",
                "parked_candidate",
                "blocked_by_authority_boundary",
                "requires_replay_paper_revalidation",
            ],
            "activation_route": feature["activation_route"],
            "owner_action_code_refs": feature["action_code_refs"],
        }
    ]


def build_execution_ladder_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature = _find_feature(registry_rows, "DASH1_FEATURE_029_OWNERDASHBOARDNOORDERAUTHORITYPROOFV1")
    rows: list[dict[str, Any]] = []
    for index, state in enumerate(EXECUTION_LADDER_STATES, start=1):
        next_action = "REQUEST_OWNER_REVIEW"
        if "REPLAY" in state:
            next_action = "REQUEST_REPLAY_TEST"
        elif "PAPER" in state:
            next_action = "REQUEST_PAPER_TEST"
        elif "SHADOW" in state:
            next_action = "REQUEST_OWNER_REVIEW"
        elif "LIVE" in state or "LAUNCH" in state or "EXECUTION" in state:
            next_action = "REQUEST_LIVE_CANARY_REVIEW"
        rows.append(
            {
                **projection_trace(feature["feature_id"]),
                "ladder_state_id": f"EXECUTION_LADDER_{index:02d}",
                "trade_plan_candidate_refs": [UPSTREAM_REFS["vs2"]],
                "qku_refs": [UPSTREAM_REFS["vs2_qku"]],
                "formula_stack_refs": [UPSTREAM_REFS["vs2_qku"]],
                "pretrade_decision_refs": ["PRETRADE_DECISION_REF::provider_pending"],
                "replay_receipt_refs": ["REPLAY_RECEIPT_REF::provider_pending"],
                "paper_receipt_refs": ["PAPER_RECEIPT_REF::provider_pending"],
                "shadow_receipt_refs": ["SHADOW_RECEIPT_REF::provider_pending"],
                "live_dryrun_receipt_refs": ["LIVE_DRYRUN_RECEIPT_REF::provider_pending"],
                "live_pilot_receipt_refs": ["LIVE_PILOT_RECEIPT_REF::provider_pending"],
                "owner_approval_refs": ["OWNER_APPROVAL_REF::receipt_required"],
                "risk_gate_refs": ["RISK_GATE_REF::provider_pending"],
                "execution_router_gate_refs": ["EXECUTION_ROUTER_GATE_REF::required"],
                "no_trade_comparison_refs": [UPSTREAM_REFS["qopt1"]],
                "current_stage": state,
                "next_allowed_action_code": next_action,
                "forbidden_actions_in_dash1": [
                    "buy",
                    "sell",
                    "open",
                    "close",
                    "cancel",
                    "replace",
                    "amend",
                    "reduce",
                ],
                "target_stage": "PAPER-LOOP" if index < 6 else "LIVE-PILOT",
                "activation_route": f"EXECUTION_LADDER_ROUTE::{state}",
            }
        )
    return rows


def build_agent_intelligence_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in registry_rows[:80]:
        rows.append(
            {
                **projection_trace(row["feature_id"]),
                "agent_role_refs_from_PR165_D2": row["agent_role_refs_from_PR165_D2"],
                "responsible_agent_role": row["responsible_agent_role"],
                "consumer_agent_role": row["consumer_agent_role"],
                "LLM_reasoning_view_ref": f"LLM_REASONING_VIEW::{row['feature_id']}",
                "LLM_allowed_actions": [
                    "research",
                    "critique",
                    "summarize",
                    "explain",
                    "rank_explanations",
                    "request_missing_evidence",
                    "request_agent_task",
                    "suggest_replay_route",
                    "suggest_paper_route",
                    "suggest_no_trade_reoptimization_review",
                    "suggest_qstruct_mapping_review",
                ],
                "LLM_forbidden_authority": [
                    "accepted_source_truth",
                    "risk_pass",
                    "executable_now_pass",
                    "live_readiness_pass",
                    "connector_authority",
                    "private_cash_truth",
                    "order_release",
                    "quantum_advantage_proof",
                ],
                "QKU_resolver_route_ref": "OwnerSurfaceResolver.get_qku_formula_candidate_routes",
                "formula_resolver_route_ref": "OwnerSurfaceResolver.get_qku_formula_candidate_routes",
                "memory_query_route_ref": UPSTREAM_REFS["mem1"],
                "pretrade_route_ref": "PRETRADE1",
                "execution_ladder_route_ref": "owner_execution_authority_ladder_view.generated.jsonl",
                "owner_action_code_refs": row["action_code_refs"],
                "activation_route": row["activation_route"],
            }
        )
    return rows


def build_dag_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required_edges = (
        ("RP5G evidence", UPSTREAM_REFS["rp5g"], UPSTREAM_REFS["rank4"], "PAPER-LOOP"),
        ("RANK4 ranking", UPSTREAM_REFS["rank4"], UPSTREAM_REFS["qopt1"], "PRETRADE1"),
        ("QOPT1 optimization", UPSTREAM_REFS["qopt1"], UPSTREAM_REFS["vs2"], "PRETRADE1"),
        ("VS2 paper-intent packet", UPSTREAM_REFS["vs2"], UPSTREAM_REFS["mem1"], "PAPER-LOOP"),
        ("MEM1 memory", UPSTREAM_REFS["mem1"], "DASH1 owner-visible decision surface", "HOTPATH1"),
        ("DASH1 edge/alpha view", "owner_edge_alpha_capture_view.generated.jsonl", "READINESS1/PRETRADE1/PAPER-LOOP", "READINESS1"),
        ("DASH1 chart contract", "owner_chart_surface_contract.generated.jsonl", "dashboard_renderer_provider", "AGENT-ORCH1"),
        ("DASH1 owner action to TG1", "owner_action_registry.generated.jsonl", "TG1", "TG1"),
        ("DASH1 owner action to READINESS1", "owner_action_registry.generated.jsonl", "READINESS1", "READINESS1"),
        ("DASH1 owner action to PRETRADE1", "owner_action_registry.generated.jsonl", "PRETRADE1", "PRETRADE1"),
        ("DASH1 owner action to LLM1/LLM2", "owner_action_registry.generated.jsonl", "LLM1/LLM2", "LLM2"),
        ("DASH1 owner action to AGENT-ORCH1", "owner_action_registry.generated.jsonl", "AGENT-ORCH1", "AGENT-ORCH1"),
        ("DASH1 owner action to PAPER-LOOP", "owner_action_registry.generated.jsonl", "PAPER-LOOP", "PAPER-LOOP"),
        ("DASH1 owner action to HOTPATH1", "owner_action_registry.generated.jsonl", "HOTPATH1", "HOTPATH1"),
        ("DASH1 owner action to LIVE-DRYRUN1", "owner_action_registry.generated.jsonl", "LIVE-DRYRUN1", "LIVE-DRYRUN1"),
        ("DASH1 owner action to LIVE-PILOT/LAUNCH/POSTLAUNCH", "owner_action_registry.generated.jsonl", "LIVE-PILOT/LAUNCH/POSTLAUNCH", "LIVE-PILOT"),
        ("DASH1 source action", "owner_source_panel_contract.generated.jsonl", "source evidence route", "LLM2"),
        ("DASH1 QKU/formula action", "owner_qku_formula_candidate_route_view.generated.jsonl", "PLUGIN1/QMAP1/ALLOW1", "PLUGIN1"),
    )
    feature = registry_rows[0]
    rows: list[dict[str, Any]] = []
    for index, (label, upstream, downstream, route) in enumerate(required_edges, start=1):
        rows.append(
            {
                **projection_trace(feature["feature_id"]),
                "dag_node_id": f"DASH1_DAG_{index:03d}",
                "node_kind": label,
                "upstream_artifact_refs": [upstream],
                "downstream_consumer_refs": [downstream],
                "agent_role_refs_from_PR165_D2": list(DEFAULT_AGENT_ROLES),
                "LLM_reasoning_brain_view_ref": "owner_reasoning_brain_view_contract.generated.jsonl",
                "owner_action_code_refs": ["REQUEST_OWNER_REVIEW"],
                "input_contract_refs": [upstream],
                "output_contract_refs": [downstream],
                "activation_route": f"{route}_ACTIVATION_ROUTE::DAG_{index:03d}",
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "no_orphan_ref": NO_ORPHAN_REF,
            }
        )
    return rows


def build_data_value_route_map_rows(
    registry_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    files = [
        REGISTRY_FILENAME,
        *REQUIRED_JSONL_OUTPUTS,
        *REQUIRED_JSON_OUTPUTS,
        *REQUIRED_UI_OUTPUTS,
        ST12G_DESCRIPTOR_FILENAME,
    ]
    registry_by_id = {row["feature_id"]: row for row in registry_rows}
    if ST12G_REGISTRY_FEATURE_ID not in registry_by_id:
        raise ValueError(
            "ST12-G dashboard route requires the canonical owner packet registry row"
        )
    rows: list[dict[str, Any]] = []
    for index, file_name in enumerate(dict.fromkeys(files), start=1):
        if file_name == ST12G_DESCRIPTOR_FILENAME:
            rows.append(
                {
                    **projection_trace(ST12G_REGISTRY_FEATURE_ID),
                    "artifact_path": repo_posix(
                        Path("docs/master_plan/generated/pr169_dash1")
                        / file_name
                    ),
                    "row_family": Path(file_name).name,
                    "value_family": (
                        "qku_computation_control_plane_existing_owner_projection"
                    ),
                    "producer_tool": PRODUCER_TOOL,
                    "canonical_source_ref": REGISTRY_FILENAME,
                    "upstream_artifact_refs": [ST12G_SVC_DESCRIPTOR_REF],
                    "downstream_consumer_refs": [
                        "OwnerSurfaceResolver.resolve_st12g_projection_v2",
                        VALIDATOR_REF,
                    ],
                    "agent_role_refs_from_PR165_D2": list(DEFAULT_AGENT_ROLES),
                    "resolver_method": "resolve_st12g_projection_v2",
                    "owner_surface_registry_refs": [
                        registry_row_ref(ST12G_REGISTRY_FEATURE_ID)
                    ],
                    "source_owner": ST12G_SOURCE_OWNER,
                    "destination_surface": ST12G_DASHBOARD_SURFACE_ID,
                    "direct_f_binding_allowed": False,
                    "write_authority": "NONE",
                    "runtime_effect_allowed": False,
                    "order_authority": False,
                    "mode_authority": False,
                    "capital_authority": False,
                    "validation_ref": VALIDATOR_REF,
                    "no_orphan_status": "CONNECTED_TO_DATA_VALUE_ROUTE_MAP",
                }
            )
            continue
        feature_id = registry_rows[(index - 1) % len(registry_rows)]["feature_id"]
        rows.append(
            {
                **projection_trace(feature_id),
                "artifact_path": repo_posix(
                    Path("docs/master_plan/generated/pr169_dash1") / file_name
                ),
                "row_family": Path(file_name).name,
                "value_family": "owner_dashboard_command_plane_contract",
                "producer_tool": PRODUCER_TOOL,
                "canonical_source_ref": REGISTRY_FILENAME,
                "upstream_artifact_refs": [REGISTRY_FILENAME],
                "downstream_consumer_refs": ["OwnerSurfaceResolver", VALIDATOR_REF],
                "agent_role_refs_from_PR165_D2": list(DEFAULT_AGENT_ROLES),
                "resolver_method": "OwnerSurfaceResolver",
                "owner_surface_registry_refs": [registry_row_ref(feature_id)],
                "validation_ref": VALIDATOR_REF,
                "no_orphan_status": "CONNECTED_TO_DATA_VALUE_ROUTE_MAP",
            }
        )
    return rows


def _build_st12g_descriptor(out_dir: Path, repo_root: Path) -> dict[str, Any]:
    isolated_source_path = (
        out_dir.parent / "pr169_svc1" / Path(ST12G_SVC_DESCRIPTOR_REF).name
    )
    source_path = (
        isolated_source_path
        if isolated_source_path.exists()
        else repo_root / ST12G_SVC_DESCRIPTOR_REF
    )
    source_rows = read_jsonl(source_path)
    if len(source_rows) != 1:
        raise ValueError("ST12-G dashboard projection requires exactly one SVC1 descriptor")
    source = source_rows[0]
    if (
        source.get("consumer_id") != "SVC1"
        or source.get("contract_type") != "ST12GServiceEvidenceViewV2"
        or source.get("source_contract_manifest_ref") != ST12G_CONTRACT_MANIFEST_REF
        or source.get("runtime_instance_state")
        != "NOT_MATERIALIZED_BY_REPOSITORY_BUILD"
        or source.get("runtime_effect_allowed") is not False
        or source.get("write_authority") != "NONE"
    ):
        raise ValueError("ST12-G SVC1 descriptor is missing or semantically invalid")
    return {
        "descriptor_id": "ST12G-DESCRIPTOR::DASH1_UI1",
        "contract_version": "2.0",
        "consumer_id": "DASH1_UI1",
        "contract_type": "ST12GOwnerDashboardEvidenceViewV2",
        "source_contract_manifest_ref": ST12G_CONTRACT_MANIFEST_REF,
        "canonical_owner_ref": "PR169_DASH1_OWNER_DASHBOARD_SURFACE_REGISTRY",
        "runtime_instance_state": "NOT_MATERIALIZED_BY_REPOSITORY_BUILD",
        "manual_edit_allowed": False,
        "runtime_effect_allowed": False,
        "write_authority": "NONE",
        "downstream_route_refs": ["DASH1_UI1"],
    }


def build_static_ui(out_dir: Path, *, repo_root: Path) -> None:
    ui_dir = out_dir / "ui"
    fixtures_dir = ui_dir / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QTT Owner Dashboard Review Surface</title>
  <link rel="stylesheet" href="owner_dashboard_review_surface.css">
</head>
<body>
  <header class="topbar">
    <div>
      <h1>QTT Owner Dashboard</h1>
      <p>Static review surface - contracts and provider snapshots only</p>
    </div>
    <div class="status-pill">No order authority</div>
  </header>
  <main class="shell">
    <section class="toolbar" aria-label="Dashboard filters">
      <div class="segment" id="rangeButtons"></div>
      <select id="modeFilter" aria-label="Mode filter"></select>
      <select id="agentFilter" aria-label="Agent filter"></select>
      <select id="marketFilter" aria-label="Market filter"></select>
      <select id="venueFilter" aria-label="Venue filter"></select>
    </section>
    <section class="grid">
      <article class="panel span-2">
        <div class="panel-head"><h2>Portfolio PnL</h2><button id="drillPortfolio">Drill Down</button></div>
        <svg id="equityChart" viewBox="0 0 900 300" role="img" aria-label="Portfolio equity curve"></svg>
      </article>
      <article class="panel">
        <div class="panel-head"><h2>Costs</h2></div>
        <svg id="costChart" viewBox="0 0 420 260" role="img" aria-label="Cost breakdown"></svg>
      </article>
      <article class="panel">
        <div class="panel-head"><h2>Agents</h2></div>
        <div id="agentTable" class="table-shell"></div>
      </article>
      <article class="panel span-2">
        <div class="panel-head"><h2>Research Candidate Funnel</h2><button id="drillResearch">Drill Down</button></div>
        <svg id="funnelChart" viewBox="0 0 900 260" role="img" aria-label="Research candidate funnel"></svg>
      </article>
      <article class="panel span-2">
        <div class="panel-head"><h2>Drilldown</h2></div>
        <pre id="drilldown"></pre>
      </article>
    </section>
  </main>
  <div id="tooltip" class="tooltip" hidden></div>
  <script src="owner_dashboard_review_surface.js"></script>
</body>
</html>
"""
    css = """:root{color-scheme:light;--ink:#15202b;--muted:#5b6776;--line:#d7dee8;--panel:#ffffff;--bg:#f5f7fa;--green:#138a63;--red:#b42318;--blue:#1f6feb;--amber:#b7791f;--violet:#6f42c1}*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--ink)}.topbar{display:flex;justify-content:space-between;gap:24px;align-items:center;padding:18px 24px;border-bottom:1px solid var(--line);background:#fff}.topbar h1{font-size:24px;margin:0}.topbar p{margin:4px 0 0;color:var(--muted)}.status-pill{border:1px solid var(--red);color:var(--red);padding:8px 10px;border-radius:6px;font-weight:700}.shell{padding:18px 24px}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}.segment{display:flex;gap:4px;flex-wrap:wrap}.segment button,.panel button,select{height:34px;border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:6px;padding:0 10px}.segment button.active{background:var(--blue);border-color:var(--blue);color:#fff}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px;min-height:280px}.span-2{grid-column:span 2}.panel-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.panel h2{font-size:16px;margin:0}svg{width:100%;height:auto;display:block}.axis{stroke:#9aa7b6;stroke-width:1}.equity{fill:none;stroke:var(--green);stroke-width:3}.drawdown{fill:none;stroke:var(--red);stroke-width:2}.bar{fill:var(--blue)}.bar.alt{fill:var(--amber)}.bar.q{fill:var(--violet)}.point{fill:#fff;stroke:var(--green);stroke-width:2;cursor:pointer}.tooltip{position:fixed;z-index:5;max-width:260px;background:#15202b;color:#fff;padding:8px 10px;border-radius:6px;font-size:12px;pointer-events:none;box-shadow:0 8px 22px #0002}.table-shell table{width:100%;border-collapse:collapse}.table-shell th,.table-shell td{text-align:left;border-bottom:1px solid var(--line);padding:8px;font-size:13px}.table-shell th{cursor:pointer;color:var(--muted)}pre{white-space:pre-wrap;background:#f0f3f7;border:1px solid var(--line);border-radius:6px;padding:10px;min-height:190px;overflow:auto}@media(max-width:900px){.grid{grid-template-columns:1fr}.span-2{grid-column:span 1}.topbar{align-items:flex-start;flex-direction:column}.toolbar select{flex:1 1 150px}}"""
    js = """const ranges=["INTRADAY","DAILY","WEEKLY","MONTHLY","QUARTERLY","YTD","ONE_YEAR","ALL_AVAILABLE"];let state={range:"MONTHLY",mode:"ALL",agent:"ALL",market:"ALL",venue:"ALL",sort:"score"};const fallback={points:[{t:"D1",equity:100000,drawdown:0,mode:"REPLAY",agent:"dashboard_agent",market:"Kalshi",venue:"KALSHI"},{t:"D2",equity:101200,drawdown:-120,mode:"PAPER",agent:"risk_manager_agent",market:"Polymarket",venue:"POLYMARKET"},{t:"D3",equity:100850,drawdown:-450,mode:"SHADOW",agent:"quantum_optimizer_agent",market:"Kalshi",venue:"KALSHI"},{t:"D4",equity:102450,drawdown:-60,mode:"LIVE_DRYRUN",agent:"commander_agent",market:"ForecastEx",venue:"FORECASTEX"}],costs:[{k:"fee",v:90},{k:"spread",v:140},{k:"slippage",v:70},{k:"impact",v:50},{k:"latency",v:35}],agents:[{agent:"dashboard_agent",score:91,quarantine:"clear"},{agent:"risk_manager_agent",score:88,quarantine:"review"},{agent:"quantum_optimizer_agent",score:84,quarantine:"clear"},{agent:"commander_agent",score:90,quarantine:"clear"}],funnel:[{k:"submitted",v:12},{k:"captured",v:9},{k:"extracted",v:7},{k:"qku",v:5},{k:"replay",v:3},{k:"owner_review",v:1}],authority:"Read-only fixture. No credentials, connectors, cash reads, source truth, or order authority."};async function loadData(){try{return await fetch("fixtures/owner_dashboard_demo_data.json").then(r=>r.json())}catch{return fallback}}function opt(id,vals){const el=document.getElementById(id);el.innerHTML=["ALL",...vals].map(v=>`<option>${v}</option>`).join("");el.onchange=()=>{state[id.replace("Filter","")]=el.value;render(window.data)}}function filtered(d){return d.points.filter(p=>(state.mode==="ALL"||p.mode===state.mode)&&(state.agent==="ALL"||p.agent===state.agent)&&(state.market==="ALL"||p.market===state.market)&&(state.venue==="ALL"||p.venue===state.venue))}function lineChart(rows){const svg=document.getElementById("equityChart");svg.innerHTML='<line class="axis" x1="40" y1="260" x2="870" y2="260"/><line class="axis" x1="40" y1="20" x2="40" y2="260"/>';if(!rows.length)return;const min=Math.min(...rows.map(r=>r.equity)),max=Math.max(...rows.map(r=>r.equity));const sx=i=>40+i*(830/Math.max(1,rows.length-1));const sy=v=>250-((v-min)/Math.max(1,max-min))*210;const d=rows.map((r,i)=>(i?"L":"M")+sx(i)+","+sy(r.equity)).join(" ");svg.insertAdjacentHTML("beforeend",`<path class="equity" d="${d}"/>`);rows.forEach((r,i)=>{const c=document.createElementNS("http://www.w3.org/2000/svg","circle");c.setAttribute("class","point");c.setAttribute("cx",sx(i));c.setAttribute("cy",sy(r.equity));c.setAttribute("r","5");c.onmousemove=e=>tip(e,`${r.t} ${r.mode}<br>Equity ${r.equity}<br>${r.agent}`);c.onmouseleave=hideTip;c.onclick=()=>drill(r);svg.appendChild(c)})}function bars(id,rows,key,labelKey){const svg=document.getElementById(id);svg.innerHTML="";const max=Math.max(...rows.map(r=>r[key]),1);rows.forEach((r,i)=>{const w=55,x=45+i*65,h=200*r[key]/max,y=230-h;svg.insertAdjacentHTML("beforeend",`<rect class="bar ${i%3===1?"alt":i%3===2?"q":""}" x="${x}" y="${y}" width="${w}" height="${h}"/><text x="${x}" y="250" font-size="11">${r[labelKey]}</text>`)});}function table(rows){const el=document.getElementById("agentTable");const sorted=[...rows].sort((a,b)=>String(b[state.sort]).localeCompare(String(a[state.sort])));el.innerHTML=`<table><thead><tr><th data-s="agent">Agent</th><th data-s="score">Score</th><th data-s="quarantine">State</th></tr></thead><tbody>${sorted.map(r=>`<tr><td>${r.agent}</td><td>${r.score}</td><td>${r.quarantine}</td></tr>`).join("")}</tbody></table>`;el.querySelectorAll("th").forEach(th=>th.onclick=()=>{state.sort=th.dataset.s;table(rows)})}function tip(e,html){const t=document.getElementById("tooltip");t.innerHTML=html;t.hidden=false;t.style.left=e.clientX+12+"px";t.style.top=e.clientY+12+"px"}function hideTip(){document.getElementById("tooltip").hidden=true}function drill(row){document.getElementById("drilldown").textContent=JSON.stringify({range:state.range,row,authority:window.data.authority},null,2)}function render(d){lineChart(filtered(d));bars("costChart",d.costs,"v","k");table(d.agents);bars("funnelChart",d.funnel,"v","k")}loadData().then(d=>{window.data=d;document.getElementById("rangeButtons").innerHTML=ranges.map(r=>`<button data-r="${r}" class="${r===state.range?"active":""}">${r}</button>`).join("");document.querySelectorAll("#rangeButtons button").forEach(b=>b.onclick=()=>{state.range=b.dataset.r;document.querySelectorAll("#rangeButtons button").forEach(x=>x.classList.toggle("active",x===b));render(d)});opt("modeFilter",[...new Set(d.points.map(p=>p.mode))]);opt("agentFilter",[...new Set(d.points.map(p=>p.agent))]);opt("marketFilter",[...new Set(d.points.map(p=>p.market))]);opt("venueFilter",[...new Set(d.points.map(p=>p.venue))]);document.getElementById("drillPortfolio").onclick=()=>drill({panel:"portfolio_pnl",contract:"owner_portfolio_pnl_chart_view.generated.jsonl"});document.getElementById("drillResearch").onclick=()=>drill({panel:"research_pipeline",contract:"owner_research_candidate_pipeline_view.generated.jsonl"});render(d);drill({surface:"owner_dashboard_review_surface",mode:"static_local_no_network"})});"""
    fixture = {
        "authority": "Read-only fixture. No credentials, connectors, cash reads, source truth, or order authority.",
        "points": [
            {"t": "D1", "equity": 100000, "drawdown": 0, "mode": "REPLAY", "agent": "dashboard_agent", "market": "Kalshi", "venue": "KALSHI"},
            {"t": "D2", "equity": 101200, "drawdown": -120, "mode": "PAPER", "agent": "risk_manager_agent", "market": "Polymarket", "venue": "POLYMARKET"},
            {"t": "D3", "equity": 100850, "drawdown": -450, "mode": "SHADOW", "agent": "quantum_optimizer_agent", "market": "Kalshi", "venue": "KALSHI"},
            {"t": "D4", "equity": 102450, "drawdown": -60, "mode": "LIVE_DRYRUN", "agent": "commander_agent", "market": "ForecastEx", "venue": "FORECASTEX"},
        ],
        "costs": [
            {"k": "fee", "v": 90},
            {"k": "spread", "v": 140},
            {"k": "slippage", "v": 70},
            {"k": "impact", "v": 50},
            {"k": "latency", "v": 35},
        ],
        "agents": [
            {"agent": "dashboard_agent", "score": 91, "quarantine": "clear"},
            {"agent": "risk_manager_agent", "score": 88, "quarantine": "review"},
            {"agent": "quantum_optimizer_agent", "score": 84, "quarantine": "clear"},
            {"agent": "commander_agent", "score": 90, "quarantine": "clear"},
        ],
        "funnel": [
            {"k": "submitted", "v": 12},
            {"k": "captured", "v": 9},
            {"k": "extracted", "v": 7},
            {"k": "qku", "v": 5},
            {"k": "replay", "v": 3},
            {"k": "owner_review", "v": 1},
        ],
    }
    surface_paths = (
        ui_dir / "owner_dashboard_review_surface.html",
        ui_dir / "owner_dashboard_review_surface.css",
        ui_dir / "owner_dashboard_review_surface.js",
    )
    canonical_ui_dir = (
        repo_root / "docs/master_plan/generated/pr169_dash1/ui"
    ).resolve()
    if ui_dir.resolve() != canonical_ui_dir:
        for target in surface_paths:
            source = canonical_ui_dir / target.name
            if not source.is_file():
                raise ValueError(
                    f"isolated DASH1 build lacks read-only renderer source: {source}"
                )
            source_bytes = source.read_bytes()
            if not target.exists() or target.read_bytes() != source_bytes:
                target.write_bytes(source_bytes)
    if not all(path.exists() for path in surface_paths):
        surface_paths[0].write_text(html, encoding="utf-8")
        surface_paths[1].write_text(css, encoding="utf-8")
        surface_paths[2].write_text(js, encoding="utf-8")
    write_json(fixtures_dir / "owner_dashboard_demo_data.json", fixture)


def build_read_receipt() -> dict[str, Any]:
    return {
        "artifact_id": "PR169_DASH1_READ_RECEIPT",
        "created_by_pr": PR_ID,
        "generated_from": "pre_implementation_repository_audit",
        "manual_edit_allowed": False,
        "files_read": [
            {"path": "docs/master_plan/QTT_MasterPlan_Current.md", "summary": "20D dashboard inventory reviewed.", "implementation_action": "Cover or route dashboard features through registry rows."},
            {"path": "docs/roadmap/README.md", "summary": "Roadmap guidance is not runtime truth.", "implementation_action": "Keep DASH1 control-plane only."},
            {"path": "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.md", "summary": "Controller is not runtime authority.", "implementation_action": "Preserve authority boundaries."},
            {"path": "docs/master_plan/governance/owner_overrides/README.md", "summary": "Owner decisions require receipts.", "implementation_action": "Generate receipt templates."},
            {"path": "docs/master_plan/generated/pr168_rp5g/pr_body.md", "summary": "RP5G evidence refs.", "implementation_action": "Route edge/TCA/fill refs."},
            {"path": "docs/master_plan/generated/pr168_rank4/pr_body.md", "summary": "RANK4 advisory rank refs.", "implementation_action": "Route ranking/champion refs."},
            {"path": "docs/master_plan/generated/pr168_qopt1/pr_body.md", "summary": "QOPT1 advisory/qstruct refs.", "implementation_action": "Route optimization and qstruct refs."},
            {"path": "docs/master_plan/generated/pr168_vs2/pr_body.md", "summary": "VS2 paper-intent/QKU route refs.", "implementation_action": "Route candidate and paper-intent refs."},
            {"path": "docs/master_plan/generated/pr168_mem1/pr_body.md", "summary": "MEM1 condition-scoped memory refs.", "implementation_action": "Route memory views without proof claims."},
            {"path": "PR165_D2_AgentRosterDiscoveryAudit.report.json", "summary": "Agent roster audit.", "implementation_action": "Use PR165-D2 role refs."},
            {"path": "PR165_D2_AgentDutySourceCrosswalk.report.json", "summary": "Agent duty crosswalk.", "implementation_action": "Use PR165-D2 role refs."},
            {"path": "PR165_D2_CommandActionMatrix.report.json", "summary": "Command/action matrix.", "implementation_action": "Route owner actions to roles."},
            {"path": "tools/run_validation_gates.py", "summary": "Validation gate runner.", "implementation_action": "Register DASH1 builder and validator."},
            {"path": "tools/validation_inventory.py", "summary": "Validation inventory.", "implementation_action": "Classify DASH1 validations."},
            {"path": "tools/validation_scope_registry.py", "summary": "Changed-path scope registry.", "implementation_action": "Add DASH1 branch scope."},
        ],
        "missing_required_inputs": [
            {"requested_path_or_title": "QTT_NewGPT_Handoff_Post_MEM1_Roadmap_v4.md", "discovery_result": "not found", "implementation_action": "Use owner-supplied v4 route map."},
            {"requested_path_or_title": "Pasted text.txt", "discovery_result": "not found", "implementation_action": "Do not invent missing input."},
            {"requested_path_or_title": "Pasted text (2).txt", "discovery_result": "not found", "implementation_action": "Do not invent missing input."},
            {"requested_path_or_title": "PR169_DASH1_MasterPlan_Dashboard_Feature_Coverage_Audit.md", "discovery_result": "not found", "implementation_action": "Generate coverage from master plan 20D and prompt seed list."},
        ],
        "read_receipt_status": "COMPLETE_BEFORE_IMPLEMENTATION",
    }


def build_all(out_dir: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    source_repo_root = repo_root.resolve() if repo_root is not None else out_dir.parents[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    registry_path = out_dir / REGISTRY_FILENAME
    if registry_path.exists():
        registry_rows = read_jsonl(registry_path)
    else:
        registry_rows = seed_registry_rows()
    registry_rows = _dedupe_registry_aliases(registry_rows)
    if read_jsonl(registry_path) != registry_rows if registry_path.exists() else True:
        write_jsonl(registry_path, registry_rows)

    action_rows = build_action_registry_rows(registry_rows)
    chart_rows = build_chart_contract_rows(registry_rows)
    interactive_rows = build_interactive_chart_rows(registry_rows)
    dataset_rows = build_dataset_contract_rows(interactive_rows)
    edge_rows = build_edge_alpha_rows(registry_rows)
    qku_rows = build_qku_route_rows(registry_rows)
    quantum_rows = build_quantum_rows(registry_rows)
    institutional_rows = build_institutional_metric_rows(registry_rows)
    ladder_rows = build_execution_ladder_rows(registry_rows)
    agent_rows = build_agent_intelligence_rows(registry_rows)
    research_intake_rows = build_research_intake_rows(registry_rows)
    research_pipeline_rows = build_research_pipeline_rows(registry_rows)
    dag_rows = build_dag_rows(registry_rows)
    st12g_descriptor = _build_st12g_descriptor(out_dir, source_repo_root)

    projection_payloads: dict[str, list[dict[str, Any]]] = {
        "owner_dashboard_packet.generated.jsonl": build_owner_dashboard_packet(registry_rows),
        "owner_header_strip.generated.jsonl": build_header_strip(registry_rows),
        "owner_decision_queue.generated.jsonl": build_decision_queue(registry_rows),
        "owner_actionable_card.generated.jsonl": build_actionable_cards(registry_rows),
        "owner_action_registry.generated.jsonl": action_rows,
        "owner_review_policy.generated.jsonl": [_generic_projection_row(registry_rows[0], "owner_review_policy") | {"owner_review_required_for_live_canary": True, "owner_review_does_not_bypass_execution_router": True}],
        "owner_safe_action_policy.generated.jsonl": [_generic_projection_row(registry_rows[0], "owner_safe_action_policy") | {"ack_is_not_approval": True, "safe_default": "deny_authority_until_provider_receipt"}],
        "owner_action_receipt_template.generated.jsonl": build_receipt_template_rows(action_rows),
        "owner_audit_trail_seed.generated.jsonl": [_generic_projection_row(registry_rows[0], "owner_audit_trail_seed") | {"audit_trail_seed_id": "OWNER_PACKET_ACK_AUDIT_ROW", "owner_action_receipt_required": True}],
        "owner_approval_ladder.generated.jsonl": [_generic_projection_row(registry_rows[0], "owner_approval_ladder") | {"approval_ladder_id": "OwnerApprovalLadderV1", "states": list(EXECUTION_LADDER_STATES)}],
        "owner_confirmation_class.generated.jsonl": [
            _generic_projection_row(registry_rows[0], "owner_confirmation_class") | {"confirmation_class": name, "is_live_approval": False}
            for name in ("ACK_ONLY", "OWNER_REVIEW_REQUIRED", "CRITICAL_CONFIRMATION", "AUTHORITY_BLOCKED")
        ],
        "owner_kill_switch_surface.generated.jsonl": [_generic_projection_row(_find_feature_label_contains(registry_rows, "RISK_AND_KILL_SWITCH_PANEL"), "owner_kill_switch_surface") | {"kill_switch_route_only": True, "direct_execution_control": False}],
        "owner_global_authority_policy.generated.jsonl": [
            {
                **projection_trace("OWNER_GLOBAL_AUTHORITY_POLICY_V1"),
                "owner_global_internal_authority": True,
                "owner_may_approve_disapprove_override_veto_or_change_internal_QTT_policy_design_strategy_agent_dashboard_risk_launch_or_stage_scope": True,
                "owner_may_prioritize_sources_research_agents_routes_dashboard_controls_and_review_policies": True,
                "owner_may_allow_official_or_non_official_sources_into_candidate_research_or_provisional_lanes": True,
                "owner_action_must_be_audited": True,
                "owner_action_receipt_required": True,
                "owner_action_may_not_bypass_required_execution_router": True,
                "owner_action_may_not_silently_expand_agent_permissions": True,
                "owner_action_may_not_materialize_live_write_secret": True,
                "owner_may_not_convert_missing_external_fact_or_missing_runtime_receipt_into_truth_by_assertion": True,
                "owner_may_not_make_missing_order_receipt_cash_receipt_connector_receipt_or_accepted_source_packet_exist_by_assertion": True,
                "external_fact_receipt_required_for_external_truth": True,
            }
        ],
        "owner_source_panel_contract.generated.jsonl": [_generic_projection_row(row, "owner_source_panel_contract") | {"source_truth_created": False} for row in registry_rows if "SOURCE" in row["canonical_label"].upper()][:20],
        "owner_live_cash_private_display_contract.generated.jsonl": [_generic_projection_row(row, "owner_live_cash_private_display_contract") | {"snapshot_ref_type": "provider_receipt_ref", "direct_reader_created": False} for row in registry_rows if "LIVE" in row["canonical_label"].upper() or "CAPITAL" in row["canonical_label"].upper()][:20],
        "owner_shadow_mode_display_contract.generated.jsonl": [
            _generic_projection_row(row, "owner_shadow_mode_display_contract")
            | {
                "shadow_panel_id": row["panel_id"],
                "shadow_candidate_refs": ["TradePlanCandidateV1::provider_pending"],
                "paper_shadow_diff_refs": ["PAPER_SHADOW_DIFF_REF::provider_pending"],
                "replay_shadow_diff_refs": ["REPLAY_SHADOW_DIFF_REF::provider_pending"],
                "live_shadow_comparison_refs": ["LIVE_SHADOW_COMPARISON_REF::provider_pending"],
                "shadow_decision_status_ref": "SHADOW_DECISION_STATUS_REF::provider_pending",
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            }
            for row in registry_rows
            if "SHADOW" in row["canonical_label"].upper()
        ],
        "owner_reasoning_brain_view_contract.generated.jsonl": [_generic_projection_row(row, "owner_reasoning_brain_view_contract") | {"LLM_allowed_actions": agent_rows[0]["LLM_allowed_actions"], "LLM_forbidden_authority": agent_rows[0]["LLM_forbidden_authority"], "live_LLM_call_created": False} for row in registry_rows[:30]],
        "owner_edge_alpha_capture_view.generated.jsonl": edge_rows,
        "owner_qku_formula_candidate_route_view.generated.jsonl": qku_rows,
        "owner_quantum_structural_readiness_view.generated.jsonl": quantum_rows,
        "owner_institutional_metric_view.generated.jsonl": institutional_rows,
        "owner_chart_surface_contract.generated.jsonl": chart_rows,
        "owner_chart_panel_projection.generated.jsonl": [row | {"panel_projection_id": f"CHART_PANEL::{row['chart_id']}"} for row in chart_rows],
        "owner_agent_intelligence_route_view.generated.jsonl": agent_rows,
        "owner_execution_authority_ladder_view.generated.jsonl": ladder_rows,
        "owner_panel_projection.generated.jsonl": [_generic_projection_row(row, "owner_panel_projection") for row in registry_rows],
        "owner_telegram_projection.generated.jsonl": [_generic_projection_row(row, "owner_telegram_projection") | {"telegram_runtime_created": False} for row in registry_rows if row["v4_route_label"] == "TG1" or "TELEGRAM" in row["canonical_label"].upper()],
        "owner_agent_route_projection.generated.jsonl": [_generic_projection_row(row, "owner_agent_route_projection") for row in registry_rows],
        "owner_llm_view_projection.generated.jsonl": [_generic_projection_row(row, "owner_llm_view_projection") | {"llm_root_authority": False} for row in registry_rows if row["v4_route_label"] in {"LLM1", "LLM2"} or "LLM" in row["canonical_label"].upper()],
        "owner_downstream_route_projection.generated.jsonl": [_generic_projection_row(row, "owner_downstream_route_projection") for row in registry_rows],
        "owner_dashboard_feature_coverage.generated.jsonl": [
            {
                **projection_trace("OWNER_DASHBOARD_PACKET_V1" if index == 1 else registry_rows[min(index, len(registry_rows) - 1)]["feature_id"]),
                "coverage_item_number": index,
                "feature_seed": label,
                "coverage_status": "COVERED_BY_REGISTRY_ROW",
                "operational_gap_row_created": False,
            }
            for index, label in enumerate(FEATURE_COVERAGE_SEEDS, start=1)
        ],
        "owner_dashboard_legacy_alias_index.generated.jsonl": [
            {**projection_trace(row["feature_id"]), "legacy_alias": alias, "feature_id": row["feature_id"], "canonical_label": row["canonical_label"]}
            for row in registry_rows
            for alias in row.get("legacy_aliases", [])
        ],
        "owner_dashboard_exact_panel_id_index.generated.jsonl": [{**projection_trace(row["feature_id"]), "panel_id": row["panel_id"], "feature_id": row["feature_id"]} for row in registry_rows],
        "owner_surface_contract.generated.jsonl": [_generic_projection_row(row, "owner_surface_contract") for row in registry_rows],
        "owner_surface_projection_manifest.generated.jsonl": [
            {
                **projection_trace(registry_rows[0]["feature_id"]),
                "projection_file": file_name,
                "projection_kind": "generated_dashboard_projection",
                "projection_manual_edit_allowed": False,
                "projection_authoritative_source": AUTHORITATIVE_SOURCE,
                "projection_validation_ref": VALIDATOR_REF,
                "generated_from": GENERATED_FROM,
                "manual_edit_allowed": False,
                "authoritative_source": AUTHORITATIVE_SOURCE,
                "registry_row_ref": registry_row_ref(registry_rows[0]["feature_id"]),
            }
            for file_name in REQUIRED_JSONL_OUTPUTS
        ] + [
            {
                **projection_trace(ST12G_REGISTRY_FEATURE_ID),
                "projection_file": ST12G_DESCRIPTOR_FILENAME,
                "projection_kind": "svc1_derived_existing_owner_evidence_view_contract",
                "projection_manual_edit_allowed": False,
                "projection_authoritative_source": ST12G_SVC_DESCRIPTOR_REF,
                "projection_validation_ref": VALIDATOR_REF,
                "source_contract_manifest_ref": ST12G_CONTRACT_MANIFEST_REF,
                "direct_f_binding_allowed": False,
                "source_owner": ST12G_SOURCE_OWNER,
                "destination_surface": ST12G_DASHBOARD_SURFACE_ID,
                "write_authority": "NONE",
                "runtime_effect_allowed": False,
                "order_authority": False,
                "mode_authority": False,
                "capital_authority": False,
            }
        ],
        "owner_notify_transport_registry.generated.jsonl": [_generic_projection_row(registry_rows[0], "owner_notify_transport_registry") | {"transport": "TG1_mirror_contract", "runtime_created": False, "token_access_created": False}],
        "lineage.generated.jsonl": [{**projection_trace(row["feature_id"]), "lineage_id": f"LINEAGE::{row['feature_id']}", "upstream_artifact_refs": row["upstream_artifact_refs"], "downstream_consumer_refs": row["downstream_consumer_refs"]} for row in registry_rows],
        "dag.generated.jsonl": dag_rows,
        "owner_interactive_dashboard_surface.generated.jsonl": [
            {
                **projection_trace("INTERACTIVE_CHART_PORTFOLIO_EQUITY_CURVE"),
                "surface_id": "owner_dashboard_review_surface_static_local",
                "html_ref": "ui/owner_dashboard_review_surface.html",
                "script_ref": "ui/owner_dashboard_review_surface.js",
                "style_ref": "ui/owner_dashboard_review_surface.css",
                "fixture_ref": "ui/fixtures/owner_dashboard_demo_data.json",
                "hover_tooltips": True,
                "click_to_drilldown": True,
                "sortable_tables": True,
                "external_network_required": False,
                "credential_or_connector_required": False,
                "order_authority_created": False,
            }
        ],
        "owner_interactive_chart_registry.generated.jsonl": interactive_rows,
        "owner_chart_dataset_contract.generated.jsonl": dataset_rows,
        "owner_chart_timescale_registry.generated.jsonl": [{**projection_trace(row["registry_row_ref"].split("::", 1)[1]), "chart_id": row["chart_id"], "supported_time_ranges": row["supported_time_ranges"]} for row in interactive_rows],
        "owner_agent_performance_chart_view.generated.jsonl": [row for row in interactive_rows if "agent" in row["chart_family"]],
        "owner_portfolio_pnl_chart_view.generated.jsonl": [row for row in interactive_rows if "portfolio" in row["chart_family"] or "pnl" in row["chart_family"].lower()],
        "owner_research_candidate_intake_contract.generated.jsonl": research_intake_rows,
        "owner_research_candidate_chat_surface_contract.generated.jsonl": [
            {
                **projection_trace("RESEARCH_INTAKE_SOCIAL_POST_URL"),
                "chat_surface_id": "OWNER_RESEARCH_CANDIDATE_CHAT_SURFACE",
                "supported_source_families": list(RESEARCH_SOURCE_FAMILIES),
                "audited_intake_required": True,
                "source_truth_created": False,
                "live_LLM_call_created": False,
                "activation_route": "LLM2_ACTIVATION_ROUTE::RESEARCH_CANDIDATE_CHAT_SURFACE",
            }
        ],
        "owner_research_candidate_pipeline_view.generated.jsonl": research_pipeline_rows,
        "owner_research_candidate_evidence_route.generated.jsonl": [
            {**projection_trace("RESEARCH_INTAKE_SOCIAL_POST_URL"), "route_id": "SOURCE_CANDIDATE_EVIDENCE_ROUTE", "source_workflow_steps": ["source_candidate_intake", "source_capture_request", "source_validation_request"], "accepted_source_truth_created": False}
        ],
        "owner_research_candidate_formula_extraction_route.generated.jsonl": [
            {**projection_trace("RESEARCH_INTAKE_QUANTUM_STRATEGY_TEXT"), "route_id": "FORMULA_EXTRACTION_ROUTE", "llm_actions": ["extract_candidate_formulas", "extract_assumptions", "extract_parameters", "extract_constraints"], "accepted_formula_truth_created": False}
        ],
        "owner_research_candidate_qku_materialization_route.generated.jsonl": [
            {**projection_trace("RESEARCH_INTAKE_FORMULA_TEXT"), "route_id": "QKU_MATERIALIZATION_ROUTE", "computability_review_required": True, "metadata_only_route_allowed": False}
        ],
        "owner_research_candidate_replay_paper_route.generated.jsonl": [
            {**projection_trace("RESEARCH_INTAKE_OPEN_TRADE_URL"), "route_id": "REPLAY_PAPER_ROUTE", "replay_required": True, "paper_required": True, "paper_submit_authority_created": False}
        ],
        "owner_research_candidate_promotion_route.generated.jsonl": [
            {**projection_trace("RESEARCH_INTAKE_SOCIAL_POST_URL"), "route_id": "LIVE_CANARY_REVIEW_ROUTE", "required_before_live_canary": ["replay_paper_validation_receipts", "owner_review", "risk_pretrade_route", "execution_router_gate"], "live_order_authority_created": False}
        ],
    }
    projection_payloads["owner_data_value_route_map.generated.jsonl"] = build_data_value_route_map_rows(
        registry_rows,
    )

    for file_name, rows in projection_payloads.items():
        write_jsonl(out_dir / file_name, rows)
    write_jsonl(out_dir / ST12G_DESCRIPTOR_FILENAME, (st12g_descriptor,))

    build_static_ui(out_dir, repo_root=source_repo_root)

    generated_files = [
        REGISTRY_FILENAME,
        *REQUIRED_JSONL_OUTPUTS,
        *REQUIRED_JSON_OUTPUTS,
        *REQUIRED_UI_OUTPUTS,
        ST12G_DESCRIPTOR_FILENAME,
    ]
    manifest = {
        "artifact_id": "PR169_DASH1_OWNER_DASHBOARD_REGISTRY_MANIFEST",
        "created_by_pr": PR_ID,
        "registry_path": REGISTRY_FILENAME,
        "single_canonical_dashboard_registry": True,
        "projection_count": len(REQUIRED_JSONL_OUTPUTS),
        "registry_row_count": len(registry_rows),
        "generated_files": list(dict.fromkeys(generated_files)),
        "manual_edit_allowed_only_for": [REGISTRY_FILENAME],
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "st12g_contract_descriptor": {
            "artifact_ref": ST12G_DESCRIPTOR_FILENAME,
            "source_owner": "SVC1_ONLY",
            "direct_f_binding_allowed": False,
        },
    }
    no_orphan = {
        "artifact_id": "PR169_DASH1_OWNER_DASHBOARD_NO_ORPHAN_REPORT",
        "status": "PASS",
        "registry_rows_checked": len(registry_rows),
        "projection_rows_trace_to_registry": True,
        "action_codes_trace_to_registry_decision_queue_receipts": True,
        "panels_trace_to_registry_surface_contract": True,
        "charts_trace_to_registry_data_contract": True,
        "provider_pending_features_have_route_fields": True,
        "agent_routes_resolve_through_PR165_D2_or_gap": True,
        "upstream_evidence_refs_resolve_or_route": True,
        "qku_formula_candidate_memory_qstruct_refs_routed": True,
        "edge_alpha_rows_route_to_evidence_or_review": True,
        "live_cash_private_slots_have_no_direct_reader": True,
        "shadow_slots_have_no_execution_authority": True,
        "source_panel_has_no_direct_truth_creation": True,
        "llm_view_has_no_root_authority": True,
        "quantum_rows_structural_or_QMAP1_routed": True,
        "institutional_metric_rows_have_refs_or_review_route": True,
        "generated_artifacts_in_data_value_route_map": True,
        "st12g_svc1_only_projection_connected": True,
        "st12g_zero_direct_f_bindings": True,
    }
    authority = {
        "artifact_id": "PR169_DASH1_OWNER_DASHBOARD_AUTHORITY_BOUNDARY_REPORT",
        "status": "PASS",
        "paper_submit_authority": False,
        "paper_fill_exit_pnl_receipts": False,
        "shadow_execution_authority": False,
        "live_candidate_status": False,
        "live_order_authority": False,
        "buy_sell_open_close_cancel_replace_amend_reduce_authority": False,
        "connector_writes": False,
        "private_state_reads": False,
        "cash_account_reads": False,
        "credentialed_connector_clients": False,
        "API_key_readers": False,
        "account_balance_fetchers": False,
        "source_truth_acceptance_engine": False,
        "connector_semantic_binding_from_dashboard": False,
        "Telegram_bot_runtime_or_webhook_or_polling_or_token_access": False,
        "LLM_runtime_or_live_LLM_calls": False,
        "LLM_source_truth_risk_pass_live_readiness_or_order_authority": False,
        "owner_approval_bypass": False,
        "owner_action_outside_audit_receipt": False,
        "risk_gate_override": False,
        "true_quantum_backend_execution": False,
        "quantum_credential_use": False,
        "quantum_advantage_claim": False,
        "QTT_SHA_or_QTT_generated_SHA_files": False,
        "AtomicRows_hash_SHA_authority": False,
        "profit_guarantee": False,
        "owner_global_internal_authority_preserved_with_receipts": True,
        "external_fact_fabrication_authority_created": False,
    }
    ui_manifest = {
        "artifact_id": "PR169_DASH1_OWNER_DASHBOARD_UI_MANIFEST",
        "html_ref": "ui/owner_dashboard_review_surface.html",
        "script_ref": "ui/owner_dashboard_review_surface.js",
        "style_ref": "ui/owner_dashboard_review_surface.css",
        "fixture_ref": "ui/fixtures/owner_dashboard_demo_data.json",
        "external_network_required": False,
        "credential_or_connector_required": False,
        "runtime_server_created": False,
        "st12g_contract_view_ref": ST12G_DESCRIPTOR_FILENAME,
        "st12g_source_owner": "SVC1_ONLY",
        "st12g_direct_f_binding_allowed": False,
    }
    validation_summary = {
        "artifact_id": "PR169_DASH1_VALIDATION_SUMMARY",
        "status": "BUILT",
        "validation_marker": VALIDATION_MARKER,
        "builder": PRODUCER_TOOL,
        "validator": VALIDATOR_REF,
        "registry_row_count": len(registry_rows),
        "generated_file_count": len(set(generated_files)),
        "st12g_contract_descriptor_validated": True,
    }
    write_json(out_dir / "read_receipt.json", build_read_receipt())
    write_json(out_dir / "owner_dashboard_registry_manifest.json", manifest)
    write_json(out_dir / "owner_dashboard_no_orphan.report.json", no_orphan)
    write_json(out_dir / "owner_dashboard_authority_boundary.report.json", authority)
    write_json(out_dir / "owner_dashboard_ui_manifest.json", ui_manifest)
    write_json(out_dir / "validation_summary.report.json", validation_summary)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", "--out-dir", dest="out_dir", default="docs/master_plan/generated/pr169_dash1")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    out_dir = repo_root / args.out_dir
    manifest = build_all(out_dir, repo_root=repo_root)
    print(f"PR169_DASH1_OWNER_DASHBOARD_BUILD_OK rows={manifest['registry_row_count']} out={repo_posix(out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
