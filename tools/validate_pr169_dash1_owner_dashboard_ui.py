from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.build_pr169_dash1_owner_dashboard_ui import (
    AUTHORITY_BOUNDARY,
    BOOT_JS,
    BOOT_JSON,
    EXPERIENCE_MODE_STORAGE_KEY,
    GUIDANCE_DENSITY_STORAGE_KEY,
    DISPLAY_TEXT_SIZES,
    ENTER_TO_SEND_STORAGE_KEY,
    MOBILE_TABS,
    OWNER_SETTINGS_SECTIONS,
    OWNER_SETTINGS_STORAGE_KEY,
    THEME_MODES,
    REQUIRED_TOP_LEVEL_KEYS,
    SEMANTIC_COLORS,
    TECHNICAL_DETAILS_STORAGE_KEY,
    TEXT_SIZE_STORAGE_KEY,
    THEME_STORAGE_KEY,
    UI_ARTIFACT_FILES,
)


SUCCESS_MARKER = "PR169_DASH1_UI1_OWNER_DASHBOARD_UI_VALIDATION_OK"
FORBIDDEN_TEXT = (
    "https://",
    "http://",
    "cdn.",
    "POST /orders",
    "submit live order directly",
    "guaranteed positive profit",
)
GENERIC_PLACEHOLDER_PATTERNS = (
    r"\bTODO\b",
    r"\bdummy\b",
    r"\bplaceholder\b",
    r"\bcoming soon\b",
    r"\bnot implemented\b(?! with no provider stage)",
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for key, child in value.items():
            values.append(key)
            values.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk(child))
    return values


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _contains_second_state_model(payload: dict[str, Any]) -> bool:
    state_model = payload.get("meta", {}).get("artifact_id") == "UI1_OWNER_DASHBOARD_REVIEW_DATA"
    renderer = payload.get("authority_boundary", {}).get("UI1_authority_boundary_ref") == AUTHORITY_BOUNDARY
    return not (state_model and renderer)


def validate(base: Path) -> tuple[str, ...]:
    failures: list[str] = []
    ui_dir = base / "ui"
    boot_json = ui_dir / BOOT_JSON
    boot_js = ui_dir / BOOT_JS
    html = ui_dir / "owner_dashboard_review_surface.html"
    css = ui_dir / "owner_dashboard_review_surface.css"
    js = ui_dir / "owner_dashboard_review_surface.js"

    for path in (boot_json, boot_js, html, css, js):
        if not path.exists():
            failures.append(f"missing_ui_file:{path}")
    for file_name in UI_ARTIFACT_FILES:
        if not (ui_dir / file_name).exists():
            failures.append(f"missing_generated_ui_artifact:{file_name}")
    if not boot_json.exists():
        return tuple(failures)

    data = _read_json(boot_json)
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            failures.append(f"boot_data_missing_top_level_key:{key}")
    if data.get("meta", {}).get("data_source") != "GENERATED_ARTIFACTS":
        failures.append("boot_data_not_generated_artifacts_primary")
    if data.get("fixture_fallback", {}).get("active") is not False:
        failures.append("fixture_fallback_active_when_generated_artifacts_exist")
    if data.get("fixture_fallback", {}).get("fixture_primary_when_generated_artifacts_exist") is not False:
        failures.append("fixture_primary_when_generated_artifacts_exist")
    if not data.get("owner_packet", {}).get("packet_id"):
        failures.append("owner_packet_not_loaded")
    if not data.get("decision_queue"):
        failures.append("decision_queue_not_loaded")
    if not data.get("actionable_cards"):
        failures.append("actionable_cards_not_loaded")
    if not data.get("action_registry"):
        failures.append("action_registry_not_loaded")

    renderer_boundary = _read_json(ui_dir / "owner_dashboard_dash1_ui1_renderer_boundary.generated.json")
    for key in (
        "DASH1_is_canonical_backend_control_plane",
        "UI1_is_renderer_enhancement_responsive_layer",
        "renders_existing_dash1_artifacts",
    ):
        if renderer_boundary.get(key) is not True:
            failures.append(f"renderer_boundary_not_true:{key}")
    for key in (
        "replacement_dashboard",
        "parallel_dashboard",
        "second_registry",
        "new_governance_plane",
        "new_action_semantics",
        "second_mobile_state_model",
        "second_chat_state_model",
        "manual_projection_truth",
    ):
        if renderer_boundary.get(key) is not False:
            failures.append(f"renderer_boundary_not_false:{key}")

    state_model = _read_json(ui_dir / "owner_dashboard_state_model.generated.json")
    for key in (
        "one_dashboard_state_model",
        "one_owner_action_grammar",
        "one_owner_agent_conversation_model",
        "one_trade_workbench_model",
        "no_duplicate_mobile_only_data_layer",
        "no_duplicate_chat_system",
        "no_duplicate_telegram_governance_plane",
    ):
        if state_model.get(key) is not True:
            failures.append(f"state_model_contract_missing:{key}")

    theme = _read_json(ui_dir / "owner_dashboard_theme_contract.generated.json")
    if not {"DARK", "LIGHT", "DARK_PRO", "MIDNIGHT_BLUE", "SLATE", "LIGHT_PRO", "LOW_GLARE", "HIGH_CONTRAST", "CUSTOM"} <= set(theme.get("supported_modes", [])):
        failures.append("theme_modes_missing_r2r3_presets")
    if theme.get("localStorage_key") != THEME_STORAGE_KEY:
        failures.append("theme_storage_key_bad")
    if set(theme.get("semantic_colors", {}).values()) != set(SEMANTIC_COLORS.values()):
        failures.append("semantic_colors_not_stable")
    if theme.get("light_mode_not_separate_dashboard_state") is not True:
        failures.append("light_mode_creates_separate_state")

    mobile = _read_json(ui_dir / "owner_dashboard_mobile_navigation.generated.json")
    labels = [tab["label"] for tab in mobile.get("tabs", [])]
    for tab in MOBILE_TABS:
        if tab not in labels:
            failures.append(f"mobile_tab_missing:{tab}")
    if mobile.get("touch_targets_minimum_px", 0) < 44:
        failures.append("mobile_touch_targets_too_small")

    provider = _read_json(ui_dir / "owner_dashboard_provider_stage_route_map.generated.json")
    stages = {row.get("stage_id") for row in provider.get("routes", [])}
    for stage in {
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
    }:
        if stage not in stages:
            failures.append(f"provider_stage_missing:{stage}")

    qku = _read_json(ui_dir / "owner_dashboard_qku_formula_computability_matrix.generated.json")
    allowed_qku_states = {
        "COMPUTABLE_WITH_CURRENT_CONTRACT",
        "COMPUTABLE_AFTER_PROVIDER_ROUTE",
        "SCHEDULABLE_AFTER_ADAPTER",
        "REPLAY_PAPER_READY_PROVIDER_PENDING",
        "QMAP_REQUIRED",
        "PLUGIN_INTAKE_REQUIRED",
        "ALLOWLIST_PROVIDER_PENDING",
        "BLOCKED_BY_AUTHORITY_BOUNDARY",
        "ACTIONABLE_GAP_ROUTE",
    }
    if not qku.get("rows"):
        failures.append("qku_computability_matrix_empty")
    for row in qku.get("rows", []):
        if row.get("computability_state") not in allowed_qku_states:
            failures.append(f"bad_qku_computability_state:{row.get('computability_state')}")
        if not row.get("activation_route"):
            failures.append("qku_matrix_row_missing_activation_route")

    five = _read_json(ui_dir / "owner_dashboard_ui1_five_question_acceptance.report.json")
    if len(five.get("questions", [])) != 5:
        failures.append("five_question_report_wrong_count")
    for row in five.get("questions", []):
        if row.get("answer_status") != "PASS":
            failures.append(f"five_question_not_pass:{row.get('question_id')}")
        if not row.get("visible_widget_refs") or not row.get("generated_artifact_refs"):
            failures.append(f"five_question_missing_refs:{row.get('question_id')}")

    html_text = _text(html)
    css_text = _text(css)
    js_text = _text(js)
    combined = "\n".join([html_text, css_text, js_text])
    for marker in FORBIDDEN_TEXT:
        if marker in combined:
            failures.append(f"forbidden_ui_text:{marker}")
    if f'<script src="{BOOT_JS}">' not in html_text:
        failures.append("bootstrap_script_missing_from_html")
    if "<script src=\"owner_dashboard_review_surface.js\">" not in html_text:
        failures.append("app_script_missing_from_html")
    if 'data-theme="dark"' not in html_text:
        failures.append("html_default_dark_theme_missing")
    for snippet in (
        "OwnerDashboardPacket",
        "OwnerDecisionQueue",
        "OwnerActionableCards",
        "Trade Workbench",
        "Owner-Agent Chat Workspace",
        "Provider Stage Route Map",
        "CENTRALIZED_AGENT_QKU_ACCESS_RESOLVER_PANEL",
        "DARK",
        "LIGHT",
        "mobile-bottom-nav",
        "drilldownDrawer",
        "ownerSettingsCenter",
        "OwnerSettingsV1",
        "OwnerSearchIndexV1",
        "OwnerChartInteractionPolicyV1",
        "data-chat-preset-dropdown",
    ):
        if snippet not in combined:
            failures.append(f"required_ui_snippet_missing:{snippet}")
    for variable in (
        "--qtt-bg",
        "--qtt-bg-panel",
        "--qtt-bg-card",
        "--qtt-border",
        "--qtt-text",
        "--qtt-muted",
        "--qtt-green",
        "--qtt-red",
        "--qtt-blue",
        "--qtt-purple",
        "--qtt-orange",
        "--qtt-yellow",
        "--qtt-gray",
    ):
        if variable not in css_text:
            failures.append(f"css_variable_missing:{variable}")
    if THEME_STORAGE_KEY not in js_text:
        failures.append("theme_storage_key_missing_from_js")
    if "window.QTT_OWNER_DASHBOARD_DATA" not in _text(boot_js):
        failures.append("bootstrap_global_missing")
    if "fetch(" in js_text:
        failures.append("app_js_uses_fetch")
    if "OwnerActionRegistry" not in combined:
        failures.append("owner_action_registry_ref_missing")
    if "OwnerSurfaceResolver" not in combined:
        failures.append("owner_surface_resolver_ref_missing")
    for snippet in (
        "data-chart-id",
        "data-chart-kind",
        "data-chart-render-state",
        "data-chart-source-ref",
        "data-provider-stage",
        "data-authority-boundary",
        'data-chat-composer="owner-plain-english"',
        'data-chat-runtime-side-effect="false"',
        'data-intent-parser="local-preview"',
        "data-workbench-id",
        "data-owner-trade-intent-preview",
        "data-trade-variable-field",
        "data-no-trade-comparator",
        "data-execution-router-provider-pending",
        "Developer Mode",
    ):
        if snippet not in combined:
            failures.append(f"required_ui1r1_snippet_missing:{snippet}")

    all_values = "\n".join(str(value) for value in _walk(data))
    if "guaranteed positive profit" in all_values:
        failures.append("profit_guarantee_wording_present")
    if "validated positive net-cash evidence" not in all_values and "validated_positive_net_cash_evidence" not in all_values:
        failures.append("validated_positive_net_cash_wording_missing")
    if _contains_second_state_model(data):
        failures.append("state_model_or_renderer_boundary_bad")
    for pattern in GENERIC_PLACEHOLDER_PATTERNS:
        if re.search(pattern, all_values, flags=re.IGNORECASE):
            failures.append(f"generic_placeholder_pattern_present:{pattern}")

    for file_name in UI_ARTIFACT_FILES:
        payload = _read_json(ui_dir / file_name)
        meta = payload.get("meta", {})
        if meta.get("manual_edit_allowed") is not False:
            failures.append(f"manual_edit_not_false:{file_name}")
        if meta.get("runtime_side_effect_allowed") is not False:
            failures.append(f"runtime_side_effect_not_false:{file_name}")
        if meta.get("credential_access_allowed") is not False:
            failures.append(f"credential_access_not_false:{file_name}")
        if meta.get("connector_access_allowed") is not False:
            failures.append(f"connector_access_not_false:{file_name}")
        if meta.get("order_execution_allowed") is not False:
            failures.append(f"order_execution_not_false:{file_name}")

    forbidden_files = (
        "owner_dashboard_workstation_expansion_matrix.generated.json",
        "owner_dashboard_workstation_expansion_matrix.generated.jsonl",
        "workstation_expansion_matrix.generated.json",
        "50_idea_backlog.generated.json",
    )
    for file_name in forbidden_files:
        if (ui_dir / file_name).exists() or (base / file_name).exists():
            failures.append(f"deferred_idea_artifact_forbidden:{file_name}")

    acceptance = _read_json(ui_dir / "ui1r1_12fix_acceptance.generated.json")
    rows = acceptance.get("rows", [])
    if len(rows) != 12:
        failures.append("ui1r1_12fix_acceptance_wrong_count")
    if any(row.get("status") != "PASS" for row in rows):
        failures.append("ui1r1_12fix_acceptance_not_all_pass")
    if acceptance.get("deferred_brainstorm_ideas_not_materialized") is not True:
        failures.append("ui1r1_deferred_brainstorm_containment_missing")

    owner_mode = _read_json(ui_dir / "ui1r1_owner_mode.report.json")
    for key in (
        "owner_mode_default",
        "developer_mode_collapsed_by_default",
        "registry_diagnostics_not_owner_default",
        "raw_json_not_primary_owner_content",
    ):
        if owner_mode.get(key) is not True:
            failures.append(f"ui1r1_owner_mode_report_missing:{key}")

    chart_manifest = _read_json(ui_dir / "ui1r1_chart_manifest.generated.json")
    chart_rows = chart_manifest.get("charts", [])
    required_chart_ids = {
        "portfolio_equity_curve",
        "net_cash_pnl_by_time_range",
        "cost_adjusted_net_pnl",
        "drawdown_curve",
        "TCA_waterfall_and_implementation_shortfall",
        "capital_allocation_by_market",
        "exposure_by_venue",
        "edge_alpha_scoreboard_visual",
        "agent_disagreement_visual",
        "DAG_route_graph_visual",
    }
    present_chart_ids = {row.get("chart_id") for row in chart_rows}
    for chart_id in required_chart_ids:
        if chart_id not in present_chart_ids:
            failures.append(f"ui1r1_chart_missing:{chart_id}")
    for row in chart_rows:
        if row.get("data_chart_render_state") not in {"VISUAL_RENDERED", "PROVIDER_PENDING_VISUAL_FRAME"}:
            failures.append(f"ui1r1_bad_chart_render_state:{row.get('chart_id')}")
        if row.get("fake_value_allowed") is not False:
            failures.append(f"ui1r1_chart_allows_fake_value:{row.get('chart_id')}")

    chat_contract = _read_json(ui_dir / "ui1r1_chat_contract.generated.json")
    if len(chat_contract.get("prompt_chips", [])) < 8:
        failures.append("ui1r1_chat_prompt_chips_missing")
    intent_contract = _read_json(ui_dir / "ui1r1_intent_contract.generated.json")
    for intent in ("TRADE_CHECK_REQUEST", "RESEARCH_ANALYSIS_REQUEST", "NO_TRADE_EXPLANATION_REQUEST", "EDGE_ALPHA_RANKING_REQUEST"):
        if intent not in intent_contract.get("intent_families", []):
            failures.append(f"ui1r1_intent_family_missing:{intent}")
    chat_examples = _read_json(ui_dir / "ui1r1_chat_examples.generated.json")
    for row in chat_examples.get("examples", []):
        parsed = row.get("parsed_preview_output", {})
        if parsed.get("object_type") != "OwnerPlainEnglishIntentV1":
            failures.append("ui1r1_chat_example_missing_owner_intent")
        if parsed.get("runtime_side_effect") is not False:
            failures.append("ui1r1_chat_example_runtime_side_effect")

    order_sim = _read_json(ui_dir / "ui1r1_order_sim.generated.json")
    if len(order_sim.get("owner_input_fields", [])) < 17:
        failures.append("ui1r1_order_sim_fields_missing")
    if order_sim.get("runtime_side_effect") is not False:
        failures.append("ui1r1_order_sim_runtime_side_effect")
    if {row.get("card_id") for row in order_sim.get("comparison_cards", [])} != {"best_candidate", "runner_up_challenger", "no_trade_alternative"}:
        failures.append("ui1r1_order_sim_comparison_cards_missing")

    edge = _read_json(ui_dir / "ui1r1_edge_alpha.generated.json")
    if edge.get("ranking_rule") != "execution_adjusted_ordering_not_raw_edge_only":
        failures.append("ui1r1_edge_alpha_ranking_rule_bad")
    for row in edge.get("rows", []):
        if row.get("metadata_only_ranking") is not False:
            failures.append("ui1r1_edge_alpha_metadata_only_ranking")

    disagreement = _read_json(ui_dir / "ui1r1_agent_disagreement.generated.json")
    if len(disagreement.get("rows", [])) < 10:
        failures.append("ui1r1_agent_disagreement_rows_missing")
    if any(row.get("fake_agent_claim") is not False for row in disagreement.get("rows", [])):
        failures.append("ui1r1_agent_disagreement_fake_claim")

    params = _read_json(ui_dir / "ui1r1_parameter_tuning.generated.json")
    if params.get("live_parameter_mutation_allowed") is not False:
        failures.append("ui1r1_parameter_live_mutation_allowed")
    if not all(row.get("atomic_drilldown") for row in params.get("rows", [])):
        failures.append("ui1r1_parameter_atomic_drilldown_missing")

    mobile_parity = _read_json(ui_dir / "ui1r1_mobile_parity.report.json")
    mobile_surfaces = {row.get("surface") for row in mobile_parity.get("surfaces", [])}
    for surface in {"Home", "Portfolio", "Trade Workbench", "Chat", "Edge/Alpha", "Agents", "Parameters", "Developer Mode"}:
        if surface not in mobile_surfaces:
            failures.append(f"ui1r1_mobile_surface_missing:{surface}")
    if mobile_parity.get("separate_mobile_state_model") is not False:
        failures.append("ui1r1_mobile_has_separate_state_model")

    crosslink = _read_json(ui_dir / "ui1r1_inst_quant_crosslink.report.json")
    if any(row.get("labels_only") is not False for row in crosslink.get("rows", [])):
        failures.append("ui1r1_inst_quant_labels_only")
    if crosslink.get("quantum_advantage_claim") is not False:
        failures.append("ui1r1_quantum_advantage_claim")

    playwright = _read_json(ui_dir / "ui1r1_playwright.report.json")
    if len(playwright.get("screenshots", [])) < 9:
        failures.append("ui1r1_playwright_screenshot_rows_missing")
    if playwright.get("network_status") != "PASS" or playwright.get("console_status") != "PASS":
        failures.append("ui1r1_playwright_status_not_pass")

    copy_map = _read_json(ui_dir / "ui1r2_copy_map.generated.json")
    copy_rows = copy_map.get("rows", [])
    exact_copy = {row.get("technical_pattern_or_exact_id"): row for row in copy_rows}
    required_copy = {
        "DASH1_FEATURE_011_ACKNOWLEDGMENT_IS_NOT_LIVE_APPROVAL": "Acknowledging review does not approve a live trade.",
        "VISIBLE_EMPTY_STATE_PROVIDER_PENDING": "Waiting for provider data.",
        "CONTRACT_DEFINED_PROVIDER_PENDING": "Provider contract defined; runtime not active yet.",
        "ROUTED_PENDING_PROVIDER": "Connected to a pending QTT provider route.",
        "NO_DASHBOARD_RUNTIME_NO_ORDER_NO_PRIVATE_READS": "Review-only dashboard.",
        "CHECK_TRADE_WITH_QTT_AGENTS": "Check trade with QTT agents.",
        "REQUEST_NO_TRADE_REOPTIMIZATION": "Ask QTT to improve the no-trade result.",
        "OwnerSurfaceResolver": "QTT routing link verified.",
        "OwnerActionRegistry": "Owner actions governed.",
        "owner_dashboard_surface_registry.jsonl": "Verified dashboard registry source.",
    }
    for technical_id, owner_title in required_copy.items():
        if exact_copy.get(technical_id, {}).get("owner_title") != owner_title:
            failures.append(f"ui1r2_copy_map_missing_translation:{technical_id}")
    for row in copy_rows:
        for key in (
            "presentation_id",
            "technical_pattern_or_exact_id",
            "owner_title",
            "owner_summary",
            "owner_status_label",
            "owner_action_label",
            "source_artifact_refs",
            "PR165_D2_agent_role_refs_or_gap",
            "QKU_formula_refs_or_gap",
            "authority_boundary",
            "provider_stage",
            "activation_route",
            "validation_ref",
        ):
            if not row.get(key):
                failures.append(f"ui1r2_copy_row_missing:{key}")

    mode = _read_json(ui_dir / "ui1r2_mode.generated.json")
    mode_rows = {row.get("mode_id"): row for row in mode.get("rows", [])}
    if mode.get("default_mode") != "GUIDED_OWNER":
        failures.append("ui1r2_default_mode_not_guided_owner")
    if set(mode_rows) != {"GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"}:
        failures.append("ui1r2_modes_missing")
    if mode.get("no_second_dashboard_state_model") is not True or mode.get("no_second_action_grammar") is not True:
        failures.append("ui1r2_mode_policy_second_model_or_action_grammar")
    if set(mode.get("local_storage_keys_allowed", [])) != {EXPERIENCE_MODE_STORAGE_KEY, GUIDANCE_DENSITY_STORAGE_KEY}:
        failures.append("ui1r2_mode_storage_keys_bad")

    disclosure = _read_json(ui_dir / "ui1r2_disclosure.report.json")
    for key, expected in (
        ("education_text_wall_visible_by_default", False),
        ("technical_details_visible_by_default", False),
        ("raw_refs_visible_by_default", False),
        ("Developer_Mode_default", False),
        ("GUIDED_OWNER_default", True),
        ("ADVANCED_OWNER_available", True),
        ("DEVELOPER_available", True),
    ):
        if disclosure.get(key) is not expected:
            failures.append(f"ui1r2_disclosure_bad:{key}")

    education = _read_json(ui_dir / "ui1r2_education.generated.json")
    glossary_terms = {row.get("term") for row in education.get("glossary", [])}
    for term in {"PnL", "expected net cash", "TCA", "no-trade", "QKU", "Execution Router", "paper trading", "replay", "shadow"}:
        if term not in glossary_terms:
            failures.append(f"ui1r2_glossary_term_missing:{term}")
    if education.get("education_text_wall_visible_by_default") is not False:
        failures.append("ui1r2_education_text_wall_default_bad")

    guided = _read_json(ui_dir / "ui1r2_guided_flow.generated.json")
    flow_ids = {row.get("workflow_id") for row in guided.get("flows", [])}
    for workflow_id in {"CHECK_TRADE", "RESEARCH_CANDIDATE", "EXPLAIN_NO_TRADE", "PARAMETER_TUNING", "EDGE_ALPHA_REVIEW"}:
        if workflow_id not in flow_ids:
            failures.append(f"ui1r2_guided_flow_missing:{workflow_id}")
    for key in (
        "runtime_side_effect_allowed",
        "live_LLM_call_allowed",
        "real_agent_execution_allowed",
        "paper_execution_allowed",
        "live_execution_allowed",
        "direct_venue_submit_allowed",
        "ExecutionRouter_release_allowed",
    ):
        if guided.get(key) is not False:
            failures.append(f"ui1r2_guided_flow_authority_bad:{key}")

    next_step = _read_json(ui_dir / "ui1r2_next_step.generated.json")
    next_rows = next_step.get("rows", [])
    next_ids = {row.get("next_step_id") for row in next_rows}
    required_next_ids = {
        "NEXT_STEP_SEND_TO_TRADE_WORKBENCH",
        "NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS",
        "NEXT_STEP_REQUEST_REPLAY_PREVIEW",
        "NEXT_STEP_REQUEST_PAPER_PREVIEW",
        "NEXT_STEP_SHOW_QKU_FORMULA_ROUTES",
        "NEXT_STEP_EXPLAIN_NO_TRADE",
        "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN",
        "NEXT_STEP_OPEN_CHART_DRILLDOWN",
        "NEXT_STEP_OPEN_TECHNICAL_DETAILS",
        "NEXT_STEP_DISABLED_PROVIDER_PENDING_EDUCATION",
    }
    if not required_next_ids <= next_ids:
        failures.append("ui1r2_next_step_required_rows_missing")
    for row in next_rows:
        for key in (
            "action_id",
            "owner_label",
            "current_surface_id",
            "target_surface_id",
            "target_workflow_id",
            "target_step_id",
            "prefill_context_refs",
            "preview_object_type",
            "provider_stage",
            "authority_boundary",
            "what_happens_next",
            "what_will_not_happen_now",
            "source_artifact_refs",
            "PR165_D2_agent_role_refs_or_gap",
            "QKU_formula_refs_or_gap",
            "LLM_view_refs_or_provider_route",
            "activation_route",
            "validation_ref",
        ):
            if not row.get(key):
                failures.append(f"ui1r2_next_step_row_missing:{key}")
        if row.get("runtime_side_effect_allowed") is not False:
            failures.append(f"ui1r2_next_step_runtime_allowed:{row.get('next_step_id')}")
        forbidden_claims = (
            "live LLM call runs",
            "agent task runs",
            "replay runs",
            "paper runs",
            "venue order",
            "Execution Router release occurs",
        )
        if any(claim in str(row.get("what_happens_next", "")) for claim in forbidden_claims):
            failures.append(f"ui1r2_next_step_bad_runtime_claim:{row.get('next_step_id')}")

    action_menu = _read_json(ui_dir / "ui1r2_action_menu.generated.json")
    option_next_ids = {
        option.get("next_step_id")
        for row in action_menu.get("rows", [])
        for option in row.get("options", [])
        if option.get("state") == "ENABLED_LOCAL_PREVIEW"
    }
    if not option_next_ids <= next_ids:
        failures.append("ui1r2_action_menu_enabled_option_without_next_step")
    for row in action_menu.get("rows", []):
        if not row.get("options"):
            failures.append(f"ui1r2_action_menu_no_options:{row.get('menu_id')}")
        if row.get("runtime_side_effect_allowed") is not False:
            failures.append(f"ui1r2_action_menu_runtime_allowed:{row.get('menu_id')}")
        for option in row.get("options", []):
            if option.get("owner_label", "").isupper() or "_" in option.get("owner_label", ""):
                failures.append(f"ui1r2_action_option_machine_label:{option.get('next_step_id')}")
            if option.get("runtime_side_effect_allowed") is not False:
                failures.append(f"ui1r2_action_option_runtime_allowed:{option.get('next_step_id')}")

    guidance = _read_json(ui_dir / "ui1r2_guidance.report.json")
    for key in (
        "all_dropdown_options_readable",
        "all_disabled_actions_explain_reason",
        "all_menus_route_to_central_registry_or_navigation_type",
        "all_enabled_menu_actions_have_next_step_route",
        "all_next_step_routes_create_only_local_preview_or_navigation",
        "all_agent_refs_resolve_or_gap",
        "all_qku_formula_refs_resolve_or_gap",
        "no_raw_action_ids_in_owner_mode",
        "no_new_blockers_created_by_guidance",
        "education_collapsed_by_default",
    ):
        if guidance.get(key) is not True:
            failures.append(f"ui1r2_guidance_report_missing:{key}")

    card_copy = _read_json(ui_dir / "ui1r2_card_copy.report.json")
    if card_copy.get("owner_cards_human_readable") is not True or card_copy.get("learning_sections_collapsed_by_default") is not True:
        failures.append("ui1r2_card_copy_report_bad")
    text_safety = _read_json(ui_dir / "ui1r2_text_safety.report.json")
    if text_safety.get("owner_mode_blocklist_visible_count") != 0:
        failures.append("ui1r2_text_safety_blocklist_nonzero")
    if "OwnerNextStepRouter" not in combined or "DashboardSystem" not in combined:
        failures.append("ui1r2_central_router_or_dashboard_system_missing_from_renderer")
    for snippet in (
        "data-experience-mode",
        "data-owner-next-action-menu",
        "data-next-step-id",
        "data-local-receipt-preview",
        "Tell me what matters",
        "How QTT will trade with AI",
        "ownerGlossary",
        "guidedWorkflowPanel",
        "routePreviewPanel",
    ):
        if snippet not in combined:
            failures.append(f"ui1r2_required_ui_snippet_missing:{snippet}")

    r2r1_files = (
        "ui1r2r1_mode_policy.generated.json",
        "ui1r2r1_mode_render.report.json",
        "ui1r2r1_interaction_map.generated.json",
        "ui1r2r1_interaction_result.report.json",
        "ui1r2r1_next_step.generated.json",
        "ui1r2r1_next_step.report.json",
        "ui1r2r1_chat_submit.report.json",
        "ui1r2r1_workbench_prefill.report.json",
        "ui1r2r1_visual_polish.report.json",
        "ui1r2r1_visual_compactness.report.json",
        "ui1r2r1_chat_intent.report.json",
        "ui1r2r1_owner_command.report.json",
        "ui1r2r1_evidence_spine.report.json",
        "ui1r2r1_playwright.report.json",
    )
    for file_name in r2r1_files:
        doc = _read_json(ui_dir / file_name)
        meta = doc.get("meta", {})
        for key in (
            "manual_edit_allowed",
            "runtime_truth_authority",
            "agent_consumable_authority",
            "credential_access_allowed",
            "connector_access_allowed",
            "order_execution_allowed",
        ):
            if meta.get(key) is not False:
                failures.append(f"ui1r2r1_meta_bad:{file_name}:{key}")
        if doc.get("runtime_side_effect_allowed", False) is not False:
            failures.append(f"ui1r2r1_runtime_allowed:{file_name}")

    mode_policy = _read_json(ui_dir / "ui1r2r1_mode_policy.generated.json")
    if mode_policy.get("mode_policy_id") != "OwnerExperienceModePolicy":
        failures.append("ui1r2r1_mode_policy_not_centralized")
    mode_rows = {row.get("mode_id"): row for row in mode_policy.get("rows", [])}
    if set(mode_rows) != {"GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"}:
        failures.append("ui1r2r1_mode_rows_missing")
    for mode_id, row in mode_rows.items():
        for field in (
            "visible_widget_groups",
            "hidden_widget_groups",
            "metric_density",
            "education_density",
            "technical_disclosure_policy",
            "default_expansion_policy",
            "source_artifact_refs",
            "action_registry_ref",
            "state_model_ref",
            "validation_ref",
        ):
            if field not in row:
                failures.append(f"ui1r2r1_mode_field_missing:{mode_id}:{field}")
    if mode_rows.get("GUIDED_OWNER", {}).get("visible_widget_groups") == mode_rows.get("ADVANCED_OWNER", {}).get("visible_widget_groups"):
        failures.append("ui1r2r1_guided_advanced_widget_groups_identical")
    if "developer_json" not in mode_rows.get("DEVELOPER", {}).get("visible_widget_groups", []):
        failures.append("ui1r2r1_developer_missing_technical_group")

    mode_render = _read_json(ui_dir / "ui1r2r1_mode_render.report.json")
    if mode_render.get("mode_content_identical") is not False:
        failures.append("ui1r2r1_mode_render_identical")
    if mode_render.get("advanced_owner_visible_metric_group_count", 0) <= mode_render.get("guided_owner_visible_metric_group_count", 0):
        failures.append("ui1r2r1_advanced_not_denser_than_guided")
    if mode_render.get("developer_visible_technical_group_count", 0) <= mode_render.get("advanced_owner_visible_metric_group_count", 0):
        failures.append("ui1r2r1_developer_not_more_technical_than_advanced")

    interaction_map = _read_json(ui_dir / "ui1r2r1_interaction_map.generated.json")
    required_handlers = {
        "OwnerExperienceModePolicy",
        "OwnerChatSubmitHandler",
        "OwnerGuidedInputHandler",
        "OwnerNextStepRouter",
        "OwnerWorkbenchPrefillAdapter",
        "OwnerDrilldownRouter",
        "OwnerInteractionReceiptPreviewBuilder",
    }
    if not required_handlers <= set(interaction_map.get("central_handlers", [])):
        failures.append("ui1r2r1_interaction_handlers_missing")
    for row in interaction_map.get("rows", []):
        if row.get("runtime_side_effect_allowed") is not False:
            failures.append(f"ui1r2r1_interaction_runtime_allowed:{row.get('interaction_id')}")
        if not row.get("owner_visible_state_change"):
            failures.append(f"ui1r2r1_interaction_no_visible_state:{row.get('interaction_id')}")

    chat_submit = _read_json(ui_dir / "ui1r2r1_chat_submit.report.json")
    if chat_submit.get("default_desktop_enter_behavior") != "NEWLINE":
        failures.append("ui1r2r1_chat_enter_not_newline_default")
    if chat_submit.get("mobile_enter_behavior") != "NEWLINE":
        failures.append("ui1r2r1_chat_mobile_enter_not_newline")
    if chat_submit.get("physical_enter_identical_to_send_by_default") is not False:
        failures.append("ui1r2r1_chat_enter_matches_send_by_default")
    if chat_submit.get("enter_to_send_default_enabled") is not False:
        failures.append("ui1r2r1_chat_enter_to_send_enabled_by_default")
    for key in (
        "enter_to_send_optional_setting_available",
        "ctrl_enter_submits_local_preview",
        "send_button_submits_local_preview",
        "shift_enter_inserts_newline",
        "empty_send_click_inline_hint",
        "empty_input_no_submit",
        "owner_and_qtt_preview_bubbles_visible",
    ):
        if chat_submit.get(key) is not True:
            failures.append(f"ui1r2r1_chat_submit_missing:{key}")
    if chat_submit.get("central_conversation_state_ref") != "OwnerConversationStateV1":
        failures.append("ui1r2r1_chat_not_central_conversation_state")
    intent_report = _read_json(ui_dir / "ui1r2r1_chat_intent.report.json")
    for intent in (
        "TRADE_CHECK_REQUEST",
        "RESEARCH_ANALYSIS_REQUEST",
        "QKU_MATERIALIZATION_REQUEST",
        "NO_TRADE_EXPLANATION_REQUEST",
        "PARAMETER_TUNING_REQUEST",
        "UNKNOWN_OWNER_REQUEST_NEEDS_CLARIFICATION",
    ):
        if intent not in intent_report.get("recognized_intent_families", []):
            failures.append(f"ui1r2r1_intent_missing:{intent}")

    visual_compactness = _read_json(ui_dir / "ui1r2r1_visual_compactness.report.json")
    if visual_compactness.get("collapsed_control_max_default_body_rows") != 0:
        failures.append("ui1r2r1_collapsed_budget_bad")
    if visual_compactness.get("technical_details_dominant_in_guided_owner") is not False:
        failures.append("ui1r2r1_technical_details_dominant")
    if visual_compactness.get("generic_owner_decision_repeated_default_allowed") is not False:
        failures.append("ui1r2r1_generic_owner_decision_allowed")
    for row in visual_compactness.get("rows", []):
        if row.get("large_empty_collapsed_body_present") is not False:
            failures.append(f"ui1r2r1_large_empty_collapsed_body:{row.get('widget_id')}")
        if row.get("specific_semantic_title_present") is not True:
            failures.append(f"ui1r2r1_semantic_title_missing:{row.get('widget_id')}")

    owner_command = _read_json(ui_dir / "ui1r2r1_owner_command.report.json")
    if owner_command.get("execution_router_release_authority_created") is not False:
        failures.append("ui1r2r1_execution_router_release_authority_created")
    evidence_spine = _read_json(ui_dir / "ui1r2r1_evidence_spine.report.json")
    required_spine = {
        "execution_adjusted_rank_ref",
        "TCA_decomposition_ref",
        "overfit_false_discovery_control_ref",
        "portfolio_marginal_utility_ref",
        "capacity_crowding_limit_ref",
        "champion_challenger_ref",
        "no_trade_comparator_and_reoptimization_route",
        "quantum_structural_readiness_ref",
        "qstruct_objective_constraint_variable_ref",
        "interpret_back_map_ref",
        "DAG_upstream_downstream_route_ref",
        "PR165_D2_agent_role_refs_or_gap",
        "QKU_formula_refs_or_gap",
        "LLM_view_refs_or_provider_route",
    }
    if not required_spine <= set(evidence_spine.get("required_evidence_spine_refs", [])):
        failures.append("ui1r2r1_evidence_spine_missing_refs")
    if evidence_spine.get("no_fake_trading_evidence") is not True or evidence_spine.get("no_fake_quantum_advantage") is not True:
        failures.append("ui1r2r1_fake_evidence_guard_missing")
    for row in evidence_spine.get("rows", []):
        for field in required_spine:
            if not row.get(field):
                failures.append(f"ui1r2r1_evidence_row_missing:{row.get('widget_id')}:{field}")

    for snippet in (
        "OwnerChatSubmitHandler",
        "OwnerGuidedInputHandler",
        "OwnerWorkbenchPrefillAdapter",
        "data-chat-submit-hint",
        "data-enter-to-send-setting",
        "CTRL_ENTER_SUBMIT",
        "data-guided-current-step",
        "data-mode-advanced-metric",
        "data-mode-developer-technical",
        "data-provider-pending-action",
    ):
        if snippet not in combined:
            failures.append(f"ui1r2r1_renderer_snippet_missing:{snippet}")

    display_prefs = _read_json(ui_dir / "ui1r2r2_display_preferences.generated.json")
    if display_prefs.get("preference_model_id") != "OwnerDisplayPreferenceV1":
        failures.append("ui1r2r2_display_preference_model_bad")
    if set(display_prefs.get("text_size", {}).get("allowed", [])) != set(DISPLAY_TEXT_SIZES):
        failures.append("ui1r2r2_text_size_options_bad")
    if display_prefs.get("text_size", {}).get("localStorage_key") != TEXT_SIZE_STORAGE_KEY:
        failures.append("ui1r2r2_text_size_key_bad")
    allowed_keys = set(display_prefs.get("allowed_localStorage_keys", []))
    for key in {
        THEME_STORAGE_KEY,
        EXPERIENCE_MODE_STORAGE_KEY,
        GUIDANCE_DENSITY_STORAGE_KEY,
        TEXT_SIZE_STORAGE_KEY,
        TECHNICAL_DETAILS_STORAGE_KEY,
        ENTER_TO_SEND_STORAGE_KEY,
    }:
        if key not in allowed_keys:
            failures.append(f"ui1r2r2_preference_key_missing:{key}")
    if display_prefs.get("no_trade_state_persisted") is not True or display_prefs.get("no_private_state_persisted") is not True:
        failures.append("ui1r2r2_preference_private_state_guard_missing")

    header_menu = _read_json(ui_dir / "ui1r2r2_header_menu.report.json")
    if header_menu.get("strict_menu_only_header_chrome") is not True:
        failures.append("ui1r2r2_header_not_strict_menu_only")
    header_match = re.search(r"<header\b.*?</header>", html_text, flags=re.IGNORECASE | re.DOTALL)
    header_markup = header_match.group(0) if header_match else ""
    if not header_markup:
        failures.append("ui1r2r2_header_markup_missing")
    for forbidden in header_menu.get("closed_header_forbidden_visible_text", []):
        if forbidden in header_markup:
            failures.append(f"ui1r2r2_closed_header_forbidden_text:{forbidden}")
    for snippet in (
        'data-header-chrome="menu-only"',
        'id="ownerOptionsToggle"',
        'aria-expanded="false"',
        'aria-controls="ownerOptionsPanel"',
        'id="ownerOptionsPanel"',
        'data-options-menu="owner-display-preferences"',
        'data-text-size-choice="small"',
        'data-text-size-choice="default"',
        'data-text-size-choice="large"',
        'data-text-size-choice="extra_large"',
        "TEXT_SIZE_STORAGE_KEY",
        "setTextSize",
        "initOptionsMenu",
    ):
        if snippet not in combined:
            failures.append(f"ui1r2r2_menu_renderer_snippet_missing:{snippet}")
    if re.search(r"<section class=\"status-strip\"", html_text):
        failures.append("ui1r2r2_status_strip_permanent_outside_menu")

    parity = _read_json(ui_dir / "ui1r2r2_mode_action_parity.report.json")
    if parity.get("guided_advanced_non_developer_action_parity") is not True:
        failures.append("ui1r2r2_guided_advanced_action_parity_missing")
    if parity.get("guided_non_developer_next_step_ids") != parity.get("advanced_non_developer_next_step_ids"):
        failures.append("ui1r2r2_guided_advanced_next_steps_differ")
    if parity.get("guided_adds_coaching_not_capability_removal") is not True:
        failures.append("ui1r2r2_guided_coaching_rule_missing")

    owner_copy = _read_json(ui_dir / "ui1r2r2_owner_readable_copy.report.json")
    if owner_copy.get("centralized_copy_adapter") is not True:
        failures.append("ui1r2r2_owner_copy_not_centralized")
    if owner_copy.get("raw_refs_available_in_developer_or_collapsed_technical_details") is not True:
        failures.append("ui1r2r2_raw_refs_not_preserved")
    for pattern in owner_copy.get("guided_advanced_raw_pattern_rejections", []):
        if not pattern:
            failures.append("ui1r2r2_owner_copy_empty_raw_pattern")

    chat_preview = _read_json(ui_dir / "ui1r2r2_chat_intent_preview.report.json")
    if chat_preview.get("primary_button_label") != "Send":
        failures.append("ui1r2r2_chat_send_label_bad")
    if chat_preview.get("send_button_attached_to_composer") is not True:
        failures.append("ui1r2r2_chat_send_not_attached")
    for intent in (
        "TRADE_CHECK_REQUEST",
        "RESEARCH_ANALYSIS_REQUEST",
        "FORMULA_EXTRACTION_REQUEST",
        "QKU_MATERIALIZATION_REQUEST",
        "QUANTUM_STRUCTURE_MAPPING_REQUEST",
        "NO_TRADE_EXPLANATION_REQUEST",
        "PARAMETER_TUNING_REQUEST",
        "EDGE_ALPHA_REVIEW_REQUEST",
        "AGENT_DISAGREEMENT_REQUEST",
        "REPLAY_PREVIEW_REQUEST",
        "PAPER_PREVIEW_REQUEST",
        "UNKNOWN_OWNER_REQUEST_NEEDS_CLARIFICATION",
    ):
        if intent not in chat_preview.get("recognized_intent_families", []):
            failures.append(f"ui1r2r2_chat_intent_missing:{intent}")
    for snippet in (
        'data-chat-send-attached="true"',
        'data-chat-send-button="true">Send<',
        "Ctrl+Enter = Send",
        "I need a market, trade idea, source link, formula, or research question to route this.",
        "data-unknown-intent-chips",
    ):
        if snippet not in combined:
            failures.append(f"ui1r2r2_chat_renderer_snippet_missing:{snippet}")

    workbench_form = _read_json(ui_dir / "ui1r2r2_workbench_form.generated.json")
    required_workbench_fields = {
        "market_event",
        "venue",
        "side",
        "objective",
        "max_budget",
        "max_loss",
        "hold_duration",
        "urgency",
        "entry_preference",
        "exit_preference",
        "maker_taker_preference",
        "source_thesis_url",
        "target_price_probability",
        "stop_exit_preference",
        "source_family",
        "route_selector",
    }
    present_fields = {row.get("field_id") for row in workbench_form.get("field_catalog", [])}
    if not required_workbench_fields <= present_fields:
        failures.append("ui1r2r2_workbench_required_fields_missing")
    for option_source in (
        "venue",
        "side",
        "objective",
        "urgency",
        "entry_preference",
        "exit_preference",
        "maker_taker_preference",
        "source_family",
        "route_selector",
    ):
        if option_source not in workbench_form.get("option_catalog", {}):
            failures.append(f"ui1r2r2_workbench_option_source_missing:{option_source}")
    if workbench_form.get("all_selectors_use_central_option_catalog") is not True:
        failures.append("ui1r2r2_workbench_option_catalog_not_central")
    for snippet in (
        "data-workbench-field",
        "data-workbench-local-status-strip",
        "TradePlanCandidatePreviewV1",
        "workbenchPreviewGrid",
        "updateWorkbenchPreview",
    ):
        if snippet not in combined:
            failures.append(f"ui1r2r2_workbench_renderer_snippet_missing:{snippet}")

    next_step_report = _read_json(ui_dir / "ui1r2r2_action_next_step.report.json")
    if next_step_report.get("router_id") != "OwnerNextStepRouter":
        failures.append("ui1r2r2_next_step_router_bad")
    if next_step_report.get("enabled_options_route_to_next_step") is not True:
        failures.append("ui1r2r2_enabled_actions_not_routed")
    if next_step_report.get("no_runtime_queue_created") is not True:
        failures.append("ui1r2r2_next_step_runtime_queue_created")

    r2r2_authority = _read_json(ui_dir / "ui1r2r2_authority_boundary.report.json")
    for key in (
        "no_SVC1_runtime",
        "no_live_LLM",
        "no_real_QTT_agent_execution",
        "no_real_replay_paper_live_execution",
        "no_connector_private_or_cash_account_reads",
        "no_source_truth_acceptance",
        "no_direct_venue_submit",
        "no_Execution_Router_release",
        "no_QTT_SHA_or_AtomicRows_hash_authority",
        "no_profit_guarantee",
    ):
        if r2r2_authority.get(key) is not True:
            failures.append(f"ui1r2r2_authority_guard_missing:{key}")

    no_orphan = _read_json(ui_dir / "ui1r2r2_no_orphan_central_routes.report.json")
    for key in (
        "no_independent_dashboard_truth_files",
        "no_chat_only_command_grammar",
        "no_workbench_only_route_ids",
        "no_mobile_only_feature_list",
        "all_new_values_route_or_gap",
    ):
        if no_orphan.get(key) is not True:
            failures.append(f"ui1r2r2_no_orphan_guard_missing:{key}")

    source_candidate = _read_json(ui_dir / "ui1r2r2_source_agnostic_candidate_only.report.json")
    if source_candidate.get("candidate_or_provisional_only") is not True:
        failures.append("ui1r2r2_source_candidate_not_candidate_only")
    if source_candidate.get("non_official_information_not_source_truth") is not True:
        failures.append("ui1r2r2_non_official_source_truth_allowed")

    pref_guard = _read_json(ui_dir / "ui1r2r2_preference_storage_guard.report.json")
    if pref_guard.get("localStorage_limited_to_non_secret_UI_preferences") is not True:
        failures.append("ui1r2r2_localstorage_not_limited_to_ui_prefs")
    if pref_guard.get("no_trade_state_in_localStorage") is not True:
        failures.append("ui1r2r2_trade_state_localstorage_allowed")

    mobile_r2r2 = _read_json(ui_dir / "ui1r2r2_mobile_responsive.report.json")
    for key in (
        "closed_header_menu_only_by_default",
        "trading_content_in_first_viewport",
        "no_horizontal_overflow_default_large_extra_large",
        "chat_and_workbench_reachable",
        "send_visible_on_mobile",
        "workbench_fields_stack_correctly",
        "no_separate_mobile_state_model",
    ):
        if mobile_r2r2.get(key) is not True:
            failures.append(f"ui1r2r2_mobile_guard_missing:{key}")

    evidence_r2r2 = _read_json(ui_dir / "ui1r2r2_evidence_spine.report.json")
    if evidence_r2r2.get("every_repaired_route_preserves_or_gap_routes_spine") is not True:
        failures.append("ui1r2r2_evidence_spine_not_preserved")
    if evidence_r2r2.get("no_fake_runtime_output") is not True or evidence_r2r2.get("no_fake_quantum_advantage") is not True:
        failures.append("ui1r2r2_fake_evidence_guard_missing")

    owner_settings = _read_json(ui_dir / "ui1r2r3_owner_settings.generated.json")
    if owner_settings.get("settings_model_id") != "OwnerSettingsV1":
        failures.append("ui1r2r3_owner_settings_model_bad")
    if owner_settings.get("settings_center_id") != "OwnerSettingsCenter":
        failures.append("ui1r2r3_settings_center_missing")
    if owner_settings.get("localStorage_key") != OWNER_SETTINGS_STORAGE_KEY:
        failures.append("ui1r2r3_owner_settings_storage_key_bad")
    present_sections = {row.get("owner_label") for row in owner_settings.get("sections", [])}
    if set(OWNER_SETTINGS_SECTIONS) - present_sections:
        failures.append("ui1r2r3_settings_sections_missing")
    if owner_settings.get("trading_preferences_preview_only") is not True:
        failures.append("ui1r2r3_trading_preferences_not_preview_only")
    allowed_r2r3_keys = set(owner_settings.get("allowed_localStorage_keys", []))
    for key in {
        OWNER_SETTINGS_STORAGE_KEY,
        THEME_STORAGE_KEY,
        EXPERIENCE_MODE_STORAGE_KEY,
        GUIDANCE_DENSITY_STORAGE_KEY,
        TEXT_SIZE_STORAGE_KEY,
        TECHNICAL_DETAILS_STORAGE_KEY,
        ENTER_TO_SEND_STORAGE_KEY,
    }:
        if key not in allowed_r2r3_keys:
            failures.append(f"ui1r2r3_settings_key_missing:{key}")

    navigation = _read_json(ui_dir / "ui1r2r3_navigation_sidebar_search.report.json")
    if navigation.get("collapsible_sidebar") is not True:
        failures.append("ui1r2r3_sidebar_not_collapsible")
    if navigation.get("developer_nav_hidden_outside_developer_or_technical_details") is not True:
        failures.append("ui1r2r3_developer_nav_not_hidden")
    top_results = navigation.get("required_top_results", {})
    for query in ("chat", "agent", "workbench", "qku", "formula", "portfolio", "decision", "research", "quantum"):
        if query not in top_results:
            failures.append(f"ui1r2r3_search_top_result_missing:{query}")

    copy_actions = _read_json(ui_dir / "ui1r2r3_owner_copy_card_audience_actions.report.json")
    if copy_actions.get("all_cards_have_audience_classification") is not True:
        failures.append("ui1r2r3_card_audience_missing")
    default_card = copy_actions.get("default_owner_card_contract", {})
    if default_card.get("one_primary_action") is not True or default_card.get("more_actions_menu") is not True:
        failures.append("ui1r2r3_default_card_action_declutter_bad")

    chat_guide = _read_json(ui_dir / "ui1r2r3_chat_guide.report.json")
    if len(chat_guide.get("chat_presets", [])) < 8:
        failures.append("ui1r2r3_chat_presets_missing")
    if chat_guide.get("qtt_guide_reuses_chat_state") is not True or chat_guide.get("qtt_guide_second_transcript_store_created") is not False:
        failures.append("ui1r2r3_qtt_guide_state_bad")

    chart_policy = _read_json(ui_dir / "ui1r2r3_chart_policy.report.json")
    for key in (
        "hover_touch_focus_enabled",
        "nearest_point_highlight",
        "crosshair_or_vertical_guide",
        "tooltip_value_panel",
        "axis_labels_units_ticks_or_pending_placeholders",
        "selected_range_state",
        "no_fake_PnL_cash_fill_order_live_values",
    ):
        if chart_policy.get(key) is not True:
            failures.append(f"ui1r2r3_chart_policy_missing:{key}")

    drawers = _read_json(ui_dir / "ui1r2r3_education_drawers.generated.json")
    drawer_kinds = {row.get("drawer_kind") for row in drawers.get("drawer_actions", [])}
    if {"explain", "learn", "why", "chart_drilldown", "tca_breakdown", "technical_details"} - drawer_kinds:
        failures.append("ui1r2r3_drawer_kinds_missing")
    signatures = [row.get("content_signature") for row in drawers.get("drawer_actions", [])]
    if len(signatures) != len(set(signatures)):
        failures.append("ui1r2r3_drawer_signatures_not_unique")

    theme_interaction = _read_json(ui_dir / "ui1r2r3_theme_interaction_accessibility.report.json")
    if set(THEME_MODES) - set(theme_interaction.get("supported_theme_presets", [])):
        failures.append("ui1r2r3_theme_presets_missing")
    if theme_interaction.get("owner_highlight_colors_editable") is not True or theme_interaction.get("contrast_validation_status") != "PASS":
        failures.append("ui1r2r3_theme_interaction_accessibility_bad")

    workbench_r2r3 = _read_json(ui_dir / "ui1r2r3_workbench_options_ranges.generated.json")
    if workbench_r2r3.get("all_options_have_source_category") is not True or workbench_r2r3.get("all_numeric_ranges_have_source_category") is not True:
        failures.append("ui1r2r3_workbench_source_categories_bad")
    for option_source in ("market_family", "event_category", "specific_event_route", "venue", "duration_unit"):
        if option_source not in workbench_r2r3.get("option_catalog", {}):
            failures.append(f"ui1r2r3_workbench_option_source_missing:{option_source}")
    for range_id in ("max_budget", "max_loss", "target_price_probability", "hold_duration", "portfolio_exposure"):
        if range_id not in workbench_r2r3.get("range_policy", {}):
            failures.append(f"ui1r2r3_workbench_range_missing:{range_id}")

    no_scattering = _read_json(ui_dir / "ui1r2r3_no_runtime_no_scattering.report.json")
    for key in (
        "no_SVC1_runtime",
        "no_live_LLM",
        "no_real_QTT_agent_execution",
        "no_real_replay_paper_live_execution",
        "no_connector_private_or_cash_account_reads",
        "no_source_truth_acceptance",
        "no_direct_venue_submit",
        "no_Execution_Router_release",
        "no_QTT_SHA_or_AtomicRows_hash_authority",
        "no_profit_guarantee",
        "no_new_QKU_formula_materialization_engine",
        "no_separate_workbench_option_arrays",
        "no_separate_chat_preset_arrays",
        "no_second_settings_store",
        "renderer_consumes_central_tokens_options_ranges_copy_actions",
    ):
        if no_scattering.get(key) is not True:
            failures.append(f"ui1r2r3_no_scattering_guard_missing:{key}")

    online_audit = _read_json(ui_dir / "ui1r2r3_online_owner_copy_audit.report.json")
    if online_audit.get("source_truth_created") is not False or online_audit.get("forbidden_owner_facing_machine_labels_absent_from_guided_advanced") is not True:
        failures.append("ui1r2r3_online_or_copy_audit_bad")

    for snippet in (
        "OWNER_SETTINGS_STORAGE_KEY",
        "OwnerSettings",
        "data-settings-center=\"OwnerSettingsV1\"",
        "data-owner-setting",
        "data-chat-preset-dropdown=\"OwnerOptionCatalogV1.chat_presets\"",
        "data-qtt-guide-route=\"existing-chat-action-system\"",
        "data-owner-drawer-action",
        "data-content-signature",
        "data-chart-interaction=\"OwnerChartInteractionPolicyV1\"",
        "provider_pending_no_value",
        "data-workbench-inline-validation",
        "data-source-category",
        "data-default-card-contract=\"one-primary-plus-more-actions\"",
        "data-secondary-actions-collapsed=\"true\"",
        "ownerSearchResults",
        "sidebarCollapseToggle",
    ):
        if snippet not in combined:
            failures.append(f"ui1r2r3_renderer_snippet_missing:{snippet}")

    return tuple(failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="docs/master_plan/generated/pr169_dash1")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    base = (Path(args.repo_root) / args.base).resolve()
    failures = validate(base)
    if failures:
        print("PR169_DASH1_UI1_OWNER_DASHBOARD_UI_VALIDATION_FAILED")
        for failure in failures[:200]:
            print(failure)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
