from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_parameter_agent_binding_command_matrix as gate


REPO_ROOT = Path(".")
SCHEMA = Path(
    "schemas/atomicrows/"
    "atomicrows_parameter_agent_binding_command_matrix.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_parameter_agent_binding_command_matrix.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsParameterAgentBindingCommandMatrix.json"
)
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


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
    assert schema["$defs"]["command_matrix_report"]["required"] == list(
        gate.REPORT_FIELDS
    )
    assert _report() == result.report


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


def test_all_required_commands_are_present_in_canonical_order():
    report = _report()

    assert report["command_count"] == 4
    assert report["required_command_count"] == 4
    assert report["required_commands_present_count"] == 4
    assert report["missing_command_count"] == 0
    assert report["command_order_valid"] is True
    assert [command["command_id"] for command in report["commands"]] == [
        spec.command_id for spec in gate.REQUIRED_COMMANDS
    ]
    assert [command["command_name"] for command in report["commands"]] == [
        spec.command_name for spec in gate.REQUIRED_COMMANDS
    ]
    assert [command["command_order"] for command in report["commands"]] == [1, 2, 3, 4]
    assert [command["command_text"] for command in report["commands"]] == [
        spec.command_text for spec in gate.REQUIRED_COMMANDS
    ]


def test_required_binding_family_commands_are_present():
    command_ids = {command["command_id"] for command in _report()["commands"]}

    assert "QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY" in command_ids
    assert "ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY" in command_ids
    assert "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE" in command_ids
    assert "ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE" in command_ids


def test_tool_schema_and_generated_report_paths_are_valid():
    report = _report()

    assert report["tool_paths_present_count"] == 4
    assert report["missing_tool_path_count"] == 0
    assert report["schema_paths_present_count"] == 4
    assert report["missing_schema_path_count"] == 0
    assert report["generated_report_output_count"] == 4
    assert report["generated_report_paths_under_generated_count"] == 4
    for command in report["commands"]:
        assert command["tool_path_exists"] is True
        assert command["schema_path_exists"] is True
        assert command["generated_report_path_expected"] is True
        assert (
            command["generated_report_path_under_docs_master_plan_generated"] is True
        )
        assert command["generated_report_path"].startswith(
            "docs/master_plan/generated/"
        )


def test_owner_override_is_supported_by_every_command_and_unblocked():
    report = _report()

    assert report["owner_global_override_authority"] is True
    assert report["owner_override_satisfies_all_qtt_internal_requirements"] is True
    assert report["owner_override_supported_command_count"] == 4
    assert report["owner_override_blocked_command_count"] == 0
    assert all(command["owner_override_supported"] is True for command in report["commands"])
    assert all(
        command["owner_override_blocked_by_command"] is False
        for command in report["commands"]
    )
    assert report["validators_block_owner_override_count"] == 0
    assert report["codex_blocks_owner_override_count"] == 0
    assert report["qtt_agents_block_owner_override_count"] == 0
    assert report["generated_reports_block_owner_override_count"] == 0
    assert report["validation_gates_block_owner_override_count"] == 0
    assert report["blocks_qtt_when_owner_override_present"] is False
    assert report["final_qtt_internal_status"] == "OWNER_OVERRIDE_SATISFIED"


def test_quantum_priority_forward_compatibility_is_preserved():
    report = _report()
    commands = {command["command_id"]: command for command in report["commands"]}

    assert report["quantum_priority_forward_compatible"] is True
    assert report["quantum_backend_binding_command_covered"] is True
    assert report["quantum_backend_consumer_gate_command_covered"] is True
    assert report["quantum_backend_artifact_created"] is False
    assert (
        report["owner_quantum_priority_policy_forward_reference"]
        == gate.OWNER_QUANTUM_PRIORITY_POLICY_FORWARD_REFERENCE
    )
    assert report["owner_can_force_quantum_priority_in_future_selection_layers"] is True
    assert (
        commands["ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY"][
            "quantum_backend_surface_covered"
        ]
        is True
    )
    assert (
        commands["ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE"][
            "quantum_backend_surface_covered"
        ]
        is True
    )


def test_no_runtime_live_order_quantum_or_profit_artifacts_are_created():
    report = _report()

    assert report["forbidden_runtime_artifact_command_count"] == 0
    assert report["forbidden_live_artifact_command_count"] == 0
    assert report["forbidden_order_artifact_command_count"] == 0
    assert report["forbidden_quantum_backend_artifact_command_count"] == 0
    assert report["forbidden_profit_artifact_command_count"] == 0
    for command in report["commands"]:
        assert command["command_creates_runtime_artifact"] is False
        assert command["command_creates_live_artifact"] is False
        assert command["command_creates_order_artifact"] is False
        assert command["command_creates_quantum_backend_artifact"] is False
        assert command["command_creates_profit_artifact"] is False


def test_no_source_connector_private_secret_repo_or_package_artifacts_are_created():
    report = _report()

    assert report["forbidden_source_acceptance_command_count"] == 0
    assert report["forbidden_connector_binding_command_count"] == 0
    assert report["forbidden_private_state_fetch_command_count"] == 0
    assert report["forbidden_secret_materialization_command_count"] == 0
    assert report["forbidden_external_repo_clone_command_count"] == 0
    assert report["forbidden_package_install_command_count"] == 0
    for command in report["commands"]:
        assert command["command_creates_source_acceptance_artifact"] is False
        assert command["command_creates_connector_binding_artifact"] is False
        assert command["command_fetches_private_state"] is False
        assert command["command_materializes_secret"] is False
        assert command["command_clones_external_repo"] is False
        assert command["command_installs_package"] is False


def test_no_atomicrows_bundle_or_hash_is_created():
    report = _report()

    assert not CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
    assert report["forbidden_bundle_command_count"] == 0
    assert report["forbidden_bundle_sha_command_count"] == 0
    for command in report["commands"]:
        assert command["command_creates_atomicrows_bundle"] is False
        assert command["command_creates_atomicrows_bundle_sha"] is False


def test_pr_number_authority_and_authority_boundary_remain_false():
    report = _report()

    assert report["uses_pr_number_as_authority"] is False
    assert report["authority_boundary_all_false"] is True
    assert all(
        command["command_uses_pr_number_as_authority"] is False
        for command in report["commands"]
    )
    assert all(
        command["command_uses_wall_clock_time"] is False for command in report["commands"]
    )


def test_static_and_qtt_internal_readiness_are_owner_override_satisfied():
    report = _report()

    assert report["static_command_matrix_ready"] is True
    assert report["qtt_internal_command_matrix_ready"] is True
    assert report["final_ready"] is False
    assert report["final_qtt_internal_status"] == "OWNER_OVERRIDE_SATISFIED"


def test_dev_mode_passes_but_final_mode_remains_incomplete():
    dev = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )
    final = gate.validate(
        mode="final",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert dev.failures == ()
    assert final.ok is False
    _assert_failure_contains(final.failures, "final mode incomplete")


def test_command_order_is_fail_closed():
    fixture = _fixture()
    fixture["commands"][1], fixture["commands"][2] = (
        fixture["commands"][2],
        fixture["commands"][1],
    )

    report = gate.build_report(repo_root=REPO_ROOT, fixture=fixture)
    failures = gate._report_safety_failures(report)

    assert report["command_order_valid"] is False
    _assert_failure_contains(failures, "command_order_valid")


def test_owner_override_blocking_is_fail_closed():
    fixture = copy.deepcopy(_fixture())
    fixture["commands"][0]["owner_override_blocked_by_command"] = True

    report = gate.build_report(repo_root=REPO_ROOT, fixture=fixture)
    failures = gate._report_safety_failures(report)

    assert report["owner_override_blocked_command_count"] == 1
    assert report["authority_boundary_all_false"] is False
    _assert_failure_contains(failures, "owner_override_blocked_command_count")


def test_forbidden_artifact_flags_are_fail_closed():
    fixture = copy.deepcopy(_fixture())
    fixture["commands"][0]["command_creates_runtime_artifact"] = True
    fixture["commands"][1]["command_creates_live_artifact"] = True
    fixture["commands"][2]["command_creates_order_artifact"] = True
    fixture["commands"][2]["command_creates_quantum_backend_artifact"] = True
    fixture["commands"][3]["command_creates_profit_artifact"] = True

    report = gate.build_report(repo_root=REPO_ROOT, fixture=fixture)
    failures = gate._report_safety_failures(report)

    assert report["forbidden_runtime_artifact_command_count"] == 1
    assert report["forbidden_live_artifact_command_count"] == 1
    assert report["forbidden_order_artifact_command_count"] == 1
    assert report["forbidden_quantum_backend_artifact_command_count"] == 1
    assert report["forbidden_profit_artifact_command_count"] == 1
    assert report["quantum_backend_artifact_created"] is True
    assert report["authority_boundary_all_false"] is False
    _assert_failure_contains(failures, "forbidden_runtime_artifact_command_count")
    _assert_failure_contains(failures, "quantum_backend_artifact_created")
