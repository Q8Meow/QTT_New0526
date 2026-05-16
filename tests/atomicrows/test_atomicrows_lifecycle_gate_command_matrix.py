from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_lifecycle_gate_command_matrix as gate


REPO_ROOT = Path(".")
SCHEMA = Path("schemas/atomicrows/atomicrows_lifecycle_gate_command_matrix.schema.json")
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_lifecycle_gate_command_matrix.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/AtomicRowsLifecycleGateCommandMatrix.json")
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_declares_command_matrix_report_fields_and_required_commands():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    fixture = _fixture()
    report_schema = schema["$defs"]["command_matrix_report"]

    assert schema["additionalProperties"] is False
    assert report_schema["required"] == list(gate._empty_report())
    assert report_schema["properties"]["report_type"]["const"] == gate.REPORT_TYPE
    assert fixture["commands"] == [
        {
            **command,
            "authority_boundary": {
                field: False for field in gate.AUTHORITY_BOUNDARY_FIELDS
            },
        }
        for command in fixture["commands"]
    ]
    assert [command["command"] for command in fixture["commands"]] == [
        spec.command for spec in gate.REQUIRED_COMMANDS
    ]


def test_fixture_report_is_deterministic_and_has_expected_counts():
    first = gate.build_report(repo_root=REPO_ROOT, fixture=_fixture())
    second = gate.build_report(repo_root=REPO_ROOT, fixture=_fixture())

    assert first == second
    assert gate.serialize_report(first) == gate.serialize_report(second)
    assert first == json.loads(REPORT.read_text(encoding="utf-8"))
    assert first["command_count"] == 6
    assert first["required_command_count"] == 6
    assert first["required_commands_present_count"] == 6
    assert first["missing_command_count"] == 0
    assert first["command_order_valid"] is True
    assert first["tool_paths_present_count"] == 6
    assert first["missing_tool_path_count"] == 0
    assert first["generated_report_output_count"] == 5
    assert first["forbidden_bundle_command_count"] == 0
    assert first["forbidden_bundle_sha_command_count"] == 0
    assert first["forbidden_runtime_authority_command_count"] == 0
    assert first["forbidden_live_authority_command_count"] == 0
    assert first["forbidden_source_acceptance_command_count"] == 0
    assert first["forbidden_connector_binding_command_count"] == 0
    assert first["forbidden_order_authority_command_count"] == 0
    assert first["forbidden_profit_claim_command_count"] == 0
    assert first["uses_pr_number_as_authority"] is False
    assert first["cumulative_ready"] is False
    assert first["final_ready"] is False
    assert first["authority_boundary_all_false"] is True


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
    fixture["commands"][2], fixture["commands"][3] = (
        fixture["commands"][3],
        fixture["commands"][2],
    )

    report = gate.build_report(repo_root=REPO_ROOT, fixture=fixture)
    failures = gate._report_safety_failures(report)

    assert report["command_order_valid"] is False
    _assert_failure_contains(failures, "command_order_valid")


def test_missing_tool_path_is_fail_closed():
    fixture = _fixture()
    fixture["commands"][0]["tool_path"] = "tools/missing_atomicrows_gate.py"

    report = gate.build_report(repo_root=REPO_ROOT, fixture=fixture)
    failures = gate._report_safety_failures(report)

    assert report["missing_tool_path_count"] == 1
    _assert_failure_contains(failures, "missing_tool_path_count")


def test_forbidden_bundle_or_hash_target_is_fail_closed():
    bundle_fixture = _fixture()
    bundle_fixture["commands"][0]["generated_report_path"] = (
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
    )
    sha_fixture = _fixture()
    sha_fixture["commands"][0]["generated_report_path"] = (
        "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
    )

    bundle_report = gate.build_report(repo_root=REPO_ROOT, fixture=bundle_fixture)
    sha_report = gate.build_report(repo_root=REPO_ROOT, fixture=sha_fixture)

    assert bundle_report["forbidden_bundle_command_count"] == 1
    assert sha_report["forbidden_bundle_sha_command_count"] == 1


def test_forbidden_authority_flags_are_fail_closed():
    fixture = copy.deepcopy(_fixture())
    fixture["commands"][1]["authority_boundary"]["creates_runtime_authority"] = True
    fixture["commands"][2]["authority_boundary"]["creates_live_reachability"] = True
    fixture["commands"][3]["authority_boundary"]["creates_source_acceptance"] = True
    fixture["commands"][4]["authority_boundary"]["creates_connector_binding"] = True
    fixture["commands"][5]["authority_boundary"]["creates_order_authority"] = True
    fixture["commands"][5]["authority_boundary"]["creates_profit_claim"] = True

    report = gate.build_report(repo_root=REPO_ROOT, fixture=fixture)
    failures = gate._report_safety_failures(report)

    assert report["forbidden_runtime_authority_command_count"] == 1
    assert report["forbidden_live_authority_command_count"] == 1
    assert report["forbidden_source_acceptance_command_count"] == 1
    assert report["forbidden_connector_binding_command_count"] == 1
    assert report["forbidden_order_authority_command_count"] == 1
    assert report["forbidden_profit_claim_command_count"] == 1
    assert report["authority_boundary_all_false"] is False
    _assert_failure_contains(failures, "forbidden_runtime_authority_command_count")
    _assert_failure_contains(failures, "authority_boundary_all_false")


def test_pr_number_authority_is_fail_closed():
    fixture = _fixture()
    fixture["commands"][0]["command_name"] = "build_parameter_lifecycle_report_pr999"

    report = gate.build_report(repo_root=REPO_ROOT, fixture=fixture)
    failures = gate._report_safety_failures(report)

    assert report["uses_pr_number_as_authority"] is True
    _assert_failure_contains(failures, "uses_pr_number_as_authority")


def test_command_matrix_does_not_create_atomicrows_bundle_or_hash():
    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()

    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert result.failures == ()
    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
