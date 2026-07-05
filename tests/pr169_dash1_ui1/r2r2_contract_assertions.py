from __future__ import annotations

import re

from tools.build_pr169_dash1_owner_dashboard_ui import (
    AUTHORITY_BOUNDARY,
    DISPLAY_TEXT_SIZES,
    ENTER_TO_SEND_STORAGE_KEY,
    EXPERIENCE_MODE_STORAGE_KEY,
    GUIDANCE_DENSITY_STORAGE_KEY,
    TECHNICAL_DETAILS_STORAGE_KEY,
    TEXT_SIZE_STORAGE_KEY,
    THEME_STORAGE_KEY,
)

from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc, ui_text


def _combined() -> str:
    return ui_text()


def _html_header() -> str:
    match = re.search(r"<header\b.*?</header>", _combined(), flags=re.IGNORECASE | re.DOTALL)
    assert match is not None
    return match.group(0)


def assert_header_menu_textsize_mobile() -> None:
    report = ui_doc("ui1r2r2_header_menu.report.json")
    prefs = ui_doc("ui1r2r2_display_preferences.generated.json")
    text = _combined()
    header = _html_header()
    assert report["strict_menu_only_header_chrome"] is True
    assert 'data-header-chrome="menu-only"' in header
    assert 'id="ownerOptionsToggle"' in header
    assert 'aria-expanded="false"' in header
    assert 'aria-controls="ownerOptionsPanel"' in header
    for forbidden in report["closed_header_forbidden_visible_text"]:
        assert forbidden not in header
    assert 'id="ownerOptionsPanel"' in text
    assert 'data-options-menu="owner-display-preferences"' in text
    assert set(prefs["text_size"]["allowed"]) == set(DISPLAY_TEXT_SIZES)
    for size in DISPLAY_TEXT_SIZES:
        assert f'data-text-size-choice="{size}"' in text
    assert "setTextSize" in text
    assert "--qtt-type-scale" in text
    assert "<section class=\"status-strip\"" not in text


def assert_experience_modes_action_parity() -> None:
    report = ui_doc("ui1r2r2_mode_action_parity.report.json")
    assert report["owner_role_is_not_a_mode"] is True
    assert report["guided_capability_rule"] == "full capability plus more coaching"
    assert report["guided_advanced_non_developer_action_parity"] is True
    assert report["guided_non_developer_next_step_ids"] == report["advanced_non_developer_next_step_ids"]
    assert report["developer_raw_refs_visible_only_when_selected_or_opened"] is True
    assert "NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS" in report["guided_non_developer_next_step_ids"]
    assert "NEXT_STEP_REQUEST_PAPER_PREVIEW" in report["advanced_non_developer_next_step_ids"]


def assert_owner_readable_copy() -> None:
    report = ui_doc("ui1r2r2_owner_readable_copy.report.json")
    copy_map = ui_doc("ui1r2_copy_map.generated.json")
    assert report["centralized_copy_adapter"] is True
    assert report["owner_readable_copy_map_ref"] == "ui1r2_copy_map.generated.json"
    assert copy_map["presentation_layer_id"] == "OwnerPresentationLayer"
    for pattern in (
        "DASH1_FEATURE_",
        "VISIBLE_EMPTY_STATE_PROVIDER_PENDING",
        "CONTRACT_DEFINED_PROVIDER_PENDING",
        "SYSTEM CONTRACT",
        "Raw refs",
        "Linked refs",
    ):
        assert pattern in report["guided_advanced_raw_pattern_rejections"]
    assert report["raw_refs_available_in_developer_or_collapsed_technical_details"] is True


def assert_chat_send_and_intent_preview() -> None:
    report = ui_doc("ui1r2r2_chat_intent_preview.report.json")
    text = _combined()
    assert report["plain_english_first"] is True
    assert report["primary_button_label"] == "Send"
    assert report["send_button_attached_to_composer"] is True
    assert report["default_enter_behavior"] == "NEWLINE"
    assert report["ctrl_enter_submits_local_preview"] is True
    assert report["enter_to_send_default_enabled"] is False
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
        assert intent in report["recognized_intent_families"]
    assert 'data-chat-send-attached="true"' in text
    assert 'data-chat-send-button="true">Send<' in text
    assert "Ctrl+Enter = Send" in text
    assert report["unknown_owner_facing_message"] in text
    assert "Unknown Owner Request Needs Clarification" not in text


def assert_workbench_form_selectors_preview() -> None:
    workbench = ui_doc("ui1r2r2_workbench_form.generated.json")
    text = _combined()
    required_fields = {
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
    assert required_fields <= {row["field_id"] for row in workbench["field_catalog"]}
    assert workbench["central_option_catalog_id"] == "OwnerInputOptionCatalogV1"
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
        assert option_source in workbench["option_catalog"]
    assert workbench["local_preview_output"]["preview_object_type"] == "TradePlanCandidatePreviewV1"
    assert workbench["runtime_side_effect_allowed"] is False
    assert "data-workbench-field" in text
    assert "workbenchPreviewGrid" in text


def assert_action_next_step_routing() -> None:
    report = ui_doc("ui1r2r2_action_next_step.report.json")
    assert report["router_id"] == "OwnerNextStepRouter"
    assert report["enabled_options_route_to_next_step"] is True
    assert report["chip_card_dropdown_workbench_actions_share_router"] is True
    assert report["disabled_provider_pending_actions_explain_safe_alternative"] is True
    assert report["local_preview_only"] is True
    assert report["no_runtime_queue_created"] is True
    for route_id in (
        "NEXT_STEP_SEND_TO_TRADE_WORKBENCH",
        "NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS",
        "NEXT_STEP_REQUEST_REPLAY_PREVIEW",
        "NEXT_STEP_REQUEST_PAPER_PREVIEW",
        "NEXT_STEP_SHOW_QKU_FORMULA_ROUTES",
        "NEXT_STEP_EXPLAIN_NO_TRADE",
        "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN",
    ):
        assert route_id in report["next_step_ids"]


def assert_authority_boundary_no_runtime() -> None:
    report = ui_doc("ui1r2r2_authority_boundary.report.json")
    assert report["authority_boundary_ref"] == AUTHORITY_BOUNDARY
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
        assert report[key] is True


def assert_no_orphan_central_routes() -> None:
    report = ui_doc("ui1r2r2_no_orphan_central_routes.report.json")
    data = boot_data()
    assert report["central_state_ref"] == "OwnerDashboardStateV1"
    assert report["surface_resolver_ref"] == "OwnerSurfaceResolver"
    assert report["action_registry_ref"] == "OwnerActionRegistryV1"
    assert report["next_step_router_ref"] == "OwnerNextStepRouter"
    assert report["no_independent_dashboard_truth_files"] is True
    assert report["no_chat_only_command_grammar"] is True
    assert report["no_workbench_only_route_ids"] is True
    assert report["no_mobile_only_feature_list"] is True
    assert data["ui1r2r2_no_orphan_central_routes"]["all_new_values_route_or_gap"] is True


def assert_source_agnostic_candidate_only() -> None:
    report = ui_doc("ui1r2r2_source_agnostic_candidate_only.report.json")
    assert report["candidate_or_provisional_only"] is True
    assert report["non_official_information_not_source_truth"] is True
    assert report["no_connector_semantics"] is True
    assert report["no_cash_truth"] is True
    assert report["no_runtime_authority"] is True
    assert report["no_trading_evidence_promotion"] is True
    assert any("PDF" in item for item in report["accepted_candidate_input_families"])
    assert any("social" in item for item in report["accepted_candidate_input_families"])


def assert_preferences_no_private_state() -> None:
    report = ui_doc("ui1r2r2_preference_storage_guard.report.json")
    assert set(report["allowed_localStorage_keys"]) == {
        THEME_STORAGE_KEY,
        EXPERIENCE_MODE_STORAGE_KEY,
        GUIDANCE_DENSITY_STORAGE_KEY,
        TEXT_SIZE_STORAGE_KEY,
        TECHNICAL_DETAILS_STORAGE_KEY,
        ENTER_TO_SEND_STORAGE_KEY,
    }
    assert report["localStorage_limited_to_non_secret_UI_preferences"] is True
    assert report["no_trade_state_in_localStorage"] is True
    assert report["no_private_or_order_or_receipt_state_in_localStorage"] is True
    text = _combined()
    for forbidden in ("order_state", "cash", "account", "credential", "token"):
        assert f"localStorage.setItem(\"{forbidden}" not in text


def assert_mobile_responsive_reachability() -> None:
    report = ui_doc("ui1r2r2_mobile_responsive.report.json")
    text = _combined()
    for key in (
        "closed_header_menu_only_by_default",
        "menu_options_open_and_close",
        "trading_content_in_first_viewport",
        "no_horizontal_overflow_default_large_extra_large",
        "chat_and_workbench_reachable",
        "send_visible_on_mobile",
        "workbench_fields_stack_correctly",
        "dropdowns_usable_in_viewport",
        "no_separate_mobile_state_model",
    ):
        assert report[key] is True
    assert "@media (max-width: 767px)" in text
    assert ".owner-options-panel" in text
    assert "chat-composer-row" in text
    assert "workbench-fields" in text


def assert_qku_formula_agent_evidence_spine() -> None:
    report = ui_doc("ui1r2r2_evidence_spine.report.json")
    required = set(report["required_evidence_spine_refs"])
    for field in (
        "execution_adjusted_rank_ref",
        "TCA_decomposition_ref",
        "portfolio_marginal_utility_ref",
        "no_trade_comparator_and_reoptimization_route",
        "quantum_structural_readiness_ref",
        "DAG_upstream_downstream_route_ref",
        "PR165_D2_agent_role_refs_or_gap",
        "QKU_formula_refs_or_gap",
    ):
        assert field in required
    assert report["every_repaired_route_preserves_or_gap_routes_spine"] is True
    assert report["no_fake_runtime_output"] is True
    assert report["no_fake_quantum_advantage"] is True
