from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.pr169_dash1_ui1.conftest import BASE, UI, boot_data, ui_doc, ui_text


R2_ARTIFACTS = (
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

REQUIRED_NEXT_STEPS = {
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


def _assert_r2_meta(doc: dict[str, Any]) -> None:
    meta = doc["meta"]
    assert meta["manual_edit_allowed"] is False
    assert meta["runtime_truth_authority"] is False
    assert meta["agent_consumable_authority"] is False
    assert meta["credential_access_allowed"] is False
    assert meta["connector_access_allowed"] is False
    assert meta["order_execution_allowed"] is False


def _action_codes() -> set[str]:
    return {row["action_code"] for row in boot_data()["action_registry"]}


def _next_rows() -> list[dict[str, Any]]:
    return ui_doc("ui1r2_next_step.generated.json")["rows"]


def _next_by_id() -> dict[str, dict[str, Any]]:
    return {row["next_step_id"]: row for row in _next_rows()}


def assert_r2_artifacts_present() -> None:
    for name in R2_ARTIFACTS:
        path = UI / name
        assert path.exists(), name
        _assert_r2_meta(ui_doc(name))
    data = boot_data()
    for key in (
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
    ):
        assert key in data


def assert_copy_map() -> None:
    doc = ui_doc("ui1r2_copy_map.generated.json")
    rows = {row["technical_pattern_or_exact_id"]: row for row in doc["rows"]}
    assert rows["DASH1_FEATURE_011_ACKNOWLEDGMENT_IS_NOT_LIVE_APPROVAL"]["owner_title"] == "Acknowledging review does not approve a live trade."
    assert rows["VISIBLE_EMPTY_STATE_PROVIDER_PENDING"]["owner_title"] == "Waiting for provider data."
    assert rows["CONTRACT_DEFINED_PROVIDER_PENDING"]["owner_title"] == "Provider contract defined; runtime not active yet."
    assert rows["ROUTED_PENDING_PROVIDER"]["owner_title"] == "Connected to a pending QTT provider route."
    assert rows["OwnerSurfaceResolver"]["owner_title"] == "QTT routing link verified."
    assert rows["OwnerActionRegistry"]["owner_title"] == "Owner actions governed."
    assert all(row["owner_title"] and row["owner_summary"] for row in doc["rows"])


def assert_modes() -> None:
    doc = ui_doc("ui1r2_mode.generated.json")
    assert doc["default_mode"] == "GUIDED_OWNER"
    assert doc["all_modes_use_same_OwnerDashboardStateV1"] is True
    assert doc["all_modes_use_same_OwnerSurfaceResolver"] is True
    assert doc["all_modes_use_same_OwnerActionRegistry"] is True
    assert doc["no_second_dashboard_state_model"] is True
    assert doc["no_second_action_grammar"] is True
    rows = {row["mode_id"]: row for row in doc["rows"]}
    assert set(rows) == {"GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"}
    assert rows["GUIDED_OWNER"]["default_state"] is True
    assert rows["ADVANCED_OWNER"]["default_state"] is False
    assert rows["DEVELOPER"]["default_state"] is False


def assert_disclosure_defaults() -> None:
    doc = ui_doc("ui1r2_disclosure.report.json")
    assert doc["default_expansion_state_on_page_load"] == "collapsed"
    assert doc["education_text_wall_visible_by_default"] is False
    assert doc["technical_details_visible_by_default"] is False
    assert doc["raw_refs_visible_by_default"] is False
    assert doc["Developer_Mode_default"] is False
    assert doc["GUIDED_OWNER_default"] is True


def assert_owner_mode_text_safety() -> None:
    doc = ui_doc("ui1r2_text_safety.report.json")
    assert doc["owner_mode_blocklist_visible_count"] == 0
    assert doc["high_priority_owner_mode_raw_id_leaks"] == []
    text = ui_text()
    assert "DashboardSystem" in text
    assert "OwnerNextStepRouter" in text
    assert "data-owner-next-action-menu" in text
    assert "data-next-step-id" in text


def assert_card_copy() -> None:
    doc = ui_doc("ui1r2_card_copy.report.json")
    assert doc["owner_cards_human_readable"] is True
    assert doc["learning_sections_collapsed_by_default"] is True
    assert {"What can I do next?", "Learn", "Why?", "Explain", "Technical Details"} <= set(doc["card_template_fields"])


def assert_guidance_coverage() -> None:
    doc = ui_doc("ui1r2_guidance.report.json")
    assert doc["all_owner_visible_widget_count"] == doc["owner_visible_widgets_with_guidance_count"]
    assert doc["missing_guidance_widget_ids"] == []
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
        assert doc[key] is True


def assert_action_menu() -> None:
    doc = ui_doc("ui1r2_action_menu.generated.json")
    next_ids = set(_next_by_id())
    assert doc["rows"]
    for row in doc["rows"]:
        assert row["runtime_side_effect_allowed"] is False
        assert row["options"]
        assert row["recommended_action_label"]
        for option in row["options"]:
            assert option["owner_label"]
            assert "_" not in option["owner_label"]
            assert option["runtime_side_effect_allowed"] is False
            if option["state"] == "ENABLED_LOCAL_PREVIEW":
                assert option["next_step_id"] in next_ids


def assert_disabled_actions_educate() -> None:
    doc = ui_doc("ui1r2_action_menu.generated.json")
    disabled = [option for row in doc["rows"] for option in row["options"] if option["state"] != "ENABLED_LOCAL_PREVIEW"]
    assert disabled
    for option in disabled:
        assert option["disabled_reason_if_blocked"] or option["safe_alternative_action"]
        assert "No live LLM call" in option["what_will_not_happen_now"]


def assert_next_step_router() -> None:
    doc = ui_doc("ui1r2_next_step.generated.json")
    assert doc["router_id"] == "OwnerNextStepRouter"
    assert "OwnerNextActionMenuModel" in doc["centralized_route_chain"]
    rows = _next_rows()
    assert REQUIRED_NEXT_STEPS <= {row["next_step_id"] for row in rows}
    action_codes = _action_codes()
    for row in rows:
        assert row["action_id"] in action_codes
        assert row["runtime_side_effect_allowed"] is False
        assert row["authority_boundary"]
        assert row["source_artifact_refs"]
        assert row["PR165_D2_agent_role_refs_or_gap"]
        assert row["QKU_formula_refs_or_gap"]
        assert row["LLM_view_refs_or_provider_route"]
        assert "No live LLM call" in row["what_will_not_happen_now"]
        assert "Execution Router release occurs" in row["what_will_not_happen_now"]


def assert_next_step_route(next_step_id: str, target_surface: str, preview_type: str) -> None:
    row = _next_by_id()[next_step_id]
    assert row["target_surface_id"] == target_surface
    assert row["preview_object_type"] == preview_type
    assert row["creates_local_receipt_preview"] is True
    assert row["runtime_side_effect_allowed"] is False


def assert_guided_flows() -> None:
    doc = ui_doc("ui1r2_guided_flow.generated.json")
    ids = {row["workflow_id"] for row in doc["flows"]}
    assert {"CHECK_TRADE", "RESEARCH_CANDIDATE", "EXPLAIN_NO_TRADE", "PARAMETER_TUNING", "EDGE_ALPHA_REVIEW"} <= ids
    for key in (
        "runtime_side_effect_allowed",
        "live_LLM_call_allowed",
        "real_agent_execution_allowed",
        "paper_execution_allowed",
        "live_execution_allowed",
        "direct_venue_submit_allowed",
        "ExecutionRouter_release_allowed",
    ):
        assert doc[key] is False
    check_trade = next(row for row in doc["flows"] if row["workflow_id"] == "CHECK_TRADE")
    assert len(check_trade["steps"]) >= 6
    assert check_trade["steps"][0]["owner_input_required"] is True


def assert_education() -> None:
    doc = ui_doc("ui1r2_education.generated.json")
    assert doc["education_text_wall_visible_by_default"] is False
    assert doc["technical_details_visible_by_default"] is False
    assert doc["raw_refs_visible_by_default"] is False
    assert all(row["collapsed_by_default"] for row in doc["page_lessons"])
    assert all(row["collapsed_by_default"] for row in doc["chart_explainers"])


def assert_glossary() -> None:
    terms = {row["term"] for row in ui_doc("ui1r2_education.generated.json")["glossary"]}
    required = {
        "PnL",
        "expected net cash",
        "TCA",
        "spread",
        "slippage",
        "latency drag",
        "market impact",
        "opportunity cost",
        "fill probability",
        "partial fill",
        "capacity",
        "crowding",
        "no-trade",
        "champion/challenger",
        "lower confidence bound",
        "FDR / false discovery",
        "overfit",
        "portfolio marginal utility",
        "regime memory",
        "QKU",
        "formula stack",
        "quantum structural readiness",
        "classical fallback",
        "Execution Router",
        "live canary",
        "paper trading",
        "replay",
        "shadow",
    }
    assert required <= terms


def assert_renderer_controls() -> None:
    text = ui_text()
    for snippet in (
        "Tell me what matters",
        "How QTT will trade with AI",
        "ownerGlossary",
        "guidedWorkflowPanel",
        "routePreviewPanel",
        "chat-bubble",
        "owner-bubble",
        "qtt-bubble",
        "data-local-receipt-preview",
        "data-workbench-id",
        "data-owner-trade-intent-preview",
        "data-chat-composer=\"owner-plain-english\"",
        "data-chat-runtime-side-effect=\"false\"",
    ):
        assert snippet in text
    assert "fetch(" not in text


def assert_no_runtime_authority() -> None:
    for name in R2_ARTIFACTS:
        _assert_r2_meta(ui_doc(name))
    for row in _next_rows():
        assert row["runtime_side_effect_allowed"] is False
    guided = ui_doc("ui1r2_guided_flow.generated.json")
    assert guided["live_LLM_call_allowed"] is False
    assert guided["real_agent_execution_allowed"] is False
    assert guided["paper_execution_allowed"] is False
    assert guided["live_execution_allowed"] is False
    assert guided["direct_venue_submit_allowed"] is False
    assert guided["ExecutionRouter_release_allowed"] is False


def assert_no_deferred_idea_artifacts() -> None:
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


def assert_no_profit_claims() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in (UI / name for name in R2_ARTIFACTS))
    banned = ("guaranteed profit", "risk-free", "QTT will win", "quantum advantage guaranteed")
    assert all(token not in text for token in banned)
    assert "profit confidence" in text


def assert_playwright_content_quality_contract() -> None:
    report = ui_doc("ui1r2_playwright.report.json")
    assert report["status"] in {"PENDING_LOCAL_RUN", "PASS"}
    assert report["runtime_side_effect_allowed"] is False
    assert Path("tools/playwright_pr169_dash1_ui1_r2_visual_smoke.py").exists()
