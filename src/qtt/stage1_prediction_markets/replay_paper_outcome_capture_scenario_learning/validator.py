"""PR161E artifact validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import constants as c
from .compact_records import (
    COMPACT_RECORD_VERSION,
    COMPACTED_REPORT_FILENAMES,
    SHARED_DICTIONARY_VERSION,
    expand_payload_records,
)
from .json_io import records_from_payload
from .models import ValidationResult
from .paths import normalize_shard_ref, resolve_repo_relative
from .schema_loader import load_all_schemas


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR161E report: {path}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            failures.append(f"PR161E report is not an object: {path}")
            continue
        reports[filename] = payload
    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))

    schemas = _load_schemas(repo_root, failures)
    if schemas:
        _validate_schema_enum_parity(schemas, failures)

    manifest = reports["PR161E_ReportShardManifest.report.json"]
    summary = reports["PR161E_FinalSummary.report.json"]
    shared_dictionary = _load_shared_dictionary(
        reports[c.SHARED_DICTIONARY_REPORT_FILENAME],
        failures,
    )
    manifest_by_report = _manifest_by_report(manifest, failures)
    _validate_manifest_paths(repo_root, reports, manifest_by_report, shared_dictionary, failures)

    preflight_records = _load_records(
        repo_root,
        "PR161E_ReplayPaperOutcomeCapturePreflightReceipt.report.json",
        reports["PR161E_ReplayPaperOutcomeCapturePreflightReceipt.report.json"],
        manifest_by_report,
        shared_dictionary,
        failures,
    )
    discovery = _load_records(repo_root, "PR161E_ReplayPaperResultArtifactDiscovery.report.json", reports["PR161E_ReplayPaperResultArtifactDiscovery.report.json"], manifest_by_report, shared_dictionary, failures)
    authenticity = _load_records(repo_root, "PR161E_ResultAuthenticityClassification.report.json", reports["PR161E_ResultAuthenticityClassification.report.json"], manifest_by_report, shared_dictionary, failures)
    outcome = _load_records(repo_root, "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json", reports["PR161E_ReplayPaperOutcomeCaptureRegistry.report.json"], manifest_by_report, shared_dictionary, failures)
    bundles = _load_records(repo_root, "PR161E_QKUBundleResultLedger.report.json", reports["PR161E_QKUBundleResultLedger.report.json"], manifest_by_report, shared_dictionary, failures)
    profitability = _load_records(repo_root, "PR161E_QKUReplayPaperProfitabilityLedger.report.json", reports["PR161E_QKUReplayPaperProfitabilityLedger.report.json"], manifest_by_report, shared_dictionary, failures)
    scenarios = _load_records(repo_root, "PR161E_QKUScenarioResultAttribution.report.json", reports["PR161E_QKUScenarioResultAttribution.report.json"], manifest_by_report, shared_dictionary, failures)
    ranking = _load_records(repo_root, "PR161E_QKUResultBackedRankingUpdateCandidates.report.json", reports["PR161E_QKUResultBackedRankingUpdateCandidates.report.json"], manifest_by_report, shared_dictionary, failures)
    patterns = _load_records(repo_root, "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json", reports["PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json"], manifest_by_report, shared_dictionary, failures)
    qch = _load_records(repo_root, "PR161E_QuantumClassicalHybridOutcomeComparison.report.json", reports["PR161E_QuantumClassicalHybridOutcomeComparison.report.json"], manifest_by_report, shared_dictionary, failures)
    compatibility = _load_records(repo_root, "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json", reports["PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json"], manifest_by_report, shared_dictionary, failures)
    confidence = _load_records(repo_root, "PR161E_ResultConfidenceGate.report.json", reports["PR161E_ResultConfidenceGate.report.json"], manifest_by_report, shared_dictionary, failures)
    owner_queue = _load_records(repo_root, "PR161E_OwnerReviewResultPromotionQueue.report.json", reports["PR161E_OwnerReviewResultPromotionQueue.report.json"], manifest_by_report, shared_dictionary, failures)
    agent_tasks = _load_records(repo_root, "PR161E_AgentOutcomeTaskQueue.report.json", reports["PR161E_AgentOutcomeTaskQueue.report.json"], manifest_by_report, shared_dictionary, failures)
    online = _load_records(repo_root, "PR161E_OnlineMetricCandidateIntake.report.json", reports["PR161E_OnlineMetricCandidateIntake.report.json"], manifest_by_report, shared_dictionary, failures)
    missing = _load_records(repo_root, "PR161E_MissingValueCandidateMaterialization.report.json", reports["PR161E_MissingValueCandidateMaterialization.report.json"], manifest_by_report, shared_dictionary, failures)
    trace = _load_records(repo_root, "PR161E_QKUGraphTraceabilityBridge.report.json", reports["PR161E_QKUGraphTraceabilityBridge.report.json"], manifest_by_report, shared_dictionary, failures)
    coverage = _load_records(repo_root, "PR161E_QKUCoverageAndOrphanAudit.report.json", reports["PR161E_QKUCoverageAndOrphanAudit.report.json"], manifest_by_report, shared_dictionary, failures)
    forbidden_records = _load_records(repo_root, "PR161E_ForbiddenAuthorityScan.report.json", reports["PR161E_ForbiddenAuthorityScan.report.json"], manifest_by_report, shared_dictionary, failures)
    hardcoded_records = _load_records(repo_root, "PR161E_NoScatteredHardcodedAuthorityAudit.report.json", reports["PR161E_NoScatteredHardcodedAuthorityAudit.report.json"], manifest_by_report, shared_dictionary, failures)
    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))
    preflight = preflight_records[0]
    forbidden = forbidden_records[0]
    hardcoded = hardcoded_records[0]

    _expect(preflight["active_branch"] == c.EXPECTED_BRANCH, failures, "preflight branch must be PR161E branch")
    _expect(preflight["git_sha_is_vcs_metadata_only_flag"] is True, failures, "git SHA must be VCS metadata only")
    _expect(preflight["pr136_route_triage_consumed_flag"] is True, failures, "PR136 route triage must be consumed")
    _expect(preflight["pr136_crosswalk_consumed_flag"] is True, failures, "PR136 crosswalk must be consumed")
    _expect(preflight["pr136_market_index_consumed_flag"] is True, failures, "PR136 market index must be consumed")
    _expect(preflight["pr136_command_action_consumed_flag"] is True, failures, "PR136 command action must be consumed")
    _expect(preflight["pr137r_atomicrows_reconciliation_consumed_flag"] is True, failures, "PR137R must be consumed")
    _expect(preflight["pr138_atomicrows_semantic_contract_consumed_flag"] is True, failures, "PR138 must be consumed")

    expected = c.DETERMINISTIC_PENDING_COUNTS
    _expect(len(outcome) == expected["outcome_capture_registry"], failures, "outcome capture count must be 9360")
    _expect(len(bundles) == expected["bundle_result_ledger"], failures, "bundle ledger count must be 1861")
    _expect(len(profitability) == expected["profitability_ledger"], failures, "profitability ledger count must be 9360")
    _expect(len(scenarios) == expected["scenario_result_attribution"], failures, "scenario attribution count must be 1861")
    _expect(len(ranking) == expected["result_backed_ranking_update_candidates"], failures, "ranking update count must be 9360")
    _expect(len(patterns) == expected["future_profitability_pattern_update_candidates"], failures, "future pattern count must be 1861")
    _expect(len(qch) == expected["quantum_classical_hybrid_outcome_comparison"], failures, "QCH comparison count must be 4525")
    _expect(len(compatibility) == expected["atomicrows_pr154_result_compatibility_bridge"], failures, "AtomicRows/PR154 result compatibility count must be 4525")
    _expect(len(agent_tasks) == expected["agent_outcome_task_queue"], failures, "agent outcome task count must be 87461")
    _expect(len(owner_queue) == expected["owner_review_result_promotion_queue"], failures, "owner review queue count must be 9149")
    _expect(len(confidence) == expected["outcome_capture_registry"], failures, "confidence gate count must match outcome capture count")
    _expect(len(trace) == c.EXPECTED_PR161C_COUNTS["primary_qku_count"], failures, "traceability must cover all QKUs")

    _expect(any(record["source_artifact_class"] == "SCHEMA_ONLY_ARTIFACT" for record in discovery), failures, "discovery must distinguish schema artifacts")
    _expect(any(record["source_artifact_class"] == "SYNTHETIC_TEST_FIXTURE_RESULT_PACKET" for record in discovery), failures, "discovery must distinguish fixtures")
    _expect(len(authenticity) == len(discovery), failures, "authenticity count must match discovery count")
    _expect(summary["validated_replay_result_packets_count"] == 0, failures, "validated replay count must be zero in pending mode")
    _expect(summary["validated_paper_result_packets_count"] == 0, failures, "validated paper count must be zero in pending mode")

    for record in [*outcome, *profitability, *ranking, *patterns]:
        _expect(record["profitability_label"] == "UNOBSERVED", failures, f"profitability label observed without result: {record['record_id']}")
        _expect(record["result_evidence_weight"] == 0, failures, f"evidence weight nonzero without result: {record['record_id']}")
        _expect(record["result_backed_score"] is None, failures, f"result-backed score populated without result: {record['record_id']}")
        _expect(record["no_profit_evidence_created_without_validated_result_packet_flag"] is True, failures, f"profit evidence boundary missing: {record['record_id']}")
    for record in scenarios:
        _expect(record["gross_profit"] is None, failures, f"scenario gross profit populated: {record['record_id']}")
        _expect(record["net_profit_after_fees"] is None, failures, f"scenario net profit populated: {record['record_id']}")
        _expect(record["max_drawdown"] is None, failures, f"scenario drawdown populated: {record['record_id']}")
    for record in qch:
        _expect(record["no_quantum_backend_execution_flag"] is True, failures, f"QCH backend execution claim: {record['record_id']}")
        _expect(record["no_quantum_simulator_execution_flag"] is True, failures, f"QCH simulator execution claim: {record['record_id']}")
        _expect(record["no_optimizer_execution_flag"] is True, failures, f"QCH optimizer execution claim: {record['record_id']}")
        _expect(record["no_quantum_advantage_claim_flag"] is True, failures, f"QCH advantage claim: {record['record_id']}")
    for record in compatibility:
        _expect(record["no_atomicrows_final_bundle_created_flag"] is True, failures, f"AtomicRows final bundle created: {record['record_id']}")
        _expect(record["no_atomicrows_bundle_jsonl_created_flag"] is True, failures, f"AtomicRows jsonl created: {record['record_id']}")
        _expect(record["no_atomicrows_bundle_sha_reference_created_flag"] is True, failures, f"AtomicRows bundle SHA reference created: {record['record_id']}")
        _expect(record["no_atomicrows_bundle_hash_sha_freeze_authority_created_flag"] is True, failures, f"AtomicRows bundle hash/SHA/freeze authority created: {record['record_id']}")
    for record in agent_tasks:
        _expect(record["agent_task_state"] in c.AGENT_TASK_STATES, failures, f"invalid agent task state: {record['record_id']}")
        _expect(record["canonical_agent_role_not_runtime_agent_claim_flag"] is True, failures, f"runtime agent claim: {record['record_id']}")
    for record in online:
        _expect(record["candidate_only_flag"] is True, failures, f"online source promoted beyond candidate: {record['record_id']}")
        _expect(record["result_evidence_created_flag"] is False, failures, f"online source created result evidence: {record['record_id']}")
    for record in missing:
        _expect(record["promoted_beyond_candidate_or_replay_paper_scope_flag"] is False, failures, f"missing value promoted: {record['record_id']}")
        _expect(record["value_authority_class"] in c.AUTHORITY_CLASSES, failures, f"invalid missing value authority class: {record['record_id']}")

    covered_qkus = {record["qku_id"] for record in profitability}
    _expect(len(covered_qkus) == c.EXPECTED_PR161C_COUNTS["primary_qku_count"], failures, "all 9360 QKUs must be covered")
    _expect(all(record["unmappable_reason_if_any"] is None for record in profitability), failures, "profitability records must not be orphaned")
    _expect(all(record["coverage_status"] == "PASS" for record in coverage), failures, "coverage audit must pass")
    _expect(forbidden["scan_status"] == "PASS", failures, "forbidden authority scan must pass")
    _expect(hardcoded["audit_status"] == "PASS", failures, "no-scattered audit must pass")
    _expect(summary["master_plan_file_edited_flag"] is False, failures, "master plan source must not be edited")
    _expect(summary["global_rename_performed_flag"] is False, failures, "global rename must not be performed")
    _expect(summary["largest_generated_pr161e_report_size_bytes"] < c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES, failures, "largest PR161E report must be under GitHub warning threshold")
    return ValidationResult(ok=not failures, failures=tuple(failures))


def _load_records(
    repo_root: Path,
    filename: str,
    payload: dict[str, Any],
    manifest_by_report: dict[str, dict[str, Any]],
    shared_dictionary: dict[str, Any],
    failures: list[str],
) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        records = expand_payload_records(payload, shared_dictionary)
        _expect(
            int(payload.get("record_count", len(records))) == len(records),
            failures,
            f"unsharded record_count must match records for {filename}",
        )
        return records
    manifest_record = manifest_by_report.get(filename)
    if manifest_record is None:
        failures.append(f"missing shard manifest record for sharded report: {filename}")
        return []
    _expect(records_from_payload(payload) == [], failures, f"sharded top-level records must be empty: {filename}")
    _expect(
        payload.get("shard_manifest_ref") == c.SHARD_MANIFEST_REPORT_PATH.as_posix(),
        failures,
        f"sharded report must reference PR161E shard manifest: {filename}",
    )
    merged: list[dict[str, Any]] = []
    for shard_ref in manifest_record.get("shard_files") or []:
        normalized = normalize_shard_ref(repo_root, shard_ref)
        shard_payload = json.loads(resolve_repo_relative(repo_root, normalized).read_text(encoding="utf-8"))
        try:
            merged.extend(expand_payload_records(shard_payload, shared_dictionary))
        except ValueError as exc:
            failures.append(str(exc))
    _expect(
        int(manifest_record.get("total_record_count", -1)) == len(merged),
        failures,
        f"manifest total_record_count must match merged shards for {filename}",
    )
    _expect(
        int(payload.get("total_record_count", -1)) == len(merged),
        failures,
        f"sharded top-level total_record_count must match merged shards for {filename}",
    )
    return merged


def _load_shared_dictionary(
    payload: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    shared_dictionary = payload.get("shared_dictionary")
    if not isinstance(shared_dictionary, dict):
        failures.append("PR161E shared dictionary report missing shared_dictionary object")
        return {}
    _expect(
        shared_dictionary.get("dictionary_version") == SHARED_DICTIONARY_VERSION,
        failures,
        "PR161E shared dictionary version mismatch",
    )
    _expect(
        shared_dictionary.get("compact_record_version") == COMPACT_RECORD_VERSION,
        failures,
        "PR161E compact record version mismatch",
    )
    _expect(
        set(shared_dictionary.get("compacted_report_filenames", [])) == COMPACTED_REPORT_FILENAMES,
        failures,
        "PR161E shared dictionary compacted report list mismatch",
    )
    _expect(
        int(shared_dictionary.get("qku_trace_index_count", -1))
        == c.EXPECTED_PR161C_COUNTS["primary_qku_count"],
        failures,
        "PR161E shared dictionary qku trace index count must cover all QKUs",
    )
    _expect(
        payload.get("record_count") == 0 and payload.get("records") == [],
        failures,
        "PR161E shared dictionary report must not duplicate records",
    )
    _expect(
        payload.get("no_authority_confirmation", {}).get("qtt_sha_authority_created") is False,
        failures,
        "PR161E shared dictionary no_qtt_sha_authority_created flag must remain false",
    )
    _expect(
        shared_dictionary.get("no_binary_compression_flag") is True,
        failures,
        "PR161E shared dictionary must use plain JSON, not binary compression",
    )
    _expect(
        shared_dictionary.get("external_storage_used_flag") is False,
        failures,
        "PR161E shared dictionary must not use external storage",
    )
    return shared_dictionary


def _load_schemas(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    try:
        return load_all_schemas(repo_root)
    except FileNotFoundError as exc:
        failures.append(f"missing PR161E schema: {exc}")
    except ValueError as exc:
        failures.append(str(exc))
    return {}


def _validate_schema_enum_parity(schemas: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, schema in schemas.items():
        properties = schema.get("properties", {})
        for field, expected_values in c.SCHEMA_ENUM_FIELDS.items():
            if field not in properties:
                continue
            actual = properties[field].get("enum")
            if actual is None:
                continue
            _expect(tuple(actual) == tuple(expected_values), failures, f"schema enum parity failed for {filename}:{field}")


def _manifest_by_report(manifest: dict[str, Any], failures: list[str]) -> dict[str, dict[str, Any]]:
    records = records_from_payload(manifest)
    by_report: dict[str, dict[str, Any]] = {}
    for record in records:
        report_filename = record.get("report_filename")
        if not isinstance(report_filename, str):
            failures.append("shard manifest record missing report_filename")
            continue
        if report_filename in by_report:
            failures.append(f"duplicate shard manifest record: {report_filename}")
            continue
        by_report[report_filename] = record
    return by_report


def _validate_manifest_paths(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    manifest_by_report: dict[str, dict[str, Any]],
    shared_dictionary: dict[str, Any],
    failures: list[str],
) -> None:
    expected_manifest_reports = {
        filename for filename, payload in reports.items() if payload.get("sharded_flag")
    }
    _expect(
        set(manifest_by_report) == expected_manifest_reports,
        failures,
        "shard manifest must list exactly the sharded PR161E reports",
    )
    for report_filename, record in manifest_by_report.items():
        payload = reports.get(report_filename, {})
        shard_files = record.get("shard_files") or []
        shard_record_counts = record.get("shard_record_counts") or []
        _expect(record.get("report_type") == payload.get("report_type"), failures, f"manifest report_type mismatch: {report_filename}")
        _expect(record.get("schema_ref") == payload.get("schema_ref"), failures, f"manifest schema_ref mismatch: {report_filename}")
        _expect(payload.get("records") == [], failures, f"sharded report must not duplicate records: {report_filename}")
        _expect(payload.get("full_records_only_in_shards_flag") is False, failures, f"sharded report must mark compact shard mode: {report_filename}")
        _expect(payload.get("compact_records_flag") is True, failures, f"sharded report must mark compact records: {report_filename}")
        _expect(payload.get("shared_dictionary_ref") == c.SHARED_DICTIONARY_REPORT_PATH.as_posix(), failures, f"sharded report dictionary ref mismatch: {report_filename}")
        _expect(record.get("compact_records_canonical_flag") is True, failures, f"manifest must mark compact canonical records: {report_filename}")
        _expect(record.get("shared_dictionary_ref") == c.SHARED_DICTIONARY_REPORT_PATH.as_posix(), failures, f"manifest dictionary ref mismatch: {report_filename}")
        _expect(payload.get("shard_manifest_ref") == c.SHARD_MANIFEST_REPORT_PATH.as_posix(), failures, f"sharded report manifest ref mismatch: {report_filename}")
        _expect(int(record.get("shard_count", -1)) == len(shard_files), failures, f"manifest shard_count mismatch: {report_filename}")
        _expect(int(payload.get("shard_count", -1)) == len(shard_files), failures, f"payload shard_count mismatch: {report_filename}")
        _expect(payload.get("shard_files") == shard_files, failures, f"payload shard refs must mirror manifest: {report_filename}")
        _expect(sum(int(count) for count in shard_record_counts) == int(record.get("total_record_count", -1)), failures, f"manifest shard counts must sum to total: {report_filename}")
        for index, shard_ref in enumerate(shard_files, start=1):
            try:
                normalized = normalize_shard_ref(repo_root, shard_ref)
            except ValueError as exc:
                failures.append(str(exc))
                continue
            _expect("\\" not in normalized, failures, f"shard ref must use POSIX slashes: {shard_ref}")
            shard_path = repo_root / normalized
            _expect(shard_path.exists(), failures, f"shard ref must exist: {normalized}")
            if not shard_path.exists():
                continue
            shard_payload = json.loads(shard_path.read_text(encoding="utf-8"))
            shard_records = records_from_payload(shard_payload)
            _expect(shard_payload.get("parent_report_filename") == report_filename, failures, f"shard parent mismatch: {normalized}")
            _expect(shard_payload.get("compact_records_flag") is True, failures, f"shard must contain compact records: {normalized}")
            _expect(shard_payload.get("shared_dictionary_ref") == c.SHARED_DICTIONARY_REPORT_PATH.as_posix(), failures, f"shard dictionary ref mismatch: {normalized}")
            _expect(int(shard_payload.get("shard_index", -1)) == index, failures, f"shard index mismatch: {normalized}")
            _expect(int(shard_payload.get("shard_count", -1)) == len(shard_files), failures, f"shard count mismatch: {normalized}")
            _expect(int(shard_payload.get("record_count", -1)) == len(shard_records), failures, f"shard record_count mismatch: {normalized}")
            try:
                expanded_records = expand_payload_records(shard_payload, shared_dictionary)
            except ValueError as exc:
                failures.append(str(exc))
                expanded_records = []
            _expect(len(expanded_records) == len(shard_records), failures, f"expanded compact record count mismatch: {normalized}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
