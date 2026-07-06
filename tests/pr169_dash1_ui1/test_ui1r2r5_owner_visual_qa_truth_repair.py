from __future__ import annotations

from pathlib import Path

from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc, ui_text, walk


REQUIRED_SCREENSHOTS = {
    ".tmp/ui1r2r5_workbench_input_state_before_valid_entry_targeted.png",
    ".tmp/ui1r2r5_workbench_input_state_after_valid_entry_targeted.png",
    ".tmp/ui1r2r5_workbench_other_custom_market_field_targeted.png",
    ".tmp/ui1r2r5_workbench_other_custom_event_field_targeted.png",
    ".tmp/ui1r2r5_settings_color_applied_to_workbench_inputs_targeted.png",
    ".tmp/ui1r2r5_owner_drawer_explain_no_raw_payload.png",
    ".tmp/ui1r2r5_owner_drawer_technical_details_payload_expanded.png",
    ".tmp/ui1r2r5_mobile_nav_no_overlap.png",
    ".tmp/ui1r2r5_mobile_more_overflow_open.png",
    ".tmp/ui1r2r5_chart_tooltip_visible_on_hover.png",
    ".tmp/ui1r2r5_chart_tooltip_hidden_after_mouseleave.png",
    ".tmp/ui1r2r5_chart_tooltip_hidden_after_escape.png",
    ".tmp/ui1r2r5_owner_copy_machine_labels_suppressed.png",
    ".tmp/ui1r2r5_more_actions_context_relevant.png",
    ".tmp/ui1r2r5_workflow_queue_targeted.png",
    ".tmp/ui1r2r5_receipt_preview_targeted.png",
    ".tmp/ui1r2r5_mobile_workbench_targeted_input_colors.png",
}


def r2r5_bundle() -> dict:
    return ui_doc("../ui1_r2_r5/owner_visual_qa_truth_repair.generated.json")


def r2r5_manifest() -> dict:
    return ui_doc("../ui1_r2_r5/centralization_manifest.generated.json")


def test_ui1r2r5_screenshot_targets_prove_named_features() -> None:
    bundle = r2r5_bundle()
    rows = {row["screenshot_path"]: row for row in bundle["screenshot_proof_registry"]}
    assert set(rows) == REQUIRED_SCREENSHOTS
    for path, row in rows.items():
        assert path.startswith(".tmp/ui1r2r5_")
        assert row["proof_selector_or_locator"]
        assert row["proof_text_or_state"]
        assert "target locator visible" in row["post_action_assertions"]
        assert "target locator intersects viewport" in row["post_action_assertions"]
        assert row["runtime_side_effect_allowed"] is False
        assert row["source_truth_created"] is False
        assert row["order_authority_created"] is False
    assert rows[".tmp/ui1r2r5_workbench_input_state_before_valid_entry_targeted.png"]["surface_id"] == "trade-workbench"
    assert "Owner Home" in rows[".tmp/ui1r2r5_workbench_other_custom_market_field_targeted.png"]["forbidden_visible_content"]
    assert rows[".tmp/ui1r2r5_workflow_queue_targeted.png"]["proof_text_or_state"] == "QTT Team Workflow Queue"
    assert rows[".tmp/ui1r2r5_receipt_preview_targeted.png"]["proof_text_or_state"] == "Audit Trail / Receipts Preview"


def test_ui1r2r5_owner_drawers_hide_raw_payload_until_technical_details() -> None:
    bundle = r2r5_bundle()
    policy = bundle["owner_drawer_policy"]
    text = ui_text()
    assert policy["raw_payload_visible_before_technical_details_expansion"] is False
    assert policy["technical_details_or_developer_may_show_raw_payload"] is True
    assert policy["primary_owner_sections_required"] == [
        "What this means",
        "Why it matters",
        "What you can do next",
        "What is missing",
        "Provider boundary",
    ]
    assert 'data-owner-drawer-primary-sections="true"' in text
    assert 'data-technical-details-collapsed="true"' in text
    assert "data-technical-details-expanded=" in text
    assert "rawTechnicalPayloadHtml" in text


def test_ui1r2r5_mobile_navigation_no_overlap_and_more_overflow() -> None:
    bundle = r2r5_bundle()
    nav = boot_data()["mobile_navigation"]
    policy = bundle["mobile_navigation_policy"]
    text = ui_text()
    assert policy["primary_tabs"] == ["Home", "Portfolio", "Trade", "Chat", "More"]
    assert policy["separate_mobile_system_created"] is False
    assert nav["mobile_primary_tab_count"] == 5
    assert nav["primary_tab_labels"] == ["Home", "Portfolio", "Trade", "Chat", "More"]
    assert nav["long_labels_moved_to_more_overflow"] is True
    assert nav["more_overflow_reuses_owner_surface_resolver"] is True
    assert nav["separate_mobile_state_model_created"] is False
    assert 'data-mobile-primary-count="5"' in text
    assert 'id="mobileMoreSheet"' in text
    for destination in ("Decision Queue", "Research", "Agent Operations", "QKU / Formula Routes", "Quantum Control Center", "Developer Mode"):
        assert destination in nav["overflow_tab_labels"]
        assert f'data-mobile-overflow-destination="{destination}"' in text


def test_ui1r2r5_workbench_field_and_other_custom_field_visual_proof() -> None:
    bundle = r2r5_bundle()
    text = ui_text()
    proof_text = "\n".join(str(value) for value in walk(bundle["screenshot_proof_registry"]))
    for phrase in (
        "Plain-English detail",
        "Input required",
        "Review required",
        "Custom market family",
        "Custom event category",
        "candidate_owner_custom",
    ):
        assert phrase in proof_text
    assert "data-owner-color-proof" in text
    assert "[data-workbench-field-shell='plain_english_detail'][data-owner-color-proof='input_required']" in proof_text
    assert "[data-workbench-field-shell='custom_market_family'][data-other-visible='true']" in proof_text
    assert "[data-workbench-field-shell='custom_event_category'][data-other-visible='true']" in proof_text


def test_ui1r2r5_owner_copy_suppresses_machine_labels() -> None:
    bundle = r2r5_bundle()
    copy_rows = {row["machine_label"]: row for row in bundle["owner_copy_suppression_map"]}
    text = ui_text()
    for machine, owner in {
        "Net Capital Cash Slot": "Net Capital",
        "Today Result Slot": "Today",
        "Provider Route: Metrics1": "Metrics provider pending",
        "Provider Route: Paper Loop": "Paper receipts pending",
        "PR165-D2 Routed Roles": "Agent roles routed",
        "No AGENT_ORCH/SVC runtime attached": "Agent runtime pending",
        "Runtime side effect: false": "No live action was run",
    }.items():
        assert copy_rows[machine]["owner_primary_label"] == owner
        assert copy_rows[machine]["technical_details_preserved"] is True
    assert 'document.body.dataset.ownerCopyCleanup = "r2-r5"' in text
    assert "cleanTechnicalText" in text
    assert ">Agent roles routed<" in text


def test_ui1r2r5_more_actions_context_relevant_and_not_noisy() -> None:
    bundle = r2r5_bundle()
    policy = bundle["more_actions_policy"]
    text = ui_text()
    assert policy["normal_owner_card_action_cap"] <= 5
    assert policy["chart_drilldown_hidden_on_non_chart_cards"] is True
    assert policy["tca_hidden_on_non_tca_cards"] is True
    assert policy["technical_actions_primary_owner_menu"] is False
    assert 'data-r2r5-action-cap="owner-contextual"' in text
    assert "normal_owner_card_action_cap" in text
    assert "chart_drilldown" in text


def test_ui1r2r5_chart_tooltip_hides_on_mouseleave_escape_and_route_change() -> None:
    bundle = r2r5_bundle()
    policy = bundle["chart_tooltip_policy"]
    text = ui_text()
    for trigger in ("pointer_leave_plot_or_card", "blur", "Escape", "range_change", "surface_navigation", "drawer_open"):
        assert policy[trigger] == "hide tooltip" or policy[trigger] == "hide transient tooltip"
    assert policy["hover_alone_pins_tooltip"] is False
    assert policy["fake_chart_values_created"] is False
    for snippet in (
        "hideChartTooltip",
        "hideAllChartTooltips",
        "pointerleave",
        "mouseleave",
        "event.key === \"Escape\"",
        "data-tooltip-state=\"hidden\"",
        "data-chart-tooltip-visible=\"false\"",
    ):
        assert snippet in text


def test_ui1r2r5_visual_qa_centralized_no_scatter_and_owned_prefix() -> None:
    bundle = r2r5_bundle()
    manifest = r2r5_manifest()
    assert bundle["central_bundle_id"] == "OwnerUXSemanticBundleV1"
    assert bundle["owned_generated_prefix"] == "docs/master_plan/generated/pr169_dash1/ui1_r2_r5/"
    assert bundle["one_builder"] == "tools/build_pr169_dash1_owner_dashboard_ui.py"
    assert bundle["one_validator"] == "tools/validate_pr169_dash1_owner_dashboard_ui.py"
    assert manifest["manifest_id"] == "UI1R2R5_CENTRALIZATION_MANIFEST"
    groups = {row["semantic_group"] for row in manifest["semantic_groups"]}
    assert {
        "screenshot_proof_targets",
        "drawer_payload_policy",
        "mobile_navigation_policy",
        "chart_tooltip_policy",
        "workbench_field_proof_targets",
        "owner_copy_suppression_policy",
        "more_actions_applicability_policy",
        "workflow_queue_projection",
        "receipt_preview_projection",
    } <= groups
    for row in manifest["semantic_groups"]:
        assert row["builder_consumer"] == "tools/build_pr169_dash1_owner_dashboard_ui.py"
        assert row["validator_consumer"] == "tools/validate_pr169_dash1_owner_dashboard_ui.py"
        assert row["runtime_side_effect_allowed"] is False
        assert row["source_truth_created"] is False
        assert row["order_authority_created"] is False


def test_ui1r2r5_source_of_truth_alias_and_changed_file_ownership() -> None:
    bundle = r2r5_bundle()
    aliases = bundle["alias_resolution_proof"]
    assert aliases["OwnerEducationCatalogV1"] == aliases["OwnerEducationCopyMap"]
    assert aliases["OwnerDefinitionGlossaryV1"] == aliases["OwnerEducationCopyMap"]
    assert aliases["tooltip state policy"] == aliases["OwnerChartInteractionPolicy"]
    assert aliases["mobile overflow policy"] == aliases["OwnerMobileNavigationModel"]
    assert aliases["Playwright proof target registry"] == aliases["OwnerScreenshotProofRegistry"]
    concepts = {row["conceptual_system"] for row in bundle["phase0_current_equivalent_mapping"]}
    assert "OwnerDashboardStateV1 / current equivalent" in concepts
    assert "OwnerActionRegistry / current equivalent" in concepts
    assert "OwnerScreenshotProofRegistry / Playwright proof target registry / visual QA target registry" in concepts
    changed = bundle["changed_file_ownership_audit"]
    assert changed
    for row in changed:
        assert row["file_path"]
        assert row["producer"]
        assert row["consumer"]
        assert row["validator_or_test_coverage"]
        assert row["orphan_risk"].startswith("low")
        assert row["runtime_authority_change"] is False
        assert row["source_truth_change"] is False
        assert row["order_authority_change"] is False
    for path in (
        "docs/master_plan/generated/pr169_dash1/ui1_r2_r5/owner_visual_qa_truth_repair.generated.json",
        "docs/master_plan/generated/pr169_dash1/ui1_r2_r5/centralization_manifest.generated.json",
    ):
        assert Path(path).exists()


def test_ui1r2r5_no_runtime_authority_and_currentization_preflight() -> None:
    bundle = r2r5_bundle()
    text = ui_text()
    boundary = bundle["no_runtime_authority"]
    for key in (
        "no_SVC1_runtime",
        "no_live_LLM",
        "no_online_search_runtime",
        "no_real_QTT_agent_execution",
        "no_real_replay_paper_live_execution",
        "no_connector_private_cash_reads",
        "no_source_truth_acceptance",
        "no_direct_venue_submit",
        "no_Execution_Router_release",
        "no_QTT_SHA_or_AtomicRows_hash_authority",
        "no_profit_guarantee",
    ):
        assert boundary[key] is True
    currentization = bundle["currentization_preflight"]
    assert currentization["new_exact_path_playwright_script_added"] is False
    assert currentization["stable_runner_extended_with_suite_arg"] is True
    assert currentization["wildcard_allowlists_added"] is False
    assert "fetch(" not in text
    assert "POST /orders" not in text
    assert "guaranteed positive profit" not in "\n".join(str(value) for value in walk(boot_data()))
