"""Optional-input missing receipts for PR165-D."""

from __future__ import annotations

from typing import Any

from .authority_policy import authority_zero_counts
from .central_vocab import AUTHORITY_BOUNDARY_REF, DOWNSTREAM_PR_ROUTES, NO_ORPHAN_STATUS, UPSTREAM_PR_REFS, VALIDATION_STATUS
from .deterministic_ids import stable_ref
from .input_consumption import InputDiscovery

DOWNSTREAM_ROUTE_BY_GROUP = {
    "pr162e_formula_plugin_authority_outputs": "PR162E",
    "pr162f_owner_agent_formula_intake_outputs": "PR162F",
    "pr162e_q_quantum_auto_mapper_outputs": "PR162E-Q",
    "pr166_q_quantum_comparator_outputs": "PR166-Q",
    "unexpected_retest_result_artifacts": "PR166-S",
}


def receipt_id(group: str) -> str:
    return stable_ref("PR165_D_OPTIONAL_INPUT_RECEIPT", group)


def build_optional_input_missing_receipts(discovery: InputDiscovery) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in sorted(discovery.optional_missing):
        missing = list(discovery.optional_missing[group])
        if not missing:
            continue
        rows.append(
            {
                "optional_input_receipt_id": receipt_id(group),
                "optional_input_group": group,
                "missing_artifact_refs": missing,
                "present_artifact_refs": list(discovery.optional_present.get(group, ())),
                "optional_missing_route_status": "OPTIONAL_INPUT_MISSING_ROUTE_CREATED",
                "candidate_selection_continues": True,
                "score_promotion_allowed_by_pr165_d": False,
                "source_truth_conversion_allowed_by_pr165_d": False,
                "downstream_pr_route": DOWNSTREAM_ROUTE_BY_GROUP.get(group, "PR162E"),
                "agent_action_type": "OPTIONAL_INPUT_MATERIALIZATION_ROUTE",
                "owning_agent": "selection_agent",
                "consuming_agent": "commander_agent",
                "evidence_requirement": "UPSTREAM_ACCEPTED_ARTIFACT_REQUIRED_BEFORE_AUTHORITY_PROMOTION",
                "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
                "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": VALIDATION_STATUS,
                **authority_zero_counts(),
            }
        )
    return rows
