"""Connectivity audit helpers for PR166-SM."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .enums import AgentId, NoOrphanStatus
from .models import common_fields, stable_id


def build_pr_file_connectivity_rows(created_files: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, file_path in enumerate(sorted(created_files), start=1):
        row_id = stable_id("PR166_SM_FILE_CONNECTIVITY", index)
        base = common_fields(
            artifact_id="PR166_SM_PR_FILE_CONNECTIVITY_AUDIT",
            row_id=row_id,
            upstream_artifact_refs=list(c.REQUIRED_INPUT_REPORTS[:6]),
            upstream_row_refs=[row_id],
            downstream_artifact_refs=[c.MANIFEST_REF],
            downstream_pr_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
            owning_agent=AgentId.GOVERNANCE.value,
            no_orphan_status=NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
        )
        base.update(
            {
                "file_path": file_path,
                "created_or_modified_by_pr": c.PR_ID,
                "purpose": "PR166-SM replay/paper score-memory refresh materialization",
                "upstream_files": list(c.REQUIRED_INPUT_REPORTS[:6]),
                "downstream_files": [c.MANIFEST_REF, "PR166_SM_FinalSummary.report.json"],
                "owning_module": c.PACKAGE_IMPORT,
                "validator": c.VALIDATOR_REF,
                "tests": "tests/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results",
                "report_manifest_ref": c.MANIFEST_REF,
            }
        )
        rows.append(base)
    return rows


def build_row_value_connectivity_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (report_name, report_rows) in enumerate(sorted(row_payloads.items()), start=1):
        row_id = stable_id("PR166_SM_ROW_VALUE_CONNECTIVITY", index)
        total = len(report_rows)
        base = common_fields(
            artifact_id="PR166_SM_ROW_VALUE_CONNECTIVITY_AUDIT",
            row_id=row_id,
            upstream_artifact_refs=list(c.REQUIRED_INPUT_REPORTS[:6]),
            upstream_row_refs=[row_id],
            downstream_artifact_refs=[report_name, c.MANIFEST_REF],
            downstream_pr_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
            owning_agent=AgentId.GOVERNANCE.value,
            no_orphan_status=NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
        )
        base.update(
            {
                "report_name": report_name,
                "source_reports": sorted({ref for row in report_rows for ref in row.get("upstream_artifact_refs", [])}),
                "source_row_ids": [str(row.get("row_id")) for row in report_rows[:20]],
                "derived_values": sorted({key for row in report_rows for key in row.keys() if key.endswith("_score") or key.endswith("_ratio")})[:50],
                "derivation_formula_ids": sorted({str(row.get("computable_formula_ref")) for row in report_rows}),
                "normalization_policy": c.NORMALIZATION_POLICY_REF,
                "score_policy": c.SCORE_POLICY_REF,
                "downstream_reports": sorted({ref for row in report_rows for ref in row.get("downstream_artifact_refs", [])}),
                "downstream_agents": sorted({agent for row in report_rows for agent in row.get("downstream_agent_consumers", [])}),
                "downstream_pr_routes": sorted({route for row in report_rows for route in row.get("downstream_pr_refs", [])}),
                "total_rows": total,
                "rows_with_upstream_refs": sum(1 for row in report_rows if row.get("upstream_artifact_refs")),
                "rows_with_downstream_refs": sum(1 for row in report_rows if row.get("downstream_artifact_refs")),
                "rows_with_agent": sum(1 for row in report_rows if row.get("owning_agent")),
                "rows_with_validator": sum(1 for row in report_rows if row.get("validator_ref")),
                "rows_with_schema": sum(1 for row in report_rows if row.get("schema_ref") is not None),
            }
        )
        rows.append(base)
    return rows


def tracked_file_list(repo_root: Path) -> list[str]:
    package_files = [str(c.PACKAGE_DIR / filename).replace("\\", "/") for filename in c.SOURCE_FILENAMES]
    schema_files = [str(c.SCHEMA_DIR / filename).replace("\\", "/") for filename in c.SCHEMA_FILENAMES]
    report_files = [str(c.GENERATED_DIR / filename).replace("\\", "/") for filename in c.REPORT_FILENAMES]
    tool_files = [
        c.BUILDER_REF,
        c.VALIDATOR_REF,
        "tools/run_validation_gates.py",
        "tools/ci_branch_context.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/tools/test_ci_branch_context.py",
    ]
    test_files = [
        str(path.relative_to(repo_root)).replace("\\", "/")
        for path in sorted((repo_root / c.TEST_DIR).glob("test_*.py"))
    ]
    return sorted(dict.fromkeys([*package_files, *schema_files, *report_files, *tool_files, *test_files]))
