"""Report manifest helpers."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .enums import AgentId, NoOrphanStatus
from .models import common_fields, stable_id


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        payload = payloads.get(filename, {})
        row_id = stable_id("PR166_SM_MANIFEST", index)
        base = common_fields(
            artifact_id="PR166_SM_REPORT_MANIFEST",
            row_id=row_id,
            upstream_artifact_refs=list(c.REQUIRED_INPUT_REPORTS),
            upstream_row_refs=[row_id],
            downstream_artifact_refs=[filename],
            downstream_pr_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
            owning_agent=AgentId.GOVERNANCE.value,
            no_orphan_status=NoOrphanStatus.CONNECTED_UPSTREAM_AND_DOWNSTREAM.value,
        )
        base.update(
            {
                "report_name": filename.replace(".report.json", ""),
                "report_path": f"docs/master_plan/generated/{filename}",
                "schema_path": f"{c.SCHEMA_DIR.as_posix()}/{c.REPORT_SCHEMA_REFS[filename]}",
                "schema_ref": c.REPORT_SCHEMA_REFS[filename],
                "row_count": int(payload.get("record_count", 0) or 0),
                "shard_count": int(payload.get("shard_count", 0) or 0),
                "created_by_pr": c.PR_ID,
                "upstream_refs": list(c.UPSTREAM_PR_REFS),
                "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
                "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
                "deterministic_generation_order": index,
            }
        )
        rows.append(base)
    return rows
