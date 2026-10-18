from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys

from tools import qtt_test_gate


def _report() -> dict:
    return qtt_test_gate.build_report(
        repo_root=Path("."),
        phase=qtt_test_gate.PHASE,
        strict_no_claim=True,
    )


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _assert_direct_cli_layout_boundaries(tmp_path: Path) -> None:
    """Real CLI children; receipt files below are synthetic existence fixtures."""
    code_root = Path(__file__).resolve().parents[2]
    foreign_cwd = tmp_path / "unrelated-cwd"
    foreign_cwd.mkdir()
    outputs = tmp_path / "cli-reports"
    outputs.mkdir()
    empty_hooks = tmp_path / "empty-hooks"
    empty_hooks.mkdir()
    empty_excludes = tmp_path / "empty-excludes"
    empty_excludes.write_text("", encoding="utf-8")
    environment = {
        key: value for key, value in os.environ.items()
        if key.upper() != "PYTHONPATH" and not key.upper().startswith("GIT_")
    }
    git_environment = dict(
        environment, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT="0",
    )
    strict_flags = [
        "--forbid-source-retrieval", "--forbid-source-acceptance",
        "--forbid-connector-binding", "--forbid-private-state-fetch",
        "--forbid-order-execution", "--forbid-neural-training",
        "--forbid-neural-inference", "--forbid-external-repo-clone",
        "--forbid-package-install-scripts",
    ]
    for case, rejection in (
        ("absent", None), ("admitted", None), ("hidden-zip", None),
        ("secret", None),
        ("file", "local directory chain contains a link, reparse point or non-directory"),
        ("unignored", "read-only layout custody query returned nonzero"),
        ("tracked", "tracked .qtt path present"),
    ):
        root = tmp_path / case
        root.mkdir()

        def git(*args: str) -> str:
            result = subprocess.run(
                ["git", "-c", "user.name=QTT synthetic fixture",
                 "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
                 "-c", f"core.hooksPath={empty_hooks}",
                 "-c", "core.autocrlf=false", "-C", str(root), *args],
                env=git_environment, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=30, check=False,
            )
            assert result.returncode == 0, (result.args, result.stdout, result.stderr)
            return result.stdout

        git("init", "--quiet", "--template", str(empty_hooks))
        git("config", "--local", "core.excludesFile", str(empty_excludes))
        (root / ".gitignore").write_text(
            "" if case == "unignored" else ".qtt/\n", encoding="utf-8",
        )
        git("add", "--", ".gitignore")
        git("commit", "--quiet", "-m", "Synthetic CLI layout fixture")
        for spec in qtt_test_gate.REQUIRED_RECEIPTS:
            for relative in spec["paths"]:
                receipt = root / relative
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text("{}\n", encoding="utf-8")
        if case == "file":
            (root / ".qtt").write_text("synthetic non-directory", encoding="utf-8")
        elif case != "absent":
            (root / ".qtt").mkdir()
            (root / ".qtt" / "local_input.zip").write_bytes(b"PK")
        if case == "hidden-zip":
            (root / "hidden_authority.zip").write_bytes(b"PK")
        if case == "secret":
            (root / ".env").write_text("SYNTHETIC_ONLY=1\n", encoding="utf-8")
        if case == "tracked":
            git("add", "-f", "--", ".qtt/local_input.zip")
        before_git = (git("rev-parse", "HEAD"), git("status", "--porcelain=v1"))
        report_path = outputs / f"{case}.json"
        assert not report_path.exists()
        outcomes = []
        for script, arguments in (
            ("qtt_test_gate.py", ["--phase", "first-coding-runbook",
             "--repo-root", str(root), "--strict-no-claim", "--out", str(report_path)]),
            ("validate_no_runtime_artifacts.py", ["--repo-root", str(root), *strict_flags]),
        ):
            try:
                outcomes.append(subprocess.run(
                    [sys.executable, "-I", "-B", str(code_root / "tools" / script), *arguments],
                    cwd=foreign_cwd, env=environment, stdin=subprocess.DEVNULL,
                    capture_output=True, text=True, timeout=30, check=False,
                ))
            except subprocess.TimeoutExpired as exc:
                outcomes.append(exc)
        # Both actual entry points run before any outcome assertion for this case.
        details = "\n".join(
            f"{case}: {result.args!r}\nexit={getattr(result, 'returncode', None)}"
            f"\nstdout={result.stdout}\nstderr={result.stderr}"
            for result in outcomes
        )
        assert all(isinstance(result, subprocess.CompletedProcess) for result in outcomes), details
        gate, scanner = outcomes
        assert all("ModuleNotFoundError" not in result.stderr and
                   "ImportError" not in result.stderr for result in outcomes), details
        assert before_git == (git("rev-parse", "HEAD"), git("status", "--porcelain=v1"))
        if rejection is not None:
            for result in outcomes:
                assert result.returncode == 1, details
                assert f"ENGVR_REPOSITORY_LOCAL_LAYOUT_REJECTED: {rejection}" in result.stderr, details
            assert "QTT_CUMULATIVE_TEST_GATE_OK" not in gate.stdout, details
            assert "NO_RUNTIME_ARTIFACT_GATE_OK" not in scanner.stdout, details
            assert "NO_RUNTIME_ARTIFACT_GATE_FAILED" in scanner.stderr.splitlines(), details
            assert not report_path.exists(), details
            continue
        assert gate.returncode == (1 if case == "hidden-zip" else 0), details
        assert gate.stderr == "", details
        assert report_path.is_file(), details
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["status"] == ("FAIL" if case == "hidden-zip" else "PASS"), details
        assert report["strict_no_claim"] is True
        assert all(value is False for value in report["no_claim_flags"].values())
        for record in (report["metadata"], *report["prior_gate_receipts"]):
            assert all(record[field] is False for field in qtt_test_gate.STATIC_AUTHORITY_FLAGS)
        filesystem = report["filesystem_claim_checks"]
        assert filesystem["hidden_zip_paths"] == (["hidden_authority.zip"] if case == "hidden-zip" else [])
        assert filesystem["hidden_zip_authority_present"] is (case == "hidden-zip")
        if case == "hidden-zip":
            assert gate.stdout.splitlines()[0] == "QTT_CUMULATIVE_TEST_GATE_FAILED", details
            assert report["findings"] == [
                "gate_checks.no_hidden_zip_authority must be true",
                "qtt test gate report.filesystem_claim_checks.hidden_zip_authority_present must remain false",
                "qtt test gate report: hidden ZIP authority must remain absent",
            ]
        else:
            assert gate.stdout.strip() == "QTT_CUMULATIVE_TEST_GATE_OK", details
            assert report["findings"] == []
        if case == "secret":
            assert scanner.returncode == 1, details
            assert "NO_RUNTIME_ARTIFACT_GATE_FAILED" in scanner.stderr.splitlines(), details
            assert "- forbidden runtime/secret artifact present: .env" in scanner.stderr.splitlines(), details
            assert "NO_RUNTIME_ARTIFACT_GATE_OK" not in scanner.stdout, details
        else:
            assert scanner.returncode == 0, details
            assert scanner.stdout.strip() == "NO_RUNTIME_ARTIFACT_GATE_OK", details


def test_qtt_cumulative_gate_valid_static_report_passes():
    report = _report()

    assert report["status"] == "PASS"
    assert report["findings"] == []
    assert (
        qtt_test_gate.validate_qtt_test_gate_report(
            report,
            repo_root=Path("."),
            strict_no_claim=True,
        )
        == []
    )


def test_qtt_cumulative_gate_requires_stage1_runtime_scaffold_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"] == "stage1_runtime_scaffold_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert (
        receipt["validation_marker"]
        == "STAGE1_RUNTIME_SCAFFOLD_GATE_STATIC_VALIDATION_OK"
    )


def test_qtt_cumulative_gate_requires_pr40_connector_semantic_binding_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "connector_semantic_binding_ledger_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK_OK"


def test_qtt_cumulative_gate_requires_pr41_runtime_resolver_snapshot_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "runtime_resolver_snapshot_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_CHECK_OK"


def test_qtt_cumulative_gate_requires_pr42_runtime_resolver_handoff_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "runtime_resolver_to_replay_paper_handoff_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert (
        receipt["validation_marker"]
        == "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_OK"
    )


def test_qtt_cumulative_gate_requires_pr43_concurrent_replay_paper_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"] == "concurrent_replay_paper_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_CHECK_OK"


def test_qtt_cumulative_gate_requires_pr44_dual_result_review_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"] == "dual_result_review_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "STAGE1_DUAL_RESULT_REVIEW_CONTRACT_CHECK_OK"


def test_qtt_cumulative_gate_requires_pr45_owner_live_promotion_review_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "owner_live_promotion_review_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert (
        receipt["validation_marker"]
        == "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_CHECK_OK"
    )


def test_qtt_cumulative_gate_requires_pr46_three_venue_canary_eligibility_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "three_venue_canary_eligibility_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert (
        receipt["validation_marker"]
        == "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_CHECK_OK"
    )


def test_qtt_cumulative_gate_represents_all_prior_receipts_or_static_bootstrap():
    report = _report()
    statuses = {item["receipt_id"]: item["status"] for item in report["prior_gate_receipts"]}

    assert statuses["owner_start_receipt_present_or_reported_missing"] == (
        "REQUIRED_PRIOR_GATE_REPORT_NOT_CREATED_STATIC_BOOTSTRAP"
    )
    assert statuses["master_plan_hash_receipt_present_or_reported_missing"] == (
        "REQUIRED_PRIOR_GATE_REPORT_NOT_CREATED_STATIC_BOOTSTRAP"
    )
    assert all(status != "MISSING_BLOCKED" for status in statuses.values())


def test_qtt_cumulative_gate_blocks_hidden_zip_authority(tmp_path):
    report = _report()
    control_zip_path = tmp_path / ".codex_inputs" / "owner_control.zip"
    control_zip_path.parent.mkdir()
    control_zip_path.write_bytes(b"PK")
    zip_path = tmp_path / "hidden_authority.zip"
    zip_path.write_bytes(b"PK")

    assert qtt_test_gate.hidden_zip_paths(tmp_path) == [
        qtt_test_gate.pathlib.PurePosixPath("hidden_authority.zip"),
    ]

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=tmp_path,
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "hidden ZIP authority")

    nested_zip_path = (
        tmp_path / "nested" / ".codex_inputs" / "hidden_authority.zip"
    )
    nested_zip_path.parent.mkdir(parents=True)
    nested_zip_path.write_bytes(b"PK")

    assert qtt_test_gate.hidden_zip_paths(tmp_path) == [
        qtt_test_gate.pathlib.PurePosixPath("hidden_authority.zip"),
        qtt_test_gate.pathlib.PurePosixPath(
            "nested/.codex_inputs/hidden_authority.zip"
        ),
    ]
    _assert_direct_cli_layout_boundaries(tmp_path)


def test_qtt_cumulative_gate_blocks_direct_main_bypass_claim():
    report = _report()
    report["filesystem_claim_checks"]["direct_main_bypass_claim_present"] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "direct_main_bypass_claim_present")


def test_qtt_cumulative_gate_blocks_atomicrows_invention_claim():
    report = _report()
    report["no_claim_flags"]["atomicrows_invention_claim"] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "atomicrows_invention_claim")


def test_qtt_cumulative_gate_blocks_stale_generated_derivative_completion_claim():
    report = _report()
    report["no_claim_flags"]["stale_generated_derivative_completion_claim"] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "stale_generated_derivative_completion_claim")


def test_actual_atomicrows_bundle_existing_at_canonical_path_fails(tmp_path):
    report = _report()
    bundle_path = (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "AtomicRows.bundle.jsonl"
    )
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("{}\n", encoding="utf-8")

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=tmp_path,
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle")


def test_actual_atomicrows_bundle_sha_existing_at_canonical_path_fails(tmp_path):
    report = _report()
    sha_path = (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "AtomicRows.bundle.sha256"
    )
    sha_path.parent.mkdir(parents=True)
    sha_path.write_text("UNAUTHORIZED_STATIC_TEST_PLACEHOLDER\n", encoding="utf-8")

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=tmp_path,
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle hash")


def test_qtt_cumulative_gate_validation_does_not_mutate_report():
    report = _report()
    frozen = copy.deepcopy(report)

    assert (
        qtt_test_gate.validate_qtt_test_gate_report(
            report,
            repo_root=Path("."),
            strict_no_claim=True,
        )
        == []
    )
    assert report == frozen


def test_qtt_generated_static_reports_create_no_authority():
    for path in [
        Path("docs/master_plan/generated/QTTTestGate.report.json"),
        Path("docs/master_plan/generated/LocalGateCommandMatrix.json"),
        Path("docs/master_plan/generated/FirstCodingPRHandoff.packet.json"),
    ]:
        report = json.loads(path.read_text(encoding="utf-8"))
        metadata = report["metadata"]
        assert metadata["authority_class"] == "STATIC_REPORT_ONLY_NOT_TRADING_AUTHORITY"
        for field in qtt_test_gate.STATIC_AUTHORITY_FLAGS:
            assert metadata[field] is False


def test_qtt_test_gate_schema_is_closed_at_root():
    schema = json.loads(
        Path("src/qtt/core/schemas/qtt_test_gate_report.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "prior_gate_receipts" in schema["required"]
