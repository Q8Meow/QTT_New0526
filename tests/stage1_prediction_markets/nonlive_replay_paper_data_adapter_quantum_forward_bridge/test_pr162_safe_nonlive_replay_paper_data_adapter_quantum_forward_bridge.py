from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.nonlive_replay_paper_data_adapter_quantum_forward_bridge import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.nonlive_replay_paper_data_adapter_quantum_forward_bridge.json_io import (
    records_from_payload,
)
from src.qtt.stage1_prediction_markets.nonlive_replay_paper_data_adapter_quantum_forward_bridge.paths import (
    normalize_shard_ref,
    resolve_repo_relative,
)
from src.qtt.stage1_prediction_markets.nonlive_replay_paper_data_adapter_quantum_forward_bridge.validator import (
    validate_artifacts,
)
from tools import ci_branch_context
from tools import run_validation_gates


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_DIR = REPO_ROOT / c.GENERATED_DIR


def _payload(filename: str) -> dict:
    return json.loads((GENERATED_DIR / filename).read_text(encoding="utf-8"))


def _manifest_by_report() -> dict[str, dict]:
    return {
        record["report_filename"]: record
        for record in records_from_payload(_payload("PR162_ReportShardManifest.report.json"))
    }


def _records(filename: str) -> list[dict]:
    payload = _payload(filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    records: list[dict] = []
    for shard_ref in _manifest_by_report()[filename]["shard_files"]:
        normalized = normalize_shard_ref(REPO_ROOT, shard_ref)
        records.extend(records_from_payload(json.loads(resolve_repo_relative(REPO_ROOT, normalized).read_text(encoding="utf-8"))))
    return records


def test_pr162_validator_summary_and_upstream_consumption() -> None:
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures

    summary = _payload("PR162_FinalSummary.report.json")
    assert summary["active_branch"] == c.EXPECTED_BRANCH
    assert summary["pr136_orchestration_artifacts_consumed_flag"] is True
    assert summary["pr137r_pr138_atomicrows_contracts_consumed_flag"] is True
    assert summary["pr152_currentization_result"] == c.PR152_CURRENTIZATION_RESULT_PASS
    assert summary["pr152_currentization_validation_command"] == c.PR152_CURRENTIZATION_VALIDATION_COMMAND
    assert summary["pr152_currentization_failure_count"] == 0
    assert summary["records"][0]["pr152_currentization_result"] == c.PR152_CURRENTIZATION_RESULT_PASS
    assert summary["pr161f_executor_inputs_consumed"] == 9360
    assert summary["pr161f_replay_requests_consumed"] == 9360
    assert summary["pr161f_paper_requests_consumed"] == 9360
    assert summary["pr161f_paired_plans_consumed"] == 9360
    assert summary["pr161f_result_eligibility_gates_consumed"] == 9360
    assert summary["master_plan_file_edited_flag"] is False
    assert summary["atomicrows_bundle_jsonl_changed_flag"] is False
    assert summary["qtt_sha_freeze_checksum_global_digest_authority_created_flag"] is False
    assert summary["atomicrows_bundle_hash_or_freeze_authority_created_flag"] is False
    for flag, expected in c.NO_AUTHORITY_FLAGS.items():
        assert summary[flag] is expected


def test_pr162_dataset_discovery_blocks_synthetic_and_metadata_only_inputs() -> None:
    datasets = _records("PR162_NonLiveDatasetDiscovery.report.json")
    artifacts = _records("PR162_RealNonLiveRunArtifactCandidateRegistry.report.json")
    separator = _records("PR162_SyntheticVsRealNonLiveSeparation.report.json")[0]
    external = _records("PR162_ExternalCandidateIntakeRegistry.report.json")

    assert artifacts == []
    assert any(record["dataset_authority_class"] == "REPO_LOCAL_SYNTHETIC_FIXTURE" for record in datasets)
    assert any(record["dataset_authority_class"] == "ONLINE_DISCOVERED_CANDIDATE_METADATA_ONLY" for record in datasets)
    assert all(record["allowed_for_real_nonlive_artifact_candidate"] is False for record in datasets)
    assert separator["synthetic_can_be_labeled_real_nonlive_flag"] is False
    assert all(record["repo_local_run_data_materialized_flag"] is False for record in external)
    assert all(record["accepted_as_official_fact_flag"] is False for record in external)


def test_pr162_lane_separation_pr161e_handoff_and_qku_coverage() -> None:
    coverage = _records("PR162_QKUArtifactCoverageBridge.report.json")
    result_handoff = _records("PR162_ResultPacketReadinessHandoffCandidate.report.json")
    pr161e_handoff = _records("PR162_PR161EIngestionHandoffCandidate.report.json")

    assert len(coverage) == 9360
    assert len(result_handoff) == 9360
    assert len(pr161e_handoff) == 9360
    assert all(record["replay_lane_state"] == "REPLAY_BLOCKED_NO_SAFE_DATA" for record in coverage)
    assert all(record["paper_lane_state"] == "PAPER_BLOCKED_NO_SAFE_DATA" for record in coverage)
    assert all(record["result_packet_ready_flag"] is False for record in result_handoff)
    assert all(record["pr161e_handoff_candidate_flag"] is False for record in pr161e_handoff)
    assert all(record["ranking_update_allowed_flag"] is False for record in pr161e_handoff)
    assert _payload("PR162_QKUArtifactCoverageBridge.report.json")["coverage_counts"]["orphan_count"] == 0


def test_pr162_quantum_forward_reports_are_blueprint_work_order_candidate_only() -> None:
    readiness = _records("PR162_QKUQuantumExecutionReadinessBridge.report.json")
    encoding = _records("PR162_QKUQuantumProblemEncodingBlueprint.report.json")
    params = _records("PR162_QuantumParameterRangeCandidateRegistry.report.json")
    backend = _records("PR162_QuantumBackendFitCandidateMatrix.report.json")
    comparator = _records("PR162_QuantumClassicalHybridComparatorBlueprint.report.json")
    work_orders = _records("PR162_QuantumReplayPaperWorkOrderQueue.report.json")
    live_bridge = _records("PR162_QuantumLiveModeControlPlaneBridge.report.json")
    latency = _records("PR162_QuantumLatencyLivePathReadinessBridge.report.json")

    assert len(readiness) == 4525
    assert len(encoding) == 4525
    assert len(backend) == 4525
    assert len(comparator) == 4525
    assert len(work_orders) == 4525
    assert len(live_bridge) == 4525
    assert len(latency) == 4525
    assert len(params) == len(c.PARAMETER_CANDIDATE_NAMES)
    assert all("QUANTUM_ENCODING_BLUEPRINT_READY" in record["readiness_states"] for record in readiness)
    assert all(record["evidence_authority_class"] == c.BLUEPRINT_AUTHORITY_CLASS for record in encoding)
    assert all(record["live_hot_path_allowed_flag"] is False for record in encoding)
    assert all(record["candidate_authority_class"] in c.PARAMETER_CANDIDATE_AUTHORITY_CLASSES for record in params)
    assert all(record["candidate_backend_family"] == "BACKEND_BLOCKED_NO_DATA" for record in backend)
    assert all(record["quantum_advantage_claim_allowed_flag"] is False for record in comparator)
    assert all(record["ready_for_future_pr163_flag"] is False for record in work_orders)
    assert all(record["pr162_live_authority_created_flag"] is False for record in live_bridge)
    assert all(record["live_hot_path_admissibility"] == "PRECOMPUTED_SNAPSHOT_ONLY" for record in latency)


def test_pr162_agents_shards_branch_context_and_validation_gate_wiring() -> None:
    agents = _records("PR162_QTTAgentExecutorHandoffBridge.report.json")
    forbidden = _records("PR162_ForbiddenAuthorityScan.report.json")[0]
    manifest = _payload("PR162_ReportShardManifest.report.json")

    assert {record["agent_id"] for record in agents} == set(c.AGENT_ROLES)
    assert all(record["self_authorizing_trading_allowed_flag"] is False for record in agents)
    assert forbidden["scan_status"] == "PASS"
    assert forbidden["no_scattered_hardcoded_policy_scan_status"] == "PASS"
    assert manifest["all_shard_refs_posix_relative_flag"] is True
    for shard_ref in manifest["all_shard_files"]:
        assert "\\" not in shard_ref
        assert normalize_shard_ref(REPO_ROOT, shard_ref.replace("/", "\\")) == shard_ref
    with pytest.raises(ValueError):
        normalize_shard_ref(REPO_ROOT, "../outside.json")

    branch = c.EXPECTED_BRANCH
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162_FinalSummary.report.json",
    )
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr162_safe_nonlive_replay_paper_quantum_forward_shards/PR162_QKUArtifactCoverageBridge.report.shard_0001.json",
    )
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
    )
    assert not ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    command_names = [Path(command[1]).name for command in run_validation_gates.build_validation_commands()]
    assert "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py" in command_names
