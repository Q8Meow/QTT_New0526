"""Input discovery for PR162D-R2A."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json, records_from_payload


MANDATORY_INPUTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md",
    "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentWorkflowOrchestrationContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentRoleIOContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentHandoffMatrix.report.json",
    "docs/master_plan/generated/PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR162D_FinalSummary.report.json",
    "docs/master_plan/generated/PR162D_PR162CBlockerReinterpretationLedger.report.json",
    "docs/master_plan/generated/PR162D_AggressiveQKUCandidateAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_QKUFieldFillExpansionMatrix.report.json",
    "docs/master_plan/generated/PR162D_QKUMaterializationProgressMatrix.report.json",
    "docs/master_plan/generated/PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR162D_ReplayPaperCandidateRouterQueue.report.json",
    "docs/master_plan/generated/PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json",
    "docs/master_plan/generated/PR162D_ReportShardManifest.report.json",
    "docs/master_plan/generated/PR162D_R1_FinalSummary.report.json",
    "docs/master_plan/generated/PR162D_R1_MasterPlanFormulaAlgorithmMiningLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_MasterPlanQKUFormulaCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_MasterPlanAlgorithmFamilyCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_MasterPlanParameterPackExtractionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_MasterPlanQuantumFormulaExtractionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_MasterPlanFormulaToExternalAcquisitionGapMatrix.report.json",
    "docs/master_plan/generated/PR162D_R1_ComputableCandidateRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_QKUExternalCandidateMappingMatrix.report.json",
    "docs/master_plan/generated/PR162D_R1_AgentExternalCandidateRouteMatrix.report.json",
    "docs/master_plan/generated/PR162D_R1_ReplayPaperExternalCandidateQueue.report.json",
    "docs/master_plan/generated/PR162D_R1_PR162RHandoffExpansion.report.json",
    "docs/master_plan/generated/PR162D_R1_FormulaAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_FormulaExpressionExpansionRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_AlgorithmAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_ParameterRangeAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_DefaultValueScaleAcquisitionLedger.report.json",
    "docs/master_plan/generated/PR162D_R1_QuantumProblemFormulationRegistry.report.json",
    "docs/master_plan/generated/PR162D_R1_SourceLocatorRegistry.report.json",
    "docs/master_plan/generated/PR162R_A_FinalSummary.report.json",
    "docs/master_plan/generated/PR162R_A_PR162D6502CoverageRollup.report.json",
    "docs/master_plan/generated/PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json",
    "docs/master_plan/generated/PR162R_A_ComputabilityClassMatrix.report.json",
    "docs/master_plan/generated/PR162R_A_PR162RAdapterRerunInputPack.report.json",
    "docs/master_plan/generated/PR162R_A_TargetedMicroMaterializationLedger.report.json",
    "docs/master_plan/generated/PR162R_A_PR162D_R2TargetedCriticalGapBacklog.report.json",
    "docs/master_plan/generated/PR162R_A_PostLaunchFormulaPluginRequirementBacklog.report.json",
    "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
    "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
    "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json",
    "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
    "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
)


@dataclass(frozen=True)
class PriorInputs:
    source_inputs: tuple[str, ...]
    missing_input_notes: tuple[dict[str, Any], ...]
    pr162d_qku_records: tuple[dict[str, Any], ...]
    pr162d_r1_candidates: tuple[dict[str, Any], ...]
    pr162r_a_classifications: tuple[dict[str, Any], ...]
    master_plan_scan_counts: dict[str, int]


def load_prior_inputs(repo_root: Path) -> PriorInputs:
    missing: list[dict[str, Any]] = []
    present: list[str] = []
    for rel in MANDATORY_INPUTS:
        path = repo_root / rel
        if path.exists():
            present.append(rel)
        else:
            missing.append(
                {
                    "input_ref": rel,
                    "present_flag": False,
                    "missing_input_note": "Required lineage input was not present; fallback data will be used if available.",
                }
            )
    qku_records = _load_pr162d_qku_records(repo_root)
    if not qku_records:
        missing.append(
            {
                "input_ref": str(p.SHARD_DIR / "PR162D_PR162CBlockerReinterpretationLedger.report.shard_*.json"),
                "present_flag": False,
                "missing_input_note": "PR162D 6502 shard records were not discovered.",
            }
        )
    r1_candidates = _load_records(repo_root / p.GENERATED_DIR / "PR162D_R1_ComputableCandidateRegistry.report.json")
    r_a_classifications = _load_records(
        repo_root / p.GENERATED_DIR / "PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json"
    )
    scan_counts = _load_master_plan_scan_counts(repo_root)
    return PriorInputs(
        source_inputs=tuple(present),
        missing_input_notes=tuple(missing),
        pr162d_qku_records=tuple(qku_records),
        pr162d_r1_candidates=tuple(r1_candidates),
        pr162r_a_classifications=tuple(r_a_classifications),
        master_plan_scan_counts=scan_counts,
    )


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return records_from_payload(read_json(path))


def _load_pr162d_qku_records(repo_root: Path) -> list[dict[str, Any]]:
    shard_glob = "PR162D_PR162CBlockerReinterpretationLedger.report.shard_*.json"
    rows: list[dict[str, Any]] = []
    for shard in sorted((repo_root / p.SHARD_DIR).glob(shard_glob)):
        rows.extend(records_from_payload(read_json(shard)))
    dedup: dict[str, dict[str, Any]] = {}
    for row in rows:
        qku_id = str(row.get("qku_id", ""))
        if qku_id:
            dedup[qku_id] = row
    return [dedup[key] for key in sorted(dedup)]


def _load_master_plan_scan_counts(repo_root: Path) -> dict[str, int]:
    path = repo_root / p.GENERATED_DIR / "PR162D_R1_MasterPlanFormulaAlgorithmMiningLedger.report.json"
    counts = {
        "formula_mentions": 0,
        "algorithm_mentions": 0,
        "parameter_pack_mentions": 0,
        "quantum_mentions": 0,
    }
    if not path.exists():
        return counts
    for row in records_from_payload(read_json(path)):
        family = row.get("scan_family")
        count = int(row.get("mentions_scanned_count", 0))
        if family == "formula":
            counts["formula_mentions"] = count
        elif family == "algorithm":
            counts["algorithm_mentions"] = count
        elif family == "parameter_pack":
            counts["parameter_pack_mentions"] = count
        elif family == "quantum":
            counts["quantum_mentions"] = count
    return counts
