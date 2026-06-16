from __future__ import annotations

import json
from pathlib import Path
import subprocess

from src.qtt.core.testing.atomicrows_bundle_state import (
    AtomicRowsBundleState,
    canonical_atomicrows_bundle_paths,
    validate_atomicrows_bundle_state,
)
from tools import generate_atomicrows_exact_row_source_files as source_generator
from tools import materialize_atomicrows_bundle_from_exact_rows as materializer
from tools import validate_atomicrows_bundle_materialization_manifest as validator
from tools import validate_no_runtime_artifacts


REPO_ROOT = Path(__file__).resolve().parents[2]
_REPORT_CACHE: dict | None = None
_ROWS_CACHE: list[dict] | None = None


def _write(path: Path, text: str = "test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _git_stdout(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        result = validator.validate(repo_root=REPO_ROOT)
        assert result.ok is True, result.failures
        assert result.report is not None
        _REPORT_CACHE = result.report
    return _REPORT_CACHE


def _rows() -> list[dict]:
    global _ROWS_CACHE
    if _ROWS_CACHE is None:
        bundle_path = REPO_ROOT / materializer.BUNDLE_PATH
        _ROWS_CACHE = [
            json.loads(line)
            for line in bundle_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
    return _ROWS_CACHE


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_materializer_creates_bundle_with_4183_rows_and_validator_marker(tmp_path, capsys):
    bundle_path, rewritten = materializer.materialize_bundle(REPO_ROOT)
    assert bundle_path == (REPO_ROOT / materializer.BUNDLE_PATH)
    assert rewritten is False
    assert len(_rows()) == 4183

    report_path = tmp_path / "AtomicRowsBundleMaterialization.report.json"
    assert validator.main(["--repo-root", str(REPO_ROOT), "--report-out", str(report_path)]) == 0
    assert [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()] == [
        validator.SUCCESS_MARKER
    ]


def test_source_and_bundle_coverage_counts_are_exact():
    report = _report()
    assert report["source_family_file_count"] == 15
    assert report["source_exact_row_record_count"] == 4183
    assert report["bundle_row_count"] == 4183
    assert report["expected_bundle_row_count"] == 4183
    assert report["all_source_rows_bundled"] is True
    assert report["all_bundle_rows_have_source"] is True
    assert report["all_bundle_rows_have_d2_e0_eligibility"] is True
    assert report["all_bundle_rows_have_scoring_readiness"] is True
    assert report["eligibility_matrix_coverage_count"] == 4183
    assert report["scoring_readiness_coverage_count"] == 4183


def test_future_scoring_stack_and_trade_context_coverage_is_complete():
    report = _report()
    assert report["future_score_component_input_coverage_count"] == 4183
    assert report["future_stack_role_input_coverage_count"] == 4183
    assert report["trade_context_metadata_or_blocker_coverage_count"] == 4183
    assert report["all_bundle_rows_have_future_score_component_contract"] is True
    assert report["all_bundle_rows_have_future_stack_role_contract"] is True
    assert report["all_bundle_rows_have_trade_context_metadata_or_blocker"] is True


def test_no_missing_duplicate_or_unexpected_rows_and_order_is_deterministic():
    report = _report()
    assert report["missing_source_row_count"] == 0
    assert report["duplicate_bundle_row_count"] == 0
    assert report["unexpected_bundle_row_count"] == 0
    assert report["row_order_valid"] is True
    assert [row["row_index"] for row in _rows()] == list(range(1, 4184))
    assert len({row["bundle_row_id"] for row in _rows()}) == 4183


def test_family_distribution_and_ranges_match_contract():
    report = _report()
    assert report["family_distribution_match"] is True
    assert report["row_range_match"] is True
    assert report["family_distribution_observed"] == {
        plan.family_id: plan.row_count for plan in source_generator.build_family_plans()
    }


def test_materializer_is_byte_stable_and_bundle_uses_lf_only():
    bundle_path = REPO_ROOT / materializer.BUNDLE_PATH
    before = bundle_path.read_bytes()
    _path, rewritten = materializer.materialize_bundle(REPO_ROOT)
    after = bundle_path.read_bytes()
    assert rewritten is False
    assert before == after
    assert _report()["byte_stable_generation_result"] == "MATCH_EXISTING_BYTES"
    assert _report()["line_ending_result"] == "LF_ONLY_FINAL_NEWLINE"
    assert b"\r" not in after
    assert after.endswith(b"\n")


def test_bundle_sha_freeze_final_readiness_and_runtime_authority_remain_absent():
    report = _report()
    assert (REPO_ROOT / materializer.BUNDLE_PATH).exists()
    assert not (REPO_ROOT / materializer.BUNDLE_SHA_PATH).exists()
    assert report["bundle_sha_file_exists"] is False
    assert report["bundle_sha_file_forbidden_absent"] is True
    assert report["sha_freeze_authority_created"] is False
    assert report["final_readiness_authority_created"] is False
    for field in (
        "live_order_authority_count",
        "final_order_submission_authority_count",
        "live_trade_intent_authority_count",
        "runtime_live_authority_count",
        "source_fact_authority_count",
        "connector_authority_count",
        "runtime_cash_authority_count",
        "backend_authority_count",
        "profit_evidence_count",
    ):
        assert report[field] == 0


def test_no_replay_paper_optimizer_quantum_execution_or_computed_outputs():
    report = _report()
    for field in (
        "replay_execution_allowed_count",
        "paper_execution_allowed_count",
        "optimizer_execution_allowed_count",
        "quantum_backend_authority_count",
        "quantum_simulator_authority_count",
        "quantum_provider_authority_count",
        "computed_score_field_count",
        "numeric_ranking_output_count",
        "selected_stack_output_count",
        "selected_order_intent_output_count",
        "optimizer_output_count",
        "replay_paper_result_count",
        "expected_profit_proof_count",
        "latency_superiority_evidence_count",
        "execution_superiority_evidence_count",
        "quantum_advantage_evidence_count",
    ):
        assert report[field] == 0


def test_family_specific_blocks_are_preserved():
    report = _report()
    assert report["quantum_family_metadata_only_result"] == {
        "families": sorted(source_generator.QUANTUM_FORWARD_FAMILY_IDS),
        "metadata_only": True,
        "row_count": 1103,
    }
    assert report["agent_governance_family_non_live_result"]["row_count"] == 270
    assert report["agent_governance_family_non_live_result"]["non_live"] is True
    assert report["source_connector_family_block_result"]["source_fact_authority_count"] == 0
    assert report["source_connector_family_block_result"]["connector_authority_count"] == 0
    assert report["capital_cash_family_runtime_cash_block_result"]["runtime_cash_authority_count"] == 0
    assert report["latency_family_superiority_claim_block_result"]["latency_superiority_evidence_count"] == 0
    assert report["replay_paper_family_execution_result_block_result"]["replay_execution_allowed_count"] == 0
    assert report["replay_paper_family_execution_result_block_result"]["paper_execution_allowed_count"] == 0
    assert report["scoring_ranking_family_execution_block_result"]["scoring_execution_allowed_count"] == 0
    assert report["scoring_ranking_family_execution_block_result"]["ranking_execution_allowed_count"] == 0


def test_master_plan_and_exact_row_sources_are_unchanged():
    report = _report()
    assert _git_stdout("diff", "--name-only", "--", "docs/master_plan/QTT_MasterPlan_Current.md") == ""
    assert _git_stdout("diff", "--name-only", "--", "docs/master_plan/atomic_rows/exact_row_sources") == ""
    assert report["master_plan_diff_check"]["unchanged"] is True
    assert report["exact_row_source_diff_check"]["unchanged"] is True


def test_central_state_and_transition_are_post_materialization_pre_sha():
    report = _report()
    assert report["current_expected_boundary_state"] == "POST_MATERIALIZATION_PRE_SHA"
    assert report["transition_from_state"] == "PRE_MATERIALIZATION"
    assert report["transition_to_state"] == "POST_MATERIALIZATION_PRE_SHA"


def test_post_materialization_pre_sha_temp_state_rules(tmp_path):
    paths = canonical_atomicrows_bundle_paths(tmp_path)
    _write(paths.bundle_jsonl, "{}\n")
    assert validate_atomicrows_bundle_state(
        tmp_path,
        AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA,
        "unit POST materialization",
    ) == []

    paths.bundle_jsonl.unlink()
    failures = validate_atomicrows_bundle_state(
        tmp_path,
        AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA,
        "unit POST missing bundle",
    )
    _assert_failure_contains(failures, "canonical AtomicRows bundle is required but missing")

    _write(paths.bundle_jsonl, "{}\n")
    _write(paths.bundle_sha256, "UNAUTHORIZED_TEST_SHA\n")
    failures = validate_atomicrows_bundle_state(
        tmp_path,
        AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA,
        "unit POST sha exists",
    )
    _assert_failure_contains(failures, "canonical AtomicRows bundle hash must remain absent")


def test_future_blocker_handoff_fields_are_future_only():
    report = _report()
    for field in (
        "future_sha_freeze_state_centralization_required",
        "future_final_readiness_state_centralization_required",
        "future_runtime_live_state_centralization_required",
        "future_profit_evidence_state_centralization_required",
        "future_quantum_execution_state_centralization_required",
        "future_sha_freeze_handoff_state",
        "future_final_readiness_handoff_state",
    ):
        assert report[field] == "REQUIRED_FUTURE_ONLY_NOT_EXECUTED"


def test_no_runtime_scanner_keeps_atomicrows_sha_forbidden():
    assert "AtomicRows.bundle.jsonl" not in validate_no_runtime_artifacts.FORBIDDEN_NAMES
    assert "AtomicRows.bundle.sha256" in validate_no_runtime_artifacts.FORBIDDEN_NAMES
