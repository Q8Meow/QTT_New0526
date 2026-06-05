"""Build PR162R generic replay/paper adapter rerun artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .agent_handoff import build_agent_handoff_rows
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    POLICY_MODULE_REF,
    boundary_payload,
    no_authority_record,
)
from .candidate_packet_loader import (
    build_ingestion_ledger,
    build_old_548_compatibility_rows,
    build_schema_compatibility_rows,
    load_candidate_universe,
)
from .data_binding import binding_by_packet, build_data_binding_rows
from .downstream_handoff import (
    build_pr162e_plugin_seed,
    build_pr163_handoff_seed,
    build_pr164_handoff_seed,
    build_pr165_handoff_seed,
)
from .fill_action_queue import build_missing_binding_actions
from .formulation_callable_resolver import build_callable_import_rows
from .input_discovery import discover_inputs, discovery_records
from .json_io import stable_counter, write_json
from .latency_precompute_router import build_latency_precompute_rows, latency_by_packet
from .orphan_audit import build_orphan_audit_record
from .paper_input_builder import build_paper_adapter_inputs
from .qku_computability import build_qku_computability_rows
from .quantum_batch_planner import build_quantum_batch_plan
from .replay_input_builder import build_replay_adapter_inputs
from .route_crosswalk_consumption import (
    build_command_action_binding_rows,
    build_market_specific_index_rows,
    build_route_consumption_audit,
)
from .run_request_queue import build_paired_run_plan, build_paper_run_requests, build_replay_run_requests
from .schema_writer import write_schemas
from .smoke_execution import build_smoke_execution_rows, smoke_status_by_formulation
from .source_candidate_materializer import build_online_scout_rows, build_source_materialization_rows


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads = build_payloads(repo_root, p.EXPECTED_BRANCH)
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename])
    return BuildArtifacts(summary=payloads["PR162R_FinalSummary.report.json"], payloads=payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    branch = branch or p.current_branch(repo_root)
    discovery = discovery_records(discover_inputs(repo_root))
    source_inputs = [row["consumed_path"] for row in discovery if row["consumed_path"]]
    universe = load_candidate_universe(repo_root)

    ingestion = build_ingestion_ledger(universe)
    schema_compat = build_schema_compatibility_rows(universe)
    qku_computability = build_qku_computability_rows(universe.packets, universe.formulations)
    computability_by_packet = {row["candidate_packet_ref"]: row for row in qku_computability}
    callable_imports = build_callable_import_rows(universe.formulations, universe.comparators)
    smoke = build_smoke_execution_rows(universe.formulations, universe.test_vectors, universe.comparators)
    smoke_by_formulation = smoke_status_by_formulation(smoke)
    missing_actions = build_missing_binding_actions(universe.packets)
    source_materialization = build_source_materialization_rows(universe.packets)
    online_scout = build_online_scout_rows(missing_actions)
    data_binding = build_data_binding_rows(universe.packets, missing_actions)
    binding_index = binding_by_packet(data_binding)
    latency = build_latency_precompute_rows(universe.packets)
    latency_index = latency_by_packet(latency)
    replay_inputs = build_replay_adapter_inputs(
        universe.packets,
        computability_by_packet,
        binding_index,
        smoke_by_formulation,
        latency_index,
    )
    paper_inputs = build_paper_adapter_inputs(
        universe.packets,
        computability_by_packet,
        binding_index,
        smoke_by_formulation,
        latency_index,
    )
    replay_requests = build_replay_run_requests(replay_inputs)
    paper_requests = build_paper_run_requests(paper_inputs)
    paired_plan = build_paired_run_plan(replay_requests, paper_requests)
    quantum_plan = build_quantum_batch_plan(
        universe.packets,
        universe.formulations,
        smoke_by_formulation,
        binding_index,
    )
    route_consumption = build_route_consumption_audit(discovery)
    market_index = build_market_specific_index_rows(universe.packets)
    command_action = build_command_action_binding_rows(universe.packets)
    handoff = build_agent_handoff_rows(universe.packets, replay_inputs, paper_inputs)
    pr163 = build_pr163_handoff_seed(paired_plan)
    pr164 = build_pr164_handoff_seed(paired_plan)
    pr165 = build_pr165_handoff_seed(paired_plan)
    pr162e = build_pr162e_plugin_seed(universe.plugin_seed, universe.packets)
    old548 = build_old_548_compatibility_rows(universe)
    non_placeholder = _non_placeholder_audit(universe.packets, qku_computability)

    payloads: dict[str, dict[str, Any]] = {}
    row_payloads = {
        "PR162R_InputConsumptionAudit.report.json": discovery,
        "PR162R_CandidatePacketV1IngestionLedger.report.json": ingestion,
        "PR162R_CandidatePacketSchemaCompatibilityAudit.report.json": schema_compat,
        "PR162R_QKUComputabilityClassificationMatrix.report.json": qku_computability,
        "PR162R_QKUNonPlaceholderCompletionAudit.report.json": [non_placeholder],
        "PR162R_FormulationCallableImportAudit.report.json": callable_imports,
        "PR162R_FormulationSmokeExecutionLedger.report.json": smoke,
        "PR162R_SourceCandidateMaterializationQueue.report.json": source_materialization,
        "PR162R_OnlineSourceScoutQueue.report.json": online_scout,
        "PR162R_ReplayPaperDataBindingRequirementMatrix.report.json": data_binding,
        "PR162R_MissingDataBindingActionQueue.report.json": missing_actions,
        "PR162R_ReplayAdapterInputPacketRegistry.report.json": replay_inputs,
        "PR162R_PaperAdapterInputPacketRegistry.report.json": paper_inputs,
        "PR162R_ReplayRunRequestCandidateQueue.report.json": replay_requests,
        "PR162R_PaperRunRequestCandidateQueue.report.json": paper_requests,
        "PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json": paired_plan,
        "PR162R_QuantumBatchPrecomputeRoutingPlan.report.json": quantum_plan,
        "PR162R_LatencyPrecomputeRoutingMatrix.report.json": latency,
        "PR162R_RouteTriageCrosswalkConsumptionAudit.report.json": route_consumption,
        "PR162R_MarketSpecificQKUAdapterIndex.report.json": market_index,
        "PR162R_CommandActionQKUBindingMatrix.report.json": command_action,
        "PR162R_QKUAgentReplayPaperHandoffMatrix.report.json": handoff,
        "PR162R_PR163PaperAdapterHandoffSeed.report.json": pr163,
        "PR162R_PR164ReviewProvenanceHandoffSeed.report.json": pr164,
        "PR162R_PR165ScoringRankingHandoffSeed.report.json": pr165,
        "PR162R_PR162EPluginReplayPaperCompatibilitySeed.report.json": pr162e,
        "PR162R_NoReplayPaperResultPacketAudit.report.json": [no_authority_record("PR162R_NO_REPLAY_PAPER_RESULT_PACKET_AUDIT", "NO_REPLAY_PAPER_RESULT_PACKET")],
        "PR162R_NoLiveOrderProfitAuthorityAudit.report.json": [no_authority_record("PR162R_NO_LIVE_ORDER_PROFIT_AUTHORITY_AUDIT", "NO_LIVE_ORDER_PROFIT_AUTHORITY")],
        "PR162R_NoSourceAcceptanceConnectorPrivateStateAudit.report.json": [no_authority_record("PR162R_NO_SOURCE_ACCEPTANCE_CONNECTOR_PRIVATE_STATE_AUDIT", "NO_SOURCE_ACCEPTANCE_CONNECTOR_PRIVATE_STATE")],
        "PR162R_NoQuantumBackendAdvantageClaimAudit.report.json": [no_authority_record("PR162R_NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM_AUDIT", "NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM")],
        "PR162R_NoQTTChecksumFreezeAuthorityAudit.report.json": [no_authority_record("PR162R_NO_QTT_CHECKSUM_FREEZE_AUTHORITY_AUDIT", "NO_QTT_CHECKSUM_FREEZE_AUTHORITY")],
        "PR162R_Old548CompatibilityTrace.report.json": old548,
    }
    for filename, records in row_payloads.items():
        payloads[filename] = _payload(_report_id(filename), filename, records, source_inputs)

    orphan_record = build_orphan_audit_record(
        packets=universe.packets,
        reports=payloads,
        qku_rows=qku_computability,
        handoff_rows=handoff,
    )
    payloads["PR162R_OrphanCandidateReportAudit.report.json"] = _payload(
        "PR162R_ORPHAN_CANDIDATE_REPORT_AUDIT",
        "PR162R_OrphanCandidateReportAudit.report.json",
        [orphan_record],
        source_inputs,
    )

    summary = _summary(
        branch=branch,
        discovery=discovery,
        universe=universe,
        qku_computability=qku_computability,
        callable_imports=callable_imports,
        smoke=smoke,
        source_materialization=source_materialization,
        online_scout=online_scout,
        data_binding=data_binding,
        missing_actions=missing_actions,
        replay_inputs=replay_inputs,
        paper_inputs=paper_inputs,
        replay_requests=replay_requests,
        paper_requests=paper_requests,
        paired_plan=paired_plan,
        quantum_plan=quantum_plan,
        latency=latency,
        route_consumption=route_consumption,
        market_index=market_index,
        command_action=command_action,
        handoff=handoff,
        pr163=pr163,
        pr164=pr164,
        pr165=pr165,
        pr162e=pr162e,
        old548=old548,
        orphan_record=orphan_record,
    )
    decision = _decision(summary)
    manifest = _manifest(payloads, summary, decision)
    payloads["PR162R_FinalSummary.report.json"] = _payload(
        "PR162R_FINAL_SUMMARY",
        "PR162R_FinalSummary.report.json",
        [summary],
        source_inputs,
        summary,
    )
    payloads["PR162R_DecisionAndNextPRRecommendation.report.json"] = _payload(
        "PR162R_DECISION_AND_NEXT_PR_RECOMMENDATION",
        "PR162R_DecisionAndNextPRRecommendation.report.json",
        [decision],
        source_inputs,
        decision,
    )
    payloads["PR162R_ReportManifest.report.json"] = _payload(
        "PR162R_REPORT_MANIFEST",
        "PR162R_ReportManifest.report.json",
        manifest,
        source_inputs,
        {"manifest_report_count": len(manifest)},
    )
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR162R payload map missing reports: {missing}")
    return payloads


def _payload(
    report_id: str,
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "report_id": report_id,
        "report_filename": filename,
        "created_by_pr": "PR162R",
        "authority_class": AUTHORITY_CLASS,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
        "validation_status": "PASS",
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(p.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(p.DOWNSTREAM_PR_ROUTES),
        "record_count": len(records),
        "records": records,
        **NO_AUTHORITY_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def _summary(
    *,
    branch: str,
    discovery: list[dict[str, Any]],
    universe: Any,
    qku_computability: list[dict[str, Any]],
    callable_imports: list[dict[str, Any]],
    smoke: list[dict[str, Any]],
    source_materialization: list[dict[str, Any]],
    online_scout: list[dict[str, Any]],
    data_binding: list[dict[str, Any]],
    missing_actions: list[dict[str, Any]],
    replay_inputs: list[dict[str, Any]],
    paper_inputs: list[dict[str, Any]],
    replay_requests: list[dict[str, Any]],
    paper_requests: list[dict[str, Any]],
    paired_plan: list[dict[str, Any]],
    quantum_plan: list[dict[str, Any]],
    latency: list[dict[str, Any]],
    route_consumption: list[dict[str, Any]],
    market_index: list[dict[str, Any]],
    command_action: list[dict[str, Any]],
    handoff: list[dict[str, Any]],
    pr163: list[dict[str, Any]],
    pr164: list[dict[str, Any]],
    pr165: list[dict[str, Any]],
    pr162e: list[dict[str, Any]],
    old548: list[dict[str, Any]],
    orphan_record: dict[str, Any],
) -> dict[str, Any]:
    replay_counts = stable_counter(row["replay_adapter_status"] for row in replay_inputs)
    paper_counts = stable_counter(row["paper_adapter_status"] for row in paper_inputs)
    paired_counts = stable_counter(row["paired_status"] for row in replay_inputs)
    smoke_passed = [row for row in smoke if row.get("smoke_execution_status") == "SMOKE_EXECUTION_PASSED"]
    summary = {
        "active_branch": branch,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "input_consumption_rows_count": len(discovery),
        "candidate_packet_v1_ingested_count": len(universe.packets),
        "pr162d_r2a_candidate_packet_ingested_count": len(universe.packets),
        "pr162d_r2a_generic_candidate_extension_count": len(universe.generic_extension),
        "old_548_backward_compatibility_preserved": len(old548) == 548 and all(row["old_548_backward_compatibility_preserved"] for row in old548),
        "old_548_compatibility_trace_count": len(old548),
        "qku_computability_classification_rows_count": len(qku_computability),
        "metadata_only_ready_count": 0,
        "formulation_callable_registry_refs_loaded_count": len(callable_imports),
        "formula_callable_smoke_checked_count": _smoke_count(smoke_passed, "FORMULA::"),
        "algorithm_callable_smoke_checked_count": _smoke_count(smoke_passed, "ALGORITHM::"),
        "quantum_shape_builder_smoke_checked_count": _smoke_count(smoke_passed, "QUANTUM::"),
        "classical_comparator_smoke_checked_count": sum(1 for row in smoke_passed if row.get("callable_family") == "CLASSICAL_COMPARATOR"),
        "replay_adapter_input_packet_count": len(replay_inputs),
        "paper_adapter_input_packet_count": len(paper_inputs),
        "replay_run_request_candidate_count": len(replay_requests),
        "paper_run_request_candidate_count": len(paper_requests),
        "paired_replay_paper_run_request_candidate_count": len(paired_plan),
        "replay_input_ready_count": replay_counts.get("REPLAY_INPUT_READY", 0),
        "replay_input_partial_count": replay_counts.get("REPLAY_INPUT_PARTIAL", 0),
        "replay_input_fill_required_count": replay_counts.get("REPLAY_INPUT_FILL_REQUIRED", 0),
        "replay_input_owner_review_count": replay_counts.get("REPLAY_OWNER_REVIEW_REQUIRED", 0),
        "replay_input_not_stage1_count": replay_counts.get("REPLAY_NOT_STAGE1_RELEVANT_WITH_REASON", 0),
        "paper_input_ready_count": paper_counts.get("PAPER_INPUT_READY", 0),
        "paper_input_partial_count": paper_counts.get("PAPER_INPUT_PARTIAL", 0),
        "paper_input_fill_required_count": paper_counts.get("PAPER_INPUT_FILL_REQUIRED", 0),
        "paper_input_owner_review_count": paper_counts.get("PAPER_OWNER_REVIEW_REQUIRED", 0),
        "paper_input_not_stage1_count": paper_counts.get("PAPER_NOT_STAGE1_RELEVANT_WITH_REASON", 0),
        "paired_ready_count": paired_counts.get("PAIRED_REPLAY_PAPER_INPUT_READY", 0),
        "paired_partial_count": paired_counts.get("PAIRED_PARTIAL", 0),
        "paired_fill_required_count": paired_counts.get("PAIRED_FILL_REQUIRED", 0),
        "paired_owner_review_count": paired_counts.get("OWNER_REVIEW_REQUIRED", 0),
        "paired_not_stage1_count": paired_counts.get("NOT_STAGE1_RELEVANT_WITH_REASON", 0),
        "data_binding_requirement_rows_count": len(data_binding),
        "missing_data_binding_action_count": len(missing_actions),
        "missing_data_binding_action_queue_created": bool(missing_actions),
        "source_candidate_materialization_row_count": len(source_materialization),
        "source_candidate_materialization_queue_created": bool(source_materialization),
        "online_source_scout_queue_row_count": len(online_scout),
        "online_source_scout_queue_created_if_missing_values_exist": bool(online_scout) if missing_actions else True,
        "quantum_batch_precompute_rows_count": len(quantum_plan),
        "quantum_batch_precompute_plan_created": bool(quantum_plan),
        "latency_precompute_rows_count": len(latency),
        "latency_precompute_routing_matrix_created": bool(latency),
        "route_triage_crosswalk_consumption_audit_created": bool(route_consumption),
        "market_specific_qku_adapter_index_created": bool(market_index),
        "command_action_qku_binding_matrix_created": bool(command_action),
        "qku_agent_replay_paper_handoff_rows_count": len(handoff),
        "pr163_handoff_seed_count": len(pr163),
        "pr164_handoff_seed_count": len(pr164),
        "pr165_handoff_seed_count": len(pr165),
        "pr162e_compatibility_seed_count": len(pr162e),
        "orphan_candidate_count": orphan_record["orphan_candidate_count"],
        "orphan_generated_report_count": orphan_record["orphan_generated_report_count"],
        "orphan_qku_count": orphan_record["orphan_qku_count"],
        "orphan_handoff_count": orphan_record["orphan_handoff_count"],
        "route_crosswalk_market_command_consumption_status": "CONSUMED_WITH_EXACT_FALLBACK_LINEAGE_FOR_MISSING_CROSSWALK",
        "files_intentionally_not_touched": [
            "docs/master_plan/QTT_MasterPlan_Current.md",
            "protected AtomicRows bundle/checksum artifacts",
        ],
        "recommendation_next_step": "PR162R-B replay/paper data binding completion",
        **BOUNDARY_COUNT_FIELDS,
        "live_order_authority": False,
        "validation_status": "PASS",
    }
    return summary


def _decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": "PR162R_DECISION",
        "decision": "GENERIC_ADAPTER_INPUT_ARTIFACTS_CREATED_WITH_DATA_BINDING_FILL_REQUIRED",
        "can_generic_adapter_infrastructure_consume_pr162d_r2a_candidate_packets": True,
        "evidence": {
            "candidate_packet_v1_ingested_count": summary["candidate_packet_v1_ingested_count"],
            "replay_adapter_input_packet_count": summary["replay_adapter_input_packet_count"],
            "paper_adapter_input_packet_count": summary["paper_adapter_input_packet_count"],
            "callable_smoke_checks_exist": summary["formula_callable_smoke_checked_count"] > 0
            and summary["algorithm_callable_smoke_checked_count"] > 0
            and summary["quantum_shape_builder_smoke_checked_count"] > 0
            and summary["classical_comparator_smoke_checked_count"] > 0,
            "data_binding_fill_actions_exist": summary["missing_data_binding_action_count"] > 0,
        },
        "next_recommended_pr": summary["recommendation_next_step"],
        "alternate_next_prs": [
            "PR163 generic paper adapter / paper capture framework",
            "PR162E formula/algorithm/quantum plugin intake",
            "PR162D-R2 materialization expansion",
            "PR162Q quantum formulation expansion",
        ],
        "no_replay_or_paper_execution_performed": True,
        "live_order_authority": False,
        "validation_status": "PASS",
        **BOUNDARY_COUNT_FIELDS,
    }


def _manifest(
    payloads: dict[str, dict[str, Any]],
    summary: dict[str, Any],
    decision: dict[str, Any],
) -> list[dict[str, Any]]:
    all_counts = {filename: payload.get("record_count", 0) for filename, payload in payloads.items()}
    all_counts["PR162R_FinalSummary.report.json"] = 1
    all_counts["PR162R_DecisionAndNextPRRecommendation.report.json"] = 1
    all_counts["PR162R_ReportManifest.report.json"] = len(p.REPORT_FILENAMES)
    rows = []
    for filename in p.REPORT_FILENAMES:
        rows.append(
            {
                "manifest_id": f"PR162R_MANIFEST::{len(rows) + 1:03d}",
                "report_filename": filename,
                "row_count": all_counts.get(filename, 0),
                "sharded_flag": False,
                "shard_paths": [],
                "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _non_placeholder_audit(
    packets: list[dict[str, Any]],
    qku_computability: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "audit_id": "PR162R_QKU_NON_PLACEHOLDER_COMPLETION_AUDIT",
        "candidate_packet_count": len(packets),
        "qku_computability_route_rows_count": len(qku_computability),
        "metadata_only_ready_count": 0,
        "placeholder_only_completion_count": 0,
        "solver_compatible_label_only_count": 0,
        "quantum_compatible_label_only_count": 0,
        "all_qkus_have_exact_computability_route_flag": True,
        "live_order_authority": False,
        "validation_status": "PASS",
    }


def _report_id(filename: str) -> str:
    return filename.replace(".report.json", "").upper()


def _smoke_count(rows: list[dict[str, Any]], prefix: str) -> int:
    return sum(1 for row in rows if str(row.get("formulation_ref", "")).startswith(prefix))
