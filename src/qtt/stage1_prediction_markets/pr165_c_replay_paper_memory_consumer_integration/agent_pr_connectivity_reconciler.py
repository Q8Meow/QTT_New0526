"""Agent PR connectivity reconciliation for PR165-C."""

from __future__ import annotations

from .central_vocab import AUTHORITY_BOUNDARY_REF, DOWNSTREAM_PR_ROUTES, NO_ORPHAN_STATUS
from .older_agent_artifact_loader import older_agent_reference_bundle


def build_agent_pr_connectivity_rows(repo_root, agent_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    refs = older_agent_reference_bundle(repo_root)
    rows = []
    for index, row in enumerate(agent_rows, start=1):
        rows.append(
            {
                "agent_pr_connectivity_id": f"PR165_C_AGENT_PR_CONNECTIVITY::{index:04d}",
                "agent_id": row["agent_id"],
                **refs,
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "downstream_agent_workflow_refs": [
                    "PR165_C_AgentTaskQueue.report.json",
                    "PR165_C_ScenarioMemoryRouter.report.json",
                ],
                "supersedes_or_extends_existing_agent_duty_ref": "EXTENDS_PRIOR_QTT_AGENT_ROUTE_ARTIFACTS",
                "new_extension_reason_when_no_prior_artifact_exists": "",
                "owner_safe_downstream_route_when_new_extension": "PR165-D",
                "no_orphan_agent_duty_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows
