from __future__ import annotations

from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc, ui_text


def test_ui1r2r3_navigation_sidebar_search_owner_destinations() -> None:
    report = ui_doc("ui1r2r3_navigation_sidebar_search.report.json")
    text = ui_text()
    assert report["collapsible_sidebar"] is True
    assert report["collapsed_state_persists_only_ui_preference"] is True
    assert report["developer_nav_hidden_outside_developer_or_technical_details"] is True
    assert "sidebarCollapseToggle" in text
    assert "ownerSearchResults" in text
    for query in ("chat", "agent", "workbench", "qku", "formula", "portfolio", "decision", "research", "quantum"):
        assert query in report["required_top_results"]
    assert report["search_results_ranked_destinations"] is True
    assert report["search_selection_scrolls_focuses_target"] is True


def test_ui1r2r3_owner_copy_card_audience_and_action_declutter() -> None:
    report = ui_doc("ui1r2r3_owner_copy_card_audience_actions.report.json")
    text = ui_text()
    assert report["all_cards_have_audience_classification"] is True
    assert set(report["card_audience_classes"]) >= {"owner_facing", "developer_facing", "agent_facing", "system_registry", "technical_evidence"}
    assert report["default_owner_card_contract"]["one_primary_action"] is True
    assert report["default_owner_card_contract"]["more_actions_menu"] is True
    assert "data-default-card-contract=\"one-primary-plus-more-actions\"" in text
    assert "data-secondary-actions-collapsed=\"true\"" in text
    for stale in ("Guided Owner Coach</h3>", "Review execution-adjusted trade metrics</h3>", "Tell me what matters</h3>"):
        assert stale not in text
    assert "QTT Coach" in text
    assert "Trade Metrics" in text
    assert "Key Insights" in text


def test_ui1r2r3_chat_presets_and_qtt_guide_local_only() -> None:
    report = ui_doc("ui1r2r3_chat_guide.report.json")
    text = ui_text()
    assert len(report["chat_presets"]) >= 8
    assert all(row["selection_fills_composer"] and not row["selection_auto_submits"] for row in report["chat_presets"])
    assert report["qtt_guide_reuses_chat_state"] is True
    assert report["qtt_guide_second_transcript_store_created"] is False
    assert report["live_LLM_call_allowed"] is False
    assert "data-chat-preset-dropdown=\"OwnerOptionCatalogV1.chat_presets\"" in text
    assert "data-qtt-guide-route=\"existing-chat-action-system\"" in text


def test_ui1r2r3_interactive_charts_no_fake_values() -> None:
    report = ui_doc("ui1r2r3_chart_policy.report.json")
    text = ui_text()
    for key in ("hover_touch_focus_enabled", "nearest_point_highlight", "crosshair_or_vertical_guide", "tooltip_value_panel", "axis_labels_units_ticks_or_pending_placeholders", "selected_range_state"):
        assert report[key] is True
    assert report["no_fake_PnL_cash_fill_order_live_values"] is True
    assert "data-chart-interaction=\"OwnerChartInteractionPolicyV1\"" in text
    assert "provider_pending_no_value" in text
    assert "Value: provider receipts pending" in text
    assert "no fake PnL, cash, fill, order, or live values shown" in text


def test_ui1r2r3_card_specific_education_distinct_drawers() -> None:
    drawers = ui_doc("ui1r2r3_education_drawers.generated.json")
    text = ui_text()
    kinds = {row["drawer_kind"] for row in drawers["drawer_actions"]}
    assert {"explain", "learn", "why", "chart_drilldown", "tca_breakdown", "technical_details"} <= kinds
    signatures = [row["content_signature"] for row in drawers["drawer_actions"]]
    assert len(signatures) == len(set(signatures))
    assert drawers["raw_refs_limited_to_technical_details"] is True
    assert "data-selected-card-id" in text
    assert "data-selected-action-id" in text
    assert "data-content-signature" in text


def test_ui1r2r3_theme_tokens_interaction_states_accessibility() -> None:
    report = ui_doc("ui1r2r3_theme_interaction_accessibility.report.json")
    text = ui_text()
    assert {"DARK_PRO", "MIDNIGHT_BLUE", "SLATE", "LIGHT_PRO", "LOW_GLARE", "HIGH_CONTRAST", "CUSTOM"} <= set(report["supported_theme_presets"])
    assert report["owner_highlight_colors_editable"] is True
    assert report["contrast_validation_status"] == "PASS"
    assert report["no_component_hardcoded_color_logic"] is True
    for state in ("input_required", "review_required", "provider_pending", "technical_only", "high_confirmation"):
        assert state in {row["state"] for row in report["interaction_states"]}
        assert f'data-interaction-state="{state}"' in text or state in text
    assert "--owner-input-required" in text


def test_ui1r2r3_settings_center_owner_settings_single_source() -> None:
    settings = ui_doc("ui1r2r3_owner_settings.generated.json")
    text = ui_text()
    assert settings["settings_model_id"] == "OwnerSettingsV1"
    assert settings["settings_center_id"] == "OwnerSettingsCenter"
    assert settings["single_safe_persistence_adapter"] is True
    assert settings["trading_preferences_preview_only"] is True
    assert settings["no_source_truth_or_order_authority"] is True
    sections = {row["owner_label"] for row in settings["sections"]}
    assert {"Appearance", "Colors", "Layout", "Charts", "Workbench", "Chat", "Dashboard", "Trading Preferences", "Accessibility", "Keyboard Shortcuts", "About"} <= sections
    assert "data-settings-center=\"OwnerSettingsV1\"" in text
    assert "OWNER_SETTINGS_STORAGE_KEY" in text
    assert "data-owner-setting" in text


def test_ui1r2r3_workbench_selectors_other_fields_and_ranges() -> None:
    workbench = ui_doc("ui1r2r3_workbench_options_ranges.generated.json")
    text = ui_text()
    option_catalog = workbench["option_catalog"]
    for source in ("market_family", "event_category", "specific_event_route", "venue", "side", "objective", "urgency", "entry_preference", "exit_preference", "maker_taker_preference", "source_family", "route_selector", "duration_unit"):
        assert source in option_catalog
    assert any(option["option_id"] == "other" for option in option_catalog["market_family"])
    assert any(option["option_id"] == "other" for option in option_catalog["event_category"])
    assert "data-hidden-until-other=\"true\"" in text
    for range_id in ("max_budget", "max_loss", "hold_duration", "target_price_probability", "portfolio_exposure"):
        assert range_id in workbench["range_policy"]
    assert "data-workbench-inline-validation=\"true\"" in text


def test_ui1r2r3_workbench_option_range_source_categories() -> None:
    workbench = ui_doc("ui1r2r3_workbench_options_ranges.generated.json")
    assert set(workbench["source_categories_allowed"]) == {"existing_registry_value", "master_plan_static_value", "safe_ui_default", "candidate_owner_custom", "provider_pending"}
    assert workbench["all_options_have_source_category"] is True
    assert workbench["all_numeric_ranges_have_source_category"] is True
    assert workbench["custom_other_candidate_only"] is True
    assert workbench["unknown_bounds_are_dependencies_not_truth"] is True
    assert workbench["no_connector_semantics_or_order_authority"] is True


def test_ui1r2r3_dropdowns_accordions_reduce_text_clutter() -> None:
    text = ui_text()
    assert "data-chat-preset-dropdown" in text
    assert "More actions" in text
    assert "data-primary-card-action=\"true\"" in text
    assert "data-secondary-actions-collapsed=\"true\"" in text
    assert "data-default-card-contract=\"one-primary-plus-more-actions\"" in text


def test_ui1r2r3_no_runtime_authority_no_scattered_systems_no_qku_scope_creep() -> None:
    report = ui_doc("ui1r2r3_no_runtime_no_scattering.report.json")
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
    ):
        assert report[key] is True


def test_ui1r2r3_online_reference_scope_and_owner_copy_grep_audit() -> None:
    audit = ui_doc("ui1r2r3_online_owner_copy_audit.report.json")
    data = boot_data()
    assert audit["online_sources_used"] == []
    assert audit["source_truth_created"] is False
    assert audit["connector_semantics_created"] is False
    assert audit["trading_range_authority_created"] is False
    assert audit["QKU_formula_materialization_created"] is False
    assert audit["live_readiness_authority_created"] is False
    assert audit["forbidden_owner_facing_machine_labels_absent_from_guided_advanced"] is True
    assert data["ui1r2r3_owner_product_polish"]["no_new_QKU_formula_materialization_engine"] is True
