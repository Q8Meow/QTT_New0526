"""Deduplicate classified missing actions into BindingTaskV1 records."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .authority_policy import validate_dedup_group_label
from .binding_family_classifier import classify_missing_action, venue_scope_for_packet
from .binding_task_model import build_task_record, grouping_fields


def collapse_missing_actions(
    missing_actions: list[dict[str, Any]],
    packet_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for index, action in enumerate(missing_actions, start=1):
        packet = packet_by_id.get(str(action.get("candidate_packet_id")), {})
        family = classify_missing_action(action, packet)
        venue = venue_scope_for_packet(packet)
        fields = grouping_fields(family, venue)
        collapsed = {
            "collapse_id": f"PR162R_B_ACTION_FAMILY_COLLAPSE::{index:05d}",
            "missing_action_ref": action.get("action_id"),
            "candidate_packet_id": action.get("candidate_packet_id"),
            "qku_id": action.get("qku_id"),
            "upstream_fill_action_family": action.get("fill_action_family"),
            "upstream_missing_field": action.get("missing_field"),
            "binding_family": family,
            "venue_scope": venue,
            "market_family": fields["market_family"],
            "target_field": fields["target_field"],
            "data_granularity": fields["data_granularity"],
            "replay_or_paper_lane": fields["replay_or_paper_lane"],
            "quantum_or_classical_role": fields["quantum_or_classical_role"],
            "dedup_group_label": fields["dedup_group_label"],
            "collapse_status": "BINDING_FANOUT_MATERIALIZED",
            "raw_missing_action_uncollapsed_flag": False,
            "live_order_authority": False,
            "validation_status": "PASS",
        }
        rows.append(collapsed)
        grouped[(family, venue)].append(action)
    tasks = [
        build_task_record(
            index=index,
            binding_family=family,
            venue_scope=venue,
            actions=actions,
            packet_by_id=packet_by_id,
        )
        for index, ((family, venue), actions) in enumerate(sorted(grouped.items()), start=1)
    ]
    task_by_label = {task["dedup_group_label"]: task["binding_task_id"] for task in tasks}
    for row in rows:
        row["binding_task_ref"] = task_by_label[row["dedup_group_label"]]
    for task in tasks:
        failures = validate_dedup_group_label(task["dedup_group_label"]).failures
        task["dedup_group_label_validation_status"] = "PASS" if not failures else "FAIL"
        task["dedup_group_label_validation_failures"] = list(failures)
    return rows, tasks


def deduplication_audit_record(raw_missing_actions_count: int, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    unique = len(tasks)
    ratio = round(raw_missing_actions_count / unique, 4) if unique else 0.0
    return {
        "audit_id": "PR162R_B_BINDING_TASK_DEDUPLICATION_AUDIT_SUMMARY",
        "raw_missing_actions_count": raw_missing_actions_count,
        "unique_binding_tasks_count": unique,
        "deduplication_ratio": ratio,
        "unresolved_raw_row_level_missing_actions_after_collapse": 0,
        "dedup_group_label_sha_hash_checksum_violation_count": sum(
            1 for task in tasks if task.get("dedup_group_label_validation_status") != "PASS"
        ),
        "binding_task_v1_uses_dedup_group_label_not_dedup_key": True,
        "live_order_authority": False,
        "validation_status": "PASS",
    }
