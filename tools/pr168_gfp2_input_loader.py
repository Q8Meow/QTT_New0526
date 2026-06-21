#!/usr/bin/env python3
"""Structured upstream input loader for PR168-GFP2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.pr168_gfp2_artifact_locator import locate_required_artifacts
from tools.pr168_gfp2_report_writer import read_json, read_jsonl, read_records, read_report


@dataclass(frozen=True)
class GFP2Inputs:
    artifact_rows: list[dict[str, Any]]
    assignments: list[dict[str, Any]]
    formulas: list[dict[str, Any]]
    truth_overlay: list[dict[str, Any]]
    qku_coverage: list[dict[str, Any]]
    candidate_coverage: list[dict[str, Any]]
    atomicrows_coverage: list[dict[str, Any]]
    rp_final_summary: list[dict[str, Any]]
    rp_positive_rows: list[dict[str, Any]]
    rp_negative_rows: list[dict[str, Any]]
    rp_neutral_rows: list[dict[str, Any]]
    rp_gap_rows: list[dict[str, Any]]
    rp_true_negative_rows: list[dict[str, Any]]
    rp_pretrade_rows: list[dict[str, Any]]
    rp_no_trade_rows: list[dict[str, Any]]
    rank_final_summary: list[dict[str, Any]]
    rank_no_trade_rows: list[dict[str, Any]]
    agent_roster_rows: list[dict[str, Any]]
    agent_duty_rows: list[dict[str, Any]]
    accepted_source_rows: list[dict[str, Any]]
    production_accepted_source_rows: list[dict[str, Any]]
    source_evidence_ledger: dict[str, Any]
    master_plan_text_present: bool
    atomicrows_records: list[dict[str, Any]]


def load_inputs(repo_root: Path) -> GFP2Inputs:
    artifacts = locate_required_artifacts(repo_root)
    accepted_ledger = _read_optional_json(
        repo_root / "docs/master_plan/source_evidence/generated/AcceptedSourceEvidenceLedger.report.json"
    )
    accepted_rows = list(accepted_ledger.get("accepted_ledger_records", []))
    production_rows = [
        row
        for row in accepted_rows
        if row.get("production_external_fact_authority") is True
        and row.get("source_class") != "TEST_FIXTURE_NOT_EXTERNAL_FACT"
    ]
    return GFP2Inputs(
        artifact_rows=artifacts,
        assignments=_safe_records(repo_root, "PR168_GFP_FormulaAssignmentMatrix.report.json"),
        formulas=_safe_records(repo_root, "PR168_GFP_SelectedFormulaExpressionRegistry.report.json"),
        truth_overlay=_safe_records(repo_root, "PR168_GFP_AuthoritativeTruthOverlay.report.json"),
        qku_coverage=_safe_records(repo_root, "PR168_GFP_QKUComputationCoverage.report.json"),
        candidate_coverage=_safe_records(repo_root, "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json"),
        atomicrows_coverage=_safe_records(repo_root, "PR168_GFP_AtomicRowsComputationCoverage.report.json"),
        rp_final_summary=_safe_records(repo_root, "PR168_RP_FinalSummary.report.json"),
        rp_positive_rows=_safe_records(repo_root, "PR168_RP_ComputedPositiveEdgeCandidates.report.json"),
        rp_negative_rows=_safe_records(repo_root, "PR168_RP_ComputedNegativeEdgeCandidates.report.json"),
        rp_neutral_rows=_safe_records(repo_root, "PR168_RP_ComputedNeutralOrZeroEdgeCandidates.report.json"),
        rp_gap_rows=_safe_records(repo_root, "PR168_RP_ActionableInputGapQueue.report.json"),
        rp_true_negative_rows=_safe_records(repo_root, "PR168_RP_TrueNegativeAfterRecoveryExhaustion.report.json"),
        rp_pretrade_rows=_safe_records(repo_root, "PR168_RP_PreTradeSimulationCandidates.report.json"),
        rp_no_trade_rows=_safe_records(repo_root, "PR168_RP_NoTradeCandidateComparison.report.json"),
        rank_final_summary=_safe_records(repo_root, "PR168_RANK_FinalSummary.report.json"),
        rank_no_trade_rows=_safe_records(repo_root, "PR168_RANK_NoTradeDominanceResults.report.json"),
        agent_roster_rows=_safe_records(repo_root, "PR165_D2_AgentRosterDiscoveryAudit.report.json"),
        agent_duty_rows=_safe_records(repo_root, "PR165_D2_AgentDutySourceCrosswalk.report.json"),
        accepted_source_rows=accepted_rows,
        production_accepted_source_rows=production_rows,
        source_evidence_ledger=accepted_ledger,
        master_plan_text_present=(repo_root / "docs/master_plan/QTT_MasterPlan_Current.md").exists(),
        atomicrows_records=_safe_jsonl(repo_root / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"),
    )


def accepted_real_market_data_available(inputs: GFP2Inputs) -> bool:
    return bool(inputs.production_accepted_source_rows)


def formula_assignment_by_key(inputs: GFP2Inputs) -> dict[str, dict[str, Any]]:
    return {str(row.get("canonical_row_key")): row for row in inputs.assignments}


def rp_negative_by_key(inputs: GFP2Inputs) -> dict[str, dict[str, Any]]:
    return {str(row.get("canonical_row_key")): row for row in inputs.rp_negative_rows}


def rp_gap_by_key(inputs: GFP2Inputs) -> dict[str, dict[str, Any]]:
    return {str(row.get("canonical_row_key")): row for row in inputs.rp_gap_rows}


def _safe_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    try:
        return read_records(repo_root, filename)
    except FileNotFoundError:
        return []


def _safe_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return read_jsonl(path)


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return read_json(path)


def read_root_report(repo_root: Path, filename: str) -> dict[str, Any]:
    return read_report(repo_root, filename)
