import json
from pathlib import Path

from tools import validate_owner_live_promotion_review_for_parameter_stacks as gate


REPO_ROOT = Path(".")
_REPORT_CACHE: dict | None = None


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert gate.main([]) == 0
        _REPORT_CACHE = json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _packet() -> dict:
    return _report()["owner_live_promotion_review_parameter_stack_packet"]


def _review_item() -> dict:
    items = _packet()["owner_review_items"]
    assert len(items) == 1
    return items[0]


def _case_packet(case_id: str) -> dict:
    for packet in _report()["fixture_case_packets"]:
        if packet["fixture_case_id"] == case_id:
            return packet
    raise AssertionError(f"missing case packet: {case_id}")


def _all_reason_codes(packet: dict) -> set[str]:
    return set(packet.get("review_reason_codes", [])) | set(packet.get("blocked_reason_codes", []))


def _assert_blocked(case_id: str, reason_code: str) -> None:
    packet = _case_packet(case_id)
    assert packet["valid_owner_review_item_count"] == 0
    assert packet["blocked_owner_review_item_count"] == 1
    assert reason_code in _all_reason_codes(packet)
    assert packet["live_promotion_created_flag"] is False
    assert packet["order_authority_created_flag"] is False


def _mock_git_stdout(monkeypatch, responses: dict[tuple[str, ...], tuple[int, str, str]]) -> None:
    def fake_git_stdout(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
        key = tuple(args)
        if key not in responses:
            raise AssertionError(f"unexpected git command: {args}")
        return responses[key]

    monkeypatch.setattr(gate, "_git_stdout", fake_git_stdout)


def _git_metadata_responses(
    *,
    branch: str = gate.TARGET_BRANCH,
    head: str = "abc1234",
    branch_rc: int = 0,
    branch_err: str = "",
    baseline_rc: int = 0,
    baseline_err: str = "",
    ancestor_rc: int = 0,
    ancestor_err: str = "",
) -> dict[tuple[str, ...], tuple[int, str, str]]:
    return {
        ("branch", "--show-current"): (branch_rc, branch, branch_err),
        ("rev-parse", "--short", "HEAD"): (0, head, ""),
        (
            "cat-file",
            "-e",
            f"{gate.EXPECTED_BASELINE_ANCESTOR}^{{commit}}",
        ): (baseline_rc, "", baseline_err),
        (
            "merge-base",
            "--is-ancestor",
            gate.EXPECTED_BASELINE_ANCESTOR,
            "HEAD",
        ): (ancestor_rc, "", ancestor_err),
    }


def test_pr92_metadata_and_semantic_task_id_are_verified_or_marked_needs_owner_confirmation():
    report = _report()
    assert report["roadmap_pr_label"] == "PR #92"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == gate.BLUEPRINT_INDEX.as_posix()
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert "NEEDS_OWNER_CONFIRMATION" not in gate.serialize_report(report)


def test_owner_live_promotion_review_parameter_stack_packet_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["stable_selected_stack_id"] == second_report["stable_selected_stack_id"]
    assert first_report["stable_owner_review_packet_id"] == second_report["stable_owner_review_packet_id"]


def test_owner_live_promotion_review_consumes_pr91_dual_result_review_packet():
    packet = _packet()
    assert packet["upstream_dual_result_review_packet_ref"] == (
        "PR91_STATIC_DUAL_RESULT_REVIEW_PARAMETER_STACK_PACKET_SYNTHETIC_V1"
    )
    assert packet["dual_result_review_item_id"] == (
        "PR91_REVIEW_ITEM__PR87_CANDIDATE_STACK__OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE"
    )
    assert _report()["owner_review_entries_derived_only_from_pr91_dual_result_review_packet"] is True


def test_owner_live_promotion_review_traces_selected_stack_to_pr90_competition_packet():
    lineage = _review_item()["selected_stack_lineage_trace"]
    assert any(step["artifact_id"] == "PR90_QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE" for step in lineage)
    assert _review_item()["competition_by_pr90_packet_ref"] == (
        "PR90_STATIC_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_PACKET_SYNTHETIC_V1"
    )


def test_owner_live_promotion_review_traces_selected_stack_to_pr89_handoff_packet():
    lineage = _review_item()["selected_stack_lineage_trace"]
    assert any(step["artifact_id"] == "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET" for step in lineage)
    assert _review_item()["handoff_by_pr89_packet_ref"] == (
        "PR89_STATIC_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_SYNTHETIC_V1"
    )


def test_owner_live_promotion_review_traces_selected_stack_to_pr88_selection_packet():
    lineage = _review_item()["selected_stack_lineage_trace"]
    assert any(step["artifact_id"] == "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE" for step in lineage)
    assert _review_item()["selected_by_pr88_packet_ref"] == (
        "PR88_STATIC_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_PACKET_SYNTHETIC_V1"
    )


def test_owner_live_promotion_review_traces_selected_stack_to_pr87_candidate_packet():
    lineage = _review_item()["selected_stack_lineage_trace"]
    assert any(step["artifact_id"] == "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE" for step in lineage)
    assert _review_item()["candidate_from_pr87_packet_ref"] == (
        "PR87_STATIC_CANDIDATE_GENERATION_PACKET_SYNTHETIC_V1"
    )


def test_owner_live_promotion_review_preserves_trade_context_and_route_lineage():
    item = _review_item()
    assert item["trade_context_ref"] == "TRADE_CONTEXT_KALSHI_BINARY_SHORT_HORIZON_STATIC_ROUTE"
    assert item["routed_selection_universe_ref"] == "KALSHI_BINARY_SHORT_HORIZON"
    assert _report()["trade_context_and_route_lineage_preserved"] is True


def test_owner_live_promotion_review_preserves_scoring_ranking_arbitration_lineage():
    item = _review_item()
    assert item["scoring_policy_refs"]
    assert item["ranking_contract_ref"] == "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_V1"
    assert item["optimizer_arbitration_policy_ref"] == "QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_POLICY_V1"
    assert _report()["scoring_ranking_arbitration_lineage_preserved"] is True


def test_owner_live_promotion_review_preserves_quantum_policy_lineage():
    item = _review_item()
    assert item["quantum_applicability_summary"]["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert item["owner_quantum_priority_summary"]["owner_quantum_priority_mode"] == "OWNER_FORCED_QUANTUM"
    assert _report()["quantum_policy_lineage_preserved"] is True


def test_quantum_owner_live_promotion_review_requires_classical_comparator_or_fallback():
    item = _review_item()
    assert item["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert item["classical_comparator_required_flag"] is True
    assert item["classical_comparator_ref"] == "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE"


def test_static_quantum_owner_review_metadata_does_not_create_backend_execution():
    report = _report()
    assert report["quantum_metadata_consumed"] is True
    assert report["backend_execution_count"] == 0
    assert report["simulator_execution_count"] == 0
    assert report["quantum_advantage_claim_created"] is False


def test_agents_may_request_but_cannot_approve():
    item = _review_item()
    assert item["requesting_agent_authority_class"] == "AGENT_MAY_REQUEST_OWNER_DECIDES"
    assert _report()["agents_may_request"] is True
    assert _report()["agents_may_approve"] is False


def test_owner_decision_state_is_pending_in_static_fixture():
    packet = _packet()
    assert packet["owner_decision_state"] == "PENDING_OWNER_DECISION"
    assert packet["owner_decision_created_flag"] is False
    assert _review_item()["owner_decision_state"] == "PENDING_OWNER_DECISION"


def test_owner_decision_option_schema_is_not_owner_decision():
    packet = _packet()
    assert packet["owner_decision_option_set"] == list(gate.OWNER_DECISION_OPTION_ORDER)
    assert packet["owner_decision_option_authority_class"] == "STATIC_OPTION_SCHEMA_ONLY_NOT_DECISION"
    assert packet["owner_decision_created_flag"] is False


def test_owner_override_basis_is_carried_without_fabricating_external_facts():
    summary = _review_item()["owner_quantum_priority_summary"]
    assert summary["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert summary["owner_override_internal_only_flag"] is True
    assert summary["owner_override_external_fact_fabrication_created"] is False


def test_owner_approval_receipt_ref_is_boundary_not_created_receipt():
    packet = _packet()
    assert packet["owner_approval_receipt_ref"] == "STAGE1_OWNER_APPROVAL_RECEIPT_BOUNDARY_STATIC_REF_ONLY"
    assert packet["owner_approval_receipt_created_flag"] is False
    assert packet["owner_approval_receipt_created_count"] == 0


def test_owner_approval_receipt_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_OWNER_APPROVAL_RECEIPT_FABRICATION",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION",
    )


def test_owner_override_receipt_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_OWNER_OVERRIDE_RECEIPT_FABRICATION",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_OVERRIDE_RECEIPT_FABRICATION",
    )


def test_auto_promotion_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_AUTO_PROMOTION_ATTEMPT",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_AUTO_PROMOTION_FORBIDDEN",
    )


def test_live_promotion_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_LIVE_PROMOTION_ATTEMPT",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    )


def test_canary_eligibility_creation_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_CANARY_ELIGIBILITY_CREATION_ATTEMPT",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN",
    )


def test_missing_pr91_dual_result_review_packet_fails_closed():
    _assert_blocked(
        "BLOCK_MISSING_PR91_DUAL_RESULT_REVIEW_PACKET",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_PR91_DUAL_RESULT_REVIEW_PACKET",
    )


def test_non_forwardable_pr91_dual_result_review_fails_closed():
    _assert_blocked(
        "BLOCK_NON_FORWARDABLE_PR91_REVIEW",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_NON_FORWARDABLE_PR91_REVIEW",
    )


def test_missing_selected_stack_id_fails_closed():
    _assert_blocked(
        "BLOCK_MISSING_SELECTED_STACK_ID",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_SELECTED_STACK_ID",
    )


def test_blocked_candidate_cannot_enter_owner_review_active_forwardable_state():
    packet = _case_packet("BLOCK_BLOCKED_CANDIDATE")
    assert packet["valid_owner_review_item_count"] == 0
    assert packet["owner_approval_queue_forwardable_flag"] is False
    assert "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_BLOCKED_CANDIDATE" in _all_reason_codes(packet)


def test_incompatible_candidate_cannot_enter_owner_review_active_forwardable_state():
    packet = _case_packet("BLOCK_INCOMPATIBLE_CANDIDATE")
    assert packet["valid_owner_review_item_count"] == 0
    assert packet["owner_approval_queue_forwardable_flag"] is False
    assert "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_INCOMPATIBLE_CANDIDATE" in _all_reason_codes(packet)


def test_missing_role_candidate_cannot_enter_owner_review_active_forwardable_state():
    packet = _case_packet("BLOCK_MISSING_ROLE_CANDIDATE")
    assert packet["valid_owner_review_item_count"] == 0
    assert packet["owner_approval_queue_forwardable_flag"] is False
    assert "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_REQUIRED_ROLE_CANDIDATE" in _all_reason_codes(packet)


def test_source_evidence_gate_required_and_not_bypassed():
    packet = _packet()
    assert packet["source_evidence_gate_required_flag"] is True
    assert packet["source_evidence_gate_satisfied_flag"] is False
    assert packet["source_retrieval_created_flag"] is False


def test_accepted_source_packet_absence_blocks_live_promotion():
    packet = _packet()
    assert packet["accepted_source_packet_required_flag"] is True
    assert packet["accepted_source_packet_created_flag"] is False
    assert packet["live_promotion_created_flag"] is False


def test_connector_semantic_gate_required_and_not_bypassed():
    packet = _packet()
    assert packet["connector_semantic_gate_required_flag"] is True
    assert packet["connector_semantic_binding_created_flag"] is False
    assert packet["connector_binding_allowed_flag"] is False


def test_connector_binding_absence_blocks_live_promotion():
    packet = _packet()
    assert packet["connector_semantic_binding_created_flag"] is False
    assert packet["live_promotion_created_flag"] is False


def test_runtime_cash_gate_required_and_not_bypassed():
    packet = _packet()
    assert packet["runtime_cash_receipt_required_flag"] is True
    assert packet["runtime_cash_receipt_created_flag"] is False
    assert packet["runtime_cash_receipt_count"] == 0


def test_runtime_cash_receipt_absence_blocks_live_promotion():
    packet = _packet()
    assert packet["runtime_cash_receipt_created_flag"] is False
    assert packet["live_promotion_created_flag"] is False


def test_order_router_final_authority_preserved():
    packet = _packet()
    assert packet["order_router_final_authority_preserved_flag"] is True
    assert packet["order_submission_allowed_flag"] is False
    assert _review_item()["no_live_order_authority_flag"] is True


def test_order_intent_surface_remains_non_authoritative_static_preview_only_if_present():
    packet = _packet()
    assert packet["order_intent_surface_present_flag"] is True
    assert packet["order_intent_surface_authority"] == "NON_AUTHORITATIVE_STATIC_PREVIEW_ONLY"
    assert packet["executable_order_intent_created_flag"] is False


def test_owner_live_promotion_review_does_not_create_order_authority():
    assert _packet()["order_authority_created_flag"] is False
    assert _report()["order_authoritative_item_count"] == 0


def test_owner_live_promotion_review_does_not_create_live_routing():
    assert _packet()["live_routing_allowed_flag"] is False
    assert _report()["live_routing_allowed"] is False


def test_owner_live_promotion_review_does_not_bind_connector_semantics():
    assert _packet()["connector_semantic_binding_created_flag"] is False
    assert _report()["connector_semantic_binding_created"] is False


def test_owner_live_promotion_review_does_not_execute_replay_or_paper():
    assert _packet()["replay_execution_created_flag"] is False
    assert _packet()["paper_execution_created_flag"] is False
    assert _report()["replay_execution_count"] == 0
    assert _report()["paper_execution_count"] == 0


def test_owner_live_promotion_review_does_not_create_real_replay_or_paper_results():
    assert _packet()["real_replay_result_packet_created_flag"] is False
    assert _packet()["real_paper_result_packet_created_flag"] is False
    assert _report()["real_replay_paper_result_created"] is False


def test_owner_live_promotion_review_does_not_execute_classical_or_quantum_optimizer():
    assert _packet()["classical_optimizer_execution_created_flag"] is False
    assert _packet()["quantum_optimizer_execution_created_flag"] is False
    assert _packet()["optimizer_execution_created_flag"] is False
    assert _report()["real_optimizer_execution_count"] == 0


def test_owner_live_promotion_review_does_not_call_quantum_backend_or_simulator():
    assert _packet()["quantum_backend_execution_created_flag"] is False
    assert _packet()["quantum_simulator_execution_created_flag"] is False
    assert _report()["quantum_backend_execution_count"] == 0
    assert _report()["quantum_simulator_execution_count"] == 0


def test_owner_live_promotion_review_does_not_create_profit_evidence():
    assert _packet()["profit_evidence_created_flag"] is False
    assert _packet()["no_profit_evidence_flag"] is True
    assert _report()["profit_evidence_created_flag"] is False


def test_pr93_queue_forwardability_metadata_does_not_create_queue_registry():
    packet = _packet()
    assert packet["pr93_owner_approval_request_queue_required_flag"] is True
    assert packet["pr93_owner_approval_request_queue_created_flag"] is False
    assert _report()["pr93_queue_forwardability_metadata_created"] is True
    assert _report()["pr93_queue_registry_created"] is False


def test_pr94_receipt_forwardability_metadata_does_not_create_receipt_authoring_gate():
    packet = _packet()
    assert packet["pr94_owner_override_receipt_authoring_required_flag"] is True
    assert packet["pr94_owner_override_receipt_created_flag"] is False
    assert _report()["pr94_receipt_forwardability_metadata_created"] is True
    assert _report()["pr94_receipt_authoring_gate_created"] is False


def test_pr95_dashboard_menu_forwardability_metadata_does_not_create_dashboard_menu():
    packet = _packet()
    assert packet["pr95_dashboard_approval_menu_required_flag"] is True
    assert packet["pr95_dashboard_approval_menu_created_flag"] is False
    assert _report()["pr95_dashboard_menu_forwardability_metadata_created"] is True
    assert _report()["pr95_dashboard_menu_created"] is False


def test_pr96_dashboard_screen_forwardability_metadata_does_not_create_dashboard_screen():
    packet = _packet()
    assert packet["pr96_dashboard_approval_static_screen_required_flag"] is True
    assert packet["pr96_dashboard_approval_static_screen_created_flag"] is False
    assert _report()["pr96_dashboard_screen_forwardability_metadata_created"] is True
    assert _report()["pr96_dashboard_screen_created"] is False


def test_dashboard_runtime_service_not_created():
    assert _packet()["dashboard_runtime_service_created_flag"] is False
    _assert_blocked(
        "BLOCK_DASHBOARD_RUNTIME_CREATION_ATTEMPT",
        "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_DASHBOARD_RUNTIME_FORBIDDEN",
    )


def test_atomicrows_bundle_and_sha_are_not_created():
    report = _report()
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()


def test_master_plan_not_edited():
    assert _report()["master_plan_diff_empty"] is True
    assert gate.validate_master_plan_diff(REPO_ROOT) == []


def test_pr93_pr94_pr95_pr96_boundaries_preserved():
    report = _report()
    assert report["pr93_queue_forwardability_metadata_created"] is True
    assert report["pr94_receipt_forwardability_metadata_created"] is True
    assert report["pr95_dashboard_menu_forwardability_metadata_created"] is True
    assert report["pr96_dashboard_screen_forwardability_metadata_created"] is True
    assert report["pr93_queue_registry_created"] is False
    assert report["pr94_receipt_authoring_gate_created"] is False
    assert report["pr95_dashboard_menu_created"] is False
    assert report["pr96_dashboard_screen_created"] is False


def test_ci_detached_head_mode_if_validator_checks_branch_or_baseline(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _mock_git_stdout(
        monkeypatch,
        _git_metadata_responses(
            branch="",
            branch_rc=1,
            branch_err="detached HEAD",
            baseline_rc=1,
            baseline_err="shallow fetch",
        ),
    )

    failures, metadata = gate.validate_pr92_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert gate.CI_DETACHED_HEAD_MODE_MARKER in metadata["ci_info_lines"]
    assert gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER in metadata["ci_info_lines"]


def test_owner_live_promotion_review_fail_closed_boundary_cases():
    cases = {
        "BLOCK_AGENT_SELF_APPROVAL_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_AGENT_SELF_APPROVAL_FORBIDDEN",
        "BLOCK_EXECUTABLE_ORDER_INTENT_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN",
        "BLOCK_ORDER_AUTHORITY_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
        "BLOCK_LIVE_ROUTING_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_LIVE_ROUTING_FORBIDDEN",
        "BLOCK_SOURCE_RETRIEVAL_ACCEPTANCE_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN",
        "BLOCK_CONNECTOR_BINDING_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
        "BLOCK_RUNTIME_CASH_CREATION_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RUNTIME_CASH_FORBIDDEN",
        "BLOCK_PR93_QUEUE_CREATION_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR93_QUEUE_CREATION_FORBIDDEN",
        "BLOCK_PR94_RECEIPT_AUTHORING_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR94_RECEIPT_AUTHORING_FORBIDDEN",
        "BLOCK_PR95_DASHBOARD_MENU_CREATION_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR95_DASHBOARD_MENU_FORBIDDEN",
        "BLOCK_PR96_DASHBOARD_SCREEN_CREATION_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR96_DASHBOARD_SCREEN_FORBIDDEN",
        "BLOCK_ATOMICROWS_BUNDLE_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
        "BLOCK_ATOMICROWS_SHA_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
        "BLOCK_OPTIMIZER_EXECUTION_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
        "BLOCK_QUANTUM_BACKEND_EXECUTION_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
        "BLOCK_QUANTUM_SIMULATOR_EXECUTION_ATTEMPT": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
        "BLOCK_PROFIT_EVIDENCE_CLAIM": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
        "BLOCK_QUANTUM_ADVANTAGE_CLAIM": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
        "BLOCK_REPLAY_PAPER_IDENTITY_MISMATCH": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_REPLAY_PAPER_IDENTITY_MISMATCH",
        "BLOCK_RESULT_MERGE": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_MERGE_FORBIDDEN",
        "BLOCK_RESULT_OVERWRITE": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_OVERWRITE_FORBIDDEN",
        "BLOCK_RESULT_COLLAPSE": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_COLLAPSE_FORBIDDEN",
    }
    for case_id, reason_code in cases.items():
        _assert_blocked(case_id, reason_code)
