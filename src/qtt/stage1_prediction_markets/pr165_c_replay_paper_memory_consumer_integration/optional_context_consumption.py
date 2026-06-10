"""Optional context receipts for PR165-C."""

from __future__ import annotations

from . import paths as p
from .artifact_discovery import InputDiscovery
from .central_vocab import AUTHORITY_BOUNDARY_REF, NO_ORPHAN_STATUS


def build_optional_context_receipts(discovery: InputDiscovery) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (group, missing) in enumerate(sorted(discovery.optional_missing.items()), start=1):
        present = discovery.optional_present[group]
        status = "OPTIONAL_CONTEXT_PRESENT" if not missing else "OPTIONAL_CONTEXT_PARTIAL_OR_ABSENT_WITH_RECEIPT"
        rows.append(
            {
                "optional_context_receipt_id": f"PR165_C_OPTIONAL_CONTEXT::{index:04d}",
                "context_group": group,
                "present_paths": [p.normalize_repo_ref(path) for path in present],
                "missing_paths": [p.normalize_repo_ref(path) for path in missing],
                "missing_count": len(missing),
                "consumption_status": status,
                "continue_decision": "CONTINUE_WITH_REQUIRED_PR165_AND_PR165_B_INPUTS",
                "downstream_pr_route": "PR165-D" if group != "retest_result_artifacts" else "retest-result-refresh-PR",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def build_crosswalk_consumption_audit(discovery: InputDiscovery) -> list[dict[str, object]]:
    groups = ("route_triage", "full_master_plan_crosswalk", "market_specific_section_index", "command_action_matrix")
    rows = []
    for index, group in enumerate(groups, start=1):
        rows.append(
            {
                "crosswalk_consumption_id": f"PR165_C_CROSSWALK_CONSUMPTION::{index:04d}",
                "context_group": group,
                "present_paths": [p.normalize_repo_ref(path) for path in discovery.optional_present.get(group, ())],
                "missing_paths": [p.normalize_repo_ref(path) for path in discovery.optional_missing.get(group, ())],
                "consumption_result": "CONSUMED_WHEN_PRESENT_WITH_RECEIPT",
                "downstream_report_refs": [
                    "PR165_C_AgentPRConnectivityReconciliation.report.json",
                    "PR165_C_PRFileConnectivityAudit.report.json",
                ],
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows
