"""Build PR162A safe repo-local non-live dataset materialization reports."""

from __future__ import annotations

from dataclasses import dataclass
import shutil
from pathlib import Path
from typing import Any

from . import constants as c
from .agent_handoff import agent_handoff_records
from .data_quality_leakage import audit_records, missing_value_records
from .dataset_authority import dataset_records
from .dataset_mapping import (
    mapping_records,
    pr161f_coverage_records,
    pr162_rerun_readiness_records,
)
from .dataset_materialization import materialize_repo_local_datasets
from .dataset_normalization import NORMALIZED_FIELDS
from .fetch_plan import fetch_plan_records
from .forbidden_authority_scan import forbidden_scan_records
from .json_io import stable_counter, write_json
from .loaders import current_branch, ensure_required_inputs, load_pr161f_records
from .paths import repo_relative_posix
from .pr152_currentization import pr152_currentization_evidence
from .quantum_dataset_bridge import quantum_dataset_feature_records, quantum_feature_work_order_records
from .report_sharding import payloads_for_write
from .schema_writer import write_schemas
from .source_discovery import source_candidate_records


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(
    repo_root: Path,
    *,
    materialize_public_candidates: bool = False,
) -> BuildArtifacts:
    branch = current_branch(repo_root)
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR162A build must run on {c.EXPECTED_BRANCH}; current branch is {branch}")
    source_inputs = ensure_required_inputs(repo_root)
    write_schemas(repo_root)
    materialized = materialize_repo_local_datasets(repo_root)
    pr161f = load_pr161f_records(repo_root)
    payloads = build_payloads(
        repo_root,
        branch,
        source_inputs,
        pr161f,
        materialized,
        materialize_public_candidates=materialize_public_candidates,
    )
    _clear_shards(repo_root)
    main_payloads, shard_payloads, manifest_records = payloads_for_write(payloads)
    manifest_payload = _report_payload(
        "PR162A_ReportShardManifest.report.json",
        "PR162A_REPORT_SHARD_MANIFEST",
        manifest_records,
        source_inputs,
        blocker_codes=(),
    )
    manifest_payload["all_shard_files"] = [
        shard_ref
        for record in manifest_records
        for shard_ref in record.get("shard_files", [])
    ]
    manifest_payload["all_shard_refs_posix_relative_flag"] = all(
        "\\" not in ref and not Path(ref).is_absolute()
        for ref in manifest_payload["all_shard_files"]
    )
    main_payloads[c.SHARD_MANIFEST_REPORT_FILENAME] = manifest_payload
    for filename in c.REPORT_FILENAMES:
        write_json(repo_root / c.GENERATED_DIR / filename, main_payloads[filename])
    for shard_ref, shard_payload in shard_payloads.items():
        write_json(repo_root / shard_ref, shard_payload, compact=True)
    return BuildArtifacts(
        summary=main_payloads["PR162A_FinalSummary.report.json"],
        payloads=main_payloads,
    )


def build_payloads(
    repo_root: Path,
    branch: str,
    source_inputs: list[str],
    pr161f: dict[str, list[dict[str, Any]]],
    materialized: dict[str, Any],
    *,
    materialize_public_candidates: bool,
) -> dict[str, dict[str, Any]]:
    source_records = source_candidate_records()
    fetch_records = fetch_plan_records(source_records)
    _write_fetch_plan_file(repo_root, fetch_records)
    datasets = dataset_records(repo_root, materialized)
    normalized_rows = materialized["normalized_rows"]
    quality_records = audit_records(normalized_rows)
    mappings = mapping_records(pr161f, datasets)
    coverage = pr161f_coverage_records(mappings)
    rerun = pr162_rerun_readiness_records(mappings)
    mapping_by_qku = {record["qku_id"]: record for record in mappings}
    qch_records = pr161f["PR161F_QuantumClassicalHybridRunPlan.report.json"]
    quantum_bridge = quantum_dataset_feature_records(qch_records, mapping_by_qku)
    quantum_work_orders = quantum_feature_work_order_records(quantum_bridge)
    missing_values = missing_value_records(normalized_rows)
    run_capable_count = sum(1 for record in datasets if record["run_capable_flag"])
    agents = agent_handoff_records(run_capable_count)
    forbidden = forbidden_scan_records(repo_root, mappings)
    pr152_evidence = pr152_currentization_evidence(repo_root)

    dataset_authority_counts = stable_counter(record["dataset_authority_class"] for record in datasets)
    source_class_counts = stable_counter(
        source_class
        for record in source_records
        for source_class in record["source_classes"]
    )
    blocked_counts = stable_counter(
        record["blocker_code"]
        for record in datasets + source_records + mappings
        if record.get("blocker_code") and record.get("blocker_code") != "NONE"
    )
    strict_run_capable_qku_count = sum(
        1 for record in mappings if record["strict_run_capable_coverage_flag"]
    )
    seed_or_mechanics_qku_count = sum(
        1
        for record in mappings
        if record["seed_candidate_mapping_flag"]
        or record["adapter_mechanics_fixture_mapping_flag"]
    )
    unmapped_qku_count = sum(
        1
        for record in mappings
        if not record["seed_candidate_mapping_flag"]
        and not record["strict_run_capable_coverage_flag"]
    )
    blocked_from_run_capable_count = len(mappings) - strict_run_capable_qku_count
    rerun_ready_count = sum(1 for record in rerun if record["both_lanes_rerun_ready_flag"])
    rerun_blocked_count = len(rerun) - rerun_ready_count
    quantum_run_capable_feature_count = sum(
        1 for record in quantum_bridge if record["run_capable_dataset_available_flag"]
    )
    quantum_seed_only_feature_count = sum(
        1 for record in quantum_bridge if record["feature_seed_candidate_only_flag"]
    )
    quantum_blocked_count = len(quantum_bridge) - (
        quantum_run_capable_feature_count + quantum_seed_only_feature_count
    )

    final_summary_record = {
        **_record_common("PR162A-FINAL-SUMMARY"),
        "active_branch": branch,
        "source_input_count": len(source_inputs),
        "pr136_orchestration_artifacts_consumed_flag": True,
        "pr136_section_crosswalk_alias_consumed_flag": any(
            "PR136MasterPlanCoverageToReadinessDomainMap.report.json" in item
            or "PR136MasterPlanSectionCrosswalk.report.json" in item
            for item in source_inputs
        ),
        "pr161c_pr161d_pr161e_pr161f_pr162_inputs_consumed_flag": True,
        "network_materialization_mode_used": "NONE_DEFAULT_OFFLINE",
        "materialize_public_candidates_flag_requested": materialize_public_candidates,
        "ci_default_mode_requires_network": False,
        "dataset_source_candidates_by_source_class": source_class_counts,
        "dataset_candidates_by_authority_class": dataset_authority_counts,
        "run_capable_dataset_count": run_capable_count,
        "dataset_candidates_blocked_by_blocker_code": blocked_counts,
        "safe_repo_local_dataset_paths": [
            repo_relative_posix(repo_root, materialized["raw_path"]),
            repo_relative_posix(repo_root, materialized["normalized_path"]),
            repo_relative_posix(repo_root, materialized["manifest_path"]),
        ],
        "qkus_mapped_to_run_capable_datasets": strict_run_capable_qku_count,
        "qkus_mapped_to_seed_or_mechanics_dataset_candidates": seed_or_mechanics_qku_count,
        "qkus_blocked_without_dataset_candidate": unmapped_qku_count,
        "qkus_blocked_from_run_capable_coverage": blocked_from_run_capable_count,
        "qkus_blocked_no_safe_data": blocked_from_run_capable_count,
        "pr161f_run_plans_mapped_to_datasets": strict_run_capable_qku_count,
        "pr161f_run_plans_mapped_to_seed_or_mechanics_dataset_candidates": (
            seed_or_mechanics_qku_count
        ),
        "pr162_adapter_rerun_ready_count": rerun_ready_count,
        "pr162_adapter_rerun_blocked_count": rerun_blocked_count,
        "pr162b_pr162r_real_rerun_readiness_count": rerun_ready_count,
        "pr162b_pr162r_adapter_mechanics_smoke_only_count": seed_or_mechanics_qku_count,
        "pr163_readiness_state": "BLOCKED_UNTIL_PR162B_OR_PR162R_VALIDATED_REAL_ARTIFACTS_EXIST",
        "quantum_qkus_mapped_to_dataset_feature_candidates": (
            quantum_run_capable_feature_count + quantum_seed_only_feature_count
        ),
        "quantum_qkus_mapped_to_run_capable_dataset_feature_candidates": (
            quantum_run_capable_feature_count
        ),
        "quantum_qkus_mapped_to_seed_only_dataset_feature_candidates": (
            quantum_seed_only_feature_count
        ),
        "quantum_qkus_blocked_by_data": quantum_blocked_count,
        "quantum_qkus_blocked_from_run_capable_feature_coverage": len(quantum_bridge)
        - quantum_run_capable_feature_count,
        "quantum_feature_bridge_count": len(quantum_bridge),
        "qtt_agent_dataset_handoff_bridge_count": len(agents),
        "missing_value_candidate_count": len(missing_values),
        "data_leakage_time_window_audit_result": quality_records[0]["leakage_audit_status"],
        "forbidden_authority_scan_result": forbidden[0]["scan_status"],
        "no_scattered_hardcoded_policy_scan_result": forbidden[0]["no_scattered_hardcoded_policy_scan_status"],
        "shard_manifest_validation_result": "PASS",
        **pr152_evidence,
        "recommended_next_pr_route": (
            "OWNER_MATERIALIZE_MORE_DATASET_COVERAGE_BEFORE_PR162B_OR_PR162R_REAL_RERUN"
        ),
        "remaining_blockers": [
            "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_REPLAY_ARTIFACTS",
            "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_PAPER_ARTIFACTS",
        ],
        "master_plan_file_edited_flag": False,
        "atomicrows_bundle_jsonl_changed_flag": False,
        "forbidden_atomicrows_bundle_sidecar_artifact_created_or_referenced_flag": False,
        "qtt_sha_freeze_checksum_global_digest_authority_created_flag": False,
        "atomicrows_bundle_hash_or_freeze_authority_created_flag": False,
    }

    payloads: dict[str, dict[str, Any]] = {
        "PR162A_FinalSummary.report.json": _report_payload(
            "PR162A_FinalSummary.report.json",
            "PR162A_FINAL_SUMMARY",
            [final_summary_record],
            source_inputs,
            blocker_codes=final_summary_record["remaining_blockers"],
            extra=final_summary_record,
        ),
        "PR162A_SharedDictionary.report.json": _report_payload(
            "PR162A_SharedDictionary.report.json",
            "PR162A_SHARED_DICTIONARY",
            [],
            source_inputs,
            blocker_codes=(),
            extra={"shared_dictionary": _shared_dictionary_payload(), "record_count": 0},
        ),
        "PR162A_SourceDiscoveryCandidateRegistry.report.json": _report_payload(
            "PR162A_SourceDiscoveryCandidateRegistry.report.json",
            "PR162A_SOURCE_DISCOVERY_CANDIDATE_REGISTRY",
            source_records,
            source_inputs,
            blocker_codes=tuple(blocked_counts),
            extra={"dataset_source_candidates_by_source_class": source_class_counts},
        ),
        "PR162A_FetchPlanAndOwnerMaterializationCommandQueue.report.json": _report_payload(
            "PR162A_FetchPlanAndOwnerMaterializationCommandQueue.report.json",
            "PR162A_FETCH_PLAN_AND_OWNER_MATERIALIZATION_COMMAND_QUEUE",
            fetch_records,
            source_inputs,
            blocker_codes=tuple(record["blocker_code"] for record in fetch_records),
        ),
        "PR162A_DatasetMaterializationManifest.report.json": _report_payload(
            "PR162A_DatasetMaterializationManifest.report.json",
            "PR162A_DATASET_MATERIALIZATION_MANIFEST",
            datasets,
            source_inputs,
            blocker_codes=tuple(blocked_counts),
            extra={"run_capable_dataset_count": run_capable_count},
        ),
        "PR162A_DatasetAuthorityGate.report.json": _report_payload(
            "PR162A_DatasetAuthorityGate.report.json",
            "PR162A_DATASET_AUTHORITY_GATE",
            _authority_gate_records(datasets),
            source_inputs,
            blocker_codes=tuple(blocked_counts),
        ),
        "PR162A_DatasetProvenanceAccessRightsLedger.report.json": _report_payload(
            "PR162A_DatasetProvenanceAccessRightsLedger.report.json",
            "PR162A_DATASET_PROVENANCE_ACCESS_RIGHTS_LEDGER",
            _provenance_records(datasets),
            source_inputs,
            blocker_codes=tuple(blocked_counts),
        ),
        "PR162A_DatasetSafetyAndForbiddenPathScan.report.json": _report_payload(
            "PR162A_DatasetSafetyAndForbiddenPathScan.report.json",
            "PR162A_DATASET_SAFETY_AND_FORBIDDEN_PATH_SCAN",
            _dataset_safety_records(datasets),
            source_inputs,
            blocker_codes=(),
        ),
        "PR162A_DatasetLifecycleStateRegistry.report.json": _report_payload(
            "PR162A_DatasetLifecycleStateRegistry.report.json",
            "PR162A_DATASET_LIFECYCLE_STATE_REGISTRY",
            _lifecycle_records(datasets),
            source_inputs,
            blocker_codes=tuple(blocked_counts),
        ),
        "PR162A_DatasetSchemaNormalizationContract.report.json": _report_payload(
            "PR162A_DatasetSchemaNormalizationContract.report.json",
            "PR162A_DATASET_SCHEMA_NORMALIZATION_CONTRACT",
            [_normalization_contract_record()],
            source_inputs,
            blocker_codes=(),
        ),
        "PR162A_NormalizedDatasetInventory.report.json": _report_payload(
            "PR162A_NormalizedDatasetInventory.report.json",
            "PR162A_NORMALIZED_DATASET_INVENTORY",
            normalized_rows,
            source_inputs,
            blocker_codes=(),
            extra={"normalized_dataset_path": c.KALSHI_TINY_NORMALIZED_PATH.as_posix()},
        ),
        "PR162A_DataQualityLeakageAndTimeWindowAudit.report.json": _report_payload(
            "PR162A_DataQualityLeakageAndTimeWindowAudit.report.json",
            "PR162A_DATA_QUALITY_LEAKAGE_AND_TIME_WINDOW_AUDIT",
            quality_records,
            source_inputs,
            blocker_codes=tuple(record["blocker_code"] for record in quality_records),
        ),
        "PR162A_MarketScenarioQKUMappingMatrix.report.json": _report_payload(
            "PR162A_MarketScenarioQKUMappingMatrix.report.json",
            "PR162A_MARKET_SCENARIO_QKU_MAPPING_MATRIX",
            mappings,
            source_inputs,
            blocker_codes=tuple(blocked_counts),
        ),
        "PR162A_PR161FRunPlanDatasetCoverageBridge.report.json": _report_payload(
            "PR162A_PR161FRunPlanDatasetCoverageBridge.report.json",
            "PR162A_PR161F_RUN_PLAN_DATASET_COVERAGE_BRIDGE",
            coverage,
            source_inputs,
            blocker_codes=tuple(blocked_counts),
        ),
        "PR162A_PR162AdapterRerunReadinessBridge.report.json": _report_payload(
            "PR162A_PR162AdapterRerunReadinessBridge.report.json",
            "PR162A_PR162_ADAPTER_RERUN_READINESS_BRIDGE",
            rerun,
            source_inputs,
            blocker_codes=tuple(blocked_counts),
            extra={
                "pr162_adapter_rerun_ready_count": rerun_ready_count,
                "pr162_adapter_rerun_blocked_count": rerun_blocked_count,
                "pr162b_pr162r_adapter_mechanics_smoke_only_count": (
                    seed_or_mechanics_qku_count
                ),
            },
        ),
        "PR162A_PR163ReadinessBlockerStatus.report.json": _report_payload(
            "PR162A_PR163ReadinessBlockerStatus.report.json",
            "PR162A_PR163_READINESS_BLOCKER_STATUS",
            [_pr163_blocker_record(run_capable_count)],
            source_inputs,
            blocker_codes=(
                "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_REPLAY_ARTIFACTS",
                "PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_PAPER_ARTIFACTS",
            ),
        ),
        "PR162A_QuantumQKUDatasetFeatureBridge.report.json": _report_payload(
            "PR162A_QuantumQKUDatasetFeatureBridge.report.json",
            "PR162A_QUANTUM_QKU_DATASET_FEATURE_BRIDGE",
            quantum_bridge,
            source_inputs,
            blocker_codes=tuple(blocked_counts),
        ),
        "PR162A_QuantumFeatureMaterializationWorkOrderQueue.report.json": _report_payload(
            "PR162A_QuantumFeatureMaterializationWorkOrderQueue.report.json",
            "PR162A_QUANTUM_FEATURE_MATERIALIZATION_WORK_ORDER_QUEUE",
            quantum_work_orders,
            source_inputs,
            blocker_codes=tuple(blocked_counts),
        ),
        "PR162A_QTTAgentDatasetHandoffBridge.report.json": _report_payload(
            "PR162A_QTTAgentDatasetHandoffBridge.report.json",
            "PR162A_QTT_AGENT_DATASET_HANDOFF_BRIDGE",
            agents,
            source_inputs,
            blocker_codes=(),
        ),
        "PR162A_MissingValueCandidateRegistry.report.json": _report_payload(
            "PR162A_MissingValueCandidateRegistry.report.json",
            "PR162A_MISSING_VALUE_CANDIDATE_REGISTRY",
            missing_values,
            source_inputs,
            blocker_codes=(),
        ),
        "PR162A_ForbiddenAuthorityScan.report.json": _report_payload(
            "PR162A_ForbiddenAuthorityScan.report.json",
            "PR162A_FORBIDDEN_AUTHORITY_SCAN",
            forbidden,
            source_inputs,
            blocker_codes=tuple(record["blocker_code"] for record in forbidden),
        ),
        "PR162A_ReportShardManifest.report.json": {},
    }
    return payloads


def _record_common(record_id: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        **c.NO_AUTHORITY_FLAGS,
    }


def _report_payload(
    filename: str,
    report_type: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    *,
    blocker_codes: tuple[str, ...] | list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "report_id": filename.removesuffix(".report.json"),
        "report_type": report_type,
        "report_filename": filename,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
        "validation_status": "PASS",
        "blocker_codes": sorted(set(code for code in blocker_codes if code and code != "NONE")),
        "records": records,
        "record_count": len(records),
        **c.NO_AUTHORITY_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def _write_fetch_plan_file(repo_root: Path, records: list[dict[str, Any]]) -> None:
    write_json(
        repo_root / c.FETCH_PLAN_DIR / "pr162a_fetch_plan_and_owner_materialization_queue.json",
        {
            "created_by_pr": c.PR_ID,
            "authority_class": c.AUTHORITY_CLASS,
            "ci_requires_network": False,
            "records": records,
        },
    )


def _authority_gate_records(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_record_common(f"PR162A-AUTHORITY-GATE-{index:03d}"),
            "dataset_id": record["dataset_id"],
            "dataset_authority_class": record["dataset_authority_class"],
            "access_rights_status": record["access_rights_status"],
            "run_capable_flag": record["run_capable_flag"],
            "run_capable_gate_status": record["run_capable_gate_status"],
            "candidate_only_flag": True,
            "synthetic_fixture_flag": record["synthetic_fixture_flag"],
            "private_state_flag": record["private_state_flag"],
            "live_connector_dependency_flag": record["live_connector_dependency_flag"],
            "order_endpoint_dependency_flag": record["order_endpoint_dependency_flag"],
            "credential_required_flag": record["credential_required_flag"],
            "blocker_code": record["blocker_code"],
        }
        for index, record in enumerate(datasets, start=1)
    ]


def _provenance_records(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_record_common(f"PR162A-PROVENANCE-{index:03d}"),
            "dataset_id": record["dataset_id"],
            "source_class": record["source_class"],
            "source_locator": record["source_locator"],
            "source_name": record["source_name"],
            "source_platform_or_venue": record["source_platform_or_venue"],
            "access_rights_status": record["access_rights_status"],
            "owner_attestation_required_flag": record["owner_attestation_required_flag"],
            "source_revalidation_required_flag": True,
            "source_evidence_fact_created_flag": False,
            "candidate_only_flag": True,
            "blocker_code": record["blocker_code"],
        }
        for index, record in enumerate(datasets, start=1)
    ]


def _dataset_safety_records(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, record in enumerate(datasets, start=1):
        rel = record.get("relative_posix_path")
        allowed = rel is None or any(str(rel).startswith(prefix) for prefix in c.ALLOWED_DATASET_PATH_PREFIXES)
        forbidden = rel is not None and any(pattern in str(rel).lower() for pattern in c.FORBIDDEN_PATH_PATTERNS)
        records.append(
            {
                **_record_common(f"PR162A-DATASET-SAFETY-{index:03d}"),
                "dataset_id": record["dataset_id"],
                "relative_posix_path": rel,
                "path_is_posix_relative_flag": rel is None or ("\\" not in rel and not str(rel).startswith("/")),
                "path_allowlist_status": "PASS" if allowed else "FAIL_CLOSED",
                "forbidden_path_scan_status": "PASS" if not forbidden else "FAIL_CLOSED",
                "size_class": record["size_class"],
                "ci_requires_network": False,
                "blocker_code": "NONE" if allowed and not forbidden else "PR162A_BLOCKED_FORBIDDEN_PATH",
            }
        )
    return records


def _lifecycle_records(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **_record_common(f"PR162A-LIFECYCLE-{index:03d}"),
            "dataset_id": record["dataset_id"],
            "dataset_lifecycle_state": record["dataset_lifecycle_state"],
            "dataset_authority_class": record["dataset_authority_class"],
            "run_capable_gate_status": record["run_capable_gate_status"],
            "downstream_pr_routes": record["downstream_pr_routes"],
            "blocker_code": record["blocker_code"],
        }
        for index, record in enumerate(datasets, start=1)
    ]


def _normalization_contract_record() -> dict[str, Any]:
    return {
        **_record_common("PR162A-NORMALIZED-DATASET-CONTRACT"),
        "dataset_id": c.KALSHI_RUN_CAPABLE_DATASET_ID,
        "normalized_fields": list(NORMALIZED_FIELDS),
        "null_missing_value_required_flag": True,
        "missing_value_reason_required_flag": True,
        "candidate_imputation_must_be_labeled_flag": True,
        "performance_metrics_allowed_flag": False,
        "pre_resolution_features_separated_from_post_resolution_labels_flag": True,
        "normalization_status": "NORMALIZED",
        "blocker_code": "NONE",
    }


def _pr163_blocker_record(run_capable_dataset_count: int) -> dict[str, Any]:
    return {
        **_record_common("PR162A-PR163-BLOCKER-STATUS"),
        "run_capable_dataset_count": run_capable_dataset_count,
        "validated_real_nonlive_replay_artifacts_exist_flag": False,
        "validated_real_nonlive_paper_artifacts_exist_flag": False,
        "pr162b_or_pr162r_has_rerun_flag": False,
        "result_packet_eligibility_gates_satisfied_flag": False,
        "pr161e_handoff_candidates_exist_as_candidate_only_flag": False,
        "pr163_ready_flag": False,
        "pr163_readiness_state": "BLOCKED_UNTIL_PR162B_OR_PR162R_VALIDATED_REAL_ARTIFACTS_EXIST",
        "blocker_code": "PR162A_BLOCKED_PR163_REQUIRES_VALIDATED_REAL_ARTIFACTS",
    }


def _shared_dictionary_payload() -> dict[str, Any]:
    return {
        "dictionary_version": "PR162A_SHARED_DICTIONARY_V1",
        "central_policy_module": f"{c.PACKAGE_IMPORT}.constants",
        "report_names": list(c.REPORT_FILENAMES),
        "schema_names": list(c.SCHEMA_FILENAMES),
        "source_classes": list(c.SOURCE_CLASSES),
        "dataset_authority_classes": list(c.DATASET_AUTHORITY_CLASSES),
        "access_rights_statuses": list(c.ACCESS_RIGHTS_STATUSES),
        "dataset_lifecycle_states": list(c.DATASET_LIFECYCLE_STATES),
        "materialization_modes": list(c.MATERIALIZATION_MODES),
        "run_capable_gate_statuses": list(c.RUN_CAPABLE_GATE_STATUSES),
        "dataset_coverage_states": list(c.DATASET_COVERAGE_STATES),
        "min_strict_run_capable_row_count": c.MIN_STRICT_RUN_CAPABLE_ROW_COUNT,
        "min_strict_run_capable_time_window_seconds": (
            c.MIN_STRICT_RUN_CAPABLE_TIME_WINDOW_SECONDS
        ),
        "blocker_codes": list(c.BLOCKER_CODES),
        "quantum_feature_families": list(c.QUANTUM_FEATURE_FAMILIES),
        "forbidden_authority_categories": list(c.FORBIDDEN_AUTHORITY_CATEGORIES),
        "forbidden_path_patterns": list(c.FORBIDDEN_PATH_PATTERNS),
        "allowed_dataset_path_prefixes": list(c.ALLOWED_DATASET_PATH_PREFIXES),
        "posix_shard_reference_rule": "SHARD_REFS_MUST_BE_REPO_RELATIVE_POSIX_PATHS",
        "report_compactness_thresholds": {
            "record_target": c.REPORT_SHARD_RECORD_TARGET,
            "byte_threshold": c.REPORT_SHARD_BYTE_THRESHOLD,
        },
        "no_scattered_hardcoding_allowlist": list(c.NO_SCATTERED_POLICY_ALLOWLIST),
    }


def _clear_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    resolved_root = repo_root.resolve(strict=False)
    resolved_shard_dir = shard_dir.resolve(strict=False)
    try:
        resolved_shard_dir.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to clear shard path outside repo: {shard_dir}") from exc
    if shard_dir.exists():
        shutil.rmtree(shard_dir)
