"""PR161F artifact validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import constants as c
from .compact_records import COMPACT_RECORD_VERSION, SHARED_DICTIONARY_VERSION, expand_payload_records
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
            failures.append(f"missing PR161F report: {path}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            failures.append(f"PR161F report is not an object: {path}")
            continue
        reports[filename] = payload
    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))

    try:
        schemas = load_all_schemas(repo_root)
        _validate_schema_enum_parity(schemas, failures)
    except (FileNotFoundError, ValueError) as exc:
        failures.append(str(exc))

    shared_dictionary = _load_shared_dictionary(
        reports[c.SHARED_DICTIONARY_REPORT_FILENAME],
        failures,
    )
    manifest = reports["PR161F_ReportShardManifest.report.json"]
    manifest_by_report = _manifest_by_report(manifest, failures)
    _validate_manifest_paths(repo_root, reports, manifest_by_report, failures)
    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))

    loaded = {
        filename: _load_records(
            repo_root,
            filename,
            reports[filename],
            manifest_by_report,
            shared_dictionary,
            failures,
        )
        for filename in c.REPORT_FILENAMES
        if filename not in {
            c.SHARED_DICTIONARY_REPORT_FILENAME,
            "PR161F_ReportShardManifest.report.json",
        }
    }
    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))

    summary = reports["PR161F_FinalSummary.report.json"]
    preflight = loaded["PR161F_ReplayPaperExecutorInputPreflightReceipt.report.json"][0]
    forbidden = loaded["PR161F_ForbiddenAuthorityScan.report.json"][0]
    hardcoded = loaded["PR161F_NoScatteredHardcodedAuthorityAudit.report.json"][0]

    _expect(preflight["active_branch"] == c.EXPECTED_BRANCH, failures, "preflight branch must be PR161F branch")
    _expect(preflight["git_sha_is_vcs_metadata_only_flag"] is True, failures, "git SHA must be VCS metadata only")
    _expect(preflight["pr136_route_triage_consumed_flag"] is True, failures, "PR136 route triage must be consumed")
    _expect(preflight["pr136_crosswalk_consumed_flag"] is True, failures, "PR136 crosswalk must be consumed")
    _expect(preflight["pr136_market_index_consumed_flag"] is True, failures, "PR136 market index must be consumed")
    _expect(preflight["pr136_command_action_consumed_flag"] is True, failures, "PR136 command action must be consumed")
    _expect(preflight["pr137r_atomicrows_reconciliation_consumed_flag"] is True, failures, "PR137R must be consumed")
    _expect(preflight["pr138_atomicrows_semantic_contract_consumed_flag"] is True, failures, "PR138 must be consumed")

    expected = c.EXPECTED_PR161F_COUNTS
    _expect(len(loaded["PR161F_ExecutorInputRegistry.report.json"]) == expected["executor_input_records"], failures, "executor input count must be 9360")
    _expect(len(loaded["PR161F_ReplayRunRequestRegistry.report.json"]) == expected["replay_run_request_records"], failures, "replay request count must be 9360")
    _expect(len(loaded["PR161F_PaperRunRequestRegistry.report.json"]) == expected["paper_run_request_records"], failures, "paper request count must be 9360")
    _expect(len(loaded["PR161F_PairedReplayPaperRunPlan.report.json"]) == expected["paired_replay_paper_run_plan_records"], failures, "paired run plan count must be 9360")
    _expect(len(loaded["PR161F_RunArtifactEnvelopeRegistry.report.json"]) == expected["run_artifact_envelope_records"], failures, "run artifact envelope count must be 9360")
    _expect(len(loaded["PR161F_ResultPacketEmissionEligibilityGate.report.json"]) == expected["result_packet_emission_eligibility_records"], failures, "eligibility count must be 9360")
    _expect(len(loaded["PR161F_QuantumClassicalHybridRunPlan.report.json"]) == expected["quantum_classical_hybrid_run_plan_records"], failures, "QCH run plan count must be 4525")
    _expect(len(loaded["PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json"]) == expected["atomicrows_pr154_run_compatibility_records"], failures, "AtomicRows/PR154 compatibility count must be 4525")
    agent_task_report = reports["PR161F_AgentRunTaskQueue.report.json"]
    agent_task_records = loaded["PR161F_AgentRunTaskQueue.report.json"]
    _expect(int(agent_task_report.get("logical_task_count", -1)) == expected["agent_run_task_logical_count"], failures, "agent task logical count must be 87461")
    _expect(sum(int(record.get("logical_task_count_for_role", 0)) for record in agent_task_records) == expected["agent_run_task_logical_count"], failures, "compact agent task role counts must sum to 87461")
    _expect({record["agent_role_id"] for record in agent_task_records} == set(c.AGENT_ROLES), failures, "compact agent task queue must cover canonical roles")
    _expect(len(loaded["PR161F_OwnerReviewRunReadinessQueue.report.json"]) == expected["owner_review_run_readiness_records"], failures, "owner run readiness count must be 9149")
    _expect(len(loaded["PR161F_QKUEndToEndTraceabilityMatrix.report.json"]) == expected["qku_end_to_end_traceability_matrix_records"], failures, "QKU traceability count must be 9360")

    executor_qkus = {record["qku_id"] for record in loaded["PR161F_ExecutorInputRegistry.report.json"]}
    matrix_qkus = {record["qku_id"] for record in loaded["PR161F_QKUEndToEndTraceabilityMatrix.report.json"]}
    _expect(executor_qkus == matrix_qkus, failures, "every executor input must resolve to traceability matrix")
    for filename in (
        "PR161F_ReplayRunRequestRegistry.report.json",
        "PR161F_PaperRunRequestRegistry.report.json",
        "PR161F_ResultPacketEmissionEligibilityGate.report.json",
        "PR161F_RunArtifactEnvelopeRegistry.report.json",
    ):
        _expect(
            {record["qku_id"] for record in loaded[filename]} == matrix_qkus,
            failures,
            f"{filename} QKUs must resolve to traceability matrix",
        )
    qch_qkus = {record["qku_id"] for record in loaded["PR161F_QuantumClassicalHybridRunPlan.report.json"]}
    _expect(qch_qkus <= matrix_qkus, failures, "QCH QKUs must resolve to traceability matrix")

    for record in loaded["PR161F_RunArtifactEnvelopeRegistry.report.json"]:
        _expect(record["result_packet_emission_eligibility_state"] == "RESULT_PACKET_EMISSION_BLOCKED", failures, f"pending envelope emitted result packet: {record['record_id']}")
        _expect(record["no_live_connector_used_flag"] is True, failures, f"live connector boundary missing: {record['record_id']}")
        _expect(record["no_profit_evidence_created_flag"] is True, failures, f"profit evidence boundary missing: {record['record_id']}")
    for record in loaded["PR161F_SyntheticSmokeRunArtifactRegistry.report.json"]:
        _expect(record["run_artifact_class"] == "SYNTHETIC_PIPELINE_SMOKE_RUN_ARTIFACT", failures, f"synthetic smoke class missing: {record['record_id']}")
        _expect(record["treated_as_performance_evidence_flag"] is False, failures, f"synthetic smoke treated as performance: {record['record_id']}")
        _expect(record["pr161e_capture_update_allowed_flag"] is False, failures, f"synthetic smoke allowed PR161E capture: {record['record_id']}")
    for record in loaded["PR161F_QuantumClassicalHybridRunPlan.report.json"]:
        _expect(record["live_order_route_blocked_until_promotion_flag"] is True, failures, f"QCH live route not blocked: {record['record_id']}")
        _expect(record["no_quantum_backend_execution_flag"] is True, failures, f"QCH backend execution claim: {record['record_id']}")
        _expect(record["no_quantum_simulator_execution_flag"] is True, failures, f"QCH simulator execution claim: {record['record_id']}")
        _expect(record["no_optimizer_execution_flag"] is True, failures, f"QCH optimizer execution claim: {record['record_id']}")
        _expect(record["no_quantum_advantage_claim_flag"] is True, failures, f"QCH advantage claim: {record['record_id']}")
    for record in loaded["PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json"]:
        _expect(record["no_atomicrows_final_bundle_created_flag"] is True, failures, f"AtomicRows final bundle created: {record['record_id']}")
        _expect(record["no_atomicrows_bundle_jsonl_created_flag"] is True, failures, f"AtomicRows JSONL created: {record['record_id']}")
        _expect(record["no_atomicrows_bundle_sha_reference_created_flag"] is True, failures, f"AtomicRows bundle SHA reference created: {record['record_id']}")

    role_contracts = loaded["PR161F_QTTAgentRoleIOContract.report.json"]
    _expect({record["agent_role_id"] for record in role_contracts} == set(c.AGENT_ROLES), failures, "every canonical agent role must have role I/O contract")
    for record in role_contracts:
        _expect(record["upstream_required_inputs"], failures, f"agent role missing upstream inputs: {record['agent_role_id']}")
        _expect(record["output_artifacts"], failures, f"agent role missing outputs: {record['agent_role_id']}")
        _expect(record["live_authority_allowed_flag"] is False, failures, f"agent live authority allowed: {record['agent_role_id']}")
        _expect(record["self_authorizing_trading_allowed_flag"] is False, failures, f"agent self-authorizes trading: {record['agent_role_id']}")
        _expect(record["permission_expansion_allowed_flag"] is False, failures, f"agent privilege escalation allowed: {record['agent_role_id']}")
        _expect(record["source_evidence_bypass_allowed_flag"] is False, failures, f"agent source evidence bypass allowed: {record['agent_role_id']}")
        _expect(record["owner_approval_bypass_allowed_flag"] is False, failures, f"agent owner bypass allowed: {record['agent_role_id']}")
        _expect(record["live_write_secret_grant_allowed_flag"] is False, failures, f"agent live secret grant allowed: {record['agent_role_id']}")

    for record in loaded["PR161F_QTTAgentHandoffMatrix.report.json"]:
        _expect(record["source_agent_role"] in c.AGENT_ROLES, failures, f"handoff source invalid: {record['record_id']}")
        _expect(record["target_agent_role"] in c.AGENT_ROLES, failures, f"handoff target invalid: {record['record_id']}")
        _expect(record["handoff_state"] in c.HANDOFF_STATES, failures, f"handoff state invalid: {record['record_id']}")
    for record in loaded["PR161F_QTTAgentFailureResponseMatrix.report.json"]:
        _expect(record["failure_class"] in c.FAILURE_CLASSES, failures, f"failure class missing: {record['record_id']}")
        _expect(bool(record["safe_next_action"]), failures, f"failure safe action missing: {record['record_id']}")
        _expect(bool(record["forbidden_next_action"]), failures, f"failure forbidden action missing: {record['record_id']}")

    online = loaded["PR161F_OnlineCandidateIntake.report.json"]
    _expect(all(record["candidate_only_flag"] is True for record in online), failures, "online candidates must be candidate-only")
    _expect(all(record["result_evidence_created_flag"] is False for record in online), failures, "online candidates must not create evidence")
    missing = loaded["PR161F_MissingValueCandidateMaterialization.report.json"]
    _expect(all(record["value_authority_class"] in c.AUTHORITY_CLASSES for record in missing), failures, "missing values need authority class")
    _expect(all(record["owner_review_required_flag"] is True for record in missing), failures, "missing values need owner review")

    size_record = loaded["PR161F_SizeAudit.report.json"][0]
    _expect(size_record["total_pr161f_generated_footprint_bytes"] < c.GENERATED_FOOTPRINT_TARGET_BYTES, failures, "PR161F generated footprint must be under target")
    _expect(size_record["largest_pr161f_shard_size_bytes"] < c.LARGEST_SHARD_TARGET_BYTES, failures, "largest PR161F shard must be under target")
    _expect(forbidden["scan_status"] == "PASS", failures, "forbidden authority scan must pass")
    _expect(hardcoded["audit_status"] == "PASS", failures, "no-scattered-hardcoded audit must pass")
    _expect(summary["master_plan_file_edited_flag"] is False, failures, "master plan source must not be edited")
    _expect(summary["global_rename_performed_flag"] is False, failures, "global rename must not be performed")
    _expect(summary["live_authority_created_flag"] is False, failures, "live authority must not be created")
    _expect(summary["optimizer_execution_created_flag"] is False, failures, "optimizer execution must not be created")
    _expect(summary["quantum_backend_or_simulator_execution_created_flag"] is False, failures, "quantum backend/simulator execution must not be created")
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
        _expect(int(payload.get("record_count", len(records))) == len(records), failures, f"unsharded record_count mismatch: {filename}")
        return records
    manifest_record = manifest_by_report.get(filename)
    if manifest_record is None:
        failures.append(f"missing shard manifest record for sharded report: {filename}")
        return []
    _expect(records_from_payload(payload) == [], failures, f"sharded top-level records must be empty: {filename}")
    merged: list[dict[str, Any]] = []
    for shard_ref in manifest_record.get("shard_files") or []:
        normalized = normalize_shard_ref(repo_root, shard_ref)
        shard_payload = json.loads(resolve_repo_relative(repo_root, normalized).read_text(encoding="utf-8"))
        merged.extend(expand_payload_records(shard_payload, shared_dictionary))
    _expect(int(manifest_record.get("total_record_count", -1)) == len(merged), failures, f"manifest total mismatch: {filename}")
    _expect(int(payload.get("total_record_count", -1)) == len(merged), failures, f"payload total mismatch: {filename}")
    return merged


def _load_shared_dictionary(payload: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    shared_dictionary = payload.get("shared_dictionary")
    if not isinstance(shared_dictionary, dict):
        failures.append("PR161F shared dictionary report missing shared_dictionary object")
        return {}
    _expect(shared_dictionary.get("dictionary_version") == SHARED_DICTIONARY_VERSION, failures, "PR161F shared dictionary version mismatch")
    _expect(shared_dictionary.get("compact_record_version") == COMPACT_RECORD_VERSION, failures, "PR161F compact record version mismatch")
    _expect(int(shared_dictionary.get("qku_trace_index_count", -1)) == c.EXPECTED_PR161C_COUNTS["primary_qku_count"], failures, "shared dictionary qku trace count must cover all QKUs")
    _expect(payload.get("record_count") == 0 and payload.get("records") == [], failures, "PR161F shared dictionary report must not duplicate records")
    _expect(shared_dictionary.get("no_binary_compression_flag") is True, failures, "PR161F shared dictionary must be plain JSON")
    _expect(shared_dictionary.get("external_storage_used_flag") is False, failures, "PR161F shared dictionary must not use external storage")
    return shared_dictionary


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
    by_report: dict[str, dict[str, Any]] = {}
    for record in records_from_payload(manifest):
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
    failures: list[str],
) -> None:
    expected_manifest_reports = {
        filename for filename, payload in reports.items() if payload.get("sharded_flag")
    }
    _expect(set(manifest_by_report) == expected_manifest_reports, failures, "shard manifest must list exactly sharded PR161F reports")
    for report_filename, record in manifest_by_report.items():
        payload = reports.get(report_filename, {})
        shard_files = record.get("shard_files") or []
        _expect(payload.get("records") == [], failures, f"sharded report must not duplicate records: {report_filename}")
        _expect(payload.get("compact_records_flag") is True, failures, f"sharded report must mark compact records: {report_filename}")
        _expect(payload.get("shared_dictionary_ref") == c.SHARED_DICTIONARY_REPORT_PATH.as_posix(), failures, f"dictionary ref mismatch: {report_filename}")
        _expect(record.get("compact_records_canonical_flag") is True, failures, f"manifest compact flag missing: {report_filename}")
        _expect(int(record.get("shard_count", -1)) == len(shard_files), failures, f"manifest shard_count mismatch: {report_filename}")
        for index, shard_ref in enumerate(shard_files, start=1):
            try:
                normalized = normalize_shard_ref(repo_root, shard_ref)
            except ValueError as exc:
                failures.append(str(exc))
                continue
            _expect("\\" not in normalized, failures, f"shard ref must use POSIX slashes: {shard_ref}")
            shard_path = repo_root / normalized
            _expect(shard_path.exists(), failures, f"shard ref must exist: {normalized}")
            if shard_path.exists():
                shard_payload = json.loads(shard_path.read_text(encoding="utf-8"))
                _expect(shard_payload.get("parent_report_filename") == report_filename, failures, f"shard parent mismatch: {normalized}")
                _expect(int(shard_payload.get("shard_index", -1)) == index, failures, f"shard index mismatch: {normalized}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
