#!/usr/bin/env python3
"""PR168-RANK input discovery and PR168-RP handoff summarization."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from tools.pr168_rank_report_writer import GENERATED_DIR, read_records, read_report


REQUIRED_PR168_RP_REPORTS = [
    "PR168_RP_FinalSummary.report.json",
    "PR168_RP_ComputedPositiveEdgeCandidates.report.json",
    "PR168_RP_RepairedPositiveCandidateEvidence.report.json",
    "PR168_RP_ComputedNegativeEdgeCandidates.report.json",
    "PR168_RP_ComputedNeutralOrZeroEdgeCandidates.report.json",
    "PR168_RP_PreTradeSimulationCandidates.report.json",
    "PR168_RP_OrderPolicyCandidateRanking.report.json",
    "PR168_RP_NoTradeCandidateComparison.report.json",
    "PR168_RP_ScenarioLadderResults.report.json",
    "PR168_RP_LatencyBudgetResults.report.json",
    "PR168_RP_ExecutionAdjustedRankingSeed.report.json",
    "PR168_RP_TCADecomposition.report.json",
    "PR168_RP_OverfitFDRResults.report.json",
    "PR168_RP_CapacityCrowdingResults.report.json",
    "PR168_RP_PortfolioMarginalUtilityResults.report.json",
    "PR168_RP_ProbabilityCalibration.report.json",
    "PR168_RP_QuantumStructuralReadiness.report.json",
    "PR168_RP_QuantumCoefficientMapInputGaps.report.json",
    "PR168_RP_QKUCombinationCandidateResults.report.json",
    "PR168_RP_OrderPolicyCombinationSelectionResults.report.json",
    "PR168_RP_ChampionChallengerEligibility.report.json",
    "PR168_RP_NegativeToPositiveRecoveryAttempts.report.json",
    "PR168_RP_TrueNegativeAfterRecoveryExhaustion.report.json",
    "PR168_RP_RegimeConditionedMemorySeed.report.json",
    "PR168_RP_PreTradeRegimeMemorySeed.report.json",
    "PR168_RP_To_PR168_RANK_ComputedRanking.report.json",
    "PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json",
    "PR168_RP_ActionableInputGapQueue.report.json",
    "PR168_RP_ArtifactInformationValueDAG.report.json",
    "PR168_RP_AgentDutyDAG.report.json",
    "PR168_RP_NoOrphanProof.report.json",
]

READ_RECEIPT_TARGETS = [
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/SectionManifest.json",
    "docs/master_plan/generated/ArtifactRegistry.json",
    "docs/master_plan/generated/ImplementationGraph.json",
    "docs/master_plan/generated/ImplementationState.generated.json",
    "docs/master_plan/generated/CoverageLedger.generated.json",
    "docs/master_plan/generated/InterfacePlacementMap.json",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
    "tools/validation_scope_registry.py",
    "tools/qtt_authority_reason_code_registry.py",
]

ONLINE_RESEARCH_RECEIPTS = [
    {
        "reference_id": "BENJAMINI_HOCHBERG_1995",
        "url": "https://rss.onlinelibrary.wiley.com/doi/10.1111/j.2517-6161.1995.tb02031.x",
        "candidate_use": "false-discovery-rate trial-family caution",
        "truth_authority_created": False,
    },
    {
        "reference_id": "BAILEY_LOPEZ_DE_PRADO_DEFLATED_SHARPE",
        "url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551",
        "candidate_use": "post-selection overfit caution",
        "truth_authority_created": False,
    },
    {
        "reference_id": "ROCKAFELLAR_URYASEV_CVAR",
        "url": "https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf",
        "candidate_use": "CVaR / expected-shortfall framing",
        "truth_authority_created": False,
    },
    {
        "reference_id": "DWAVE_MODELS",
        "url": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "candidate_use": "BQM/QUBO/Ising/CQM/DQM structural fields",
        "truth_authority_created": False,
    },
    {
        "reference_id": "QISKIT_QUADRATIC_PROGRAM",
        "url": "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.QuadraticProgram.html",
        "candidate_use": "QuadraticProgram structural fields",
        "truth_authority_created": False,
    },
    {
        "reference_id": "SKLEARN_PROBABILITY_CALIBRATION",
        "url": "https://scikit-learn.org/stable/modules/calibration.html",
        "candidate_use": "probability calibration vocabulary",
        "truth_authority_created": False,
    },
]


@dataclass(frozen=True)
class LoadedRankInputs:
    report_roots: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    input_summary: dict[str, Any]
    read_receipt_rows: list[dict[str, Any]]


def load_rank_inputs(repo_root: Path) -> LoadedRankInputs:
    report_roots: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    malformed: list[str] = []
    missing: list[str] = []
    for filename in REQUIRED_PR168_RP_REPORTS:
        path = repo_root / GENERATED_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        try:
            report_roots[filename] = read_report(repo_root, filename)
            records[filename] = read_records(repo_root, filename)
        except (json.JSONDecodeError, OSError, KeyError, TypeError) as exc:
            malformed.append(f"{filename}: {type(exc).__name__}")

    summary = _input_summary(repo_root, report_roots, records, missing, malformed)
    return LoadedRankInputs(
        report_roots=report_roots,
        records=records,
        input_summary=summary,
        read_receipt_rows=_read_receipts(repo_root, report_roots),
    )


def _report_count(report_roots: dict[str, dict[str, Any]], records: dict[str, list[dict[str, Any]]], filename: str) -> int:
    root = report_roots.get(filename, {})
    if "record_count" in root:
        return int(root["record_count"])
    return len(records.get(filename, []))


def _input_summary(
    repo_root: Path,
    report_roots: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    missing: list[str],
    malformed: list[str],
) -> dict[str, Any]:
    no_trade_rows = records.get("PR168_RP_NoTradeCandidateComparison.report.json", [])
    champion_rows = records.get("PR168_RP_ChampionChallengerEligibility.report.json", [])
    recovery_rows = records.get("PR168_RP_NegativeToPositiveRecoveryAttempts.report.json", [])
    failure_counts: Counter[str] = Counter()
    for row in recovery_rows:
        failure_counts.update(str(code) for code in row.get("negative_reason_codes", []))
    no_orphan_status = report_roots.get("PR168_RP_NoOrphanProof.report.json", {}).get("no_orphan_status")
    agent_roster = repo_root / GENERATED_DIR / "PR165_D2_AgentRosterDiscoveryAudit.report.json"
    agent_crosswalk = repo_root / GENERATED_DIR / "PR165_D2_AgentDutySourceCrosswalk.report.json"
    handoff_ok = all(
        filename in report_roots
        for filename in (
            "PR168_RP_To_PR168_RANK_ComputedRanking.report.json",
            "PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json",
        )
    )
    decision = "PROCEED_TO_PR168_RANK"
    reason_codes = ["PR168_RP_NUMERIC_HANDOFF_AVAILABLE"]
    if missing or malformed or not handoff_ok:
        decision = "STOP_AND_ROUTE_PR168_RP_POSTMERGE_REPAIR"
        reason_codes = ["PR168_RP_REQUIRED_INPUT_MISSING_OR_MALFORMED"]
    return {
        "report_id": "PR168_RANK_PR168RPInputResultSummary",
        "created_by": "PR168_RANK_EVIDENCE_BACKED_RANKING",
        "input_search_roots": [
            "docs/master_plan/generated",
            "docs/master_plan/generated/pr168_rp_shards",
        ],
        "required_report_count": len(REQUIRED_PR168_RP_REPORTS),
        "found_required_report_count": len(REQUIRED_PR168_RP_REPORTS) - len(missing),
        "missing_required_reports": missing,
        "malformed_required_reports": malformed,
        "computed_positive_count": _report_count(report_roots, records, "PR168_RP_ComputedPositiveEdgeCandidates.report.json"),
        "repaired_positive_count": _report_count(report_roots, records, "PR168_RP_RepairedPositiveCandidateEvidence.report.json"),
        "computed_negative_count": _report_count(report_roots, records, "PR168_RP_ComputedNegativeEdgeCandidates.report.json"),
        "neutral_or_zero_count": _report_count(report_roots, records, "PR168_RP_ComputedNeutralOrZeroEdgeCandidates.report.json"),
        "input_gap_count": _report_count(report_roots, records, "PR168_RP_ActionableInputGapQueue.report.json"),
        "quantum_gap_count": _report_count(report_roots, records, "PR168_RP_QuantumCoefficientMapInputGaps.report.json"),
        "pretrade_candidate_count": _report_count(report_roots, records, "PR168_RP_PreTradeSimulationCandidates.report.json"),
        "order_policy_candidate_count": _report_count(report_roots, records, "PR168_RP_OrderPolicyCandidateRanking.report.json"),
        "no_trade_dominant_count": len([row for row in no_trade_rows if row.get("no_trade_dominates") is True]),
        "champion_eligible_input_count": len([row for row in champion_rows if row.get("champion_eligible") is True]),
        "challenger_input_count": len([row for row in champion_rows if row.get("challenger_eligible") is True]),
        "retest_input_count": len([row for row in champion_rows if "RETEST" in " ".join(map(str, row.get("reason_codes", [])))]),
        "repair_queue_input_count": _report_count(report_roots, records, "PR168_RP_ActionableInputGapQueue.report.json"),
        "true_negative_or_terminal_input_count": _report_count(report_roots, records, "PR168_RP_TrueNegativeAfterRecoveryExhaustion.report.json"),
        "qku_formula_algorithm_combination_input_count": _report_count(report_roots, records, "PR168_RP_QKUCombinationCandidateResults.report.json"),
        "candidate_stack_input_count": _report_count(report_roots, records, "PR168_RP_To_PR168_RANK_ComputedRanking.report.json"),
        "trade_order_simulation_input_count": _report_count(report_roots, records, "PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json"),
        "mode_scoped_input_count": len([row for row in records.get("PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json", []) if row.get("mode")]),
        "top_alpha_source_candidates": _top_alpha_candidates(records),
        "dominant_failure_reasons": failure_counts.most_common(10),
        "highest_value_repair_queues": _repair_queues(records),
        "no_orphan_input_status": no_orphan_status or "MISSING",
        "agent_roster_crosswalk_status": "FOUND" if agent_roster.exists() and agent_crosswalk.exists() else "GAP_ROUTED",
        "decision": decision,
        "reason_codes": reason_codes,
        "upstream_report_refs": sorted(report_roots),
    }


def _top_alpha_candidates(records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = records.get("PR168_RP_To_PR168_RANK_ComputedRanking.report.json", [])
    top = sorted(rows, key=lambda row: float(row.get("fill_adjusted_expected_pnl", 0.0)), reverse=True)[:5]
    return [
        {
            "result_ref": row.get("result_ref"),
            "qku_id": row.get("qku_id"),
            "fill_adjusted_expected_pnl": row.get("fill_adjusted_expected_pnl"),
            "lower_confidence_bound_edge": row.get("lower_confidence_bound_edge"),
            "computed_status": row.get("computed_status"),
            "positive_alpha_claim": False,
        }
        for row in top
    ]


def _repair_queues(records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = records.get("PR168_RP_NegativeToPositiveRecoveryAttempts.report.json", [])
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(str(code) for code in row.get("negative_reason_codes", []))
    return [{"reason_code": reason, "candidate_count": count} for reason, count in counts.most_common(10)]


def _read_receipts(repo_root: Path, report_roots: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in READ_RECEIPT_TARGETS:
        path = repo_root / target
        rows.append(
            {
                "receipt_id": f"READ::{target}",
                "target": target,
                "read_status": "FOUND" if path.exists() else "MISSING_GAP_ROUTED",
                "length_bytes": path.stat().st_size if path.exists() else 0,
                "upstream_source": target,
                "downstream_route": "PR168_RANK_InputConsumption.report.json",
                "owning_agent": "RankingAgent",
                "no_orphan_status": "CONNECTED_TO_READ_RECEIPT_CONSUMER",
            }
        )
    for filename in sorted(report_roots):
        rows.append(
            {
                "receipt_id": f"READ::{filename}",
                "target": f"docs/master_plan/generated/{filename}",
                "read_status": "FOUND",
                "length_bytes": (repo_root / GENERATED_DIR / filename).stat().st_size,
                "upstream_source": filename,
                "downstream_route": "PR168_RANK_PR168RPInputResultSummary.report.json",
                "owning_agent": "RankingAgent",
                "no_orphan_status": "CONNECTED_TO_READ_RECEIPT_CONSUMER",
            }
        )
    for receipt in ONLINE_RESEARCH_RECEIPTS:
        rows.append(
            {
                "receipt_id": f"ONLINE::{receipt['reference_id']}",
                "target": receipt["url"],
                "read_status": "RESEARCH_READ_RECEIPT_CANDIDATE_ONLY",
                "candidate_use": receipt["candidate_use"],
                "source_truth_authority_created": False,
                "live_authority_created": False,
                "upstream_source": receipt["url"],
                "downstream_route": "PR168_RANK_ReadReceipt.report.json",
                "owning_agent": "QKUResearchAgent",
                "no_orphan_status": "CONNECTED_TO_RESEARCH_RECEIPT_CONSUMER",
            }
        )
    return rows
