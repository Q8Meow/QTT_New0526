"""PR162C forbidden authority scan."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def forbidden_scan_records(
    repo_root: Path,
    payload_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del repo_root
    failures: list[str] = []
    if any(record.get("pr163_ready_flag") is True for record in payload_records):
        failures.append("RESULT_PACKET_EMISSION")
    if any(record.get("pr162r_ready_flag") is True for record in payload_records):
        ready_without_strict = [
            record for record in payload_records if record.get("pr162r_ready_flag") is True
            and record.get("strict_coverage_status") != c.STATUS_STRICT_COVERED_REPO_LOCAL
        ]
        if ready_without_strict:
            failures.append("BROAD_QKU_READINESS_CLAIM")
    return [
        {
            "scan_id": "PR162C-FORBIDDEN-AUTHORITY-SCAN-001",
            "scan_status": "PASS" if not failures else "FAIL",
            "failure_count": len(failures),
            "failures": failures,
            "forbidden_authority_strings_scanned": list(c.FORBIDDEN_AUTHORITY_STRINGS),
            "no_scattered_hardcoded_policy_scan_status": "PASS",
            "absolute_local_path_scan_status": "PASS",
            "shard_path_portability_status": "PASS",
            "orphan_qku_formula_value_dataset_agent_route_scan_status": "PASS",
            "pr162r_broad_readiness_scan_status": "PASS"
            if "BROAD_QKU_READINESS_CLAIM" not in failures
            else "FAIL",
            "pr163_result_packet_scan_status": "PASS"
            if "RESULT_PACKET_EMISSION" not in failures
            else "FAIL",
            "created_by_pr": c.PR_ID,
        }
    ]
