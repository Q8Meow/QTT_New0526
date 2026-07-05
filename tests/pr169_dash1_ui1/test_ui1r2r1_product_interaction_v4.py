from __future__ import annotations

from tests.pr169_dash1_ui1.r2r1_contract_assertions import (
    assert_chat_keyboard_policy,
    assert_chat_preview_contract,
    assert_evidence_spine_and_authority,
    assert_guided_single_line_enter_policy,
    assert_interaction_controller_centralized,
    assert_mode_policy_distinct,
    assert_next_step_routes,
    assert_no_runtime_or_parallel_state,
    assert_r2r1_artifacts_present,
    assert_renderer_mode_markers,
    assert_visual_compactness,
    assert_workbench_prefill_and_drilldowns,
)


def test_ui1r2r1_interaction_controller_centralized() -> None:
    assert_r2r1_artifacts_present()
    assert_interaction_controller_centralized()


def test_ui1r2r1_modes_render_distinct_content() -> None:
    assert_mode_policy_distinct()
    assert_renderer_mode_markers()


def test_ui1r2r1_guided_mode_hides_advanced_and_developer_fields() -> None:
    assert_mode_policy_distinct()


def test_ui1r2r1_advanced_mode_shows_more_metrics_than_guided() -> None:
    assert_mode_policy_distinct()


def test_ui1r2r1_developer_mode_shows_raw_refs_only_in_developer() -> None:
    assert_mode_policy_distinct()


def test_chat_enter_inserts_newline_by_default() -> None:
    assert_chat_keyboard_policy()


def test_chat_ctrl_enter_submits() -> None:
    assert_chat_keyboard_policy()
    assert_chat_preview_contract()


def test_chat_send_button_submits() -> None:
    assert_chat_keyboard_policy()
    assert_chat_preview_contract()


def test_chat_shift_enter_inserts_newline() -> None:
    assert_chat_keyboard_policy()


def test_chat_enter_to_send_setting_disabled_by_default() -> None:
    assert_chat_keyboard_policy()


def test_ui1r2r1_chat_empty_input_no_submit() -> None:
    assert_chat_keyboard_policy()


def test_ui1r2r1_chat_submit_creates_owner_and_qtt_preview_bubbles() -> None:
    assert_chat_preview_contract()


def test_ui1r2r1_plain_english_chat_intent_preview() -> None:
    assert_chat_preview_contract()


def test_ui1r2r1_chat_message_routes_to_trade_research_qku() -> None:
    assert_chat_preview_contract()


def test_ui1r2r1_chat_no_separate_conversation_state() -> None:
    assert_chat_preview_contract()
    assert_no_runtime_or_parallel_state()


def test_guided_single_line_input_enter_advances_step() -> None:
    assert_guided_single_line_enter_policy()


def test_ui1r2r1_guided_numeric_input_enter_advances_step() -> None:
    assert_guided_single_line_enter_policy()


def test_ui1r2r1_guided_invalid_numeric_input_blocks_with_inline_message() -> None:
    assert_guided_single_line_enter_policy()


def test_ui1r2r1_guided_continue_button_matches_enter() -> None:
    assert_guided_single_line_enter_policy()


def test_ui1r2r1_dropdown_action_routes_to_next_step() -> None:
    assert_next_step_routes()


def test_ui1r2r1_send_to_trade_workbench_prefills_context() -> None:
    assert_next_step_routes()
    assert_workbench_prefill_and_drilldowns()


def test_ui1r2r1_workbench_prefill_from_card_edge_and_chat() -> None:
    assert_workbench_prefill_and_drilldowns()


def test_ui1r2r1_show_qku_formula_routes_opens_drawer() -> None:
    assert_workbench_prefill_and_drilldowns()


def test_ui1r2r1_explain_no_trade_opens_panel() -> None:
    assert_workbench_prefill_and_drilldowns()


def test_ui1r2r1_show_tca_opens_cost_drilldown() -> None:
    assert_workbench_prefill_and_drilldowns()


def test_ui1r2r1_collapsed_sections_do_not_reserve_empty_body() -> None:
    assert_visual_compactness()


def test_ui1r2r1_guided_mode_compact_card_density() -> None:
    assert_visual_compactness()


def test_ui1r2r1_technical_details_not_prominent_in_owner_mode() -> None:
    assert_visual_compactness()


def test_ui1r2r1_cards_have_specific_owner_titles() -> None:
    assert_visual_compactness()


def test_ui1r2r1_no_repetitive_generic_owner_decision_cards() -> None:
    assert_visual_compactness()


def test_ui1r2r1_primary_secondary_disabled_actions_visually_distinct() -> None:
    assert_visual_compactness()


def test_ui1r2r1_institutional_decision_spine_preserved() -> None:
    assert_evidence_spine_and_authority()


def test_ui1r2r1_quantum_structural_routes_preserved() -> None:
    assert_evidence_spine_and_authority()


def test_ui1r2r1_no_fake_quantum_advantage_claim() -> None:
    assert_evidence_spine_and_authority()
    assert_no_runtime_or_parallel_state()


def test_ui1r2r1_no_fake_trading_evidence() -> None:
    assert_evidence_spine_and_authority()


def test_ui1r2r1_owner_command_authority_no_direct_release() -> None:
    assert_evidence_spine_and_authority()
    assert_no_runtime_or_parallel_state()


def test_ui1r2r1_next_step_preserves_evidence_spine() -> None:
    assert_next_step_routes()
    assert_evidence_spine_and_authority()


def test_ui1r2r1_mode_density_thresholds_by_mode() -> None:
    assert_mode_policy_distinct()


def test_ui1r2r1_semantic_title_gap_report() -> None:
    assert_visual_compactness()


def test_ui1r2r1_guided_first_viewport_no_empty_disclosure_panels() -> None:
    assert_visual_compactness()


def test_ui1r2r1_advanced_mode_metric_groups_exceed_guided() -> None:
    assert_mode_policy_distinct()


def test_ui1r2r1_developer_mode_technical_evidence_exceeds_advanced() -> None:
    assert_mode_policy_distinct()
