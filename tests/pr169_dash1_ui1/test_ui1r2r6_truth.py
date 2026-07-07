from __future__ import annotations

from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc, ui_text, walk


REQUIRED_R2R6_SCREENSHOTS = {
    ".tmp/r2r6_mobile_wb.png",
    ".tmp/r2r6_queue.png",
    ".tmp/r2r6_receipts.png",
    ".tmp/r2r6_other_market.png",
    ".tmp/r2r6_other_event.png",
    ".tmp/r2r6_more_actions.png",
    ".tmp/r2r6_color_proof.png",
    ".tmp/r2r6_theme_custom.png",
    ".tmp/r2r6_theme_applied.png",
    ".tmp/r2r6_density.png",
    ".tmp/r2r6_chart_axis.png",
    ".tmp/r2r6_chart_crosshair.png",
    ".tmp/r2r6_chart_grid.png",
    ".tmp/r2r6_chart_tooltip.png",
    ".tmp/r2r6_no_tooltips.png",
    ".tmp/r2r6_market_catalog.png",
}


def r2r6_bundle() -> dict:
    return ui_doc("../ui1_r2r6/truth.generated.json")


def r2r6_manifest() -> dict:
    return ui_doc("../ui1_r2r6/centralization_manifest.json")


def test_r2r6_settings_truth() -> None:
    bundle = r2r6_bundle()
    text = ui_text()
    control_ids = {row["setting_id"] for row in bundle["control_effect_proof_matrix"]}
    assert {
        "custom_theme_selected",
        "density_compact",
        "density_comfortable",
        "chart_axis_labels_enabled",
        "chart_crosshair_enabled",
        "chart_grid_lines_enabled",
        "chart_tooltips_enabled",
    } <= control_ids
    assert bundle["theme_truth_contract"]["custom_visible"] is True
    assert bundle["theme_truth_contract"]["custom_editor_required"] is True
    assert bundle["theme_truth_contract"]["custom_tokens_consumed_by_real_surface"] is True
    assert bundle["theme_truth_contract"]["custom_token_controls"]
    assert bundle["density_truth_contract"]["workbench_and_cards_consume_same_policy"] is True
    for snippet in (
        'data-custom-theme-editor="OwnerCustomThemeTokenEditorV1"',
        'data-owner-theme-consumer="custom-theme-token"',
        'data-owner-density-policy="OwnerDensityPolicyV1"',
        "readableTextFor",
        "--qtt-card-padding",
        "--qtt-card-gap",
        "--qtt-row-gap",
        "--qtt-control-height",
        "--qtt-section-padding",
    ):
        assert snippet in text


def test_r2r6_chart_truth() -> None:
    bundle = r2r6_bundle()
    text = ui_text()
    policy = bundle["chart_registration_policy"]
    assert policy["registered_chart_tooltips_only"] is True
    assert policy["generic_card_svg_tooltips_allowed"] is False
    assert policy["provider_pending_fake_numeric_values_allowed"] is False
    for chart_id in {
        "capital_allocation_by_market",
        "exposure_by_venue",
        "edge_alpha_scoreboard_visual",
        "agent_disagreement_visual",
        "DAG_route_graph_visual",
    }:
        assert chart_id in policy["non_chart_visual_ids"]
        assert policy["negative_surface_tooltip_policy"][chart_id] == "no_chart_point_tooltip_non_chart_visual"
    chart_rows = {row["chart_id"]: row for row in boot_data()["ui1r1_chart_manifest"]["charts"]}
    assert all(chart_rows[chart_id]["chart_registered"] is False for chart_id in policy["non_chart_visual_ids"])
    for snippet in (
        "OwnerChartSettingPolicyV1",
        "applyChartSettings",
        "data-chart-registered=",
        "data-axis-labels-enabled=",
        "data-crosshair-enabled=",
        "data-grid-lines-enabled=",
        "data-tooltips-enabled=",
        "No chart point tooltip",
        "provider_pending_no_value",
    ):
        assert snippet in text


def test_r2r6_workbench_catalog() -> None:
    bundle = r2r6_bundle()
    text = ui_text()
    market = bundle["market_taxonomy_contract"]
    labels = {row["owner_label"] for row in market["market_family_rows"]}
    assert {
        "Prediction Market",
        "Equities / Stocks",
        "Crypto Spot & Derivatives",
        "Listed Options",
        "Futures & Commodities",
        "FX / Macro",
        "Fixed Income / RFQ",
        "Repo / Securities Financing",
        "Cross-Market / Hedged Overlay",
        "Other / Owner-Defined",
    } <= labels
    assert not {"Sports Market", "Financial Market", "Stock Market", "Crypto Market"} & labels
    event_labels = {row["owner_label"] for row in market["event_category_rows"]}
    assert "Sports" in event_labels
    for row in market["market_family_rows"]:
        for field in (
            "market_family_id",
            "owner_visible_label",
            "canonical_market_sleeve",
            "activation_state",
            "lifecycle_state",
            "timing_state_or_snapshot_state",
            "downstream_consumer_ref",
            "pr164_review_consumer_ref_or_gap",
            "pr165_scoring_consumer_ref_or_gap",
            "responsible_agent_role_refs_or_gap",
            "provider_pending_copy",
        ):
            assert row[field]
        assert row["runtime_side_effect_allowed"] is False
        assert row["source_truth_created"] is False
        assert row["order_authority_created"] is False
    assert "MARKET_FAMILY_FALLBACK_OPTIONS" in text
    assert "Sports is an event category under Prediction Market, not a Market Family." in text


def test_r2r6_visual_proofs() -> None:
    bundle = r2r6_bundle()
    rows = {row["screenshot_path"]: row for row in bundle["screenshot_proof_registry"]}
    assert set(rows) == REQUIRED_R2R6_SCREENSHOTS
    for path, row in rows.items():
        assert path.startswith(".tmp/r2r6_")
        assert row["proof_selector_or_locator"]
        assert row["proof_text_or_state"]
        assert row["min_bounding_box_width_px"] > 0
        assert row["min_bounding_box_height_px"] > 0
        assert row["must_not_be_clipped_sliver_flag"] is True
        assert row["runtime_side_effect_allowed"] is False
        assert row["source_truth_created"] is False
        assert row["order_authority_created"] is False
    assert rows[".tmp/r2r6_mobile_wb.png"]["min_bounding_box_width_px"] >= 280
    assert "sticky/header overlays do not intersect target" in rows[".tmp/r2r6_queue.png"]["post_action_assertions"]
    assert "sticky/header overlays do not intersect target" in rows[".tmp/r2r6_receipts.png"]["post_action_assertions"]
    assert "Open technical details" in rows[".tmp/r2r6_more_actions.png"]["forbidden_visible_content"]
    proof_blob = "\n".join(str(value) for value in walk(rows))
    assert "Other / Owner-Defined" in proof_blob
    assert "Custom market family" in proof_blob
    assert "Custom event category" in proof_blob


def test_r2r6_no_runtime_no_scatter() -> None:
    bundle = r2r6_bundle()
    manifest = r2r6_manifest()
    assert bundle["central_bundle_id"] == "OwnerUXSemanticBundleV1"
    assert bundle["owned_generated_prefix"] == "docs/master_plan/generated/pr169_dash1/ui1_r2r6/"
    assert manifest["manifest_id"] == "UI1R2R6_CENTRALIZATION_MANIFEST"
    assert len({row["conceptual_domain"] for row in bundle["phase0_current_equivalent_mapping"]}) == len(bundle["phase0_current_equivalent_mapping"])
    aliases = bundle["alias_resolution_proof"]
    assert aliases["settings schema"] == "OwnerSettingsV1"
    assert aliases["theme presets"] == "OwnerThemeTokenRegistryV1"
    assert aliases["layout density tokens"] == "OwnerDensityPolicyV1"
    assert aliases["tooltip policy"] == "ChartSpecificationRegistryV1"
    assert aliases["market-family dropdowns"] == "OwnerWorkbenchOptionCatalogV1"
    for row in manifest["rows"]:
        assert row["producer"]
        assert row["central_source"]
        assert row["renderer_consumer"]
        assert row["validator_or_test_consumer"]
        assert row["playwright_proof_or_na"]
        assert row["orphan_risk"].startswith("low")
        assert row["runtime_side_effect_allowed"] is False
        assert row["source_truth_created"] is False
        assert row["order_authority_created"] is False
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
        assert bundle["no_runtime_authority"][key] is True


def test_r2r6_currentization() -> None:
    bundle = r2r6_bundle()
    preflight = bundle["currentization_preflight"]
    assert preflight["new_exact_path_playwright_script_added"] is False
    assert preflight["stable_runner_extended_with_suite_arg"] is True
    assert preflight["wildcard_allowlists_added"] is False
    assert preflight["generated_inventory_change_requires_pr152_currentization"] is True
    assert "tools/currentize_pr152_after_generated_artifacts.py" in "\n".join(preflight["mandatory_pre_push_commands"])
    for row in bundle["changed_file_ownership_audit"]:
        assert row["file_path"]
        assert row["owned_prefix_or_allowed_shared_reason"]
        assert row["runtime_authority_change"] is False
        assert row["source_truth_change"] is False
        assert row["order_authority_change"] is False
