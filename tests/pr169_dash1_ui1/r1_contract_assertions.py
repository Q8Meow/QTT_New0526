from tests.pr169_dash1_ui1.conftest import BASE, UI, boot_data, ui_doc, ui_text


def assert_12fix_acceptance_all_pass() -> None:
    doc = ui_doc("ui1r1_12fix_acceptance.generated.json")
    assert len(doc["rows"]) == 12
    assert doc["all_pass"] is True
    assert all(row["status"] == "PASS" for row in doc["rows"])
    assert doc["deferred_brainstorm_ideas_not_materialized"] is True


def assert_owner_mode_migrated() -> None:
    doc = ui_doc("ui1r1_owner_mode.report.json")
    assert doc["owner_mode_default"] is True
    assert doc["developer_mode_collapsed_by_default"] is True
    assert doc["registry_diagnostics_not_owner_default"] is True
    assert doc["raw_json_not_primary_owner_content"] is True
    assert "registry_row_count" in doc["moved_to_developer_mode"]


def assert_developer_mode_diagnostics() -> None:
    doc = ui_doc("ui1r1_dev_mode.generated.json")
    ids = {row["diagnostic_id"] for row in doc["diagnostics"]}
    assert {"registry_row_count", "artifact_directory", "validator_status", "no_orphan_report_status", "authority_boundary_report_status"} <= ids
    assert doc["developer_mode_collapsed_by_default"] is True


def assert_owner_home() -> None:
    doc = ui_doc("ui1r1_home.generated.json")
    assert doc["default_mode"] == "OWNER_MODE"
    assert len(doc["hero_cards"]) >= 10
    assert any(row["widget_id"] == "net_capital_cash_slot" for row in doc["hero_cards"])
    assert "portfolio_equity_curve" in doc["first_viewport_order"]
    assert "plain_english_chat_composer_quick_card" in doc["first_viewport_order"]


def assert_chart_markers() -> None:
    text = ui_text()
    for token in (
        "data-chart-id",
        "data-chart-kind",
        "data-chart-render-state",
        "data-chart-source-ref",
        "data-provider-stage",
        "data-authority-boundary",
        "chart-svg",
        "provider-overlay",
    ):
        assert token in text
    doc = ui_doc("ui1r1_chart_manifest.generated.json")
    assert len(doc["charts"]) >= 10
    assert all(row["fake_value_allowed"] is False for row in doc["charts"])


def assert_tca_waterfall() -> None:
    doc = ui_doc("ui1r1_chart_manifest.generated.json")
    row = next(row for row in doc["charts"] if row["chart_id"] == "TCA_waterfall_and_implementation_shortfall")
    assert row["chart_kind"] == "waterfall"
    assert "tca_decomp.jsonl" in row["source_artifact_ref"]
    assert row["fake_value_allowed"] is False


def assert_portfolio_exposure_cards() -> None:
    charts = ui_doc("ui1r1_chart_manifest.generated.json")["charts"]
    ids = {row["chart_id"] for row in charts}
    assert {"capital_allocation_by_market", "exposure_by_venue"} <= ids
    home = ui_doc("ui1r1_home.generated.json")
    assert any(row["widget_id"] == "net_capital_cash_slot" for row in home["hero_cards"])


def assert_no_fake_cash_or_positions() -> None:
    text = "\n".join(str(value) for value in boot_data().values())
    banned = ("live position value", "account balance:", "fill price:", "guaranteed positive profit")
    assert all(token not in text.lower() for token in banned)
    assert "Provider-pending cash/capital receipt slot" in text


def assert_qku_route_closure() -> None:
    doc = ui_doc("ui1r1_qku_route_closure.report.json")
    assert doc["status"] == "PASS"
    assert doc["all_owner_visible_qku_formula_candidate_refs_have_route_or_actionable_gap"] is True
    assert doc["rows"]
    assert all(row["no_orphan_status"] == "PASS" for row in doc["rows"])


def assert_chat_examples_parse() -> None:
    doc = ui_doc("ui1r1_chat_examples.generated.json")
    assert doc["all_examples_parse_to_preview_objects"] is True
    assert len(doc["examples"]) >= 6
    for row in doc["examples"]:
        parsed = row["parsed_preview_output"]
        assert parsed["object_type"] == "OwnerPlainEnglishIntentV1"
        assert parsed["runtime_side_effect"] is False
        assert parsed["agent_role_refs_from_PR165_D2_or_gap"]


def assert_chat_composer_contract() -> None:
    text = ui_text()
    for token in (
        'data-chat-composer="owner-plain-english"',
        'data-chat-runtime-side-effect="false"',
        'data-intent-parser="local-preview"',
        "ownerChatInput",
        "routePreviewButton",
        "OwnerPlainEnglishIntentV1",
    ):
        assert token in text
    doc = ui_doc("ui1r1_chat_contract.generated.json")
    assert len(doc["prompt_chips"]) >= 8
    assert doc["live_LLM_call_created"] is False


def assert_chat_routes() -> None:
    doc = ui_doc("ui1r1_chat_routes.generated.json")
    route_ids = {row["route_id"] for row in doc["routes"]}
    assert {"UI1R1_CHAT_TO_TRADE", "UI1R1_CHAT_TO_RESEARCH"} <= route_ids
    assert all(row["runtime_side_effect"] is False for row in doc["routes"])
    assert all(row["PR165_D2_agent_role_refs_or_gap"] for row in doc["routes"])


def assert_trade_workbench() -> None:
    doc = ui_doc("ui1r1_order_sim.generated.json")
    assert len(doc["owner_input_fields"]) >= 17
    assert {row["card_id"] for row in doc["comparison_cards"]} == {"best_candidate", "runner_up_challenger", "no_trade_alternative"}
    assert doc["runtime_side_effect"] is False
    assert doc["execution_router_provider_pending"] is True


def assert_edge_alpha() -> None:
    doc = ui_doc("ui1r1_edge_alpha.generated.json")
    assert doc["ranking_rule"] == "execution_adjusted_ordering_not_raw_edge_only"
    assert doc["rows"]
    for row in doc["rows"]:
        assert row["metadata_only_ranking"] is False
        assert row["ranking_components"]
        assert "TCA_cost_drag_component" in row["ranking_components"]


def assert_agent_disagreement() -> None:
    doc = ui_doc("ui1r1_agent_disagreement.generated.json")
    assert len(doc["rows"]) >= 10
    assert "Trade Workbench section" in doc["placements"]
    for row in doc["rows"]:
        assert row["agent_role_ref_from_PR165_D2_or_gap"]
        assert row["fake_agent_claim"] is False


def assert_parameter_tuning() -> None:
    doc = ui_doc("ui1r1_parameter_tuning.generated.json")
    assert doc["live_parameter_mutation_allowed"] is False
    assert doc["rows"]
    for row in doc["rows"]:
        assert row["atomic_drilldown"]
        assert row["live_mutation_allowed"] is False


def assert_mobile_parity() -> None:
    doc = ui_doc("ui1r1_mobile_parity.report.json")
    surfaces = {row["surface"] for row in doc["surfaces"]}
    assert {"Home", "Portfolio", "Trade Workbench", "Chat", "Edge/Alpha", "Agents", "Parameters", "Developer Mode"} <= surfaces
    assert doc["separate_mobile_state_model"] is False
    assert doc["touch_targets_minimum_px"] >= 44


def assert_inst_quant_crosslink() -> None:
    doc = ui_doc("ui1r1_inst_quant_crosslink.report.json")
    assert doc["quantum_advantage_claim"] is False
    assert doc["rows"]
    for row in doc["rows"]:
        assert row["labels_only"] is False
        assert row["decision_spine_fields"]["execution_adjusted_rank"]
        assert row["quantum_refs"]["classical_fallback_ref"]


def assert_playwright_report() -> None:
    doc = ui_doc("ui1r1_playwright.report.json")
    assert doc["status"] == "PASS"
    assert len(doc["screenshots"]) >= 9
    assert doc["network_status"] == "PASS"
    assert doc["console_status"] == "PASS"


def assert_no_deferred_artifacts() -> None:
    forbidden = {
        "owner_dashboard_workstation_expansion_matrix.generated.json",
        "owner_dashboard_workstation_expansion_matrix.generated.jsonl",
        "workstation_expansion_matrix.generated.json",
        "50_idea_backlog.generated.json",
    }
    ui_files = {path.name for path in UI.iterdir() if path.is_file()}
    base_files = {path.name for path in BASE.iterdir() if path.is_file()}
    assert forbidden.isdisjoint(ui_files)
    assert forbidden.isdisjoint(base_files)
