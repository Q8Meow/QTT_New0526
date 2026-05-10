from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_parameter_agent_binding_registry as binding_gate


REPO_ROOT = Path(".")
REGISTRY = Path(
    "docs/master_plan/atomic_rows/AtomicRowsParameterAgentBindingRegistry.yaml"
)
SCHEMA = Path(
    "schemas/atomicrows/atomicrows_parameter_agent_binding_registry.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_parameter_agent_binding_registry.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/AtomicRowsParameterAgentBindingReport.json")
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _registry() -> dict:
    return binding_gate.load_registry(REGISTRY)


def _fixture() -> dict:
    return binding_gate.load_fixture(FIXTURE)


def _binding(binding_id: str) -> dict:
    for binding in _registry()["bindings"]:
        if binding["binding_id"] == binding_id:
            return binding
    raise AssertionError(f"missing binding {binding_id}")


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_declares_required_binding_enums_and_report_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["$defs"]["binding_status"]["enum"] == list(
        binding_gate.BINDING_STATUSES
    )
    assert schema["$defs"]["agent_role"]["enum"] == list(binding_gate.AGENT_ROLES)
    assert schema["$defs"]["consumer_class"]["enum"] == list(
        binding_gate.CONSUMER_CLASSES
    )
    assert schema["$defs"]["agent_use_scope"]["enum"] == list(
        binding_gate.AGENT_USE_SCOPES
    )
    assert schema["$defs"]["owner_override_token"]["enum"] == list(
        binding_gate.OWNER_OVERRIDE_TOKENS
    )
    assert schema["$defs"]["binding"]["required"] == list(binding_gate.BINDING_FIELDS)
    assert schema["$defs"]["parameter_agent_binding_report"]["required"] == list(
        binding_gate._empty_report()
    )


def test_registry_and_fixture_validate_with_owner_authority_boundary():
    registry = _registry()
    fixture = _fixture()

    assert binding_gate.validate_registry_shape(registry) == []
    assert binding_gate.validate_fixture_shape(fixture) == []
    assert binding_gate.validate_bindings(registry["bindings"]) == []
    assert binding_gate.validate_bindings(fixture["bindings"]) == []
    assert registry["canonical_source_for_parameter_agent_assignment"] is True
    assert registry["owner_global_override_authority"] is True
    assert registry["owner_override_satisfies_all_qtt_internal_requirements"] is True
    assert registry["codex_authority_over_owner"] is False
    assert registry["qtt_agent_authority_over_owner"] is False
    assert registry["validator_authority_over_owner"] is False


def test_report_is_deterministic_and_has_required_counts():
    first, first_failures = binding_gate.build_report(
        repo_root=REPO_ROOT.resolve(),
        registry=_registry(),
        fixture=_fixture(),
    )
    second, second_failures = binding_gate.build_report(
        repo_root=REPO_ROOT.resolve(),
        registry=_registry(),
        fixture=_fixture(),
    )

    assert first_failures == []
    assert second_failures == []
    assert first == second
    assert binding_gate.serialize_report(first) == binding_gate.serialize_report(second)
    assert first == json.loads(REPORT.read_text(encoding="utf-8"))
    assert first["binding_count"] == 13
    assert first["parameter_family_binding_count"] == 13
    assert first["row_level_binding_count"] == 1
    assert first["pattern_level_binding_count"] == 12
    assert first["owner_approved_binding_count"] == 7
    assert first["owner_global_override_binding_count"] == 4
    assert first["owner_override_satisfied_binding_count"] == 4
    assert first["missing_binding_normal_blocked_count"] == 1
    assert first["missing_binding_owner_override_satisfied_count"] == 1
    assert first["runtime_binding_count"] == 1
    assert first["live_binding_count"] == 1
    assert first["quantum_backend_binding_count"] == 1
    assert first["uses_pr_number_as_authority"] is False
    assert first["final_ready"] is False
    assert first["authority_boundary_all_false"] is True


def test_dev_mode_passes_but_final_mode_remains_incomplete():
    dev = binding_gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    final = binding_gate.validate(
        mode="final",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert dev.failures == ()
    assert final.ok is False
    _assert_failure_contains(final.failures, "final mode incomplete")


def test_owner_approved_bindings_are_accepted_without_codex_or_agent_blocking():
    binding = copy.deepcopy(
        _binding("binding_research_source_candidate_family_to_research_agent")
    )
    binding["binding_id"] = "synthetic_owner_approved_internal_requirement_satisfied"
    binding["authorized_agent_roles"] = []
    binding["authorized_agent_ids"] = []
    binding["authorized_consumer_classes"] = []
    binding["binding_authority_basis"] = "OWNER_APPROVED"
    binding["final_qtt_internal_status"] = "OWNER_APPROVED"

    assert binding_gate.validate_bindings([binding]) == []


def test_owner_global_override_satisfies_missing_agent_binding():
    registry = _registry()
    binding = _binding("binding_owner_override_missing_agent_assignment_satisfied")

    assert binding["authorized_agent_roles"] == []
    assert binding["authorized_agent_ids"] == []
    assert binding["authorized_consumer_classes"] == []
    assert binding["owner_override_applied"] is True
    assert binding["final_qtt_internal_status"] == "OWNER_OVERRIDE_SATISFIED"
    assert binding["blocks_qtt_when_owner_override_present"] is False

    decision = binding_gate.is_agent_assignment_allowed(
        registry,
        parameter_family="OWNER_OVERRIDE_MISSING_AGENT_ASSIGNMENT_FAMILY",
        agent_role="RUNTIME_RESOLVER_AGENT",
    )
    missing_decision = binding_gate.is_agent_assignment_allowed(
        registry,
        parameter_family="UNREGISTERED_OWNER_OVERRIDE_PARAMETER_FAMILY",
        agent_role="OWNER_APPROVAL_REQUEST_AGENT",
        owner_override_token="OWNER_GLOBAL_OVERRIDE",
    )

    assert decision.allowed is True
    assert missing_decision.allowed is True


def test_missing_binding_blocks_in_normal_mode():
    decision = binding_gate.is_agent_assignment_allowed(
        _registry(),
        parameter_family="UNREGISTERED_NORMAL_MODE_PARAMETER_FAMILY",
        agent_role="OPTIMIZER_AGENT",
    )

    assert decision.allowed is False
    assert decision.reason == "missing binding blocked in normal mode"


def test_binding_registry_is_canonical_source_and_no_per_agent_list_is_required():
    registry = _registry()

    decision = binding_gate.is_agent_assignment_allowed(
        registry,
        parameter_family="RESEARCH_SOURCE_CANDIDATE_FAMILY",
        agent_role="ATOMICROWS_RESEARCH_AGENT",
    )
    blocked = binding_gate.is_agent_assignment_allowed(
        registry,
        parameter_family="OPTIMIZER_CANDIDATE_FAMILY",
        agent_role="ORDER_ROUTER_AGENT",
    )

    assert registry["canonical_source_for_parameter_agent_assignment"] is True
    assert decision.allowed is True
    assert blocked.allowed is False
    assert "agent role is explicitly blocked" in blocked.reason


def test_unknown_agent_consumer_and_lifecycle_values_fail_closed():
    unknown_role = copy.deepcopy(
        _binding("binding_replay_paper_candidate_family_to_replay_and_paper_agents")
    )
    unknown_role["binding_id"] = "synthetic_unknown_role"
    unknown_role["authorized_agent_roles"] = ["UNKNOWN_AGENT_ROLE"]
    role_failures = binding_gate.validate_bindings([unknown_role])

    unknown_consumer = copy.deepcopy(unknown_role)
    unknown_consumer["binding_id"] = "synthetic_unknown_consumer"
    unknown_consumer["authorized_agent_roles"] = ["REPLAY_AGENT"]
    unknown_consumer["authorized_consumer_classes"] = ["UNKNOWN_CONSUMER"]
    consumer_failures = binding_gate.validate_bindings([unknown_consumer])

    unknown_lifecycle = copy.deepcopy(unknown_role)
    unknown_lifecycle["binding_id"] = "synthetic_unknown_lifecycle"
    unknown_lifecycle["authorized_agent_roles"] = ["REPLAY_AGENT"]
    unknown_lifecycle["requires_lifecycle_status_at_least"] = "UNKNOWN_STATUS"
    lifecycle_failures = binding_gate.validate_bindings([unknown_lifecycle])

    _assert_failure_contains(role_failures, "unknown agent role")
    _assert_failure_contains(consumer_failures, "unknown consumer class")
    _assert_failure_contains(lifecycle_failures, "requires_lifecycle_status_at_least")


def test_owner_override_cannot_be_reported_as_blocking():
    binding = copy.deepcopy(
        _binding("binding_owner_override_missing_agent_assignment_satisfied")
    )
    binding["blocks_qtt_when_owner_override_present"] = True

    failures = binding_gate.validate_bindings([binding])

    _assert_failure_contains(failures, "owner override may not block")


def test_no_bundle_hash_or_runtime_live_order_quantum_profit_artifact_is_created():
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert not CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
    assert report["bundle_file_present"] is False
    assert report["bundle_sha_present"] is False
    assert report["real_runtime_artifact_created"] is False
    assert report["real_live_artifact_created"] is False
    assert report["real_order_artifact_created"] is False
    assert report["real_quantum_backend_artifact_created"] is False
    assert report["real_profit_artifact_created"] is False


def test_uses_pr_number_as_authority_remains_false():
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert _registry()["uses_pr_number_as_authority"] is False
    assert report["uses_pr_number_as_authority"] is False
