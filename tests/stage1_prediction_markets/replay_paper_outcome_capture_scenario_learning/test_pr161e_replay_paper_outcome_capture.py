from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning import constants as c
from src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.compact_records import (
    COMPACT_RECORD_VERSION,
    COMPACTED_REPORT_FILENAMES,
    expand_payload_records,
)
from src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.json_io import records_from_payload
from src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.online_metric_candidate_intake import (
    build_records as build_online_metric_candidates,
)
from src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.paths import (
    normalize_shard_ref,
)
from src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.schema_loader import (
    load_all_schemas,
)
from src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.validator import (
    validate_artifacts,
)
from tools import ci_branch_context


REPO_ROOT = Path(__file__).resolve().parents[3]


def _report(filename: str) -> dict:
    return json.loads((REPO_ROOT / c.GENERATED_DIR / filename).read_text(encoding="utf-8"))


def _records(filename: str) -> list[dict]:
    payload = _report(filename)
    shared_dictionary = _shared_dictionary()
    if not payload.get("sharded_flag"):
        return expand_payload_records(payload, shared_dictionary)
    manifest_record = _shard_manifest_record(filename)
    merged: list[dict] = []
    for shard_ref in manifest_record["shard_files"]:
        normalized = normalize_shard_ref(REPO_ROOT, shard_ref)
        shard_payload = json.loads((REPO_ROOT / normalized).read_text(encoding="utf-8"))
        merged.extend(expand_payload_records(shard_payload, shared_dictionary))
    return merged


def _shared_dictionary() -> dict:
    return _report(c.SHARED_DICTIONARY_REPORT_FILENAME)["shared_dictionary"]


def _shard_manifest_record(filename: str) -> dict:
    manifest = _report("PR161E_ReportShardManifest.report.json")
    matches = [
        record
        for record in records_from_payload(manifest)
        if record["report_filename"] == filename
    ]
    assert len(matches) == 1
    return matches[0]


def test_pr161e_validator_passes_and_upstream_counts_are_loaded():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures
    summary = _report("PR161E_FinalSummary.report.json")

    assert summary["pr136_artifacts_consumed_status"] == "PASS"
    assert summary["pr137r_pr138_artifacts_consumed_status"] == "PASS"
    assert summary["pr161c_inventory_qku_count_loaded"] == 9360
    assert summary["pr161c_graph_node_count_loaded"] == 9360
    assert summary["pr161c_graph_edge_count_loaded"] == 60375
    assert summary["pr161d_replay_paper_scenario_count_loaded"] == 9360
    assert summary["pr161d_bundle_candidate_count_loaded"] == 1861
    assert summary["pr161d_scenario_matrix_count_loaded"] == 1861
    assert summary["pr161d_result_backed_ranking_slot_count_loaded"] == 9360


def test_pending_mode_deterministic_counts_and_no_fake_results():
    summary = _report("PR161E_FinalSummary.report.json")
    assert summary["validated_replay_result_packets_count"] == 0
    assert summary["validated_paper_result_packets_count"] == 0
    assert summary["outcome_capture_registry_count"] == 9360
    assert summary["bundle_result_ledger_count"] == 1861
    assert summary["profitability_ledger_count"] == 9360
    assert summary["scenario_attribution_record_count"] == 1861
    assert summary["result_backed_ranking_update_candidate_count"] == 9360
    assert summary["future_profitability_pattern_update_candidate_count"] == 1861
    assert summary["quantum_classical_hybrid_outcome_comparison_count"] == 4525
    assert summary["atomicrows_pr154_result_compatibility_record_count"] == 4525
    assert summary["agent_outcome_task_queue_count"] == 87461
    assert summary["owner_review_result_promotion_queue_count"] == 9149
    assert summary["replay_paper_result_fabricated_flag"] is False
    assert summary["replay_paper_performance_evidence_fabricated_flag"] is False

    first_outcome = _records("PR161E_ReplayPaperOutcomeCaptureRegistry.report.json")[0]
    assert first_outcome["result_state"] == "NO_RESULT_YET"
    assert first_outcome["profitability_label"] == "UNOBSERVED"
    assert first_outcome["result_evidence_weight"] == 0
    assert first_outcome["result_backed_score"] is None
    assert first_outcome["no_profit_evidence_created_without_validated_result_packet_flag"] is True


def test_result_discovery_distinguishes_schemas_fixtures_and_pre_result_surfaces():
    discovery = _records("PR161E_ReplayPaperResultArtifactDiscovery.report.json")
    classes = {record["source_artifact_class"] for record in discovery}
    assert "SCHEMA_ONLY_ARTIFACT" in classes
    assert "SYNTHETIC_TEST_FIXTURE_RESULT_PACKET" in classes
    assert "CONTRACT_ONLY_ARTIFACT" in classes
    assert "PRE_RESULT_RANKING_ARTIFACT" in classes
    assert all(record["treated_as_qtt_result_evidence_flag"] is False for record in discovery)

    authenticity = _records("PR161E_ResultAuthenticityClassification.report.json")
    assert len(authenticity) == len(discovery)
    assert all(record["evidence_state"] == "NO_EVIDENCE" for record in authenticity)


def test_authority_boundaries_for_qch_atomicrows_agents_and_summary():
    summary = _report("PR161E_FinalSummary.report.json")
    assert summary["live_authority_created_flag"] is False
    assert summary["optimizer_execution_created_flag"] is False
    assert summary["quantum_backend_or_simulator_execution_created_flag"] is False
    assert summary["atomicrows_final_bundle_created_flag"] is False
    assert summary["atomicrows_bundle_jsonl_created_flag"] is False
    assert summary["atomicrows_bundle_sha_reference_created_flag"] is False
    assert summary["atomicrows_bundle_hash_sha_freeze_authority_created_flag"] is False
    assert summary["qtt_sha_or_generated_sha_authority_created_flag"] is False
    assert summary["qtt_freeze_checksum_global_digest_authority_created_flag"] is False
    assert summary["live_profit_evidence_or_profit_guarantee_created_flag"] is False

    qch = _records("PR161E_QuantumClassicalHybridOutcomeComparison.report.json")[0]
    assert qch["no_quantum_backend_execution_flag"] is True
    assert qch["no_quantum_simulator_execution_flag"] is True
    assert qch["no_optimizer_execution_flag"] is True
    assert qch["no_quantum_advantage_claim_flag"] is True

    compat = _records("PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json")[0]
    assert compat["no_atomicrows_final_bundle_created_flag"] is True
    assert compat["no_atomicrows_bundle_jsonl_created_flag"] is True
    assert compat["no_atomicrows_bundle_sha_reference_created_flag"] is True
    assert compat["no_atomicrows_bundle_hash_sha_freeze_authority_created_flag"] is True

    task = _records("PR161E_AgentOutcomeTaskQueue.report.json")[0]
    assert task["agent_task_state"] in c.AGENT_TASK_STATES
    assert task["canonical_agent_role_not_runtime_agent_claim_flag"] is True


def test_online_candidates_are_candidate_only_and_unavailable_is_non_blocking():
    online = _records("PR161E_OnlineMetricCandidateIntake.report.json")
    assert len(online) == 10
    assert all(record["candidate_only_flag"] is True for record in online)
    assert all(record["result_evidence_created_flag"] is False for record in online)
    assert build_online_metric_candidates(False) == []

    missing = _records("PR161E_MissingValueCandidateMaterialization.report.json")
    assert missing
    assert all(record["promoted_beyond_candidate_or_replay_paper_scope_flag"] is False for record in missing)
    assert all(record["owner_review_required_flag"] is True for record in missing)


def test_graph_coverage_orphan_audit_and_traceability_pass():
    trace = _records("PR161E_QKUGraphTraceabilityBridge.report.json")
    assert len(trace) == 9360
    assert all(record["qku_graph_node_id"] for record in trace[:100])

    coverage = _records("PR161E_QKUCoverageAndOrphanAudit.report.json")
    assert all(record["coverage_status"] == "PASS" for record in coverage)
    assert any(record["coverage_dimension"] == "PRIMARY_QKU_COVERAGE" for record in coverage)
    assert any(record["coverage_dimension"] == "QUANTUM_QKU_COVERAGE" for record in coverage)


def test_schema_enum_parity_and_shard_path_portability():
    schemas = load_all_schemas(REPO_ROOT)
    for schema in schemas.values():
        properties = schema.get("properties", {})
        for field, expected_values in c.SCHEMA_ENUM_FIELDS.items():
            if field in properties and "enum" in properties[field]:
                assert tuple(properties[field]["enum"]) == tuple(expected_values)

    manifest = _report("PR161E_ReportShardManifest.report.json")
    assert manifest["report_sharding_status"] == "SHARDED_LARGE_REPORTS_UNDER_50_MB"
    assert manifest["all_shard_refs_posix_flag"] is True
    for record in records_from_payload(manifest):
        for shard_ref in record["shard_files"]:
            assert "\\" not in shard_ref
            assert normalize_shard_ref(REPO_ROOT, shard_ref) == shard_ref
            assert normalize_shard_ref(REPO_ROOT, shard_ref.replace("/", "\\")) == shard_ref

    for bad_ref in ("/abs/path.json", "C:/abs/path.json", r"\\server\share\file.json", "../escape.json"):
        with pytest.raises(ValueError):
            normalize_shard_ref(REPO_ROOT, bad_ref)


def test_compact_dictionary_refs_resolve_and_preserve_traceability():
    shared_dictionary = _shared_dictionary()
    assert set(shared_dictionary["compacted_report_filenames"]) == COMPACTED_REPORT_FILENAMES
    assert shared_dictionary["qku_trace_index_count"] == 9360
    assert shared_dictionary["no_binary_compression_flag"] is True
    assert shared_dictionary["external_storage_used_flag"] is False

    manifest_record = _shard_manifest_record("PR161E_AgentOutcomeTaskQueue.report.json")
    shard_ref = manifest_record["shard_files"][0]
    shard_payload = json.loads((REPO_ROOT / shard_ref).read_text(encoding="utf-8"))
    compact_record = records_from_payload(shard_payload)[0]
    compact_with_defaults = {
        **shard_payload["compact_record_defaults"],
        **compact_record,
    }

    assert shard_payload["compact_records_flag"] is True
    assert shard_payload["compact_record_version"] == COMPACT_RECORD_VERSION
    assert shard_payload["shared_dictionary_ref"] == c.SHARED_DICTIONARY_REPORT_PATH.as_posix()
    assert compact_with_defaults["schema_ref"] in shared_dictionary["schema_refs"]
    assert compact_with_defaults["policy_ref"] in shared_dictionary["policy_flag_groups"]
    assert compact_with_defaults["authority_boundary_ref"] in shared_dictionary["authority_boundary_groups"]
    assert compact_with_defaults["route_ref"] in shared_dictionary["route_groups"]
    assert compact_with_defaults["agent_route_ref"] in shared_dictionary["agent_route_groups"]
    assert compact_record["qku_id"] in shared_dictionary["qku_trace_index"]

    expanded = expand_payload_records(shard_payload, shared_dictionary)[0]
    assert expanded["record_id"] == compact_record["record_id"]
    assert expanded["qku_id"] == compact_record["qku_id"]
    assert expanded["assigned_agent_role"] == compact_record["agent_role_if_applicable"]
    assert expanded["source_task_id"] == expanded["pr161d_agent_task_ref_if_available"]
    assert expanded["downstream_workflow_routes"] == [
        "PR161E_REPLAY_PAPER_OUTCOME_CAPTURE",
        "PR161E_SCENARIO_LEARNING_BRIDGE",
    ]
    assert expanded["downstream_process_routes"] == [
        "RESULT_PACKET_VALIDATION",
        "OWNER_REVIEW_RESULT_PROMOTION_QUEUE",
    ]


def test_large_report_top_levels_are_compact_shard_indexes():
    expected_counts = {
        "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json": 9360,
        "PR161E_QKUBundleResultLedger.report.json": 1861,
        "PR161E_QKUReplayPaperProfitabilityLedger.report.json": 9360,
        "PR161E_QKUScenarioResultAttribution.report.json": 1861,
        "PR161E_QKUResultBackedRankingUpdateCandidates.report.json": 9360,
        "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json": 1861,
        "PR161E_QuantumClassicalHybridOutcomeComparison.report.json": 4525,
        "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json": 4525,
        "PR161E_ResultConfidenceGate.report.json": 9360,
        "PR161E_OwnerReviewResultPromotionQueue.report.json": 9149,
        "PR161E_AgentOutcomeTaskQueue.report.json": 87461,
        "PR161E_QKUGraphTraceabilityBridge.report.json": 9360,
    }
    manifest = _report("PR161E_ReportShardManifest.report.json")
    manifest_filenames = {record["report_filename"] for record in records_from_payload(manifest)}
    assert set(expected_counts) <= manifest_filenames

    for filename, expected_count in expected_counts.items():
        payload = _report(filename)
        manifest_record = _shard_manifest_record(filename)
        assert payload["records"] == []
        assert payload["sharded_flag"] is True
        assert payload["compact_records_flag"] is True
        assert payload["shared_dictionary_ref"] == c.SHARED_DICTIONARY_REPORT_PATH.as_posix()
        assert payload["full_records_only_in_shards_flag"] is False
        assert payload["full_records_resolvable_from_compact_records_flag"] is True
        assert payload["total_record_count"] == expected_count
        assert payload["record_count"] == expected_count
        assert payload["shard_manifest_ref"] == c.SHARD_MANIFEST_REPORT_PATH.as_posix()
        assert payload["schema_ref"] == manifest_record["schema_ref"]
        assert payload["summary_counts"]["total_records"] == expected_count
        assert sum(manifest_record["shard_record_counts"]) == expected_count
        assert manifest_record["shard_count"] == len(manifest_record["shard_files"])
        assert manifest_record["compact_records_canonical_flag"] is True


def test_generated_byte_footprint_and_shard_sizes_are_reduced():
    top_level_reports = [
        path
        for path in (REPO_ROOT / c.GENERATED_DIR).glob("*PR161E*.report.json")
        if path.is_file()
    ]
    shard_files = [
        path
        for path in (REPO_ROOT / c.SHARD_DIR).glob("*.json")
        if path.is_file()
    ]
    total_bytes = sum(path.stat().st_size for path in [*top_level_reports, *shard_files])
    largest_top_level = max(path.stat().st_size for path in top_level_reports)
    largest_shard = max(path.stat().st_size for path in shard_files)

    assert total_bytes < 75 * 1024 * 1024
    assert largest_top_level < 5 * 1024 * 1024
    assert largest_shard < 5 * 1024 * 1024


def test_forbidden_authority_and_no_scattered_audits_pass():
    forbidden = _records("PR161E_ForbiddenAuthorityScan.report.json")[0]
    hardcoded = _records("PR161E_NoScatteredHardcodedAuthorityAudit.report.json")[0]
    assert forbidden["scan_status"] == "PASS"
    assert forbidden["source_evidence_digest_exception_limited_to_packet_integrity_flag"] is True
    assert hardcoded["audit_status"] == "PASS"


def test_branch_context_and_run_validation_gates_include_pr161e():
    branch = c.EXPECTED_BRANCH
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161E_FinalSummary.report.json",
    )
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr161e_replay_paper_outcome_capture_shards/PR161E_AgentOutcomeTaskQueue.report.shard_0001.json",
    )
    assert not ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )
    run_gates_text = (REPO_ROOT / "tools/run_validation_gates.py").read_text(encoding="utf-8")
    assert "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py" in run_gates_text
    assert c.PR152_AUDIT_REPORT_PATH.as_posix() == "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
