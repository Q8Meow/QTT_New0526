from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import build_atomicrows_bundle as builder
from tools import validate_atomicrows_bundle_builder_deterministic_assembly_gate as validator


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
    return validator.load_yaml(ROOT / validator.DEFAULT_BUILDER_CONFIG)


def _fixture() -> dict:
    return validator.load_json(ROOT / validator.DEFAULT_FIXTURE)


def _inputs() -> builder.BundleInputs:
    inputs, failures = builder.load_bundle_inputs(repo_root=ROOT.resolve())
    assert failures == []
    assert inputs is not None
    return inputs


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert validator.main([]) == 0
        _REPORT_CACHE = json.loads((ROOT / validator.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _blocked_reasons_for_source_files(
    source_files: dict[str, dict],
    *,
    repo_root: Path = ROOT,
) -> tuple[str, ...]:
    inputs = _inputs()
    summary = builder.summarize_source_files(
        repo_root=repo_root.resolve(),
        pr97_plan=inputs.pr97_plan,
        source_files=source_files,
    )
    mutated_inputs = builder.BundleInputs(
        builder_config=inputs.builder_config,
        pr97_plan=inputs.pr97_plan,
        pr98_source_file_set=inputs.pr98_source_file_set,
        pr98_report=inputs.pr98_report,
        source_summary=summary,
    )
    return builder.build_block_reason_codes(mutated_inputs)


def test_production_builder_gate_validates_and_report_is_deterministic(capsys):
    first = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        builder_config_path=validator.DEFAULT_BUILDER_CONFIG,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    second = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        builder_config_path=validator.DEFAULT_BUILDER_CONFIG,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    report_text = (ROOT / validator.DEFAULT_REPORT).read_text(encoding="utf-8")
    branch_context = validator.pr98_gate._current_branch_context(ROOT)
    default_report_write_skipped = validator._should_skip_default_report_write(
        repo_root=ROOT.resolve(),
        output_abs=(ROOT / validator.DEFAULT_REPORT).resolve(),
        metadata={"branch": branch_context.branch},
    )

    assert first.failures == second.failures == ()
    assert first.report == second.report
    if not default_report_write_skipped:
        assert first.report == json.loads(report_text)
    assert report_text == json.dumps(json.loads(report_text), indent=2, sort_keys=True) + "\n"
    assert validator.main([]) == 0
    output_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    allowed = {
        validator.SUCCESS_MARKER,
        validator.CI_DETACHED_HEAD_MODE_MARKER,
        validator.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER,
        validator.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER,
    }
    assert output_lines
    assert output_lines[0] == validator.SUCCESS_MARKER
    assert set(output_lines[1:]) <= allowed


def test_pr99_validator_allows_main_cumulative_context_stdout(
    tmp_path,
    monkeypatch,
    capsys,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    _mock_git_branch(monkeypatch, "ignored", detached=True)

    assert validator.main(["--out", str(tmp_path / "report.json")]) == 0

    output_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert output_lines == [validator.SUCCESS_MARKER]


def test_required_concepts_config_schema_fixture_and_report_exist():
    config = _config()
    fixture = _fixture()
    report = _report()

    assert validator.validate_builder_config(config, _schema()) == []
    assert config["required_builder_concepts"] == list(validator.REQUIRED_CONCEPTS)
    assert report["builder_id"] == "ATOMICROWS_DETERMINISTIC_BUNDLE_BUILDER_CONFIG"
    assert report["source_file_consumer_contract"]["contract_id"] == (
        "ATOMICROWS_ROW_FAMILY_SOURCE_FILE_CONSUMER_CONTRACT"
    )
    assert report["assembly_gate"]["gate_id"] == "ATOMICROWS_BUNDLE_ASSEMBLY_GATE"
    assert report["report_id"] == "ATOMICROWS_BUNDLE_BUILDER_DRY_RUN_REPORT"
    assert report["output_contract"]["contract_id"] == "ATOMICROWS_BUNDLE_JSONL_OUTPUT_CONTRACT"
    assert report["forbidden_artifact_boundary"]["boundary_id"] == (
        "ATOMICROWS_BUNDLE_BUILDER_FORBIDDEN_ARTIFACT_BOUNDARY"
    )
    assert report["quantum_metadata_validation"]["validation_id"] == (
        "ATOMICROWS_BUNDLE_BUILDER_QUANTUM_METADATA_VALIDATION"
    )
    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"


def test_pr97_pr98_consumption_and_source_file_contract_are_path_stable():
    inputs = _inputs()
    summary = inputs.source_summary
    report = _report()

    assert inputs.builder_config["consumes_pr97_expansion_plan_flag"] is True
    assert inputs.builder_config["consumes_pr98_source_files_flag"] is True
    assert inputs.pr98_source_file_set["consumes_pr97_expansion_plan_flag"] is True
    assert inputs.pr98_report["source_file_count"] == 15
    assert report["source_file_count_expected"] == 15
    assert report["source_file_count_found"] == 15
    assert len(summary.ordered_paths) == 15
    assert len(summary.source_files) == 15
    assert summary.missing_source_files == ()
    assert summary.unknown_source_files == ()
    assert report["target_total_row_count"] == 4183
    assert report["target_total_row_count_planning_authority_only_flag"] is True
    assert [entry["planned_path"] for entry in report["source_file_consumer_contract"]["source_files"]] == list(
        summary.ordered_paths
    )


def test_path_b_is_selected_for_blueprint_only_sources_and_bundle_is_not_created():
    report = _report()

    assert report["build_path_decision"] == builder.PATH_DECISION
    assert report["build_allowed_flag"] is False
    assert report["build_blocked_flag"] is True
    assert report["bundle_file_created_flag"] is False
    assert report["bundle_sha_created_flag"] is False
    assert report["exact_source_rows_found_count"] == 0
    assert report["source_blueprints_found_count"] == 15
    assert report["blueprint_only_source_files_detected_flag"] is True
    assert builder.BUILD_BLOCKED_REASON_EXACT_SOURCE_ROWS in report["blocked_reason_codes"]
    assert not (ROOT / builder.CANONICAL_BUNDLE_JSONL).exists()
    assert not (ROOT / builder.CANONICAL_BUNDLE_SHA256).exists()


def test_materialize_mode_fails_closed_from_blueprints_without_creating_bundle(tmp_path):
    report_path = tmp_path / "blocked.report.json"

    assert (
        builder.main(
            [
                "--repo-root",
                str(ROOT),
                "--out",
                str(report_path),
                "--materialize",
            ]
        )
        == 1
    )
    assert report_path.exists()
    assert not (ROOT / builder.CANONICAL_BUNDLE_JSONL).exists()
    assert not (ROOT / builder.CANONICAL_BUNDLE_SHA256).exists()


def test_duplicate_source_file_id_row_family_ownership_and_row_id_fail_closed():
    source_files = copy.deepcopy(_inputs().source_summary.source_files)
    paths = list(builder.expected_source_paths(_inputs().pr97_plan))
    source_files[paths[1]]["source_file_id"] = source_files[paths[0]]["source_file_id"]
    assert "ATOMICROWS_BUNDLE_BUILD_BLOCKED_DUPLICATE_SOURCE_FILE_IDS" in (
        _blocked_reasons_for_source_files(source_files)
    )

    source_files = copy.deepcopy(_inputs().source_summary.source_files)
    source_files[paths[1]]["row_family_id"] = source_files[paths[0]]["row_family_id"]
    assert "ATOMICROWS_BUNDLE_BUILD_BLOCKED_DUPLICATE_ROW_FAMILY_OWNERSHIP" in (
        _blocked_reasons_for_source_files(source_files)
    )

    source_files = copy.deepcopy(_inputs().source_summary.source_files)
    exact_record = {
        "canonical_order": 1,
        "exact_row_created_flag": True,
        "record_class": "EXACT_SOURCE_ROW_RECORD",
        "row_family_id": source_files[paths[0]]["row_family_id"],
        "row_id": "AR_EXACT_ROW_DUPLICATE",
    }
    source_files[paths[0]]["source_records_or_blueprints"] = [copy.deepcopy(exact_record)]
    source_files[paths[1]]["source_records_or_blueprints"] = [copy.deepcopy(exact_record)]
    assert "ATOMICROWS_BUNDLE_BUILD_BLOCKED_DUPLICATE_ROW_IDS" in (
        _blocked_reasons_for_source_files(source_files)
    )


def test_unknown_source_file_and_nondeterministic_order_fail_closed(tmp_path):
    inputs = _inputs()
    source_files = copy.deepcopy(inputs.source_summary.source_files)
    unknown = (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "pr98_row_family_sources"
        / "999_unknown.source.jsonl"
    )
    unknown.parent.mkdir(parents=True, exist_ok=True)
    unknown.write_text("{}\n", encoding="utf-8")

    assert "ATOMICROWS_BUNDLE_BUILD_BLOCKED_UNKNOWN_SOURCE_FILES" in (
        _blocked_reasons_for_source_files(source_files, repo_root=tmp_path)
    )

    paths = list(builder.expected_source_paths(inputs.pr97_plan))
    source_files[paths[0]]["canonical_order"] = 99
    assert "ATOMICROWS_BUNDLE_BUILD_BLOCKED_NONDETERMINISTIC_ORDERING" in (
        _blocked_reasons_for_source_files(source_files)
    )


def test_forbidden_bundle_hash_freeze_final_readiness_and_runtime_boundaries_fail_closed():
    forbidden_paths = [
        validator.CANONICAL_BUNDLE_JSONL,
        validator.CANONICAL_BUNDLE_SHA256,
        Path("docs")
        / "master_plan"
        / "atomic_rows"
        / "AtomicRowsBundleFreezeAuthority.yaml",
        Path("docs")
        / "master_plan"
        / "generated"
        / "AtomicRowsFullBundleFinalReadinessGate.report.json",
    ]
    for path in forbidden_paths:
        failures = validator.validate_no_forbidden_artifacts(
            ROOT,
            extra_existing_paths=(path,),
        )
        _assert_failure_contains(failures, path.as_posix())

    report = _report()
    assert report["forbidden_artifact_boundary"]["runtime_live_order_source_connector_profit_quantum_backend_effect_created_flag"] is False
    for effect in [
        "EXTERNAL_SOURCE_RETRIEVAL",
        "SOURCE_ACCEPTANCE",
        "ACCEPTED_SOURCE_PACKETS",
        "CONNECTOR_SEMANTIC_BINDING",
        "PRIVATE_STATE_FETCH",
        "RUNTIME_CASH_RECEIPT",
        "REPLAY_PAPER_EXECUTION",
        "OPTIMIZER_EXECUTION",
        "ORDER_SUBMISSION_CANCELLATION_REDUCTION_OR_CLOSE",
        "PROFIT_EVIDENCE",
        "LATENCY_EVIDENCE",
    ]:
        assert effect in report["blocked_effects"]


def test_quantum_metadata_is_validated_as_static_non_executable_metadata_only():
    report = _report()
    quantum = report["quantum_metadata_validation"]

    for ref in validator.pr98_gate.QUANTUM_METADATA_REFS:
        assert ref in quantum["required_static_metadata_refs"]
    for effect in validator.pr97_gate.FORBIDDEN_QUANTUM_EFFECTS:
        assert effect in quantum["forbidden_quantum_execution_effects"]
    assert quantum["static_metadata_only_flag"] is True
    assert quantum["quantum_execution_fields_true_flag"] is False
    assert quantum["quantum_advantage_claim_created_flag"] is False
    assert "QAOA_EXECUTION" in quantum["forbidden_quantum_execution_effects"]
    assert "VQE_EXECUTION" in quantum["forbidden_quantum_execution_effects"]
    assert "ANNEALING_EXECUTION" in quantum["forbidden_quantum_execution_effects"]
    assert "QUBO_SOLVING" in quantum["forbidden_quantum_execution_effects"]
    assert "ISING_SOLVING" in quantum["forbidden_quantum_execution_effects"]
    assert "QUANTUM_PROVIDER_CALL" in quantum["forbidden_quantum_execution_effects"]


def test_fixture_cases_cover_required_fail_closed_contracts():
    fixture = _fixture()

    assert [case["case_id"] for case in fixture["fixture_cases"]] == list(
        validator.REQUIRED_FIXTURE_CASE_IDS
    )
    assert validator.validate_fixture_payload(fixture) == []
