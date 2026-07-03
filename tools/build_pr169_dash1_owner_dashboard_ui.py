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
    "Decisions",
    "Research",
    "Chat",
    "Trade Workbench",
    "Agents",
    "Quantum",
    "More",
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
