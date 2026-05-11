from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

from tools import validate_atomicrows_parameter_stack_role_taxonomy as gate


REPO_ROOT = Path(".")
REGISTRY = Path("docs/master_plan/atomicrows/AtomicRowsParameterStackRoleTaxonomy.yaml")
SCHEMA = Path(
    "schemas/atomicrows/atomicrows_parameter_stack_role_taxonomy.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_parameter_stack_role_taxonomy.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsParameterStackRoleTaxonomy.report.json"
)


def _schema() -> dict:
    return gate.load_json(SCHEMA)


def _registry() -> dict:
    return gate.load_yaml(REGISTRY)


def _fixture() -> dict:
    return gate.load_fixture(FIXTURE)


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _mutated_registry() -> dict:
    return copy.deepcopy(_registry())


def _mutated_fixture() -> dict:
    return copy.deepcopy(_fixture())


def _validate_registry_payload(payload: dict) -> list[str]:
    return gate.validate_registry_payload(payload, schema=_schema())


def test_production_taxonomy_validates_and_main_prints_marker(capsys):
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert gate.main([]) == 0
    assert capsys.readouterr().out.strip() == gate.SUCCESS_MARKER


def test_generated_report_is_deterministic_and_contains_success_marker():
    first = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    second = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    report = _report()

    assert first.failures == second.failures == ()
    assert first.report == second.report == report
    assert gate.serialize_report(first.report or {}) == gate.serialize_report(
        second.report or {}
    )
    assert report["validation_marker"] == gate.SUCCESS_MARKER


def test_required_role_list_order_count_and_definitions_are_canonical():
    registry = _registry()
    schema = _schema()
    roles = list(gate.REQUIRED_STACK_ROLES)
    definitions = registry["role_definitions"]
    definition_ids = [definition["role_id"] for definition in definitions]

    assert registry["required_stack_roles"] == roles
    assert schema["$defs"]["role_id"]["enum"] == roles
    assert registry["minimum_required_role_count"] == 9
    assert len(definitions) == 9
    assert definition_ids == roles
    assert len(set(definition_ids)) == 9
    assert [definition["role_order"] for definition in definitions] == list(range(1, 10))
    assert all(definition["role_required"] is True for definition in definitions)
    assert set(definition_ids) == {
        "SIGNAL",
        "SCORING",
        "NORMALIZATION",
        "RISK",
        "EXECUTION",
        "CAPITAL",
        "LATENCY",
        "ERROR_GUARD",
        "QUANTUM_ADVISORY",
    }


def test_single_set_and_missing_role_policies_match_owner_override_boundary():
    registry = _registry()
    single_parameter = registry["single_parameter_set_policy"]
    single_algorithm = registry["single_algorithm_set_policy"]
    missing_role = registry["missing_role_policy"]

    assert single_parameter["single_parameter_set_complete_without_owner_override"] is False
    assert single_algorithm["single_algorithm_set_complete_without_owner_override"] is False
    assert single_parameter["single_parameter_set_complete_with_owner_override"] is True
    assert single_algorithm["single_algorithm_set_complete_with_owner_override"] is True
    assert single_parameter["owner_override_state"] == gate.OWNER_OVERRIDE_INTERNAL_ONLY
    assert single_algorithm["owner_override_state"] == gate.OWNER_OVERRIDE_INTERNAL_ONLY
    assert missing_role["missing_required_role_blocks_normal_stack_readiness"] is True
    assert (
        missing_role["missing_required_role_owner_override_state"]
        == gate.OWNER_OVERRIDE_INTERNAL_ONLY
    )
    assert missing_role["missing_required_role_creates_runtime_use"] is False
    assert missing_role["missing_required_role_creates_order_authority"] is False


def test_fixture_cases_prove_static_taxonomy_behaviors():
    fixture = _fixture()
    failures = gate.validate_fixture_payload(fixture)
    case_by_id = {case["case_id"]: case for case in fixture["fixture_cases"]}

    assert failures == []
    assert gate.fixture_contains_only_synthetic_cases(fixture) is True
    assert (
        case_by_id["SYNTHETIC_VALID_ALL_ROLES_CANONICAL_ORDER"]["role_ids"]
        == list(gate.REQUIRED_STACK_ROLES)
    )
    missing_state = case_by_id[
        "SYNTHETIC_MISSING_ROLE_BLOCKS_NORMAL_READINESS"
    ]["expected_state"]
    override_state = case_by_id[
        "SYNTHETIC_MISSING_ROLE_OWNER_OVERRIDE_INTERNAL_ONLY"
    ]["expected_state"]
    assert missing_state["normal_stack_readiness_blocked"] is True
    assert override_state["owner_override_state"] == gate.OWNER_OVERRIDE_INTERNAL_ONLY
    assert override_state["evidence_fabricated"] is False
    assert case_by_id[
        "SYNTHETIC_SINGLE_PARAMETER_INCOMPLETE_WITHOUT_OWNER_OVERRIDE"
    ]["expected_state"]["single_parameter_set_complete"] is False
    assert case_by_id[
        "SYNTHETIC_SINGLE_PARAMETER_OWNER_OVERRIDE_INTERNAL_ONLY"
    ]["expected_state"]["single_parameter_set_complete"] is True
    assert case_by_id[
        "SYNTHETIC_SINGLE_ALGORITHM_INCOMPLETE_WITHOUT_OWNER_OVERRIDE"
    ]["expected_state"]["single_algorithm_set_complete"] is False
    assert case_by_id[
        "SYNTHETIC_SINGLE_ALGORITHM_OWNER_OVERRIDE_INTERNAL_ONLY"
    ]["expected_state"]["single_algorithm_set_complete"] is True


def test_owner_override_cannot_fabricate_external_facts_or_evidence():
    registry = _registry()
    policy = registry["owner_override_policy"]

    assert policy["owner_override_supported"] is True
    assert policy["owner_override_satisfies_internal_stack_readiness_only"] is True
    for field in gate.OWNER_OVERRIDE_FALSE_FIELDS:
        assert policy[field] is False

    mutated = _mutated_registry()
    mutated["owner_override_policy"]["owner_override_fabricates_external_fact"] = True
    mutated["owner_override_policy"]["owner_override_fabricates_profit_evidence"] = True

    failures = _validate_registry_payload(mutated)

    _assert_failure_contains(failures, "owner_override_fabricates_external_fact")
    _assert_failure_contains(failures, "owner_override_fabricates_profit_evidence")


def test_quantum_advisory_is_required_static_only_and_evidence_neutral():
    registry = _registry()
    policy = registry["quantum_forward_role_policy"]
    quantum_role = next(
        role for role in registry["role_definitions"] if role["role_id"] == "QUANTUM_ADVISORY"
    )

    assert policy["quantum_advisory_role_required"] is True
    assert policy["quantum_advisory_role_is_static_taxonomy_only"] is True
    assert policy["quantum_backend_execution_created"] is False
    assert policy["quantum_advantage_claim_created"] is False
    assert policy["quantum_scoring_created"] is False
    assert policy["quantum_arbitration_created"] is False
    assert (
        policy["strongest_classical_comparator_required_before_quantum_advantage_claim"]
        is True
    )
    assert policy["replay_paper_evidence_required_before_advantage_claim"] is True
    assert policy["live_evidence_required_before_profit_claim"] is True
    assert quantum_role["runtime_use_allowed"] is False
    assert quantum_role["quantum_backend_evidence_created"] is False


def test_future_stack_gates_and_selection_behaviors_are_not_implemented():
    registry = _registry()

    assert registry["stack_completeness_evaluated_by_this_registry"] is False
    assert registry["stack_compatibility_evaluated_by_this_registry"] is False
    assert registry["stack_selection_created_by_this_registry"] is False
    assert registry["stack_scoring_created_by_this_registry"] is False
    assert registry["optimizer_arbitration_created_by_this_registry"] is False
    assert registry["trade_context_routing_created_by_this_registry"] is False
    assert registry["creates_stack_completeness_gate"] is False
    assert registry["creates_stack_compatibility_gate"] is False
    assert registry["creates_stack_selection"] is False
    assert registry["creates_ranking"] is False
    assert registry["creates_scoring"] is False
    assert registry["creates_optimizer_arbitration"] is False
    assert registry["creates_trade_context_routing"] is False
    assert registry["production_stack_ready"] is False
    assert registry["final_ready"] is False


def test_forbidden_claim_flags_are_false_and_bundle_files_absent():
    registry = _registry()
    report = _report()

    for field in gate.TOP_LEVEL_FALSE_FIELDS:
        assert registry[field] is False
    for field in gate.FORBIDDEN_ARTIFACT_FLAG_FIELDS:
        assert registry["forbidden_artifact_flags"][field] is False
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert gate.validate_master_plan_not_modified(REPO_ROOT) == []


def test_source_acceptance_connector_semantic_runtime_and_order_claims_fail():
    source_failures = gate.validate_no_forbidden_claims(
        (("fixture", "accepted source packet" + " created"),)
    )
    connector_failures = gate.validate_no_forbidden_claims(
        (("fixture", "connector semantic binding" + " created"),)
    )
    runtime = _mutated_registry()
    runtime["creates_runtime_artifacts"] = True
    live_order = _mutated_registry()
    live_order["creates_live_readiness"] = True
    live_order["creates_order_authority"] = True

    _assert_failure_contains(source_failures, "SOURCE_ACCEPTANCE_CLAIM")
    _assert_failure_contains(connector_failures, "CONNECTOR_SEMANTIC_CLAIM")
    _assert_failure_contains(
        _validate_registry_payload(runtime), "creates_runtime_artifacts"
    )
    live_order_failures = _validate_registry_payload(live_order)
    _assert_failure_contains(live_order_failures, "creates_live_readiness")
    _assert_failure_contains(live_order_failures, "creates_order_authority")


def test_bundle_replay_paper_profit_and_quantum_claims_fail():
    bundle = _mutated_registry()
    bundle["creates_atomicrows_bundle_rows"] = True
    bundle["creates_atomicrows_bundle_jsonl"] = True
    bundle["creates_atomicrows_bundle_sha256"] = True
    profit = _mutated_registry()
    profit["creates_profit_evidence"] = True
    quantum = _mutated_registry()
    quantum["creates_quantum_backend_evidence"] = True
    quantum["creates_quantum_advantage_claim"] = True
    quantum["quantum_forward_role_policy"]["quantum_scoring_created"] = True
    quantum["quantum_forward_role_policy"]["quantum_arbitration_created"] = True

    bundle_failures = _validate_registry_payload(bundle)
    _assert_failure_contains(bundle_failures, "creates_atomicrows_bundle_rows")
    _assert_failure_contains(bundle_failures, "creates_atomicrows_bundle_jsonl")
    _assert_failure_contains(bundle_failures, "creates_atomicrows_bundle_sha256")
    _assert_failure_contains(
        gate.validate_no_forbidden_claims(
            (("fixture", "AtomicRows.bundle.jsonl" + " created"),)
        ),
        "BUNDLE_JSONL_CREATION_CLAIM",
    )
    _assert_failure_contains(
        gate.validate_no_forbidden_claims(
            (("fixture", "AtomicRows.bundle.sha256" + " created"),)
        ),
        "BUNDLE_SHA_CREATION_CLAIM",
    )
    _assert_failure_contains(
        gate.validate_no_forbidden_claims((("fixture", "replay passed" + " as proof"),)),
        "REPLAY_PROOF_CLAIM",
    )
    _assert_failure_contains(
        gate.validate_no_forbidden_claims((("fixture", "paper passed" + " as proof"),)),
        "PAPER_PROOF_CLAIM",
    )
    _assert_failure_contains(_validate_registry_payload(profit), "creates_profit_evidence")
    quantum_failures = _validate_registry_payload(quantum)
    _assert_failure_contains(quantum_failures, "creates_quantum_backend_evidence")
    _assert_failure_contains(quantum_failures, "creates_quantum_advantage_claim")
    _assert_failure_contains(quantum_failures, "quantum_scoring_created")
    _assert_failure_contains(quantum_failures, "quantum_arbitration_created")


def test_real_url_and_secret_like_values_fail_in_memory():
    registry = _mutated_registry()
    registry["upstream_dependency_contract"]["synthetic_locator"] = (
        "http" + "://synthetic.invalid"
    )
    fixture = _mutated_fixture()
    fixture["fixture_cases"][0]["synthetic_locator"] = (
        "https" + "://synthetic.invalid"
    )
    fixture["fixture_cases"][0]["synthetic_secret"] = "api" + "_key placeholder"

    registry_failures = _validate_registry_payload(registry)
    fixture_failures = gate.validate_fixture_payload(fixture)

    _assert_failure_contains(registry_failures, "REAL_HTTP_LOCATOR")
    _assert_failure_contains(fixture_failures, "REAL_HTTPS_LOCATOR")
    _assert_failure_contains(fixture_failures, "SECRET_LIKE_API_KEY_UNDERSCORE")


def test_missing_upstream_dependency_and_forbidden_artifact_fail_closed():
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=None,
    )
    missing_root = Path(".pytest-pr73-missing-dependencies")
    artifact_root = Path(".pytest-pr73-forbidden-artifacts")
    shutil.rmtree(missing_root, ignore_errors=True)
    shutil.rmtree(artifact_root, ignore_errors=True)
    try:
        missing_root.mkdir()
        missing_failures = gate.validate_upstream_dependencies(missing_root)
        bundle = artifact_root / gate.CANONICAL_BUNDLE_JSONL
        bundle.parent.mkdir(parents=True)
        bundle.write_text("", encoding="utf-8")
        bundle_hash = artifact_root / gate.CANONICAL_BUNDLE_SHA256
        bundle_hash.write_text("", encoding="utf-8")
        artifact_failures = gate.validate_no_forbidden_artifacts(artifact_root)
    finally:
        shutil.rmtree(missing_root, ignore_errors=True)
        shutil.rmtree(artifact_root, ignore_errors=True)

    assert result.failures == ()
    _assert_failure_contains(missing_failures, "PR70_CLASSIFIER_DEPENDENCY_BLOCK")
    _assert_failure_contains(missing_failures, "PR71_INTAKE_REGISTRY_DEPENDENCY_BLOCK")
    _assert_failure_contains(missing_failures, "PR72_CANDIDATE_FAMILY_GATE_DEPENDENCY_BLOCK")
    _assert_failure_contains(artifact_failures, "AtomicRows.bundle.jsonl")
    _assert_failure_contains(artifact_failures, "AtomicRows.bundle.sha256")
