#!/usr/bin/env python3
"""Report writer helpers for PR168-DATA1."""

from __future__ import annotations

from typing import Mapping

from tools.pr168_data1_config import (
    REPORT_VERSION,
    TOOL_NAME,
    authority_flags,
    report_path,
    route_defaults,
)
from tools.pr168_data1_snapshot_writer import write_json


def report_payload(
    report_id: str,
    created_at_utc: str,
    records: object,
    *,
    route_key: str = "governance",
    upstream_input_refs: list[str] | None = None,
    snapshot_manifest_refs: list[str] | None = None,
    l2_replay_manifest_refs: list[str] | None = None,
    data_provenance_refs: list[str] | None = None,
    computed_feature_refs: list[str] | None = None,
    authority_class: str = "PUBLIC_READ_ONLY_DATA_ACQUISITION_CANDIDATE",
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
) -> dict[str, object]:
    route = route_defaults(route_key)
    payload = {
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "created_by_tool": TOOL_NAME,
        "created_at_utc": created_at_utc,
        "upstream_input_refs": upstream_input_refs or [],
        "snapshot_manifest_refs": snapshot_manifest_refs or [],
        "l2_replay_manifest_refs": l2_replay_manifest_refs or [],
        "data_provenance_refs": data_provenance_refs or [],
        "computed_feature_refs": computed_feature_refs or [],
        "owning_agent": route["owning_agent"],
        "downstream_consumers": route["downstream_consumers"],
        "downstream_pr_refs": route["downstream_pr_refs"],
        "validator_refs": route["validator_refs"],
        "test_refs": route["test_refs"],
        "no_orphan_status": "NO_ORPHAN_ROUTED",
        "terminal_by_nature_flag": terminal_by_nature_flag,
        "terminal_reason_code": terminal_reason_code,
        "authority_class": authority_class,
        "records": records,
        **authority_flags(),
    }
    return payload


def write_report(report_id: str, payload: Mapping[str, object]) -> None:
    write_json(report_path(report_id), dict(payload))
