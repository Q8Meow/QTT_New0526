from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile

import pytest

from tools import validate_atomicrows_row_family_source_manifest_currentization as validator
from tools import run_validation_gates as runner


ROOT = Path(__file__).resolve().parents[2]
_CACHE: dict[str, object] = {}


def _schema() -> dict:
    if "schema" not in _CACHE:
        _CACHE["schema"] = validator.load_json(ROOT / validator.DEFAULT_SCHEMA)
    return deepcopy(_CACHE["schema"])


def _manifest() -> dict:
    if "manifest" not in _CACHE:
        _CACHE["manifest"] = validator.load_yaml(ROOT / validator.DEFAULT_MANIFEST)
    return deepcopy(_CACHE["manifest"])


def _fixture() -> dict:
    if "fixture" not in _CACHE:
        _CACHE["fixture"] = validator.load_json(ROOT / validator.DEFAULT_FIXTURE)
    return deepcopy(_CACHE["fixture"])


def _payloads() -> dict:
    if "payloads" not in _CACHE:
        payloads, failures = validator._load_json_evidence(ROOT)
        assert failures == []
        _CACHE["payloads"] = payloads
    return deepcopy(_CACHE["payloads"])


def _entries(manifest: dict | None = None) -> list[dict]:
    payload = _manifest() if manifest is None else manifest
    return payload["row_family_source_manifest"]["row_family_entries"]


def _failures_for_manifest_mutation(mutator) -> set[str]:
    manifest = _manifest()
    mutator(manifest)
    return set(validator.validate_manifest_payload(manifest, _schema(), _payloads(), ROOT))


def _assert_has(failures: set[str] | tuple[str, ...], expected: str) -> None:
    assert any(expected in failure for failure in failures), failures


@contextmanager
def _temp_validation_dir():
    base = ROOT / ".tmp" / "pr139_atomicrows_manifest_tests"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="case_", dir=base) as temp_dir:
        yield Path(temp_dir)


def _copy_validation_tree(tmp_path: Path) -> Path:
    for rel_path in (
        validator.DEFAULT_SCHEMA,
        validator.DEFAULT_MANIFEST,
        validator.DEFAULT_FIXTURE,
        validator.MASTER_PLAN_PATH,
    ):
        src = ROOT / rel_path
        dst = tmp_path / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    for _field, rel_path in validator.EVIDENCE_REF_FIELDS:
        src = ROOT / rel_path
        dst = tmp_path / rel_path
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return tmp_path


def _run_in_temp_without(tmp_path: Path, rel_path: Path) -> tuple[str, ...]:
    repo = _copy_validation_tree(tmp_path)
    target = repo / rel_path
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    result = validator.validate(repo_root=repo, output_path=None)
    return result.failures


def test_valid_manifest_passes_and_report_serialization_is_deterministic() -> None:
    with _temp_validation_dir() as tmp_path:
        first_path = tmp_path / "first.report.json"
        second_path = tmp_path / "second.report.json"
        first = validator.validate(repo_root=ROOT, output_path=first_path)
        second = validator.validate(repo_root=ROOT, output_path=second_path)

        first_text = first_path.read_text(encoding="utf-8")
        second_text = second_path.read_text(encoding="utf-8")
    assert first.failures == second.failures == ()
    assert first.report == second.report
    assert first_text == second_text
    assert first_text == json.dumps(json.loads(first_text), indent=2, sort_keys=True) + "\n"
    assert first.report["validation_marker"] == validator.SUCCESS_MARKER
    assert first.report["final_ready"] is False
    assert str(ROOT) not in first_text


def test_manifest_is_derived_from_pr137r_source_paths_and_pr138_semantic_fields() -> None:
    manifest = _manifest()
    payloads = _payloads()
    pr137r = payloads["pr137r_report_ref"]
    inventory = payloads["pr138_field_inventory_ref"]

    source_paths = validator._source_paths_from_pr137r(pr137r)
    required_fields = validator._field_ids_from_inventory(inventory)
    required_groups = validator._group_ids_from_inventory(inventory)
    supported_fields = validator._supported_fields_from_pr137r(pr137r)
    expected_missing = [
        field_id for field_id in required_fields if field_id not in set(supported_fields)
    ]

    entries = _entries(manifest)
    assert len(entries) == 15
    assert [entry["source_file_path"] for entry in entries] == source_paths
    assert [entry["canonical_family_order"] for entry in entries] == list(range(1, 16))
    for entry in entries:
        assert entry["required_field_ids"] == required_fields
        assert entry["required_field_group_ids"] == required_groups
        assert entry["supported_field_ids_currently_present_if_known"] == ["row_id"]
        assert entry["missing_field_ids_requiring_future_enrichment"] == expected_missing


def test_pr136_control_plane_evidence_is_consumed_read_only() -> None:
    refs = [path for _field, path in validator.PR136_JSON_EVIDENCE_REFS]
    before = {path.as_posix(): (ROOT / path).read_bytes() for path in refs}
    with _temp_validation_dir() as tmp_path:
        result = validator.validate(repo_root=ROOT, output_path=tmp_path / "report.json")
    after = {path.as_posix(): (ROOT / path).read_bytes() for path in refs}

    assert result.failures == ()
    assert before == after
    report_refs = set(result.report["pr136_evidence_consumed"])
    for required in (
        "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
        "docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json",
        "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json",
        "docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
    ):
        assert required in report_refs


def test_atomicrows_pr137_pr138_evidence_links_are_consumed_read_only() -> None:
    protected = [
        validator.ATOMICROWS_BUNDLE_PATH,
        *sorted(validator.ROW_FAMILY_SOURCE_DIRECTORY.glob("*.source.jsonl")),
    ]
    before = {path.as_posix(): (ROOT / path).read_bytes() for path in protected}
    with _temp_validation_dir() as tmp_path:
        result = validator.validate(repo_root=ROOT, output_path=tmp_path / "report.json")
    after = {path.as_posix(): (ROOT / path).read_bytes() for path in protected}

    assert result.failures == ()
    assert before == after
    assert result.report["pr137r_evidence_consumed"]
    assert result.report["pr137l_evidence_consumed"]
    assert result.report["pr138_evidence_consumed"]
    assert result.report["row_family_source_file_count"] == 15
    assert result.report["existing_bundle_row_count"] == 4183
    assert result.report["required_field_count"] == 59
    assert result.report["required_field_group_count"] == 8


def test_quantum_prediction_market_and_source_requirements_are_metadata_only() -> None:
    entry = _entries()[0]
    prediction = entry["prediction_market_compatibility_requirements"]
    quantum = entry["quantum_metadata_currentization_requirements"]
    objective = entry["profit_risk_latency_objective_metadata_requirements"]
    agent = entry["agent_selection_replay_paper_requirements"]
    source = entry["source_provenance_requirements"]

    assert prediction["canonical_stage1_venue_ids"] == list(validator.CANONICAL_STAGE1_VENUE_IDS)
    for venue_id in validator.CANONICAL_STAGE1_VENUE_IDS:
        assert prediction[venue_id] == validator.VENUE_COMPATIBILITY_PLACEHOLDER
    assert not set(prediction["canonical_stage1_venue_ids"]) & set(
        validator.FORBIDDEN_VENUE_ALIASES
    )
    assert prediction["forbidden_venue_aliases"] == list(validator.FORBIDDEN_VENUE_ALIASES)

    for field in (
        "quantum_applicability_class",
        "classical_only_flag",
        "quantum_inspired_flag",
        "true_quantum_compatible_flag",
        "qubo_compatible_flag",
        "ising_compatible_flag",
        "qaoa_compatible_flag",
        "vqe_compatible_flag",
        "annealing_compatible_flag",
        "quantum_kernel_feature_map_compatible_flag",
    ):
        assert field in quantum
    assert quantum["metadata_only_flag"] is True
    assert quantum["execution_allowed_by_pr139_flag"] is False
    assert quantum["quantum_backend_execution_allowed_flag"] is False
    assert objective["profit_latency_execution_superiority_claim_created_flag"] is False
    assert agent["live_use_allowed_flag"] is False
    assert agent["order_authority_created_flag"] is False
    assert agent["profit_evidence_created_flag"] is False
    assert source["source_evidence_required_flag"] is True
    assert source["accepted_source_packet_required_flag"] is True
    assert source["research_input_only_flag"] is True
    assert source["external_fact_authority_flag"] is False


def test_fixture_lists_expected_negative_cases_without_becoming_authority() -> None:
    fixture = _fixture()
    assert fixture["validator_marker"] == validator.SUCCESS_MARKER
    assert fixture["authority_class"] == validator.AUTHORITY_CLASS
    assert fixture["positive_expected_entry_count"] == 15
    assert [case["case_id"] for case in fixture["negative_case_expectations"]] == [
        case_id for case_id, _reason in validator.NEGATIVE_FIXTURE_EXPECTATIONS
    ]


@pytest.mark.parametrize(
    ("rel_path", "expected"),
    [
        (
            dict(validator.PR136_JSON_EVIDENCE_REFS)["pr136_route_triage_ref"],
            validator.REASON_PR136_ROUTE_TRIAGE_MISSING,
        ),
        (
            dict(validator.PR136_JSON_EVIDENCE_REFS)[
                "pr136_master_plan_coverage_to_readiness_domain_map_ref"
            ],
            validator.REASON_PR136_COVERAGE_MAP_MISSING,
        ),
        (
            dict(validator.PR136_JSON_EVIDENCE_REFS)[
                "pr136_quantum_atomicrows_optimization_readiness_map_ref"
            ],
            validator.REASON_PR136_QUANTUM_MAP_MISSING,
        ),
        (
            dict(validator.ATOMICROWS_JSON_EVIDENCE_REFS)["pr137r_report_ref"],
            validator.REASON_PR137R_MISSING,
        ),
        (
            dict(validator.ATOMICROWS_JSON_EVIDENCE_REFS)[
                "pr138_semantic_contract_report_ref"
            ],
            validator.REASON_PR138_MISSING,
        ),
        (
            Path(
                "docs/master_plan/atomic_rows/pr98_row_family_sources/"
                "001_signal_features.source.jsonl"
            ),
            validator.REASON_SOURCE_FILE_MISSING,
        ),
    ],
)
def test_missing_required_evidence_or_source_file_fails_closed(
    rel_path: Path,
    expected: str,
) -> None:
    with _temp_validation_dir() as tmp_path:
        failures = _run_in_temp_without(tmp_path, rel_path)
    _assert_has(failures, expected)


@pytest.mark.parametrize(
    ("case_id", "mutator", "expected"),
    [
        (
            "PR136 same-number inference flag true fails",
            lambda manifest: manifest.update(roadmap_identity_inference_used=True),
            validator.REASON_PR136_SAME_NUMBER,
        ),
        (
            "PR136 authority preservation flag false fails",
            lambda manifest: manifest["pr136_alignment"].update(
                pr136_no_authority_flags_preserved=False
            ),
            validator.REASON_PR136_NO_AUTHORITY_DRIFT,
        ),
        (
            "Missing source file path fails",
            lambda manifest: _entries(manifest)[0].update(source_file_path="missing.source.jsonl"),
            validator.REASON_SOURCE_FILE_MISSING,
        ),
        (
            "Duplicate family id fails",
            lambda manifest: _entries(manifest)[1].update(
                family_id=_entries(manifest)[0]["family_id"]
            ),
            validator.REASON_DUPLICATE_FAMILY_ID,
        ),
        (
            "Duplicate source path fails",
            lambda manifest: _entries(manifest)[1].update(
                source_file_path=_entries(manifest)[0]["source_file_path"]
            ),
            validator.REASON_DUPLICATE_SOURCE_PATH,
        ),
        (
            "Missing PR138 required field fails",
            lambda manifest: _entries(manifest)[0].update(
                required_field_ids=[
                    field
                    for field in _entries(manifest)[0]["required_field_ids"]
                    if field != "row_id"
                ]
            ),
            validator.REASON_REQUIRED_FIELD_MISSING,
        ),
        (
            "Unknown field id fails",
            lambda manifest: _entries(manifest)[0]["required_field_ids"].append(
                "unknown_future_field"
            ),
            validator.REASON_UNKNOWN_FIELD_ID,
        ),
        (
            "Missing required field group fails",
            lambda manifest: _entries(manifest)[0].update(
                required_field_group_ids=[
                    group
                    for group in _entries(manifest)[0]["required_field_group_ids"]
                    if group != "IDENTITY"
                ]
            ),
            validator.REASON_REQUIRED_FIELD_GROUP_MISSING,
        ),
        (
            "Unknown field group fails",
            lambda manifest: _entries(manifest)[0]["required_field_group_ids"].append(
                "UNKNOWN_GROUP"
            ),
            validator.REASON_UNKNOWN_FIELD_GROUP_ID,
        ),
        (
            "Unknown missing enrichment field fails",
            lambda manifest: _entries(manifest)[0][
                "missing_field_ids_requiring_future_enrichment"
            ].append("unknown_missing_field"),
            validator.REASON_MISSING_FIELD_NOT_TRACEABLE,
        ),
        (
            "Forbidden ForecastEx alias outside blocked list fails",
            lambda manifest: _entries(manifest)[0][
                "prediction_market_compatibility_requirements"
            ]["canonical_stage1_venue_ids"].append("FORECASTX"),
            validator.REASON_FORBIDDEN_VENUE_ALIAS,
        ),
        (
            "New forbidden field-name fragment fails",
            lambda manifest: manifest.update(sha_authority_created_flag=False),
            validator.REASON_CRYPTO_FIELD_NAME,
        ),
    ],
)
def test_manifest_mutations_fail_closed(case_id: str, mutator, expected: str) -> None:
    failures = _failures_for_manifest_mutation(mutator)
    _assert_has(failures, expected)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("source_file_mutation_allowed_flag", validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS["source_file_mutation_allowed_flag"]),
        ("bundle_mutation_allowed_flag", validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS["bundle_mutation_allowed_flag"]),
        (
            "semantic_value_materialization_allowed_flag",
            validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                "semantic_value_materialization_allowed_flag"
            ],
        ),
        ("final_readiness_created_flag", validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS["final_readiness_created_flag"]),
        (
            "runtime_live_order_authority_created_flag",
            validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                "runtime_live_order_authority_created_flag"
            ],
        ),
        ("source_acceptance_created_flag", validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS["source_acceptance_created_flag"]),
        (
            "connector_semantic_binding_created_flag",
            validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                "connector_semantic_binding_created_flag"
            ],
        ),
        (
            "replay_paper_execution_created_flag",
            validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                "replay_paper_execution_created_flag"
            ],
        ),
        (
            "neural_training_or_inference_created_flag",
            validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                "neural_training_or_inference_created_flag"
            ],
        ),
        (
            "quantum_backend_execution_created_flag",
            validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                "quantum_backend_execution_created_flag"
            ],
        ),
        (
            "profit_latency_execution_superiority_claim_created_flag",
            validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                "profit_latency_execution_superiority_claim_created_flag"
            ],
        ),
        (
            "cryptographic_sidecar_authority_created_flag",
            validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS[
                "cryptographic_sidecar_authority_created_flag"
            ],
        ),
        ("freeze_authority_created_flag", validator.FORBIDDEN_AUTHORITY_CLAIM_FIELDS["freeze_authority_created_flag"]),
    ],
)
def test_authority_claim_flags_true_fail(field: str, expected: str) -> None:
    failures = _failures_for_manifest_mutation(lambda manifest: manifest.update({field: True}))
    _assert_has(failures, expected)


def test_run_validation_gates_invokes_pr139_after_pr138_gate() -> None:
    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr138_index = next(
        index
        for index, command in enumerate(commands)
        if command[1] == "-c"
        and command[2] == runner.PR138_NON_MUTATING_VALIDATION_SCRIPT
    )
    pr139_index = command_names.index(
        "validate_atomicrows_row_family_source_manifest_currentization.py"
    )
    pr140_index = command_names.index(
        "validate_atomicrows_semantic_field_coverage_enrichment_plan.py"
    )
    pytest_index = command_names.index(runner.PYTEST_FRESH_BASETEMP_SCRIPT)

    assert pr138_index < pr139_index < pr140_index < pytest_index
    assert "stage1_atomicrows_semantic_row_contract_gate.py" not in command_names
