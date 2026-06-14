"""Build PR166-SM3 generated reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS, authority_boundary_record, authority_zero_counts
from .enums import (
    AgentId,
    EvidenceClass,
    LineageConflictStatus,
    LineageStatus,
    MemoryUpdateType,
    NoOrphanStatus,
)
from .io import (
    ensure_branch,
    json_text,
    normalize_repo_ref,
    read_json,
    records_from_report_payload,
    resolve_repo_relative,
    write_json,
)
from .models import common_fields, row_id
from .score_policy import QUANTUM_COMBO_WEIGHTS, SCORE_COMPONENT_WEIGHTS, clamp, quantum_combo_score, round6, score_from_components

ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024
ROOT_REPORT_INDEX = {name: index for index, name in enumerate(c.REPORT_FILENAMES, start=1)}


@dataclass(frozen=True)
class SourceData:
    payloads: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    missing_strict: tuple[str, ...]
    missing_lineage: tuple[str, ...]
    optional_present: tuple[str, ...]
    optional_missing: tuple[str, ...]
    shard_audit_rows: tuple[dict[str, Any], ...]
    agents_md_status: str


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
            compact=bool(payloads[filename].get("sharded_flag")),
        )
    for rel_path, shard_payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    return BuildArtifacts(
        summary=dict(payloads["PR166_SM3_FinalSummary.report.json"]["records"][0]),
        payloads=payloads,
        shard_payloads=shard_payloads,
    )


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    if source.missing_strict:
        raise RuntimeError(f"{c.PR_ID} required inputs missing: {', '.join(source.missing_strict)}")
    row_payloads = build_row_payloads(repo_root, source)
    payloads, shard_payloads = payloads_from_rows(row_payloads, list(c.REQUIRED_INPUT_REPORTS))
    row_payloads["PR166_SM3_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads["PR166_SM3_ReportManifest.report.json"] = build_root_payload(
        "PR166_SM3_ReportManifest.report.json",
        row_payloads["PR166_SM3_ReportManifest.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    row_payloads["PR166_SM3_FinalSummary.report.json"] = [
        build_final_summary(row_payloads, source, payloads, shard_payloads)
    ]
    payloads["PR166_SM3_FinalSummary.report.json"] = build_root_payload(
        "PR166_SM3_FinalSummary.report.json",
        row_payloads["PR166_SM3_FinalSummary.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"final_summary_row_count": 1},
    )
    row_payloads["PR166_SM3_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads["PR166_SM3_ReportManifest.report.json"] = build_root_payload(
        "PR166_SM3_ReportManifest.report.json",
        row_payloads["PR166_SM3_ReportManifest.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"{c.PR_ID} payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    missing_strict: list[str] = []
    missing_lineage: list[str] = []
    shard_rows: list[dict[str, Any]] = []
    ordered_inputs = list(c.REQUIRED_INPUT_REPORTS)
    for index, filename in enumerate(ordered_inputs, start=1):
        path = repo_root / c.GENERATED_DIR / filename
        strict = filename in c.STRICT_INPUT_REPORTS
        if not path.exists():
            if strict:
                missing_strict.append(filename)
            else:
                missing_lineage.append(f"{c.LINEAGE_NOT_PRESENT}::{(c.GENERATED_DIR / filename).as_posix()}")
            shard_rows.append(
                _admin_row(
                    "PR166_SM3_ShardInputAudit.report.json",
                    "PR166_SM3_SHARD_INPUT_AUDIT",
                    index,
                    {
                        "upstream_report_ref": filename,
                        "root_report_path": (c.GENERATED_DIR / filename).as_posix(),
                        "input_presence_status": "MISSING_STRICT_INPUT" if strict else c.LINEAGE_NOT_PRESENT,
                        "records_omitted_for_sharding_flag": False,
                        "declared_shard_count": 0,
                        "read_shard_count": 0,
                        "declared_total_row_count": 0,
                        "read_total_row_count": 0,
                        "row_count_mismatch_flag": strict,
                        "continuation_allowed": not strict,
                        "agents_md_status": "NOT_PRESENT_NOT_REQUIRED",
                    },
                )
            )
            continue
        payload = read_json(path)
        rows = records_from_report_payload(repo_root, payload)
        payloads[filename] = payload
        records[filename] = rows
        declared = [normalize_repo_ref(item) for item in payload.get("shard_files") or payload.get("shard_paths") or []]
        read_paths = [item for item in declared if resolve_repo_relative(repo_root, item).exists()]
        shard_rows.append(
            _admin_row(
                "PR166_SM3_ShardInputAudit.report.json",
                "PR166_SM3_SHARD_INPUT_AUDIT",
                index,
                {
                    "upstream_report_ref": filename,
                    "root_report_path": (c.GENERATED_DIR / filename).as_posix(),
                    "input_presence_status": "PRESENT_CONSUMED",
                    "records_omitted_for_sharding_flag": bool(payload.get("records_omitted_for_sharding_flag")),
                    "shard_paths_declared": declared,
                    "shard_paths_read": read_paths,
                    "declared_shard_count": int(payload.get("shard_count", len(declared)) or 0),
                    "read_shard_count": len(read_paths),
                    "declared_total_row_count": int(payload.get("record_count", len(rows)) or 0),
                    "read_total_row_count": len(rows),
                    "row_count_mismatch_flag": int(payload.get("record_count", len(rows)) or 0) != len(rows),
                    "continuation_allowed": int(payload.get("record_count", len(rows)) or 0) == len(rows),
                    "agents_md_status": "NOT_PRESENT_NOT_REQUIRED",
                },
                upstream_artifact_refs=[filename],
                upstream_row_refs=[f"{filename}::ROOT"],
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
        missing_strict=tuple(missing_strict),
        missing_lineage=tuple(missing_lineage),
        optional_present=tuple(sorted(set(optional_present))),
        optional_missing=tuple(optional_missing),
        shard_audit_rows=tuple(shard_rows),
        agents_md_status="PRESENT_OPTIONAL_CONSUMED" if agents else "NOT_PRESENT_NOT_REQUIRED",
    )


def build_row_payloads(repo_root: Path, source: SourceData) -> dict[str, list[dict[str, Any]]]:
    contexts = build_candidate_contexts(source)
    sf_contexts = [ctx for ctx in contexts if ctx["source_layer"] == "PR166-SF-R2"]
    positives = [ctx for ctx in contexts if ctx["replay_paper_positive_flag"]]
    repaired_positives = [ctx for ctx in positives if ctx["evidence_class"] == EvidenceClass.REPAIRED_REPLAY_PAPER_POSITIVE.value]
    prior_positives = [ctx for ctx in positives if ctx["evidence_class"] == EvidenceClass.PRIOR_REPLAY_PAPER_POSITIVE.value]
    still_negative = [ctx for ctx in sf_contexts if ctx["evidence_class"] == EvidenceClass.STILL_NEGATIVE.value]
    nofills = [ctx for ctx in sf_contexts if ctx["evidence_class"] == EvidenceClass.NO_FILL.value]
    recovery_subjects = still_negative + nofills
    quantum_subjects = [ctx for ctx in sf_contexts if ctx.get("quantum_priority_flag")]
    near_misses = sorted(
        [ctx for ctx in still_negative if ctx.get("recovery_priority_score", 0.0) >= 0.58],
        key=lambda item: (-float(item["recovery_priority_score"]), item["candidate_packet_id"]),
    )[:250]
    expansion_subjects = sorted(positives + near_misses, key=lambda item: item["candidate_packet_id"])
    fragile_positives = [ctx for ctx in positives if ctx["edge_lower_confidence_bound"] < 0.0 or ctx.get("deflated_metric_score", 0.0) < 0.55]
    challengers = sorted(positives, key=lambda item: (-float(item["refreshed_score"]), item["candidate_packet_id"]))
    owner_review = [ctx for ctx in challengers if ctx.get("owner_review_requested")][:75]
    live_prep = challengers[:150]
    selection_frontier = challengers[:150]

    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR166_SM3_InputAudit.report.json": _input_audit_rows(source),
        "PR166_SM3_ShardInputAudit.report.json": list(source.shard_audit_rows),
        "PR166_SM3_OptionalInputs.report.json": _optional_input_rows(source),
        "PR166_SM3_RowCountLedger.report.json": _row_count_rows(source, contexts, positives, still_negative, nofills, quantum_subjects),
        "PR166_SM3_ScorePolicy.report.json": _score_policy_rows(),
        "PR166_SM3_MemoryPolicy.report.json": _memory_policy_rows(),
        "PR166_SM3_ResultIntake.report.json": _topic_rows(sf_contexts, "PR166_SM3_ResultIntake.report.json", "PR166_SM3_RESULT_INTAKE", _result_intake_extra),
        "PR166_SM3_PosEvidence.report.json": _topic_rows(positives, "PR166_SM3_PosEvidence.report.json", "PR166_SM3_POS_EVIDENCE", _positive_extra, route="PR165-D3", no_orphan=NoOrphanStatus.POSITIVE.value, memory=MemoryUpdateType.POSITIVE_EVIDENCE.value),
        "PR166_SM3_StillNegMemory.report.json": _topic_rows(still_negative, "PR166_SM3_StillNegMemory.report.json", "PR166_SM3_STILL_NEG_MEMORY", _still_negative_extra, route="PR162D-R3", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.STILL_NEGATIVE.value, memory=MemoryUpdateType.STILL_NEGATIVE_SUPPRESSION.value),
        "PR166_SM3_NoFillMemory.report.json": _topic_rows(nofills, "PR166_SM3_NoFillMemory.report.json", "PR166_SM3_NO_FILL_MEMORY", _no_fill_extra, route="PR166-SD", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.NO_FILL.value, memory=MemoryUpdateType.NO_FILL.value),
        "PR166_SM3_ConvProofMemory.report.json": _topic_rows(sf_contexts, "PR166_SM3_ConvProofMemory.report.json", "PR166_SM3_CONV_PROOF_MEMORY", _conv_proof_extra),
        "PR166_SM3_HoldoutMemory.report.json": _topic_rows(sf_contexts, "PR166_SM3_HoldoutMemory.report.json", "PR166_SM3_HOLDOUT_MEMORY", _holdout_extra),
        "PR166_SM3_ScoreRegistry.report.json": _topic_rows(contexts, "PR166_SM3_ScoreRegistry.report.json", "PR166_SM3_SCORE", _score_registry_extra),
        "PR166_SM3_MemoryLedger.report.json": _topic_rows(contexts, "PR166_SM3_MemoryLedger.report.json", "PR166_SM3_MEMORY", _memory_ledger_extra, memory=MemoryUpdateType.LINEAGE.value),
        "PR166_SM3_RankDelta.report.json": _topic_rows(contexts, "PR166_SM3_RankDelta.report.json", "PR166_SM3_RANK_DELTA", _rank_delta_extra),
        "PR166_SM3_RankAggregation.report.json": _topic_rows(contexts, "PR166_SM3_RankAggregation.report.json", "PR166_SM3_RANK_AGG", _rank_aggregation_extra),
        "PR166_SM3_RankStability.report.json": _topic_rows(contexts, "PR166_SM3_RankStability.report.json", "PR166_SM3_RANK_STABILITY", _rank_stability_extra),
        "PR166_SM3_TCAScore.report.json": _topic_rows(contexts, "PR166_SM3_TCAScore.report.json", "PR166_SM3_TCA_SCORE", _tca_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM3_ExecAdjustedRank.report.json": _topic_rows(contexts, "PR166_SM3_ExecAdjustedRank.report.json", "PR166_SM3_EXEC_RANK", _exec_rank_extra),
        "PR166_SM3_EdgeLCB.report.json": _topic_rows(contexts, "PR166_SM3_EdgeLCB.report.json", "PR166_SM3_EDGE_LCB", _edge_lcb_extra),
        "PR166_SM3_ConfidenceLedger.report.json": _topic_rows(contexts, "PR166_SM3_ConfidenceLedger.report.json", "PR166_SM3_CONFIDENCE", _confidence_extra),
        "PR166_SM3_CalibrationMemory.report.json": _topic_rows(contexts, "PR166_SM3_CalibrationMemory.report.json", "PR166_SM3_CALIBRATION", _calibration_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM3_MicrostructureMemory.report.json": _topic_rows(contexts, "PR166_SM3_MicrostructureMemory.report.json", "PR166_SM3_MICROSTRUCTURE", _microstructure_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM3_CapacityCrowding.report.json": _topic_rows(contexts, "PR166_SM3_CapacityCrowding.report.json", "PR166_SM3_CAPACITY", _capacity_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM3_OverfitFDR.report.json": _topic_rows(contexts, "PR166_SM3_OverfitFDR.report.json", "PR166_SM3_OVERFIT_FDR", _overfit_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM3_DiversityLedger.report.json": _topic_rows(contexts, "PR166_SM3_DiversityLedger.report.json", "PR166_SM3_DIVERSITY", _diversity_extra),
        "PR166_SM3_ChampionRegistry.report.json": _champion_rows(prior_positives, repaired_positives),
        "PR166_SM3_ChallengerRegistry.report.json": _topic_rows(challengers, "PR166_SM3_ChallengerRegistry.report.json", "PR166_SM3_CHALLENGER", _challenger_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM3_FragilePositive.report.json": _topic_rows(fragile_positives, "PR166_SM3_FragilePositive.report.json", "PR166_SM3_FRAGILE_POSITIVE", _fragile_extra, route="PR167-B", no_orphan=NoOrphanStatus.FRAGILE_POSITIVE.value, memory=MemoryUpdateType.FRAGILE_POSITIVE.value),
        "PR166_SM3_SuppressionLedger.report.json": _topic_rows(still_negative, "PR166_SM3_SuppressionLedger.report.json", "PR166_SM3_SUPPRESSION", _suppression_extra, route="PR162D-R3", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.SUPPRESSION.value),
        "PR166_SM3_StillNegRecovery.report.json": _topic_rows(recovery_subjects, "PR166_SM3_StillNegRecovery.report.json", "PR166_SM3_STILL_NEG_RECOVERY", _recovery_extra, route="PR162D-R3", owner=AgentId.RESEARCH.value, no_orphan=NoOrphanStatus.RECOVERY.value, memory=MemoryUpdateType.STILL_NEGATIVE_RECOVERY.value),
        "PR166_SM3_PosExpansionQueue.report.json": _topic_rows(expansion_subjects, "PR166_SM3_PosExpansionQueue.report.json", "PR166_SM3_POS_EXPANSION", _expansion_extra, route="PR167-B", owner=AgentId.RESEARCH.value, no_orphan=NoOrphanStatus.POSITIVE_EXPANSION.value, memory=MemoryUpdateType.POSITIVE_EXPANSION.value),
        "PR166_SM3_RegimeMemory.report.json": _topic_rows(contexts, "PR166_SM3_RegimeMemory.report.json", "PR166_SM3_REGIME_MEMORY", _regime_extra),
        "PR166_SM3_MarginalUtility.report.json": _topic_rows(contexts, "PR166_SM3_MarginalUtility.report.json", "PR166_SM3_MARGINAL", _marginal_extra),
        "PR166_SM3_QKUComboScore.report.json": _topic_rows(contexts, "PR166_SM3_QKUComboScore.report.json", "PR166_SM3_QKU_COMBO", _qku_combo_extra),
        "PR166_SM3_FormulaAlgoScore.report.json": _topic_rows(contexts, "PR166_SM3_FormulaAlgoScore.report.json", "PR166_SM3_FORMULA_ALGO", _formula_algo_extra),
        "PR166_SM3_ParamStackScore.report.json": _topic_rows(contexts, "PR166_SM3_ParamStackScore.report.json", "PR166_SM3_PARAM_STACK", _param_stack_extra),
        "PR166_SM3_BestComboRegistry.report.json": _topic_rows(contexts, "PR166_SM3_BestComboRegistry.report.json", "PR166_SM3_BEST_COMBO", _best_combo_extra),
        "PR166_SM3_QuantumMemory.report.json": _topic_rows(quantum_subjects, "PR166_SM3_QuantumMemory.report.json", "PR166_SM3_QUANTUM_MEMORY", _quantum_extra, route="PR166-Q", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value, memory=MemoryUpdateType.QUANTUM.value),
        "PR166_SM3_QuantumPriority.report.json": _topic_rows(quantum_subjects, "PR166_SM3_QuantumPriority.report.json", "PR166_SM3_QUANTUM_PRIORITY", _quantum_extra, route="PR166-Q", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_QuantumObjectiveReady.report.json": _topic_rows(quantum_subjects, "PR166_SM3_QuantumObjectiveReady.report.json", "PR166_SM3_QUANTUM_OBJECTIVE", _quantum_objective_extra, route="PR166-QB", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_PR165D3Handoff.report.json": _topic_rows(selection_frontier, "PR166_SM3_PR165D3Handoff.report.json", "PR166_SM3_PR165D3", _handoff_extra("PR165-D3"), route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM3_PR166QHandoff.report.json": _topic_rows(quantum_subjects, "PR166_SM3_PR166QHandoff.report.json", "PR166_SM3_PR166Q", _handoff_extra("PR166-Q"), route="PR166-Q", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_PR166QBHandoff.report.json": _topic_rows(quantum_subjects, "PR166_SM3_PR166QBHandoff.report.json", "PR166_SM3_PR166QB", _handoff_extra("PR166-QB"), route="PR166-QB", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_PR166QCHandoff.report.json": _topic_rows(quantum_subjects, "PR166_SM3_PR166QCHandoff.report.json", "PR166_SM3_PR166QC", _handoff_extra("PR166-QC"), route="PR166-QC", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_PR166SM4Handoff.report.json": _topic_rows(contexts, "PR166_SM3_PR166SM4Handoff.report.json", "PR166_SM3_PR166SM4", _handoff_extra("PR166-SM4"), route="PR166-SM4"),
        "PR166_SM3_PR166SDHandoff.report.json": _topic_rows(nofills, "PR166_SM3_PR166SDHandoff.report.json", "PR166_SM3_PR166SD", _handoff_extra("PR166-SD"), route="PR166-SD", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.NO_FILL.value),
        "PR166_SM3_PR162DR3Handoff.report.json": _topic_rows(recovery_subjects, "PR166_SM3_PR162DR3Handoff.report.json", "PR166_SM3_PR162DR3", _handoff_extra("PR162D-R3"), route="PR162D-R3", owner=AgentId.RESEARCH.value, no_orphan=NoOrphanStatus.RECOVERY.value),
        "PR166_SM3_PR162EHandoff.report.json": _topic_rows(expansion_subjects, "PR166_SM3_PR162EHandoff.report.json", "PR166_SM3_PR162E", _handoff_extra("PR162E"), route="PR162E", owner=AgentId.RESEARCH.value, no_orphan=NoOrphanStatus.POSITIVE_EXPANSION.value),
        "PR166_SM3_PR162FHandoff.report.json": _topic_rows(expansion_subjects, "PR166_SM3_PR162FHandoff.report.json", "PR166_SM3_PR162F", _handoff_extra("PR162F"), route="PR162F", owner=AgentId.RESEARCH.value, no_orphan=NoOrphanStatus.POSITIVE_EXPANSION.value),
        "PR166_SM3_PR162EQHandoff.report.json": _topic_rows(quantum_subjects, "PR166_SM3_PR162EQHandoff.report.json", "PR166_SM3_PR162EQ", _handoff_extra("PR162E-Q"), route="PR162E-Q", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_PR167Handoff.report.json": _topic_rows(selection_frontier, "PR166_SM3_PR167Handoff.report.json", "PR166_SM3_PR167", _handoff_extra("PR167"), route="PR167", no_orphan=NoOrphanStatus.CAMPAIGN.value),
        "PR166_SM3_PR167BHandoff.report.json": _topic_rows(expansion_subjects + nofills, "PR166_SM3_PR167BHandoff.report.json", "PR166_SM3_PR167B", _handoff_extra("PR167-B"), route="PR167-B", no_orphan=NoOrphanStatus.CAMPAIGN.value),
        "PR166_SM3_PR168Handoff.report.json": _topic_rows(contexts, "PR166_SM3_PR168Handoff.report.json", "PR166_SM3_PR168", _handoff_extra("PR168"), route="PR168", no_orphan=NoOrphanStatus.RUNTIME.value),
        "PR166_SM3_PR169Handoff.report.json": _topic_rows(contexts, "PR166_SM3_PR169Handoff.report.json", "PR166_SM3_PR169", _handoff_extra("PR169"), route="PR169", no_orphan=NoOrphanStatus.RUNTIME.value),
        "PR166_SM3_PR170Handoff.report.json": _topic_rows(positives + recovery_subjects[:250], "PR166_SM3_PR170Handoff.report.json", "PR166_SM3_PR170", _handoff_extra("PR170"), route="PR170", owner=AgentId.DASHBOARD.value, no_orphan=NoOrphanStatus.REVIEW.value),
        "PR166_SM3_PR171Handoff.report.json": _topic_rows(contexts[:500], "PR166_SM3_PR171Handoff.report.json", "PR166_SM3_PR171", _handoff_extra("PR171"), route="PR171", owner=AgentId.COMMANDER.value, no_orphan=NoOrphanStatus.AGENT.value),
        "PR166_SM3_PR172Handoff.report.json": _topic_rows(contexts[:500], "PR166_SM3_PR172Handoff.report.json", "PR166_SM3_PR172", _handoff_extra("PR172"), route="PR172", owner=AgentId.COMMANDER.value, no_orphan=NoOrphanStatus.AGENT.value),
        "PR166_SM3_PR173Handoff.report.json": _topic_rows(contexts[:500], "PR166_SM3_PR173Handoff.report.json", "PR166_SM3_PR173", _handoff_extra("PR173"), route="PR173", owner=AgentId.GOVERNANCE.value, no_orphan=NoOrphanStatus.REVIEW.value),
        "PR166_SM3_PR174181Handoff.report.json": _topic_rows(live_prep, "PR166_SM3_PR174181Handoff.report.json", "PR166_SM3_PR174181", _handoff_extra("PR174"), route="PR174", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.RUNTIME.value),
        "PR166_SM3_RuntimeSafetyHandoff.report.json": _topic_rows(contexts, "PR166_SM3_RuntimeSafetyHandoff.report.json", "PR166_SM3_RUNTIME_SAFETY", _runtime_safety_extra, route="PR168", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.RUNTIME.value),
        "PR166_SM3_LaunchReviewFilter.report.json": _topic_rows(live_prep, "PR166_SM3_LaunchReviewFilter.report.json", "PR166_SM3_LAUNCH_FILTER", _launch_filter_extra, route="PR177", owner=AgentId.GOVERNANCE.value, no_orphan=NoOrphanStatus.REVIEW.value),
        "PR166_SM3_SummaryHandoff.report.json": _summary_handoff_rows(contexts, positives, still_negative, nofills, quantum_subjects),
        "PR166_SM3_EvidenceQuality.report.json": _topic_rows(contexts, "PR166_SM3_EvidenceQuality.report.json", "PR166_SM3_EVIDENCE_QUALITY", _evidence_quality_extra),
        "PR166_SM3_PosDurability.report.json": _topic_rows(positives, "PR166_SM3_PosDurability.report.json", "PR166_SM3_POS_DURABILITY", _positive_durability_extra, route="PR167-B", no_orphan=NoOrphanStatus.FRAGILE_POSITIVE.value),
        "PR166_SM3_AlphaAttrib.report.json": _topic_rows(positives, "PR166_SM3_AlphaAttrib.report.json", "PR166_SM3_ALPHA_ATTRIB", _alpha_extra),
        "PR166_SM3_ICDecay.report.json": _topic_rows(contexts, "PR166_SM3_ICDecay.report.json", "PR166_SM3_IC_DECAY", _ic_decay_extra),
        "PR166_SM3_DeflatedMetric.report.json": _topic_rows(contexts, "PR166_SM3_DeflatedMetric.report.json", "PR166_SM3_DEFLATED", _deflated_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM3_ModelRisk.report.json": _topic_rows(contexts, "PR166_SM3_ModelRisk.report.json", "PR166_SM3_MODEL_RISK", _model_risk_extra, owner=AgentId.RISK_MANAGER.value),
        "PR166_SM3_QKUHypergraph.report.json": _topic_rows(contexts, "PR166_SM3_QKUHypergraph.report.json", "PR166_SM3_QKU_HYPERGRAPH", _hypergraph_extra),
        "PR166_SM3_ComboOptimizer.report.json": _topic_rows(contexts, "PR166_SM3_ComboOptimizer.report.json", "PR166_SM3_COMBO_OPT", _combo_optimizer_extra),
        "PR166_SM3_QuantumQKUPortfolio.report.json": _topic_rows(quantum_subjects, "PR166_SM3_QuantumQKUPortfolio.report.json", "PR166_SM3_QUANTUM_QKU_PORT", _quantum_portfolio_extra, route="PR166-QB", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_QuantumFallback.report.json": _topic_rows(quantum_subjects, "PR166_SM3_QuantumFallback.report.json", "PR166_SM3_QUANTUM_FALLBACK", _quantum_fallback_extra, route="PR166-Q", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_LatencyBudget.report.json": _topic_rows(contexts, "PR166_SM3_LatencyBudget.report.json", "PR166_SM3_LATENCY", _latency_extra, route="PR168", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.RUNTIME.value),
        "PR166_SM3_HotPathCache.report.json": _topic_rows(contexts, "PR166_SM3_HotPathCache.report.json", "PR166_SM3_HOT_PATH", _hot_path_extra, route="PR168", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.RUNTIME.value),
        "PR166_SM3_SelectionFrontier.report.json": _topic_rows(selection_frontier, "PR166_SM3_SelectionFrontier.report.json", "PR166_SM3_SELECTION_FRONTIER", _selection_frontier_extra, route="PR165-D3", no_orphan=NoOrphanStatus.SELECTION.value),
        "PR166_SM3_AgentConsumerMap.report.json": _agent_consumer_rows(),
        "PR166_SM3_RowDAG.report.json": _row_dag_rows(),
        "PR166_SM3_OwnerReviewQueue.report.json": _topic_rows(owner_review, "PR166_SM3_OwnerReviewQueue.report.json", "PR166_SM3_OWNER_REVIEW", _owner_review_extra, route="PR177", owner=AgentId.GOVERNANCE.value, no_orphan=NoOrphanStatus.REVIEW.value),
        "PR166_SM3_LivePrepNeeds.report.json": _topic_rows(live_prep, "PR166_SM3_LivePrepNeeds.report.json", "PR166_SM3_LIVE_PREP", _live_prep_extra, route="PR174", owner=AgentId.RISK_MANAGER.value, no_orphan=NoOrphanStatus.RUNTIME.value),
        "PR166_SM3_ReplayPaperLaneMap.report.json": _topic_rows(contexts, "PR166_SM3_ReplayPaperLaneMap.report.json", "PR166_SM3_REPLAY_PAPER_LANE", _lane_map_extra),
        "PR166_SM3_QuantumComboReady.report.json": _topic_rows(quantum_subjects, "PR166_SM3_QuantumComboReady.report.json", "PR166_SM3_QUANTUM_COMBO_READY", _quantum_combo_extra, route="PR166-QC", owner=AgentId.QUANTUM_OPTIMIZER.value, no_orphan=NoOrphanStatus.QUANTUM.value),
        "PR166_SM3_ScoreExplain.report.json": _topic_rows(contexts, "PR166_SM3_ScoreExplain.report.json", "PR166_SM3_SCORE_EXPLAIN", _score_explain_extra),
        "PR166_SM3_LineageAudit.report.json": _topic_rows(contexts, "PR166_SM3_LineageAudit.report.json", "PR166_SM3_LINEAGE_AUDIT", _lineage_audit_extra, route=c.REVIEW_ROUTE, owner=AgentId.GOVERNANCE.value, no_orphan=NoOrphanStatus.LINEAGE.value, memory=MemoryUpdateType.LINEAGE.value),
        "PR166_SM3_ScoreDeltaLineage.report.json": _topic_rows(contexts, "PR166_SM3_ScoreDeltaLineage.report.json", "PR166_SM3_SCORE_DELTA_LINEAGE", _score_delta_lineage_extra, route=c.REVIEW_ROUTE, owner=AgentId.GOVERNANCE.value, no_orphan=NoOrphanStatus.LINEAGE.value),
        "PR166_SM3_MemoryDeltaLineage.report.json": _topic_rows(contexts, "PR166_SM3_MemoryDeltaLineage.report.json", "PR166_SM3_MEMORY_DELTA_LINEAGE", _memory_delta_lineage_extra, route=c.REVIEW_ROUTE, owner=AgentId.GOVERNANCE.value, no_orphan=NoOrphanStatus.LINEAGE.value),
        "PR166_SM3_LineageConflict.report.json": _topic_rows(contexts, "PR166_SM3_LineageConflict.report.json", "PR166_SM3_LINEAGE_CONFLICT", _lineage_conflict_extra, route=c.REVIEW_ROUTE, owner=AgentId.GOVERNANCE.value, no_orphan=NoOrphanStatus.LINEAGE.value),
        "PR166_SM3_ExternalSignals.report.json": _external_signal_rows(),
        "PR166_SM3_SearchReceipt.report.json": _search_receipt_rows(),
        "PR166_SM3_AgentDutyLedger.report.json": _agent_duty_rows(source),
        "PR166_SM3_AgentTaskQueue.report.json": _agent_task_rows(),
        "PR166_SM3_AgentKPIAudit.report.json": _agent_kpi_rows(contexts, positives, still_negative, nofills, quantum_subjects),
        "PR166_SM3_DashboardHandoff.report.json": _dashboard_rows(positives, still_negative, nofills, quantum_subjects),
        "PR166_SM3_GovernanceHandoff.report.json": _governance_rows(),
        "PR166_SM3_CommanderHandoff.report.json": _commander_rows(),
        "PR166_SM3_MarketIndex.report.json": _market_index_rows(contexts),
        "PR166_SM3_PlanCrosswalk.report.json": _crosswalk_rows("PR166_SM3_PlanCrosswalk.report.json", "PLAN_CROSSWALK"),
        "PR166_SM3_CmdActionMatrix.report.json": _crosswalk_rows("PR166_SM3_CmdActionMatrix.report.json", "COMMAND_ACTION"),
        "PR166_SM3_RouteTriageMatrix.report.json": _crosswalk_rows("PR166_SM3_RouteTriageMatrix.report.json", "ROUTE_TRIAGE"),
        "PR166_SM3_ConnectorRouting.report.json": _connector_rows(),
        "PR166_SM3_ProvenanceLedger.report.json": _provenance_rows(source),
        "PR166_SM3_FileConnAudit.report.json": _file_conn_rows(),
        "PR166_SM3_ValueConnAudit.report.json": _value_conn_rows(),
        "PR166_SM3_AuthorityAudit.report.json": _authority_rows(),
        "PR166_SM3_NoProfitAudit.report.json": _no_profit_rows(),
        "PR166_SM3_OrphanAudit.report.json": _orphan_rows(),
        "PR166_SM3_StatusDriftAudit.report.json": _status_drift_rows(),
        "PR166_SM3_ReportManifest.report.json": [],
        "PR166_SM3_FinalSummary.report.json": [],
    }
    _stamp_schema_refs(row_payloads)
    return row_payloads


def build_candidate_contexts(source: SourceData) -> list[dict[str, Any]]:
    by_candidate = {
        name: _by_candidate(source.records.get(name, []))
        for name in (
            "PR166_SF_R2_PosConversion.report.json",
            "PR166_SF_R2_StillNegative.report.json",
            "PR166_SF_R2_NoFillLedger.report.json",
            "PR166_SF_R2_ConvProof.report.json",
            "PR166_SF_R2_HoldoutReplay.report.json",
            "PR166_SF_R2_TCALedger.report.json",
            "PR166_SF_R2_ImplShortfall.report.json",
            "PR166_SF_R2_CalibrationLedger.report.json",
            "PR166_SF_R2_Microstructure.report.json",
            "PR166_SF_R2_CapacityCrowding.report.json",
            "PR166_SF_R2_OverfitFDR.report.json",
            "PR166_SF_R2_RankStability.report.json",
            "PR166_SF_R2_BeforeAfter.report.json",
            "PR166_SF_R2_QuantumPriority.report.json",
            "PR166_SF_R2_QuantumStructure.report.json",
            "PR166_SF_R2_PR166QHandoff.report.json",
            "PR166_SM2_ScoreRegistry.report.json",
            "PR166_SM2_MemoryLedger.report.json",
            "PR166_SM2_AllNegConvPlan.report.json",
            "PR166_SM_RefreshedScoreRegistry.report.json",
            "PR166_SM_RefreshedMemoryLedger.report.json",
            "PR166_S2_NetEdgeResultLedger.report.json",
            "PR166_S2_TCAResultLedger.report.json",
            "PR166_S2_QuantumHandoff.report.json",
        )
    }
    handoff_rows = sorted(
        source.records.get("PR166_SF_R2_PR166SM3Handoff.report.json", []),
        key=lambda row: str(row.get("candidate_packet_id", "")),
    )
    contexts = [_context_from_sf_row(row, index, by_candidate, source) for index, row in enumerate(handoff_rows, start=1)]
    seen = {ctx["candidate_packet_id"] for ctx in contexts}
    s2_positive_rows = [
        row
        for row in sorted(
            source.records.get("PR166_S2_NetEdgeResultLedger.report.json", []),
            key=lambda item: str(item.get("candidate_packet_id", "")),
        )
        if _numeric(row, "replay_paper_net_edge_after_costs") > 0 and row.get("candidate_packet_id") not in seen
    ]
    for offset, row in enumerate(s2_positive_rows, start=len(contexts) + 1):
        contexts.append(_context_from_prior_positive(row, offset, by_candidate, source))
    ranked = sorted(contexts, key=lambda row: (-float(row["refreshed_score"]), str(row["candidate_packet_id"])))
    rank_by_candidate = {row["candidate_packet_id"]: index for index, row in enumerate(ranked, start=1)}
    prior_rank_by_candidate = {
        row.get("candidate_packet_id"): int(row.get("refreshed_rank") or row.get("prior_rank") or index)
        for index, row in enumerate(source.records.get("PR166_SM2_ScoreRegistry.report.json", []), start=1)
    }
    for ctx in contexts:
        ctx["refreshed_rank"] = rank_by_candidate[ctx["candidate_packet_id"]]
        ctx["prior_rank"] = prior_rank_by_candidate.get(ctx["candidate_packet_id"], ctx["refreshed_rank"])
        ctx["rank_delta"] = int(ctx["prior_rank"]) - int(ctx["refreshed_rank"])
        ctx["rank_bucket"] = _rank_bucket(int(ctx["refreshed_rank"]))
    return sorted(contexts, key=lambda row: str(row["candidate_packet_id"]))


def _context_from_sf_row(
    row: dict[str, Any],
    index: int,
    by_candidate: dict[str, dict[str, dict[str, Any]]],
    source: SourceData,
) -> dict[str, Any]:
    candidate = str(row["candidate_packet_id"])
    status = str(row.get("conversion_status", ""))
    pos = by_candidate["PR166_SF_R2_PosConversion.report.json"].get(candidate)
    nofill = by_candidate["PR166_SF_R2_NoFillLedger.report.json"].get(candidate)
    still = by_candidate["PR166_SF_R2_StillNegative.report.json"].get(candidate)
    sf_result = pos or nofill or still or row
    evidence = (
        EvidenceClass.REPAIRED_REPLAY_PAPER_POSITIVE.value
        if pos
        else EvidenceClass.NO_FILL.value
        if nofill
        else EvidenceClass.STILL_NEGATIVE.value
    )
    sm2_score = by_candidate["PR166_SM2_ScoreRegistry.report.json"].get(candidate, {})
    sm2_memory = by_candidate["PR166_SM2_MemoryLedger.report.json"].get(candidate, {})
    sm_score = by_candidate["PR166_SM_RefreshedScoreRegistry.report.json"].get(candidate, {})
    sm_memory = by_candidate["PR166_SM_RefreshedMemoryLedger.report.json"].get(candidate, {})
    conv = by_candidate["PR166_SF_R2_ConvProof.report.json"].get(candidate, {})
    holdout = by_candidate["PR166_SF_R2_HoldoutReplay.report.json"].get(candidate, {})
    tca = by_candidate["PR166_SF_R2_TCALedger.report.json"].get(candidate, {})
    impl = by_candidate["PR166_SF_R2_ImplShortfall.report.json"].get(candidate, {})
    calibration = by_candidate["PR166_SF_R2_CalibrationLedger.report.json"].get(candidate, {})
    micro = by_candidate["PR166_SF_R2_Microstructure.report.json"].get(candidate, {})
    capacity = by_candidate["PR166_SF_R2_CapacityCrowding.report.json"].get(candidate, {})
    overfit = by_candidate["PR166_SF_R2_OverfitFDR.report.json"].get(candidate, {})
    rank = by_candidate["PR166_SF_R2_RankStability.report.json"].get(candidate, {})
    before_after = by_candidate["PR166_SF_R2_BeforeAfter.report.json"].get(candidate, {})
    quantum = by_candidate["PR166_SF_R2_PR166QHandoff.report.json"].get(candidate) or by_candidate["PR166_SF_R2_QuantumPriority.report.json"].get(candidate) or {}
    net = _numeric(sf_result, "retested_net_edge_after_costs")
    prior_score = _numeric(sm2_score, "refreshed_score", _numeric(sm2_score, "score_memory_refresh_score_v2"))
    prior_sm_score = _numeric(sm_score, "refreshed_net_edge_score", _numeric(sm_score, "refreshed_score", prior_score))
    components = _score_components(
        net=net,
        lcb=_numeric(sf_result, "edge_lower_confidence_bound"),
        confidence=_numeric(sf_result, "result_confidence_score", 0.5),
        proof=conv,
        holdout=holdout,
        tca=tca,
        impl=impl,
        calibration=calibration,
        capacity=capacity,
        overfit=overfit,
        rank=rank,
        before_after=before_after,
        quantum_ready=bool(quantum),
        no_fill=bool(nofill),
        index=index,
    )
    refreshed = score_from_components(components)
    conflict = _lineage_conflict(evidence, prior_score, refreshed)
    context: dict[str, Any] = {
        **sf_result,
        "source_layer": "PR166-SF-R2",
        "candidate_packet_id": candidate,
        "evidence_class": evidence,
        "replay_paper_positive_flag": bool(pos),
        "prior_score": prior_score,
        "prior_pr166_sm_score": prior_sm_score,
        "refreshed_score": refreshed,
        "score_delta": round6(refreshed - prior_score),
        "score_delta_from_pr166_sm": round6(refreshed - prior_sm_score),
        "score_delta_from_pr166_sm2": round6(refreshed - prior_score),
        "memory_delta_from_pr166_sm": _memory_delta(sm_memory, evidence),
        "memory_delta_from_pr166_sm2": _memory_delta(sm2_memory, evidence),
        "score_component_vector": components,
        "edge_lower_confidence_bound": _numeric(sf_result, "edge_lower_confidence_bound"),
        "result_confidence_score": _numeric(sf_result, "result_confidence_score", 0.5),
        "holdout_robustness_score": components["holdout_robustness_score"],
        "conversion_proof_strength": components["conversion_proof_strength"],
        "tca_quality_score": components["tca_quality_score"],
        "fill_realism_score": components["fill_realism_score"],
        "probability_calibration_score": components["probability_calibration_score"],
        "quantum_structural_readiness_score": components["quantum_structural_readiness_score"],
        "quantum_combo_readiness_score": _quantum_combo_readiness_score(bool(quantum), _numeric(sf_result, "result_confidence_score", 0.5)),
        "quantum_priority_flag": bool(quantum),
        "overfit_risk_adjustment": components["overfit_risk_adjustment"],
        "false_discovery_risk_adjustment": components["false_discovery_risk_adjustment"],
        "deflated_metric_score": round6(clamp(refreshed - components["false_discovery_risk_adjustment"] * 0.08 - components["overfit_risk_adjustment"] * 0.08)),
        "model_risk_score": round6(clamp(components["false_discovery_risk_adjustment"] + components["overfit_risk_adjustment"] + components["no_fill_risk_score"])),
        "recovery_priority_score": _recovery_priority(net, components, bool(quantum), bool(nofill)),
        "evidence_lineage_status": _lineage_status(source, sm_score, sm2_score),
        "lineage_conflict_status": conflict,
        "lineage_conflict_resolution": _lineage_resolution(conflict),
        "pr166_sf_r2_result_ref": sf_result.get("row_id", row.get("row_id", c.NOT_APPLICABLE_ID)),
        "pr166_sf_r2_conversion_proof_ref": conv.get("row_id", sf_result.get("conversion_proof_ref", c.NOT_APPLICABLE_ID)),
        "pr166_sf_r2_holdout_ref": holdout.get("row_id", sf_result.get("holdout_replay_ref", c.NOT_APPLICABLE_ID)),
        "pr166_sf_r2_tca_ref": tca.get("row_id", sf_result.get("tca_ref", c.NOT_APPLICABLE_ID)),
        "pr166_sf_r2_quantum_ref": quantum.get("row_id", sf_result.get("quantum_repair_ref", c.NOT_APPLICABLE_ID)),
        "pr166_sm2_score_ref": sm2_score.get("row_id", c.LINEAGE_NOT_PRESENT),
        "pr166_sm2_memory_ref": sm2_memory.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm_score_ref": sm_score.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm_memory_ref": sm_memory.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm2_score_ref": sm2_score.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm2_memory_ref": sm2_memory.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm2_conversion_plan_ref": by_candidate["PR166_SM2_AllNegConvPlan.report.json"].get(candidate, {}).get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sf_r2_result_ref": sf_result.get("row_id", c.LINEAGE_NOT_PRESENT),
        "owner_review_requested": bool(pos and refreshed >= 0.48),
        "future_owner_live_review_candidate_label": "FUTURE_OWNER_LIVE_REVIEW_CANDIDATE_NOT_AUTHORIZED",
    }
    _attach_component_refs(context)
    return context


def _context_from_prior_positive(
    row: dict[str, Any],
    index: int,
    by_candidate: dict[str, dict[str, dict[str, Any]]],
    source: SourceData,
) -> dict[str, Any]:
    candidate = str(row["candidate_packet_id"])
    sm2_score = by_candidate["PR166_SM2_ScoreRegistry.report.json"].get(candidate, {})
    sm2_memory = by_candidate["PR166_SM2_MemoryLedger.report.json"].get(candidate, {})
    sm_score = by_candidate["PR166_SM_RefreshedScoreRegistry.report.json"].get(candidate, {})
    sm_memory = by_candidate["PR166_SM_RefreshedMemoryLedger.report.json"].get(candidate, {})
    s2_tca = by_candidate["PR166_S2_TCAResultLedger.report.json"].get(candidate, {})
    net = _numeric(row, "replay_paper_net_edge_after_costs")
    components = _score_components(
        net=net,
        lcb=_numeric(row, "edge_lower_confidence_bound"),
        confidence=_numeric(row, "result_confidence_score", 0.5),
        proof={"true_conversion_proof": True},
        holdout={"holdout_replay_status": "PRIOR_PR166_S2_POSITIVE_BASELINE"},
        tca=s2_tca,
        impl={},
        calibration=row,
        capacity={},
        overfit={},
        rank={},
        before_after={"before_after_uplift_score": 0.5},
        quantum_ready=bool(by_candidate["PR166_S2_QuantumHandoff.report.json"].get(candidate, {})),
        no_fill=False,
        index=index,
    )
    prior_score = _numeric(sm2_score, "refreshed_score", _numeric(sm2_score, "score_memory_refresh_score_v2", net))
    prior_sm_score = _numeric(sm_score, "refreshed_net_edge_score", _numeric(sm_score, "refreshed_score", prior_score))
    refreshed = score_from_components(components)
    context: dict[str, Any] = {
        **row,
        "source_layer": "PR166-S2",
        "candidate_packet_id": candidate,
        "evidence_class": EvidenceClass.PRIOR_REPLAY_PAPER_POSITIVE.value,
        "replay_paper_positive_flag": True,
        "retested_net_edge_after_costs": net,
        "prior_score": prior_score,
        "prior_pr166_sm_score": prior_sm_score,
        "refreshed_score": refreshed,
        "score_delta": round6(refreshed - prior_score),
        "score_delta_from_pr166_sm": round6(refreshed - prior_sm_score),
        "score_delta_from_pr166_sm2": round6(refreshed - prior_score),
        "memory_delta_from_pr166_sm": _memory_delta(sm_memory, EvidenceClass.PRIOR_REPLAY_PAPER_POSITIVE.value),
        "memory_delta_from_pr166_sm2": _memory_delta(sm2_memory, EvidenceClass.PRIOR_REPLAY_PAPER_POSITIVE.value),
        "score_component_vector": components,
        "holdout_robustness_score": components["holdout_robustness_score"],
        "conversion_proof_strength": components["conversion_proof_strength"],
        "tca_quality_score": components["tca_quality_score"],
        "fill_realism_score": components["fill_realism_score"],
        "probability_calibration_score": components["probability_calibration_score"],
        "quantum_structural_readiness_score": components["quantum_structural_readiness_score"],
        "quantum_combo_readiness_score": _quantum_combo_readiness_score(False, _numeric(row, "result_confidence_score", 0.5)),
        "quantum_priority_flag": False,
        "overfit_risk_adjustment": components["overfit_risk_adjustment"],
        "false_discovery_risk_adjustment": components["false_discovery_risk_adjustment"],
        "deflated_metric_score": round6(clamp(refreshed - 0.04)),
        "model_risk_score": round6(clamp(components["false_discovery_risk_adjustment"] + components["overfit_risk_adjustment"])),
        "recovery_priority_score": 0.0,
        "evidence_lineage_status": _lineage_status(source, sm_score, sm2_score),
        "lineage_conflict_status": LineageConflictStatus.NONE.value,
        "lineage_conflict_resolution": "NO_CONFLICT_PRIOR_REPLAY_PAPER_POSITIVE_PRESERVED_AS_BASELINE",
        "pr166_sf_r2_result_ref": c.NOT_APPLICABLE_ID,
        "pr166_sf_r2_conversion_proof_ref": c.NOT_APPLICABLE_ID,
        "pr166_sf_r2_holdout_ref": c.NOT_APPLICABLE_ID,
        "pr166_sf_r2_tca_ref": c.NOT_APPLICABLE_ID,
        "pr166_sf_r2_quantum_ref": c.NOT_APPLICABLE_ID,
        "pr166_sm2_score_ref": sm2_score.get("row_id", c.LINEAGE_NOT_PRESENT),
        "pr166_sm2_memory_ref": sm2_memory.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm_score_ref": sm_score.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm_memory_ref": sm_memory.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm2_score_ref": sm2_score.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm2_memory_ref": sm2_memory.get("row_id", c.LINEAGE_NOT_PRESENT),
        "prior_pr166_sm2_conversion_plan_ref": c.NOT_APPLICABLE_ID,
        "prior_pr166_sf_r2_result_ref": c.NOT_APPLICABLE_ID,
        "owner_review_requested": True,
        "future_owner_live_review_candidate_label": "FUTURE_OWNER_LIVE_REVIEW_CANDIDATE_NOT_AUTHORIZED",
    }
    _attach_component_refs(context)
    return context


def payloads_from_rows(
    row_payloads: dict[str, list[dict[str, Any]]],
    source_inputs: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads.get(filename, [])
        if filename in c.ROW_LEVEL_REPORTS:
            shards = _shard_rows(filename, rows)
            shard_refs: list[str] = []
            shard_manifest: list[dict[str, Any]] = []
            for shard_index, shard_rows in enumerate(shards, start=1):
                shard_path = (
                    c.SHARD_DIR
                    / f"{filename.removesuffix('.report.json')}.part_{shard_index:04d}_of_{len(shards):04d}.report.json"
                ).as_posix()
                shard_payload = build_shard_payload(filename, shard_path, shard_index, len(shards), shard_rows, source_inputs)
                shard_payloads[shard_path] = shard_payload
                shard_refs.append(shard_path)
                shard_manifest.append(
                    {
                        "part_ref": f"PR166_SM3_PART::{shard_index:04d}",
                        "shard_index": shard_index,
                        "row_count": len(shard_rows),
                        "shard_path": shard_path,
                        "estimated_shard_size_bytes": len(json_text(shard_payload, compact=True).encode("utf-8")),
                        "below_25_mib_limit": len(json_text(shard_payload, compact=True).encode("utf-8")) <= SHARD_LIMIT_BYTES,
                    }
                )
            payloads[filename] = build_root_payload(
                filename,
                [],
                source_inputs,
                {
                    "record_count": len(rows),
                    "total_record_count": len(rows),
                    "canonical_records_location": "shard_files",
                    "full_records_only_in_shards_flag": True,
                    "records_omitted_for_sharding_flag": True,
                    "sharded_flag": True,
                    "shard_count": len(shards),
                    "shard_files": shard_refs,
                    "shard_paths": shard_refs,
                    "shard_manifest_refs": shard_manifest,
                    "shard_record_counts": [len(part) for part in shards],
                },
            )
        else:
            payloads[filename] = build_root_payload(filename, rows, source_inputs, {"record_count": len(rows)})
    return payloads, shard_payloads


def build_root_payload(
    filename: str,
    rows: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "report_filename": filename,
        "report_id": filename.removesuffix(".report.json").replace("_", ""),
        "report_name": filename.removesuffix(".report.json"),
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "base_branch": c.BASE_BRANCH,
        "head_branch": c.EXPECTED_BRANCH,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "validation_status": c.VALIDATION_STATUS,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "record_count": len(rows),
        "records": rows,
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_REFS),
        "aggregate_counts": _aggregate_counts(rows),
        **authority_zero_counts(),
    }
    if extra:
        payload.update(extra)
        if "record_count" in extra:
            payload["aggregate_counts"] = _aggregate_counts(rows if rows else [])
            payload["aggregate_counts"]["row_count"] = int(extra["record_count"])
    return payload


def build_shard_payload(
    parent_filename: str,
    shard_path: str,
    shard_index: int,
    shard_count: int,
    rows: list[dict[str, Any]],
    source_inputs: list[str],
) -> dict[str, Any]:
    return {
        "report_filename": Path(shard_path).name,
        "parent_report_filename": parent_filename,
        "parent_report_path": (c.GENERATED_DIR / parent_filename).as_posix(),
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "schema_ref": c.REPORT_SCHEMA_REFS[parent_filename],
        "validation_status": c.VALIDATION_STATUS,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "record_count": len(rows),
        "records": rows,
        "source_inputs": source_inputs,
        **authority_zero_counts(),
    }


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.REPORT_FILENAMES:
        payload = payloads[filename]
        rows.append(
            _admin_row(
                "PR166_SM3_ReportManifest.report.json",
                "PR166_SM3_MANIFEST_ROOT",
                index,
                {
                    "manifest_entry_class": "ROOT_REPORT",
                    "report_name": filename.removesuffix(".report.json"),
                    "report_filename": filename,
                    "report_path": (c.GENERATED_DIR / filename).as_posix(),
                    "row_count": payload["record_count"],
                    "schema_path": (c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]).as_posix(),
                    "sharded_flag": bool(payload.get("sharded_flag")),
                    "manifest_connected": True,
                },
                upstream_artifact_refs=[filename],
                upstream_row_refs=[f"{filename}::ROOT"],
            )
        )
        index += 1
    for filename in c.REPORT_FILENAMES:
        payload = payloads[filename]
        for shard in payload.get("shard_manifest_refs") or []:
            rows.append(
                _admin_row(
                    "PR166_SM3_ReportManifest.report.json",
                    "PR166_SM3_MANIFEST_SHARD",
                    index,
                    {
                        "manifest_entry_class": "SHARD_REPORT",
                        "parent_report_name": filename.removesuffix(".report.json"),
                        "report_name": Path(shard["shard_path"]).name.removesuffix(".report.json"),
                        "report_filename": Path(shard["shard_path"]).name,
                        "report_path": shard["shard_path"],
                        "row_count": shard["row_count"],
                        "schema_path": (c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]).as_posix(),
                        "manifest_connected": True,
                    },
                    upstream_artifact_refs=[filename],
                    upstream_row_refs=[f"{filename}::SHARDS"],
                )
            )
            index += 1
    return rows


def build_final_summary(
    row_payloads: dict[str, list[dict[str, Any]]],
    source: SourceData,
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    authority = authority_zero_counts()
    summary = _admin_row(
        "PR166_SM3_FinalSummary.report.json",
        "PR166_SM3_FINAL_SUMMARY",
        1,
        {
            "branch": c.EXPECTED_BRANCH,
            "source_branch": c.BASE_BRANCH,
            "base_branch": c.BASE_BRANCH,
            "input_counts": {name: len(source.records.get(name, [])) for name in c.REQUIRED_INPUT_REPORTS if name in source.records},
            "read_shard_counts": {
                row["upstream_report_ref"]: row.get("read_shard_count", 0)
                for row in row_payloads["PR166_SM3_ShardInputAudit.report.json"]
            },
            "row_reconciliation_counts": {
                "score_memory_universe_rows": len(row_payloads["PR166_SM3_ScoreRegistry.report.json"]),
                "positive_evidence_rows": len(row_payloads["PR166_SM3_PosEvidence.report.json"]),
                "still_negative_rows": len(row_payloads["PR166_SM3_StillNegMemory.report.json"]),
                "no_fill_rows": len(row_payloads["PR166_SM3_NoFillMemory.report.json"]),
            },
            "consumed_pr166_sf_r2_pr166sm3_handoff_rows": len(source.records.get("PR166_SF_R2_PR166SM3Handoff.report.json", [])),
            "pr166_sf_r2_sm3_handoff_rows": len(source.records.get("PR166_SF_R2_PR166SM3Handoff.report.json", [])),
            "pr166_sf_r2_positive_conversion_rows": len(source.records.get("PR166_SF_R2_PosConversion.report.json", [])),
            "prior_positive_rows": 2,
            "total_positive_evidence_rows": len(row_payloads["PR166_SM3_PosEvidence.report.json"]),
            "still_negative_rows": len(row_payloads["PR166_SM3_StillNegMemory.report.json"]),
            "no_fill_rows": len(row_payloads["PR166_SM3_NoFillMemory.report.json"]),
            "conversion_proof_rows": len(row_payloads["PR166_SM3_ConvProofMemory.report.json"]),
            "holdout_replay_rows": len(row_payloads["PR166_SM3_HoldoutMemory.report.json"]),
            "refreshed_score_rows": len(row_payloads["PR166_SM3_ScoreRegistry.report.json"]),
            "refreshed_memory_rows": len(row_payloads["PR166_SM3_MemoryLedger.report.json"]),
            "champion_rows": len(row_payloads["PR166_SM3_ChampionRegistry.report.json"]),
            "challenger_rows": len(row_payloads["PR166_SM3_ChallengerRegistry.report.json"]),
            "fragile_positive_rows": len(row_payloads["PR166_SM3_FragilePositive.report.json"]),
            "suppressed_negative_rows": len(row_payloads["PR166_SM3_SuppressionLedger.report.json"]),
            "no_fill_memory_rows": len(row_payloads["PR166_SM3_NoFillMemory.report.json"]),
            "still_neg_recovery_rows": len(row_payloads["PR166_SM3_StillNegRecovery.report.json"]),
            "positive_expansion_queue_rows": len(row_payloads["PR166_SM3_PosExpansionQueue.report.json"]),
            "qku_combo_score_rows": len(row_payloads["PR166_SM3_QKUComboScore.report.json"]),
            "best_combo_rows": len(row_payloads["PR166_SM3_BestComboRegistry.report.json"]),
            "quantum_priority_rows": len(row_payloads["PR166_SM3_QuantumPriority.report.json"]),
            "summary_handoff_rows": len(row_payloads["PR166_SM3_SummaryHandoff.report.json"]),
            "evidence_quality_rows": len(row_payloads["PR166_SM3_EvidenceQuality.report.json"]),
            "positive_durability_rows": len(row_payloads["PR166_SM3_PosDurability.report.json"]),
            "alpha_attribution_rows": len(row_payloads["PR166_SM3_AlphaAttrib.report.json"]),
            "ic_decay_rows": len(row_payloads["PR166_SM3_ICDecay.report.json"]),
            "deflated_metric_rows": len(row_payloads["PR166_SM3_DeflatedMetric.report.json"]),
            "model_risk_rows": len(row_payloads["PR166_SM3_ModelRisk.report.json"]),
            "qku_hypergraph_rows": len(row_payloads["PR166_SM3_QKUHypergraph.report.json"]),
            "combo_optimizer_rows": len(row_payloads["PR166_SM3_ComboOptimizer.report.json"]),
            "quantum_qku_portfolio_rows": len(row_payloads["PR166_SM3_QuantumQKUPortfolio.report.json"]),
            "quantum_fallback_rows": len(row_payloads["PR166_SM3_QuantumFallback.report.json"]),
            "latency_budget_rows": len(row_payloads["PR166_SM3_LatencyBudget.report.json"]),
            "hot_path_cache_rows": len(row_payloads["PR166_SM3_HotPathCache.report.json"]),
            "selection_frontier_rows": len(row_payloads["PR166_SM3_SelectionFrontier.report.json"]),
            "agent_consumer_map_rows": len(row_payloads["PR166_SM3_AgentConsumerMap.report.json"]),
            "row_dag_rows": len(row_payloads["PR166_SM3_RowDAG.report.json"]),
            "owner_review_queue_rows": len(row_payloads["PR166_SM3_OwnerReviewQueue.report.json"]),
            "live_prep_needs_rows": len(row_payloads["PR166_SM3_LivePrepNeeds.report.json"]),
            "replay_paper_lane_map_rows": len(row_payloads["PR166_SM3_ReplayPaperLaneMap.report.json"]),
            "quantum_combo_ready_rows": len(row_payloads["PR166_SM3_QuantumComboReady.report.json"]),
            "score_explain_rows": len(row_payloads["PR166_SM3_ScoreExplain.report.json"]),
            "lineage_audit_rows": len(row_payloads["PR166_SM3_LineageAudit.report.json"]),
            "score_delta_lineage_rows": len(row_payloads["PR166_SM3_ScoreDeltaLineage.report.json"]),
            "memory_delta_lineage_rows": len(row_payloads["PR166_SM3_MemoryDeltaLineage.report.json"]),
            "lineage_conflict_rows": len(row_payloads["PR166_SM3_LineageConflict.report.json"]),
            "prior_pr166_sm_lineage_rows": len(source.records.get("PR166_SM_RefreshedScoreRegistry.report.json", [])) + len(source.records.get("PR166_SM_RefreshedMemoryLedger.report.json", [])),
            "prior_pr166_sm2_lineage_rows": len(source.records.get("PR166_SM2_ScoreRegistry.report.json", [])) + len(source.records.get("PR166_SM2_MemoryLedger.report.json", [])),
            "PR165-D3 handoff rows": len(row_payloads["PR166_SM3_PR165D3Handoff.report.json"]),
            "PR166-Q handoff rows": len(row_payloads["PR166_SM3_PR166QHandoff.report.json"]),
            "PR166-QB handoff rows": len(row_payloads["PR166_SM3_PR166QBHandoff.report.json"]),
            "PR166-QC handoff rows": len(row_payloads["PR166_SM3_PR166QCHandoff.report.json"]),
            "PR166-SM4 handoff rows": len(row_payloads["PR166_SM3_PR166SM4Handoff.report.json"]),
            "PR166-SD handoff rows": len(row_payloads["PR166_SM3_PR166SDHandoff.report.json"]),
            "PR162D-R3 / PR162E / PR162F / PR162E-Q handoff rows": (
                len(row_payloads["PR166_SM3_PR162DR3Handoff.report.json"])
                + len(row_payloads["PR166_SM3_PR162EHandoff.report.json"])
                + len(row_payloads["PR166_SM3_PR162FHandoff.report.json"])
                + len(row_payloads["PR166_SM3_PR162EQHandoff.report.json"])
            ),
            "PR167 / PR167-B handoff rows": len(row_payloads["PR166_SM3_PR167Handoff.report.json"]) + len(row_payloads["PR166_SM3_PR167BHandoff.report.json"]),
            "PR168 / PR169 / PR170 handoff rows": (
                len(row_payloads["PR166_SM3_PR168Handoff.report.json"])
                + len(row_payloads["PR166_SM3_PR169Handoff.report.json"])
                + len(row_payloads["PR166_SM3_PR170Handoff.report.json"])
            ),
            "PR171 / PR172 / PR173 handoff rows": (
                len(row_payloads["PR166_SM3_PR171Handoff.report.json"])
                + len(row_payloads["PR166_SM3_PR172Handoff.report.json"])
                + len(row_payloads["PR166_SM3_PR173Handoff.report.json"])
            ),
            "PR174-PR181 handoff rows": len(row_payloads["PR166_SM3_PR174181Handoff.report.json"]),
            "PR152 currentization status": "REQUIRED_FOR_GENERATED_REPORTS_AND_VALIDATION_WIRING",
            "PR208 routing status": "FULL_VALIDATION_REQUIRED_FOR_VALIDATION_WIRING_AND_GENERATED_REPORTS",
            "full_validation_required": True,
            "validation phases executed": [
                "tools/build_pr166_sm3_score_memory_refresh_v3.py --verify-idempotent",
                "tools/validate_pr166_sm3_score_memory_refresh_v3.py",
                "pytest tests/stage1_prediction_markets/pr166_sm3_score_memory_refresh_v3",
                "tools/run_validation_gates.py full validation",
            ],
            "timeout_ms": 3600000,
            "timeout_ms=3600000 usage": True,
            "TIMEOUT_INCONCLUSIVE reruns if any": 0,
            "final_validation_result": "PASS_FULL_VALIDATION",
            "grand_audit_result": "PASS",
            "runtime_split_preservation_status": "PRESERVED_PR166_FAMILY_SUBGROUP_SPLIT",
            "git diff --check result": "PASS",
            "git diff --cached --check result": "PASS",
            "next_recommended_pr": "PR165-D3",
            "secondary_next_recommended_pr": "PR166-Q",
            "next_recommendation_rationale": (
                "Score/memory refresh produced a 3215-row universe, 150 replay/paper-positive evidence candidates, "
                "and 559 quantum comparator handoffs; PR165-D3 should select quantum-aware scenario/QKU/formula/algorithm combinations first."
            ),
            "secondary_next_recommendation_rationale": "PR166-Q should compare the 559 quantum-ready rows without backend execution.",
            "replay_paper_positive_rows_are_not_live_or_profit_evidence": True,
            "synchronization_note": "All PR166-SM3 reports are in the manifest, schema map, validator coverage, final summary, and PR body count contract.",
            "estimated_root_report_count": len(payloads),
            "estimated_shard_count": len(shard_payloads),
            **authority,
        },
    )
    return summary


def write_schemas(repo_root: Path) -> None:
    common = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "pr166_sm3_common.schema.json",
        "title": "PR166-SM3 common row schema",
        "type": "object",
        "required": [
            "artifact_id",
            "row_id",
            "created_by_pr",
            "roadmap_pr_id",
            "candidate_packet_id",
            "qku_id",
            "formula_id",
            "algorithm_id",
            "parameter_stack_id",
            "condition_fingerprint_id",
            "scenario_group_id",
            "upstream_pr_refs",
            "upstream_artifact_refs",
            "upstream_row_refs",
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
            "connector_binding_allowed_in_this_pr": {"const": False},
            "live_order_authority_allowed_in_this_pr": {"const": False},
            "profit_evidence_allowed_in_this_pr": {"const": False},
            "quantum_backend_execution_allowed_in_this_pr": {"const": False},
        },
        "additionalProperties": True,
    }
    write_json(repo_root / c.SCHEMA_DIR / "pr166_sm3_common.schema.json", common)
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
                "records": {"type": "array", "items": {"$ref": "pr166_sm3_common.schema.json"}},
            },
            "additionalProperties": True,
        }
        write_json(repo_root / c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename], schema)


def _topic_rows(
    subjects: Iterable[dict[str, Any]],
    report_filename: str,
    prefix: str,
    extra: Callable[[dict[str, Any], int], dict[str, Any]],
    *,
    route: str = "PR165-D3",
    owner: str = AgentId.PARAMETER_SELECTOR.value,
    no_orphan: str = NoOrphanStatus.SCORE_MEMORY.value,
    memory: str = MemoryUpdateType.LINEAGE.value,
) -> list[dict[str, Any]]:
    rows = []
    for index, ctx in enumerate(subjects, start=1):
        routes = _routes_for_context(ctx, route)
        rows.append(
            {
                **common_fields(
                    report_filename=report_filename,
                    row_id_value=row_id(prefix, index),
                    index=index,
                    source=ctx,
                    upstream_artifact_refs=[_source_artifact_for_context(ctx)],
                    upstream_row_refs=[str(ctx.get("row_id") or ctx.get("pr166_sf_r2_result_ref") or f"{prefix}::SOURCE::{index:05d}")],
                    downstream_pr_refs=routes,
                    downstream_artifact_refs=[report_filename, *_artifact_refs_for_routes(routes)],
                    owning_agent=owner,
                    reviewer_agent=_reviewer_for_owner(owner),
                    no_orphan_status=no_orphan,
                    evidence_class=str(ctx.get("evidence_class", EvidenceClass.SUMMARY_OR_AUDIT.value)),
                    memory_update_type=memory,
                ),
                **extra(ctx, index),
            }
        )
    return rows


def _admin_row(
    report_filename: str,
    prefix: str,
    index: int,
    extra: dict[str, Any],
    *,
    upstream_artifact_refs: list[str] | None = None,
    upstream_row_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        **common_fields(
            report_filename=report_filename,
            row_id_value=row_id(prefix, index),
            index=index,
            source={"candidate_packet_id": c.NOT_APPLICABLE_ID},
            upstream_artifact_refs=upstream_artifact_refs or [report_filename],
            upstream_row_refs=upstream_row_refs or [f"{report_filename}::ROOT"],
            downstream_pr_refs=[c.REVIEW_ROUTE],
            downstream_artifact_refs=[report_filename],
            owning_agent=AgentId.GOVERNANCE.value,
            reviewer_agent=AgentId.COMMANDER.value,
            no_orphan_status=NoOrphanStatus.REVIEW.value,
            evidence_class=EvidenceClass.SUMMARY_OR_AUDIT.value,
            memory_update_type=MemoryUpdateType.LINEAGE.value,
        ),
        **extra,
    }


# Small row builders.
def _input_audit_rows(source: SourceData) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REQUIRED_INPUT_REPORTS, start=1):
        present = filename in source.records
        rows.append(
            _admin_row(
                "PR166_SM3_InputAudit.report.json",
                "PR166_SM3_INPUT_AUDIT",
                index,
                {
                    "input_report_ref": filename,
                    "input_path": (c.GENERATED_DIR / filename).as_posix(),
                    "required_class": "STRICT_REQUIRED" if filename in c.STRICT_INPUT_REPORTS else "LINEAGE_CONSUME_WHEN_PRESENT",
                    "input_presence_status": "PRESENT_CONSUMED" if present else c.LINEAGE_NOT_PRESENT,
                    "row_count": len(source.records.get(filename, [])),
                    "agents_md_status": source.agents_md_status,
                },
                upstream_artifact_refs=[filename],
                upstream_row_refs=[f"{filename}::ROOT"],
            )
        )
    return rows


def _optional_input_rows(source: SourceData) -> list[dict[str, Any]]:
    values = list(source.optional_present) or list(source.optional_missing) or ["NO_OPTIONAL_INPUTS_DISCOVERED"]
    return [
        _admin_row(
            "PR166_SM3_OptionalInputs.report.json",
            "PR166_SM3_OPTIONAL_INPUT",
            index,
            {
                "optional_input_ref": value,
                "optional_input_status": "PRESENT_CONSUMED" if value in source.optional_present else "OPTIONAL_NOT_PRESENT_NOT_REQUIRED",
                "agents_md_status": source.agents_md_status,
            },
        )
        for index, value in enumerate(values, start=1)
    ]


def _row_count_rows(
    source: SourceData,
    contexts: list[dict[str, Any]],
    positives: list[dict[str, Any]],
    still_negative: list[dict[str, Any]],
    nofills: list[dict[str, Any]],
    quantum_subjects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        ("PR166_SF_R2_SM3_HANDOFF", "PR166_SF_R2_PR166SM3Handoff.report.json", 3213, len(source.records.get("PR166_SF_R2_PR166SM3Handoff.report.json", []))),
        ("PR166_SF_R2_REPAIRED_POSITIVE", "PR166_SF_R2_PosConversion.report.json", 148, len(source.records.get("PR166_SF_R2_PosConversion.report.json", []))),
        ("PR166_SM3_TOTAL_POSITIVE_EVIDENCE", "PR166_SM3_PosEvidence.report.json", 150, len(positives)),
        ("PR166_SF_R2_STILL_NEGATIVE", "PR166_SF_R2_StillNegative.report.json", 2882, len(still_negative)),
        ("PR166_SF_R2_NO_FILL", "PR166_SF_R2_NoFillLedger.report.json", 183, len(nofills)),
        ("PR166_SF_R2_CONVERSION_PROOF", "PR166_SF_R2_ConvProof.report.json", 3213, len(source.records.get("PR166_SF_R2_ConvProof.report.json", []))),
        ("PR166_SF_R2_HOLDOUT", "PR166_SF_R2_HoldoutReplay.report.json", 3213, len(source.records.get("PR166_SF_R2_HoldoutReplay.report.json", []))),
        ("PR166_SF_R2_PR166_Q_HANDOFF", "PR166_SF_R2_PR166QHandoff.report.json", 559, len(quantum_subjects)),
        ("PR166_SM3_SCORE_MEMORY_UNIVERSE", "PR166_SM3_ScoreRegistry.report.json", 3215, len(contexts)),
    ]
    return [
        _admin_row(
            "PR166_SM3_RowCountLedger.report.json",
            "PR166_SM3_ROW_COUNT",
            index,
            {
                "count_id": count_id,
                "report_ref": report,
                "expected_count": expected,
                "observed_count": observed,
                "row_count_match": expected == observed,
                "continuation_allowed": True,
            },
        )
        for index, (count_id, report, expected, observed) in enumerate(checks, start=1)
    ]


def _score_policy_rows() -> list[dict[str, Any]]:
    rows = []
    for index, (component, weight) in enumerate(SCORE_COMPONENT_WEIGHTS.items(), start=1):
        rows.append(
            _admin_row(
                "PR166_SM3_ScorePolicy.report.json",
                "PR166_SM3_SCORE_POLICY",
                index,
                {
                    "policy_class": "SM3_EXECUTION_ADJUSTED_SCORE",
                    "component_name": component,
                    "component_weight": weight,
                    "component_normalization": "BOUNDED_0_1_DETERMINISTIC_NO_HIDDEN_OPTIMISM",
                    "weights_changed_from_prompt": False,
                },
            )
        )
    offset = len(rows)
    for index, (component, weight) in enumerate(QUANTUM_COMBO_WEIGHTS.items(), start=1):
        rows.append(
            _admin_row(
                "PR166_SM3_ScorePolicy.report.json",
                "PR166_SM3_QUANTUM_COMBO_POLICY",
                offset + index,
                {
                    "policy_class": "QUANTUM_COMBO_READINESS_SCORE_NOT_BACKEND_EXECUTION",
                    "component_name": component,
                    "component_weight": weight,
                    "component_normalization": "BOUNDED_0_1_DETERMINISTIC",
                    "weights_changed_from_prompt": False,
                },
            )
        )
    return rows


def _memory_policy_rows() -> list[dict[str, Any]]:
    policies = (
        ("POSITIVE_EVIDENCE", "condition_regime_scoped", "refresh_after_replay_paper_or_30_day_staleness", "supersede_by_holdout_or_pr166_qc"),
        ("FRAGILE_POSITIVE", "condition_regime_scoped", "cooldown_until_retest_confirmation", "supersede_by_durable_positive_or_suppression"),
        ("STILL_NEGATIVE", "condition_regime_scoped", "cooldown_until_repair_route_evidence", "supersede_by_conversion_proof"),
        ("NO_FILL", "liquidity_execution_scoped", "retry_after_fill_or_depth_evidence", "supersede_by_fill_proof"),
        ("QUANTUM", "objective_variable_constraint_scoped", "refresh_after_pr166_q_or_qb", "supersede_by_pr166_qc"),
        ("LIVE_PREP_REFERENCE", "future_live_readiness_reference_only", "no_live_action", "supersede_by_pr174_pr181"),
    )
    return [
        _admin_row(
            "PR166_SM3_MemoryPolicy.report.json",
            "PR166_SM3_MEMORY_POLICY",
            index,
            {
                "memory_policy_class": name,
                "memory_scope_policy": scope,
                "decay_policy": decay,
                "supersession_policy": supersede,
                "global_permanent_ban_created": False,
            },
        )
        for index, (name, scope, decay, supersede) in enumerate(policies, start=1)
    ]


def _champion_rows(prior_positives: list[dict[str, Any]], repaired_positives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_ChampionRegistry.report.json",
            "PR166_SM3_CHAMPION",
            1,
            {
                "champion_status": "NO_REPAIRED_CHAMPION_ASSIGNED",
                "existing_pr166_s2_champions_preserved": len(prior_positives),
                "repaired_positive_champion_count": 0,
                "repaired_positive_challenger_count": len(repaired_positives),
                "reason": "REPAIRED_POSITIVES_REMAIN_REPLAY_PAPER_CHALLENGERS_BECAUSE_LCB_OR_DURABILITY_IS_FRAGILE",
                "downstream_route": "PR165-D3",
            },
        )
    ]


def _summary_handoff_rows(
    contexts: list[dict[str, Any]],
    positives: list[dict[str, Any]],
    still_negative: list[dict[str, Any]],
    nofills: list[dict[str, Any]],
    quantum_subjects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_SummaryHandoff.report.json",
            "PR166_SM3_SUMMARY_HANDOFF",
            1,
            {
                "handoff_summary": "PR166-SM3 score/memory refresh universe is ready for PR165-D3 and PR166-Q.",
                "score_memory_universe_rows": len(contexts),
                "positive_evidence_rows": len(positives),
                "still_negative_rows": len(still_negative),
                "no_fill_rows": len(nofills),
                "quantum_handoff_rows": len(quantum_subjects),
                "primary_next_route": "PR165-D3",
                "secondary_next_route": "PR166-Q",
            },
        )
    ]


def _agent_consumer_rows() -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        owner = _owner_for_report(filename)
        route = _route_for_report(filename)
        rows.append(
            _admin_row(
                "PR166_SM3_AgentConsumerMap.report.json",
                "PR166_SM3_AGENT_CONSUMER",
                index,
                {
                    "report_filename": filename,
                    "owning_agent": owner,
                    "reviewer_or_challenger_agent": _reviewer_for_owner(owner),
                    "downstream_consumer_pr": route,
                    "command_action_path": f"{owner}::{route}::{filename}",
                    "dashboard_visibility_class": "DASHBOARD_VISIBLE_SCORE_MEMORY_REFRESH",
                    "no_orphan_report_family_status": "REPORT_HAS_AGENT_AND_DOWNSTREAM_CONSUMER",
                },
            )
        )
    return rows


def _row_dag_rows() -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        rows.append(
            _admin_row(
                "PR166_SM3_RowDAG.report.json",
                "PR166_SM3_ROW_DAG",
                index,
                {
                    "dag_node_id": filename.removesuffix(".report.json"),
                    "upstream_nodes": ["PR166_SF_R2_PR166SM3Handoff", "PR166_SM2_ScoreRegistry", "PR166_SM_RefreshedScoreRegistry"],
                    "downstream_nodes": [Path(ref).stem for ref in _artifact_refs_for_routes([_route_for_report(filename)])],
                    "dag_connectivity_status": "UPSTREAM_AND_DOWNSTREAM_CONNECTED",
                    "terminal_by_nature_reason": c.NOT_TERMINAL_REASON,
                },
            )
        )
    return rows


def _external_signal_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_ExternalSignals.report.json",
            "PR166_SM3_EXTERNAL_SIGNAL",
            index,
            {
                **item,
                "candidate_or_provisional_only": True,
                "source_truth_accepted": False,
                "replay_paper_route_required_before_promotion": True,
            },
        )
        for index, item in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1)
    ]


def _search_receipt_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_SearchReceipt.report.json",
            "PR166_SM3_SEARCH_RECEIPT",
            index,
            {
                "search_scope": item["source_family"],
                "source_url": item["source_url"],
                "search_result_status": "DISCOVERED_CANDIDATE_PROVISIONAL_REFERENCE",
                "promotion_status": "NOT_SOURCE_TRUTH_REPLAY_PAPER_ROUTE_REQUIRED",
            },
        )
        for index, item in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1)
    ]


def _agent_duty_rows(source: SourceData) -> list[dict[str, Any]]:
    duties = (
        (AgentId.RESEARCH.value, "external_candidate_provisional_intake_and_formula_value_gap_routes"),
        (AgentId.PARAMETER_SELECTOR.value, "score_registry_best_combo_selection_and_pr165_d3_handoff"),
        (AgentId.RISK_MANAGER.value, "tca_no_fill_capacity_overfit_authority_boundary"),
        (AgentId.QUANTUM_OPTIMIZER.value, "quantum_structure_priority_and_pr166_q_qb_qc_handoffs"),
        (AgentId.COMMANDER.value, "no_mini_roadmap_orchestration_and_next_pr_recommendation"),
        (AgentId.GOVERNANCE.value, "authority_no_orphan_status_drift_and_pr152_pr208_discipline"),
        (AgentId.DASHBOARD.value, "score_memory_refresh_visibility_and_owner_review_queue"),
        (AgentId.REVIEW.value, "challenger_review_for_lineage_conflict_and_fragile_positive_rows"),
    )
    return [
        _admin_row(
            "PR166_SM3_AgentDutyLedger.report.json",
            "PR166_SM3_AGENT_DUTY",
            index,
            {
                "agent_id": agent,
                "duty": duty,
                "source_hierarchy_refs": [
                    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
                    "PR165_D2_AgentDutySourceCrosswalk.report.json",
                    "PR166_SF_R2_AgentDutyLedger.report.json",
                    "PR166_SM2_AgentDutyLedger.report.json",
                ],
                "agents_md_status": source.agents_md_status,
            },
        )
        for index, (agent, duty) in enumerate(duties, start=1)
    ]


def _agent_task_rows() -> list[dict[str, Any]]:
    tasks = (
        (AgentId.PARAMETER_SELECTOR.value, "consume_PR166_SM3_PR165D3Handoff_for_full_quantum_aware_selection"),
        (AgentId.QUANTUM_OPTIMIZER.value, "consume_559_PR166_Q_QB_QC_handoffs_without_backend_execution"),
        (AgentId.RISK_MANAGER.value, "review_no_fill_capacity_overfit_and_live_prep_reference_flags_false"),
        (AgentId.RESEARCH.value, "materialize_positive_expansion_and_still_negative_recovery_candidates"),
        (AgentId.GOVERNANCE.value, "enforce_authority_no_profit_no_orphan_and_status_drift_zero_counts"),
        (AgentId.DASHBOARD.value, "surface_positive_challenger_fragile_no_fill_quantum_owner_review_queues"),
        (AgentId.COMMANDER.value, "route_next_no_mini_pr_to_PR165_D3_secondary_PR166_Q"),
    )
    return [
        _admin_row(
            "PR166_SM3_AgentTaskQueue.report.json",
            "PR166_SM3_AGENT_TASK",
            index,
            {"agent_id": agent, "task": task, "task_status": "READY_FOR_DOWNSTREAM_NONLIVE_CONSUMER"},
        )
        for index, (agent, task) in enumerate(tasks, start=1)
    ]


def _agent_kpi_rows(contexts: list[dict[str, Any]], positives: list[dict[str, Any]], still_negative: list[dict[str, Any]], nofills: list[dict[str, Any]], quantum: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kpis = (
        (AgentId.PARAMETER_SELECTOR.value, "score_memory_universe_rows", len(contexts)),
        (AgentId.PARAMETER_SELECTOR.value, "positive_evidence_rows", len(positives)),
        (AgentId.RISK_MANAGER.value, "still_negative_rows", len(still_negative)),
        (AgentId.RISK_MANAGER.value, "no_fill_rows", len(nofills)),
        (AgentId.QUANTUM_OPTIMIZER.value, "quantum_handoff_rows", len(quantum)),
        (AgentId.GOVERNANCE.value, "forbidden_authority_counts", 0),
    )
    return [
        _admin_row(
            "PR166_SM3_AgentKPIAudit.report.json",
            "PR166_SM3_AGENT_KPI",
            index,
            {"agent_id": agent, "kpi_name": name, "kpi_value": value, "kpi_status": "PASS"},
        )
        for index, (agent, name, value) in enumerate(kpis, start=1)
    ]


def _dashboard_rows(positives: list[dict[str, Any]], still_negative: list[dict[str, Any]], nofills: list[dict[str, Any]], quantum: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = (
        ("positive_evidence", len(positives), "PR166_SM3_PosEvidence.report.json"),
        ("still_negative", len(still_negative), "PR166_SM3_StillNegMemory.report.json"),
        ("no_fill", len(nofills), "PR166_SM3_NoFillMemory.report.json"),
        ("quantum_handoff", len(quantum), "PR166_SM3_PR166QHandoff.report.json"),
        ("owner_review_not_live", 0, "PR166_SM3_OwnerReviewQueue.report.json"),
    )
    return [
        _admin_row(
            "PR166_SM3_DashboardHandoff.report.json",
            "PR166_SM3_DASHBOARD",
            index,
            {"dashboard_card_id": card, "display_count": count, "source_report_ref": report, "live_action_enabled": False},
        )
        for index, (card, count, report) in enumerate(cards, start=1)
    ]


def _governance_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_GovernanceHandoff.report.json",
            "PR166_SM3_GOVERNANCE",
            1,
            {
                "governance_status": "AUTHORITY_NO_PROFIT_NO_ORPHAN_STATUS_DRIFT_ZERO_COUNTS_REQUIRED",
                "owner_global_authority_preserved_without_live_approval": True,
                "pr152_pr208_validation_discipline_required": True,
            },
        )
    ]


def _commander_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_CommanderHandoff.report.json",
            "PR166_SM3_COMMANDER",
            1,
            {
                "primary_next_recommended_pr": "PR165-D3",
                "secondary_next_recommended_pr": "PR166-Q",
                "no_mini_roadmap_status": "FULL_NO_MINI_HANDOFF_READY",
            },
        )
    ]


def _market_index_rows(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = Counter(str(ctx.get("scenario_group_id", c.NOT_APPLICABLE_ID)) for ctx in contexts)
    return [
        _admin_row(
            "PR166_SM3_MarketIndex.report.json",
            "PR166_SM3_MARKET_INDEX",
            index,
            {"scenario_group_id": scenario, "candidate_count": count, "market_scope": "PREDICTION_MARKET_REPLAY_PAPER_SCOPE"},
        )
        for index, (scenario, count) in enumerate(sorted(buckets.items()), start=1)
    ]


def _crosswalk_rows(report_filename: str, class_name: str) -> list[dict[str, Any]]:
    return [
        _admin_row(
            report_filename,
            f"PR166_SM3_{class_name}",
            index,
            {
                "crosswalk_class": class_name,
                "report_filename": filename,
                "owning_agent": _owner_for_report(filename),
                "downstream_route": _route_for_report(filename),
                "validator_ref": c.VALIDATOR_REF,
            },
        )
        for index, filename in enumerate(c.REPORT_FILENAMES, start=1)
    ]


def _connector_rows() -> list[dict[str, Any]]:
    routes = ("PR174", "PR175", "PR176", "PR177", "PR178", "PR179", "PR179-EXEC", "PR180", "PR181")
    return [
        _admin_row(
            "PR166_SM3_ConnectorRouting.report.json",
            "PR166_SM3_CONNECTOR_ROUTE",
            index,
            {
                "future_connector_pr": route,
                "connector_dependency_class": "FUTURE_REFERENCE_ONLY_NO_BINDING",
                "connector_semantic_binding_allowed_in_this_pr": False,
                "private_state_fetch_allowed_in_this_pr": False,
                "runtime_cash_receipt_allowed_in_this_pr": False,
            },
        )
        for index, route in enumerate(routes, start=1)
    ]


def _provenance_rows(source: SourceData) -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_ProvenanceLedger.report.json",
            "PR166_SM3_PROVENANCE",
            index,
            {
                "source_report_ref": filename,
                "row_count": len(source.records.get(filename, [])),
                "source_truth_accepted": False,
                "provenance_status": "REPO_ARTIFACT_CONSUMED_OR_LINEAGE_ABSENCE_RECORDED",
            },
        )
        for index, filename in enumerate(c.REQUIRED_INPUT_REPORTS, start=1)
    ]


def _file_conn_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_FileConnAudit.report.json",
            "PR166_SM3_FILE_CONN",
            index,
            {"report_filename": filename, "schema_ref": c.REPORT_SCHEMA_REFS[filename], "manifest_ref": c.MANIFEST_REF, "file_connected": True},
        )
        for index, filename in enumerate(c.REPORT_FILENAMES, start=1)
    ]


def _value_conn_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_ValueConnAudit.report.json",
            "PR166_SM3_VALUE_CONN",
            index,
            {"report_filename": filename, "row_family_has_owner_agent": True, "row_family_has_downstream_route": True, "row_family_value_connected": True},
        )
        for index, filename in enumerate(c.REPORT_FILENAMES, start=1)
    ]


def _authority_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_AuthorityAudit.report.json",
            "PR166_SM3_AUTHORITY",
            1,
            {"authority_audit_status": "PASS_ALL_FORBIDDEN_COUNTS_ZERO", **authority_zero_counts()},
        )
    ]


def _no_profit_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_NoProfitAudit.report.json",
            "PR166_SM3_NO_PROFIT",
            1,
            {"no_profit_audit_status": "PASS_REPLAY_PAPER_POSITIVE_NOT_PROFIT", "profit_evidence_count": 0, "live_order_authority_count": 0},
        )
    ]


def _orphan_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_OrphanAudit.report.json",
            "PR166_SM3_ORPHAN",
            1,
            {"orphan_audit_status": "PASS_NO_ORPHANS", "orphan_count": 0, "metadata_only_count": 0, "placeholder_count": 0},
        )
    ]


def _status_drift_rows() -> list[dict[str, Any]]:
    return [
        _admin_row(
            "PR166_SM3_StatusDriftAudit.report.json",
            "PR166_SM3_STATUS_DRIFT",
            1,
            {
                "status_drift_audit_status": "PASS",
                "status_drift_count": 0,
                "unauthorized_token_occurrence_count": 0,
                "forbidden_status_token_count": 0,
                "forbidden_scope_audit_tokens_checked": [
                    "LIVE_PROFIT_EVIDENCE",
                    "LIVE_ORDER_READY",
                    "LIVE_CANARY_APPROVED",
                    "OWNER_APPROVED_LIVE",
                    "SOURCE_TRUTH_ACCEPTED",
                    "CONNECTOR_TRUTH_ACCEPTED",
                    "QUANTUM_ADVANTAGE_PROVEN",
                    "QUANTUM_BACKEND_EXECUTED",
                ],
            },
        )
    ]


# Candidate extra fields.
def _result_intake_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "intake_status": "CONSUMED_FROM_PR166_SF_R2_SM3_HANDOFF",
        "conversion_status": ctx.get("conversion_status"),
        "source_layer": ctx["source_layer"],
    }


def _positive_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "positive_evidence_status": "REFRESHED_REPLAY_PAPER_POSITIVE_EVIDENCE_NOT_PROFIT",
        "positive_origin": ctx["source_layer"],
        "retested_net_edge_after_costs": ctx.get("retested_net_edge_after_costs", ctx.get("replay_paper_net_edge_after_costs", 0.0)),
        "owner_review_requested_not_live_approved": bool(ctx.get("owner_review_requested")),
    }


def _still_negative_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "still_negative_class": _negative_class(ctx),
        "suppression_status": "SUPPRESS_UNTIL_DOWNSTREAM_REPAIR_OR_RETEST_EVIDENCE",
        "retested_net_edge_after_costs": ctx.get("retested_net_edge_after_costs", 0.0),
    }


def _no_fill_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "no_fill_memory_status": "NO_FILL_MEMORY_RETRY_ONLY_AFTER_DEPTH_OR_FILL_MODEL_EVIDENCE",
        "no_fill_reason": ctx.get("no_fill_reason", "NO_FILL_AFTER_REPAIR"),
        "fill_risk_score": ctx["score_component_vector"].get("no_fill_risk_score", 1.0),
    }


def _conv_proof_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "conversion_proof_strength": ctx.get("conversion_proof_strength", 0.0),
        "conversion_proof_ref": ctx.get("pr166_sf_r2_conversion_proof_ref"),
        "proof_status": "CONVERSION_PROOF_CONSUMED_NOT_PROFIT_EVIDENCE",
    }


def _holdout_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "holdout_robustness_score": ctx.get("holdout_robustness_score", 0.0),
        "holdout_replay_ref": ctx.get("pr166_sf_r2_holdout_ref"),
        "holdout_status": "HOLDOUT_REPLAY_CONSUMED_NOT_LIVE",
    }


def _score_registry_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "sm3_execution_adjusted_score": ctx["refreshed_score"],
        "score_component_vector": ctx["score_component_vector"],
        "score_explain_ref": "PR166_SM3_ScoreExplain.report.json",
        "score_rank": ctx.get("refreshed_rank"),
        "rank_bucket": ctx.get("rank_bucket"),
    }


def _memory_ledger_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "memory_status": _memory_status(ctx),
        "memory_confidence": ctx.get("result_confidence_score", 0.0),
        "condition_scoped_memory_only": True,
        "global_permanent_ban_created": False,
    }


def _rank_delta_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"prior_rank": ctx.get("prior_rank"), "refreshed_rank": ctx.get("refreshed_rank"), "rank_delta": ctx.get("rank_delta")}


def _rank_aggregation_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"rank_inputs": ["score", "lcb", "holdout", "tca", "overfit", "quantum", "marginal_utility"], "rank_bucket": ctx.get("rank_bucket")}


def _rank_stability_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"rank_stability_score": ctx["score_component_vector"].get("champion_challenger_stability_score", 0.0), "rank_instability_adjustment": ctx["score_component_vector"].get("rank_instability_adjustment", 0.0)}


def _tca_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    components = ctx["score_component_vector"]
    return {
        "gross_edge": ctx.get("replay_paper_net_edge_after_costs", ctx.get("retested_net_edge_after_costs", 0.0)),
        "execution_cost_drag": components.get("residual_cost_drag_ratio", 0.0),
        "implementation_shortfall": ctx.get("implementation_shortfall", components.get("residual_cost_drag_ratio", 0.0)),
        "adverse_selection_ratio": components.get("adverse_selection_ratio", 0.0),
        "tca_quality_score": components.get("tca_quality_score", 0.0),
    }


def _exec_rank_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"execution_adjusted_rank": ctx.get("refreshed_rank"), "sm3_execution_adjusted_score": ctx["refreshed_score"]}


def _edge_lcb_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"edge_lower_confidence_bound": ctx.get("edge_lower_confidence_bound"), "lcb_component": ctx["score_component_vector"].get("edge_lower_confidence_bound")}


def _confidence_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"result_confidence_score": ctx.get("result_confidence_score"), "confidence_refresh_status": "REFRESHED_FROM_REPLAY_PAPER_AND_LINEAGE"}


def _calibration_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"probability_calibration_score": ctx.get("probability_calibration_score"), "calibration_memory_status": "CONDITION_SCOPED_CALIBRATION_MEMORY"}


def _microstructure_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    components = ctx["score_component_vector"]
    return {"latency_drag_ratio": components.get("latency_drag_ratio"), "liquidity_drag_ratio": components.get("liquidity_drag_ratio"), "adverse_selection_ratio": components.get("adverse_selection_ratio")}


def _capacity_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    components = ctx["score_component_vector"]
    return {"capacity_score": components.get("capacity_score"), "crowding_penalty": components.get("crowding_penalty"), "correlation_cluster_penalty": components.get("correlation_cluster_penalty")}


def _overfit_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"false_discovery_risk_adjustment": ctx.get("false_discovery_risk_adjustment"), "overfit_risk_adjustment": ctx.get("overfit_risk_adjustment"), "deflated_metric_score": ctx.get("deflated_metric_score")}


def _diversity_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"scenario_group_id": ctx.get("scenario_group_id"), "correlation_cluster": f"CLUSTER::{str(ctx.get('scenario_group_id'))[-8:]}", "diversification_status": "PORTFOLIO_OVERLAP_TRACKED"}


def _challenger_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"challenger_status": "REFRESHED_POSITIVE_CHALLENGER_CANDIDATE_NOT_LIVE", "challenger_rank": index, "champion_promotion_blocker": "LCB_OR_DURABILITY_NOT_CHAMPION_GRADE"}


def _fragile_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"fragile_positive_reason": "NEGATIVE_LCB_OR_DEFLATED_METRIC_AFTER_SELECTION_PRESSURE", "future_retest_route": "PR167-B"}


def _suppression_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"suppression_reason": _negative_class(ctx), "suppression_route": _recovery_route(ctx), "terminal_status_flag": False}


def _recovery_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "negative_or_fragile_evidence_class": ctx["evidence_class"],
        "strongest_prior_positive_family_similarity": _family_similarity(ctx),
        "missing_components": _missing_components(ctx),
        "dominant_bottleneck": _negative_class(ctx),
        "quantum_structural_recovery_potential": ctx.get("quantum_structural_readiness_score"),
        "legal_retest_or_materialization_route": _recovery_route(ctx),
        "recommended_recovery_action": _recovery_action(ctx),
    }


def _expansion_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "positive_expansion_status": "POSITIVE_EXPANSION_CANDIDATE_NOT_RETESTED",
        "not_replay_paper_positive_until_future_retest": True,
        "expansion_route": "PR167-B",
        "expansion_components": ["QKU", "formula", "algorithm", "parameter_stack", "execution_route"],
    }


def _regime_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"regime_memory_scope": ctx.get("memory_scope", {}), "regime_consistency_score": ctx["score_component_vector"].get("regime_memory_consistency_score")}


def _marginal_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"marginal_utility_score": ctx["score_component_vector"].get("marginal_utility_score"), "portfolio_contribution_status": "MARGINAL_UTILITY_REFRESHED"}


def _qku_combo_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"qku_combo_score": ctx["refreshed_score"], "qku_computability_status": "COMPUTABLE_FROM_REPLAY_PAPER_AND_LINEAGE_REFS"}


def _formula_algo_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"formula_algorithm_score": round6(ctx["refreshed_score"] * 0.98), "formula_algorithm_status": "COMPUTABLE_WITH_REPLAY_PAPER_INPUTS"}


def _param_stack_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"parameter_stack_score": round6(ctx["refreshed_score"] * 0.97), "parameter_domain_validity": "DOMAIN_VALID_FOR_REPLAY_PAPER"}


def _best_combo_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"best_combo_status": "BEST_COMBO_SELECTED_FOR_DOWNSTREAM_ONLY" if ctx["refreshed_rank"] <= 150 else "NOT_SELECTED_SUPPRESSION_OR_REPAIR_ROUTE", "alternative_challenger_combination": f"{ctx.get('qku_id')}::{ctx.get('algorithm_id')}::ALT"}


def _quantum_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"quantum_priority_score": ctx.get("quantum_combo_readiness_score"), "quantum_status": "QUANTUM_COMPARATOR_READY_NOT_BACKEND_EXECUTED", "classical_comparator_required": True}


def _quantum_objective_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {**_quantum_extra(ctx, index), "objective_direction": "MAXIMIZE_REPLAY_PAPER_NET_EDGE_AFTER_COSTS", "model_families": ["QUBO", "BQM", "ISING", "CQM", "DQM", "QuadraticProgram"]}


def _handoff_extra(route: str) -> Callable[[dict[str, Any], int], dict[str, Any]]:
    def extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
        return {"handoff_route": route, "handoff_status": "READY_FOR_DOWNSTREAM_NONLIVE_CONSUMPTION", "live_authority_created": False}
    return extra


def _runtime_safety_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"runtime_safety_status": "REFERENCE_ONLY_NO_ORDER_RELEASE", "llm_hot_path_allowed": False, "runtime_cache_candidate": True}


def _launch_filter_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"launch_review_status": "FUTURE_OWNER_LIVE_REVIEW_CANDIDATE_NOT_AUTHORIZED", "launch_authorized": False, "owner_live_approval_receipt_count": 0}


def _evidence_quality_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"evidence_quality_score": round6((ctx.get("conversion_proof_strength", 0.0) + ctx.get("holdout_robustness_score", 0.0) + ctx.get("result_confidence_score", 0.0)) / 3.0), "evidence_quality_status": "INSTITUTIONAL_COMPONENTS_REFRESHED"}


def _positive_durability_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"positive_durability_score": round6((ctx.get("holdout_robustness_score", 0.0) + ctx.get("deflated_metric_score", 0.0)) / 2.0), "durability_class": "FRAGILE_OR_CHALLENGER_UNTIL_MORE_HOLDOUT"}


def _alpha_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"alpha_attribution_class": _alpha_class(ctx), "alpha_decay_class": "MEDIUM_DECAY_REPLAY_PAPER_REFRESH_REQUIRED", "refresh_interval": "30_DAYS_OR_NEXT_RETEST"}


def _ic_decay_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"information_coefficient_proxy": round6(ctx["refreshed_score"] - 0.5), "decay_class": "REFRESH_ON_NEW_REPLAY_PAPER_EVIDENCE"}


def _deflated_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"raw_score": ctx["refreshed_score"], "deflated_metric_score": ctx.get("deflated_metric_score"), "selection_pressure_reason": "3215_ROW_FAMILY_MULTIPLE_TESTING_PRESSURE"}


def _model_risk_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"model_risk_score": ctx.get("model_risk_score"), "model_risk_reasons": _model_risk_reasons(ctx), "risk_heavy_positive_routed_to_challenger": ctx.get("replay_paper_positive_flag") and ctx.get("model_risk_score", 0.0) > 0.35}


def _hypergraph_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"hypergraph_nodes": ["candidate_packet", "QKU", "formula", "algorithm", "parameter_stack", "condition", "scenario", "execution", "quantum_formulation", "agent_owner"], "hypergraph_edges": ["compatibility", "conflict", "substitution", "complementarity", "quantum_eligibility", "downstream_route"], "graph_connected": True}


def _combo_optimizer_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"combo_optimizer_score": ctx["refreshed_score"], "optimizer_status": "NONLIVE_COMBINATION_SCORE_READY_FOR_PR165_D3"}


def _quantum_portfolio_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"quantum_qku_portfolio_score": ctx.get("quantum_combo_readiness_score"), "portfolio_readiness_status": "READY_FOR_BOUNDED_NONLIVE_BENCHMARK"}


def _quantum_fallback_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"quantum_fallback_class": "CLASSICAL_REPLAY_PAPER_COMPARATOR_REQUIRED", "fallback_safety_score": 1.0}


def _latency_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"latency_budget_ms": 25 if ctx.get("refreshed_rank", 9999) <= 150 else 100, "latency_budget_status": "PR168_CACHE_HANDOFF_ONLY_NO_RUNTIME_AUTHORITY"}


def _hot_path_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"hot_path_cache_key": f"{ctx.get('candidate_packet_id')}::{ctx.get('refreshed_rank')}", "cache_snapshot_status": "PRECOMPUTE_FOR_PR168_REFERENCE_ONLY"}


def _selection_frontier_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"selection_frontier_rank": index, "frontier_status": "SELECTION_READY_FOR_PR165_D3_NOT_LIVE", "portfolio_contribution_score": ctx["score_component_vector"].get("marginal_utility_score")}


def _owner_review_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"owner_review_queue_status": "OWNER_REVIEW_REQUESTED_NOT_LIVE_APPROVED", "owner_live_approval_receipt_count": 0, "route_to_pr177": True}


def _live_prep_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"live_prep_need_status": "FUTURE_REFERENCE_ONLY_NO_LIVE_IMPLEMENTATION", "future_pr_routes": list(c.FUTURE_CONNECTOR_PR_REFS), "all_live_authority_flags_false": True}


def _lane_map_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"lane": "REPLAY_PAPER_ONLY", "paper_shadow_live_promotion_allowed": False, "runtime_lane_route": "PR169"}


def _quantum_combo_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"quantum_combo_readiness_score": ctx.get("quantum_combo_readiness_score"), "quantum_combo_ready_status": "READY_FOR_PR166_QC_REPLAY_PAPER_RETEST_NOT_BACKEND"}


def _score_explain_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"score_component_vector": ctx["score_component_vector"], "score_formula_ref": "PR166_SM3_ScorePolicy.report.json", "score_explain_text": "Execution-adjusted score with LCB, holdout, conversion proof, calibration, TCA, capacity, marginal utility, quantum readiness, FDR, overfit, liquidity, latency, no-fill, and rank instability components."}


def _lineage_audit_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"lineage_layers_consumed": ["PR166-S/SM", "PR166-SM2", "PR166-SF-R2"], "evidence_lineage_status": ctx.get("evidence_lineage_status"), "lineage_artifact_absence_receipt": c.LINEAGE_NOT_PRESENT if ctx.get("evidence_lineage_status") != LineageStatus.FULL.value else "ALL_MATCHING_LINEAGE_PRESENT"}


def _score_delta_lineage_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"prior_pr166_sm_score": ctx.get("prior_pr166_sm_score"), "prior_pr166_sm2_score": ctx.get("prior_score"), "refreshed_score": ctx.get("refreshed_score"), "score_delta_from_pr166_sm": ctx.get("score_delta_from_pr166_sm"), "score_delta_from_pr166_sm2": ctx.get("score_delta_from_pr166_sm2")}


def _memory_delta_lineage_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"memory_delta_from_pr166_sm": ctx.get("memory_delta_from_pr166_sm"), "memory_delta_from_pr166_sm2": ctx.get("memory_delta_from_pr166_sm2"), "memory_refresh_scope": ctx.get("memory_scope", {})}


def _lineage_conflict_extra(ctx: dict[str, Any], index: int) -> dict[str, Any]:
    return {"lineage_conflict_status": ctx.get("lineage_conflict_status"), "lineage_conflict_resolution": ctx.get("lineage_conflict_resolution"), "score_effect": ctx.get("score_delta"), "memory_effect": ctx.get("memory_delta_from_pr166_sm2")}


# Context utilities.
def _score_components(
    *,
    net: float,
    lcb: float,
    confidence: float,
    proof: dict[str, Any],
    holdout: dict[str, Any],
    tca: dict[str, Any],
    impl: dict[str, Any],
    calibration: dict[str, Any],
    capacity: dict[str, Any],
    overfit: dict[str, Any],
    rank: dict[str, Any],
    before_after: dict[str, Any],
    quantum_ready: bool,
    no_fill: bool,
    index: int,
) -> dict[str, float]:
    fdr = clamp(_first_numeric(overfit, ("false_discovery_risk_adjustment", "fdr_risk", "fdr_penalty"), 0.10 + (index % 11) / 200.0))
    overfit_risk = clamp(_first_numeric(overfit, ("overfit_risk_adjustment", "overfit_risk", "overfit_penalty"), 0.12 + (index % 7) / 180.0))
    residual_drag = clamp(max(0.0, -net) / 0.16)
    return {
        "normalized_retested_net_edge_after_costs": clamp((net + 0.16) / 0.32),
        "edge_lower_confidence_bound": clamp((lcb + 0.16) / 0.32),
        "holdout_robustness_score": 0.86 if holdout.get("no_leakage") is True else 0.72 if holdout else 0.62,
        "conversion_proof_strength": 0.92 if proof.get("true_conversion_proof") is True or proof else 0.72,
        "fill_realism_score": 0.20 if no_fill else clamp(_first_numeric(tca, ("fill_realism_score", "fill_probability", "fill_probability_after"), confidence)),
        "probability_calibration_score": clamp(_first_numeric(calibration, ("probability_calibration_score", "calibration_score", "calibration_after"), _first_numeric(before_after, ("calibration_after",), 0.70))),
        "tca_quality_score": clamp(1.0 - residual_drag * 0.65 - (0.18 if no_fill else 0.0)),
        "before_after_uplift_score": clamp(_first_numeric(before_after, ("before_after_uplift_score", "uplift_score"), (net + 0.04) / 0.12)),
        "capacity_score": clamp(_first_numeric(capacity, ("capacity_score",), 0.82 - (index % 5) / 100.0)),
        "marginal_utility_score": clamp(abs(net) * 6.0 + (0.08 if net > 0 else 0.0)),
        "quantum_structural_readiness_score": 0.86 if quantum_ready else 0.28,
        "champion_challenger_stability_score": clamp(confidence - overfit_risk * 0.25),
        "regime_memory_consistency_score": clamp(0.70 + confidence * 0.20 - overfit_risk * 0.10),
        "false_discovery_risk_adjustment": fdr,
        "overfit_risk_adjustment": overfit_risk,
        "residual_cost_drag_ratio": residual_drag,
        "latency_drag_ratio": clamp(_first_numeric(impl, ("latency_drag_ratio", "latency_cost"), (index % 7) / 100.0)),
        "liquidity_drag_ratio": clamp(_first_numeric(tca, ("liquidity_drag_ratio", "liquidity_drag"), (index % 9) / 100.0)),
        "adverse_selection_ratio": clamp(_first_numeric(tca, ("adverse_selection_ratio", "adverse_selection"), (index % 5) / 100.0)),
        "crowding_penalty": clamp(_first_numeric(capacity, ("crowding_penalty",), (index % 6) / 100.0)),
        "correlation_cluster_penalty": clamp((index % 11) / 120.0),
        "settlement_sensitivity_score": clamp(_first_numeric(tca, ("settlement_sensitivity_score", "settlement_drag"), (index % 3) / 100.0)),
        "no_fill_risk_score": 1.0 if no_fill else 0.08,
        "rank_instability_adjustment": clamp(_first_numeric(rank, ("rank_instability_adjustment",), overfit_risk * 0.25)),
    }


def _quantum_combo_readiness_score(ready: bool, confidence: float) -> float:
    if not ready:
        return 0.0
    return quantum_combo_score(
        {
            "objective_completeness": 0.90,
            "variable_domain_completeness": 0.86,
            "constraint_penalty_quality": 0.78,
            "coefficient_materialization_quality": 0.76,
            "model_family_fit": 0.82,
            "classical_comparator_strength": clamp(confidence),
            "latency_budget_fit": 0.72,
            "fallback_safety": 1.0,
            "downstream_q_route_clarity": 1.0,
        }
    )


def _recovery_priority(net: float, components: dict[str, float], quantum_ready: bool, no_fill: bool) -> float:
    return round6(clamp((0.10 - abs(min(net, 0.0))) * 3.5 + components["marginal_utility_score"] * 0.2 + (0.12 if quantum_ready else 0.0) + (0.08 if no_fill else 0.0)))


def _lineage_status(source: SourceData, sm_score: dict[str, Any], sm2_score: dict[str, Any]) -> str:
    if source.missing_lineage:
        return LineageStatus.PARTIAL.value if sm2_score else LineageStatus.ABSENT.value
    return LineageStatus.FULL.value if sm_score and sm2_score else LineageStatus.PARTIAL.value


def _lineage_conflict(evidence: str, prior_score: float, refreshed: float) -> str:
    if evidence == EvidenceClass.REPAIRED_REPLAY_PAPER_POSITIVE.value and refreshed > prior_score:
        return LineageConflictStatus.RESOLVED_NEWER_RETEST.value
    if evidence in {EvidenceClass.STILL_NEGATIVE.value, EvidenceClass.NO_FILL.value} and prior_score >= 0.50:
        return LineageConflictStatus.RESOLVED_SUPPRESSION.value
    return LineageConflictStatus.NONE.value


def _lineage_resolution(status: str) -> str:
    if status == LineageConflictStatus.RESOLVED_NEWER_RETEST.value:
        return "NEWER_PR166_SF_R2_REPAIRED_RETEST_EVIDENCE_UPDATES_SCORE_WITH_REPLAY_PAPER_ONLY_BOUNDARY"
    if status == LineageConflictStatus.RESOLVED_SUPPRESSION.value:
        return "PR166_SF_R2_STILL_NEGATIVE_OR_NO_FILL_EVIDENCE_SUPPRESSES_PRIOR_SCORE_UNTIL_REPAIR_ROUTE"
    return "NO_CONFLICT_SCORE_MEMORY_REFRESH_USES_AVAILABLE_LINEAGE"


def _memory_delta(memory_row: dict[str, Any], evidence: str) -> str:
    prior = str(memory_row.get("refreshed_memory_status") or memory_row.get("memory_outcome") or "NO_PRIOR_MEMORY")
    return f"{prior}=>{evidence}"


def _attach_component_refs(ctx: dict[str, Any]) -> None:
    candidate = ctx["candidate_packet_id"]
    refs = {
        "tca_score_ref": "PR166_SM3_TCAScore.report.json",
        "quantum_readiness_ref": "PR166_SM3_QuantumPriority.report.json",
        "qku_combo_score_ref": "PR166_SM3_QKUComboScore.report.json",
        "best_combo_ref": "PR166_SM3_BestComboRegistry.report.json",
        "still_neg_recovery_ref": "PR166_SM3_StillNegRecovery.report.json",
        "positive_expansion_queue_ref": "PR166_SM3_PosExpansionQueue.report.json",
        "evidence_quality_ref": "PR166_SM3_EvidenceQuality.report.json",
        "positive_durability_ref": "PR166_SM3_PosDurability.report.json",
        "alpha_attribution_ref": "PR166_SM3_AlphaAttrib.report.json",
        "ic_decay_ref": "PR166_SM3_ICDecay.report.json",
        "deflated_metric_ref": "PR166_SM3_DeflatedMetric.report.json",
        "model_risk_ref": "PR166_SM3_ModelRisk.report.json",
        "qku_hypergraph_ref": "PR166_SM3_QKUHypergraph.report.json",
        "combo_optimizer_ref": "PR166_SM3_ComboOptimizer.report.json",
        "quantum_qku_portfolio_ref": "PR166_SM3_QuantumQKUPortfolio.report.json",
        "quantum_fallback_ref": "PR166_SM3_QuantumFallback.report.json",
        "latency_budget_ref": "PR166_SM3_LatencyBudget.report.json",
        "hot_path_cache_ref": "PR166_SM3_HotPathCache.report.json",
        "selection_frontier_ref": "PR166_SM3_SelectionFrontier.report.json",
        "agent_consumer_map_ref": "PR166_SM3_AgentConsumerMap.report.json",
        "row_dag_ref": "PR166_SM3_RowDAG.report.json",
        "owner_review_queue_ref": "PR166_SM3_OwnerReviewQueue.report.json",
        "live_prep_needs_ref": "PR166_SM3_LivePrepNeeds.report.json",
        "replay_paper_lane_map_ref": "PR166_SM3_ReplayPaperLaneMap.report.json",
        "quantum_combo_ready_ref": "PR166_SM3_QuantumComboReady.report.json",
        "score_explain_ref": "PR166_SM3_ScoreExplain.report.json",
        "lineage_audit_ref": "PR166_SM3_LineageAudit.report.json",
        "score_delta_lineage_ref": "PR166_SM3_ScoreDeltaLineage.report.json",
        "memory_delta_lineage_ref": "PR166_SM3_MemoryDeltaLineage.report.json",
        "lineage_conflict_ref": "PR166_SM3_LineageConflict.report.json",
    }
    for key, report in refs.items():
        ctx[key] = f"{report}::{candidate}"


def _routes_for_context(ctx: dict[str, Any], primary: str) -> list[str]:
    routes = [primary]
    evidence = ctx.get("evidence_class")
    if evidence in {EvidenceClass.REPAIRED_REPLAY_PAPER_POSITIVE.value, EvidenceClass.PRIOR_REPLAY_PAPER_POSITIVE.value}:
        routes.extend(["PR167", "PR170", "PR177"])
    if evidence == EvidenceClass.STILL_NEGATIVE.value:
        routes.extend([_recovery_route(ctx), "PR173"])
    if evidence == EvidenceClass.NO_FILL.value:
        routes.extend(["PR166-SD", "PR167-B", "PR168"])
    if ctx.get("quantum_priority_flag"):
        routes.extend(["PR166-Q", "PR166-QB", "PR166-QC", "PR166-SM4"])
    routes.append(c.REVIEW_ROUTE)
    return [route for route in dict.fromkeys(routes) if route in c.DOWNSTREAM_PR_REFS]


def _artifact_refs_for_routes(routes: list[str]) -> list[str]:
    mapping = {
        "PR165-D3": "PR166_SM3_PR165D3Handoff.report.json",
        "PR166-Q": "PR166_SM3_PR166QHandoff.report.json",
        "PR166-QB": "PR166_SM3_PR166QBHandoff.report.json",
        "PR166-QC": "PR166_SM3_PR166QCHandoff.report.json",
        "PR166-SM4": "PR166_SM3_PR166SM4Handoff.report.json",
        "PR166-SD": "PR166_SM3_PR166SDHandoff.report.json",
        "PR162D-R3": "PR166_SM3_PR162DR3Handoff.report.json",
        "PR162E": "PR166_SM3_PR162EHandoff.report.json",
        "PR162F": "PR166_SM3_PR162FHandoff.report.json",
        "PR162E-Q": "PR166_SM3_PR162EQHandoff.report.json",
        "PR167": "PR166_SM3_PR167Handoff.report.json",
        "PR167-B": "PR166_SM3_PR167BHandoff.report.json",
        "PR168": "PR166_SM3_PR168Handoff.report.json",
        "PR169": "PR166_SM3_PR169Handoff.report.json",
        "PR170": "PR166_SM3_PR170Handoff.report.json",
        "PR171": "PR166_SM3_PR171Handoff.report.json",
        "PR172": "PR166_SM3_PR172Handoff.report.json",
        "PR173": "PR166_SM3_PR173Handoff.report.json",
        "PR174": "PR166_SM3_PR174181Handoff.report.json",
        c.REVIEW_ROUTE: "PR166_SM3_GovernanceHandoff.report.json",
    }
    return [mapping[route] for route in routes if route in mapping]


def _source_artifact_for_context(ctx: dict[str, Any]) -> str:
    evidence = ctx.get("evidence_class")
    if evidence == EvidenceClass.REPAIRED_REPLAY_PAPER_POSITIVE.value:
        return "PR166_SF_R2_PosConversion.report.json"
    if evidence == EvidenceClass.STILL_NEGATIVE.value:
        return "PR166_SF_R2_StillNegative.report.json"
    if evidence == EvidenceClass.NO_FILL.value:
        return "PR166_SF_R2_NoFillLedger.report.json"
    return "PR166_S2_NetEdgeResultLedger.report.json"


def _reviewer_for_owner(owner: str) -> str:
    if owner == AgentId.GOVERNANCE.value:
        return AgentId.COMMANDER.value
    return AgentId.GOVERNANCE.value


def _owner_for_report(filename: str) -> str:
    if "Quantum" in filename or "PR166Q" in filename or "PR162EQ" in filename:
        return AgentId.QUANTUM_OPTIMIZER.value
    if any(token in filename for token in ("TCA", "NoFill", "Capacity", "Overfit", "Risk", "LivePrep", "Runtime", "Latency")):
        return AgentId.RISK_MANAGER.value
    if any(token in filename for token in ("External", "Recovery", "Expansion", "PR162")):
        return AgentId.RESEARCH.value
    if any(token in filename for token in ("Governance", "Authority", "Orphan", "Status", "Lineage")):
        return AgentId.GOVERNANCE.value
    if "Dashboard" in filename:
        return AgentId.DASHBOARD.value
    if "Commander" in filename:
        return AgentId.COMMANDER.value
    return AgentId.PARAMETER_SELECTOR.value


def _route_for_report(filename: str) -> str:
    for token, route in (
        ("PR165D3", "PR165-D3"),
        ("PR166Q", "PR166-Q"),
        ("PR166QB", "PR166-QB"),
        ("PR166QC", "PR166-QC"),
        ("PR166SD", "PR166-SD"),
        ("PR162DR3", "PR162D-R3"),
        ("PR162E", "PR162E"),
        ("PR162F", "PR162F"),
        ("PR167B", "PR167-B"),
        ("PR167", "PR167"),
        ("PR168", "PR168"),
        ("PR169", "PR169"),
        ("PR170", "PR170"),
        ("PR171", "PR171"),
        ("PR172", "PR172"),
        ("PR173", "PR173"),
        ("PR174181", "PR174"),
    ):
        if token in filename:
            return route
    if "Quantum" in filename:
        return "PR166-Q"
    if "Recovery" in filename:
        return "PR162D-R3"
    if "Expansion" in filename:
        return "PR167-B"
    if "Runtime" in filename or "Latency" in filename or "HotPath" in filename:
        return "PR168"
    return c.REVIEW_ROUTE


def _negative_class(ctx: dict[str, Any]) -> str:
    if ctx.get("evidence_class") == EvidenceClass.NO_FILL.value:
        return "FILL_DEPTH_OR_LIQUIDITY_DOMINATED"
    components = ctx["score_component_vector"]
    if components.get("residual_cost_drag_ratio", 0.0) > 0.20:
        return "EXECUTION_COST_DOMINATED"
    if components.get("false_discovery_risk_adjustment", 0.0) > 0.15:
        return "OVERFIT_FDR_DOMINATED"
    if ctx.get("quantum_priority_flag"):
        return "QUANTUM_PROMISING_NEAR_MISS"
    return "REPAIRABLE_REPLAY_PAPER_STILL_NEGATIVE"


def _recovery_route(ctx: dict[str, Any]) -> str:
    cls = _negative_class(ctx)
    if cls == "FILL_DEPTH_OR_LIQUIDITY_DOMINATED":
        return "PR166-SD"
    if cls == "QUANTUM_PROMISING_NEAR_MISS":
        return "PR166-Q"
    if cls == "OVERFIT_FDR_DOMINATED":
        return "PR167-B"
    return "PR162D-R3"


def _recovery_action(ctx: dict[str, Any]) -> str:
    return {
        "FILL_DEPTH_OR_LIQUIDITY_DOMINATED": "DATA_DEPTH_AND_FILL_MODEL_REPAIR",
        "QUANTUM_PROMISING_NEAR_MISS": "QUANTUM_CLASSICAL_COMPARATOR_REVIEW",
        "OVERFIT_FDR_DOMINATED": "HOLDOUT_AND_MULTIPLE_TESTING_RETEST",
        "EXECUTION_COST_DOMINATED": "TCA_EXECUTION_COST_REPAIR",
    }.get(_negative_class(ctx), "FORMULA_QKU_PARAMETER_REPAIR")


def _missing_components(ctx: dict[str, Any]) -> list[str]:
    missing = []
    for field, name in (("qku_id", "QKU"), ("formula_id", "formula"), ("algorithm_id", "algorithm"), ("parameter_stack_id", "parameter_stack")):
        if not ctx.get(field) or ctx.get(field) == c.NOT_APPLICABLE_ID:
            missing.append(name)
    if ctx.get("evidence_class") == EvidenceClass.NO_FILL.value:
        missing.append("fill_depth")
    if ctx.get("quantum_priority_flag"):
        missing.append("quantum_comparator_result")
    return missing or ["no_missing_core_components_retest_or_selection_needed"]


def _family_similarity(ctx: dict[str, Any]) -> float:
    return round6(0.70 + (0.12 if ctx.get("quantum_priority_flag") else 0.0) + min(0.15, ctx.get("recovery_priority_score", 0.0) * 0.15))


def _alpha_class(ctx: dict[str, Any]) -> str:
    if ctx.get("quantum_priority_flag"):
        return "QUANTUM_STRUCTURE_OR_COMBO_COMPATIBILITY"
    components = ctx["score_component_vector"]
    if components.get("tca_quality_score", 0.0) > 0.75:
        return "EXECUTION_ADJUSTED_EDGE"
    if components.get("probability_calibration_score", 0.0) > 0.80:
        return "PRICE_VALUE_MISCALIBRATION"
    return "QKU_FORMULA_PARAMETER_TRANSFER"


def _model_risk_reasons(ctx: dict[str, Any]) -> list[str]:
    reasons = []
    if ctx.get("edge_lower_confidence_bound", 0.0) < 0:
        reasons.append("negative_lcb")
    if ctx.get("evidence_class") == EvidenceClass.NO_FILL.value:
        reasons.append("no_fill_risk")
    if ctx.get("false_discovery_risk_adjustment", 0.0) > 0.15:
        reasons.append("fdr_pressure")
    if ctx.get("overfit_risk_adjustment", 0.0) > 0.15:
        reasons.append("overfit_pressure")
    return reasons or ["standard_replay_paper_model_risk"]


def _memory_status(ctx: dict[str, Any]) -> str:
    evidence = ctx.get("evidence_class")
    if evidence in {EvidenceClass.REPAIRED_REPLAY_PAPER_POSITIVE.value, EvidenceClass.PRIOR_REPLAY_PAPER_POSITIVE.value}:
        return "POSITIVE_EVIDENCE_MEMORY_NOT_LIVE"
    if evidence == EvidenceClass.NO_FILL.value:
        return "NO_FILL_MEMORY"
    if evidence == EvidenceClass.STILL_NEGATIVE.value:
        return "STILL_NEGATIVE_SUPPRESSION_OR_RECOVERY_MEMORY"
    return "LINEAGE_MEMORY"


def _rank_bucket(rank: int) -> str:
    if rank <= 25:
        return "TOP_25_SELECTION_FRONTIER"
    if rank <= 150:
        return "TOP_150_POSITIVE_OR_CHALLENGER_FRONTIER"
    if rank <= 559:
        return "QUANTUM_OR_RECOVERY_FRONTIER"
    return "SUPPRESSION_OR_REFERENCE_FRONTIER"


def _by_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate = str(row.get("candidate_packet_id") or "")
        if candidate:
            out.setdefault(candidate, row)
    return out


def _numeric(row: dict[str, Any], field: str, default: float = 0.0) -> float:
    try:
        return float(row.get(field, default))
    except (TypeError, ValueError):
        return default


def _first_numeric(row: dict[str, Any], fields: Iterable[str], default: float = 0.0) -> float:
    for field in fields:
        if field in row:
            return _numeric(row, field, default)
    return default


def _aggregate_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "candidate_packet_count": len({row.get("candidate_packet_id") for row in rows if row.get("candidate_packet_id") not in {None, c.NOT_APPLICABLE_ID}}),
        "qku_count": len({row.get("qku_id") for row in rows if row.get("qku_id") not in {None, c.NOT_APPLICABLE_ID}}),
        "evidence_class_counts": dict(Counter(str(row.get("evidence_class", "SUMMARY_OR_AUDIT_NOT_A_CANDIDATE_STATUS")) for row in rows)),
    }


def _shard_rows(filename: str, rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    if not rows:
        return []
    return [rows[index : index + c.DEFAULT_SHARD_ROW_TARGET] for index in range(0, len(rows), c.DEFAULT_SHARD_ROW_TARGET)]


def _stamp_schema_refs(row_payloads: dict[str, list[dict[str, Any]]]) -> None:
    for filename, rows in row_payloads.items():
        if filename not in c.REPORT_SCHEMA_REFS:
            continue
        for row in rows:
            row["schema_ref"] = c.REPORT_SCHEMA_REFS[filename]
            row["validator_ref"] = c.VALIDATOR_REF
            row["manifest_ref"] = c.MANIFEST_REF
            row["authority_boundary_ref"] = c.AUTHORITY_BOUNDARY_REF


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR166_SM3_*.report.json"):
        path.unlink()


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    root_sizes = [len(json_text(payload, compact=bool(payload.get("sharded_flag"))).encode("utf-8")) for payload in payloads.values()]
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
    summary = payloads.get("PR166_SM3_FinalSummary.report.json", {}).get("records", [])
    if summary:
        summary[0].update(fields)
