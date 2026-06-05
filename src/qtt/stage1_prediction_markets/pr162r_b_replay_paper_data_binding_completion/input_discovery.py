"""Input discovery for PR162R-B lineage consumption."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .json_io import read_json, record_count


REQUIRED_INPUTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
    "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
    "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162D_FinalSummary.report.json",
    "docs/master_plan/generated/PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR162D_ReplayPaperCandidateRouterQueue.report.json",
    "docs/master_plan/generated/PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json",
    "docs/master_plan/generated/PR162D_R1_FinalSummary.report.json",
    "docs/master_plan/generated/PR162D_R1_ComputableCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_QKUExternalCandidateMappingMatrix.report.json",
    "docs/master_plan/generated/PR162D_R1_AgentExternalCandidateRouteMatrix.report.json",
    "docs/master_plan/generated/PR162D_R1_ReplayPaperExternalCandidateQueue.report.json",
    "docs/master_plan/generated/PR162D_R1_PR162RHandoffExpansion.report.json",
    "docs/master_plan/generated/PR162D_R1_SourceLocatorRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_QuantumProblemFormulationRegistry.report.json",
    "docs/master_plan/generated/PR162R_A_FinalSummary.report.json",
    "docs/master_plan/generated/PR162R_A_PR162RAdapterRerunInputPack.report.json",
    "docs/master_plan/generated/PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json",
    "docs/master_plan/generated/PR162R_A_ComputabilityClassMatrix.report.json",
    "docs/master_plan/generated/PR162R_A_PR162D6502CoverageRollup.report.json",
    "docs/master_plan/generated/PR162D_R2A_FinalSummary.report.json",
    "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json",
    "docs/master_plan/generated/PR162D_R2A_PR162RGenericCandidateInputExtension.report.json",
    "docs/master_plan/generated/PR162D_R2A_FormulationRecordRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_FormulaExpressionRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_AlgorithmProcedureRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_QuantumObjectiveRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_ClassicalComparatorRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json",
    "docs/master_plan/generated/PR162D_R2A_FormulationCoverageAudit.report.json",
    "docs/master_plan/generated/PR162D_R2A_FormulaLatencyClassRegistry.report.json",
    "docs/master_plan/generated/PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json",
    "docs/master_plan/generated/PR162D_R2A_PR162EPluginSeedCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162R_FinalSummary.report.json",
    "docs/master_plan/generated/PR162R_InputConsumptionAudit.report.json",
    "docs/master_plan/generated/PR162R_CandidatePacketV1IngestionLedger.report.json",
    "docs/master_plan/generated/PR162R_QKUComputabilityClassificationMatrix.report.json",
    "docs/master_plan/generated/PR162R_ReplayPaperDataBindingRequirementMatrix.report.json",
    "docs/master_plan/generated/PR162R_MissingDataBindingActionQueue.report.json",
    "docs/master_plan/generated/PR162R_OnlineSourceScoutQueue.report.json",
    "docs/master_plan/generated/PR162R_SourceCandidateMaterializationQueue.report.json",
    "docs/master_plan/generated/PR162R_ReplayAdapterInputPacketRegistry.report.json",
    "docs/master_plan/generated/PR162R_PaperAdapterInputPacketRegistry.report.json",
    "docs/master_plan/generated/PR162R_ReplayRunRequestCandidateQueue.report.json",
    "docs/master_plan/generated/PR162R_PaperRunRequestCandidateQueue.report.json",
    "docs/master_plan/generated/PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json",
    "docs/master_plan/generated/PR162R_QuantumBatchPrecomputeRoutingPlan.report.json",
    "docs/master_plan/generated/PR162R_LatencyPrecomputeRoutingMatrix.report.json",
    "docs/master_plan/generated/PR162R_QKUAgentReplayPaperHandoffMatrix.report.json",
    "docs/master_plan/generated/PR162R_MarketSpecificQKUAdapterIndex.report.json",
    "docs/master_plan/generated/PR162R_CommandActionQKUBindingMatrix.report.json",
    "docs/master_plan/generated/PR162R_PR163PaperAdapterHandoffSeed.report.json",
    "docs/master_plan/generated/PR162R_PR164ReviewProvenanceHandoffSeed.report.json",
    "docs/master_plan/generated/PR162R_PR165ScoringRankingHandoffSeed.report.json",
    "docs/master_plan/generated/PR162R_PR162EPluginReplayPaperCompatibilitySeed.report.json",
    "docs/master_plan/generated/PR162R_DecisionAndNextPRRecommendation.report.json",
    "docs/master_plan/generated/PR162R_ReportManifest.report.json",
)

FALLBACK_INPUTS = {
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json": (
        "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json"
    ),
}


def discover_inputs(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, requested in enumerate(REQUIRED_INPUTS, start=1):
        requested_path = repo_root / requested
        consumed = requested
        fallback_lineage_used = False
        exact_missing_input_note = ""
        if not requested_path.exists() and requested in FALLBACK_INPUTS:
            fallback = FALLBACK_INPUTS[requested]
            if (repo_root / fallback).exists():
                consumed = fallback
                fallback_lineage_used = True
                exact_missing_input_note = (
                    f"{requested} absent in merged state; consumed canonical fallback {fallback}"
                )
        consumed_path = repo_root / consumed
        present = consumed_path.exists()
        record_count_value = 0
        top_level_shape = "MISSING"
        if present:
            if consumed_path.suffix == ".json":
                payload = read_json(consumed_path)
                record_count_value = record_count(payload)
                top_level_shape = type(payload).__name__
            else:
                text = consumed_path.read_text(encoding="utf-8")
                record_count_value = text.count("\n") + 1
                top_level_shape = "markdown"
        rows.append(
            {
                "input_id": f"PR162R_B_INPUT::{index:03d}",
                "requested_path": requested,
                "consumed_path": consumed if present else "",
                "present_flag": present,
                "record_count": record_count_value,
                "top_level_shape": top_level_shape,
                "fallback_lineage_used": fallback_lineage_used,
                "exact_missing_input_note": exact_missing_input_note,
                "consumed_before_report_pass_flag": present,
                "live_order_authority": False,
                "validation_status": "PASS" if present else "INPUT_ABSENT_WITH_EXACT_FALLBACK_OR_NOTE",
            }
        )
    return rows
