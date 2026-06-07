"""Load and join PR164 trigger context for PR163-C."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .artifact_discovery import (
    index_by_candidate,
    index_by_candidate_qku,
    load_report_payload,
    load_report_records,
)


@dataclass(frozen=True)
class PR164Context:
    trigger_root: dict[str, Any]
    triggers: list[dict[str, Any]]
    infrastructure_by_candidate: dict[str, dict[str, Any]]
    readiness_rows: list[dict[str, Any]]
    readiness_by_candidate_qku: dict[tuple[str, str], dict[str, Any]]
    missing_fill_by_qku: dict[str, dict[str, Any]]
    computability_by_candidate_qku: dict[tuple[str, str], dict[str, Any]]
    execution_cost_by_candidate_qku: dict[tuple[str, str], dict[str, Any]]
    latency_by_candidate_qku: dict[tuple[str, str], dict[str, Any]]
    model_risk_by_qku: dict[str, dict[str, Any]]
    agent_by_candidate_qku: dict[tuple[str, str], dict[str, Any]]
    quantum_by_candidate_qku: dict[tuple[str, str], dict[str, Any]]
    quantum_comparator_by_candidate_qku: dict[tuple[str, str], dict[str, Any]]
    source_rows: list[dict[str, Any]]
    point_in_time_source_rows: list[dict[str, Any]]
    pr163b_tca_by_candidate: dict[str, dict[str, Any]]
    pr163b_fill_by_candidate: dict[str, dict[str, Any]]
    pr163b_divergence_by_candidate: dict[str, dict[str, Any]]
    pr163b_remediation_by_candidate: dict[str, dict[str, Any]]


def load_pr164_context(repo_root: Path) -> PR164Context:
    trigger_root = load_report_payload(repo_root, "PR164_PR163CRepairTriggerMatrix.report.json")
    triggers = load_report_records(repo_root, "PR164_PR163CRepairTriggerMatrix.report.json")
    if not triggers:
        raise RuntimeError("PR164 PR163-C trigger matrix is missing canonical trigger records")
    infra = load_report_records(repo_root, "PR164_PR163BInfrastructureRejectionReview.report.json")
    readiness = load_report_records(repo_root, "PR164_PR165ScoringReadinessMatrix.report.json")
    missing_fill = load_report_records(repo_root, "PR164_QKUMissingValueFillRouter.report.json")
    computability = load_report_records(repo_root, "PR164_QKUComputabilityMaterializationRegistry.report.json")
    execution_cost = load_report_records(repo_root, "PR164_ExecutionCostComponentCoverage.report.json")
    latency = load_report_records(repo_root, "PR164_LatencyHotPathClassifier.report.json")
    model_risk = load_report_records(repo_root, "PR164_ModelRiskInventoryForQKU.report.json")
    agent = load_report_records(repo_root, "PR164_AgentOrchestrationRouter.report.json")
    quantum = load_report_records(repo_root, "PR164_QuantumCompatibilityRouter.report.json")
    quantum_comparator = load_report_records(repo_root, "PR164_QuantumClassicalComparatorPreparation.report.json")
    source_rows = load_report_records(repo_root, "PR164_CandidateSourceAcquisitionLedger.report.json")
    point_sources = load_report_records(repo_root, "PR164_PointInTimeCandidateSourceLedger.report.json")
    return PR164Context(
        trigger_root=trigger_root,
        triggers=sorted(triggers, key=_trigger_sort_key),
        infrastructure_by_candidate=index_by_candidate(infra),
        readiness_rows=readiness,
        readiness_by_candidate_qku=index_by_candidate_qku(readiness),
        missing_fill_by_qku={str(row["qku_id"]): row for row in missing_fill if row.get("qku_id")},
        computability_by_candidate_qku=index_by_candidate_qku(computability),
        execution_cost_by_candidate_qku=index_by_candidate_qku(execution_cost),
        latency_by_candidate_qku=index_by_candidate_qku(latency),
        model_risk_by_qku={str(row["qku_id"]): row for row in model_risk if row.get("qku_id")},
        agent_by_candidate_qku=index_by_candidate_qku(agent),
        quantum_by_candidate_qku=index_by_candidate_qku(quantum),
        quantum_comparator_by_candidate_qku=index_by_candidate_qku(quantum_comparator),
        source_rows=source_rows,
        point_in_time_source_rows=point_sources,
        pr163b_tca_by_candidate=_optional_pr163b_index(repo_root, "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json"),
        pr163b_fill_by_candidate=_optional_pr163b_index(repo_root, "PR163_B_ReplayPaperFillIntegrityReceiptRegistry.report.json"),
        pr163b_divergence_by_candidate=_optional_pr163b_index(repo_root, "PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json"),
        pr163b_remediation_by_candidate=_optional_pr163b_index(repo_root, "PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json"),
    )


def _optional_pr163b_index(repo_root: Path, filename: str) -> dict[str, dict[str, Any]]:
    path = repo_root / "docs/master_plan/generated" / filename
    if not path.exists():
        return {}
    return index_by_candidate(load_report_records(repo_root, filename))


def _trigger_sort_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    qku = str((row.get("qku_ids") or [""])[0])
    candidate = str(row.get("candidate_id") or "")
    remediation = str(row.get("remediation_ref") or "")
    reason = str(row.get("repair_trigger_reason") or "")
    route_ref = str(row.get("downstream_route_record_ref") or "")
    return qku, candidate, remediation, reason, route_ref
