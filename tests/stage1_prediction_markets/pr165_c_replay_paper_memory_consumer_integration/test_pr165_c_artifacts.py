from pathlib import Path
from typing import Any

import pytest

from src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration import (
    paths,
)
from src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration.central_vocab import (
    AGENT_IDS,
    NO_ORPHAN_STATUS,
)
from src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration.computability_action_vocab import (
    COMPUTABILITY_ACTIONS,
)
from src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration.authority_policy import (
    FORBIDDEN_COMPUTABILITY_LITERALS,
)
from src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration.json_io import (
    read_json,
)
from src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration.report_sharding import (
    load_report_records,
)
from src.qtt.stage1_prediction_markets.pr165_c_replay_paper_memory_consumer_integration.validators import (
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _payload(filename: str) -> dict:
    return read_json(REPO_ROOT / paths.GENERATED_DIR / filename)


def _records(filename: str) -> list[dict]:
    return load_report_records(REPO_ROOT, _payload(filename))


def _string_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for nested in value.values():
            values.extend(_string_values(nested))
        return values
    if isinstance(value, list):
        values = []
        for nested in value:
            values.extend(_string_values(nested))
        return values
    if isinstance(value, str):
        return [value]
    return []


def test_pr165_c_validator_accepts_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, "\n".join(result.failures[:25])


def test_pr165_c_resolve_repo_relative_normalizes_legacy_backslash_refs():
    legacy_ref = r"docs\master_plan\generated\PR165_C_FinalSummary.report.json"
    normalized = "docs/master_plan/generated/PR165_C_FinalSummary.report.json"

    assert paths.normalize_repo_ref(legacy_ref) == normalized
    assert paths.resolve_repo_relative(REPO_ROOT, legacy_ref).relative_to(REPO_ROOT).as_posix() == normalized
    assert paths.resolve_repo_relative(REPO_ROOT, legacy_ref).exists()

    for bad_ref in (
        "../docs/master_plan/generated/PR165_C_FinalSummary.report.json",
        "docs/master_plan/../generated/PR165_C_FinalSummary.report.json",
        "/docs/master_plan/generated/PR165_C_FinalSummary.report.json",
        r"C:\repo\docs\master_plan\generated\PR165_C_FinalSummary.report.json",
    ):
        with pytest.raises(ValueError):
            paths.resolve_repo_relative(REPO_ROOT, bad_ref)


def test_pr165_c_shard_refs_are_repo_relative_posix():
    for filename in paths.ROW_LEVEL_REPORTS:
        payload = _payload(filename)
        for shard_ref in payload.get("shard_files") or []:
            assert "\\" not in shard_ref
            assert paths.normalize_repo_ref(shard_ref) == shard_ref
            assert paths.resolve_repo_relative(REPO_ROOT, shard_ref).exists()
        for entry in payload.get("shard_manifest_refs") or []:
            shard_ref = entry["shard_path"]
            assert "\\" not in shard_ref
            assert paths.normalize_repo_ref(shard_ref) == shard_ref
            assert shard_ref in payload.get("shard_files", [])


def test_pr165_c_root_reports_contain_no_backslash_path_refs():
    offenders = []
    for filename in paths.REPORT_FILENAMES:
        for value in _string_values(_payload(filename)):
            if "\\" in value:
                offenders.append((filename, value))
    assert offenders == []


def test_pr165_c_load_report_records_loads_posix_shard_refs():
    payload = _payload("PR165_C_MemoryConsumerRouter.report.json")
    assert payload["sharded_flag"] is True
    assert all(paths.normalize_repo_ref(ref) == ref for ref in payload["shard_files"])

    rows = load_report_records(REPO_ROOT, payload)

    assert len(rows) == payload["record_count"] == 6502


def test_pr165_c_validate_artifacts_finds_required_upstream_inputs_from_repo_root():
    missing = [
        ref
        for ref in paths.REQUIRED_INPUTS
        if not paths.resolve_repo_relative(REPO_ROOT, ref).exists()
    ]
    assert missing == []

    result = validate_artifacts(REPO_ROOT)
    assert result.ok, "\n".join(result.failures[:25])


def test_pr165_c_row_conservation_and_core_counts():
    summary = _records("PR165_C_FinalSummary.report.json")[0]

    assert summary["memory_consumer_rows"] == 6502
    assert summary["computable_artifact_payload_rows"] == 6502
    assert summary["computable_qku_action_rows"] == 6502
    assert summary["formula_test_vector_rows"] == 6502
    assert summary["pending_retest_queue_rows"] == 6497
    assert summary["retest_priority_rows"] == 6497
    assert summary["repair_to_retest_handoff_rows"] == 2512
    assert summary["quantum_consumer_route_rows"] == 6502
    assert summary["dashboard_handoff_rows"] == 6502
    assert summary["governance_handoff_rows"] == 6502
    assert summary["commander_handoff_rows"] >= summary["pending_retest_queue_rows"]
    assert summary["metadata_only_rows"] == 0
    assert summary["placeholder_only_rows"] == 0
    assert summary["unknown_status_rows"] == 0
    assert summary["generic_blocked_rows"] == 0
    assert summary["orphan_counts_all_0"] is True
    assert summary["authority_boundary_violation_counts_all_0"] is True
    assert summary["exact_next_recommended_PR"] == (
        "PR165-D / PR166-S scenario-specific QKU combination selection engine"
    )


def test_pr165_c_memory_rows_are_agent_consumable_and_computable():
    rows = _records("PR165_C_MemoryConsumerRouter.report.json")
    assert len(rows) == 6502

    for row in rows:
        assert row["computability_action_status"] in COMPUTABILITY_ACTIONS
        assert row["computable_artifact_payload_ref"]
        assert row["computable_formula_ref_or_action"]
        assert row["formula_test_vector_ref_or_action"]
        assert row["scenario_memory_route_ref"]
        assert row["agent_consumer_set"]
        assert row["primary_agent_owner"] in AGENT_IDS
        assert row["independent_challenger_agent"] in AGENT_IDS
        assert row["lineage_graph_ref"]
        assert row["authority_boundary_ref"]
        assert row["no_orphan_status"] == NO_ORPHAN_STATUS
        assert row["computability_action_status"] not in FORBIDDEN_COMPUTABILITY_LITERALS


def test_pr165_c_pr_file_connectivity_covers_created_files():
    rows = _records("PR165_C_PRFileConnectivityAudit.report.json")
    created_files = [
        *list((REPO_ROOT / paths.PACKAGE_DIR).rglob("*")),
        REPO_ROOT / "tools/build_pr165_c_replay_paper_memory_consumer_integration.py",
        REPO_ROOT / "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
        *list((REPO_ROOT / paths.TEST_DIR).rglob("*")),
        *list((REPO_ROOT / paths.GENERATED_DIR).glob("PR165_C_*.report.json")),
        *list((REPO_ROOT / paths.SHARD_DIR).glob("*.report.json")),
    ]
    created_file_count = sum(
        1
        for path in created_files
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )

    assert len(rows) >= created_file_count
    for row in rows:
        assert row["upstream_source_pr_refs"]
        assert row["upstream_source_artifact_refs"]
        assert row["downstream_consumer_pr_refs"]
        assert row["downstream_consumer_artifact_refs"]
        assert row["owning_agent"] in AGENT_IDS
        assert row["owning_builder_or_tool"]
        assert row["validator"] == (
            "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py"
        )
        assert row["manifest_entry_ref"] == "PR165_C_ReportManifest.report.json"
        assert row["no_orphan_status"] == NO_ORPHAN_STATUS
        assert row["authority_boundary_ref"]


def test_pr165_c_retest_repair_and_priority_routes_are_complete():
    memory_rows = _records("PR165_C_MemoryConsumerRouter.report.json")
    pending_rows = _records("PR165_C_PendingRetestQueue.report.json")
    repair_rows = _records("PR165_C_RepairToRetestHandoff.report.json")
    priority_rows = _records("PR165_C_RetestPriorityRanking.report.json")

    retest_required_ids = {
        row["candidate_packet_id"] for row in memory_rows if row["retest_required"]
    }
    pending_ids = {row["candidate_packet_id"] for row in pending_rows}
    repair_ids = {row["candidate_packet_id"] for row in repair_rows}
    repair_required_ids = {
        row["candidate_packet_id"]
        for row in memory_rows
        if row["repair_consumer_action"] != "NO_ACTION_WITH_REASON"
    }

    assert retest_required_ids <= pending_ids
    assert repair_required_ids <= repair_ids
    assert len(priority_rows) == len(pending_rows)
    assert sorted(row["retest_priority_rank"] for row in priority_rows) == list(
        range(1, len(priority_rows) + 1)
    )


def test_pr165_c_agent_duties_are_distinct_and_typed():
    duty_rows = _records("PR165_C_AgentDutyDistinctnessMatrix.report.json")
    overlap_rows = _records("PR165_C_AgentOverlapConflictAudit.report.json")

    assert {row["agent_id"] for row in duty_rows} == set(AGENT_IDS)
    assert len(overlap_rows) >= len(AGENT_IDS)
    for row in duty_rows:
        assert row["forbidden_duties"]
        assert row["receipt_required"] is True
        assert row["no_orphan_agent_duty_status"] == NO_ORPHAN_STATUS
    assert all(row["overlap_status"] != "UNTYPED_OVERLAP" for row in overlap_rows)


def test_pr165_c_quantum_routes_do_not_claim_runtime_or_advantage():
    quantum_rows = _records("PR165_C_QuantumConsumerRouter.report.json")
    assert len(quantum_rows) == 6502

    for row in quantum_rows:
        assert row["quantum_backend_execution_count"] == 0
        assert row["quantum_advantage_claim_count"] == 0
        assert row["quantum_consumer_action"] != "QUANTUM_BACKEND_EXECUTION"
        assert row["quantum_consumer_action"] != "QUANTUM_ADVANTAGE_CLAIM"
        assert row["authority_boundary_ref"]
