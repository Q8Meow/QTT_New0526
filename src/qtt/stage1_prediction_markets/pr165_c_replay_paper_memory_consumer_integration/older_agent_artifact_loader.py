"""Load older QTT-agent artifacts that PR165-C extends."""

from __future__ import annotations

from pathlib import Path

from . import paths as p
from .central_vocab import AUTHORITY_BOUNDARY_REF, NO_ORPHAN_STATUS

OLDER_AGENT_ARTIFACTS = (
    "docs/master_plan/generated/PR161D_QKUAgentGraphRoutingMatrix.report.json",
    "docs/master_plan/generated/PR161D_QKUAgentTaskQueue.report.json",
    "docs/master_plan/generated/PR161D_QTTAgentRoleNetworkRegistry.report.json",
    "docs/master_plan/generated/PR161D_QKUAgentRoleBundleSlice.report.json",
    "docs/master_plan/generated/PR163_B_PairedReplayPaperResultCandidateRegistry.report.json",
    "docs/master_plan/generated/PR163_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "docs/master_plan/generated/PR164_AgentOrchestrationRouter.report.json",
    "docs/master_plan/generated/PR164_QKUUpstreamDownstreamClosureMatrix.report.json",
    "docs/master_plan/generated/PR164_QuantumCompatibilityRouter.report.json",
    "docs/master_plan/generated/PR163_C_AgentTaskHandoffMatrix.report.json",
    "docs/master_plan/generated/PR163_C_RepairToPR165ReadinessHandoff.report.json",
    "docs/master_plan/generated/PR165_AgentScoringOrchestrationRouter.report.json",
    "docs/master_plan/generated/PR165_QKUAgentConsumerCoverageMatrix.report.json",
    "docs/master_plan/generated/PR165_DashboardScoreHandoff.report.json",
    "docs/master_plan/generated/PR165_B_AgentMemoryRouter.report.json",
    "docs/master_plan/generated/PR165_B_DashboardMemoryHandoff.report.json",
    "docs/master_plan/generated/PR165_B_GovernanceMemoryHandoff.report.json",
)


def load_older_agent_artifact_refs(repo_root: Path) -> tuple[str, ...]:
    return tuple(
        p.normalize_repo_ref(rel)
        for rel in OLDER_AGENT_ARTIFACTS
        if p.resolve_repo_relative(repo_root, rel).exists()
    )


def build_older_agent_artifact_consumption_rows(repo_root: Path) -> list[dict[str, object]]:
    rows = []
    for index, rel_path in enumerate(load_older_agent_artifact_refs(repo_root), start=1):
        rows.append(
            {
                "older_agent_artifact_consumption_id": f"PR165_C_OLDER_AGENT_ARTIFACT::{index:04d}",
                "artifact_path": p.normalize_repo_ref(rel_path),
                "artifact_present": True,
                "consumed_by_pr165_c": True,
                "consumption_role": _role_for_path(rel_path),
                "downstream_pr165_c_report_refs": [
                    "PR165_C_AgentDutyDistinctnessMatrix.report.json",
                    "PR165_C_AgentPRConnectivityReconciliation.report.json",
                    "PR165_C_LineageGraph.report.json",
                ],
                "not_consumed_reason": "",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def older_agent_reference_bundle(repo_root: Path) -> dict[str, list[str]]:
    refs = load_older_agent_artifact_refs(repo_root)
    return {
        "upstream_agent_pr_refs": ["PR161D", "PR163", "PR163-B", "PR164", "PR163-C", "PR165", "PR165-B"],
        "upstream_qku_agent_route_refs": [ref for ref in refs if "QKUAgent" in ref or "QKU" in ref][:8],
        "upstream_agent_manifest_refs": [ref for ref in refs if "RoleNetwork" in ref or "OrchestrationRouter" in ref][:8],
        "upstream_agent_task_queue_refs": [ref for ref in refs if "Task" in ref][:8],
        "upstream_agent_role_slice_refs": [ref for ref in refs if "RoleBundle" in ref or "RoleNetwork" in ref][:8],
        "upstream_dashboard_handoff_refs": [ref for ref in refs if "Dashboard" in ref][:8],
        "upstream_governance_handoff_refs": [ref for ref in refs if "Governance" in ref][:8],
        "upstream_commander_handoff_refs": ["PR165_B_GovernanceMemoryHandoff.commander_summary_route"],
    }


def _role_for_path(rel_path: str) -> str:
    lowered = rel_path.lower()
    if "dashboard" in lowered:
        return "UPSTREAM_DASHBOARD_HANDOFF"
    if "governance" in lowered:
        return "UPSTREAM_GOVERNANCE_HANDOFF"
    if "task" in lowered:
        return "UPSTREAM_AGENT_TASK_QUEUE"
    if "qku" in lowered:
        return "UPSTREAM_QKU_AGENT_ROUTE"
    return "UPSTREAM_AGENT_MANIFEST"
