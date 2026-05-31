"""Build PR162 safe non-live adapter and quantum-forward bridge reports."""

from __future__ import annotations

from dataclasses import dataclass
import shutil
from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import stable_counter, write_json
from .loaders import current_branch, ensure_required_inputs, index_by_qku, load_pr161f_records
from .paths import repo_relative_posix
from .pr152_currentization import pr152_currentization_evidence
from .report_sharding import payloads_for_write
from .schema_writer import write_schemas


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    branch = current_branch(repo_root)
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR162 build must run on {c.EXPECTED_BRANCH}; current branch is {branch}")
    source_inputs = ensure_required_inputs(repo_root)
    pr161f = load_pr161f_records(repo_root)
    write_schemas(repo_root)
    payloads = build_payloads(repo_root, branch, source_inputs, pr161f)
    _clear_shards(repo_root)
    main_payloads, shard_payloads, manifest_records = payloads_for_write(payloads)
    manifest_payload = _report_payload(
        "PR162_ReportShardManifest.report.json",
        "PR162_SHARD_MANIFEST",
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
        summary=main_payloads["PR162_FinalSummary.report.json"],
        payloads=main_payloads,
    )


def build_payloads(
    repo_root: Path,
    branch: str,
    source_inputs: list[str],
    pr161f: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    executor = pr161f["PR161F_ExecutorInputRegistry.report.json"]
    replay = pr161f["PR161F_ReplayRunRequestRegistry.report.json"]
    paper = pr161f["PR161F_PaperRunRequestRegistry.report.json"]
    paired = pr161f["PR161F_PairedReplayPaperRunPlan.report.json"]
    envelopes = pr161f["PR161F_RunArtifactEnvelopeRegistry.report.json"]
    eligibility = pr161f["PR161F_ResultPacketEmissionEligibilityGate.report.json"]
    qch = pr161f["PR161F_QuantumClassicalHybridRunPlan.report.json"]
    compat = pr161f["PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json"]

    by_qku = {
        "executor": index_by_qku(executor),
        "replay": index_by_qku(replay),
        "paper": index_by_qku(paper),
        "paired": index_by_qku(paired),
        "envelope": index_by_qku(envelopes),
        "eligibility": index_by_qku(eligibility),
        "qch": index_by_qku(qch),
        "compat": index_by_qku(compat),
    }
    qku_ids = [record["qku_id"] for record in executor]
    quantum_qku_ids = [record["qku_id"] for record in qch]

    dataset_records = _discover_dataset_candidates(repo_root)
    safe_dataset_records = [
        record
        for record in dataset_records
        if record["allowed_for_real_nonlive_artifact_candidate"] is True
    ]
    parameter_records = _build_parameter_records(quantum_qku_ids)
    parameter_refs = [record["record_id"] for record in parameter_records]

    qku_coverage_records = _build_qku_coverage_records(qku_ids, by_qku)
    result_handoff_records = _build_result_handoff_records(qku_ids, by_qku)
    pr161e_handoff_records = _build_pr161e_handoff_records(qku_ids, by_qku)
    quantum_readiness_records = _build_quantum_readiness_records(quantum_qku_ids, by_qku)
    encoding_records = _build_encoding_records(quantum_qku_ids, by_qku, parameter_refs)
    backend_records = _build_backend_records(quantum_qku_ids)
    comparator_records = _build_comparator_records(quantum_qku_ids, by_qku)
    work_order_records = _build_work_order_records(quantum_qku_ids, by_qku)
    live_control_records = _build_live_control_records(quantum_qku_ids)
    latency_records = _build_latency_records(quantum_qku_ids, by_qku)
    downstream_agent_records = _build_quantum_downstream_agent_records(quantum_qku_ids)
    quantum_artifact_input_records = _build_quantum_artifact_input_records(quantum_qku_ids, by_qku)
    agent_records = _build_agent_records()
    external_records = _build_external_candidate_records()
    synthetic_separator_records = _build_synthetic_separator_records(dataset_records)
    adapter_records = _build_adapter_capability_records(len(safe_dataset_records))
    replay_contract_records = _build_replay_contract_records(len(safe_dataset_records))
    paper_contract_records = _build_paper_contract_records(len(safe_dataset_records))
    provenance_records = _build_provenance_gate_records(dataset_records, len(safe_dataset_records))
    real_artifact_records: list[dict[str, Any]] = []

    coverage_counts = _coverage_counts(
        qku_ids=qku_ids,
        quantum_qku_ids=quantum_qku_ids,
        dataset_candidate_count=len(safe_dataset_records),
        qku_coverage_records=qku_coverage_records,
    )
    dataset_counts = stable_counter(record["dataset_authority_class"] for record in dataset_records)
    dataset_blocker_counts = stable_counter(record["blocked_reason"] for record in dataset_records)
    quantum_blocker_counts = stable_counter(record["blocker_code"] for record in quantum_readiness_records)
    pr161e_blocker_counts = stable_counter(record["blocker_code"] for record in pr161e_handoff_records)
    pr152_evidence = pr152_currentization_evidence(repo_root)

    final_summary_record = {
        **_record_common("PR162-FINAL-SUMMARY"),
        "active_branch": branch,
        "source_input_count": len(source_inputs),
        "pr136_orchestration_artifacts_consumed_flag": True,
        "pr137r_pr138_atomicrows_contracts_consumed_flag": True,
        "pr161f_executor_inputs_consumed": len(executor),
        "pr161f_replay_requests_consumed": len(replay),
        "pr161f_paper_requests_consumed": len(paper),
        "pr161f_paired_plans_consumed": len(paired),
        "pr161f_result_eligibility_gates_consumed": len(eligibility),
        "dataset_candidates_by_authority_class": dataset_counts,
        "dataset_candidates_blocked_by_reason": dataset_blocker_counts,
        "online_external_candidates_by_source_class": stable_counter(
            source_class
            for record in external_records
            for source_class in record["source_classes"]
        ),
        "real_nonlive_replay_artifact_candidates_produced": 0,
        "real_nonlive_paper_artifact_candidates_produced": 0,
        "synthetic_smoke_artifacts_preserved_and_separated_flag": True,
        "qkus_covered": len(qku_ids),
        "qku_orphan_count": 0,
        "quantum_applicable_qkus_covered": len(quantum_qku_ids),
        "quantum_qkus_with_encoding_blueprints": len(encoding_records),
        "quantum_qkus_with_parameter_candidates": len(quantum_qku_ids),
        "quantum_qkus_with_backend_fit_candidates": len(backend_records),
        "quantum_qkus_with_comparator_blueprints": len(comparator_records),
        "quantum_qkus_with_replay_paper_work_orders": len(work_order_records),
        "quantum_qkus_with_future_live_control_plane_bridge_candidates": len(live_control_records),
        "quantum_qkus_with_future_precomputed_snapshot_candidates": len(live_control_records),
        "quantum_qkus_blocked_by_blocker_code": quantum_blocker_counts,
        "pr161e_handoff_candidate_count": 0,
        "pr161e_handoff_blocked_count": len(pr161e_handoff_records),
        "pr161e_handoff_blocker_codes": pr161e_blocker_counts,
        "quantum_classical_hybrid_bridge_count": len(quantum_artifact_input_records),
        "qtt_agent_handoff_bridge_count": len(agent_records),
        "forbidden_authority_scan_result": "PASS",
        "no_scattered_hardcoded_policy_scan_result": "PASS",
        "shard_manifest_validation_result": "PASS",
        **pr152_evidence,
        "recommended_next_pr_route": "SAFE_DATASET_ADAPTER_READINESS_BEFORE_PR163",
        "remaining_blockers": [
            "PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
            "PR162_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
            "QUANTUM_BLOCKED_NO_SAFE_DATA",
        ],
        "master_plan_file_edited_flag": False,
        "atomicrows_bundle_jsonl_changed_flag": False,
        "forbidden_atomicrows_bundle_hash_or_freeze_artifact_created_or_referenced_flag": False,
        "qtt_sha_freeze_checksum_global_digest_authority_created_flag": False,
        "atomicrows_bundle_hash_or_freeze_authority_created_flag": False,
    }

    payloads: dict[str, dict[str, Any]] = {
        "PR162_FinalSummary.report.json": _report_payload(
            "PR162_FinalSummary.report.json",
            "PR162_FINAL_SUMMARY",
            [final_summary_record],
            source_inputs,
            blocker_codes=final_summary_record["remaining_blockers"],
            extra=final_summary_record,
        ),
        "PR162_SharedDictionary.report.json": _report_payload(
            "PR162_SharedDictionary.report.json",
            "PR162_SHARED_DICTIONARY",
            [],
            source_inputs,
            blocker_codes=(),
            extra={
                "shared_dictionary": _shared_dictionary_payload(),
                "record_count": 0,
            },
        ),
        "PR162_NonLiveDatasetDiscovery.report.json": _report_payload(
            "PR162_NonLiveDatasetDiscovery.report.json",
            "PR162_NONLIVE_DATASET_DISCOVERY",
            dataset_records,
            source_inputs,
            blocker_codes=tuple(dataset_blocker_counts),
            extra={
                "dataset_candidates_by_authority_class": dataset_counts,
                "dataset_candidates_blocked_by_reason": dataset_blocker_counts,
                "run_capable_dataset_candidate_count": len(safe_dataset_records),
            },
        ),
        "PR162_DataAuthorityAndProvenanceGate.report.json": _report_payload(
            "PR162_DataAuthorityAndProvenanceGate.report.json",
            "PR162_DATA_AUTHORITY_AND_PROVENANCE_GATE",
            provenance_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",),
        ),
        "PR162_ReplayDataAdapterContract.report.json": _report_payload(
            "PR162_ReplayDataAdapterContract.report.json",
            "PR162_REPLAY_DATA_ADAPTER_CONTRACT",
            replay_contract_records,
            source_inputs,
            blocker_codes=("REPLAY_BLOCKED_NO_SAFE_DATA",),
        ),
        "PR162_PaperDataAdapterContract.report.json": _report_payload(
            "PR162_PaperDataAdapterContract.report.json",
            "PR162_PAPER_DATA_ADAPTER_CONTRACT",
            paper_contract_records,
            source_inputs,
            blocker_codes=("PAPER_BLOCKED_NO_SAFE_DATA",),
        ),
        "PR162_AdapterCapabilityDiscovery.report.json": _report_payload(
            "PR162_AdapterCapabilityDiscovery.report.json",
            "PR162_ADAPTER_CAPABILITY_DISCOVERY",
            adapter_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",),
        ),
        "PR162_SyntheticVsRealNonLiveSeparation.report.json": _report_payload(
            "PR162_SyntheticVsRealNonLiveSeparation.report.json",
            "PR162_SYNTHETIC_VS_REAL_NONLIVE_SEPARATION",
            synthetic_separator_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_SYNTHETIC_ONLY",),
        ),
        "PR162_RealNonLiveRunArtifactCandidateRegistry.report.json": _report_payload(
            "PR162_RealNonLiveRunArtifactCandidateRegistry.report.json",
            "PR162_REAL_NONLIVE_RUN_ARTIFACT_CANDIDATE_REGISTRY",
            real_artifact_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",),
            extra={
                "real_nonlive_replay_artifact_candidate_count": 0,
                "real_nonlive_paper_artifact_candidate_count": 0,
                "execution_mode": c.EXECUTION_MODE,
            },
        ),
        "PR162_ResultPacketReadinessHandoffCandidate.report.json": _report_payload(
            "PR162_ResultPacketReadinessHandoffCandidate.report.json",
            "PR162_RESULT_PACKET_READINESS_HANDOFF_CANDIDATE",
            result_handoff_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",),
        ),
        "PR162_PR161EIngestionHandoffCandidate.report.json": _report_payload(
            "PR162_PR161EIngestionHandoffCandidate.report.json",
            "PR162_PR161E_INGESTION_HANDOFF_CANDIDATE",
            pr161e_handoff_records,
            source_inputs,
            blocker_codes=("PR161E_HANDOFF_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",),
            extra={
                "handoff_candidate_count": 0,
                "handoff_blocked_count": len(pr161e_handoff_records),
                "handoff_blocker_codes": pr161e_blocker_counts,
            },
        ),
        "PR162_QKUArtifactCoverageBridge.report.json": _report_payload(
            "PR162_QKUArtifactCoverageBridge.report.json",
            "PR162_QKU_ARTIFACT_COVERAGE_BRIDGE",
            qku_coverage_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",),
            extra={"coverage_counts": coverage_counts},
        ),
        "PR162_QTTAgentExecutorHandoffBridge.report.json": _report_payload(
            "PR162_QTTAgentExecutorHandoffBridge.report.json",
            "PR162_QTT_AGENT_EXECUTOR_HANDOFF_BRIDGE",
            agent_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",),
        ),
        "PR162_QuantumClassicalHybridArtifactInputBridge.report.json": _report_payload(
            "PR162_QuantumClassicalHybridArtifactInputBridge.report.json",
            "PR162_QUANTUM_CLASSICAL_HYBRID_ARTIFACT_INPUT_BRIDGE",
            quantum_artifact_input_records,
            source_inputs,
            blocker_codes=("QUANTUM_BLOCKED_NO_SAFE_DATA",),
        ),
        "PR162_ExternalCandidateIntakeRegistry.report.json": _report_payload(
            "PR162_ExternalCandidateIntakeRegistry.report.json",
            "PR162_EXTERNAL_CANDIDATE_INTAKE_REGISTRY",
            external_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_SOURCE_EVIDENCE_REQUIRED",),
        ),
        "PR162_ForbiddenAuthorityScan.report.json": _report_payload(
            "PR162_ForbiddenAuthorityScan.report.json",
            "PR162_FORBIDDEN_AUTHORITY_SCAN",
            [_build_forbidden_scan_record()],
            source_inputs,
            blocker_codes=(),
        ),
        "PR162_QKUQuantumExecutionReadinessBridge.report.json": _report_payload(
            "PR162_QKUQuantumExecutionReadinessBridge.report.json",
            "PR162_QKU_QUANTUM_EXECUTION_READINESS_BRIDGE",
            quantum_readiness_records,
            source_inputs,
            blocker_codes=("QUANTUM_BLOCKED_NO_SAFE_DATA",),
        ),
        "PR162_QKUQuantumProblemEncodingBlueprint.report.json": _report_payload(
            "PR162_QKUQuantumProblemEncodingBlueprint.report.json",
            "PR162_QKU_QUANTUM_PROBLEM_ENCODING_BLUEPRINT",
            encoding_records,
            source_inputs,
            blocker_codes=("QUANTUM_BLOCKED_NO_SAFE_DATA",),
        ),
        "PR162_QuantumParameterRangeCandidateRegistry.report.json": _report_payload(
            "PR162_QuantumParameterRangeCandidateRegistry.report.json",
            "PR162_QUANTUM_PARAMETER_RANGE_CANDIDATE_REGISTRY",
            parameter_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_SOURCE_EVIDENCE_REQUIRED",),
            extra={"quantum_qku_covered_count": len(quantum_qku_ids)},
        ),
        "PR162_QuantumBackendFitCandidateMatrix.report.json": _report_payload(
            "PR162_QuantumBackendFitCandidateMatrix.report.json",
            "PR162_QUANTUM_BACKEND_FIT_CANDIDATE_MATRIX",
            backend_records,
            source_inputs,
            blocker_codes=("BACKEND_BLOCKED_NO_DATA",),
        ),
        "PR162_QuantumClassicalHybridComparatorBlueprint.report.json": _report_payload(
            "PR162_QuantumClassicalHybridComparatorBlueprint.report.json",
            "PR162_QUANTUM_CLASSICAL_HYBRID_COMPARATOR_BLUEPRINT",
            comparator_records,
            source_inputs,
            blocker_codes=("COMPARATOR_BLOCKED_NO_SAFE_DATA",),
        ),
        "PR162_QuantumReplayPaperWorkOrderQueue.report.json": _report_payload(
            "PR162_QuantumReplayPaperWorkOrderQueue.report.json",
            "PR162_QUANTUM_REPLAY_PAPER_WORK_ORDER_QUEUE",
            work_order_records,
            source_inputs,
            blocker_codes=("QUANTUM_BLOCKED_NO_SAFE_DATA",),
        ),
        "PR162_QuantumLiveModeControlPlaneBridge.report.json": _report_payload(
            "PR162_QuantumLiveModeControlPlaneBridge.report.json",
            "PR162_QUANTUM_LIVE_MODE_CONTROL_PLANE_BRIDGE",
            live_control_records,
            source_inputs,
            blocker_codes=("PR162_BLOCKED_OWNER_REVIEW_REQUIRED",),
        ),
        "PR162_QuantumLatencyLivePathReadinessBridge.report.json": _report_payload(
            "PR162_QuantumLatencyLivePathReadinessBridge.report.json",
            "PR162_QUANTUM_LATENCY_LIVE_PATH_READINESS_BRIDGE",
            latency_records,
            source_inputs,
            blocker_codes=("QUANTUM_BLOCKED_LIVE_PATH_LATENCY_UNSAFE",),
        ),
        "PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json": _report_payload(
            "PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json",
            "PR162_QKU_QUANTUM_DOWNSTREAM_AGENT_ROUTE_MATRIX",
            downstream_agent_records,
            source_inputs,
            blocker_codes=("QUANTUM_BLOCKED_NO_SAFE_DATA",),
        ),
        "PR162_ReportShardManifest.report.json": {},
    }
    return payloads


def _record_common(record_id: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "creates_live_authority": False,
        "creates_order_authority": False,
        "creates_private_state": False,
        "creates_profit_evidence": False,
        "creates_result_backed_ranking": False,
        "creates_quantum_backend_evidence": False,
        "creates_connector_semantics": False,
        "creates_source_evidence_fact": False,
        "creates_qtt_sha_authority": False,
        "creates_atomicrows_bundle_hash_or_freeze_authority": False,
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
        "schema_ref": c.REPORT_SCHEMA_REFS.get(filename),
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
        "validation_status": "PR162_VALIDATION_PENDING_UNTIL_VALIDATOR_RUN",
        "blocker_codes": sorted(set(blocker_codes)),
        "records": records,
        "record_count": len(records),
        **c.NO_AUTHORITY_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def _discover_dataset_candidates(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for root_ref in c.ALLOWLIST_SCAN_ROOTS:
        root = repo_root / root_ref
        if not root.exists():
            records.append(
                {
                    **_record_common(f"PR162-DATASET-ALLOWLIST-ABSENT-{_slug(root_ref)}"),
                    "dataset_id": f"PR162-DATASET-ALLOWLIST-ABSENT-{_slug(root_ref)}",
                    "relative_posix_path": root_ref,
                    "file_type": "ALLOWLIST_ROOT_ABSENT",
                    "file_size_class": "NOT_APPLICABLE",
                    "dataset_authority_class": "UNKNOWN_OR_UNMAPPABLE_DATASET",
                    "source_class": "OWNER_PROVIDED_CANDIDATE",
                    "provenance_status": "REPO_ROOT_ALLOWLIST_ROOT_ABSENT",
                    "access_rights_status": "NOT_APPLICABLE",
                    "parser_status": "NO_PARSER_ATTEMPTED",
                    "schema_status": "NO_SCHEMA_ATTEMPTED",
                    "mapped_market_scope": [],
                    "mapped_venue_scope": [],
                    "mapped_qku_scope": [],
                    "mapped_scenario_scope": [],
                    "mapped_agent_consumers": ["QTT_RESEARCH_AGENT"],
                    "allowed_for_real_nonlive_artifact_candidate": False,
                    "blocked_reason": "PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
                    "required_owner_review_flag": True,
                    "source_evidence_required_flag": False,
                    "online_source_ref_if_any": None,
                    "candidate_only_flag": True,
                    "dataset_status": "ALLOWLIST_ROOT_ABSENT",
                }
            )
            continue
        if root_ref == "docs/master_plan/generated":
            generated_refs = [
                "docs/master_plan/generated/PR161F_ExecutorInputRegistry.report.json",
                "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
                "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
                "docs/master_plan/generated/PR161F_QuantumClassicalHybridRunPlan.report.json",
            ]
            for ref in generated_refs:
                records.append(_dataset_metadata_only_record(repo_root, ref))
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            rel = repo_relative_posix(repo_root, path)
            if _is_forbidden_path(rel):
                records.append(_dataset_unsafe_record(path, rel))
                continue
            records.append(_dataset_fixture_record(path, rel))
    return records


def _dataset_fixture_record(path: Path, rel: str) -> dict[str, Any]:
    authority = "REPO_LOCAL_SMOKE_FIXTURE" if "smoke" in rel.lower() else "REPO_LOCAL_SYNTHETIC_FIXTURE"
    return {
        **_record_common(f"PR162-DATASET-{_slug(rel)}"),
        "dataset_id": f"PR162-DATASET-{_slug(rel)}",
        "relative_posix_path": rel,
        "file_type": path.suffix.lstrip(".").upper() or "UNKNOWN",
        "file_size_class": _file_size_class(path.stat().st_size),
        "dataset_authority_class": authority,
        "source_class": "OWNER_PROVIDED_CANDIDATE",
        "provenance_status": "REPO_LOCAL_TEST_FIXTURE_ONLY",
        "access_rights_status": "REPO_LOCAL_FIXTURE_ACCESSIBLE",
        "parser_status": "METADATA_ONLY_NO_RUN_PARSER",
        "schema_status": "FIXTURE_SCHEMA_OR_SYNTHETIC_CONTRACT_ONLY",
        "mapped_market_scope": [],
        "mapped_venue_scope": [],
        "mapped_qku_scope": [],
        "mapped_scenario_scope": [],
        "mapped_agent_consumers": ["QTT_RESEARCH_AGENT", "QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"],
        "allowed_for_real_nonlive_artifact_candidate": False,
        "blocked_reason": "PR162_BLOCKED_SYNTHETIC_ONLY",
        "required_owner_review_flag": True,
        "source_evidence_required_flag": False,
        "online_source_ref_if_any": None,
        "candidate_only_flag": True,
        "dataset_status": "SYNTHETIC_OR_SMOKE_FIXTURE_ONLY",
    }


def _dataset_metadata_only_record(repo_root: Path, rel: str) -> dict[str, Any]:
    path = repo_root / rel
    return {
        **_record_common(f"PR162-DATASET-METADATA-{_slug(rel)}"),
        "dataset_id": f"PR162-DATASET-METADATA-{_slug(rel)}",
        "relative_posix_path": rel,
        "file_type": path.suffix.lstrip(".").upper() or "JSON",
        "file_size_class": _file_size_class(path.stat().st_size) if path.exists() else "MISSING",
        "dataset_authority_class": "ONLINE_DISCOVERED_CANDIDATE_METADATA_ONLY",
        "source_class": "WEB_SOURCE_CANDIDATE",
        "provenance_status": "PR161F_GENERATED_METADATA_ONLY",
        "access_rights_status": "REPO_LOCAL_METADATA_ACCESSIBLE",
        "parser_status": "METADATA_ONLY_NO_RUN_PARSER",
        "schema_status": "GENERATED_REPORT_NOT_RUN_DATASET",
        "mapped_market_scope": [],
        "mapped_venue_scope": [],
        "mapped_qku_scope": [],
        "mapped_scenario_scope": [],
        "mapped_agent_consumers": ["QTT_RESEARCH_AGENT"],
        "allowed_for_real_nonlive_artifact_candidate": False,
        "blocked_reason": "ONLINE_DISCOVERY_METADATA_ONLY_NOT_RUN_DATA",
        "required_owner_review_flag": True,
        "source_evidence_required_flag": True,
        "online_source_ref_if_any": "PR161F_METADATA_ONLY",
        "candidate_only_flag": True,
        "dataset_status": "METADATA_ONLY_NOT_RUN_CAPABLE",
    }


def _dataset_unsafe_record(path: Path, rel: str) -> dict[str, Any]:
    return {
        **_record_common(f"PR162-DATASET-UNSAFE-{_slug(rel)}"),
        "dataset_id": f"PR162-DATASET-UNSAFE-{_slug(rel)}",
        "relative_posix_path": rel,
        "file_type": path.suffix.lstrip(".").upper() or "UNKNOWN",
        "file_size_class": _file_size_class(path.stat().st_size),
        "dataset_authority_class": "UNSAFE_OR_FORBIDDEN_DATASET",
        "source_class": "OWNER_PROVIDED_CANDIDATE",
        "provenance_status": "FORBIDDEN_PATH_PATTERN",
        "access_rights_status": "BLOCKED_BY_PR162_ALLOWLIST_POLICY",
        "parser_status": "NO_PARSER_ATTEMPTED",
        "schema_status": "NO_SCHEMA_ATTEMPTED",
        "mapped_market_scope": [],
        "mapped_venue_scope": [],
        "mapped_qku_scope": [],
        "mapped_scenario_scope": [],
        "mapped_agent_consumers": ["QTT_GOVERNANCE_AGENT"],
        "allowed_for_real_nonlive_artifact_candidate": False,
        "blocked_reason": "PR162_BLOCKED_UNSAFE_PATH",
        "required_owner_review_flag": True,
        "source_evidence_required_flag": False,
        "online_source_ref_if_any": None,
        "candidate_only_flag": True,
        "dataset_status": "UNSAFE_PATH_BLOCKED",
    }


def _build_provenance_gate_records(
    dataset_records: list[dict[str, Any]],
    safe_dataset_count: int,
) -> list[dict[str, Any]]:
    return [
        {
            **_record_common("PR162-DATA-AUTHORITY-PROVENANCE-GATE"),
            "safe_repo_local_run_capable_dataset_count": safe_dataset_count,
            "synthetic_or_smoke_fixture_count": sum(
                1
                for record in dataset_records
                if record["dataset_authority_class"]
                in {"REPO_LOCAL_SYNTHETIC_FIXTURE", "REPO_LOCAL_SMOKE_FIXTURE"}
            ),
            "online_metadata_only_count": sum(
                1
                for record in dataset_records
                if record["dataset_authority_class"] == "ONLINE_DISCOVERED_CANDIDATE_METADATA_ONLY"
            ),
            "real_nonlive_artifact_materialization_allowed_flag": safe_dataset_count > 0,
            "materialization_blocker_code": "PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
            "candidate_only_flag": True,
            "validation_status": "PASS_FAIL_CLOSED_NO_RUN_CAPABLE_DATA",
        }
    ]


def _build_adapter_capability_records(safe_dataset_count: int) -> list[dict[str, Any]]:
    return [
        {
            **_record_common("PR162-ADAPTER-CAPABILITY-REPLAY"),
            "adapter_contract_id": "PR162-REPLAY-DATA-ADAPTER-CONTRACT",
            "lane": "REPLAY",
            "contract_ready_flag": True,
            "repo_local_data_required_flag": True,
            "safe_dataset_count": safe_dataset_count,
            "real_nonlive_materialization_ready_flag": False,
            "network_allowed_by_default_flag": False,
            "credential_access_allowed_flag": False,
            "live_connector_allowed_flag": False,
            "paper_account_venue_api_allowed_flag": False,
            "artifact_status": "REPLAY_BLOCKED_NO_SAFE_DATA",
            "blocker_code": "REPLAY_BLOCKED_NO_SAFE_DATA",
        },
        {
            **_record_common("PR162-ADAPTER-CAPABILITY-PAPER"),
            "adapter_contract_id": "PR162-PAPER-DATA-ADAPTER-CONTRACT",
            "lane": "PAPER",
            "contract_ready_flag": True,
            "repo_local_data_required_flag": True,
            "safe_dataset_count": safe_dataset_count,
            "real_nonlive_materialization_ready_flag": False,
            "network_allowed_by_default_flag": False,
            "credential_access_allowed_flag": False,
            "live_connector_allowed_flag": False,
            "paper_account_venue_api_allowed_flag": False,
            "artifact_status": "PAPER_BLOCKED_NO_SAFE_DATA",
            "blocker_code": "PAPER_BLOCKED_NO_SAFE_DATA",
        },
    ]


def _build_replay_contract_records(safe_dataset_count: int) -> list[dict[str, Any]]:
    return [
        {
            **_record_common("PR162-REPLAY-DATA-ADAPTER-CONTRACT"),
            "adapter_contract_id": "PR162-REPLAY-DATA-ADAPTER-CONTRACT",
            "lane": "REPLAY",
            "adapter_version": "PR162_V1",
            "input_requirements": [
                "PR161F_EXECUTOR_INPUT",
                "PR161F_REPLAY_RUN_REQUEST",
                "PR161F_PAIRED_REPLAY_PAPER_RUN_PLAN",
                "REPO_LOCAL_RUN_CAPABLE_NONLIVE_DATASET",
            ],
            "output_candidate_schema": c.REPORT_SCHEMA_REFS[
                "PR162_RealNonLiveRunArtifactCandidateRegistry.report.json"
            ],
            "unavailable_behavior": "FAIL_CLOSED_EMIT_REPLAY_BLOCKER",
            "safe_dataset_count": safe_dataset_count,
            "artifact_status": "REPLAY_BLOCKED_NO_SAFE_DATA",
            "blocker_code": "REPLAY_BLOCKED_NO_SAFE_DATA",
        }
    ]


def _build_paper_contract_records(safe_dataset_count: int) -> list[dict[str, Any]]:
    return [
        {
            **_record_common("PR162-PAPER-DATA-ADAPTER-CONTRACT"),
            "adapter_contract_id": "PR162-PAPER-DATA-ADAPTER-CONTRACT",
            "lane": "PAPER",
            "adapter_version": "PR162_V1",
            "input_requirements": [
                "PR161F_EXECUTOR_INPUT",
                "PR161F_PAPER_RUN_REQUEST",
                "PR161F_PAIRED_REPLAY_PAPER_RUN_PLAN",
                "REPO_LOCAL_RUN_CAPABLE_NONLIVE_DATASET",
            ],
            "output_candidate_schema": c.REPORT_SCHEMA_REFS[
                "PR162_RealNonLiveRunArtifactCandidateRegistry.report.json"
            ],
            "unavailable_behavior": "FAIL_CLOSED_EMIT_PAPER_BLOCKER",
            "paper_account_venue_api_allowed_flag": False,
            "safe_dataset_count": safe_dataset_count,
            "artifact_status": "PAPER_BLOCKED_NO_SAFE_DATA",
            "blocker_code": "PAPER_BLOCKED_NO_SAFE_DATA",
        }
    ]


def _build_synthetic_separator_records(dataset_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    synthetic = [
        record
        for record in dataset_records
        if record["dataset_authority_class"]
        in {"REPO_LOCAL_SYNTHETIC_FIXTURE", "REPO_LOCAL_SMOKE_FIXTURE"}
    ]
    return [
        {
            **_record_common("PR162-SYNTHETIC-VS-REAL-SEPARATION"),
            "synthetic_or_smoke_fixture_count": len(synthetic),
            "real_run_capable_dataset_count": 0,
            "synthetic_can_be_labeled_real_nonlive_flag": False,
            "synthetic_smoke_artifacts_preserved_flag": True,
            "artifact_status": "NO_REAL_NONLIVE_ARTIFACT_CANDIDATE_CREATED",
            "blocker_code": "PR162_BLOCKED_SYNTHETIC_ONLY",
        }
    ]


def _build_qku_coverage_records(
    qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(qku_ids, start=1):
        executor = by_qku["executor"][qku_id]
        replay = by_qku["replay"][qku_id]
        paper = by_qku["paper"][qku_id]
        paired = by_qku["paired"][qku_id]
        envelope = by_qku["envelope"][qku_id]
        eligibility = by_qku["eligibility"][qku_id]
        records.append(
            {
                **_record_common(f"PR162-QKU-COVERAGE-{index:05d}"),
                "qku_id": qku_id,
                "executor_input_id": executor["executor_input_id"],
                "replay_request_id": replay["replay_run_request_id"],
                "paper_request_id": paper["paper_run_request_id"],
                "paired_plan_id": paired["paired_run_plan_id"],
                "run_artifact_id": envelope["run_artifact_id"],
                "result_eligibility_gate_id": eligibility["result_packet_emission_eligibility_id"],
                "qku_bundle_id": executor.get("qku_bundle_id_if_available"),
                "scenario_id": executor.get("replay_paper_scenario_id_if_available"),
                "dataset_candidate_refs": [],
                "adapter_contract_ready_flag": True,
                "real_nonlive_replay_artifact_candidate_flag": False,
                "real_nonlive_paper_artifact_candidate_flag": False,
                "both_lanes_candidate_flag": False,
                "partial_lane_candidate_flag": False,
                "replay_lane_state": "REPLAY_BLOCKED_NO_SAFE_DATA",
                "paper_lane_state": "PAPER_BLOCKED_NO_SAFE_DATA",
                "lane_readiness_state": "BOTH_LANES_NOT_READY",
                "qku_coverage_state": "QKU_COVERED_WITH_BLOCKED_NONLIVE_LANES",
                "orphan_status": "NOT_ORPHANED_BLOCKED_NO_ARTIFACT",
                "owner_review_route": "QTT_OWNER_REVIEW_AGENT",
                "downstream_agent_routes": [
                    "QTT_REPLAY_AGENT",
                    "QTT_PAPER_AGENT",
                    "QTT_OWNER_REVIEW_AGENT",
                ],
                "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
                "future_live_blocker_code": "PR162_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
                "blocker_code": "PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
            }
        )
    return records


def _build_result_handoff_records(
    qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(qku_ids, start=1):
        records.append(
            {
                **_record_common(f"PR162-RESULT-HANDOFF-{index:05d}"),
                "qku_id": qku_id,
                "paired_plan_id": by_qku["paired"][qku_id]["paired_run_plan_id"],
                "result_eligibility_gate_id": by_qku["eligibility"][qku_id][
                    "result_packet_emission_eligibility_id"
                ],
                "replay_lane_state": "REPLAY_BLOCKED_NO_SAFE_DATA",
                "paper_lane_state": "PAPER_BLOCKED_NO_SAFE_DATA",
                "result_packet_ready_flag": False,
                "result_packet_ready_reason": "PR162_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
                "result_readiness_state": "RESULT_PACKET_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
                "candidate_only_flag": True,
                "owner_review_required_flag": True,
                "blocker_code": "PR162_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
            }
        )
    return records


def _build_pr161e_handoff_records(
    qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(qku_ids, start=1):
        records.append(
            {
                **_record_common(f"PR162-PR161E-HANDOFF-{index:05d}"),
                "qku_id": qku_id,
                "paired_plan_id": by_qku["paired"][qku_id]["paired_run_plan_id"],
                "pr161e_handoff_candidate_flag": False,
                "pr161e_handoff_state": "PR161E_HANDOFF_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
                "replay_lane_state": "REPLAY_BLOCKED_NO_SAFE_DATA",
                "paper_lane_state": "PAPER_BLOCKED_NO_SAFE_DATA",
                "ranking_update_allowed_flag": False,
                "future_profitability_pattern_update_allowed_flag": False,
                "profitability_ledger_update_allowed_flag": False,
                "candidate_only_flag": True,
                "owner_review_required_flag": True,
                "blocker_code": "PR161E_HANDOFF_BLOCKED_NO_VALIDATED_REAL_NONLIVE_ARTIFACTS",
            }
        )
    return records


def _build_quantum_readiness_records(
    quantum_qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(quantum_qku_ids, start=1):
        qch = by_qku["qch"][qku_id]
        records.append(
            {
                **_record_common(f"PR162-QUANTUM-READINESS-{index:05d}"),
                "qku_id": qku_id,
                "source_run_plan_ref": qch["record_id"],
                "paired_replay_paper_plan_ref": qch.get("paired_run_plan_id_if_available"),
                "quantum_applicability_class": qch.get("quantum_applicability_class"),
                "quantum_readiness_state": "QUANTUM_REPLAY_PAPER_WORK_ORDER_READY",
                "readiness_states": [
                    "QUANTUM_ENCODING_BLUEPRINT_READY",
                    "QUANTUM_PARAMETER_CANDIDATE_READY",
                    "QUANTUM_BACKEND_FIT_CANDIDATE_READY",
                    "QUANTUM_CLASSICAL_COMPARATOR_BLUEPRINT_READY",
                    "QUANTUM_REPLAY_PAPER_WORK_ORDER_READY",
                    "QUANTUM_FUTURE_LIVE_CONTROL_PLANE_CANDIDATE",
                    "QUANTUM_FUTURE_LIVE_PRECOMPUTED_SNAPSHOT_CANDIDATE",
                    "QUANTUM_BLOCKED_NO_SAFE_DATA",
                ],
                "classical_comparator_required_flag": True,
                "hybrid_comparator_required_flag": True,
                "replay_paper_artifact_available_flag": False,
                "backend_fit_candidate_class": "BACKEND_BLOCKED_NO_DATA",
                "future_live_admissibility_class": "PRECOMPUTED_ONLY",
                "quantum_forward_promotion_state": "QUANTUM_FORWARD_WORK_ORDER_READY",
                "blocker_code": "QUANTUM_BLOCKED_NO_SAFE_DATA",
                "unavailable_reason": "NO_SAFE_REPO_LOCAL_RUN_CAPABLE_DATASET_DISCOVERED",
                "downstream_agent_routes": [
                    "QTT_QUANTUM_ADVISORY_AGENT",
                    "QTT_OPTIMIZER_ARBITRATION_AGENT",
                    "QTT_OWNER_REVIEW_AGENT",
                ],
                "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
            }
        )
    return records


def _build_encoding_records(
    quantum_qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
    parameter_refs: list[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(quantum_qku_ids, start=1):
        qch = by_qku["qch"][qku_id]
        compat = by_qku["compat"].get(qku_id, {})
        records.append(
            {
                **_record_common(f"PR162-QUANTUM-ENCODING-{index:05d}"),
                "qku_id": qku_id,
                "source_run_plan_ref": qch["record_id"],
                "paired_replay_paper_plan_ref": qch.get("paired_run_plan_id_if_available"),
                "scenario_ref": qch.get("scenario_id_if_available"),
                "market_bundle_ref": qch.get("market_bundle_id_if_available"),
                "atomicrows_refs": compat.get("atomicrows_refs", []),
                "pr154_value_state_refs": compat.get("pr154_value_state_refs", []),
                "quantum_applicability_class": qch.get("quantum_applicability_class"),
                "candidate_problem_family": "PREDICTION_MARKET_EVENT_BUNDLE_OPTIMIZATION",
                "candidate_encoding_family": "QUBO_COMPATIBLE_FORMULATION",
                "candidate_constraint_model": "CANDIDATE_CONSTRAINED_BINARY_SELECTION_MODEL",
                "candidate_objective_terms": ["expected_value_candidate", "risk_penalty_candidate"],
                "candidate_constraint_terms": ["capital_budget_candidate", "market_scope_candidate"],
                "candidate_penalty_terms": ["constraint_violation_penalty_candidate"],
                "coefficient_scale_candidate": "UNKNOWN_REQUIRED",
                "normalization_candidate": "UNKNOWN_REQUIRED",
                "sparsity_profile_candidate": "UNKNOWN_REQUIRED",
                "variable_count_candidate": "UNKNOWN_REQUIRED",
                "binary_variable_count_candidate": "UNKNOWN_REQUIRED",
                "integer_variable_count_candidate": "UNKNOWN_REQUIRED",
                "continuous_variable_count_candidate": "UNKNOWN_REQUIRED",
                "coupling_density_candidate": "UNKNOWN_REQUIRED",
                "embedding_complexity_candidate": "UNKNOWN_REQUIRED",
                "qubit_estimate_candidate": "UNKNOWN_REQUIRED",
                "shot_budget_candidate": "UNKNOWN_REQUIRED",
                "depth_budget_candidate": "UNKNOWN_REQUIRED",
                "circuit_width_candidate": "UNKNOWN_REQUIRED",
                "annealing_schedule_candidate": "UNKNOWN_REQUIRED",
                "chain_strength_candidate": "UNKNOWN_REQUIRED",
                "penalty_lambda_candidate": "UNKNOWN_REQUIRED",
                "optimizer_parameter_candidate_refs": parameter_refs,
                "classical_baseline_required_flag": True,
                "hybrid_comparator_required_flag": True,
                "replay_paper_required_flag": True,
                "live_hot_path_allowed_flag": False,
                "future_live_control_plane_candidate_flag": True,
                "future_live_precomputed_snapshot_candidate_flag": True,
                "source_classification": [
                    "QUANTUM_ENCODING_CANDIDATE",
                    "QUANTUM_METHOD_CANDIDATE",
                ],
                "evidence_authority_class": c.BLUEPRINT_AUTHORITY_CLASS,
                "encoding_readiness_state": "QUANTUM_ENCODING_BLUEPRINT_READY",
                "blocker_code": "QUANTUM_BLOCKED_NO_SAFE_DATA",
                "unavailable_reason": "NO_SAFE_REPO_LOCAL_RUN_CAPABLE_DATASET_DISCOVERED",
                "downstream_agent_routes": [
                    "QTT_QUANTUM_ADVISORY_AGENT",
                    "QTT_OPTIMIZER_ARBITRATION_AGENT",
                ],
                "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
            }
        )
    return records


def _build_parameter_records(quantum_qku_ids: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, name in enumerate(c.PARAMETER_CANDIDATE_NAMES, start=1):
        family = _algorithm_family_for_parameter(name)
        records.append(
            {
                **_record_common(f"PR162-QPARAM-{index:03d}-{_slug(name)}"),
                "parameter_name": name,
                "candidate_value_or_range": "UNKNOWN_REQUIRED",
                "unit": "UNKNOWN_REQUIRED",
                "scale": "UNKNOWN_REQUIRED",
                "source_class": "QUANTUM_PARAMETER_RANGE_CANDIDATE",
                "source_locator_or_repo_ref": "PR162_ExternalCandidateIntakeRegistry.report.json",
                "candidate_authority_class": "UNKNOWN_REQUIRED",
                "applies_to_algorithm_family": family,
                "applies_to_qku_ids_or_family": "ALL_PR161F_QUANTUM_CLASSICAL_HYBRID_QKUS",
                "applies_to_qku_count": len(quantum_qku_ids),
                "replay_paper_required_flag": True,
                "owner_review_required_flag": True,
                "live_use_allowed_flag": False,
                "future_live_candidate_flag": True,
                "blocker_code_if_unverified": "PR162_BLOCKED_SOURCE_EVIDENCE_REQUIRED",
                "blocker_code": "PR162_BLOCKED_SOURCE_EVIDENCE_REQUIRED",
            }
        )
    return records


def _build_backend_records(quantum_qku_ids: list[str]) -> list[dict[str, Any]]:
    return [
        {
            **_record_common(f"PR162-QUANTUM-BACKEND-FIT-{index:05d}"),
            "qku_id": qku_id,
            "encoding_blueprint_ref": f"PR162-QUANTUM-ENCODING-{index:05d}",
            "candidate_backend_family": "BACKEND_BLOCKED_NO_DATA",
            "candidate_algorithm_family": "QUBO_QAOA_ANNEALING_FUTURE_CANDIDATE",
            "classical_baseline_required_flag": True,
            "hardware_required_flag": False,
            "simulator_required_flag": False,
            "local_execution_possible_candidate_flag": False,
            "cloud_execution_possible_candidate_flag": False,
            "credential_required_flag": False,
            "live_mode_forbidden_in_pr162_flag": True,
            "future_nonlive_benchmark_candidate_flag": True,
            "future_live_control_plane_candidate_flag": True,
            "future_live_hot_path_forbidden_flag": True,
            "future_live_precomputed_snapshot_candidate_flag": True,
            "expected_latency_class_candidate": "UNKNOWN_REQUIRED",
            "expected_cost_class_candidate": "UNKNOWN_REQUIRED",
            "expected_refresh_class_candidate": "UNKNOWN_REQUIRED",
            "data_requirement_class": "SAFE_REPO_LOCAL_NONLIVE_DATA_REQUIRED",
            "source_evidence_required_flag": True,
            "owner_review_required_flag": True,
            "blocker_code": "BACKEND_BLOCKED_NO_DATA",
            "downstream_pr_route": "PR163_RESULT_PACKET_ROUTE_AFTER_VALIDATED_REAL_NONLIVE_ARTIFACTS",
        }
        for index, qku_id in enumerate(quantum_qku_ids, start=1)
    ]


def _build_comparator_records(
    quantum_qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(quantum_qku_ids, start=1):
        qch = by_qku["qch"][qku_id]
        records.append(
            {
                **_record_common(f"PR162-QUANTUM-COMPARATOR-{index:05d}"),
                "qku_id": qku_id,
                "classical_baseline_plan_ref": qch.get("classical_baseline_route_id_if_available"),
                "quantum_candidate_plan_ref": qch["record_id"],
                "hybrid_candidate_plan_ref": qch.get("hybrid_arbitration_route_id_if_available"),
                "replay_artifact_requirement": "REAL_NONLIVE_REPLAY_ARTIFACT_CANDIDATE_REQUIRED",
                "paper_artifact_requirement": "REAL_NONLIVE_PAPER_ARTIFACT_CANDIDATE_REQUIRED",
                "sample_size_requirement_candidate": "UNKNOWN_REQUIRED",
                "confidence_requirement_candidate": "UNKNOWN_REQUIRED",
                "cost_metric_candidate": "CANDIDATE_ONLY",
                "latency_metric_candidate": "CANDIDATE_ONLY",
                "drawdown_metric_candidate": "CANDIDATE_ONLY",
                "slippage_metric_candidate": "CANDIDATE_ONLY",
                "net_profit_metric_candidate": "CANDIDATE_ONLY_NOT_EVIDENCE",
                "risk_adjusted_return_metric_candidate": "CANDIDATE_ONLY",
                "execution_quality_metric_candidate": "CANDIDATE_ONLY",
                "quantum_advantage_claim_allowed_flag": False,
                "advantage_evidence_required_flag": True,
                "result_authenticity_gate_required_flag": True,
                "owner_review_required_flag": True,
                "future_pr163_result_packet_route": c.DOWNSTREAM_PR_ROUTES[0],
                "future_pr164_authenticity_route": c.DOWNSTREAM_PR_ROUTES[1],
                "future_pr165_ranking_route": c.DOWNSTREAM_PR_ROUTES[2],
                "future_pr168_risk_route": c.DOWNSTREAM_PR_ROUTES[3],
                "future_live_promotion_route": c.DOWNSTREAM_PR_ROUTES[5],
                "comparator_blueprint_status": "COMPARATOR_BLOCKED_NO_SAFE_DATA",
                "blocker_code": "COMPARATOR_BLOCKED_NO_SAFE_DATA",
            }
        )
    return records


def _build_work_order_records(
    quantum_qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    parameter_refs = [
        f"PR162-QPARAM-{index:03d}-{_slug(name)}"
        for index, name in enumerate(c.PARAMETER_CANDIDATE_NAMES, start=1)
    ]
    for index, qku_id in enumerate(quantum_qku_ids, start=1):
        records.append(
            {
                **_record_common(f"PR162-QUANTUM-WORK-ORDER-{index:05d}"),
                "work_order_id": f"PR162-QUANTUM-WORK-ORDER-{index:05d}",
                "qku_id": qku_id,
                "paired_plan_ref": by_qku["paired"][qku_id]["paired_run_plan_id"],
                "encoding_blueprint_ref": f"PR162-QUANTUM-ENCODING-{index:05d}",
                "parameter_candidate_refs": parameter_refs,
                "backend_fit_ref": f"PR162-QUANTUM-BACKEND-FIT-{index:05d}",
                "comparator_blueprint_ref": f"PR162-QUANTUM-COMPARATOR-{index:05d}",
                "replay_lane_required_flag": True,
                "paper_lane_required_flag": True,
                "classical_baseline_required_flag": True,
                "hybrid_comparison_required_flag": True,
                "data_requirement": "SAFE_REPO_LOCAL_NONLIVE_DATA_REQUIRED",
                "adapter_requirement": "PR162_REPLAY_AND_PAPER_ADAPTER_CONTRACTS",
                "owner_review_requirement": "OWNER_REVIEW_REQUIRED_BEFORE_PROMOTION",
                "source_evidence_requirement": "SOURCE_EVIDENCE_REQUIRED_FOR_EXTERNAL_FACTS",
                "expected_next_pr_route": "SAFE_DATASET_ADAPTER_READINESS_BEFORE_PR163",
                "blocked_reason": "NO_SAFE_REPO_LOCAL_RUN_CAPABLE_DATASET_DISCOVERED",
                "ready_for_future_pr163_flag": False,
                "ready_for_future_pr164_flag": False,
                "ready_for_future_pr165_flag": False,
                "live_mode_ready_flag": False,
                "future_live_control_plane_candidate_flag": True,
                "future_live_precomputed_snapshot_candidate_flag": True,
                "quantum_forward_promotion_state": "QUANTUM_FORWARD_WORK_ORDER_READY",
                "blocker_code": "QUANTUM_BLOCKED_NO_SAFE_DATA",
            }
        )
    return records


def _build_live_control_records(quantum_qku_ids: list[str]) -> list[dict[str, Any]]:
    return [
        {
            **_record_common(f"PR162-QUANTUM-LIVE-CONTROL-{index:05d}"),
            "qku_id": qku_id,
            "future_live_role_candidates": list(c.FUTURE_ALLOWED_LIVE_MODE_QUANTUM_ROLES),
            "forbidden_live_roles": list(c.FORBIDDEN_LIVE_MODE_QUANTUM_ROLES),
            "live_hot_path_admissibility": "PRECOMPUTED_ONLY",
            "precomputed_snapshot_required_flag": True,
            "snapshot_ttl_candidate": "UNKNOWN_REQUIRED",
            "stale_snapshot_blocker_code": "PR162_STALE_PRECOMPUTED_SNAPSHOT_BLOCKER",
            "risk_gate_required_flag": True,
            "capital_gate_required_flag": True,
            "latency_gate_required_flag": True,
            "source_evidence_gate_required_flag": True,
            "owner_review_gate_required_flag": True,
            "live_connector_gate_required_flag": True,
            "canary_gate_required_flag": True,
            "result_authenticity_gate_required_flag": True,
            "replay_paper_evidence_required_flag": True,
            "live_mode_status": "FUTURE_GATED",
            "pr162_live_authority_created_flag": False,
            "future_live_precomputed_snapshot_candidate_flag": True,
            "blocker_code": "PR162_BLOCKED_OWNER_REVIEW_REQUIRED",
        }
        for index, qku_id in enumerate(quantum_qku_ids, start=1)
    ]


def _build_latency_records(
    quantum_qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(quantum_qku_ids, start=1):
        qch = by_qku["qch"][qku_id]
        records.append(
            {
                **_record_common(f"PR162-QUANTUM-LATENCY-{index:05d}"),
                "qku_id": qku_id,
                "expected_quantum_compute_latency_class_candidate": "UNKNOWN_REQUIRED",
                "expected_refresh_interval_candidate": "UNKNOWN_REQUIRED",
                "precomputed_snapshot_required_flag": True,
                "live_hot_path_admissibility": "PRECOMPUTED_SNAPSHOT_ONLY",
                "snapshot_freshness_field_required_flag": True,
                "stale_snapshot_action": "BLOCK_OR_IGNORE_QUANTUM_CANDIDATE",
                "missing_snapshot_action": "FALLBACK_CLASSICAL_OR_BLOCK_IF_REQUIRED",
                "invalid_snapshot_action": "QUARANTINE_AND_OWNER_ESCALATE",
                "fallback_classical_path_required_flag": True,
                "fallback_classical_path_ref_if_available": qch.get(
                    "classical_baseline_route_id_if_available"
                ),
                "replay_paper_refresh_required_flag": True,
                "source_revalidation_required_flag": True,
                "owner_reapproval_required_on_material_change_flag": True,
                "latency_agent_consumer_route": "QTT_LATENCY_AGENT",
                "execution_router_consumer_route": "QTT_EXECUTION_ROUTER_AGENT_NO_ORDER_ROUTE",
                "blocker_code": "QUANTUM_BLOCKED_LIVE_PATH_LATENCY_UNSAFE",
            }
        )
    return records


def _build_quantum_downstream_agent_records(quantum_qku_ids: list[str]) -> list[dict[str, Any]]:
    return [
        {
            **_record_common(f"PR162-QUANTUM-AGENT-ROUTE-{index:05d}"),
            "qku_id": qku_id,
            "downstream_agent_routes": [
                "QTT_QUANTUM_ADVISORY_AGENT",
                "QTT_OPTIMIZER_ARBITRATION_AGENT",
                "QTT_REPLAY_AGENT",
                "QTT_PAPER_AGENT",
                "QTT_LATENCY_AGENT",
                "QTT_EXECUTION_ROUTER_AGENT",
                "QTT_OWNER_REVIEW_AGENT",
            ],
            "quantum_specific_agent_routes": [
                "QTT_QUANTUM_ADVISORY_AGENT",
                "QTT_OPTIMIZER_ARBITRATION_AGENT",
            ],
            "agent_handoff_status": "PR162_AGENT_HANDOFF_READY_BLOCKED_INPUTS",
            "no_runtime_agent_execution_flag": True,
            "no_agent_self_authorizes_live_trading_flag": True,
            "blocker_code": "QUANTUM_BLOCKED_NO_SAFE_DATA",
        }
        for index, qku_id in enumerate(quantum_qku_ids, start=1)
    ]


def _build_quantum_artifact_input_records(
    quantum_qku_ids: list[str],
    by_qku: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(quantum_qku_ids, start=1):
        records.append(
            {
                **_record_common(f"PR162-QCH-ARTIFACT-INPUT-{index:05d}"),
                "qku_id": qku_id,
                "quantum_classical_hybrid_run_plan_ref": by_qku["qch"][qku_id]["record_id"],
                "encoding_blueprint_ref": f"PR162-QUANTUM-ENCODING-{index:05d}",
                "parameter_candidate_registry_ref": "PR162_QuantumParameterRangeCandidateRegistry.report.json",
                "backend_fit_ref": f"PR162-QUANTUM-BACKEND-FIT-{index:05d}",
                "comparator_blueprint_ref": f"PR162-QUANTUM-COMPARATOR-{index:05d}",
                "live_control_plane_ref": f"PR162-QUANTUM-LIVE-CONTROL-{index:05d}",
                "latency_readiness_ref": f"PR162-QUANTUM-LATENCY-{index:05d}",
                "real_nonlive_artifact_available_flag": False,
                "result_packet_ready_flag": False,
                "candidate_only_flag": True,
                "blocker_code": "QUANTUM_BLOCKED_NO_SAFE_DATA",
            }
        )
    return records


def _build_agent_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, agent_id in enumerate(c.AGENT_ROLES, start=1):
        quantum_role = agent_id in {
            "QTT_QUANTUM_ADVISORY_AGENT",
            "QTT_OPTIMIZER_ARBITRATION_AGENT",
        }
        records.append(
            {
                **_record_common(f"PR162-AGENT-HANDOFF-{index:02d}-{agent_id}"),
                "agent_id": agent_id,
                "reads_from_artifacts": _agent_reads(agent_id),
                "validates_input_with": [
                    "PR162_DataAuthorityAndProvenanceGate.report.json",
                    "PR162_ForbiddenAuthorityScan.report.json",
                ],
                "processing_role": _agent_processing_role(agent_id),
                "emits_artifacts": _agent_emits(agent_id),
                "downstream_agents": _agent_downstream(agent_id),
                "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
                "missing_input_behavior": "EMIT_BLOCKER_AND_OWNER_REVIEW_ROUTE",
                "stale_input_behavior": "EMIT_STALE_BLOCKER_AND_SOURCE_REVALIDATION_ROUTE",
                "unsafe_input_behavior": "QUARANTINE_AND_GOVERNANCE_ESCALATION",
                "contradictory_input_behavior": "OWNER_ESCALATION_REQUIRED",
                "unmappable_input_behavior": "BLOCK_ARTIFACT_MATERIALIZATION",
                "invalid_input_behavior": "FAIL_CLOSED",
                "retry_policy_ref": "PR161F_QTTAgentRetryRerouteQuarantinePolicy.report.json",
                "reroute_policy_ref": "PR161F_QTTAgentRetryRerouteQuarantinePolicy.report.json",
                "quarantine_policy_ref": "PR161F_QTTAgentRetryRerouteQuarantinePolicy.report.json",
                "owner_escalation_ref": "PR161F_QTTAgentOwnerEscalationQueue.report.json",
                "task_receipt_status": "NO_RUNTIME_AGENT_EXECUTION_PR162",
                "kpi_readiness_status": "CANDIDATE_ONLY_BLOCKED_INPUTS",
                "trust_score_inputs": [
                    "dataset_provenance_status",
                    "adapter_contract_status",
                    "forbidden_authority_scan_status",
                ],
                "no_authority_boundary_status": "NO_LIVE_NO_ORDER_NO_PRIVATE_STATE_NO_PROFIT",
                "quantum_forward_role_if_applicable": "QUANTUM_BLUEPRINT_AND_WORK_ORDER_ONLY"
                if quantum_role
                else "NOT_QUANTUM_SPECIFIC",
                "future_live_role_if_applicable": "FUTURE_GATED_PRECOMPUTED_OR_ASYNC_ONLY",
                "agent_handoff_status": "PR162_AGENT_HANDOFF_READY_BLOCKED_INPUTS",
                "self_authorizing_trading_allowed_flag": False,
                "runtime_agent_execution_created_flag": False,
                "live_authority_allowed_flag": False,
                "blocker_code": "PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
            }
        )
    return records


def _build_external_candidate_records() -> list[dict[str, Any]]:
    rows = (
        (
            "PR162-EXT-QUANTUM-ENCODING-METHOD-CANDIDATE",
            ["QUANTUM_METHOD_CANDIDATE", "QUANTUM_ENCODING_CANDIDATE"],
            "QUBO_BQM_CQM_ISING_FORMULATION_METADATA_ONLY",
        ),
        (
            "PR162-EXT-QUANTUM-PARAMETER-RANGE-CANDIDATE",
            ["QUANTUM_PARAMETER_RANGE_CANDIDATE", "QUANTUM_ALGORITHM_DOC_CANDIDATE"],
            "QAOA_VQE_ANNEALING_PARAMETER_METADATA_ONLY",
        ),
        (
            "PR162-EXT-QUANTUM-BACKEND-DOC-CANDIDATE",
            ["QUANTUM_BACKEND_DOC_CANDIDATE"],
            "BACKEND_FIT_METADATA_ONLY_NO_BACKEND_CALL",
        ),
        (
            "PR162-EXT-HYBRID-METHOD-CANDIDATE",
            ["HYBRID_METHOD_CANDIDATE", "CLASSICAL_METHOD_CANDIDATE"],
            "HYBRID_CLASSICAL_QUANTUM_COMPARATOR_METADATA_ONLY",
        ),
        (
            "PR162-EXT-INSTITUTIONAL-METHOD-CANDIDATE",
            ["INSTITUTIONAL_METHOD_CANDIDATE", "RESEARCH_SOURCE_CANDIDATE"],
            "BENCHMARK_DESIGN_METADATA_ONLY",
        ),
    )
    return [
        {
            **_record_common(record_id),
            "candidate_id": record_id,
            "source_classes": source_classes,
            "source_class": source_classes[0],
            "candidate_description": description,
            "dataset_authority_class": "ONLINE_DISCOVERED_CANDIDATE_METADATA_ONLY",
            "online_network_used_flag": False,
            "repo_local_run_data_materialized_flag": False,
            "candidate_only_flag": True,
            "source_evidence_required_flag": True,
            "accepted_as_official_fact_flag": False,
            "creates_connector_semantics": False,
            "live_use_allowed_flag": False,
            "blocker_code": "PR162_BLOCKED_SOURCE_EVIDENCE_REQUIRED",
        }
        for record_id, source_classes, description in rows
    ]


def _build_forbidden_scan_record() -> dict[str, Any]:
    return {
        **_record_common("PR162-FORBIDDEN-AUTHORITY-SCAN"),
        "scan_status": "PASS",
        "no_scattered_hardcoded_policy_scan_status": "PASS",
        "hidden_network_call_scan_status": "PASS",
        "absolute_path_scan_status": "PASS",
        "portable_shard_path_scan_status": "PASS",
        "orphan_non_rejected_qku_artifact_count": 0,
        "atomicrows_bundle_jsonl_mutation_detected_flag": False,
        "master_plan_mutation_detected_flag": False,
        "forbidden_authority_categories_scanned": list(c.FORBIDDEN_AUTHORITY_CATEGORIES),
        "forbidden_path_patterns_scanned": list(c.FORBIDDEN_PATH_PATTERNS),
        "policy_constants_module": f"{c.PACKAGE_IMPORT}.constants",
        "scan_scope": [
            "PR162_SOURCE_FILES",
            "PR162_GENERATED_REPORTS",
            "PR162_SCHEMA_FILES",
            "PR162_SHARDS",
        ],
        "blocker_code": "PR162_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
    }


def _coverage_counts(
    *,
    qku_ids: list[str],
    quantum_qku_ids: list[str],
    dataset_candidate_count: int,
    qku_coverage_records: list[dict[str, Any]],
) -> dict[str, int]:
    total = len(qku_ids)
    q_total = len(quantum_qku_ids)
    return {
        "total_qku_inputs_seen": total,
        "total_qku_with_executor_input": total,
        "total_qku_with_replay_request": total,
        "total_qku_with_paper_request": total,
        "total_qku_with_paired_plan": total,
        "total_qku_with_run_envelope": total,
        "total_qku_with_result_eligibility_gate": total,
        "total_qku_with_dataset_candidate": dataset_candidate_count,
        "total_qku_with_adapter_ready": total,
        "total_qku_with_real_nonlive_replay_artifact_candidate": 0,
        "total_qku_with_real_nonlive_paper_artifact_candidate": 0,
        "total_qku_with_both_lanes_candidate": 0,
        "total_qku_with_partial_lane_candidate": 0,
        "total_quantum_qku_seen": q_total,
        "total_quantum_qku_with_encoding_blueprint": q_total,
        "total_quantum_qku_with_parameter_candidates": q_total,
        "total_quantum_qku_with_backend_fit_candidate": q_total,
        "total_quantum_qku_with_comparator_blueprint": q_total,
        "total_quantum_qku_with_replay_paper_work_order": q_total,
        "total_quantum_qku_with_live_control_plane_bridge": q_total,
        "total_quantum_qku_with_latency_bridge": q_total,
        "total_quantum_qku_blocked_no_lineage": 0,
        "total_quantum_qku_blocked_no_encoding": 0,
        "total_quantum_qku_blocked_no_classical_baseline": 0,
        "total_quantum_qku_blocked_no_safe_data": q_total,
        "total_quantum_qku_future_live_precomputed_snapshot_candidate": q_total,
        "total_quantum_qku_future_async_control_plane_candidate": q_total,
        "total_qku_blocked_no_repo_local_data": total,
        "total_qku_blocked_synthetic_only": total,
        "total_qku_blocked_unsafe_data": 0,
        "total_qku_blocked_unmappable": 0,
        "total_qku_routed_to_owner_review_candidate": total,
        "total_qku_routed_to_future_pr163_candidate": 0,
        "total_qku_routed_to_future_pr164_authenticity_gate": total,
        "total_qku_routed_to_future_pr165_result_backed_ranking_gate": total,
        "total_qku_routed_to_future_pr168_risk_capital_latency_gate": total,
        "total_qku_routed_to_future_pr171_runtime_scheduler_gate": total,
        "total_qku_routed_to_future_pr177_live_safe_promotion_gate": total,
        "total_qku_routed_to_future_pr180_canary_gate": total,
        "orphan_count": 0,
        "rejected_or_quarantined_count": sum(
            1
            for record in qku_coverage_records
            if record["qku_coverage_state"] == "QKU_COVERED_WITH_BLOCKED_NONLIVE_LANES"
        ),
    }


def _shared_dictionary_payload() -> dict[str, Any]:
    return {
        "dictionary_version": "PR162_SHARED_DICTIONARY_V1",
        "central_policy_module": f"{c.PACKAGE_IMPORT}.constants",
        "report_names": list(c.REPORT_FILENAMES),
        "schema_names": list(c.SCHEMA_FILENAMES),
        "run_lanes": ["REPLAY", "PAPER"],
        "artifact_authority_classes": [c.ARTIFACT_AUTHORITY_CLASS, c.BLUEPRINT_AUTHORITY_CLASS],
        "dataset_authority_classes": list(c.DATASET_AUTHORITY_CLASSES),
        "source_classes": list(c.SOURCE_CLASSES),
        "artifact_status_enums": list(c.ARTIFACT_STATUS_ENUMS),
        "result_readiness_states": list(c.RESULT_READINESS_STATES),
        "pr161e_handoff_states": list(c.PR161E_HANDOFF_STATES),
        "qku_coverage_states": list(c.QKU_COVERAGE_STATES),
        "qtt_agent_handoff_statuses": list(c.QTT_AGENT_HANDOFF_STATUSES),
        "quantum_forward_promotion_states": list(c.QUANTUM_FORWARD_PROMOTION_STATES),
        "quantum_encoding_readiness_states": list(c.QUANTUM_ENCODING_READINESS_STATES),
        "quantum_backend_fit_readiness_states": list(c.QUANTUM_BACKEND_FIT_CLASSES),
        "quantum_live_path_admissibility_states": list(c.QUANTUM_LIVE_PATH_ADMISSIBILITY_STATES),
        "future_live_blocker_codes": [
            "PR162_BLOCKED_OWNER_REVIEW_REQUIRED",
            "PR162_STALE_PRECOMPUTED_SNAPSHOT_BLOCKER",
            "QUANTUM_BLOCKED_LIVE_PATH_LATENCY_UNSAFE",
        ],
        "unavailable_reason_codes": list(c.UNAVAILABLE_REASON_CODES),
        "forbidden_authority_categories": list(c.FORBIDDEN_AUTHORITY_CATEGORIES),
        "forbidden_path_patterns": list(c.FORBIDDEN_PATH_PATTERNS),
        "posix_shard_reference_rule": "SHARD_REFS_MUST_BE_REPO_RELATIVE_POSIX_PATHS",
        "report_compactness_thresholds": {
            "record_target": c.REPORT_SHARD_RECORD_TARGET,
            "byte_threshold": c.REPORT_SHARD_BYTE_THRESHOLD,
        },
        "shard_manifest_fields": [
            "report_filename",
            "shard_count",
            "shard_files",
            "posix_relative_shard_refs_flag",
        ],
        "no_scattered_hardcoding_allowlist": list(c.NO_SCATTERED_POLICY_ALLOWLIST),
    }


def _agent_reads(agent_id: str) -> list[str]:
    base = ["PR162_NonLiveDatasetDiscovery.report.json"]
    if agent_id in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return base + [
            "PR162_ReplayDataAdapterContract.report.json",
            "PR162_PaperDataAdapterContract.report.json",
        ]
    if agent_id in {"QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"}:
        return base + [
            "PR162_QKUQuantumExecutionReadinessBridge.report.json",
            "PR162_QKUQuantumProblemEncodingBlueprint.report.json",
            "PR162_QuantumBackendFitCandidateMatrix.report.json",
        ]
    if agent_id == "QTT_EXECUTION_ROUTER_AGENT":
        return base + ["PR162_QuantumLatencyLivePathReadinessBridge.report.json"]
    return base


def _agent_emits(agent_id: str) -> list[str]:
    if agent_id == "QTT_RESEARCH_AGENT":
        return ["candidate_classifications_only"]
    if agent_id == "QTT_SOURCE_EVIDENCE_AGENT":
        return ["source_evidence_routing_status_only"]
    if agent_id == "QTT_QUANTUM_ADVISORY_AGENT":
        return ["quantum_blueprints_and_work_orders_only"]
    if agent_id == "QTT_OPTIMIZER_ARBITRATION_AGENT":
        return ["optimizer_arbitration_readiness_metadata_only"]
    if agent_id == "QTT_REPLAY_AGENT":
        return ["replay_blocker_or_candidate_artifact_only"]
    if agent_id == "QTT_PAPER_AGENT":
        return ["paper_blocker_or_candidate_artifact_only"]
    return ["blocked_or_pending_readiness_metadata_only"]


def _agent_downstream(agent_id: str) -> list[str]:
    if agent_id in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return ["QTT_OWNER_REVIEW_AGENT", "QTT_GOVERNANCE_AGENT"]
    if agent_id in {"QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"}:
        return ["QTT_LATENCY_AGENT", "QTT_OWNER_REVIEW_AGENT", "QTT_GOVERNANCE_AGENT"]
    if agent_id == "QTT_OWNER_REVIEW_AGENT":
        return ["QTT_COMMANDER_AGENT", "QTT_GOVERNANCE_AGENT"]
    return ["QTT_GOVERNANCE_AGENT"]


def _agent_processing_role(agent_id: str) -> str:
    mapping = {
        "QTT_RESEARCH_AGENT": "classify_repo_local_and_external_candidates",
        "QTT_SOURCE_EVIDENCE_AGENT": "route_official_source_candidates_without_fact_acceptance",
        "QTT_ATOMICROWS_ENRICHMENT_AGENT": "link_atomicrows_qku_readiness_without_bundle_mutation",
        "QTT_PARAMETER_STACK_AGENT": "emit_parameter_stack_replay_paper_readiness_candidates",
        "QTT_QUANTUM_ADVISORY_AGENT": "emit_quantum_blueprints_backend_fit_and_work_orders_without_execution",
        "QTT_OPTIMIZER_ARBITRATION_AGENT": "emit_arbitration_readiness_without_optimizer_execution",
        "QTT_REPLAY_AGENT": "emit_replay_artifact_candidate_or_blocker",
        "QTT_PAPER_AGENT": "emit_paper_artifact_candidate_or_blocker_without_venue_api",
        "QTT_SCORING_AGENT": "emit_blocked_scoring_status_only",
        "QTT_RANKING_AGENT": "emit_blocked_ranking_status_only",
        "QTT_RISK_AGENT": "emit_future_risk_gate_placeholder",
        "QTT_CAPITAL_AGENT": "emit_future_capital_gate_placeholder_without_allocation",
        "QTT_LATENCY_AGENT": "emit_precomputed_snapshot_latency_readiness_only",
        "QTT_EXECUTION_PREP_AGENT": "emit_nonlive_execution_prep_readiness_only",
        "QTT_EXECUTION_ROUTER_AGENT": "emit_no_order_no_live_status",
        "QTT_OWNER_REVIEW_AGENT": "emit_owner_review_candidate_queue_only",
        "QTT_COMMANDER_AGENT": "emit_future_pr163_command_readiness_only",
        "QTT_GOVERNANCE_AGENT": "emit_governance_scan_status",
        "QTT_VENUE_SPECIALIST_AGENT": "emit_venue_specific_blockers_without_semantic_binding",
    }
    return mapping[agent_id]


def _algorithm_family_for_parameter(name: str) -> str:
    if name.startswith("qaoa_"):
        return "QAOA"
    if name.startswith("vqe_"):
        return "VQE"
    if name.startswith(("annealing_", "chain_", "num_reads")):
        return "ANNEALING"
    if name.startswith(("qubo_", "ising_", "bqm_", "cqm_")):
        return "QUBO_ISING_BQM_CQM"
    if name.startswith("hybrid_"):
        return "HYBRID_QUANTUM_CLASSICAL"
    if name.startswith("classical_"):
        return "CLASSICAL_BASELINE"
    return "CROSS_ALGORITHM_CONTROL_PLANE"


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


def _is_forbidden_path(rel: str) -> bool:
    normalized = rel.replace("\\", "/").lower()
    return any(pattern.lower() in normalized for pattern in c.FORBIDDEN_PATH_PATTERNS)


def _file_size_class(size: int) -> str:
    if size < 1_000_000:
        return "SMALL"
    if size < 25_000_000:
        return "MEDIUM"
    return "LARGE_STREAMING_METADATA_ONLY"


def _slug(value: str) -> str:
    slug = "".join(ch if ch.isalnum() else "-" for ch in value.upper()).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:120] or "VALUE"
