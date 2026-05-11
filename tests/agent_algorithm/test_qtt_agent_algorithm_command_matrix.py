from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_qtt_agent_algorithm_command_matrix as gate


REPO_ROOT = Path(".")
SCHEMA = Path(
    "schemas/agent_algorithm/qtt_agent_algorithm_command_matrix.schema.json"
)
MATRIX = Path("docs/master_plan/agent_algorithm/QTTAgentAlgorithmCommandMatrix.yaml")
FIXTURE = Path(
    "tests/fixtures/agent_algorithm/"
    "synthetic_qtt_agent_algorithm_command_matrix.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/QTTAgentAlgorithmCommandMatrix.json")


def _matrix() -> dict:
    return gate.load_matrix(MATRIX)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _failures_for_matrix(matrix: dict) -> list[str]:
    report = gate.build_report(repo_root=REPO_ROOT, matrix=matrix)
    return [
        *gate._validate_matrix_shape(
            repo_root=REPO_ROOT.resolve(),
            matrix=matrix,
            label="test_matrix",
            schema=None,
        ),
        *gate._report_safety_failures(report),
    ]


def test_valid_matrix_passes_and_generated_report_matches():
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        matrix_path=MATRIX,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert result.report == _report()
    assert _fixture() == _matrix()


def test_schema_is_fail_closed_for_matrix_and_report_surfaces():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert schema["required"] == list(gate.ROOT_FIELDS)
    assert schema["properties"]["commands"]["minItems"] == 8
    assert schema["properties"]["commands"]["maxItems"] == 8
    assert schema["$defs"]["command_id"]["enum"] == [
        spec.command_id for spec in gate.REQUIRED_COMMANDS
    ]
    assert schema["$defs"]["command"]["required"] == list(
        gate.COMMAND_SCHEMA_REQUIRED_FIELDS
    )
    assert schema["$defs"]["command_matrix_report"]["required"] == list(
        gate.REPORT_FIELDS
    )


def test_generated_report_has_deterministic_fields_and_expected_counts():
    report = _report()

    assert report["report_type"] == gate.REPORT_TYPE
    assert report["deterministic_output"] is True
    assert report["generated_at_utc"] == gate.DETERMINISTIC_GENERATED_AT
    assert report["source_of_command_matrix_substance"] == (
        "docs/master_plan/QTT_MasterPlan_Current.md"
    )
    assert report["command_matrix_type"] == gate.COMMAND_MATRIX_TYPE
    assert report["command_count"] == 8
    assert report["required_command_count"] == 8
    assert report["required_commands_present_count"] == 8
    assert report["missing_command_count"] == 0
    assert report["invalid_command_order_count"] == 0
    assert report["commands_with_tool_path_count"] == 7
    assert report["commands_with_success_marker_count"] == 7
    assert report["command_ids"] == [spec.command_id for spec in gate.REQUIRED_COMMANDS]


def test_exact_8_command_order_is_enforced():
    matrix = _matrix()
    commands = matrix["commands"]

    assert len(commands) == 8
    assert [command["command_id"] for command in commands] == [
        spec.command_id for spec in gate.REQUIRED_COMMANDS
    ]
    assert [command["ordinal"] for command in commands] == list(range(1, 9))

    too_short = copy.deepcopy(matrix)
    too_short["commands"] = too_short["commands"][:-1]
    _assert_failure_contains(_failures_for_matrix(too_short), "command_count")


def test_missing_owner_override_command_fails():
    matrix = copy.deepcopy(_matrix())
    matrix["commands"].pop(0)

    failures = _failures_for_matrix(matrix)

    _assert_failure_contains(failures, "owner_global_override_command_present")
    _assert_failure_contains(failures, "missing_command_count")


def test_swapped_command_order_fails():
    matrix = copy.deepcopy(_matrix())
    matrix["commands"][1], matrix["commands"][2] = (
        matrix["commands"][2],
        matrix["commands"][1],
    )

    _assert_failure_contains(_failures_for_matrix(matrix), "invalid_command_order_count")


def test_missing_tool_path_on_commands_1_through_7_fails():
    for index in range(7):
        matrix = copy.deepcopy(_matrix())
        del matrix["commands"][index]["tool_path"]

        failures = _failures_for_matrix(matrix)

        _assert_failure_contains(failures, "tool_path")


def test_missing_success_marker_on_commands_1_through_7_fails():
    for index in range(7):
        matrix = copy.deepcopy(_matrix())
        del matrix["commands"][index]["success_marker"]

        failures = _failures_for_matrix(matrix)

        _assert_failure_contains(failures, "success_marker")


def test_command_8_must_be_owner_manual_sequence():
    matrix = copy.deepcopy(_matrix())
    matrix["commands"][7]["command_type"] = "VALIDATOR"

    _assert_failure_contains(
        _failures_for_matrix(matrix),
        "OWNER_MANUAL_COMMAND_SEQUENCE",
    )


def test_command_8_allows_null_or_absent_tool_path_and_success_marker():
    matrix = copy.deepcopy(_matrix())
    assert matrix["commands"][7]["tool_path"] is None
    assert matrix["commands"][7]["success_marker"] is None
    assert _failures_for_matrix(matrix) == []

    without_optional = copy.deepcopy(matrix)
    del without_optional["commands"][7]["tool_path"]
    del without_optional["commands"][7]["success_marker"]
    assert _failures_for_matrix(without_optional) == []


def test_quantum_forward_design_supported_must_be_true():
    matrix = copy.deepcopy(_matrix())
    matrix["quantum_forward_design_supported"] = False

    _assert_failure_contains(
        _failures_for_matrix(matrix),
        "quantum_forward_design_supported",
    )


def test_any_evidence_or_artifact_boolean_true_fails():
    for field in (
        "quantum_evidence_claim_created",
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "cash_receipt_artifact_created",
        "sha_freeze_authority_created",
    ):
        matrix = copy.deepcopy(_matrix())
        matrix[field] = True

        _assert_failure_contains(_failures_for_matrix(matrix), field)

    command_matrix = copy.deepcopy(_matrix())
    command_matrix["commands"][0]["creates_runtime_artifact"] = True
    _assert_failure_contains(_failures_for_matrix(command_matrix), "runtime_artifact")


def test_bundle_file_present_true_fails():
    matrix = copy.deepcopy(_matrix())
    matrix["bundle_file_present"] = True

    _assert_failure_contains(_failures_for_matrix(matrix), "bundle_file_present")


def test_bundle_sha_present_true_fails():
    matrix = copy.deepcopy(_matrix())
    matrix["bundle_sha_present"] = True

    _assert_failure_contains(_failures_for_matrix(matrix), "bundle_sha_present")


def test_uses_pr_number_as_authority_true_fails():
    matrix = copy.deepcopy(_matrix())
    matrix["uses_pr_number_as_authority"] = True

    _assert_failure_contains(_failures_for_matrix(matrix), "uses_pr_number_as_authority")


def test_final_ready_true_fails():
    matrix = copy.deepcopy(_matrix())
    matrix["final_ready"] = True

    _assert_failure_contains(_failures_for_matrix(matrix), "final_ready")


def test_success_marker_prints_exactly(capsys):
    exit_code = gate.main(
        [
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--schema",
            str(SCHEMA),
            "--matrix",
            str(MATRIX),
            "--fixture",
            str(FIXTURE),
            "--out",
            str(REPORT),
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out == f"{gate.SUCCESS_MARKER}\n"
