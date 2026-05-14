import json
from pathlib import Path

from tools import validate_dual_result_review_for_parameter_stacks as gate


REPO_ROOT = Path(".")
_REPORT_CACHE: dict | None = None


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
    return _report()["dual_result_review_parameter_stack_packet"]


def _review_item() -> dict:
    items = _packet()["review_items"]
    assert len(items) == 1
    return items[0]


def _case_packet(report: dict, case_id: str) -> dict:
    for packet in report["fixture_case_packets"]:
        if packet["fixture_case_id"] == case_id:
            return packet
    raise AssertionError(f"missing case packet: {case_id}")


def _all_reason_codes(packet: dict) -> set[str]:
    blocked = {
        code
        for item in packet["blocked_review_items"]
        for code in item.get("blocked_reason_codes", [])
    }
    return set(packet["review_reason_codes"]) | blocked


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


def test_pr91_metadata_and_semantic_task_id_are_verified_or_marked_needs_owner_confirmation():
    report = _report()
    assert report["roadmap_pr_label"] == "PR #91"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == gate.BLUEPRINT_INDEX.as_posix()
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert "NEEDS_OWNER_CONFIRMATION" not in gate.serialize_report(report)


def test_dual_result_review_parameter_stack_packet_is_deterministic_across_runs():
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


def test_dual_result_review_consumes_pr90_competition_packet():
    packet = _packet()
    assert packet["upstream_replay_paper_competition_packet_ref"] == (
        "PR90_STATIC_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_PACKET_SYNTHETIC_V1"
    )
    assert packet["competition_entry_id"] == (
        "PR90_COMPETITION_ENTRY__PR87_CANDIDATE_STACK__OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE"
    )
    assert _report()["review_entries_derived_only_from_pr90_competition_packet"] is True


def test_dual_result_review_traces_selected_stack_to_pr89_handoff_packet():
    lineage = _review_item()["selected_stack_lineage_trace"]
    assert any(step["artifact_id"] == "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET" for step in lineage)
    assert _review_item()["handoff_by_pr89_packet_ref"] == (
        "PR89_STATIC_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_SYNTHETIC_V1"
    )


def test_dual_result_review_traces_selected_stack_to_pr88_selection_packet():
    lineage = _review_item()["selected_stack_lineage_trace"]
    assert any(step["artifact_id"] == "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE" for step in lineage)
    assert _review_item()["selected_by_pr88_packet_ref"] == (
        "PR88_STATIC_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_PACKET_SYNTHETIC_V1"
    )


def test_dual_result_review_traces_selected_stack_to_pr87_candidate_packet():
    lineage = _review_item()["selected_stack_lineage_trace"]
    assert any(step["artifact_id"] == "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE" for step in lineage)
    assert _review_item()["candidate_from_pr87_packet_ref"] == (
        "PR87_STATIC_CANDIDATE_GENERATION_PACKET_SYNTHETIC_V1"
    )


def test_dual_result_review_preserves_trade_context_and_route_lineage():
    packet = _packet()
    item = _review_item()
    assert packet["upstream_trade_context_ref"] == "TRADE_CONTEXT_KALSHI_BINARY_SHORT_HORIZON_STATIC_ROUTE"
    assert packet["upstream_routed_selection_universe_ref"] == "KALSHI_BINARY_SHORT_HORIZON"
    assert item["trade_context_ref"] == packet["upstream_trade_context_ref"]
    assert item["routed_selection_universe_ref"] == packet["upstream_routed_selection_universe_ref"]


def test_dual_result_review_preserves_scoring_ranking_arbitration_lineage():
    item = _review_item()
    assert item["scoring_policy_refs"]
    assert item["ranking_contract_ref"] == "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_V1"
    assert item["optimizer_arbitration_policy_ref"] == "QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_POLICY_V1"
    assert _report()["scoring_ranking_arbitration_lineage_preserved"] is True


def test_dual_result_review_preserves_quantum_policy_lineage():
    item = _review_item()
    assert item["quantum_applicability_summary"]["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert item["owner_quantum_priority_summary"]["owner_quantum_priority_mode"] == "OWNER_FORCED_QUANTUM"
    assert _report()["quantum_policy_lineage_preserved"] is True


def test_quantum_dual_result_review_requires_classical_comparator_or_fallback():
    item = _review_item()
    assert item["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert item["classical_comparator_required_flag"] is True
    assert item["classical_comparator_ref"] == "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE"


def test_static_quantum_classical_comparison_metadata_does_not_create_backend_execution():
    packet = _packet()
    assert packet["comparison_matrix"]["quantum_vs_classical_review_supported_flag"] is True
    assert packet["comparison_metric_values_real_flag"] is False
    assert _report()["quantum_backend_execution_count"] == 0
    assert _report()["quantum_simulator_execution_count"] == 0


def test_owner_override_basis_is_carried_without_fabricating_external_facts():
    summary = _review_item()["owner_quantum_priority_summary"]
    assert summary["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert summary["owner_override_internal_only_flag"] is True
    assert summary["owner_override_external_fact_fabrication_created"] is False
    assert _report()["owner_override_records_basis_without_external_fact_fabrication"] is True


def test_dual_result_review_requires_separate_replay_and_paper_result_packet_refs():
    packet = _packet()
    assert packet["replay_result_packet_ref"] != packet["paper_result_packet_ref"]
    assert packet["replay_result_ref_count"] == 1
    assert packet["paper_result_ref_count"] == 1
    assert _report()["replay_and_paper_result_refs_separate"] is True


def test_dual_result_review_shared_input_identity_match_required():
    packet = _packet()
    assert packet["shared_input_identity_match_flag"] is True
    assert packet["runtime_resolver_snapshot_match_flag"] is True
    assert packet["input_lock_match_flag"] is True
    assert packet["owner_policy_snapshot_match_flag"] is True


def test_dual_result_review_shared_input_identity_mismatch_fails_closed():
    packet = _case_packet(_report(), "BLOCK_REPLAY_PAPER_INPUT_IDENTITY_MISMATCH")
    assert packet["valid_review_item_count"] == 0
    assert "DUAL_RESULT_REVIEW_BLOCKED_SHARED_INPUT_IDENTITY_MISMATCH" in _all_reason_codes(packet)


def test_dual_result_review_missing_replay_result_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_MISSING_REPLAY_RESULT_PACKET")
    assert packet["replay_result_ref_count"] == 0
    assert "DUAL_RESULT_REVIEW_BLOCKED_MISSING_REPLAY_RESULT_PACKET" in _all_reason_codes(packet)


def test_dual_result_review_missing_paper_result_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_MISSING_PAPER_RESULT_PACKET")
    assert packet["paper_result_ref_count"] == 0
    assert "DUAL_RESULT_REVIEW_BLOCKED_MISSING_PAPER_RESULT_PACKET" in _all_reason_codes(packet)


def test_dual_result_review_stale_replay_result_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_STALE_REPLAY_RESULT_PACKET")
    assert packet["valid_review_item_count"] == 0
    assert "DUAL_RESULT_REVIEW_BLOCKED_STALE_REPLAY_RESULT_PACKET" in _all_reason_codes(packet)


def test_dual_result_review_stale_paper_result_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_STALE_PAPER_RESULT_PACKET")
    assert packet["valid_review_item_count"] == 0
    assert "DUAL_RESULT_REVIEW_BLOCKED_STALE_PAPER_RESULT_PACKET" in _all_reason_codes(packet)


def test_dual_result_review_invalid_replay_result_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_INVALID_REPLAY_RESULT_PACKET")
    assert packet["valid_review_item_count"] == 0
    assert "DUAL_RESULT_REVIEW_BLOCKED_INVALID_REPLAY_RESULT_PACKET" in _all_reason_codes(packet)


def test_dual_result_review_invalid_paper_result_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_INVALID_PAPER_RESULT_PACKET")
    assert packet["valid_review_item_count"] == 0
    assert "DUAL_RESULT_REVIEW_BLOCKED_INVALID_PAPER_RESULT_PACKET" in _all_reason_codes(packet)


def test_dual_result_review_blocks_result_merge():
    packet = _case_packet(_report(), "BLOCK_REPLAY_PAPER_RESULT_MERGE")
    assert packet["result_merge_detected_flag"] is True
    assert "DUAL_RESULT_REVIEW_BLOCKED_RESULT_MERGE_FORBIDDEN" in _all_reason_codes(packet)


def test_dual_result_review_blocks_result_overwrite():
    packet = _case_packet(_report(), "BLOCK_REPLAY_PAPER_RESULT_OVERWRITE")
    assert packet["result_overwrite_detected_flag"] is True
    assert "DUAL_RESULT_REVIEW_BLOCKED_RESULT_OVERWRITE_FORBIDDEN" in _all_reason_codes(packet)


def test_dual_result_review_blocks_result_collapse_or_averaging_away():
    packet = _case_packet(_report(), "BLOCK_REPLAY_PAPER_RESULT_COLLAPSE")
    assert packet["result_collapse_detected_flag"] is True
    assert "DUAL_RESULT_REVIEW_BLOCKED_RESULT_COLLAPSE_FORBIDDEN" in _all_reason_codes(packet)


def test_synthetic_result_fixture_is_not_real_replay_or_paper_evidence():
    packet = _packet()
    for shape_key in ("synthetic_replay_result_packet_shape", "synthetic_paper_result_packet_shape"):
        shape = packet[shape_key]
        assert shape["authority_class"] == gate.SYNTHETIC_FIXTURE_AUTHORITY_CLASS
        assert shape["synthetic_fixture_flag"] is True
        assert shape["not_execution_evidence_flag"] is True
        assert shape["not_profit_evidence_flag"] is True
        assert shape["real_result_packet_created_flag"] is False


def test_dual_result_review_does_not_execute_replay_or_paper():
    report = _report()
    assert report["replay_execution_count"] == 0
    assert report["paper_execution_count"] == 0
    assert report["replay_execution_created_flag"] is False
    assert report["paper_execution_created_flag"] is False


def test_dual_result_review_does_not_create_real_replay_or_paper_results():
    report = _report()
    assert report["real_result_packet_created_count"] == 0
    assert report["real_replay_result_packet_created_flag"] is False
    assert report["real_paper_result_packet_created_flag"] is False


def test_dual_result_review_does_not_create_owner_live_promotion_review():
    assert _report()["owner_live_promotion_review_packet_count"] == 0
    assert _packet()["owner_live_promotion_review_required_flag"] is True
    assert _packet()["owner_live_promotion_review_created_flag"] is False


def test_dual_result_review_does_not_create_owner_approval():
    assert _report()["owner_approval_count"] == 0
    assert _packet()["owner_approval_created_flag"] is False


def test_dual_result_review_does_not_create_canary_eligibility():
    assert _packet()["canary_eligibility_created_flag"] is False


def test_dual_result_review_does_not_create_live_promotion():
    assert _report()["live_promotion_count"] == 0
    assert _packet()["live_promotion_created_flag"] is False


def test_dual_result_review_does_not_create_order_authority():
    assert _report()["order_authoritative_item_count"] == 0
    assert _packet()["order_authority_created_flag"] is False
    assert _packet()["order_submission_allowed_flag"] is False


def test_dual_result_review_does_not_create_live_routing():
    assert _packet()["live_routing_allowed_flag"] is False


def test_dual_result_review_does_not_bind_connector_semantics():
    assert _packet()["connector_binding_allowed_flag"] is False
    assert _packet()["connector_semantic_binding_created_flag"] is False


def test_dual_result_review_does_not_execute_classical_or_quantum_optimizer():
    packet = _packet()
    assert packet["classical_optimizer_execution_created_flag"] is False
    assert packet["quantum_optimizer_execution_created_flag"] is False
    assert packet["optimizer_execution_created_flag"] is False
    assert _report()["real_optimizer_execution_count"] == 0


def test_dual_result_review_does_not_call_quantum_backend_or_simulator():
    assert _packet()["quantum_backend_execution_created_flag"] is False
    assert _packet()["quantum_simulator_execution_created_flag"] is False
    assert _report()["quantum_backend_execution_count"] == 0
    assert _report()["quantum_simulator_execution_count"] == 0


def test_dual_result_review_does_not_create_profit_evidence():
    assert _packet()["profit_evidence_created_flag"] is False
    assert _report()["profit_evidence_created_flag"] is False
    assert _packet()["no_profit_evidence_flag"] is True


def test_dual_result_review_routes_pass_only_to_pr92_required_not_created():
    packet = _packet()
    assert packet["future_pass_route_if_real_results_validate"] == "OWNER_LIVE_PROMOTION_REVIEW_REQUIRED"
    assert packet["pr92_owner_live_promotion_review_required_flag"] is True
    assert packet["pr92_owner_live_promotion_review_created_flag"] is False
    assert packet["owner_approval_created_flag"] is False


def test_dual_result_review_routes_negative_or_ambiguous_static_states_without_live_authority():
    negative = _case_packet(_report(), "PASS_NEGATIVE_ROUTE_STATIC_ONLY")
    ambiguous = _case_packet(_report(), "PASS_AMBIGUOUS_ROUTE_STATIC_ONLY")
    assert negative["review_state"] == "RETEST_REQUIRED"
    assert ambiguous["review_state"] == "OWNER_REVIEW_REQUIRED"
    assert negative["live_routing_allowed_flag"] is False
    assert ambiguous["order_submission_allowed_flag"] is False


def test_atomicrows_bundle_and_sha_are_not_created():
    report = _report()
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()


def test_master_plan_not_edited():
    assert _report()["master_plan_diff_empty"] is True
    assert gate.validate_master_plan_diff(REPO_ROOT) == []


def test_pr92_boundary_preserved():
    packet = _packet()
    assert packet["pr92_owner_live_promotion_review_required_flag"] is True
    assert packet["pr92_owner_live_promotion_review_created_flag"] is False
    assert packet["pr92_owner_review_forwardable_flag"] is False


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

    failures, metadata = gate.validate_pr91_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert gate.CI_DETACHED_HEAD_MODE_MARKER in metadata["ci_info_lines"]
    assert gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER in metadata["ci_info_lines"]
