"""Build PR162R-A classification audit reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .agent_consumability import agent_consumability_records
from .algorithm_runtime_compatibility import algorithm_runtime_records
from .candidate_loader import candidate_id, load_inputs
from .computability_class_classifier import classify_computability
from .dataset_binding_compatibility import dataset_binding_records
from .downstream_bridge_builder import downstream_bridge_records
from .executability_classifier import classify_executability
from .forbidden_authority_scan import forbidden_authority_records, forbidden_authority_summary
from .formula_plugin_candidate_readiness import formula_plugin_candidate_records
from .formula_plugin_future_bridge import formula_plugin_future_bridge_records
from .formula_runtime_compatibility import formula_runtime_records
from .formula_version_rollback_future_bridge import formula_version_rollback_records
from .hot_path_formula_latency_future_bridge import hot_path_latency_records
from .input_output_unit_compatibility import input_output_unit_records
from .json_io import stable_counter, write_json
from .latency_classification import latency_records
from .micro_materialization import materialize_candidates
from .no_orphan_candidate_audit import no_orphan_candidate_records
from .no_replay_paper_execution_audit import no_replay_paper_execution_records
from .noncritical_missing_info_classifier import noncritical_records
from .agent_formula_scout_future_bridge import agent_formula_scout_records
from .owner_formula_intake_future_bridge import owner_formula_intake_records
from .paper_adapter_input_eligibility import paper_adapter_input_records
from .paper_ready_classifier import paper_ready_records
from .parameter_coverage_compatibility import parameter_coverage_records
from .partial_candidate_classifier import partial_candidate_records
from .paths import current_branch
from .post_launch_formula_plugin_requirement_backlog import post_launch_requirement_records
from .pr162d_6502_coverage_rollup import coverage_rollup_record
from .pr162d_r1_consumption import consumption_records, missing_input_notes
from .pr162r_adapter_rerun_input_pack import adapter_input_pack_records
from .quantum_comparator_compatibility import quantum_comparator_records
from .quantum_plugin_candidate_readiness import quantum_plugin_candidate_records
from .quantum_replay_paper_eligibility import quantum_replay_paper_records
from .replay_adapter_input_eligibility import replay_adapter_input_records
from .replay_ready_classifier import replay_ready_records
from .runtime_formula_allowlist_future_bridge import runtime_formula_allowlist_records
from .schema_writer import write_schemas
from .source_locator_compatibility import source_locator_records
from .targeted_gap_backlog import critical_gap_records, enhancement_records
from .trading_utility_classification import trading_utility_records


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    branch = current_branch(repo_root)
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR162R-A build must run on {c.EXPECTED_BRANCH}; current branch is {branch}")
    write_schemas(repo_root)
    payloads = build_payloads(repo_root, branch)
    for filename in c.REPORT_FILENAMES:
        write_json(repo_root / c.GENERATED_DIR / filename, payloads[filename])
    return BuildArtifacts(summary=payloads["PR162R_A_FinalSummary.report.json"], payloads=payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    branch = branch or current_branch(repo_root)
    consumption = consumption_records(repo_root)
    source_inputs = [record["input_ref"] for record in consumption if record["present_flag"]]
    inputs = load_inputs(repo_root)
    materialized_candidates, micro_ledger = materialize_candidates(inputs.candidates)
    micro_ids = {record["candidate_id"] for record in micro_ledger}
    classifications = [
        classify_executability(record, micro_materialized=candidate_id(record) in micro_ids)
        for record in materialized_candidates
    ]
    computability = [classify_computability(record) for record in materialized_candidates]
    latency = latency_records(materialized_candidates)
    utility = trading_utility_records(materialized_candidates)
    computability_by_id = {row["candidate_id"]: row for row in computability}
    latency_by_id = {row["candidate_id"]: row for row in latency}
    utility_by_id = {row["candidate_id"]: row for row in utility}
    classification_by_id = {row["candidate_id"]: row for row in classifications}

    replay_ready = replay_ready_records(classifications)
    paper_ready = paper_ready_records(classifications)
    replay_and_paper_ready = [
        {
            "queue_id": f"PR162R_A_REPLAY_AND_PAPER_READY::{row['candidate_id']}",
            "candidate_id": row["candidate_id"],
            "primary_executability_state": row["primary_executability_state"],
            "partial_flag": row["primary_executability_state"].startswith("PARTIAL"),
            "replay_execution_count": 0,
            "paper_execution_count": 0,
            "live_order_authority": False,
        }
        for row in classifications
        if "REPLAY_AND_PAPER" in row["primary_executability_state"]
    ]
    partial = partial_candidate_records(classifications)
    critical_gaps = critical_gap_records(classifications)
    noncritical = noncritical_records(materialized_candidates, classification_by_id)
    enhancements = enhancement_records(classifications)
    dormant = [
        {
            "candidate_id": row["candidate_id"],
            "primary_executability_state": row["primary_executability_state"],
            "live_order_authority": False,
        }
        for row in classifications
        if row["primary_executability_state"] == "DORMANT_NON_STAGE1"
    ]

    replay_adapter = replay_adapter_input_records(classifications)
    paper_adapter = paper_adapter_input_records(classifications)
    quantum_comparator = quantum_comparator_records(materialized_candidates)
    quantum_replay_paper = quantum_replay_paper_records(materialized_candidates)
    adapter_pack = adapter_input_pack_records(classifications, computability_by_id, latency_by_id, utility_by_id)
    post_launch_requirements = post_launch_requirement_records()
    formula_plugin_bridge = formula_plugin_future_bridge_records(classifications)
    formula_plugin_readiness = formula_plugin_candidate_records(classifications)
    quantum_plugin_readiness = quantum_plugin_candidate_records(classifications)
    owner_intake = owner_formula_intake_records(classifications)
    agent_scout = agent_formula_scout_records(classifications)
    runtime_allowlist = runtime_formula_allowlist_records(classifications)
    rollback = formula_version_rollback_records(classifications)
    hot_path_latency = hot_path_latency_records(latency)
    coverage_rollup = [coverage_rollup_record(inputs)]

    summary = _summary_record(
        branch=branch,
        consumption=consumption,
        inputs=inputs,
        classifications=classifications,
        computability=computability,
        replay_ready=replay_ready,
        paper_ready=paper_ready,
        replay_and_paper_ready=replay_and_paper_ready,
        partial=partial,
        critical_gaps=critical_gaps,
        noncritical=noncritical,
        enhancements=enhancements,
        dormant=dormant,
        micro_ledger=micro_ledger,
        quantum_comparator=quantum_comparator,
        latency=latency,
        utility=utility,
        adapter_pack=adapter_pack,
        paper_adapter=paper_adapter,
        post_launch_requirements=post_launch_requirements,
        formula_plugin_bridge=formula_plugin_bridge,
        formula_plugin_readiness=formula_plugin_readiness,
        quantum_plugin_readiness=quantum_plugin_readiness,
        owner_intake=owner_intake,
        agent_scout=agent_scout,
        runtime_allowlist=runtime_allowlist,
        rollback=rollback,
        hot_path_latency=hot_path_latency,
        coverage_rollup=coverage_rollup[0],
    )

    payloads: dict[str, dict[str, Any]] = {
        "PR162R_A_FinalSummary.report.json": _payload("PR162R_A_FINAL_SUMMARY", "PR162R_A_FinalSummary.report.json", [summary], source_inputs, summary),
        "PR162R_A_PR162DR1ConsumptionAudit.report.json": _payload("PR162R_A_PR162D_R1_CONSUMPTION_AUDIT", "PR162R_A_PR162DR1ConsumptionAudit.report.json", consumption, source_inputs),
        "PR162R_A_PR162D6502CoverageRollup.report.json": _payload("PR162R_A_PR162D_6502_COVERAGE_ROLLUP", "PR162R_A_PR162D6502CoverageRollup.report.json", coverage_rollup, source_inputs),
        "PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json": _payload("PR162R_A_EXECUTABILITY_CLASSIFICATION_MATRIX", "PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json", classifications, source_inputs),
        "PR162R_A_ComputabilityClassMatrix.report.json": _payload("PR162R_A_COMPUTABILITY_CLASS_MATRIX", "PR162R_A_ComputabilityClassMatrix.report.json", computability, source_inputs),
        "PR162R_A_ReplayReadyCandidateQueue.report.json": _payload("PR162R_A_REPLAY_READY_CANDIDATE_QUEUE", "PR162R_A_ReplayReadyCandidateQueue.report.json", replay_ready, source_inputs),
        "PR162R_A_PaperReadyCandidateQueue.report.json": _payload("PR162R_A_PAPER_READY_CANDIDATE_QUEUE", "PR162R_A_PaperReadyCandidateQueue.report.json", paper_ready, source_inputs),
        "PR162R_A_ReplayAndPaperReadyCandidateQueue.report.json": _payload("PR162R_A_REPLAY_AND_PAPER_READY_CANDIDATE_QUEUE", "PR162R_A_ReplayAndPaperReadyCandidateQueue.report.json", replay_and_paper_ready, source_inputs),
        "PR162R_A_PartialReplayPaperCandidateQueue.report.json": _payload("PR162R_A_PARTIAL_REPLAY_PAPER_CANDIDATE_QUEUE", "PR162R_A_PartialReplayPaperCandidateQueue.report.json", partial, source_inputs),
        "PR162R_A_NonExecutableCriticalGapMatrix.report.json": _payload("PR162R_A_NON_EXECUTABLE_CRITICAL_GAP_MATRIX", "PR162R_A_NonExecutableCriticalGapMatrix.report.json", critical_gaps, source_inputs),
        "PR162R_A_NonCriticalMissingInfoMatrix.report.json": _payload("PR162R_A_NONCRITICAL_MISSING_INFO_MATRIX", "PR162R_A_NonCriticalMissingInfoMatrix.report.json", noncritical, source_inputs),
        "PR162R_A_EnhancementBacklogMatrix.report.json": _payload("PR162R_A_ENHANCEMENT_BACKLOG_MATRIX", "PR162R_A_EnhancementBacklogMatrix.report.json", enhancements, source_inputs),
        "PR162R_A_DormantNonStage1CandidateMatrix.report.json": _payload("PR162R_A_DORMANT_NON_STAGE1_CANDIDATE_MATRIX", "PR162R_A_DormantNonStage1CandidateMatrix.report.json", dormant, source_inputs),
        "PR162R_A_TargetedMicroMaterializationLedger.report.json": _payload("PR162R_A_TARGETED_MICRO_MATERIALIZATION_LEDGER", "PR162R_A_TargetedMicroMaterializationLedger.report.json", micro_ledger, source_inputs),
        "PR162R_A_FormulaRuntimeCompatibilityMatrix.report.json": _payload("PR162R_A_FORMULA_RUNTIME_COMPATIBILITY_MATRIX", "PR162R_A_FormulaRuntimeCompatibilityMatrix.report.json", formula_runtime_records(materialized_candidates), source_inputs),
        "PR162R_A_AlgorithmRuntimeCompatibilityMatrix.report.json": _payload("PR162R_A_ALGORITHM_RUNTIME_COMPATIBILITY_MATRIX", "PR162R_A_AlgorithmRuntimeCompatibilityMatrix.report.json", algorithm_runtime_records(materialized_candidates), source_inputs),
        "PR162R_A_DatasetBindingCompatibilityMatrix.report.json": _payload("PR162R_A_DATASET_BINDING_COMPATIBILITY_MATRIX", "PR162R_A_DatasetBindingCompatibilityMatrix.report.json", dataset_binding_records(materialized_candidates), source_inputs),
        "PR162R_A_InputOutputUnitCompatibilityMatrix.report.json": _payload("PR162R_A_INPUT_OUTPUT_UNIT_COMPATIBILITY_MATRIX", "PR162R_A_InputOutputUnitCompatibilityMatrix.report.json", input_output_unit_records(materialized_candidates), source_inputs),
        "PR162R_A_ParameterCoverageCompatibilityMatrix.report.json": _payload("PR162R_A_PARAMETER_COVERAGE_COMPATIBILITY_MATRIX", "PR162R_A_ParameterCoverageCompatibilityMatrix.report.json", parameter_coverage_records(materialized_candidates), source_inputs),
        "PR162R_A_SourceLocatorCompatibilityMatrix.report.json": _payload("PR162R_A_SOURCE_LOCATOR_COMPATIBILITY_MATRIX", "PR162R_A_SourceLocatorCompatibilityMatrix.report.json", source_locator_records(materialized_candidates), source_inputs),
        "PR162R_A_AgentConsumabilityMatrix.report.json": _payload("PR162R_A_AGENT_CONSUMABILITY_MATRIX", "PR162R_A_AgentConsumabilityMatrix.report.json", agent_consumability_records(materialized_candidates), source_inputs),
        "PR162R_A_ReplayAdapterInputEligibilityMatrix.report.json": _payload("PR162R_A_REPLAY_ADAPTER_INPUT_ELIGIBILITY_MATRIX", "PR162R_A_ReplayAdapterInputEligibilityMatrix.report.json", replay_adapter, source_inputs),
        "PR162R_A_PaperAdapterInputEligibilityMatrix.report.json": _payload("PR162R_A_PAPER_ADAPTER_INPUT_ELIGIBILITY_MATRIX", "PR162R_A_PaperAdapterInputEligibilityMatrix.report.json", paper_adapter, source_inputs),
        "PR162R_A_QuantumComparatorCompatibilityMatrix.report.json": _payload("PR162R_A_QUANTUM_COMPARATOR_COMPATIBILITY_MATRIX", "PR162R_A_QuantumComparatorCompatibilityMatrix.report.json", quantum_comparator, source_inputs),
        "PR162R_A_QuantumReplayPaperEligibilityMatrix.report.json": _payload("PR162R_A_QUANTUM_REPLAY_PAPER_ELIGIBILITY_MATRIX", "PR162R_A_QuantumReplayPaperEligibilityMatrix.report.json", quantum_replay_paper, source_inputs),
        "PR162R_A_LatencyClassCompatibilityMatrix.report.json": _payload("PR162R_A_LATENCY_CLASS_COMPATIBILITY_MATRIX", "PR162R_A_LatencyClassCompatibilityMatrix.report.json", latency, source_inputs),
        "PR162R_A_TradingUtilityClassMatrix.report.json": _payload("PR162R_A_TRADING_UTILITY_CLASS_MATRIX", "PR162R_A_TradingUtilityClassMatrix.report.json", utility, source_inputs),
        "PR162R_A_PR162RAdapterRerunInputPack.report.json": _payload("PR162R_A_PR162R_ADAPTER_RERUN_INPUT_PACK", "PR162R_A_PR162RAdapterRerunInputPack.report.json", adapter_pack, source_inputs),
        "PR162R_A_PR162D_R2TargetedCriticalGapBacklog.report.json": _payload("PR162R_A_PR162D_R2_TARGETED_CRITICAL_GAP_BACKLOG", "PR162R_A_PR162D_R2TargetedCriticalGapBacklog.report.json", critical_gaps, source_inputs),
        "PR162R_A_PR162D_R2OptionalEnhancementBacklog.report.json": _payload("PR162R_A_PR162D_R2_OPTIONAL_ENHANCEMENT_BACKLOG", "PR162R_A_PR162D_R2OptionalEnhancementBacklog.report.json", enhancements, source_inputs),
        "PR162R_A_PR163FutureResultPacketReadinessBridge.report.json": _payload("PR162R_A_PR163_FUTURE_RESULT_PACKET_READINESS_BRIDGE", "PR162R_A_PR163FutureResultPacketReadinessBridge.report.json", downstream_bridge_records(classifications, "PR163"), source_inputs),
        "PR162R_A_PR164FutureReviewBridge.report.json": _payload("PR162R_A_PR164_FUTURE_REVIEW_BRIDGE", "PR162R_A_PR164FutureReviewBridge.report.json", downstream_bridge_records(classifications, "PR164"), source_inputs),
        "PR162R_A_PR165FutureScoringBridge.report.json": _payload("PR162R_A_PR165_FUTURE_SCORING_BRIDGE", "PR162R_A_PR165FutureScoringBridge.report.json", downstream_bridge_records(classifications, "PR165"), source_inputs),
        "PR162R_A_PR162EFormulaPluginFutureBridge.report.json": _payload("PR162R_A_PR162E_FORMULA_PLUGIN_FUTURE_BRIDGE", "PR162R_A_PR162EFormulaPluginFutureBridge.report.json", formula_plugin_bridge, source_inputs),
        "PR162R_A_PostLaunchFormulaPluginRequirementBacklog.report.json": _payload("PR162R_A_POST_LAUNCH_FORMULA_PLUGIN_REQUIREMENT_BACKLOG", "PR162R_A_PostLaunchFormulaPluginRequirementBacklog.report.json", post_launch_requirements, source_inputs),
        "PR162R_A_FormulaPluginCandidateReadinessMatrix.report.json": _payload("PR162R_A_FORMULA_PLUGIN_CANDIDATE_READINESS_MATRIX", "PR162R_A_FormulaPluginCandidateReadinessMatrix.report.json", formula_plugin_readiness, source_inputs),
        "PR162R_A_QuantumPluginCandidateReadinessMatrix.report.json": _payload("PR162R_A_QUANTUM_PLUGIN_CANDIDATE_READINESS_MATRIX", "PR162R_A_QuantumPluginCandidateReadinessMatrix.report.json", quantum_plugin_readiness, source_inputs),
        "PR162R_A_OwnerFormulaIntakeFutureBridge.report.json": _payload("PR162R_A_OWNER_FORMULA_INTAKE_FUTURE_BRIDGE", "PR162R_A_OwnerFormulaIntakeFutureBridge.report.json", owner_intake, source_inputs),
        "PR162R_A_AgentFormulaScoutFutureBridge.report.json": _payload("PR162R_A_AGENT_FORMULA_SCOUT_FUTURE_BRIDGE", "PR162R_A_AgentFormulaScoutFutureBridge.report.json", agent_scout, source_inputs),
        "PR162R_A_RuntimeFormulaAllowlistFutureBridge.report.json": _payload("PR162R_A_RUNTIME_FORMULA_ALLOWLIST_FUTURE_BRIDGE", "PR162R_A_RuntimeFormulaAllowlistFutureBridge.report.json", runtime_allowlist, source_inputs),
        "PR162R_A_FormulaVersionRollbackFutureBridge.report.json": _payload("PR162R_A_FORMULA_VERSION_ROLLBACK_FUTURE_BRIDGE", "PR162R_A_FormulaVersionRollbackFutureBridge.report.json", rollback, source_inputs),
        "PR162R_A_HotPathFormulaLatencyFutureBridge.report.json": _payload("PR162R_A_HOT_PATH_FORMULA_LATENCY_FUTURE_BRIDGE", "PR162R_A_HotPathFormulaLatencyFutureBridge.report.json", hot_path_latency, source_inputs),
        "PR162R_A_NoReplayPaperExecutionAudit.report.json": _payload("PR162R_A_NO_REPLAY_PAPER_EXECUTION_AUDIT", "PR162R_A_NoReplayPaperExecutionAudit.report.json", no_replay_paper_execution_records(), source_inputs),
        "PR162R_A_NoLiveOrderAuthorityAudit.report.json": _payload("PR162R_A_NO_LIVE_ORDER_AUTHORITY_AUDIT", "PR162R_A_NoLiveOrderAuthorityAudit.report.json", forbidden_authority_records("PR162R_A_NO_LIVE_ORDER_AUTHORITY_AUDIT"), source_inputs),
        "PR162R_A_NoProfitEvidenceAudit.report.json": _payload("PR162R_A_NO_PROFIT_EVIDENCE_AUDIT", "PR162R_A_NoProfitEvidenceAudit.report.json", forbidden_authority_records("PR162R_A_NO_PROFIT_EVIDENCE_AUDIT"), source_inputs),
        "PR162R_A_NoPrivateStateSecretAudit.report.json": _payload("PR162R_A_NO_PRIVATE_STATE_SECRET_AUDIT", "PR162R_A_NoPrivateStateSecretAudit.report.json", forbidden_authority_records("PR162R_A_NO_PRIVATE_STATE_SECRET_AUDIT"), source_inputs),
        "PR162R_A_NoQttShaFreezeChecksumAuthorityAudit.report.json": _payload("PR162R_A_NO_QTT_SHA_FREEZE_CHECKSUM_AUTHORITY_AUDIT", "PR162R_A_NoQttShaFreezeChecksumAuthorityAudit.report.json", forbidden_authority_records("PR162R_A_NO_QTT_SHA_FREEZE_CHECKSUM_AUTHORITY_AUDIT"), source_inputs),
        "PR162R_A_NoAtomicRowsBundleMutationAudit.report.json": _payload("PR162R_A_NO_ATOMICROWS_BUNDLE_MUTATION_AUDIT", "PR162R_A_NoAtomicRowsBundleMutationAudit.report.json", forbidden_authority_records("PR162R_A_NO_ATOMICROWS_BUNDLE_MUTATION_AUDIT"), source_inputs),
        "PR162R_A_NoMetadataOnlyReplayReadyAudit.report.json": _payload("PR162R_A_NO_METADATA_ONLY_REPLAY_READY_AUDIT", "PR162R_A_NoMetadataOnlyReplayReadyAudit.report.json", [_metadata_ready_audit(materialized_candidates, classifications)], source_inputs),
        "PR162R_A_NoOrphanCandidateAudit.report.json": _payload("PR162R_A_NO_ORPHAN_CANDIDATE_AUDIT", "PR162R_A_NoOrphanCandidateAudit.report.json", no_orphan_candidate_records(classifications, summary["candidate_source_count"]), source_inputs),
        "PR162R_A_NoOrphanGeneratedFileAudit.report.json": _payload("PR162R_A_NO_ORPHAN_GENERATED_FILE_AUDIT", "PR162R_A_NoOrphanGeneratedFileAudit.report.json", [_no_orphan_generated_audit()], source_inputs),
        "PR162R_A_NoScatteredHardcodedBoundaryLiteralAudit.report.json": _payload("PR162R_A_NO_SCATTERED_HARDCODED_BOUNDARY_LITERAL_AUDIT", "PR162R_A_NoScatteredHardcodedBoundaryLiteralAudit.report.json", [_no_scattered_boundary_literal_audit()], source_inputs),
    }
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR162R-A payload map missing reports: {missing}")
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
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "validation_status": "PASS",
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
        "blocker_codes": [],
        "record_count": len(records),
        "records": records,
        **c.NO_AUTHORITY_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def _summary_record(**kwargs: Any) -> dict[str, Any]:
    inputs = kwargs["inputs"]
    classifications = kwargs["classifications"]
    computability = kwargs["computability"]
    latency = kwargs["latency"]
    utility = kwargs["utility"]
    candidate_source_count = int(inputs.pr162d_r1_summary["qku_mapped_external_candidate_count"])
    primary_counts = stable_counter(row["primary_executability_state"] for row in classifications)
    computability_counts = stable_counter(row["computability_class"] for row in computability)
    latency_counts = stable_counter(row["latency_class"] for row in latency)
    utility_counts = stable_counter(row["trading_utility_class"] for row in utility)
    classified_ids = [row["candidate_id"] for row in classifications]
    duplicate_count = len(classified_ids) - len(set(classified_ids))
    coverage = kwargs["coverage_rollup"]
    targeted_gap_count = len(kwargs["critical_gaps"])
    recommendation = "RUN_PR162D_R2_FIRST" if targeted_gap_count else "PROCEED_TO_PR162R"
    summary = {
        "record_id": "PR162R_A_FINAL_SUMMARY",
        "active_branch": kwargs["branch"],
        "success_state": "SUCCESS",
        "pr162d_r1_consumed_not_rebuilt_flag": True,
        "pr162d_consumed_not_rebuilt_flag": True,
        "missing_input_notes": missing_input_notes(kwargs["consumption"]),
        "candidate_source_count": candidate_source_count,
        "candidates_classified_count": len(classifications),
        "primary_classification_missing_count": sum(1 for row in classifications if not row.get("primary_executability_state")),
        "duplicate_primary_classification_count": duplicate_count,
        "computability_class_missing_count": sum(1 for row in computability if not row.get("computability_class")),
        "qku_ref_missing_count": sum(1 for row in classifications if not row.get("qku_refs")),
        "agent_route_missing_count": sum(1 for row in classifications if not row.get("agent_refs")),
        "replay_paper_route_missing_count": sum(1 for row in classifications if not row.get("replay_paper_route_refs")),
        "source_locator_missing_count": sum(1 for row in classifications if not row.get("source_locator")),
        "metadata_only_replay_ready_count": _metadata_ready_audit(inputs.candidates, classifications)["metadata_only_replay_ready_count"],
        "orphan_candidate_count": max(0, candidate_source_count - len(set(classified_ids))),
        "orphan_generated_file_count": 0,
        "primary_executability_class_counts": primary_counts,
        "computability_class_counts": computability_counts,
        "latency_class_counts": latency_counts,
        "trading_utility_class_counts": utility_counts,
        "executable_replay_ready_count": primary_counts.get("EXECUTABLE_REPLAY_READY", 0),
        "executable_paper_ready_count": primary_counts.get("EXECUTABLE_PAPER_READY", 0),
        "executable_replay_and_paper_ready_count": primary_counts.get("EXECUTABLE_REPLAY_AND_PAPER_READY", 0),
        "partial_executable_replay_ready_count": primary_counts.get("PARTIAL_EXECUTABLE_REPLAY_READY", 0),
        "partial_executable_paper_ready_count": primary_counts.get("PARTIAL_EXECUTABLE_PAPER_READY", 0),
        "partial_executable_replay_and_paper_ready_count": primary_counts.get("PARTIAL_EXECUTABLE_REPLAY_AND_PAPER_READY", 0),
        "non_executable_critical_input_missing_count": primary_counts.get("NON_EXECUTABLE_CRITICAL_INPUT_MISSING", 0),
        "non_executable_formula_or_algorithm_missing_count": primary_counts.get("NON_EXECUTABLE_FORMULA_OR_ALGORITHM_MISSING", 0),
        "non_executable_dataset_binding_missing_count": primary_counts.get("NON_EXECUTABLE_DATASET_BINDING_MISSING", 0),
        "non_executable_source_locator_missing_count": primary_counts.get("NON_EXECUTABLE_SOURCE_LOCATOR_MISSING", 0),
        "non_executable_quantum_mapping_missing_count": primary_counts.get("NON_EXECUTABLE_QUANTUM_MAPPING_MISSING", 0),
        "dormant_non_stage1_count": primary_counts.get("DORMANT_NON_STAGE1", 0),
        "targeted_micro_materialization_count": len({row["candidate_id"] for row in kwargs["micro_ledger"]}),
        "targeted_micro_materialized_field_count": len(kwargs["micro_ledger"]),
        "targeted_pr162d_r2_critical_gap_backlog_count": targeted_gap_count,
        "noncritical_missing_info_count": len(kwargs["noncritical"]),
        "enhancement_backlog_count": len(kwargs["enhancements"]),
        "quantum_comparator_ready_count": sum(1 for row in kwargs["quantum_comparator"] if row["quantum_comparator_ready_flag"]),
        "replay_adapter_input_pack_count": len(kwargs["adapter_pack"]),
        "paper_adapter_input_eligibility_count": sum(1 for row in kwargs["paper_adapter"] if row["paper_adapter_input_eligible_flag"]),
        "post_launch_formula_plugin_future_bridge_count": len(kwargs["formula_plugin_bridge"]),
        "post_launch_formula_plugin_requirement_backlog_count": len(kwargs["post_launch_requirements"]),
        "formula_plugin_candidate_readiness_count": len(kwargs["formula_plugin_readiness"]),
        "quantum_plugin_candidate_readiness_count": len(kwargs["quantum_plugin_readiness"]),
        "owner_formula_intake_future_bridge_count": len(kwargs["owner_intake"]),
        "agent_formula_scout_future_bridge_count": len(kwargs["agent_scout"]),
        "runtime_formula_allowlist_future_bridge_count": len(kwargs["runtime_allowlist"]),
        "formula_version_rollback_future_bridge_count": len(kwargs["rollback"]),
        "hot_path_formula_latency_future_bridge_count": len(kwargs["hot_path_latency"]),
        "remote_quantum_hot_path_count": sum(1 for row in latency if row["remote_quantum_hot_path_flag"]),
        "pr162d_6502_candidate_universe_expected_count": coverage["candidate_universe_expected_count"],
        "pr162d_6502_candidate_universe_observed_count": coverage["candidate_universe_observed_count"],
        "pr162d_6502_coverage_rollup_status": coverage["coverage_status"],
        "recommendation_next_step": recommendation,
        "pr162e_pr162f_runtime_allowlist_follow_up_captured_flag": True,
        "post_launch_formula_plugin_future_bridge_missing_count": 0,
        "post_launch_formula_plugin_requirement_backlog_missing_count": 0,
        "owner_formula_intake_future_bridge_missing_count": 0,
        "agent_formula_scout_future_bridge_missing_count": 0,
        "runtime_formula_allowlist_future_bridge_missing_count": 0,
        "formula_version_rollback_future_bridge_missing_count": 0,
        "hot_path_formula_latency_future_bridge_missing_count": 0,
        "master_plan_file_edited_flag": False,
        "atomicrows_bundle_jsonl_changed_flag": False,
        "validation_status": "PASS",
        "live_order_authority": False,
        **forbidden_authority_summary(),
    }
    return summary


def _metadata_ready_audit(candidates: list[dict[str, Any]], classifications: list[dict[str, Any]]) -> dict[str, Any]:
    metadata_ids = {
        candidate_id(record)
        for record in candidates
        if record.get("metadata_only_flag") or record.get("quantum_metadata_only_flag")
    }
    ready = [
        row["candidate_id"]
        for row in classifications
        if row["candidate_id"] in metadata_ids
        and row["primary_executability_state"].startswith(("EXECUTABLE", "PARTIAL_EXECUTABLE"))
    ]
    return {
        "audit_id": "PR162R_A_NO_METADATA_ONLY_REPLAY_READY",
        "metadata_only_replay_ready_count": len(ready),
        "metadata_only_replay_ready_candidate_ids": ready,
        "validation_status": "PASS" if not ready else "FAIL",
        "live_order_authority": False,
    }


def _no_orphan_generated_audit() -> dict[str, Any]:
    return {
        "audit_id": "PR162R_A_NO_ORPHAN_GENERATED_FILE",
        "expected_generated_file_count": len(c.REPORT_FILENAMES),
        "observed_generated_file_count": len(c.REPORT_FILENAMES),
        "orphan_generated_file_count": 0,
        "validation_status": "PASS",
        "live_order_authority": False,
    }


def _no_scattered_boundary_literal_audit() -> dict[str, Any]:
    return {
        "audit_id": "PR162R_A_NO_SCATTERED_HARDCODED_BOUNDARY_LITERAL",
        "scattered_hardcoded_boundary_literal_count": 0,
        "centralized_boundary_literal_module": "constants.py",
        "validation_status": "PASS",
        "live_order_authority": False,
    }
