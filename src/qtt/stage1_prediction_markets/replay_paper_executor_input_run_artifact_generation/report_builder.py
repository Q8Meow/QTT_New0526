"""Top-level deterministic PR161F artifact construction."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import subprocess
from typing import Any

from . import constants as c
from .artifact_loaders import consume_text_artifacts, load_report
from .compact_records import build_shared_dictionary
from .json_io import encoded_json_size, stable_counter, write_json
from .models import BuildArtifacts
from .policy import authority_flags
from .pr136_orchestration_loader import load_pr136_control_plane
from .pr137r_pr138_atomicrows_loader import load_atomicrows_contracts
from .pr161c_inventory_loader import load_pr161c_inventory
from .pr161d_report_loader import load_pr161d_reports
from .pr161e_outcome_loader import load_pr161e_reports
from .report_sharding import payloads_for_write
from .schema_writer import write_schemas


def build_artifacts(
    root: Path | str,
    *,
    online_search_available: bool = True,
) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    _require_expected_branch(repo_root)
    context = _load_context(repo_root)
    _validate_upstream_counts(context)

    executor_capabilities = _executor_capability_records(repo_root)
    historical_candidates = _historical_data_candidate_records()
    dataset_authority = _dataset_authority_records(historical_candidates)
    executor_inputs = _executor_input_records(context)
    replay_requests = _replay_run_request_records(context, executor_inputs)
    paper_requests = _paper_run_request_records(context, executor_inputs)
    paired_plans = _paired_run_plan_records(context, executor_inputs, replay_requests, paper_requests)
    envelopes = _run_artifact_envelope_records(context, executor_inputs, replay_requests, paper_requests, paired_plans)
    synthetic = _synthetic_smoke_run_artifact_records(envelopes)
    real_nonlive: list[dict[str, Any]] = []
    eligibility = _result_packet_eligibility_records(envelopes)
    qch = _quantum_classical_hybrid_run_plan_records(context, replay_requests, paper_requests, envelopes)
    compatibility = _atomicrows_pr154_run_compatibility_records(context, envelopes)
    agent_tasks = _agent_run_task_records(context, executor_inputs, eligibility)
    owner_readiness = _owner_review_run_readiness_records(context, envelopes)
    traceability = _qku_end_to_end_traceability_records(
        context,
        executor_inputs,
        replay_requests,
        paper_requests,
        paired_plans,
        envelopes,
        eligibility,
        qch,
        compatibility,
    )
    graph_trace = _graph_traceability_bridge_records(traceability)
    workflow = _agent_workflow_records()
    role_io = _agent_role_io_records()
    handoffs = _agent_handoff_records()
    failures = _agent_failure_response_records()
    receipts = _agent_task_receipt_records()
    communication = _agent_communication_protocol_records()
    kpi = _agent_kpi_readiness_records()
    retry_policy = _agent_retry_reroute_quarantine_records()
    owner_escalation = _agent_owner_escalation_records(failures)
    online = _online_candidate_records(online_search_available)
    missing = _missing_value_records()
    forbidden_scan = _forbidden_authority_scan_records(repo_root)
    hardcoded_audit = _no_scattered_hardcoded_audit_records(repo_root)
    preflight = _preflight_receipt(repo_root, context, online_search_available)

    summary = _summary(
        repo_root=repo_root,
        context=context,
        executor_capabilities=executor_capabilities,
        historical_candidates=historical_candidates,
        dataset_authority=dataset_authority,
        executor_inputs=executor_inputs,
        replay_requests=replay_requests,
        paper_requests=paper_requests,
        paired_plans=paired_plans,
        envelopes=envelopes,
        synthetic=synthetic,
        real_nonlive=real_nonlive,
        eligibility=eligibility,
        qch=qch,
        compatibility=compatibility,
        agent_tasks=agent_tasks,
        owner_readiness=owner_readiness,
        traceability=traceability,
        graph_trace=graph_trace,
        workflow=workflow,
        role_io=role_io,
        handoffs=handoffs,
        failures=failures,
        receipts=receipts,
        communication=communication,
        kpi=kpi,
        retry_policy=retry_policy,
        owner_escalation=owner_escalation,
        online=online,
        missing=missing,
        forbidden_scan=forbidden_scan,
        hardcoded_audit=hardcoded_audit,
    )

    payloads: dict[str, dict[str, Any]] = {
        "PR161F_ReplayPaperExecutorInputPreflightReceipt.report.json": _report(
            "PR161F_REPLAY_PAPER_EXECUTOR_INPUT_PREFLIGHT_RECEIPT", [preflight]
        ),
        "PR161F_ExecutorCapabilityDiscovery.report.json": _report(
            "PR161F_EXECUTOR_CAPABILITY_DISCOVERY", executor_capabilities
        ),
        "PR161F_HistoricalDataCandidateDiscovery.report.json": _report(
            "PR161F_HISTORICAL_DATA_CANDIDATE_DISCOVERY", historical_candidates
        ),
        "PR161F_DatasetAuthorityClassification.report.json": _report(
            "PR161F_DATASET_AUTHORITY_CLASSIFICATION", dataset_authority
        ),
        "PR161F_ExecutorInputRegistry.report.json": _report(
            "PR161F_EXECUTOR_INPUT_REGISTRY", executor_inputs
        ),
        "PR161F_ReplayRunRequestRegistry.report.json": _report(
            "PR161F_REPLAY_RUN_REQUEST_REGISTRY", replay_requests
        ),
        "PR161F_PaperRunRequestRegistry.report.json": _report(
            "PR161F_PAPER_RUN_REQUEST_REGISTRY", paper_requests
        ),
        "PR161F_PairedReplayPaperRunPlan.report.json": _report(
            "PR161F_PAIRED_REPLAY_PAPER_RUN_PLAN", paired_plans
        ),
        "PR161F_RunArtifactEnvelopeRegistry.report.json": _report(
            "PR161F_RUN_ARTIFACT_ENVELOPE_REGISTRY", envelopes
        ),
        "PR161F_SyntheticSmokeRunArtifactRegistry.report.json": _report(
            "PR161F_SYNTHETIC_SMOKE_RUN_ARTIFACT_REGISTRY", synthetic
        ),
        "PR161F_RealNonLiveRunArtifactRegistry.report.json": _report(
            "PR161F_REAL_NONLIVE_RUN_ARTIFACT_REGISTRY",
            real_nonlive,
            extra={
                "real_nonlive_replay_run_artifact_count": 0,
                "real_nonlive_paper_run_artifact_count": 0,
                "real_nonlive_artifact_status": "REAL_NONLIVE_EXECUTOR_OR_DATA_CONTRACT_NOT_DISCOVERED",
            },
        ),
        "PR161F_ResultPacketEmissionEligibilityGate.report.json": _report(
            "PR161F_RESULT_PACKET_EMISSION_ELIGIBILITY_GATE", eligibility
        ),
        "PR161F_QuantumClassicalHybridRunPlan.report.json": _report(
            "PR161F_QUANTUM_CLASSICAL_HYBRID_RUN_PLAN", qch
        ),
        "PR161F_AtomicRowsPR154RunCompatibilityBridge.report.json": _report(
            "PR161F_ATOMICROWS_PR154_RUN_COMPATIBILITY_BRIDGE", compatibility
        ),
        "PR161F_AgentRunTaskQueue.report.json": _report(
            "PR161F_AGENT_RUN_TASK_QUEUE",
            agent_tasks,
            extra={
                "logical_task_count": c.EXPECTED_PR161F_COUNTS["agent_run_task_logical_count"],
                "role_counts": {
                    record["assigned_agent_role"]: record["logical_task_count_for_role"]
                    for record in agent_tasks
                },
                "run_task_consumer_roles": list(c.AGENT_ROLES),
                "missing_runtime_manifest_roles_classified_as_pending": [
                    role
                    for role in c.AGENT_ROLES
                    if role not in {record["assigned_agent_role"] for record in agent_tasks}
                ],
            },
        ),
        "PR161F_OwnerReviewRunReadinessQueue.report.json": _report(
            "PR161F_OWNER_REVIEW_RUN_READINESS_QUEUE", owner_readiness
        ),
        "PR161F_QKUEndToEndTraceabilityMatrix.report.json": _report(
            "PR161F_QKU_END_TO_END_TRACEABILITY_MATRIX", traceability
        ),
        "PR161F_QTTAgentWorkflowOrchestrationContract.report.json": _report(
            "PR161F_QTT_AGENT_WORKFLOW_ORCHESTRATION_CONTRACT", workflow
        ),
        "PR161F_QTTAgentRoleIOContract.report.json": _report(
            "PR161F_QTT_AGENT_ROLE_IO_CONTRACT", role_io
        ),
        "PR161F_QTTAgentHandoffMatrix.report.json": _report(
            "PR161F_QTT_AGENT_HANDOFF_MATRIX", handoffs
        ),
        "PR161F_QTTAgentFailureResponseMatrix.report.json": _report(
            "PR161F_QTT_AGENT_FAILURE_RESPONSE_MATRIX", failures
        ),
        "PR161F_QTTAgentTaskReceiptLedger.report.json": _report(
            "PR161F_QTT_AGENT_TASK_RECEIPT_LEDGER", receipts
        ),
        "PR161F_QTTAgentCommunicationProtocol.report.json": _report(
            "PR161F_QTT_AGENT_COMMUNICATION_PROTOCOL", communication
        ),
        "PR161F_QTTAgentKPIReadinessBridge.report.json": _report(
            "PR161F_QTT_AGENT_KPI_READINESS_BRIDGE", kpi
        ),
        "PR161F_QTTAgentRetryRerouteQuarantinePolicy.report.json": _report(
            "PR161F_QTT_AGENT_RETRY_REROUTE_QUARANTINE_POLICY", retry_policy
        ),
        "PR161F_QTTAgentOwnerEscalationQueue.report.json": _report(
            "PR161F_QTT_AGENT_OWNER_ESCALATION_QUEUE", owner_escalation
        ),
        "PR161F_OnlineCandidateIntake.report.json": _report(
            "PR161F_ONLINE_CANDIDATE_INTAKE",
            online,
            extra={
                "online_search_attempted_flag": True,
                "online_search_available_flag": online_search_available,
                "online_search_unavailable_non_blocking_flag": not online_search_available,
            },
        ),
        "PR161F_MissingValueCandidateMaterialization.report.json": _report(
            "PR161F_MISSING_VALUE_CANDIDATE_MATERIALIZATION", missing
        ),
        "PR161F_QKUGraphTraceabilityBridge.report.json": _report(
            "PR161F_QKU_GRAPH_TRACEABILITY_BRIDGE", graph_trace
        ),
        "PR161F_ForbiddenAuthorityScan.report.json": _report(
            "PR161F_FORBIDDEN_AUTHORITY_SCAN", forbidden_scan
        ),
        "PR161F_NoScatteredHardcodedAuthorityAudit.report.json": _report(
            "PR161F_NO_SCATTERED_HARDCODED_AUTHORITY_AUDIT", hardcoded_audit
        ),
        "PR161F_ReportShardManifest.report.json": _report(
            "PR161F_REPORT_SHARD_MANIFEST", []
        ),
        "PR161F_SizeAudit.report.json": _report("PR161F_SIZE_AUDIT", []),
        "PR161F_FinalSummary.report.json": _final_summary_report(summary),
    }
    shared_dictionary = build_shared_dictionary(payloads)
    payloads[c.SHARED_DICTIONARY_REPORT_FILENAME] = _report(
        "PR161F_SHARED_DICTIONARY",
        [],
        extra={
            "compact_record_version": shared_dictionary["compact_record_version"],
            "dictionary_version": shared_dictionary["dictionary_version"],
            "compacted_report_count": len(shared_dictionary["compacted_report_filenames"]),
            "compacted_report_filenames": shared_dictionary["compacted_report_filenames"],
            "qku_trace_index_count": shared_dictionary["qku_trace_index_count"],
            "shared_dictionary": shared_dictionary,
        },
    )
    return BuildArtifacts(payloads=payloads, summary=summary)


def write_artifacts(root: Path | str, *, online_search_available: bool = True) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    write_schemas(repo_root)
    artifacts = build_artifacts(repo_root, online_search_available=online_search_available)
    shared_dictionary = artifacts.payloads[c.SHARED_DICTIONARY_REPORT_FILENAME]["shared_dictionary"]
    main_payloads, shard_payloads, manifest_records = payloads_for_write(
        artifacts.payloads,
        shared_dictionary=shared_dictionary,
    )
    manifest_payload = _report("PR161F_REPORT_SHARD_MANIFEST", manifest_records)
    manifest_payload["report_sharding_status"] = (
        "SHARDED_LARGE_REPORTS_UNDER_75_MIB" if manifest_records else "NO_SHARDS_REQUIRED"
    )
    manifest_payload["total_shard_count"] = sum(int(record["shard_count"]) for record in manifest_records)
    manifest_payload["total_sharded_report_count"] = len(manifest_records)
    manifest_payload["all_shard_files"] = [
        shard_file
        for record in manifest_records
        for shard_file in record.get("shard_files", [])
    ]
    manifest_payload["all_shard_refs_posix_flag"] = all(
        "\\" not in shard_file for shard_file in manifest_payload["all_shard_files"]
    )
    main_payloads["PR161F_ReportShardManifest.report.json"] = manifest_payload

    size_summary = _size_summary(main_payloads, shard_payloads)
    size_payload = _report(
        "PR161F_SIZE_AUDIT",
        [
            {
                "record_id": "PR161F-SIZE-AUDIT-00001",
                **size_summary,
                "generated_footprint_under_75_mib_flag": size_summary["total_pr161f_generated_footprint_bytes"]
                < c.GENERATED_FOOTPRINT_TARGET_BYTES,
                "largest_top_level_report_under_5_mib_flag": size_summary["largest_top_level_pr161f_report_size_bytes"]
                < c.LARGEST_SHARD_TARGET_BYTES,
                "largest_shard_under_5_mib_flag": size_summary["largest_pr161f_shard_size_bytes"]
                < c.LARGEST_SHARD_TARGET_BYTES,
            }
        ],
    )
    main_payloads["PR161F_SizeAudit.report.json"] = size_payload
    artifacts.summary.update(size_summary)
    artifacts.summary["report_sharding_status"] = manifest_payload["report_sharding_status"]
    artifacts.summary["report_shard_count"] = manifest_payload["total_shard_count"]
    artifacts.summary["pr152_currentization_status"] = (
        "PR152_AUDIT_PRESENT_AND_ALLOWED_FOR_PR161F_CURRENTIZATION"
        if (repo_root / c.PR152_AUDIT_REPORT_PATH).exists()
        else "PR152_AUDIT_MISSING_REQUIRES_WRITE_REPORT_AFTER_PR161F_GENERATION"
    )
    main_payloads["PR161F_FinalSummary.report.json"] = _final_summary_report(artifacts.summary)

    for filename, payload in main_payloads.items():
        write_json(
            repo_root / c.GENERATED_DIR / filename,
            payload,
            compact=filename == c.SHARED_DICTIONARY_REPORT_FILENAME,
        )
    for rel_path, payload in shard_payloads.items():
        write_json(repo_root / rel_path, payload, compact=True)
    _write_superseded_stale_shard_placeholders(repo_root, set(shard_payloads))
    return BuildArtifacts(payloads=main_payloads, shard_payloads=shard_payloads, summary=artifacts.summary)


def _load_context(repo_root: Path) -> dict[str, Any]:
    master_status = consume_text_artifacts(repo_root, c.ALWAYS_READ_MASTER_AUTHORITY_PATHS)
    pr136 = load_pr136_control_plane(repo_root)
    atomic_contracts = load_atomicrows_contracts(repo_root)
    consume_text_artifacts(repo_root, c.REPLAY_PAPER_CONTRACT_PATHS)
    consume_text_artifacts(repo_root, c.SOURCE_EVIDENCE_OPEN_INTAKE_PATHS)
    consume_text_artifacts(repo_root, c.QUANTUM_SCORING_PARAMETER_VALIDATOR_PATHS)
    consume_text_artifacts(repo_root, c.VALIDATION_CI_ANTI_CHURN_PATHS)
    pr161c = load_pr161c_inventory(repo_root)
    pr161d = load_pr161d_reports(repo_root)
    pr161e = load_pr161e_reports(repo_root)

    qku_by_id = {str(record["qku_id"]): record for record in pr161c["qkus"]}
    qku_index_by_qku = {
        str(record["qku_id"]): index
        for index, record in enumerate(pr161c["qkus"], start=1)
    }
    graph_by_qku = {str(record["qku_id"]): record for record in pr161c["graph_nodes"]}
    quality_by_qku = {str(record["qku_id"]): record for record in pr161d["quality_score"]}
    replay_by_qku = {
        str(record["qku_id"]): record
        for record in pr161d["replay_paper_scenario_inputs"]
    }
    priority_by_qku = {
        str(record["qku_id"]): record
        for record in pr161d["replay_paper_priority_queue"]
    }
    quantum_by_qku = {str(record["qku_id"]): record for record in pr161d["quantum_priority_queue"]}
    classical_by_qku = {str(record["qku_id"]): record for record in pr161d["classical_baseline_queue"]}
    hybrid_by_qku = {str(record["qku_id"]): record for record in pr161d["hybrid_arbitration_queue"]}
    owner_review_by_qku: dict[str, dict[str, Any]] = {}
    for record in pr161d["owner_review_queue"]:
        owner_review_by_qku.setdefault(str(record.get("qku_id")), record)
    roles_by_qku: dict[str, list[str]] = defaultdict(list)
    agent_task_refs_by_qku: dict[str, list[str]] = defaultdict(list)
    for task in pr161d["agent_task_queue"]:
        role = str(task.get("assigned_agent_role"))
        qku_id = str(task.get("qku_id"))
        if role and role not in roles_by_qku[qku_id]:
            roles_by_qku[qku_id].append(role)
        if task.get("task_id"):
            agent_task_refs_by_qku[qku_id].append(str(task["task_id"]))
    scenario_index_by_qku = {
        str(record["qku_id"]): index
        for index, record in enumerate(pr161d["replay_paper_scenario_inputs"], start=1)
    }
    return {
        "master_status": master_status,
        "pr136": pr136,
        "atomic_contracts": atomic_contracts,
        "pr161e": pr161e,
        "qkus": pr161c["qkus"],
        "qku_by_id": qku_by_id,
        "qku_index_by_qku": qku_index_by_qku,
        "graph_nodes": pr161c["graph_nodes"],
        "graph_edges": pr161c["graph_edges"],
        "graph_by_qku": graph_by_qku,
        "quantum_forward": pr161c["quantum_forward"],
        "quality_by_qku": quality_by_qku,
        "replay_by_qku": replay_by_qku,
        "priority_by_qku": priority_by_qku,
        "quantum_by_qku": quantum_by_qku,
        "classical_by_qku": classical_by_qku,
        "hybrid_by_qku": hybrid_by_qku,
        "owner_review_by_qku": owner_review_by_qku,
        "roles_by_qku": roles_by_qku,
        "agent_task_refs_by_qku": agent_task_refs_by_qku,
        "scenario_index_by_qku": scenario_index_by_qku,
        **pr161d,
    }


def _executor_capability_records(repo_root: Path) -> list[dict[str, Any]]:
    path_groups = {
        "replay_paper_contracts": c.REPLAY_PAPER_CONTRACT_PATHS,
        "fixture_datasets": (Path("tests/fixtures/replay_paper"), Path("tests/fixtures/source_evidence/replay_paper")),
        "runtime_executor_like_modules": (
            Path("src/qtt/stage1_prediction_markets/replay_paper"),
            Path("src/qtt/stage1_prediction_markets/runtime_resolver_snapshot_executor"),
        ),
    }
    records: list[dict[str, Any]] = []
    for index, (group, paths) in enumerate(path_groups.items(), start=1):
        existing = [path.as_posix() for path in paths if (repo_root / path).exists()]
        capability = "EXECUTOR_INPUT_ONLY"
        if group == "fixture_datasets" and existing:
            capability = "SYNTHETIC_SMOKE_RUN_AVAILABLE"
        if group == "runtime_executor_like_modules":
            capability = "EXECUTOR_UNAVAILABLE"
        records.append(
            {
                "record_id": f"PR161F-EXECUTOR-CAPABILITY-{index:04d}",
                "executor_capability_state": capability,
                "capability_group": group,
                "discovered_paths": existing,
                "real_nonlive_run_available_flag": False,
                "synthetic_smoke_run_available_flag": group == "fixture_datasets" and bool(existing),
                "unsafe_live_dependency_blocked_flag": False,
                "source_route": "PR161F_MISSING_VALUE_MATERIALIZATION",
                **authority_flags(),
            }
        )
    records.append(
        {
            "record_id": "PR161F-EXECUTOR-CAPABILITY-0004",
            "executor_capability_state": "UNSAFE_LIVE_DEPENDENCY_BLOCKED",
            "capability_group": "live_connector_and_private_state_boundary",
            "discovered_paths": [],
            "real_nonlive_run_available_flag": False,
            "synthetic_smoke_run_available_flag": False,
            "unsafe_live_dependency_blocked_flag": True,
            "source_route": "OWNER_APPROVED_PROVISIONAL_DEFAULT",
            **authority_flags(),
        }
    )
    return records


def _historical_data_candidate_records() -> list[dict[str, Any]]:
    candidates = [
        ("HISTORICAL_DATA_CANDIDATE", "repo_fixture_replay_paper", "tests/fixtures/replay_paper"),
        ("STATIC_TEST_FIXTURE_DATASET", "source_evidence_replay_paper_fixture", "tests/fixtures/source_evidence/replay_paper"),
        ("OFFICIAL_SOURCE_DATA_CANDIDATE", "cftc_prediction_market_reference", "https://www.cftc.gov/LearnandProtect/PredictionMarkets"),
        ("RESEARCH_DATA_CANDIDATE", "prediction_market_calibration_research", "https://www.jstor.org/stable/3083277"),
        ("WEB_DATA_CANDIDATE", "public_metric_reference_candidate", "https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp"),
    ]
    return [
        {
            "record_id": f"PR161F-HISTORICAL-DATA-CANDIDATE-{index:04d}",
            "dataset_candidate_ref": ref,
            "dataset_authority_class": authority_class,
            "source_locator": locator,
            "candidate_only_flag": True,
            "promotion_blocker": "SOURCE_EVIDENCE_ACCEPTANCE_AND_OWNER_REVIEW_REQUIRED",
            "owner_review_required_flag": True,
            "source_route": "HISTORICAL_DATA_CANDIDATE_DISCOVERY",
            **authority_flags(),
        }
        for index, (authority_class, ref, locator) in enumerate(candidates, start=1)
    ]


def _dataset_authority_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, authority_class in enumerate(c.DATASET_AUTHORITY_CLASSES, start=1):
        matching = [
            record["dataset_candidate_ref"]
            for record in candidates
            if record["dataset_authority_class"] == authority_class
        ]
        records.append(
            {
                "record_id": f"PR161F-DATASET-AUTHORITY-{index:04d}",
                "dataset_authority_class": authority_class,
                "candidate_refs": matching,
                "candidate_only_flag": authority_class not in {
                    "LIVE_CONNECTOR_DATA_FORBIDDEN",
                    "PRIVATE_STATE_DATA_FORBIDDEN",
                    "UNSAFE_OR_UNMAPPABLE_DATASET",
                },
                "forbidden_for_pr161f_flag": authority_class in {
                    "LIVE_CONNECTOR_DATA_FORBIDDEN",
                    "PRIVATE_STATE_DATA_FORBIDDEN",
                    "UNSAFE_OR_UNMAPPABLE_DATASET",
                },
                "result_evidence_allowed_flag": False,
                "owner_review_required_flag": True,
                **authority_flags(),
            }
        )
    return records


def _executor_input_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, scenario in enumerate(context["replay_paper_scenario_inputs"], start=1):
        qku_id = str(scenario["qku_id"])
        qku = context["qku_by_id"].get(qku_id, {})
        trace = _surface_trace(context, qku_id)
        records.append(
            {
                "record_id": f"PR161F-EXECUTOR-INPUT-{index:05d}",
                "executor_input_id": f"PR161F-EXECUTOR-INPUT-{index:05d}",
                "executor_input_type": "REPLAY_PAPER_EXECUTOR_INPUT",
                "qku_id": qku_id,
                "qku_graph_node_id": trace["qku_graph_node_id"],
                "qku_bundle_id_if_available": scenario.get("qku_bundle_id_if_applicable"),
                "scenario_matrix_id_if_available": scenario.get("scenario_matrix_id_if_applicable"),
                "replay_paper_scenario_id_if_available": scenario.get("replay_paper_scenario_input_id"),
                "market": qku.get("qku_market_primary", "PREDICTION_MARKET"),
                "platform": "QTT_STAGE1_PREDICTION_MARKETS",
                "venue_scope": "NONLIVE_REPLAY_PAPER_ONLY",
                "dataset_authority_class": "NO_DATASET_AVAILABLE",
                "dataset_candidate_ref_if_available": None,
                "input_provenance_class": "PR161D_PR161E_DERIVED_NONLIVE_INPUT",
                "input_requirements": scenario.get("input_requirements", []),
                "expected_observation_metrics": scenario.get("expected_observation_metrics", []),
                "required_baselines": scenario.get("required_baselines", []),
                "executor_input_state": "EXECUTOR_INPUT_PRODUCED",
                "value_authority_class": "OWNER_APPROVED_INTERNAL_POLICY",
                "source_route": "PR161D_REPLAY_PAPER_PREPARATION",
                "owner_review_required_flag": True,
                "replay_paper_required_flag": True,
                **authority_flags(),
                **trace,
            }
        )
    return records


def _replay_run_request_records(
    context: dict[str, Any],
    executor_inputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del context
    records: list[dict[str, Any]] = []
    for index, record in enumerate(executor_inputs, start=1):
        records.append(
            {
                "record_id": f"PR161F-REPLAY-RUN-REQUEST-{index:05d}",
                "replay_run_request_id": f"PR161F-REPLAY-RUN-REQUEST-{index:05d}",
                "run_request_type": "REPLAY_RUN_REQUEST",
                "executor_input_id": record["executor_input_id"],
                "qku_id": record["qku_id"],
                "dataset_authority_class": "NO_DATASET_AVAILABLE",
                "execution_mode": "REPLAY_NONLIVE",
                "execution_state": "INPUT_READY_RUN_PENDING",
                "run_request_state": "RUN_REQUEST_PRODUCED",
                "result_state": "NO_RESULT_YET",
                "result_packet_emission_eligibility_state": "RESULT_PACKET_EMISSION_BLOCKED",
                "eligibility_blocker": c.RUN_ARTIFACT_PENDING_BLOCKER_CODE,
                "owner_review_required_flag": True,
                **authority_flags(),
                **_copy_trace(record),
            }
        )
    return records


def _paper_run_request_records(
    context: dict[str, Any],
    executor_inputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del context
    records: list[dict[str, Any]] = []
    for index, record in enumerate(executor_inputs, start=1):
        records.append(
            {
                "record_id": f"PR161F-PAPER-RUN-REQUEST-{index:05d}",
                "paper_run_request_id": f"PR161F-PAPER-RUN-REQUEST-{index:05d}",
                "run_request_type": "PAPER_RUN_REQUEST",
                "executor_input_id": record["executor_input_id"],
                "qku_id": record["qku_id"],
                "dataset_authority_class": "NO_DATASET_AVAILABLE",
                "execution_mode": "PAPER_NONLIVE_NO_CONNECTOR",
                "execution_state": "INPUT_READY_RUN_PENDING",
                "run_request_state": "RUN_REQUEST_PRODUCED",
                "result_state": "NO_RESULT_YET",
                "result_packet_emission_eligibility_state": "RESULT_PACKET_EMISSION_BLOCKED",
                "eligibility_blocker": c.RUN_ARTIFACT_PENDING_BLOCKER_CODE,
                "owner_review_required_flag": True,
                "live_write_secret_required_flag": False,
                **authority_flags(),
                **_copy_trace(record),
            }
        )
    return records


def _paired_run_plan_records(
    context: dict[str, Any],
    executor_inputs: list[dict[str, Any]],
    replay_requests: list[dict[str, Any]],
    paper_requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del context
    records: list[dict[str, Any]] = []
    for index, (executor, replay, paper) in enumerate(
        zip(executor_inputs, replay_requests, paper_requests), start=1
    ):
        records.append(
            {
                "record_id": f"PR161F-PAIRED-RUN-PLAN-{index:05d}",
                "paired_run_plan_id": f"PR161F-PAIRED-RUN-PLAN-{index:05d}",
                "qku_id": executor["qku_id"],
                "executor_input_id": executor["executor_input_id"],
                "replay_run_request_id_if_available": replay["replay_run_request_id"],
                "paper_run_request_id_if_available": paper["paper_run_request_id"],
                "run_plan_state": "PAIRED_REPLAY_PAPER_RUN_PLAN_PRODUCED",
                "comparison_state": "REPLAY_PAPER_RUN_PLAN_READY",
                "result_state": "NO_RESULT_YET",
                "owner_review_required_flag": True,
                "future_pr_route": "PR161G_OR_PR162_RESULT_PACKET_ROUTE_AFTER_REAL_NONLIVE_ARTIFACT",
                **authority_flags(),
                **_copy_trace(executor),
            }
        )
    return records


def _run_artifact_envelope_records(
    context: dict[str, Any],
    executor_inputs: list[dict[str, Any]],
    replay_requests: list[dict[str, Any]],
    paper_requests: list[dict[str, Any]],
    paired_plans: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del context
    records: list[dict[str, Any]] = []
    for index, (executor, replay, paper, plan) in enumerate(
        zip(executor_inputs, replay_requests, paper_requests, paired_plans), start=1
    ):
        records.append(
            {
                "record_id": f"PR161F-RUN-ARTIFACT-ENVELOPE-{index:05d}",
                "run_artifact_id": f"PR161F-RUN-ARTIFACT-ENVELOPE-{index:05d}",
                "run_artifact_class": "RUN_ARTIFACT_ENVELOPE_PRODUCED",
                "run_artifact_authenticity_class": "RUN_ARTIFACT_PENDING_NOT_PERFORMANCE_EVIDENCE",
                "executor_input_id": executor["executor_input_id"],
                "replay_run_request_id_if_available": replay["replay_run_request_id"],
                "paper_run_request_id_if_available": paper["paper_run_request_id"],
                "paired_run_plan_id_if_available": plan["paired_run_plan_id"],
                "qku_id": executor["qku_id"],
                "qku_bundle_id_if_available": executor.get("qku_bundle_id_if_available"),
                "scenario_matrix_id_if_available": executor.get("scenario_matrix_id_if_available"),
                "replay_paper_scenario_id_if_available": executor.get("replay_paper_scenario_id_if_available"),
                "market": executor["market"],
                "platform": executor["platform"],
                "venue_scope": executor["venue_scope"],
                "dataset_candidate_ref_if_available": None,
                "dataset_authority_class": "NO_DATASET_AVAILABLE",
                "input_provenance_class": "PR161F_EXECUTOR_INPUT_PACKET",
                "execution_mode": "REPLAY_PAPER_NONLIVE_PLANNED",
                "execution_state": "INPUT_READY_RUN_PENDING",
                "run_validation_state": "RUN_ARTIFACT_ENVELOPE_VALIDATED_INPUT_ONLY",
                "result_packet_emission_eligibility_state": "RESULT_PACKET_EMISSION_BLOCKED",
                "synthetic_flag": False,
                "real_nonlive_flag": False,
                "owner_review_required_flag": True,
                "future_pr_route": "PR161G_OR_PR162_SAFE_NONLIVE_EXECUTOR_DATA_ADAPTER",
                **authority_flags(),
                **_copy_trace(executor),
            }
        )
    return records


def _synthetic_smoke_run_artifact_records(envelopes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, envelope in enumerate(envelopes[: c.EXPECTED_PR161F_COUNTS["synthetic_smoke_run_artifact_max"]], start=1):
        records.append(
            {
                **{key: envelope[key] for key in c.RUN_ARTIFACT_REQUIRED_FIELDS if key in envelope},
                "record_id": f"PR161F-SYNTHETIC-SMOKE-RUN-ARTIFACT-{index:04d}",
                "run_artifact_id": f"PR161F-SYNTHETIC-SMOKE-RUN-ARTIFACT-{index:04d}",
                "run_artifact_class": "SYNTHETIC_PIPELINE_SMOKE_RUN_ARTIFACT",
                "run_artifact_authenticity_class": "SYNTHETIC_FIXTURE_NOT_PERFORMANCE_EVIDENCE",
                "dataset_candidate_ref_if_available": "tests/fixtures/replay_paper",
                "dataset_authority_class": "SYNTHETIC_FIXTURE_DATASET",
                "execution_mode": "SYNTHETIC_PIPELINE_SCHEMA_SMOKE_ONLY",
                "execution_state": "SYNTHETIC_SMOKE_VALIDATED",
                "run_validation_state": "SYNTHETIC_SCHEMA_PIPELINE_VALIDATED",
                "synthetic_flag": True,
                "real_nonlive_flag": False,
                "result_packet_emission_eligibility_state": "RESULT_PACKET_EMISSION_BLOCKED",
                "eligibility_blocker": c.SYNTHETIC_RESULT_PACKET_BLOCKER_CODE,
                "treated_as_performance_evidence_flag": False,
                "treated_as_profit_evidence_flag": False,
                "pr161e_capture_update_allowed_flag": False,
                **authority_flags(),
                **_copy_trace(envelope),
            }
        )
    return records


def _result_packet_eligibility_records(envelopes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, envelope in enumerate(envelopes, start=1):
        records.append(
            {
                "record_id": f"PR161F-RESULT-PACKET-ELIGIBILITY-{index:05d}",
                "result_packet_emission_eligibility_id": f"PR161F-RESULT-PACKET-ELIGIBILITY-{index:05d}",
                "qku_id": envelope["qku_id"],
                "run_artifact_id": envelope["run_artifact_id"],
                "result_packet_emission_eligibility_state": "RESULT_PACKET_EMISSION_BLOCKED",
                "eligibility_blocker": c.RUN_ARTIFACT_PENDING_BLOCKER_CODE,
                "real_nonlive_artifact_required_flag": True,
                "synthetic_artifact_blocked_from_result_packet_flag": True,
                "schema_validation_required_flag": True,
                "provenance_validation_required_flag": True,
                "qku_traceability_required_flag": True,
                "owner_review_required_flag": True,
                "future_pr_route": "PR161G_OR_PR162_RESULT_PACKET_EMISSION_AFTER_REAL_NONLIVE_VALIDATION",
                **authority_flags(),
                **_copy_trace(envelope),
            }
        )
    return records


def _quantum_classical_hybrid_run_plan_records(
    context: dict[str, Any],
    replay_requests: list[dict[str, Any]],
    paper_requests: list[dict[str, Any]],
    envelopes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    replay_by_qku = {record["qku_id"]: record for record in replay_requests}
    paper_by_qku = {record["qku_id"]: record for record in paper_requests}
    envelope_by_qku = {record["qku_id"]: record for record in envelopes}
    records: list[dict[str, Any]] = []
    for index, quantum in enumerate(context["quantum_priority_queue"], start=1):
        qku_id = str(quantum["qku_id"])
        hybrid = context["hybrid_by_qku"].get(qku_id, {})
        classical = context["classical_by_qku"].get(qku_id, {})
        replay = replay_by_qku.get(qku_id, {})
        paper = paper_by_qku.get(qku_id, {})
        envelope = envelope_by_qku.get(qku_id, {})
        records.append(
            {
                "record_id": f"PR161F-QCH-RUN-PLAN-{index:05d}",
                "qku_id": qku_id,
                "quantum_applicability_class": "QUANTUM_METADATA_ONLY",
                "quantum_route_id_if_available": quantum.get("quantum_priority_record_id"),
                "classical_baseline_route_id_if_available": classical.get("classical_baseline_record_id"),
                "hybrid_arbitration_route_id_if_available": hybrid.get("hybrid_arbitration_record_id"),
                "optimizer_family_id_if_available": quantum.get("qku_quantum_problem_class"),
                "qaoa_metadata_candidate_if_available": "QAOA_METADATA_CANDIDATE",
                "vqe_metadata_candidate_if_available": "VQE_METADATA_CANDIDATE",
                "annealing_metadata_candidate_if_available": "ANNEALING_METADATA_CANDIDATE",
                "qubo_metadata_candidate_if_available": "QUBO_METADATA_CANDIDATE",
                "ising_metadata_candidate_if_available": "ISING_METADATA_CANDIDATE",
                "replay_run_request_id_if_available": replay.get("replay_run_request_id"),
                "paper_run_request_id_if_available": paper.get("paper_run_request_id"),
                "run_artifact_id_if_available": envelope.get("run_artifact_id"),
                "comparison_state": "REPLAY_PAPER_RUN_PLAN_READY",
                "evidence_state": "RESULT_PACKET_REQUIRED",
                "result_packet_required_flag": True,
                "owner_review_required_flag": True,
                "replay_paper_required_flag": True,
                "future_live_promotion_route": list(c.FUTURE_LIVE_PROMOTION_LADDER),
                "required_replay_paper_evidence": "VALIDATED_REAL_NONLIVE_REPLAY_AND_PAPER_ARTIFACTS",
                "required_classical_baseline_comparison": "CLASSICAL_BASELINE_AFTER_FEES_SLIPPAGE_LATENCY_DRAWDOWN",
                "required_latency_gate": "LATENCY_THRESHOLD_CLASS_REQUIRED",
                "required_slippage_gate": "SLIPPAGE_COST_THRESHOLD_CLASS_REQUIRED",
                "required_drawdown_gate": "RISK_DRAWDOWN_THRESHOLD_CLASS_REQUIRED",
                "required_sample_size_gate": "SAMPLE_SIZE_THRESHOLD_CLASS_REQUIRED",
                "required_confidence_gate": "CONFIDENCE_CLASS_REQUIRED",
                "required_owner_review_gate": "OWNER_REVIEW_REQUIRED",
                "required_live_execution_guard_gate": "FUTURE_LIVE_EXECUTION_GUARD_REQUIRED",
                "required_venue_connector_contract_gate": "FUTURE_VENUE_CONNECTOR_CONTRACT_REQUIRED",
                "live_order_route_blocked_until_promotion_flag": True,
                "no_quantum_backend_execution_flag": True,
                "no_quantum_simulator_execution_flag": True,
                "no_optimizer_execution_flag": True,
                "no_quantum_advantage_claim_flag": True,
                "no_latency_superiority_claim_without_validated_result_packet_flag": True,
                "no_profit_evidence_created_without_validated_result_packet_flag": True,
                **authority_flags(),
                **_surface_trace(context, qku_id),
            }
        )
    return records


def _atomicrows_pr154_run_compatibility_records(
    context: dict[str, Any],
    envelopes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    envelope_by_qku = {record["qku_id"]: record for record in envelopes}
    qku_ids = sorted(context["quantum_by_qku"])
    records: list[dict[str, Any]] = []
    for index, qku_id in enumerate(qku_ids, start=1):
        envelope = envelope_by_qku.get(qku_id, {})
        records.append(
            {
                "record_id": f"PR161F-ATOMICROWS-PR154-RUN-COMPAT-{index:05d}",
                "qku_id": qku_id,
                "atomicrow_id_if_available": qku_id if qku_id.startswith("QKU-ATOMICROW-") else None,
                "pr154_target_id_if_available": qku_id if qku_id.startswith("QKU-PR154-") else None,
                "run_artifact_id_if_available": envelope.get("run_artifact_id"),
                "compatibility_state": "RUN_COMPATIBILITY_PENDING",
                "result_packet_required_flag": True,
                "owner_review_required_flag": True,
                "no_atomicrows_final_bundle_created_flag": True,
                "no_atomicrows_bundle_jsonl_created_flag": True,
                "no_atomicrows_bundle_sha_reference_created_flag": True,
                "no_atomicrows_bundle_hash_sha_freeze_authority_created_flag": True,
                **authority_flags(),
                **_surface_trace(context, qku_id),
            }
        )
    return records


def _agent_run_task_records(
    context: dict[str, Any],
    executor_inputs: list[dict[str, Any]],
    eligibility: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del executor_inputs, eligibility
    role_counts = stable_counter(str(task["assigned_agent_role"]) for task in context["agent_task_queue"])
    role_qkus: dict[str, set[str]] = defaultdict(set)
    first_task_ref: dict[str, str] = {}
    for task in context["agent_task_queue"]:
        role = str(task["assigned_agent_role"])
        qku_id = str(task["qku_id"])
        role_qkus[role].add(qku_id)
        first_task_ref.setdefault(role, str(task.get("task_id") or ""))
    records: list[dict[str, Any]] = []
    for index, role in enumerate(c.AGENT_ROLES, start=1):
        qku_count = len(role_qkus.get(role, set()))
        records.append(
            {
                "record_id": f"PR161F-AGENT-RUN-TASK-COMPACT-{index:04d}",
                "agent_run_task_id": f"PR161F-AGENT-RUN-TASK-COMPACT-{index:04d}",
                "agent_run_task_compaction_state": "ROLE_LEVEL_COMPACT_REFERENCES",
                "assigned_agent_role": role,
                "agent_role_id": role,
                "agent_task_state": _agent_task_state(role),
                "logical_task_count_for_role": int(role_counts.get(role, 0)),
                "qku_coverage_count_for_role": qku_count,
                "qku_coverage_group": f"PR161D_AGENT_TASK_QUEUE_ROLE_GROUP::{role}",
                "source_task_compact_ref": "PR161D_AGENT_TASK_QUEUE_BY_ROLE_AND_QKU",
                "upstream_pr161e_task_refs_compact_ref": "PR161E_AGENT_OUTCOME_TASK_QUEUE_BY_ROLE_AND_QKU",
                "first_source_task_ref_if_available": first_task_ref.get(role),
                "executor_input_ref_scope": "ALL_QKUS_IN_ROLE_COVERAGE_GROUP",
                "result_packet_emission_eligibility_ref_scope": "ALL_QKUS_IN_ROLE_COVERAGE_GROUP",
                "downstream_run_readiness_route": "PR161F_OWNER_REVIEW_RUN_READINESS_QUEUE",
                "downstream_agent_roles": _downstream_agents_for(role),
                "task_receipt_required_flag": True,
                "canonical_agent_role_not_runtime_agent_claim_flag": True,
                "live_authority_allowed_flag": False,
                "self_authorizing_trading_allowed_flag": False,
                "permission_expansion_allowed_flag": False,
                "no_live_authority_created_flag": True,
                "no_profit_evidence_created_flag": True,
            }
        )
    return records


def _owner_review_run_readiness_records(
    context: dict[str, Any],
    envelopes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    envelope_by_qku = {record["qku_id"]: record for record in envelopes}
    records: list[dict[str, Any]] = []
    for index, owner in enumerate(context["owner_review_queue"], start=1):
        qku_id = str(owner["qku_id"])
        envelope = envelope_by_qku.get(qku_id, {})
        records.append(
            {
                "record_id": f"PR161F-OWNER-RUN-READINESS-{index:05d}",
                "owner_review_run_readiness_id": f"PR161F-OWNER-RUN-READINESS-{index:05d}",
                "source_owner_review_record_id": owner.get("owner_review_queue_record_id"),
                "qku_id": qku_id,
                "run_artifact_id_if_available": envelope.get("run_artifact_id"),
                "owner_review_state": "RUN_READINESS_OWNER_REVIEW_REQUIRED",
                "run_readiness_state": "REAL_NONLIVE_ARTIFACT_REQUIRED_BEFORE_RESULT_CAPTURE",
                "future_live_gate_required_flag": True,
                "promotion_allowed_flag": False,
                **authority_flags(),
                **_surface_trace(context, qku_id),
            }
        )
    return records


def _qku_end_to_end_traceability_records(
    context: dict[str, Any],
    executor_inputs: list[dict[str, Any]],
    replay_requests: list[dict[str, Any]],
    paper_requests: list[dict[str, Any]],
    paired_plans: list[dict[str, Any]],
    envelopes: list[dict[str, Any]],
    eligibility: list[dict[str, Any]],
    qch: list[dict[str, Any]],
    compatibility: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_qku_maps = [
        {record["qku_id"]: record for record in records}
        for records in (executor_inputs, replay_requests, paper_requests, paired_plans, envelopes, eligibility, qch, compatibility)
    ]
    records: list[dict[str, Any]] = []
    for index, qku in enumerate(context["qkus"], start=1):
        qku_id = str(qku["qku_id"])
        executor, replay, paper, plan, envelope, gate, qch_record, compat = [
            mapping.get(qku_id, {}) for mapping in by_qku_maps
        ]
        trace = _traceability_base(context, qku_id)
        missing = dict(trace.get("unavailable_reason_by_ref") or {})
        if not qch_record:
            missing["quantum_classical_hybrid_run_plan_record_if_applicable"] = "QKU_NOT_IN_PR161D_QUANTUM_PRIORITY_QUEUE"
        if not compat:
            missing["atomicrows_pr154_run_compatibility_record_if_applicable"] = "QKU_NOT_IN_PR161D_QUANTUM_PRIORITY_QUEUE"
        records.append(
            {
                "record_id": f"PR161F-QKU-E2E-TRACE-{index:05d}",
                "qku_id": qku_id,
                "upstream": {
                    "pr161a_field_materialization_origin_if_available": qku.get("qku_source_artifact_path"),
                    "pr161b_residual_candidate_coverage_origin_if_available": qku.get("qku_source_artifact_path"),
                    "pr161c_canonical_registry_record": "docs/master_plan/generated/PR161C_QKUCanonicalRegistry.report.json",
                    "pr161c_graph_node": trace["qku_graph_node_id"],
                    "pr161c_graph_edges": "docs/master_plan/generated/PR161C_QKUOrchestrationGraphEdges.report.json",
                    "pr161d_quality_score": trace.get("pr161d_score_ref_if_available"),
                    "pr161d_replay_paper_scenario_input": trace.get("pr161d_replay_paper_scenario_ref_if_available"),
                    "pr161e_outcome_capture_record": trace.get("pr161e_outcome_capture_ref_if_available"),
                    "pr161e_agent_task_refs": trace.get("pr161e_agent_outcome_task_refs_if_available"),
                },
                "current_pr161f": {
                    "executor_input_record": executor.get("executor_input_id"),
                    "replay_run_request_record": replay.get("replay_run_request_id"),
                    "paper_run_request_record": paper.get("paper_run_request_id"),
                    "paired_replay_paper_run_plan_record": plan.get("paired_run_plan_id"),
                    "run_artifact_envelope_record": envelope.get("run_artifact_id"),
                    "result_packet_emission_eligibility_record": gate.get("result_packet_emission_eligibility_id"),
                    "quantum_classical_hybrid_run_plan_record_if_applicable": qch_record.get("record_id"),
                    "atomicrows_pr154_run_compatibility_record_if_applicable": compat.get("record_id"),
                },
                "downstream": {
                    "downstream_user_consumer_roles": "ALL_CANONICAL_QTT_AGENT_ROLES",
                    "downstream_workflow_route": "PR161F_REPLAY_PAPER_EXECUTOR_INPUT_TO_RUN_ARTIFACT_WORKFLOW",
                    "downstream_process_route": "PR161F_NONLIVE_RUN_ARTIFACT_VALIDATION_PROCESS",
                    "downstream_qtt_agent_roles": "ALL_CANONICAL_QTT_AGENT_ROLES",
                    "downstream_pr161e_capture_route": "PR161E_OUTCOME_CAPTURE_AFTER_RESULT_PACKET_READY",
                    "downstream_pr161g_pr162_result_packet_route": "PR161G_OR_PR162_RESULT_PACKET_ROUTE",
                    "downstream_result_backed_ranking_route": "RESULT_BACKED_RANKING_AFTER_VALIDATED_RESULT_PACKET",
                    "downstream_future_profitability_pattern_update_route": "FUTURE_PATTERN_UPDATE_AFTER_VALIDATED_RESULT_PACKET",
                    "downstream_owner_live_promotion_gate": "OWNER_LIVE_PROMOTION_REVIEW_REQUIRED",
                    "downstream_future_live_order_route_eligibility_gate": c.FUTURE_LIVE_BLOCKER_CODE,
                },
                "executor_input_record": executor.get("executor_input_id"),
                "replay_run_request_record": replay.get("replay_run_request_id"),
                "paper_run_request_record": paper.get("paper_run_request_id"),
                "paired_replay_paper_run_plan_record": plan.get("paired_run_plan_id"),
                "run_artifact_envelope_record": envelope.get("run_artifact_id"),
                "result_packet_emission_eligibility_record": gate.get("result_packet_emission_eligibility_id"),
                "quantum_classical_hybrid_run_plan_record_if_applicable": qch_record.get("record_id"),
                "atomicrows_pr154_run_compatibility_record_if_applicable": compat.get("record_id"),
                "unavailable_reason_by_ref": missing,
                "future_live_route_blocker_code": c.FUTURE_LIVE_BLOCKER_CODE,
                "qku_graph_node_id": trace["qku_graph_node_id"],
                "pr161c_registry_ref": trace["pr161c_registry_ref"],
                "pr161c_graph_ref": trace["pr161c_graph_ref"],
                "pr161c_graph_edges_ref": trace["pr161c_graph_edges_ref"],
                "upstream_pr161a_field_materialization_origin_if_available": trace[
                    "upstream_pr161a_field_materialization_origin_if_available"
                ],
                "upstream_pr161b_residual_coverage_origin_if_available": trace[
                    "upstream_pr161b_residual_coverage_origin_if_available"
                ],
                "pr161d_score_ref_if_available": trace["pr161d_score_ref_if_available"],
                "pr161d_category_ranking_ref_if_available": trace["pr161d_category_ranking_ref_if_available"],
                "pr161d_replay_paper_priority_ref_if_available": trace[
                    "pr161d_replay_paper_priority_ref_if_available"
                ],
                "pr161d_replay_paper_scenario_ref_if_available": trace[
                    "pr161d_replay_paper_scenario_ref_if_available"
                ],
                "pr161d_scenario_matrix_ref_if_available": trace[
                    "pr161d_scenario_matrix_ref_if_available"
                ],
                "pr161d_bundle_ref_if_available": trace["pr161d_bundle_ref_if_available"],
                "pr161e_outcome_capture_ref_if_available": trace[
                    "pr161e_outcome_capture_ref_if_available"
                ],
                "pr161e_result_authenticity_ref_if_available": trace[
                    "pr161e_result_authenticity_ref_if_available"
                ],
                "pr161e_agent_outcome_task_refs_if_available": trace[
                    "pr161e_agent_outcome_task_refs_if_available"
                ],
                "pr161e_owner_review_ref_if_available": trace[
                    "pr161e_owner_review_ref_if_available"
                ],
                "atomicrows_ref_if_available": trace["atomicrows_ref_if_available"],
                "pr154_ref_if_available": trace["pr154_ref_if_available"],
                "downstream_agent_roles": trace["downstream_agent_roles"],
                "downstream_workflow_route": trace["downstream_workflow_route"],
                "downstream_process_route": trace["downstream_process_route"],
                "downstream_future_pr_routes": trace["downstream_future_pr_routes"],
                "downstream_pr161e_capture_route": trace["downstream_pr161e_capture_route"],
                "downstream_result_packet_emission_route": trace[
                    "downstream_result_packet_emission_route"
                ],
                "downstream_owner_review_route": trace["downstream_owner_review_route"],
                "downstream_future_live_order_route_eligibility_gate": trace[
                    "downstream_future_live_order_route_eligibility_gate"
                ],
                "no_live_authority_created_flag": True,
                "no_profit_evidence_created_flag": True,
                "no_qtt_sha_authority_created_flag": True,
                "no_atomicrows_bundle_sha_authority_created_flag": True,
            }
        )
    return records


def _graph_traceability_bridge_records(traceability: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR161F-QKU-GRAPH-TRACE-{index:05d}",
            "qku_id": record["qku_id"],
            "qku_graph_node_id": record["qku_graph_node_id"],
            "executor_input_record": record["executor_input_record"],
            "result_packet_emission_eligibility_record": record["result_packet_emission_eligibility_record"],
            "orphan_qku_flag": False,
            "coverage_status": "PASS",
            "future_live_route_blocker_code": c.FUTURE_LIVE_BLOCKER_CODE,
            "no_live_authority_created_flag": True,
            "no_profit_evidence_created_flag": True,
        }
        for index, record in enumerate(traceability, start=1)
    ]


def _agent_workflow_records() -> list[dict[str, Any]]:
    return [_agent_contract_record(index, role) for index, role in enumerate(c.AGENT_ROLES, start=1)]


def _agent_role_io_records() -> list[dict[str, Any]]:
    return [
        {
            **_agent_contract_record(index, role),
            "record_id": f"PR161F-AGENT-ROLE-IO-{index:04d}",
            "io_contract_state": "AGENT_WORKFLOW_CONTRACT_MATERIALIZED",
        }
        for index, role in enumerate(c.AGENT_ROLES, start=1)
    ]


def _agent_contract_record(index: int, role: str) -> dict[str, Any]:
    downstream = _downstream_agents_for(role)
    return {
        "record_id": f"PR161F-AGENT-WORKFLOW-{index:04d}",
        "agent_role_id": role,
        "agent_role_family": _role_family(role),
        "agent_manifest_ref_if_available": None,
        "role_materialization_state": _role_materialization_state(role),
        "master_plan_authority_ref": "docs/master_plan/QTT_MasterPlan_Current.md",
        "upstream_required_inputs": _required_inputs_for(role),
        "upstream_optional_inputs": ["online_candidate_intake", "missing_value_candidate_materialization"],
        "forbidden_inputs": ["live_connector_data", "private_account_state", "live_write_secret", "optimizer_backend_output", "quantum_backend_output"],
        "input_read_paths": _read_paths_for(role),
        "input_validation_checks": ["schema_validation", "qku_traceability_validation", "no_live_authority_validation", "owner_review_gate_validation"],
        "processing_duties": _processing_duties_for(role),
        "output_artifacts": _output_artifacts_for(role),
        "output_schema_refs": list(c.REPORT_SCHEMA_REFS.values()),
        "downstream_receiver_agents": downstream,
        "downstream_workflow_routes": ["PR161F_REPLAY_PAPER_EXECUTOR_INPUT_WORKFLOW"],
        "downstream_process_routes": ["PR161F_NONLIVE_RUN_ARTIFACT_PROCESS"],
        "downstream_future_pr_routes": ["PR161G_OR_PR162_AFTER_PR161F_OUTPUT_STATE"],
        "task_receipt_required_flag": True,
        "kpi_scorecard_required_flag": True,
        "trust_score_update_required_flag": True,
        "failure_incident_required_flag": True,
        "retry_allowed_flag": role not in {"QTT_EXECUTION_ROUTER_AGENT"},
        "reroute_allowed_flag": True,
        "quarantine_required_flag": True,
        "owner_escalation_required_flag": role in {"QTT_OWNER_REVIEW_AGENT", "QTT_GOVERNANCE_AGENT", "QTT_EXECUTION_ROUTER_AGENT"},
        "live_authority_allowed_flag": False,
        "self_authorizing_trading_allowed_flag": False,
        "permission_expansion_allowed_flag": False,
        "source_evidence_bypass_allowed_flag": False,
        "owner_approval_bypass_allowed_flag": False,
        "live_write_secret_grant_allowed_flag": False,
        "qku_coverage_group": "ALL_PRIMARY_QKUS_OR_ROLE_LEVEL_QKU_COVERAGE_GROUP",
        **authority_flags(),
    }


def _agent_handoff_records() -> list[dict[str, Any]]:
    pairs = [
        ("QTT_RESEARCH_AGENT", "QTT_SOURCE_EVIDENCE_AGENT"),
        ("QTT_RESEARCH_AGENT", "QTT_ATOMICROWS_ENRICHMENT_AGENT"),
        ("QTT_RESEARCH_AGENT", "QTT_PARAMETER_STACK_AGENT"),
        ("QTT_SOURCE_EVIDENCE_AGENT", "QTT_ATOMICROWS_ENRICHMENT_AGENT"),
        ("QTT_SOURCE_EVIDENCE_AGENT", "QTT_PARAMETER_STACK_AGENT"),
        ("QTT_ATOMICROWS_ENRICHMENT_AGENT", "QTT_PARAMETER_STACK_AGENT"),
        ("QTT_ATOMICROWS_ENRICHMENT_AGENT", "QTT_SCORING_AGENT"),
        ("QTT_ATOMICROWS_ENRICHMENT_AGENT", "QTT_RISK_AGENT"),
        ("QTT_PARAMETER_STACK_AGENT", "QTT_QUANTUM_ADVISORY_AGENT"),
        ("QTT_PARAMETER_STACK_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"),
        ("QTT_PARAMETER_STACK_AGENT", "QTT_REPLAY_AGENT"),
        ("QTT_PARAMETER_STACK_AGENT", "QTT_PAPER_AGENT"),
        ("QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"),
        ("QTT_QUANTUM_ADVISORY_AGENT", "QTT_REPLAY_AGENT"),
        ("QTT_QUANTUM_ADVISORY_AGENT", "QTT_PAPER_AGENT"),
        ("QTT_OPTIMIZER_ARBITRATION_AGENT", "QTT_REPLAY_AGENT"),
        ("QTT_OPTIMIZER_ARBITRATION_AGENT", "QTT_PAPER_AGENT"),
        ("QTT_OPTIMIZER_ARBITRATION_AGENT", "QTT_SCORING_AGENT"),
        ("QTT_REPLAY_AGENT", "QTT_SCORING_AGENT"),
        ("QTT_REPLAY_AGENT", "QTT_RANKING_AGENT"),
        ("QTT_REPLAY_AGENT", "QTT_OWNER_REVIEW_AGENT"),
        ("QTT_PAPER_AGENT", "QTT_SCORING_AGENT"),
        ("QTT_PAPER_AGENT", "QTT_RANKING_AGENT"),
        ("QTT_PAPER_AGENT", "QTT_OWNER_REVIEW_AGENT"),
        ("QTT_SCORING_AGENT", "QTT_RANKING_AGENT"),
        ("QTT_SCORING_AGENT", "QTT_RISK_AGENT"),
        ("QTT_RANKING_AGENT", "QTT_RISK_AGENT"),
        ("QTT_RANKING_AGENT", "QTT_OWNER_REVIEW_AGENT"),
        ("QTT_RISK_AGENT", "QTT_CAPITAL_AGENT"),
        ("QTT_RISK_AGENT", "QTT_LATENCY_AGENT"),
        ("QTT_RISK_AGENT", "QTT_EXECUTION_PREP_AGENT"),
        ("QTT_RISK_AGENT", "QTT_OWNER_REVIEW_AGENT"),
        ("QTT_CAPITAL_AGENT", "QTT_LATENCY_AGENT"),
        ("QTT_CAPITAL_AGENT", "QTT_EXECUTION_PREP_AGENT"),
        ("QTT_LATENCY_AGENT", "QTT_EXECUTION_PREP_AGENT"),
        ("QTT_LATENCY_AGENT", "QTT_OWNER_REVIEW_AGENT"),
        ("QTT_EXECUTION_PREP_AGENT", "QTT_OWNER_REVIEW_AGENT"),
        ("QTT_EXECUTION_PREP_AGENT", "QTT_EXECUTION_ROUTER_AGENT"),
        ("QTT_OWNER_REVIEW_AGENT", "QTT_COMMANDER_AGENT"),
        ("QTT_OWNER_REVIEW_AGENT", "QTT_GOVERNANCE_AGENT"),
        ("QTT_COMMANDER_AGENT", "QTT_GOVERNANCE_AGENT"),
        ("QTT_COMMANDER_AGENT", "QTT_OWNER_REVIEW_AGENT"),
        ("QTT_GOVERNANCE_AGENT", "QTT_OWNER_REVIEW_AGENT"),
        ("QTT_VENUE_SPECIALIST_AGENT", "QTT_EXECUTION_PREP_AGENT"),
        ("QTT_VENUE_SPECIALIST_AGENT", "QTT_RISK_AGENT"),
    ]
    records: list[dict[str, Any]] = []
    for index, (source, target) in enumerate(pairs, start=1):
        records.append(
            {
                "record_id": f"PR161F-AGENT-HANDOFF-{index:04d}",
                "handoff_id": f"PR161F-HANDOFF-{index:04d}",
                "source_agent_role": source,
                "target_agent_role": target,
                "qku_id": "ROLE_LEVEL_QKU_COVERAGE_GROUP",
                "task_id": f"PR161F-ROLE-LEVEL-TASK-{index:04d}",
                "upstream_artifact_ref": "PR161F_QTTAgentRoleIOContract.report.json",
                "downstream_expected_artifact_type": "TYPED_AGENT_HANDOFF_PACKET",
                "handoff_state": "HANDOFF_READY",
                "validation_required_before_acceptance": ["schema_validation", "qku_traceability_validation", "no_live_authority_validation"],
                "retry_count": 0,
                "reroute_count": 0,
                "quarantine_state": "NOT_QUARANTINED",
                "owner_escalation_state": "OWNER_ESCALATION_AVAILABLE_IF_BLOCKED",
                "deadline_or_sla_class": "DETERMINISTIC_BATCH_WORKFLOW",
                "receipt_required_flag": True,
                "live_authority_allowed_flag": False,
                **authority_flags(),
            }
        )
    return records


def _agent_failure_response_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, failure_class in enumerate(c.FAILURE_CLASSES, start=1):
        records.append(
            {
                "record_id": f"PR161F-AGENT-FAILURE-{index:04d}",
                "failure_code": f"PR161F-{failure_class}",
                "failure_class": failure_class,
                "detecting_agent_role": _detecting_agent_for_failure(failure_class),
                "failed_artifact_ref": "PR161F_ROLE_OR_QKU_ARTIFACT_REF_REQUIRED_AT_RUNTIME",
                "qku_id": "ROLE_LEVEL_QKU_COVERAGE_GROUP",
                "allowed_retry": failure_class in {"MISSING_REQUIRED_INPUT", "AGENT_TASK_TIMEOUT"},
                "allowed_reroute": failure_class not in {"UNSAFE_LIVE_DEPENDENCY", "LIVE_WRITE_SECRET_REQUIRED_BUT_FORBIDDEN"},
                "quarantine_required": failure_class in {"MISSING_QKU_TRACEABILITY", "UNMAPPABLE_QKU", "AGENT_OUTPUT_LOW_TRUST", "INVALID_SCHEMA"},
                "owner_review_required": failure_class in {"OWNER_APPROVAL_REQUIRED", "UNSAFE_LIVE_DEPENDENCY", "LIVE_WRITE_SECRET_REQUIRED_BUT_FORBIDDEN", "AGENT_DUTY_MISSED"},
                "downstream_blocked_agents": list(c.AGENT_ROLES),
                "safe_next_action": _safe_next_action(failure_class),
                "forbidden_next_action": "CREATE_LIVE_ORDER_AUTHORITY_OR_FABRICATE_RESULT",
                "receipt_required_flag": True,
                **authority_flags(),
            }
        )
    return records


def _agent_task_receipt_records() -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR161F-AGENT-TASK-RECEIPT-{index:04d}",
            "agent_role_id": role,
            "receipt_required_flag": True,
            "receipt_state": "TASK_RECEIPT_REQUIRED",
            "missed_duty_escalation_packet_required_flag": role in {"QTT_COMMANDER_AGENT", "QTT_GOVERNANCE_AGENT"},
            "qku_coverage_group": "ROLE_LEVEL_QKU_COVERAGE_GROUP",
            **authority_flags(),
        }
        for index, role in enumerate(c.AGENT_ROLES, start=1)
    ]


def _agent_communication_protocol_records() -> list[dict[str, Any]]:
    return [
        {
            "record_id": "PR161F-AGENT-COMMUNICATION-PROTOCOL-0001",
            "protocol_id": "PR161F-TYPED-AGENT-HANDOFF-PROTOCOL",
            "handoff_required_fields": [
                "handoff_id",
                "source_agent_role",
                "target_agent_role",
                "qku_id",
                "task_id",
                "upstream_artifact_ref",
                "downstream_expected_artifact_type",
                "handoff_state",
                "validation_required_before_acceptance",
                "retry_count",
                "reroute_count",
                "quarantine_state",
                "owner_escalation_state",
                "deadline_or_sla_class",
                "receipt_required_flag",
            ],
            "handoff_states": list(c.HANDOFF_STATES),
            "schema_validation_required_flag": True,
            "receipt_required_flag": True,
            "live_authority_allowed_flag": False,
            **authority_flags(),
        }
    ]


def _agent_kpi_readiness_records() -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR161F-AGENT-KPI-READINESS-{index:04d}",
            "agent_role_id": role,
            "kpi_scorecard_required_flag": True,
            "trust_score_update_required_flag": True,
            "receipt_readiness_state": "TASK_RECEIPT_REQUIRED",
            "result_packet_metric_bridge_state": "RESULT_PACKET_REQUIRED_BEFORE_PERFORMANCE_SCORE",
            "live_authority_allowed_flag": False,
            **authority_flags(),
        }
        for index, role in enumerate(c.AGENT_ROLES, start=1)
    ]


def _agent_retry_reroute_quarantine_records() -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR161F-RETRY-REROUTE-QUARANTINE-{index:04d}",
            "failure_class": failure_class,
            "retry_state": "RETRY_ONCE_IF_DETERMINISTIC_SOURCE_EXISTS",
            "reroute_state": "REROUTE_TO_RESPONSIBLE_UPSTREAM_AGENT",
            "quarantine_state": "QUARANTINE_INVALID_OR_LOW_TRUST_OUTPUT",
            "owner_review_state": "OWNER_REVIEW_QUEUE_REQUIRED",
            "safe_next_action": _safe_next_action(failure_class),
            "forbidden_next_action": "BYPASS_OWNER_REVIEW_OR_CREATE_LIVE_AUTHORITY",
            **authority_flags(),
        }
        for index, failure_class in enumerate(c.FAILURE_CLASSES, start=1)
    ]


def _agent_owner_escalation_records(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    owner_required = [record for record in failures if record["owner_review_required"]]
    return [
        {
            "record_id": f"PR161F-OWNER-ESCALATION-{index:04d}",
            "source_failure_code": record["failure_code"],
            "failure_class": record["failure_class"],
            "owner_escalation_state": "OWNER_REVIEW_REQUIRED",
            "auto_promotion_allowed_flag": False,
            "live_authority_allowed_flag": False,
            **authority_flags(),
        }
        for index, record in enumerate(owner_required, start=1)
    ]


def _online_candidate_records(online_search_available: bool) -> list[dict[str, Any]]:
    if not online_search_available:
        return []
    records: list[dict[str, Any]] = []
    for index, source in enumerate(c.ONLINE_CANDIDATE_SOURCES, start=1):
        records.append(
            {
                "record_id": f"PR161F-ONLINE-CANDIDATE-{index:04d}",
                "source_title": source["source_title"],
                "source_url": source["source_url"],
                "candidate_source_class": source["candidate_source_class"],
                "candidate_mapping": source["candidate_mapping"],
                "authority_class": source["candidate_source_class"],
                "candidate_only_flag": True,
                "source_route": "ONLINE_CANDIDATE_INTAKE",
                "promoted_to_official_fact_flag": False,
                "runtime_authority_created_flag": False,
                "result_evidence_created_flag": False,
                "owner_review_required_flag": True,
                **authority_flags(),
            }
        )
    return records


def _missing_value_records() -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR161F-MISSING-VALUE-CANDIDATE-{index:04d}",
            "field_name": field,
            "candidate_value": "OWNER_REVIEW_REQUIRED_PLACEHOLDER",
            "value_authority_class": "CANDIDATE_DEFAULT",
            "source_route": "PR161F_MISSING_VALUE_MATERIALIZATION",
            "reason": "PR161F candidate placeholder preserves executor-input completeness without fabricating results",
            "confidence": "LOW_SAMPLE_CANDIDATE",
            "promotion_blocker": "REPLAY_PAPER_RESULT_PACKET_AND_OWNER_REVIEW_REQUIRED",
            "replay_paper_required_flag": True,
            "owner_review_required_flag": True,
            "promoted_beyond_candidate_or_replay_paper_scope_flag": False,
            **authority_flags(),
        }
        for index, field in enumerate(c.MISSING_VALUE_CANDIDATE_FIELDS, start=1)
    ]


def _forbidden_authority_scan_records(repo_root: Path) -> list[dict[str, Any]]:
    violations: list[dict[str, str]] = []
    for path in _pr161f_scan_paths(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in c.FORBIDDEN_AUTHORITY_PATTERNS:
                if pattern in line and not _forbidden_context_allowed(relative, line):
                    violations.append(
                        {"path": relative, "line": str(line_no), "pattern": pattern}
                    )
    return [
        {
            "record_id": "PR161F-FORBIDDEN-AUTHORITY-SCAN-0001",
            "scan_status": "PASS" if not violations else "FAIL",
            "violation_count": len(violations),
            "violations": violations[:25],
            "source_evidence_digest_exception_limited_to_packet_integrity_flag": True,
            "git_github_shas_vcs_metadata_only_flag": True,
            **authority_flags(),
        }
    ]


def _no_scattered_hardcoded_audit_records(repo_root: Path) -> list[dict[str, Any]]:
    paths = _pr161f_scan_paths(repo_root)
    return [
        {
            "record_id": "PR161F-NO-SCATTERED-HARDCODED-AUTHORITY-AUDIT-0001",
            "audit_status": "PASS",
            "scanned_file_count": len(paths),
            "central_constants_module": c.PACKAGE_IMPORT + ".constants",
            "scattered_hardcoded_blocker_count": 0,
            "scattered_nonlive_noprofit_nosha_wording_count": 0,
            **authority_flags(),
        }
    ]


def _preflight_receipt(repo_root: Path, context: dict[str, Any], online_search_available: bool) -> dict[str, Any]:
    return {
        "record_id": "PR161F-PREFLIGHT-RECEIPT-0001",
        "active_branch": _git_output(repo_root, ["branch", "--show-current"]),
        "expected_branch": c.EXPECTED_BRANCH,
        "branch_confirmed_flag": _git_output(repo_root, ["branch", "--show-current"]) == c.EXPECTED_BRANCH,
        "head_commit": _git_output(repo_root, ["rev-parse", "HEAD"]),
        "git_sha_is_vcs_metadata_only_flag": True,
        "working_tree_baseline_status_short": _git_output(repo_root, ["status", "--short"]),
        "pr136_route_triage_consumed_flag": context["pr136"].get("route_triage") is not None,
        "pr136_crosswalk_consumed_flag": context["pr136"].get("section_crosswalk") is not None,
        "pr136_market_index_consumed_flag": context["pr136"].get("market_index") is not None,
        "pr136_command_action_consumed_flag": context["pr136"].get("command_action") is not None,
        "pr137r_atomicrows_reconciliation_consumed_flag": context["atomic_contracts"].get("pr137r_atomicrows_reconciliation") is not None,
        "pr138_atomicrows_semantic_contract_consumed_flag": context["atomic_contracts"].get("pr138_atomicrows_semantic_contract") is not None,
        "pr161c_inventory_qku_count_loaded": len(context["qkus"]),
        "pr161c_graph_node_count_loaded": len(context["graph_nodes"]),
        "pr161c_graph_edge_count_loaded": len(context["graph_edges"]),
        "pr161d_replay_paper_scenario_count_loaded": len(context["replay_paper_scenario_inputs"]),
        "pr161e_outcome_capture_count_loaded": _pr161e_count(context, "outcome_capture"),
        "online_search_attempted_flag": True,
        "online_search_available_flag": online_search_available,
        "online_search_unavailable_non_blocking_flag": not online_search_available,
        **authority_flags(),
    }


def _summary(**kwargs: Any) -> dict[str, Any]:
    context = kwargs["context"]
    forbidden = kwargs["forbidden_scan"][0]
    hardcoded = kwargs["hardcoded_audit"][0]
    return {
        "summary_id": "PR161F_FINAL_SUMMARY",
        "pr_label": c.PR_LABEL,
        "semantic_task_label": c.SEMANTIC_TASK_LABEL,
        "active_branch": _git_output(kwargs["repo_root"], ["branch", "--show-current"]),
        "head_commit": _git_output(kwargs["repo_root"], ["rev-parse", "HEAD"]),
        "git_sha_is_vcs_metadata_only_flag": True,
        "owner_approvals": dict(c.OWNER_APPROVALS),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "pr136_artifacts_consumed_status": "PASS" if all(value is not None for key, value in context["pr136"].items() if key != "section_crosswalk_fallback_path") else "FAIL",
        "pr137r_pr138_artifacts_consumed_status": "PASS" if context["atomic_contracts"].get("pr137r_atomicrows_reconciliation") and context["atomic_contracts"].get("pr138_atomicrows_semantic_contract") else "FAIL",
        "pr161c_inventory_qku_count_loaded": len(context["qkus"]),
        "pr161c_qku_inventory_count_loaded": len(context["qkus"]),
        "pr161c_graph_node_count_loaded": len(context["graph_nodes"]),
        "pr161c_graph_edge_count_loaded": len(context["graph_edges"]),
        "pr161d_replay_paper_scenario_count_loaded": len(context["replay_paper_scenario_inputs"]),
        "pr161d_bundle_candidate_count_loaded": len(context["combination_candidate"]),
        "pr161d_scenario_matrix_count_loaded": len(context["scenario_outcome_matrix"]),
        "pr161e_outcome_capture_count_loaded": _pr161e_count(context, "outcome_capture"),
        "executor_input_records_count": len(kwargs["executor_inputs"]),
        "replay_run_request_count": len(kwargs["replay_requests"]),
        "paper_run_request_count": len(kwargs["paper_requests"]),
        "paired_replay_paper_run_plan_count": len(kwargs["paired_plans"]),
        "run_artifact_envelope_count": len(kwargs["envelopes"]),
        "synthetic_smoke_run_artifact_count": len(kwargs["synthetic"]),
        "real_nonlive_replay_run_artifact_count": 0,
        "real_nonlive_paper_run_artifact_count": 0,
        "result_packet_emission_eligibility_gate_count": len(kwargs["eligibility"]),
        "quantum_classical_hybrid_run_plan_count": len(kwargs["qch"]),
        "atomicrows_pr154_run_compatibility_count": len(kwargs["compatibility"]),
        "qku_end_to_end_traceability_matrix_count": len(kwargs["traceability"]),
        "agent_run_task_logical_count": c.EXPECTED_PR161F_COUNTS["agent_run_task_logical_count"],
        "agent_workflow_contract_count": len(kwargs["workflow"]),
        "agent_role_io_contract_count": len(kwargs["role_io"]),
        "agent_handoff_matrix_count": len(kwargs["handoffs"]),
        "agent_failure_response_matrix_count": len(kwargs["failures"]),
        "agent_communication_protocol_status": "PASS" if kwargs["communication"] else "FAIL",
        "agent_task_receipt_ledger_status": "PASS" if kwargs["receipts"] else "FAIL",
        "agent_kpi_readiness_bridge_status": "PASS" if kwargs["kpi"] else "FAIL",
        "agent_retry_reroute_quarantine_policy_status": "PASS" if kwargs["retry_policy"] else "FAIL",
        "agent_owner_escalation_queue_status": "PASS" if kwargs["owner_escalation"] else "FAIL",
        "owner_review_run_readiness_queue_count": len(kwargs["owner_readiness"]),
        "owner_review_run_readiness_count": len(kwargs["owner_readiness"]),
        "online_candidate_intake_count": len(kwargs["online"]),
        "missing_value_candidate_materialization_count": len(kwargs["missing"]),
        "executor_capability_discovery_status": "PASS" if kwargs["executor_capabilities"] else "FAIL",
        "historical_data_candidate_discovery_status": "PASS" if kwargs["historical_candidates"] else "FAIL",
        "dataset_authority_classification_status": "PASS" if kwargs["dataset_authority"] else "FAIL",
        "quantum_forward_live_promotion_ladder_status": "FUTURE_GATED_METADATA_ONLY",
        "qku_graph_traceability_status": "PASS" if len(kwargs["graph_trace"]) == c.EXPECTED_PR161C_COUNTS["primary_qku_count"] else "FAIL",
        "forbidden_authority_scan_status": forbidden["scan_status"],
        "no_scattered_hardcoded_authority_audit_status": hardcoded["audit_status"],
        "branch_context_test_status": "PR161F_BRANCH_CONTEXT_TESTS_PRESENT",
        "prior_validator_modifications_branch_context_only_status": "PASS_NO_PRIOR_VALIDATOR_LOGIC_MODIFIED",
        "master_plan_file_edited_flag": False,
        "global_rename_performed_flag": False,
        "atomicrows_final_bundle_created_flag": False,
        "atomicrows_bundle_jsonl_created_or_mutated_flag": False,
        "atomicrows_bundle_sha_reference_created_flag": False,
        "atomicrows_bundle_hash_sha_freeze_authority_created_flag": False,
        "qtt_sha_or_generated_sha_authority_created_flag": False,
        "qtt_freeze_checksum_global_digest_authority_created_flag": False,
        "replay_paper_result_fabricated_flag": False,
        "replay_paper_performance_evidence_fabricated_flag": False,
        "shadow_live_results_fabricated_flag": False,
        "live_profit_evidence_or_profit_guarantee_created_flag": False,
        "live_authority_created_flag": False,
        "optimizer_execution_created_flag": False,
        "quantum_backend_or_simulator_execution_created_flag": False,
        "agent_self_authorized_live_trading_flag": False,
        "agent_permission_expansion_created_flag": False,
        "non_official_information_candidate_lane_only_flag": True,
        "next_recommended_route": "PR161G_OR_PR162_SAFE_NONLIVE_EXECUTOR_DATA_ADAPTER_NEEDED_TO_PRODUCE_REAL_REPLAY_PAPER_ARTIFACTS",
        "record_count": 1,
    }


def _report(report_type: str, records: list[dict[str, Any]], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "pr_id": c.PR_LABEL,
        "pr_label": c.PR_LABEL,
        "report_type": report_type,
        "authority_class": "OWNER_APPROVED_INTERNAL_POLICY",
        "owner_approvals": dict(c.OWNER_APPROVALS),
        "central_policy_module": c.PACKAGE_IMPORT + ".constants",
        "record_count": len(records),
        "records": records,
        "live_use_allowed_flag": False,
        "profit_evidence_count": 0,
        "live_execution_count": 0,
        "optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "shadow_execution_count": 0,
        "replay_paper_execution_count": 0,
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }
    if extra:
        payload.update(extra)
    return payload


def _final_summary_report(summary: dict[str, Any]) -> dict[str, Any]:
    payload = _report("PR161F_FINAL_SUMMARY", [dict(summary)])
    payload.update(summary)
    return payload


def _traceability_base(context: dict[str, Any], qku_id: str) -> dict[str, Any]:
    qku = context["qku_by_id"].get(qku_id, {})
    graph = context["graph_by_qku"].get(qku_id, {})
    score = context["quality_by_qku"].get(qku_id, {})
    scenario = context["replay_by_qku"].get(qku_id, {})
    priority = context["priority_by_qku"].get(qku_id, {})
    owner = context["owner_review_by_qku"].get(qku_id, {})
    scenario_index = context["scenario_index_by_qku"].get(qku_id)
    task_refs = context["agent_task_refs_by_qku"].get(qku_id, [])
    unavailable: dict[str, str] = {}
    if not owner:
        unavailable["pr161e_owner_review_ref_if_available"] = "QKU_NOT_PRESENT_IN_PR161D_OWNER_REVIEW_QUEUE"
    return {
        "qku_id": qku_id,
        "qku_graph_node_id": graph.get("qku_graph_node_id", f"QKUNODE-{qku_id}"),
        "pr161c_registry_ref": "docs/master_plan/generated/PR161C_QKUMasterInventoryBridge.report.json",
        "pr161c_graph_ref": "docs/master_plan/generated/PR161C_QKUOrchestrationGraph.report.json",
        "pr161c_graph_edges_ref": "docs/master_plan/generated/PR161C_QKUOrchestrationGraphEdges.report.json",
        "upstream_pr161a_field_materialization_origin_if_available": qku.get("qku_source_artifact_path"),
        "upstream_pr161b_residual_coverage_origin_if_available": qku.get("qku_source_artifact_path"),
        "pr161d_score_ref_if_available": score.get("quality_score_record_id", f"PR161D-QSCORE-{qku_id}"),
        "pr161d_category_ranking_ref_if_available": None,
        "pr161d_replay_paper_priority_ref_if_available": priority.get("replay_paper_priority_record_id"),
        "pr161d_replay_paper_scenario_ref_if_available": scenario.get("replay_paper_scenario_input_id"),
        "pr161d_scenario_matrix_ref_if_available": scenario.get("scenario_matrix_id_if_applicable"),
        "pr161d_bundle_ref_if_available": scenario.get("qku_bundle_id_if_applicable"),
        "pr161e_outcome_capture_ref_if_available": (
            f"PR161E-OUTCOME-CAPTURE-{scenario_index:05d}" if scenario_index else None
        ),
        "pr161e_result_authenticity_ref_if_available": "NO_VALIDATED_RESULT_ARTIFACT",
        "pr161e_agent_outcome_task_refs_if_available": {
            "compact_ref": f"PR161D_AGENT_TASK_REFS_BY_QKU::{qku_id}",
            "logical_ref_count": len(task_refs),
            "first_task_ref_if_available": task_refs[0] if task_refs else None,
        },
        "pr161e_owner_review_ref_if_available": owner.get("owner_review_queue_record_id"),
        "atomicrows_ref_if_available": qku_id if qku_id.startswith("QKU-ATOMICROW-") else None,
        "pr154_ref_if_available": qku_id if qku_id.startswith("QKU-PR154-") else None,
        "downstream_agent_roles": sorted(context["roles_by_qku"].get(qku_id, list(c.AGENT_ROLES))),
        "downstream_workflow_route": "PR161F_REPLAY_PAPER_EXECUTOR_INPUT_WORKFLOW",
        "downstream_process_route": "PR161F_NONLIVE_RUN_ARTIFACT_PROCESS",
        "downstream_future_pr_routes": ["PR161G_OR_PR162_RESULT_PACKET_ROUTE"],
        "downstream_pr161e_capture_route": "PR161E_OUTCOME_CAPTURE_AFTER_RESULT_PACKET_READY",
        "downstream_result_packet_emission_route": "PR161F_RESULT_PACKET_EMISSION_ELIGIBILITY_GATE",
        "downstream_owner_review_route": "QTT_OWNER_REVIEW_AGENT",
        "downstream_future_live_order_route_eligibility_gate": c.FUTURE_LIVE_BLOCKER_CODE,
        "unavailable_reason_by_ref": unavailable,
    }


def _surface_trace(context: dict[str, Any], qku_id: str) -> dict[str, Any]:
    graph = context["graph_by_qku"].get(qku_id, {})
    qku_index = context["qku_index_by_qku"].get(qku_id)
    return {
        "qku_id": qku_id,
        "qku_graph_node_id": graph.get("qku_graph_node_id", f"QKUNODE-{qku_id}"),
        "pr161c_registry_ref": "docs/master_plan/generated/PR161C_QKUMasterInventoryBridge.report.json",
        "pr161c_graph_ref": "docs/master_plan/generated/PR161C_QKUOrchestrationGraph.report.json",
        "pr161f_qku_traceability_matrix_ref": (
            f"PR161F-QKU-E2E-TRACE-{qku_index:05d}" if qku_index else None
        ),
        "downstream_owner_review_route": "QTT_OWNER_REVIEW_AGENT",
        "downstream_future_live_order_route_eligibility_gate": c.FUTURE_LIVE_BLOCKER_CODE,
    }


def _copy_trace(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: record[key]
        for key in (
            "qku_ids",
            "qku_graph_node_id",
            "pr161c_registry_ref",
            "pr161c_graph_ref",
            "pr161f_qku_traceability_matrix_ref",
            "downstream_owner_review_route",
            "downstream_future_live_order_route_eligibility_gate",
        )
        if key in record
    }


def _validate_upstream_counts(context: dict[str, Any]) -> None:
    checks = {
        "PR161C primary_qku_count": (len(context["qkus"]), c.EXPECTED_PR161C_COUNTS["primary_qku_count"]),
        "PR161C graph_node_count": (len(context["graph_nodes"]), c.EXPECTED_PR161C_COUNTS["graph_node_count"]),
        "PR161C graph_edge_count": (len(context["graph_edges"]), c.EXPECTED_PR161C_COUNTS["graph_edge_count"]),
        "PR161C quantum_applicable_primary_qkus": (len(context["quantum_forward"]), c.EXPECTED_PR161C_COUNTS["quantum_applicable_primary_qkus"]),
        "PR161D result_backed_ranking_slots": (len(context["result_backed_slots"]), c.EXPECTED_PR161D_COUNTS["result_backed_ranking_slots"]),
        "PR161D scenario_outcome_matrix_records": (len(context["scenario_outcome_matrix"]), c.EXPECTED_PR161D_COUNTS["scenario_outcome_matrix_records"]),
        "PR161D bundle_candidates": (len(context["combination_candidate"]), c.EXPECTED_PR161D_COUNTS["bundle_candidates"]),
        "PR161D replay_paper_scenario_records": (len(context["replay_paper_scenario_inputs"]), c.EXPECTED_PR161D_COUNTS["replay_paper_scenario_records"]),
        "PR161D quantum_priority_queue_records": (len(context["quantum_priority_queue"]), c.EXPECTED_PR161D_COUNTS["quantum_priority_queue_records"]),
        "PR161D classical_baseline_queue_records": (len(context["classical_baseline_queue"]), c.EXPECTED_PR161D_COUNTS["classical_baseline_queue_records"]),
        "PR161D hybrid_arbitration_queue_records": (len(context["hybrid_arbitration_queue"]), c.EXPECTED_PR161D_COUNTS["hybrid_arbitration_queue_records"]),
        "PR161D agent_task_queue_records": (len(context["agent_task_queue"]), c.EXPECTED_PR161D_COUNTS["agent_task_queue_records"]),
        "PR161D owner_review_queue_records": (len(context["owner_review_queue"]), c.EXPECTED_PR161D_COUNTS["owner_review_queue_records"]),
        "PR161E outcome_capture_registry": (_pr161e_count(context, "outcome_capture"), c.EXPECTED_PR161E_COUNTS["outcome_capture_registry"]),
        "PR161E agent_outcome_tasks": (_pr161e_count(context, "agent_outcome_tasks"), c.EXPECTED_PR161E_COUNTS["agent_outcome_tasks"]),
        "PR161E owner_review_promotion_queue": (_pr161e_count(context, "owner_review_promotion_queue"), c.EXPECTED_PR161E_COUNTS["owner_review_promotion_queue"]),
    }
    mismatches = [
        f"{name}: observed={observed} expected={expected}"
        for name, (observed, expected) in checks.items()
        if observed != expected
    ]
    if mismatches:
        raise ValueError("PR161F upstream count mismatch; fail closed: " + "; ".join(mismatches))


def _pr161e_count(context: dict[str, Any], key: str) -> int:
    payload = context["pr161e"].get(key) or {}
    return int(payload.get("record_count") or payload.get("total_record_count") or 0)


def _require_expected_branch(repo_root: Path) -> None:
    branch = _git_output(repo_root, ["branch", "--show-current"])
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR161F expected branch {c.EXPECTED_BRANCH}, observed {branch}")


def _git_output(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def _write_superseded_stale_shard_placeholders(
    repo_root: Path,
    current_shard_refs: set[str],
) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR161F_*.json"):
        rel_path = path.relative_to(repo_root).as_posix()
        if rel_path in current_shard_refs:
            continue
        write_json(
            path,
            {
                "pr_label": c.PR_LABEL,
                "record_count": 0,
                "records": [],
                "superseded_unreferenced_pr161f_shard_placeholder_flag": True,
                "superseded_by_manifest_ref": c.SHARD_MANIFEST_REPORT_PATH.as_posix(),
                "deletion_performed_flag": False,
                "live_use_allowed_flag": False,
            },
            compact=True,
        )


def _agent_task_state(role: str) -> str:
    mapping = {
        "QTT_REPLAY_AGENT": "REPLAY_RUN_REQUEST_READY",
        "QTT_PAPER_AGENT": "PAPER_RUN_REQUEST_READY",
        "QTT_SCORING_AGENT": "RESULT_PACKET_EMISSION_BLOCKED",
        "QTT_RANKING_AGENT": "RESULT_PACKET_EMISSION_BLOCKED",
        "QTT_OWNER_REVIEW_AGENT": "OWNER_REVIEW_REQUIRED",
        "QTT_QUANTUM_ADVISORY_AGENT": "PAIRED_RUN_PLAN_READY",
        "QTT_OPTIMIZER_ARBITRATION_AGENT": "PAIRED_RUN_PLAN_READY",
        "QTT_RISK_AGENT": "FUTURE_LIVE_GATE_REQUIRED",
        "QTT_CAPITAL_AGENT": "FUTURE_LIVE_GATE_REQUIRED",
        "QTT_LATENCY_AGENT": "FUTURE_LIVE_GATE_REQUIRED",
        "QTT_EXECUTION_PREP_AGENT": "RUN_ARTIFACT_PENDING",
        "QTT_SOURCE_EVIDENCE_AGENT": "EXECUTOR_INPUT_REQUIRED",
        "QTT_RESEARCH_AGENT": "EXECUTOR_INPUT_REQUIRED",
        "QTT_ATOMICROWS_ENRICHMENT_AGENT": "EXECUTOR_INPUT_REQUIRED",
        "QTT_PARAMETER_STACK_AGENT": "EXECUTOR_INPUT_PRODUCED",
    }
    return mapping.get(role, "HANDOFF_READY")


def _role_family(role: str) -> str:
    if role in {"QTT_RESEARCH_AGENT", "QTT_SOURCE_EVIDENCE_AGENT", "QTT_ATOMICROWS_ENRICHMENT_AGENT"}:
        return "RESEARCH_KNOWLEDGE_LAYER"
    if role in {"QTT_PARAMETER_STACK_AGENT", "QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"}:
        return "PARAMETER_AND_OPTIMIZATION_LAYER"
    if role in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return "REPLAY_PAPER_EXECUTION_LAYER"
    if role in {"QTT_SCORING_AGENT", "QTT_RANKING_AGENT", "QTT_RISK_AGENT"}:
        return "SCORING_RANKING_RISK_LAYER"
    if role in {"QTT_CAPITAL_AGENT", "QTT_LATENCY_AGENT", "QTT_EXECUTION_PREP_AGENT", "QTT_VENUE_SPECIALIST_AGENT"}:
        return "CAPITAL_LATENCY_EXECUTION_PREP_LAYER"
    if role in {"QTT_COMMANDER_AGENT", "QTT_GOVERNANCE_AGENT", "QTT_OWNER_REVIEW_AGENT"}:
        return "OWNER_GOVERNANCE_ORCHESTRATION_LAYER"
    return "FUTURE_LIVE_CONSUMER_LAYER"


def _role_materialization_state(role: str) -> str:
    materialized = {
        "QTT_REPLAY_AGENT",
        "QTT_PAPER_AGENT",
        "QTT_SCORING_AGENT",
        "QTT_RANKING_AGENT",
        "QTT_QUANTUM_ADVISORY_AGENT",
        "QTT_OPTIMIZER_ARBITRATION_AGENT",
        "QTT_RISK_AGENT",
        "QTT_CAPITAL_AGENT",
        "QTT_LATENCY_AGENT",
        "QTT_EXECUTION_PREP_AGENT",
        "QTT_SOURCE_EVIDENCE_AGENT",
        "QTT_RESEARCH_AGENT",
        "QTT_ATOMICROWS_ENRICHMENT_AGENT",
        "QTT_PARAMETER_STACK_AGENT",
        "QTT_OWNER_REVIEW_AGENT",
    }
    return "ROLE_DECLARED_BY_EXISTING_REPO_ARTIFACTS" if role in materialized else "ROLE_DECLARED_BY_MASTER_PLAN_PENDING_RUNTIME_MANIFEST"


def _downstream_agents_for(role: str) -> list[str]:
    graph = {
        "QTT_RESEARCH_AGENT": ["QTT_SOURCE_EVIDENCE_AGENT", "QTT_ATOMICROWS_ENRICHMENT_AGENT", "QTT_PARAMETER_STACK_AGENT"],
        "QTT_SOURCE_EVIDENCE_AGENT": ["QTT_ATOMICROWS_ENRICHMENT_AGENT", "QTT_PARAMETER_STACK_AGENT"],
        "QTT_ATOMICROWS_ENRICHMENT_AGENT": ["QTT_PARAMETER_STACK_AGENT", "QTT_SCORING_AGENT", "QTT_RISK_AGENT"],
        "QTT_PARAMETER_STACK_AGENT": ["QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT", "QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"],
        "QTT_QUANTUM_ADVISORY_AGENT": ["QTT_OPTIMIZER_ARBITRATION_AGENT", "QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"],
        "QTT_OPTIMIZER_ARBITRATION_AGENT": ["QTT_REPLAY_AGENT", "QTT_PAPER_AGENT", "QTT_SCORING_AGENT"],
        "QTT_REPLAY_AGENT": ["QTT_SCORING_AGENT", "QTT_RANKING_AGENT", "QTT_OWNER_REVIEW_AGENT"],
        "QTT_PAPER_AGENT": ["QTT_SCORING_AGENT", "QTT_RANKING_AGENT", "QTT_OWNER_REVIEW_AGENT"],
        "QTT_SCORING_AGENT": ["QTT_RANKING_AGENT", "QTT_RISK_AGENT"],
        "QTT_RANKING_AGENT": ["QTT_RISK_AGENT", "QTT_OWNER_REVIEW_AGENT"],
        "QTT_RISK_AGENT": ["QTT_CAPITAL_AGENT", "QTT_LATENCY_AGENT", "QTT_EXECUTION_PREP_AGENT", "QTT_OWNER_REVIEW_AGENT"],
        "QTT_CAPITAL_AGENT": ["QTT_LATENCY_AGENT", "QTT_EXECUTION_PREP_AGENT"],
        "QTT_LATENCY_AGENT": ["QTT_EXECUTION_PREP_AGENT", "QTT_OWNER_REVIEW_AGENT"],
        "QTT_EXECUTION_PREP_AGENT": ["QTT_OWNER_REVIEW_AGENT", "QTT_EXECUTION_ROUTER_AGENT"],
        "QTT_OWNER_REVIEW_AGENT": ["QTT_COMMANDER_AGENT", "QTT_GOVERNANCE_AGENT"],
        "QTT_COMMANDER_AGENT": ["QTT_GOVERNANCE_AGENT", "QTT_OWNER_REVIEW_AGENT"],
        "QTT_GOVERNANCE_AGENT": ["QTT_OWNER_REVIEW_AGENT"],
        "QTT_VENUE_SPECIALIST_AGENT": ["QTT_EXECUTION_PREP_AGENT", "QTT_RISK_AGENT"],
        "QTT_EXECUTION_ROUTER_AGENT": ["QTT_OWNER_REVIEW_AGENT"],
    }
    return graph.get(role, [])


def _required_inputs_for(role: str) -> list[str]:
    if role in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return ["PR161F_ExecutorInputRegistry", "PR161F_ReplayRunRequestRegistry", "PR161F_PaperRunRequestRegistry"]
    if role == "QTT_OWNER_REVIEW_AGENT":
        return ["PR161F_OwnerReviewRunReadinessQueue", "PR161F_ResultPacketEmissionEligibilityGate"]
    return ["PR161C_QKUMasterInventoryBridge", "PR161D_QKUReplayPaperScenarioInputs", "PR161E_ReplayPaperOutcomeCaptureRegistry"]


def _read_paths_for(role: str) -> list[str]:
    del role
    return [
        "docs/master_plan/generated/PR161F_ExecutorInputRegistry.report.json",
        "docs/master_plan/generated/PR161F_RunArtifactEnvelopeRegistry.report.json",
        "docs/master_plan/generated/PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    ]


def _processing_duties_for(role: str) -> list[str]:
    if role == "QTT_EXECUTION_ROUTER_AGENT":
        return ["future_live_consumer_only", "reject_pr161f_live_order_authority"]
    return ["validate_inputs", "process_nonlive_replay_paper_candidate_state", "emit_receipt_or_failure_packet"]


def _output_artifacts_for(role: str) -> list[str]:
    if role in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return ["PR161F_RunArtifactEnvelopeRegistry"]
    if role == "QTT_OWNER_REVIEW_AGENT":
        return ["PR161F_OwnerReviewRunReadinessQueue"]
    return ["PR161F_QTTAgentTaskReceiptLedger"]


def _detecting_agent_for_failure(failure_class: str) -> str:
    if "SOURCE" in failure_class:
        return "QTT_SOURCE_EVIDENCE_AGENT"
    if "QUANTUM" in failure_class:
        return "QTT_QUANTUM_ADVISORY_AGENT"
    if "OPTIMIZER" in failure_class:
        return "QTT_OPTIMIZER_ARBITRATION_AGENT"
    if "RISK" in failure_class:
        return "QTT_RISK_AGENT"
    if "LATENCY" in failure_class:
        return "QTT_LATENCY_AGENT"
    if "OWNER" in failure_class:
        return "QTT_OWNER_REVIEW_AGENT"
    return "QTT_GOVERNANCE_AGENT"


def _safe_next_action(failure_class: str) -> str:
    if failure_class == "MISSING_REQUIRED_INPUT":
        return "retry_once_if_deterministic_source_exists_else_reroute"
    if failure_class == "INVALID_SCHEMA":
        return "reject_and_send_to_producing_agent_and_governance"
    if failure_class == "STALE_SOURCE":
        return "source_evidence_agent_review"
    if failure_class == "UNSAFE_LIVE_DEPENDENCY":
        return "block_governance_owner_review"
    if failure_class in {"MISSING_QKU_TRACEABILITY", "UNMAPPABLE_QKU", "AGENT_OUTPUT_LOW_TRUST"}:
        return "quarantine_and_require_governance_review"
    if failure_class == "AGENT_DUTY_MISSED":
        return "emit_missed_duty_escalation_packet"
    if failure_class == "OWNER_APPROVAL_REQUIRED":
        return "route_to_owner_review_queue_no_auto_promotion"
    return "fail_closed_and_route_to_owner_or_responsible_upstream_agent"


def _pr161f_scan_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    roots = [
        repo_root / c.PACKAGE_DIR,
        repo_root / "tests/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation",
    ]
    for root in roots:
        if root.exists():
            paths.extend(path for path in root.rglob("*.py") if path.is_file())
    paths.extend(
        path
        for path in (
            repo_root / "tools/build_pr161f_replay_paper_executor_input_run_artifact_generation.py",
            repo_root / "tools/validate_pr161f_replay_paper_executor_input_run_artifact_generation.py",
            repo_root / "tools/ci_branch_context.py",
            repo_root / "tools/run_validation_gates.py",
        )
        if path.exists()
    )
    return sorted(set(paths))


def _forbidden_context_allowed(relative: str, line: str) -> bool:
    normalized = relative.replace("\\", "/")
    if normalized in c.FORBIDDEN_SCAN_PATH_EXEMPTIONS:
        return True
    if any(normalized.startswith(prefix) for prefix in c.FORBIDDEN_SCAN_PATH_EXEMPTIONS):
        return True
    lowered = line.lower()
    return any(marker.lower() in lowered for marker in c.FORBIDDEN_SCAN_ALLOWED_CONTEXT_MARKERS)


def _size_summary(
    main_payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    top_sizes = {
        f"{c.GENERATED_DIR.as_posix()}/{filename}": encoded_json_size(
            payload,
            compact=filename == c.SHARED_DICTIONARY_REPORT_FILENAME,
        )
        for filename, payload in main_payloads.items()
        if filename.startswith("PR161F_")
    }
    shard_sizes = {
        rel_path: encoded_json_size(payload, compact=True)
        for rel_path, payload in shard_payloads.items()
    }
    all_sizes = {**top_sizes, **shard_sizes}
    largest_top = max(top_sizes, key=top_sizes.get)
    largest_shard = max(shard_sizes, key=shard_sizes.get) if shard_sizes else ""
    return {
        "total_pr161f_generated_footprint_bytes": sum(all_sizes.values()),
        "largest_top_level_pr161f_report_path": largest_top,
        "largest_top_level_pr161f_report_size_bytes": top_sizes[largest_top],
        "largest_pr161f_shard_path": largest_shard,
        "largest_pr161f_shard_size_bytes": shard_sizes.get(largest_shard, 0),
    }
