from __future__ import annotations

from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.safe_repo_local_nonlive_dataset_materialization_authority_gate import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.safe_repo_local_nonlive_dataset_materialization_authority_gate.json_io import (
    read_json,
    records_from_payload,
)
from src.qtt.stage1_prediction_markets.safe_repo_local_nonlive_dataset_materialization_authority_gate.paths import (
    resolve_repo_relative,
)
from src.qtt.stage1_prediction_markets.safe_repo_local_nonlive_dataset_materialization_authority_gate.validator import (
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _report(filename: str) -> dict[str, Any]:
    return read_json(REPO_ROOT / c.GENERATED_DIR / filename)


def _records(filename: str) -> list[dict[str, Any]]:
    payload = _report(filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    manifest = _report(c.SHARD_MANIFEST_REPORT_FILENAME)
    manifest_record = {
        record["report_filename"]: record
        for record in records_from_payload(manifest)
    }[filename]
    rows: list[dict[str, Any]] = []
    for shard_ref in manifest_record["shard_files"]:
        rows.extend(records_from_payload(read_json(resolve_repo_relative(REPO_ROOT, shard_ref))))
    return rows


def test_pr162a_validator_accepts_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)

    assert result.ok, result.failures


def test_pr162a_offline_source_discovery_and_fetch_plans_are_candidate_only():
    summary = _report("PR162A_FinalSummary.report.json")
    sources = _records("PR162A_SourceDiscoveryCandidateRegistry.report.json")
    fetch_plans = _records("PR162A_FetchPlanAndOwnerMaterializationCommandQueue.report.json")

    assert summary["pr136_orchestration_artifacts_consumed_flag"] is True
    assert summary["pr161c_pr161d_pr161e_pr161f_pr162_inputs_consumed_flag"] is True
    assert summary["ci_default_mode_requires_network"] is False
    assert summary["network_materialization_mode_used"] == "NONE_DEFAULT_OFFLINE"
    assert all(record["candidate_only_flag"] is True for record in sources)
    assert all(record["accepted_as_official_fact_flag"] is False for record in sources)
    assert all(record["creates_connector_semantics"] is False for record in sources)
    assert all(record["ci_requires_network"] is False for record in fetch_plans)
    assert all(record["execute_in_pr162a_default_build_flag"] is False for record in fetch_plans)
    discovered_classes = {
        source_class
        for record in sources
        for source_class in record["source_classes"]
    }
    assert set(c.SOURCE_CLASSES) - discovered_classes <= {
        "THIRD_PARTY_DATA_VENDOR_CANDIDATE",
        "SOCIAL_SIGNAL_CANDIDATE",
        "OWNER_PROVIDED_CANDIDATE",
    }


def test_pr162a_dataset_normalization_and_leakage_controls():
    datasets = _records("PR162A_DatasetMaterializationManifest.report.json")
    normalized = _records("PR162A_NormalizedDatasetInventory.report.json")
    audit = _records("PR162A_DataQualityLeakageAndTimeWindowAudit.report.json")[0]
    missing = _records("PR162A_MissingValueCandidateRegistry.report.json")

    run_capable = [record for record in datasets if record["run_capable_flag"]]
    synthetic = next(record for record in datasets if record["dataset_id"] == c.SYNTHETIC_BLOCKED_DATASET_ID)
    assert len(run_capable) == 1
    assert run_capable[0]["dataset_id"] == c.KALSHI_RUN_CAPABLE_DATASET_ID
    assert run_capable[0]["candidate_only_flag"] is True
    assert run_capable[0]["source_class"] == "OFFICIAL_PUBLIC_HISTORICAL_DATA_CANDIDATE"
    assert run_capable[0]["venue_scope"] == "KALSHI"
    assert run_capable[0]["adapter_mechanics_fixture_flag"] is True
    assert run_capable[0]["dataset_seed_candidate_flag"] is True
    assert run_capable[0]["schema_validation_status"] == "PASS"
    assert run_capable[0]["normalization_status"] == "NORMALIZED"
    assert run_capable[0]["leakage_audit_status"] == "PASS"
    assert run_capable[0]["strict_pr161f_run_plan_coverage_count"] == 0
    assert synthetic["run_capable_flag"] is False
    assert synthetic["synthetic_fixture_flag"] is True
    assert synthetic["blocker_code"] in c.BLOCKER_CODES
    assert all(row["settlement_status_candidate"] is None for row in normalized)
    assert all(row["resolution_candidate"] is None for row in normalized)
    assert all(
        row.get(field) is None
        for row in normalized
        for field in row["missing_value_flags"]
    )
    assert all(record["value_fabricated_flag"] is False for record in missing)
    assert audit["leakage_audit_status"] == "PASS"
    assert audit["pre_resolution_feature_separation_status"] == "PASS"
    assert audit["performance_metric_creation_status"] == "NOT_CREATED"


def test_pr162a_mapping_rerun_pr163_quantum_agent_and_guardrail_contracts():
    summary = _report("PR162A_FinalSummary.report.json")
    mappings = _records("PR162A_MarketScenarioQKUMappingMatrix.report.json")
    rerun = _records("PR162A_PR162AdapterRerunReadinessBridge.report.json")
    pr163 = _records("PR162A_PR163ReadinessBlockerStatus.report.json")[0]
    quantum = _records("PR162A_QuantumQKUDatasetFeatureBridge.report.json")
    agents = _records("PR162A_QTTAgentDatasetHandoffBridge.report.json")
    scan = _records("PR162A_ForbiddenAuthorityScan.report.json")[0]

    strict_run_capable = [record for record in mappings if record["run_capable_dataset_available_flag"]]
    seed_only = [
        record
        for record in mappings
        if record["seed_candidate_mapping_flag"] and not record["run_capable_dataset_available_flag"]
    ]
    blocked_without_dataset = [
        record
        for record in mappings
        if not record["seed_candidate_mapping_flag"] and not record["run_capable_dataset_available_flag"]
    ]
    assert len(strict_run_capable) == 0
    assert len(seed_only) == 9354
    assert len(blocked_without_dataset) == 6
    assert all(
        record["dataset_candidate_refs"]
        for record in mappings
        if record["mapping_status"] != "BLOCKED_UNMAPPABLE_QKU"
    )
    assert all(record["mapping_status"] == "MAPPED_TO_CANDIDATE_BLOCKED_FROM_RUN" for record in seed_only)
    assert all(record["blocker_code"] == c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS for record in seed_only)
    assert all(record["strict_row_count_coverage_flag"] is False for record in seed_only)
    assert all(c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS in record["coverage_blocker_codes"] for record in seed_only)
    assert sum(1 for record in rerun if record["both_lanes_rerun_ready_flag"]) == 0
    assert summary["qkus_mapped_to_run_capable_datasets"] == 0
    assert summary["qkus_mapped_to_seed_or_mechanics_dataset_candidates"] == 9354
    assert summary["qkus_blocked_from_run_capable_coverage"] == 9360
    assert summary["pr162_adapter_rerun_ready_count"] == 0
    assert summary["pr162_adapter_rerun_blocked_count"] == 9360
    assert all(
        not record["both_lanes_rerun_ready_flag"]
        or record["strict_run_capable_coverage_flag"]
        for record in rerun
    )
    assert all(record["remaining_blocker_code"] != "NONE" for record in rerun)
    assert all(record["real_artifact_candidate_creation_allowed_flag"] is False for record in rerun)
    assert all(record["pr162b_real_artifact_candidate_allowed_flag"] is False for record in rerun)
    assert all(record["pr162r_real_artifact_candidate_allowed_flag"] is False for record in rerun)
    assert sum(1 for record in rerun if record["adapter_mechanics_smoke_allowed_flag"]) == 9354
    assert pr163["pr163_ready_flag"] is False
    assert pr163["validated_real_nonlive_replay_artifacts_exist_flag"] is False
    assert pr163["validated_real_nonlive_paper_artifacts_exist_flag"] is False
    assert len(quantum) == 4525
    assert sum(1 for record in quantum if record["run_capable_dataset_available_flag"]) == 0
    assert sum(1 for record in quantum if record["feature_seed_candidate_only_flag"]) == 4519
    assert summary["quantum_qkus_mapped_to_run_capable_dataset_feature_candidates"] == 0
    assert summary["quantum_qkus_mapped_to_seed_only_dataset_feature_candidates"] == 4519
    assert sum(
        1
        for record in quantum
        if not record["run_capable_dataset_available_flag"]
        and not record["feature_seed_candidate_only_flag"]
    ) == 6
    assert all(
        record["quantum_feature_materialization_status"] == "FEATURE_SEED_CANDIDATE_ONLY"
        for record in quantum
        if record["feature_seed_candidate_only_flag"]
    )
    assert all(record["quantum_backend_execution_created_flag"] is False for record in quantum)
    assert all(record["quantum_simulator_execution_created_flag"] is False for record in quantum)
    assert all(record["optimizer_execution_created_flag"] is False for record in quantum)
    assert {record["agent_id"] for record in agents} == set(c.AGENT_ROLES)
    assert all(record["order_routing_allowed_flag"] is False for record in agents)
    assert scan["scan_status"] == "PASS"
    assert scan["no_scattered_hardcoded_policy_scan_status"] == "PASS"
