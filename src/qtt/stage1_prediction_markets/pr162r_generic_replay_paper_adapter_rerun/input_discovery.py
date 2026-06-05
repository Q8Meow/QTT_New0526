"""Input discovery and fallback lineage audit for PR162R."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class InputSpec:
    input_id: str
    path: str
    required: bool = True
    fallback_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoveredInput:
    input_id: str
    requested_path: str
    present_flag: bool
    consumed_path: str | None
    fallback_lineage_used: list[str]
    exact_missing_input_note: str | None
    record_count: int
    top_level_shape: str


REQUIRED_INPUT_SPECS: tuple[InputSpec, ...] = (
    InputSpec("MASTER_PLAN", "docs/master_plan/QTT_MasterPlan_Current.md"),
    InputSpec("PR_IDENTITY_ROSTER", "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    InputSpec("ROADMAP_EXECUTION_CONTROLLER", "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"),
    InputSpec("POST_PR135_DAY1_ROADMAP", "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
    InputSpec("PR136_ROUTE_TRIAGE", "docs/master_plan/generated/PR136RouteTriage.report.json"),
    InputSpec(
        "PR136_MASTER_PLAN_SECTION_CROSSWALK",
        "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
        fallback_paths=("docs/master_plan/generated/PR162D_PR136CrosswalkConsumptionAudit.report.json",),
    ),
    InputSpec("PR136_MARKET_INDEX", "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"),
    InputSpec("PR136_COMMAND_ACTION", "docs/master_plan/generated/PR136CommandActionMatrix.report.json"),
    InputSpec("PR136_COVERAGE_TO_READINESS", "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"),
    InputSpec("PR161F_REPLAY_RUN_REQUEST", "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json"),
    InputSpec("PR161F_PAPER_RUN_REQUEST", "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json"),
    InputSpec("PR161F_PAIRED_RUN_PLAN", "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json"),
    InputSpec("PR161F_RESULT_ELIGIBILITY", "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json"),
    InputSpec("PR162_REPLAY_CONTRACT", "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json"),
    InputSpec("PR162_PAPER_CONTRACT", "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json"),
    InputSpec("PR162D_FINAL_SUMMARY", "docs/master_plan/generated/PR162D_FinalSummary.report.json"),
    InputSpec("PR162D_TRACEABILITY", "docs/master_plan/generated/PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json"),
    InputSpec("PR162D_ROUTER_QUEUE", "docs/master_plan/generated/PR162D_ReplayPaperCandidateRouterQueue.report.json"),
    InputSpec("PR162D_HANDOFF", "docs/master_plan/generated/PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json"),
    InputSpec("PR162D_R1_FINAL_SUMMARY", "docs/master_plan/generated/PR162D_R1_FinalSummary.report.json"),
    InputSpec("PR162D_R1_COMPUTABLE", "docs/master_plan/generated/PR162D_R1_ComputableCandidateRegistry.report.json"),
    InputSpec("PR162D_R1_QKU_MAPPING", "docs/master_plan/generated/PR162D_R1_QKUExternalCandidateMappingMatrix.report.json"),
    InputSpec("PR162D_R1_AGENT_ROUTE", "docs/master_plan/generated/PR162D_R1_AgentExternalCandidateRouteMatrix.report.json"),
    InputSpec("PR162D_R1_REPLAY_PAPER_QUEUE", "docs/master_plan/generated/PR162D_R1_ReplayPaperExternalCandidateQueue.report.json"),
    InputSpec("PR162D_R1_HANDOFF", "docs/master_plan/generated/PR162D_R1_PR162RHandoffExpansion.report.json"),
    InputSpec("PR162D_R1_SOURCE_LOCATOR", "docs/master_plan/generated/PR162D_R1_SourceLocatorRegistry.report.json"),
    InputSpec("PR162D_R1_QUANTUM", "docs/master_plan/generated/PR162D_R1_QuantumProblemFormulationRegistry.report.json"),
    InputSpec("PR162R_A_FINAL_SUMMARY", "docs/master_plan/generated/PR162R_A_FinalSummary.report.json"),
    InputSpec("PR162R_A_CLASSIFICATION", "docs/master_plan/generated/PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json"),
    InputSpec("PR162R_A_COMPUTABILITY", "docs/master_plan/generated/PR162R_A_ComputabilityClassMatrix.report.json"),
    InputSpec("PR162R_A_ADAPTER_PACK", "docs/master_plan/generated/PR162R_A_PR162RAdapterRerunInputPack.report.json"),
    InputSpec("PR162R_A_6502_ROLLUP", "docs/master_plan/generated/PR162R_A_PR162D6502CoverageRollup.report.json"),
    InputSpec("PR162D_R2A_FINAL_SUMMARY", "docs/master_plan/generated/PR162D_R2A_FinalSummary.report.json"),
    InputSpec("PR162D_R2A_CANDIDATE_PACKETS", "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json"),
    InputSpec("PR162D_R2A_GENERIC_EXTENSION", "docs/master_plan/generated/PR162D_R2A_PR162RGenericCandidateInputExtension.report.json"),
    InputSpec("PR162D_R2A_FORMULATIONS", "docs/master_plan/generated/PR162D_R2A_FormulationRecordRegistry.report.json"),
    InputSpec("PR162D_R2A_FORMULAS", "docs/master_plan/generated/PR162D_R2A_FormulaExpressionRegistry.report.json"),
    InputSpec("PR162D_R2A_ALGORITHMS", "docs/master_plan/generated/PR162D_R2A_AlgorithmProcedureRegistry.report.json"),
    InputSpec("PR162D_R2A_QUANTUM", "docs/master_plan/generated/PR162D_R2A_QuantumObjectiveRegistry.report.json"),
    InputSpec("PR162D_R2A_COMPARATORS", "docs/master_plan/generated/PR162D_R2A_ClassicalComparatorRegistry.report.json"),
    InputSpec("PR162D_R2A_TEST_VECTORS", "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json"),
    InputSpec("PR162D_R2A_TRACEABILITY", "docs/master_plan/generated/PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json"),
    InputSpec("PR162D_R2A_ORCHESTRATION", "docs/master_plan/generated/PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json"),
    InputSpec("PR162D_R2A_COVERAGE", "docs/master_plan/generated/PR162D_R2A_FormulationCoverageAudit.report.json"),
    InputSpec("PR162D_R2A_LATENCY", "docs/master_plan/generated/PR162D_R2A_FormulaLatencyClassRegistry.report.json"),
    InputSpec("PR162D_R2A_HOTPATH", "docs/master_plan/generated/PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json"),
    InputSpec("PR162D_R2A_PLUGIN_SEED", "docs/master_plan/generated/PR162D_R2A_PR162EPluginSeedCandidateRegistry.report.json"),
)


def discover_inputs(repo_root: Path) -> list[DiscoveredInput]:
    rows: list[DiscoveredInput] = []
    for spec in REQUIRED_INPUT_SPECS:
        consumed_path = _first_existing(repo_root, (spec.path, *spec.fallback_paths))
        requested = repo_root / spec.path
        fallback_lineage = []
        exact_note = None
        if consumed_path is None:
            exact_note = f"missing required input path: {spec.path}"
            present = False
        else:
            present = requested.exists()
            if Path(consumed_path).as_posix() != Path(spec.path).as_posix():
                fallback_lineage = [Path(consumed_path).as_posix()]
                exact_note = f"requested path missing: {spec.path}; fallback lineage used: {consumed_path}"
        count, shape = _count_and_shape(repo_root / consumed_path) if consumed_path else (0, "MISSING")
        rows.append(
            DiscoveredInput(
                input_id=spec.input_id,
                requested_path=spec.path,
                present_flag=present,
                consumed_path=consumed_path,
                fallback_lineage_used=fallback_lineage,
                exact_missing_input_note=exact_note,
                record_count=count,
                top_level_shape=shape,
            )
        )
    return rows


def discovery_records(rows: list[DiscoveredInput]) -> list[dict[str, Any]]:
    return [
        {
            "input_id": row.input_id,
            "requested_path": row.requested_path,
            "present_flag": row.present_flag,
            "consumed_path": row.consumed_path,
            "fallback_lineage_used": row.fallback_lineage_used,
            "exact_missing_input_note": row.exact_missing_input_note,
            "record_count": row.record_count,
            "top_level_shape": row.top_level_shape,
            "consumed_before_report_pass_flag": row.consumed_path is not None,
        }
        for row in rows
    ]


def load_payload(repo_root: Path, relative_path: str) -> Any:
    return read_json(repo_root / relative_path)


def _first_existing(repo_root: Path, paths: tuple[str, ...]) -> str | None:
    for candidate in paths:
        if (repo_root / candidate).exists():
            return candidate
    return None


def _count_and_shape(path: Path) -> tuple[int, str]:
    if path.suffix.lower() != ".json":
        return (1 if path.exists() else 0), "TEXT_FILE"
    payload = read_json(path)
    if isinstance(payload, dict):
        if "records" in payload:
            return len(records_from_payload(payload)), "JSON_OBJECT_WITH_RECORDS"
        return len(payload), "JSON_OBJECT"
    if isinstance(payload, list):
        return len(payload), "JSON_ARRAY"
    return 0, type(payload).__name__.upper()
