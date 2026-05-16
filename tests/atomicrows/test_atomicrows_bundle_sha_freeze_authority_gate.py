from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_bundle_sha_freeze_authority_gate as validator


ROOT = Path(".")
_REPORT_CACHE: dict | None = None


def _clear_branch_context_env(monkeypatch) -> None:
    for env_name in ("GITHUB_ACTIONS", *validator.BRANCH_CONTEXT_ENV_CANDIDATES):
        monkeypatch.delenv(env_name, raising=False)


def _mock_git_branch(monkeypatch, branch: str, *, detached: bool = False) -> None:
    original_git_stdout = validator.pr98_gate._git_stdout

    def fake_git_stdout(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, "" if detached else branch, ""
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, "HEAD" if detached else branch, ""
        return original_git_stdout(repo_root, args)

    monkeypatch.setattr(validator.pr98_gate, "_git_stdout", fake_git_stdout)


def _schema() -> dict:
    return validator.load_json(ROOT / validator.DEFAULT_SCHEMA)


def _config() -> dict:
    return validator.load_yaml(ROOT / validator.DEFAULT_CONFIG)


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        result = validator.validate(repo_root=ROOT)
        assert result.ok is True
        assert result.report is not None
        _REPORT_CACHE = result.report
    return _REPORT_CACHE


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_static_yaml_validates_against_schema_and_required_identity():
    config = _config()

    assert validator.validate_config_payload(config, _schema()) == []
    assert config["artifact_id"] == validator.ARTIFACT_ID
    assert config["roadmap_pr"] == "PR_100"
    assert config["semantic_task_id"] == validator.SEMANTIC_TASK_ID
    assert config["authority_class"] == validator.AUTHORITY_CLASS
    assert config["gate_mode"] == "BLOCKED"


def test_validator_emits_blocked_success_marker_and_writes_report(tmp_path, capsys):
    report_path = tmp_path / "AtomicRowsBundleShaFreezeAuthorityGate.report.json"

    assert (
        validator.main(
            [
                "--repo-root",
                str(ROOT),
                "--config",
                str(validator.DEFAULT_CONFIG),
                "--report-out",
                str(report_path),
            ]
        )
        == 0
    )

    output_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert output_lines[0] == validator.SUCCESS_MARKER
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["validation_result"] == "PASS_BLOCKED_EXPECTED"
    assert report["gate_mode"] == "BLOCKED"
    assert report["validator_stdout_marker"] == validator.SUCCESS_MARKER


def test_materialized_bundle_and_missing_sha_block_sha_freeze_authority():
    report = _report()

    assert report["atomicrows_bundle_jsonl_exists"] is True
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert report["forbidden_artifacts_absent"]["AtomicRows.bundle.jsonl"] is False
    assert report["forbidden_artifacts_absent"]["AtomicRows.bundle.sha256"] is True
    assert report["sha_materialization_allowed"] is False
    assert (
        "ATOMICROWS_SHA_FREEZE_BLOCKED_POST_MATERIALIZATION_PRE_SHA_STATE"
        in report["blocked_reason_codes"]
    )
    assert "ATOMICROWS_SHA_FREEZE_BLOCKED_SHA_FILE_MUST_NOT_BE_CREATED" in report["blocked_reason_codes"]


def test_no_sha_digest_value_or_digest_computation_exists():
    config = _config()
    report = _report()

    assert validator.validate_no_digest_values(config, "CONFIG") == []
    assert validator.validate_no_digest_values(report, "REPORT") == []
    assert config["actual_sha256_value"] is None
    assert config["digest_value"] is None
    assert report["actual_sha256_value"] is None
    assert report["digest_value"] is None
    assert report["sha_computation_attempted"] is False
    assert report["sha_computed"] is False
    assert report["missing_bundle_digest_computation_blocked"] is False


def test_materialized_bundle_remains_and_sha_file_remains_absent_after_validator(tmp_path):
    bundle_path = ROOT / validator.CANONICAL_BUNDLE_JSONL
    sha_path = ROOT / validator.CANONICAL_BUNDLE_SHA256

    assert bundle_path.exists()
    assert not sha_path.exists()
    assert (
        validator.main(
            [
                "--repo-root",
                str(ROOT),
                "--out",
                str(tmp_path / "report.json"),
            ]
        )
        == 0
    )
    assert bundle_path.exists()
    assert not sha_path.exists()


def test_pr99_path_b_blocked_state_and_pr98_blueprints_are_preserved():
    report = _report()
    upstream = report["upstream_status"]

    assert upstream["pr99_assembly_path"] == "PATH_B_BLOCKED"
    assert upstream["pr99_build_path_decision"] == validator.builder.PATH_DECISION
    assert upstream["pr99_build_allowed_flag"] is False
    assert upstream["pr99_build_blocked_flag"] is True
    assert upstream["source_file_count_found"] == 15
    assert upstream["source_blueprints_found_count"] == 15
    assert upstream["exact_source_rows_found_count"] == 0
    assert upstream["pr98_source_files_are_blueprints_only"] is True
    assert all(
        entry["declared_source_blueprint_count"] == 1
        and entry["declared_source_record_count"] == 0
        and entry["exact_row_count_created_by_pr98_flag"] is False
        for entry in upstream["source_file_entries"]
    )


def test_final_readiness_remains_blocked():
    report = _report()

    assert report["final_readiness_created"] is False
    assert report["downstream_status"]["roadmap_pr101_final_readiness_gate"] == (
        "BLOCKED_UNTIL_VALID_BUNDLE_AND_SHA_FREEZE_AUTHORITY_EXIST"
    )
    assert report["downstream_blocked_until"] == ["ROADMAP_ATOMICROWS_FULL_BUNDLE_READINESS"]
    failures = validator.validate_no_forbidden_artifacts(
        ROOT,
        extra_existing_paths=(
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsFullBundleFinalReadinessGate.report.json",
        ),
    )
    _assert_failure_contains(failures, "AtomicRowsFullBundleFinalReadinessGate.report.json")


def test_runtime_live_order_source_connector_profit_and_quantum_backend_claims_are_false():
    no_claims = _report()["no_claims_confirmed"]

    for field in validator.NO_CLAIM_FALSE_FIELDS:
        assert no_claims[field] is False


def test_quantum_metadata_is_static_and_non_executable_only():
    report = _report()
    quantum = report["quantum_static_metadata_confirmed"]

    for field in validator.QUANTUM_TRUE_FIELDS:
        assert quantum[field] is True
    for field in validator.QUANTUM_FALSE_FIELDS:
        assert quantum[field] is False
    for effect in [
        "QUBO_SOLVING",
        "ISING_SOLVING",
        "QAOA_EXECUTION",
        "VQE_EXECUTION",
        "ANNEALING_EXECUTION",
        "QUANTUM_INSPIRED_OPTIMIZER_EXECUTION",
        "QUANTUM_SIMULATOR_EXECUTION",
        "QUANTUM_PROVIDER_CALL",
        "TRUE_QUANTUM_BACKEND_EXECUTION",
        "QUANTUM_ADVANTAGE_VALIDATION",
    ]:
        assert effect in report["forbidden_execution_effects"]


def test_schema_and_custom_validation_fail_closed_for_open_gate_or_sha_output():
    schema = _schema()
    config = copy.deepcopy(_config())
    config["gate_mode"] = "OPEN"
    _assert_failure_contains(
        validator.validate_config_payload(config, schema),
        "gate_mode",
    )

    config = copy.deepcopy(_config())
    config["outputs_created_by_this_pr"] = [validator.CANONICAL_BUNDLE_SHA256.as_posix()]
    _assert_failure_contains(
        validator.validate_config_payload(config, schema),
        "outputs_created_by_this_pr",
    )


def test_schema_and_custom_validation_fail_closed_for_sha_digest_or_claims():
    schema = _schema()
    config = copy.deepcopy(_config())
    config["actual_sha256_value"] = "a" * 64
    _assert_failure_contains(
        validator.validate_config_payload(config, schema),
        "actual_sha256_value",
    )

    config = copy.deepcopy(_config())
    config["no_claims"]["quantum_backend_executed"] = True
    _assert_failure_contains(
        validator.validate_config_payload(config, schema),
        "quantum_backend_executed",
    )


def test_owner_authority_boundary_preserves_internal_authority_without_fabrication():
    boundary = _config()["owner_authority_boundary"]

    assert boundary["owner_global_internal_workflow_authority_preserved"] is True
    assert boundary["owner_approval_may_approve_future_internal_workflow_movement"] is True
    assert boundary["owner_approval_does_not_create_sha_freeze_truth"] is True
    for item in validator.OWNER_APPROVAL_CANNOT_FABRICATE:
        assert item in boundary["owner_approval_cannot_fabricate"]


def test_main_cumulative_and_repair_context_remain_supported(monkeypatch, tmp_path, capsys):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", "repair/main-cumulative-pr101-validation-context")
    _mock_git_branch(monkeypatch, "ignored", detached=True)

    assert validator.main(["--out", str(tmp_path / "repair.report.json")]) == 0
    output_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert output_lines[0] == validator.SUCCESS_MARKER
    assert set(output_lines[1:]) <= {validator.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER}


def test_validator_static_surface_does_not_import_runtime_quantum_or_materialize_calls():
    assert (
        validator.validate_static_surface(
            ROOT / "tools" / "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
        )
        == []
    )


def test_master_plan_is_unchanged_and_forbidden_artifacts_are_absent():
    assert validator.validate_master_plan_not_modified(ROOT) == []
    assert validator.validate_no_forbidden_artifacts(ROOT) == []
    assert (ROOT / validator.CANONICAL_BUNDLE_JSONL).exists()
    assert not (ROOT / validator.CANONICAL_BUNDLE_SHA256).exists()
