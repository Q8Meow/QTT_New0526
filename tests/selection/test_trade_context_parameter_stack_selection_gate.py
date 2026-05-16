import json
from pathlib import Path

from tools import validate_trade_context_parameter_stack_selection_gate as gate


REPO_ROOT = Path(".")
_REPORT_CACHE: dict | None = None


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _fixture() -> dict:
    return json.loads((REPO_ROOT / gate.DEFAULT_FIXTURE).read_text(encoding="utf-8"))


def _upstream() -> dict:
    failures, upstream = gate.validate_upstream_reports(REPO_ROOT)
    assert failures == []
    return upstream


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert gate.main([]) == 0
        _REPORT_CACHE = json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _case_packet(report: dict, case_id: str) -> dict:
    for packet in report["fixture_case_packets"]:
        if packet["fixture_case_id"] == case_id:
            return packet
    raise AssertionError(f"missing case packet: {case_id}")


def _all_reason_codes(packet: dict) -> set[str]:
    return set(packet["selection_reason_codes"]) | set(packet["blocked_or_rejected_candidate_reason_codes"])


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
    baseline_rc: int = 0,
    baseline_err: str = "",
    ancestor_rc: int = 0,
    ancestor_err: str = "",
) -> dict[tuple[str, ...], tuple[int, str, str]]:
    return {
        ("branch", "--show-current"): (0, branch, ""),
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


def test_pr88_metadata_and_semantic_task_id_are_verified_or_marked_needs_owner_confirmation():
    report = _report()
    assert report["roadmap_pr_label"] == "PR #88"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == gate.BLUEPRINT_INDEX.as_posix()
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert "NEEDS_OWNER_CONFIRMATION" not in gate.serialize_report(report)


def test_trade_context_stack_selection_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["deterministic_selection_key"] == second_report["deterministic_selection_key"]
    assert first_report["static_selected_candidate_stack_id"] == second_report["static_selected_candidate_stack_id"]


def test_trade_context_stack_selection_selects_one_eligible_candidate_from_valid_multi_candidate_fixture():
    report = _report()
    packet = _case_packet(report, "PASS_VALID_MULTI_CANDIDATE_TRADE_CONTEXT_SELECTION")
    assert packet["selected_candidate_count"] == 1
    assert packet["selected_candidate_stack_id"] == (
        "PR87_CANDIDATE_STACK__OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE"
    )
    selected = packet["static_selected_candidate_descriptor"]
    assert selected["eligibility_status"] == "ELIGIBLE_FOR_STATIC_SELECTION"
    assert selected["route_match_state"] == "ROUTE_MATCH"
    assert selected["trade_context_match_state"] == "TRADE_CONTEXT_MATCH"
    assert selected["candidate_stack_id"] in report["pr87_active_candidate_stack_ids"]


def test_trade_context_stack_selection_rejects_route_mismatch():
    packet = _case_packet(_report(), "PASS_ROUTE_MISMATCH_REJECTED")
    assert packet["selected_candidate_count"] == 0
    assert "TRADE_CONTEXT_SELECTION_BLOCKED_ROUTE_MISMATCH" in _all_reason_codes(packet)


def test_trade_context_stack_selection_rejects_blocked_candidate():
    packet = _case_packet(_report(), "PASS_BLOCKED_CANDIDATE_REJECTED")
    assert packet["selected_candidate_count"] == 0
    assert "TRADE_CONTEXT_SELECTION_BLOCKED_CANDIDATE_STATUS" in _all_reason_codes(packet)


def test_trade_context_stack_selection_rejects_missing_required_role():
    packet = _case_packet(_report(), "PASS_MISSING_REQUIRED_ROLE_REJECTED")
    assert packet["selected_candidate_count"] == 0
    assert "TRADE_CONTEXT_SELECTION_BLOCKED_MISSING_REQUIRED_ROLE" in _all_reason_codes(packet)


def test_trade_context_stack_selection_rejects_incompatible_candidate():
    packet = _case_packet(_report(), "PASS_INCOMPATIBLE_CANDIDATE_REJECTED")
    assert packet["selected_candidate_count"] == 0
    assert "TRADE_CONTEXT_SELECTION_BLOCKED_INCOMPATIBLE_CANDIDATE" in _all_reason_codes(packet)


def test_trade_context_stack_selection_fail_closed_when_no_eligible_candidate():
    packet = _case_packet(_report(), "PASS_NO_ELIGIBLE_CANDIDATE_FAILS_CLOSED")
    assert packet["packet_status"] == "BLOCKED_NO_ELIGIBLE_CANDIDATE_STACK"
    assert packet["selected_candidate_count"] == 0
    assert packet["selected_candidate_stack_id"] is None
    assert "TRADE_CONTEXT_SELECTION_BLOCKED_NO_ELIGIBLE_CANDIDATE_STACK" in packet["selection_reason_codes"]


def test_trade_context_stack_selection_deterministic_tie_break_is_stable():
    fixture = _fixture()
    upstream = _upstream()
    packet_one, failures_one = gate.build_trade_context_parameter_stack_selection_packet(
        _registry(),
        fixture,
        upstream,
        case_id="PASS_DETERMINISTIC_TIE_BREAK",
    )
    packet_two, failures_two = gate.build_trade_context_parameter_stack_selection_packet(
        _registry(),
        fixture,
        upstream,
        case_id="PASS_DETERMINISTIC_TIE_BREAK",
    )
    assert failures_one == []
    assert failures_two == []
    assert gate.serialize_report(packet_one) == gate.serialize_report(packet_two)
    assert packet_one["selected_candidate_stack_id"] == packet_two["selected_candidate_stack_id"]
    assert "TRADE_CONTEXT_SELECTION_ALLOWED_DETERMINISTIC_TIE_BREAK" in packet_one["selection_reason_codes"]


def test_trade_context_stack_selection_does_not_create_pr89_handoff_packet():
    report = _report()
    packet = _case_packet(report, "PASS_PR89_PR90_BOUNDARY_FORWARDABLE_NOT_HANDED_OFF")
    assert packet["selected_stack_handoff_created_flag"] is False
    assert report["selected_stack_handoff_packet_created"] is False
    assert report["pr89_selected_stack_handoff_packet_created"] is False
    assert report["future_pr89_selected_stack_handoff_implemented"] is False


def test_trade_context_stack_selection_does_not_create_order_authority():
    report = _report()
    assert report["live_order_authority"] is False
    assert report["order_authority_created"] is False
    assert report["order_submission_created"] is False
    assert report["trade_context_parameter_stack_selection_packet"]["no_order_authority_flag"] is True


def test_trade_context_stack_selection_does_not_execute_replay_or_paper():
    report = _report()
    assert report["replay_execution_count"] == 0
    assert report["paper_execution_count"] == 0
    assert report["replay_execution_created"] is False
    assert report["paper_execution_created"] is False
    assert report["replay_paper_result_packet_created"] is False


def test_trade_context_stack_selection_does_not_execute_classical_or_quantum_optimizer():
    report = _report()
    assert report["real_optimizer_execution_count"] == 0
    assert report["classical_optimizer_execution_created"] is False
    assert report["quantum_optimizer_execution_created"] is False
    assert report["optimizer_execution_created"] is False


def test_trade_context_stack_selection_does_not_call_quantum_backend_or_simulator():
    report = _report()
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_simulator_execution_created"] is False


def test_quantum_candidate_selection_requires_classical_comparator_or_fallback():
    selected_packet = _case_packet(_report(), "PASS_QUANTUM_PREFERRED_WITH_CLASSICAL_COMPARATOR_SELECTED")
    selected = selected_packet["static_selected_candidate_descriptor"]
    assert selected["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert selected["classical_comparator_required_flag"] is True
    assert selected["classical_comparator_ref"] == "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE"

    blocked_packet = _case_packet(_report(), "PASS_QUANTUM_PREFERRED_BLOCKED_WITHOUT_COMPARATOR")
    assert blocked_packet["selected_candidate_count"] == 0
    assert "TRADE_CONTEXT_SELECTION_BLOCKED_MISSING_CLASSICAL_COMPARATOR" in _all_reason_codes(blocked_packet)


def test_owner_quantum_priority_is_static_policy_metadata_only():
    report = _report()
    selected = report["trade_context_parameter_stack_selection_packet"]["static_selected_candidate_descriptor"]
    assert selected["owner_quantum_priority_summary"]["owner_quantum_priority_mode"] == "OWNER_FORCED_QUANTUM"
    assert report["owner_quantum_priority_static_policy_metadata_only"] is True
    assert report["owner_quantum_priority_fabricates_external_facts"] is False
    assert report["quantum_metadata_static_advisory_policy_gated"] is True


def test_owner_override_records_basis_without_fabricating_external_facts():
    report = _report()
    selected = report["trade_context_parameter_stack_selection_packet"]["static_selected_candidate_descriptor"]
    assert selected["owner_quantum_priority_summary"]["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert selected["owner_quantum_priority_summary"]["owner_override_internal_only_flag"] is True
    assert selected["owner_quantum_priority_summary"]["owner_override_external_fact_fabrication_created"] is False
    assert report["owner_override_records_basis_without_external_fact_fabrication"] is True
    assert report["owner_override_fabricates_external_facts"] is False


def test_atomicrows_bundle_and_sha_are_not_created():
    report = _report()
    assert report["atomicrows_bundle_jsonl_exists"] is True
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()


def test_master_plan_not_edited():
    report = _report()
    assert report["master_plan_diff_empty"] is True
    assert gate.validate_master_plan_diff(REPO_ROOT) == []


def test_pr89_and_pr90_boundaries_preserved():
    report = _report()
    packet = _case_packet(report, "PASS_PR89_PR90_BOUNDARY_FORWARDABLE_NOT_HANDED_OFF")
    assert packet["pr89_selected_stack_handoff_required_flag"] is True
    assert packet["replay_paper_competition_required_flag"] is True
    assert packet["selected_stack_handoff_created_flag"] is False
    assert packet["replay_execution_created"] is False
    assert packet["paper_execution_created"] is False
    assert report["future_pr89_selected_stack_handoff_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False


def test_ci_detached_head_mode_if_validator_checks_branch_or_baseline(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _mock_git_stdout(
        monkeypatch,
        _git_metadata_responses(branch=""),
    )

    failures, metadata = gate.validate_pr88_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert metadata["branch"] == ""
    assert metadata["ci_info_lines"] == (gate.CI_DETACHED_HEAD_MODE_MARKER,)
