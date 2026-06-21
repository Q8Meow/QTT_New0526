#!/usr/bin/env python3
"""DAG-style upstream/downstream orchestration for DATA1A."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import REQUIRED_REPORT_IDS, generated_ref, report_path, route_defaults


def build_dag_nodes(created_at_utc: str, shard_manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    data1_node = {
        "node_id": "dag_node_data1_inputs",
        "node_type": "upstream_DATA1_artifacts",
        "artifact_path_or_data_ref": "docs/master_plan/generated/PR168_DATA1_*.report.json",
        "upstream_refs": ["PR168-DATA1", "PR233"],
        "downstream_refs": ["dag_node_data1a_reports"],
        "owning_agent": "market_data_acquisition_agent",
        "consumer_agents": ["governance_validation_agent", "qku_formula_materialization_agent"],
        "downstream_prs": ["PR168-DATA1A"],
        "value_type": "market_data_snapshot_and_handoff",
        "evidence_tier": "COMMITTED_DATA1_ROW_SCAN",
        "validation_refs": ["tools/pr168_data1a_validator.py"],
        "test_refs": ["tests/pr168_data1a"],
        "repair_route_if_gap": None,
        "created_at_utc": created_at_utc,
        **route_defaults("market_data"),
    }
    nodes.append(data1_node)
    nodes.append(
        {
            "node_id": "dag_node_data1a_reports",
            "node_type": "DATA1A_audit_reports",
            "artifact_path_or_data_ref": "docs/master_plan/generated/PR168_DATA1A_*.report.json",
            "upstream_refs": ["dag_node_data1_inputs", "PR165-D2"],
            "downstream_refs": [
                "PR168-GFP2R formula/provenance recompute",
                "PR168-RP2 replay/paper recompute",
                "PR168-RANK2 evidence-backed ranking",
                "PR165-B condition-scoped negative memory",
                "PR167 open-trade opportunity simulator",
                "PR162E-Q quantum automapper",
                "PR166-Q/QB/QC quantum comparator/retest",
                "future dashboard formula/trade control",
            ],
            "owning_agent": "governance_validation_agent",
            "consumer_agents": ["dashboard_operator_agent", "source_evidence_agent", "ranking_scoring_agent"],
            "downstream_prs": ["PR168-GFP2R", "PR168-RP2", "PR168-RANK2", "PR165-B", "PR167", "PR162E-Q", "PR166-Q", "PR166-QB", "PR166-QC"],
            "value_type": "audit_readiness_contract",
            "evidence_tier": "DATA1A_COMPUTED_AUDIT",
            "validation_refs": ["tools/pr168_data1a_validator.py"],
            "test_refs": ["tests/pr168_data1a"],
            "repair_route_if_gap": None,
            "created_at_utc": created_at_utc,
            **route_defaults("governance"),
        }
    )
    for manifest in shard_manifests:
        nodes.append(
            {
                "node_id": f"dag_node_{manifest['manifest_id']}",
                "node_type": "DATA1A_row_shard",
                "artifact_path_or_data_ref": manifest["shard_path"],
                "upstream_refs": ["dag_node_data1_inputs"],
                "downstream_refs": ["dag_node_data1a_reports"],
                "owning_agent": manifest.get("owning_agent"),
                "consumer_agents": manifest.get("consumer_agents"),
                "downstream_prs": manifest.get("downstream_pr_refs"),
                "value_type": manifest.get("data_family"),
                "evidence_tier": "ROW_LEVEL_JSONL_SHARD",
                "validation_refs": manifest.get("validator_refs"),
                "test_refs": manifest.get("test_refs"),
                "repair_route_if_gap": None,
                "created_at_utc": created_at_utc,
                **route_defaults("governance", row_shard_refs=[manifest["shard_path"]]),
            }
        )
    for report_id in REQUIRED_REPORT_IDS:
        nodes.append(
            {
                "node_id": f"dag_node_{report_id}",
                "node_type": "DATA1A_report",
                "artifact_path_or_data_ref": generated_ref(report_path(report_id)),
                "upstream_refs": ["dag_node_data1a_reports"],
                "downstream_refs": ["PR168-GFP2R", "PR168-RP2", "PR168-RANK2"],
                "owning_agent": "governance_validation_agent",
                "consumer_agents": ["dashboard_operator_agent", "source_evidence_agent"],
                "downstream_prs": ["PR168-GFP2R", "PR168-RP2", "PR168-RANK2"],
                "value_type": "report",
                "evidence_tier": "DATA1A_REPORT",
                "validation_refs": ["tools/pr168_data1a_validator.py"],
                "test_refs": ["tests/pr168_data1a"],
                "repair_route_if_gap": None,
                "created_at_utc": created_at_utc,
                **route_defaults("governance"),
            }
        )
    return nodes
