from __future__ import annotations

from typing import Any

from tests.pr169_dash1_ui1.conftest import UI, boot_data, ui_doc, ui_text


R2R1_ARTIFACTS = (
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

REQUIRED_HANDLERS = {
    "OwnerExperienceModePolicy",
    "OwnerChatSubmitHandler",
    "OwnerGuidedInputHandler",
    "OwnerNextStepRouter",
    "OwnerWorkbenchPrefillAdapter",
    "OwnerDrilldownRouter",
    "OwnerInteractionReceiptPreviewBuilder",
}

REQUIRED_INTENTS = {
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
}

REQUIRED_SPINE_REFS = {
    "execution_adjusted_rank_ref",
    "TCA_decomposition_ref",
    "implementation_shortfall_ref",
    "overfit_false_discovery_control_ref",
    "portfolio_diversification_ref",
    "portfolio_marginal_utility_ref",
    "capacity_crowding_limit_ref",
    "champion_challenger_ref",
    "regime_conditioned_memory_ref",
    "MEM1_similarity_and_shrinkage_prior_refs",
    "no_trade_comparator_and_reoptimization_route",
    "scenario_ladder_ref",
    "calibration_ref",
    "quantum_structural_readiness_ref",
    "QUBO_BQM_CQM_QuadraticProgram_Ising_readiness_ref",
    "QAOA_VQE_annealing_candidate_readiness_ref",
    "classical_fallback_ref",
    "qstruct_objective_constraint_variable_ref",
    "interpret_back_map_ref",
    "DAG_upstream_downstream_route_ref",
    "PR165_D2_agent_role_refs_or_gap",
    "QKU_formula_refs_or_gap",
    "LLM_view_refs_or_provider_route",
}


def _assert_meta(doc: dict[str, Any]) -> None:
    meta = doc["meta"]
    assert meta["manual_edit_allowed"] is False
    assert meta["runtime_truth_authority"] is False
    assert meta["agent_consumable_authority"] is False
    assert meta["credential_access_allowed"] is False
    assert meta["connector_access_allowed"] is False
    assert meta["order_execution_allowed"] is False


def assert_r2r1_artifacts_present() -> None:
    data = boot_data()
    for name in R2R1_ARTIFACTS:
        assert (UI / name).exists(), name
        _assert_meta(ui_doc(name))
    for key in (
        "ui1r2r1_mode_policy",
        "ui1r2r1_mode_render",
        "ui1r2r1_interaction_map",
        "ui1r2r1_interaction_result",
        "ui1r2r1_next_step",
        "ui1r2r1_next_step_report",
        "ui1r2r1_chat_submit",
        "ui1r2r1_workbench_prefill",
        "ui1r2r1_visual_polish",
        "ui1r2r1_visual_compactness",
        "ui1r2r1_chat_intent",
        "ui1r2r1_owner_command",
        "ui1r2r1_evidence_spine",
        "ui1r2r1_playwright",
    ):
        assert key in data


def assert_interaction_controller_centralized() -> None:
    doc = ui_doc("ui1r2r1_interaction_map.generated.json")
    assert doc["controller_id"] == "OwnerInteractionController"
    assert REQUIRED_HANDLERS <= set(doc["central_handlers"])
    for row in doc["rows"]:
        assert row["runtime_side_effect_allowed"] is False
        assert row["owner_visible_state_change"]
        assert row["local_preview_object_refs"]
        assert row["authority_boundary"]


def assert_mode_policy_distinct() -> None:
    policy = ui_doc("ui1r2r1_mode_policy.generated.json")
    render = ui_doc("ui1r2r1_mode_render.report.json")
    assert policy["mode_policy_id"] == "OwnerExperienceModePolicy"
    rows = {row["mode_id"]: row for row in policy["rows"]}
    assert set(rows) == {"GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"}
    assert rows["GUIDED_OWNER"]["state_model_ref"] == rows["ADVANCED_OWNER"]["state_model_ref"] == rows["DEVELOPER"]["state_model_ref"]
    assert rows["GUIDED_OWNER"]["metric_density"] == "LOW"
    assert rows["ADVANCED_OWNER"]["metric_density"] == "HIGH_OWNER_READABLE"
    assert rows["DEVELOPER"]["metric_density"] == "TECHNICAL_AUDIT"
    assert "developer_json" not in rows["GUIDED_OWNER"]["visible_widget_groups"]
    assert "developer_json" in rows["DEVELOPER"]["visible_widget_groups"]
    assert render["modes_render_identical_content"] is False
    assert render["advanced_owner_visible_metric_group_count"] > render["guided_owner_visible_metric_group_count"]
    assert render["developer_visible_technical_group_count"] > render["advanced_owner_visible_metric_group_count"]


def assert_renderer_mode_markers() -> None:
    text = ui_text()
    assert "OwnerExperienceModePolicy" in text
    assert "data-mode-panel=\"GUIDED_OWNER\"" in text
    assert "data-mode-panel=\"ADVANCED_OWNER\"" in text
    assert "data-mode-panel=\"DEVELOPER\"" in text
    assert "data-mode-advanced-metric" in text
    assert "data-mode-developer-technical" in text


def assert_chat_keyboard_policy() -> None:
    doc = ui_doc("ui1r2r1_chat_submit.report.json")
    text = ui_text()
    assert doc["default_desktop_enter_behavior"] == "NEWLINE"
    assert doc["mobile_enter_behavior"] == "NEWLINE"
    assert doc["physical_enter_identical_to_send_by_default"] is False
    assert doc["enter_to_send_default_enabled"] is False
    assert doc["enter_to_send_optional_setting_available"] is True
    assert doc["ctrl_enter_submits_local_preview"] is True
    assert doc["send_button_submits_local_preview"] is True
    assert doc["shift_enter_inserts_newline"] is True
    assert doc["empty_send_click_inline_hint"] is True
    assert "data-chat-enter-to-send-default=\"false\"" in text
    assert "data-enter-to-send-setting=\"optional\"" in text
    assert "CTRL_ENTER_SUBMIT" in text
    assert "BUTTON_SUBMIT" in text
    assert "Enter inserted a newline" in text


def assert_chat_preview_contract() -> None:
    submit = ui_doc("ui1r2r1_chat_submit.report.json")
    intents = ui_doc("ui1r2r1_chat_intent.report.json")
    assert submit["central_conversation_state_ref"] == "OwnerConversationStateV1"
    assert submit["owner_and_qtt_preview_bubbles_visible"] is True
    assert submit["runtime_side_effect_allowed"] is False
    assert REQUIRED_INTENTS <= set(intents["recognized_intent_families"])
    for row in submit["rows"] + intents["rows"]:
        assert row["runtime_side_effect_allowed"] is False
        assert row["target_surface_id"]
        assert row["PR165_D2_agent_role_refs_or_gap"]
        assert row["QKU_formula_refs_or_gap"]
        assert row["LLM_view_refs_or_provider_route"]


def assert_guided_single_line_enter_policy() -> None:
    text = ui_text()
    assert "OwnerGuidedInputHandler" in text
    assert "data-guided-text-input=\"true\"" in text
    assert "data-guided-numeric-input=\"true\"" in text
    assert "advance(\"ENTER_SUBMIT\")" in text
    assert "Enter a number or choose a preset." in text
    assert "data-guided-current-step" in text


def assert_next_step_routes() -> None:
    doc = ui_doc("ui1r2r1_next_step.generated.json")
    rows = doc["rows"]
    assert doc["router_id"] == "OwnerNextStepRouter"
    assert rows
    required_routes = {
        "NEXT_STEP_SEND_TO_TRADE_WORKBENCH",
        "NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS",
        "NEXT_STEP_REQUEST_REPLAY_PREVIEW",
        "NEXT_STEP_REQUEST_PAPER_PREVIEW",
        "NEXT_STEP_SHOW_QKU_FORMULA_ROUTES",
        "NEXT_STEP_EXPLAIN_NO_TRADE",
        "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN",
    }
    assert required_routes <= {row["next_step_id"] for row in rows}
    for row in rows:
        assert row["runtime_side_effect_allowed"] is False
        assert row["target_surface_id"]
        assert row["preview_object_type"]
        assert row["source_artifact_refs"]
        assert row["PR165_D2_agent_role_refs_or_gap"]
        assert row["QKU_formula_refs_or_gap"]


def assert_workbench_prefill_and_drilldowns() -> None:
    workbench = ui_doc("ui1r2r1_workbench_prefill.report.json")
    text = ui_text()
    assert workbench["adapter_id"] == "OwnerWorkbenchPrefillAdapter"
    assert {"card", "Edge/Alpha row", "chat message"} <= set(workbench["prefill_sources"])
    for section in (
        "Owner intent",
        "Source/research context",
        "QKU/formula stack route",
        "Replay preview route",
        "Paper preview route",
        "TCA / cost route",
        "No-trade comparator",
        "Execution Router provider-pending route",
    ):
        assert section in workbench["visible_sections_verified"]
    assert "data-workbench-context-preview=\"WorkbenchContextPreviewV1\"" in text
    assert "data-drilldown-kind" in text
    assert "No-trade is a comparator and reoptimization route" in text
    assert "QKU/formula refs or explicit gap route" in text
    assert "no raw JSONL scanning path" in text


def assert_visual_compactness() -> None:
    compact = ui_doc("ui1r2r1_visual_compactness.report.json")
    polish = ui_doc("ui1r2r1_visual_polish.report.json")
    text = ui_text()
    assert compact["collapsed_control_max_default_body_rows"] == 0
    assert compact["technical_details_dominant_in_guided_owner"] is False
    assert compact["generic_owner_decision_repeated_default_allowed"] is False
    assert polish["action_states_distinct"] is True
    assert ".owner-card-controls details:not([open]) > :not(summary)" in text
    assert "action-primary" in text
    assert "action-secondary" in text
    assert "is-provider-pending" in text
    assert "is-disabled" in text
    titles = [row["semantic_title"] for row in compact["rows"]]
    assert len(set(titles)) >= 8
    assert "Owner Decision" not in titles
    for row in compact["rows"]:
        assert row["collapsed_controls_compact"] is True
        assert row["large_empty_collapsed_body_present"] is False
        assert row["specific_semantic_title_present"] is True


def assert_evidence_spine_and_authority() -> None:
    spine = ui_doc("ui1r2r1_evidence_spine.report.json")
    owner_command = ui_doc("ui1r2r1_owner_command.report.json")
    assert REQUIRED_SPINE_REFS <= set(spine["required_evidence_spine_refs"])
    assert spine["refs_absent_use_provider_pending_gap_route"] is True
    assert spine["no_fake_trading_evidence"] is True
    assert spine["no_fake_quantum_advantage"] is True
    assert owner_command["owner_trading_command_preview_authority"] is True
    assert owner_command["execution_router_release_authority_created"] is False
    assert owner_command["direct_venue_submit_allowed"] is False
    for row in spine["rows"]:
        for key in REQUIRED_SPINE_REFS:
            assert row[key]
        assert row["runtime_side_effect_allowed"] is False


def assert_no_runtime_or_parallel_state() -> None:
    text = "\n".join((UI / name).read_text(encoding="utf-8") for name in R2R1_ARTIFACTS) + "\n" + ui_text()
    forbidden = (
        "live_LLM_call_allowed\": true",
        "real_agent_execution_allowed\": true",
        "connector_access_allowed\": true",
        "private_cash_account",
        "direct_venue_submit_allowed\": true",
        "ExecutionRouter_release_allowed\": true",
        "quantum_advantage_claim\": true",
        "profit guarantee",
        "new OwnerDashboardState",
        "second action grammar",
    )
    assert all(token not in text for token in forbidden)
    for name in R2R1_ARTIFACTS:
        doc = ui_doc(name)
        assert doc.get("runtime_side_effect_allowed", False) is False
        _assert_meta(doc)
