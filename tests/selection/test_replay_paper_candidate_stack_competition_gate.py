import json
from pathlib import Path

from tools import validate_replay_paper_candidate_stack_competition_gate as gate


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


def _packet() -> dict:
    return _report()["replay_paper_candidate_stack_competition_packet"]


def _entry() -> dict:
    entries = _packet()["competition_entries"]
    assert len(entries) == 1
    return entries[0]


def _case_packet(report: dict, case_id: str) -> dict:
    for packet in report["fixture_case_packets"]:
        if packet["fixture_case_id"] == case_id:
            return packet
    raise AssertionError(f"missing case packet: {case_id}")


def _all_reason_codes(packet: dict) -> set[str]:
    blocked = {
        code
        for item in packet["blocked_competition_entries"]
        for code in item.get("blocked_reason_codes", [])
    }
    return set(packet["selection_reason_codes"]) | blocked


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


def test_pr90_metadata_and_semantic_task_id_are_verified_or_marked_needs_owner_confirmation():
    report = _report()
    assert report["roadmap_pr_label"] == "PR #90"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == gate.BLUEPRINT_INDEX.as_posix()
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert "NEEDS_OWNER_CONFIRMATION" not in gate.serialize_report(report)


def test_replay_paper_candidate_stack_competition_packet_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["selected_stack_id"] == second_report["selected_stack_id"]
    assert first_report["replay_paper_input_identity_digest_or_static_ref"] == (
        second_report["replay_paper_input_identity_digest_or_static_ref"]
    )


def test_competition_packet_consumes_pr89_selected_stack_handoff_packet():
    packet = _packet()
    assert packet["upstream_selected_stack_handoff_packet_ref"] == (
        "PR89_STATIC_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_SYNTHETIC_V1"
    )
    assert packet["selected_stack_id"] == (
        "PR87_CANDIDATE_STACK__OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE"
    )
    assert "REPLAY_PAPER_COMPETITION_ALLOWED_PR89_HANDOFF_PACKET" in packet["selection_reason_codes"]


def test_competition_packet_traces_selected_stack_to_pr88_selection_packet():
    packet = _packet()
    assert packet["upstream_trade_context_selection_packet_ref"] == (
        "PR88_STATIC_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_PACKET_SYNTHETIC_V1"
    )
    assert any(
        step["artifact_id"] == "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE"
        for step in packet["selected_stack_lineage_trace"]
    )


def test_competition_packet_traces_selected_stack_to_pr87_candidate_packet():
    packet = _packet()
    assert packet["upstream_candidate_generation_packet_ref"] == (
        "PR87_STATIC_CANDIDATE_GENERATION_PACKET_SYNTHETIC_V1"
    )
    assert any(
        step["artifact_id"] == "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE"
        for step in packet["selected_stack_lineage_trace"]
    )


def test_competition_packet_preserves_trade_context_and_route_lineage():
    packet = _packet()
    entry = _entry()
    assert packet["upstream_trade_context_ref"] == "TRADE_CONTEXT_KALSHI_BINARY_SHORT_HORIZON_STATIC_ROUTE"
    assert packet["upstream_routed_selection_universe_ref"] == "KALSHI_BINARY_SHORT_HORIZON"
    assert entry["trade_context_ref"] == packet["upstream_trade_context_ref"]
    assert entry["routed_selection_universe_ref"] == packet["upstream_routed_selection_universe_ref"]


def test_competition_packet_preserves_scoring_ranking_arbitration_lineage():
    packet = _packet()
    entry = _entry()
    assert entry["scoring_policy_refs"]
    assert entry["ranking_contract_ref"] == "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_V1"
    assert entry["optimizer_arbitration_policy_ref"] == "QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_POLICY_V1"
    assert "REPLAY_PAPER_COMPETITION_ALLOWED_SCORING_RANKING_ARBITRATION_LINEAGE" in packet["selection_reason_codes"]


def test_competition_packet_preserves_quantum_policy_lineage():
    packet = _packet()
    entry = _entry()
    assert entry["quantum_applicability_summary"]["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert entry["owner_quantum_priority_summary"]["owner_quantum_priority_mode"] == "OWNER_FORCED_QUANTUM"
    assert "REPLAY_PAPER_COMPETITION_ALLOWED_QUANTUM_POLICY_LINEAGE" in packet["selection_reason_codes"]


def test_quantum_competition_entry_requires_classical_comparator_or_fallback():
    entry = _entry()
    assert entry["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert entry["classical_comparator_required_flag"] is True
    assert entry["classical_comparator_ref"] == "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE"


def test_classical_comparator_and_quantum_candidate_can_be_declared_as_static_competition_pair_without_backend_execution():
    report = _report()
    entry = _entry()
    assert entry["competition_role"] == "HYBRID_STATIC_PAIR"
    assert entry["static_competition_pair_id"]
    assert report["quantum_classical_static_competition_pair_declared"] is True
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0


def test_owner_override_basis_is_carried_without_fabricating_external_facts():
    report = _report()
    summary = _entry()["owner_quantum_priority_summary"]
    assert summary["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert summary["owner_override_internal_only_flag"] is True
    assert summary["owner_override_external_fact_fabrication_created"] is False
    assert report["owner_override_records_basis_without_external_fact_fabrication"] is True


def test_missing_pr89_handoff_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_MISSING_PR89_HANDOFF_PACKET")
    assert packet["eligible_competition_entry_count"] == 0
    assert packet["selected_stack_id"] is None
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_PR89_HANDOFF_PACKET" in _all_reason_codes(packet)


def test_missing_selected_stack_id_fails_closed():
    packet = _case_packet(_report(), "BLOCK_MISSING_SELECTED_STACK_ID")
    assert packet["eligible_competition_entry_count"] == 0
    assert packet["selected_stack_id"] is None
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_SELECTED_STACK_ID" in _all_reason_codes(packet)


def test_untraceable_selected_stack_id_fails_closed():
    packet = _case_packet(_report(), "BLOCK_UNTRACEABLE_SELECTED_STACK_LINEAGE")
    assert packet["eligible_competition_entry_count"] == 0
    assert packet["selected_stack_id"] is None
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_NOT_TRACEABLE_TO_PR89_PR88_PR87" in _all_reason_codes(packet)


def test_non_forwardable_selected_stack_fails_closed():
    packet = _case_packet(_report(), "BLOCK_SELECTED_STACK_NOT_FORWARDABLE")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_NOT_FORWARDABLE_TO_PR90" in _all_reason_codes(packet)


def test_blocked_candidate_cannot_enter_active_competition():
    packet = _case_packet(_report(), "BLOCK_BLOCKED_SELECTED_STACK")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_BLOCKED_ROW_PRESENT" in _all_reason_codes(packet)


def test_incompatible_candidate_cannot_enter_active_competition():
    packet = _case_packet(_report(), "BLOCK_INCOMPATIBLE_SELECTED_STACK")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_INCOMPATIBLE_SELECTED_STACK" in _all_reason_codes(packet)


def test_missing_role_candidate_cannot_enter_active_competition():
    packet = _case_packet(_report(), "BLOCK_MISSING_ROLE_SELECTED_STACK")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_REQUIRED_ROLE" in _all_reason_codes(packet)


def test_replay_and_paper_lanes_are_separate_static_descriptors():
    packet = _packet()
    replay = packet["replay_lane_input_descriptors"][0]
    paper = packet["paper_lane_input_descriptors"][0]
    assert replay["replay_lane_input_descriptor_id"] != paper["paper_lane_input_descriptor_id"]
    assert packet["replay_lane_descriptor_count"] == 1
    assert packet["paper_lane_descriptor_count"] == 1


def test_replay_paper_shared_input_identity_is_deterministic():
    packet = _packet()
    replay = packet["replay_lane_input_descriptors"][0]
    paper = packet["paper_lane_input_descriptors"][0]
    assert replay["replay_paper_input_identity_digest_or_static_ref"] == (
        paper["replay_paper_input_identity_digest_or_static_ref"]
    )
    assert packet["replay_paper_input_identity_digest_or_static_ref"] == (
        replay["replay_paper_input_identity_digest_or_static_ref"]
    )


def test_replay_paper_input_identity_mismatch_fails_closed():
    packet = _case_packet(_report(), "BLOCK_REPLAY_PAPER_INPUT_IDENTITY_MISMATCH")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_AMBIGUOUS_REPLAY_PAPER_INPUT_IDENTITY" in _all_reason_codes(packet)


def test_replay_lane_missing_fails_closed():
    packet = _case_packet(_report(), "BLOCK_REPLAY_LANE_MISSING")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_LANE_MISSING" in _all_reason_codes(packet)


def test_paper_lane_missing_fails_closed():
    packet = _case_packet(_report(), "BLOCK_PAPER_LANE_MISSING")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_PAPER_LANE_MISSING" in _all_reason_codes(packet)


def test_competition_gate_does_not_execute_replay_or_paper():
    report = _report()
    packet = _packet()
    assert report["replay_execution_count"] == 0
    assert report["paper_execution_count"] == 0
    assert packet["replay_execution_created_flag"] is False
    assert packet["paper_execution_created_flag"] is False


def test_competition_gate_does_not_create_replay_or_paper_results():
    report = _report()
    packet = _packet()
    assert report["replay_result_packet_count"] == 0
    assert report["paper_result_packet_count"] == 0
    assert packet["replay_result_packet_created_flag"] is False
    assert packet["paper_result_packet_created_flag"] is False
    assert report["result_boundary_refs_are_not_result_packets"] is True


def test_competition_gate_rejects_replay_result_packet_created_in_pr90():
    packet = _case_packet(_report(), "BLOCK_REPLAY_RESULT_PACKET_PRESENT")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_RESULT_CREATED_IN_STATIC_COMPETITION_SCOPE" in _all_reason_codes(packet)


def test_competition_gate_rejects_paper_result_packet_created_in_pr90():
    packet = _case_packet(_report(), "BLOCK_PAPER_RESULT_PACKET_PRESENT")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_RESULT_CREATED_IN_STATIC_COMPETITION_SCOPE" in _all_reason_codes(packet)


def test_competition_gate_does_not_create_dual_result_review():
    report = _report()
    packet = _packet()
    assert report["dual_result_review_packet_count"] == 0
    assert packet["pr91_dual_result_review_created_flag"] is False
    assert report["dual_result_review_created"] is False


def test_competition_gate_does_not_create_owner_live_promotion_review():
    report = _report()
    packet = _packet()
    assert packet["pr92_owner_live_promotion_review_created_flag"] is False
    assert report["owner_live_promotion_review_created"] is False
    assert report["pr92_owner_review_created"] is False


def test_order_intent_surface_remains_non_authoritative_static_preview_only_if_present():
    packet = _packet()
    preview = packet["order_intent_preview_surface"]
    assert preview["authority_class"] == gate.ORDER_INTENT_PREVIEW_AUTHORITY
    assert preview["executable_order_intent_created"] is False
    assert preview["order_submission_allowed_flag"] is False
    assert _report()["order_intent_preview_is_authoritative"] is False


def test_competition_gate_does_not_create_order_authority():
    report = _report()
    packet = _packet()
    assert packet["order_intent_authority_created"] is False
    assert packet["order_authoritative_item_count"] == 0
    assert report["live_order_authority"] is False
    assert packet["no_order_authority_flag"] is True


def test_competition_gate_does_not_create_live_routing():
    packet = _packet()
    assert packet["live_routing_allowed_flag"] is False
    assert packet["no_live_trade_authority_flag"] is True


def test_competition_gate_does_not_bind_connector_semantics():
    report = _report()
    packet = _packet()
    assert packet["connector_binding_allowed_flag"] is False
    assert packet["connector_semantic_binding_created_flag"] is False
    assert report["connector_semantic_binding_created"] is False


def test_competition_gate_does_not_execute_classical_or_quantum_optimizer():
    report = _report()
    assert report["real_optimizer_execution_count"] == 0
    assert report["classical_optimizer_execution_created"] is False
    assert report["quantum_optimizer_execution_created"] is False
    assert report["optimizer_execution_created"] is False


def test_competition_gate_does_not_call_quantum_backend_or_simulator():
    report = _report()
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_simulator_execution_created"] is False


def test_competition_gate_does_not_create_owner_approval_or_live_promotion():
    report = _report()
    packet = _packet()
    assert packet["owner_approval_created_flag"] is False
    assert report["owner_approval_created"] is False
    assert report["live_promotion_created"] is False
    assert packet["live_promotion_created_flag"] is False


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


def test_pr91_and_pr92_boundaries_preserved():
    report = _report()
    packet = _case_packet(report, "PASS_PR91_BOUNDARY_FUTURE_RESULTS_REQUIRED_NO_REVIEW_CREATED")
    entry = packet["competition_entries"][0]
    assert packet["pr91_dual_result_review_required_flag"] is True
    assert packet["pr91_dual_result_review_created_flag"] is False
    assert entry["pr91_dual_review_forwardable_flag"] is False
    assert entry["pr91_dual_review_forwardable_after_future_results_flag"] is True
    assert packet["pr92_owner_live_promotion_review_required_flag"] is True
    assert packet["pr92_owner_live_promotion_review_created_flag"] is False


def test_no_competition_entries_fails_closed():
    packet = _case_packet(_report(), "BLOCK_NO_COMPETITION_ENTRIES")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_NO_COMPETITION_ENTRIES" in _all_reason_codes(packet)


def test_executable_order_intent_present_fails_closed():
    packet = _case_packet(_report(), "BLOCK_EXECUTABLE_ORDER_INTENT_PRESENT")
    assert packet["eligible_competition_entry_count"] == 0
    assert "REPLAY_PAPER_COMPETITION_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN" in _all_reason_codes(packet)


def test_ci_detached_head_mode_if_validator_checks_branch_or_baseline(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _mock_git_stdout(
        monkeypatch,
        _git_metadata_responses(branch=""),
    )

    failures, metadata = gate.validate_pr90_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert metadata["branch"] == ""
    assert metadata["ci_info_lines"] == (gate.CI_DETACHED_HEAD_MODE_MARKER,)
