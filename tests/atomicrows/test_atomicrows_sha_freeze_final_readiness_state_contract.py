from __future__ import annotations

import json
from pathlib import Path
import subprocess

from src.qtt.core.testing.atomicrows_bundle_state import (
    AtomicRowsBundleState,
    expected_atomicrows_bundle_state_from_contract,
)
from src.qtt.core.testing.atomicrows_sha_freeze_final_readiness_state import (
    ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_DEFINITIONS,
    EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
    AtomicRowsShaFreezeFinalReadinessState,
    atomicrows_sha_freeze_final_readiness_state_report,
    canonical_atomicrows_sha_freeze_paths,
    canonical_atomicrows_sha_freeze_presence,
    expected_atomicrows_sha_freeze_final_readiness_state_from_contract,
    validate_atomicrows_sha_freeze_final_readiness_state,
)
from tools import validate_atomicrows_bundle_boundary_state_contract as boundary_gate
from tools import validate_atomicrows_bundle_materialization_manifest as materialization_gate
from tools import validate_atomicrows_bundle_sha_freeze_authority_gate as sha_freeze_gate
from tools import validate_atomicrows_sha_freeze_final_readiness_state_contract as validator
from tools import validate_no_runtime_artifacts


REPO_ROOT = Path(__file__).resolve().parents[2]
_REPORT_CACHE: dict | None = None
_MATERIALIZATION_REPORT_CACHE: dict | None = None


def _write(path: Path, text: str = "test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_valid_bundle(repo_root: Path, rows: int = EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT) -> None:
    paths = canonical_atomicrows_sha_freeze_paths(repo_root)
    paths.bundle_jsonl.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps({"row_index": index}) + "\n" for index in range(1, rows + 1))
    paths.bundle_jsonl.write_text(payload, encoding="utf-8", newline="\n")


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


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        result = validator.validate(repo_root=REPO_ROOT)
        assert result.ok is True, result.failures
        assert result.report is not None
        _REPORT_CACHE = result.report
    return _REPORT_CACHE


def _materialization_report() -> dict:
    global _MATERIALIZATION_REPORT_CACHE
    if _MATERIALIZATION_REPORT_CACHE is None:
        result = materialization_gate.validate(repo_root=REPO_ROOT)
        assert result.ok is True, result.failures
        assert result.report is not None
        _MATERIALIZATION_REPORT_CACHE = result.report
    return _MATERIALIZATION_REPORT_CACHE


def test_contract_schema_validates():
    contract = validator.load_yaml(REPO_ROOT / validator.DEFAULT_CONTRACT)
    schema = validator.load_json(REPO_ROOT / validator.DEFAULT_SCHEMA)

    assert validator.validate_contract_payload(contract, schema) == []
    assert contract["contract_id"] == validator.CONTRACT_ID
    assert contract["current_expected_state"] == "BUNDLE_MATERIALIZED_PRE_SHA_FREEZE"


def test_validator_emits_success_marker_and_writes_report(tmp_path, capsys):
    report_path = tmp_path / "AtomicRowsShaFreezeFinalReadinessStateContract.report.json"

    assert (
        validator.main(
            [
                "--repo-root",
                str(REPO_ROOT),
                "--report-out",
                str(report_path),
            ]
        )
        == 0
    )

    output = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert output == [validator.SUCCESS_MARKER]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["result_marker"] == validator.SUCCESS_MARKER


def test_current_state_passes_with_valid_bundle_and_no_future_artifacts(tmp_path):
    _write_valid_bundle(tmp_path)

    assert (
        validate_atomicrows_sha_freeze_final_readiness_state(
            tmp_path,
            AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE,
            "unit current state",
        )
        == []
    )


def test_current_state_fails_when_bundle_jsonl_missing(tmp_path):
    failures = validate_atomicrows_sha_freeze_final_readiness_state(
        tmp_path,
        AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE,
        "unit missing bundle",
    )

    _assert_failure_contains(failures, "unit missing bundle")
    _assert_failure_contains(failures, "expected_state=BUNDLE_MATERIALIZED_PRE_SHA_FREEZE")
    _assert_failure_contains(failures, "observed_bundle_jsonl_exists=False")


def test_current_state_fails_when_bundle_sha256_exists(tmp_path):
    paths = canonical_atomicrows_sha_freeze_paths(tmp_path)
    _write_valid_bundle(tmp_path)
    _write(paths.bundle_sha256, "UNAUTHORIZED_TEST_SHA\n")

    failures = validate_atomicrows_sha_freeze_final_readiness_state(
        tmp_path,
        AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE,
        "unit sha exists",
    )

    _assert_failure_contains(failures, "unit sha exists")
    _assert_failure_contains(failures, "observed_bundle_sha256_exists=True")
    _assert_failure_contains(failures, paths.bundle_sha256_relative.as_posix())


def test_current_state_fails_when_future_sha_freeze_authority_artifact_exists(tmp_path):
    paths = canonical_atomicrows_sha_freeze_paths(tmp_path)
    _write_valid_bundle(tmp_path)
    authority = next(
        entry for entry in paths.artifact_authority_paths if entry.artifact_kind == "sha_freeze_authority"
    )
    _write(authority.path, "future-only test artifact\n")

    failures = validate_atomicrows_sha_freeze_final_readiness_state(
        tmp_path,
        AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE,
        "unit sha authority exists",
    )

    _assert_failure_contains(failures, "observed_sha_freeze_authority_exists=True")
    _assert_failure_contains(failures, authority.relative.as_posix())


def test_current_state_fails_when_future_final_readiness_artifact_exists(tmp_path):
    paths = canonical_atomicrows_sha_freeze_paths(tmp_path)
    _write_valid_bundle(tmp_path)
    final_readiness = next(
        entry for entry in paths.artifact_authority_paths if entry.artifact_kind == "final_readiness"
    )
    _write(final_readiness.path, "future-only test artifact\n")

    failures = validate_atomicrows_sha_freeze_final_readiness_state(
        tmp_path,
        AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE,
        "unit final readiness exists",
    )

    _assert_failure_contains(failures, "observed_final_readiness_exists=True")
    _assert_failure_contains(failures, final_readiness.relative.as_posix())


def test_future_sha_freeze_state_is_represented_but_not_current():
    definition = ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_DEFINITIONS[
        AtomicRowsShaFreezeFinalReadinessState.SHA_FREEZE_AUTHORIZED_PRE_FINAL_READINESS
    ]

    assert expected_atomicrows_sha_freeze_final_readiness_state_from_contract(REPO_ROOT) == (
        AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE
    )
    assert definition.bundle_sha256_required is True
    assert definition.sha_freeze_authority_required is True
    assert definition.freeze_receipt_required is True
    assert definition.final_readiness_allowed is False


def test_future_final_readiness_state_is_represented_but_not_current():
    definition = ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_DEFINITIONS[
        AtomicRowsShaFreezeFinalReadinessState.FINAL_READINESS_AUTHORIZED
    ]

    assert expected_atomicrows_sha_freeze_final_readiness_state_from_contract(REPO_ROOT) != (
        AtomicRowsShaFreezeFinalReadinessState.FINAL_READINESS_AUTHORIZED
    )
    assert definition.bundle_sha256_required is True
    assert definition.sha_freeze_authority_required is True
    assert definition.final_readiness_required is True
    assert definition.live_trading_allowed is False


def test_helper_reports_correct_current_presence():
    presence = canonical_atomicrows_sha_freeze_presence(REPO_ROOT)
    report = atomicrows_sha_freeze_final_readiness_state_report(
        REPO_ROOT,
        AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE,
    )

    assert presence.bundle_jsonl_exists is True
    assert presence.bundle_sha256_exists is False
    assert presence.sha_freeze_authority_exists is False
    assert presence.freeze_receipt_exists is False
    assert presence.final_readiness_exists is False
    assert report["bundle_row_count"] == 4183
    assert report["bundle_jsonl_valid"] is True


def test_existing_atomicrows_bundle_materialization_validator_still_passes():
    report = _materialization_report()

    assert report["result_marker"] == materialization_gate.SUCCESS_MARKER
    assert report["bundle_row_count"] == 4183


def test_existing_atomicrows_bundle_boundary_state_remains_post_materialization_pre_sha():
    result = boundary_gate.validate(repo_root=REPO_ROOT)

    assert result.ok is True, result.failures
    assert expected_atomicrows_bundle_state_from_contract(REPO_ROOT) == (
        AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA
    )


def test_existing_atomicrows_bundle_sha_freeze_authority_gate_remains_blocked(tmp_path):
    result = sha_freeze_gate.validate(
        repo_root=REPO_ROOT,
        output_path=tmp_path / "sha_freeze.report.json",
    )

    assert result.ok is True, result.failures
    assert result.report is not None
    assert result.report["gate_mode"] == "BLOCKED"
    assert result.report["validation_result"] == "PASS_BLOCKED_EXPECTED"
    assert result.report["freeze_authority_created"] is False
    assert result.report["final_readiness_created"] is False


def test_workflow_still_verifies_bundle_materialized_and_sha_absent():
    workflow = (REPO_ROOT / ".github/workflows/qtt_validation.yml").read_text(encoding="utf-8")

    assert "Verify AtomicRows bundle materialized and SHA absent" in workflow
    assert "test -f docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl" in workflow
    assert "test ! -e docs/master_plan/atomic_rows/AtomicRows.bundle.sha256" in workflow
    assert "expected 4183 AtomicRows rows" in workflow


def test_atomicrows_bundle_sha256_remains_forbidden_in_no_runtime_scanner():
    assert "AtomicRows.bundle.sha256" in validate_no_runtime_artifacts.FORBIDDEN_NAMES


def test_no_runtime_scanner_has_no_pr114a_diff():
    assert _git_stdout("diff", "--", "tools/validate_no_runtime_artifacts.py") == ""


def test_master_plan_current_is_unchanged():
    assert _git_stdout(
        "diff",
        "--name-only",
        "--",
        "docs/master_plan/QTT_MasterPlan_Current.md",
    ) == ""


def test_exact_row_sources_are_unchanged():
    assert _git_stdout(
        "diff",
        "--name-only",
        "--",
        "docs/master_plan/atomic_rows/exact_row_sources",
    ) == ""


def test_atomicrows_bundle_jsonl_is_unchanged():
    assert _git_stdout(
        "diff",
        "--name-only",
        "--",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    ) == ""


def test_no_runtime_live_source_connector_order_cash_backend_profit_quantum_authority():
    report = _report()
    materialization_report = _materialization_report()

    for field in (
        "runtime_live_authority_created",
        "source_connector_authority_created",
        "order_authority_created",
        "profit_evidence_created",
        "quantum_backend_authority_created",
    ):
        assert report[field] is False
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
        "quantum_backend_authority_count",
    ):
        assert materialization_report[field] == 0


def test_no_scoring_ranking_selection_execution():
    report = _report()
    materialization_report = _materialization_report()

    assert report["scoring_ranking_selection_execution_created"] is False
    for field in (
        "scoring_execution_allowed_count",
        "ranking_execution_allowed_count",
        "selection_execution_allowed_count",
        "computed_score_field_count",
        "numeric_ranking_output_count",
        "selected_stack_output_count",
        "selected_order_intent_output_count",
    ):
        assert materialization_report[field] == 0


def test_no_replay_paper_optimizer_quantum_execution():
    report = _report()
    materialization_report = _materialization_report()

    assert report["replay_paper_execution_created"] is False
    assert report["optimizer_execution_created"] is False
    for field in (
        "replay_execution_allowed_count",
        "paper_execution_allowed_count",
        "optimizer_execution_allowed_count",
        "quantum_backend_authority_count",
        "quantum_simulator_authority_count",
        "quantum_provider_authority_count",
        "optimizer_output_count",
        "replay_paper_result_count",
    ):
        assert materialization_report[field] == 0


def test_no_profit_latency_execution_or_quantum_advantage_evidence():
    materialization_report = _materialization_report()

    for field in (
        "profit_evidence_count",
        "expected_profit_proof_count",
        "latency_superiority_evidence_count",
        "execution_superiority_evidence_count",
        "quantum_advantage_evidence_count",
    ):
        assert materialization_report[field] == 0
