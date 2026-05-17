from __future__ import annotations

import json
from pathlib import Path

from tools import (
    validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate as gate,
)


REPO_ROOT = Path(".")
SCHEMA = Path(
    "schemas/atomicrows/"
    "atomicrows_parameter_agent_binding_cumulative_readiness_gate.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_parameter_agent_binding_cumulative_readiness_gate.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/"
    "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
)
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _fixture_expected_report() -> dict:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return fixture["expected_report"]


def test_schema_exists_and_validates_generated_report():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["cumulative_readiness_report"]["required"] == list(
        gate.REPORT_FIELDS
    )
    assert _report() == result.report == _fixture_expected_report()


def test_validator_produces_deterministic_report():
    first = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    second = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert first.failures == ()
    assert second.failures == ()
    assert first.report == second.report == _report()
    assert gate.serialize_report(first.report or {}) == gate.serialize_report(
        second.report or {}
    )


def test_required_upstream_artifacts_are_present_and_consumed():
    report = _report()

    assert report["upstream_artifact_count"] >= 7
    assert report["upstream_artifacts_present_count"] == report["upstream_artifact_count"]
    assert report["upstream_artifacts_missing_count"] == 0
    assert report["registry_present"] is True
    assert report["registry_schema_present"] is True
    assert report["registry_report_present"] is True
    assert report["consumer_gate_schema_present"] is True
    assert report["consumer_gate_report_present"] is True
    assert report["owner_global_override_report_present"] is True


def test_binding_registry_report_counts_are_imported():
    report = _report()

    assert report["registry_binding_count"] >= 13
    assert report["registry_owner_approved_binding_count"] >= 7
    assert report["registry_owner_global_override_binding_count"] >= 4
    assert report["registry_owner_override_satisfied_binding_count"] >= 4
    assert report["registry_missing_binding_owner_override_satisfied_count"] >= 1
    assert report["registry_runtime_binding_count"] == 1
    assert report["registry_live_binding_count"] == 1
    assert report["registry_quantum_backend_binding_count"] == 1
    assert report["registry_final_ready"] is False


def test_binding_consumer_gate_report_counts_are_imported():
    report = _report()

    assert report["consumer_attempted_access_count"] >= 38
    assert report["consumer_allowed_access_count"] >= 28
    assert report["consumer_blocked_access_count"] >= 10
    assert report["consumer_invalid_access_count"] == 0
    assert report["consumer_owner_override_attempt_count"] >= 12
    assert report["consumer_owner_override_allowed_count"] >= 12
    assert report["consumer_owner_override_blocked_count"] == 0
    assert report["consumer_allowed_by_owner_global_override_count"] >= 7
    assert report["consumer_allowed_by_agent_assignment_owner_approved_count"] >= 1
    assert report["consumer_allowed_by_owner_override_satisfied_count"] >= 4
    assert report["consumer_missing_binding_owner_override_satisfied_count"] >= 1
    assert (
        report["consumer_unauthorized_agent_role_owner_override_satisfied_count"] >= 1
    )
    assert report["consumer_unauthorized_agent_id_owner_override_satisfied_count"] >= 1
    assert (
        report["consumer_unauthorized_consumer_class_owner_override_satisfied_count"]
        >= 1
    )
    assert report["consumer_scope_mismatch_owner_override_satisfied_count"] >= 1
    assert report["consumer_unknown_parameter_target_owner_override_satisfied_count"] >= 1


def test_owner_global_override_report_is_consumed_and_nonblocking():
    report = _report()

    assert report["owner_global_override_authority"] is True
    assert report["owner_override_satisfies_all_qtt_internal_requirements"] is True
    assert report["owner_override_satisfies_binding_readiness"] is True
    assert report["owner_override_blocked_count"] == 0
    assert report["validators_block_owner_override_count"] == 0
    assert report["codex_blocks_owner_override_count"] == 0
    assert report["qtt_agents_block_owner_override_count"] == 0
    assert report["generated_reports_block_owner_override_count"] == 0
    assert report["validation_gates_block_owner_override_count"] == 0


def test_owner_override_satisfies_internal_readiness_while_normal_readiness_is_incomplete():
    report = _report()

    assert report["static_binding_foundation_ready"] is True
    assert report["normal_full_binding_coverage_ready"] is False
    assert report["owner_override_satisfies_binding_readiness"] is True
    assert report["qtt_internal_binding_cumulative_ready"] is True
    assert report["final_qtt_internal_status"] == "OWNER_OVERRIDE_SATISFIED"
    assert report["cumulative_ready_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert report["final_ready"] is False
    assert report["blocks_qtt_when_owner_override_present"] is False


def test_final_ready_false_does_not_block_owner_override():
    report = _report()

    assert report["final_ready"] is False
    assert report["normal_full_binding_coverage_ready"] is False
    assert report["owner_override_satisfies_binding_readiness"] is True
    assert report["qtt_internal_binding_cumulative_ready"] is True
    assert report["blocks_qtt_when_owner_override_present"] is False


def test_no_forbidden_runtime_live_order_quantum_or_profit_artifacts_are_created():
    report = _report()

    assert report["real_runtime_artifact_created"] is False
    assert report["real_live_artifact_created"] is False
    assert report["real_order_artifact_created"] is False
    assert report["real_quantum_backend_artifact_created"] is False
    assert report["real_profit_artifact_created"] is False


def test_no_source_acceptance_connector_private_secret_external_or_package_artifacts():
    report = _report()

    assert report["source_acceptance_artifact_created"] is False
    assert report["connector_binding_artifact_created"] is False
    assert report["private_state_fetch_created"] is False
    assert report["secret_materialization_created"] is False
    assert report["external_repo_clone_created"] is False
    assert report["package_install_created"] is False


def test_no_atomicrows_bundle_or_hash_is_created():
    report = _report()

    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
    assert report["bundle_file_present"] is True
    assert report["bundle_sha_present"] is False


def test_authority_boundary_and_pr_number_authority_remain_false():
    report = _report()

    assert report["uses_pr_number_as_authority"] is False
    assert report["authority_boundary_all_false"] is True
