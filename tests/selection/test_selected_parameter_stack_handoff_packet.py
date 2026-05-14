import json
from pathlib import Path

from tools import validate_selected_parameter_stack_handoff_packet as gate


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
    return _report()["selected_parameter_stack_handoff_packet"]


def _selected_item() -> dict:
    items = _packet()["selected_handoff_items"]
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
        for item in packet["blocked_handoff_items"]
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


def test_pr89_metadata_and_semantic_task_id_are_verified_or_marked_needs_owner_confirmation():
    report = _report()
    assert report["roadmap_pr_label"] == "PR #89"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == gate.BLUEPRINT_INDEX.as_posix()
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert "NEEDS_OWNER_CONFIRMATION" not in gate.serialize_report(report)


def test_selected_stack_handoff_packet_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["deterministic_handoff_key"] == second_report["deterministic_handoff_key"]
    assert first_report["selected_stack_id"] == second_report["selected_stack_id"]


def test_selected_stack_handoff_consumes_pr88_selection_packet():
    report = _report()
    packet = report["selected_parameter_stack_handoff_packet"]
    assert packet["upstream_trade_context_selection_packet_ref"] == (
        "PR88_STATIC_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_PACKET_SYNTHETIC_V1"
    )
    assert packet["selected_stack_id"] == report["pr88_static_selected_candidate_stack_id"]
    assert "SELECTED_STACK_HANDOFF_ALLOWED_PR88_SELECTION_PACKET" in packet["selection_reason_codes"]


def test_selected_stack_handoff_traces_selected_stack_to_pr87_candidate_packet():
    report = _report()
    selected = report["selected_stack_id"]
    assert selected in report["pr87_active_candidate_stack_ids"]
    assert report["selected_stack_lineage_traces_to_pr87_candidate_packet"] is True
    assert any(step["artifact_id"] == "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE" for step in report["selected_stack_lineage_trace"])


def test_selected_stack_handoff_preserves_trade_context_and_route_lineage():
    packet = _packet()
    item = _selected_item()
    assert packet["upstream_trade_context_ref"] == "TRADE_CONTEXT_KALSHI_BINARY_SHORT_HORIZON_STATIC_ROUTE"
    assert packet["upstream_routed_selection_universe_ref"] == "KALSHI_BINARY_SHORT_HORIZON"
    assert item["trade_context_ref"] == packet["upstream_trade_context_ref"]
    assert item["routed_selection_universe_ref"] == packet["upstream_routed_selection_universe_ref"]


def test_selected_stack_handoff_preserves_scoring_ranking_arbitration_lineage():
    packet = _packet()
    item = _selected_item()
    assert packet["score_breakdown_ref"]
    assert packet["ranking_contract_ref"] == item["ranking_contract_ref"]
    assert packet["optimizer_arbitration_policy_ref"] == item["optimizer_arbitration_policy_ref"]
    assert "SELECTED_STACK_HANDOFF_ALLOWED_SCORING_RANKING_LINEAGE" in packet["selection_reason_codes"]
    assert "SELECTED_STACK_HANDOFF_ALLOWED_OPTIMIZER_ARBITRATION_LINEAGE" in packet["selection_reason_codes"]


def test_selected_stack_handoff_preserves_quantum_policy_lineage():
    packet = _packet()
    item = _selected_item()
    assert packet["quantum_applicability_ref"] == "docs/master_plan/generated/QuantumApplicabilityClassificationRegistry.report.json"
    assert packet["owner_quantum_priority_ref"] == "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json"
    assert item["quantum_applicability_summary"]
    assert item["owner_quantum_priority_summary"]
    assert packet["quantum_priority_applied"] is True


def test_quantum_selected_stack_handoff_requires_classical_comparator_or_fallback():
    item = _selected_item()
    assert item["quantum_candidate_type"] == "TRUE_QUANTUM"
    assert item["classical_comparator_required_flag"] is True
    assert item["classical_comparator_ref"] == "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE"


def test_owner_override_basis_is_carried_without_fabricating_external_facts():
    report = _report()
    item = _selected_item()
    summary = item["owner_quantum_priority_summary"]
    assert summary["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert summary["owner_override_internal_only_flag"] is True
    assert summary["owner_override_external_fact_fabrication_created"] is False
    assert report["owner_override_records_basis_without_external_fact_fabrication"] is True
    assert report["owner_override_applied"] is True


def test_missing_pr88_selection_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_MISSING_PR88_SELECTION_PACKET")
    assert packet["selected_handoff_item_count"] == 0
    assert packet["selected_stack_id"] is None
    assert "SELECTED_STACK_HANDOFF_BLOCKED_MISSING_PR88_SELECTION_PACKET" in _all_reason_codes(packet)


def test_missing_selected_stack_id_fails_closed():
    packet = _case_packet(_report(), "BLOCK_MISSING_SELECTED_STACK_ID")
    assert packet["selected_handoff_item_count"] == 0
    assert packet["selected_stack_id"] is None
    assert "SELECTED_STACK_HANDOFF_BLOCKED_MISSING_SELECTED_STACK_ID" in _all_reason_codes(packet)


def test_untraceable_selected_stack_id_fails_closed():
    packet = _case_packet(_report(), "BLOCK_UNTRACEABLE_SELECTED_STACK_ID")
    assert packet["selected_handoff_item_count"] == 0
    assert packet["selected_stack_id"] is None
    assert "SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_STACK_ID_NOT_IN_PR88_SELECTION" in _all_reason_codes(packet)


def test_blocked_candidate_cannot_be_handed_off_as_active_selected_stack():
    packet = _case_packet(_report(), "BLOCK_BLOCKED_CANDIDATE")
    assert packet["selected_handoff_item_count"] == 0
    assert "SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_CANDIDATE_STATUS" in _all_reason_codes(packet)


def test_incompatible_candidate_cannot_be_handed_off_as_active_selected_stack():
    packet = _case_packet(_report(), "BLOCK_INCOMPATIBLE_CANDIDATE")
    assert packet["selected_handoff_item_count"] == 0
    assert "SELECTED_STACK_HANDOFF_BLOCKED_INCOMPATIBLE_CANDIDATE" in _all_reason_codes(packet)


def test_missing_role_candidate_cannot_be_handed_off_as_active_selected_stack():
    packet = _case_packet(_report(), "BLOCK_MISSING_ROLE_CANDIDATE")
    assert packet["selected_handoff_item_count"] == 0
    assert "SELECTED_STACK_HANDOFF_BLOCKED_MISSING_REQUIRED_ROLE" in _all_reason_codes(packet)


def test_order_intent_surface_is_non_authoritative_static_preview_only():
    packet = _packet()
    preview = packet["order_intent_preview_surface"]
    assert packet["order_intent_surface_present_flag"] is True
    assert packet["order_intent_surface_authority"] == gate.ORDER_INTENT_PREVIEW_AUTHORITY
    assert preview["authority_class"] == gate.ORDER_INTENT_PREVIEW_AUTHORITY
    assert preview["executable_order_intent_created"] is False
    assert _report()["order_intent_preview_is_authoritative"] is False


def test_selected_stack_handoff_does_not_create_order_authority():
    report = _report()
    packet = _packet()
    assert packet["order_intent_authority_created"] is False
    assert report["live_order_authority"] is False
    assert report["selected_stack_handoff_packet_is_live_order_authority"] is False
    assert packet["no_order_authority_flag"] is True
    assert packet["order_authoritative_item_count"] == 0


def test_selected_stack_handoff_does_not_create_live_routing():
    packet = _packet()
    assert packet["live_routing_allowed_flag"] is False
    assert packet["no_live_trade_authority_flag"] is True


def test_selected_stack_handoff_does_not_bind_connector_semantics():
    packet = _packet()
    report = _report()
    assert packet["connector_binding_allowed_flag"] is False
    assert packet["connector_semantic_binding_created_flag"] is False
    assert report["connector_semantic_binding_created"] is False


def test_selected_stack_handoff_does_not_execute_replay_or_paper():
    report = _report()
    assert report["replay_execution_count"] == 0
    assert report["paper_execution_count"] == 0
    assert report["replay_execution_created"] is False
    assert report["paper_execution_created"] is False


def test_selected_stack_handoff_does_not_create_replay_or_paper_results():
    report = _report()
    assert report["replay_result_packet_created"] is False
    assert report["paper_result_packet_created"] is False
    assert _packet()["replay_result_packet_created_flag"] is False
    assert _packet()["paper_result_packet_created_flag"] is False


def test_selected_stack_handoff_does_not_execute_classical_or_quantum_optimizer():
    report = _report()
    assert report["real_optimizer_execution_count"] == 0
    assert report["classical_optimizer_execution_created"] is False
    assert report["quantum_optimizer_execution_created"] is False
    assert report["optimizer_execution_created"] is False


def test_selected_stack_handoff_does_not_call_quantum_backend_or_simulator():
    report = _report()
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_simulator_execution_created"] is False


def test_selected_stack_handoff_does_not_create_owner_approval_or_live_promotion():
    report = _report()
    packet = _packet()
    assert packet["owner_approval_created_flag"] is False
    assert report["owner_approval_created"] is False
    assert report["live_promotion_created"] is False
    assert packet["live_promotion_created_flag"] is False


def test_atomicrows_bundle_and_sha_are_not_created():
    report = _report()
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()


def test_master_plan_not_edited():
    report = _report()
    assert report["master_plan_diff_empty"] is True
    assert gate.validate_master_plan_diff(REPO_ROOT) == []


def test_pr90_boundary_preserved():
    report = _report()
    packet = _case_packet(report, "PASS_PR90_BOUNDARY_FORWARDABLE_NOT_EXECUTED")
    assert packet["pr90_competition_gate_required_flag"] is True
    assert packet["pr90_forwardable_metadata"]["pr90_forwardable_flag"] is True
    assert packet["pr90_forwardable_metadata"]["pr90_execution_created"] is False
    assert report["pr90_execution_created"] is False


def test_no_eligible_handoff_item_fails_closed():
    packet = _case_packet(_report(), "BLOCK_NO_ELIGIBLE_HANDOFF_ITEM")
    assert packet["selected_handoff_item_count"] == 0
    assert "SELECTED_STACK_HANDOFF_BLOCKED_NO_ELIGIBLE_HANDOFF_ITEM" in _all_reason_codes(packet)


def test_selected_candidate_not_traceable_to_pr87_candidate_packet_fails_closed():
    packet = _case_packet(_report(), "BLOCK_SELECTED_CANDIDATE_NOT_TRACEABLE_TO_PR87")
    assert packet["selected_handoff_item_count"] == 0
    assert "SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_CANDIDATE_NOT_TRACEABLE_TO_PR87" in _all_reason_codes(packet)


def test_ci_detached_head_mode_if_validator_checks_branch_or_baseline(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _mock_git_stdout(
        monkeypatch,
        _git_metadata_responses(branch=""),
    )

    failures, metadata = gate.validate_pr89_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert metadata["branch"] == ""
    assert metadata["ci_info_lines"] == (gate.CI_DETACHED_HEAD_MODE_MARKER,)
