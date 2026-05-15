import json
from pathlib import Path

from tools import validate_owner_override_receipt_authoring_gate as gate


REPO_ROOT = Path(".")
_REPORT_CACHE: dict | None = None


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert gate.main([]) == 0
        _REPORT_CACHE = json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _packet() -> dict:
    return _report()["owner_override_receipt_authoring_gate_packet"]


def _entries() -> list[dict]:
    return _packet()["owner_override_receipt_entries"]


def _valid_entry() -> dict:
    for entry in _entries():
        if entry["receipt_effective_state"] == "EFFECTIVE_FOR_STATIC_INTERNAL_WORKFLOW_FIXTURE_ONLY":
            return entry
    raise AssertionError("missing valid receipt entry")


def _case_packet(case_id: str) -> dict:
    for packet in _report()["fixture_case_packets"]:
        if packet["fixture_case_id"] == case_id:
            return packet
    raise AssertionError(f"missing case packet: {case_id}")


def _all_reason_codes(packet: dict) -> set[str]:
    return set(packet.get("receipt_reason_codes", [])) | set(packet.get("blocked_reason_codes", []))


def _assert_blocked(case_id: str, reason_code: str) -> None:
    packet = _case_packet(case_id)
    assert packet["valid_receipt_count"] == 0
    assert packet["blocked_receipt_count"] >= 1
    assert reason_code in _all_reason_codes(packet)
    assert packet["owner_override_receipt_created_flag"] is False
    assert packet["owner_override_receipt_created_count"] == 0
    assert packet["owner_approval_receipt_created_count"] == 0
    assert packet["live_promotion_created_flag"] is False
    assert packet["canary_eligibility_created_flag"] is False
    assert packet["order_submission_allowed_flag"] is False
    assert packet["live_routing_allowed_flag"] is False


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


def test_pr94_metadata_and_semantic_task_id_are_verified_or_marked_needs_owner_confirmation():
    report = _report()
    assert report["roadmap_pr_label"] == "PR #94"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == gate.BLUEPRINT_INDEX.as_posix()
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert "NEEDS_OWNER_CONFIRMATION" not in gate.serialize_report(report)


def test_owner_override_receipt_authoring_gate_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["stable_receipt_gate_id"] == second_report["stable_receipt_gate_id"]
    assert first_report["stable_receipt_ids"] == second_report["stable_receipt_ids"]
    assert first_report["stable_receipt_entry_ids"] == second_report["stable_receipt_entry_ids"]


def test_owner_override_receipt_authoring_consumes_pr93_queue_registry():
    report = _report()
    packet = _packet()
    assert report["upstream_pr93_report_marker"] == "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_OK"
    assert packet["upstream_owner_approval_request_queue_registry_ref"]["artifact_id"] == (
        "PR93_QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY"
    )
    assert packet["queue_entry_count"] == 4


def test_owner_override_receipt_traces_to_pr93_queue_entry():
    packet = _packet()
    entry = _valid_entry()
    assert packet["upstream_queue_entry_ref"] == "PR93_QUEUE_ENTRY__002__OWNER_OVERRIDE_REQUEST"
    assert entry["source_queue_entry_id"] == "PR93_QUEUE_ENTRY__002__OWNER_OVERRIDE_REQUEST"
    assert entry["source_request_id"] == (
        "PR93_REQUEST__OWNER_OVERRIDE_INTERNAL_POLICY__PR87_OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK"
    )


def test_owner_override_receipt_traces_parameter_stack_lineage_when_applicable():
    report = _report()
    assert report["selected_stack_lineage_traces_to_pr92_owner_review"] is True
    assert report["selected_stack_lineage_traces_to_pr91_dual_result_review"] is True
    assert report["selected_stack_lineage_traces_to_pr90_competition"] is True
    assert report["selected_stack_lineage_traces_to_pr89_handoff"] is True
    assert report["selected_stack_lineage_traces_to_pr88_selection"] is True
    assert report["selected_stack_lineage_traces_to_pr87_candidate"] is True


def test_owner_override_receipt_satisfies_internal_workflow_requirement_only():
    packet = _packet()
    assert packet["receipt_satisfies_internal_qtt_requirement_flag"] is True
    assert packet["receipt_satisfies_external_fact_requirement_flag"] is False
    assert packet["override_scope"] == "INTERNAL_QTT_WORKFLOW_REQUIREMENT_ONLY"
    assert _valid_entry()["internal_requirement_satisfied_state"] == (
        "SATISFIED_BY_STATIC_OWNER_OVERRIDE_RECEIPT"
    )


def test_owner_override_receipt_does_not_satisfy_external_fact_requirement():
    assert _packet()["receipt_satisfies_external_fact_requirement_flag"] is False
    assert _valid_entry()["external_requirement_exclusion_state"] == (
        "EXCLUDED_NOT_SATISFIED_BY_OWNER_OVERRIDE"
    )


def test_owner_override_receipt_does_not_create_accepted_source_packet():
    packet = _packet()
    assert packet["accepted_source_packet_created_flag"] is False
    assert packet["accepted_source_packet_created_count"] == 0


def test_owner_override_receipt_does_not_create_connector_semantic_binding():
    packet = _packet()
    assert packet["connector_semantic_binding_created_flag"] is False
    assert packet["connector_binding_created_count"] == 0


def test_owner_override_receipt_does_not_create_runtime_cash_receipt():
    packet = _packet()
    assert packet["runtime_cash_receipt_created_flag"] is False
    assert packet["runtime_cash_receipt_created_count"] == 0


def test_owner_override_receipt_does_not_create_account_balance_receipt():
    packet = _packet()
    assert packet["account_balance_receipt_created_flag"] is False
    assert packet["account_balance_receipt_created_count"] == 0


def test_owner_override_receipt_does_not_create_open_order_receipt():
    packet = _packet()
    assert packet["open_order_receipt_created_flag"] is False
    assert packet["open_order_receipt_created_count"] == 0


def test_owner_override_receipt_does_not_create_order_or_fill_receipt():
    packet = _packet()
    assert packet["order_receipt_created_flag"] is False
    assert packet["fill_receipt_created_flag"] is False
    assert packet["order_receipt_created_count"] == 0
    assert packet["fill_receipt_created_count"] == 0


def test_owner_override_receipt_does_not_create_replay_or_paper_result():
    packet = _packet()
    assert packet["real_replay_result_packet_created_flag"] is False
    assert packet["real_paper_result_packet_created_flag"] is False
    assert packet["real_replay_result_packet_created_count"] == 0
    assert packet["real_paper_result_packet_created_count"] == 0


def test_owner_override_receipt_does_not_create_live_order_authority():
    packet = _packet()
    assert packet["receipt_satisfies_live_order_authority_requirement_flag"] is False
    assert packet["live_order_execution_allowed_flag"] is False
    assert packet["order_intent_authority_created_flag"] is False


def test_receipt_canonicalization_and_digest_are_deterministic():
    packet = _packet()
    assert gate._sha256(packet["canonical_receipt_payload"]) == (
        packet["owner_override_receipt_digest_or_static_ref"]
    )
    assert _valid_entry()["receipt_canonical_payload_digest"] == (
        packet["owner_override_receipt_digest_or_static_ref"]
    )


def test_receipt_idempotency_key_is_deterministic():
    packet = _packet()
    expected = gate._sha256(["OWNER_OVERRIDE_RECEIPT_IDEMPOTENCY", packet["canonical_receipt_payload"]])
    assert packet["owner_receipt_idempotency_key"] == expected
    assert _valid_entry()["idempotency_key"] == expected


def test_duplicate_receipt_is_blocked_or_deduplicated_deterministically():
    packet = _packet()
    duplicates = [
        entry
        for entry in _entries()
        if entry["receipt_effective_state"] == "BLOCKED_FAIL_CLOSED_NO_RECEIPT_CREATED"
    ]
    assert packet["duplicate_receipt_count"] == 1
    assert len(duplicates) == 1
    assert duplicates[0]["duplicate_of_receipt_id"] == packet["owner_override_receipt_id"]
    assert "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_DUPLICATE_RECEIPT_DETERMINISTIC" in (
        duplicates[0]["reason_codes"]
    )


def test_missing_pr93_queue_entry_fails_closed():
    _assert_blocked(
        "BLOCK_MISSING_PR93_QUEUE_ENTRY",
        "BLOCKED_NO_FORWARDABLE_OWNER_APPROVAL_REQUEST_FOR_OVERRIDE_RECEIPT",
    )


def test_non_forwardable_pr93_request_fails_closed():
    _assert_blocked(
        "BLOCK_NON_FORWARDABLE_PR93_REQUEST",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_NON_FORWARDABLE_PR93_REQUEST",
    )


def test_missing_owner_override_basis_fails_closed():
    _assert_blocked(
        "BLOCK_MISSING_OWNER_OVERRIDE_BASIS",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_MISSING_OWNER_OVERRIDE_BASIS",
    )


def test_agent_self_approval_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_AGENT_SELF_APPROVAL_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_AGENT_SELF_APPROVAL_FORBIDDEN",
    )


def test_external_fact_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_EXTERNAL_FACT_FABRICATION_ATTEMPT",
        "BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_OR_RECEIPT_FABRICATION",
    )


def test_accepted_source_packet_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_ACCEPTED_SOURCE_PACKET_FABRICATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_ACCEPTED_SOURCE_PACKET_FABRICATION",
    )


def test_connector_semantic_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_CONNECTOR_SEMANTIC_FABRICATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_CONNECTOR_SEMANTIC_FABRICATION",
    )


def test_runtime_cash_receipt_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_RUNTIME_CASH_RECEIPT_FABRICATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_RUNTIME_CASH_RECEIPT_FABRICATION",
    )


def test_order_receipt_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_ORDER_RECEIPT_FABRICATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_ORDER_RECEIPT_FABRICATION",
    )


def test_fill_receipt_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_FILL_RECEIPT_FABRICATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_FILL_RECEIPT_FABRICATION",
    )


def test_replay_result_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_REPLAY_RESULT_FABRICATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_REPLAY_RESULT_FABRICATION",
    )


def test_paper_result_fabrication_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_PAPER_RESULT_FABRICATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_PAPER_RESULT_FABRICATION",
    )


def test_live_promotion_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_LIVE_PROMOTION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_LIVE_PROMOTION",
    )


def test_canary_eligibility_creation_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_CANARY_ELIGIBILITY_CREATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_CANARY_ELIGIBILITY",
    )


def test_order_authority_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_ORDER_AUTHORITY_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_ORDER_AUTHORITY",
    )


def test_live_routing_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_LIVE_ROUTING_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_LIVE_ROUTING",
    )


def test_source_retrieval_or_acceptance_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_SOURCE_RETRIEVAL_ACCEPTANCE_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE",
    )


def test_replay_or_paper_execution_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_REPLAY_EXECUTION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_REPLAY_EXECUTION",
    )
    _assert_blocked(
        "BLOCK_PAPER_EXECUTION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_PAPER_EXECUTION",
    )


def test_classical_or_quantum_optimizer_execution_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_CLASSICAL_QUANTUM_OPTIMIZER_EXECUTION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_OPTIMIZER_EXECUTION",
    )


def test_quantum_backend_or_simulator_execution_attempt_fails_closed():
    _assert_blocked(
        "BLOCK_QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_QUANTUM_BACKEND_EXECUTION",
    )
    assert _case_packet("BLOCK_QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION_ATTEMPT")[
        "quantum_simulator_execution_count"
    ] == 0


def test_profit_evidence_claim_fails_closed():
    _assert_blocked(
        "BLOCK_PROFIT_EVIDENCE_CLAIM",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_PROFIT_EVIDENCE",
    )


def test_quantum_advantage_claim_fails_closed():
    _assert_blocked(
        "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_QUANTUM_ADVANTAGE",
    )


def test_pr95_forwardability_metadata_does_not_create_dashboard_menu():
    packet = _packet()
    assert packet["pr95_dashboard_approval_menu_forwardable_flag"] is True
    assert packet["pr95_dashboard_approval_menu_created_flag"] is False
    _assert_blocked(
        "BLOCK_DASHBOARD_MENU_CREATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_PR95_DASHBOARD_MENU_CREATION",
    )


def test_pr96_forwardability_metadata_does_not_create_dashboard_screen():
    packet = _packet()
    assert packet["pr96_dashboard_approval_static_screen_forwardable_flag"] is True
    assert packet["pr96_dashboard_approval_static_screen_created_flag"] is False
    _assert_blocked(
        "BLOCK_DASHBOARD_SCREEN_CREATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_PR96_DASHBOARD_SCREEN_CREATION",
    )


def test_dashboard_runtime_service_not_created():
    assert _packet()["dashboard_runtime_service_created_flag"] is False
    _assert_blocked(
        "BLOCK_DASHBOARD_RUNTIME_CREATION_ATTEMPT",
        "OWNER_OVERRIDE_RECEIPT_AUTHORING_BLOCKED_DASHBOARD_RUNTIME_CREATION",
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


def test_main_branch_allowed_for_cumulative_validation(monkeypatch):
    _mock_git_stdout(monkeypatch, _git_metadata_responses(branch="main"))

    failures, metadata = gate.validate_pr94_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert metadata["branch"] == "main"
    assert gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER in metadata["ci_info_lines"]


def test_non_downstream_branch_still_fails_branch_strict_validation(monkeypatch):
    branch = "feature/non-downstream-validation"
    _mock_git_stdout(monkeypatch, _git_metadata_responses(branch=branch))

    failures, metadata = gate.validate_pr94_roadmap_metadata(REPO_ROOT)

    assert f"current branch must be {gate.TARGET_BRANCH}, got {branch}" in failures
    assert metadata["branch"] == branch


def test_pr95_pr96_boundaries_preserved():
    report = _report()
    assert report["pr95_dashboard_menu_forwardability_metadata_created"] is True
    assert report["pr95_dashboard_menu_created"] is False
    assert report["pr96_dashboard_screen_forwardability_metadata_created"] is True
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

    failures, metadata = gate.validate_pr94_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert gate.CI_DETACHED_HEAD_MODE_MARKER in metadata["ci_info_lines"]
    assert gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER in metadata["ci_info_lines"]
