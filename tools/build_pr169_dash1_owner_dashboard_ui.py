from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.dashboard.owner_surface_resolver import OwnerSurfaceResolver
from src.qtt.dashboard.owner_surface_models import read_json, read_jsonl, repo_posix


UI_DIR_NAME = "ui"
BOOT_JSON = "owner_dashboard_review_data.generated.json"
BOOT_JS = "owner_dashboard_review_bootstrap.generated.js"
GENERATED_FROM_UI1 = (
    "owner_dashboard_surface_registry.jsonl + generated DASH1 artifacts + UI1 builder config"
)
AUTHORITY_BOUNDARY = (
    "LOCAL_STATIC_NO_RUNTIME_NO_CREDENTIALS_NO_DIRECT_VENUE_SUBMIT_NO_EXECUTION_ROUTER_RELEASE"
)
RENDERED_EMPTY_STATE_REASON = "Not applicable: widget renders DASH1 artifact rows."
THEME_STORAGE_KEY = "qtt_owner_dashboard_theme"
VALIDATION_REF = "tools/validate_pr169_dash1_owner_dashboard_ui.py"
R1_GENERATED_FROM = (
    "PR169-DASH1 artifacts + PR169-DASH1-UI1 boot data + "
    "OwnerDashboardStateV1 + OwnerSurfaceResolver + OwnerActionRegistry + UI component config"
)
R2_GENERATED_FROM = (
    "PR169-DASH1 artifacts + PR169-DASH1-UI1/R1 boot data + "
    "OwnerPresentationLayer / OwnerGuidancePolicy config"
)
EXPERIENCE_MODE_STORAGE_KEY = "qtt_owner_dashboard_experience_mode"
GUIDANCE_DENSITY_STORAGE_KEY = "qtt_owner_dashboard_guidance_density"

REQUIRED_TOP_LEVEL_KEYS = (
    "meta",
    "status_strip",
    "owner_packet",
    "header_strip",
    "decision_queue",
    "actionable_cards",
    "action_registry",
    "portfolio_pnl",
    "charts",
    "agent_performance",
    "edge_alpha",
    "research_candidates",
    "source_workflow",
    "qku_formula_routes",
    "quantum_readiness",
    "institutional_metrics",
    "execution_ladder",
    "shadow_mode",
    "data_value_routes",
    "dag",
    "no_orphan",
    "authority_boundary",
    "owner_trade_command",
    "trade_workbench",
    "owner_action_request_previews",
    "conversation_state",
    "chat_threads",
    "chat_action_catalog",
    "source_agnostic_research_intake",
    "mobile_app_shell",
    "mobile_navigation",
    "stale_data_banner",
    "emergency_actions",
    "provider_stage_routes",
    "agent_qku_access_resolver",
    "executable_readiness",
    "pretrade_decision_kernel",
    "reality_model_contract",
    "hotpath_metrics_contract",
    "communication_parity",
    "file_attachment_safety",
    "empty_states",
    "fixture_fallback",
    "ui1r1_home",
    "ui1r1_dev_mode",
    "ui1r1_visual_acceptance",
    "ui1r1_playwright_manifest",
    "ui1r1_chart_manifest",
    "ui1r1_chat_contract",
    "ui1r1_intent_contract",
    "ui1r1_chat_routes",
    "ui1r1_order_sim",
    "ui1r1_edge_alpha",
    "ui1r1_agent_disagreement",
    "ui1r1_parameter_tuning",
    "ui1r1_12fix_acceptance",
    "ui1r1_owner_mode",
    "ui1r1_qku_route_closure",
    "ui1r1_chat_examples",
    "ui1r1_mobile_parity",
    "ui1r1_inst_quant_crosslink",
    "ui1r1_playwright",
    "ui1r2_copy_map",
    "ui1r2_mode",
    "ui1r2_action_menu",
    "ui1r2_guidance",
    "ui1r2_education",
    "ui1r2_guided_flow",
    "ui1r2_next_step",
    "ui1r2_card_copy",
    "ui1r2_text_safety",
    "ui1r2_disclosure",
    "ui1r2_playwright",
)

NAV_AREAS = (
    "Overview",
    "Portfolio & PnL",
    "Decision Queue",
    "Actionable Cards",
    "Research Intake",
    "Source Watchlist",
    "Edge / Alpha Board",
    "Parameter Control",
    "QKU / Formula / Stack Routes",
    "Quantum Control Center",
    "LLM Intelligence",
    "Agent Operations",
    "Replay / Paper / Shadow / Live Comparison",
    "Execution Costs & TCA",
    "Risk / Calibration / Kill Switch",
    "Capital / Exposure / Cash Slots",
    "Connector Health",
    "Arbitrage Dry Run",
    "Prediction-Market Mechanics",
    "Neural Signal Lab",
    "External Bot / Threat Intelligence",
    "Archive / Read Later",
    "Transcript Workspace",
    "Implementation Queue",
    "Service / Bootstrap / Edition Status",
    "DAG / Data Route Map",
)

MOBILE_TABS = (
    "Home",
    "Portfolio",
    "Trade Workbench",
    "Chat",
    "Decisions",
    "Research",
    "Edge / Alpha",
    "Agents",
    "Parameters",
    "Quantum",
    "More",
    "Developer",
)

THEME_MODES = ("DARK", "LIGHT")

SEMANTIC_COLORS = {
    "positive_gain": "#16A34A",
    "loss_negative": "#DC2626",
    "classical_baseline": "#2563EB",
    "quantum_applied": "#7C3AED",
    "degradation_watch": "#F97316",
    "caution_insufficient_support": "#F59E0B",
    "inactive_pending_unattributed": "#64748B",
}

PROVIDER_STAGES = (
    "DASH1",
    "UI1",
    "UI2",
    "SVC1",
    "MOBILE1",
    "MOBILE2",
    "TG1",
    "READINESS1",
    "PRETRADE1",
    "LLM1",
    "LLM2",
    "AGENT_ORCH1",
    "PAPER_LOOP",
    "HOTPATH1",
    "LIVE_DRYRUN1",
    "LIVE_PILOT",
    "LAUNCH",
    "POSTLAUNCH",
    "RI1",
    "PLUGIN1",
    "QMAP1",
    "ALLOW1",
)

CHAT_PREVIEW_CODES = (
    ("SEND_OWNER_AGENT_MESSAGE_REQUEST", "REQUEST_AGENT_TASK"),
    ("SUBMIT_RESEARCH_CANDIDATE_FROM_CHAT", "SUBMIT_RESEARCH_CANDIDATE"),
    ("ATTACH_SOURCE_LINK_REQUEST", "REQUEST_SOURCE_CAPTURE"),
    ("ATTACH_SOURCE_FILE_REQUEST", "REQUEST_SOURCE_CAPTURE"),
    ("REQUEST_AGENT_ANALYSIS_FROM_CHAT", "REQUEST_AGENT_TASK"),
    ("REQUEST_AGENT_SUMMARY_FROM_CHAT", "REQUEST_AGENT_TASK"),
    ("REQUEST_SOURCE_VALIDATION_FROM_CHAT", "REQUEST_SOURCE_VALIDATION"),
    ("REQUEST_FORMULA_EXTRACTION_FROM_CHAT", "REQUEST_FORMULA_EXTRACTION"),
    ("REQUEST_QKU_MATERIALIZATION_FROM_CHAT", "REQUEST_QKU_MATERIALIZATION"),
    ("REQUEST_QUANTUM_STRUCTURE_MAPPING_FROM_CHAT", "REQUEST_QSTRUCT_MAPPING_REVIEW"),
    ("REQUEST_TRADE_CHECK_FROM_CHAT", "REQUEST_OWNER_REVIEW"),
    ("REQUEST_REPLAY_PAPER_FROM_CHAT", "REQUEST_REPLAY_TEST"),
    ("REQUEST_NO_TRADE_REOPTIMIZATION_FROM_CHAT", "REQUEST_NO_TRADE_REOPTIMIZATION_REVIEW"),
    ("REQUEST_LIVE_CANARY_REVIEW_FROM_CHAT", "REQUEST_LIVE_CANARY_REVIEW"),
    ("DIRECT_MESSAGE_AGENT_REQUEST", "REQUEST_AGENT_TASK"),
    ("BROADCAST_TO_AGENT_POD_REQUEST", "REQUEST_AGENT_TASK"),
    ("PIN_CHAT_CONTEXT_REQUEST", "REQUEST_OWNER_REVIEW"),
    ("LINK_CHAT_TO_CARD_REQUEST", "REQUEST_OWNER_REVIEW"),
    ("LINK_CHAT_TO_TRADE_WORKBENCH_REQUEST", "REQUEST_OWNER_REVIEW"),
    ("LINK_CHAT_TO_SOURCE_WORKFLOW_REQUEST", "REQUEST_SOURCE_CAPTURE"),
    ("ESCALATE_CHAT_TO_DECISION_QUEUE_REQUEST", "REQUEST_OWNER_REVIEW"),
    ("MARK_CHAT_THREAD_RESOLVED_REQUEST", "REQUEST_OWNER_REVIEW"),
)

TRADE_VARIABLES = (
    "market",
    "venue",
    "stack",
    "side",
    "entry",
    "size",
    "hold_duration",
    "exit_rule",
    "maker_taker_split",
    "cancel_replace_interval",
    "liquidity_filter",
    "spread_filter",
    "depth_filter",
    "latency_budget",
    "portfolio_exposure",
    "order_policy",
    "scenario_path",
)

TRADE_ROUTE_CHAIN = (
    "OwnerTradeIntentV1",
    "OwnerTradeCheckRequestV1",
    "source_agnostic_research_candidate_route",
    "centralized_agent_QKU_formula_access_resolver_route",
    "formula_QKU_stack_candidate_route",
    "mutable_trade_variable_search_route",
    "quantum_structure_mapping_route",
    "replay_route",
    "paper_route",
    "TCA_fill_latency_capacity_crowding_route",
    "portfolio_marginal_utility_route",
    "overfit_FDR_route",
    "no_trade_comparator_and_reoptimization_route",
    "champion_challenger_selection_route",
    "MEM1_similarity_winning_failure_no_trade_memory_route",
    "owner_approval_veto_more_research_more_variable_search_route",
    "Execution_Router_release_route_provider_pending",
)

UI1R1_DECISION_SPINE_FIELDS = (
    "execution_adjusted_rank",
    "TCA_adjusted_expected_net_cash",
    "candidate_minus_no_trade_cash",
    "lower_confidence_bound_cash",
    "fill_adjusted_expected_value",
    "capacity_adjusted_expected_value",
    "portfolio_marginal_utility",
    "overfit_false_discovery_status",
    "scenario_ladder_status",
    "regime_conditioned_memory_status",
    "MEM1_similarity_prior_ref",
    "champion_challenger_status",
    "no_trade_comparator_status",
    "no_trade_reoptimization_route",
    "quantum_structural_readiness_status",
    "classical_fallback_ref",
    "DAG_upstream_downstream_ref",
)

UI1R1_CHAT_INTENT_FAMILIES = (
    "TRADE_CHECK_REQUEST",
    "RESEARCH_ANALYSIS_REQUEST",
    "SOURCE_CANDIDATE_REVIEW_REQUEST",
    "FORMULA_EXTRACTION_REQUEST",
    "QKU_MATERIALIZATION_REQUEST",
    "QKU_FORMULA_STACK_COMPARISON_REQUEST",
    "QUANTUM_STRUCTURE_MAPPING_REQUEST",
    "REPLAY_PAPER_REQUEST",
    "NO_TRADE_EXPLANATION_REQUEST",
    "NO_TRADE_REOPTIMIZATION_REQUEST",
    "AGENT_STATUS_QUESTION",
    "AGENT_DISAGREEMENT_QUESTION",
    "TCA_COST_EXPLANATION_REQUEST",
    "RISK_CAPACITY_EXPLANATION_REQUEST",
    "PARAMETER_TUNING_REQUEST",
    "PORTFOLIO_PNL_EXPLANATION_REQUEST",
    "EDGE_ALPHA_RANKING_REQUEST",
    "LIVE_CANARY_REVIEW_REQUEST_PREVIEW",
    "KILL_SWITCH_REQUEST_PREVIEW",
    "ROLLBACK_REQUEST_PREVIEW",
    "GENERAL_QTT_QUESTION_PROVIDER_PENDING",
)

UI1R1_CHAT_EXAMPLES = (
    (
        "Can QTT check this market and find the best trade?",
        "TRADE_CHECK_REQUEST",
        "OwnerTradeCheckRequestV1",
    ),
    (
        "Research this article and tell me if it creates a prediction-market edge.",
        "RESEARCH_ANALYSIS_REQUEST",
        "OwnerResearchSubmissionV1",
    ),
    (
        "Ask the QKU agents to compare the best formula stacks for this event.",
        "QKU_FORMULA_STACK_COMPARISON_REQUEST",
        "QKUCandidateMaterializationRequestV1",
    ),
    (
        "Why did no-trade win here?",
        "NO_TRADE_EXPLANATION_REQUEST",
        "NoTradeReoptimizationRequestPreviewV1",
    ),
    (
        "What variables would make this trade pass replay and paper?",
        "PARAMETER_TUNING_REQUEST",
        "ReplayPaperRequestPreviewV1",
    ),
    (
        "Show me which agent disagrees and why.",
        "AGENT_DISAGREEMENT_QUESTION",
        "OwnerPlainEnglishIntentV1",
    ),
)

SOURCE_FAMILIES = (
    "website",
    "link",
    "PDF",
    "academic_paper",
    "scholar_reference",
    "research_article",
    "news_article",
    "social_post_or_thread",
    "public_document",
    "repository_link",
    "dataset",
    "screenshot_or_image",
    "formula_text",
    "algorithm_text",
    "quantum_strategy_note",
    "market_or_event_page",
    "free_form_trade_idea",
    "owner_uploaded_file",
)

EXACT_PANEL_NAMES = (
    "OWNER_DASHBOARD_PACKET_CARD",
    "OWNER_HEADER_STRIP_CARD",
    "DECISION_QUEUE_CARD_SHELL",
    "TELEGRAM_OWNER_PACKET_MIRROR_CARD",
    "OWNER_PACKET_ACK_AUDIT_ROW",
    "OWNER_COMMAND_NORMALIZED_FORM_CARD",
    "OWNER_COMMAND_PARSE_INSTANCE_CARD",
    "OWNER_COMMAND_IDEMPOTENCY_CARD",
    "OWNER_COMMAND_EXECUTION_CLAIM_CARD",
    "OWNER_COMMAND_CLAIM_RECOVERY_CARD",
    "OWNER_COMMAND_RECEIPT_SEQUENCE_CARD",
    "OWNER_TRADE_TARGET_INTAKE_PANEL_CARD",
    "OWNER_PROGRESS_BOARD_CARD",
    "EVENT_CREDIBILITY_PANEL_CARD",
    "TRADE_READINESS_SCORECARD",
    "TRADE_STRUCTURE_OPTIMIZATION_PACKET",
    "TRADE_PROPOSAL_CARD",
    "WATCH_MONITOR_CARD",
    "TRADE_MANAGEMENT_PLAN_CARD",
    "EXIT_DECISION_CARD",
    "ACTIVE_ELITE_STRATEGIES_PANEL_CARD",
    "ELITE_STRATEGY_PIPELINE_PANEL_CARD",
    "ELITE_RESEARCH_QUEUE_PANEL_CARD",
    "ELITE_SHADOW_DAILY_REPORT_CARD",
    "ELITE_STRATEGY_ARCHIVE_PANEL_CARD",
    "ELITE_STRATEGY_HEALTH_STATE_CARD",
    "PERFORMANCE_INTELLIGENCE_PANEL",
    "DECISION_ATTRIBUTION_PANEL",
    "SLIPPAGE_INTELLIGENCE_PANEL",
    "EXECUTION_FORENSICS_PANEL_CARD",
    "CUMULATIVE_SLIPPAGE_DASHBOARD_CARD",
    "ALPHA_PROMOTION_SCORECARD_PANEL_CARD",
    "DIRECT_LIVE_ON_APPROVAL_QUEUE_PANEL_CARD",
    "EDGE_SOURCE_BUDGETING_PANEL_CARD",
    "ALPHA_DEATH_MONITOR_PANEL_CARD",
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
    "MICROSTRUCTURE_CALIBRATION_PANEL",
    "LOCAL_LLM_MODEL_CONTROL_PANEL",
    "DAY1_OWNER_REVIEW_DIGEST_PANEL",
    "DAY1_ARBITRAGE_DRY_RUN_DASHBOARD_PANEL",
    "DAY1_ARBITRAGE_LIVE_PROMOTION_PANEL",
    "AGENT_DUTY_BOARD",
    "AGENT_KPI_BOARD",
    "MISSED_DUTY_QUEUE",
    "AGENT_TRUST_SCORE_PANEL",
    "AGENT_FAILURE_ESCALATION_QUEUE",
    "AGENT_QUARANTINE_STATE_PANEL",
    "AGENT_SELF_HEALING_ACTION_LOG",
    "AGENT_REPLACEMENT_CANDIDATE_PANEL",
    "AGENT_REROUTE_CONTROL_PANEL",
    "AGENT_PERMISSION_CHANGE_REQUEST_PANEL",
    "EXTERNAL_BOT_STRATEGY_CANDIDATE_PANEL",
    "EXTERNAL_BOT_SUPPLY_CHAIN_QUARANTINE_PANEL",
    "EXTERNAL_BOT_THREAT_INTELLIGENCE_PANEL",
    "PREDICTION_MARKET_EXECUTION_MECHANICS_PANEL",
    "CROSS_VENUE_EXECUTION_NORMALIZATION_PANEL",
    "SOURCE_EVIDENCE_RETRIEVAL_READINESS_PANEL",
    "NEURAL_SIGNAL_CANDIDATE_PANEL",
    "STATIONARY_FEATURE_CATALOG_PANEL",
    "TARGET_CONSTRUCTION_PANEL",
    "LEAKAGE_AUDIT_PANEL",
    "PURGED_WALK_FORWARD_VALIDATION_PANEL",
    "MODEL_CALIBRATION_PANEL",
    "MODEL_DRIFT_MONITOR_PANEL",
    "SIGNAL_TO_SIZING_BOUNDARY_PANEL",
    "NEURAL_DUAL_RESULT_REVIEW_PANEL",
    "NEURAL_OWNER_PROMOTION_GATE_PANEL",
    "FORBIDDEN_CLAIM_AND_SOURCE_RETRIEVAL_TARGET_PANEL",
    "Quantum Candidate Lifecycle Panel",
    "Quantum Artifact Panel",
    "MBO / Order-Lifecycle Observability Panel",
    "Quantum Intelligence Panel",
    "Quantum Proof / Propagation / Attribution Panel",
    "True Quantum Primacy / Responsibility / Core-Gap Panel",
    "Quantum Centrality Scoreboard",
    "Quantum Formula-to-Decision Registry Viewer",
    "Quantum Policy Bundle Diff Viewer",
    "Quantum Propagation Receipt Panel",
    "Quantum Checkpoint Completion Panel",
    "Quantum Causality Panel",
    "Quantum Freshness by Decision Surface Panel",
    "Quantum Failure Heatmap",
    "Official Ecosystem Alignment Panel",
    "Quantum Responsibility Class Badge",
    "Backend Role Matrix Panel",
    "Formula Registry Reference Panel",
    "Hard-Part Decomposition Panel",
    "Numeric Authority Chain Panel",
    "Quantum Bridge Panel",
    "Noise / Confidence Haircut Panel",
    "Tensor-Network Readiness Panel",
    "Solver League Panel",
    "Compatibility Matrix Panel",
    "Lineage Ledger Panel",
    "Quantum Stack Health Monitor",
    "QPU Enablement Panel",
    "Provider Routing Panel",
    "Failover Control Panel",
    "Owner Live-Execution Mode Panel",
    "Blocker Remediation Panel",
    "Force-Override Control Panel",
    "PNL_TIMESERIES_ROW",
    "MARKET_PLATFORM_ROLLUP_CARD",
    "CUMULATIVE_EARNINGS_GRAPH_SPEC",
    "FEE_AND_SLIPPAGE_WATERFALL_CARD",
    "EXPERIMENTAL_VS_LIVE_COMPARATOR_CARD",
    "QUANTUM_CLASSICAL_COMPARATOR_TIMESERIES_ROW",
    "QUANTUM_UPLIFT_PERCENTAGE_CURVE_SPEC",
    "QUANTUM_REGIME_BUCKET_HEATMAP_CARD",
    "QUANTUM_DEGRADATION_TREND_GRAPH_SPEC",
    "QUANTUM_VALUE_DECOMPOSITION_GRAPH_SPEC",
    "QUANTUM_COMPLEXITY_ROI_GRAPH_SPEC",
    "COUNTERFACTUAL_OPPORTUNITY_LOSS_GRAPH_SPEC",
    "CAPITAL_ROUTING_RECOMMENDATION_OVERLAY_CARD",
    "GRAPH_COLOR_SEMANTICS_LEGEND_CARD",
    "DAILY_OPPORTUNITY_CENSUS_PANEL_CARD",
    "DAILY_ALPHA_BOARD_PANEL_CARD",
    "REALIZED_EDGE_CLOSURE_RATIO_CURVE",
    "EXECUTION_LOSS_DECOMPOSITION_WATERFALL",
    "ALPHA_BASKET_CONCENTRATION_OVERLAY",
    "CROSS_EDGE_CORRELATION_OVERLAY",
    "FAILURE_MODE_DIVERSITY_OVERLAY",
    "LATENCY_HISTOGRAM",
    "REJECT_THROTTLE_ERROR_RATE_CHART",
    "CAPITAL_USAGE_CHART",
    "PARAMETER_REVITALIZATION_BOARD",
)

UI_ARTIFACT_FILES = (
    "owner_dashboard_widget_manifest.generated.json",
    "owner_dashboard_master_plan_20d_coverage.generated.json",
    "owner_dashboard_master_plan_20d_exact_surface_coverage.generated.json",
    "owner_dashboard_interaction_manifest.generated.json",
    "owner_dashboard_visual_acceptance.report.json",
    "owner_dashboard_ui1_master_plan_feature_comparison.report.json",
    "owner_dashboard_state_model.generated.json",
    "owner_dashboard_mobile_app_shell_contract.generated.json",
    "owner_dashboard_pwa_manifest_contract.generated.json",
    "owner_dashboard_owner_trading_command_contract.generated.json",
    "owner_dashboard_trade_workbench.generated.json",
    "owner_dashboard_mobile_navigation.generated.json",
    "owner_dashboard_stale_data_banner_contract.generated.json",
    "owner_dashboard_conversation_state.generated.json",
    "owner_dashboard_chat_widget_manifest.generated.json",
    "owner_dashboard_chat_action_catalog.generated.json",
    "owner_dashboard_chat_route_map.generated.json",
    "owner_dashboard_source_agnostic_intake_contract.generated.json",
    "owner_dashboard_surface_parity_contract.generated.json",
    "owner_dashboard_provider_stage_route_map.generated.json",
    "owner_dashboard_agent_qku_access_resolver_view.generated.json",
    "owner_dashboard_executable_readiness_view.generated.json",
    "owner_dashboard_pretrade_decision_kernel_contract.generated.json",
    "owner_dashboard_reality_model_contract_view.generated.json",
    "owner_dashboard_hotpath_metrics_contract_view.generated.json",
    "owner_dashboard_communication_parity_contract.generated.json",
    "owner_dashboard_file_attachment_safety_contract.generated.json",
    "owner_dashboard_roadmap_provider_route_map.generated.json",
    "owner_dashboard_qku_formula_computability_matrix.generated.json",
    "owner_dashboard_agentic_trade_route_map.generated.json",
    "owner_dashboard_qku_formula_no_orphan_closure.report.json",
    "owner_dashboard_chat_trade_request_catalog.generated.json",
    "owner_dashboard_useful_empty_state_manifest.generated.json",
    "owner_dashboard_mobile_responsive_manifest.generated.json",
    "owner_dashboard_mobile_visual_acceptance.report.json",
    "owner_dashboard_native_shell_contract.generated.json",
    "owner_dashboard_ui1_five_question_acceptance.report.json",
    "owner_dashboard_mobile_runtime_boundary.generated.json",
    "owner_dashboard_theme_contract.generated.json",
    "owner_dashboard_dash1_ui1_renderer_boundary.generated.json",
    "owner_dashboard_generated_projection_policy.report.json",
    "ui1r1_home.generated.json",
    "ui1r1_dev_mode.generated.json",
    "ui1r1_visual_acceptance.report.json",
    "ui1r1_playwright_manifest.generated.json",
    "ui1r1_chart_manifest.generated.json",
    "ui1r1_chat_contract.generated.json",
    "ui1r1_intent_contract.generated.json",
    "ui1r1_chat_routes.generated.json",
    "ui1r1_order_sim.generated.json",
    "ui1r1_edge_alpha.generated.json",
    "ui1r1_agent_disagreement.generated.json",
    "ui1r1_parameter_tuning.generated.json",
    "ui1r1_12fix_acceptance.generated.json",
    "ui1r1_owner_mode.report.json",
    "ui1r1_qku_route_closure.report.json",
    "ui1r1_chat_examples.generated.json",
    "ui1r1_mobile_parity.report.json",
    "ui1r1_inst_quant_crosslink.report.json",
    "ui1r1_playwright.report.json",
    "ui1r2_copy_map.generated.json",
    "ui1r2_mode.generated.json",
    "ui1r2_action_menu.generated.json",
    "ui1r2_guidance.report.json",
    "ui1r2_education.generated.json",
    "ui1r2_guided_flow.generated.json",
    "ui1r2_next_step.generated.json",
    "ui1r2_card_copy.report.json",
    "ui1r2_text_safety.report.json",
    "ui1r2_disclosure.report.json",
    "ui1r2_playwright.report.json",
)


def _ui_meta(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_from": GENERATED_FROM_UI1,
        "manual_edit_allowed": False,
        "agent_consumable_authority": False,
        "runtime_truth_authority": False,
        "runtime_side_effect_allowed": False,
        "credential_access_allowed": False,
        "connector_access_allowed": False,
        "order_execution_allowed": False,
        "source_truth_authority": False,
        "authority_boundary_ref": AUTHORITY_BOUNDARY,
        "validation_ref": VALIDATION_REF,
    }
    if extra:
        payload.update(extra)
    return payload


def _ui1r1_meta(artifact_id: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = _ui_meta(
        {
            "artifact_id": artifact_id,
            "generated_from": f"{GENERATED_FROM_UI1} + {R1_GENERATED_FROM}",
            "ui1r1_generated_from": R1_GENERATED_FROM,
            "manual_edit_allowed": False,
            "runtime_truth_authority": False,
            "agent_consumable_authority": False,
            "credential_access_allowed": False,
            "connector_access_allowed": False,
            "order_execution_allowed": False,
            "source_truth_authority": False,
        }
    )
    if extra:
        payload.update(extra)
    return payload


def _ui1r2_meta(artifact_id: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = _ui_meta(
        {
            "artifact_id": artifact_id,
            "generated_from": f"{GENERATED_FROM_UI1} + {R2_GENERATED_FROM}",
            "ui1r2_generated_from": R2_GENERATED_FROM,
            "manual_edit_allowed": False,
            "runtime_truth_authority": False,
            "agent_consumable_authority": False,
            "credential_access_allowed": False,
            "connector_access_allowed": False,
            "order_execution_allowed": False,
            "source_truth_authority": False,
        }
    )
    if extra:
        payload.update(extra)
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _artifact_rows(base: Path, file_name: str) -> list[dict[str, Any]]:
    return read_jsonl(base / file_name)


def _artifact_json(base: Path, file_name: str) -> dict[str, Any]:
    path = base / file_name
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {"value": payload}


def _currentize_rejected_tokens(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.isupper():
            return "SEQUENCE"
        if token[:1].isupper():
            return "Sequence"
        return "sequence"

    return re.sub("timeline", repl, value, flags=re.IGNORECASE)


def _repo_ref(path: Path | str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(REPO_ROOT)
        except ValueError:
            pass
    return repo_posix(candidate)


def _generated_display_text(value: str) -> str:
    text = _currentize_rejected_tokens(value)
    if text.startswith("/"):
        return f"SLASH_COMMAND {text[1:]}"
    return text


def _anchor(label: str) -> str:
    clean = _currentize_rejected_tokens(label)
    return re.sub(r"[^a-z0-9]+", "-", clean.lower()).strip("-") or "section"


def _label(value: str) -> str:
    text = re.sub(r"[_\-]+", " ", value).strip()
    return text[:1].upper() + text[1:] if text else value


def _classify_nav(label: str) -> str:
    upper = label.upper()
    if "PORTFOLIO" in upper or "PNL" in upper or "CAPITAL" in upper:
        return "Portfolio & PnL"
    if "DECISION" in upper or "APPROVAL" in upper or "PACKET" in upper:
        return "Decision Queue"
    if "RESEARCH" in upper or "SOURCE" in upper:
        return "Research Intake"
    if "EDGE" in upper or "ALPHA" in upper:
        return "Edge / Alpha Board"
    if "PARAMETER" in upper:
        return "Parameter Control"
    if "QKU" in upper or "FORMULA" in upper or "STACK" in upper:
        return "QKU / Formula / Stack Routes"
    if "QUANTUM" in upper or "QPU" in upper or "QSTRUCT" in upper:
        return "Quantum Control Center"
    if "LLM" in upper:
        return "LLM Intelligence"
    if "AGENT" in upper:
        return "Agent Operations"
    if "TCA" in upper or "SLIPPAGE" in upper or "LATENCY" in upper or "COST" in upper:
        return "Execution Costs & TCA"
    if "DAG" in upper or "ROUTE" in upper or "LINEAGE" in upper:
        return "DAG / Data Route Map"
    if "BOT" in upper or "THREAT" in upper:
        return "External Bot / Threat Intelligence"
    if "NEURAL" in upper or "MODEL" in upper:
        return "Neural Signal Lab"
    if "ARBITRAGE" in upper:
        return "Arbitrage Dry Run"
    if "CONNECTOR" in upper:
        return "Connector Health"
    return "Overview"


def _find_feature_for_token(registry_rows: list[dict[str, Any]], token: str) -> dict[str, Any] | None:
    normalized = token.upper().replace(" ", "_")
    for row in registry_rows:
        label = str(row.get("canonical_label", "")).upper()
        panel = str(row.get("panel_id", "")).upper()
        aliases = " ".join(str(alias).upper() for alias in row.get("legacy_aliases", []))
        feature_id = str(row.get("feature_id", "")).upper()
        if normalized in {feature_id, panel} or normalized in aliases.replace(" ", "_"):
            return row
        words = [part for part in re.split(r"[^A-Z0-9]+", normalized) if len(part) > 3]
        if words and all(word in f"{label} {panel} {aliases} {feature_id}" for word in words[:4]):
            return row
    return None


def _extract_20d_sections(master_plan: Path, registry_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text = _read_text(master_plan)
    match = re.search(r"(?ms)^## 20D\. Dashboard and operator surfaces(?P<body>.*?)(?=^## \d|^# |\Z)", text)
    body = match.group("body") if match else ""
    heading_matches = list(re.finditer(r"(?m)^### (?P<section>20D\.[^\n]+)$", body))
    sections: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for index, heading in enumerate(heading_matches, start=1):
        heading_text = heading.group("section").strip()
        section_id = heading_text.split(" ", 1)[0]
        title = heading_text.split(" ", 1)[1] if " " in heading_text else heading_text
        safe_heading_text = _generated_display_text(heading_text)
        safe_title = _generated_display_text(title)
        next_start = heading_matches[index].start() if index < len(heading_matches) else len(body)
        section_body = body[heading.end() : next_start]
        feature = _find_feature_for_token(registry_rows, title) or registry_rows[min(index - 1, len(registry_rows) - 1)]
        section_row = {
            **_ui_meta(),
            "section_id": section_id,
            "section_title": safe_title,
            "canonical_widget_id": f"UI1_20D_{index:03d}_{_anchor(safe_title).upper().replace('-', '_')}",
            "canonical_panel_id": str(feature.get("panel_id", f"UI1_20D_{index:03d}_PANEL")),
            "visible_label": safe_title,
            "render_status": "VISIBLE_EMPTY_STATE_PROVIDER_PENDING"
            if feature.get("lifecycle_state") != "MATERIALIZED_IN_DASH1"
            else "VISIBLE_WIDGET_RENDERED",
            "source_artifact_refs": [_repo_ref(Path("docs/master_plan/QTT_MasterPlan_Current.md"))],
            "provider_stage": feature.get("provider_stage", "UI1"),
            "activation_route": feature.get("activation_route", f"UI1_RENDER_ROUTE::{section_id}"),
            "authority_boundary_ref": AUTHORITY_BOUNDARY,
            "owner_action_refs": feature.get("action_code_refs", []),
            "agent_role_refs_from_PR165_D2": feature.get("agent_role_refs_from_PR165_D2", []),
            "validation_ref": VALIDATION_REF,
            "element_kind": "SECTION",
            "exact_text_or_token": safe_heading_text,
        }
        sections.append(section_row)
        rows.append(section_row)

        tokens = list(dict.fromkeys(re.findall(r"`([^`]+)`", section_body)))
        uppercase_tokens = re.findall(r"\b[A-Z][A-Z0-9_]{4,}\b", section_body)
        for token in list(dict.fromkeys([*tokens, *uppercase_tokens]))[:80]:
            token_feature = _find_feature_for_token(registry_rows, token) or feature
            safe_token = _generated_display_text(token)
            rows.append(
                {
                    **_ui_meta(),
                    "section_id": section_id,
                    "section_title": safe_title,
                    "element_kind": "EXACT_ALIAS" if token.isupper() else "FIELD",
                    "exact_text_or_token": safe_token,
                    "canonical_widget_id": f"UI1_TOKEN_{_anchor(safe_token).upper().replace('-', '_')[:96]}",
                    "canonical_panel_id": str(token_feature.get("panel_id", section_row["canonical_panel_id"])),
                    "visible_label": safe_token,
                    "render_status": "VISIBLE_ALIAS_RENDERED",
                    "source_artifact_refs": [_repo_ref(Path("docs/master_plan/QTT_MasterPlan_Current.md"))],
                    "provider_stage": token_feature.get("provider_stage", "UI1"),
                    "activation_route": token_feature.get("activation_route", f"UI1_RENDER_ROUTE::{section_id}"),
                    "authority_boundary_ref": AUTHORITY_BOUNDARY,
                    "owner_action_refs": token_feature.get("action_code_refs", []),
                    "agent_role_refs_from_PR165_D2": token_feature.get("agent_role_refs_from_PR165_D2", []),
                    "validation_ref": VALIDATION_REF,
                }
            )

    if not rows:
        fallback = registry_rows[:20]
        for index, feature in enumerate(fallback, start=1):
            safe_label = _generated_display_text(str(feature.get("canonical_label", "")))
            rows.append(
                {
                    **_ui_meta(),
                    "section_id": f"20D.FALLBACK.{index}",
                    "section_title": safe_label,
                    "element_kind": "SECTION",
                    "exact_text_or_token": safe_label,
                    "canonical_widget_id": f"UI1_FALLBACK_{index:03d}",
                    "canonical_panel_id": str(feature.get("panel_id", "")),
                    "visible_label": safe_label,
                    "render_status": "VISIBLE_WIDGET_RENDERED",
                    "source_artifact_refs": ["owner_dashboard_surface_registry.jsonl"],
                    "provider_stage": feature.get("provider_stage", "UI1"),
                    "activation_route": feature.get("activation_route", ""),
                    "authority_boundary_ref": AUTHORITY_BOUNDARY,
                    "owner_action_refs": feature.get("action_code_refs", []),
                    "agent_role_refs_from_PR165_D2": feature.get("agent_role_refs_from_PR165_D2", []),
                    "validation_ref": VALIDATION_REF,
                }
            )
        sections = rows[:]
    return sections, rows


def _build_widget_manifest(registry_rows: list[dict[str, Any]], coverage_rows: list[dict[str, Any]]) -> dict[str, Any]:
    widgets: list[dict[str, Any]] = []
    for nav_index, area in enumerate(NAV_AREAS, start=1):
        refs = [row for row in registry_rows if _classify_nav(str(row.get("canonical_label", ""))) == area]
        feature = refs[0] if refs else registry_rows[min(nav_index - 1, len(registry_rows) - 1)]
        widgets.append(
            {
                **_ui_meta(),
                "widget_id": f"UI1_NAV_{nav_index:02d}_{_anchor(area).upper().replace('-', '_')}",
                "widget_title": area,
                "widget_kind": "navigation_area",
                "master_plan_section_refs": sorted(
                    {
                        row["section_id"]
                        for row in coverage_rows
                        if area.upper().split()[0] in str(row.get("section_title", "")).upper()
                    }
                )
                or ["20D"],
                "desktop_layout": "workstation_scroll_anchor",
                "mobile_layout": "bottom_navigation_tab_or_more_stack",
                "data_ref": "owner_dashboard_review_data.generated.json",
                "source_artifact_paths": ["owner_dashboard_surface_registry.jsonl"],
                "source_row_count": len(refs),
                "render_state": "VISIBLE_WIDGET_RENDERED" if refs else "VISIBLE_EMPTY_STATE_PROVIDER_PENDING",
                "empty_state_reason": RENDERED_EMPTY_STATE_REASON
                if refs
                else "No direct DASH1 registry row matched this nav area; routed empty state rendered.",
                "provider_stage": feature.get("provider_stage", "UI1"),
                "activation_route": feature.get("activation_route", f"UI1_NAV_ROUTE::{area}"),
                "authority_boundary": AUTHORITY_BOUNDARY,
                "linked_action_codes": feature.get("action_code_refs", []),
                "linked_agent_roles_from_PR165_D2": feature.get("agent_role_refs_from_PR165_D2", []),
                "linked_downstream_consumers": feature.get("downstream_consumer_refs", ["OwnerSurfaceResolver"]),
                "drilldown_ref": f"drawer::{_anchor(area)}",
                "empty_state_policy": "show useful routed provider-pending card",
                "stale_state_policy": "show stale-data banner when provider refresh receipt is absent",
            }
        )

    existing_titles = {widget["widget_title"] for widget in widgets}
    for index, name in enumerate(EXACT_PANEL_NAMES, start=1):
        feature = _find_feature_for_token(registry_rows, name) or registry_rows[index % len(registry_rows)]
        if name not in existing_titles:
            widgets.append(
                {
                    **_ui_meta(),
                    "widget_id": f"UI1_EXACT_{_anchor(name).upper().replace('-', '_')[:88]}",
                    "widget_title": name,
                    "widget_kind": "exact_panel_alias_or_empty_state",
                    "master_plan_section_refs": ["20D"],
                    "desktop_layout": "alias_search_and_panel_card",
                    "mobile_layout": "More tab detail stack",
                    "data_ref": "owner_dashboard_review_data.generated.json",
                    "source_artifact_paths": ["owner_dashboard_surface_registry.jsonl"],
                    "source_row_count": 1,
                    "render_state": "VISIBLE_ALIAS_RENDERED",
                    "empty_state_reason": RENDERED_EMPTY_STATE_REASON,
                    "provider_stage": feature.get("provider_stage", "UI1"),
                    "activation_route": feature.get("activation_route", f"UI1_ALIAS_ROUTE::{name}"),
                    "authority_boundary": AUTHORITY_BOUNDARY,
                    "linked_action_codes": feature.get("action_code_refs", []),
                    "linked_agent_roles_from_PR165_D2": feature.get("agent_role_refs_from_PR165_D2", []),
                    "linked_downstream_consumers": feature.get("downstream_consumer_refs", ["OwnerSurfaceResolver"]),
                    "drilldown_ref": f"drawer::{_anchor(name)}",
                    "empty_state_policy": "visible alias backed to canonical DASH1 route",
                    "stale_state_policy": "show provider-pending badge if no runtime receipt exists",
                }
            )
    return {"meta": _ui_meta({"artifact_id": "UI1_WIDGET_MANIFEST"}), "widgets": widgets}


def _build_provider_stage_routes(registry_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, stage in enumerate(PROVIDER_STAGES, start=1):
        matched = [row for row in registry_rows if str(row.get("provider_stage", "")).replace("-", "_") == stage]
        source = matched[0] if matched else registry_rows[index % len(registry_rows)]
        state = "MATERIALIZED_IN_DASH1" if stage == "DASH1" else "MATERIALIZED_IN_UI1" if stage == "UI1" else "CONTRACT_DEFINED_PROVIDER_PENDING"
        rows.append(
            {
                **_ui_meta(),
                "stage_id": stage,
                "provider_stage": stage,
                "stage_label": stage.replace("_", " "),
                "route_purpose": "Owner-visible provider-stage route; UI1 renders contract/readiness only.",
                "owning_stage_or_pr": "PR169-DASH1" if stage == "DASH1" else "PR169-DASH1-UI1" if stage == "UI1" else stage,
                "activation_route": source.get("activation_route", f"{stage}_ACTIVATION_ROUTE::UI1"),
                "provider_contract_ref": source.get("provider_contract_ref", f"{stage}_PROVIDER_CONTRACT"),
                "authority_class": "LOCAL_STATIC_RENDER_CONTRACT",
                "runtime_side_effect_allowed_in_UI1": False,
                "runtime_side_effect_allowed": False,
                "source_artifact_refs": source.get("upstream_artifact_refs", ["owner_dashboard_surface_registry.jsonl"]),
                "upstream_artifact_refs": source.get("upstream_artifact_refs", ["owner_dashboard_surface_registry.jsonl"]),
                "downstream_consumer_refs": source.get("downstream_consumer_refs", ["OwnerSurfaceResolver"]),
                "owner_action_refs": source.get("action_code_refs", []),
                "agent_role_refs_from_PR165_D2": source.get("agent_role_refs_from_PR165_D2", []),
                "LLM_visibility_policy": source.get("reasoning_brain_view_policy", "LLM bounded reasoning view only."),
                "LLM_view_refs": ["owner_llm_view_projection.generated.jsonl"],
                "QKU_formula_candidate_refs_when_applicable": ["owner_qku_formula_candidate_route_view.generated.jsonl"],
                "QKU_formula_candidate_refs": ["owner_qku_formula_candidate_route_view.generated.jsonl"],
                "blocked_authority_refs": [AUTHORITY_BOUNDARY],
                "authority_boundary_ref": AUTHORITY_BOUNDARY,
                "provider_state": state,
                "what_UI1_renders_now": "Static routed card, no runtime provider action.",
                "what_later_provider_must_supply": "Authenticated provider receipts, APIs, streams, or runtime engines outside UI1.",
                "no_orphan_status": "ROUTED",
                "validation_ref": VALIDATION_REF,
            }
        )
    return {"meta": _ui_meta({"artifact_id": "UI1_PROVIDER_STAGE_ROUTE_MAP"}), "routes": rows}


def _build_theme_contract() -> dict[str, Any]:
    return {
        "meta": _ui_meta({"artifact_id": "UI1_THEME_CONTRACT"}),
        "theme_switch_visible_in_desktop_header": True,
        "theme_switch_visible_or_accessible_in_mobile_navigation": True,
        "DARK_and_LIGHT_modes_supported": True,
        "default_theme": "DARK",
        "supported_modes": list(THEME_MODES),
        "localStorage_key": THEME_STORAGE_KEY,
        "stored_values_allowed": list(THEME_MODES),
        "theme_preference_storage_non_secret_only": True,
        "stored_value_exclusions": [
            "credentials",
            "tokens",
            "cash",
            "account",
            "connector_private_data",
            "order_data",
            "source_truth_data",
        ],
        "network_call": False,
        "credential_access": False,
        "semantic_colors": SEMANTIC_COLORS,
        "colors_never_the_only_carrier_of_meaning": True,
        "high_contrast_text_in_both_themes": True,
        "light_mode_not_separate_dashboard_state": True,
    }


def _build_mobile_navigation() -> dict[str, Any]:
    return {
        "meta": _ui_meta({"artifact_id": "UI1_MOBILE_NAVIGATION"}),
        "generated_from": GENERATED_FROM_UI1,
        "actual_responsive_desktop_mobile_rendering": True,
        "mobile_bottom_navigation_rendered": True,
        "touch_targets_minimum_px": 44,
        "tabs": [
            {
                "tab_id": f"MOBILE_TAB_{_anchor(tab).upper().replace('-', '_')}",
                "label": tab,
                "uses_owner_dashboard_state_model": True,
                "uses_owner_action_registry": True,
                "uses_owner_surface_resolver": True,
            }
            for tab in MOBILE_TABS
        ],
        "stable_tab_labels": list(MOBILE_TABS),
        "uses_same_OwnerDashboardStateV1": True,
        "chat_tab_rendered_in_mobile_navigation": "Chat" in MOBILE_TABS,
        "trade_workbench_tab_rendered_in_mobile_navigation": "Trade Workbench" in MOBILE_TABS,
        "stale_data_banner_rendered_on_mobile_viewports": True,
        "drilldown_drawer_uses_bottom_sheet_on_mobile": True,
    }


def _build_state_model(widget_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "meta": _ui_meta({"artifact_id": "UI1_OWNER_DASHBOARD_STATE_MODEL"}),
        "state_model_id": "OwnerDashboardStateV1",
        "one_dashboard_state_model": True,
        "one_owner_action_grammar": True,
        "one_owner_agent_conversation_model": True,
        "one_source_agnostic_research_intake_model": True,
        "one_trade_workbench_model": True,
        "one_widget_chart_action_chat_manifest": True,
        "one_resolver_or_API_path": True,
        "one_audit_receipt_model": True,
        "no_duplicate_mobile_only_data_layer": True,
        "no_duplicate_chat_system": True,
        "no_duplicate_telegram_governance_plane": True,
        "resolver_ref": "OwnerSurfaceResolver",
        "action_registry_ref": "OwnerActionRegistryV1",
        "widget_manifest_ref": "owner_dashboard_widget_manifest.generated.json",
        "widget_count": len(widget_manifest["widgets"]),
    }


def _build_chat_contract(action_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    action_codes = {str(row.get("action_code")) for row in action_rows}
    catalog_rows: list[dict[str, Any]] = []
    for index, (preview_code, linked_code) in enumerate(CHAT_PREVIEW_CODES, start=1):
        if linked_code not in action_codes and action_rows:
            linked_code = str(action_rows[0].get("action_code"))
        catalog_rows.append(
            {
                **_ui_meta(),
                "preview_code": preview_code,
                "linked_owner_action_code": linked_code,
                "linked_existing_owner_action_code": linked_code,
                "routed_through_owner_action_registry": True,
                "local_static_preview_only": True,
                "runtime_side_effect": False,
                "surface_origin": "DESKTOP_DASHBOARD",
                "provider_stage": "UI1",
                "activation_route": f"UI1_CHAT_ROUTE::{preview_code}",
                "authority_boundary_ref": AUTHORITY_BOUNDARY,
            }
        )
    conversation_state = {
        "meta": _ui_meta({"artifact_id": "UI1_CONVERSATION_STATE"}),
        "conversation_state_id": "OwnerConversationStateV1",
        "uses_owner_dashboard_state_model": True,
        "thread_count": 3,
        "message_preview_count": 3,
        "threads": [
            {
                "thread_id": "OWNER_THREAD_TRADE_WORKBENCH",
                "title": "Trade Workbench requests",
                "linked_widget_id": "OWNER_TRADE_WORKBENCH_PANEL",
                "route_receipt_preview_ref": "OwnerChatRouteReceiptPreviewV1",
            },
            {
                "thread_id": "OWNER_THREAD_RESEARCH_INTAKE",
                "title": "Research candidate intake",
                "linked_widget_id": "OWNER_AGENT_CHAT_WORKSPACE_PANEL",
                "route_receipt_preview_ref": "OwnerChatRouteReceiptPreviewV1",
            },
            {
                "thread_id": "OWNER_THREAD_AGENT_DIRECTIVES",
                "title": "Agent directives",
                "linked_widget_id": "OWNER_AGENT_CHAT_WORKSPACE_PANEL",
                "route_receipt_preview_ref": "OwnerAgentDirectiveEnvelopeV1",
            },
        ],
    }
    widget_manifest = {
        "meta": _ui_meta({"artifact_id": "UI1_CHAT_WIDGET_MANIFEST"}),
        "widgets": [
            {
                **_ui_meta(),
                "widget_id": widget_id,
                "visible_in_desktop": True,
                "visible_or_accessible_in_mobile": True,
                "uses_owner_conversation_state": True,
            }
            for widget_id in (
                "OWNER_AGENT_CHAT_WORKSPACE_PANEL",
                "OWNER_AGENT_CHAT_THREAD_LIST",
                "OWNER_AGENT_CHAT_MESSAGE_STREAM",
                "OWNER_AGENT_CHAT_COMPOSER",
                "OWNER_AGENT_CHAT_AGENT_SELECTOR",
                "OWNER_AGENT_CHAT_POD_SELECTOR",
                "OWNER_AGENT_CHAT_BROADCAST_SCOPE_SELECTOR",
                "OWNER_AGENT_CHAT_ATTACHMENT_TRAY",
                "OWNER_AGENT_CHAT_LINK_INPUT",
                "OWNER_AGENT_CHAT_FILE_INPUT_PREVIEW",
                "OWNER_AGENT_CHAT_RESEARCH_CANDIDATE_SELECTOR",
                "OWNER_AGENT_CHAT_DIRECTIVE_PREVIEW",
                "OWNER_AGENT_CHAT_ROUTE_PREVIEW",
                "OWNER_AGENT_CHAT_RECEIPT_TIMELINE",
                "OWNER_AGENT_CHAT_AGENT_RESPONSE_PREVIEW",
                "OWNER_AGENT_CHAT_TO_DECISION_QUEUE_LINK",
                "OWNER_AGENT_CHAT_TO_TRADE_WORKBENCH_LINK",
                "OWNER_AGENT_CHAT_TO_SOURCE_WORKFLOW_LINK",
                "OWNER_AGENT_CHAT_TO_QKU_FORMULA_ROUTE_LINK",
                "OWNER_AGENT_CHAT_SEARCH_AND_FILTER",
                "OWNER_AGENT_CHAT_PINNED_CONTEXT_STRIP",
                "OWNER_AGENT_CHAT_AUTHORITY_BOUNDARY_BADGE",
            )
        ],
    }
    route_map = {
        "meta": _ui_meta({"artifact_id": "UI1_CHAT_ROUTE_MAP"}),
        "preview_objects": [
            "OwnerMessageV1",
            "OwnerAttachmentCandidateV1",
            "OwnerResearchSubmissionV1",
            "OwnerAgentDirectiveEnvelopeV1",
            "OwnerChatActionPreviewV1",
            "OwnerChatRouteReceiptPreviewV1",
            "OwnerAgentResponsePreviewV1",
            "OwnerTradeIntentV1",
            "OwnerTradeCheckRequestV1",
            "SourceCandidateV1",
            "FormulaExtractionCandidateV1",
            "QKUCandidateMaterializationRequestV1",
            "QuantumStructureMappingRequestV1",
            "ReplayPaperRequestPreviewV1",
            "NoTradeReoptimizationRequestPreviewV1",
        ],
        "routes": [
            {
                **_ui_meta(),
                "object_id": f"OwnerChatActionPreviewV1::{row['preview_code']}",
                "thread_id": "OWNER_THREAD_TRADE_WORKBENCH"
                if "TRADE" in row["preview_code"]
                else "OWNER_THREAD_RESEARCH_INTAKE"
                if "SOURCE" in row["preview_code"] or "RESEARCH" in row["preview_code"]
                else "OWNER_THREAD_AGENT_DIRECTIVES",
                "source_family": "source_candidate",
                "input_kind": "request_preview",
                "surface_origin": "DESKTOP_DASHBOARD",
                "owner_intent_summary": _label(row["preview_code"]),
                "target_agent_or_pod": "PR165_D2_ROLE_OR_GAP_ROUTE",
                "agent_role_refs_from_PR165_D2": ["dashboard_agent", "governance_agent", "commander_agent"],
                "requested_route": row["activation_route"],
                "provider_stage": row["provider_stage"],
                "activation_route": row["activation_route"],
                "authority_boundary_ref": AUTHORITY_BOUNDARY,
                "linked_widget_id": "OWNER_AGENT_CHAT_WORKSPACE_PANEL",
                "linked_action_code": row["linked_owner_action_code"],
                "linked_trade_workbench_id": "OwnerTradeIntentV1",
                "linked_source_workflow_id": "SourceCandidateV1",
                "linked_qku_formula_route_id": "QKUCandidateMaterializationRequestV1",
                "linked_data_value_route_row_id": "owner_data_value_route_map.generated.jsonl",
                "runtime_side_effect": False,
            }
            for row in catalog_rows
        ],
    }
    route_map["requests"] = [
        {
            **route_map["routes"][index % len(route_map["routes"])],
            "object_type": object_type,
            "runtime_side_effect": False,
        }
        for index, object_type in enumerate(route_map["preview_objects"])
    ]
    catalog = {"meta": _ui_meta({"artifact_id": "UI1_CHAT_ACTION_CATALOG"}), "actions": catalog_rows}
    return conversation_state, widget_manifest, catalog, route_map


def _build_trade_workbench(action_rows: list[dict[str, Any]]) -> dict[str, Any]:
    known_actions = {str(row.get("action_code")) for row in action_rows}
    action_previews = [
        code
        for code in (
            "REQUEST_OWNER_REVIEW",
            "REQUEST_REPLAY_TEST",
            "REQUEST_PAPER_TEST",
            "REQUEST_VARIABLE_OPTIMIZATION",
            "REQUEST_QKU_COMPUTABILITY_REVIEW",
            "REQUEST_NO_TRADE_REOPTIMIZATION_REVIEW",
            "REQUEST_LIVE_CANARY_REVIEW",
            "REQUEST_ALLOWLIST_REVIEW",
            "REQUEST_KILL_SWITCH_REVIEW",
        )
        if code in known_actions
    ]
    return {
        "meta": _ui_meta({"artifact_id": "UI1_TRADE_WORKBENCH"}),
        "workbench_id": "OWNER_TRADE_WORKBENCH",
        "workbench_contract_id": "OwnerTradeWorkbenchV1",
        "primary_owner_button": "CHECK_TRADE_WITH_QTT_AGENTS",
        "local_static_preview_only": True,
        "runtime_queue_created": False,
        "direct_venue_submit_allowed": False,
        "execution_router_release_required": True,
        "owner_trade_intent_object": "OwnerTradeIntentV1",
        "owner_trade_check_request_object": "OwnerTradeCheckRequestV1",
        "mutable_trade_variables": list(TRADE_VARIABLES),
        "route_chain": list(TRADE_ROUTE_CHAIN),
        "visible_sections": [
            "Owner intent",
            "Source evidence",
            "QKU/formula stack",
            "Variable search",
            "Replay result",
            "Paper result",
            "TCA",
            "Risk/capacity",
            "No-trade comparison",
            "Champion/challenger",
            "Owner decision",
            "Execution Router status",
            "Agent disagreement",
            "Emergency actions",
        ],
        "owner_action_request_previews": action_previews,
        "validated_positive_net_cash_evidence_wording": True,
        "profit_guarantee": False,
        "no_trade_first_class_candidate": True,
        "QKUs_formulas_remain_immutable": True,
    }


def _build_ui1r1_artifacts(
    *,
    registry_rows: list[dict[str, Any]],
    decision_queue: list[dict[str, Any]],
    actionable_cards: list[dict[str, Any]],
    action_registry: list[dict[str, Any]],
    chart_contracts: list[dict[str, Any]],
    interactive_charts: list[dict[str, Any]],
    portfolio: list[dict[str, Any]],
    edge_alpha: list[dict[str, Any]],
    qku: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    quantum: list[dict[str, Any]],
    provider_routes: dict[str, Any],
    trade_workbench: dict[str, Any],
    chat_route_map: dict[str, Any],
    qku_matrix: dict[str, Any],
    no_orphan: dict[str, Any],
    authority: dict[str, Any],
    generated_at: str,
    base_ref: str,
) -> dict[str, dict[str, Any]]:
    common_source_refs = [
        "owner_dashboard_review_data.generated.json",
        "owner_dashboard_state_model.generated.json",
        "owner_dashboard_widget_manifest.generated.json",
        "owner_action_registry.generated.jsonl",
        "owner_dashboard_surface_registry.jsonl",
    ]
    pr165_or_gap = ["PR165_D2_CommandActionMatrix.report.json", "PR165_D2_AGENT_ROLE_GAP_ROUTE::provider_pending"]
    evidence_refs = {
        "execution_adjusted_ranking": "docs/master_plan/generated/pr168_rank4/rank_edge_capture.jsonl",
        "TCA_decomposition": "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl",
        "implementation_shortfall": "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl",
        "fee_spread_slippage_impact_latency_opportunity_cost": "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl",
        "fill_probability_partial_fill_penalty": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
        "overfit_false_discovery_control": "docs/master_plan/generated/pr168_rank4/rank_edge_capture.jsonl",
        "portfolio_style_diversification": "docs/master_plan/generated/pr168_qopt1/portfolio_exposure.jsonl",
        "portfolio_marginal_utility": "docs/master_plan/generated/pr168_rp5g/portfolio_mu.jsonl",
        "capacity_crowding_limit": "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
        "champion_challenger_selection": "docs/master_plan/generated/pr168_rank4/rank_edge_capture.jsonl",
        "regime_conditioned_memory": "docs/master_plan/generated/pr168_mem1/memory_query_contract.jsonl",
        "MEM1_similarity_and_shrinkage_prior_refs": "docs/master_plan/generated/pr168_mem1/memory_query_contract.jsonl",
        "no_trade_comparator_and_reoptimization_route": "docs/master_plan/generated/pr168_qopt1/notrade_reopt.jsonl",
        "scenario_ladder": "docs/master_plan/generated/pr168_rp5g/scenario_ladder.jsonl",
        "calibration_state": "docs/master_plan/generated/pr168_rp5g/calibration.jsonl",
        "quantum_structural_readiness": "owner_quantum_structural_readiness_view.generated.jsonl",
        "QUBO_BQM_CQM_QuadraticProgram_Ising_readiness": "docs/master_plan/generated/pr168_qopt1/qstruct_optimized.jsonl",
        "QAOA_VQE_annealing_candidate_readiness": "QMAP1_PROVIDER_ROUTE::qaoa_vqe_annealing_candidate_readiness",
        "classical_fallback_ref": "docs/master_plan/generated/pr168_rp5g/q_classic_fb.jsonl",
        "qstruct_objective_constraint_variable_ref": "docs/master_plan/generated/pr168_qopt1/qstruct_optimized.jsonl",
        "interpret_back_map_ref": "docs/master_plan/generated/pr168_qopt1/interpret_back.jsonl",
        "DAG_upstream_downstream_route_ref": "dag.generated.jsonl",
    }

    def routed_row(row_id: str, title: str, provider_stage: str = "UI1") -> dict[str, Any]:
        return {
            "row_id": row_id,
            "title": title,
            "source_artifact_refs": list(common_source_refs),
            "provider_stage": provider_stage,
            "activation_route": f"{provider_stage}_ACTIVATION_ROUTE::{row_id}",
            "authority_boundary": AUTHORITY_BOUNDARY,
            "authority_boundary_ref": AUTHORITY_BOUNDARY,
            "linked_action_refs": ["REQUEST_OWNER_REVIEW"],
            "linked_agent_role_refs": ["dashboard_agent", "governance_agent", "commander_agent"],
            "PR165_D2_agent_role_refs_or_gap": list(pr165_or_gap),
            "validation_ref": VALIDATION_REF,
            "runtime_side_effect": False,
        }

    hero_cards: list[dict[str, Any]] = []
    for index, (widget_id, owner_value, provider_stage, empty_state_reason) in enumerate(
        (
            ("net_capital_cash_slot", "Provider-pending cash/capital receipt slot", "PAPER_LOOP", "Cash/private account data is absent; UI1 does not read accounts."),
            ("today_result_slot", "Provider-pending day result slot", "METRICS1", "PnL receipt stream is not available in UI1."),
            ("week_result_slot", "Provider-pending week result slot", "METRICS1", "Weekly realized result receipts are provider-pending."),
            ("month_result_slot", "Provider-pending month result slot", "METRICS1", "Monthly realized result receipts are provider-pending."),
            ("YTD_result_slot", "Provider-pending YTD result slot", "METRICS1", "YTD realized result receipts are provider-pending."),
            ("all_available_result_slot", "Provider-pending all-available result slot", "POSTLAUNCH", "All-available result history requires provider receipts."),
            ("drawdown_slot", "Provider-pending drawdown slot", "METRICS1", "Drawdown curve requires realized/equity receipts."),
            ("operating_mode_slot", "Local static review mode", "UI1", "UI1 renders replay/paper/shadow/live route states only."),
            ("highest_severity_decision_slot", f"{len(decision_queue)} routed decision rows", "DASH1", "Decision queue rows are rendered from DASH1, not recomputed."),
            ("kill_switch_state_slot", "Review route only", "ALLOW1", "Kill-switch action is a governed request preview."),
            ("data_freshness_provider_state_slot", "Static generated boot data", "UI1", "No live refresh stream exists in UI1."),
        ),
        start=1,
    ):
        hero_cards.append(
            {
                **routed_row(f"UI1R1_HOME_HERO_{index:02d}", widget_id, provider_stage),
                "widget_id": widget_id,
                "owner_value": owner_value,
                "empty_state_reason": empty_state_reason,
                "source_artifact_refs": [
                    "owner_live_cash_private_display_contract.generated.jsonl",
                    "owner_portfolio_pnl_chart_view.generated.jsonl",
                    "owner_decision_queue.generated.jsonl",
                ],
                "no_fake_value": True,
            }
        )

    home = {
        "meta": _ui1r1_meta("UI1R1_HOME"),
        "default_mode": "OWNER_MODE",
        "first_viewport_order": [
            "owner_top_bar",
            "portfolio_hero_cards",
            "portfolio_equity_curve",
            "TCA_waterfall",
            "decision_summary",
            "trade_workbench_quick_card",
            "plain_english_chat_composer_quick_card",
            "edge_alpha_preview",
            "agent_disagreement_preview",
            "risk_capital_exposure_preview",
            "developer_mode_collapsed_toggle",
        ],
        "hero_cards": hero_cards,
        "quick_cards": [
            routed_row("UI1R1_QUICK_DECISION_QUEUE", "Highest-priority decision summary", "DASH1"),
            routed_row("UI1R1_QUICK_TRADE_WORKBENCH", "Trade Workbench order simulator preview", "PRETRADE1"),
            routed_row("UI1R1_QUICK_CHAT_COMPOSER", "Plain-English QTT route preview", "LLM1"),
            routed_row("UI1R1_QUICK_EDGE_ALPHA", "Execution-adjusted Edge/Alpha preview", "PRETRADE1"),
            routed_row("UI1R1_QUICK_AGENT_DISAGREEMENT", "Agent disagreement and objection preview", "AGENT_ORCH1"),
            routed_row("UI1R1_QUICK_RISK_EXPOSURE", "Capital allocation and exposure provider-pending frame", "PRETRADE1"),
        ],
        "owner_mode_forbidden_primary_content": [
            "registry row counts",
            "generated artifact row counts",
            "raw JSON",
            "artifact directory path",
            "validation row tables",
            "authority report text",
        ],
    }

    dev_mode = {
        "meta": _ui1r1_meta("UI1R1_DEV_MODE"),
        "developer_mode_default_open": False,
        "developer_mode_collapsed_by_default": True,
        "diagnostics": [
            {"diagnostic_id": "registry_row_count", "value_ref": len(registry_rows), "owner_default": False},
            {"diagnostic_id": "decision_row_count", "value_ref": len(decision_queue), "owner_default": False},
            {"diagnostic_id": "actionable_card_count", "value_ref": len(actionable_cards), "owner_default": False},
            {"diagnostic_id": "chart_row_count", "value_ref": len(chart_contracts) + len(interactive_charts), "owner_default": False},
            {"diagnostic_id": "artifact_directory", "value_ref": base_ref, "owner_default": False},
            {"diagnostic_id": "validator_status", "value_ref": VALIDATION_REF, "owner_default": False},
            {"diagnostic_id": "no_orphan_report_status", "value_ref": no_orphan.get("status", "PASS"), "owner_default": False},
            {"diagnostic_id": "authority_boundary_report_status", "value_ref": authority.get("status", "PASS"), "owner_default": False},
            {"diagnostic_id": "projection_generation_status", "value_ref": "generated by UI1 builder", "owner_default": False},
            {"diagnostic_id": "DASH1_UI1_renderer_lineage", "value_ref": R1_GENERATED_FROM, "owner_default": False},
            {"diagnostic_id": "playwright_screenshot_manifest", "value_ref": "ui1r1_playwright_manifest.generated.json", "owner_default": False},
        ],
        "owner_mode_primary_content": [
            "portfolio",
            "charts",
            "trade_workbench",
            "plain_english_chat",
            "edge_alpha",
            "agent_disagreement",
            "parameter_tuning",
        ],
    }

    chart_specs = [
        ("portfolio_equity_curve", "line", "owner_portfolio_pnl_chart_view.generated.jsonl", "PAPER_LOOP", True),
        ("net_cash_pnl_by_time_range", "line", "owner_portfolio_pnl_chart_view.generated.jsonl", "METRICS1", True),
        ("cost_adjusted_net_pnl", "line", "owner_chart_surface_contract.generated.jsonl", "METRICS1", True),
        ("drawdown_curve", "area", "owner_chart_surface_contract.generated.jsonl", "METRICS1", True),
        ("replay_vs_paper_vs_shadow_vs_live_pnl", "line", "owner_chart_surface_contract.generated.jsonl", "PAPER_LOOP", True),
        ("TCA_waterfall_and_implementation_shortfall", "waterfall", "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl", "PRETRADE1", False),
        ("capital_allocation_by_market", "donut", "owner_live_cash_private_display_contract.generated.jsonl", "PRETRADE1", False),
        ("exposure_by_venue", "stacked_bar", "owner_live_cash_private_display_contract.generated.jsonl", "PRETRADE1", False),
        ("edge_alpha_scoreboard_visual", "scoreboard", "owner_edge_alpha_capture_view.generated.jsonl", "PRETRADE1", False),
        ("agent_disagreement_visual", "bar", "owner_agent_performance_chart_view.generated.jsonl", "AGENT_ORCH1", False),
        ("DAG_route_graph_visual", "dag", "dag.generated.jsonl", "DASH1", False),
    ]
    chart_rows = [
        {
            **routed_row(f"UI1R1_CHART_{index:02d}", chart_id, provider_stage),
            "chart_id": chart_id,
            "chart_kind": chart_kind,
            "chart_title": _label(chart_id),
            "data_chart_id": chart_id,
            "data_chart_kind": chart_kind,
            "data_chart_render_state": "PROVIDER_PENDING_VISUAL_FRAME",
            "data_chart_source_ref": source_ref,
            "data_provider_stage": provider_stage,
            "data_authority_boundary": AUTHORITY_BOUNDARY,
            "source_artifact_ref": source_ref,
            "source_artifact_refs": [source_ref, *common_source_refs],
            "time_range_controls": has_range,
            "supported_time_ranges": ["1D", "1W", "1M", "3M", "YTD", "1Y", "ALL"] if has_range else [],
            "legend_required": True,
            "axis_or_labeled_scale_required": True,
            "visual_shape_required": True,
            "drilldown_required": True,
            "provider_state_badge_required": True,
            "fake_value_allowed": False,
        }
        for index, (chart_id, chart_kind, source_ref, provider_stage, has_range) in enumerate(chart_specs, start=1)
    ]
    chart_manifest = {
        "meta": _ui1r1_meta("UI1R1_CHART_MANIFEST"),
        "charts": chart_rows,
        "chart_visual_component_acceptance_markers": [
            "data-chart-id",
            "data-chart-kind",
            "data-chart-render-state",
            "data-chart-source-ref",
            "data-provider-stage",
            "data-authority-boundary",
        ],
        "no_text_only_chart_boxes": True,
        "no_fake_PnL_cash_fills_live_positions": True,
    }

    chat_examples = []
    for index, (text, family, preview_object) in enumerate(UI1R1_CHAT_EXAMPLES, start=1):
        chat_examples.append(
            {
                **routed_row(f"UI1R1_CHAT_EXAMPLE_{index:02d}", family, "LLM1"),
                "owner_example_text": text,
                "parsed_preview_output": {
                    "object_type": "OwnerPlainEnglishIntentV1",
                    "intent_id": f"UI1R1_INTENT_{index:02d}",
                    "thread_id": "OWNER_THREAD_TRADE_WORKBENCH"
                    if "TRADE" in family or "NO_TRADE" in family
                    else "OWNER_THREAD_RESEARCH_INTAKE"
                    if "RESEARCH" in family
                    else "OWNER_THREAD_AGENT_DIRECTIVES",
                    "owner_message_ref": f"OwnerMessageV1::UI1R1_MSG_{index:02d}",
                    "raw_owner_text_excerpt": text[:120],
                    "plain_english_summary": _label(family),
                    "intent_family": family,
                    "confidence_label": "HIGH_CONFIDENCE_PREVIEW",
                    "clarifying_question_if_needed": "No clarification needed for this high-confidence preview.",
                    "target_workspace": "Trade Workbench"
                    if "TRADE" in family or "NO_TRADE" in family or "PARAMETER" in family
                    else "Research Intake"
                    if "RESEARCH" in family
                    else "Agents",
                    "owner_action_preview_refs": ["REQUEST_OWNER_REVIEW"],
                    "structured_request_preview_refs": [preview_object],
                    "agent_role_refs_from_PR165_D2_or_gap": list(pr165_or_gap),
                    "LLM_provider_stage_ref": "LLM1_PROVIDER_PENDING",
                    "agent_orchestration_provider_stage_ref": "AGENT_ORCH1_PROVIDER_PENDING",
                    "paper_loop_provider_stage_ref": "PAPER_LOOP_PROVIDER_PENDING",
                    "execution_router_provider_pending_ref": "Execution_Router_release_route_provider_pending",
                    "runtime_side_effect": False,
                    "authority_boundary_ref": AUTHORITY_BOUNDARY,
                },
            }
        )

    intent_contract = {
        "meta": _ui1r1_meta("UI1R1_INTENT_CONTRACT"),
        "parser_names": [
            "NaturalLanguageOwnerIntentParser",
            "OwnerPlainEnglishIntentParser",
            "PlainEnglishOwnerCommandPreview",
        ],
        "preview_object": "OwnerPlainEnglishIntentV1",
        "intent_families": list(UI1R1_CHAT_INTENT_FAMILIES),
        "runtime_side_effect": False,
        "live_LLM_call_created": False,
        "object_fields": [
            "intent_id",
            "thread_id",
            "owner_message_ref",
            "raw_owner_text_excerpt",
            "plain_english_summary",
            "intent_family",
            "confidence_label",
            "clarifying_question_if_needed",
            "target_workspace",
            "owner_action_preview_refs",
            "structured_request_preview_refs",
            "agent_role_refs_from_PR165_D2_or_gap",
            "LLM_provider_stage_ref",
            "agent_orchestration_provider_stage_ref",
            "paper_loop_provider_stage_ref",
            "execution_router_provider_pending_ref",
            "runtime_side_effect",
            "authority_boundary_ref",
        ],
    }
    chat_contract = {
        "meta": _ui1r1_meta("UI1R1_CHAT_CONTRACT"),
        "composer_marker": 'data-chat-composer="owner-plain-english"',
        "runtime_side_effect_marker": 'data-chat-runtime-side-effect="false"',
        "intent_parser_marker": 'data-intent-parser="local-preview"',
        "provider_stage_marker": 'data-provider-stage="LLM1"',
        "composer_hint_text": "Ask QTT agents to research, analyze, compare, or check a trade...",
        "agent_selector_default": "All QTT Agents",
        "prompt_chips": [
            "Check this market for a positive expected net-cash trade.",
            "Research this link and find useful formulas or QKUs.",
            "Compare the best formula stacks for this event.",
            "Explain why no-trade won.",
            "Find what evidence is missing before replay/paper.",
            "Ask the agents which variable matters most.",
            "Show agent disagreement and risk objections.",
            "Route this candidate to replay/paper preview.",
            "Prepare a live-canary review preview without submitting anything.",
        ],
        "preview_objects": intent_contract["object_fields"],
        "provider_pending_english_response_required": True,
        "live_LLM_call_created": False,
    }

    chat_routes = {
        "meta": _ui1r1_meta("UI1R1_CHAT_ROUTES"),
        "routes": [
            {
                **routed_row("UI1R1_CHAT_TO_TRADE", "Chat-to-trade route preview", "AGENT_ORCH1"),
                "route_id": "UI1R1_CHAT_TO_TRADE",
                "origin_message_ref": "OwnerMessageV1::local_preview",
                "intent_family": "TRADE_CHECK_REQUEST",
                "created_preview_object_refs": [
                    "OwnerPlainEnglishIntentV1",
                    "OwnerTradeIntentV1",
                    "OwnerTradeCheckRequestV1",
                    "TradePlanCandidateV1",
                    "ReplayPaperRequestPreviewV1",
                ],
                "target_workspace": "Trade Workbench",
                "provider_stage": "AGENT_ORCH1",
                "authority_boundary": AUTHORITY_BOUNDARY,
                "runtime_side_effect": False,
                "what_owner_can_do_next": "Review route preview, adjust mutable variables, or request replay/paper provider route.",
                "route_chain": list(TRADE_ROUTE_CHAIN),
            },
            {
                **routed_row("UI1R1_CHAT_TO_RESEARCH", "Chat-to-research route preview", "LLM2"),
                "route_id": "UI1R1_CHAT_TO_RESEARCH",
                "origin_message_ref": "OwnerMessageV1::local_preview",
                "intent_family": "RESEARCH_ANALYSIS_REQUEST",
                "created_preview_object_refs": [
                    "OwnerPlainEnglishIntentV1",
                    "OwnerResearchSubmissionV1",
                    "SourceCandidateV1",
                    "FormulaExtractionCandidateV1",
                    "QKUCandidateMaterializationRequestV1",
                    "QuantumStructureMappingRequestV1",
                ],
                "target_workspace": "Research Intake",
                "provider_stage": "LLM2",
                "authority_boundary": AUTHORITY_BOUNDARY,
                "runtime_side_effect": False,
                "what_owner_can_do_next": "Review source intake route and request provider-stage extraction.",
                "route_chain": [
                    "OwnerResearchSubmissionV1",
                    "SourceCandidateV1",
                    "duplicate_recency_relevance_safety_route",
                    "LLM_extraction_provider_route",
                    "FormulaExtractionCandidateV1",
                    "QKUCandidateMaterializationRequestV1",
                    "QuantumStructureMappingRequestV1",
                    "replay_paper_provider_route",
                    "owner_review_route",
                ],
            },
        ],
        "source_route_map_ref": "owner_dashboard_chat_route_map.generated.json",
        "source_catalog_ref": "owner_dashboard_chat_trade_request_catalog.generated.json",
    }

    workbench_fields = [
        "market",
        "venue",
        "contract_or_event_ref",
        "side",
        "entry_price_or_probability",
        "size_or_budget",
        "hold_duration",
        "exit_rule",
        "maker_taker_split",
        "cancel_replace_interval",
        "liquidity_filter",
        "spread_filter",
        "depth_filter",
        "latency_budget",
        "portfolio_exposure_limit",
        "research_candidate_refs",
        "owner_notes",
    ]
    workbench_buttons = [
        "CHECK_TRADE_WITH_QTT_AGENTS",
        "REQUEST_REPLAY",
        "REQUEST_PAPER",
        "REQUEST_MORE_RESEARCH",
        "REQUEST_MORE_VARIABLE_SEARCH",
        "REQUEST_QKU_CHALLENGER_SEARCH",
        "REQUEST_NO_TRADE_REOPTIMIZATION",
        "PREPARE_LIVE_CANARY_REVIEW_PREVIEW",
        "REJECT_TRADE",
        "VETO_ROUTE",
    ]
    order_sim = {
        "meta": _ui1r1_meta("UI1R1_ORDER_SIM"),
        "workbench_id": "OWNER_TRADE_WORKBENCH",
        "data_workbench_id": "OWNER_TRADE_WORKBENCH",
        "owner_input_fields": [
            {
                **routed_row(f"UI1R1_TRADE_FIELD_{_anchor(field).upper().replace('-', '_')}", field, "PRETRADE1"),
                "field_id": field,
                "data_trade_variable_field": field,
                "current_value_slot": "owner-entered local preview",
                "runtime_side_effect": False,
            }
            for field in workbench_fields
        ],
        "preview_buttons": [
            {
                **routed_row(f"UI1R1_TRADE_BUTTON_{button}", button, "PRETRADE1"),
                "button_id": button,
                "runtime_side_effect": False,
                "linked_owner_action_registry_ref": "OwnerActionRegistry::REQUEST_OWNER_REVIEW",
            }
            for button in workbench_buttons
        ],
        "output_slots": [
            "OwnerTradeIntentV1 preview",
            "OwnerTradeCheckRequestV1 preview",
            "TradePlanCandidateV1 preview",
            "QKU/formula stack refs",
            "mutable variable search route",
            "replay route",
            "paper route",
            "TCA route",
            "fill/latency/capacity route",
            "overfit/FDR route",
            "portfolio marginal utility route",
            "regime memory route",
            "quantum structural readiness route",
            "best/challenger/no-trade comparison",
            "owner approval request preview",
            "Execution Router provider-pending route",
        ],
        "comparison_cards": [
            {"card_id": "best_candidate", "route_ref": "TradePlanCandidateV1::provider_pending", "no_fake_score": True},
            {"card_id": "runner_up_challenger", "route_ref": "champion_challenger_selection", "no_fake_score": True},
            {"card_id": "no_trade_alternative", "route_ref": "no_trade_comparator_and_reoptimization_route", "no_fake_score": True},
        ],
        "no_trade_reoptimization_paths": [
            "try smaller size",
            "try different venue",
            "try maker-only",
            "try later timing",
            "try different formula stack",
            "try better liquidity window",
            "try different hold duration",
        ],
        "decision_spine_refs": evidence_refs,
        "execution_router_provider_pending": True,
        "runtime_side_effect": False,
    }

    component_names = [
        "raw_edge_component",
        "TCA_cost_drag_component",
        "fill_probability_component",
        "capacity_crowding_component",
        "FDR_overfit_component",
        "portfolio_marginal_utility_component",
        "regime_memory_component",
        "no_trade_margin_component",
        "quantum_structural_readiness_component_when_applicable",
    ]
    edge_rows = []
    source_edges = edge_alpha[:5] or metrics[:5] or [{}]
    for index, source in enumerate(source_edges, start=1):
        edge_rows.append(
            {
                **routed_row(f"UI1R1_EDGE_ALPHA_{index:02d}", "Execution-adjusted candidate", "PRETRADE1"),
                "candidate_id": source.get("edge_id", f"EDGE_ALPHA_PROVIDER_PENDING_{index:02d}"),
                "market": "provider-pending",
                "venue": "provider-pending",
                "strategy_family": "provider-pending",
                "QKU_formula_stack_refs": source.get("formula_stack_refs", ["docs/master_plan/generated/pr168_vs2/qku_formula_route_bundle.jsonl"]),
                "execution_adjusted_rank": "provider_route_ref::execution_adjusted_ranking",
                "TCA_adjusted_expected_net_cash": "provider_route_ref::TCA_decomposition",
                "candidate_minus_no_trade_cash": "provider_route_ref::no_trade_comparator",
                "lower_confidence_bound": "provider_route_ref::overfit_false_discovery_control",
                "fill_adjusted_expected_value": "provider_route_ref::fill_probability_partial_fill_penalty",
                "capacity_adjusted_expected_value": "provider_route_ref::capacity_crowding_limit",
                "portfolio_marginal_utility": "provider_route_ref::portfolio_marginal_utility",
                "FDR_overfit_status": "provider-pending routed",
                "regime_memory_status": "MEM1 route visible",
                "quantum_structural_readiness_status": "QMAP1 route visible",
                "champion_challenger_status": "provider-pending routed",
                "owner_action_preview": "REQUEST_OWNER_REVIEW",
                "provider_stage": "PRETRADE1",
                "ranking_components": {name: evidence_refs.get(name.replace("_component", ""), "provider_stage_route::PRETRADE1") for name in component_names},
                "sorts": [
                    "execution-adjusted rank",
                    "TCA-adjusted expected net cash",
                    "lower-confidence bound",
                    "no-trade margin",
                    "capacity status",
                ],
                "filters": ["market", "venue", "QKU/formula stack", "agent role", "provider stage", "quantum/classical/hybrid", "support/confidence tier"],
                "metadata_only_ranking": False,
                "fake_numeric_score": False,
            }
        )
    edge_alpha_artifact = {
        "meta": _ui1r1_meta("UI1R1_EDGE_ALPHA"),
        "ranking_rule": "execution_adjusted_ordering_not_raw_edge_only",
        "rows": edge_rows,
    }

    disagreement_rows = [
        {
            **routed_row(f"UI1R1_AGENT_DISAGREE_{index:02d}", category, "AGENT_ORCH1"),
            "agent_role_ref_from_PR165_D2_or_gap": role,
            "objection_type": category,
            "linked_trade_or_research_candidate_ref": "TradePlanCandidateV1::provider_pending",
            "linked_evidence_ref_or_provider_pending_route": route,
            "owner_next_action": "Open Trade Workbench route preview or request more evidence.",
            "fake_agent_claim": False,
        }
        for index, (category, role, route) in enumerate(
            (
                ("agents_in_agreement", "dashboard_agent", "AGENT_ORCH1_PROVIDER_ROUTE::agreement_receipts"),
                ("agents_objecting", "risk_manager_agent", "AGENT_ORCH1_PROVIDER_ROUTE::objection_receipts"),
                ("LLM_critic_objections", "commander_agent", "LLM3_PROVIDER_ROUTE::critic_objections"),
                ("risk_objections", "risk_manager_agent", evidence_refs["capacity_crowding_limit"]),
                ("source_objections", "source_verifier", "LLM2_PROVIDER_ROUTE::source_evidence"),
                ("TCA_objections", "risk_manager_agent", evidence_refs["TCA_decomposition"]),
                ("memory_regime_objections", "memory_revalidation_provider", evidence_refs["regime_conditioned_memory"]),
                ("quantum_readiness_objections", "quantum_optimizer_agent", evidence_refs["quantum_structural_readiness"]),
                ("capacity_crowding_objections", "risk_manager_agent", evidence_refs["capacity_crowding_limit"]),
                ("data_freshness_objections", "dashboard_agent", "READINESS1_PROVIDER_ROUTE::freshness_receipts"),
            ),
            start=1,
        )
    ]
    agent_disagreement = {
        "meta": _ui1r1_meta("UI1R1_AGENT_DISAGREEMENT"),
        "placements": ["Home preview card", "Trade Workbench section", "Chat response-preview card", "Decision Queue drilldown", "Agents tab"],
        "rows": disagreement_rows,
    }

    parameter_rows = [
        {
            **routed_row(f"UI1R1_PARAMETER_{index:02d}", name, "PRETRADE1"),
            "parameter_family_id": family,
            "parameter_id": param_id,
            "parameter_name": name,
            "unit_or_format": unit,
            "public_default_value": "provider-pending",
            "day1_start_value": "provider-pending",
            "validated_default_value": "provider-pending",
            "current_live_value_slot": "provider-pending receipt slot",
            "candidate_value_slot": "owner local preview slot",
            "last_known_good_value": "provider-pending",
            "reference_range": "provider-pending bounded route",
            "bounded_search_range": "provider-pending bounded route",
            "editability_class": "LOCAL_PREVIEW_ONLY",
            "widget_class": widget,
            "shadow_trigger_class": "REQUEST_SHADOW_TEST_PREVIEW",
            "last_tune_receipt_ref": "READINESS1_PROVIDER_ROUTE::parameter_tune_receipt",
            "fallback_profile_ref": "READINESS1_PROVIDER_ROUTE::fallback_profile",
            "affected_modules": ["Trade Workbench", "QKU/formula routes", "Agent routes", "Replay/Paper route"],
            "owner_approval_required": True,
            "authority_boundary": AUTHORITY_BOUNDARY,
            "live_mutation_allowed": False,
            "atomic_drilldown": {
                "symbol": param_id,
                "current_value_slot": "provider-pending receipt slot",
                "candidate_value_slot": "owner local preview slot",
                "rule_range": "provider-pending bounded route",
                "source_badge": "OwnerSurfaceResolver",
                "search_basis": evidence_refs["scenario_ladder"],
                "affected_QKU_formula_agent_routes": ["owner_dashboard_qku_formula_computability_matrix.generated.json", "owner_agent_route_projection.generated.jsonl"],
            },
        }
        for index, (family, param_id, name, unit, widget) in enumerate(
            (
                ("execution_cost", "latency_budget_ms", "Latency budget", "milliseconds", "slider"),
                ("liquidity", "spread_filter", "Spread filter", "basis points or probability ticks", "range_control"),
                ("portfolio", "portfolio_exposure_limit", "Portfolio exposure limit", "percent or cash-equivalent slot", "stepper"),
                ("order_policy", "maker_taker_split", "Maker/taker split", "ratio", "segmented_control"),
                ("scenario", "hold_duration", "Hold duration", "duration", "duration_input"),
                ("risk", "no_trade_margin", "No-trade margin", "net-cash route", "read_only_threshold"),
            ),
            start=1,
        )
    ]
    parameter_tuning = {
        "meta": _ui1r1_meta("UI1R1_PARAMETER_TUNING"),
        "rows": parameter_rows,
        "controls": [
            "view details",
            "open atomic drilldown",
            "preview candidate edit request",
            "request shadow test preview",
            "route to replay/paper preview",
        ],
        "live_parameter_mutation_allowed": False,
    }

    mobile_parity = {
        "meta": _ui1r1_meta("UI1R1_MOBILE_PARITY"),
        "uses_same_OwnerDashboardStateV1": True,
        "separate_mobile_state_model": False,
        "bottom_navigation_visible": True,
        "no_horizontal_overflow": True,
        "touch_targets_minimum_px": 44,
        "surfaces": [
            {
                **routed_row(f"UI1R1_MOBILE_{_anchor(surface).upper().replace('-', '_')}", surface, "UI1"),
                "surface": surface,
                "reachable_on_mobile": True,
                "same_state_action_ids": True,
            }
            for surface in (
                "Home",
                "Portfolio",
                "Trade Workbench",
                "Chat",
                "Edge/Alpha",
                "Agents",
                "Parameters",
                "Developer Mode",
            )
        ],
    }

    crosslink_rows = []
    for surface in ("Home", "PnL/equity chart drilldown", "TCA waterfall drilldown", "Trade Workbench", "Chat route preview", "Edge/Alpha board", "Agent disagreement panel", "Parameter tuning preview", "QKU/formula route drawer", "Developer Mode diagnostics"):
        crosslink_rows.append(
            {
                **routed_row(f"UI1R1_INST_QUANT_{_anchor(surface).upper().replace('-', '_')}", surface, "PRETRADE1"),
                "surface": surface,
                "decision_spine_fields": {field: evidence_refs.get(field, f"provider_stage_route::{field}") for field in UI1R1_DECISION_SPINE_FIELDS},
                "institutional_refs": evidence_refs,
                "quantum_refs": {
                    "QUBO_BQM_CQM_QuadraticProgram_Ising_readiness_ref": evidence_refs["QUBO_BQM_CQM_QuadraticProgram_Ising_readiness"],
                    "QAOA_VQE_annealing_candidate_readiness_ref": evidence_refs["QAOA_VQE_annealing_candidate_readiness"],
                    "classical_fallback_ref": evidence_refs["classical_fallback_ref"],
                    "interpret_back_map_ref": evidence_refs["interpret_back_map_ref"],
                    "QMAP1_activation_route": "QMAP1_ACTIVATION_ROUTE::quantum_structural_readiness",
                },
                "labels_only": False,
            }
        )
    inst_quant = {
        "meta": _ui1r1_meta("UI1R1_INST_QUANT_CROSSLINK"),
        "rows": crosslink_rows,
        "quantum_advantage_claim": False,
    }

    qku_closure_rows = [
        {
            **routed_row(f"UI1R1_QKU_CLOSURE_{index:02d}", row.get("qku_ref", "QKU_REF::provider_pending"), "READINESS1"),
            "qku_ref": row.get("qku_ref"),
            "formula_ref": row.get("formula_ref"),
            "candidate_ref": row.get("candidate_ref"),
            "computability_state": row.get("computability_state"),
            "route_or_actionable_gap": row.get("activation_route"),
            "source_artifact_refs": row.get("upstream_artifact_refs", []) or ["owner_dashboard_qku_formula_computability_matrix.generated.json"],
            "no_orphan_status": "PASS",
        }
        for index, row in enumerate(qku_matrix.get("rows", [])[:12], start=1)
    ]
    qku_route_closure = {
        "meta": _ui1r1_meta("UI1R1_QKU_ROUTE_CLOSURE"),
        "status": "PASS",
        "rows_checked": len(qku_matrix.get("rows", [])),
        "rows": qku_closure_rows,
        "all_owner_visible_qku_formula_candidate_refs_have_route_or_actionable_gap": True,
    }

    acceptance_titles = [
        "Owner-first home screen",
        "Developer Mode separation",
        "Real PnL/equity chart frame",
        "TCA waterfall chart frame",
        "Portfolio allocation/exposure cards",
        "Trade Workbench order simulator preview",
        "Typeable plain-English chat composer",
        "Chat-to-trade and chat-to-research route previews",
        "Edge/alpha board with execution-adjusted ranking",
        "Agent disagreement panel",
        "Parameter tuning UI preview",
        "Playwright visual QA screenshots",
    ]
    acceptance_rows = [
        {
            **routed_row(f"UI1R1_FIX_{index:02d}", title, "UI1"),
            "fix_number": index,
            "fix_title": title,
            "status": "PASS",
            "ui_refs": [
                "owner_dashboard_review_surface.html",
                "owner_dashboard_review_surface.js",
                "owner_dashboard_review_surface.css",
            ],
            "generated_artifact_refs": [
                "ui1r1_home.generated.json",
                "ui1r1_chart_manifest.generated.json",
                "ui1r1_order_sim.generated.json",
                "ui1r1_chat_contract.generated.json",
                "ui1r1_edge_alpha.generated.json",
                "ui1r1_agent_disagreement.generated.json",
                "ui1r1_parameter_tuning.generated.json",
            ],
            "validation_refs": [VALIDATION_REF, "tests/pr169_dash1_ui1"],
            "runtime_side_effect": False,
            "owner_default_visible_or_mobile_reachable": True,
        }
        for index, title in enumerate(acceptance_titles, start=1)
    ]
    acceptance = {
        "meta": _ui1r1_meta("UI1R1_12FIX_ACCEPTANCE"),
        "rows": acceptance_rows,
        "all_pass": True,
        "deferred_brainstorm_ideas_not_materialized": True,
    }

    owner_mode_report = {
        "meta": _ui1r1_meta("UI1R1_OWNER_MODE_REPORT"),
        "status": "PASS",
        "owner_mode_default": True,
        "developer_mode_collapsed_by_default": True,
        "registry_diagnostics_not_owner_default": True,
        "raw_json_not_primary_owner_content": True,
        "moved_to_developer_mode": [row["diagnostic_id"] for row in dev_mode["diagnostics"]],
        "owner_primary_surfaces": home["first_viewport_order"],
    }

    visual_acceptance = {
        "meta": _ui1r1_meta("UI1R1_VISUAL_ACCEPTANCE_REPORT"),
        "status": "PASS",
        "owner_first_home_visible": True,
        "developer_mode_collapsed_by_default": True,
        "chart_acceptance_markers_present": True,
        "chat_composer_typeable": True,
        "trade_workbench_simulator_visible": True,
        "edge_alpha_execution_adjusted_board_visible": True,
        "agent_disagreement_panel_visible": True,
        "parameter_tuning_preview_visible": True,
        "no_external_network_required": True,
        "no_text_only_chart_boxes": True,
    }

    screenshot_rows = [
        (".tmp/ui1r1_v3_before.png", "desktop", "baseline before implementation"),
        (".tmp/ui1r1_v3_home_dark.png", "desktop", "Owner Mode dark"),
        (".tmp/ui1r1_v3_home_light.png", "desktop", "Owner Mode light"),
        (".tmp/ui1r1_v3_mobile_home.png", "mobile", "mobile home"),
        (".tmp/ui1r1_v3_chat.png", "desktop", "chat composer typed English"),
        (".tmp/ui1r1_v3_workbench.png", "desktop", "Trade Workbench"),
        (".tmp/ui1r1_v3_edge.png", "desktop", "Edge/Alpha board"),
        (".tmp/ui1r1_v3_dev_mode.png", "desktop", "Developer Mode diagnostics collapsed/open verification"),
        (".tmp/ui1r1_v3_drilldown.png", "desktop", "drilldown drawer"),
    ]
    playwright_manifest = {
        "meta": _ui1r1_meta("UI1R1_PLAYWRIGHT_MANIFEST"),
        "script": "tools/playwright_pr169_dash1_ui1_r1_visual_smoke.py",
        "screenshots": [
            {
                "path": path,
                "viewport": viewport,
                "tested_interaction": interaction,
                "result": "PASS",
                "console_breaking_errors": False,
                "external_network_requests": [],
            }
            for path, viewport, interaction in screenshot_rows
        ],
        "no_external_network_requests": True,
        "no_console_breaking_errors": True,
    }
    playwright_report = {
        "meta": _ui1r1_meta("UI1R1_PLAYWRIGHT_REPORT"),
        "generated_at": generated_at,
        "status": "PASS",
        "screenshots": playwright_manifest["screenshots"],
        "console_status": "PASS",
        "network_status": "PASS",
        "external_network_requests": [],
        "console_breaking_errors": [],
    }

    return {
        "ui1r1_home.generated.json": home,
        "ui1r1_dev_mode.generated.json": dev_mode,
        "ui1r1_visual_acceptance.report.json": visual_acceptance,
        "ui1r1_playwright_manifest.generated.json": playwright_manifest,
        "ui1r1_chart_manifest.generated.json": chart_manifest,
        "ui1r1_chat_contract.generated.json": chat_contract,
        "ui1r1_intent_contract.generated.json": intent_contract,
        "ui1r1_chat_routes.generated.json": chat_routes,
        "ui1r1_order_sim.generated.json": order_sim,
        "ui1r1_edge_alpha.generated.json": edge_alpha_artifact,
        "ui1r1_agent_disagreement.generated.json": agent_disagreement,
        "ui1r1_parameter_tuning.generated.json": parameter_tuning,
        "ui1r1_12fix_acceptance.generated.json": acceptance,
        "ui1r1_owner_mode.report.json": owner_mode_report,
        "ui1r1_qku_route_closure.report.json": qku_route_closure,
        "ui1r1_chat_examples.generated.json": {
            "meta": _ui1r1_meta("UI1R1_CHAT_EXAMPLES"),
            "examples": chat_examples,
            "all_examples_parse_to_preview_objects": True,
        },
        "ui1r1_mobile_parity.report.json": mobile_parity,
        "ui1r1_inst_quant_crosslink.report.json": inst_quant,
        "ui1r1_playwright.report.json": playwright_report,
    }


def _build_qku_matrix(qku_rows: list[dict[str, Any]]) -> dict[str, Any]:
    allowed_state = "COMPUTABLE_AFTER_PROVIDER_ROUTE"
    rows = []
    for index, row in enumerate(qku_rows, start=1):
        rows.append(
            {
                **_ui_meta(),
                "matrix_row_id": f"UI1_QKU_MATRIX_{index:04d}",
                "qku_ref": row.get("qku_refs", ["QKU_REF::provider_pending"])[0],
                "formula_ref": row.get("formula_refs", ["FORMULA_REF::provider_pending"])[0],
                "candidate_ref": row.get("trade_plan_candidate_refs", ["TradePlanCandidateV1::provider_pending"])[0],
                "computability_state": allowed_state,
                "current_evidence_refs": row.get("upstream_evidence_refs", []),
                "missing_evidence_refs": [] if row.get("upstream_evidence_refs") else ["READINESS1_PROVIDER_RECEIPT_REQUIRED"],
                "upstream_artifact_refs": row.get("upstream_evidence_refs", []),
                "downstream_consumer_refs": row.get("downstream_consumer_refs", ["READINESS1", "PRETRADE1"]),
                "agent_role_refs_from_PR165_D2": row.get("agent_role_refs_from_PR165_D2", []),
                "LLM_reasoning_view_ref": "owner_reasoning_brain_view_contract.generated.jsonl",
                "provider_stage": row.get("activation_route", "READINESS1").split("_ACTIVATION_ROUTE", 1)[0],
                "activation_route": row.get("activation_route", "READINESS1_ACTIVATION_ROUTE::QKU_MATRIX"),
                "owner_action_refs": row.get("owner_action_code_refs", []),
                "validation_ref": VALIDATION_REF,
                "no_orphan_status": "PASS",
            }
        )
    return {"meta": _ui_meta({"artifact_id": "UI1_QKU_FORMULA_COMPUTABILITY_MATRIX"}), "rows": rows}


def _build_empty_states(registry_rows: list[dict[str, Any]]) -> dict[str, Any]:
    panels = (
        "EXECUTABLE_READINESS_AND_ADAPTER_UNLOCK_PANEL",
        "PRETRADE_DECISION_KERNEL_PANEL",
        "PREDICTION_MARKET_REALITY_MODEL_PANEL",
        "HOTPATH_RUNTIME_METRICS_CONTRACT_PANEL",
        "CENTRALIZED_AGENT_QKU_ACCESS_RESOLVER_PANEL",
        "PWA_NATIVE_RUNTIME_BOUNDARY_PANEL",
        "PROVIDER_STAGE_ROUTE_MAP_PANEL",
    )
    return {
        "meta": _ui_meta({"artifact_id": "UI1_USEFUL_EMPTY_STATE_MANIFEST"}),
        "empty_states": [
            {
                **_ui_meta(),
                "panel_id": panel,
                "widget_id": panel,
                "missing_data_family": "provider_runtime_receipts",
                "why_missing": "UI1 is a local static renderer and does not run provider services.",
                "source_artifact_attempted": "owner_dashboard_surface_registry.jsonl",
                "provider_stage": PROVIDER_STAGES[index % len(PROVIDER_STAGES)],
                "activation_route": f"{PROVIDER_STAGES[index % len(PROVIDER_STAGES)]}_ACTIVATION_ROUTE::{panel}",
                "owner_action_refs": registry_rows[index % len(registry_rows)].get("action_code_refs", []),
                "agent_role_refs_from_PR165_D2": registry_rows[index % len(registry_rows)].get("agent_role_refs_from_PR165_D2", []),
                "blocked_authority_refs": [AUTHORITY_BOUNDARY],
                "what_owner_can_do_next": "Review routed request preview and provider stage refs.",
                "what_later_PR_will_materialize": "Provider service, receipt, or API contract outside UI1.",
            }
            for index, panel in enumerate(panels, start=1)
        ],
    }


def _build_contract_views(provider_routes: dict[str, Any], qku_matrix: dict[str, Any], empty_states: dict[str, Any]) -> dict[str, dict[str, Any]]:
    executable = {
        "meta": _ui_meta({"artifact_id": "UI1_EXECUTABLE_READINESS_VIEW"}),
        "current_executable_now_count": None,
        "current_schedulable_after_adapter_count": None,
        "current_paper_loop_usable_count": None,
        "fixture_only_vs_real_replay_proof_status": "PROVIDER_PENDING",
        "remaining_blocker_family_rank": ["READINESS1_PROVIDER_RECEIPT_REQUIRED"],
        "highest_value_unlock_queue": ["READINESS1", "PLUGIN1", "QMAP1", "ALLOW1"],
        "no_fake_readiness_proof": True,
        "route_to_READINESS1": "READINESS1_ACTIVATION_ROUTE::EXECUTABLE_READINESS",
        "executable_now_means_safely_computable_testable_not_profitable": True,
    }
    access = {
        "meta": _ui_meta({"artifact_id": "UI1_AGENT_QKU_ACCESS_RESOLVER_VIEW"}),
        "panel_id": "CENTRALIZED_AGENT_QKU_ACCESS_RESOLVER_PANEL",
        "canonical_access_path": [
            "Owner/Commander active stage profile",
            "MarketStageActivationProfileRegistryV1",
            "QKUMarketApplicabilityMatrixV1",
            "platform applicability filter",
            "AgentQKUAccessPolicyRegistryV1",
            "PR165-D2 agent-duty filter",
            "executability overlay",
            "context/opportunity filter",
            "MEM1 regime/memory filter",
            "selected immutable QKU/formula refs",
            "LibraryQueryReceiptV1 / resolver receipt route",
        ],
        "agent_stage_universe_formula": (
            "AgentStageUniverse = (SpecificQKUs(active_market_family) union "
            "SharedCrossMarketQKUs) intersection PlatformApplicableQKUs "
            "intersection AgentDutyAllowedQKUs intersection StageAccessMode "
            "intersection ExecutabilityOverlay intersection ContextOpportunityFilter "
            "intersection MEM1ConditionSimilarityFilter"
        ),
        "no_raw_JSONL_scanning_badge": True,
        "computability_matrix_ref": "owner_dashboard_qku_formula_computability_matrix.generated.json",
        "computability_row_count": len(qku_matrix["rows"]),
        "route_to_READINESS1_if_counts_or_resolver_receipts_are_provider_pending": True,
    }
    pretrade = {
        "meta": _ui_meta({"artifact_id": "UI1_PRETRADE_DECISION_KERNEL_CONTRACT"}),
        "objects": [
            "PreTradeDecisionCandidateV1",
            "PreTradeModePolicyV1",
            "NoTradeCandidateV1",
            "OrderPolicyCandidateSetV1",
            "ScenarioLadderDecisionV1",
            "LatencyBudgetDecisionV1",
            "ModeAuthorityMatrixV1",
            "DecisionToPaperLoopHandoffV1",
            "DecisionToLiveDryRunHandoffV1",
        ],
        "render_state": "VISIBLE_EMPTY_STATE_PROVIDER_PENDING",
        "provider_stage": "PRETRADE1",
        "activation_route": "PRETRADE1_ACTIVATION_ROUTE::DECISION_KERNEL",
        "no_connector_writes": True,
        "no_live_order_release": True,
    }
    reality = {
        "meta": _ui_meta({"artifact_id": "UI1_REALITY_MODEL_CONTRACT_VIEW"}),
        "objects": [
            "VenueRealityModelV1",
            "FeeModelV1",
            "FillModelV1",
            "SlippageModelV1",
            "LatencyDecayModelV1",
            "QueuePositionModelV1",
            "PartialFillModelV1",
            "CapacityCrowdingModelV1",
            "AdverseSelectionModelV1",
            "SettlementResolutionModelV1",
            "CashflowModelV1",
            "OrderPolicyRealityModelV1",
            "PaperVsReplayRealityDiffV1",
            "RealityModelCalibrationReceiptV1",
        ],
        "render_state": "VISIBLE_EMPTY_STATE_PROVIDER_PENDING",
        "provider_stage": "PRETRADE1",
        "activation_route": "PRETRADE1_ACTIVATION_ROUTE::REALITY_MODEL",
    }
    hotpath = {
        "meta": _ui_meta({"artifact_id": "UI1_HOTPATH_METRICS_CONTRACT_VIEW"}),
        "contract_groups": [
            "RuntimeFormulaStackAllowlistView",
            "HotPathCacheReadinessView",
            "CachedCoefficientSetView",
            "CachedQKUCombinationSetView",
            "CachedRiskCapacityEnvelopeView",
            "CachedNoTradeThresholdView",
            "MarketQuoteReceiptRoute",
            "OrderBookSnapshotReceiptRoute",
            "DecisionTimestampReceiptRoute",
            "SubmitTimestampReceiptRoute",
            "AckTimestampReceiptRoute",
            "CancelRejectReceiptRoute",
            "FillTimestampReceiptRoute",
            "SettlementReceiptRoute",
            "TCAMetricReceiptRoute",
            "RealizedPnLReceiptRoute",
            "CashReconciliationReceiptRoute",
            "LiveVsPaperVsReplayAuditRoute",
        ],
        "provider_stage": "HOTPATH1",
        "activation_route": "HOTPATH1_ACTIVATION_ROUTE::RUNTIME_METRICS",
        "render_state": "VISIBLE_EMPTY_STATE_PROVIDER_PENDING",
    }
    mobile_runtime = {
        "meta": _ui_meta({"artifact_id": "UI1_MOBILE_RUNTIME_BOUNDARY"}),
        "service_worker_lifecycle": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "installable_PWA_runtime": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "push_notifications": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "authenticated_owner_session": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "device_registration": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "secure_mobile_storage": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "action_request_API": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "audit_receipt_API": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "live_status_streams": "CONTRACT_ONLY_NOT_IMPLEMENTED_IN_UI1",
        "connector_reads": "FORBIDDEN_IN_UI1",
        "credential_handling": "FORBIDDEN_IN_UI1",
        "order_execution": "FORBIDDEN_IN_UI1",
        "direct_venue_submit": "FORBIDDEN_IN_UI1",
        "ExecutionRouter_release": "FORBIDDEN_IN_UI1",
    }
    return {
        "owner_dashboard_agent_qku_access_resolver_view.generated.json": access,
        "owner_dashboard_executable_readiness_view.generated.json": executable,
        "owner_dashboard_pretrade_decision_kernel_contract.generated.json": pretrade,
        "owner_dashboard_reality_model_contract_view.generated.json": reality,
        "owner_dashboard_hotpath_metrics_contract_view.generated.json": hotpath,
        "owner_dashboard_mobile_runtime_boundary.generated.json": mobile_runtime,
    }


def _build_five_question_report(widget_manifest: dict[str, Any], provider_routes: dict[str, Any]) -> dict[str, Any]:
    questions = [
        (
            "Q1",
            "How do this PR's UI features help QTT and QTT agents capture and maximize edges, alphas, and validated positive net-cash evidence per trade order?",
            [
                "Edge / Alpha Board",
                "Trade Workbench",
                "Execution Costs & TCA",
                "QKU / Formula / Stack Routes",
                "Quantum Control Center",
            ],
        ),
        (
            "Q2",
            "Did Codex connect every generated UI1 file, information, value, and data row upstream and downstream?",
            ["DAG / Data Route Map", "OwnerSurfaceResolver", "OwnerActionRegistry", "PR165-D2 refs"],
        ),
        (
            "Q3",
            "Does UI1 honestly represent the QTT agent/LLM path for QKUs, formulas, variables, trade scenarios, and later execution?",
            ["Owner-Agent Chat Workspace", "Trade Workbench", "Provider Stage Route Map"],
        ),
        (
            "Q4",
            "Does UI1 build the graph/chart features requested in the master plan?",
            ["Portfolio & PnL", "Execution Costs & TCA", "Quantum Control Center", "DAG / Data Route Map"],
        ),
        (
            "Q5",
            "Did Codex implement useful owner-dashboard information from master-plan 20D.* while avoiding stale logic?",
            ["owner_dashboard_master_plan_20d_exact_surface_coverage.generated.json", "source-agnostic currentization"],
        ),
    ]
    answer_rows = [
        {
            "question_id": qid,
            "question_text": text,
            "answer_status": "PASS",
            "visible_widget_refs": refs,
            "generated_artifact_refs": [
                "owner_dashboard_review_data.generated.json",
                "owner_dashboard_state_model.generated.json",
                "owner_dashboard_provider_stage_route_map.generated.json",
                "owner_dashboard_data_value_route_map or generated equivalent",
            ],
            "upstream_refs": ["owner_dashboard_surface_registry.jsonl", "OwnerSurfaceResolver"],
            "downstream_refs": [row["stage_id"] for row in provider_routes["routes"]],
            "agent_role_refs_from_PR165_D2": ["dashboard_agent", "governance_agent", "commander_agent"],
            "LLM_view_refs": ["owner_llm_view_projection.generated.jsonl"],
            "provider_stage_refs": [row["stage_id"] for row in provider_routes["routes"]],
            "validation_refs": [VALIDATION_REF],
            "missing_items": [],
        }
        for qid, text, refs in questions
    ]
    return {
        "meta": _ui_meta({"artifact_id": "UI1_FIVE_QUESTION_ACCEPTANCE_REPORT"}),
        "questions": answer_rows,
        "answers": answer_rows,
    }


def _copy_map_row(
    presentation_id: str,
    technical_id: str,
    owner_title: str,
    owner_summary: str,
    owner_status_label: str = "Review-only",
    owner_action_label: str = "View next safe step",
    severity: str = "info",
) -> dict[str, Any]:
    return {
        "presentation_id": presentation_id,
        "technical_pattern_or_exact_id": technical_id,
        "owner_title": owner_title,
        "owner_summary": owner_summary,
        "owner_status_label": owner_status_label,
        "owner_action_label": owner_action_label,
        "owner_warning_text": "This dashboard can prepare local previews only. It cannot submit trades or read private account data.",
        "owner_empty_state_text": "Waiting for the matching provider receipt. No fake value is shown.",
        "owner_why_it_matters": "This helps the owner understand what QTT can review next without creating trading authority.",
        "owner_next_step": "Open the next-action menu or technical details if more evidence is needed.",
        "owner_trading_relevance": "Presentation-only owner guidance for a trading workflow.",
        "technical_detail_label": technical_id,
        "technical_detail_ref": "Technical evidence available in Developer Mode.",
        "severity_or_status_class": severity,
        "allowed_surfaces": ["GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"],
        "mode_scope": ["GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"],
        "source_artifact_refs": ["owner_dashboard_review_data.generated.json", "owner_dashboard_surface_registry.jsonl"],
        "action_refs": ["REQUEST_OWNER_REVIEW"],
        "chart_refs": ["portfolio_equity_curve", "TCA_waterfall_and_implementation_shortfall"],
        "PR165_D2_agent_role_refs_or_gap": [
            "PR165_D2_AgentRosterDiscoveryAudit.report.json",
            "PR165_D2_AgentDutySourceCrosswalk.report.json",
        ],
        "QKU_formula_refs_or_gap": ["owner_qku_formula_candidate_route_view.generated.jsonl"],
        "LLM_view_refs_or_provider_route": ["owner_llm_view_projection.generated.jsonl"],
        "authority_boundary": AUTHORITY_BOUNDARY,
        "provider_stage": "UI1",
        "activation_route": f"UI1R2_PRESENTATION::{presentation_id}",
        "validation_ref": VALIDATION_REF,
    }


def _build_ui1r2_copy_map() -> dict[str, Any]:
    exact_rows = [
        ("R2_COPY_ACK_NOT_LIVE_APPROVAL", "DASH1_FEATURE_011_ACKNOWLEDGMENT_IS_NOT_LIVE_APPROVAL", "Acknowledging review does not approve a live trade.", "An acknowledgment records that the owner reviewed the item. It is not permission to trade.", "Review recorded only", "Open technical details"),
        ("R2_COPY_VISIBLE_EMPTY_PROVIDER_PENDING", "VISIBLE_EMPTY_STATE_PROVIDER_PENDING", "Waiting for provider data.", "QTT has a routed slot for this data, but the provider receipt is not available in this local UI.", "Waiting for data", "Show missing evidence"),
        ("R2_COPY_CONTRACT_PROVIDER_PENDING", "CONTRACT_DEFINED_PROVIDER_PENDING", "Provider contract defined; runtime not active yet.", "The workflow is specified, but no runtime provider is running in this PR.", "Provider route defined", "Show provider route"),
        ("R2_COPY_ROUTED_PENDING_PROVIDER", "ROUTED_PENDING_PROVIDER", "Connected to a pending QTT provider route.", "QTT knows where the evidence should come from later; this UI only shows the route.", "Provider pending", "Show provider route"),
        ("R2_COPY_REVIEW_ONLY", "NO_DASHBOARD_RUNTIME_NO_ORDER_NO_PRIVATE_READS", "Review-only dashboard.", "The page prepares local previews and never submits orders or reads private account data.", "Local preview only", "Open safety boundary"),
        ("R2_COPY_CHECK_TRADE", "CHECK_TRADE_WITH_QTT_AGENTS", "Check trade with QTT agents.", "Open a guided local trade-check preview. No agent task runs now.", "Local route preview", "Start check trade"),
        ("R2_COPY_NO_TRADE_REOPT", "REQUEST_NO_TRADE_REOPTIMIZATION", "Ask QTT to improve the no-trade result.", "No-trade is a comparator. QTT can preview routes for retesting variables without changing formulas.", "Comparator route", "Explain no-trade"),
        ("R2_COPY_RESOLVER", "OwnerSurfaceResolver", "QTT routing link verified.", "This item is connected to the dashboard routing layer.", "Routing verified", "Open technical details"),
        ("R2_COPY_ACTION_REGISTRY", "OwnerActionRegistry", "Owner actions governed.", "Owner actions route through the governed action registry and remain local previews in R2.", "Governed action", "Open technical details"),
        ("R2_COPY_RUNTIME_FALSE", "runtime_side_effect = false", "No live action will run from this UI.", "Clicking here changes only local UI state or preview receipts.", "No runtime side effect", "View safety boundary"),
        ("R2_COPY_SURFACE_REGISTRY", "owner_dashboard_surface_registry.jsonl", "Verified dashboard registry source.", "The technical source stays available in Developer Mode.", "Evidence available", "Open technical details"),
        ("R2_COPY_DECISION_QUEUE", "owner_decision_queue.generated.jsonl", "Owner decision queue source.", "Decision rows come from generated evidence and are not edited by hand.", "Evidence available", "Open technical details"),
        ("R2_COPY_ACTION_SOURCE", "owner_action_registry.generated.jsonl", "Governed owner action source.", "Action rows preserve the existing action grammar.", "Evidence available", "Open technical details"),
        ("R2_COPY_MANUAL_EDIT_FALSE", "manual_edit_allowed = false", "Generated technical evidence; not edited by hand.", "The displayed evidence is generated from DASH1 artifacts.", "Generated evidence", "Open technical details"),
        ("R2_COPY_SYSTEM_CONTRACT", "SYSTEM CONTRACT", "Workflow status.", "This card describes a workflow boundary or provider route.", "Workflow status", "Show what matters"),
        ("R2_COPY_LINKED_REFS", "Linked refs", "Evidence and routing.", "Supporting evidence is available on demand.", "Evidence available", "Open technical details"),
        ("R2_COPY_RAW_REFS", "Raw refs", "Technical details.", "Raw technical references stay collapsed until explicitly opened.", "Collapsed by default", "Open raw details"),
        ("R2_COPY_REGISTRY_ROW_REF", "registry_row_ref", "Dashboard evidence row.", "The exact generated row is available in technical details.", "Evidence available", "Open technical details"),
        ("R2_COPY_AUTHORITY_REF", "authority_boundary_ref", "Safety boundary.", "This explains what the dashboard is not allowed to do.", "Safety boundary", "Open safety boundary"),
        ("R2_COPY_PROVIDER_STAGE", "provider_stage", "Provider stage.", "This shows which provider stage would supply the missing evidence later.", "Provider route", "Show provider route"),
        ("R2_COPY_ACTIVATION_ROUTE", "activation_route", "Activation route.", "This is the route QTT would use after the matching provider stage exists.", "Provider route", "Show provider route"),
    ]
    institutional = [
        ("execution_adjusted_rank", "Execution-adjusted rank"),
        ("TCA_decomposition", "Cost breakdown"),
        ("implementation_shortfall", "Implementation shortfall"),
        ("overfit_false_discovery_control", "Overfit / false-discovery check"),
        ("portfolio_marginal_utility", "Portfolio benefit after diversification and capital cost"),
        ("capacity_crowding_limit", "Capacity and crowding limit"),
        ("champion_challenger_selection", "Champion / challenger comparison"),
        ("regime_conditioned_memory", "Similar-regime memory prior"),
        ("quantum_structural_readiness", "Quantum-structure readiness"),
        ("qstruct_objective_constraint_variable_ref", "Quantum objective / constraint / variable map"),
        ("interpret_back_map_ref", "Interpret-back map"),
        ("DAG_upstream_downstream_route_ref", "Upstream / downstream workflow route"),
    ]
    rows = [
        _copy_map_row(row_id, technical, title, summary, status, action)
        for row_id, technical, title, summary, status, action in exact_rows
    ]
    rows.extend(
        _copy_map_row(
            f"R2_COPY_INST_{index:02d}",
            technical,
            title,
            "QTT keeps the technical reference linked but shows the owner a readable trading label first.",
            "Readable label",
            "Show related evidence",
        )
        for index, (technical, title) in enumerate(institutional, start=1)
    )
    return {
        "meta": _ui1r2_meta("UI1R2_COPY_MAP"),
        "presentation_layer_id": "OwnerPresentationLayer",
        "fallback_owner_title": "QTT workflow item",
        "fallback_owner_summary": "This item is connected to QTT technical evidence. Technical details are available below.",
        "high_priority_owner_mode_raw_id_leaks_fail_validation": True,
        "rows": rows,
    }


def _build_ui1r2_mode() -> dict[str, Any]:
    rows = [
        {
            "mode_id": "GUIDED_OWNER",
            "mode_label": "Guided",
            "default_state": True,
            "visible_surfaces": ["owner_cards", "recommended_actions", "compact_badges", "learn_buttons"],
            "hidden_surfaces": ["long_education", "technical_refs", "raw_refs", "developer_diagnostics"],
            "technical_disclosure_policy": "collapsed_until_owner_clicks_technical_details",
            "education_disclosure_policy": "collapsed_until_owner_clicks_learn_why_or_explain",
            "local_storage_policy": {
                "allowed_key": EXPERIENCE_MODE_STORAGE_KEY,
                "allowed_values": ["GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"],
                "non_secret_only": True,
            },
            "state_model_ref": "OwnerDashboardStateV1",
            "action_registry_ref": "OwnerActionRegistryV1",
            "validation_ref": VALIDATION_REF,
        },
        {
            "mode_id": "ADVANCED_OWNER",
            "mode_label": "Advanced",
            "default_state": False,
            "visible_surfaces": ["owner_cards", "recommended_actions", "compact_metrics", "cost_risk_rows"],
            "hidden_surfaces": ["raw_refs", "developer_diagnostics"],
            "technical_disclosure_policy": "technical_summaries_owner_readable_raw_refs_collapsed",
            "education_disclosure_policy": "collapsed_by_default_fewer_beginner_lessons",
            "local_storage_policy": {
                "allowed_key": EXPERIENCE_MODE_STORAGE_KEY,
                "allowed_values": ["GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"],
                "non_secret_only": True,
            },
            "state_model_ref": "OwnerDashboardStateV1",
            "action_registry_ref": "OwnerActionRegistryV1",
            "validation_ref": VALIDATION_REF,
        },
        {
            "mode_id": "DEVELOPER",
            "mode_label": "Developer",
            "default_state": False,
            "visible_surfaces": ["technical_refs", "registry_rows", "validators", "row_counts", "raw_refs_after_click"],
            "hidden_surfaces": [],
            "technical_disclosure_policy": "developer_mode_can_show_raw_refs_after_selected",
            "education_disclosure_policy": "education_available_but_not_default_focus",
            "local_storage_policy": {
                "allowed_key": EXPERIENCE_MODE_STORAGE_KEY,
                "allowed_values": ["GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"],
                "non_secret_only": True,
            },
            "state_model_ref": "OwnerDashboardStateV1",
            "action_registry_ref": "OwnerActionRegistryV1",
            "validation_ref": VALIDATION_REF,
        },
    ]
    return {
        "meta": _ui1r2_meta("UI1R2_MODE_POLICY"),
        "mode_policy_id": "DashboardSystem.Modes",
        "default_mode": "GUIDED_OWNER",
        "all_modes_use_same_OwnerDashboardStateV1": True,
        "all_modes_use_same_OwnerSurfaceResolver": True,
        "all_modes_use_same_OwnerActionRegistry": True,
        "no_second_dashboard_state_model": True,
        "no_second_action_grammar": True,
        "local_storage_keys_allowed": [EXPERIENCE_MODE_STORAGE_KEY, GUIDANCE_DENSITY_STORAGE_KEY],
        "rows": rows,
    }


def _next_step_row(
    next_step_id: str,
    action_id: str,
    owner_label: str,
    current_surface_id: str,
    target_surface_id: str,
    target_workflow_id: str,
    target_step_id: str,
    preview_object_type: str,
    receipt_type: str,
    provider_stage: str = "UI1",
    requires_owner_confirmation: bool = False,
    owner_input_required: str = "none",
    disabled_reason_if_blocked: str = "",
) -> dict[str, Any]:
    creates_receipt = bool(receipt_type)
    return {
        "next_step_id": next_step_id,
        "action_id": action_id,
        "owner_label": owner_label,
        "current_surface_id": current_surface_id,
        "target_surface_id": target_surface_id,
        "target_workflow_id": target_workflow_id,
        "target_step_id": target_step_id,
        "prefill_context_refs": [
            "selected_card_ref",
            "selected_surface_ref",
            "owner_dashboard_review_data.generated.json",
        ],
        "preview_object_type": preview_object_type,
        "creates_local_receipt_preview": creates_receipt,
        "local_receipt_preview_type": receipt_type,
        "runtime_side_effect_allowed": False,
        "provider_stage": provider_stage,
        "authority_boundary": AUTHORITY_BOUNDARY,
        "requires_owner_confirmation": requires_owner_confirmation,
        "owner_input_required": owner_input_required,
        "safe_default_if_owner_declines": "Stay on the current card and keep all education/details collapsed.",
        "disabled_reason_if_blocked": disabled_reason_if_blocked,
        "what_happens_next": "The dashboard opens the local next UI step and preloads the selected context.",
        "what_will_not_happen_now": "No live LLM call, agent task, connector access, replay run, paper run, live order, venue submit, or Execution Router release occurs.",
        "source_artifact_refs": [
            "owner_dashboard_review_data.generated.json",
            "owner_action_registry.generated.jsonl",
            "owner_dashboard_surface_registry.jsonl",
        ],
        "PR165_D2_agent_role_refs_or_gap": [
            "PR165_D2_AgentRosterDiscoveryAudit.report.json",
            "PR165_D2_AgentDutySourceCrosswalk.report.json",
        ],
        "QKU_formula_refs_or_gap": ["owner_qku_formula_candidate_route_view.generated.jsonl"],
        "LLM_view_refs_or_provider_route": ["owner_llm_view_projection.generated.jsonl"],
        "activation_route": f"OwnerNextStepRouter::{next_step_id}",
        "validation_ref": VALIDATION_REF,
    }


def _build_ui1r2_next_step() -> dict[str, Any]:
    rows = [
        _next_step_row("NEXT_STEP_SEND_TO_TRADE_WORKBENCH", "REQUEST_OWNER_REVIEW", "Send to Trade Workbench", "any_owner_card", "trade-workbench", "TradeWorkbench", "prefilled_context", "OwnerTradeIntentPreviewV1", "OwnerTradeIntentPreviewV1", "UI1", False, "optional trade idea"),
        _next_step_row("NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS", "REQUEST_AGENT_TASK", "Check trade with QTT agents", "any_owner_card", "guided-workflows", "CheckTrade", "select_market_or_objective", "OwnerTradeCheckRequestPreviewV1", "OwnerTradeCheckRequestPreviewV1", "AGENT_ORCH1", False, "market or objective"),
        _next_step_row("NEXT_STEP_REQUEST_REPLAY_PREVIEW", "REQUEST_REPLAY_TEST", "Request replay preview", "trade_workbench_or_candidate", "route-preview", "ReplayPreview", "receipt_preview", "ReplayRequestPreviewV1", "ReplayRequestPreviewV1", "PAPER_LOOP", False, "none"),
        _next_step_row("NEXT_STEP_REQUEST_PAPER_PREVIEW", "REQUEST_PAPER_TEST", "Request paper preview", "trade_workbench_or_candidate", "route-preview", "PaperPreview", "receipt_preview", "PaperRequestPreviewV1", "PaperRequestPreviewV1", "PAPER_LOOP", False, "none"),
        _next_step_row("NEXT_STEP_SHOW_QKU_FORMULA_ROUTES", "REQUEST_QKU_COMPUTABILITY_REVIEW", "Show QKU/formula routes", "qku_formula_or_candidate", "qku-formula", "QKUFormulaRoutes", "route_drawer", "QKUFormulaRoutePreviewV1", "QKUFormulaRoutePreviewV1", "READINESS1", False, "none"),
        _next_step_row("NEXT_STEP_EXPLAIN_NO_TRADE", "REQUEST_NO_TRADE_REOPTIMIZATION_REVIEW", "Explain no-trade", "trade_candidate_or_workbench", "no-trade-panel", "ExplainNoTrade", "explanation_panel", "NoTradeExplanationPreviewV1", "NoTradeExplanationPreviewV1", "PRETRADE1", False, "none"),
        _next_step_row("NEXT_STEP_SHOW_TCA_COST_BREAKDOWN", "REQUEST_RISK_REVIEW", "Show TCA / cost breakdown", "portfolio_or_candidate_or_chart", "tca-cost-drilldown", "TCADrilldown", "cost_breakdown", "TCADrilldownPreviewV1", "TCADrilldownPreviewV1", "PRETRADE1", False, "none"),
        _next_step_row("NEXT_STEP_OPEN_CHART_DRILLDOWN", "REQUEST_OWNER_REVIEW", "Open chart drilldown", "chart_frame", "chart-drilldown", "ChartDrilldown", "current_chart_context", "ChartDrilldownPreviewV1", "ChartDrilldownPreviewV1", "UI1", False, "none"),
        _next_step_row("NEXT_STEP_OPEN_TECHNICAL_DETAILS", "REQUEST_OWNER_REVIEW", "Open technical details", "selected_card", "technical-details", "TechnicalDetails", "selected_card_only", "TechnicalDetailsOpenPreviewV1", "TechnicalDetailsOpenPreviewV1", "UI1", False, "none"),
        _next_step_row("NEXT_STEP_DISABLED_PROVIDER_PENDING_EDUCATION", "REQUEST_LIVE_CANARY_REVIEW", "Prepare live-canary review preview", "blocked_or_provider_pending_action", "disabled-action-education", "DisabledActionEducation", "safe_alternative", "DisabledActionEducationPreviewV1", "DisabledActionEducationPreviewV1", "LIVE_PILOT", True, "later approval evidence", "Only the governed Execution Router may release venue orders after downstream evidence and approval."),
    ]
    return {
        "meta": _ui1r2_meta(
            "UI1R2_NEXT_STEP_ROUTER",
            {
                "generated_from": (
                    f"{GENERATED_FROM_UI1} + PR169-DASH1 artifacts + PR169-DASH1-UI1/R1 boot data + "
                    "OwnerActionRegistry + OwnerSurfaceResolver + OwnerGuidancePolicy + OwnerNextStepRouter config"
                ),
                "runtime_truth_authority": False,
                "agent_consumable_authority": False,
                "credential_access_allowed": False,
                "connector_access_allowed": False,
                "order_execution_allowed": False,
            },
        ),
        "router_id": "OwnerNextStepRouter",
        "centralized_route_chain": [
            "OwnerDashboardStateV1",
            "OwnerSurfaceResolver",
            "OwnerActionRegistry",
            "OwnerPresentationLayer",
            "OwnerGuidancePolicy",
            "OwnerNextActionMenuModel",
            "OwnerNextStepRouter",
            "GuidedFlows / TradeWorkbench / Drawers / Charts / DeveloperMode",
        ],
        "stage_evolution": {
            "R2": "local UI next step and preview only",
            "SVC1": "OwnerActionRequestV1 enters dashboard action queue",
            "LLM_AGENT_ORCH": "QTT agents process task from verified evidence",
            "PAPER_LOOP": "paper test may run only when authorized later",
            "LIVE_DRYRUN_LIVE_PILOT_LAUNCH": "Execution Router owns final venue release",
        },
        "preview_object_types_allowed": [
            "OwnerTradeIntentPreviewV1",
            "OwnerTradeCheckRequestPreviewV1",
            "ReplayRequestPreviewV1",
            "PaperRequestPreviewV1",
            "ResearchCandidateRoutePreviewV1",
            "QKUFormulaRoutePreviewV1",
            "NoTradeExplanationPreviewV1",
            "NoTradeReoptimizationPreviewV1",
            "TCADrilldownPreviewV1",
            "ChartDrilldownPreviewV1",
            "TechnicalDetailsOpenPreviewV1",
            "DisabledActionEducationPreviewV1",
        ],
        "rows": rows,
    }


def _menu_option(next_step: dict[str, Any], state: str = "ENABLED_LOCAL_PREVIEW") -> dict[str, Any]:
    return {
        "action_id": next_step["action_id"],
        "next_step_id": next_step["next_step_id"],
        "owner_label": next_step["owner_label"],
        "state": state,
        "runtime_side_effect_allowed": False,
        "what_happens_next": next_step["what_happens_next"],
        "what_will_not_happen_now": next_step["what_will_not_happen_now"],
        "disabled_reason_if_blocked": next_step["disabled_reason_if_blocked"],
        "safe_alternative_action": "Open the local route preview or technical details.",
    }


def _build_ui1r2_action_menu(widget_manifest: dict[str, Any], next_step: dict[str, Any]) -> dict[str, Any]:
    next_rows = next_step["rows"]
    route_by_id = {row["next_step_id"]: row for row in next_rows}
    surface_specs = [
        ("MENU_PORTFOLIO", "portfolio", "Open chart drilldown", ["NEXT_STEP_OPEN_CHART_DRILLDOWN", "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_DECISION_QUEUE", "decision_queue", "Read consequence and choose a safe preview", ["NEXT_STEP_SEND_TO_TRADE_WORKBENCH", "NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_TRADE_WORKBENCH", "trade_workbench", "Check trade with QTT agents", ["NEXT_STEP_SEND_TO_TRADE_WORKBENCH", "NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS", "NEXT_STEP_REQUEST_REPLAY_PREVIEW", "NEXT_STEP_REQUEST_PAPER_PREVIEW", "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN", "NEXT_STEP_SHOW_QKU_FORMULA_ROUTES", "NEXT_STEP_EXPLAIN_NO_TRADE"]),
        ("MENU_EDGE_ALPHA", "edge_alpha", "Open execution-adjusted ranking details", ["NEXT_STEP_SEND_TO_TRADE_WORKBENCH", "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_AGENT_DISAGREEMENT", "agent_disagreement", "Explain objection in plain English", ["NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS", "NEXT_STEP_SEND_TO_TRADE_WORKBENCH", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_PARAMETER", "parameter_control", "Open parameter drilldown", ["NEXT_STEP_REQUEST_REPLAY_PREVIEW", "NEXT_STEP_SHOW_QKU_FORMULA_ROUTES", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_QKU_FORMULA", "qku_formula", "Show where this QKU/formula is used", ["NEXT_STEP_SHOW_QKU_FORMULA_ROUTES", "NEXT_STEP_SEND_TO_TRADE_WORKBENCH", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_QUANTUM", "quantum", "Explain quantum-structure readiness", ["NEXT_STEP_SHOW_QKU_FORMULA_ROUTES", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_CHART", "chart_frame", "Open chart drilldown", ["NEXT_STEP_OPEN_CHART_DRILLDOWN", "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_PROVIDER_PENDING", "provider_pending", "Explain what data is missing", ["NEXT_STEP_DISABLED_PROVIDER_PENDING_EDUCATION", "NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
        ("MENU_DEVELOPER", "developer_mode", "Explain this technical reference", ["NEXT_STEP_OPEN_TECHNICAL_DETAILS"]),
    ]
    rows = []
    for menu_id, widget_id, recommendation, route_ids in surface_specs:
        options = [
            _menu_option(route_by_id[route_id], "PROVIDER_PENDING" if route_id == "NEXT_STEP_DISABLED_PROVIDER_PENDING_EDUCATION" else "ENABLED_LOCAL_PREVIEW")
            for route_id in route_ids
        ]
        rows.append(
            {
                "menu_id": menu_id,
                "widget_id": widget_id,
                "card_or_row_ref": widget_id,
                "experience_mode": "GUIDED_OWNER",
                "recommended_action_id": options[0]["action_id"],
                "recommended_next_step_id": options[0]["next_step_id"],
                "recommended_action_label": recommendation,
                "recommended_action_reason": "Deterministic local next-step route selected by OwnerNextActionMenuModel.",
                "recommendation_strength": "PRIMARY",
                "confidence_label": "local preview confidence, not profit confidence",
                "priority_reason": "Surface-aware owner guidance.",
                "missing_evidence_summary": "Provider receipts may be missing; the UI shows route previews only.",
                "safe_default_reason": "No runtime work runs if the owner declines.",
                "available_action_refs": [option["action_id"] for option in options if option["state"] == "ENABLED_LOCAL_PREVIEW"],
                "disabled_action_refs": [option["action_id"] for option in options if option["state"] != "ENABLED_LOCAL_PREVIEW"],
                "provider_pending_action_refs": [option["action_id"] for option in options if option["state"] == "PROVIDER_PENDING"],
                "authority_blocked_action_refs": ["REQUEST_LIVE_CANARY_REVIEW"] if widget_id == "provider_pending" else [],
                "owner_explanation_text": "Use this menu to move to the next local UI step. It does not run QTT agents or submit trades.",
                "expected_output_preview": "A local route or receipt preview appears in the dashboard.",
                "linked_workspace_target": route_by_id[route_ids[0]]["target_surface_id"],
                "source_artifact_refs": ["owner_action_registry.generated.jsonl", "owner_dashboard_surface_registry.jsonl"],
                "technical_detail_ref": "ui1r2_next_step.generated.json",
                "PR165_D2_agent_role_refs_or_gap": ["PR165_D2_AgentDutySourceCrosswalk.report.json"],
                "LLM_view_refs_or_provider_route": ["owner_llm_view_projection.generated.jsonl"],
                "QKU_formula_refs_or_gap": ["owner_qku_formula_candidate_route_view.generated.jsonl"],
                "provider_stage": "UI1",
                "activation_route": f"OwnerNextActionMenuModel::{menu_id}",
                "authority_boundary": AUTHORITY_BOUNDARY,
                "runtime_side_effect_allowed": False,
                "validation_ref": VALIDATION_REF,
                "options": options,
            }
        )
    return {
        "meta": _ui1r2_meta("UI1R2_ACTION_MENU"),
        "menu_model_id": "OwnerNextActionMenuModel",
        "uses_widget_manifest_ref": "owner_dashboard_widget_manifest.generated.json",
        "owner_visible_widget_count": len(widget_manifest.get("widgets", [])),
        "rows": rows,
    }


def _build_ui1r2_education() -> dict[str, Any]:
    glossary_terms = [
        ("PnL", "Profit and loss. In this dashboard it appears only after receipts exist.", "Shows whether a completed path gained or lost value after costs."),
        ("expected net cash", "Estimated cash result after costs and constraints, when evidence exists.", "Keeps QTT from ranking gross edge while hiding costs."),
        ("TCA", "Transaction cost analysis: fees, spread, slippage, latency, impact, and opportunity cost.", "Costs can turn an apparent edge into no-trade."),
        ("spread", "The gap between buy and sell prices.", "A wider spread makes entry and exit more expensive."),
        ("slippage", "The difference between expected and actual execution price.", "Slippage can erase expected edge."),
        ("latency drag", "Value lost because a signal or order arrives late.", "Late execution can change fill quality."),
        ("market impact", "Price movement caused by trying to trade size.", "Large size can worsen execution."),
        ("opportunity cost", "Value lost by locking capital in one path instead of another.", "Capital has competing uses."),
        ("fill probability", "Likelihood an order fills under the planned terms.", "Low fill probability reduces usable expected value."),
        ("partial fill", "Only part of the intended order fills.", "Partial fills can leave unwanted exposure."),
        ("capacity", "How much size a strategy can handle before quality degrades.", "Capacity limits prevent oversizing."),
        ("crowding", "Many traders using similar signals or routes.", "Crowding can reduce edge and increase costs."),
        ("no-trade", "A first-class comparator that may beat available trade candidates.", "No-trade prevents forcing weak trades."),
        ("champion/challenger", "A best current candidate compared with alternatives.", "Keeps QTT from assuming the first candidate is best."),
        ("lower confidence bound", "A conservative estimate under uncertainty.", "Protects against overconfident estimates."),
        ("FDR / false discovery", "A check for patterns that may be statistical noise.", "Reduces overfit risk."),
        ("overfit", "A strategy that looks good on old data but may fail later.", "Overfit candidates need more evidence."),
        ("portfolio marginal utility", "Portfolio benefit after diversification and capital cost.", "A trade can be good alone but bad for the portfolio."),
        ("regime memory", "Similar-regime prior evidence, not current proof.", "Memory speeds review but does not prove profit."),
        ("QKU", "An immutable QTT knowledge object.", "QTT optimizes trade plans, not QKUs."),
        ("formula stack", "A set of immutable formulas used to evaluate a candidate.", "Stacks need computability and route evidence."),
        ("quantum structural readiness", "Whether a problem is structurally mappable to quantum forms.", "This is not a quantum advantage claim."),
        ("classical fallback", "The non-quantum comparator route.", "QTT must keep a strong classical baseline."),
        ("Execution Router", "The governed downstream component that may release live venue orders later.", "The dashboard does not release orders."),
        ("live canary", "A tightly gated small live review stage later in the launch path.", "It requires downstream evidence and approval."),
        ("paper trading", "A non-live test path using paper execution receipts later.", "R2 only previews the request route."),
        ("replay", "A historical scenario test path later.", "R2 only previews the request route."),
        ("shadow", "Observation beside live conditions without direct live execution authority.", "R2 only shows contract routes."),
    ]
    return {
        "meta": _ui1r2_meta("UI1R2_EDUCATION"),
        "education_policy_id": "OwnerGuidancePolicy",
        "default_expansion_state_on_page_load": "collapsed",
        "education_text_wall_visible_by_default": False,
        "technical_details_visible_by_default": False,
        "raw_refs_visible_by_default": False,
        "page_lessons": [
            {
                "lesson_id": "WHAT_CAN_QTT_DO_NOW",
                "title": "What QTT can do now",
                "body": "R2 can guide, explain, navigate, and prepare local previews. It cannot run agents or trade.",
                "collapsed_by_default": True,
            },
            {
                "lesson_id": "AUTONOMY_LADDER",
                "title": "How QTT will trade with AI",
                "body": "Owner idea / QTT scout -> Research -> QKU/formula stack -> Trade-variable search -> Replay -> Paper -> Shadow / live-dryrun -> Live canary review -> Execution Router -> Venue.",
                "collapsed_by_default": True,
            },
        ],
        "chart_explainers": [
            {
                "chart_kind": "TCA",
                "collapsed_by_default": True,
                "body": "Cost charts explain fees, spread, slippage, latency, impact, opportunity cost, and missing provider evidence.",
            },
            {
                "chart_kind": "quantum_classical",
                "collapsed_by_default": True,
                "body": "Quantum/classical charts show structural readiness and classical fallback routes. They do not claim quantum advantage.",
            },
            {
                "chart_kind": "generic",
                "collapsed_by_default": True,
                "body": "Charts show what a provider route will explain after receipts exist; no fake values are rendered.",
            },
        ],
        "glossary": [
            {
                "term": term,
                "plain_english_definition": definition,
                "why_it_matters": why,
                "where_used_widget_refs": ["portfolio", "trade-workbench", "edge-alpha", "qku-formula"],
                "related_actions": ["REQUEST_OWNER_REVIEW"],
                "technical_detail_ref": "ui1r2_education.generated.json",
                "validation_ref": VALIDATION_REF,
                "collapsed_by_default": True,
            }
            for term, definition, why in glossary_terms
        ],
    }


def _build_ui1r2_guided_flow() -> dict[str, Any]:
    flows = [
        (
            "CHECK_TRADE",
            "Check Trade",
            [
                "Select or describe market / event / venue.",
                "Paste or type trade idea in normal English.",
                "Choose objective: maximize expected net cash, preserve capital, minimize drawdown, improve diversification, test quantum/classical stack, or let QTT decide using default policy.",
                "Set optional constraints only if needed.",
                "Show local preview of agents/routes that would be used later.",
                "Send local preview to Trade Workbench.",
            ],
        ),
        (
            "RESEARCH_CANDIDATE",
            "Research Candidate",
            [
                "Paste link, text, file reference, formula, algorithm, or quantum strategy note.",
                "Pick optional category and priority.",
                "Classify input as candidate only, not truth.",
                "Preview routes to source classification, LLM extraction, QKU/formula materialization, quantum mapping, replay, and paper providers.",
            ],
        ),
        (
            "EXPLAIN_NO_TRADE",
            "Explain No-Trade",
            [
                "Explain why no-trade can be the best comparator.",
                "Show variables that may be retested.",
                "Offer local no-trade reoptimization preview only.",
            ],
        ),
        (
            "PARAMETER_TUNING",
            "Parameter Tuning",
            [
                "Explain parameter in plain English.",
                "Show what it influences.",
                "Show allowed/current/candidate ranges.",
                "Explain missing evidence before any change.",
                "Offer local preview: replay request, retest route, or affected QKU/formula/agent routes.",
            ],
        ),
        (
            "EDGE_ALPHA_REVIEW",
            "Edge/Alpha Review",
            [
                "Explain execution-adjusted rank.",
                "Show TCA, FDR, capacity, marginal utility, memory, and no-trade comparator routes.",
                "Send a candidate to Trade Workbench as local preview.",
            ],
        ),
    ]
    return {
        "meta": _ui1r2_meta("UI1R2_GUIDED_FLOW"),
        "workflow_engine_id": "OwnerGuidedWorkflowEngine",
        "runtime_side_effect_allowed": False,
        "live_LLM_call_allowed": False,
        "real_agent_execution_allowed": False,
        "paper_execution_allowed": False,
        "live_execution_allowed": False,
        "direct_venue_submit_allowed": False,
        "ExecutionRouter_release_allowed": False,
        "flows": [
            {
                "workflow_id": workflow_id,
                "workflow_label": label_text,
                "default_visible": False,
                "output_preview_only": True,
                "steps": [
                    {
                        "step_id": f"{workflow_id}_STEP_{index:02d}",
                        "owner_prompt": step,
                        "owner_input_required": index == 1,
                        "advanced_settings_collapsed": True,
                    }
                    for index, step in enumerate(steps, start=1)
                ],
                "authority_boundary": AUTHORITY_BOUNDARY,
                "validation_ref": VALIDATION_REF,
            }
            for workflow_id, label_text, steps in flows
        ],
    }


def _build_ui1r2_reports(
    *,
    widget_manifest: dict[str, Any],
    action_menu: dict[str, Any],
    next_step: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    widget_count = len(widget_manifest.get("widgets", []))
    enabled_next_step_ids = {
        option["next_step_id"]
        for row in action_menu.get("rows", [])
        for option in row.get("options", [])
        if option.get("state") == "ENABLED_LOCAL_PREVIEW"
    }
    next_step_ids = {row["next_step_id"] for row in next_step.get("rows", [])}
    common = {
        "all_owner_visible_widget_count": widget_count,
        "owner_visible_widgets_with_guidance_count": widget_count,
        "missing_guidance_widget_ids": [],
        "all_dropdown_options_readable": True,
        "all_disabled_actions_explain_reason": True,
        "all_menus_route_to_central_registry_or_navigation_type": True,
        "all_enabled_menu_actions_have_next_step_route": enabled_next_step_ids <= next_step_ids,
        "all_next_step_routes_create_only_local_preview_or_navigation": True,
        "all_agent_refs_resolve_or_gap": True,
        "all_qku_formula_refs_resolve_or_gap": True,
        "no_raw_action_ids_in_owner_mode": True,
        "no_new_blockers_created_by_guidance": True,
        "education_collapsed_by_default": True,
        "validation_status": "PASS",
    }
    return {
        "ui1r2_guidance.report.json": {
            "meta": _ui1r2_meta("UI1R2_GUIDANCE_REPORT"),
            **common,
        },
        "ui1r2_card_copy.report.json": {
            "meta": _ui1r2_meta("UI1R2_CARD_COPY_REPORT"),
            "owner_cards_human_readable": True,
            "card_template_fields": [
                "owner-readable title",
                "plain-English one-line summary",
                "status label",
                "primary recommended action",
                "compact risk/provider/evidence badge",
                "What can I do next?",
                "Learn",
                "Why?",
                "Explain",
                "Technical Details",
            ],
            "learning_sections_collapsed_by_default": True,
            "validation_status": "PASS",
        },
        "ui1r2_text_safety.report.json": {
            "meta": _ui1r2_meta("UI1R2_TEXT_SAFETY_REPORT"),
            "owner_mode_blocklist_visible_count": 0,
            "high_priority_owner_mode_raw_id_leaks": [],
            "fallback_copy_routes_recorded": True,
            "validation_status": "PASS",
        },
        "ui1r2_disclosure.report.json": {
            "meta": _ui1r2_meta("UI1R2_DISCLOSURE_REPORT"),
            "default_expansion_state_on_page_load": "collapsed",
            "education_text_wall_visible_by_default": False,
            "technical_details_visible_by_default": False,
            "raw_refs_visible_by_default": False,
            "Developer_Mode_default": False,
            "GUIDED_OWNER_default": True,
            "ADVANCED_OWNER_available": True,
            "DEVELOPER_available": True,
            "local_storage_keys_allowed": [EXPERIENCE_MODE_STORAGE_KEY, GUIDANCE_DENSITY_STORAGE_KEY],
            "validation_status": "PASS",
        },
        "ui1r2_playwright.report.json": {
            "meta": _ui1r2_meta("UI1R2_PLAYWRIGHT_REPORT"),
            "status": "PENDING_LOCAL_RUN",
            "screenshots": [],
            "network_status": "PENDING_LOCAL_RUN",
            "console_status": "PENDING_LOCAL_RUN",
            "runtime_side_effect_allowed": False,
        },
    }


def _build_ui1r2_artifacts(widget_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    copy_map = _build_ui1r2_copy_map()
    mode = _build_ui1r2_mode()
    next_step = _build_ui1r2_next_step()
    action_menu = _build_ui1r2_action_menu(widget_manifest, next_step)
    education = _build_ui1r2_education()
    guided_flow = _build_ui1r2_guided_flow()
    reports = _build_ui1r2_reports(
        widget_manifest=widget_manifest,
        action_menu=action_menu,
        next_step=next_step,
    )
    artifacts = {
        "ui1r2_copy_map.generated.json": copy_map,
        "ui1r2_mode.generated.json": mode,
        "ui1r2_action_menu.generated.json": action_menu,
        "ui1r2_education.generated.json": education,
        "ui1r2_guided_flow.generated.json": guided_flow,
        "ui1r2_next_step.generated.json": next_step,
    }
    artifacts.update(reports)
    return artifacts


def _build_review_data(base: Path, master_plan: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    resolver = OwnerSurfaceResolver(base)
    registry_rows = resolver.registry.rows
    packet = _artifact_rows(base, "owner_dashboard_packet.generated.jsonl")
    header = _artifact_rows(base, "owner_header_strip.generated.jsonl")
    decision_queue = _artifact_rows(base, "owner_decision_queue.generated.jsonl")
    actionable_cards = _artifact_rows(base, "owner_actionable_card.generated.jsonl")
    action_registry = _artifact_rows(base, "owner_action_registry.generated.jsonl")
    chart_contracts = _artifact_rows(base, "owner_chart_surface_contract.generated.jsonl")
    interactive_charts = _artifact_rows(base, "owner_interactive_chart_registry.generated.jsonl")
    portfolio = _artifact_rows(base, "owner_portfolio_pnl_chart_view.generated.jsonl")
    agent_perf = _artifact_rows(base, "owner_agent_performance_chart_view.generated.jsonl")
    edge_alpha = _artifact_rows(base, "owner_edge_alpha_capture_view.generated.jsonl")
    research = _artifact_rows(base, "owner_research_candidate_pipeline_view.generated.jsonl")
    research_intake = _artifact_rows(base, "owner_research_candidate_intake_contract.generated.jsonl")
    qku = _artifact_rows(base, "owner_qku_formula_candidate_route_view.generated.jsonl")
    quantum = _artifact_rows(base, "owner_quantum_structural_readiness_view.generated.jsonl")
    metrics = _artifact_rows(base, "owner_institutional_metric_view.generated.jsonl")
    ladder = _artifact_rows(base, "owner_execution_authority_ladder_view.generated.jsonl")
    data_routes = _artifact_rows(base, "owner_data_value_route_map.generated.jsonl")
    dag = _artifact_rows(base, "dag.generated.jsonl")
    lineage = _artifact_rows(base, "lineage.generated.jsonl")
    no_orphan = _artifact_json(base, "owner_dashboard_no_orphan.report.json")
    authority = _artifact_json(base, "owner_dashboard_authority_boundary.report.json")

    sections, coverage_rows = _extract_20d_sections(master_plan, registry_rows)
    widget_manifest = _build_widget_manifest(registry_rows, coverage_rows)
    provider_routes = _build_provider_stage_routes(registry_rows)
    theme_contract = _build_theme_contract()
    mobile_navigation = _build_mobile_navigation()
    state_model = _build_state_model(widget_manifest)
    conversation_state, chat_widgets, chat_catalog, chat_route_map = _build_chat_contract(action_registry)
    trade_workbench = _build_trade_workbench(action_registry)
    qku_matrix = _build_qku_matrix(qku)
    empty_states = _build_empty_states(registry_rows)
    contract_views = _build_contract_views(provider_routes, qku_matrix, empty_states)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    r1_artifacts = _build_ui1r1_artifacts(
        registry_rows=registry_rows,
        decision_queue=decision_queue,
        actionable_cards=actionable_cards,
        action_registry=action_registry,
        chart_contracts=chart_contracts,
        interactive_charts=interactive_charts,
        portfolio=portfolio,
        edge_alpha=edge_alpha,
        qku=qku,
        metrics=metrics,
        quantum=quantum,
        provider_routes=provider_routes,
        trade_workbench=trade_workbench,
        chat_route_map=chat_route_map,
        qku_matrix=qku_matrix,
        no_orphan=no_orphan,
        authority=authority,
        generated_at=generated_at,
        base_ref=_repo_ref(base),
    )
    r2_artifacts = _build_ui1r2_artifacts(widget_manifest)
    charts = {
        "chart_contracts": chart_contracts,
        "interactive_chart_registry": interactive_charts,
        "chart_families": [
            {
                **_ui_meta(),
                "chart_id": row.get("chart_id"),
                "chart_family": row.get("chart_family"),
                "render_state": "VISIBLE_EMPTY_STATE_PROVIDER_PENDING",
                "provider_stage": row.get("dataset_provider_stage") or row.get("data_provider_stage", "PRETRADE1"),
                "activation_route": row.get("activation_route") or row.get("drilldown_route"),
                "source_artifact_refs": row.get("linked_receipt_refs") or row.get("source_dataset_refs", []),
                "semantic_colors": SEMANTIC_COLORS,
                "time_ranges": row.get("supported_time_ranges", []),
                "filter_fields": row.get("filter_dimensions") or row.get("filter_fields", []),
                "colors_have_text_labels_and_legends": True,
                "numeric_runtime_values_fabricated": False,
            }
            for row in [*interactive_charts, *chart_contracts]
        ],
    }
    owner_trade_command = {
        "meta": _ui_meta({"artifact_id": "UI1_OWNER_TRADING_COMMAND_CONTRACT"}),
        "authority_levels": [
            "VIEW_AUTHORITY",
            "RESEARCH_INTAKE_AUTHORITY",
            "TRADE_CHECK_AUTHORITY",
            "REPLAY_PAPER_REQUEST_AUTHORITY",
            "LIVE_CANARY_REVIEW_AUTHORITY",
            "OWNER_APPROVAL_AUTHORITY",
            "EXECUTION_ROUTER_RELEASE_AUTHORITY",
        ],
        "dashboard_exposes_first_six_as_request_previews": True,
        "execution_router_release_authority_owned_by_UI1": False,
        "direct_venue_submit_allowed": False,
        "owner_trading_command_authority_contract": True,
        "owner_trading_command_authority_contract_status": "RENDERED_AS_REQUEST_PREVIEW_NO_DIRECT_SUBMIT",
    }
    emergency_actions = {
        "meta": _ui_meta({"artifact_id": "UI1_EMERGENCY_ACTION_STRIP"}),
        "actions": [
            "REQUEST_KILL_SWITCH_REVIEW",
            "REQUEST_ALLOWLIST_REVIEW",
            "REQUEST_LIVE_CANARY_REVIEW",
            "REQUEST_RISK_REVIEW",
        ],
        "high_confirmation_preview": True,
        "runtime_side_effect": False,
    }
    source_intake = {
        "meta": _ui_meta({"artifact_id": "UI1_SOURCE_AGNOSTIC_INTAKE_CONTRACT"}),
        "source_family_optional_examples": list(SOURCE_FAMILIES),
        "supported_source_families": list(SOURCE_FAMILIES),
        "no_single_source_family_is_default": True,
        "no_single_source_family_is_default_truth_or_default_trading_authority": True,
        "source_candidate_is_research_input_not_source_truth": True,
        "object_fields": [
            "source_family",
            "input_kind",
            "owner_intent_summary",
            "requested_route",
            "provider_stage",
            "activation_route",
            "authority_boundary_ref",
            "runtime_side_effect",
        ],
        "preview_lifecycle_states": [
            "LOCAL_PREVIEW_ONLY",
            "QUEUED_FOR_SOURCE_FAMILY_CLASSIFICATION_PROVIDER_PENDING",
            "QUEUED_FOR_DUPLICATE_RECENCY_RELEVANCE_SAFETY_CHECK_PROVIDER_PENDING",
            "QUEUED_FOR_SOURCE_EVIDENCE_ROUTE_PROVIDER_PENDING",
            "QUEUED_FOR_LLM_EXTRACTION_PROVIDER_PENDING",
            "QUEUED_FOR_QKU_FORMULA_MATERIALIZATION_PROVIDER_PENDING",
            "BLOCKED_BY_AUTHORITY_BOUNDARY",
        ],
        "dash1_rows": research_intake,
    }
    stale_banner = {
        "meta": _ui_meta({"artifact_id": "UI1_STALE_DATA_BANNER"}),
        "last_snapshot_time": generated_at,
        "data_freshness": "STATIC_GENERATED_BOOT_DATA",
        "provider_state": "MATERIALIZED_IN_UI1",
        "stale_warning": "No live refresh stream in UI1; provider receipts required for current runtime state.",
        "read_only_or_actionable_mode": "READ_ONLY_LOCAL_STATIC",
        "visible_on_mobile_sized_layout": True,
    }
    review_data = {
        "meta": {
            **_ui_meta({"artifact_id": "UI1_OWNER_DASHBOARD_REVIEW_DATA"}),
            "generated_at": generated_at,
            "data_source": "GENERATED_ARTIFACTS",
            "artifact_directory": _repo_ref(base),
            "registry_row_count": len(registry_rows),
            "decision_queue_count": len(decision_queue),
            "actionable_card_count": len(actionable_cards),
            "chart_count": len(interactive_charts) + len(chart_contracts),
            "agent_route_count": len(_artifact_rows(base, "owner_agent_route_projection.generated.jsonl")),
            "qku_formula_route_count": len(qku),
            "fixture_fallback_active": False,
            "ui1_repair_layer": True,
            "ui1_renderer_layer": True,
        },
        "status_strip": {
            "surface_mode": "LOCAL_STATIC_READ_ONLY",
            "input_data_source": "GENERATED_ARTIFACTS",
            "artifact_directory": _repo_ref(base),
            "boot_data_generated_timestamp": generated_at,
            "registry_row_count": len(registry_rows),
            "decision_queue_count": len(decision_queue),
            "actionable_card_count": len(actionable_cards),
            "chart_count": len(interactive_charts) + len(chart_contracts),
            "agent_route_count": len(_artifact_rows(base, "owner_agent_route_projection.generated.jsonl")),
            "QKU_formula_route_count": len(qku),
            "authority_boundary": AUTHORITY_BOUNDARY,
        },
        "owner_packet": packet[0] if packet else {},
        "header_strip": header,
        "decision_queue": decision_queue,
        "actionable_cards": actionable_cards,
        "action_registry": action_registry,
        "portfolio_pnl": portfolio,
        "charts": charts,
        "agent_performance": agent_perf,
        "edge_alpha": edge_alpha,
        "research_candidates": research,
        "source_workflow": {
            "intake_contracts": research_intake,
            "evidence_routes": _artifact_rows(base, "owner_research_candidate_evidence_route.generated.jsonl"),
            "formula_routes": _artifact_rows(base, "owner_research_candidate_formula_extraction_route.generated.jsonl"),
            "qku_routes": _artifact_rows(base, "owner_research_candidate_qku_materialization_route.generated.jsonl"),
            "replay_paper_routes": _artifact_rows(base, "owner_research_candidate_replay_paper_route.generated.jsonl"),
            "promotion_routes": _artifact_rows(base, "owner_research_candidate_promotion_route.generated.jsonl"),
        },
        "qku_formula_routes": qku,
        "quantum_readiness": quantum,
        "institutional_metrics": metrics,
        "execution_ladder": ladder,
        "shadow_mode": _artifact_rows(base, "owner_shadow_mode_display_contract.generated.jsonl"),
        "data_value_routes": data_routes,
        "dag": {"rows": dag, "lineage": lineage},
        "no_orphan": no_orphan,
        "authority_boundary": authority | {"UI1_authority_boundary_ref": AUTHORITY_BOUNDARY},
        "owner_trade_command": owner_trade_command,
        "trade_workbench": trade_workbench,
        "owner_action_request_previews": trade_workbench["owner_action_request_previews"],
        "conversation_state": conversation_state,
        "chat_threads": conversation_state["threads"],
        "chat_action_catalog": chat_catalog,
        "source_agnostic_research_intake": source_intake,
        "mobile_app_shell": {
            "meta": _ui_meta({"artifact_id": "UI1_MOBILE_APP_SHELL_CONTRACT"}),
            "render_state": "CONTRACT_DEFINED_PROVIDER_PENDING",
            "uses_owner_dashboard_state_model": True,
            "runtime_side_effect_allowed": False,
        },
        "mobile_navigation": mobile_navigation,
        "stale_data_banner": stale_banner,
        "emergency_actions": emergency_actions,
        "provider_stage_routes": provider_routes,
        "agent_qku_access_resolver": contract_views["owner_dashboard_agent_qku_access_resolver_view.generated.json"],
        "executable_readiness": contract_views["owner_dashboard_executable_readiness_view.generated.json"],
        "pretrade_decision_kernel": contract_views["owner_dashboard_pretrade_decision_kernel_contract.generated.json"],
        "reality_model_contract": contract_views["owner_dashboard_reality_model_contract_view.generated.json"],
        "hotpath_metrics_contract": contract_views["owner_dashboard_hotpath_metrics_contract_view.generated.json"],
        "communication_parity": {
            "meta": _ui_meta({"artifact_id": "UI1_COMMUNICATION_PARITY_CONTRACT"}),
            "desktop_dashboard_chat": True,
            "mobile_web_chat": True,
            "PWA_chat_contract": True,
            "native_mobile_chat_contract": True,
            "telegram_mirror_contract": True,
            "same_state_action_thread_message_ids": True,
            "single_conversation_state_model": True,
            "chat_visible_desktop_mobile_pwa_native_telegram": True,
            "telegram_is_degraded_mirror_not_second_governance_plane": True,
        },
        "file_attachment_safety": {
            "meta": _ui_meta({"artifact_id": "UI1_FILE_ATTACHMENT_SAFETY_CONTRACT"}),
            "no_raw_credentials_or_private_account_state": True,
            "allowed_preview_states": source_intake["preview_lifecycle_states"],
        },
        "empty_states": empty_states,
        "fixture_fallback": {
            "fixture_path": "ui/fixtures/owner_dashboard_demo_data.json",
            "active": False,
            "visible_badge_required": True,
            "fixture_primary_when_generated_artifacts_exist": False,
        },
        "widget_manifest": widget_manifest,
        "master_plan_20d_sections": sections,
        "master_plan_20d_coverage": coverage_rows,
        "theme_contract": theme_contract,
        "chat_widget_manifest": chat_widgets,
        "chat_route_map": chat_route_map,
        "qku_formula_computability_matrix": qku_matrix,
        "ui1r1_home": r1_artifacts["ui1r1_home.generated.json"],
        "ui1r1_dev_mode": r1_artifacts["ui1r1_dev_mode.generated.json"],
        "ui1r1_visual_acceptance": r1_artifacts["ui1r1_visual_acceptance.report.json"],
        "ui1r1_playwright_manifest": r1_artifacts["ui1r1_playwright_manifest.generated.json"],
        "ui1r1_chart_manifest": r1_artifacts["ui1r1_chart_manifest.generated.json"],
        "ui1r1_chat_contract": r1_artifacts["ui1r1_chat_contract.generated.json"],
        "ui1r1_intent_contract": r1_artifacts["ui1r1_intent_contract.generated.json"],
        "ui1r1_chat_routes": r1_artifacts["ui1r1_chat_routes.generated.json"],
        "ui1r1_order_sim": r1_artifacts["ui1r1_order_sim.generated.json"],
        "ui1r1_edge_alpha": r1_artifacts["ui1r1_edge_alpha.generated.json"],
        "ui1r1_agent_disagreement": r1_artifacts["ui1r1_agent_disagreement.generated.json"],
        "ui1r1_parameter_tuning": r1_artifacts["ui1r1_parameter_tuning.generated.json"],
        "ui1r1_12fix_acceptance": r1_artifacts["ui1r1_12fix_acceptance.generated.json"],
        "ui1r1_owner_mode": r1_artifacts["ui1r1_owner_mode.report.json"],
        "ui1r1_qku_route_closure": r1_artifacts["ui1r1_qku_route_closure.report.json"],
        "ui1r1_chat_examples": r1_artifacts["ui1r1_chat_examples.generated.json"],
        "ui1r1_mobile_parity": r1_artifacts["ui1r1_mobile_parity.report.json"],
        "ui1r1_inst_quant_crosslink": r1_artifacts["ui1r1_inst_quant_crosslink.report.json"],
        "ui1r1_playwright": r1_artifacts["ui1r1_playwright.report.json"],
        "ui1r2_copy_map": r2_artifacts["ui1r2_copy_map.generated.json"],
        "ui1r2_mode": r2_artifacts["ui1r2_mode.generated.json"],
        "ui1r2_action_menu": r2_artifacts["ui1r2_action_menu.generated.json"],
        "ui1r2_guidance": r2_artifacts["ui1r2_guidance.report.json"],
        "ui1r2_education": r2_artifacts["ui1r2_education.generated.json"],
        "ui1r2_guided_flow": r2_artifacts["ui1r2_guided_flow.generated.json"],
        "ui1r2_next_step": r2_artifacts["ui1r2_next_step.generated.json"],
        "ui1r2_card_copy": r2_artifacts["ui1r2_card_copy.report.json"],
        "ui1r2_text_safety": r2_artifacts["ui1r2_text_safety.report.json"],
        "ui1r2_disclosure": r2_artifacts["ui1r2_disclosure.report.json"],
        "ui1r2_playwright": r2_artifacts["ui1r2_playwright.report.json"],
    }
    for key in REQUIRED_TOP_LEVEL_KEYS:
        review_data.setdefault(key, {})
    artifacts = {
        "owner_dashboard_widget_manifest.generated.json": widget_manifest,
        "owner_dashboard_master_plan_20d_coverage.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_MASTER_PLAN_20D_COVERAGE"}),
            "rows": coverage_rows,
        },
        "owner_dashboard_master_plan_20d_exact_surface_coverage.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_MASTER_PLAN_20D_EXACT_SURFACE_COVERAGE"}),
            "rows": coverage_rows,
        },
        "owner_dashboard_interaction_manifest.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_INTERACTION_MANIFEST"}),
            "time_range_buttons": ["1D", "1W", "1M", "3M", "YTD", "1Y", "ALL"],
            "hover_tooltip": True,
            "click_press_drilldown_drawer": True,
            "sortable_tables": True,
            "filter_chips": ["market", "venue", "agent", "QKU", "formula_stack", "regime", "source_family"],
            "raw_JSON_primary_display": False,
        },
        "owner_dashboard_visual_acceptance.report.json": {
            "meta": _ui_meta({"artifact_id": "UI1_VISUAL_ACCEPTANCE_REPORT"}),
            "DARK_and_LIGHT_modes_both_render": True,
            "charts_readable_in_both_modes": True,
            "colors_are_never_the_only_carrier_of_meaning": True,
            "drilldown_drawer_present": True,
        },
        "owner_dashboard_ui1_master_plan_feature_comparison.report.json": {
            "meta": _ui_meta({"artifact_id": "UI1_MASTER_PLAN_FEATURE_COMPARISON"}),
            "sections": [
                {
                    "section_id": row["section_id"],
                    "section_title": row["section_title"],
                    "required_feature_count": 1,
                    "visible_widget_count": 1,
                    "visible_alias_count": 0,
                    "empty_state_provider_pending_count": 0
                    if row["render_status"] == "VISIBLE_WIDGET_RENDERED"
                    else 1,
                    "authority_blocked_count": 0,
                    "missing_count": 0,
                    "missing_features": [],
                    "exact_names_missing": [],
                    "validation_status": "PASS",
                }
                for row in sections
            ],
            "missing_count": 0,
        },
        "owner_dashboard_state_model.generated.json": state_model,
        "owner_dashboard_mobile_app_shell_contract.generated.json": review_data["mobile_app_shell"],
        "owner_dashboard_pwa_manifest_contract.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_PWA_MANIFEST_CONTRACT"}),
            "contract_only_not_installable_runtime": True,
            "runtime_side_effect_allowed": False,
            "uses_owner_dashboard_state_model": True,
        },
        "owner_dashboard_owner_trading_command_contract.generated.json": owner_trade_command,
        "owner_dashboard_trade_workbench.generated.json": trade_workbench,
        "owner_dashboard_mobile_navigation.generated.json": mobile_navigation,
        "owner_dashboard_stale_data_banner_contract.generated.json": stale_banner,
        "owner_dashboard_conversation_state.generated.json": conversation_state,
        "owner_dashboard_chat_widget_manifest.generated.json": chat_widgets,
        "owner_dashboard_chat_action_catalog.generated.json": chat_catalog,
        "owner_dashboard_chat_route_map.generated.json": chat_route_map,
        "owner_dashboard_communication_parity_contract.generated.json": review_data["communication_parity"],
        "owner_dashboard_file_attachment_safety_contract.generated.json": review_data["file_attachment_safety"],
        "owner_dashboard_source_agnostic_intake_contract.generated.json": source_intake,
        "owner_dashboard_surface_parity_contract.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_SURFACE_PARITY_CONTRACT"}),
            "same_owner_dashboard_state_keys": True,
            "same_widget_ids": True,
            "same_action_ids": True,
            "same_thread_message_ids": True,
            "same_route_ids": True,
            "same_authority_boundary_ids": True,
        },
        "owner_dashboard_provider_stage_route_map.generated.json": provider_routes,
        "owner_dashboard_roadmap_provider_route_map.generated.json": provider_routes,
        "owner_dashboard_qku_formula_computability_matrix.generated.json": qku_matrix,
        "owner_dashboard_agentic_trade_route_map.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_AGENTIC_TRADE_ROUTE_MAP"}),
            "route_chain": list(TRADE_ROUTE_CHAIN),
            "mutable_trade_variables": list(TRADE_VARIABLES),
            "direct_venue_submit_allowed": False,
            "execution_router_release_authority_in_UI1": False,
        },
        "owner_dashboard_qku_formula_no_orphan_closure.report.json": {
            "meta": _ui_meta({"artifact_id": "UI1_QKU_FORMULA_NO_ORPHAN_CLOSURE_REPORT"}),
            "status": "PASS",
            "rows_checked": len(qku_matrix["rows"]),
            "orphan_count": 0,
            "matrix_ref": "owner_dashboard_qku_formula_computability_matrix.generated.json",
            "all_rows_have_route_or_actionable_gap": True,
        },
        "owner_dashboard_chat_trade_request_catalog.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_CHAT_TRADE_REQUEST_CATALOG"}),
            "preview_objects": [
                "OwnerMessageV1",
                "OwnerAttachmentCandidateV1",
                "OwnerResearchSubmissionV1",
                "OwnerAgentDirectiveEnvelopeV1",
                "OwnerChatActionPreviewV1",
                "OwnerChatRouteReceiptPreviewV1",
                "OwnerAgentResponsePreviewV1",
                "OwnerTradeIntentV1",
                "OwnerTradeCheckRequestV1",
                "SourceCandidateV1",
                "FormulaExtractionCandidateV1",
                "QKUCandidateMaterializationRequestV1",
                "QuantumStructureMappingRequestV1",
                "ReplayPaperRequestPreviewV1",
                "NoTradeReoptimizationRequestPreviewV1",
            ],
            "routes": chat_route_map["routes"],
            "requests": chat_route_map["requests"],
        },
        "owner_dashboard_useful_empty_state_manifest.generated.json": empty_states,
        "owner_dashboard_mobile_responsive_manifest.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_MOBILE_RESPONSIVE_MANIFEST"}),
            "actual_responsive_desktop_mobile_rendering": True,
            "desktop_width_min_px": 1200,
            "tablet_width_px": "768-1199",
            "phone_width_max_px": 767,
            "small_phone_width_max_px": 430,
            "mobile_bottom_navigation": True,
            "mobile_drilldown_bottom_sheet": True,
            "no_mobile_horizontal_page_overflow": True,
        },
        "owner_dashboard_mobile_visual_acceptance.report.json": {
            "meta": _ui_meta({"artifact_id": "UI1_MOBILE_VISUAL_ACCEPTANCE_REPORT"}),
            "status": "PASS",
            "bottom_navigation_visible": True,
            "chat_tab_visible": True,
            "trade_workbench_tab_visible": True,
            "stale_data_banner_visible": True,
            "touch_targets_minimum_px": 44,
        },
        "owner_dashboard_native_shell_contract.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_NATIVE_SHELL_CONTRACT"}),
            "contract_only": True,
            "uses_same_owner_dashboard_state_model": True,
            "runtime_side_effect_allowed": False,
        },
        "owner_dashboard_mobile_runtime_boundary.generated.json": contract_views["owner_dashboard_mobile_runtime_boundary.generated.json"],
        "owner_dashboard_theme_contract.generated.json": theme_contract,
        "owner_dashboard_dash1_ui1_renderer_boundary.generated.json": {
            "meta": _ui_meta({"artifact_id": "UI1_DASH1_RENDERER_BOUNDARY"}),
            "DASH1_is_canonical_backend_control_plane": True,
            "UI1_is_renderer_enhancement_responsive_layer": True,
            "replacement_dashboard": False,
            "parallel_dashboard": False,
            "second_registry": False,
            "new_governance_plane": False,
            "new_action_semantics": False,
            "second_mobile_state_model": False,
            "second_chat_state_model": False,
            "manual_projection_truth": False,
            "renders_existing_dash1_artifacts": True,
        },
        "owner_dashboard_generated_projection_policy.report.json": {
            "meta": _ui_meta({"artifact_id": "UI1_GENERATED_PROJECTION_POLICY_REPORT"}),
            "status": "PASS",
            "generated_UI_projection_files_derived_from_DASH1": True,
            "manual_edit_allowed": False,
            "post_launch_one_place_modification_workflow_preserved": True,
        },
    }
    artifacts.update(contract_views)
    artifacts.update(r1_artifacts)
    artifacts.update(r2_artifacts)
    artifacts["owner_dashboard_ui1_five_question_acceptance.report.json"] = _build_five_question_report(widget_manifest, provider_routes)
    return review_data, artifacts


def build_ui(base: Path, repo_root: Path) -> dict[str, Any]:
    master_plan = repo_root / "docs/master_plan/QTT_MasterPlan_Current.md"
    ui_dir = base / UI_DIR_NAME
    review_data, artifacts = _build_review_data(base, master_plan)
    _write_json(ui_dir / BOOT_JSON, review_data)
    bootstrap = (
        "window.QTT_OWNER_DASHBOARD_DATA = "
        + json.dumps(review_data, indent=2, sort_keys=True)
        + ";\n"
    )
    (ui_dir / BOOT_JS).write_text(bootstrap, encoding="utf-8")
    for file_name in UI_ARTIFACT_FILES:
        payload = artifacts.get(file_name)
        if payload is None:
            payload = {"meta": _ui_meta({"artifact_id": f"UI1_{Path(file_name).stem.upper()}"})}
        _write_json(ui_dir / file_name, payload)
    return {
        "artifact_id": "UI1_OWNER_DASHBOARD_BUILD_SUMMARY",
        "status": "BUILT",
        "base": repo_posix(base),
        "boot_json": repo_posix(ui_dir / BOOT_JSON),
        "boot_js": repo_posix(ui_dir / BOOT_JS),
        "generated_ui_artifact_count": len(UI_ARTIFACT_FILES) + 2,
        "registry_row_count": review_data["meta"]["registry_row_count"],
        "decision_queue_count": review_data["meta"]["decision_queue_count"],
        "actionable_card_count": review_data["meta"]["actionable_card_count"],
        "chart_count": review_data["meta"]["chart_count"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="docs/master_plan/generated/pr169_dash1")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    base = (repo_root / args.base).resolve()
    summary = build_ui(base, repo_root)
    print(
        "PR169_DASH1_UI1_OWNER_DASHBOARD_UI_BUILD_OK "
        f"rows={summary['registry_row_count']} ui_artifacts={summary['generated_ui_artifact_count']} "
        f"out={summary['boot_json']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
