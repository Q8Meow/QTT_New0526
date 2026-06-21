#!/usr/bin/env python3
"""PR165-D2 agent routing and every-value crosswalks for DATA1A."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import REQUIRED_REPORT_IDS, generated_ref, report_path, route_defaults
from tools.pr168_data1a_input_discovery import AGENT_DUTY_PATH, AGENT_ROSTER_PATH


def build_agent_routing(created_at_utc: str, *, row_counts: dict[str, int]) -> dict[str, Any]:
    consumed = AGENT_ROSTER_PATH.exists() and AGENT_DUTY_PATH.exists()
    return {
        "agent_routing_id": "pr168_data1a_agent_routing_and_no_orphan_proof",
        "created_at_utc": created_at_utc,
        "PR165_D2_AgentRosterDiscoveryAudit_consumed_flag": AGENT_ROSTER_PATH.exists(),
        "PR165_D2_AgentDutySourceCrosswalk_consumed_flag": AGENT_DUTY_PATH.exists(),
        "agent_crosswalk_consumed_flag": consumed,
        "agent_roster_ref": generated_ref(AGENT_ROSTER_PATH),
        "agent_duty_ref": generated_ref(AGENT_DUTY_PATH),
        "route_classes": [
            "market_data_acquisition_agent",
            "source_evidence_agent",
            "venue_specialist_agent",
            "qku_formula_materialization_agent",
            "quantum_optimizer_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
            "risk_tca_capacity_agent",
            "dashboard_operator_agent",
            "governance_validation_agent",
        ],
        "row_counts_by_family": row_counts,
        "no_orphan_violation_count": 0 if consumed else 1,
        **route_defaults("governance", upstream_refs=[generated_ref(AGENT_ROSTER_PATH), generated_ref(AGENT_DUTY_PATH)]),
    }


def build_every_value_rows(
    created_at_utc: str,
    *,
    report_ids: list[str],
    shard_manifests: list[dict[str, Any]],
    count_rows: list[dict[str, Any]],
    operator_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report_id in report_ids:
        rows.append(
            {
                "artifact_or_value_id": report_id,
                "artifact_or_value_type": "report",
                "file_path_if_any": generated_ref(report_path(report_id)),
                "source_row_refs": [],
                "computed_from_refs": ["DATA1 artifacts", "PR165-D2 agent crosswalk"],
                "DATA1_artifact_refs": ["docs/master_plan/generated/PR168_DATA1_FinalSummary.report.json"],
                "upstream_refs": ["PR168-DATA1", "PR165-D2"],
                "repair_route_if_gap": None,
                "created_at_utc": created_at_utc,
                **route_defaults("governance", data1_refs=["docs/master_plan/generated/PR168_DATA1_FinalSummary.report.json"]),
            }
        )
    for manifest in shard_manifests:
        rows.append(
            {
                "artifact_or_value_id": manifest["manifest_id"],
                "artifact_or_value_type": "row_shard_manifest",
                "file_path_if_any": manifest["shard_path"].replace(".jsonl", ".manifest.json"),
                "source_row_refs": manifest.get("row_refs", []),
                "computed_from_refs": [manifest["shard_path"]],
                "DATA1_artifact_refs": manifest.get("DATA1_artifact_refs", []),
                "upstream_refs": ["PR168-DATA1"],
                "repair_route_if_gap": None,
                "created_at_utc": created_at_utc,
                **route_defaults("governance", row_shard_refs=[manifest["shard_path"]]),
            }
        )
    for count in count_rows:
        rows.append(
            {
                "artifact_or_value_id": f"count::{count['count_name']}",
                "artifact_or_value_type": "summary_count",
                "file_path_if_any": generated_ref(report_path("PR168_DATA1A_CountConfidenceAndLineageLedger")),
                "source_row_refs": count.get("source_file_refs", []),
                "computed_from_refs": [count.get("row_selection_rule")],
                "DATA1_artifact_refs": count.get("source_file_refs", []),
                "upstream_refs": count.get("source_file_refs", []),
                "repair_route_if_gap": count.get("missing_or_unknown_reason"),
                "created_at_utc": created_at_utc,
                **route_defaults("governance", data1_refs=count.get("source_file_refs", [])),
            }
        )
    for action in operator_rows:
        rows.append(
            {
                "artifact_or_value_id": action["action_id"],
                "artifact_or_value_type": "operator_action",
                "file_path_if_any": generated_ref(report_path("PR168_DATA1A_OperatorActionMatrix")),
                "source_row_refs": [action.get("artifact_ref")],
                "computed_from_refs": [action.get("missing_input_or_gap_code")],
                "DATA1_artifact_refs": [action.get("artifact_ref")],
                "upstream_refs": [action.get("artifact_ref")],
                "repair_route_if_gap": action.get("next_command_or_next_pr"),
                "created_at_utc": created_at_utc,
                **route_defaults("governance", data1_refs=[str(action.get("artifact_ref"))]),
            }
        )
    return rows


def build_agent_consumable_rows(every_value_rows: list[dict[str, Any]], created_at_utc: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(every_value_rows, start=1):
        rows.append(
            {
                "artifact_or_value_id": row["artifact_or_value_id"],
                "artifact_or_value_type": row["artifact_or_value_type"],
                "file_path_if_any": row.get("file_path_if_any"),
                "source_row_refs": row.get("source_row_refs", []),
                "computed_from_refs": row.get("computed_from_refs", []),
                "DATA1_artifact_refs": row.get("DATA1_artifact_refs", []),
                "upstream_refs": row.get("upstream_refs", []),
                "downstream_consumers": row.get("downstream_consumers", []),
                "downstream_pr_refs": row.get("downstream_pr_refs", []),
                "owning_agent": row.get("owning_agent"),
                "consumer_agents": row.get("consumer_agents", []),
                "validator_refs": row.get("validator_refs", []),
                "test_refs": row.get("test_refs", []),
                "authority_class": row.get("authority_class"),
                "no_orphan_status": row.get("no_orphan_status"),
                "terminal_by_nature_flag": row.get("terminal_by_nature_flag", False),
                "terminal_reason_code_if_terminal": row.get("terminal_reason_code"),
                "repair_route_if_gap": row.get("repair_route_if_gap"),
                "agent_consumable_route_id": f"agent_consumable_route_{index:05d}",
                "created_at_utc": created_at_utc,
                **{key: row[key] for key in row if key.endswith("_flag") and key in row},
            }
        )
    return rows
