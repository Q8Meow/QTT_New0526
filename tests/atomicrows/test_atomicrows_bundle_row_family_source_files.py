from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools import validate_atomicrows_bundle_row_family_source_files as validator


ROOT = Path(".")
_REPORT_CACHE: dict | None = None


def _schema() -> dict:
    return validator.load_json(ROOT / validator.DEFAULT_SCHEMA)


def _source_file_set() -> dict:
    return validator.load_yaml(ROOT / validator.DEFAULT_SOURCE_FILE_SET)


def _fixture() -> dict:
    return validator.load_json(ROOT / validator.DEFAULT_FIXTURE)


def _pr97_plan() -> dict:
    return validator.load_yaml(ROOT / validator.PR97_PLAN_PATH)


def _source_files() -> dict[str, dict]:
    source_files, failures = validator.load_source_files(ROOT, _pr97_plan())
    assert failures == []
    return source_files


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert validator.main([]) == 0
        _REPORT_CACHE = json.loads((ROOT / validator.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _validate_source_files(source_files: dict[str, dict]) -> list[str]:
    return validator.validate_source_file_payloads(source_files, _schema(), _pr97_plan())


def _first_two_paths() -> tuple[str, str]:
    paths = [path.as_posix() for path in validator._source_file_paths_from_pr97(_pr97_plan())]
    return paths[0], paths[1]


def _first_blueprint(source_file: dict) -> dict:
    blueprints = validator._list_of_mappings(source_file.get("source_records_or_blueprints"))
    assert blueprints
    return blueprints[0]


def test_production_source_file_set_validates_and_report_is_deterministic(capsys):
    first = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        source_file_set_path=validator.DEFAULT_SOURCE_FILE_SET,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    second = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        source_file_set_path=validator.DEFAULT_SOURCE_FILE_SET,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    report_text = (ROOT / validator.DEFAULT_REPORT).read_text(encoding="utf-8")

    assert first.failures == second.failures == ()
    assert first.report == second.report == json.loads(report_text)
    assert report_text == json.dumps(json.loads(report_text), indent=2, sort_keys=True) + "\n"
    assert json.loads(report_text)["validation_marker"] == validator.SUCCESS_MARKER
    assert validator.main([]) == 0
    output_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    allowed = {
        validator.SUCCESS_MARKER,
        validator.CI_DETACHED_HEAD_MODE_MARKER,
        validator.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER,
        validator.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER,
    }
    assert output_lines
    assert output_lines[-1] in allowed
    assert validator.SUCCESS_MARKER in output_lines


def test_required_concepts_manifest_validation_owner_and_quantum_sections_exist():
    source_file_set = _source_file_set()
    fixture = _fixture()
    report = _report()

    assert source_file_set["required_source_file_concepts"] == list(
        validator.REQUIRED_SOURCE_FILE_CONCEPTS
    )
    assert report["required_source_file_concepts"] == list(
        validator.REQUIRED_SOURCE_FILE_CONCEPTS
    )
    assert source_file_set["source_file_set_id"] == "ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILE_SET"
    assert source_file_set["row_family_source_manifest"]["manifest_id"] == (
        "ATOMICROWS_ROW_FAMILY_SOURCE_MANIFEST"
    )
    assert source_file_set["validation_matrix"]["matrix_id"] == (
        "ATOMICROWS_ROW_FAMILY_SOURCE_VALIDATION_MATRIX"
    )
    assert source_file_set["owner_approval_boundary"]["boundary_id"] == (
        "ATOMICROWS_ROW_FAMILY_SOURCE_OWNER_APPROVAL_BOUNDARY"
    )
    assert source_file_set["quantum_metadata_source_plan"]["plan_id"] == (
        "ATOMICROWS_ROW_FAMILY_QUANTUM_METADATA_SOURCE_PLAN"
    )
    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"


def test_pr97_consumption_path_alignment_and_planning_only_counts():
    source_file_set = _source_file_set()
    pr97_plan = _pr97_plan()
    source_files = _source_files()
    families = validator._row_families(pr97_plan)
    manifest_entries = validator._manifest_entries(source_file_set)

    assert source_file_set["consumes_pr97_expansion_plan_flag"] is True
    assert source_file_set["target_total_row_count"] == 4183
    assert source_file_set["target_total_row_count_planning_authority_only_flag"] is True
    assert len(source_files) == len(families) == len(manifest_entries) == 15
    assert set(source_files) == {
        path.as_posix() for path in validator._source_file_paths_from_pr97(pr97_plan)
    }
    for family, manifest in zip(families, manifest_entries):
        planned_path = family["planned_downstream_source_file_path"]
        source_file = source_files[planned_path]
        assert manifest["planned_downstream_source_file_path"] == planned_path
        assert manifest["actual_created_source_file_path"] == planned_path
        assert source_file["source_file_path"] == planned_path
        assert source_file["row_family_id"] == family["row_family_id"]
        assert source_file["row_family_class"] == family["row_family_class"]
        assert source_file["planned_count_policy"] == family["planned_count_policy"]
        assert source_file["planned_count_authority"] == family["planned_count_authority"]
        assert manifest["exact_row_count_authority"] == (
            "EXACT_PER_FAMILY_COUNTS_NOT_AUTHORIZED_BY_PR97"
        )
        assert source_file["exact_row_count_created_by_pr98_flag"] is False
        assert source_file["declared_source_record_count"] == 0
        assert "exact_row_count" not in source_file
        assert "planned_row_count" not in source_file


def test_source_files_are_deterministic_blueprints_not_final_rows():
    source_files = _source_files()
    ordered = [source_files[path.as_posix()] for path in validator._source_file_paths_from_pr97(_pr97_plan())]
    source_file_ids = [source_file["source_file_id"] for source_file in ordered]
    row_family_ids = [source_file["row_family_id"] for source_file in ordered]
    blueprint_ids = [
        _first_blueprint(source_file)["blueprint_id"] for source_file in ordered
    ]

    assert [source_file["canonical_order"] for source_file in ordered] == list(range(1, 16))
    assert len(source_file_ids) == len(set(source_file_ids))
    assert len(row_family_ids) == len(set(row_family_ids))
    assert len(blueprint_ids) == len(set(blueprint_ids))
    for source_file in ordered:
        assert source_file["source_file_mode"] == "SOURCE_REQUIRED"
        assert source_file["source_file_created_by_pr98_flag"] is True
        assert source_file["final_bundle_row_file_flag"] is False
        assert source_file["final_bundle_row_flag"] is False
        assert source_file["bundle_hash_authority_flag"] is False
        assert source_file["runtime_live_authority_flag"] is False
        assert source_file["builder_input_candidate_flag"] is True
        assert source_file["builder_execution_allowed_by_pr98_flag"] is False
        blueprint = _first_blueprint(source_file)
        assert blueprint["record_type"] == "ATOMICROWS_ROW_SOURCE_RECORD_OR_BLUEPRINT"
        assert blueprint["record_class"] == "SOURCE_ROW_BLUEPRINT_NOT_EXACT_FINAL_ROW"
        assert blueprint["canonical_order"] == 1
        assert "row_source_id" not in blueprint
        assert blueprint["exact_row_created_flag"] is False
        assert blueprint["exact_final_row_created_flag"] is False
        assert blueprint["final_bundle_membership_created_flag"] is False
        assert blueprint["owner_review_required_before_row_materialization"] is True
        assert blueprint["no_final_bundle_authority_flag"] is True


def test_repository_source_file_boundary_does_not_create_source_acceptance_or_connector_binding():
    source_file_set = _source_file_set()

    assert source_file_set["repository_source_files_only_flag"] is True
    assert source_file_set["external_source_retrieval_flag"] is False
    assert source_file_set["external_source_retrieval_created_flag"] is False
    assert source_file_set["source_acceptance_flag"] is False
    assert source_file_set["source_acceptance_created_flag"] is False
    assert source_file_set["connector_semantic_created_flag"] is False
    for source_file in _source_files().values():
        assert source_file["source_file_mode"] == "SOURCE_REQUIRED"
        assert source_file["repository_source_file_only_flag"] is True
        assert source_file["external_source_retrieval_created_flag"] is False
        assert source_file["source_acceptance_created_flag"] is False
        blueprint = _first_blueprint(source_file)
        assert blueprint["source_evidence_created_flag"] is False
        assert blueprint["connector_semantic_created_flag"] is False


def test_bundle_hash_builder_freeze_and_final_readiness_boundaries_are_absent():
    report = _report()

    assert validator.validate_no_forbidden_artifacts(ROOT) == []
    assert not (ROOT / validator.CANONICAL_BUNDLE_JSONL).exists()
    assert not (ROOT / validator.CANONICAL_BUNDLE_SHA256).exists()
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert report["pr99_bundle_builder_created"] is False
    assert report["pr100_sha_freeze_authority_created"] is False
    assert report["pr101_final_readiness_created"] is False
    for field in validator.FALSE_AUTHORITY_FIELDS:
        assert report[field] is False


def test_pr99_pr100_pr101_runtime_profit_latency_and_order_separation():
    report = _report()
    boundary = report["remaining_boundary"].lower()

    assert "no bundle" in boundary
    assert "hash" in boundary
    assert "final readiness" in boundary
    assert "runtime" in boundary
    assert "live trading" in boundary
    assert "profit" in boundary
    assert "latency" in boundary
    assert "quantum advantage" in boundary
    assert report["runtime_live_order_source_connector_profit_quantum_backend_effect_created"] is False
    for source_file in _source_files().values():
        blueprint = _first_blueprint(source_file)
        assert blueprint["runtime_live_order_authority_created_flag"] is False
        assert blueprint["profit_evidence_created_flag"] is False


def test_quantum_forward_metadata_is_static_and_non_executable():
    source_files = _source_files()
    quantum_refs_by_family = {
        source_file["row_family_id"]: set(_first_blueprint(source_file)["quantum_metadata_refs"])
        for source_file in source_files.values()
        if source_file["quantum_relevance_class"] != "NOT_QUANTUM_SPECIFIC_STATIC_METADATA"
    }

    assert quantum_refs_by_family["AR_FAMILY_012_QUANTUM_ADVISORY_OPTIMIZATION"] == {
        "QUANTUM_ADVISORY_ROW_FAMILIES",
        "QUANTUM_APPLICABILITY_METADATA",
        "OWNER_QUANTUM_PRIORITY_POLICY_REFERENCE",
    }
    assert quantum_refs_by_family["AR_FAMILY_013_QUANTUM_QUBO_ISING_METADATA"] == {
        "QUBO_COMPATIBLE_METADATA",
        "ISING_COMPATIBLE_METADATA",
    }
    assert quantum_refs_by_family["AR_FAMILY_014_QUANTUM_QAOA_VQE_ANNEALING_METADATA"] == {
        "QAOA_COMPATIBLE_METADATA",
        "VQE_COMPATIBLE_METADATA",
        "ANNEALING_COMPATIBLE_METADATA",
    }
    assert quantum_refs_by_family["AR_FAMILY_015_QUANTUM_PORTFOLIO_HYBRID_COMPARATOR"] == {
        "QUANTUM_PORTFOLIO_OPTIMIZATION_METADATA",
        "HYBRID_CLASSICAL_QUANTUM_COMPARISON_METADATA",
        "OWNER_QUANTUM_PRIORITY_POLICY_REFERENCE",
    }
    for source_file in source_files.values():
        blueprint = _first_blueprint(source_file)
        assert blueprint["quantum_backend_execution_created_flag"] is False
    assert _report()["quantum_backend_execution_created_flag"] is False
    assert _report()["quantum_advantage_evidence_created_flag"] is False
    assert validator.validate_validator_static_surface(
        ROOT / "tools" / "validate_atomicrows_bundle_row_family_source_files.py"
    ) == []


def test_fixture_cases_cover_required_fail_closed_contracts():
    fixture = _fixture()

    assert [case["case_id"] for case in fixture["fixture_cases"]] == list(
        validator.REQUIRED_FIXTURE_CASE_IDS
    )
    assert validator.validate_fixture_cases(
        fixture,
        _source_file_set(),
        _source_files(),
        _schema(),
        _pr97_plan(),
        ROOT,
    ) == []


def test_missing_required_source_file_fails_closed():
    source_files = copy.deepcopy(_source_files())
    source_files.pop(_first_two_paths()[0])

    _assert_failure_contains(_validate_source_files(source_files), "missing required source files")


def test_unknown_row_family_relative_to_pr97_fails_closed():
    source_files = copy.deepcopy(_source_files())
    first_path, _second_path = _first_two_paths()
    source_files[first_path]["row_family_id"] = "AR_FAMILY_UNKNOWN"

    _assert_failure_contains(_validate_source_files(source_files), "row_family_id must be")


def test_duplicate_source_file_id_fails_closed():
    source_files = copy.deepcopy(_source_files())
    first_path, second_path = _first_two_paths()
    source_files[second_path]["source_file_id"] = source_files[first_path]["source_file_id"]

    _assert_failure_contains(_validate_source_files(source_files), "duplicate source_file_id")


def test_duplicate_row_family_ownership_fails_closed():
    source_files = copy.deepcopy(_source_files())
    first_path, second_path = _first_two_paths()
    source_files[second_path]["row_family_id"] = source_files[first_path]["row_family_id"]

    _assert_failure_contains(_validate_source_files(source_files), "duplicate row_family_id ownership")


def test_duplicate_blueprint_id_fails_closed():
    source_files = copy.deepcopy(_source_files())
    first_path, second_path = _first_two_paths()
    _first_blueprint(source_files[second_path])["blueprint_id"] = _first_blueprint(
        source_files[first_path]
    )["blueprint_id"]

    _assert_failure_contains(_validate_source_files(source_files), "duplicate blueprint_id")


def test_unstable_source_file_and_blueprint_order_fail_closed():
    source_files = copy.deepcopy(_source_files())
    first_path, _second_path = _first_two_paths()
    source_files[first_path]["canonical_order"] = 99

    _assert_failure_contains(_validate_source_files(source_files), "canonical_order")

    source_files = copy.deepcopy(_source_files())
    _first_blueprint(source_files[first_path])["canonical_order"] = 99

    _assert_failure_contains(_validate_source_files(source_files), "blueprint canonical_order")


def test_fabricated_exact_counts_fail_closed():
    source_files = copy.deepcopy(_source_files())
    first_path, _second_path = _first_two_paths()
    source_files[first_path]["exact_row_count"] = 42
    source_files[first_path]["exact_row_count_created_by_pr98_flag"] = True

    failures = _validate_source_files(source_files)

    _assert_failure_contains(failures, "exact_row_count_created_by_pr98_flag must be false")
    _assert_failure_contains(failures, "must not fabricate exact per-family counts")


@pytest.mark.parametrize(
    ("path", "fragment"),
    [
        (validator.CANONICAL_BUNDLE_JSONL, "forbidden AtomicRows bundle exists"),
        (validator.CANONICAL_BUNDLE_SHA256, "forbidden AtomicRows bundle hash exists"),
        (Path("tools") / "build_atomicrows_bundle.py", "forbidden bundle builder artifact exists"),
        (
            Path("docs")
            / "master_plan"
            / "atomic_rows"
            / "AtomicRowsBundleFreezeAuthority.yaml",
            "forbidden SHA/freeze authority artifact exists",
        ),
        (
            Path("docs")
            / "master_plan"
            / "generated"
            / "AtomicRowsFullBundleFinalReadinessGate.report.json",
            "forbidden final readiness artifact exists",
        ),
    ],
)
def test_forbidden_bundle_hash_builder_freeze_and_final_readiness_artifacts_fail_closed(
    path: Path,
    fragment: str,
):
    failures = validator.validate_no_forbidden_artifacts(
        ROOT,
        extra_existing_paths=(path,),
    )

    _assert_failure_contains(failures, fragment)


def test_runtime_live_order_source_connector_profit_effects_fail_closed():
    source_files = copy.deepcopy(_source_files())
    first_path, _second_path = _first_two_paths()
    source_files[first_path]["external_source_retrieval_created_flag"] = True
    source_files[first_path]["source_acceptance_created_flag"] = True
    source_files[first_path]["runtime_live_authority_flag"] = True
    blueprint = _first_blueprint(source_files[first_path])
    blueprint["connector_semantic_created_flag"] = True
    blueprint["runtime_live_order_authority_created_flag"] = True
    blueprint["profit_evidence_created_flag"] = True

    failures = _validate_source_files(source_files)

    _assert_failure_contains(failures, "external_source_retrieval_created_flag must be false")
    _assert_failure_contains(failures, "source_acceptance_created_flag must be false")
    _assert_failure_contains(failures, "runtime_live_authority_flag must be false")
    _assert_failure_contains(failures, "connector_semantic_created_flag must be false")
    _assert_failure_contains(failures, "runtime_live_order_authority_created_flag must be false")
    _assert_failure_contains(failures, "profit_evidence_created_flag must be false")


def test_quantum_execution_metadata_fails_closed():
    source_files = copy.deepcopy(_source_files())
    first_path, _second_path = _first_two_paths()
    _first_blueprint(source_files[first_path])["quantum_backend_execution_created_flag"] = True

    _assert_failure_contains(
        _validate_source_files(source_files),
        "quantum_backend_execution_created_flag must be false",
    )
