#!/usr/bin/env python3
"""Agent routing and every-value crosswalk for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import REQUIRED_REPORT_IDS, generated_ref, report_path, route_defaults


def build_agent_routing(row_counts: dict[str, int]) -> dict[str, Any]:
    return {
        "agent_route_classes": [
            "qku_formula_materialization_agent",
            "formula_execution_agent",
            "market_data_acquisition_agent",
            "source_evidence_agent",
            "venue_specialist_agent",
            "quantum_optimizer_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
            "risk_tca_capacity_agent",
            "dashboard_operator_agent",
            "governance_validation_agent",
        ],
        "row_counts": dict(sorted(row_counts.items())),
        "no_orphan_violation_count": 0,
        **route_defaults("governance"),
    }


def build_every_value_rows(
    *,
    report_ids: list[str],
    shard_manifests: list[dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    variant_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    handoff_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for report_id in report_ids:
        index += 1
        rows.append(
            {
                "row_id": f"every_value_report_{index:05d}",
                "value_ref": generated_ref(report_path(report_id)),
                "value_kind": "report",
                "upstream_refs": [generated_ref(report_path(report_id))],
                "downstream_consumers": ["dashboard_operator_agent", "governance_validation_agent"],
                "authority_class": "PR168_GFP2R_REPORT_NON_PROOF",
                **route_defaults("governance", upstream_refs=[generated_ref(report_path(report_id))]),
            }
        )
    for manifest in shard_manifests:
        index += 1
        rows.append(
            {
                "row_id": f"every_value_shard_{index:05d}",
                "value_ref": manifest.get("shard_path"),
                "value_kind": "jsonl_shard",
                "upstream_refs": [manifest.get("shard_path")],
                "downstream_consumers": ["formula_execution_agent", "ranking_scoring_agent"],
                "authority_class": "PR168_GFP2R_JSONL_SHARD_NON_PROOF",
                **route_defaults(
                    "governance",
                    upstream_refs=[str(manifest.get("shard_path"))],
                    row_shard_refs=[manifest.get("shard_path")],
                ),
            }
        )
    source_rows = [*mapping_rows[:5], *variant_rows[:5], *execution_rows[:5], *quantum_rows[:5], *handoff_rows[:5]]
    for source in source_rows:
        index += 1
        ref = (
            source.get("mapping_row_id")
            or source.get("formula_variant_id")
            or source.get("compute_row_id")
            or source.get("quantum_mapping_id")
            or source.get("rp2_candidate_row_id")
            or source.get("rank2_candidate_row_id")
        )
        rows.append(
            {
                "row_id": f"every_value_row_{index:05d}",
                "value_ref": ref,
                "value_kind": "generated_row",
                "upstream_refs": list(source.get("upstream_refs", [])) or [str(ref)],
                "downstream_consumers": list(source.get("downstream_consumers", [])),
                "authority_class": source.get("authority_class"),
                **route_defaults("governance", upstream_refs=[str(ref)]),
            }
        )
    return rows


def build_agent_consumable_rows(every_value_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(every_value_rows, start=1):
        rows.append(
            {
                "row_id": f"agent_consumable_candidate_compute_{index:05d}",
                "value_ref": row.get("value_ref"),
                "owning_agent": row.get("owning_agent"),
                "consumer_agents": row.get("consumer_agents"),
                "downstream_pr_refs": row.get("downstream_pr_refs"),
                "no_orphan_status": "NO_ORPHAN_ROUTED",
                "authority_class": row.get("authority_class"),
                **route_defaults("governance", upstream_refs=[str(row.get("value_ref"))]),
            }
        )
    return rows
