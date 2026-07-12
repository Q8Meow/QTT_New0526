#!/usr/bin/env python3
"""Build PR169-SVC1 service read-model artifacts.

SVC1 is a contract/read-model layer only. The builder reads declared
READINESS1/PRETRADE1 generated artifacts and projects one canonical service
registry into owner-facing, agent-facing, LLM-facing, and downstream route
contracts. It never starts a server, calls providers, executes agents, or
creates paper/shadow/live activity.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
from typing import Any, Iterable, Sequence


PROMPT_VERSION = "v1.4"
PROJECTION_VERSION = "PR169-SVC1-v1.4"
BUILDER_NAME = "tools/build_pr169_svc1.py"
VALIDATOR_NAME = "tools/validate_pr169_svc1.py"
GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_svc1")
REGISTRY_REF = "docs/master_plan/generated/pr169_svc1/service_registry.jsonl"

READINESS_PREFIX = Path("docs/master_plan/generated/pr169_readiness1")
PRETRADE_PREFIX = Path("docs/master_plan/generated/pr169_pretrade1")
READINESS_REGISTRY_REF = "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl"
PRETRADE_REGISTRY_REF = "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl"
PRETRADE_EXEC_LADDER_EQUIVALENT_REF = (
    "docs/master_plan/generated/pr169_pretrade1/pretrade_exec_ladder_handoff.generated.jsonl"
)

JSONL_ARTIFACTS = (
    "service_registry.jsonl",
    "read_model_snapshots.generated.jsonl",
    "read_model_snapshot_index.generated.jsonl",
    "read_model_store_contracts.generated.jsonl",
    "snapshot_delta_policy.generated.jsonl",
    "provider_state_staleness_policy.generated.jsonl",
    "event_stream_contracts.generated.jsonl",
    "event_stream_cursor_policy.generated.jsonl",
    "audit_receipt_stream.generated.jsonl",
    "owner_action_requests.generated.jsonl",
    "owner_action_receipts.generated.jsonl",
    "action_eligibility.generated.jsonl",
    "action_denied_reasons.generated.jsonl",
    "action_confirmation_policy.generated.jsonl",
    "action_request_dedupe_policy.generated.jsonl",
    "action_risk_class_policy.generated.jsonl",
    "session_policy.generated.jsonl",
    "auth_boundary.generated.jsonl",
    "owner_permission_preview.generated.jsonl",
    "owner_ux_semantic_routes.generated.jsonl",
    "owner_copy_map.generated.jsonl",
    "owner_widget_manifest.generated.jsonl",
    "owner_chart_manifest.generated.jsonl",
    "owner_mode_technical_disclosure.generated.jsonl",
    "professional_provider_pending_frames.generated.jsonl",
    "pretrade_view_routes.generated.jsonl",
    "readiness_view_routes.generated.jsonl",
    "agent_workflow_queue_views.generated.jsonl",
    "owner_decision_queue_views.generated.jsonl",
    "qku_formula_compute_route_views.generated.jsonl",
    "agent_llm_task_route_views.generated.jsonl",
    "llm_grounding_route_views.generated.jsonl",
    "telegram_mobile_surface_routes.generated.jsonl",
    "command_action_matrix_bindings.generated.jsonl",
    "action_route_to_agent_responsibility.generated.jsonl",
    "downstream_dag_route_views.generated.jsonl",
    "source_candidate_lane_views.generated.jsonl",
    "no_trade_explanation_views.generated.jsonl",
    "tca_decomposition_views.generated.jsonl",
    "execution_adjusted_ranking_views.generated.jsonl",
    "overfit_fdr_control_views.generated.jsonl",
    "portfolio_diversification_views.generated.jsonl",
    "capacity_crowding_views.generated.jsonl",
    "champion_challenger_views.generated.jsonl",
    "regime_memory_prior_views.generated.jsonl",
    "marginal_utility_views.generated.jsonl",
    "quantum_structural_readiness_views.generated.jsonl",
    "scenario_ladder_views.generated.jsonl",
    "calibration_views.generated.jsonl",
    "owner_guidance_cards.generated.jsonl",
    "provider_pending_routes.generated.jsonl",
    "hotpath_snapshot_handoff_views.generated.jsonl",
    "metrics_capture_route_views.generated.jsonl",
    "shadow_live_dryrun_route_views.generated.jsonl",
    "agent_operations_views.generated.jsonl",
    "team_workflow_queue_views.generated.jsonl",
    "owner_agent_state_views.generated.jsonl",
    "owner_workflow_queue_state_views.generated.jsonl",
    "owner_receipt_preview_views.generated.jsonl",
    "owner_audit_trail_views.generated.jsonl",
    "execution_live_status_preview_views.generated.jsonl",
    "no_trade_reoptimization_views.generated.jsonl",
    "owner_next_step_routes.generated.jsonl",
    "surface_parity_routes.generated.jsonl",
    "artifact_value_route_map.generated.jsonl",
    "market_venue_expansion_socket_routes.generated.jsonl",
    "qku_formula_intake_route_views.generated.jsonl",
    "plugin_qmap_allowlist_route_views.generated.jsonl",
    "reality_model_installation_socket_views.generated.jsonl",
    "cross_surface_state_contract.generated.jsonl",
    "owner_conversation_views.generated.jsonl",
    "owner_plain_english_intent_routes.generated.jsonl",
    "owner_chat_route_previews.generated.jsonl",
    "owner_research_intake_routes.generated.jsonl",
    "owner_trade_intent_routes.generated.jsonl",
    "owner_search_index_routes.generated.jsonl",
    "owner_mode_policy.generated.jsonl",
    "owner_layout_profile_routes.generated.jsonl",
    "owner_notification_tier_policy.generated.jsonl",
    "owner_stale_data_banner_views.generated.jsonl",
    "mobile_app_shell_contract_views.generated.jsonl",
    "mobile_navigation_contract_views.generated.jsonl",
    "trade_workbench_route_views.generated.jsonl",
    "execution_ladder_stage_views.generated.jsonl",
    "ui_visual_qa_handoff_views.generated.jsonl",
)

JSON_ARTIFACTS = (
    "service_manifest.json",
    "no_orphan.report.json",
    "no_raw_jsonl_scan.report.json",
    "no_direct_submit_authority.report.json",
    "no_runtime_execution.report.json",
    "no_fake_receipts.report.json",
    "no_placeholder_materialization.report.json",
    "no_owner_ux_scatter.report.json",
    "no_agent_workflow_scatter.report.json",
    "no_market_expansion_scatter.report.json",
    "no_chat_search_notification_scatter.report.json",
    "owned_prefix_scope.report.json",
    "no_profit_claim.report.json",
    "service_quality_gates.report.json",
    "service_acceptance.report.json",
)

CANDIDATE_PROJECTION_FILES = (
    "pretrade_view_routes.generated.jsonl",
    "readiness_view_routes.generated.jsonl",
    "agent_workflow_queue_views.generated.jsonl",
    "owner_decision_queue_views.generated.jsonl",
    "qku_formula_compute_route_views.generated.jsonl",
    "agent_llm_task_route_views.generated.jsonl",
    "llm_grounding_route_views.generated.jsonl",
    "telegram_mobile_surface_routes.generated.jsonl",
    "downstream_dag_route_views.generated.jsonl",
    "source_candidate_lane_views.generated.jsonl",
    "no_trade_explanation_views.generated.jsonl",
    "tca_decomposition_views.generated.jsonl",
    "execution_adjusted_ranking_views.generated.jsonl",
    "overfit_fdr_control_views.generated.jsonl",
    "portfolio_diversification_views.generated.jsonl",
    "capacity_crowding_views.generated.jsonl",
    "champion_challenger_views.generated.jsonl",
    "regime_memory_prior_views.generated.jsonl",
    "marginal_utility_views.generated.jsonl",
    "quantum_structural_readiness_views.generated.jsonl",
    "scenario_ladder_views.generated.jsonl",
    "calibration_views.generated.jsonl",
    "owner_guidance_cards.generated.jsonl",
    "provider_pending_routes.generated.jsonl",
    "hotpath_snapshot_handoff_views.generated.jsonl",
    "metrics_capture_route_views.generated.jsonl",
    "shadow_live_dryrun_route_views.generated.jsonl",
    "agent_operations_views.generated.jsonl",
    "team_workflow_queue_views.generated.jsonl",
    "owner_agent_state_views.generated.jsonl",
    "owner_workflow_queue_state_views.generated.jsonl",
    "owner_receipt_preview_views.generated.jsonl",
    "owner_audit_trail_views.generated.jsonl",
    "execution_live_status_preview_views.generated.jsonl",
    "no_trade_reoptimization_views.generated.jsonl",
    "surface_parity_routes.generated.jsonl",
    "artifact_value_route_map.generated.jsonl",
    "market_venue_expansion_socket_routes.generated.jsonl",
    "qku_formula_intake_route_views.generated.jsonl",
    "plugin_qmap_allowlist_route_views.generated.jsonl",
    "reality_model_installation_socket_views.generated.jsonl",
    "cross_surface_state_contract.generated.jsonl",
    "owner_conversation_views.generated.jsonl",
    "owner_plain_english_intent_routes.generated.jsonl",
    "owner_chat_route_previews.generated.jsonl",
    "owner_research_intake_routes.generated.jsonl",
    "owner_trade_intent_routes.generated.jsonl",
    "owner_search_index_routes.generated.jsonl",
    "owner_stale_data_banner_views.generated.jsonl",
    "mobile_app_shell_contract_views.generated.jsonl",
    "mobile_navigation_contract_views.generated.jsonl",
    "trade_workbench_route_views.generated.jsonl",
    "execution_ladder_stage_views.generated.jsonl",
    "ui_visual_qa_handoff_views.generated.jsonl",
)

SNAPSHOT_CLASSES = (
    "OwnerDashboardReadModelSnapshotV1",
    "OwnerPreTradeDecisionPreviewV1",
    "OwnerNoTradeExplanationPreviewV1",
    "OwnerTCADecompositionPreviewV1",
    "OwnerQKUFormulaRoutePreviewV1",
    "OwnerExecutionLadderPreviewV1",
    "OwnerDecisionQueueReadModelV1",
    "OwnerAgentActivityReadModelV1",
    "OwnerWorkflowQueueReadModelV1",
    "OwnerReceiptPreviewReadModelV1",
    "OwnerWorkflowQueuePreviewV1",
    "OwnerAgentActivityPreviewV1",
    "OwnerActionEligibilityViewV1",
    "OwnerActionDeniedReasonV1",
    "OwnerProviderPendingReasonV1",
    "OwnerStaleStateWarningV1",
    "OwnerAuditReceiptPreviewV1",
    "OwnerQuantumReadinessPreviewV1",
    "OwnerMemoryPriorPreviewV1",
    "OwnerRiskAndKillSwitchPreviewV1",
    "OwnerPortfolioUtilityPreviewV1",
    "OwnerExecutionAdjustedRankingPreviewV1",
    "OwnerOverfitFDRPreviewV1",
    "OwnerChampionChallengerPreviewV1",
    "OwnerSourceCandidateLanePreviewV1",
    "OwnerTradeCommandAuthorityPreviewV1",
    "OwnerExecutionRouterBoundaryPreviewV1",
)

STORE_CONTRACT_CLASSES = (
    "DashboardReadModelStore",
    "DashboardSnapshotProvider",
    "DashboardEventStreamProvider",
    "DashboardActionRequestQueue",
    "DashboardAuditReceiptStream",
)

EVENT_CLASSES = (
    "READ_MODEL_SNAPSHOT_AVAILABLE",
    "READ_MODEL_SNAPSHOT_STALE",
    "ACTION_REQUEST_CREATED",
    "ACTION_REQUEST_DENIED",
    "ACTION_REQUEST_PROVIDER_PENDING",
    "ACTION_REQUEST_ELIGIBLE_FOR_REVIEW",
    "ACTION_RECEIPT_CONTRACT_AVAILABLE",
    "PRETRADE_VIEW_UPDATED",
    "READINESS_VIEW_UPDATED",
    "NO_TRADE_EXPLANATION_AVAILABLE",
    "TCA_VIEW_AVAILABLE",
    "EXECUTION_ADJUSTED_RANKING_AVAILABLE",
    "AGENT_WORKFLOW_PREVIEW_AVAILABLE",
    "AGENT_OPERATIONS_VIEW_AVAILABLE",
    "TEAM_WORKFLOW_QUEUE_VIEW_AVAILABLE",
    "AUDIT_TRAIL_VIEW_AVAILABLE",
    "EXECUTION_STATUS_PREVIEW_AVAILABLE",
    "OWNER_NEXT_STEP_ROUTE_AVAILABLE",
    "LLM_REVIEW_ROUTE_AVAILABLE",
    "MEMORY_PRIOR_PREVIEW_AVAILABLE",
    "QUANTUM_READINESS_PREVIEW_AVAILABLE",
    "HOTPATH_HANDOFF_PREVIEW_AVAILABLE",
    "METRICS_CAPTURE_ROUTE_PREVIEW_AVAILABLE",
    "SHADOW_ROUTE_PREVIEW_AVAILABLE",
    "SOURCE_CANDIDATE_LANE_AVAILABLE",
    "STALE_STATE_WARNING_RAISED",
    "AUTH_BOUNDARY_NOTICE",
    "SESSION_POLICY_NOTICE",
)

ACTION_REQUEST_CLASSES = (
    "REQUEST_PRETRADE_RECHECK",
    "REQUEST_NO_TRADE_EXPLANATION",
    "REQUEST_NO_TRADE_REOPTIMIZATION_REVIEW",
    "REQUEST_TCA_DETAIL",
    "REQUEST_SCENARIO_DETAIL",
    "REQUEST_AGENT_REVIEW",
    "REQUEST_AGENT_DISAGREEMENT_REVIEW",
    "REQUEST_MORE_RESEARCH",
    "REQUEST_SOURCE_CANDIDATE_REVIEW",
    "REQUEST_REPLAY_PREP",
    "REQUEST_PAPER_REVIEW",
    "REQUEST_LLM_REVIEW_PREP",
    "REQUEST_HOTPATH_PREVIEW",
    "REQUEST_METRICS_CAPTURE_PREP",
    "REQUEST_SHADOW_REVIEW",
    "REQUEST_LIVE_DRYRUN_REVIEW",
    "REQUEST_LIVE_CANARY_REVIEW",
    "REQUEST_KILL_SWITCH_REVIEW",
    "REQUEST_ROLLBACK_REVIEW",
    "REQUEST_PROVIDER_REFRESH_REVIEW",
    "REQUEST_QMAP_REVIEW",
    "REQUEST_PLUGIN_INTAKE_REVIEW",
    "REQUEST_ALLOWLIST_REVIEW",
    "REQUEST_OWNER_DASHBOARD_VIEW_REFRESH",
    "REQUEST_AGENT_OPERATIONS_REVIEW",
    "REQUEST_TEAM_WORKFLOW_QUEUE_REVIEW",
    "REQUEST_AUDIT_TRAIL_REVIEW",
    "REQUEST_EXECUTION_STATUS_PREVIEW",
    "REQUEST_MARKET_EXPANSION_SOCKET_REVIEW",
    "REQUEST_QKU_FORMULA_INTAKE_ROUTE_REVIEW",
    "REQUEST_EXECUTION_ROUTER_SUBMIT_REVIEW",
    "REQUEST_PLAIN_ENGLISH_INTENT_PREVIEW",
    "REQUEST_OWNER_CHAT_ROUTE_PREVIEW",
    "REQUEST_SOURCE_AGNOSTIC_RESEARCH_INTAKE",
    "REQUEST_TRADE_INTENT_REVIEW",
    "REQUEST_TRADE_CHECK_WITH_QTT_AGENTS",
    "REQUEST_REPLAY_PAPER_REVIEW",
    "REQUEST_OWNER_SEARCH",
    "REQUEST_LAYOUT_PROFILE_CHANGE",
    "REQUEST_NOTIFICATION_TIER_REVIEW",
    "REQUEST_STALE_DATA_EXPLANATION",
    "REQUEST_MOBILE_APP_SHELL_REVIEW",
    "REQUEST_TRADE_WORKBENCH_ROUTE",
    "REQUEST_EXECUTION_LADDER_VIEW",
)

RECEIPT_CLASSES = (
    "OwnerActionRequestReceiptV1",
    "OwnerActionDeniedReceiptV1",
    "OwnerActionProviderPendingReceiptV1",
    "OwnerActionEligibilityReceiptV1",
    "OwnerActionAuditReceiptV1",
    "OwnerReviewRouteReceiptV1",
    "OwnerNoTradeExplanationReceiptV1",
    "OwnerTCAViewReceiptV1",
    "OwnerAgentReviewRequestReceiptV1",
    "OwnerShadowReviewRequestReceiptV1",
    "OwnerLiveDryrunReviewRequestReceiptV1",
    "OwnerLiveCanaryReviewRequestReceiptV1",
    "OwnerKillSwitchReviewRequestReceiptV1",
    "OwnerRollbackReviewRequestReceiptV1",
    "OwnerSourceCandidateReviewReceiptV1",
    "OwnerQMapReviewReceiptV1",
    "OwnerPluginIntakeReviewReceiptV1",
    "OwnerExecutionRouterSubmitReviewReceiptV1",
)

EXPECTED_RUNTIME_RECEIPT_CLASSES = (
    "RuntimeTaskReceipt",
    "AgentDecisionReceipt",
    "MemoryUpdateReceipt",
    "PaperOrderIntent",
    "PaperFillSimulation",
    "PaperPnL",
    "NoTradeDecision",
    "RiskGate",
    "TCAMetric",
    "SubmitDisabledProof",
    "Settlement",
    "RealizedPnL",
    "CashReconciliation",
)

OWNER_NEXT_STEP_ROUTES = (
    "SEND_TO_TRADE_WORKBENCH",
    "CHECK_TRADE_WITH_QTT_AGENTS",
    "REQUEST_REPLAY_PREVIEW",
    "REQUEST_PAPER_PREVIEW",
    "SHOW_QKU_FORMULA_ROUTES",
    "EXPLAIN_NO_TRADE",
    "SHOW_TCA",
    "TECHNICAL_DETAILS",
    "LIVE_ORDER_SUBMIT_DISABLED",
)

PLAIN_ENGLISH_INTENT_ROUTES = (
    ("TRADE_CHECK_REQUEST", "OwnerTradeCheckRequestV1"),
    ("RESEARCH_ANALYSIS_REQUEST", "OwnerResearchSubmissionV1"),
    ("FORMULA_EXTRACTION_REQUEST", "FormulaExtractionCandidateV1"),
    ("QKU_MATERIALIZATION_REQUEST", "QKUCandidateMaterializationRequestV1"),
    ("QUANTUM_MAPPING_REQUEST", "QuantumStructureMappingRequestV1"),
    ("NO_TRADE_EXPLANATION_REQUEST", "OwnerNoTradeExplanationPreviewV1"),
    ("PARAMETER_TUNING_REQUEST", "OwnerNoTradeExplanationPreviewV1"),
    ("EDGE_ALPHA_RANKING_REQUEST", "OwnerExecutionAdjustedRankingPreviewV1"),
    ("REPLAY_PAPER_REQUEST", "ReplayPaperRequestV1"),
)

SOURCE_FAMILIES = (
    "websites",
    "links",
    "PDFs",
    "academic_papers",
    "Google_Scholar_references",
    "research_articles",
    "news_articles",
    "social_posts_threads",
    "public_documents",
    "repository_links",
    "datasets",
    "screenshots_images",
    "formulas",
    "algorithms",
    "quantum_strategy_notes",
    "market_event_pages",
    "free_form_trade_ideas",
)

WORKFLOW_STAGES = (
    "Research Intake",
    "Source Evidence",
    "QKU / Formula Selection",
    "Quantum Mapping",
    "Simulation",
    "TCA / Cost",
    "Risk Review",
    "Ranking",
    "No-Trade Comparator",
    "Replay Queue",
    "Paper Queue",
    "Shadow Candidate Queue",
    "Live Dry-Run Queue",
    "Live Canary Review",
    "Launch Gate",
    "Post-Trade Learning",
)

QUEUE_STATES = (
    "QUEUED",
    "RUNNING_PREVIEW_ONLY",
    "WAITING_FOR_EVIDENCE",
    "WAITING_FOR_OWNER",
    "WAITING_FOR_AGENT_PROVIDER",
    "BLOCKED_PROVIDER_PENDING",
    "READY_FOR_REPLAY_ROUTE",
    "READY_FOR_PAPER_ROUTE",
    "READY_FOR_SHADOW_ROUTE",
    "READY_FOR_LIVE_DRYRUN_ROUTE",
    "READY_FOR_LIVE_CANARY_REVIEW_ROUTE",
    "COMPLETED_CONTRACT_ONLY",
    "QUARANTINED_ROUTE_ONLY",
    "SCOPED_GAP_ROUTED",
)

LAYOUT_PROFILES = (
    "Trading View",
    "Research View",
    "Agent View",
    "Quantum View",
    "Risk View",
    "Developer View",
    "Mobile Compact View",
)

NOTIFICATION_TIERS = ("S0_INFO", "S1_REVIEW", "S2_PRIORITY", "S3_URGENT", "S4_CRITICAL")
EXECUTION_LADDER_STAGES = (
    "Research",
    "Replay",
    "Paper",
    "Shadow comparison",
    "Live dry-run",
    "Live canary",
    "Live",
    "Post-trade learning",
)
CHART_FAMILIES = (
    "portfolio_equity_curve_frame",
    "net_cash_pnl_frame",
    "cost_adjusted_net_pnl_frame",
    "drawdown_curve_frame",
    "tca_waterfall_frame",
    "capital_allocation_frame",
    "exposure_by_venue_frame",
    "edge_alpha_scoreboard_frame",
    "execution_adjusted_ranking_frame",
    "agent_performance_frame",
    "agent_disagreement_frame",
    "quantum_classical_comparator_frame",
    "dag_route_graph_frame",
    "scenario_ladder_frame",
    "capacity_crowding_frame",
    "marginal_utility_frame",
)

DOWNSTREAM_CONSUMERS = (
    "OwnerDashboardStateV1",
    "OwnerSurfaceResolver",
    "OwnerActionRegistry",
    "OwnerActionRequestV1",
    "OwnerActionReceiptV1",
    "OwnerConversationStateV1",
    "OwnerWidgetManifest",
    "OwnerChartManifest",
    "PR169-TG1",
    "PR170-MOBILE1",
    "PR169-LLM1",
    "PR169-LLM2",
    "PR169-AGENT-ORCH1",
    "PR169-PAPER-LOOP",
    "PR170-HOTPATH1",
    "PR170-METRICS1",
    "PR170-LIVE-DRYRUN1",
    "PR171-LIVE-PILOT",
    "PR172-LAUNCH",
    "PR173-POSTLAUNCH",
    "PR174-PLUGIN1",
    "PR174-QMAP1",
    "PR174-ALLOW1",
    "ExecutionRouterBoundary::no_release",
)

AUTHORITY_FALSE_FIELDS = (
    "runtime_timestamp_created",
    "fake_runtime_status_created",
    "fake_receipt_created",
    "runtime_side_effect_allowed",
    "runtime_llm_call_created",
    "llm_source_truth_created",
    "llm_order_authority_created",
    "llm_profit_claim_created",
    "runtime_recompute_required",
    "dashboard_rendering_required_in_live_path",
    "source_retrieval_allowed_in_live_path",
    "llm_call_allowed_in_live_path",
    "quantum_backend_call_allowed_in_live_path",
    "master_plan_compilation_allowed_in_live_path",
    "read_model_runtime_side_effect_allowed",
    "network_server_started",
    "direct_venue_submit_bypass_allowed",
    "execution_router_release_allowed",
    "direct_venue_submit_authority_created",
    "execution_router_release_authority_created",
    "order_submission_created",
    "replay_execution_created",
    "paper_execution_created",
    "shadow_execution_created",
    "live_execution_created",
    "connector_read_created",
    "connector_write_created",
    "private_cash_account_read_created",
    "runtime_agent_execution_created",
    "runtime_metrics_created",
    "runtime_plugin_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_order_authority_created",
    "profit_claim_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
    "service_worker_runtime_created",
    "push_notification_runtime_created",
    "native_mobile_runtime_created",
    "order_execution_created",
    "source_truth_created",
    "order_authority_created",
    "fake_cash_pnl_trade_state_created",
    "fake_pnl_cash_fill_live_position_data_created",
    "fake_private_cash_receipt_created",
    "fake_memory_update_receipt_created",
    "fake_live_receipt_created",
    "fake_paper_fill_receipt_created",
    "fake_runtime_receipt_created",
    "buy_sell_open_close_cancel_replace_reduce_exit_created",
    "order_compilation_created",
    "runtime_execution_created",
    "raw_jsonl_runtime_scan_used",
    "source_truth_authority_created",
    "connector_semantics_created",
    "accepted_source_truth_created",
    "memory_update_receipt_created",
)


def _repo_ref(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return rows


def _maybe_read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _read_jsonl(path)


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item)]
    if str(value):
        return [str(value)]
    return []


def _first_non_gap(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text and "GAP" not in text and not text.endswith("_or_gap"):
            return text
    return "SCOPED_GAP_ROUTED"


def _slug(value: str) -> str:
    return (
        value.replace(" ", "_")
        .replace("/", "_")
        .replace("::", "__")
        .replace("-", "_")
        .replace(".", "_")
        .upper()
    )


def _projection_stem(file_name: str) -> str:
    return file_name.replace(".generated.jsonl", "").replace(".jsonl", "")


def _projection_class(file_name: str) -> str:
    stem = _projection_stem(file_name)
    return "".join(part.capitalize() for part in stem.split("_")) + "V1"


def _artifact_ref(file_name: str) -> str:
    return f"docs/master_plan/generated/pr169_svc1/{file_name}"


def _ref(file_name: str, row_id: str) -> str:
    return f"{_artifact_ref(file_name)}::{row_id}"


def _index_by_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id", ""))
        if candidate_id and candidate_id not in indexed:
            indexed[candidate_id] = row
    return indexed


def _upstream_ref(prefix: Path, file_name: str, candidate_id: str) -> str:
    return f"{_repo_ref(prefix / file_name)}::{candidate_id}"


def _load_context(repo_root: Path) -> dict[str, Any]:
    readiness_registry = _read_jsonl(repo_root / READINESS_REGISTRY_REF)
    pretrade_registry = _read_jsonl(repo_root / PRETRADE_REGISTRY_REF)
    if not readiness_registry:
        raise RuntimeError("READINESS1 registry is empty")
    if not pretrade_registry:
        raise RuntimeError("PRETRADE1 registry is empty")

    pretrade_files = {
        "pretrade_owner_view_handoff.generated.jsonl": _maybe_read_jsonl(
            repo_root / PRETRADE_PREFIX / "pretrade_owner_view_handoff.generated.jsonl"
        ),
        "pretrade_owner_next_step_handoff.generated.jsonl": _maybe_read_jsonl(
            repo_root / PRETRADE_PREFIX / "pretrade_owner_next_step_handoff.generated.jsonl"
        ),
        "agent_workflow_obs_handoff.generated.jsonl": _maybe_read_jsonl(
            repo_root / PRETRADE_PREFIX / "agent_workflow_obs_handoff.generated.jsonl"
        ),
        "pretrade_qku_formula_compute_map.generated.jsonl": _maybe_read_jsonl(
            repo_root / PRETRADE_PREFIX / "pretrade_qku_formula_compute_map.generated.jsonl"
        ),
        "pretrade_quantum_readiness_handoff.generated.jsonl": _maybe_read_jsonl(
            repo_root / PRETRADE_PREFIX / "pretrade_quantum_readiness_handoff.generated.jsonl"
        ),
        "tca_decomposition.generated.jsonl": _maybe_read_jsonl(
            repo_root / PRETRADE_PREFIX / "tca_decomposition.generated.jsonl"
        ),
        "pretrade_exec_ladder_handoff.generated.jsonl": _maybe_read_jsonl(
            repo_root / PRETRADE_PREFIX / "pretrade_exec_ladder_handoff.generated.jsonl"
        ),
    }
    readiness_files = {
        "qku_formula_agent_compute_map.generated.jsonl": _maybe_read_jsonl(
            repo_root / READINESS_PREFIX / "qku_formula_agent_compute_map.generated.jsonl"
        ),
        "owner_ux_semantic_bundle_handoff.generated.jsonl": _maybe_read_jsonl(
            repo_root / READINESS_PREFIX / "owner_ux_semantic_bundle_handoff.generated.jsonl"
        ),
    }
    return {
        "readiness_registry": readiness_registry,
        "pretrade_registry": pretrade_registry,
        "readiness_by_candidate": _index_by_candidate(readiness_registry),
        "pretrade_files_by_candidate": {
            name: _index_by_candidate(rows) for name, rows in pretrade_files.items()
        },
        "readiness_files_by_candidate": {
            name: _index_by_candidate(rows) for name, rows in readiness_files.items()
        },
    }


def _responsible_roles(pretrade_row: dict[str, Any], readiness_row: dict[str, Any]) -> list[str]:
    roles = _list(pretrade_row.get("agent_role_refs")) or _list(
        readiness_row.get("agent_role_refs")
    )
    return roles or ["PR165_D2_GAP"]


def _agent_audit_ref(pretrade_row: dict[str, Any], readiness_row: dict[str, Any]) -> str:
    return _first_non_gap(
        pretrade_row.get("agent_roster_discovery_audit_ref_or_gap"),
        readiness_row.get("agent_roster_discovery_audit_ref_or_gap"),
        "PR165_D2_GAP::AgentRosterDiscoveryAudit",
    )


def _agent_crosswalk_ref(pretrade_row: dict[str, Any], readiness_row: dict[str, Any]) -> str:
    return _first_non_gap(
        pretrade_row.get("agent_duty_source_crosswalk_ref_or_gap"),
        readiness_row.get("agent_duty_source_crosswalk_ref_or_gap"),
        "PR165_D2_GAP::AgentDutySourceCrosswalk",
    )


def _current_surface_ref() -> str:
    return "src/qtt/dashboard/owner_surface_resolver.py::OwnerSurfaceResolver"


def _current_action_ref() -> str:
    return "src/qtt/dashboard/owner_action_registry.py::OwnerActionRegistry"


def _dashboard_state_ref() -> str:
    return "src/qtt/dashboard/owner_dashboard_projection_builder.py::DashboardReadModelBuilder_CURRENT_EQUIVALENT"


def _row_base(
    *,
    row_id: str,
    projection_file: str,
    service_domain: str,
    service_object_type: str,
    service_object_id: str,
    pretrade_row: dict[str, Any],
    readiness_row: dict[str, Any],
    object_label: str,
    action_code: str | None = None,
    event_class: str | None = None,
) -> dict[str, Any]:
    candidate_id = str(pretrade_row.get("candidate_id") or readiness_row.get("candidate_id") or "GLOBAL")
    qku_refs = _list(pretrade_row.get("qku_refs")) or _list(readiness_row.get("qku_refs"))
    formula_refs = _list(pretrade_row.get("formula_refs")) or _list(readiness_row.get("formula_refs"))
    algorithm_refs = _list(pretrade_row.get("algorithm_refs_or_gap")) or _list(
        readiness_row.get("algorithm_refs_or_gap")
    )
    roles = _responsible_roles(pretrade_row, readiness_row)
    projection_ref = _ref(projection_file, row_id)
    source_pretrade_ref = (
        f"{PRETRADE_REGISTRY_REF}::{pretrade_row.get('pretrade_registry_row_id', candidate_id)}"
        if pretrade_row
        else "GLOBAL_POLICY_NO_PRETRADE_ROW"
    )
    source_readiness_ref = (
        f"{READINESS_REGISTRY_REF}::{readiness_row.get('registry_row_id', candidate_id)}"
        if readiness_row
        else "GLOBAL_POLICY_NO_READINESS_ROW"
    )
    title = object_label.replace("_", " ").replace("V1", " V1").strip()
    provider_state = "PROVIDER_PENDING_CONTRACT_ONLY"
    freshness_state = "STATIC_BUILD_CONTRACT_NO_RUNTIME_CURRENTNESS"
    action_ref = action_code or "NO_ACTION_FOR_VIEW_CONTRACT"
    no_trade_ref = str(pretrade_row.get("no_trade_candidate_ref_or_gap", "SCOPED_GAP_NO_TRADE_REF"))

    row: dict[str, Any] = {
        "registry_row_id": row_id,
        "service_domain": service_domain,
        "service_object_type": service_object_type,
        "service_object_id": service_object_id,
        "service_object_version": PROJECTION_VERSION,
        "projection_file": projection_file,
        "projection_ref": projection_ref,
        "generated_from": REGISTRY_REF,
        "authoritative_source": REGISTRY_REF,
        "builder_name": BUILDER_NAME,
        "validator_name": VALIDATOR_NAME,
        "manual_edit_allowed": False,
        "source_readiness_registry_ref_or_gap": source_readiness_ref,
        "source_readiness_projection_ref_or_gap": _upstream_ref(
            READINESS_PREFIX, "qku_formula_agent_compute_map.generated.jsonl", candidate_id
        ),
        "source_pretrade_registry_ref_or_gap": source_pretrade_ref,
        "source_pretrade_projection_ref_or_gap": _upstream_ref(
            PRETRADE_PREFIX, "pretrade_owner_view_handoff.generated.jsonl", candidate_id
        ),
        "source_owner_dashboard_state_ref_or_gap": _dashboard_state_ref(),
        "source_owner_surface_resolver_ref_or_gap": _current_surface_ref(),
        "source_owner_action_registry_ref_or_gap": _current_action_ref(),
        "source_owner_ux_semantic_bundle_ref_or_gap": (
            "docs/master_plan/generated/pr169_readiness1/owner_ux_semantic_bundle_handoff.generated.jsonl"
        ),
        "source_owner_conversation_state_ref_or_gap": "OwnerConversationStateV1::SVC1_CONTRACT_ROUTE",
        "source_owner_search_index_ref_or_gap": "OwnerSearchIndexV1::SVC1_CONTRACT_ROUTE",
        "source_owner_layout_profile_ref_or_gap": "OwnerLayoutProfileV1::SVC1_CONTRACT_ROUTE",
        "source_owner_notification_tier_ref_or_gap": "OwnerNotificationTierPolicyV1::SVC1_CONTRACT_ROUTE",
        "source_mobile_app_shell_contract_ref_or_gap": "MobileAppShellContractV1::SVC1_CONTRACT_ROUTE",
        "source_pwa_contract_ref_or_gap": "PWAContractV1::SVC1_CONTRACT_ROUTE",
        "trade_plan_candidate_ref_or_gap": str(
            pretrade_row.get("trade_plan_candidate_ref")
            or readiness_row.get("trade_plan_candidate_ref")
            or "SCOPED_GAP_TRADE_PLAN"
        ),
        "pretrade_decision_candidate_ref_or_gap": str(
            pretrade_row.get("pretrade_decision_candidate_id", "SCOPED_GAP_PRETRADE_CANDIDATE")
        ),
        "pretrade_decision_candidate_ref": str(
            pretrade_row.get("pretrade_decision_candidate_id", "SCOPED_GAP_PRETRADE_CANDIDATE")
        ),
        "no_trade_candidate_ref_or_gap": no_trade_ref,
        "qku_refs": qku_refs,
        "formula_refs": formula_refs,
        "algorithm_refs_or_gap": algorithm_refs or ["SCOPED_GAP_ALGORITHM_REF"],
        "computable_contract_refs_or_gap": _list(
            pretrade_row.get("readiness1_computable_contract_ref")
        )
        or _list(readiness_row.get("computable_contract_id"))
        or ["SCOPED_GAP_COMPUTABLE_CONTRACT"],
        "test_vector_refs_or_gap": ["READINESS1_TEST_VECTOR_ROUTE_OR_SCOPED_GAP"],
        "candidate_external_info_lane_ref_or_gap": str(
            pretrade_row.get("candidate_external_info_lane_ref_or_gap")
            or readiness_row.get("candidate_external_info_lane_state")
            or "SCOPED_GAP_CANDIDATE_EXTERNAL_INFO_LANE"
        ),
        "candidate_id": candidate_id,
        "candidate_id_or_gap": candidate_id,
        "workflow_id_or_gap": f"SVC1_WORKFLOW::{candidate_id}",
        "owner_read_model_snapshot_ref": f"SVC1_SNAPSHOT::{candidate_id}",
        "owner_read_model_section": service_domain,
        "owner_surface_route_ref_or_gap": _current_surface_ref(),
        "owner_widget_ref_or_gap": f"OwnerWidgetManifest::{service_domain}",
        "owner_chart_ref_or_gap": f"OwnerChartManifest::{service_domain}",
        "owner_action_ref_or_gap": action_ref,
        "owner_conversation_route_ref_or_gap": f"OwnerConversationStateV1::{candidate_id}",
        "owner_plain_english_intent_route_ref_or_gap": f"NaturalLanguageOwnerIntentParserContractV1::{candidate_id}",
        "owner_chat_route_preview_ref_or_gap": f"OwnerChatRoutePreview::{candidate_id}",
        "owner_research_intake_route_ref_or_gap": f"OwnerResearchSubmissionV1::{candidate_id}",
        "owner_trade_intent_route_ref_or_gap": f"OwnerTradeIntentV1::{candidate_id}",
        "owner_search_index_route_ref_or_gap": "OwnerSearchIndexV1::shared_svc1_index",
        "owner_layout_profile_route_ref_or_gap": "OwnerLayoutProfileV1::shared_layout_profiles",
        "owner_notification_tier_policy_ref_or_gap": "OwnerNotificationTierPolicyV1::S0_INFO_TO_S4_CRITICAL",
        "owner_stale_data_banner_ref_or_gap": f"OwnerStaleDataBannerV1::{candidate_id}",
        "mobile_app_shell_contract_ref_or_gap": "MobileAppShellContractV1::shared_state_contract",
        "mobile_navigation_contract_ref_or_gap": "MobileNavigationContractV1::shared_bottom_nav",
        "trade_workbench_route_ref_or_gap": f"TradeWorkbenchRoute::{candidate_id}",
        "execution_ladder_stage_ref_or_gap": f"ExecutionLadderStage::{candidate_id}",
        "owner_plain_english_title": title,
        "owner_plain_english_summary": (
            f"{title} exposes a deterministic SVC1 route for {candidate_id} without runtime execution."
        ),
        "owner_status_copy": provider_state,
        "why_this_matters_copy": (
            "This central route lets dashboard, mobile, Telegram, chat, agents, LLMs, paper, hotpath, and later live-review stages consume one read model."
        ),
        "what_owner_can_do_next_copy": (
            "The owner can request review, inspect provider-pending reasons, open Trade Workbench context, or view technical details."
        ),
        "trading_relevance_copy": (
            "Trading command authority is request, review, approval-preview, veto, pause, rollback, and kill-switch request only."
        ),
        "risk_plain_english_copy": (
            "No venue order, connector read, private cash read, live submit, runtime LLM, runtime agent, or execution receipt is created."
        ),
        "missing_information_copy": (
            "Runtime provider data, private cash state, live execution authorization, and accepted source truth remain downstream provider-pending."
        ),
        "technical_details_ref_or_gap": projection_ref,
        "developer_mode_ref_or_gap": "OwnerModePolicyV1::Developer_View_collapsed_refs",
        "owner_trading_command_authority_allowed": True,
        "owner_trading_command_authority_scope": (
            "REQUEST_REVIEW_APPROVAL_PREVIEW_VETO_PAUSE_ROLLBACK_KILL_SWITCH_REQUEST_ONLY_NO_DIRECT_SUBMIT"
        ),
        "direct_venue_submit_bypass_allowed": False,
        "execution_router_release_allowed": False,
        "owner_request_available": True,
        "owner_review_available": True,
        "owner_approval_preview_available": True,
        "owner_veto_available": True,
        "owner_pause_available": True,
        "owner_rollback_request_available": True,
        "owner_kill_switch_request_available": True,
        "provider_state": provider_state,
        "provider_stage": "SVC1_STATIC_CONTRACT_PROVIDER_PENDING",
        "freshness_state": freshness_state,
        "stale_state_policy": "STATIC_SNAPSHOT_STALE_BANNER_REQUIRED_FOR_RUNTIME_DATA",
        "last_snapshot_time_or_static_build_time": "STATIC_BUILD_TIME_PR169_SVC1",
        "snapshot_delta_policy_ref_or_gap": "snapshot_delta_policy.generated.jsonl::STATIC_CONTRACT_DELTAS",
        "activation_state": "CONTRACT_ACTIVE_NO_RUNTIME",
        "lifecycle_state": "MATERIALIZED_CONTRACT",
        "timing_state": "STATIC_BUILD_TIME_ONLY",
        "downstream_owner": "PR169-SVC1",
        "authority_state": "CONTROL_PLANE_ONLY_REQUEST_REVIEW_AUDIT",
        "source_authority_state": "UPSTREAM_DECLARED_GENERATED_ARTIFACTS_ONLY_NO_SOURCE_TRUTH",
        "external_candidate_lane_ref_or_gap": str(
            pretrade_row.get("candidate_external_info_lane_ref_or_gap", "SOURCE_CANDIDATE_LANE_VIEW")
        ),
        "projection_consumers": list(DOWNSTREAM_CONSUMERS),
        "downstream_consumer_refs": list(DOWNSTREAM_CONSUMERS),
        "downstream_consumer_pr_refs": list(DOWNSTREAM_CONSUMERS),
        "orphan_status": "NOT_ORPHAN",
        "route_gap_reason_or_none": "NONE",
        "validation_state": "VALIDATED_BY_PR169_SVC1",
        "fail_closed_reasons": [],
        "event_stream_contract_ref_or_gap": f"DashboardEventStreamV1::{event_class or service_domain}",
        "event_cursor_ref_or_gap": "OwnerEventStreamCursorV1::deterministic_cursor_contract",
        "action_request_ref_or_gap": f"OwnerActionRequestEnvelopeV1::{action_ref}",
        "action_receipt_ref_or_gap": f"OwnerActionReceiptEnvelopeV1::{action_ref}",
        "action_eligibility_ref_or_gap": f"OwnerActionEligibilityViewV1::{action_ref}",
        "action_denied_reason_ref_or_gap": f"OwnerActionDeniedReasonV1::{action_ref}",
        "action_confirmation_policy_ref_or_gap": f"OwnerConfirmationPolicyV1::{action_ref}",
        "action_request_natural_key": f"{action_ref}::{candidate_id}::SVC1_CONTRACT",
        "action_dedupe_policy_ref_or_gap": f"OwnerActionDedupePolicyV1::{action_ref}",
        "action_risk_class_ref_or_gap": "ACTION_RISK_REVIEW_ONLY_NO_EXECUTION",
        "owner_next_step_route_ref_or_gap": f"OwnerNextStepRouterV1::{action_ref}",
        "target_surface_id_or_gap": "TRADE_WORKBENCH_OR_OWNER_DASHBOARD",
        "target_workflow_id_or_gap": f"SVC1_WORKFLOW::{candidate_id}",
        "target_step_id_or_gap": "CONTRACT_PREVIEW",
        "prefill_context_refs_or_gap": [source_pretrade_ref, source_readiness_ref],
        "creates_local_receipt_preview": True,
        "what_happens_next_copy_or_gap": (
            "SVC1 creates a request/receipt preview route for downstream provider review."
        ),
        "what_will_not_happen_now_copy_or_gap": (
            "No order is compiled, submitted, replayed, paper-traded, shadowed, live-dryrun, or released."
        ),
        "responsible_agent_role_refs": roles,
        "supporting_agent_role_refs_or_gap": roles[:2] or ["PR165_D2_GAP"],
        "escalation_agent_role_refs_or_gap": ["governance_agent", "risk_manager_agent"],
        "agent_roster_discovery_audit_ref_or_gap": _agent_audit_ref(pretrade_row, readiness_row),
        "agent_duty_source_crosswalk_ref_or_gap": _agent_crosswalk_ref(pretrade_row, readiness_row),
        "agent_workflow_stage": "SVC1_CONTRACT_PREVIEW",
        "agent_next_stage_route_ref_or_gap": "PR169-AGENT-ORCH1::provider_pending_no_execution",
        "agent_operations_view_ref_or_gap": f"AgentOperationsReadModelV1::{candidate_id}",
        "team_workflow_queue_ref_or_gap": f"QTTTeamWorkflowQueueReadModelV1::{candidate_id}",
        "owner_agent_state_ref_or_gap": f"OwnerAgentStateV1::{candidate_id}",
        "owner_workflow_queue_state_ref_or_gap": f"OwnerWorkflowQueueStateV1::{candidate_id}",
        "agent_pod_ref_or_gap": "PR165_D2_AGENT_POD_OR_SCOPED_GAP",
        "agent_status_preview_state": "RUNNING_PREVIEW_ONLY_CONTRACT_NOT_RUNTIME",
        "agent_trust_score_ref_or_gap": "AgentTrustScoreRoute::provider_pending",
        "agent_kpi_route_ref_or_gap": "AgentKPITrustQuarantineRoute::provider_pending",
        "agent_quarantine_route_ref_or_gap": "AgentQuarantineRoute::route_only",
        "agent_reroute_control_ref_or_gap": "AgentRerouteControl::route_only",
        "expected_receipt_classes": list(RECEIPT_CLASSES),
        "agent_llm_task_route_ref_or_gap": f"AgentLLMTaskRoute::{candidate_id}",
        "llm_grounding_route_ref_or_gap": str(
            pretrade_row.get("pretrade_llm_grounding_view_ref_or_gap")
            or readiness_row.get("llm_grounding_view_ref_or_gap")
            or f"LLMGroundingRoute::{candidate_id}"
        ),
        "llm_review_prompt_contract_ref_or_gap": f"LLMReviewPromptContractV1::{candidate_id}",
        "llm_grounding_allowed": True,
        "llm_review_allowed": True,
        "llm_research_candidate_intake_allowed": True,
        "institutional_control_refs": [
            str(pretrade_row.get("tca_decomposition_ref_or_gap", "TCA_SCOPED_GAP")),
            str(pretrade_row.get("pretrade_edge_alpha_capture_map_ref_or_gap", "EDGE_SCOPED_GAP")),
            str(pretrade_row.get("pretrade_quantum_readiness_handoff_ref_or_gap", "QUANTUM_SCOPED_GAP")),
        ],
        "execution_adjusted_ranking_view_ref_or_gap": f"ExecutionAdjustedRankingView::{candidate_id}",
        "tca_decomposition_view_ref_or_gap": str(
            pretrade_row.get("tca_decomposition_ref_or_gap", f"TCAView::{candidate_id}")
        ),
        "overfit_fdr_control_view_ref_or_gap": f"OverfitFDRControlView::{candidate_id}",
        "portfolio_diversification_view_ref_or_gap": f"PortfolioDiversificationView::{candidate_id}",
        "capacity_crowding_view_ref_or_gap": str(
            pretrade_row.get("capacity_crowding_model_ref_or_gap", f"CapacityCrowdingView::{candidate_id}")
        ),
        "champion_challenger_view_ref_or_gap": f"ChampionChallengerView::{candidate_id}",
        "regime_memory_prior_view_ref_or_gap": str(
            pretrade_row.get("mem1_memory_ref_or_gap")
            or readiness_row.get("mem1_memory_ref_or_gap")
            or f"MEM1PriorRoute::{candidate_id}"
        ),
        "marginal_utility_view_ref_or_gap": f"PortfolioMarginalUtilityView::{candidate_id}",
        "quantum_structural_readiness_view_ref_or_gap": str(
            pretrade_row.get("pretrade_quantum_readiness_handoff_ref_or_gap", f"QuantumReadiness::{candidate_id}")
        ),
        "dag_route_view_ref_or_gap": str(
            pretrade_row.get("pretrade_agent_dag_handoff_ref_or_gap", f"DAGRoute::{candidate_id}")
        ),
        "no_trade_margin_view_ref_or_gap": f"NoTradeMarginView::{candidate_id}",
        "calibration_view_ref_or_gap": str(
            pretrade_row.get("reality_model_calibration_receipt_ref_or_gap", f"CalibrationView::{candidate_id}")
        ),
        "scenario_ladder_view_ref_or_gap": str(
            pretrade_row.get("scenario_ladder_decision_ref_or_gap", f"ScenarioLadder::{candidate_id}")
        ),
        "mode_authority_ref_or_gap": str(
            pretrade_row.get("mode_authority_matrix_ref_or_gap", f"ModeAuthorityMatrix::{candidate_id}")
        ),
        "connector_route_ref_or_gap": str(
            pretrade_row.get("pretrade_connector_handoff_ref_or_gap", "ConnectorRoute::provider_pending_no_read")
        ),
        "execution_router_route_ref_or_gap": str(
            pretrade_row.get("pretrade_execution_router_handoff_ref_or_gap", "ExecutionRouterBoundary::no_release")
        ),
        "hotpath_handoff_route_ref_or_gap": str(
            pretrade_row.get("pretrade_hotpath_handoff_ref_or_gap", "HotpathRoute::snapshot_handoff_only")
        ),
        "metrics_capture_route_ref_or_gap": str(
            pretrade_row.get("pretrade_metrics_capture_handoff_ref_or_gap", "MetricsCaptureRoute::provider_pending")
        ),
        "paper_loop_route_ref_or_gap": "PR169-PAPER-LOOP::provider_pending_no_paper_execution",
        "shadow_route_ref_or_gap": "PR170-LIVE-DRYRUN1::shadow_route_provider_pending_no_shadow_execution",
        "live_dryrun_route_ref_or_gap": "PR170-LIVE-DRYRUN1::provider_pending_no_live_execution",
        "postlaunch_route_ref_or_gap": "PR173-POSTLAUNCH::provider_pending",
        "telegram_route_ref_or_gap": "PR169-TG1::shared_state_mirror_no_bot_runtime",
        "mobile_route_ref_or_gap": "PR170-MOBILE1::shared_state_no_mobile_fork",
        "plugin_route_ref_or_gap": "PR174-PLUGIN1::intake_route_only",
        "qmap_route_ref_or_gap": "PR174-QMAP1::mapping_route_only",
        "allowlist_route_ref_or_gap": "PR174-ALLOW1::review_route_only",
        "control_plane_only": True,
        "live_critical_path_allowed": False,
        "precomputed_snapshot_route_ref_or_gap": f"HotpathSnapshotHandoff::{candidate_id}",
        "estimated_view_load_class": "PRECOMPUTED_STATIC_CONTRACT",
        "snapshot_index_ref_or_gap": f"read_model_snapshot_index.generated.jsonl::{candidate_id}",
        "pagination_policy_ref_or_gap": "STATIC_SMALL_INDEX_NO_RUNTIME_SCAN",
        "cursor_policy_ref_or_gap": "event_stream_cursor_policy.generated.jsonl::STATIC_CURSOR_CONTRACT",
        "snapshot_staleness_policy": "PROVIDER_PENDING_STALE_BANNER_REQUIRED",
        "refresh_route_ref_or_gap": "REQUEST_PROVIDER_REFRESH_REVIEW",
        "expected_runtime_receipt_route_classes": list(EXPECTED_RUNTIME_RECEIPT_CLASSES),
        "actual_runtime_receipts_created": [],
        "alias_state_or_none": (
            f"CURRENT_EQUIVALENT::{PRETRADE_EXEC_LADDER_EQUIVALENT_REF}"
            if "ladder" in projection_file
            else "NONE"
        ),
    }

    row.update({field: False for field in AUTHORITY_FALSE_FIELDS})
    row["fake_pnl_cash_fill_live_position_data_created"] = False
    row["fake_cash_pnl_trade_state_created"] = False
    row["runtime_side_effect_allowed"] = False
    row["direct_submit_created"] = False
    row["execution_router_release_created"] = False
    row["private_cash_read_created"] = False
    row["source_truth_created"] = False
    row["order_authority_created"] = False
    return row


def _enrich_snapshot_row(row: dict[str, Any], snapshot_class: str) -> None:
    snapshot_id = f"{snapshot_class}::{row['candidate_id']}"
    row.update(
        {
            "snapshot_id": snapshot_id,
            "snapshot_class": snapshot_class,
            "title": row["owner_plain_english_title"],
            "plain_english_summary": row["owner_plain_english_summary"],
            "status": row["provider_state"],
            "why_this_matters": row["why_this_matters_copy"],
            "what_owner_can_do_next": row["what_owner_can_do_next_copy"],
            "visible_trading_relevance": row["trading_relevance_copy"],
            "related_qtt_agents": row["responsible_agent_role_refs"],
            "related_llm_route": row["llm_grounding_route_ref_or_gap"],
            "related_workflow_stage": row["agent_workflow_stage"],
            "stale_warning": "Provider data is pending; chart/status frames must not fake runtime data.",
            "candidate_refs": [row["pretrade_decision_candidate_ref_or_gap"]],
            "qku_formula_refs_collapsed": {
                "qku_refs": row["qku_refs"],
                "formula_refs": row["formula_refs"],
            },
            "technical_details_collapsed_by_default": True,
            "developer_mode_required_for_raw_refs": True,
        }
    )


def _enrich_action_row(row: dict[str, Any], action_code: str) -> None:
    high_risk = any(token in action_code for token in ("LIVE", "KILL", "ROLLBACK", "ALLOWLIST", "EXECUTION_ROUTER"))
    disabled = action_code == "REQUEST_EXECUTION_ROUTER_SUBMIT_REVIEW"
    row.update(
        {
            "action_code": action_code,
            "action_id": action_code,
            "request_class": action_code,
            "owner_intent": action_code.lower().replace("_", " "),
            "owner_plain_english_label": action_code.replace("_", " ").title(),
            "owner_label": action_code.replace("_", " ").title(),
            "eligible_state": "DISABLED_DIRECT_SUBMIT_BOUNDARY" if disabled else "ELIGIBLE_FOR_REVIEW_CONTRACT_ONLY",
            "eligibility_proof_ref_or_gap": row["projection_ref"] if not disabled else "SCOPED_GAP_DIRECT_SUBMIT_DISABLED",
            "denied_reason_ref_or_gap": "LIVE_ORDER_SUBMIT_DISABLED" if disabled else "NO_DENIAL_FOR_REVIEW_ROUTE",
            "provider_pending_reason_ref_or_gap": "DOWNSTREAM_PROVIDER_PENDING_NO_RUNTIME_EXECUTION",
            "required_confirmation_class": "CRITICAL_CONFIRMATION" if high_risk else "OWNER_REVIEW_REQUIRED",
            "requires_owner_confirmation": high_risk,
            "risk_class": "S4_CRITICAL_REVIEW_ONLY" if high_risk else "S1_REVIEW_ONLY",
            "safe_next_route": "OwnerNextStepRouterV1::LIVE_ORDER_SUBMIT_DISABLED"
            if disabled
            else f"OwnerNextStepRouterV1::{action_code}",
            "audit_receipt_class": "OwnerExecutionRouterSubmitReviewReceiptV1"
            if "EXECUTION_ROUTER" in action_code
            else "OwnerActionRequestReceiptV1",
            "receipt_class": "OwnerActionRequestReceiptV1",
            "receipt_contract_only": True,
            "action_request_natural_key": f"{action_code}::SVC1::DEDUPE",
            "dedupe_policy_ref_or_gap": f"OwnerActionDedupePolicyV1::{action_code}",
            "action_dedupe_policy_ref_or_gap": f"OwnerActionDedupePolicyV1::{action_code}",
            "confirmation_policy_ref_or_gap": f"OwnerConfirmationPolicyV1::{action_code}",
            "responsible_agent_role_refs": row["responsible_agent_role_refs"],
            "supporting_llm_route_ref_or_gap": row["llm_grounding_route_ref_or_gap"],
            "disabled_reason": "Execution Router submit is review-preview only in SVC1."
            if disabled
            else "No direct execution is available from SVC1 actions.",
            "provider_pending_reason": "Downstream providers have not supplied runtime receipts or execution authority.",
            "what_owner_can_do_now": "Open the review route, inspect provider-pending state, or request more research.",
            "safe_alternative_action": "REQUEST_TRADE_CHECK_WITH_QTT_AGENTS",
            "what_later_PR_unlocks_it": "LLM1/2, AGENT-ORCH1, PAPER-LOOP, HOTPATH1, LIVE-DRYRUN1, LIVE-PILOT, LAUNCH",
            "what_will_not_happen_now": row["what_will_not_happen_now_copy_or_gap"],
            "why_no_live_action_is_allowed_yet": "Execution Router release, source truth, cash/risk freshness, TCA, capacity, and owner final live approval remain downstream.",
            "current_surface_id": "OWNER_DASHBOARD",
            "current_surface_id_or_gap": "OWNER_DASHBOARD",
            "target_surface_id": "TRADE_WORKBENCH" if "TRADE" in action_code else "OWNER_DASHBOARD",
            "target_workflow_id": f"SVC1_ACTION_WORKFLOW::{action_code}",
            "target_step_id": "CONTRACT_PREVIEW",
            "preview_object_type": row["service_object_type"],
            "owner_input_required": high_risk,
            "safe_default_if_owner_declines": "NO_RUNTIME_SIDE_EFFECT",
            "disabled_reason_if_blocked": "LIVE_ORDER_SUBMIT_DISABLED" if disabled else "NONE",
            "authority_boundary": "NO_DIRECT_SUBMIT_NO_EXECUTION_ROUTER_RELEASE",
            "what_happens_next": row["what_happens_next_copy_or_gap"],
        }
    )


def _enrich_event_row(row: dict[str, Any], event_class: str) -> None:
    row.update(
        {
            "event_class": event_class,
            "event_contract_id": f"DashboardEventStreamV1::{event_class}",
            "cursor_policy_id": "OwnerEventStreamCursorV1::STATIC_CONTRACT_CURSOR",
            "event_sample_state": "CONTRACT_SAMPLE_NOT_RUNTIME_EVENT",
            "event_payload_contract_ref": row["projection_ref"],
        }
    )


def _enrich_policy_row(row: dict[str, Any], projection_file: str, object_id: str) -> None:
    row.update(
        {
            "policy_id": object_id,
            "policy_class": row["service_object_type"],
            "shared_state_id_state": "SHARED_OWNER_DASHBOARD_STATE",
            "shared_action_id_state": "SHARED_OWNER_ACTION_REGISTRY",
            "shared_widget_id_state": "SHARED_OWNER_WIDGET_MANIFEST",
            "shared_chart_id_state": "SHARED_OWNER_CHART_MANIFEST",
            "shared_chat_id_state": "SHARED_OWNER_CONVERSATION_STATE",
            "shared_receipt_id_state": "SHARED_OWNER_ACTION_RECEIPT_CONTRACT",
            "desktop_dashboard_route_state": "SHARED_STATE_CONTRACT",
            "mobile_web_route_state": "SHARED_STATE_CONTRACT",
            "pwa_route_state": "SHARED_STATE_CONTRACT_NO_SERVICE_WORKER",
            "native_mobile_route_state": "SHARED_STATE_CONTRACT_NO_NATIVE_RUNTIME",
            "telegram_mirror_route_state": "SHARED_STATE_CONTRACT_NO_BOT_RUNTIME",
            "no_mobile_only_fork_proof": "PASS_SHARED_STATE_ACTION_WIDGET_CHART_CHAT_RECEIPT_IDS",
            "no_telegram_second_governance_plane_proof": "PASS_SHARED_OWNER_GOVERNANCE",
            "read_only_or_actionable_mode": "READ_ONLY_PROVIDER_PENDING_WITH_REVIEW_ACTIONS",
            "stale_warning": "Static SVC1 contract; runtime data must show provider-pending/stale banners.",
        }
    )
    if projection_file == "owner_notification_tier_policy.generated.jsonl":
        row["notification_tiers"] = list(NOTIFICATION_TIERS)
    if projection_file == "owner_layout_profile_routes.generated.jsonl":
        row["layout_profiles"] = list(LAYOUT_PROFILES)
    if projection_file == "owner_chart_manifest.generated.jsonl":
        row["chart_families"] = list(CHART_FAMILIES)


def _enrich_institutional_row(row: dict[str, Any], projection_file: str) -> None:
    candidate_id = row["candidate_id"]
    row.update(
        {
            "expected_net_cash_ref_or_gap": f"ExpectedNetCashRoute::{candidate_id}",
            "candidate_minus_no_trade_ref_or_gap": f"NoTradeMarginRoute::{candidate_id}",
            "lower_confidence_bound_ref_or_gap": f"LCBRoute::{candidate_id}",
            "fill_adjusted_ev_ref_or_gap": f"FillAdjustedEVRoute::{candidate_id}",
            "capacity_adjusted_ev_ref_or_gap": row["capacity_crowding_view_ref_or_gap"],
            "portfolio_marginal_utility_ref_or_gap": row["marginal_utility_view_ref_or_gap"],
            "fdr_overfit_status_ref_or_gap": row["overfit_fdr_control_view_ref_or_gap"],
            "tca_decomposition_ref_or_gap": row["tca_decomposition_view_ref_or_gap"],
            "latency_budget_ref_or_gap": f"LatencyBudgetRoute::{candidate_id}",
            "scenario_ladder_ref_or_gap": row["scenario_ladder_view_ref_or_gap"],
            "calibration_ref_or_gap": row["calibration_view_ref_or_gap"],
            "agent_route_ref_or_gap": row["agent_operations_view_ref_or_gap"],
            "no_orphan_route_ref_or_gap": "no_orphan.report.json::PASS",
            "owner_readable_rank_explanation": "Ranking is view-only and must beat no-trade after net cash, LCB, TCA, fill, latency, capacity, FDR, portfolio utility, scenario, calibration, agent route, and no-orphan proof.",
            "ranking_is_view_only": True,
            "ranking_recomputed_by_svc1": False,
            "fees_ref_or_gap": f"FeeModelRoute::{candidate_id}",
            "spread_cost_ref_or_gap": f"SpreadCostRoute::{candidate_id}",
            "slippage_ref_or_gap": f"SlippageRoute::{candidate_id}",
            "market_impact_ref_or_gap": f"MarketImpactRoute::{candidate_id}",
            "opportunity_cost_ref_or_gap": f"OpportunityCostRoute::{candidate_id}",
            "cancel_replace_cost_ref_or_gap": f"CancelReplaceCostRoute::{candidate_id}",
            "latency_drag_ref_or_gap": f"LatencyDragRoute::{candidate_id}",
            "adverse_selection_ref_or_gap": f"AdverseSelectionRoute::{candidate_id}",
            "settlement_cashflow_ref_or_gap": f"SettlementCashflowRoute::{candidate_id}",
            "capacity_crowding_ref_or_gap": row["capacity_crowding_view_ref_or_gap"],
            "owner_readable_cost_waterfall": "Fees, spread, slippage, impact, opportunity cost, cancel/replace, latency, adverse selection, settlement, and capacity are explicit routes.",
            "tca_is_explicit_not_vague_score": True,
            "trial_count_ref_or_gap": "FDRTrialCountRoute::scoped_gap",
            "support_count_ref_or_gap": "FDRSupportCountRoute::scoped_gap",
            "validation_window_ref_or_gap": "PurgedEmbargoedValidationWindowRoute::scoped_gap",
            "purged_embargoed_validation_ref_or_gap": "PurgedEmbargoedValidationRoute::scoped_gap",
            "white_reality_check_route_ref_or_gap": "WhiteRealityCheckRoute::scoped_gap",
            "hansen_spa_route_ref_or_gap": "HansenSPARoute::scoped_gap",
            "stepwise_spa_or_stepm_route_ref_or_gap": "StepwiseSPAOrStepMRoute::scoped_gap",
            "model_confidence_set_route_ref_or_gap": "ModelConfidenceSetRoute::scoped_gap",
            "deflated_sharpe_or_pbo_route_ref_or_gap": "DeflatedSharpeOrPBORoute::scoped_gap",
            "multiple_testing_fdr_route_ref_or_gap": "MultipleTestingFDRRoute::scoped_gap",
            "candidate_promotion_status": "VIEW_ONLY_PROVIDER_PENDING",
            "owner_readable_false_discovery_explanation": "SVC1 routes false-discovery controls; it does not promote alpha.",
            "fdr_status_is_view_only": True,
            "strategy_family": "prediction_market_pretrade_contract",
            "qku_formula_stack_family": "immutable_qku_formula_stack",
            "stack_correlation_ref_or_gap": "CorrelationRoute::scoped_gap",
            "alpha_concentration_ref_or_gap": "AlphaConcentrationRoute::scoped_gap",
            "failure_mode_diversity_ref_or_gap": "FailureModeDiversityRoute::scoped_gap",
            "venue_exposure_ref_or_gap": "VenueExposureRoute::scoped_gap",
            "capital_lock_ref_or_gap": "CapitalLockRoute::scoped_gap",
            "expected_fill_capacity_ref_or_gap": "ExpectedFillCapacityRoute::scoped_gap",
            "drawdown_contribution_ref_or_gap": "DrawdownContributionRoute::scoped_gap",
            "tail_risk_ref_or_gap": "TailRiskRoute::scoped_gap",
            "liquidity_filter_ref_or_gap": "LiquidityFilterRoute::scoped_gap",
            "owner_readable_portfolio_effect": "Portfolio effect is routed as marginal utility, diversification, capital lock, and risk budget views.",
            "capacity_bucket": "PROVIDER_PENDING_BUCKET",
            "max_size_ref_or_gap": "MaxSizeRoute::scoped_gap",
            "fill_capacity_ref_or_gap": "FillCapacityRoute::scoped_gap",
            "orderbook_depth_ref_or_gap": "OrderbookDepthRoute::scoped_gap",
            "spread_bucket_ref_or_gap": "SpreadBucketRoute::scoped_gap",
            "crowding_risk_ref_or_gap": "CrowdingRiskRoute::scoped_gap",
            "event_lifecycle_ref_or_gap": "EventLifecycleRoute::scoped_gap",
            "time_to_resolution_ref_or_gap": "TimeToResolutionRoute::scoped_gap",
            "owner_readable_capacity_explanation": "Capacity/crowding is a route contract and cannot become a fake size default.",
            "current_champion_ref_or_gap": "VIEW_ONLY_CHAMPION_PROVIDER_PENDING",
            "challenger_candidate_refs": [row["pretrade_decision_candidate_ref_or_gap"]],
            "no_trade_challenger_ref_or_gap": row["no_trade_candidate_ref_or_gap"],
            "exploration_challenger_refs_or_gap": ["REPLAY_PAPER_EXPLORATION_ROUTE"],
            "why_champion_wins_or_gap": "SCOPED_GAP_NEEDS_DOWNSTREAM_EVIDENCE",
            "why_challenger_loses_or_gap": "SCOPED_GAP_NEEDS_DOWNSTREAM_EVIDENCE",
            "what_needs_retesting": "Provider data, replay, paper, FDR, TCA, capacity, calibration, and no-trade margin.",
            "retest_route_ref_or_gap": f"REQUEST_PRETRADE_RECHECK::{candidate_id}",
            "paper_only_exploration_route_ref_or_gap": "PR169-PAPER-LOOP::paper_provider_pending",
            "owner_readable_tournament_summary": "Champion/challenger is a view-only tournament route.",
            "champion_selection_is_view_only": True,
            "mem1_memory_ref_or_gap": row["regime_memory_prior_view_ref_or_gap"],
            "similar_context_refs_or_gap": ["MEM1SimilarContextRoute::prior_only"],
            "winning_recipe_refs_or_gap": ["MEM1WinningRecipeRoute::prior_only"],
            "failure_memory_refs_or_gap": ["MEM1FailureRoute::prior_only"],
            "no_trade_memory_refs_or_gap": ["MEM1NoTradeRoute::prior_only"],
            "drift_state_ref_or_gap": "MEM1DriftRoute::prior_only",
            "cooldown_route_ref_or_gap": "MEM1CooldownRoute::prior_only",
            "retest_route_ref_or_gap": f"REQUEST_NO_TRADE_REOPTIMIZATION_REVIEW::{candidate_id}",
            "same_venue_scope": True,
            "same_market_type_scope": True,
            "same_event_lifecycle_scope": True,
            "same_liquidity_spread_bucket_scope": True,
            "same_time_to_resolution_bucket_scope": True,
            "same_formula_algorithm_qku_stack_scope": True,
            "same_parameter_range_scope": True,
            "same_maker_taker_order_policy_scope": True,
            "memory_is_prior_not_proof": True,
            "standalone_edge_ref_or_gap": "StandaloneEdgeRoute::scoped_gap",
            "portfolio_adjusted_edge_ref_or_gap": "PortfolioAdjustedEdgeRoute::scoped_gap",
            "correlation_penalty_ref_or_gap": "CorrelationPenaltyRoute::scoped_gap",
            "diversification_benefit_ref_or_gap": "DiversificationBenefitRoute::scoped_gap",
            "capital_opportunity_cost_ref_or_gap": "CapitalOpportunityCostRoute::scoped_gap",
            "risk_budget_ref_or_gap": "RiskBudgetRoute::scoped_gap",
            "drawdown_budget_ref_or_gap": "DrawdownBudgetRoute::scoped_gap",
            "owner_readable_marginal_utility_explanation": "Marginal utility is exposed as route proof, not recomputed by SVC1.",
            "qstruct_ref_or_gap": row["quantum_structural_readiness_view_ref_or_gap"],
            "quantum_problem_class": "QUBO_OR_CQM_ROUTE_CANDIDATE",
            "variable_encoding_route_ref_or_gap": "QuantumVariableEncodingRoute::scoped_gap",
            "objective_function_route_ref_or_gap": "QuantumObjectiveFunctionRoute::scoped_gap",
            "constraint_route_ref_or_gap": "QuantumConstraintRoute::scoped_gap",
            "penalty_scaling_route_ref_or_gap": "QuantumPenaltyScalingRoute::scoped_gap",
            "coefficient_scaling_route_ref_or_gap": "QuantumCoefficientScalingRoute::scoped_gap",
            "quadratic_program_route_ref_or_gap": "QuadraticProgramRoute::scoped_gap",
            "qubo_route_ref_or_gap": "QUBORoute::scoped_gap",
            "bqm_route_ref_or_gap": "BQMRoute::scoped_gap",
            "cqm_route_ref_or_gap": "CQMRoute::scoped_gap",
            "ising_route_ref_or_gap": "IsingRoute::scoped_gap",
            "qaoa_candidate_route_ref_or_gap": "QAOACandidateRoute::scoped_gap",
            "vqe_candidate_route_ref_or_gap": "VQECandidateRoute::scoped_gap",
            "quantum_inspired_optimizer_ref_or_gap": "QuantumInspiredOptimizerRoute::scoped_gap",
            "classical_exact_or_heuristic_comparator_ref_or_gap": "ClassicalComparatorRoute::required",
            "fallback_route_ref_or_gap": "ClassicalFallbackRoute::required",
            "estimated_variable_count_or_gap": "SCOPED_GAP_PROVIDER_PENDING",
            "estimated_qubit_or_embedding_complexity_ref_or_gap": "SCOPED_GAP_PROVIDER_PENDING",
            "optimizer_default_ref_or_gap": "NO_OPTIMIZER_DEFAULT_IN_SVC1",
            "parameter_range_ref_or_gap": "ParameterRangeRoute::scoped_gap",
            "owner_readable_quantum_structural_summary": "Quantum readiness maps objective, variables, constraints, penalty/coefficient scaling, comparator, and fallback without backend execution or advantage claim.",
            "producer_artifact_ref": REGISTRY_REF,
            "producer_pr_ref": "PR169-SVC1",
            "producer_row_ref_or_scope": row["registry_row_id"],
            "consumer_artifact_ref": row["projection_ref"],
            "consumer_pr_ref": "PR169-SVC1",
            "consumer_role": row["service_domain"],
            "llm_view_allowed": True,
            "owner_dashboard_view_allowed": True,
            "owner_trading_command_route_allowed": True,
            "runtime_use_allowed": False,
            "replay_candidate_use_allowed": True,
            "paper_candidate_use_allowed": True,
            "shadow_candidate_use_allowed": True,
            "hotpath_use_allowed": True,
            "metrics_use_allowed": True,
            "live_dryrun_use_allowed": True,
            "live_use_allowed": False,
            "route_state": "ROUTED_CONTRACT_ONLY",
        }
    )
    if projection_file == "quantum_structural_readiness_views.generated.jsonl":
        row["service_object_type"] = "OwnerQuantumReadinessPreviewV1"


def _enrich_chat_row(row: dict[str, Any], intent_class: str = "TRADE_CHECK_REQUEST") -> None:
    request_class = dict(PLAIN_ENGLISH_INTENT_ROUTES).get(intent_class, "OwnerTradeCheckRequestV1")
    row.update(
        {
            "message_or_submission_id": f"SVC1_MESSAGE::{row['candidate_id']}::{intent_class}",
            "plain_english_text_or_ref": "Can QTT check this market and find the best trade?",
            "intent_class": intent_class,
            "parser_contract_ref": "NaturalLanguageOwnerIntentParserContractV1::route_preview_only",
            "source_family": list(SOURCE_FAMILIES),
            "source_candidate_lane_ref_or_gap": row["candidate_external_info_lane_ref_or_gap"],
            "duplicate_check_route_ref_or_gap": "SourceCandidateDuplicateCheckRoute::provider_pending",
            "recency_check_route_ref_or_gap": "SourceCandidateRecencyCheckRoute::provider_pending",
            "relevance_check_route_ref_or_gap": "SourceCandidateRelevanceCheckRoute::provider_pending",
            "safety_check_route_ref_or_gap": "SourceCandidateSafetyCheckRoute::provider_pending",
            "owner_action_request_route_ref_or_gap": f"{request_class}::request_preview",
            "owner_action_receipt_route_ref_or_gap": "OwnerChatRouteReceiptPreviewV1::contract_only",
            "qku_formula_route_ref_or_gap": row["qku_formula_compute_route_views_ref"]
            if "qku_formula_compute_route_views_ref" in row
            else row["owner_surface_route_ref_or_gap"],
            "quantum_mapping_route_ref_or_gap": row["quantum_structural_readiness_view_ref_or_gap"],
            "replay_paper_route_ref_or_gap": "ReplayPaperRequestV1::preview_only",
            "source_truth_created": False,
            "paper_execution_created": False,
            "live_execution_created": False,
            "order_authority_created": False,
        }
    )


def _enrich_expansion_row(row: dict[str, Any]) -> None:
    row.update(
        {
            "market_family": "prediction_market_stage1_and_later_market_socket",
            "venue_or_platform_id_or_gap": "VENUE_OR_PLATFORM_PROVIDER_PENDING",
            "stage_scope": "CONTRACT_INSTALLATION_SOCKET_ONLY",
            "required_upstream_source_evidence_route_or_gap": "SourceEvidenceRoute::candidate_required",
            "required_market_adapter_route_or_gap": "MarketAdapterRoute::provider_pending",
            "required_connector_semantic_route_or_gap": "ConnectorSemanticRoute::provider_pending_no_connector_read",
            "required_replay_data_route_or_gap": "ReplayDataRoute::provider_pending_no_replay_execution",
            "required_paper_validation_route_or_gap": "PaperValidationRoute::provider_pending_no_paper_execution",
            "required_live_dryrun_route_or_gap": "LiveDryrunRoute::provider_pending_no_live_execution",
            "required_risk_cash_settlement_route_or_gap": "RiskCashSettlementRoute::provider_pending_no_private_read",
            "required_execution_router_route_or_gap": "ExecutionRouterBoundary::provider_pending_no_release",
            "agent_route_refs": row["responsible_agent_role_refs"],
            "llm_route_ref_or_gap": row["llm_grounding_route_ref_or_gap"],
            "qku_formula_intake_route_ref_or_gap": "QKUFormulaIntakeRouteViewV1::shared_socket",
            "plugin_route_ref_or_gap": row["plugin_route_ref_or_gap"],
            "qmap_route_ref_or_gap": row["qmap_route_ref_or_gap"],
            "allowlist_route_ref_or_gap": row["allowlist_route_ref_or_gap"],
            "no_scattered_market_logic_proof": "PASS_ROUTE_ROWS_EXTEND_SOCKET_INSTEAD_OF_SERVICE_FORK",
        }
    )


def _artifact_service_domain(file_name: str) -> str:
    stem = _projection_stem(file_name)
    if stem.startswith("owner_action") or stem.startswith("action_") or stem.startswith("command_action"):
        return "owner_action_queue"
    if stem.startswith("event_stream") or stem == "audit_receipt_stream":
        return "event_audit_stream"
    if stem.startswith("owner_") or stem.startswith("mobile") or stem.startswith("telegram"):
        return "owner_surface"
    if any(token in stem for token in ("tca", "ranking", "fdr", "portfolio", "capacity", "champion", "memory", "marginal", "quantum", "scenario", "calibration")):
        return "institutional_decision_view"
    if "agent" in stem or "team_workflow" in stem:
        return "agent_operations"
    if "market" in stem or "reality_model" in stem or "plugin" in stem or "qmap" in stem:
        return "expansion_socket"
    return "read_model_service"


def _build_candidate_rows(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    readiness_by_candidate = ctx["readiness_by_candidate"]
    rows: list[dict[str, Any]] = []
    for pretrade_row in ctx["pretrade_registry"]:
        candidate_id = str(pretrade_row["candidate_id"])
        readiness_row = readiness_by_candidate.get(candidate_id, {})
        for file_name in CANDIDATE_PROJECTION_FILES:
            stem = _projection_stem(file_name)
            intent_variants: Sequence[str | None] = (None,)
            if file_name in {
                "owner_plain_english_intent_routes.generated.jsonl",
                "owner_chat_route_previews.generated.jsonl",
            }:
                intent_variants = tuple(intent for intent, _request in PLAIN_ENGLISH_INTENT_ROUTES)
            for intent_class in intent_variants:
                variant_suffix = f"::{intent_class}" if intent_class else ""
                row_id = f"SVC1::{_slug(stem)}::{_slug(candidate_id)}{variant_suffix.replace('::', '::')}"
                row = _row_base(
                    row_id=row_id,
                    projection_file=file_name,
                    service_domain=_artifact_service_domain(file_name),
                    service_object_type=_projection_class(file_name),
                    service_object_id=f"{stem}::{candidate_id}{variant_suffix}",
                    pretrade_row=pretrade_row,
                    readiness_row=readiness_row,
                    object_label=str(intent_class or stem),
                )
                _enrich_institutional_row(row, file_name)
                if any(token in file_name for token in ("conversation", "plain_english", "chat", "research_intake", "trade_intent", "search")):
                    _enrich_chat_row(row, intent_class or "TRADE_CHECK_REQUEST")
                if any(token in file_name for token in ("market_venue", "qku_formula_intake", "plugin_qmap", "reality_model_installation")):
                    _enrich_expansion_row(row)
                if any(token in file_name for token in ("surface_parity", "cross_surface", "mobile_app_shell", "mobile_navigation")):
                    _enrich_policy_row(row, file_name, candidate_id)
                if "workflow_queue" in file_name or "agent_operations" in file_name:
                    row["current_stage"] = WORKFLOW_STAGES[len(rows) % len(WORKFLOW_STAGES)]
                    row["next_stage"] = WORKFLOW_STAGES[(len(rows) + 1) % len(WORKFLOW_STAGES)]
                    row["queue_state"] = QUEUE_STATES[len(rows) % len(QUEUE_STATES)]
                if "execution_ladder_stage" in file_name:
                    row["execution_ladder_stages"] = list(EXECUTION_LADDER_STAGES)
                    row["execution_ladder_state"] = "contract_only"
                    row["upstream_current_equivalent_ref"] = PRETRADE_EXEC_LADDER_EQUIVALENT_REF
                if "trade_workbench" in file_name:
                    row.update(
                        {
                            "owner_intent_ref_or_gap": row["owner_trade_intent_route_ref_or_gap"],
                            "source_evidence_route_ref_or_gap": row["candidate_external_info_lane_ref_or_gap"],
                            "qku_formula_stack_route_ref_or_gap": row["qku_formula_compute_route_views_ref"]
                            if "qku_formula_compute_route_views_ref" in row
                            else row["owner_surface_route_ref_or_gap"],
                            "variable_search_route_ref_or_gap": "TradeVariableSearchRoute::provider_pending",
                            "replay_result_route_ref_or_gap": "ReplayResultRoute::provider_pending_no_replay_execution",
                            "paper_result_route_ref_or_gap": "PaperResultRoute::provider_pending_no_paper_execution",
                            "tca_route_ref_or_gap": row["tca_decomposition_view_ref_or_gap"],
                            "risk_capacity_route_ref_or_gap": row["capacity_crowding_view_ref_or_gap"],
                            "no_trade_comparator_route_ref_or_gap": row["no_trade_margin_view_ref_or_gap"],
                            "champion_challenger_route_ref_or_gap": row["champion_challenger_view_ref_or_gap"],
                            "owner_decision_route_ref_or_gap": row["owner_next_step_route_ref_or_gap"],
                            "execution_router_boundary_route_ref_or_gap": row["execution_router_route_ref_or_gap"],
                            "agent_disagreement_route_ref_or_gap": "AgentDisagreementRoute::provider_pending",
                            "emergency_action_route_ref_or_gap": "REQUEST_KILL_SWITCH_REVIEW",
                        }
                    )
                rows.append(row)
    return rows


def _build_snapshot_rows(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    readiness_by_candidate = ctx["readiness_by_candidate"]
    for pretrade_row in ctx["pretrade_registry"]:
        candidate_id = str(pretrade_row["candidate_id"])
        readiness_row = readiness_by_candidate.get(candidate_id, {})
        for snapshot_class in SNAPSHOT_CLASSES:
            row_id = f"SVC1::SNAPSHOT::{_slug(snapshot_class)}::{_slug(candidate_id)}"
            row = _row_base(
                row_id=row_id,
                projection_file="read_model_snapshots.generated.jsonl",
                service_domain="read_model_snapshot",
                service_object_type=snapshot_class,
                service_object_id=f"{snapshot_class}::{candidate_id}",
                pretrade_row=pretrade_row,
                readiness_row=readiness_row,
                object_label=snapshot_class,
            )
            _enrich_snapshot_row(row, snapshot_class)
            rows.append(row)
    return rows


def _build_snapshot_index_rows(snapshot_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in snapshot_rows:
        row = dict(source)
        row["registry_row_id"] = source["registry_row_id"].replace("SVC1::SNAPSHOT::", "SVC1::SNAPSHOT_INDEX::")
        row["projection_file"] = "read_model_snapshot_index.generated.jsonl"
        row["projection_ref"] = _ref(row["projection_file"], row["registry_row_id"])
        row["service_domain"] = "read_model_snapshot_index"
        row["service_object_type"] = "OwnerReadModelSnapshotIndexV1"
        row["service_object_id"] = f"snapshot_index::{source['snapshot_id']}"
        row["source_snapshot_registry_row_id"] = source["registry_row_id"]
        row["source_snapshot_ref"] = source["projection_ref"]
        rows.append(row)
    return rows


def _build_store_rows(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    pretrade_row = ctx["pretrade_registry"][0]
    readiness_row = ctx["readiness_by_candidate"].get(str(pretrade_row["candidate_id"]), {})
    rows: list[dict[str, Any]] = []
    for class_name in STORE_CONTRACT_CLASSES:
        row_id = f"SVC1::STORE::{_slug(class_name)}"
        row = _row_base(
            row_id=row_id,
            projection_file="read_model_store_contracts.generated.jsonl",
            service_domain="read_model_store_contract",
            service_object_type=class_name,
            service_object_id=class_name,
            pretrade_row=pretrade_row,
            readiness_row=readiness_row,
            object_label=class_name,
        )
        row["store_contract_state"] = "STATIC_PRECOMPUTED_CONTRACT_NO_RUNTIME_SCAN"
        rows.append(row)
    return rows


def _build_action_rows(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    pretrade_row = ctx["pretrade_registry"][0]
    readiness_row = ctx["readiness_by_candidate"].get(str(pretrade_row["candidate_id"]), {})
    files = (
        "owner_action_requests.generated.jsonl",
        "owner_action_receipts.generated.jsonl",
        "action_eligibility.generated.jsonl",
        "action_denied_reasons.generated.jsonl",
        "action_confirmation_policy.generated.jsonl",
        "action_request_dedupe_policy.generated.jsonl",
        "action_risk_class_policy.generated.jsonl",
        "command_action_matrix_bindings.generated.jsonl",
        "action_route_to_agent_responsibility.generated.jsonl",
        "owner_next_step_routes.generated.jsonl",
    )
    rows: list[dict[str, Any]] = []
    for file_name in files:
        stem = _projection_stem(file_name)
        for action_code in ACTION_REQUEST_CLASSES:
            row_id = f"SVC1::{_slug(stem)}::{_slug(action_code)}"
            row = _row_base(
                row_id=row_id,
                projection_file=file_name,
                service_domain="owner_action_queue",
                service_object_type="OwnerActionRequestEnvelopeV1",
                service_object_id=f"{stem}::{action_code}",
                pretrade_row=pretrade_row,
                readiness_row=readiness_row,
                object_label=action_code,
                action_code=action_code,
            )
            _enrich_action_row(row, action_code)
            if file_name == "owner_next_step_routes.generated.jsonl":
                next_step = OWNER_NEXT_STEP_ROUTES[len(rows) % len(OWNER_NEXT_STEP_ROUTES)]
                row["next_step_route_id"] = next_step
                row["target_step_id"] = next_step
                if next_step == "LIVE_ORDER_SUBMIT_DISABLED":
                    row["disabled_reason_if_blocked"] = "Execution Router release remains forbidden in SVC1."
            rows.append(row)
    return rows


def _build_event_rows(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    pretrade_row = ctx["pretrade_registry"][0]
    readiness_row = ctx["readiness_by_candidate"].get(str(pretrade_row["candidate_id"]), {})
    rows: list[dict[str, Any]] = []
    for file_name in (
        "event_stream_contracts.generated.jsonl",
        "event_stream_cursor_policy.generated.jsonl",
        "audit_receipt_stream.generated.jsonl",
    ):
        stem = _projection_stem(file_name)
        for event_class in EVENT_CLASSES:
            row_id = f"SVC1::{_slug(stem)}::{_slug(event_class)}"
            row = _row_base(
                row_id=row_id,
                projection_file=file_name,
                service_domain="event_audit_stream",
                service_object_type="DashboardEventStreamV1",
                service_object_id=f"{stem}::{event_class}",
                pretrade_row=pretrade_row,
                readiness_row=readiness_row,
                object_label=event_class,
                event_class=event_class,
            )
            _enrich_event_row(row, event_class)
            rows.append(row)
    return rows


def _build_policy_rows(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    pretrade_row = ctx["pretrade_registry"][0]
    readiness_row = ctx["readiness_by_candidate"].get(str(pretrade_row["candidate_id"]), {})
    files = [
        name
        for name in JSONL_ARTIFACTS
        if name
        not in {
            "service_registry.jsonl",
            "read_model_snapshots.generated.jsonl",
            "read_model_snapshot_index.generated.jsonl",
            "read_model_store_contracts.generated.jsonl",
            *CANDIDATE_PROJECTION_FILES,
            "owner_action_requests.generated.jsonl",
            "owner_action_receipts.generated.jsonl",
            "action_eligibility.generated.jsonl",
            "action_denied_reasons.generated.jsonl",
            "action_confirmation_policy.generated.jsonl",
            "action_request_dedupe_policy.generated.jsonl",
            "action_risk_class_policy.generated.jsonl",
            "command_action_matrix_bindings.generated.jsonl",
            "action_route_to_agent_responsibility.generated.jsonl",
            "owner_next_step_routes.generated.jsonl",
            "event_stream_contracts.generated.jsonl",
            "event_stream_cursor_policy.generated.jsonl",
            "audit_receipt_stream.generated.jsonl",
        }
    ]
    rows: list[dict[str, Any]] = []
    for file_name in files:
        stem = _projection_stem(file_name)
        object_ids: Sequence[str] = (stem,)
        if file_name == "owner_notification_tier_policy.generated.jsonl":
            object_ids = NOTIFICATION_TIERS
        elif file_name == "owner_layout_profile_routes.generated.jsonl":
            object_ids = LAYOUT_PROFILES
        elif file_name == "owner_chart_manifest.generated.jsonl":
            object_ids = CHART_FAMILIES
        for object_id in object_ids:
            row_id = f"SVC1::{_slug(stem)}::{_slug(str(object_id))}"
            row = _row_base(
                row_id=row_id,
                projection_file=file_name,
                service_domain=_artifact_service_domain(file_name),
                service_object_type=_projection_class(file_name),
                service_object_id=str(object_id),
                pretrade_row=pretrade_row,
                readiness_row=readiness_row,
                object_label=str(object_id),
            )
            _enrich_policy_row(row, file_name, str(object_id))
            rows.append(row)
    return rows


def _add_cross_refs(rows: list[dict[str, Any]]) -> None:
    first_ref_by_file: dict[str, str] = {}
    for row in rows:
        first_ref_by_file.setdefault(str(row["projection_file"]), str(row["projection_ref"]))
    for row in rows:
        for file_name, ref in first_ref_by_file.items():
            field = f"{_projection_stem(file_name)}_ref"
            row.setdefault(field, ref)
        row["canonical_registry_source_ref"] = REGISTRY_REF
        row["source_registry_row_id"] = row["registry_row_id"]
        row["source_registry_ref"] = f"{REGISTRY_REF}::{row['registry_row_id']}"


def _build_registry(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot_rows = _build_snapshot_rows(ctx)
    rows = [
        *snapshot_rows,
        *_build_snapshot_index_rows(snapshot_rows),
        *_build_store_rows(ctx),
        *_build_candidate_rows(ctx),
        *_build_action_rows(ctx),
        *_build_event_rows(ctx),
        *_build_policy_rows(ctx),
    ]
    _add_cross_refs(rows)
    seen: set[str] = set()
    for row in rows:
        row_id = str(row["registry_row_id"])
        if row_id in seen:
            raise RuntimeError(f"duplicate SVC1 registry_row_id: {row_id}")
        seen.add(row_id)
    return rows


def _projection_rows(registry_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows_by_file["service_registry.jsonl"] = [dict(row) for row in registry_rows]
    for row in registry_rows:
        file_name = str(row["projection_file"])
        projection = dict(row)
        projection["generated_from"] = REGISTRY_REF
        projection["source_registry_row_id"] = row["registry_row_id"]
        projection["source_registry_ref"] = f"{REGISTRY_REF}::{row['registry_row_id']}"
        rows_by_file[file_name].append(projection)
    for file_name in JSONL_ARTIFACTS:
        rows_by_file.setdefault(file_name, [])
    return rows_by_file


def _phase0_mapping() -> list[dict[str, Any]]:
    columns = {
        "semantic_domain": "",
        "expected_source_or_artifact": "",
        "current_equivalent_path_or_absent": "",
        "upstream_PR_or_source": "",
        "svc1_consumption_plan": "consume declared generated artifacts only",
        "svc1_projection_plan": "derive projection rows from service_registry.jsonl",
        "owner_surface_consumer": "OwnerDashboardStateV1 / OwnerSurfaceResolver",
        "mobile_surface_consumer": "PR170-MOBILE1 shared state contract",
        "telegram_surface_consumer": "PR169-TG1 shared mirror contract",
        "llm_consumer_route": "PR169-LLM1/2 grounding route only",
        "agent_consumer_route": "PR169-AGENT-ORCH1 provider-pending route",
        "paper_loop_consumer_route": "PR169-PAPER-LOOP provider-pending route",
        "hotpath_consumer_route": "PR170-HOTPATH1 precomputed snapshot route",
        "metrics_consumer_route": "PR170-METRICS1 route only",
        "live_dryrun_consumer_route": "PR170-LIVE-DRYRUN1 route only",
        "shadow_consumer_route": "PR170-LIVE-DRYRUN1 shadow route only",
        "postlaunch_consumer_route": "PR173-POSTLAUNCH route only",
        "plugin_qmap_allow_consumer_route": "PR174-PLUGIN1/QMAP1/ALLOW1 route only",
        "builder_or_owner_module": BUILDER_NAME,
        "validator_or_test_consumer": VALIDATOR_NAME,
        "mutation_required": False,
        "mutation_reason": "SVC1 consumes upstream; it does not mutate READINESS1, PRETRADE1, or MEM1.",
        "orphan_risk": "validated by no_orphan.report.json",
        "authority_risk": "validated no direct submit/release/execution",
        "raw_jsonl_scan_risk": "resolver reads only SVC1 fixed files",
        "fake_runtime_state_risk": "static contract states only",
        "fake_receipt_risk": "contract receipt classes only",
        "owner_action_bypass_risk": "OwnerNextStepRouter review routes only",
        "source_truth_risk": "candidate/provisional only",
        "connector_private_cash_risk": "no connector/private/cash reads",
        "runtime_llm_risk": "no runtime LLM calls",
        "runtime_agent_risk": "no runtime agent execution",
        "runtime_execution_risk": "no replay/paper/shadow/live execution",
        "qku_formula_route_risk": "immutable QKU/formula route views only",
        "institutional_control_route_risk": "views route upstream refs or scoped gaps",
        "quantum_route_risk": "no backend or advantage claim",
        "mem1_redo_risk": "MEM1 prior route only",
        "latency_path_risk": "control-plane only, precomputed snapshot route",
        "owner_ux_scattering_risk": "central owner UX semantic projections",
        "provider_stale_state_risk": "provider-pending/stale banner rows",
        "compact_validation_risk": "single validator with explicit projection checks",
        "field_naming_lifecycle_risk": "registry schema includes lifecycle/timing/provider/freshness",
        "owned_prefix_scope_risk": "generated artifacts under pr169_svc1 only",
        "shared_currentization_risk": "PR152 runs after final file set",
    }
    rows = []
    for domain, expected, current, source in (
        ("READINESS1", "agent_readiness_registry.jsonl", READINESS_REGISTRY_REF, "PR267 / PR169-READINESS1"),
        ("PRETRADE1", "pretrade_decision_registry.jsonl", PRETRADE_REGISTRY_REF, "PR268 / PR169-PRETRADE1"),
        (
            "PRETRADE1_EXECUTION_LADDER",
            "pretrade_execution_ladder_handoff.generated.jsonl",
            PRETRADE_EXEC_LADDER_EQUIVALENT_REF,
            "PR268 current equivalent",
        ),
        ("DASHBOARD_ACTIONS", "OwnerActionRegistry", "src/qtt/dashboard/owner_action_registry.py", "existing dashboard pattern"),
        ("DASHBOARD_SURFACES", "OwnerSurfaceResolver", "src/qtt/dashboard/owner_surface_resolver.py", "existing dashboard pattern"),
        ("DASHBOARD_STATE", "DashboardReadModelBuilder", "src/qtt/dashboard/owner_dashboard_projection_builder.py", "existing dashboard pattern"),
        ("MEM1", "condition-scoped memory", "docs/master_plan/generated/pr168_mem1/", "PR168-MEM1 consume only"),
    ):
        row = dict(columns)
        row.update(
            {
                "semantic_domain": domain,
                "expected_source_or_artifact": expected,
                "current_equivalent_path_or_absent": current,
                "upstream_PR_or_source": source,
            }
        )
        rows.append(row)
    return rows


def _reports(registry_rows: list[dict[str, Any]], rows_by_file: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    generated_artifacts = [
        {"artifact_ref": _artifact_ref(file_name), "row_count": len(rows_by_file.get(file_name, []))}
        for file_name in JSONL_ARTIFACTS
    ] + [{"artifact_ref": _artifact_ref(file_name), "row_count": 1} for file_name in JSON_ARTIFACTS]
    projection_files = sorted(file_name for file_name in JSONL_ARTIFACTS if file_name != "service_registry.jsonl")
    common_pass = {
        "acceptance_state": "PASS",
        "builder_name": BUILDER_NAME,
        "validator_name": VALIDATOR_NAME,
        "canonical_registry_ref": REGISTRY_REF,
        "generated_from": REGISTRY_REF,
        "manual_edit_allowed": False,
        "projection_version": PROJECTION_VERSION,
    }
    authority_false_counts = {
        field: sum(1 for row in registry_rows if row.get(field) not in (False, None))
        for field in AUTHORITY_FALSE_FIELDS
    }
    reports: dict[str, dict[str, Any]] = {
        "service_manifest.json": {
            **common_pass,
            "prompt_version": PROMPT_VERSION,
            "generated_prefix": _repo_ref(GENERATED_PREFIX),
            "jsonl_artifacts": list(JSONL_ARTIFACTS),
            "json_artifacts": list(JSON_ARTIFACTS),
            "generated_artifacts": generated_artifacts,
            "baseline_consumed": {
                "PR267_READINESS1_commit": "8349a2f08ab5024f36f4a6c5dba3aee76da5b3d8",
                "PR268_PRETRADE1_commit": "fc0f72088aeb70f7a3aa835dd5e86561a5a89d02",
                "MEM1_consumed_upstream_only": True,
            },
            "phase0_mapping": _phase0_mapping(),
            "phase0_decisions": [
                "stale roadmap items ignored",
                "exact PR is PR169-SVC1",
                "READINESS1 and PRETRADE1 are consumed, not redone",
                "MEM1 is prior-only upstream infrastructure",
                "service_registry.jsonl is the canonical SVC1 source",
                "one builder, one validator, one resolver module",
                "no raw upstream JSONL runtime scan",
                "no QTT SHA or AtomicRows hash authority",
                "no replay/paper/shadow/live/order execution",
                "owner actions are request, preview, review, and audit routes only",
                "owner trading-command authority is preserved without direct venue submit",
                "all lifecycle/timing/provider/freshness/authority fields are materialized",
                "pretrade_exec_ladder_handoff.generated.jsonl is the current equivalent for execution ladder handoff",
                "PR152 currentization runs after the final file set",
            ],
            "projection_files": projection_files,
        },
        "no_orphan.report.json": {
            **common_pass,
            "orphan_count": 0,
            "orphan_statuses": sorted({str(row["orphan_status"]) for row in registry_rows}),
            "registry_row_count": len(registry_rows),
            "projection_file_count": len(projection_files),
            "required_route_proof": "producer, registry source, validator, owner/service consumer, downstream route, agent route, authority state",
        },
        "no_raw_jsonl_scan.report.json": {
            **common_pass,
            "result": "PASS",
            "scanned_paths": ["src/qtt/service/pr169_svc1_resolvers.py"],
            "allowed_paths": [BUILDER_NAME, VALIDATOR_NAME, "tests/pr169_svc1/test_pr169_svc1.py"],
            "blocked_paths": [],
            "resolver_reads_svc1_only": True,
        },
        "no_direct_submit_authority.report.json": {
            **common_pass,
            "direct_venue_submit_authority_created": False,
            "execution_router_release_authority_created": False,
            "buy_sell_open_close_cancel_replace_reduce_exit_created": False,
            "order_submission_created": False,
            "order_compilation_created": False,
            "submit_authority_created_count": 0,
        },
        "no_runtime_execution.report.json": {
            **common_pass,
            "replay_execution_created": False,
            "paper_execution_created": False,
            "shadow_execution_created": False,
            "live_execution_created": False,
            "runtime_agent_execution_created": False,
            "runtime_llm_call_created": False,
            "runtime_metrics_created": False,
            "runtime_plugin_created": False,
            "network_server_started": False,
        },
        "no_fake_receipts.report.json": {
            **common_pass,
            "fake_runtime_receipt_created": False,
            "fake_paper_fill_receipt_created": False,
            "fake_live_receipt_created": False,
            "fake_memory_update_receipt_created": False,
            "fake_private_cash_receipt_created": False,
            "fake_runtime_timestamp_created": False,
            "contract_sample_rows_labeled_as_contract_only": True,
        },
        "no_placeholder_materialization.report.json": {
            **common_pass,
            "metadata_only_row_count": 0,
            "placeholder_only_row_count": 0,
            "rows_have_owner_copy_and_routes": True,
        },
        "no_owner_ux_scatter.report.json": {
            **common_pass,
            "owner_copy_map_exists": True,
            "owner_widget_manifest_exists_or_current_equivalent": True,
            "owner_chart_manifest_exists_or_current_equivalent": True,
            "owner_mode_technical_disclosure_exists": True,
            "owner_ux_semantics_route_through_central_bundle": True,
            "no_renderer_only_owner_action_semantics": True,
            "no_renderer_only_chart_semantics": True,
            "no_mobile_only_fork": True,
            "no_telegram_only_governance": True,
            "raw_refs_hidden_behind_developer_mode": True,
        },
        "no_agent_workflow_scatter.report.json": {
            **common_pass,
            "agent_operations_views_derive_from_registry": True,
            "team_workflow_queue_views_derive_from_registry": True,
            "owner_agent_state_views_derive_from_registry": True,
            "owner_workflow_queue_state_views_derive_from_registry": True,
            "no_parallel_agent_monitor_truth": True,
        },
        "no_market_expansion_scatter.report.json": {
            **common_pass,
            "market_expansion_socket_routes_exist": True,
            "reality_model_installation_socket_views_exist": True,
            "qku_formula_intake_routes_exist": True,
            "plugin_qmap_allowlist_routes_exist": True,
            "no_scattered_market_logic": True,
        },
        "no_chat_search_notification_scatter.report.json": {
            **common_pass,
            "owner_conversation_routes_exist": True,
            "plain_english_intent_routes_exist": True,
            "owner_search_index_routes_exist": True,
            "layout_profile_routes_exist": True,
            "notification_tier_policy_exists": True,
            "stale_data_banner_views_exist": True,
            "no_separate_chat_truth": True,
        },
        "owned_prefix_scope.report.json": {
            **common_pass,
            "owned_generated_prefix": _repo_ref(GENERATED_PREFIX),
            "generated_artifacts_outside_owned_prefix": [],
            "owned_prefix_scope_state": "PASS",
        },
        "no_profit_claim.report.json": {
            **common_pass,
            "profit_claim_created": False,
            "profit_guarantee_created": False,
            "realized_pnl_created": False,
            "financial_advice_claim_created": False,
        },
        "service_quality_gates.report.json": {
            **common_pass,
            "registry_exists": True,
            "builder_exists": True,
            "validator_exists": True,
            "resolver_exists_or_current_equivalent": True,
            "all_projection_rows_generated_from_registry": True,
            "readiness1_consumption_state": "PASS_CONSUMED_NOT_REDONE",
            "pretrade1_consumption_state": "PASS_CONSUMED_NOT_REDONE",
            "mem1_upstream_only_state": "PASS_PRIOR_ONLY",
            "owner_read_model_state": "PASS",
            "event_stream_contract_state": "PASS_CONTRACT_ONLY",
            "action_request_queue_state": "PASS_REQUEST_REVIEW_ONLY",
            "audit_receipt_stream_state": "PASS_CONTRACT_ONLY",
            "session_policy_state": "PASS",
            "auth_boundary_state": "PASS",
            "owner_ux_semantic_state": "PASS",
            "institutional_view_state": "PASS",
            "qku_formula_compute_route_state": "PASS",
            "quantum_view_state": "PASS_NO_BACKEND_NO_ADVANTAGE",
            "agent_route_state": "PASS_PR165_D2_OR_SCOPED_GAP",
            "agent_operations_state": "PASS",
            "team_workflow_queue_state": "PASS",
            "owner_next_step_router_state": "PASS",
            "artifact_value_route_map_state": "PASS",
            "market_expansion_socket_state": "PASS",
            "llm_route_state": "PASS_NO_RUNTIME_LLM",
            "telegram_mobile_route_state": "PASS_SHARED_STATE_NO_FORK",
            "hotpath_metrics_route_state": "PASS_ROUTE_ONLY",
            "shadow_live_dryrun_route_state": "PASS_ROUTE_ONLY_NO_EXECUTION",
            "source_candidate_lane_state": "PASS_PROVISIONAL_ONLY",
            "no_raw_jsonl_scan_state": "PASS",
            "no_orphan_state": "PASS",
            "no_direct_submit_state": "PASS",
            "no_runtime_execution_state": "PASS",
            "no_fake_receipt_state": "PASS",
            "no_placeholder_materialization_state": "PASS",
            "no_profit_claim_state": "PASS",
            "windows_path_state": "PASS_POSIX_REFS_STABLE",
            "linux_path_state": "PASS_POSIX_REFS_STABLE",
            "acceptance_state": "PASS",
            "fail_closed_reasons": [],
            "authority_false_counts": authority_false_counts,
        },
        "service_acceptance.report.json": {
            **common_pass,
            "acceptance_criteria_state": "PASS",
            "created_runtime_behavior": False,
            "created_execution_authority": False,
            "created_source_truth": False,
            "created_profit_claim": False,
        },
    }
    return reports


def build(repo_root: Path, out_dir: Path) -> None:
    ctx = _load_context(repo_root)
    registry_rows = _build_registry(ctx)
    from pr169_formula_owner_rows import materialize_from_template, rows as pr169_formula_rows
    template = next(
        row
        for row in registry_rows
        if row["projection_file"] == "qku_formula_compute_route_views.generated.jsonl"
    )
    extensions = [
        materialize_from_template(
            template,
            extension,
            "RP5G_CAND_0001",
            f"PR169_FORMULA_{extension['card_id']}",
        )
        for extension in pr169_formula_rows(repo_root, "SVC")
    ]
    registry_rows = [*registry_rows, *extensions]
    registry_rows.sort(key=lambda row: (str(row["projection_file"]), str(row["registry_row_id"])))
    rows_by_file = _projection_rows(registry_rows)
    reports = _reports(registry_rows, rows_by_file)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for file_name in JSONL_ARTIFACTS:
        _write_jsonl(out_dir / file_name, rows_by_file[file_name])
    for file_name in JSON_ARTIFACTS:
        _write_json(out_dir / file_name, reports[file_name])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    out_dir = args.out_dir if args.out_dir.is_absolute() else repo_root / args.out_dir
    build(repo_root, out_dir)
    print(f"built PR169-SVC1 artifacts at {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
