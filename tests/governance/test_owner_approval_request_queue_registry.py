import json
from pathlib import Path

from tools import validate_owner_approval_request_queue_registry as gate


REPO_ROOT = Path(".")
_REPORT_CACHE: dict | None = None


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert gate.main([]) == 0
        _REPORT_CACHE = json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _packet() -> dict:
    return _report()["owner_approval_request_queue_registry_packet"]


def _entries() -> list[dict]:
    return _packet()["queue_entries"]


def _entry(request_type: str) -> dict:
    for entry in _entries():
        if entry["request_type"] == request_type and entry["valid_queue_entry_flag"] is True:
            return entry
    raise AssertionError(f"missing valid request entry: {request_type}")


def _case_packet(case_id: str) -> dict:
    for packet in _report()["fixture_case_packets"]:
        if packet["fixture_case_id"] == case_id:
            return packet
    raise AssertionError(f"missing case packet: {case_id}")


def _all_reason_codes(packet: dict) -> set[str]:
    return set(packet.get("queue_reason_codes", [])) | set(packet.get("blocked_reason_codes", []))


def _assert_blocked(case_id: str, reason_code: str) -> None:
    packet = _case_packet(case_id)
    assert packet["valid_request_count"] == 0
    assert packet["blocked_request_count"] >= 1
    assert reason_code in _all_reason_codes(packet)
    assert packet["owner_decision_created_flag"] is False
    assert packet["owner_approval_receipt_created_flag"] is False
    assert packet["owner_override_receipt_created_flag"] is False
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


def test_pr93_metadata_and_semantic_task_id_are_verified_or_marked_needs_owner_confirmation():
    report = _report()
    assert report["roadmap_pr_label"] == "PR #93"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == gate.BLUEPRINT_INDEX.as_posix()
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert "NEEDS_OWNER_CONFIRMATION" not in gate.serialize_report(report)


def test_owner_approval_request_queue_registry_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["stable_queue_registry_id"] == second_report["stable_queue_registry_id"]
    assert first_report["stable_queue_entry_ids"] == second_report["stable_queue_entry_ids"]
    assert first_report["stable_request_ids"] == second_report["stable_request_ids"]


def test_owner_approval_request_queue_consumes_pr92_owner_review_packet():
    packet = _packet()
    assert packet["upstream_owner_live_promotion_review_packet_ref"] == (
        "PR92_STATIC_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACK_PACKET_SYNTHETIC_V1"
    )
    assert _report()["pr92_owner_live_promotion_review_report_marker"] == (
        "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_OK"
    )


def test_owner_approval_request_queue_traces_selected_stack_to_pr91_dual_review_packet():
    assert _report()["selected_stack_lineage_traces_to_pr91_dual_result_review_packet"] is True
    assert any(
        step["artifact_id"] == "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS"
        for step in _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")["selected_stack_lineage_trace"]
    )


def test_owner_approval_request_queue_traces_selected_stack_to_pr90_competition_packet():
    assert _report()["selected_stack_lineage_traces_to_pr90_competition_packet"] is True


def test_owner_approval_request_queue_traces_selected_stack_to_pr89_handoff_packet():
    assert _report()["selected_stack_lineage_traces_to_pr89_handoff_packet"] is True


def test_owner_approval_request_queue_traces_selected_stack_to_pr88_selection_packet():
    assert _report()["selected_stack_lineage_traces_to_pr88_selection_packet"] is True


def test_owner_approval_request_queue_traces_selected_stack_to_pr87_candidate_packet():
    assert _report()["selected_stack_lineage_traces_to_pr87_candidate_packet"] is True


def test_agents_may_request_but_cannot_approve():
    entry = _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")
    assert entry["requesting_agent_authority_class"] == "AGENT_MAY_REQUEST_OWNER_DECIDES"
    assert _report()["agents_may_request"] is True
    assert _report()["agents_may_approve"] is False


def test_owner_decision_state_is_pending_in_static_queue():
    packet = _packet()
    assert packet["owner_decision_state"] == "PENDING_OWNER_DECISION"
    assert packet["pending_owner_decision_count"] == 3
    assert all(
        entry["owner_decision_state"] == "PENDING_OWNER_DECISION"
        for entry in _entries()
        if entry["valid_queue_entry_flag"] is True
    )


def test_owner_decision_options_are_not_owner_decisions():
    packet = _packet()
    assert packet["owner_decision_option_set"] == list(gate.OWNER_DECISION_OPTION_ORDER)
    assert packet["owner_decision_option_authority_class"] == "STATIC_OPTION_SCHEMA_ONLY_NOT_DECISION"
    assert packet["owner_decision_created_flag"] is False


def test_owner_approval_receipt_ref_is_boundary_not_created_receipt():
    entry = _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")
    assert "stage1_owner_approval_receipt_boundary.schema.json" in entry["owner_approval_receipt_ref"]
    assert entry["owner_approval_receipt_created_flag"] is False
    assert _packet()["owner_approval_receipt_created_count"] == 0


def test_owner_override_receipt_ref_is_boundary_not_created_receipt():
    entry = _entry("OWNER_OVERRIDE_REQUEST")
    assert entry["owner_override_receipt_ref"] == (
        "schemas/governance/qtt_owner_override_receipt.schema.json#future-pr94-boundary-ref-only"
    )
    assert entry["owner_override_receipt_created_flag"] is False
    assert _packet()["owner_override_receipt_created_count"] == 0


def test_owner_override_request_records_basis_without_fabricating_external_facts():
    entry = _entry("OWNER_OVERRIDE_REQUEST")
    assert "OWNER_OVERRIDE_REQUESTED_FOR_INTERNAL_QTT_WORKFLOW_ONLY" in entry["request_reason_codes"]
    assert "EXTERNAL_FACT_FABRICATION_FORBIDDEN" in entry["request_reason_codes"]
    assert entry["source_retrieval_created_flag"] is False
    assert entry["connector_semantic_binding_created_flag"] is False
    assert entry["runtime_cash_receipt_created_flag"] is False


def test_duplicate_request_handling_is_deterministic():
    packet = _packet()
    duplicates = [
        entry for entry in packet["queue_entries"] if entry["request_status"] == "BLOCKED_DUPLICATE_REQUEST"
    ]
    assert packet["duplicate_request_count"] == 1
    assert len(duplicates) == 1
    assert duplicates[0]["duplicate_of_request_id"] == (
        "PR93_REQUEST__OWNER_OVERRIDE_INTERNAL_POLICY__PR87_OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK"
    )
    assert "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DUPLICATE_REQUEST_COLLISION" in duplicates[0]["blocked_reason_codes"]


def test_queue_ordering_is_stable():
    report = _report()
    assert report["deterministic_queue_ordering"] is True
    assert report["stable_queue_entry_ids"] == [
        "PR93_QUEUE_ENTRY__001__LIVE_PROMOTION_OWNER_APPROVAL_REQUEST",
        "PR93_QUEUE_ENTRY__002__OWNER_OVERRIDE_REQUEST",
        "PR93_QUEUE_ENTRY__003__DASHBOARD_APPROVAL_REQUEST",
        "PR93_QUEUE_ENTRY__004__DUPLICATE_OWNER_OVERRIDE_REQUEST_BLOCKED",
    ]


def test_missing_request_basis_fails_closed():
    _assert_blocked(
        "BLOCK_MISSING_REQUEST_BASIS",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_REQUEST_BASIS",
    )


def test_missing_pr92_owner_review_packet_fails_closed():
    _assert_blocked(
        "BLOCK_MISSING_PR92_OWNER_REVIEW_PACKET",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_PR92_OWNER_REVIEW_PACKET",
    )


def test_non_forwardable_pr92_owner_review_fails_closed():
    _assert_blocked(
        "BLOCK_NON_FORWARDABLE_PR92_OWNER_REVIEW",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_NON_FORWARDABLE_PR92_OWNER_REVIEW",
    )


def test_missing_selected_stack_id_fails_closed():
    _assert_blocked(
        "BLOCK_MISSING_SELECTED_STACK_ID",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_SELECTED_STACK_ID",
    )


def test_untraceable_selected_stack_fails_closed():
    _assert_blocked(
        "BLOCK_UNTRACEABLE_SELECTED_STACK",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_UNTRACEABLE_SELECTED_STACK",
    )


def test_blocked_candidate_lineage_cannot_enter_active_approval_queue():
    _assert_blocked(
        "BLOCK_BLOCKED_CANDIDATE_LINEAGE",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_BLOCKED_CANDIDATE_LINEAGE",
    )


def test_incompatible_candidate_lineage_cannot_enter_active_approval_queue():
    _assert_blocked(
        "BLOCK_INCOMPATIBLE_CANDIDATE_LINEAGE",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_INCOMPATIBLE_CANDIDATE_LINEAGE",
    )


def test_missing_role_candidate_lineage_cannot_enter_active_approval_queue():
    _assert_blocked(
        "BLOCK_MISSING_ROLE_CANDIDATE_LINEAGE",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_ROLE_CANDIDATE_LINEAGE",
    )


def test_source_evidence_dependency_blocks_live_promotion_authority():
    packet = _packet()
    assert packet["source_retrieval_count"] == 0
    assert _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")["source_evidence_gate_state"] == (
        "REQUIRED_NOT_SATISFIED_BLOCKS_APPROVAL_AND_LIVE_PROMOTION"
    )
    assert packet["live_promotion_created_flag"] is False


def test_connector_semantic_dependency_blocks_live_promotion_authority():
    entry = _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")
    assert entry["connector_semantic_binding_required_flag"] is True
    assert entry["connector_semantic_binding_created_flag"] is False
    assert entry["live_promotion_created_flag"] is False


def test_runtime_cash_dependency_blocks_live_promotion_authority():
    entry = _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")
    assert entry["runtime_cash_receipt_required_flag"] is True
    assert entry["runtime_cash_receipt_created_flag"] is False
    assert entry["live_promotion_created_flag"] is False


def test_risk_dependency_blocks_live_promotion_authority():
    entry = _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")
    assert entry["risk_gate_state"] == "REVIEW_REQUIRED_BLOCKS_LIVE_PROMOTION"
    assert entry["live_promotion_created_flag"] is False


def test_order_router_dependency_blocks_live_promotion_authority():
    entry = _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")
    assert entry["order_router_gate_state"] == "FINAL_AUTHORITY_PRESERVED_BLOCKS_DIRECT_ORDER"
    assert entry["order_submission_allowed_flag"] is False
    assert entry["live_promotion_created_flag"] is False


def test_dashboard_dependency_blocks_live_promotion_authority():
    entry = _entry("DASHBOARD_APPROVAL_REQUEST")
    assert entry["dashboard_gate_state"] == "FUTURE_PR95_PR96_DASHBOARD_APPROVAL_SURFACES_REQUIRED_NOT_CREATED"
    assert entry["dashboard_runtime_service_created_flag"] is False
    assert entry["live_promotion_created_flag"] is False


def test_order_router_final_authority_preserved():
    packet = _packet()
    assert packet["order_router_final_authority_preserved_flag"] is True
    assert packet["order_submission_allowed_flag"] is False
    assert _report()["live_order_authority_created"] is False


def test_quantum_backend_enablement_request_does_not_execute_backend():
    case = _case_packet("PASS_QUANTUM_BACKEND_ENABLEMENT_REQUEST_METADATA_ONLY")
    entry = case["queue_entries"][0]
    assert entry["quantum_backend_enablement_requested_flag"] is True
    assert entry["quantum_backend_enablement_allowed_flag"] is False
    assert case["quantum_backend_execution_count"] == 0
    assert case["quantum_simulator_execution_count"] == 0


def test_quantum_request_preserves_classical_comparator_or_fallback():
    entry = _entry("LIVE_PROMOTION_OWNER_APPROVAL_REQUEST")
    assert entry["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert entry["classical_comparator_required_flag"] is True
    assert entry["classical_comparator_ref"] or entry["classical_fallback_ref"]
    assert _report()["classical_comparator_fallback_preserved"] is True


def test_agent_self_approval_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_AGENT_SELF_APPROVAL_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_AGENT_SELF_APPROVAL_FORBIDDEN",
    )


def test_owner_approval_receipt_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_OWNER_APPROVAL_RECEIPT_FABRICATION",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION",
    )


def test_owner_override_receipt_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_OWNER_OVERRIDE_RECEIPT_FABRICATION",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OWNER_OVERRIDE_RECEIPT_FABRICATION",
    )


def test_auto_approval_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_AUTO_APPROVAL_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_AUTO_APPROVAL_FORBIDDEN",
    )


def test_live_promotion_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_LIVE_PROMOTION_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    )


def test_canary_eligibility_creation_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_CANARY_ELIGIBILITY_CREATION_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN",
    )


def test_order_authority_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_ORDER_AUTHORITY_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    )


def test_live_routing_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_LIVE_ROUTING_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    )


def test_source_retrieval_or_acceptance_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_SOURCE_RETRIEVAL_ACCEPTANCE_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN",
    )


def test_connector_binding_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_CONNECTOR_BINDING_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    )


def test_runtime_cash_receipt_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_RUNTIME_CASH_CREATION_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_RUNTIME_CASH_FORBIDDEN",
    )


def test_replay_or_paper_execution_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_REPLAY_PAPER_DEPENDENCY_BYPASS",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_REPLAY_OR_PAPER_EXECUTION_FORBIDDEN",
    )


def test_real_replay_or_paper_result_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_REAL_REPLAY_OR_PAPER_RESULT_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_REAL_REPLAY_OR_PAPER_RESULT_FORBIDDEN",
    )


def test_classical_or_quantum_optimizer_execution_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_CLASSICAL_OR_QUANTUM_OPTIMIZER_EXECUTION_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    )


def test_quantum_backend_or_simulator_execution_attempt_fails_closed():
    case = _case_packet("BLOCK_QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION_ATTEMPT")
    assert case["valid_request_count"] == 0
    assert (
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN"
        in _all_reason_codes(case)
    )
    assert case["quantum_backend_execution_count"] == 0
    assert case["quantum_simulator_execution_count"] == 0


def test_dashboard_runtime_service_not_created():
    assert _packet()["dashboard_runtime_service_created_flag"] is False
    _assert_blocked(
        "BLOCK_DASHBOARD_RUNTIME_CREATION_ATTEMPT",
        "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DASHBOARD_RUNTIME_FORBIDDEN",
    )


def test_pr94_forwardability_metadata_does_not_create_receipt_authoring_gate():
    report = _report()
    assert report["pr94_receipt_forwardability_metadata_created"] is True
    assert report["pr94_receipt_authoring_gate_created"] is False
    assert _entry("OWNER_OVERRIDE_REQUEST")["pr94_owner_override_receipt_authoring_required_flag"] is True


def test_pr95_forwardability_metadata_does_not_create_dashboard_menu():
    report = _report()
    assert report["pr95_dashboard_menu_forwardability_metadata_created"] is True
    assert report["pr95_dashboard_menu_created"] is False
    assert _entry("DASHBOARD_APPROVAL_REQUEST")["pr95_dashboard_approval_menu_required_flag"] is True


def test_pr96_forwardability_metadata_does_not_create_dashboard_screen():
    report = _report()
    assert report["pr96_dashboard_screen_forwardability_metadata_created"] is True
    assert report["pr96_dashboard_screen_created"] is False
    assert _entry("DASHBOARD_APPROVAL_REQUEST")["pr96_dashboard_approval_static_screen_required_flag"] is True


def test_atomicrows_bundle_and_sha_are_not_created():
    report = _report()
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()


def test_master_plan_not_edited():
    assert _report()["master_plan_diff_empty"] is True
    assert gate.validate_master_plan_diff(REPO_ROOT) == []


def test_pr94_pr95_pr96_boundaries_preserved():
    report = _report()
    assert report["pr94_receipt_forwardability_metadata_created"] is True
    assert report["pr95_dashboard_menu_forwardability_metadata_created"] is True
    assert report["pr96_dashboard_screen_forwardability_metadata_created"] is True
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

    failures, metadata = gate.validate_pr93_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert gate.CI_DETACHED_HEAD_MODE_MARKER in metadata["ci_info_lines"]
    assert gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER in metadata["ci_info_lines"]
