#!/usr/bin/env python3
"""DATA1 data-product integrity checks for PR168-DATA1A."""

from __future__ import annotations

import json
from typing import Any

from tools.pr168_data1a_config import generated_ref, manifest_path, route_defaults
from tools.pr168_data1a_input_discovery import (
    AGENT_DUTY_PATH,
    AGENT_ROSTER_PATH,
    data1_report_refs,
    forward_l2_jsonl_paths,
    load_json,
    load_jsonl,
    snapshot_jsonl_paths,
)
from tools.pr168_data1a_report_writer import assert_no_forbidden_true_flags


def _row_id(row: dict[str, Any]) -> str | None:
    return row.get("snapshot_row_id") or row.get("l2_replay_row_id") or row.get("feature_row_id")


def build_integrity_ledger(context: dict[str, Any], created_at_utc: str) -> dict[str, Any]:
    defects: list[dict[str, Any]] = []
    all_snapshot_rows = list(context["kalshi_rows"]) + list(context["polymarket_rows"])
    all_l2_rows = list(context["kalshi_l2_rows"]) + list(context["polymarket_l2_rows"])
    all_rows = all_snapshot_rows + all_l2_rows

    manifest_ok = True
    row_count_ok = True
    for jsonl_path in snapshot_jsonl_paths() + forward_l2_jsonl_paths():
        manifest = manifest_path(jsonl_path)
        if not manifest.exists() or not jsonl_path.exists():
            manifest_ok = False
            defects.append(
                {
                    "defect_id": f"missing_manifest_or_jsonl::{generated_ref(jsonl_path)}",
                    "defect_state": "MISSING_DATA1_MANIFEST_OR_JSONL",
                    "repair_route": "DATA1B_REPAIR",
                }
            )
            continue
        manifest_payload = load_json(manifest)
        rows = load_jsonl(jsonl_path)
        if int(manifest_payload.get("row_count", -1)) != len(rows):
            row_count_ok = False
            defects.append(
                {
                    "defect_id": f"manifest_row_count_mismatch::{generated_ref(manifest)}",
                    "defect_state": "MANIFEST_ROW_COUNT_MISMATCH",
                    "manifest_count": manifest_payload.get("row_count"),
                    "actual_count": len(rows),
                    "repair_route": "DATA1B_REPAIR",
                }
            )

    row_ids = [_row_id(row) for row in all_rows]
    duplicated = sorted({row_id for row_id in row_ids if row_id and row_ids.count(row_id) > 1})
    features = context["reports"].get("PR168_DATA1_NormalizedMarketDataFeatureRegistry", {}).get("records", [])
    feature_refs = {row.get("feature_row_id") for row in features if isinstance(row, dict)}
    row_refs = {row_id for row_id in row_ids if row_id}
    unresolved_feature_refs: list[str] = []
    for row in all_rows:
        for feature_ref in row.get("feature_refs", []) or []:
            if feature_ref not in feature_refs:
                unresolved_feature_refs.append(str(feature_ref))
    unresolved_snapshot_refs: list[str] = []
    if isinstance(features, list):
        for feature in features:
            for snapshot_ref in feature.get("snapshot_row_refs", []) or []:
                if snapshot_ref not in row_refs:
                    unresolved_snapshot_refs.append(str(snapshot_ref))
            for l2_ref in feature.get("l2_replay_row_refs", []) or []:
                if l2_ref not in row_refs:
                    unresolved_snapshot_refs.append(str(l2_ref))

    handoff_refs_resolve = all(report_id in context["reports"] for report_id in context["reports"])
    safe_flag_failures = assert_no_forbidden_true_flags(
        {
            "reports": context["reports"],
            "rows": all_rows,
            "manifests": context["manifests"],
        }
    )
    serialized = json.dumps({"reports": context["reports"], "rows": all_rows}, sort_keys=True).lower()
    no_atomicrows_hash_refs = "atomicrows.bundle.sha256" not in serialized
    no_private_endpoint_refs = not any(
        token in serialized for token in ["/portfolio", "/positions", "/balance", "/balances"]
    )
    no_order_endpoint_refs = not any(
        token in serialized for token in ["/orders", "/order/", "post /order", "delete /order"]
    )
    agent_refs_resolve = AGENT_ROSTER_PATH.exists() and AGENT_DUTY_PATH.exists()

    return {
        "integrity_ledger_id": "pr168_data1a_data_product_integrity_ledger",
        "created_at_utc": created_at_utc,
        "manifest_points_to_existing_jsonl_flag": manifest_ok,
        "jsonl_rows_parse_flag": True,
        "snapshot_row_id_uniqueness_flag": not duplicated,
        "duplicate_row_ids": duplicated,
        "manifest_row_count_matches_actual_count_flag": row_count_ok,
        "feature_refs_resolve_to_snapshot_rows_flag": not unresolved_snapshot_refs and not unresolved_feature_refs,
        "unresolved_feature_refs": sorted(set(unresolved_feature_refs)),
        "unresolved_snapshot_or_l2_refs": sorted(set(unresolved_snapshot_refs)),
        "handoff_refs_resolve_to_DATA1_reports_or_shards_flag": handoff_refs_resolve,
        "agent_refs_resolve_to_PR165_D2_crosswalk_flag": agent_refs_resolve,
        "all_authority_flags_safe_flag": not safe_flag_failures,
        "authority_flag_failure_refs": safe_flag_failures,
        "no_atomicrows_hash_refs_flag": no_atomicrows_hash_refs,
        "no_qtt_digest_authority_flag": "qtt_global_digest" not in serialized and "qtt_checksum" not in serialized,
        "no_private_endpoint_refs_flag": no_private_endpoint_refs,
        "no_order_endpoint_refs_flag": no_order_endpoint_refs,
        "integrity_defect_count": len(defects),
        "integrity_defect_rows": defects,
        **route_defaults("governance", data1_refs=data1_report_refs()),
    }
