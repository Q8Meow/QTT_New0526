from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_qtt_algorithm_formula_family_registry as gate


REPO_ROOT = Path(".")
SCHEMA = Path("schemas/algorithms/qtt_algorithm_formula_family_registry.schema.json")
REGISTRY = Path("docs/master_plan/algorithms/QTTAlgorithmFormulaFamilyRegistry.yaml")
FIXTURE = Path(
    "tests/fixtures/algorithms/"
    "synthetic_qtt_algorithm_formula_family_registry.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/QTTAlgorithmFormulaFamilyReport.json")
AGENT_REGISTRY = Path("docs/master_plan/agents/QTTAgentRoleOperatingCharterRegistry.yaml")
MASTER_PLAN = Path("docs/master_plan/QTT_MasterPlan_Current.md")
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _registry() -> dict:
    return gate.load_registry(REGISTRY)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _agent_roles() -> set[str]:
    roles, failures = gate._load_agent_roles(AGENT_REGISTRY)
    assert failures == []
    return roles


def _assert_failure_contains(failures: tuple[str, ...] | list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_exists_and_is_valid_json():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(gate.TOP_FIELDS)
    assert schema["$defs"]["algorithm_family"]["required"] == list(gate.FAMILY_FIELDS)
    assert schema["$defs"]["algorithm_family_id"]["enum"] == [
        gate.FAMILY_IDS[name] for name in gate.FAMILY_ORDER
    ]
    assert schema["$defs"]["algorithm_family_name"]["enum"] == list(gate.FAMILY_ORDER)
    assert schema["$defs"]["agent_role"]["enum"] == list(gate.AGENT_ROLE_ORDER)
    assert schema["$defs"]["algorithm_formula_family_report"]["required"] == list(
        gate.REPORT_FIELDS
    )


def test_registry_fixture_and_report_validate():
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        registry_path=REGISTRY,
        fixture_path=FIXTURE,
        agent_registry_path=AGENT_REGISTRY,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert _report() == result.report


def test_report_has_expected_static_values():
    report = _report()

    assert report["report_type"] == gate.REPORT_TYPE
    assert report["deterministic_output"] is True
    assert report["generated_at_utc"] == gate.DETERMINISTIC_GENERATED_AT
    assert report["source_of_family_substance"] == gate.MASTER_PLAN.as_posix()
    assert report["agent_charter_registry_dependency"] == gate.AGENT_CHARTER_REGISTRY.as_posix()
    assert report["master_plan_followed_as_controlling_doctrine"] is True
    assert report["agent_charter_registry_used_for_role_validation"] is True
    assert report["existing_pr_patterns_used_for_style_only"] is True
    assert report["pr65_is_scope_boundary_not_algorithm_authority"] is True
    assert report["architecture_emphasis"] == gate.ARCHITECTURE_EMPHASIS
    assert report["algorithm_family_count"] == 15
    assert report["required_algorithm_family_count"] == 15
    assert report["required_algorithm_families_present_count"] == 15
    assert report["missing_algorithm_family_count"] == 0
    assert report["classical_algorithm_family_count"] == 6
    assert report["quantum_or_quantum_compatible_algorithm_family_count"] == 9
    assert report["final_ready"] is False


def test_exact_family_order_and_ids():
    registry_families = _registry()["algorithm_families"]
    fixture_families = _fixture()["algorithm_families"]

    assert [family["algorithm_family_name"] for family in registry_families] == list(
        gate.FAMILY_ORDER
    )
    assert [family["algorithm_family_id"] for family in registry_families] == [
        gate.FAMILY_IDS[name] for name in gate.FAMILY_ORDER
    ]
    assert [family["algorithm_family_name"] for family in fixture_families] == list(
        gate.FAMILY_ORDER
    )
    assert [family["algorithm_family_id"] for family in fixture_families] == [
        gate.FAMILY_IDS[name] for name in gate.FAMILY_ORDER
    ]
    assert len({family["algorithm_family_id"] for family in registry_families}) == 15
    assert len({family["algorithm_family_name"] for family in registry_families}) == 15


def test_classical_and_quantum_family_sets_exist():
    families = {family["algorithm_family_name"]: family for family in _registry()["algorithm_families"]}

    for name in gate.CLASSICAL_FAMILY_NAMES:
        assert families[name]["classical_or_quantum"] == "CLASSICAL"
    for name in gate.QUANTUM_OR_COMPATIBLE_FAMILY_NAMES:
        assert families[name]["classical_or_quantum"] != "CLASSICAL"


def test_every_family_has_formula_policy_inputs_outputs_and_context():
    for family in _registry()["algorithm_families"]:
        assert family["formula_class"]
        assert family["formula_expression_profile"].startswith("SYMBOLIC_")
        assert family["formula_default_policy"] == gate.FORMULA_DEFAULT_POLICY
        assert family["formula_value_range_policy"] == gate.FORMULA_VALUE_RANGE_POLICY
        assert family["authorized_agent_roles"]
        assert family["input_parameter_families"]
        assert family["output_signal_type"]
        assert family["output_artifact_types"]
        assert family["trade_context_applicability"]
        assert family["optimizer_compatibility"]
        assert family["quantum_applicability"]
        assert family["deterministic_selection_role"]
        assert family["scoring_ranking_role"]
        assert family["quantum_classical_arbitration_role"]
        assert family["master_plan_doctrine_terms_used"]
        assert family["master_plan_family_derivation_summary"]


def test_authorized_agent_roles_exist_in_agent_charter_registry():
    roles = _agent_roles()

    for family in _registry()["algorithm_families"]:
        assert set(family["authorized_agent_roles"]).issubset(roles)
        assert family["agent_charter_roles_validated"] == family["authorized_agent_roles"]


def test_quantum_forward_fields_are_present_without_evidence_claims():
    registry = _registry()
    report = _report()

    assert registry["quantum_forward_design_supported"] is True
    assert registry["quantum_evidence_claim_created"] is False
    assert registry["alpha_evidence_claim_created"] is False
    assert registry["profit_evidence_claim_created"] is False
    assert registry["latency_superiority_evidence_claim_created"] is False
    assert registry["execution_superiority_evidence_claim_created"] is False
    assert report["quantum_forward_design_supported"] is True
    assert report["quantum_evidence_claim_created"] is False
    assert report["alpha_evidence_claim_created"] is False
    assert report["profit_evidence_claim_created"] is False
    assert report["latency_superiority_evidence_claim_created"] is False
    assert report["execution_superiority_evidence_claim_created"] is False


def test_quantum_and_hybrid_families_require_comparator_fallback_and_evidence():
    for family in _registry()["algorithm_families"]:
        if family["algorithm_family_name"] in gate.QUANTUM_OR_COMPATIBLE_FAMILY_NAMES:
            assert family["strongest_classical_comparator_required"] is True
            assert family["fallback_bundle_required"] is True
            assert family["replay_paper_evidence_required_before_advantage_claim"] is True
            assert family["owner_quantum_priority_supported"] is True
            assert family["owner_can_force_quantum_priority"] is True
        assert family["live_evidence_required_before_profit_claim"] is True


def test_owner_override_support_is_present_for_all_families():
    report = _report()

    assert report["families_with_owner_override_supported_count"] == 15
    assert report["owner_quantum_priority_supported_count"] >= 9
    assert report["owner_can_force_quantum_priority_count"] >= 9
    for family in _registry()["algorithm_families"]:
        assert family["owner_override_supported"] is True
        assert (
            family["owner_override_satisfaction_basis"]
            == gate.OWNER_OVERRIDE_SATISFACTION_BASIS
        )
        assert family["agent_binding_required_before_consumption"] is True
        assert family["consumer_gate_required_before_consumption"] is True


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
        "bundle_file_present",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "agent_algorithm_binding_created",
        "agent_algorithm_consumer_gate_created",
        "final_ready",
    )

    assert not CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
    for field in false_fields:
        assert registry[field] is False
        assert report[field] is False
    assert report["profit_evidence_claim_created"] is False
    assert report["authority_boundary_all_false"] is True
    for family in registry["algorithm_families"]:
        assert family["runtime_live_order_authority_created"] is False
        assert family["direct_order_submission_allowed"] is False
        assert family["execution_router_required_for_live_order_path"] is True


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
            "--agent-registry",
            str(AGENT_REGISTRY),
            "--out",
            str(REPORT),
        ]
    )

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_unknown_authorized_agent_role_is_fail_closed():
    registry = copy.deepcopy(_registry())
    registry["algorithm_families"][0]["authorized_agent_roles"] = ["NOT_A_QTT_AGENT"]
    registry["algorithm_families"][0]["agent_charter_roles_validated"] = ["NOT_A_QTT_AGENT"]

    failures = gate._validate_families(
        registry,
        label="registry",
        agent_roles=_agent_roles(),
    )

    _assert_failure_contains(failures, "unknown role NOT_A_QTT_AGENT")


def test_artifact_flags_are_fail_closed():
    registry = copy.deepcopy(_registry())
    registry["runtime_artifact_created"] = True

    report = gate.build_report(registry, agent_roles=_agent_roles(), repo_root=REPO_ROOT)
    failures = gate._report_safety_failures(report)

    assert report["runtime_artifact_created"] is True
    assert report["authority_boundary_all_false"] is False
    _assert_failure_contains(failures, "runtime_artifact_created")
