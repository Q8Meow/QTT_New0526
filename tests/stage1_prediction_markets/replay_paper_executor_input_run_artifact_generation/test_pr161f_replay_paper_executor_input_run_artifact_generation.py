from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation.compact_records import (
    expand_payload_records,
)
from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation.json_io import (
    records_from_payload,
)
from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation.paths import (
    normalize_shard_ref,
    resolve_repo_relative,
)
from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation.schema_loader import (
    load_all_schemas,
)
from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation.validator import (
    validate_artifacts,
)
from tools import ci_branch_context
from tools import run_validation_gates


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_DIR = REPO_ROOT / c.GENERATED_DIR


def _payload(filename: str) -> dict:
    return json.loads((GENERATED_DIR / filename).read_text(encoding="utf-8"))


def _shared_dictionary() -> dict:
    return _payload(c.SHARED_DICTIONARY_REPORT_FILENAME)["shared_dictionary"]


def _manifest_by_report() -> dict[str, dict]:
    return {
        record["report_filename"]: record
        for record in records_from_payload(_payload("PR161F_ReportShardManifest.report.json"))
    }


def _records(filename: str) -> list[dict]:
    payload = _payload(filename)
    shared_dictionary = _shared_dictionary()
    if not payload.get("sharded_flag"):
        return expand_payload_records(payload, shared_dictionary)
    records: list[dict] = []
    manifest_record = _manifest_by_report()[filename]
    for shard_ref in manifest_record["shard_files"]:
        normalized = normalize_shard_ref(REPO_ROOT, shard_ref)
        records.extend(
            expand_payload_records(
                json.loads(resolve_repo_relative(REPO_ROOT, normalized).read_text(encoding="utf-8")),
                shared_dictionary,
            )
        )
    return records


def test_pr161f_validator_and_upstream_consumption_counts() -> None:
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures

    summary = _payload("PR161F_FinalSummary.report.json")
    preflight = _records("PR161F_ReplayPaperExecutorInputPreflightReceipt.report.json")[0]

    assert preflight["active_branch"] == c.EXPECTED_BRANCH
    assert preflight["git_sha_is_vcs_metadata_only_flag"] is True
    assert preflight["pr136_route_triage_consumed_flag"] is True
    assert preflight["pr137r_atomicrows_reconciliation_consumed_flag"] is True
    assert preflight["pr138_atomicrows_semantic_contract_consumed_flag"] is True
    assert summary["pr136_artifacts_consumed_status"] == "PASS"
    assert summary["pr137r_pr138_artifacts_consumed_status"] == "PASS"
    assert summary["pr161c_qku_inventory_count_loaded"] == 9360
    assert summary["pr161d_replay_paper_scenario_count_loaded"] == 9360
    assert summary["pr161e_outcome_capture_count_loaded"] == 9360


def test_pr161f_record_counts_and_qku_traceability_matrix_resolution() -> None:
    executor = _records("PR161F_ExecutorInputRegistry.report.json")
    replay = _records("PR161F_ReplayRunRequestRegistry.report.json")
    paper = _records("PR161F_PaperRunRequestRegistry.report.json")
    paired = _records("PR161F_PairedReplayPaperRunPlan.report.json")
    envelopes = _records("PR161F_RunArtifactEnvelopeRegistry.report.json")
    eligibility = _records("PR161F_ResultPacketEmissionEligibilityGate.report.json")
    qch = _records("PR161F_QuantumClassicalHybridRunPlan.report.json")
    compat = _records("PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json")
    matrix = _records("PR161F_QKUEndToEndTraceabilityMatrix.report.json")

    assert len(executor) == 9360
    assert len(replay) == 9360
    assert len(paper) == 9360
    assert len(paired) == 9360
    assert len(envelopes) == 9360
    assert len(eligibility) == 9360
    assert len(qch) == 4525
    assert len(compat) == 4525
    assert len(matrix) == 9360

    matrix_qkus = {record["qku_id"] for record in matrix}
    assert {record["qku_id"] for record in executor} == matrix_qkus
    assert {record["qku_id"] for record in replay} == matrix_qkus
    assert {record["qku_id"] for record in paper} == matrix_qkus
    assert {record["qku_id"] for record in envelopes} == matrix_qkus
    assert {record["qku_id"] for record in eligibility} == matrix_qkus
    assert {record["qku_id"] for record in qch} <= matrix_qkus
    assert {record["qku_id"] for record in compat} <= matrix_qkus

    sample = matrix[0]
    assert sample["pr161c_registry_ref"]
    assert sample["pr161d_replay_paper_scenario_ref_if_available"]
    assert sample["pr161e_outcome_capture_ref_if_available"]
    assert sample["executor_input_record"]
    assert sample["result_packet_emission_eligibility_record"]
    assert sample["downstream_future_live_order_route_eligibility_gate"] == c.FUTURE_LIVE_BLOCKER_CODE
    assert all(record["qku_graph_node_id"] for record in matrix)


def test_pr161f_run_artifact_and_quantum_safety_gates() -> None:
    envelopes = _records("PR161F_RunArtifactEnvelopeRegistry.report.json")
    synthetic = _records("PR161F_SyntheticSmokeRunArtifactRegistry.report.json")
    real_nonlive = _records("PR161F_RealNonLiveRunArtifactRegistry.report.json")
    eligibility = _records("PR161F_ResultPacketEmissionEligibilityGate.report.json")
    qch = _records("PR161F_QuantumClassicalHybridRunPlan.report.json")
    compat = _records("PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json")

    assert len(synthetic) == 25
    assert real_nonlive == []
    assert all(record["result_packet_emission_eligibility_state"] == "RESULT_PACKET_EMISSION_BLOCKED" for record in envelopes)
    assert all(record["no_live_connector_used_flag"] is True for record in envelopes)
    assert all(record["no_profit_evidence_created_flag"] is True for record in envelopes)
    assert all(record["synthetic_artifact_blocked_from_result_packet_flag"] is True for record in eligibility)
    assert all(record["run_artifact_class"] == "SYNTHETIC_PIPELINE_SMOKE_RUN_ARTIFACT" for record in synthetic)
    assert all(record["treated_as_performance_evidence_flag"] is False for record in synthetic)
    assert all(record["pr161e_capture_update_allowed_flag"] is False for record in synthetic)

    assert all(record["live_order_route_blocked_until_promotion_flag"] is True for record in qch)
    assert all(record["no_quantum_backend_execution_flag"] is True for record in qch)
    assert all(record["no_quantum_simulator_execution_flag"] is True for record in qch)
    assert all(record["no_optimizer_execution_flag"] is True for record in qch)
    assert all(record["no_quantum_advantage_claim_flag"] is True for record in qch)
    assert all(record["future_live_promotion_route"] == list(c.FUTURE_LIVE_PROMOTION_LADDER) for record in qch)
    assert all(record["no_atomicrows_final_bundle_created_flag"] is True for record in compat)
    assert all(record["no_atomicrows_bundle_jsonl_created_flag"] is True for record in compat)
    assert all(record["no_atomicrows_bundle_sha_reference_created_flag"] is True for record in compat)


def test_pr161f_agent_workflow_contracts_and_failure_policy() -> None:
    workflow = _records("PR161F_QTTAgentWorkflowOrchestrationContract.report.json")
    role_io = _records("PR161F_QTTAgentRoleIOContract.report.json")
    handoffs = _records("PR161F_QTTAgentHandoffMatrix.report.json")
    failures = _records("PR161F_QTTAgentFailureResponseMatrix.report.json")
    receipts = _records("PR161F_QTTAgentTaskReceiptLedger.report.json")
    communication = _records("PR161F_QTTAgentCommunicationProtocol.report.json")
    kpi = _records("PR161F_QTTAgentKPIReadinessBridge.report.json")
    retry = _records("PR161F_QTTAgentRetryRerouteQuarantinePolicy.report.json")
    owner_escalation = _records("PR161F_QTTAgentOwnerEscalationQueue.report.json")
    agent_tasks = _records("PR161F_AgentRunTaskQueue.report.json")

    assert {record["agent_role_id"] for record in workflow} == set(c.AGENT_ROLES)
    assert {record["agent_role_id"] for record in role_io} == set(c.AGENT_ROLES)
    assert sum(record["logical_task_count_for_role"] for record in agent_tasks) == 87461
    assert {record["agent_role_id"] for record in agent_tasks} == set(c.AGENT_ROLES)

    for record in role_io:
        assert record["upstream_required_inputs"]
        assert record["output_artifacts"]
        assert record["live_authority_allowed_flag"] is False
        assert record["self_authorizing_trading_allowed_flag"] is False
        assert record["permission_expansion_allowed_flag"] is False
        assert record["source_evidence_bypass_allowed_flag"] is False
        assert record["owner_approval_bypass_allowed_flag"] is False
        assert record["live_write_secret_grant_allowed_flag"] is False

    assert all(record["source_agent_role"] in c.AGENT_ROLES for record in handoffs)
    assert all(record["target_agent_role"] in c.AGENT_ROLES for record in handoffs)
    assert all(record["handoff_state"] in c.HANDOFF_STATES for record in handoffs)
    assert {record["failure_class"] for record in failures} == set(c.FAILURE_CLASSES)
    assert all(record["safe_next_action"] for record in failures)
    assert all(record["forbidden_next_action"] for record in failures)
    assert any(record["failure_class"] == "AGENT_DUTY_MISSED" for record in failures)
    assert any(record["failure_class"] == "AGENT_OUTPUT_LOW_TRUST" and record["quarantine_required"] for record in failures)
    assert any(record["owner_review_required"] for record in failures)
    assert receipts and communication and kpi and retry and owner_escalation


def test_pr161f_candidate_lanes_and_authority_audits() -> None:
    online = _records("PR161F_OnlineCandidateIntake.report.json")
    missing = _records("PR161F_MissingValueCandidateMaterialization.report.json")
    capability = _records("PR161F_ExecutorCapabilityDiscovery.report.json")
    historical = _records("PR161F_HistoricalDataCandidateDiscovery.report.json")
    dataset = _records("PR161F_DatasetAuthorityClassification.report.json")
    forbidden = _records("PR161F_ForbiddenAuthorityScan.report.json")[0]
    hardcoded = _records("PR161F_NoScatteredHardcodedAuthorityAudit.report.json")[0]

    assert all(record["candidate_only_flag"] is True for record in online)
    assert all(record["result_evidence_created_flag"] is False for record in online)
    assert all(record["promotion_blocker"] for record in missing)
    assert all(record["owner_review_required_flag"] is True for record in missing)
    assert {record["dataset_authority_class"] for record in dataset} == set(c.DATASET_AUTHORITY_CLASSES)
    assert any(record["executor_capability_state"] == "SYNTHETIC_SMOKE_RUN_AVAILABLE" for record in capability)
    assert historical
    assert forbidden["scan_status"] == "PASS"
    assert hardcoded["audit_status"] == "PASS"


def test_pr161f_schemas_shards_size_branch_context_and_validation_gate_wiring() -> None:
    schemas = load_all_schemas(REPO_ROOT)
    assert set(schemas) == set(c.SCHEMA_FILENAMES)
    for schema in schemas.values():
        for field, expected_values in c.SCHEMA_ENUM_FIELDS.items():
            properties = schema.get("properties", {})
            if field in properties and "enum" in properties[field]:
                assert tuple(properties[field]["enum"]) == tuple(expected_values)

    manifest = _payload("PR161F_ReportShardManifest.report.json")
    for shard_ref in manifest["all_shard_files"]:
        assert "\\" not in shard_ref
        assert normalize_shard_ref(REPO_ROOT, shard_ref.replace("/", "\\")) == shard_ref
    with pytest.raises(ValueError):
        normalize_shard_ref(REPO_ROOT, "../outside.json")
    with pytest.raises(ValueError):
        normalize_shard_ref(REPO_ROOT, str(REPO_ROOT / "absolute.json"))

    size = _records("PR161F_SizeAudit.report.json")[0]
    assert size["total_pr161f_generated_footprint_bytes"] < c.GENERATED_FOOTPRINT_TARGET_BYTES
    assert size["largest_pr161f_shard_size_bytes"] < c.LARGEST_SHARD_TARGET_BYTES

    branch = c.EXPECTED_BRANCH
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161F_FinalSummary.report.json",
    )
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation/validator.py",
    )
    assert not ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )

    command_names = [Path(command[1]).name for command in run_validation_gates.build_validation_commands()]
    assert "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py" in command_names
