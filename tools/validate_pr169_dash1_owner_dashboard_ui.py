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
    MOBILE_TABS,
    REQUIRED_TOP_LEVEL_KEYS,
    SEMANTIC_COLORS,
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
    if set(theme.get("supported_modes", [])) != {"DARK", "LIGHT"}:
        failures.append("theme_modes_not_dark_light")
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
