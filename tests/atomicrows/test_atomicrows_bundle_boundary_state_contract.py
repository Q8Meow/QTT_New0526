from __future__ import annotations

import json
from pathlib import Path
import subprocess

from src.qtt.core.testing.atomicrows_bundle_state import (
    ATOMICROWS_BUNDLE_STATE_DEFINITIONS,
    AtomicRowsBundleState,
    canonical_atomicrows_bundle_paths,
    expected_atomicrows_bundle_state_from_contract,
    validate_atomicrows_bundle_state,
)
from src.qtt.core.testing.gate_result import canonical_atomicrows_absence_failures
from tools import validate_atomicrows_bundle_boundary_state_contract as validator
from tools import validate_atomicrows_bundle_schema_checker_static as schema_checker
from tools import validate_no_runtime_artifacts


REPO_ROOT = Path(__file__).resolve().parents[2]
ROW_SCHEMA_PATH = REPO_ROOT / "schemas/atomicrows/atomic_parameter_row.schema.json"
BUNDLE_SCHEMA_PATH = REPO_ROOT / "schemas/atomicrows/atomic_row_bundle.schema.json"
BUNDLE_SCHEMA_FIXTURE = (
    REPO_ROOT
    / "tests/fixtures/atomicrows/synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json"
)


def _write(path: Path, text: str = "test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


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


def test_contract_schema_validates_and_preserves_required_identity():
    contract = validator.load_yaml(REPO_ROOT / validator.DEFAULT_CONTRACT)
    schema = validator.load_json(REPO_ROOT / validator.DEFAULT_SCHEMA)

    assert validator.validate_contract_payload(contract, schema) == []
    assert contract["contract_id"] == validator.CONTRACT_ID
    assert contract["authority_class"] == validator.AUTHORITY_CLASS
    assert contract["current_expected_state"] == "PRE_MATERIALIZATION"


def test_validator_emits_success_marker_and_writes_report(tmp_path, capsys):
    report_path = tmp_path / "AtomicRowsBundleBoundaryStateContract.report.json"

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
    assert report["current_expected_state"] == "PRE_MATERIALIZATION"


def test_current_pre_materialization_state_passes_when_bundle_and_sha_are_absent(tmp_path):
    assert (
        validate_atomicrows_bundle_state(
            tmp_path,
            AtomicRowsBundleState.PRE_MATERIALIZATION,
            "unit PRE",
        )
        == []
    )


def test_current_pre_materialization_state_fails_when_bundle_jsonl_exists(tmp_path):
    paths = canonical_atomicrows_bundle_paths(tmp_path)
    _write(paths.bundle_jsonl, "{}\n")

    failures = validate_atomicrows_bundle_state(
        tmp_path,
        AtomicRowsBundleState.PRE_MATERIALIZATION,
        "unit PRE bundle exists",
    )

    _assert_failure_contains(failures, "unit PRE bundle exists")
    _assert_failure_contains(failures, "expected_state=PRE_MATERIALIZATION")
    _assert_failure_contains(failures, "observed_bundle_jsonl_exists=True")
    _assert_failure_contains(failures, paths.bundle_jsonl_relative.as_posix())


def test_current_pre_materialization_state_fails_when_bundle_sha_exists(tmp_path):
    paths = canonical_atomicrows_bundle_paths(tmp_path)
    _write(paths.bundle_sha256, "UNAUTHORIZED_TEST_SHA\n")

    failures = validate_atomicrows_bundle_state(
        tmp_path,
        AtomicRowsBundleState.PRE_MATERIALIZATION,
        "unit PRE sha exists",
    )

    _assert_failure_contains(failures, "unit PRE sha exists")
    _assert_failure_contains(failures, "expected_state=PRE_MATERIALIZATION")
    _assert_failure_contains(failures, "observed_bundle_sha256_exists=True")
    _assert_failure_contains(failures, paths.bundle_sha256_relative.as_posix())


def test_future_post_materialization_pre_sha_state_passes_with_bundle_and_no_sha(tmp_path):
    paths = canonical_atomicrows_bundle_paths(tmp_path)
    _write(paths.bundle_jsonl, "{}\n")

    assert (
        validate_atomicrows_bundle_state(
            tmp_path,
            AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA,
            "unit POST materialization",
        )
        == []
    )


def test_future_post_materialization_pre_sha_state_fails_when_bundle_missing(tmp_path):
    failures = validate_atomicrows_bundle_state(
        tmp_path,
        AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA,
        "unit POST missing bundle",
    )

    _assert_failure_contains(failures, "unit POST missing bundle")
    _assert_failure_contains(failures, "expected_state=POST_MATERIALIZATION_PRE_SHA")
    _assert_failure_contains(failures, "canonical AtomicRows bundle is required but missing")


def test_future_post_materialization_pre_sha_state_fails_when_sha_exists(tmp_path):
    paths = canonical_atomicrows_bundle_paths(tmp_path)
    _write(paths.bundle_jsonl, "{}\n")
    _write(paths.bundle_sha256, "UNAUTHORIZED_TEST_SHA\n")

    failures = validate_atomicrows_bundle_state(
        tmp_path,
        AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA,
        "unit POST sha exists",
    )

    _assert_failure_contains(failures, "unit POST sha exists")
    _assert_failure_contains(failures, "expected_state=POST_MATERIALIZATION_PRE_SHA")
    _assert_failure_contains(failures, "canonical AtomicRows bundle hash must remain absent")


def test_post_sha_freeze_state_is_represented_but_not_current():
    definition = ATOMICROWS_BUNDLE_STATE_DEFINITIONS[
        AtomicRowsBundleState.POST_SHA_FREEZE
    ]

    assert expected_atomicrows_bundle_state_from_contract(REPO_ROOT) == (
        AtomicRowsBundleState.PRE_MATERIALIZATION
    )
    assert definition.bundle_jsonl_required is True
    assert definition.bundle_sha_required is True
    assert definition.sha_freeze_authority_allowed is True
    assert definition.final_readiness_allowed is False


def test_canonical_atomicrows_absence_wrapper_preserves_pre_materialization_semantics(
    tmp_path,
):
    paths = canonical_atomicrows_bundle_paths(tmp_path)
    assert canonical_atomicrows_absence_failures(tmp_path, "compat wrapper") == []

    _write(paths.bundle_jsonl, "{}\n")
    failures = canonical_atomicrows_absence_failures(tmp_path, "compat wrapper")

    _assert_failure_contains(failures, "compat wrapper")
    _assert_failure_contains(failures, "expected_state=PRE_MATERIALIZATION")
    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")


def test_existing_bundle_schema_checker_uses_central_helper_and_rejects_current_bundle(
    tmp_path,
    monkeypatch,
):
    paths = canonical_atomicrows_bundle_paths(tmp_path)
    _write(paths.bundle_jsonl, "{}\n")
    calls: list[tuple[Path, str]] = []
    original = schema_checker.validate_current_atomicrows_bundle_state

    def wrapped(repo_root: Path, label: str) -> list[str]:
        calls.append((repo_root, label))
        return original(repo_root, label)

    monkeypatch.setattr(schema_checker, "validate_current_atomicrows_bundle_state", wrapped)

    failures = schema_checker.validate_static_surface(
        row_schema_path=ROW_SCHEMA_PATH,
        bundle_schema_path=BUNDLE_SCHEMA_PATH,
        fixture_path=BUNDLE_SCHEMA_FIXTURE,
        repo_root=tmp_path,
    )

    assert calls == [(tmp_path, "bootstrap validation")]
    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")
    _assert_failure_contains(failures, "expected_state=PRE_MATERIALIZATION")


def test_atomicrows_bundle_jsonl_is_not_created():
    paths = canonical_atomicrows_bundle_paths(REPO_ROOT)

    assert not paths.bundle_jsonl.exists()


def test_atomicrows_bundle_sha256_is_not_created():
    paths = canonical_atomicrows_bundle_paths(REPO_ROOT)

    assert not paths.bundle_sha256.exists()


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


def test_no_runtime_scanner_scope_is_unchanged():
    assert _git_stdout("diff", "--", "tools/validate_no_runtime_artifacts.py") == ""
    assert "AtomicRows.bundle.jsonl" in validate_no_runtime_artifacts.FORBIDDEN_NAMES


def test_atomicrows_bundle_sha256_remains_forbidden_in_no_runtime_scanner():
    assert "AtomicRows.bundle.sha256" in validate_no_runtime_artifacts.FORBIDDEN_NAMES


def test_no_runtime_live_source_connector_order_cash_backend_profit_quantum_authority(
    tmp_path,
):
    report_path = tmp_path / "AtomicRowsBundleBoundaryStateContract.report.json"
    result = validator.validate(repo_root=REPO_ROOT, report_out=report_path)

    assert result.ok is True, result.failures
    assert result.report is not None
    report = result.report
    assert report["runtime_live_authority_created"] is False
    assert report["source_connector_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["quantum_backend_authority_created"] is False
    assert report["sha_freeze_authority_created"] is False
    assert report["final_readiness_created"] is False
