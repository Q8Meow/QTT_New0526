from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_full_bundle_row_expansion_plan as validator


ROOT = Path(".")
PR98_BRANCH = "pr98-atomicrows-bundle-row-family-source-files"
PR99_BRANCH = "pr99-atomicrows-bundle-builder-deterministic-assembly-gate"
FEATURE_BRANCH = "feature/non-downstream-validation"
_REPORT_CACHE: dict | None = None


def _clear_branch_context_env(monkeypatch) -> None:
    for env_name in ("GITHUB_ACTIONS", *validator.BRANCH_CONTEXT_ENV_CANDIDATES):
        monkeypatch.delenv(env_name, raising=False)


def _mock_git_branch(monkeypatch, branch: str, *, detached: bool = False) -> None:
    original_git_stdout = validator._git_stdout

    def fake_git_stdout(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, "" if detached else branch, ""
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, "HEAD" if detached else branch, ""
        return original_git_stdout(repo_root, args)

    monkeypatch.setattr(validator, "_git_stdout", fake_git_stdout)


def _write_file(root: Path, relative_path: Path, content: str = "{}\n") -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _schema() -> dict:
    return validator.load_json(ROOT / validator.DEFAULT_SCHEMA)


def _plan() -> dict:
    return validator.load_yaml(ROOT / validator.DEFAULT_PRODUCTION_PLAN)


def _fixture() -> dict:
    return validator.load_json(ROOT / validator.DEFAULT_FIXTURE)


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert validator.main([]) == 0
        _REPORT_CACHE = json.loads((ROOT / validator.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_production_plan_validates_and_report_is_deterministic(capsys):
    first = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_plan_path=validator.DEFAULT_PRODUCTION_PLAN,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    second = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_plan_path=validator.DEFAULT_PRODUCTION_PLAN,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    report_text = (ROOT / validator.DEFAULT_REPORT).read_text(encoding="utf-8")
    report_json = json.loads(report_text)
    branch_context = validator._current_branch_context(ROOT)
    default_report_write_skipped = validator._should_skip_default_report_write(
        repo_root=ROOT.resolve(),
        output_abs=(ROOT / validator.DEFAULT_REPORT).resolve(),
        metadata={"branch": branch_context.branch},
    )

    assert first.failures == second.failures == ()
    assert first.report == second.report
    if not default_report_write_skipped:
        assert first.report == report_json
    assert report_text == json.dumps(json.loads(report_text), indent=2, sort_keys=True) + "\n"
    assert report_json["validation_marker"] == validator.SUCCESS_MARKER
    assert validator.main([]) == 0
    output_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    allowed_info_lines = {
        validator.CI_DETACHED_HEAD_MODE_MARKER,
        validator.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER,
        validator.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER,
    }
    assert output_lines
    assert output_lines[0] == validator.SUCCESS_MARKER
    assert set(output_lines[1:]) <= allowed_info_lines


def test_required_plan_concepts_and_target_total_are_traceable_static_only():
    plan = _plan()
    report = _report()

    assert plan["required_plan_concepts"] == list(validator.REQUIRED_PLAN_CONCEPTS)
    assert validator.validate_required_plan_concepts(plan) == []
    assert plan["target_total_row_count"] == 4183
    assert plan["target_total_row_count_authority"] == validator.TARGET_TOTAL_ROW_COUNT_AUTHORITY
    assert plan["target_total_row_count_created_by_pr97_flag"] is False
    assert validator.validate_master_plan_target_count_authority(ROOT) == []
    assert report["target_total_row_count"] == 4183
    assert report["target_total_row_count_created_by_pr97_flag"] is False


def test_row_family_split_plan_is_deterministic_intent_only_and_has_no_exact_counts():
    plan = _plan()
    families = validator._row_families(plan)
    branch_context = validator._current_branch_context(ROOT)
    downstream_pr98_or_later = validator._downstream_or_main_validation_branch_allowed(
        branch_context.branch
    )

    assert [family["row_family_id"] for family in families] == list(validator.ROW_FAMILY_IDS)
    assert [family["row_family_class"] for family in families] == list(validator.ROW_FAMILY_CLASSES)
    assert [family["canonical_order"] for family in families] == list(range(1, len(families) + 1))
    for family in families:
        assert family["source_file_created_by_pr97_flag"] is False
        assert family["row_records_created_by_pr97_flag"] is False
        assert family["exact_row_count_created_by_pr97_flag"] is False
        assert family["planned_count_policy"] == "OWNER_REVIEW_REQUIRED"
        assert family["planned_count_authority"] == "FUTURE_PR98_OR_OWNER_APPROVED_SOURCE"
        assert "exact_row_count" not in family
        assert "planned_row_count" not in family
        assert family["planned_downstream_source_file_path"].startswith(
            "docs/master_plan/atomic_rows/pr98_row_family_sources/"
        )
        if not downstream_pr98_or_later:
            assert not (ROOT / family["planned_downstream_source_file_path"]).exists()


def test_generation_sequence_separates_pr98_pr99_pr100_and_pr101():
    plan = _plan()
    stages = plan["generation_sequence_plan"]["downstream_stages"]

    assert [(stage["roadmap_pr_label"], stage["downstream_pr_stage"]) for stage in stages] == list(
        validator.GENERATION_SEQUENCE
    )
    for stage in stages:
        assert stage["creates_artifact_by_pr97_flag"] is False
        assert stage["owner_approval_required_before_stage_flag"] is True
    assert plan["downstream_pr_handoff_plan"] == {
        "pr98_handoff_intent_only": True,
        "pr99_handoff_intent_only": True,
        "pr100_handoff_intent_only": True,
        "pr101_handoff_intent_only": True,
        "runtime_live_handoff_created_flag": False,
    }


def test_validation_matrix_covers_required_classes_and_blocks_runtime_use():
    plan = _plan()
    validations = validator._validations(plan)

    assert [entry["validation_class"] for entry in validations] == list(validator.VALIDATION_CLASSES)
    assert [entry["canonical_order"] for entry in validations] == list(range(1, len(validations) + 1))
    assert len({entry["validation_id"] for entry in validations}) == len(validations)
    for entry in validations:
        assert entry["fail_closed_reason_code"]
        assert entry["blocks_live_or_runtime_use_flag"] is True


def test_owner_approval_sequence_preserves_owner_authority_without_fabrication():
    approval = _plan()["owner_approval_sequence_plan"]

    assert approval["owner_final_authority_flag"] is True
    assert approval["owner_review_required_before_pr98_source_creation"] is True
    assert approval["owner_review_required_before_pr99_builder_execution"] is True
    assert approval["owner_review_required_before_pr100_sha_freeze"] is True
    assert approval["owner_review_required_before_pr101_final_readiness_claim"] is True
    assert approval["owner_override_satisfies_internal_workflow_only_flag"] is True
    for blocked in [
        "ROW_RECORDS",
        "SOURCE_FACTS",
        "ACCEPTED_SOURCE_PACKETS",
        "CONNECTOR_SEMANTICS",
        "RUNTIME_CASH_RECEIPTS",
        "ORDER_OR_FILL_RECEIPTS",
        "REPLAY_OR_PAPER_RESULTS",
        "BUNDLE_HASH",
        "PROFIT_EVIDENCE",
        "LATENCY_EVIDENCE",
        "QUANTUM_ADVANTAGE_EVIDENCE",
    ]:
        assert blocked in approval["owner_override_cannot_fabricate"]


def test_quantum_forward_planning_is_metadata_only_and_non_executable():
    plan = _plan()
    quantum = plan["quantum_forward_row_family_plan"]

    assert quantum["metadata_only_flag"] is True
    assert quantum["quantum_execution_created_flag"] is False
    assert quantum["quantum_advantage_evidence_created_flag"] is False
    assert quantum["quantum_metadata_planning_entries"] == list(validator.QUANTUM_METADATA_ENTRIES)
    for effect in validator.FORBIDDEN_QUANTUM_EFFECTS:
        assert effect in quantum["forbidden_quantum_execution_effects"]
    for forbidden_text in [
        "QAOA_EXECUTION",
        "VQE_EXECUTION",
        "ANNEALING_EXECUTION",
        "QUBO_SOLVING",
        "ISING_SOLVING",
        "QUANTUM_SIMULATOR_EXECUTION",
        "QUANTUM_PROVIDER_CALL",
        "QUANTUM_DIRECT_ORDER_AUTHORITY",
    ]:
        assert forbidden_text in quantum["forbidden_quantum_execution_effects"]


def test_forbidden_artifact_runtime_live_order_source_connector_profit_boundaries():
    plan = _plan()
    boundary = plan["forbidden_artifact_boundary_plan"]
    report = _report()

    assert boundary["all_blocked_effects_active_in_pr97_flag"] is True
    assert validator.CANONICAL_BUNDLE_JSONL.as_posix() in boundary["blocked_artifacts"]
    assert validator.CANONICAL_BUNDLE_SHA256.as_posix() in boundary["blocked_artifacts"]
    assert "PR98_ROW_FAMILY_SOURCE_FILES" in boundary["blocked_artifacts"]
    assert "PR99_BUNDLE_BUILDER" in boundary["blocked_artifacts"]
    assert "PR100_SHA_FREEZE_AUTHORITY" in boundary["blocked_artifacts"]
    assert "PR101_FINAL_READINESS_GATE" in boundary["blocked_artifacts"]
    for runtime_effect in [
        "SOURCE_RETRIEVAL",
        "SOURCE_ACCEPTANCE",
        "ACCEPTED_SOURCE_PACKETS",
        "CONNECTOR_SEMANTIC_BINDING",
        "PRIVATE_STATE_FETCH",
        "RUNTIME_CASH_RECEIPT",
        "REPLAY_EXECUTION",
        "PAPER_EXECUTION",
        "OPTIMIZER_EXECUTION",
        "QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION",
        "LIVE_ROUTING",
        "ORDER_SUBMISSION_CANCELLATION_REDUCTION_OR_CLOSE",
    ]:
        assert runtime_effect in boundary["blocked_runtime_effects"]
    for field in validator.FALSE_FIELDS:
        assert plan[field] is False
        assert report[field] is False


def test_fixture_cases_cover_required_negative_boundaries():
    fixture = _fixture()

    assert [case["case_id"] for case in fixture["fixture_cases"]] == list(
        validator.REQUIRED_FIXTURE_CASE_IDS
    )
    assert validator.validate_fixture_cases(_fixture(), _plan(), _schema(), ROOT) == []
    assert fixture["future_pr_handoff_notes"]["pr98"].startswith("source file paths are intent only")
    assert fixture["positive_plan_static_only_flags"]["bundle_file_created_flag"] is False


def test_missing_required_concept_duplicate_ids_unstable_order_and_exact_counts_fail_closed():
    plan = _plan()
    schema = _schema()

    missing = copy.deepcopy(plan)
    missing["required_plan_concepts"].remove("ATOMICROWS_QUANTUM_FORWARD_ROW_FAMILY_PLAN")
    _assert_failure_contains(
        validator.validate_plan_payload(missing, schema, ROOT),
        "required_plan_concepts",
    )

    duplicate_family = copy.deepcopy(plan)
    duplicate_family["row_family_split_plan"]["row_families"].append(
        copy.deepcopy(duplicate_family["row_family_split_plan"]["row_families"][0])
    )
    _assert_failure_contains(
        validator.validate_plan_payload(duplicate_family, schema, ROOT),
        "duplicate row_family_id",
    )

    duplicate_validation = copy.deepcopy(plan)
    duplicate_validation["validation_matrix_plan"]["validations"].append(
        copy.deepcopy(duplicate_validation["validation_matrix_plan"]["validations"][0])
    )
    _assert_failure_contains(
        validator.validate_plan_payload(duplicate_validation, schema, ROOT),
        "duplicate validation_id",
    )

    unstable = copy.deepcopy(plan)
    families = unstable["row_family_split_plan"]["row_families"]
    families[0], families[1] = families[1], families[0]
    _assert_failure_contains(
        validator.validate_plan_payload(unstable, schema, ROOT),
        "row_family_id values must match canonical PR97 order",
    )

    exact_count = copy.deepcopy(plan)
    exact_count["row_family_split_plan"]["row_families"][0]["exact_row_count"] = 7
    _assert_failure_contains(
        validator.validate_plan_payload(exact_count, schema, ROOT),
        "exact_row_count",
    )


def test_unknown_row_family_class_unknown_validation_class_and_bad_downstream_stage_fail_closed():
    plan = _plan()
    schema = _schema()

    bad_family = copy.deepcopy(plan)
    bad_family["row_family_split_plan"]["row_families"][0]["row_family_class"] = "UNKNOWN"
    _assert_failure_contains(
        validator.validate_plan_payload(bad_family, schema, ROOT),
        "row_family_class",
    )

    bad_validation = copy.deepcopy(plan)
    bad_validation["validation_matrix_plan"]["validations"][0]["validation_class"] = "UNKNOWN"
    _assert_failure_contains(
        validator.validate_plan_payload(bad_validation, schema, ROOT),
        "validation_class",
    )

    bad_stage = copy.deepcopy(plan)
    bad_stage["generation_sequence_plan"]["downstream_stages"][0]["downstream_pr_stage"] = "UNKNOWN"
    _assert_failure_contains(
        validator.validate_plan_payload(bad_stage, schema, ROOT),
        "downstream_pr_stage",
    )


def test_bundle_hash_source_builder_freeze_and_final_readiness_flags_fail_closed():
    plan = _plan()
    schema = _schema()
    fields = [
        "bundle_file_created_flag",
        "bundle_sha_created_flag",
        "row_family_source_files_created_flag",
        "row_records_created_flag",
        "bundle_builder_created_flag",
        "bundle_builder_executed_flag",
        "sha_authority_created_flag",
        "freeze_authority_created_flag",
        "final_readiness_created_flag",
    ]
    for field in fields:
        mutated = copy.deepcopy(plan)
        mutated[field] = True
        _assert_failure_contains(
            validator.validate_plan_payload(mutated, schema, ROOT),
            field,
        )


def test_runtime_live_order_source_connector_profit_latency_and_quantum_flags_fail_closed():
    plan = _plan()
    schema = _schema()
    for field in [
        "creates_runtime_live_authority_flag",
        "creates_order_authority_flag",
        "creates_source_fact_flag",
        "creates_connector_semantic_flag",
        "creates_runtime_cash_receipt_flag",
        "creates_replay_paper_result_flag",
        "creates_optimizer_execution_flag",
        "creates_quantum_backend_execution_flag",
        "creates_profit_evidence_flag",
        "creates_latency_evidence_flag",
        "creates_quantum_advantage_evidence_flag",
    ]:
        mutated = copy.deepcopy(plan)
        mutated[field] = True
        _assert_failure_contains(
            validator.validate_plan_payload(mutated, schema, ROOT),
            field,
        )


def test_planned_source_files_bundle_sha_builder_and_final_readiness_files_absent(
    tmp_path,
    monkeypatch,
):
    plan = _plan()

    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, PR99_BRANCH)
    assert validator.validate_no_forbidden_artifacts(ROOT, plan) == []
    bundle_path = tmp_path / validator.CANONICAL_BUNDLE_JSONL
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("{}\n", encoding="utf-8")
    _assert_failure_contains(
        validator.validate_no_forbidden_artifacts(tmp_path, plan),
        validator.CANONICAL_BUNDLE_JSONL.as_posix(),
    )

    bundle_path.unlink()
    sha_path = tmp_path / validator.CANONICAL_BUNDLE_SHA256
    sha_path.write_text("abc\n", encoding="utf-8")
    _assert_failure_contains(
        validator.validate_no_forbidden_artifacts(tmp_path, plan),
        validator.CANONICAL_BUNDLE_SHA256.as_posix(),
    )

    sha_path.unlink()
    _mock_git_branch(monkeypatch, validator.TARGET_BRANCH)
    planned_source = Path(
        plan["row_family_split_plan"]["row_families"][0][
            "planned_downstream_source_file_path"
        ]
    )
    _write_file(tmp_path, planned_source)
    _assert_failure_contains(
        validator.validate_no_forbidden_artifacts(tmp_path, plan),
        "PR98 row-family source file exists during PR97",
    )


def test_pr98_row_family_source_files_allowed_on_local_pr98_downstream_branch(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, PR98_BRANCH)
    for path in validator.planned_pr98_source_paths(plan):
        _write_file(tmp_path, path)

    assert validator.validate_no_forbidden_artifacts(tmp_path, plan) == []


def test_pr98_row_family_source_files_allowed_on_main_cumulative_context(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, "main")
    for path in validator.planned_pr98_source_paths(plan):
        _write_file(tmp_path, path)

    assert validator.validate_no_forbidden_artifacts(tmp_path, plan) == []


def test_pr98_row_family_source_files_allowed_in_github_push_main_context(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    _mock_git_branch(monkeypatch, "ignored", detached=True)
    for path in validator.planned_pr98_source_paths(plan):
        _write_file(tmp_path, path)

    assert validator.validate_no_forbidden_artifacts(tmp_path, plan) == []


def test_pr98_row_family_source_files_allowed_in_github_actions_detached_head_context(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", PR98_BRANCH)
    monkeypatch.setenv("GITHUB_REF_NAME", "98/merge")
    _mock_git_branch(monkeypatch, PR98_BRANCH, detached=True)
    for path in validator.planned_pr98_source_paths(plan):
        _write_file(tmp_path, path)

    assert validator.validate_no_forbidden_artifacts(tmp_path, plan) == []


def test_pr98_row_family_source_files_blocked_on_non_downstream_branch(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, FEATURE_BRANCH)
    for path in validator.planned_pr98_source_paths(plan):
        _write_file(tmp_path, path)

    failures = validator.validate_no_forbidden_artifacts(tmp_path, plan)

    for path in validator.planned_pr98_source_paths(plan):
        _assert_failure_contains(
            failures,
            f"PR98 row-family source file exists during PR97: {path.as_posix()}",
        )


def test_pr98_row_family_source_files_blocked_on_pr97_same_pr_branch(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, validator.TARGET_BRANCH)
    for path in validator.planned_pr98_source_paths(plan):
        _write_file(tmp_path, path)

    failures = validator.validate_no_forbidden_artifacts(tmp_path, plan)

    for path in validator.planned_pr98_source_paths(plan):
        _assert_failure_contains(
            failures,
            f"PR98 row-family source file exists during PR97: {path.as_posix()}",
        )


def test_bundle_hash_builder_freeze_and_final_readiness_remain_blocked_on_pr98_branch(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, PR98_BRANCH)
    for path in validator.planned_pr98_source_paths(plan):
        _write_file(tmp_path, path)
    for path in validator.ALWAYS_FORBIDDEN_ARTIFACT_PATHS:
        _write_file(tmp_path, path)

    failures = validator.validate_no_forbidden_artifacts(tmp_path, plan)

    for path in validator.ALWAYS_FORBIDDEN_ARTIFACT_PATHS:
        if path in {validator.CANONICAL_BUNDLE_JSONL, validator.CANONICAL_BUNDLE_SHA256}:
            _assert_failure_contains(failures, "expected_state=PRE_MATERIALIZATION")
            _assert_failure_contains(failures, path.as_posix())
        else:
            _assert_failure_contains(
                failures,
                f"forbidden downstream artifact exists: {path.as_posix()}",
            )
    for path in validator.planned_pr98_source_paths(plan):
        assert not any(path.as_posix() in failure for failure in failures)


def test_bundle_hash_freeze_final_readiness_remain_blocked_on_main_context(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, "main")
    for path in validator.planned_pr98_source_paths(plan):
        _write_file(tmp_path, path)
    for path in validator.ALWAYS_FORBIDDEN_ARTIFACT_PATHS:
        _write_file(tmp_path, path)

    failures = validator.validate_no_forbidden_artifacts(tmp_path, plan)

    for path in validator.ALWAYS_FORBIDDEN_ARTIFACT_PATHS:
        if path in {validator.CANONICAL_BUNDLE_JSONL, validator.CANONICAL_BUNDLE_SHA256}:
            _assert_failure_contains(failures, "expected_state=PRE_MATERIALIZATION")
            _assert_failure_contains(failures, path.as_posix())
        else:
            _assert_failure_contains(
                failures,
                f"forbidden downstream artifact exists: {path.as_posix()}",
            )
    for path in validator.planned_pr98_source_paths(plan):
        assert not any(path.as_posix() in failure for failure in failures)


def test_pr99_static_bundle_builder_allowed_only_on_pr99_or_later_branch(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    builder_path = validator.PR99_STATIC_BUILDER_ARTIFACT_PATHS[0]
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, PR98_BRANCH)
    _write_file(tmp_path, builder_path)

    failures = validator.validate_no_forbidden_artifacts(tmp_path, plan)

    _assert_failure_contains(
        failures,
        f"forbidden downstream artifact exists: {builder_path.as_posix()}",
    )

    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, PR99_BRANCH)

    assert validator.validate_no_forbidden_artifacts(tmp_path, plan) == []


def test_pr99_static_bundle_builder_allowed_on_main_cumulative_context(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    builder_path = validator.PR99_STATIC_BUILDER_ARTIFACT_PATHS[0]
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, "main")
    _write_file(tmp_path, builder_path)

    assert validator.validate_no_forbidden_artifacts(tmp_path, plan) == []


def test_pr99_static_bundle_builder_allowed_in_github_actions_detached_head_context(
    tmp_path,
    monkeypatch,
):
    plan = _plan()
    builder_path = validator.PR99_STATIC_BUILDER_ARTIFACT_PATHS[0]
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", PR99_BRANCH)
    monkeypatch.setenv("GITHUB_REF_NAME", "99/merge")
    _mock_git_branch(monkeypatch, PR99_BRANCH, detached=True)
    _write_file(tmp_path, builder_path)

    assert validator.validate_no_forbidden_artifacts(tmp_path, plan) == []


def test_report_does_not_claim_bundle_live_profit_latency_or_quantum_advantage_readiness():
    report = _report()

    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert report["pr98_row_family_source_files_created"] is False
    assert report["pr99_bundle_builder_created"] is False
    assert report["pr100_sha_freeze_authority_created"] is False
    assert report["pr101_final_readiness_created"] is False
    assert report["runtime_live_order_source_connector_profit_quantum_backend_effect_created"] is False
    assert "creates no bundle hash freeze row records" in report["remaining_boundary"]


def test_validator_surface_does_not_import_hashlib_or_quantum_runtime_execution_modules():
    text = (ROOT / "tools" / "validate_atomicrows_full_bundle_row_expansion_plan.py").read_text(
        encoding="utf-8"
    )

    assert "import hashlib" not in text
    assert "qiskit" not in text.lower()
    assert "dwave" not in text.lower()
    assert "cirq" not in text.lower()
    assert "pennylane" not in text.lower()
    assert "requests" not in text
