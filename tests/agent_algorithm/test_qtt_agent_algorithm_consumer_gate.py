from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_qtt_agent_algorithm_consumer_gate as gate


REPO_ROOT = Path(".")
SCHEMA = Path("schemas/agent_algorithm/qtt_agent_algorithm_consumer_gate.schema.json")
REGISTRY = Path("docs/master_plan/agent_algorithm/QTTAgentAlgorithmConsumerGate.yaml")
FIXTURE = Path(
    "tests/fixtures/agent_algorithm/"
    "synthetic_qtt_agent_algorithm_consumer_gate.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/QTTAgentAlgorithmConsumerGate.report.json")
AGENT_REGISTRY = Path("docs/master_plan/agents/QTTAgentRoleOperatingCharterRegistry.yaml")
ALGORITHM_REGISTRY = Path(
    "docs/master_plan/algorithms/QTTAlgorithmFormulaFamilyRegistry.yaml"
)
BINDING_REGISTRY = Path(
    "docs/master_plan/agent_algorithm/QTTAgentAlgorithmBindingRegistry.yaml"
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


def _binding_registry() -> dict:
    return gate.load_registry(BINDING_REGISTRY)


def _agent_charters_by_role() -> dict:
    charters, failures = gate._agent_charters_by_role(_agent_registry())
    assert failures == []
    return charters


def _families_by_name() -> dict:
    families, _, failures = gate._algorithm_families_by_name(_algorithm_registry())
    assert failures == []
    return families


def _algorithm_families() -> list[dict]:
    _, families, failures = gate._algorithm_families_by_name(_algorithm_registry())
    assert failures == []
    return families


def _bindings() -> list[dict]:
    _, bindings, failures = gate._bindings_by_id(_binding_registry())
    assert failures == []
    return bindings


def _allowed_attempts(value: dict) -> list[dict]:
    return [
        attempt
        for attempt in value["consumer_attempts"]
        if attempt["attempt_type"] == gate.ATTEMPT_TYPE_ALLOWED
    ]


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_exists_and_is_valid_json():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    charters = _agent_charters_by_role()
    families = _algorithm_families()

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(gate.TOP_FIELDS)
    assert schema["$defs"]["consumer_attempt"]["required"] == list(gate.ATTEMPT_FIELDS)
    assert schema["$defs"]["agent_algorithm_consumer_gate_report"]["required"] == list(
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
    assert AGENT_REGISTRY.exists()
    assert ALGORITHM_REGISTRY.exists()
    assert BINDING_REGISTRY.exists()

    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        registry_path=REGISTRY,
        fixture_path=FIXTURE,
        agent_registry_path=AGENT_REGISTRY,
        algorithm_registry_path=ALGORITHM_REGISTRY,
        binding_registry_path=BINDING_REGISTRY,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert _report() == result.report


def test_report_has_expected_static_values():
    report = _report()
    binding_count = len(_bindings())

    assert report["report_type"] == gate.REPORT_TYPE
    assert report["deterministic_output"] is True
    assert report["generated_at_utc"] == gate.DETERMINISTIC_GENERATED_AT
    assert report["source_of_gate_substance"] == gate.MASTER_PLAN.as_posix()
    assert report["agent_charter_registry_dependency"] == gate.AGENT_CHARTER_REGISTRY.as_posix()
    assert (
        report["algorithm_formula_family_registry_dependency"]
        == gate.ALGORITHM_FORMULA_FAMILY_REGISTRY.as_posix()
    )
    assert (
        report["agent_algorithm_binding_registry_dependency"]
        == gate.AGENT_ALGORITHM_BINDING_REGISTRY.as_posix()
    )
    assert report["gate_generation_policy"] == gate.GATE_GENERATION_POLICY
    assert report["agent_role_count_from_charter_registry"] == 25
    assert report["algorithm_family_count_from_algorithm_registry"] == 15
    assert report["binding_count_from_binding_registry"] == binding_count
    assert report["expected_allowed_attempt_count_from_binding_registry"] == binding_count
    assert report["actual_allowed_attempt_count"] == binding_count
    assert report["missing_allowed_attempt_count"] == 0
    assert report["unexpected_allowed_attempt_count"] == 0
    assert report["blocked_attempt_count"] >= 5
    assert report["owner_override_attempt_count"] >= 5
    assert report["attempts_with_duplicate_id_count"] == 0
    assert report["invalid_agent_role_attempt_count"] == 0
    assert report["invalid_algorithm_family_attempt_count"] == 0
    assert report["invalid_binding_attempt_count"] == 0
    assert report["invalid_consumer_class_authorization_count"] == 0
    assert report["invalid_trade_context_authorization_count"] == 0
    assert report["authority_boundary_all_false"] is True
    assert report["final_ready"] is False


def test_allowed_attempts_are_derived_from_binding_registry_exactly():
    allowed = _allowed_attempts(_registry())
    bindings = _bindings()

    assert len(allowed) == len(bindings)
    assert [gate._allowed_attempt_key(attempt) for attempt in allowed] == (
        gate._expected_allowed_attempt_keys(bindings)
    )
    for index, (attempt, binding) in enumerate(zip(allowed, bindings), start=1):
        assert attempt["attempt_id"] == gate.attempt_id_for_allowed(
            index,
            agent_role=binding["agent_role"],
            algorithm_family_name=binding["algorithm_family_name"],
        )
        assert attempt["binding_id"] == binding["binding_id"]
        assert attempt["requested_consumer_class"] == binding["authorized_consumer_classes"][0]
        assert attempt["requested_trade_context"] == binding["trade_context_applicability"][0]
        assert attempt["gate_decision"] == "ALLOW"
        assert attempt["owner_override_present"] is False


def test_every_allowed_attempt_matches_dependency_registries_and_binding_fields():
    charters = _agent_charters_by_role()
    families = _families_by_name()
    bindings_by_id, _, failures = gate._bindings_by_id(_binding_registry())
    assert failures == []

    for attempt in _allowed_attempts(_registry()):
        binding = bindings_by_id[attempt["binding_id"]]
        charter = charters[attempt["agent_role"]]
        family = families[attempt["algorithm_family_name"]]

        assert attempt["agent_role_id"] == charter["agent_role_id"]
        assert attempt["algorithm_family_id"] == family["algorithm_family_id"]
        assert attempt["agent_role"] in family["authorized_agent_roles"]
        assert attempt["requested_consumer_class"] in binding["authorized_consumer_classes"]
        assert attempt["requested_trade_context"] in binding["trade_context_applicability"]
        assert attempt["authorized_consumer_classes_from_binding"] == binding[
            "authorized_consumer_classes"
        ]
        assert attempt["trade_context_applicability_from_binding"] == binding[
            "trade_context_applicability"
        ]
        assert attempt["input_parameter_families"] == binding["input_parameter_families"]
        assert attempt["output_signal_type"] == binding["output_signal_type"]
        assert attempt["output_artifact_types"] == binding["output_artifact_types"]
        assert attempt["family_category"] == binding["family_category"]
        assert attempt["classical_or_quantum"] == binding["classical_or_quantum"]
        assert attempt["optimizer_compatibility"] == binding["optimizer_compatibility"]


def test_blocked_attempts_prove_fail_closed_coverage():
    blocked = [
        attempt
        for attempt in _registry()["consumer_attempts"]
        if attempt["gate_decision"] == "BLOCK"
    ]
    types = {attempt["attempt_type"] for attempt in blocked}

    assert len(blocked) >= 5
    assert "BLOCKED_MISSING_BINDING" in types
    assert "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS" in types
    assert "BLOCKED_UNAUTHORIZED_TRADE_CONTEXT" in types
    assert "BLOCKED_DIRECT_ORDER_AUTHORITY" in types
    assert "BLOCKED_METADATA_MISMATCH" in types
    for attempt in blocked:
        assert attempt["owner_override_present"] is False
        assert attempt["reason_codes"]
        assert attempt["gate_decision"] == "BLOCK"


def test_owner_override_satisfies_internal_workflow_without_fabricating_artifacts():
    owner_attempts = [
        attempt
        for attempt in _registry()["consumer_attempts"]
        if attempt["gate_decision"] == "OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW"
    ]
    types = {attempt["attempt_type"] for attempt in owner_attempts}

    assert len(owner_attempts) >= 5
    assert "OWNER_OVERRIDE_MISSING_BINDING" in types
    assert "OWNER_OVERRIDE_UNAUTHORIZED_CONSUMER_CLASS" in types
    assert "OWNER_OVERRIDE_UNAUTHORIZED_TRADE_CONTEXT" in types
    assert "OWNER_OVERRIDE_METADATA_MISMATCH" in types
    for attempt in owner_attempts:
        assert attempt["owner_override_present"] is True
        assert attempt["owner_override_satisfaction_result"] == "OWNER_OVERRIDE_SATISFIED"
        assert attempt["binding_row_fabricated_by_owner_override"] is False
        for field in gate.ATTEMPT_FALSE_ARTIFACT_FIELDS:
            assert attempt[field] is False


def test_fixture_contains_required_synthetic_cases():
    attempts = _fixture()["consumer_attempts"]
    types = {attempt["attempt_type"] for attempt in attempts}

    assert "ALLOWED_BOUND_CONSUMPTION" in types
    assert "BLOCKED_MISSING_BINDING" in types
    assert "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS" in types
    assert "BLOCKED_UNAUTHORIZED_TRADE_CONTEXT" in types
    assert "OWNER_OVERRIDE_MISSING_BINDING" in types
    assert "OWNER_OVERRIDE_UNAUTHORIZED_CONSUMER_CLASS" in types
    assert "OWNER_OVERRIDE_UNAUTHORIZED_TRADE_CONTEXT" in types


def test_quantum_forward_fields_preserve_owner_priority_without_evidence_claims():
    registry = _registry()
    report = _report()
    quantum_allowed = [
        attempt
        for attempt in _allowed_attempts(registry)
        if gate._is_quantum_or_quantum_compatible(attempt)
    ]

    assert registry["quantum_forward_design_supported"] is True
    assert report["quantum_forward_design_supported"] is True
    assert report["quantum_or_quantum_compatible_allowed_attempt_count"] == len(
        quantum_allowed
    )
    for attempt in quantum_allowed:
        assert attempt["owner_quantum_priority_supported"] is True
        assert attempt["owner_can_force_quantum_priority"] is True
        assert attempt["strongest_classical_comparator_required"] is True
        assert attempt["fallback_bundle_required"] is True
        assert attempt["replay_paper_evidence_required_before_advantage_claim"] is True
        assert attempt["live_evidence_required_before_profit_claim"] is True


def test_no_evidence_runtime_live_order_source_connector_replay_paper_or_backend_artifacts():
    registry = _registry()
    report = _report()
    false_top_fields = (
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "quantum_evidence_claim_created",
        "agent_algorithm_cumulative_readiness_gate_created",
        "agent_algorithm_command_matrix_created",
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    )

    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
    assert registry["bundle_file_present"] is False
    assert report["bundle_file_present"] is True
    for field in false_top_fields:
        assert registry[field] is False
        assert report[field] is False
    for attempt in registry["consumer_attempts"]:
        assert attempt["direct_order_submission_allowed_by_binding"] is False
        assert attempt["runtime_live_order_authority_created_by_binding"] is False
        for field in gate.ATTEMPT_FALSE_ARTIFACT_FIELDS:
            assert attempt[field] is False


def test_master_plan_is_unchanged_and_final_ready_is_false():
    assert MASTER_PLAN.exists()
    assert gate.binding_gate._master_plan_has_no_diff(REPO_ROOT.resolve()) == []
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
            "--binding-registry",
            str(BINDING_REGISTRY),
            "--out",
            str(REPORT),
        ]
    )

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_allowed_attempts_fail_closed_for_missing_binding_and_bad_authorization():
    registry = copy.deepcopy(_registry())
    registry["consumer_attempts"] = registry["consumer_attempts"][1:]

    failures = gate._validate_attempts(
        value=registry,
        label="registry",
        strict_full_registry=True,
        charters_by_role=_agent_charters_by_role(),
        families_by_name=_families_by_name(),
        bindings_by_id=gate._bindings_by_id(_binding_registry())[0],
        bindings=_bindings(),
    )

    _assert_failure_contains(failures, "allowed attempts must exactly match")

    unauthorized = copy.deepcopy(_registry())
    first_allowed = _allowed_attempts(unauthorized)[0]
    first_allowed["requested_consumer_class"] = "UNAUTHORIZED_CONSUMER_CLASS_FOR_GATE"
    first_allowed["consumer_class_authorized_by_binding"] = False
    unauthorized_failures = gate._validate_attempts(
        value=unauthorized,
        label="registry",
        strict_full_registry=True,
        charters_by_role=_agent_charters_by_role(),
        families_by_name=_families_by_name(),
        bindings_by_id=gate._bindings_by_id(_binding_registry())[0],
        bindings=_bindings(),
    )

    _assert_failure_contains(unauthorized_failures, "requested_consumer_class")


def test_owner_override_fabricated_binding_or_artifact_is_fail_closed():
    registry = copy.deepcopy(_registry())
    owner_attempt = next(
        attempt
        for attempt in registry["consumer_attempts"]
        if attempt["gate_decision"] == "OWNER_OVERRIDE_ALLOW_INTERNAL_WORKFLOW"
    )
    owner_attempt["binding_row_fabricated_by_owner_override"] = True
    owner_attempt["profit_evidence_claim_created"] = True

    failures = gate._validate_attempts(
        value=registry,
        label="registry",
        strict_full_registry=True,
        charters_by_role=_agent_charters_by_role(),
        families_by_name=_families_by_name(),
        bindings_by_id=gate._bindings_by_id(_binding_registry())[0],
        bindings=_bindings(),
    )

    _assert_failure_contains(failures, "fabricated binding row")
    _assert_failure_contains(failures, "profit_evidence_claim_created must be false")
