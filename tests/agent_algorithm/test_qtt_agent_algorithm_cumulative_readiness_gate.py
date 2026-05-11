from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_qtt_agent_algorithm_cumulative_readiness_gate as gate


REPO_ROOT = Path(".")
SCHEMA = Path(
    "schemas/agent_algorithm/qtt_agent_algorithm_cumulative_readiness_gate.schema.json"
)
REGISTRY = Path(
    "docs/master_plan/agent_algorithm/QTTAgentAlgorithmCumulativeReadinessGate.yaml"
)
FIXTURE = Path(
    "tests/fixtures/agent_algorithm/"
    "synthetic_qtt_agent_algorithm_cumulative_readiness_gate.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/QTTAgentAlgorithmCumulativeReadinessGate.report.json"
)
OWNER_REPORT = Path("docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json")
AGENT_REGISTRY = Path("docs/master_plan/agents/QTTAgentRoleOperatingCharterRegistry.yaml")
ALGORITHM_REGISTRY = Path(
    "docs/master_plan/algorithms/QTTAlgorithmFormulaFamilyRegistry.yaml"
)
BINDING_REGISTRY = Path(
    "docs/master_plan/agent_algorithm/QTTAgentAlgorithmBindingRegistry.yaml"
)
CONSUMER_GATE = Path("docs/master_plan/agent_algorithm/QTTAgentAlgorithmConsumerGate.yaml")
AGENT_REPORT = Path("docs/master_plan/generated/QTTAgentRoleOperatingCharterReport.json")
ALGORITHM_REPORT = Path("docs/master_plan/generated/QTTAlgorithmFormulaFamilyReport.json")
BINDING_REPORT = Path("docs/master_plan/generated/QTTAgentAlgorithmBindingReport.json")
CONSUMER_REPORT = Path(
    "docs/master_plan/generated/QTTAgentAlgorithmConsumerGate.report.json"
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


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _agent_registry() -> dict:
    return gate.load_registry(AGENT_REGISTRY)


def _algorithm_registry() -> dict:
    return gate.load_registry(ALGORITHM_REGISTRY)


def _binding_registry() -> dict:
    return gate.load_registry(BINDING_REGISTRY)


def _consumer_gate() -> dict:
    return gate.load_registry(CONSUMER_GATE)


def _metrics(registry: dict | None = None) -> dict:
    return gate.collect_metrics(
        repo_root=REPO_ROOT.resolve(),
        registry=_registry() if registry is None else registry,
        owner_report=_json(OWNER_REPORT),
        agent_registry=_agent_registry(),
        algorithm_registry=_algorithm_registry(),
        binding_registry=_binding_registry(),
        consumer_registry=_consumer_gate(),
        agent_report=_json(AGENT_REPORT),
        algorithm_report=_json(ALGORITHM_REPORT),
        binding_report=_json(BINDING_REPORT),
        consumer_report=_json(CONSUMER_REPORT),
    )


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_exists_and_is_valid_json():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(gate.TOP_FIELDS)
    assert schema["properties"]["readiness_components"]["minItems"] == 8
    assert schema["properties"]["readiness_components"]["maxItems"] == 8
    assert schema["properties"]["readiness_components"]["uniqueItems"] is True
    assert schema["$defs"]["readiness_component"]["required"] == list(
        gate.COMPONENT_FIELDS
    )
    assert schema["$defs"]["agent_algorithm_cumulative_readiness_gate_report"][
        "required"
    ] == list(gate.REPORT_FIELDS)


def test_registry_fixture_report_and_dependencies_validate():
    for path in (
        SCHEMA,
        REGISTRY,
        FIXTURE,
        REPORT,
        OWNER_REPORT,
        AGENT_REGISTRY,
        ALGORITHM_REGISTRY,
        BINDING_REGISTRY,
        CONSUMER_GATE,
        AGENT_REPORT,
        ALGORITHM_REPORT,
        BINDING_REPORT,
        CONSUMER_REPORT,
    ):
        assert path.exists()

    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        registry_path=REGISTRY,
        fixture_path=FIXTURE,
        owner_report_path=OWNER_REPORT,
        agent_registry_path=AGENT_REGISTRY,
        algorithm_registry_path=ALGORITHM_REGISTRY,
        binding_registry_path=BINDING_REGISTRY,
        consumer_registry_path=CONSUMER_GATE,
        agent_report_path=AGENT_REPORT,
        algorithm_report_path=ALGORITHM_REPORT,
        binding_report_path=BINDING_REPORT,
        consumer_report_path=CONSUMER_REPORT,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert _report() == result.report


def test_component_order_ids_and_required_fields_are_deterministic():
    for value in (_registry(), _fixture()):
        components = value["readiness_components"]

        assert len(components) == 8
        assert [component["component_id"] for component in components] == list(
            gate.COMPONENT_IDS
        )
        assert len({component["component_id"] for component in components}) == 8
        for component in components:
            assert set(component) == set(gate.COMPONENT_FIELDS)
            assert component["dependency_paths"]
            assert component["dependency_reports"]
            assert component["expected_success_markers"]
            assert component["measured_counts"]
            assert component["reason_codes"]
            assert component["owner_override_supported"] is True
            assert (
                component["owner_override_satisfaction_basis"]
                == gate.OWNER_OVERRIDE_SATISFACTION_BASIS
            )
            assert component["final_ready_contribution"] is False


def test_report_has_expected_dependency_derived_counts():
    report = _report()
    metrics = _metrics()

    assert report["component_count"] == 8
    assert report["required_component_count"] == 8
    assert report["components_present_count"] == 8
    assert report["missing_component_count"] == 0
    assert report["invalid_component_order_count"] == 0
    assert report["agent_role_count_from_charter_registry"] == 25
    assert report["algorithm_family_count_from_algorithm_registry"] == 15
    assert report["binding_count_from_binding_registry"] == metrics[
        "expected_binding_count_from_binding_report"
    ]
    assert report["consumer_allowed_attempt_count"] == report[
        "binding_count_from_binding_registry"
    ]
    assert report["consumer_blocked_attempt_count"] >= 5
    assert report["consumer_owner_override_attempt_count"] >= 5
    assert report["invalid_agent_role_count"] == 0
    assert report["invalid_algorithm_family_count"] == 0
    assert report["invalid_binding_count"] == 0
    assert report["invalid_consumer_authorization_count"] == 0


def test_static_internal_readiness_and_future_boundaries_are_encoded():
    registry = _registry()
    report = _report()

    for value in (registry, report):
        assert value["owner_global_override_authority"] is True
        assert value["owner_override_satisfies_all_qtt_internal_requirements"] is True
        assert value["owner_override_satisfies_agent_algorithm_readiness"] is True
        assert value["static_agent_algorithm_foundation_ready"] is True
        assert value["normal_static_agent_algorithm_coverage_ready"] is True
        assert value["normal_full_agent_algorithm_coverage_ready"] is False
        assert value["qtt_internal_agent_algorithm_ready"] is True
        assert value["future_command_matrix_required"] is False
        assert value["agent_algorithm_command_matrix_created"] is True
        assert value["future_parameter_stack_layers_required"] is True
        assert value["future_scoring_ranking_layers_required"] is True
        assert value["future_quantum_classical_arbitration_required"] is True
        assert value["future_replay_paper_evidence_required"] is True
        assert value["future_runtime_live_readiness_required"] is True
        assert value["future_atomicrows_bundle_hash_required"] is True
        assert value["final_ready"] is False


def test_quantum_forward_fields_preserve_compatibility_without_evidence_claims():
    report = _report()
    quantum_component = _registry()["readiness_components"][5]

    assert report["quantum_forward_design_supported"] is True
    assert report["quantum_algorithm_family_count"] >= 9
    assert report["quantum_binding_count"] >= 1
    assert report["quantum_consumer_allowed_attempt_count"] >= 1
    assert report["owner_quantum_priority_supported"] is True
    assert report["owner_can_force_quantum_priority_supported"] is True
    assert quantum_component["component_id"] == gate.COMPONENT_IDS[5]
    assert quantum_component["quantum_forward_contribution"] is True
    assert quantum_component["quantum_evidence_claim_created"] is False
    assert "NO_QUANTUM_ADVANTAGE_OR_BACKEND_EVIDENCE_CLAIMED" in quantum_component[
        "reason_codes"
    ]


def test_no_runtime_live_order_source_connector_replay_paper_profit_or_backend_artifacts():
    registry = _registry()
    report = _report()
    false_fields = (
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "quantum_evidence_claim_created",
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
    for value in (registry, report):
        for field in false_fields:
            assert value[field] is False
    for component in registry["readiness_components"]:
        for field in (
            "evidence_claim_created",
            "alpha_evidence_claim_created",
            "profit_evidence_claim_created",
            "latency_superiority_evidence_claim_created",
            "execution_superiority_evidence_claim_created",
            "quantum_evidence_claim_created",
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
        ):
            assert component[field] is False
    assert report["authority_boundary_all_false"] is True


def test_master_plan_is_unchanged_and_fixture_is_synthetic():
    fixture = _fixture()

    assert MASTER_PLAN.exists()
    assert gate.binding_gate._master_plan_has_no_diff(REPO_ROOT.resolve()) == []
    assert fixture["fixture_id"] == (
        "SYNTHETIC_QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_FIXTURE"
    )
    assert fixture["fixture_authority_class"] == (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_BINDING_READINESS_AUTHORITY"
    )
    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"


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
            "--owner-report",
            str(OWNER_REPORT),
            "--agent-registry",
            str(AGENT_REGISTRY),
            "--algorithm-registry",
            str(ALGORITHM_REGISTRY),
            "--binding-registry",
            str(BINDING_REGISTRY),
            "--consumer-registry",
            str(CONSUMER_GATE),
            "--agent-report",
            str(AGENT_REPORT),
            "--algorithm-report",
            str(ALGORITHM_REPORT),
            "--binding-report",
            str(BINDING_REPORT),
            "--consumer-report",
            str(CONSUMER_REPORT),
            "--out",
            str(REPORT),
        ]
    )

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_cumulative_gate_fails_closed_for_bad_component_order_and_artifact_claims():
    registry = copy.deepcopy(_registry())
    registry["readiness_components"] = list(reversed(registry["readiness_components"]))

    failures = gate._validate_components(registry, label="registry")

    _assert_failure_contains(failures, "deterministic order")

    unsafe = copy.deepcopy(_registry())
    unsafe["final_ready"] = True
    unsafe["runtime_artifact_created"] = True
    unsafe["readiness_components"][0]["profit_evidence_claim_created"] = True

    top_failures = gate._validate_top_level(
        unsafe,
        label="registry",
        schema=json.loads(SCHEMA.read_text(encoding="utf-8")),
    )
    component_failures = gate._validate_components(unsafe, label="registry")

    _assert_failure_contains(top_failures, "final_ready")
    _assert_failure_contains(top_failures, "runtime_artifact_created")
    _assert_failure_contains(component_failures, "profit_evidence_claim_created")
