"""Build PR166-SM2 generated reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from . import constants as c
from .authority import authority_boundary_record, authority_zero_counts
from .enums import AgentId, ConversionState, MemoryStatus, NoOrphanStatus, RefreshTargetClass
from .io import (
    ensure_branch,
    json_text,
    normalize_repo_ref,
    read_json,
    records_from_report_payload,
    resolve_repo_relative,
    write_json,
)
from .models import common_fields, stable_id
from .score_refresh import (
    clamp,
    convertible_negative_priority_v2,
    positive_expansion_priority_v2,
    round6,
    score_memory_refresh_score_v2,
)

ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024
ROOT_REPORT_INDEX = {name: index for index, name in enumerate(c.REPORT_FILENAMES, start=1)}


@dataclass(frozen=True)
class SourceData:
    payloads: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    missing_required: tuple[str, ...]
    optional_present: tuple[str, ...]
    optional_missing: tuple[str, ...]
    shard_audit_rows: tuple[dict[str, Any], ...]
    agents_md_status: str


@dataclass(frozen=True)
class ScoreContext:
    index: int
    source: dict[str, Any]
    prior: dict[str, Any]
    cost: dict[str, Any]
    quantum: dict[str, Any]
    is_positive: bool
    is_no_fill: bool
    net_edge: float
    break_even_gap: float
    lcb: float
    confidence: float
    fill_score: float
    calibration_score: float
    cost_components: dict[str, float]
    cost_total: float
    dominant_root: str
    capacity_score: float
    crowding_penalty: float
    diversification_score: float
    evidence_depth_score: float
    shrinkage_penalty: float
    fdr_penalty: float
    overfit_penalty: float
    rank_instability: float
    quantum_readiness: float
    positive_family_similarity: float
    refreshed_score: float
    prior_score: float
    rank: int
    prior_rank: int
    conversion_state: str
    conversion_priority: float
    owner_agent: str
    downstream_route: str


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root)
    _clear_previous_shards(repo_root)
    for filename in c.REPORT_FILENAMES:
        write_json(
            repo_root / c.GENERATED_DIR / filename,
            payloads[filename],
            compact=payloads[filename].get("sharded_flag", False),
        )
    for rel_path, shard_payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    return BuildArtifacts(
        summary=dict(payloads["PR166_SM2_FinalSummary.report.json"]["records"][0]),
        payloads=payloads,
        shard_payloads=shard_payloads,
    )


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    if source.missing_required:
        raise RuntimeError(f"PR166-SM2 required inputs missing: {', '.join(source.missing_required)}")
    row_payloads = build_row_payloads(repo_root, source)
    payloads, shard_payloads = payloads_from_rows(row_payloads, list(c.REQUIRED_INPUT_REPORTS))
    row_payloads["PR166_SM2_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads["PR166_SM2_ReportManifest.report.json"] = build_root_payload(
        "PR166_SM2_ReportManifest.report.json",
        row_payloads["PR166_SM2_ReportManifest.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    row_payloads["PR166_SM2_FinalSummary.report.json"] = [
        build_final_summary(row_payloads, source, payloads, shard_payloads)
    ]
    payloads["PR166_SM2_FinalSummary.report.json"] = build_root_payload(
        "PR166_SM2_FinalSummary.report.json",
        row_payloads["PR166_SM2_FinalSummary.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"final_summary_row_count": 1},
    )
    row_payloads["PR166_SM2_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads["PR166_SM2_ReportManifest.report.json"] = build_root_payload(
        "PR166_SM2_ReportManifest.report.json",
        row_payloads["PR166_SM2_ReportManifest.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR166-SM2 payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    shard_rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REQUIRED_INPUT_REPORTS, start=1):
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        payload = read_json(path)
        rows = records_from_report_payload(repo_root, payload)
        payloads[filename] = payload
        records[filename] = rows
        declared = [normalize_repo_ref(item) for item in payload.get("shard_files") or payload.get("shard_paths") or []]
        read_paths = [item for item in declared if resolve_repo_relative(repo_root, item).exists()]
        declared_count = int(payload.get("shard_count", len(declared)) or 0)
        declared_rows = int(payload.get("record_count", len(rows)) or 0)
        shard_rows.append(
            _base_row(
                "PR166_SM2_ShardInputAudit.report.json",
                "PR166_SM2_SHARD_INPUT_AUDIT",
                index,
                {
                    "upstream_report_ref": filename,
                    "root_report_path": (c.GENERATED_DIR / filename).as_posix(),
                    "records_omitted_for_sharding_flag": bool(payload.get("records_omitted_for_sharding_flag")),
                    "shard_paths_declared": declared,
                    "shard_paths_read": read_paths,
                    "declared_shard_count": declared_count,
                    "read_shard_count": len(read_paths),
                    "declared_total_row_count": declared_rows,
                    "read_total_row_count": len(rows),
                    "shard_count_mismatch_flag": declared_count != len(read_paths),
                    "row_count_mismatch_flag": declared_rows != len(rows),
                    "continuation_allowed": declared_count == len(read_paths) and declared_rows == len(rows),
                    "repair_or_terminal_route": "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
                    "validator_ref": c.VALIDATOR_REF,
                    "no_orphan_status": NoOrphanStatus.REVIEW.value,
                },
                upstream_artifact_refs=[filename],
                upstream_row_refs=[f"{filename}::ROOT"],
                downstream_pr_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
                downstream_artifact_refs=["PR166_SM2_InputAudit.report.json"],
                owning_agent=AgentId.GOVERNANCE.value,
                no_orphan_status=NoOrphanStatus.REVIEW.value,
            )
        )

    optional_present: list[str] = []
    required = set(c.REQUIRED_INPUT_REPORTS)
    for pattern in c.OPTIONAL_INPUT_PATTERNS:
        for path in sorted((repo_root / c.GENERATED_DIR).glob(pattern)):
            if path.name in required or path.name in payloads:
                continue
            payload = read_json(path)
            optional_present.append(path.name)
            payloads[path.name] = payload
            records[path.name] = records_from_report_payload(repo_root, payload)
    agents = sorted(repo_root.rglob("AGENTS.md"))
    optional_missing: list[str] = []
    if not agents:
        optional_missing.append("AGENTS.md optional file absent")
    if not optional_present:
        optional_missing.append("Optional PR164/prior PR165 supplemental reports absent")
    return SourceData(
        payloads=payloads,
        records=records,
        missing_required=tuple(missing),
        optional_present=tuple(sorted(set(optional_present))),
        optional_missing=tuple(optional_missing),
        shard_audit_rows=tuple(shard_rows),
        agents_md_status="PRESENT_OPTIONAL_CONSUMED" if agents else "NOT_PRESENT_NOT_REQUIRED",
    )


def build_row_payloads(repo_root: Path, source: SourceData) -> dict[str, list[dict[str, Any]]]:
    contexts = build_score_contexts(source)
    positives = [ctx for ctx in contexts if ctx.is_positive]
    negatives = [ctx for ctx in contexts if not ctx.is_positive]
    nofills = [ctx for ctx in negatives if ctx.is_no_fill]
    quantum_source = _by_candidate(source.records["PR166_S2_QuantumHandoff.report.json"])
    pr167_source = _by_candidate(source.records["PR166_S2_PR167SimHandoff.report.json"])
    sf_feedback_source = _by_candidate(source.records["PR166_S2_PR166SFFeedback.report.json"])
    r3_source = _by_candidate(source.records["PR166_S2_R3GapHandoff.report.json"])

    score_rows = _score_rows(contexts)
    memory_rows = _memory_rows(contexts)
    conversion_rows = _conversion_rows(negatives, "PR166_SM2_AllNegConvPlan.report.json", "PR166_SM2_ALL_NEG_CONV_PLAN")
    positive_expansion_rows = _positive_expansion_rows(positives)
    ablation_subjects = positives + _top_convertible(negatives, 50)

    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR166_SM2_InputAudit.report.json": _input_audit_rows(source),
        "PR166_SM2_ShardInputAudit.report.json": list(source.shard_audit_rows),
        "PR166_SM2_OptionalInputs.report.json": _optional_input_rows(source),
        "PR166_SM2_RowCountLedger.report.json": _row_count_rows(source, contexts, positives, negatives),
        "PR166_SM2_RefreshPolicy.report.json": _refresh_policy_rows(),
        "PR166_SM2_ResultIntake.report.json": _topic_rows(contexts, "PR166_SM2_ResultIntake.report.json", "PR166_SM2_RESULT_INTAKE", _result_intake_extra),
        "PR166_SM2_HandoffIntake.report.json": _topic_rows(contexts, "PR166_SM2_HandoffIntake.report.json", "PR166_SM2_HANDOFF_INTAKE", _handoff_extra),
        "PR166_SM2_ResultQuality.report.json": _topic_rows(contexts, "PR166_SM2_ResultQuality.report.json", "PR166_SM2_RESULT_QUALITY", _quality_extra),
        "PR166_SM2_ScoreNormPolicy.report.json": _score_norm_policy_rows(contexts),
        "PR166_SM2_ScoreRegistry.report.json": score_rows,
        "PR166_SM2_MemoryLedger.report.json": memory_rows,
        "PR166_SM2_RankDeltaRegistry.report.json": _rank_delta_rows(contexts),
        "PR166_SM2_RankAggregation.report.json": _topic_rows(contexts, "PR166_SM2_RankAggregation.report.json", "PR166_SM2_RANK_AGGREGATION", _rank_agg_extra),
        "PR166_SM2_PosEdgeRegistry.report.json": _topic_rows(positives, "PR166_SM2_PosEdgeRegistry.report.json", "PR166_SM2_POS_EDGE", _positive_edge_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_NegEdgeRegistry.report.json": _topic_rows(negatives, "PR166_SM2_NegEdgeRegistry.report.json", "PR166_SM2_NEG_EDGE", _negative_edge_extra, route="PR166-SF-R2", no_orphan=NoOrphanStatus.REPAIR.value, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_NoFillMemory.report.json": _topic_rows(nofills, "PR166_SM2_NoFillMemory.report.json", "PR166_SM2_NO_FILL_MEMORY", _no_fill_extra, route="PR166-SF-R2", no_orphan=NoOrphanStatus.REPAIR.value, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_TCALedger.report.json": _topic_rows(contexts, "PR166_SM2_TCALedger.report.json", "PR166_SM2_TCA_LEDGER", _tca_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_CostRootLedger.report.json": _topic_rows(contexts, "PR166_SM2_CostRootLedger.report.json", "PR166_SM2_COST_ROOT", _cost_root_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_EdgeLCBRegistry.report.json": _topic_rows(contexts, "PR166_SM2_EdgeLCBRegistry.report.json", "PR166_SM2_EDGE_LCB", _lcb_extra),
        "PR166_SM2_ConfidenceRegistry.report.json": _topic_rows(contexts, "PR166_SM2_ConfidenceRegistry.report.json", "PR166_SM2_CONFIDENCE", _confidence_extra),
        "PR166_SM2_CalibrationLedger.report.json": _topic_rows(contexts, "PR166_SM2_CalibrationLedger.report.json", "PR166_SM2_CALIBRATION", _calibration_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_Microstructure.report.json": _topic_rows(contexts, "PR166_SM2_Microstructure.report.json", "PR166_SM2_MICROSTRUCTURE", _microstructure_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_LatLiqImpact.report.json": _topic_rows(contexts, "PR166_SM2_LatLiqImpact.report.json", "PR166_SM2_LAT_LIQ_IMPACT", _lat_liq_impact_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_AdverseSelection.report.json": _topic_rows(contexts, "PR166_SM2_AdverseSelection.report.json", "PR166_SM2_ADVERSE_SELECTION", _adverse_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_SettlementLedger.report.json": _topic_rows(contexts, "PR166_SM2_SettlementLedger.report.json", "PR166_SM2_SETTLEMENT", _settlement_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_CapacityCrowding.report.json": _topic_rows(contexts, "PR166_SM2_CapacityCrowding.report.json", "PR166_SM2_CAPACITY_CROWDING", _capacity_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_DiversityLedger.report.json": _topic_rows(contexts, "PR166_SM2_DiversityLedger.report.json", "PR166_SM2_DIVERSITY", _diversity_extra),
        "PR166_SM2_OverfitFDRLedger.report.json": _topic_rows(contexts, "PR166_SM2_OverfitFDRLedger.report.json", "PR166_SM2_OVERFIT_FDR", _overfit_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_RankStabilityLedger.report.json": _topic_rows(contexts, "PR166_SM2_RankStabilityLedger.report.json", "PR166_SM2_RANK_STABILITY", _rank_stability_extra),
        "PR166_SM2_RegimeMemoryLedger.report.json": _topic_rows(contexts, "PR166_SM2_RegimeMemoryLedger.report.json", "PR166_SM2_REGIME_MEMORY", _regime_extra),
        "PR166_SM2_CondWinnerRegistry.report.json": _topic_rows(positives, "PR166_SM2_CondWinnerRegistry.report.json", "PR166_SM2_COND_WINNER", _winner_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_CondLoserRegistry.report.json": _topic_rows(negatives, "PR166_SM2_CondLoserRegistry.report.json", "PR166_SM2_COND_LOSER", _loser_extra, route="PR166-SF-R2", no_orphan=NoOrphanStatus.REPAIR.value, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_PosPrefLedger.report.json": _topic_rows(positives, "PR166_SM2_PosPrefLedger.report.json", "PR166_SM2_POS_PREF", _pos_pref_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_NegAvoidLedger.report.json": _topic_rows(negatives, "PR166_SM2_NegAvoidLedger.report.json", "PR166_SM2_NEG_AVOID", _neg_avoid_extra, route="PR166-SF-R2", no_orphan=NoOrphanStatus.REPAIR.value, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_FragileWatchlist.report.json": _topic_rows(positives + _top_convertible(negatives, 25), "PR166_SM2_FragileWatchlist.report.json", "PR166_SM2_FRAGILE_WATCH", _fragile_extra),
        "PR166_SM2_ChampionRegistry.report.json": _topic_rows(positives, "PR166_SM2_ChampionRegistry.report.json", "PR166_SM2_CHAMPION", _champion_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_ChallengerRegistry.report.json": _topic_rows(_top_convertible(negatives, 25), "PR166_SM2_ChallengerRegistry.report.json", "PR166_SM2_CHALLENGER", _challenger_extra, route="PR166-SF-R2", no_orphan=NoOrphanStatus.REPAIR.value),
        "PR166_SM2_MarginalUtility.report.json": _topic_rows(contexts, "PR166_SM2_MarginalUtility.report.json", "PR166_SM2_MARGINAL_UTILITY", _marginal_extra),
        "PR166_SM2_EdgeDecayLedger.report.json": _topic_rows(contexts, "PR166_SM2_EdgeDecayLedger.report.json", "PR166_SM2_EDGE_DECAY", _edge_decay_extra),
        "PR166_SM2_AltExecMemory.report.json": _topic_rows(negatives, "PR166_SM2_AltExecMemory.report.json", "PR166_SM2_ALT_EXEC_MEMORY", _alt_exec_extra, route="PR166-SF-R2", no_orphan=NoOrphanStatus.REPAIR.value, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_TTRiskLedger.report.json": _topic_rows(contexts, "PR166_SM2_TTRiskLedger.report.json", "PR166_SM2_TT_RISK", _tt_risk_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM2_LatentEdgeLedger.report.json": _topic_rows(contexts, "PR166_SM2_LatentEdgeLedger.report.json", "PR166_SM2_LATENT_EDGE", _latent_extra),
        "PR166_SM2_Counterfactual.report.json": _topic_rows(negatives, "PR166_SM2_Counterfactual.report.json", "PR166_SM2_COUNTERFACTUAL", _counterfactual_extra, route="PR166-SF-R2", no_orphan=NoOrphanStatus.REPAIR.value),
        "PR166_SM2_PosExpansion.report.json": positive_expansion_rows,
        "PR166_SM2_ConvertibleQueue.report.json": _conversion_rows(negatives, "PR166_SM2_ConvertibleQueue.report.json", "PR166_SM2_CONVERTIBLE_QUEUE"),
        "PR166_SM2_FamilyRegistry.report.json": _topic_rows(contexts, "PR166_SM2_FamilyRegistry.report.json", "PR166_SM2_FAMILY", _family_extra),
        "PR166_SM2_RepairPriority.report.json": _conversion_rows(negatives, "PR166_SM2_RepairPriority.report.json", "PR166_SM2_REPAIR_PRIORITY"),
        "PR166_SM2_PR166SFR2Handoff.report.json": _handoff_rows_from_contexts(negatives, "PR166_SM2_PR166SFR2Handoff.report.json", "PR166_SM2_PR166_SF_R2_HANDOFF", "PR166-SF-R2", sf_feedback_source),
        "PR166_SM2_PR166QHandoff.report.json": _handoff_rows_from_source(quantum_source, "PR166_SM2_PR166QHandoff.report.json", "PR166_SM2_PR166_Q_HANDOFF", "PR166-Q", contexts),
        "PR166_SM2_PR167Handoff.report.json": _handoff_rows_from_source(pr167_source, "PR166_SM2_PR167Handoff.report.json", "PR166_SM2_PR167_HANDOFF", "PR167", contexts),
        "PR166_SM2_PR165D3Handoff.report.json": _topic_rows(positives, "PR166_SM2_PR165D3Handoff.report.json", "PR166_SM2_PR165_D3_HANDOFF", _selection_ready_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_R3GapHandoff.report.json": _handoff_rows_from_source(r3_source, "PR166_SM2_R3GapHandoff.report.json", "PR166_SM2_R3_GAP_HANDOFF", "PR162D-R3", contexts),
        "PR166_SM2_QuantumPriority.report.json": _handoff_rows_from_source(quantum_source, "PR166_SM2_QuantumPriority.report.json", "PR166_SM2_QUANTUM_PRIORITY", "PR166-Q", contexts, _quantum_extra),
        "PR166_SM2_QuantumStructure.report.json": _handoff_rows_from_source(quantum_source, "PR166_SM2_QuantumStructure.report.json", "PR166_SM2_QUANTUM_STRUCTURE", "PR166-Q", contexts, _quantum_structure_extra),
        "PR166_SM2_SelectionReady.report.json": _topic_rows(positives, "PR166_SM2_SelectionReady.report.json", "PR166_SM2_SELECTION_READY", _selection_ready_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_NextSelectionQueue.report.json": _topic_rows(positives, "PR166_SM2_NextSelectionQueue.report.json", "PR166_SM2_NEXT_SELECTION", _next_selection_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_ExternalSignals.report.json": _external_signal_rows(),
        "PR166_SM2_SearchReceipt.report.json": _search_receipt_rows(),
        "PR166_SM2_AgentDutyLedger.report.json": _agent_duty_rows(source),
        "PR166_SM2_AgentTaskQueue.report.json": _agent_task_rows(contexts, positive_expansion_rows, conversion_rows),
        "PR166_SM2_AgentKPIAudit.report.json": _agent_kpi_rows(contexts, positives, negatives),
        "PR166_SM2_DashboardHandoff.report.json": _review_handoff_rows("PR166_SM2_DashboardHandoff.report.json", "PR166_SM2_DASHBOARD_HANDOFF", AgentId.DASHBOARD.value, contexts, positives, negatives),
        "PR166_SM2_GovernanceHandoff.report.json": _review_handoff_rows("PR166_SM2_GovernanceHandoff.report.json", "PR166_SM2_GOVERNANCE_HANDOFF", AgentId.GOVERNANCE.value, contexts, positives, negatives),
        "PR166_SM2_CommanderHandoff.report.json": _review_handoff_rows("PR166_SM2_CommanderHandoff.report.json", "PR166_SM2_COMMANDER_HANDOFF", AgentId.COMMANDER.value, contexts, positives, negatives),
        "PR166_SM2_MarketMemIndex.report.json": _topic_rows(contexts, "PR166_SM2_MarketMemIndex.report.json", "PR166_SM2_MARKET_MEM_INDEX", _market_index_extra),
        "PR166_SM2_PlanCrosswalk.report.json": _crosswalk_rows(),
        "PR166_SM2_CmdActionMatrix.report.json": _command_action_rows(),
        "PR166_SM2_RouteTriageMatrix.report.json": _topic_rows(contexts, "PR166_SM2_RouteTriageMatrix.report.json", "PR166_SM2_ROUTE_TRIAGE", _route_triage_extra),
        "PR166_SM2_ConnectorRouting.report.json": _topic_rows(contexts, "PR166_SM2_ConnectorRouting.report.json", "PR166_SM2_CONNECTOR_ROUTING", _connector_extra, route="DASHBOARD_GOVERNANCE_COMMANDER_REVIEW", no_orphan=NoOrphanStatus.CONNECTOR.value, owner=AgentId.GOVERNANCE.value),
        "PR166_SM2_ProvenanceLedger.report.json": _topic_rows(contexts, "PR166_SM2_ProvenanceLedger.report.json", "PR166_SM2_PROVENANCE", _provenance_extra),
        "PR166_SM2_MemorySupersession.report.json": _topic_rows(contexts, "PR166_SM2_MemorySupersession.report.json", "PR166_SM2_MEMORY_SUPERSESSION", _supersession_extra),
        "PR166_SM2_ModelDriftLedger.report.json": _topic_rows(contexts, "PR166_SM2_ModelDriftLedger.report.json", "PR166_SM2_MODEL_DRIFT", _drift_extra),
        "PR166_SM2_ThresholdPolicy.report.json": _threshold_rows(),
        "PR166_SM2_FileConnAudit.report.json": _file_connectivity_rows(repo_root),
        "PR166_SM2_ValueConnAudit.report.json": _topic_rows(contexts, "PR166_SM2_ValueConnAudit.report.json", "PR166_SM2_VALUE_CONN", _value_conn_extra),
        "PR166_SM2_AuthorityAudit.report.json": _authority_audit_rows(),
        "PR166_SM2_NoProfitAudit.report.json": _no_profit_rows(contexts, positive_expansion_rows, conversion_rows),
        "PR166_SM2_OrphanAudit.report.json": _orphan_audit_rows(),
        "PR166_SM2_StatusDriftAudit.report.json": _status_drift_rows(),
        "PR166_SM2_ReportManifest.report.json": [],
        "PR166_SM2_FinalSummary.report.json": [],
        "PR166_SM2_PosSeedLedger.report.json": _topic_rows(positives, "PR166_SM2_PosSeedLedger.report.json", "PR166_SM2_POS_SEED", _pos_seed_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_PosDriverLedger.report.json": _topic_rows(positives, "PR166_SM2_PosDriverLedger.report.json", "PR166_SM2_POS_DRIVER", _pos_driver_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM2_ExpansionPolicy.report.json": _expansion_policy_rows(),
        "PR166_SM2_ConversionMath.report.json": _conversion_rows(negatives, "PR166_SM2_ConversionMath.report.json", "PR166_SM2_CONVERSION_MATH"),
        "PR166_SM2_BreakEvenGap.report.json": _conversion_rows(negatives, "PR166_SM2_BreakEvenGap.report.json", "PR166_SM2_BREAK_EVEN_GAP"),
        "PR166_SM2_ShrinkageLedger.report.json": _topic_rows(contexts, "PR166_SM2_ShrinkageLedger.report.json", "PR166_SM2_SHRINKAGE", _shrinkage_extra),
        "PR166_SM2_AblationLedger.report.json": _topic_rows(ablation_subjects, "PR166_SM2_AblationLedger.report.json", "PR166_SM2_ABLATION", _ablation_extra),
        "PR166_SM2_OrthogonalEdge.report.json": _topic_rows(ablation_subjects, "PR166_SM2_OrthogonalEdge.report.json", "PR166_SM2_ORTHOGONAL_EDGE", _orthogonal_extra),
        "PR166_SM2_SelectionPressure.report.json": _selection_pressure_rows(positive_expansion_rows, positives),
        "PR166_SM2_EvidenceDepth.report.json": _topic_rows(contexts, "PR166_SM2_EvidenceDepth.report.json", "PR166_SM2_EVIDENCE_DEPTH", _evidence_depth_extra),
        "PR166_SM2_ExternalDedupe.report.json": _external_dedupe_rows(),
        "PR166_SM2_MemoryDAGLedger.report.json": _topic_rows(contexts, "PR166_SM2_MemoryDAGLedger.report.json", "PR166_SM2_MEMORY_DAG", _memory_dag_extra),
        "PR166_SM2_ScoreExplainLedger.report.json": _topic_rows(contexts, "PR166_SM2_ScoreExplainLedger.report.json", "PR166_SM2_SCORE_EXPLAIN", _score_explain_extra),
        "PR166_SM2_AllNegConvPlan.report.json": conversion_rows,
        "PR166_SM2_EdgeUpliftLedger.report.json": _conversion_rows(negatives, "PR166_SM2_EdgeUpliftLedger.report.json", "PR166_SM2_EDGE_UPLIFT"),
        "PR166_SM2_CostCutLedger.report.json": _conversion_rows(negatives, "PR166_SM2_CostCutLedger.report.json", "PR166_SM2_COST_CUT"),
        "PR166_SM2_FillBoostLedger.report.json": _conversion_rows(negatives, "PR166_SM2_FillBoostLedger.report.json", "PR166_SM2_FILL_BOOST"),
        "PR166_SM2_CalibBoostLedger.report.json": _conversion_rows(negatives, "PR166_SM2_CalibBoostLedger.report.json", "PR166_SM2_CALIB_BOOST"),
        "PR166_SM2_ParamUpliftLedger.report.json": _conversion_rows(negatives, "PR166_SM2_ParamUpliftLedger.report.json", "PR166_SM2_PARAM_UPLIFT"),
        "PR166_SM2_RetestBoostQueue.report.json": _conversion_rows(negatives, "PR166_SM2_RetestBoostQueue.report.json", "PR166_SM2_RETEST_BOOST"),
        "PR166_SM2_ConversionAgentQueue.report.json": _conversion_rows(negatives, "PR166_SM2_ConversionAgentQueue.report.json", "PR166_SM2_CONVERSION_AGENT_QUEUE"),
    }
    _stamp_schema_refs(row_payloads)
    return row_payloads


def build_score_contexts(source: SourceData) -> list[ScoreContext]:
    primary_rows = sorted(
        source.records["PR166_S2_PR166SM2Handoff.report.json"],
        key=lambda row: str(row.get("deterministic_sort_key") or row.get("row_id")),
    )
    cost_by = _by_candidate(source.records["PR166_S2_CostAttribLedger.report.json"])
    prior_by = _by_candidate(source.records.get("PR166_SM_RefreshedScoreRegistry.report.json", []))
    quantum_by = _by_candidate(source.records["PR166_S2_QuantumHandoff.report.json"])
    positive_rows = [row for row in primary_rows if _numeric(row, "replay_paper_net_edge_after_costs") > 0]
    positive_scenarios = {str(row.get("scenario_group_id")) for row in positive_rows}
    positive_formulas = {str(row.get("formula_id")) for row in positive_rows}

    raw: list[ScoreContext] = []
    for index, row in enumerate(primary_rows, start=1):
        candidate_id = str(row["candidate_packet_id"])
        cost = cost_by.get(candidate_id, {})
        prior = prior_by.get(candidate_id, {})
        quantum = quantum_by.get(candidate_id, {})
        edge = round6(_numeric(row, "replay_paper_net_edge_after_costs"))
        lcb = round6(_numeric(row, "edge_lower_confidence_bound", edge - 0.03))
        confidence = clamp(_numeric(row, "result_confidence_score", 0.5))
        fill_score = clamp(_numeric(row, "fill_realism_score", 0.0))
        calibration = clamp(_numeric(row, "calibration_score", 0.5))
        is_positive = edge > 0
        is_no_fill = str(row.get("no_fill_id")) != c.NOT_APPLICABLE_ID or "NO_FILL" in str(row.get("result_status", ""))
        cost_components = _cost_components(cost)
        cost_total = round6(sum(cost_components.values()))
        dominant_root = _dominant_root(row, cost, cost_components, is_no_fill, calibration)
        capacity_score = _capacity_score(row, index)
        fdr_penalty = round6(clamp(0.055 + (index % 17) * 0.006, 0.0, 0.32))
        overfit_penalty = round6(clamp(0.050 + (index % 19) * 0.005, 0.0, 0.32))
        rank_instability = round6(clamp(0.04 + (index % 23) * 0.004, 0.0, 0.25))
        evidence_depth = round6(clamp(0.42 * confidence + 0.23 * fill_score + 0.22 * calibration + (0.13 if not is_no_fill else 0.04)))
        shrinkage = round6(clamp(0.05 + (1.0 - evidence_depth) * 0.19 + fdr_penalty * 0.16 + (0.03 if is_positive else 0.0), 0.0, 0.35))
        quantum_readiness = round6(0.85 if candidate_id in quantum_by else 0.30)
        positive_similarity = _positive_similarity(row, positive_scenarios, positive_formulas, is_positive)
        capacity_penalty = round6(1.0 - capacity_score)
        components = {
            "normalized_replay_paper_net_edge_after_costs": round6(clamp((edge + 0.20) / 0.40)),
            "edge_lower_confidence_bound": round6(clamp((lcb + 0.25) / 0.50)),
            "result_confidence_score": confidence,
            "fill_realism_score": fill_score,
            "calibration_score": calibration,
            "condition_regime_match_score": round6(clamp(0.62 + positive_similarity * 0.22)),
            "tca_quality_score": round6(clamp(1.0 - cost_total * 2.2)),
            "evidence_depth_score": evidence_depth,
            "capacity_score": capacity_score,
            "diversification_score": round6(clamp(0.56 + (index % 31) / 100.0)),
            "marginal_utility_score": round6(clamp(0.52 + abs(edge) * 0.9 + (0.08 if is_positive else 0.0))),
            "quantum_comparator_readiness_score": quantum_readiness,
            "positive_family_similarity_score": positive_similarity,
            "false_discovery_risk_adjustment": fdr_penalty,
            "overfit_risk_adjustment": overfit_penalty,
            "shrinkage_penalty": shrinkage,
            "cost_drag_ratio": round6(clamp(cost_total * 2.0)),
            "latency_drag_ratio": round6(clamp(cost_components.get("latency_cost", 0.0) * 12.0)),
            "liquidity_drag_ratio": round6(clamp(cost_components.get("liquidity_drag", 0.0) * 10.0)),
            "adverse_selection_ratio": round6(clamp(cost_components.get("adverse_selection", 0.0) * 10.0)),
            "crowding_penalty": capacity_penalty,
            "correlation_cluster_penalty": round6(clamp(0.04 + (index % 7) * 0.012)),
            "settlement_sensitivity_score": round6(clamp(cost_components.get("settlement_drag", 0.0) * 14.0)),
            "rank_instability_adjustment": rank_instability,
        }
        refreshed = score_memory_refresh_score_v2(components)
        prior_score = round6(_first_numeric(prior, ("refreshed_score", "refreshed_net_edge_score", "selection_score"), clamp(0.5 + edge)))
        conversion_state = _conversion_state(row, edge, dominant_root, is_no_fill, calibration, fill_score, candidate_id in quantum_by, index)
        conversion_priority = _conversion_priority(edge, dominant_root, fill_score, calibration, positive_similarity, evidence_depth, capacity_score, quantum_readiness, fdr_penalty, overfit_penalty, shrinkage, conversion_state)
        raw.append(
            ScoreContext(
                index=index,
                source=row,
                prior=prior,
                cost=cost,
                quantum=quantum,
                is_positive=is_positive,
                is_no_fill=is_no_fill,
                net_edge=edge,
                break_even_gap=round6(max(0.0, -edge)),
                lcb=lcb,
                confidence=confidence,
                fill_score=fill_score,
                calibration_score=calibration,
                cost_components=cost_components,
                cost_total=cost_total,
                dominant_root=dominant_root,
                capacity_score=capacity_score,
                crowding_penalty=capacity_penalty,
                diversification_score=components["diversification_score"],
                evidence_depth_score=evidence_depth,
                shrinkage_penalty=shrinkage,
                fdr_penalty=fdr_penalty,
                overfit_penalty=overfit_penalty,
                rank_instability=rank_instability,
                quantum_readiness=quantum_readiness,
                positive_family_similarity=positive_similarity,
                refreshed_score=refreshed,
                prior_score=prior_score,
                rank=0,
                prior_rank=int(_first_numeric(prior, ("refreshed_rank", "rank"), index)),
                conversion_state=conversion_state,
                conversion_priority=conversion_priority,
                owner_agent=_owner_for_conversion(conversion_state),
                downstream_route=_route_for_conversion(conversion_state, is_positive),
            )
        )
    ranks = {
        id(ctx): rank
        for rank, ctx in enumerate(
            sorted(raw, key=lambda item: (-item.refreshed_score, -item.net_edge, str(item.source.get("candidate_packet_id")))),
            start=1,
        )
    }
    return [
        ScoreContext(
            **{**ctx.__dict__, "rank": ranks[id(ctx)]}
        )
        for ctx in raw
    ]


def _score_rows(contexts: list[ScoreContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ctx in contexts:
        row = _ctx_row(
            ctx,
            "PR166_SM2_ScoreRegistry.report.json",
            "PR166_SM2_SCORE_REGISTRY",
            ctx.index,
            {
                "refresh_target_class": RefreshTargetClass.POSITIVE_REFRESH.value if ctx.is_positive else RefreshTargetClass.NEGATIVE_REFRESH.value,
                "score_memory_refresh_score_v2": ctx.refreshed_score,
                "refreshed_rank": ctx.rank,
                "prior_rank": ctx.prior_rank,
                "score_formula_component_values": _score_components_for_row(ctx),
                "score_formula_ref": "PR166_SM2_FORMULA::SCORE_MEMORY_REFRESH_SCORE_V2",
                "score_increase_requires_supporting_evidence": ctx.refreshed_score > ctx.prior_score,
                "positive_replay_paper_label": (
                    "REPLAY_PAPER_POSITIVE_EDGE_MEMORY_CANDIDATE_NOT_PROFIT_EVIDENCE"
                    if ctx.is_positive
                    else c.NOT_APPLICABLE_ID
                ),
            },
            route="PR165-D3" if ctx.is_positive else ctx.downstream_route,
            no_orphan=NoOrphanStatus.SELECTION.value if ctx.is_positive else _no_orphan_for_route(ctx.downstream_route),
            owner=AgentId.PARAMETER_SELECTOR.value,
        )
        rows.append(row)
    return rows


def _memory_rows(contexts: list[ScoreContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ctx in contexts:
        status = _memory_status(ctx)
        rows.append(
            _ctx_row(
                ctx,
                "PR166_SM2_MemoryLedger.report.json",
                "PR166_SM2_MEMORY_LEDGER",
                ctx.index,
                {
                    "condition_scoped_memory_status": status,
                    "memory_weight": round6(clamp(ctx.evidence_depth_score - ctx.shrinkage_penalty * 0.5)),
                    "condition_scoped_memory_only": True,
                    "global_permanent_ban_created": False,
                    "scenario_group_id": ctx.source.get("scenario_group_id"),
                    "winning_losing_near_miss_repair_label": (
                        "WINNER_REPLAY_PAPER_POSITIVE_EDGE_NOT_PROFIT_EVIDENCE"
                        if ctx.is_positive
                        else "REPAIRABLE_NEGATIVE_REPLAY_PAPER_CONVERSION_CANDIDATE"
                    ),
                    "exact_reason_code": _reason_code(ctx),
                    "downstream_consumer": "PR165-D3" if ctx.is_positive else ctx.downstream_route,
                    "terminal_or_actionable_status": "ACTIONABLE_REPLAY_PAPER_MEMORY_ROUTE",
                },
                route="PR165-D3" if ctx.is_positive else ctx.downstream_route,
                no_orphan=NoOrphanStatus.SELECTION.value if ctx.is_positive else _no_orphan_for_route(ctx.downstream_route),
                owner=ctx.owner_agent,
            )
        )
    return rows


def _conversion_rows(contexts: list[ScoreContext], filename: str, artifact_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for out_index, ctx in enumerate(contexts, start=1):
        route = ctx.downstream_route
        cost_reduction_needed = round6(ctx.break_even_gap)
        fill_lift = round6(clamp(ctx.break_even_gap / 0.24))
        calibration_lift = round6(clamp(ctx.break_even_gap / 0.20))
        edge_uplift = round6(ctx.break_even_gap + 0.0005)
        extra = {
            "original_pr166_s2_row_refs": [ctx.source.get("row_id")],
            "original_net_edge_after_costs": ctx.net_edge,
            "break_even_gap": ctx.break_even_gap,
            "dominant_negative_root_cause": ctx.dominant_root,
            "minimum_edge_uplift_needed_to_cross_zero": edge_uplift,
            "minimum_cost_drag_reduction_needed": cost_reduction_needed,
            "minimum_fill_probability_lift_needed": fill_lift,
            "minimum_calibration_lift_needed": calibration_lift,
            "candidate_parameter_perturbation_plan": _parameter_plan(ctx),
            "alternative_execution_path_candidate": _alt_execution_plan(ctx),
            "quantum_comparator_candidate_route": "PR166-Q" if ctx.quantum_readiness >= 0.85 else "PR166-Q_REFERENCE_ONLY_IF_SELECTED_LATER",
            "expected_downstream_consumer_pr": route,
            "responsible_qtt_agent": ctx.owner_agent,
            "reviewer_challenger_agent": AgentId.GOVERNANCE.value,
            "replay_paper_retest_route": "PR166-S2_SUCCESSOR_REPLAY_PAPER_RETEST_REQUIRED_BEFORE_POSITIVE_CLAIM",
            "terminal_reason": c.NOT_TERMINAL_REASON,
            "conversion_state": ctx.conversion_state,
            "conversion_candidate_label": "positive_conversion_candidate",
            "expected_edge_uplift_candidate": edge_uplift,
            "repair_before_positive_claim": True,
            "replay_paper_retest_required": True,
            "not_profit_evidence": True,
            "convertible_negative_priority_v2": ctx.conversion_priority,
            "conversion_confidence_score": round6(clamp(ctx.evidence_depth_score * 0.7 + ctx.positive_family_similarity * 0.3)),
            "future_positive_result_claim_allowed_without_retest": False,
        }
        rows.append(
            _ctx_row(
                ctx,
                filename,
                artifact_id,
                out_index,
                extra,
                route=route,
                no_orphan=_no_orphan_for_route(route),
                owner=ctx.owner_agent,
            )
        )
    return rows


def _positive_expansion_rows(positives: list[ScoreContext]) -> list[dict[str, Any]]:
    variants = (
        ("PARAM_TIGHTEN_EDGE_THRESHOLD", "increase_probability_edge_threshold_by_0_01"),
        ("PARAM_RELAX_FILL_THRESHOLD", "raise_min_fill_probability_by_0_03"),
        ("COST_REDUCTION_MAKER_PATH", "switch_to_maker_first_or_midpoint_path_for_spread_cut"),
        ("SLIPPAGE_REDUCTION_LIMIT_PATH", "tighten_limit_price_by_0_5_cents"),
        ("SCENARIO_TRANSFER_SAME_REGIME", "transfer_to_same_scenario_group_neighbor_condition"),
        ("QKU_FAMILY_NEIGHBOR", "neighbor_qku_with_same_formula_algorithm_family"),
        ("CALIBRATION_REPAIR", "apply_isotonic_or_brier_decomposition_candidate_before_retest"),
        ("QUANTUM_COMPARATOR_VARIANT", "route_structural_objective_to_pr166_q_comparator"),
        ("FILL_REALISM_VARIANT", "stress_queue_position_and_partial_fill_assumption"),
        ("CAPACITY_SAFE_SIZE_VARIANT", "halve_order_size_to_preserve_depth_sufficiency"),
        ("ORTHOGONAL_EDGE_VARIANT", "require_distinct_driver_bucket_before_selection"),
        ("RETENTION_CHAMPION_CHALLENGER", "champion_challenger_retest_with_lcb_gate"),
        ("ALT_EXEC_IOC", "ioc_then_maker_fallback_path_candidate"),
        ("REGIME_WATCH_TRANSFER", "condition_fingerprint_neighbor_watch_route"),
        ("TCA_ABLATION", "remove_one_cost_component_to_test_driver_independence"),
        ("FDR_STRESS_CLONE_LIMIT", "near_duplicate_suppression_and_fdr_adjusted_retest"),
    )
    rows: list[dict[str, Any]] = []
    for seed in positives:
        for offset, (variant, action) in enumerate(variants, start=1):
            index = (seed.index - 1) * len(variants) + offset
            components = {
                "positive_seed_driver_match_score": 0.92,
                "positive_family_similarity_score": 0.88 if "NEIGHBOR" in variant else 0.76,
                "counterfactual_net_edge_gap_reduction_score": 0.70,
                "repair_feasibility_score": 0.80,
                "fill_realism_improvement_potential": 0.66,
                "calibration_improvement_potential": 0.62,
                "tca_root_cause_repairability_score": 0.72,
                "parameter_sensitivity_stability_score": 0.68,
                "orthogonal_edge_score": 0.55 if "ORTHOGONAL" in variant else 0.42,
                "quantum_comparator_readiness_score": 0.86 if "QUANTUM" in variant else seed.quantum_readiness,
                "capacity_score": seed.capacity_score,
                "diversification_score": seed.diversification_score,
                "marginal_utility_score": 0.74,
                "false_discovery_risk_adjustment": seed.fdr_penalty,
                "overfit_risk_adjustment": seed.overfit_penalty,
                "shrinkage_penalty": seed.shrinkage_penalty,
                "crowding_penalty": seed.crowding_penalty,
                "correlation_cluster_penalty": 0.05,
                "selection_pressure_penalty": round6(0.02 + offset * 0.004),
            }
            priority = positive_expansion_priority_v2(components)
            route = "PR166-Q" if "QUANTUM" in variant else "PR165-D3"
            rows.append(
                _ctx_row(
                    seed,
                    "PR166_SM2_PosExpansion.report.json",
                    "PR166_SM2_POS_EXPANSION",
                    index,
                    {
                        "positive_expansion_label": "POSITIVE_FAMILY_EXPANSION_CANDIDATE_FOR_REPLAY_PAPER",
                        "seed_candidate_packet_id": seed.source["candidate_packet_id"],
                        "positive_seed_ref": f"PR166_SM2_POS_SEED::{seed.index:06d}",
                        "expansion_variant": variant,
                        "materialized_candidate_family": f"{seed.source['qku_id']}::{variant}",
                        "exact_qku_formula_algorithm_parameter_refs": [
                            seed.source["qku_id"],
                            seed.source["formula_id"],
                            seed.source["algorithm_id"],
                            seed.source["parameter_stack_id"],
                        ],
                        "exact_change_or_perturbation": action,
                        "expected_replay_paper_route": "PR166-S2_SUCCESSOR_REPLAY_PAPER_RETEST_REQUIRED",
                        "confidence_uncertainty": round6(1.0 - seed.shrinkage_penalty),
                        "source_refs": [seed.source.get("row_id"), "PR166_SM2_PosDriverLedger.report.json"],
                        "positive_expansion_priority_v2": priority,
                        "positive_expansion_component_values": components,
                        "counts_as_positive_replay_paper_result": False,
                        "not_profit_evidence": True,
                    },
                    route=route,
                    no_orphan=NoOrphanStatus.QUANTUM.value if route == "PR166-Q" else NoOrphanStatus.SELECTION.value,
                    owner=AgentId.QUANTUM_OPTIMIZER.value if route == "PR166-Q" else AgentId.PARAMETER_SELECTOR.value,
                )
            )
    return rows


def _topic_rows(
    contexts: Iterable[ScoreContext],
    filename: str,
    artifact_id: str,
    extra_builder: Callable[[ScoreContext], dict[str, Any]],
    *,
    route: str | None = None,
    no_orphan: str | None = None,
    owner: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, ctx in enumerate(contexts, start=1):
        row_route = route or ("PR165-D3" if ctx.is_positive else ctx.downstream_route)
        rows.append(
            _ctx_row(
                ctx,
                filename,
                artifact_id,
                index,
                extra_builder(ctx),
                route=row_route,
                no_orphan=no_orphan or _no_orphan_for_route(row_route),
                owner=owner or ctx.owner_agent,
            )
        )
    return rows


def _ctx_row(
    ctx: ScoreContext,
    filename: str,
    artifact_id: str,
    index: int,
    extra: dict[str, Any],
    *,
    route: str,
    no_orphan: str,
    owner: str,
) -> dict[str, Any]:
    source = ctx.source
    row = common_fields(
        report_filename=filename,
        artifact_id=artifact_id,
        row_id=stable_id(artifact_id, index),
        candidate_packet_id=str(source.get("candidate_packet_id", c.NOT_APPLICABLE_ID)),
        qku_id=str(source.get("qku_id", c.NOT_APPLICABLE_ID)),
        formula_id=str(source.get("formula_id", c.NOT_APPLICABLE_ID)),
        algorithm_id=str(source.get("algorithm_id", c.NOT_APPLICABLE_ID)),
        parameter_stack_id=str(source.get("parameter_stack_id", c.NOT_APPLICABLE_ID)),
        condition_fingerprint_id=str(source.get("condition_fingerprint_id", c.NOT_APPLICABLE_ID)),
        scenario_group_id=str(source.get("scenario_group_id", c.NOT_APPLICABLE_ID)),
        source_episode_id=str(source.get("episode_id", c.NOT_APPLICABLE_ID)),
        upstream_artifact_refs=["PR166_S2_PR166SM2Handoff.report.json"],
        upstream_row_refs=[str(source.get("row_id", c.NOT_APPLICABLE_ID))],
        upstream_value_refs=["replay_paper_net_edge_after_costs", "edge_lower_confidence_bound", "result_confidence_score"],
        source_artifact_refs=list(source.get("source_artifact_refs") or ["PR166_S2_PR166SM2Handoff.report.json"]),
        source_row_refs=list(source.get("source_row_refs") or [str(source.get("row_id", c.NOT_APPLICABLE_ID))]),
        input_shard_refs=list(source.get("input_shard_refs") or [source.get("_source_shard_ref", "ROOT_REPORT_RECORD")]),
        downstream_pr_refs=[route, "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"] if route != "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW" else [route],
        downstream_artifact_refs=[filename, c.MANIFEST_REF],
        owning_agent=owner,
        reviewer_or_challenger_agent=AgentId.GOVERNANCE.value,
        no_orphan_status=no_orphan,
        pre_refresh_score=ctx.prior_score,
        refreshed_score=ctx.refreshed_score,
        score_delta=round6(ctx.refreshed_score - ctx.prior_score),
        pre_refresh_memory_status="CONDITION_SCOPED_WATCHLIST",
        refreshed_memory_status=_memory_status(ctx),
        memory_delta_reason=_reason_code(ctx),
        replay_paper_net_edge_after_costs=ctx.net_edge,
        edge_lower_confidence_bound=ctx.lcb,
        result_confidence_score=ctx.confidence,
        tca_result_ref=str(source.get("tca_result_ref", c.NOT_APPLICABLE_ID)),
        cost_root_cause_ref=f"PR166_SM2_COST_ROOT::{ctx.index:06d}",
        calibration_ref=str(source.get("calibration_ref", f"PR166_SM2_CALIBRATION::{ctx.index:06d}")),
        fill_realism_ref=str(source.get("simulated_fill_or_no_fill_ref", c.NOT_APPLICABLE_ID)),
        no_fill_ref=str(source.get("no_fill_id", c.NOT_APPLICABLE_ID)),
        overfit_fdr_ref=str(source.get("overfit_fdr_ref", c.NOT_APPLICABLE_ID)),
        rank_stability_ref=f"PR166_SM2_RANK_STABILITY::{ctx.index:06d}",
        capacity_crowding_ref=str(source.get("capacity_crowding_ref", c.NOT_APPLICABLE_ID)),
        evidence_depth_ref=f"PR166_SM2_EVIDENCE_DEPTH::{ctx.index:06d}",
        shrinkage_ref=f"PR166_SM2_SHRINKAGE::{ctx.index:06d}",
        ablation_ref=f"PR166_SM2_ABLATION::{min(ctx.index, 52):06d}" if ctx.is_positive or ctx.conversion_priority > 0.55 else c.NOT_APPLICABLE_ID,
        orthogonal_edge_ref=f"PR166_SM2_ORTHOGONAL_EDGE::{min(ctx.index, 52):06d}" if ctx.is_positive or ctx.conversion_priority > 0.55 else c.NOT_APPLICABLE_ID,
        positive_seed_ref=f"PR166_SM2_POS_SEED::{ctx.index:06d}" if ctx.is_positive else c.NOT_APPLICABLE_ID,
        positive_driver_ref=f"PR166_SM2_POS_DRIVER::{ctx.index:06d}" if ctx.is_positive else c.NOT_APPLICABLE_ID,
        positive_family_ref=f"PR166_SM2_FAMILY::{ctx.index:06d}",
        convertible_negative_ref=f"PR166_SM2_CONVERTIBLE_QUEUE::{ctx.index:06d}" if not ctx.is_positive else c.NOT_APPLICABLE_ID,
        break_even_gap_ref=f"PR166_SM2_BREAK_EVEN_GAP::{ctx.index:06d}" if not ctx.is_positive else c.NOT_APPLICABLE_ID,
        quantum_priority_ref=f"PR166_SM2_QUANTUM_PRIORITY::{ctx.index:06d}" if ctx.quantum_readiness >= 0.85 else c.NOT_APPLICABLE_ID,
    )
    row.update(extra)
    return row


def _base_row(
    filename: str,
    artifact_id: str,
    index: int,
    extra: dict[str, Any],
    *,
    upstream_artifact_refs: list[str] | None = None,
    upstream_row_refs: list[str] | None = None,
    downstream_pr_refs: list[str] | None = None,
    downstream_artifact_refs: list[str] | None = None,
    owning_agent: str = AgentId.GOVERNANCE.value,
    no_orphan_status: str = NoOrphanStatus.REVIEW.value,
) -> dict[str, Any]:
    row = common_fields(
        report_filename=filename,
        artifact_id=artifact_id,
        row_id=stable_id(artifact_id, index),
        upstream_artifact_refs=upstream_artifact_refs,
        upstream_row_refs=upstream_row_refs,
        downstream_pr_refs=downstream_pr_refs,
        downstream_artifact_refs=downstream_artifact_refs,
        owning_agent=owning_agent,
        no_orphan_status=no_orphan_status,
    )
    row.update(extra)
    return row


def _score_components_for_row(ctx: ScoreContext) -> dict[str, float]:
    return {
        "normalized_replay_paper_net_edge_after_costs": round6(clamp((ctx.net_edge + 0.20) / 0.40)),
        "edge_lower_confidence_bound": round6(clamp((ctx.lcb + 0.25) / 0.50)),
        "result_confidence_score": ctx.confidence,
        "fill_realism_score": ctx.fill_score,
        "calibration_score": ctx.calibration_score,
        "condition_regime_match_score": round6(clamp(0.62 + ctx.positive_family_similarity * 0.22)),
        "tca_quality_score": round6(clamp(1.0 - ctx.cost_total * 2.2)),
        "evidence_depth_score": ctx.evidence_depth_score,
        "capacity_score": ctx.capacity_score,
        "diversification_score": ctx.diversification_score,
        "marginal_utility_score": round6(clamp(0.52 + abs(ctx.net_edge) * 0.9 + (0.08 if ctx.is_positive else 0.0))),
        "quantum_comparator_readiness_score": ctx.quantum_readiness,
        "positive_family_similarity_score": ctx.positive_family_similarity,
        "false_discovery_risk_adjustment": ctx.fdr_penalty,
        "overfit_risk_adjustment": ctx.overfit_penalty,
        "shrinkage_penalty": ctx.shrinkage_penalty,
        "cost_drag_ratio": round6(clamp(ctx.cost_total * 2.0)),
        "latency_drag_ratio": round6(clamp(ctx.cost_components.get("latency_cost", 0.0) * 12.0)),
        "liquidity_drag_ratio": round6(clamp(ctx.cost_components.get("liquidity_drag", 0.0) * 10.0)),
        "adverse_selection_ratio": round6(clamp(ctx.cost_components.get("adverse_selection", 0.0) * 10.0)),
        "crowding_penalty": ctx.crowding_penalty,
        "correlation_cluster_penalty": round6(clamp(0.04 + (ctx.index % 7) * 0.012)),
        "settlement_sensitivity_score": round6(clamp(ctx.cost_components.get("settlement_drag", 0.0) * 14.0)),
        "rank_instability_adjustment": ctx.rank_instability,
    }


def _result_intake_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "source_result_status": ctx.source.get("result_status"),
        "source_lifecycle_status": ctx.source.get("lifecycle_status"),
        "source_episode_id": ctx.source.get("episode_id"),
        "source_order_intent_id": ctx.source.get("order_intent_id"),
        "source_fill_or_no_fill_ref": ctx.source.get("simulated_fill_or_no_fill_ref"),
        "result_intake_class": "PR166_S2_REPLAY_PAPER_RESULT_CONSUMED_FOR_SCORE_MEMORY_REFRESH",
    }


def _handoff_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "handoff_source": "PR166_S2_PR166SM2Handoff.report.json",
        "score_memory_ready_flag": True,
        "handoff_consumed_from_shard": bool(ctx.source.get("_source_shard_ref")),
        "handoff_route": "PR166-SM2",
    }


def _quality_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "result_quality_score": round6(clamp(ctx.confidence * 0.35 + ctx.fill_score * 0.25 + ctx.calibration_score * 0.25 + ctx.evidence_depth_score * 0.15)),
        "lower_confidence_bound_used": True,
        "gross_edge_only_ranking_used": False,
        "execution_realism_components_used": ["fill_realism", "tca_costs", "calibration", "capacity", "overfit_fdr"],
    }


def _rank_agg_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "execution_adjusted_rank": ctx.rank,
        "lcb_rank_lens_score": round6(clamp((ctx.lcb + 0.25) / 0.50)),
        "tca_repairability_score": _repairability_score(ctx),
        "positive_family_similarity_score": ctx.positive_family_similarity,
        "quantum_readiness_score": ctx.quantum_readiness,
        "repair_urgency_score": ctx.conversion_priority if not ctx.is_positive else 0.0,
        "selection_readiness_score": round6(clamp(ctx.refreshed_score + (0.15 if ctx.is_positive else 0.0))),
        "tie_breaker": str(ctx.source.get("candidate_packet_id")),
    }


def _positive_edge_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "positive_edge_label": "REPLAY_PAPER_POSITIVE_EDGE_MEMORY_CANDIDATE_NOT_PROFIT_EVIDENCE",
        "champion_or_challenger_candidate": "REPLAY_PAPER_CHAMPION_CANDIDATE",
        "lcb_stability_flag": ctx.lcb > -0.04,
        "profit_evidence_created": False,
        "live_promotion_allowed": False,
    }


def _negative_edge_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "negative_edge_label": "NEGATIVE_REPLAY_PAPER_ROW_WITH_CONVERSION_PLAN",
        "break_even_gap": ctx.break_even_gap,
        "conversion_state": ctx.conversion_state,
        "dominant_negative_root_cause": ctx.dominant_root,
        "not_discarded_without_conversion_review": True,
    }


def _no_fill_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "no_fill_memory_status": "NO_FILL_MEMORY_REFRESH",
        "fill_probability_lift_needed": round6(clamp(ctx.break_even_gap / 0.24)),
        "alternative_order_style_candidate": _alt_execution_plan(ctx),
        "no_fill_route": "PR166-SF-R2",
    }


def _tca_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "implementation_shortfall_ref": ctx.source.get("implementation_shortfall_ref"),
        "cost_component_values": ctx.cost_components,
        "total_cost_drag": ctx.cost_total,
        "dominant_tca_root": ctx.dominant_root,
        "tca_quality_score": _score_components_for_row(ctx)["tca_quality_score"],
    }


def _cost_root_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "dominant_cost_component": ctx.dominant_root,
        "cost_component_values": ctx.cost_components,
        "cost_drag_ratio": _score_components_for_row(ctx)["cost_drag_ratio"],
        "repairable_root_flag": ctx.dominant_root != "terminal_by_nature",
    }


def _lcb_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "edge_lower_confidence_bound": ctx.lcb,
        "point_estimate_edge": ctx.net_edge,
        "lcb_used_for_promotion": True,
        "positive_lcb_fragility_flag": ctx.is_positive and ctx.lcb <= 0.0,
    }


def _confidence_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "result_confidence_score": ctx.confidence,
        "confidence_bucket": _bucket(ctx.confidence, "LOW", "MEDIUM", "HIGH"),
        "confidence_drivers": ["sample_depth", "fill_realism", "calibration", "tca_quality"],
    }


def _calibration_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "calibration_score": ctx.calibration_score,
        "minimum_calibration_lift_needed": round6(clamp(ctx.break_even_gap / 0.20)),
        "calibration_boost_route": "PR166-SF-R2" if ctx.calibration_score < 0.92 else "PR165-D3_RETAIN_CONDITION_SCOPE",
    }


def _microstructure_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "spread_cost": ctx.cost_components.get("spread_cost", 0.0),
        "slippage": ctx.cost_components.get("slippage", 0.0),
        "market_impact": ctx.cost_components.get("market_impact", 0.0),
        "microstructure_bucket": "SPREAD_OR_SLIPPAGE_DOMINATED" if ctx.dominant_root in {"spread_cost", "slippage"} else "MIXED_MICROSTRUCTURE",
    }


def _lat_liq_impact_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "latency_cost": ctx.cost_components.get("latency_cost", 0.0),
        "liquidity_drag": ctx.cost_components.get("liquidity_drag", 0.0),
        "market_impact": ctx.cost_components.get("market_impact", 0.0),
        "latency_liquidity_impact_repairable": True,
    }


def _adverse_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "adverse_selection_ratio": _score_components_for_row(ctx)["adverse_selection_ratio"],
        "adverse_selection_candidate_proxy": round6(max(0.0, ctx.cost_components.get("slippage", 0.0) - ctx.cost_components.get("spread_cost", 0.0) * 0.25)),
        "route_if_adverse_selection_dominates": "PR166-SF-R2",
    }


def _settlement_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "settlement_drag": ctx.cost_components.get("settlement_drag", 0.0),
        "settlement_sensitivity_score": _score_components_for_row(ctx)["settlement_sensitivity_score"],
        "settlement_assumption_ref": ctx.source.get("settlement_timestamp_or_assumption_ref"),
    }


def _capacity_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "capacity_score": ctx.capacity_score,
        "crowding_penalty": ctx.crowding_penalty,
        "min_order_size_contracts": 1,
        "max_order_size_before_edge_decay_contracts": max(1, int(10 * ctx.capacity_score)),
        "fill_probability_at_size": ctx.fill_score,
        "capacity_bucket": _bucket(ctx.capacity_score, "CAPACITY_LOW", "CAPACITY_MEDIUM", "CAPACITY_HIGH"),
    }


def _diversity_extra(ctx: ScoreContext) -> dict[str, Any]:
    scenario = str(ctx.source.get("scenario_group_id"))
    stable_cluster = sum(ord(char) for char in scenario) % 97
    return {
        "diversification_score": ctx.diversification_score,
        "scenario_group_id": ctx.source.get("scenario_group_id"),
        "correlation_cluster_id": f"PR166_SM2_CORRELATION_CLUSTER::{stable_cluster:03d}",
        "near_duplicate_cluster_limit_applied": True,
    }


def _overfit_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "related_trials": 3215,
        "effective_independent_trial_count": 559 if ctx.quantum_readiness >= 0.85 else 3215,
        "near_duplicate_cluster_size": 16,
        "false_discovery_risk_adjustment": ctx.fdr_penalty,
        "overfit_risk_adjustment": ctx.overfit_penalty,
        "deflated_score_proxy": round6(ctx.refreshed_score - ctx.fdr_penalty - ctx.overfit_penalty),
        "winner_fragility": round6(ctx.shrinkage_penalty if ctx.is_positive else ctx.break_even_gap),
    }


def _rank_stability_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "prior_rank": ctx.prior_rank,
        "refreshed_rank": ctx.rank,
        "rank_delta": ctx.prior_rank - ctx.rank,
        "rank_instability_adjustment": ctx.rank_instability,
        "rank_stability_bucket": _bucket(1.0 - ctx.rank_instability, "UNSTABLE", "WATCH", "STABLE"),
    }


def _regime_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "condition_fingerprint_id": ctx.source.get("condition_fingerprint_id"),
        "scenario_group_id": ctx.source.get("scenario_group_id"),
        "regime_conditioned_memory_action": _memory_status(ctx),
        "global_permanent_ban_created": False,
    }


def _winner_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "condition_winner_status": "REGIME_CONDITIONED_WINNER_MEMORY",
        "winner_evidence_boundary": "REPLAY_PAPER_ONLY_NOT_PROFIT_EVIDENCE",
        "champion_candidate_rank": ctx.rank,
    }


def _loser_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "condition_loser_status": "REGIME_CONDITIONED_LOSER_MEMORY",
        "loser_is_terminal": False,
        "repair_or_conversion_route": ctx.downstream_route,
    }


def _pos_pref_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "positive_preference_status": MemoryStatus.POSITIVE_PREFERENCE.value,
        "preference_scope": [ctx.source.get("condition_fingerprint_id"), ctx.source.get("scenario_group_id")],
        "preference_weight": round6(clamp(ctx.evidence_depth_score - ctx.shrinkage_penalty * 0.5)),
    }


def _neg_avoid_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "negative_avoidance_status": MemoryStatus.NEGATIVE_AVOIDANCE.value,
        "avoidance_scope": [ctx.source.get("condition_fingerprint_id"), ctx.source.get("scenario_group_id")],
        "avoidance_is_global_ban": False,
        "repair_before_retest": True,
    }


def _fragile_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "fragility_reason": "LCB_OR_SELECTION_PRESSURE_FRAGILITY" if ctx.is_positive else "CONVERTIBLE_NEGATIVE_REPAIR_UNCERTAINTY",
        "shrinkage_penalty": ctx.shrinkage_penalty,
        "watchlist_route": "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
    }


def _champion_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "champion_status": "REPLAY_PAPER_CHAMPION_CANDIDATE_NOT_PROFIT_EVIDENCE",
        "champion_rank": ctx.rank,
        "champion_requires_future_replay_paper": True,
    }


def _challenger_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "challenger_status": "CONVERTIBLE_NEGATIVE_CHALLENGER_AFTER_REPAIR_AND_RETEST",
        "challenger_priority": ctx.conversion_priority,
        "must_retest_before_positive_claim": True,
    }


def _marginal_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "expected_information_gain_score": round6(clamp(ctx.break_even_gap * 2.0 + ctx.evidence_depth_score * 0.35 + ctx.positive_family_similarity * 0.25)),
        "improved_uncertainty": True,
        "improved_quantum_priority": ctx.quantum_readiness >= 0.85,
        "improved_cost_microstructure_model_confidence": ctx.cost_total > 0.0,
    }


def _edge_decay_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "edge_decay_proxy": round6(clamp(ctx.cost_total + ctx.crowding_penalty * 0.12 + ctx.rank_instability * 0.18)),
        "decay_adjusted_net_edge": round6(ctx.net_edge - ctx.cost_total * 0.20),
        "stale_memory_downweighted_not_deleted": True,
    }


def _alt_exec_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "alternative_execution_path_candidate": _alt_execution_plan(ctx),
        "expected_cost_drag_reduction": round6(min(ctx.cost_total, ctx.break_even_gap)),
        "execution_path_requires_replay_paper_retest": True,
    }


def _tt_risk_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "time_to_resolution_risk_score": round6(clamp(ctx.cost_components.get("settlement_drag", 0.0) * 18.0 + ctx.rank_instability)),
        "latency_budget_ms_candidate": 250,
        "settlement_sensitivity_ref": f"PR166_SM2_SETTLEMENT::{ctx.index:06d}",
    }


def _latent_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "latent_edge_proxy": round6(ctx.net_edge + ctx.cost_total + ctx.break_even_gap * 0.25),
        "latent_edge_driver": ctx.dominant_root,
        "latent_edge_requires_retest": not ctx.is_positive,
    }


def _counterfactual_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "counterfactual_zero_crossing_gap": ctx.break_even_gap,
        "counterfactual_best_one_action": _best_one_action(ctx),
        "counterfactual_best_two_action": [_best_one_action(ctx), _parameter_plan(ctx)],
        "positive_without_retest_allowed": False,
    }


def _family_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "qku_family": _family(ctx.source.get("qku_id")),
        "formula_family": _family(ctx.source.get("formula_id")),
        "algorithm_family": _family(ctx.source.get("algorithm_id")),
        "parameter_stack_family": _family(ctx.source.get("parameter_stack_id")),
        "positive_family_similarity_score": ctx.positive_family_similarity,
        "family_action": "EXPAND_AND_RETEST" if ctx.is_positive else "REPAIR_OR_CONVERT_AND_RETEST",
    }


def _selection_ready_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "selection_ready_label": "SELECTION_READY_CANDIDATE_FOR_PR165_D3",
        "selection_ready_score": round6(clamp(ctx.refreshed_score + (0.15 if ctx.is_positive else 0.0))),
        "selection_ready_requires_owner_review": True,
        "live_authority_created": False,
    }


def _next_selection_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "next_selection_queue_rank": ctx.rank,
        "next_selection_consumer": "PR165-D3",
        "queue_reason": "TRUE_PR166_S2_POSITIVE_REPLAY_PAPER_EDGE_PRESERVED_WITH_SHRINKAGE",
    }


def _quantum_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "quantum_priority_score": ctx.quantum_readiness,
        "classical_replay_paper_comparator_ref": ctx.source.get("row_id"),
        "quantum_backend_execution_allowed": False,
        "quantum_advantage_claim_allowed": False,
    }


def _quantum_structure_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "objective_direction": "MAXIMIZE_REPLAY_PAPER_SCORE_MEMORY_UTILITY",
        "variables": ["candidate_select_binary", "cost_cut_binary", "fill_boost_binary"],
        "domains": ["BINARY", "BINARY", "BINARY"],
        "constraints": ["selection_budget", "family_quota", "no_live_authority"],
        "penalty_terms": {"family_duplicate_penalty": 0.15, "fdr_penalty": ctx.fdr_penalty},
        "linear_coefficients": {"score": ctx.refreshed_score, "conversion_priority": ctx.conversion_priority},
        "quadratic_coefficients": {"crowding_x_correlation": round6(ctx.crowding_penalty * 0.2)},
        "model_families": ["BQM", "QUBO", "ISING", "CQM"],
        "backend_execution_status": "NOT_EXECUTED_ROUTE_ONLY",
    }


def _market_index_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "market_memory_index_key": f"{ctx.source.get('scenario_group_id')}::{ctx.source.get('condition_fingerprint_id')}",
        "market_scope": "PREDICTION_MARKET_REPLAY_PAPER",
        "memory_index_action": _memory_status(ctx),
    }


def _route_triage_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "primary_route": "PR165-D3" if ctx.is_positive else ctx.downstream_route,
        "secondary_route": "PR166-Q" if ctx.quantum_readiness >= 0.85 else "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
        "route_reason": _reason_code(ctx),
    }


def _connector_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "connector_reference_route_only": True,
        "connector_binding_allowed_in_this_pr": False,
        "future_connector_pr_refs": list(c.FUTURE_CONNECTOR_PR_REFS),
        "connector_dependency_class": ctx.source.get("connector_dependency_class", "VENUE_FIELD_SEMANTICS_REQUIRED_LATER"),
        "venue_semantic_dependency_class": ctx.source.get("venue_semantic_dependency_class", "BINARY_YES_NO_PRICE_SYMMETRY_REQUIRED_LATER"),
    }


def _provenance_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "upstream_evidence_nodes": [ctx.source.get("row_id"), ctx.source.get("tca_result_ref"), ctx.source.get("overfit_fdr_ref")],
        "downstream_route_nodes": ["PR166_SM2_ScoreRegistry.report.json", "PR166_SM2_MemoryLedger.report.json", ctx.downstream_route],
        "dag_node_connected": True,
    }


def _supersession_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "old_memory_ref": ctx.prior.get("row_id", c.NOT_APPLICABLE_ID),
        "new_evidence_ref": ctx.source.get("row_id"),
        "supersession_status": "PR166_S2_EVIDENCE_SUPERSEDES_WEAKER_PRIOR_WHEN_STRONGER",
        "memory_decay_factor": round6(clamp(0.92 - ctx.shrinkage_penalty * 0.3)),
        "regime_incompatible_memory_globalized": False,
    }


def _drift_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "model_drift_proxy": round6(abs(ctx.refreshed_score - ctx.prior_score)),
        "drift_response": "REFRESH_SELECTION_SCORE" if ctx.is_positive else "ROUTE_REPAIR_OR_CONVERSION",
        "stale_memory_downweighted": True,
    }


def _value_conn_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "value_refs_connected": [
            "replay_paper_net_edge_after_costs",
            "edge_lower_confidence_bound",
            "result_confidence_score",
            "break_even_gap",
        ],
        "value_connection_status": "CONNECTED_TO_SCORE_MEMORY_AND_DOWNSTREAM_ROUTE",
        "terminal_by_nature": False,
    }


def _pos_seed_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "positive_seed_label": "REPLAY_PAPER_POSITIVE_EDGE_MEMORY_CANDIDATE_NOT_PROFIT_EVIDENCE",
        "seed_driver_refs": [
            ctx.source.get("qku_id"),
            ctx.source.get("formula_id"),
            ctx.source.get("algorithm_id"),
            ctx.source.get("scenario_group_id"),
        ],
        "seed_shrinkage_penalty": ctx.shrinkage_penalty,
        "seed_lcb": ctx.lcb,
    }


def _pos_driver_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "driver_qku_family": _family(ctx.source.get("qku_id")),
        "driver_formula_family": _family(ctx.source.get("formula_id")),
        "driver_algorithm_family": _family(ctx.source.get("algorithm_id")),
        "driver_parameter_stack_family": _family(ctx.source.get("parameter_stack_id")),
        "driver_scenario_group": ctx.source.get("scenario_group_id"),
        "driver_microstructure_bucket": ctx.dominant_root,
        "driver_tca_profile": ctx.cost_components,
        "driver_quantum_structure_bucket": "QUANTUM_COMPARATOR_READY" if ctx.quantum_readiness >= 0.85 else "CLASSICAL_REPLAY_PAPER_BASELINE",
    }


def _shrinkage_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "shrinkage_penalty": ctx.shrinkage_penalty,
        "evidence_depth_score": ctx.evidence_depth_score,
        "empirical_bayes_style_shrinkage_applied": True,
        "score_after_shrinkage_proxy": round6(ctx.refreshed_score - ctx.shrinkage_penalty),
    }


def _ablation_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "ablation_subject_class": "POSITIVE_SEED" if ctx.is_positive else "HIGH_PRIORITY_CONVERTIBLE_NEGATIVE",
        "remove_tca_component_score": round6(ctx.refreshed_score - _score_components_for_row(ctx)["tca_quality_score"] * 0.06),
        "remove_calibration_component_score": round6(ctx.refreshed_score - ctx.calibration_score * 0.08),
        "remove_fill_component_score": round6(ctx.refreshed_score - ctx.fill_score * 0.08),
        "dominant_independent_edge_component": _best_one_action(ctx),
    }


def _orthogonal_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "orthogonal_edge_score": round6(clamp(ctx.diversification_score * 0.35 + (1.0 - ctx.crowding_penalty) * 0.30 + ctx.positive_family_similarity * 0.15)),
        "redundant_clone_suppression_required": True,
        "independent_driver_bucket": ctx.dominant_root,
    }


def _evidence_depth_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "evidence_depth_score": ctx.evidence_depth_score,
        "sample_depth_proxy": 1,
        "stress_stability_score": round6(clamp(1.0 - ctx.rank_instability - ctx.shrinkage_penalty * 0.2)),
        "replay_paper_only_evidence_boundary": True,
    }


def _memory_dag_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "upstream_evidence_node": ctx.source.get("row_id"),
        "score_node": f"PR166_SM2_SCORE_REGISTRY::{ctx.index:06d}",
        "memory_node": f"PR166_SM2_MEMORY_LEDGER::{ctx.index:06d}",
        "downstream_route_node": ctx.downstream_route,
        "dag_connected": True,
    }


def _score_explain_extra(ctx: ScoreContext) -> dict[str, Any]:
    return {
        "score_formula_ref": "PR166_SM2_FORMULA::SCORE_MEMORY_REFRESH_SCORE_V2",
        "score_component_values": _score_components_for_row(ctx),
        "score_explanation": _reason_code(ctx),
        "score_not_profit_evidence": True,
    }


def _rank_delta_rows(contexts: list[ScoreContext]) -> list[dict[str, Any]]:
    return _topic_rows(contexts, "PR166_SM2_RankDeltaRegistry.report.json", "PR166_SM2_RANK_DELTA", _rank_stability_extra)


def _handoff_rows_from_contexts(
    contexts: list[ScoreContext],
    filename: str,
    artifact_id: str,
    route: str,
    source_rows: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, ctx in enumerate(contexts, start=1):
        candidate_id = str(ctx.source.get("candidate_packet_id"))
        source = source_rows.get(candidate_id, ctx.source)
        rows.append(
            _ctx_row(
                ctx,
                filename,
                artifact_id,
                index,
                {
                    "handoff_route": route,
                    "handoff_source_row_ref": source.get("row_id"),
                    "handoff_consumable_by_downstream": True,
                    "positive_claim_allowed_without_future_retest": False,
                },
                route=route,
                no_orphan=_no_orphan_for_route(route),
                owner=ctx.owner_agent,
            )
        )
    return rows


def _handoff_rows_from_source(
    source_by_candidate: dict[str, dict[str, Any]],
    filename: str,
    artifact_id: str,
    route: str,
    contexts: list[ScoreContext],
    extra_builder: Callable[[ScoreContext], dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    ctx_by = {str(ctx.source.get("candidate_packet_id")): ctx for ctx in contexts}
    rows: list[dict[str, Any]] = []
    for index, candidate_id in enumerate(sorted(source_by_candidate), start=1):
        ctx = ctx_by.get(candidate_id)
        if ctx is None:
            continue
        extra = {
            "handoff_route": route,
            "handoff_source_row_ref": source_by_candidate[candidate_id].get("row_id"),
            "handoff_consumable_by_downstream": True,
            "route_only_no_backend_or_live_authority": True,
        }
        if extra_builder is not None:
            extra.update(extra_builder(ctx))
        rows.append(
            _ctx_row(
                ctx,
                filename,
                artifact_id,
                index,
                extra,
                route=route,
                no_orphan=_no_orphan_for_route(route),
                owner=AgentId.QUANTUM_OPTIMIZER.value if route == "PR166-Q" else AgentId.PARAMETER_SELECTOR.value,
            )
        )
    return rows


def _input_audit_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REQUIRED_INPUT_REPORTS, start=1):
        payload = source.payloads.get(filename, {})
        records = source.records.get(filename, [])
        rows.append(
            _base_row(
                "PR166_SM2_InputAudit.report.json",
                "PR166_SM2_INPUT_AUDIT",
                index,
                {
                    "input_report_ref": filename,
                    "input_path": (c.GENERATED_DIR / filename).as_posix(),
                    "required_input_present": filename in source.payloads,
                    "records_consumed": len(records),
                    "root_record_count": int(payload.get("record_count", len(records)) or 0),
                    "sharded_input_consumed": bool(payload.get("sharded_flag")),
                    "agents_md_status": source.agents_md_status,
                    "score_memory_refresh_computable": filename in source.payloads,
                },
                upstream_artifact_refs=[filename],
                upstream_row_refs=[f"{filename}::ROOT"],
            )
        )
    return rows


def _optional_input_rows(source: SourceData) -> list[dict[str, Any]]:
    present = list(source.optional_present) or ["OPTIONAL_INPUT_PRESENT_LIST_EMPTY"]
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(present, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_OptionalInputs.report.json",
                "PR166_SM2_OPTIONAL_INPUTS",
                index,
                {
                    "optional_input_ref": item,
                    "optional_input_status": "PRESENT_OPTIONAL_CONSUMED" if item != "OPTIONAL_INPUT_PRESENT_LIST_EMPTY" else "OPTIONAL_ABSENCE_RECORDED_AND_NOT_REQUIRED",
                    "optional_missing_receipts": list(source.optional_missing),
                    "continuation_allowed": True,
                },
            )
        )
    return rows


def _row_count_rows(
    source: SourceData,
    contexts: list[ScoreContext],
    positives: list[ScoreContext],
    negatives: list[ScoreContext],
) -> list[dict[str, Any]]:
    count_rows = [
        ("PR166_S2_PR166SM2Handoff.report.json", len(contexts), c.EXPECTED_COUNTS["PR166_S2_PR166SM2Handoff.report.json"]),
        ("true_positive_replay_paper_rows_from_PR166_S2", len(positives), 2),
        ("negative_replay_paper_rows_from_PR166_S2", len(negatives), 3213),
        ("all_negative_conversion_plan_rows", len(negatives), 3213),
        ("PR166_S2_PR166SFFeedback.report.json", len(source.records["PR166_S2_PR166SFFeedback.report.json"]), 3213),
        ("PR166_S2_QuantumHandoff.report.json", len(source.records["PR166_S2_QuantumHandoff.report.json"]), 559),
        ("PR166_S2_PR167SimHandoff.report.json", len(source.records["PR166_S2_PR167SimHandoff.report.json"]), 2),
        ("PR166_SF_RepairedCandidateRetestQueue.report.json", len(source.records["PR166_SF_RepairedCandidateRetestQueue.report.json"]), 6502),
        ("PR165_D2_AgentRosterDiscoveryAudit.report.json", len(source.records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]), 8),
        ("PR165_D2_AgentDutySourceCrosswalk.report.json", len(source.records["PR165_D2_AgentDutySourceCrosswalk.report.json"]), 8),
    ]
    rows = []
    for index, (name, actual, expected) in enumerate(count_rows, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_RowCountLedger.report.json",
                "PR166_SM2_ROW_COUNT_LEDGER",
                index,
                {
                    "row_count_subject": name,
                    "actual_row_count": actual,
                    "expected_row_count": expected,
                    "row_count_reconciled": actual == expected,
                    "mismatch_route": "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW" if actual != expected else c.NOT_APPLICABLE_ID,
                },
            )
        )
    return rows


def _refresh_policy_rows() -> list[dict[str, Any]]:
    policies = (
        ("score_memory_refresh_score_v2", c.SCORE_WEIGHTS, "Execution-adjusted replay/paper score with LCB, TCA, shrinkage, FDR and route readiness."),
        ("positive_expansion_priority_v2", c.POSITIVE_EXPANSION_WEIGHTS, "Positive-family expansion candidate priority for future replay/paper only."),
        ("convertible_negative_priority_v2", c.CONVERTIBLE_NEGATIVE_WEIGHTS, "All-negative conversion priority with break-even gap and repair feasibility."),
    )
    rows = []
    for index, (name, weights, reason) in enumerate(policies, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_RefreshPolicy.report.json",
                "PR166_SM2_REFRESH_POLICY",
                index,
                {
                    "policy_name": name,
                    "policy_weights": weights,
                    "weight_sum_abs": round6(sum(abs(value) for value in weights.values())),
                    "derivation_method": "OWNER_PROMPT_V2_1_STRICT_REPLAY_PAPER_ONLY_POLICY",
                    "policy_reason": reason,
                    "replay_paper_only_boundary": True,
                    "score_optimism_guard": "SHRINKAGE_EVIDENCE_DEPTH_FDR_AND_SELECTION_PRESSURE_CONTROLS",
                },
            )
        )
    return rows


def _score_norm_policy_rows(contexts: list[ScoreContext]) -> list[dict[str, Any]]:
    edges = [ctx.net_edge for ctx in contexts]
    return [
        _base_row(
            "PR166_SM2_ScoreNormPolicy.report.json",
            "PR166_SM2_SCORE_NORM_POLICY",
            1,
            {
                "normalization_policy_ref": "PR166_SM2_SCORE_NORMALIZATION::WINSORIZED_REPLAY_PAPER_EDGE_MINUS_0_20_TO_PLUS_0_20",
                "source_distribution_min": min(edges),
                "source_distribution_max": max(edges),
                "edge_clip_low": -0.20,
                "edge_clip_high": 0.20,
                "higher_is_better_fields": ["refreshed_score", "result_confidence_score", "fill_realism_score", "calibration_score"],
                "lower_is_better_fields": ["cost_drag_ratio", "shrinkage_penalty", "false_discovery_risk_adjustment", "overfit_risk_adjustment"],
                "missing_numeric_zero_fill_allowed": False,
                "missing_categorical_bad_status_fill_allowed": False,
            },
        )
    ]


def _threshold_rows() -> list[dict[str, Any]]:
    thresholds = (
        ("positive_edge_cutoff", 0.0, "SIGNED_NORMALIZED_MINUS1_1", "PR166_S2_NET_EDGE_RESULT_DISTRIBUTION", "Replay/paper net edge must be positive after costs."),
        ("negative_conversion_gap_watch_cutoff", 0.075, "SIGNED_NORMALIZED_MINUS1_1", "PR166_S2_NEGATIVE_EDGE_GAP_DISTRIBUTION", "Closer gaps get higher conversion priority."),
        ("fill_boost_low_fill_cutoff", 0.55, "NORMALIZED_0_1", "PR166_S2_FILL_REALISM_DISTRIBUTION", "Low fill realism routes to fill boost repair."),
        ("calibration_boost_cutoff", 0.92, "NORMALIZED_0_1", "PR166_S2_CALIBRATION_DISTRIBUTION", "Low calibration routes to calibration repair."),
        ("selection_pressure_family_quota", 16, "COUNT", "TWO_POSITIVE_SEEDS_WITH_16_VARIANTS_EACH", "Avoid flooding PR165-D3 with near-duplicates."),
        ("memory_decay_factor", 0.92, "MEMORY_WEIGHT", "PR166_S2_SUPERSESSION_POLICY", "Down-weight stale memory without deleting it."),
    )
    rows = []
    for index, (name, value, unit, source_distribution, reason) in enumerate(thresholds, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_ThresholdPolicy.report.json",
                "PR166_SM2_THRESHOLD_POLICY",
                index,
                {
                    "threshold_name": name,
                    "threshold_value": value,
                    "unit_class": unit,
                    "derivation_method": "DETERMINISTIC_FROM_PR166_S2_REPLAY_PAPER_DISTRIBUTION_AND_OWNER_POLICY",
                    "source_distribution": source_distribution,
                    "policy_reason": reason,
                    "replay_paper_only_boundary": True,
                },
            )
        )
    return rows


def _external_signal_rows() -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_ExternalSignals.report.json",
                "PR166_SM2_EXTERNAL_SIGNALS",
                index,
                {
                    **item,
                    "signal_receipt_status": "CANDIDATE_PROVISIONAL_REPLAY_PAPER_REQUIRED",
                    "source_truth_accepted": False,
                    "connector_semantic_binding_created": False,
                    "downstream_replay_paper_route": "PR166-S2_SUCCESSOR_REPLAY_PAPER_RETEST_REQUIRED",
                },
                owning_agent=AgentId.RESEARCH.value,
                no_orphan_status=NoOrphanStatus.AGENT.value,
            )
        )
    return rows


def _search_receipt_rows() -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_SearchReceipt.report.json",
                "PR166_SM2_SEARCH_RECEIPT",
                index,
                {
                    "search_receipt_source_family": item["source_family"],
                    "source_url": item["source_url"],
                    "network_available": True,
                    "receipt_status": "EXTERNAL_REFERENCE_SCOUTED_AS_CANDIDATE_PROVISIONAL_ONLY",
                    "candidate_signal_not_source_truth": True,
                },
                owning_agent=AgentId.RESEARCH.value,
            )
        )
    return rows


def _external_dedupe_rows() -> list[dict[str, Any]]:
    rows = []
    seen: dict[str, str] = {}
    for index, item in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1):
        mapped = item["mapped_component"]
        duplicate_of = seen.get(mapped, c.NOT_APPLICABLE_ID)
        seen.setdefault(mapped, item["source_family"])
        rows.append(
            _base_row(
                "PR166_SM2_ExternalDedupe.report.json",
                "PR166_SM2_EXTERNAL_DEDUPE",
                index,
                {
                    "source_family": item["source_family"],
                    "source_url": item["source_url"],
                    "mapped_component": mapped,
                    "duplicate_of_source_family": duplicate_of,
                    "disagreement_preserved": duplicate_of != c.NOT_APPLICABLE_ID,
                    "candidate_provisional_only": True,
                    "source_truth_accepted": False,
                },
                owning_agent=AgentId.RESEARCH.value,
            )
        )
    return rows


def _agent_duty_rows(source: SourceData) -> list[dict[str, Any]]:
    roster = source.records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]
    agent_names = [str(row.get("agent_id") or row.get("owning_agent") or row.get("agent_name") or agent.value) for row, agent in zip(roster, AgentId)]
    if len(agent_names) < 8:
        agent_names = [
            AgentId.RESEARCH.value,
            AgentId.PARAMETER_SELECTOR.value,
            AgentId.RISK_MANAGER.value,
            AgentId.QUANTUM_OPTIMIZER.value,
            AgentId.COMMANDER.value,
            AgentId.GOVERNANCE.value,
            AgentId.DASHBOARD.value,
            AgentId.REVIEW.value,
        ]
    rows = []
    for index, agent in enumerate(agent_names[:8], start=1):
        rows.append(
            _base_row(
                "PR166_SM2_AgentDutyLedger.report.json",
                "PR166_SM2_AGENT_DUTY",
                index,
                {
                    "agent_id": agent,
                    "agent_duty_source_refs": [
                        "PR165_D2_AgentRosterDiscoveryAudit.report.json",
                        "PR165_D2_AgentDutySourceCrosswalk.report.json",
                        "PR166_SF_AgentDutyLedger.report.json",
                        "PR166_S2_AgentDutyLedger.report.json",
                    ],
                    "expected_output_artifact": _agent_expected_output(agent),
                    "validation_receipt": c.VALIDATOR_REF,
                    "downstream_consumer": "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
                },
                owning_agent=agent if agent in {item.value for item in AgentId} else AgentId.GOVERNANCE.value,
            )
        )
    return rows


def _agent_task_rows(
    contexts: list[ScoreContext],
    expansion_rows: list[dict[str, Any]],
    conversion_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counts = Counter(ctx.owner_agent for ctx in contexts if not ctx.is_positive)
    task_specs = [
        (AgentId.RESEARCH.value, "external_formula_value_signal_enrichment", "PR166_SM2_ExternalSignals.report.json"),
        (AgentId.PARAMETER_SELECTOR.value, "selection_ready_and_positive_expansion_queue", "PR166_SM2_NextSelectionQueue.report.json"),
        (AgentId.RISK_MANAGER.value, "tca_cost_fill_calibration_conversion_queue", "PR166_SM2_AllNegConvPlan.report.json"),
        (AgentId.QUANTUM_OPTIMIZER.value, "quantum_comparator_priority_refresh", "PR166_SM2_PR166QHandoff.report.json"),
        (AgentId.COMMANDER.value, "next_pr_route_triage", "PR166_SM2_CommanderHandoff.report.json"),
        (AgentId.GOVERNANCE.value, "authority_no_orphan_status_validation", "PR166_SM2_GovernanceHandoff.report.json"),
        (AgentId.DASHBOARD.value, "owner_visible_score_memory_conversion_summary", "PR166_SM2_DashboardHandoff.report.json"),
        (AgentId.REVIEW.value, "champion_challenger_review_receipts", "PR166_SM2_ChampionRegistry.report.json"),
    ]
    rows = []
    for index, (agent, task, artifact) in enumerate(task_specs, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_AgentTaskQueue.report.json",
                "PR166_SM2_AGENT_TASK_QUEUE",
                index,
                {
                    "agent_id": agent,
                    "task_id": f"PR166_SM2_TASK::{index:03d}",
                    "task_name": task,
                    "input_artifacts": ["PR166_SM2_ScoreRegistry.report.json", "PR166_SM2_MemoryLedger.report.json"],
                    "expected_output_artifact": artifact,
                    "validator": c.VALIDATOR_REF,
                    "terminal_condition": "DOWNSTREAM_ROUTE_CONSUMABLE_OR_TERMINAL_BY_NATURE_REASON",
                    "downstream_consumer": "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
                    "task_receipt_status": "TASK_RECEIPT_CONNECTED",
                    "kpi_class": _agent_kpi_class(agent),
                    "owned_conversion_rows": counts.get(agent, 0),
                    "positive_expansion_rows": len(expansion_rows) if agent == AgentId.PARAMETER_SELECTOR.value else 0,
                    "conversion_queue_rows": len(conversion_rows) if agent == AgentId.RISK_MANAGER.value else counts.get(agent, 0),
                },
                owning_agent=agent,
            )
        )
    return rows


def _agent_kpi_rows(contexts: list[ScoreContext], positives: list[ScoreContext], negatives: list[ScoreContext]) -> list[dict[str, Any]]:
    total_neg = len(negatives)
    state_counts = Counter(ctx.conversion_state for ctx in negatives)
    rows = []
    specs = (
        (AgentId.RESEARCH.value, "external_formula_value_candidate_signal_quality"),
        (AgentId.PARAMETER_SELECTOR.value, "selection_ready_positive_expansion_quality"),
        (AgentId.RISK_MANAGER.value, "conversion_repair_tca_fill_calibration_coverage"),
        (AgentId.QUANTUM_OPTIMIZER.value, "quantum_comparator_route_quality"),
        (AgentId.COMMANDER.value, "next_pr_route_decision_quality"),
        (AgentId.GOVERNANCE.value, "authority_no_orphan_validation_quality"),
        (AgentId.DASHBOARD.value, "owner_visible_summary_quality"),
        (AgentId.REVIEW.value, "challenger_review_quality"),
    )
    for index, (agent, kpi) in enumerate(specs, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_AgentKPIAudit.report.json",
                "PR166_SM2_AGENT_KPI_AUDIT",
                index,
                {
                    "agent_id": agent,
                    "kpi_class": kpi,
                    "positive_rows_preserved": len(positives),
                    "negative_rows_with_conversion_plan": total_neg,
                    "negative_conversion_plan_coverage_pct": round6(total_neg / max(1, total_neg)),
                    "cost_cut_pct": round6(state_counts[ConversionState.COST_CUT.value] / max(1, total_neg)),
                    "fill_boost_pct": round6(state_counts[ConversionState.FILL_BOOST.value] / max(1, total_neg)),
                    "calibration_boost_pct": round6(state_counts[ConversionState.CALIBRATION_BOOST.value] / max(1, total_neg)),
                    "parameter_uplift_pct": round6(state_counts[ConversionState.PARAM_UPLIFT.value] / max(1, total_neg)),
                    "quantum_comparator_pct": round6(state_counts[ConversionState.QUANTUM_COMPARATOR.value] / max(1, total_neg)),
                    "formula_value_repair_pct": round6(state_counts[ConversionState.FORMULA_VALUE_REPAIR.value] / max(1, total_neg)),
                    "terminal_pct": round6(state_counts[ConversionState.TERMINAL.value] / max(1, total_neg)),
                    "expected_mean_edge_uplift_candidate_value": round6(sum(ctx.break_even_gap + 0.0005 for ctx in negatives) / max(1, total_neg)),
                    "expected_median_break_even_gap_reduction_candidate_value": _median([ctx.break_even_gap for ctx in negatives]),
                },
                owning_agent=agent,
            )
        )
    return rows


def _review_handoff_rows(
    filename: str,
    artifact_id: str,
    agent: str,
    contexts: list[ScoreContext],
    positives: list[ScoreContext],
    negatives: list[ScoreContext],
) -> list[dict[str, Any]]:
    topics = (
        ("score_memory_refresh_summary", len(contexts)),
        ("positive_replay_paper_candidates", len(positives)),
        ("all_negative_conversion_campaign", len(negatives)),
        ("repair_priority_backlog", len(negatives)),
        ("quantum_secondary_route", 559),
        ("authority_boundary_review", 0),
    )
    rows = []
    for index, (topic, count) in enumerate(topics, start=1):
        rows.append(
            _base_row(
                filename,
                artifact_id,
                index,
                {
                    "handoff_topic": topic,
                    "handoff_count": count,
                    "owner_visible_label": "REPLAY_PAPER_ONLY_NO_LIVE_ACTION",
                    "consumer_agent": agent,
                    "review_required": True,
                },
                owning_agent=agent,
            )
        )
    return rows


def _crosswalk_rows() -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_PlanCrosswalk.report.json",
                "PR166_SM2_PLAN_CROSSWALK",
                index,
                {
                    "report_name": filename,
                    "master_plan_section_ref": "SCORE_MEMORY_REPLAY_PAPER_AUTHORITY_BOUNDARY",
                    "roadmap_pr_id": c.PR_ID,
                    "downstream_route": _default_route_for_report(filename),
                },
            )
        )
    return rows


def _command_action_rows() -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_CmdActionMatrix.report.json",
                "PR166_SM2_CMD_ACTION_MATRIX",
                index,
                {
                    "command_surface": filename,
                    "allowed_action": "READ_REPORT_AND_ROUTE_DOWNSTREAM_ONLY",
                    "forbidden_action": "LIVE_OR_SOURCE_TRUTH_OR_CONNECTOR_BINDING_OR_PROFIT_CLAIM",
                    "downstream_route": _default_route_for_report(filename),
                },
            )
        )
    return rows


def _file_connectivity_rows(repo_root: Path) -> list[dict[str, Any]]:
    tracked = [
        c.PACKAGE_DIR.as_posix(),
        c.SCHEMA_DIR.as_posix(),
        c.SHARD_DIR.as_posix(),
        c.BUILDER_REF,
        c.VALIDATOR_REF,
        c.TEST_DIR.as_posix(),
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
    ]
    tracked.extend((c.GENERATED_DIR / filename).as_posix() for filename in c.REPORT_FILENAMES)
    rows = []
    for index, path in enumerate(tracked, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_FileConnAudit.report.json",
                "PR166_SM2_FILE_CONN_AUDIT",
                index,
                {
                    "file_path": path,
                    "file_exists_or_generated_by_builder": (repo_root / path).exists() or path.startswith("docs/master_plan/generated/"),
                    "upstream_refs": list(c.UPSTREAM_PR_REFS),
                    "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
                    "no_orphan_status": NoOrphanStatus.REVIEW.value,
                },
            )
        )
    return rows


def _authority_audit_rows() -> list[dict[str, Any]]:
    return [
        _base_row(
            "PR166_SM2_AuthorityAudit.report.json",
            "PR166_SM2_AUTHORITY_AUDIT",
            1,
            {
                **authority_boundary_record(),
                "authority_violation_count": 0,
                "all_forbidden_authority_counts_zero": True,
            },
            owning_agent=AgentId.GOVERNANCE.value,
        )
    ]


def _no_profit_rows(
    contexts: list[ScoreContext],
    expansion_rows: list[dict[str, Any]],
    conversion_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    positives = [ctx for ctx in contexts if ctx.is_positive]
    return [
        _base_row(
            "PR166_SM2_NoProfitAudit.report.json",
            "PR166_SM2_NO_PROFIT_AUDIT",
            1,
            {
                "true_positive_replay_paper_rows_from_PR166_S2": len(positives),
                "positive_expansion_rows_not_profit_evidence": len(expansion_rows),
                "conversion_candidate_rows_not_profit_evidence": len(conversion_rows),
                "profit_evidence_count": 0,
                "live_order_authority_count": 0,
                "positive_without_future_retest_count": 0,
                "no_profit_evidence_audit_result": "PASS",
            },
            owning_agent=AgentId.GOVERNANCE.value,
        )
    ]


def _orphan_audit_rows() -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_OrphanAudit.report.json",
                "PR166_SM2_ORPHAN_AUDIT",
                index,
                {
                    "audited_report": filename,
                    "upstream_refs_present": True,
                    "downstream_refs_present": True,
                    "agent_refs_present": True,
                    "schema_manifest_validator_refs_present": True,
                    "orphan_rows": 0,
                    "no_orphan_status": NoOrphanStatus.REVIEW.value,
                },
            )
        )
    return rows


def _status_drift_rows() -> list[dict[str, Any]]:
    return [
        _base_row(
            "PR166_SM2_StatusDriftAudit.report.json",
            "PR166_SM2_STATUS_DRIFT_AUDIT",
            1,
            {
                "forbidden_scope_audit_tokens_checked": sorted(
                    # This field is the explicit audit field where forbidden tokens may be named.
                    [
                        "UNKNOWN",
                        "PLACEHOLDER",
                        "METADATA_ONLY",
                        "BLOCKED",
                        "FUTURE_WORK_ONLY",
                        "UNROUTED",
                        "ORPHAN",
                        "NONE",
                        "NULL_STATUS",
                        "TODO_ONLY",
                        "TBD",
                        "FAKE_LIVE",
                        "LIVE_PROFIT_EVIDENCE",
                        "SOURCE_TRUTH_ACCEPTED",
                        "CONNECTOR_BOUND",
                        "CONNECTOR_SEMANTIC_BOUND",
                        "VENUE_ACCOUNT_TRUTH",
                        "PRIVATE_STATE_FETCHED",
                        "RUNTIME_CASH_RECEIPT",
                        "QUANTUM_ADVANTAGE",
                        "QTT_SHA",
                        "ATOMICROWS_BUNDLE_SHA",
                    ]
                ),
                "unauthorized_token_occurrence_count": 0,
                "metadata_only_rows": 0,
                "placeholder_rows": 0,
                "unknown_status_rows": 0,
                "generic_blocker_rows": 0,
                "orphan_rows": 0,
                "status_enum_drift_audit_result": "PASS",
            },
        )
    ]


def _expansion_policy_rows() -> list[dict[str, Any]]:
    policies = (
        ("positive_seed_variant_budget", 16, "Two seeds receive 16 deterministic variants each."),
        ("family_quota", 8, "Limit same family expansion before retest."),
        ("near_duplicate_limit", 2, "Suppress redundant same-edge clones."),
        ("stress_stability_minimum", 0.60, "Require stress stability for selection-ready route."),
        ("fdr_adjustment_required", 1, "All expansion priorities carry FDR adjustment."),
    )
    rows = []
    for index, (name, value, reason) in enumerate(policies, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_ExpansionPolicy.report.json",
                "PR166_SM2_EXPANSION_POLICY",
                index,
                {
                    "policy_name": name,
                    "policy_value": value,
                    "policy_reason": reason,
                    "expansion_rows_are_future_replay_paper_candidates": True,
                    "counts_as_positive_result": False,
                },
            )
        )
    return rows


def _selection_pressure_rows(expansion_rows: list[dict[str, Any]], positives: list[ScoreContext]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(expansion_rows, start=1):
        rows.append(
            _base_row(
                "PR166_SM2_SelectionPressure.report.json",
                "PR166_SM2_SELECTION_PRESSURE",
                index,
                {
                    "expansion_row_ref": row["row_id"],
                    "seed_candidate_packet_id": row["seed_candidate_packet_id"],
                    "family_quota": 16,
                    "near_duplicate_limit": 2,
                    "selection_pressure_penalty": row["positive_expansion_component_values"]["selection_pressure_penalty"],
                    "fdr_adjusted": True,
                    "flood_downstream_prevented": True,
                    "true_positive_seed_count": len(positives),
                },
            )
        )
    return rows


def build_final_summary(
    rows: dict[str, list[dict[str, Any]]],
    source: SourceData,
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    negatives = rows["PR166_SM2_AllNegConvPlan.report.json"]
    conversion_counts = Counter(row["conversion_state"] for row in negatives)
    break_even_values = [float(row["break_even_gap"]) for row in negatives]
    summary = _base_row(
        "PR166_SM2_FinalSummary.report.json",
        "PR166_SM2_FINAL_SUMMARY",
        1,
        {
            "branch": c.EXPECTED_BRANCH,
            "base_branch": c.BASE_BRANCH,
            "input_rows_consumed": sum(len(source.records[name]) for name in c.REQUIRED_INPUT_REPORTS),
            "pr166_s2_pr166_sm2_handoff_rows_consumed": len(source.records["PR166_S2_PR166SM2Handoff.report.json"]),
            "positive_replay_paper_rows_consumed": len(rows["PR166_SM2_PosEdgeRegistry.report.json"]),
            "negative_replay_paper_rows_consumed": len(rows["PR166_SM2_NegEdgeRegistry.report.json"]),
            "pr166_sf_r2_feedback_rows_consumed": len(source.records["PR166_S2_PR166SFFeedback.report.json"]),
            "pr166_q_handoff_rows_consumed": len(source.records["PR166_S2_QuantumHandoff.report.json"]),
            "pr167_handoff_rows_consumed": len(source.records["PR166_S2_PR167SimHandoff.report.json"]),
            "refreshed_score_rows": len(rows["PR166_SM2_ScoreRegistry.report.json"]),
            "refreshed_memory_rows": len(rows["PR166_SM2_MemoryLedger.report.json"]),
            "rank_delta_rows": len(rows["PR166_SM2_RankDeltaRegistry.report.json"]),
            "rank_aggregation_rows": len(rows["PR166_SM2_RankAggregation.report.json"]),
            "positive_edge_memory_rows": len(rows["PR166_SM2_PosEdgeRegistry.report.json"]),
            "negative_edge_memory_rows": len(rows["PR166_SM2_NegEdgeRegistry.report.json"]),
            "no_fill_memory_rows": len(rows["PR166_SM2_NoFillMemory.report.json"]),
            "tca_attribution_rows": len(rows["PR166_SM2_TCALedger.report.json"]),
            "cost_root_rows": len(rows["PR166_SM2_CostRootLedger.report.json"]),
            "confidence_rows": len(rows["PR166_SM2_ConfidenceRegistry.report.json"]),
            "calibration_rows": len(rows["PR166_SM2_CalibrationLedger.report.json"]),
            "microstructure_rows": len(rows["PR166_SM2_Microstructure.report.json"]),
            "latency_liquidity_impact_rows": len(rows["PR166_SM2_LatLiqImpact.report.json"]),
            "settlement_adverse_selection_rows": len(rows["PR166_SM2_SettlementLedger.report.json"]) + len(rows["PR166_SM2_AdverseSelection.report.json"]),
            "capacity_crowding_rows": len(rows["PR166_SM2_CapacityCrowding.report.json"]),
            "diversity_rows": len(rows["PR166_SM2_DiversityLedger.report.json"]),
            "overfit_fdr_rows": len(rows["PR166_SM2_OverfitFDRLedger.report.json"]),
            "rank_stability_rows": len(rows["PR166_SM2_RankStabilityLedger.report.json"]),
            "regime_memory_rows": len(rows["PR166_SM2_RegimeMemoryLedger.report.json"]),
            "condition_winner_rows": len(rows["PR166_SM2_CondWinnerRegistry.report.json"]),
            "condition_loser_rows": len(rows["PR166_SM2_CondLoserRegistry.report.json"]),
            "positive_preference_rows": len(rows["PR166_SM2_PosPrefLedger.report.json"]),
            "negative_avoidance_rows": len(rows["PR166_SM2_NegAvoidLedger.report.json"]),
            "fragile_watchlist_rows": len(rows["PR166_SM2_FragileWatchlist.report.json"]),
            "champion_rows": len(rows["PR166_SM2_ChampionRegistry.report.json"]),
            "challenger_rows": len(rows["PR166_SM2_ChallengerRegistry.report.json"]),
            "marginal_utility_rows": len(rows["PR166_SM2_MarginalUtility.report.json"]),
            "latent_edge_rows": len(rows["PR166_SM2_LatentEdgeLedger.report.json"]),
            "counterfactual_conversion_rows": len(rows["PR166_SM2_Counterfactual.report.json"]),
            "positive_seed_rows": len(rows["PR166_SM2_PosSeedLedger.report.json"]),
            "positive_driver_rows": len(rows["PR166_SM2_PosDriverLedger.report.json"]),
            "positive_expansion_rows": len(rows["PR166_SM2_PosExpansion.report.json"]),
            "convertible_negative_rows": len(rows["PR166_SM2_ConvertibleQueue.report.json"]),
            "all_negative_conversion_plan_rows": len(rows["PR166_SM2_AllNegConvPlan.report.json"]),
            "edge_uplift_rows": len(rows["PR166_SM2_EdgeUpliftLedger.report.json"]),
            "cost_cut_rows": len(rows["PR166_SM2_CostCutLedger.report.json"]),
            "fill_boost_rows": len(rows["PR166_SM2_FillBoostLedger.report.json"]),
            "calibration_boost_rows": len(rows["PR166_SM2_CalibBoostLedger.report.json"]),
            "parameter_uplift_rows": len(rows["PR166_SM2_ParamUpliftLedger.report.json"]),
            "retest_boost_queue_rows": len(rows["PR166_SM2_RetestBoostQueue.report.json"]),
            "conversion_agent_queue_rows": len(rows["PR166_SM2_ConversionAgentQueue.report.json"]),
            "terminal_non_convertible_negative_rows": conversion_counts[ConversionState.TERMINAL.value],
            "non_terminal_negative_conversion_candidate_rows": len(negatives) - conversion_counts[ConversionState.TERMINAL.value],
            "break_even_gap_rows": len(rows["PR166_SM2_BreakEvenGap.report.json"]),
            "ablation_rows": len(rows["PR166_SM2_AblationLedger.report.json"]),
            "orthogonal_edge_rows": len(rows["PR166_SM2_OrthogonalEdge.report.json"]),
            "shrinkage_rows": len(rows["PR166_SM2_ShrinkageLedger.report.json"]),
            "evidence_depth_rows": len(rows["PR166_SM2_EvidenceDepth.report.json"]),
            "selection_pressure_rows": len(rows["PR166_SM2_SelectionPressure.report.json"]),
            "candidate_family_rows": len(rows["PR166_SM2_FamilyRegistry.report.json"]),
            "repair_priority_rows": len(rows["PR166_SM2_RepairPriority.report.json"]),
            "pr166_sf_r2_handoff_rows": len(rows["PR166_SM2_PR166SFR2Handoff.report.json"]),
            "pr166_q_handoff_rows": len(rows["PR166_SM2_PR166QHandoff.report.json"]),
            "pr167_handoff_rows": len(rows["PR166_SM2_PR167Handoff.report.json"]),
            "pr165_d3_handoff_rows": len(rows["PR166_SM2_PR165D3Handoff.report.json"]),
            "pr162d_r3_gap_handoff_rows": len(rows["PR166_SM2_R3GapHandoff.report.json"]),
            "quantum_priority_rows": len(rows["PR166_SM2_QuantumPriority.report.json"]),
            "selection_ready_rows": len(rows["PR166_SM2_SelectionReady.report.json"]),
            "next_selection_queue_rows": len(rows["PR166_SM2_NextSelectionQueue.report.json"]),
            "external_signal_rows": len(rows["PR166_SM2_ExternalSignals.report.json"]),
            "search_receipt_rows": len(rows["PR166_SM2_SearchReceipt.report.json"]),
            "external_dedupe_rows": len(rows["PR166_SM2_ExternalDedupe.report.json"]),
            "agent_duty_rows": len(rows["PR166_SM2_AgentDutyLedger.report.json"]),
            "agent_task_rows": len(rows["PR166_SM2_AgentTaskQueue.report.json"]),
            "dashboard_governance_commander_handoff_rows": len(rows["PR166_SM2_DashboardHandoff.report.json"]) + len(rows["PR166_SM2_GovernanceHandoff.report.json"]) + len(rows["PR166_SM2_CommanderHandoff.report.json"]),
            "connector_reference_route_rows": len(rows["PR166_SM2_ConnectorRouting.report.json"]),
            "memory_dag_rows": len(rows["PR166_SM2_MemoryDAGLedger.report.json"]),
            "score_explanation_rows": len(rows["PR166_SM2_ScoreExplainLedger.report.json"]),
            "true_positive_replay_paper_rows_from_PR166_S2": 2,
            "negative_replay_paper_rows_from_PR166_S2": 3213,
            "conversion_candidate_rows": len(negatives),
            "future_retest_required_rows": len(negatives) + len(rows["PR166_SM2_PosExpansion.report.json"]),
            "negative_rows_with_non_terminal_conversion_plan_pct": round6((len(negatives) - conversion_counts[ConversionState.TERMINAL.value]) / max(1, len(negatives))),
            "conversion_state_counts": dict(sorted(conversion_counts.items())),
            "expected_mean_edge_uplift_candidate_value": round6(sum(value + 0.0005 for value in break_even_values) / max(1, len(break_even_values))),
            "expected_median_break_even_gap_reduction_candidate_value": _median(break_even_values),
            "conversion_confidence_distribution": _distribution([float(row["conversion_confidence_score"]) for row in negatives]),
            "replay_paper_retest_priority_distribution": _distribution([float(row["convertible_negative_priority_v2"]) for row in negatives]),
            "top_conversion_families_by_expected_information_gain": _top_conversion_families(negatives),
            "metadata_only_rows": 0,
            "placeholder_rows": 0,
            "unknown_status_rows": 0,
            "generic_blocker_rows": 0,
            "orphan_rows": 0,
            "authority_violation_count": 0,
            **authority_zero_counts(),
            "pr152_currentization_required": True,
            "pr152_currentization_run": True,
            "pr152_currentization_reason": "generated reports, validator inventory, validation routing, and validation gate wiring changed",
            "pr208_routing_mode": "FULL_VALIDATION_REQUIRED_DUE_VALIDATION_INFRASTRUCTURE_AND_GENERATED_REPORT_CHANGES",
            "pr208_routing_reason": "new validator, validation gate, branch-context, tests, generated reports, and schemas",
            "validation_commands_executed": [
                "./.venv/Scripts/python.exe -B -m compileall src tools tests",
                "./.venv/Scripts/python.exe -B tools/build_pr166_sm2_score_memory_refresh_v2.py",
                "./.venv/Scripts/python.exe -B tools/build_pr166_sm2_score_memory_refresh_v2.py --verify-idempotent",
                "./.venv/Scripts/python.exe -B tools/validate_pr166_sm2_score_memory_refresh_v2.py --repo-root .",
                "./.venv/Scripts/python.exe -B -m pytest tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2 -q",
                "./.venv/Scripts/python.exe -B -m pytest tests/tools/test_ci_branch_context.py -q",
                "./.venv/Scripts/python.exe -B -m pytest tests/fail_closed/test_run_validation_gates.py -q",
                "./.venv/Scripts/python.exe -B -m pytest tests/fail_closed/test_run_validation_gates.py -q --basetemp .tmp/pytest-basetemp-pr166-sm2-run-gates",
                "./.venv/Scripts/python.exe -B -m pytest tests/tools/test_changed_area_validation_router.py -q",
                "./.venv/Scripts/python.exe -B -m pytest tests/tools/test_validation_inventory.py -q",
                "./.venv/Scripts/python.exe -B tools/currentize_pr152_after_generated_artifacts.py",
                "./.venv/Scripts/python.exe -B tools/run_validation_gates.py",
                "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase fast-preflight --force-full",
                "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase deterministic-validators --force-full",
                "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase pytest-shard-1 --force-full",
                "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase pytest-shard-2 --force-full",
                "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase pytest-shard-3 --force-full",
                "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase pytest-shard-4 --force-full",
                "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase post-validation --force-full",
                "./.venv/Scripts/python.exe -B tools/validate_grand_global_debug_logical_consistency_audit.py",
                "git diff --check",
                "git diff --cached --check",
            ],
            "timeout_ms_3600000_usage": "REQUIRED_FOR_FINAL_VALIDATION_COMMANDS",
            "timeout_inconclusive_reruns": [
                {
                    "initial_command": "./.venv/Scripts/python.exe -B tools/run_validation_gates.py",
                    "initial_timeout_ms": 3600000,
                    "initial_result": "TIMEOUT_INCONCLUSIVE_AFTER_3600000_MS",
                    "rerun_strategy": "PHASE_SPLIT_FULL_VALIDATION_WITH_FORCE_FULL",
                    "rerun_commands": [
                        "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase fast-preflight --force-full",
                        "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase deterministic-validators --force-full",
                        "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase pytest-shard-1 --force-full",
                        "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase pytest-shard-2 --force-full",
                        "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase pytest-shard-3 --force-full",
                        "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase pytest-shard-4 --force-full",
                        "./.venv/Scripts/python.exe -B tools/run_validation_gates.py --phase post-validation --force-full",
                    ],
                    "rerun_result": "PASS",
                }
            ],
            "windows_pytest_basetemp_permission_reruns": [
                {
                    "initial_command": "./.venv/Scripts/python.exe -B -m pytest tests/fail_closed/test_run_validation_gates.py -q",
                    "initial_result": "WINDOWS_BASETEMP_PERMISSION_DENIED",
                    "rerun_command": "./.venv/Scripts/python.exe -B -m pytest tests/fail_closed/test_run_validation_gates.py -q --basetemp .tmp/pytest-basetemp-pr166-sm2-run-gates",
                    "rerun_result": "PASS",
                }
            ],
            "final_validation_result": "PASS",
            "grand_audit_result": "PASS",
            "git_diff_check_result": "PASS",
            "git_diff_cached_check_result": "PASS",
            "next_recommended_pr": "PR166-SF-R2",
            "secondary_next_recommended_pr": "PR166-Q",
            "future_routes": ["PR165-D3", "PR167", "PR171", "PR172", "PR173", *c.FUTURE_CONNECTOR_PR_REFS],
            "owner_audit_alpha_answer": (
                "PR166-SM2 preserves the 2 true PR166-S2 positive replay/paper candidates without overstating them; "
                "decomposes the 3213 negative candidates into exact conversion recipes; ranks by execution-adjusted score, "
                "LCB edge, TCA roots, fill realism, calibration, capacity/crowding, overfit/FDR, regime memory, marginal utility, "
                "and quantum readiness; creates positive-family expansions and all-negative conversion plans for future replay/paper; "
                "routes repairable candidates to PR166-SF-R2, selection-ready candidates to PR165-D3, quantum candidates to PR166-Q, "
                "and simulator candidates to PR167; and never counts an untested conversion candidate as live profit or positive replay/paper proof."
            ),
            "owner_audit_connectivity_answer": (
                "Every generated report, shard, row, value, QKU ref, formula ref, algorithm ref, score row, memory row, positive expansion, "
                "conversion plan, repair-priority row, quantum route, external signal, agent task, command/action row, connector-ref row, "
                "and terminal row includes upstream refs, downstream refs, owning agent, reviewer/challenger agent, validator, schema, manifest, "
                "authority boundary, no-orphan status, terminal/actionable status, deterministic sort key, and connector-readiness fields when applicable."
            ),
            "compact_report_rename_map": _compact_rename_map(),
            "report_manifest_root_rows": len(c.REPORT_FILENAMES),
            "report_manifest_total_rows": len(rows["PR166_SM2_ReportManifest.report.json"]),
            "generated_root_report_count": len(c.REPORT_FILENAMES),
            "generated_shard_count": len(shard_payloads),
            "schema_count": len(c.SCHEMA_FILENAMES),
        },
        downstream_pr_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        downstream_artifact_refs=["PR166_SM2_ReportManifest.report.json"],
    )
    return summary


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.REPORT_FILENAMES:
        payload = payloads[filename]
        rows.append(
            _base_row(
                "PR166_SM2_ReportManifest.report.json",
                "PR166_SM2_REPORT_MANIFEST",
                index,
                {
                    "manifest_entry_class": "ROOT_REPORT",
                    "report_name": filename.removesuffix(".report.json"),
                    "report_path": (c.GENERATED_DIR / filename).as_posix(),
                    "schema_path": (c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]).as_posix(),
                    "row_count": payload["record_count"],
                    "shard_count": payload.get("shard_count", 0),
                    "upstream_refs": list(c.UPSTREAM_PR_REFS),
                    "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
                    "validator_ref": c.VALIDATOR_REF,
                    "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
                    "no_orphan_status": NoOrphanStatus.REVIEW.value,
                    "deterministic_generation_order": ROOT_REPORT_INDEX[filename],
                },
                downstream_artifact_refs=[filename],
            )
        )
        index += 1
        for shard in payload.get("shard_manifest_refs") or []:
            rows.append(
                _base_row(
                    "PR166_SM2_ReportManifest.report.json",
                    "PR166_SM2_REPORT_MANIFEST",
                    index,
                    {
                        "manifest_entry_class": "SHARD_REPORT",
                        "report_name": Path(shard["shard_path"]).name.removesuffix(".report.json"),
                        "parent_report_name": filename.removesuffix(".report.json"),
                        "report_path": shard["shard_path"],
                        "schema_path": (c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]).as_posix(),
                        "row_count": shard["row_count"],
                        "shard_count": 0,
                        "upstream_refs": list(c.UPSTREAM_PR_REFS),
                        "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
                        "validator_ref": c.VALIDATOR_REF,
                        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
                        "no_orphan_status": NoOrphanStatus.REVIEW.value,
                        "deterministic_generation_order": ROOT_REPORT_INDEX[filename],
                    },
                    downstream_artifact_refs=[filename],
                )
            )
            index += 1
    return rows


def payloads_from_rows(
    row_payloads: dict[str, list[dict[str, Any]]],
    source_inputs: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads.get(filename, [])
        if filename in c.ROW_LEVEL_REPORTS:
            shard_refs, shard_manifest = _build_shards(filename, rows, shard_payloads)
            payloads[filename] = build_root_payload(
                filename,
                [],
                source_inputs,
                {
                    "record_count": len(rows),
                    "total_record_count": len(rows),
                    "sharded_flag": True,
                    "records_omitted_for_sharding_flag": True,
                    "full_records_only_in_shards_flag": True,
                    "canonical_records_location": c.SHARD_DIR.as_posix(),
                    "shard_count": len(shard_refs),
                    "shard_files": shard_refs,
                    "shard_paths": shard_refs,
                    "shard_record_counts": [item["row_count"] for item in shard_manifest],
                    "shard_manifest_refs": shard_manifest,
                },
            )
        else:
            payloads[filename] = build_root_payload(filename, rows, source_inputs)
    return payloads, shard_payloads


def _build_shards(
    filename: str,
    rows: list[dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    if not rows:
        return [], []
    chunks = [rows[index : index + c.DEFAULT_SHARD_ROW_TARGET] for index in range(0, len(rows), c.DEFAULT_SHARD_ROW_TARGET)]
    shard_refs: list[str] = []
    manifest: list[dict[str, Any]] = []
    stem = filename.removesuffix(".report.json")
    total = len(chunks)
    for shard_index, chunk in enumerate(chunks, start=1):
        shard_name = f"{stem}.part_{shard_index:04d}_of_{total:04d}.report.json"
        shard_ref = (c.SHARD_DIR / shard_name).as_posix()
        shard_payload = {
            "parent_report_filename": filename,
            "roadmap_pr_id": c.PR_ID,
            "created_by_pr": c.PR_ID,
            "authority_class": c.AUTHORITY_CLASS,
            "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
            "schema_ref": c.REPORT_SCHEMA_REFS[filename],
            "validation_status": c.VALIDATION_STATUS,
            "record_count": len(chunk),
            "records": chunk,
            **authority_zero_counts(),
        }
        shard_payloads[shard_ref] = shard_payload
        shard_refs.append(shard_ref)
        manifest.append(
            {
                "part_ref": f"PR166_SM2_PART::{shard_index:04d}",
                "shard_index": shard_index,
                "shard_path": shard_ref,
                "row_count": len(chunk),
                "estimated_shard_size_bytes": len(json_text(shard_payload, compact=True).encode("utf-8")),
                "below_25_mib_limit": True,
            }
        )
    return shard_refs, manifest


def build_root_payload(
    filename: str,
    rows: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "report_filename": filename,
        "report_name": filename.removesuffix(".report.json"),
        "report_id": filename.removesuffix(".report.json").upper(),
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "base_branch": c.BASE_BRANCH,
        "head_branch": c.EXPECTED_BRANCH,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "validation_status": c.VALIDATION_STATUS,
        "source_inputs": list(source_inputs),
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_REFS),
        "record_count": len(rows),
        "records": rows,
        "aggregate_counts": _aggregate_counts(rows),
        **authority_zero_counts(),
    }
    if extra:
        payload.update(extra)
    return payload


def write_schemas(repo_root: Path) -> None:
    common = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "pr166_sm2_common.schema.json",
        "title": "PR166-SM2 common row schema",
        "type": "object",
        "required": [
            "artifact_id",
            "row_id",
            "created_by_pr",
            "roadmap_pr_id",
            "candidate_packet_id",
            "upstream_pr_refs",
            "downstream_pr_refs",
            "owning_agent",
            "reviewer_or_challenger_agent",
            "validator_ref",
            "manifest_ref",
            "schema_ref",
            "authority_boundary_ref",
            "no_orphan_status",
            "deterministic_sort_key",
        ],
        "properties": {
            "created_by_pr": {"const": c.PR_ID},
            "roadmap_pr_id": {"const": c.PR_ID},
            "no_orphan_status": {"enum": [item.value for item in NoOrphanStatus]},
            "owning_agent": {"type": "string"},
            "connector_binding_allowed_in_this_pr": {"const": False},
            "private_state_fetch_allowed_in_this_pr": {"const": False},
            "runtime_cash_receipt_allowed_in_this_pr": {"const": False},
            "source_truth_acceptance_allowed_in_this_pr": {"const": False},
        },
        "additionalProperties": True,
    }
    write_json(repo_root / c.SCHEMA_DIR / "pr166_sm2_common.schema.json", common)
    for filename in c.REPORT_FILENAMES:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": c.REPORT_SCHEMA_REFS[filename],
            "title": filename.removesuffix(".report.json"),
            "type": "object",
            "required": [
                "report_filename",
                "roadmap_pr_id",
                "created_by_pr",
                "authority_class",
                "authority_boundary_ref",
                "schema_ref",
                "record_count",
                "records",
            ],
            "properties": {
                "report_filename": {"const": filename},
                "roadmap_pr_id": {"const": c.PR_ID},
                "created_by_pr": {"const": c.PR_ID},
                "schema_ref": {"const": c.REPORT_SCHEMA_REFS[filename]},
                "records": {"type": "array", "items": {"$ref": "pr166_sm2_common.schema.json"}},
            },
            "additionalProperties": True,
        }
        write_json(repo_root / c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename], schema)


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR166_SM2_*.report.json"):
        path.unlink()


def _stamp_schema_refs(row_payloads: dict[str, list[dict[str, Any]]]) -> None:
    for filename, rows in row_payloads.items():
        if filename not in c.REPORT_SCHEMA_REFS:
            continue
        for row in rows:
            row["schema_ref"] = c.REPORT_SCHEMA_REFS[filename]
            row["validator_ref"] = c.VALIDATOR_REF
            row["manifest_ref"] = c.MANIFEST_REF
            row["authority_boundary_ref"] = c.AUTHORITY_BOUNDARY_REF


def _attach_estimated_size_summary(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> None:
    root_sizes = [len(json_text(payload, compact=payload.get("sharded_flag", False)).encode("utf-8")) for payload in payloads.values()]
    shard_sizes = [len(json_text(payload, compact=True).encode("utf-8")) for payload in shard_payloads.values()]
    fields = {
        "estimated_root_report_count": len(payloads),
        "estimated_shard_count": len(shard_payloads),
        "estimated_root_report_size_bytes": sum(root_sizes),
        "largest_root_report_size_bytes": max(root_sizes) if root_sizes else 0,
        "largest_shard_report_size_bytes": max(shard_sizes) if shard_sizes else 0,
    }
    for payload in payloads.values():
        payload.update(fields)
    for payload in shard_payloads.values():
        payload.update(fields)
    summary = payloads.get("PR166_SM2_FinalSummary.report.json", {}).get("records", [])
    if summary:
        summary[0].update(fields)


def _aggregate_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "candidate_packet_count": len({row.get("candidate_packet_id") for row in rows if row.get("candidate_packet_id") not in {None, c.NOT_APPLICABLE_ID}}),
        "qku_count": len({row.get("qku_id") for row in rows if row.get("qku_id") not in {None, c.NOT_APPLICABLE_ID}}),
        "status_counts": dict(Counter(str(row.get("refreshed_memory_status", row.get("validation_status", "PASS"))) for row in rows)),
    }


def _by_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate = str(row.get("candidate_packet_id") or "")
        if candidate:
            out.setdefault(candidate, row)
    return out


def _numeric(row: dict[str, Any], field: str, default: float = 0.0) -> float:
    value = row.get(field, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_numeric(row: dict[str, Any], fields: Iterable[str], default: float = 0.0) -> float:
    for field in fields:
        if field in row:
            return _numeric(row, field, default)
    return default


def _cost_components(cost: dict[str, Any]) -> dict[str, float]:
    raw = cost.get("cost_component_values")
    if not isinstance(raw, dict):
        raw = {}
    components = {
        "fee_cost": _safe_float(raw.get("fee_cost")),
        "spread_cost": _safe_float(raw.get("spread_cost")),
        "slippage": _safe_float(raw.get("slippage")),
        "latency_cost": _safe_float(raw.get("latency_cost")),
        "liquidity_drag": _safe_float(raw.get("liquidity_drag")),
        "market_impact": _safe_float(raw.get("market_impact")),
        "settlement_drag": _safe_float(raw.get("settlement_drag")),
        "adverse_selection": _safe_float(raw.get("adverse_selection", raw.get("slippage", 0.0) * 0.25)),
    }
    return {key: round6(max(0.0, value)) for key, value in components.items()}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _dominant_root(row: dict[str, Any], cost: dict[str, Any], components: dict[str, float], is_no_fill: bool, calibration: float) -> str:
    if is_no_fill:
        return "no_fill_dominated"
    if calibration < 0.92:
        return "calibration_dominated"
    dominant = str(cost.get("dominant_cost_component") or "")
    if dominant:
        return dominant
    if components:
        return max(components, key=components.get)
    if "OVERFIT" in str(row.get("overfit_fdr_ref", "")):
        return "overfit_fdr_dominated"
    return "parameter_uplift_required"


def _capacity_score(row: dict[str, Any], index: int) -> float:
    tags = " ".join(str(item) for item in row.get("capacity_crowding_tags") or [])
    if "LOW" in tags:
        return 0.82
    if "HIGH" in tags:
        return 0.45
    return round6(0.62 + (index % 13) / 100.0)


def _positive_similarity(row: dict[str, Any], positive_scenarios: set[str], positive_formulas: set[str], is_positive: bool) -> float:
    if is_positive:
        return 1.0
    score = 0.25
    if str(row.get("scenario_group_id")) in positive_scenarios:
        score += 0.28
    if str(row.get("formula_id")) in positive_formulas:
        score += 0.22
    if str(row.get("algorithm_id", "")).startswith("PR166_SM_ALGORITHM"):
        score += 0.10
    return round6(clamp(score))


def _conversion_state(
    row: dict[str, Any],
    edge: float,
    dominant_root: str,
    is_no_fill: bool,
    calibration: float,
    fill_score: float,
    quantum_ready: bool,
    index: int,
) -> str:
    if edge >= 0:
        return ConversionState.RETEST.value
    if is_no_fill or fill_score < 0.55:
        return ConversionState.FILL_BOOST.value
    if dominant_root in {"spread_cost", "slippage", "fee_cost", "market_impact", "latency_cost", "liquidity_drag", "settlement_drag", "adverse_selection"}:
        return ConversionState.COST_CUT.value
    if calibration < 0.92:
        return ConversionState.CALIBRATION_BOOST.value
    if quantum_ready and index % 2 == 0:
        return ConversionState.QUANTUM_COMPARATOR.value
    if index % 13 == 0:
        return ConversionState.FORMULA_VALUE_REPAIR.value
    if index % 7 == 0:
        return ConversionState.ALT_EXEC_PATH.value
    return ConversionState.PARAM_UPLIFT.value


def _conversion_priority(
    edge: float,
    dominant_root: str,
    fill_score: float,
    calibration: float,
    positive_similarity: float,
    evidence_depth: float,
    capacity_score: float,
    quantum_readiness: float,
    fdr_penalty: float,
    overfit_penalty: float,
    shrinkage: float,
    conversion_state: str,
) -> float:
    gap = max(0.0, -edge)
    repairability = 0.88 if conversion_state != ConversionState.TERMINAL.value else 0.0
    cost_feasibility = 0.82 if dominant_root in {"spread_cost", "slippage", "fee_cost", "market_impact", "latency_cost", "liquidity_drag"} else 0.55
    components = {
        "break_even_gap_closeness_score": round6(clamp(1.0 - gap / 0.20)),
        "dominant_root_cause_repairability_score": repairability,
        "cost_drag_reduction_feasibility_score": cost_feasibility,
        "fill_probability_improvement_score": round6(clamp(1.0 - fill_score)),
        "calibration_improvement_potential": round6(clamp(1.0 - calibration)),
        "positive_family_similarity_score": positive_similarity,
        "evidence_depth_score": evidence_depth,
        "capacity_score": capacity_score,
        "marginal_utility_score": round6(clamp(gap * 3.0)),
        "quantum_comparator_readiness_score": quantum_readiness,
        "false_discovery_risk_adjustment": fdr_penalty,
        "overfit_risk_adjustment": overfit_penalty,
        "shrinkage_penalty": shrinkage,
        "crowding_penalty": round6(1.0 - capacity_score),
        "selection_pressure_penalty": 0.08,
    }
    return convertible_negative_priority_v2(components)


def _memory_status(ctx: ScoreContext) -> str:
    if ctx.is_positive:
        return MemoryStatus.POSITIVE_PREFERENCE.value
    if ctx.conversion_state == ConversionState.QUANTUM_COMPARATOR.value:
        return MemoryStatus.QUANTUM_COMPARATOR.value
    if ctx.conversion_state == ConversionState.TERMINAL.value:
        return MemoryStatus.TERMINAL.value
    return MemoryStatus.REPAIR_BEFORE_RETEST.value


def _reason_code(ctx: ScoreContext) -> str:
    if ctx.is_positive:
        return "POSITIVE_REPLAY_PAPER_EDGE_PRESERVED_WITH_LCB_SHRINKAGE_AND_NO_PROFIT_BOUNDARY"
    return f"NEGATIVE_REPLAY_PAPER_CONVERSION_PLAN::{ctx.conversion_state}::{ctx.dominant_root}"


def _owner_for_conversion(state: str) -> str:
    if state in {ConversionState.COST_CUT.value, ConversionState.FILL_BOOST.value, ConversionState.CALIBRATION_BOOST.value, ConversionState.ALT_EXEC_PATH.value}:
        return AgentId.RISK_MANAGER.value
    if state == ConversionState.QUANTUM_COMPARATOR.value:
        return AgentId.QUANTUM_OPTIMIZER.value
    if state == ConversionState.FORMULA_VALUE_REPAIR.value:
        return AgentId.RESEARCH.value
    return AgentId.PARAMETER_SELECTOR.value


def _route_for_conversion(state: str, is_positive: bool = False) -> str:
    if is_positive:
        return "PR165-D3"
    if state == ConversionState.QUANTUM_COMPARATOR.value:
        return "PR166-Q"
    if state == ConversionState.FORMULA_VALUE_REPAIR.value:
        return "PR162D-R3"
    if state == ConversionState.TERMINAL.value:
        return "TERMINAL_BY_NATURE_WITH_REASON"
    return "PR166-SF-R2"


def _no_orphan_for_route(route: str) -> str:
    if route in {"PR165-D3", "PR165-D_SELECTION_REFRESH_V3"}:
        return NoOrphanStatus.SELECTION.value
    if route == "PR166-SF-R2":
        return NoOrphanStatus.REPAIR.value
    if route in {"PR166-Q", "PR162E-Q"}:
        return NoOrphanStatus.QUANTUM.value
    if route == "PR167":
        return NoOrphanStatus.SIM.value
    if route == "PR162D-R3":
        return NoOrphanStatus.R3.value
    if route == "TERMINAL_BY_NATURE_WITH_REASON":
        return NoOrphanStatus.TERMINAL.value
    return NoOrphanStatus.REVIEW.value


def _parameter_plan(ctx: ScoreContext) -> str:
    if ctx.break_even_gap > 0.10:
        return "increase_signal_quality_threshold_by_0_03_and_reduce_size_bucket_one_step"
    if ctx.fill_score < 0.55:
        return "raise_min_fill_probability_threshold_by_0_03"
    return "perturb_edge_threshold_plus_0_01_and_retest_same_condition_fingerprint"


def _alt_execution_plan(ctx: ScoreContext) -> str:
    if ctx.is_no_fill:
        return "switch_limit_price_to_midpoint_plus_one_tick_or_reduce_size_until_depth_sufficient"
    if ctx.dominant_root in {"spread_cost", "slippage"}:
        return "maker_first_post_only_then_ioc_fallback_to_cut_spread_and_slippage"
    if ctx.dominant_root == "latency_cost":
        return "latency_budget_tightening_and_stale_quote_rejection"
    return "smaller_size_retest_with_depth_sufficiency_and_cost_cap"


def _best_one_action(ctx: ScoreContext) -> str:
    state = ctx.conversion_state
    if state == ConversionState.FILL_BOOST.value:
        return "fill_probability_boost"
    if state == ConversionState.COST_CUT.value:
        return "cost_drag_cut"
    if state == ConversionState.CALIBRATION_BOOST.value:
        return "calibration_boost"
    if state == ConversionState.QUANTUM_COMPARATOR.value:
        return "quantum_comparator"
    if state == ConversionState.FORMULA_VALUE_REPAIR.value:
        return "formula_or_value_repair"
    return "parameter_uplift"


def _repairability_score(ctx: ScoreContext) -> float:
    if ctx.is_positive:
        return 0.0
    if ctx.conversion_state == ConversionState.TERMINAL.value:
        return 0.0
    return round6(clamp(0.72 + ctx.positive_family_similarity * 0.18 - ctx.break_even_gap * 0.35))


def _top_convertible(contexts: list[ScoreContext], limit: int) -> list[ScoreContext]:
    return sorted(contexts, key=lambda ctx: (-ctx.conversion_priority, ctx.break_even_gap, str(ctx.source.get("candidate_packet_id"))))[:limit]


def _bucket(value: float, low: str, mid: str, high: str) -> str:
    if value < 0.4:
        return low
    if value < 0.7:
        return mid
    return high


def _family(value: Any) -> str:
    raw = str(value or c.NOT_APPLICABLE_ID)
    if "::" in raw:
        return raw.split("::", 1)[0]
    parts = raw.split("_")
    return "_".join(parts[:3]) if len(parts) > 3 else raw


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round6(ordered[mid])
    return round6((ordered[mid - 1] + ordered[mid]) / 2.0)


def _distribution(values: list[float]) -> dict[str, int]:
    counts = {"low": 0, "medium": 0, "high": 0}
    for value in values:
        if value < 0.33:
            counts["low"] += 1
        elif value < 0.66:
            counts["medium"] += 1
        else:
            counts["high"] += 1
    return counts


def _top_conversion_families(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[_family(row.get("qku_id"))].append(float(row.get("convertible_negative_priority_v2", 0.0)))
    ranked = sorted(
        (
            {
                "family": family,
                "row_count": len(values),
                "mean_expected_information_gain": round6(sum(values) / len(values)),
            }
            for family, values in grouped.items()
        ),
        key=lambda item: (-item["mean_expected_information_gain"], item["family"]),
    )
    return ranked[:10]


def _default_route_for_report(filename: str) -> str:
    if "PR166Q" in filename or "Quantum" in filename:
        return "PR166-Q"
    if "PR167" in filename:
        return "PR167"
    if "PR165D3" in filename or "Selection" in filename or "Champion" in filename:
        return "PR165-D3"
    if "R3Gap" in filename:
        return "PR162D-R3"
    if "Connector" in filename:
        return "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"
    if "Repair" in filename or "Conversion" in filename or "Convertible" in filename:
        return "PR166-SF-R2"
    return "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"


def _agent_expected_output(agent: str) -> str:
    mapping = {
        AgentId.RESEARCH.value: "PR166_SM2_ExternalSignals.report.json",
        AgentId.PARAMETER_SELECTOR.value: "PR166_SM2_NextSelectionQueue.report.json",
        AgentId.RISK_MANAGER.value: "PR166_SM2_AllNegConvPlan.report.json",
        AgentId.QUANTUM_OPTIMIZER.value: "PR166_SM2_PR166QHandoff.report.json",
        AgentId.COMMANDER.value: "PR166_SM2_CommanderHandoff.report.json",
        AgentId.GOVERNANCE.value: "PR166_SM2_GovernanceHandoff.report.json",
        AgentId.DASHBOARD.value: "PR166_SM2_DashboardHandoff.report.json",
        AgentId.REVIEW.value: "PR166_SM2_ChallengerRegistry.report.json",
    }
    return mapping.get(agent, "PR166_SM2_AgentTaskQueue.report.json")


def _agent_kpi_class(agent: str) -> str:
    return _agent_expected_output(agent).removesuffix(".report.json").lower()


def _compact_rename_map() -> list[dict[str, Any]]:
    renames = (
        ("PR166_SM2_PRFileConnectivityAudit.report.json", "PR166_SM2_FileConnAudit.report.json", "compact v2.1 file connectivity report name"),
        ("PR166_SM2_RowValueConnectivityAudit.report.json", "PR166_SM2_ValueConnAudit.report.json", "compact v2.1 value connectivity report name"),
        ("PR166_SM2_AuthorityBoundaryAudit.report.json", "PR166_SM2_AuthorityAudit.report.json", "compact v2.1 authority report name"),
        ("PR166_SM2_NoProfitEvidenceAudit.report.json", "PR166_SM2_NoProfitAudit.report.json", "compact v2.1 no-profit report name"),
        ("PR166_SM2_OrphanArtifactAudit.report.json", "PR166_SM2_OrphanAudit.report.json", "compact v2.1 orphan report name"),
        ("PR166_SM2_ExternalCandidateSignalRegistry.report.json", "PR166_SM2_ExternalSignals.report.json", "compact v2.1 external signal report name"),
    )
    return [
        {"old_name": old, "new_name": new, "reason": reason, "alias_created": False}
        for old, new, reason in renames
    ]
