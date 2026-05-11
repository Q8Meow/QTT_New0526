from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_qtt_agent_algorithm_binding_registry as gate


REPO_ROOT = Path(".")
SCHEMA = Path("schemas/agent_algorithm/qtt_agent_algorithm_binding_registry.schema.json")
REGISTRY = Path("docs/master_plan/agent_algorithm/QTTAgentAlgorithmBindingRegistry.yaml")
FIXTURE = Path(
    "tests/fixtures/agent_algorithm/"
    "synthetic_qtt_agent_algorithm_binding_registry.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/QTTAgentAlgorithmBindingReport.json")
AGENT_REGISTRY = Path("docs/master_plan/agents/QTTAgentRoleOperatingCharterRegistry.yaml")
ALGORITHM_REGISTRY = Path(
    "docs/master_plan/algorithms/QTTAlgorithmFormulaFamilyRegistry.yaml"
)
MASTER_PLAN = Path("docs/master_plan/QTT_MasterPlan_Current.md")
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _registry() -> dict:
    return gate.load_registry(REGISTRY)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _agent_registry() -> dict:
    return gate.load_registry(AGENT_REGISTRY)


def _algorithm_registry() -> dict:
    return gate.load_registry(ALGORITHM_REGISTRY)


def _agent_charters_by_role() -> dict:
    charters, failures = gate._agent_charters_by_role(_agent_registry())
    assert failures == []
    return charters


def _algorithm_families() -> list[dict]:
    _, families, failures = gate._algorithm_families_by_name(_algorithm_registry())
    assert failures == []
    return families


def _families_by_name() -> dict:
    families, _, failures = gate._algorithm_families_by_name(_algorithm_registry())
    assert failures == []
    return families


def _actual_pairs(value: dict) -> list[tuple[str, str]]:
    return [
        (binding["algorithm_family_name"], binding["agent_role"])
        for binding in value["agent_algorithm_bindings"]
    ]


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_exists_and_is_valid_json():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    charters = _agent_charters_by_role()
    families = _algorithm_families()

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(gate.TOP_FIELDS)
    assert schema["$defs"]["agent_algorithm_binding"]["required"] == list(
        gate.BINDING_FIELDS
    )
    assert schema["$defs"]["agent_algorithm_binding_report"]["required"] == list(
        gate.REPORT_FIELDS
    )
    assert schema["$defs"]["agent_role"]["enum"] == list(charters)
    assert schema["$defs"]["agent_role_id"]["enum"] == [
        charters[role]["agent_role_id"] for role in charters
    ]
    assert schema["$defs"]["algorithm_family_name"]["enum"] == [
        family["algorithm_family_name"] for family in families
    ]
    assert schema["$defs"]["algorithm_family_id"]["enum"] == [
        family["algorithm_family_id"] for family in families
    ]


def test_registry_fixture_and_report_validate():
    assert SCHEMA.exists()
    assert REGISTRY.exists()
    assert FIXTURE.exists()
    assert REPORT.exists()

    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        registry_path=REGISTRY,
        fixture_path=FIXTURE,
        agent_registry_path=AGENT_REGISTRY,
        algorithm_registry_path=ALGORITHM_REGISTRY,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert _report() == result.report


def test_report_has_expected_static_values():
    report = _report()

    assert report["report_type"] == gate.REPORT_TYPE
    assert report["deterministic_output"] is True
    assert report["generated_at_utc"] == gate.DETERMINISTIC_GENERATED_AT
    assert report["source_of_binding_substance"] == gate.MASTER_PLAN.as_posix()
    assert report["agent_charter_registry_dependency"] == gate.AGENT_CHARTER_REGISTRY.as_posix()
    assert (
        report["algorithm_formula_family_registry_dependency"]
        == gate.ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
    )
    assert report["binding_generation_policy"] == gate.BINDING_GENERATION_POLICY
    assert report["agent_role_count_from_charter_registry"] == 25
    assert report["algorithm_family_count_from_algorithm_registry"] == 15
    assert report["expected_binding_count_from_algorithm_registry_authorized_roles"] == 71
    assert report["actual_binding_count"] == 71
    assert report["missing_binding_count"] == 0
    assert report["unexpected_binding_count"] == 0
    assert report["duplicate_binding_id_count"] == 0
    assert report["invalid_agent_role_count"] == 0
    assert report["invalid_algorithm_family_count"] == 0
    assert report["invalid_agent_role_id_count"] == 0
    assert report["invalid_algorithm_family_id_count"] == 0
    assert report["algorithm_families_with_at_least_one_binding_count"] == 15
    assert report["required_roadmap_example_binding_count"] == 5
    assert report["required_roadmap_example_bindings_present_count"] == 5
    assert report["bindings_with_owner_override_supported_count"] == 71
    assert report["bindings_block_owner_override_count"] == 0
    assert report["bindings_with_missing_binding_owner_override_supported_count"] == 71
    assert report["bindings_with_consumer_gate_required_count"] == 71
    assert report["quantum_or_quantum_compatible_binding_count"] == 27
    assert report["quantum_bindings_with_owner_quantum_priority_supported_count"] == 27
    assert report["quantum_bindings_with_owner_can_force_quantum_priority_count"] == 27
    assert report["authority_boundary_all_false"] is True
    assert report["final_ready"] is False


def test_dependency_registries_exist_and_expected_pairs_are_derived_from_algorithm_registry():
    assert AGENT_REGISTRY.exists()
    assert ALGORITHM_REGISTRY.exists()

    expected_pairs = gate.expected_binding_pairs(_algorithm_families())

    assert len(expected_pairs) == 71
    assert _actual_pairs(_registry()) == expected_pairs
    assert _actual_pairs(_fixture()) == expected_pairs
    assert expected_pairs[0] == ("CLASSICAL_SIGNAL_ALGORITHM", "OPTIMIZER_AGENT")


def test_deterministic_binding_order_and_ids():
    for index, binding in enumerate(_registry()["agent_algorithm_bindings"], start=1):
        assert binding["binding_id"] == gate.binding_id_for(
            index,
            agent_role=binding["agent_role"],
            algorithm_family_name=binding["algorithm_family_name"],
        )

    binding_ids = [
        binding["binding_id"] for binding in _registry()["agent_algorithm_bindings"]
    ]
    assert len(binding_ids) == len(set(binding_ids)) == 71


def test_every_binding_matches_agent_and_algorithm_registries():
    charters = _agent_charters_by_role()
    families = _families_by_name()

    for binding in _registry()["agent_algorithm_bindings"]:
        agent_role = binding["agent_role"]
        family_name = binding["algorithm_family_name"]
        family = families[family_name]

        assert agent_role in charters
        assert binding["agent_role_id"] == charters[agent_role]["agent_role_id"]
        assert family_name in families
        assert binding["algorithm_family_id"] == family["algorithm_family_id"]
        assert agent_role in family["authorized_agent_roles"]
        assert binding["authorized_consumer_classes"] == family["authorized_consumer_classes"]
        assert binding["input_parameter_families"] == family["input_parameter_families"]
        assert binding["output_artifact_types"] == family["output_artifact_types"]
        assert binding["trade_context_applicability"] == family["trade_context_applicability"]


def test_all_required_roadmap_example_bindings_are_present():
    pairs = {
        (binding["agent_role"], binding["algorithm_family_name"])
        for binding in _registry()["agent_algorithm_bindings"]
    }

    for pair in gate.REQUIRED_ROADMAP_EXAMPLE_BINDINGS:
        assert pair in pairs


def test_every_binding_has_consumption_emission_selection_and_owner_override_fields():
    for binding in _registry()["agent_algorithm_bindings"]:
        assert binding["authorized_consumer_classes"]
        assert binding["trade_context_applicability"]
        assert binding["input_parameter_families"]
        assert binding["output_signal_type"]
        assert binding["output_artifact_types"]
        assert binding["deterministic_selection_role"]
        assert binding["scoring_ranking_role"]
        assert binding["quantum_classical_arbitration_role"]
        assert binding["master_plan_doctrine_terms_used"]
        assert binding["binding_derivation_summary"]
        assert binding["owner_override_supported"] is True
        assert binding["owner_override_satisfaction_basis"] == gate.OWNER_OVERRIDE_SATISFACTION_BASIS
        assert binding["missing_binding_owner_override_supported"] is True
        assert binding["blocks_qtt_when_owner_override_present"] is False
        assert binding["consumer_gate_required_before_consumption"] is True


def test_quantum_forward_bindings_do_not_claim_quantum_advantage_evidence():
    registry = _registry()
    report = _report()
    families = _families_by_name()

    assert registry["quantum_forward_design_supported"] is True
    assert report["quantum_forward_design_supported"] is True
    assert registry["quantum_evidence_claim_created"] is False
    assert report["quantum_evidence_claim_created"] is False
    for binding in registry["agent_algorithm_bindings"]:
        family = families[binding["algorithm_family_name"]]
        if gate._family_is_quantum_or_compatible(family):
            assert binding["owner_quantum_priority_supported"] is True
            assert binding["owner_can_force_quantum_priority"] is True
            assert binding["strongest_classical_comparator_required"] is True
            assert binding["fallback_bundle_required"] is True
            assert binding["replay_paper_evidence_required_before_advantage_claim"] is True


def test_no_evidence_runtime_live_order_source_connector_replay_paper_or_backend_artifacts():
    registry = _registry()
    report = _report()
    false_fields = (
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "quantum_evidence_claim_created",
        "agent_algorithm_consumer_gate_created",
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "bundle_file_present",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    )

    assert not CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
    for field in false_fields:
        assert registry[field] is False
        assert report[field] is False
    for binding in registry["agent_algorithm_bindings"]:
        assert binding["runtime_live_order_authority_created"] is False
        assert binding["direct_order_submission_allowed"] is False
        assert binding["execution_router_required_for_live_order_path"] is True


def test_master_plan_is_unchanged_and_final_ready_is_false():
    assert MASTER_PLAN.exists()
    assert gate._master_plan_has_no_diff(REPO_ROOT.resolve()) == []
    assert _registry()["final_ready"] is False
    assert _report()["final_ready"] is False


def test_success_marker_appears(capsys):
    exit_code = gate.main(
        [
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--schema",
            str(SCHEMA),
            "--registry",
            str(REGISTRY),
            "--fixture",
            str(FIXTURE),
            "--agent-registry",
            str(AGENT_REGISTRY),
            "--algorithm-registry",
            str(ALGORITHM_REGISTRY),
            "--out",
            str(REPORT),
        ]
    )

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_missing_or_unauthorized_binding_is_fail_closed():
    registry = copy.deepcopy(_registry())
    registry["agent_algorithm_bindings"] = registry["agent_algorithm_bindings"][1:]

    failures = gate._validate_bindings(
        registry,
        label="registry",
        charters_by_role=_agent_charters_by_role(),
        algorithm_families=_algorithm_families(),
        families_by_name=_families_by_name(),
    )

    _assert_failure_contains(failures, "must exactly match")

    unauthorized = copy.deepcopy(_registry())
    unauthorized["agent_algorithm_bindings"][0]["agent_role"] = "OWNER"
    unauthorized["agent_algorithm_bindings"][0]["agent_role_id"] = (
        _agent_charters_by_role()["OWNER"]["agent_role_id"]
    )
    unauthorized_failures = gate._validate_bindings(
        unauthorized,
        label="registry",
        charters_by_role=_agent_charters_by_role(),
        algorithm_families=_algorithm_families(),
        families_by_name=_families_by_name(),
    )

    _assert_failure_contains(unauthorized_failures, "is not authorized")


def test_bad_agent_or_algorithm_id_is_fail_closed():
    registry = copy.deepcopy(_registry())
    registry["agent_algorithm_bindings"][0]["agent_role_id"] = "BAD_AGENT_ID"
    registry["agent_algorithm_bindings"][1]["algorithm_family_id"] = "BAD_FAMILY_ID"

    failures = gate._validate_bindings(
        registry,
        label="registry",
        charters_by_role=_agent_charters_by_role(),
        algorithm_families=_algorithm_families(),
        families_by_name=_families_by_name(),
    )

    _assert_failure_contains(failures, "agent_role_id does not match")
    _assert_failure_contains(failures, "algorithm_family_id does not match")
