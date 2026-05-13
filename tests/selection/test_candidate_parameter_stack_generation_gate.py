import copy
import json
from pathlib import Path

from tools import validate_candidate_parameter_stack_generation_gate as gate


REPO_ROOT = Path(".")


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _fixture() -> dict:
    return json.loads((REPO_ROOT / gate.DEFAULT_FIXTURE).read_text(encoding="utf-8"))


def _upstream() -> dict:
    failures, upstream = gate.validate_upstream_reports(REPO_ROOT)
    assert failures == []
    return upstream


def _report() -> dict:
    assert gate.main([]) == 0
    return json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))


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


def _seed(payload: dict, seed_id: str) -> dict:
    for item in payload["candidate_seed_descriptors"]:
        if item["seed_descriptor_id"] == seed_id:
            return item
    raise AssertionError(f"missing seed {seed_id}")


def _packet_from(payload: dict) -> dict:
    packet, failures = gate.build_candidate_generation_packet(
        _registry(),
        payload,
        _upstream(),
    )
    assert failures == []
    return packet


def test_local_mode_still_fails_on_wrong_branch(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    _mock_git_stdout(
        monkeypatch,
        _git_metadata_responses(branch="wrong-pr87-branch"),
    )

    failures, metadata = gate.validate_pr87_roadmap_metadata(REPO_ROOT)

    assert any(
        f"current branch must be {gate.TARGET_BRANCH}, got wrong-pr87-branch" in failure
        for failure in failures
    )
    assert metadata["ci_info_lines"] == ()


def test_ci_detached_head_mode_skips_branch_name_equality(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _mock_git_stdout(
        monkeypatch,
        _git_metadata_responses(branch=""),
    )

    failures, metadata = gate.validate_pr87_roadmap_metadata(REPO_ROOT)

    assert failures == []
    assert metadata["branch"] == ""
    assert metadata["ci_info_lines"] == (gate.CI_DETACHED_HEAD_MODE_MARKER,)


def test_ci_shallow_fetch_mode_skips_missing_baseline_ancestry(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    responses = _git_metadata_responses(
        baseline_rc=128,
        baseline_err=f"fatal: Not a valid object name {gate.EXPECTED_BASELINE_ANCESTOR}",
    )
    responses.pop(
        (
            "merge-base",
            "--is-ancestor",
            gate.EXPECTED_BASELINE_ANCESTOR,
            "HEAD",
        )
    )
    _mock_git_stdout(monkeypatch, responses)

    output_path = tmp_path / "CandidateParameterStackGenerationGate.report.json"
    assert gate.main(["--out", str(output_path)]) == 0

    assert capsys.readouterr().out.splitlines() == [
        gate.SUCCESS_MARKER,
        gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER,
    ]
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["final_selection"] is False
    assert report["live_order_authority"] is False
    assert report["order_authority_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["quantum_backend_execution_created"] is False


def test_local_mode_still_enforces_ancestry(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    _mock_git_stdout(
        monkeypatch,
        _git_metadata_responses(
            baseline_rc=128,
            baseline_err=f"fatal: Not a valid object name {gate.EXPECTED_BASELINE_ANCESTOR}",
            ancestor_rc=128,
            ancestor_err=f"fatal: Not a valid object name {gate.EXPECTED_BASELINE_ANCESTOR}",
        ),
    )

    failures, metadata = gate.validate_pr87_roadmap_metadata(REPO_ROOT)

    assert any(
        f"HEAD must descend from {gate.EXPECTED_BASELINE_ANCESTOR}" in failure
        for failure in failures
    )
    assert metadata["ci_info_lines"] == ()


def test_pr87_metadata_and_semantic_task_id_are_verified_or_marked_needs_owner_confirmation():
    report = _report()
    assert report["roadmap_pr_label"] == "PR #87"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == gate.BLUEPRINT_INDEX.as_posix()
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert "NEEDS_OWNER_CONFIRMATION" not in gate.serialize_report(report)


def test_candidate_generation_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["active_candidate_stack_ids"] == second_report["active_candidate_stack_ids"]
    assert first_report["candidate_generation_packet"]["candidate_stacks"] == second_report["candidate_generation_packet"]["candidate_stacks"]


def test_candidate_generation_produces_multiple_candidates_when_valid_fixture_permits():
    report = _report()
    assert report["candidate_generation_packet_status"] == "STATIC_CANDIDATE_GENERATION_PACKET_READY"
    assert report["candidate_stack_generation_count"] == 4
    assert report["active_candidate_stack_ids"] == list(gate.EXPECTED_ACTIVE_CANDIDATE_IDS)


def test_candidate_generation_rejects_or_blocks_missing_required_role():
    report = _report()
    packet = report["candidate_generation_packet"]
    missing = next(
        item
        for item in packet["candidate_stacks"]
        if item["seed_descriptor_id"] == "BLOCKED_MISSING_SIGNAL_ROLE_FIXTURE"
    )
    assert missing["candidate_status"] == "BLOCKED_CANDIDATE_STACK"
    assert "CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_ROLE" in missing["blocked_reason_codes"]
    assert missing["blocked_row_ids_and_reasons"] == [
        {"row_id": "SYNTHETIC_ROW_SIGNAL_MISSING", "reason": "MISSING_SIGNAL_ROLE"}
    ]

    mutated = _fixture()
    classical = _seed(mutated, "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE")
    classical["selected_stack_role_map"].pop("SIGNAL")
    classical["expected_candidate_status"] = "BLOCKED_CANDIDATE_STACK"
    packet = _packet_from(mutated)
    changed = next(item for item in packet["candidate_stacks"] if item["seed_descriptor_id"] == classical["seed_descriptor_id"])
    assert changed["candidate_status"] == "BLOCKED_CANDIDATE_STACK"
    assert "CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_ROLE" in changed["blocked_reason_codes"]


def test_candidate_generation_rejects_or_blocks_incompatible_role_tuple():
    report = _report()
    packet = report["candidate_generation_packet"]
    incompatible = next(
        item
        for item in packet["candidate_stacks"]
        if item["seed_descriptor_id"] == "BLOCKED_INCOMPATIBLE_ROLE_TUPLE_FIXTURE"
    )
    assert incompatible["candidate_status"] == "BLOCKED_CANDIDATE_STACK"
    assert "CANDIDATE_GENERATION_BLOCKED_INCOMPATIBLE_ROLE_TUPLE" in incompatible["blocked_reason_codes"]

    mutated = _fixture()
    classical = _seed(mutated, "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE")
    classical["compatibility_state"] = "INCOMPATIBLE_ROLE_TUPLE"
    classical["expected_candidate_status"] = "BLOCKED_CANDIDATE_STACK"
    packet = _packet_from(mutated)
    changed = next(item for item in packet["candidate_stacks"] if item["seed_descriptor_id"] == classical["seed_descriptor_id"])
    assert changed["candidate_status"] == "BLOCKED_CANDIDATE_STACK"
    assert "CANDIDATE_GENERATION_BLOCKED_INCOMPATIBLE_ROLE_TUPLE" in changed["blocked_reason_codes"]


def test_candidate_generation_does_not_emit_final_selection():
    report = _report()
    packet = report["candidate_generation_packet"]
    assert "selected_stack_id" not in packet
    assert report["final_selection"] is False
    assert report["final_selection_created"] is False
    assert report["static_candidate_generation_packet_is_final_selection"] is False
    for candidate in packet["candidate_stacks"]:
        assert candidate["no_final_selection_flag"] is True
        assert candidate["final_selection_created"] is False
        assert candidate["selected_stack_created"] is False


def test_candidate_generation_does_not_create_order_authority():
    report = _report()
    assert report["live_order_authority"] is False
    assert report["order_authority_created"] is False
    assert report["live_authority_created"] is False
    assert report["static_candidate_generation_packet_is_live_order_authority"] is False
    for candidate in report["candidate_generation_packet"]["candidate_stacks"]:
        assert candidate["no_live_order_authority_flag"] is True
        assert candidate["order_authority_created"] is False


def test_candidate_generation_does_not_execute_replay_or_paper():
    report = _report()
    assert report["replay_execution_count"] == 0
    assert report["paper_execution_count"] == 0
    assert report["replay_execution_created"] is False
    assert report["paper_execution_created"] is False


def test_candidate_generation_does_not_execute_classical_or_quantum_optimizer():
    report = _report()
    assert report["real_optimizer_execution_count"] == 0
    assert report["classical_optimizer_execution_created"] is False
    assert report["quantum_optimizer_execution_created"] is False
    assert report["optimizer_execution_created"] is False
    for candidate in report["candidate_generation_packet"]["candidate_stacks"]:
        assert candidate["classical_optimizer_execution_created"] is False
        assert candidate["quantum_optimizer_execution_created"] is False
        assert candidate["optimizer_execution_created"] is False


def test_candidate_generation_does_not_call_quantum_backend_or_simulator():
    report = _report()
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_simulator_execution_created"] is False
    for candidate in report["candidate_generation_packet"]["candidate_stacks"]:
        assert candidate["no_backend_execution_flag"] is True
        assert candidate["quantum_backend_execution_created"] is False
        assert candidate["quantum_simulator_execution_created"] is False


def test_quantum_candidate_requires_classical_comparator_or_fallback():
    report = _report()
    for candidate in report["candidate_generation_packet"]["candidate_stacks"]:
        if candidate["quantum_candidate_type"] != "CLASSICAL_ONLY":
            assert candidate["classical_comparator_required_flag"] is True
            assert candidate["classical_comparator_ref"] == "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE"

    mutated = _fixture()
    quantum = _seed(mutated, "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE")
    quantum["classical_comparator_ref"] = None
    quantum["expected_candidate_status"] = "BLOCKED_CANDIDATE_STACK"
    packet = _packet_from(mutated)
    changed = next(item for item in packet["candidate_stacks"] if item["seed_descriptor_id"] == quantum["seed_descriptor_id"])
    assert changed["candidate_status"] == "BLOCKED_CANDIDATE_STACK"
    assert "CANDIDATE_GENERATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR" in changed["blocked_reason_codes"]


def test_owner_quantum_priority_is_static_policy_metadata_only():
    report = _report()
    assert report["owner_quantum_priority_static_policy_metadata_only"] is True
    assert report["owner_quantum_priority_fabricates_external_facts"] is False
    assert report["quantum_metadata_static_advisory_policy_gated"] is True
    assert report["active_candidate_stack_ids"][0] == (
        "PR87_CANDIDATE_STACK__OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE"
    )


def test_owner_override_records_basis_without_fabricating_external_facts():
    report = _report()
    packet = report["candidate_generation_packet"]
    owner = next(
        item
        for item in packet["candidate_stacks"]
        if item["seed_descriptor_id"] == "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE"
    )
    assert owner["owner_quantum_priority_summary"]["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert owner["owner_quantum_priority_summary"]["owner_override_internal_only_flag"] is True
    assert owner["owner_quantum_priority_summary"]["owner_override_external_fact_fabrication_created"] is False
    assert report["owner_override_records_basis_without_external_fact_fabrication"] is True
    assert report["owner_override_fabricates_external_facts"] is False


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


def test_pr88_and_pr90_boundaries_preserved():
    report = _report()
    boundary = report["pr88_pr90_handoff_boundary"]
    assert boundary["packet_is_forwardable_to_pr88_static_selection_gate"] is True
    assert boundary["packet_is_forwardable_to_pr90_replay_paper_competition_gate"] is True
    assert boundary["selected_stack_id"] is None
    assert boundary["final_selection_created"] is False
    assert boundary["replay_execution_created"] is False
    assert boundary["paper_execution_created"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False


def test_insufficient_candidate_count_fails_closed_without_promoting_single_candidate():
    fixture = _fixture()
    insufficient = fixture["insufficient_candidate_count_case"]
    packet, failures = gate.build_candidate_generation_packet(
        _registry(),
        fixture,
        _upstream(),
        seed_filter=set(insufficient["candidate_seed_descriptor_ids"]),
    )
    assert failures == []
    assert packet["candidate_stack_generation_count"] == 1
    assert packet["packet_status"] == "BLOCKED_INSUFFICIENT_CANDIDATE_STACKS"
    assert "CANDIDATE_GENERATION_BLOCKED_INSUFFICIENT_CANDIDATE_STACKS" in packet["generation_reason_codes"]
    assert "selected_stack_id" not in packet


def test_candidate_generation_packet_validation_catches_selected_stack_field():
    report = _report()
    packet = copy.deepcopy(report["candidate_generation_packet"])
    packet["selected_stack_id"] = "ILLEGAL_FINAL_SELECTION"
    failures = gate.validate_candidate_generation_packet(packet)
    assert any("CANDIDATE_GENERATION_BLOCKED_SELECTED_STACK_FORBIDDEN" in failure for failure in failures)
