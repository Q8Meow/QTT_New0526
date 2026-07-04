from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess

import pytest

from tools.validate_source_fact_binding_connector_semantic_readiness_static import (
    ACCEPTED_PACKET_REQUIRED,
    BLOCKED_PENDING_PACKET,
    REQUIRED_TYPED_ARTIFACTS,
    SOURCE_REQUIRED,
    TARGET_FIELDS,
    VENUE_IDS,
    validate_connector_semantic_target_field_matrix_fixture,
    validate_readiness_gate_report_fixture,
    validate_source_to_connector_matrix_fixture,
    validate_static_surface,
)


SOURCE_MATRIX_SCHEMA = Path(
    "schemas/source_fact_binding_readiness/stage1_source_to_connector_field_binding_matrix.schema.json"
)
SOURCE_MATRIX_FIXTURE = Path(
    "tests/fixtures/source_fact_binding_readiness/"
    "synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json"
)
CONNECTOR_MATRIX_SCHEMA = Path(
    "schemas/source_fact_binding_readiness/stage1_connector_semantic_target_field_matrix.schema.json"
)
CONNECTOR_MATRIX_FIXTURE = Path(
    "tests/fixtures/source_fact_binding_readiness/"
    "synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json"
)
GATE_REPORT_SCHEMA = Path(
    "schemas/source_fact_binding_readiness/stage1_connector_semantic_readiness_gate_report.schema.json"
)
GATE_REPORT_FIXTURE = Path(
    "tests/fixtures/source_fact_binding_readiness/"
    "synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json"
)
VALIDATOR = Path(
    "tools/validate_source_fact_binding_connector_semantic_readiness_static.py"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_matrix() -> dict:
    return _load(SOURCE_MATRIX_FIXTURE)


def _connector_matrix() -> dict:
    return _load(CONNECTOR_MATRIX_FIXTURE)


def _gate_report() -> dict:
    return _load(GATE_REPORT_FIXTURE)


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_pr38_readiness_artifacts_exist():
    for path in [
        SOURCE_MATRIX_SCHEMA,
        SOURCE_MATRIX_FIXTURE,
        CONNECTOR_MATRIX_SCHEMA,
        CONNECTOR_MATRIX_FIXTURE,
        GATE_REPORT_SCHEMA,
        GATE_REPORT_FIXTURE,
        VALIDATOR,
    ]:
        assert path.exists(), path

    report = _gate_report()
    assert report["required_typed_artifacts_represented"] == REQUIRED_TYPED_ARTIFACTS


def test_source_to_connector_field_binding_matrix_is_schema_valid():
    assert (
        validate_static_surface(
            repo_root=Path("."),
            source_to_connector_schema_path=SOURCE_MATRIX_SCHEMA,
            source_to_connector_fixture_path=SOURCE_MATRIX_FIXTURE,
            connector_target_schema_path=CONNECTOR_MATRIX_SCHEMA,
            connector_target_fixture_path=CONNECTOR_MATRIX_FIXTURE,
            gate_report_schema_path=GATE_REPORT_SCHEMA,
            gate_report_fixture_path=GATE_REPORT_FIXTURE,
            scan_python_usage=False,
        )
        == []
    )
    assert validate_source_to_connector_matrix_fixture(_source_matrix()) == []


def test_connector_semantic_target_field_matrix_is_schema_valid():
    assert validate_connector_semantic_target_field_matrix_fixture(_connector_matrix()) == []


def test_readiness_gate_report_is_schema_valid():
    assert validate_readiness_gate_report_fixture(_gate_report(), repo_root=Path(".")) == []


def test_all_target_fields_remain_source_required_or_accepted_packet_required():
    source_matrix = _source_matrix()
    connector_matrix = _connector_matrix()

    assert [row["venue_id"] for row in source_matrix["venue_rows"]] == VENUE_IDS
    assert [row["venue_id"] for row in connector_matrix["venue_rows"]] == VENUE_IDS

    for row in source_matrix["venue_rows"]:
        assert row["target_field_paths"] == TARGET_FIELDS
        assert row["source_dependency_state"] == SOURCE_REQUIRED
        assert row["accepted_packet_requirement_state"] == ACCEPTED_PACKET_REQUIRED
        assert row["readiness_state"] == BLOCKED_PENDING_PACKET
        assert row["connector_semantic_value_state"] == SOURCE_REQUIRED
        assert row["connector_semantic_value_populated"] is False

    for row in connector_matrix["venue_rows"]:
        assert row["target_field_paths"] == TARGET_FIELDS
        assert row["target_field_state"] == SOURCE_REQUIRED
        assert row["accepted_packet_requirement_state"] == ACCEPTED_PACKET_REQUIRED
        assert row["readiness_state"] == BLOCKED_PENDING_PACKET
        assert row["connector_semantic_value_state"] == SOURCE_REQUIRED
        assert row["connector_semantic_value_populated"] is False


def test_validator_blocks_accepted_source_facts():
    report = _gate_report()
    report["source_fact_binding_readiness_report"][
        "accepted_source_fact_created_count"
    ] = 1
    report["no_claim_flags"]["accepts_source_facts"] = True

    failures = validate_readiness_gate_report_fixture(report, repo_root=Path("."))

    _assert_failure_contains(failures, "accepted_source_fact_created_count")
    _assert_failure_contains(failures, "accepts_source_facts")


def test_validator_blocks_connector_semantic_value_population():
    matrix = _connector_matrix()
    row = matrix["venue_rows"][0]
    row["connector_semantic_value_state"] = "CONNECTOR_SEMANTIC_VALUE_POPULATED"
    row["connector_semantic_value_populated"] = True

    failures = validate_connector_semantic_target_field_matrix_fixture(matrix)

    _assert_failure_contains(failures, "connector_semantic_value_state")
    _assert_failure_contains(failures, "connector_semantic_value_populated")


def test_validator_blocks_runtime_resolver_snapshot_claims():
    matrix = _connector_matrix()
    matrix["venue_rows"][0]["runtime_resolver_snapshot_created"] = True

    failures = validate_connector_semantic_target_field_matrix_fixture(matrix)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_created")


def test_validator_blocks_replay_paper_live_order_and_profit_claims():
    report = _gate_report()
    report["connector_semantic_readiness_summary"][
        "replay_paper_execution_violation_count"
    ] = 1
    report["connector_semantic_readiness_summary"][
        "live_reachability_violation_count"
    ] = 1
    report["forbidden_action_flags"]["order_authority_enabled"] = True
    report["forbidden_action_flags"]["profit_evidence_creation_enabled"] = True
    report["no_claim_flags"]["creates_profit_evidence"] = True

    failures = validate_readiness_gate_report_fixture(report, repo_root=Path("."))

    _assert_failure_contains(failures, "replay_paper_execution_violation_count")
    _assert_failure_contains(failures, "live_reachability_violation_count")
    _assert_failure_contains(failures, "order_authority_enabled")
    _assert_failure_contains(failures, "profit_evidence_creation_enabled")
    _assert_failure_contains(failures, "creates_profit_evidence")


def test_validator_blocks_atomicrows_bundle_hash_creation_or_mutation(tmp_path):
    bundle = tmp_path / "docs" / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
    bundle.parent.mkdir(parents=True)
    bundle.write_text("", encoding="utf-8")

    failures = validate_readiness_gate_report_fixture(_gate_report(), repo_root=tmp_path)

    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")


@pytest.mark.parametrize(
    "script_name",
    [
        "playwright_pr169_dash1_ui1_r1_visual_smoke.py",
        "playwright_pr169_dash1_ui1_r2_visual_smoke.py",
    ],
)
def test_python_usage_scan_allows_exact_local_visual_qa_playwright_path(tmp_path, script_name):
    script = tmp_path / "tools" / script_name
    script.parent.mkdir(parents=True)
    script.write_text(
        "\n".join(
            [
                "from playwright.sync_api import sync_playwright",
                "def main():",
                "    return sync_playwright",
            ]
        ),
        encoding="utf-8",
    )

    failures = validate_static_surface(
        repo_root=tmp_path,
        source_to_connector_schema_path=SOURCE_MATRIX_SCHEMA,
        source_to_connector_fixture_path=SOURCE_MATRIX_FIXTURE,
        connector_target_schema_path=CONNECTOR_MATRIX_SCHEMA,
        connector_target_fixture_path=CONNECTOR_MATRIX_FIXTURE,
        gate_report_schema_path=GATE_REPORT_SCHEMA,
        gate_report_fixture_path=GATE_REPORT_FIXTURE,
    )

    assert failures == []


def test_python_usage_scan_rejects_unregistered_playwright_path(tmp_path):
    script = tmp_path / "tools" / "bad_browser_fetch.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        "from playwright.sync_api import sync_playwright\n",
        encoding="utf-8",
    )

    failures = validate_static_surface(
        repo_root=tmp_path,
        source_to_connector_schema_path=SOURCE_MATRIX_SCHEMA,
        source_to_connector_fixture_path=SOURCE_MATRIX_FIXTURE,
        connector_target_schema_path=CONNECTOR_MATRIX_SCHEMA,
        connector_target_fixture_path=CONNECTOR_MATRIX_FIXTURE,
        gate_report_schema_path=GATE_REPORT_SCHEMA,
        gate_report_fixture_path=GATE_REPORT_FIXTURE,
    )

    _assert_failure_contains(
        failures,
        "tools/bad_browser_fetch.py imports forbidden network/client module playwright.sync_api",
    )


def test_validator_does_not_mutate_inputs_or_create_atomicrows_files(tmp_path):
    source_before = SOURCE_MATRIX_FIXTURE.read_bytes()
    connector_before = CONNECTOR_MATRIX_FIXTURE.read_bytes()
    report_before = GATE_REPORT_FIXTURE.read_bytes()
    source = _source_matrix()
    connector = _connector_matrix()
    report = _gate_report()
    frozen = (copy.deepcopy(source), copy.deepcopy(connector), copy.deepcopy(report))

    assert validate_source_to_connector_matrix_fixture(source) == []
    assert validate_connector_semantic_target_field_matrix_fixture(connector) == []
    assert validate_readiness_gate_report_fixture(report, repo_root=tmp_path) == []

    assert SOURCE_MATRIX_FIXTURE.read_bytes() == source_before
    assert CONNECTOR_MATRIX_FIXTURE.read_bytes() == connector_before
    assert GATE_REPORT_FIXTURE.read_bytes() == report_before
    assert (source, connector, report) == frozen
    assert not (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "AtomicRows.bundle.jsonl"
    ).exists()
    assert not (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "AtomicRows.bundle.sha256"
    ).exists()


def test_master_plan_remains_unchanged():
    completed = subprocess.run(
        ["git", "diff", "--", "docs/master_plan/QTT_MasterPlan_Current.md"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
