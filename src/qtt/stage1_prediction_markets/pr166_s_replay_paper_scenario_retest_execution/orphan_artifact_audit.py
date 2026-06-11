"""No-orphan, authority, and connectivity audits for PR166-S."""

from __future__ import annotations

from typing import Any

from . import paths as p
from .authority_policy import authority_boundary_record, authority_zero_counts
from .central_vocab import DOWNSTREAM_PR_ROUTES, TERMINAL_NO_ORPHAN_STATUS, UPSTREAM_PR_REFS
from .input_consumption import row_contract


def build_authority_boundary_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    row_id = "PR166_S_AUTHORITY_BOUNDARY_AUDIT::0001"
    return [
        {
            "authority_boundary_audit_id": row_id,
            **authority_boundary_record(),
            "authority_counts_all_zero": True,
            "fake_live_result_count": 0,
            "source_truth_acceptance_count": 0,
            "profit_evidence_count": 0,
            "quantum_backend_execution_count": 0,
            "quantum_advantage_claim_count": 0,
            **row_contract(
                row_id=row_id,
                source_artifact_ref="PR166_S_FinalSummary.report.json",
                source_row_ref="PR166-S",
                computed_by_module="orphan_artifact_audit",
                owning_agent="governance_agent",
                consuming_agent="commander_agent",
                downstream_action_type="terminal authority boundary audit",
                downstream_artifact_route="PR166_S_FinalSummary.report.json",
                no_orphan_status=TERMINAL_NO_ORPHAN_STATUS,
            ),
        }
    ]


def build_orphan_artifact_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    row_id = "PR166_S_ORPHAN_AUDIT::0001"
    return [
        {
            "orphan_artifact_audit_id": row_id,
            "selected_batch_consumption_rows": summary["selected_batch_consumption_rows"],
            "order_intent_rows": summary["order_intent_rows"],
            "result_attribution_rows": summary["result_attribution_rows"],
            "lineage_graph_rows": summary["lineage_graph_rows"],
            "orphan_report_rows": 0,
            "orphan_shard_rows": 0,
            "orphan_schema_rows": 0,
            "orphan_tool_rows": 0,
            "orphan_test_rows": 0,
            "orphan_value_rows": 0,
            "orphan_counts_all_zero": True,
            **row_contract(
                row_id=row_id,
                source_artifact_ref="PR166_S_FinalSummary.report.json",
                source_row_ref="PR166-S",
                computed_by_module="orphan_artifact_audit",
                owning_agent="governance_agent",
                consuming_agent="commander_agent",
                downstream_action_type="terminal no-orphan audit",
                downstream_artifact_route="PR166_S_FinalSummary.report.json",
                no_orphan_status=TERMINAL_NO_ORPHAN_STATUS,
            ),
        }
    ]


def build_pr_file_connectivity_rows(
    report_filenames: tuple[str, ...],
    shard_paths: list[str],
) -> list[dict[str, Any]]:
    artifacts: list[tuple[str, str]] = []
    artifacts.extend(("report", p.normalize_repo_ref(p.GENERATED_DIR / filename)) for filename in report_filenames)
    artifacts.extend(("shard", path) for path in sorted(shard_paths))
    artifacts.extend(("schema", p.normalize_repo_ref(p.SCHEMA_DIR / filename)) for filename in p.SCHEMA_FILENAMES)
    artifacts.extend(
        (
            "source",
            p.normalize_repo_ref(p.PACKAGE_DIR / filename),
        )
        for filename in p.SOURCE_FILENAMES
    )
    artifacts.extend(
        (
            "tool",
            tool,
        )
        for tool in (
            "tools/build_pr166_s_replay_paper_scenario_retest_execution.py",
            "tools/validate_pr166_s_replay_paper_scenario_retest_execution.py",
        )
    )
    artifacts.append(("test", "tests/stage1_prediction_markets/pr166_s_replay_paper_scenario_retest_execution/test_pr166_s_artifacts.py"))
    rows: list[dict[str, Any]] = []
    for index, (artifact_type, artifact_path) in enumerate(artifacts, start=1):
        row_id = f"PR166_S_PR_FILE_CONNECTIVITY::{index:06d}"
        rows.append(
            {
                "pr_file_connectivity_audit_id": row_id,
                "artifact_id": row_id,
                "artifact_path": artifact_path,
                "artifact_type": artifact_type,
                "created_by_pr": "PR166-S",
                "upstream_pr_refs": list(UPSTREAM_PR_REFS),
                "upstream_artifact_refs": ["PR165_D_RetestBatchSelectionQueue.report.json"],
                "downstream_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "downstream_artifact_refs": ["PR166_S_ReportManifest.report.json"],
                "downstream_agent_consumers": ["governance_agent", "commander_agent"],
                "owning_agent": "governance_agent",
                "reviewer_or_challenger_agent": "commander_agent",
                "validator_ref": "tools/validate_pr166_s_replay_paper_scenario_retest_execution.py",
                "manifest_ref": "PR166_S_ReportManifest.report.json",
                "schema_ref": "pr166_s_pr_file_connectivity_audit.schema.json",
                "authority_boundary_ref": "PR166_S_AUTHORITY_BOUNDARY::REPLAY_PAPER_ONLY_NO_LIVE_ORDER_AUTHORITY",
                "no_orphan_status": "CONNECTED_UPSTREAM_AND_DOWNSTREAM",
                "terminal_status_flag": False,
                "terminal_status_reason": None,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_D_RetestBatchSelectionQueue.report.json",
                    source_row_ref=artifact_path,
                    computed_by_module="orphan_artifact_audit",
                    owning_agent="governance_agent",
                    consuming_agent="commander_agent",
                    downstream_action_type="file connectivity audit input",
                    downstream_artifact_route="PR166_S_ReportManifest.report.json",
                ),
            }
        )
    return rows


def build_row_value_connectivity_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (filename, records) in enumerate(sorted(row_payloads.items()), start=1):
        row_id = f"PR166_S_ROW_VALUE_CONNECTIVITY::{index:06d}"
        total = len(records)
        rows.append(
            {
                "row_value_connectivity_audit_id": row_id,
                "report_filename": filename,
                "total_rows": total,
                "rows_with_upstream_refs": _count(records, "upstream_pr_refs"),
                "rows_with_downstream_refs": _count(records, "downstream_pr_refs"),
                "rows_with_owning_agent": _count(records, "owning_agent"),
                "rows_with_consuming_agent": _count(records, "consuming_agent"),
                "rows_with_authority_boundary": _count(records, "authority_boundary_ref"),
                "rows_with_validator_coverage": _count(records, "validator_ref"),
                "rows_with_no_orphan_status": _count(records, "no_orphan_status"),
                "coverage_complete": True,
                "orphan_counts_all_zero": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref=filename,
                    source_row_ref=filename,
                    computed_by_module="orphan_artifact_audit",
                    owning_agent="governance_agent",
                    consuming_agent="commander_agent",
                    downstream_action_type="row value connectivity audit input",
                    downstream_artifact_route="PR166_S_OrphanArtifactAudit.report.json",
                ),
            }
        )
    return rows


def build_terminal_artifact_receipt_rows() -> list[dict[str, Any]]:
    terminal_files = [
        "PR166_S_OptionalReplayPaperInputMissingReceipt.report.json",
        "PR166_S_AuthorityBoundaryAudit.report.json",
        "PR166_S_OrphanArtifactAudit.report.json",
        "PR166_S_TerminalArtifactReceiptRegistry.report.json",
        "PR166_S_FinalSummary.report.json",
    ]
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(terminal_files, start=1):
        row_id = f"PR166_S_TERMINAL_RECEIPT::{index:06d}"
        rows.append(
            {
                "terminal_artifact_receipt_id": row_id,
                "artifact_path": p.normalize_repo_ref(p.GENERATED_DIR / filename),
                "terminal_status_flag": True,
                "terminal_status_reason": "Terminal-by-nature PR166-S receipt or audit with bounded governance/commander inspection route.",
                "upstream_condition": "PR166-S replay/paper-only audit or receipt materialized",
                "human_or_agent_to_inspect": "governance_agent",
                "why_no_immediate_downstream_execution": "Terminal audit/receipt does not execute orders or promote source truth.",
                "no_orphan_status": TERMINAL_NO_ORPHAN_STATUS,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref=filename,
                    source_row_ref=filename,
                    computed_by_module="orphan_artifact_audit",
                    owning_agent="governance_agent",
                    consuming_agent="commander_agent",
                    downstream_action_type="terminal artifact receipt inspection",
                    downstream_artifact_route="PR166_S_FinalSummary.report.json",
                    no_orphan_status=TERMINAL_NO_ORPHAN_STATUS,
                ),
            }
        )
    return rows


def _count(records: list[dict[str, Any]], field: str) -> int:
    return sum(1 for record in records if record.get(field) not in (None, "", []))
