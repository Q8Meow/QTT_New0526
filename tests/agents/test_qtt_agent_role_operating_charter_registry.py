from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_qtt_agent_role_operating_charter_registry as gate


REPO_ROOT = Path(".")
SCHEMA = Path("schemas/agents/qtt_agent_role_operating_charter_registry.schema.json")
REGISTRY = Path("docs/master_plan/agents/QTTAgentRoleOperatingCharterRegistry.yaml")
FIXTURE = Path(
    "tests/fixtures/agents/"
    "synthetic_qtt_agent_role_operating_charter_registry.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/QTTAgentRoleOperatingCharterReport.json")
MASTER_PLAN = Path("docs/master_plan/QTT_MasterPlan_Current.md")
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _registry() -> dict:
    return gate.load_registry(REGISTRY)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_exists_and_is_valid_json():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(gate.TOP_FIELDS)
    assert schema["$defs"]["agent_role"]["enum"] == list(gate.ROLE_ORDER)
    assert schema["$defs"]["agent_role_id"]["enum"] == [
        gate.ROLE_IDS[role] for role in gate.ROLE_ORDER
    ]
    assert schema["$defs"]["agent_charter"]["required"] == list(gate.CHARTER_FIELDS)
    assert schema["$defs"]["agent_role_operating_charter_report"]["required"] == list(
        gate.REPORT_FIELDS
    )


def test_registry_fixture_and_report_validate():
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        registry_path=REGISTRY,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert _report() == result.report


def test_report_has_expected_static_values():
    report = _report()

    assert report["report_type"] == gate.REPORT_TYPE
    assert report["deterministic_output"] is True
    assert report["generated_at_utc"] == gate.DETERMINISTIC_GENERATED_AT
    assert report["source_of_role_substance"] == gate.MASTER_PLAN.as_posix()
    assert report["master_plan_followed_as_controlling_doctrine"] is True
    assert report["existing_pr_patterns_used_for_style_only"] is True
    assert report["pr64_is_scope_boundary_not_role_authority"] is True
    assert report["architecture_emphasis"] == gate.ARCHITECTURE_EMPHASIS
    assert report["agent_role_count"] == 25
    assert report["required_agent_role_count"] == 25
    assert report["required_agent_roles_present_count"] == 25
    assert report["missing_agent_role_count"] == 0
    assert report["final_ready"] is False


def test_exact_role_order_and_ids():
    roles = _registry()["agent_charters"]
    fixture_roles = _fixture()["agent_charters"]

    assert [role["agent_role"] for role in roles] == list(gate.ROLE_ORDER)
    assert [role["agent_role_id"] for role in roles] == [
        gate.ROLE_IDS[role] for role in gate.ROLE_ORDER
    ]
    assert [role["agent_role"] for role in fixture_roles] == list(gate.ROLE_ORDER)
    assert [role["agent_role_id"] for role in fixture_roles] == [
        gate.ROLE_IDS[role] for role in gate.ROLE_ORDER
    ]
    assert len({role["agent_role"] for role in roles}) == 25
    assert len({role["agent_role_id"] for role in roles}) == 25


def test_every_role_has_required_operational_content_and_relationships():
    for role in _registry()["agent_charters"]:
        assert role["master_plan_doctrine_terms_used"]
        assert role["master_plan_role_derivation_summary"]
        assert role["master_plan_static_authority_basis"]
        assert role["master_plan_runtime_boundary_basis"]
        assert role["primary_duties"]
        assert role["owned_surfaces"]
        assert role["consumed_artifacts"]
        assert role["emitted_artifacts"]
        assert role["handoff_inputs"]
        assert role["handoff_outputs"]
        assert role["input_packet_types"]
        assert role["output_packet_types"]
        assert role["applicable_parameter_family_scopes"]
        assert role["applicable_algorithm_family_scopes"]
        assert role["authorized_consumer_classes"]
        assert role["optimizer_arbitration_relationship"]
        for field in gate.RELATIONSHIP_FIELDS:
            assert role[field]
        affirmative = sum(
            len(role[field])
            for field in (
                "primary_duties",
                "secondary_duties",
                "owned_surfaces",
                "consumed_artifacts",
                "emitted_artifacts",
                "handoff_inputs",
                "handoff_outputs",
            )
        )
        assert affirmative > len(role["forbidden_decision_authority"])


def test_quantum_forward_fields_are_present_without_evidence_claims():
    registry = _registry()
    report = _report()

    assert registry["quantum_forward_design_supported"] is True
    assert registry["quantum_evidence_claim_created"] is False
    assert report["quantum_forward_design_supported"] is True
    assert report["quantum_evidence_claim_created"] is False
    assert report["owner_can_force_quantum_priority_count"] >= 8
    for role in registry["agent_charters"]:
        assert role["quantum_scope"]
        assert role["classical_scope"]
        assert role["quantum_applicability_scope"]
        assert role["quantum_algorithm_family_access"]
        assert role["quantum_parameter_family_access"]
        assert role["quantum_priority_forward_compatible"] is True
        assert role["owner_quantum_priority_supported"] is True
        assert role["quantum_backend_artifact_created"] is False
        assert role["quantum_runtime_authority_created"] is False
        assert role["true_quantum_execution_created"] is False
        assert role["quantum_evidence_claim_created"] is False
    optimizer = registry["agent_charters"][12]
    assert optimizer["agent_role"] == "OPTIMIZER_AGENT"
    assert set(gate.QUANTUM_COMPATIBILITY_CLASSES).issubset(
        optimizer["quantum_applicability_scope"]
    )


def test_owner_authority_boundary_is_preserved_for_every_agent():
    report = _report()

    assert report["agents_with_owner_override_supported_count"] == 25
    assert report["agents_block_owner_override_count"] == 0
    assert report["agents_may_approve_for_owner_count"] == 0
    assert report["codex_may_approve_for_owner_count"] == 0
    assert report["chatgpt_may_approve_for_owner_count"] == 0
    assert report["qtt_agent_authority_over_owner_count"] == 0
    for role in _registry()["agent_charters"]:
        assert role["owner_override_supported"] is True
        assert (
            role["owner_override_satisfaction_basis"]
            == gate.OWNER_OVERRIDE_SATISFACTION_BASIS
        )
        assert role["may_approve_for_owner"] is False
        assert role["codex_may_approve_for_owner"] is False
        assert role["chatgpt_may_approve_for_owner"] is False
        assert role["qtt_agent_authority_over_owner"] is False
        assert role["blocks_qtt_when_owner_override_present"] is False


def test_no_runtime_live_order_source_connector_replay_paper_profit_or_backend_artifacts():
    registry = _registry()
    report = _report()
    false_fields = (
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "profit_artifact_created",
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
    assert report["authority_boundary_all_false"] is True


def test_master_plan_is_unchanged():
    assert MASTER_PLAN.exists()
    assert gate._master_plan_has_no_diff(REPO_ROOT.resolve()) == []


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
            "--out",
            str(REPORT),
        ]
    )

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_owner_approval_boundary_is_fail_closed():
    registry = copy.deepcopy(_registry())
    registry["agent_charters"][0]["may_approve_for_owner"] = True

    failures = gate._validate_charters(registry, label="registry")

    _assert_failure_contains(failures, "may_approve_for_owner must be false")


def test_artifact_flags_are_fail_closed():
    registry = copy.deepcopy(_registry())
    registry["runtime_artifact_created"] = True

    report = gate.build_report(registry)
    failures = gate._report_safety_failures(report)

    assert report["runtime_artifact_created"] is True
    assert report["authority_boundary_all_false"] is False
    _assert_failure_contains(failures, "runtime_artifact_created")
