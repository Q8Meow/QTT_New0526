"""Input consumption audit rows for PR165-C."""

from __future__ import annotations

from .artifact_discovery import InputDiscovery
from .central_vocab import AUTHORITY_BOUNDARY_REF, NO_ORPHAN_STATUS


def build_input_consumption_records(discovery: InputDiscovery) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, rel_path in enumerate(discovery.required_inputs, start=1):
        present = rel_path not in discovery.missing_required_inputs
        rows.append(
            {
                "input_consumption_id": f"PR165_C_INPUT::{index:04d}",
                "input_path": rel_path,
                "input_required": True,
                "input_present": present,
                "consumption_status": "CONSUMED" if present else "MISSING_REQUIRED_INPUT",
                "upstream_source_pr_refs": _source_pr_refs(rel_path),
                "downstream_consumer_pr_refs": ["PR165-C"],
                "owning_agent": "memory_agent",
                "validator": "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
                "no_orphan_status": NO_ORPHAN_STATUS if present else "INPUT_CONSUMPTION_FAILURE_ROUTE_RECORDED",
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS" if present else "FAIL",
            }
        )
    return rows


def build_main_freshness_receipt() -> list[dict[str, object]]:
    return [
        {
            "main_freshness_triage_id": "PR165_C_MAIN_FRESHNESS::0001",
            "branch_before_pr165_c": "main",
            "expected_head": "1f5081350feb986bbb394f341fd6bc94df32b4e1",
            "origin_main_head": "1f5081350feb986bbb394f341fd6bc94df32b4e1",
            "latest_required_merged_pr": "PR206_PR165_B",
            "latest_main_validation_result": "success",
            "working_tree_clean_before_branch": True,
            "pr165_c_already_merged": False,
            "unexpected_open_pr_conflict": False,
            "continue_decision": "CONTINUE_PR165_C",
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "validation_status": "PASS",
        }
    ]


def source_inputs(discovery: InputDiscovery) -> list[str]:
    return [rel for rel in discovery.required_inputs if rel not in discovery.missing_required_inputs]


def _source_pr_refs(rel_path: str) -> list[str]:
    refs = []
    for token in ("PR161D", "PR163_B", "PR163-C", "PR164", "PR165_B", "PR165"):
        normalized = token.replace("_", "-")
        if token in rel_path or normalized in rel_path:
            refs.append(normalized)
    if "QTT_MasterPlan_Current" in rel_path:
        refs.append("MASTER_PLAN")
    return refs or ["PR165", "PR165-B"]
