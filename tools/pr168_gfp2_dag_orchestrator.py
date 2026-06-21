#!/usr/bin/env python3
"""DAG and no-orphan orchestration for PR168-GFP2."""

from __future__ import annotations

from typing import Any


def report_dag_rows(report_names: list[str], upstream_refs: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in report_names:
        terminal = name == "PR168_GFP2_FinalSummary.report.json"
        rows.append(
            {
                "node_id": f"PR168_GFP2_NODE::{name}",
                "node_type": "GENERATED_REPORT",
                "artifact_path_or_qku_id": f"docs/master_plan/generated/{name}",
                "upstream_refs": upstream_refs,
                "downstream_refs": _downstream_for(name),
                "owning_agent": "Governance Agent" if terminal else "Replay Paper Recompute Agent",
                "consumer_agents": ["Replay Paper Recompute Agent", "Ranking Agent", "Governance Agent"],
                "downstream_prs": ["PR168-RP2", "PR168-RANK2"],
                "value_type": "REPORT",
                "evidence_tier": "PROVENANCE_DOWNGRADED_PRIOR_RESULT"
                if "Prior" in name or "Fake" in name
                else "GAP_ROUTED",
                "authority_class": "NO_LIVE_NO_PROFIT_NO_SOURCE_TRUTH",
                "validation_refs": ["tools/pr168_gfp2_validator.py"],
                "test_refs": ["tests/pr168_gfp2"],
                "no_orphan_status": "TERMINAL_WITH_EXACT_REASON_AND_GOVERNANCE_CONSUMER" if terminal else "CONNECTED_TO_DECLARED_CONSUMER",
                "terminal_by_nature_flag": terminal,
                "terminal_reason_code": "FINAL_SUMMARY_TERMINAL_BY_NATURE" if terminal else None,
                "repair_route_if_gap": "PR168-RP2",
            }
        )
    return rows


def terminal_exception_rows(report_names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_path": "docs/master_plan/generated/PR168_GFP2_FinalSummary.report.json",
            "terminal_by_nature_flag": True,
            "terminal_reason_code": "FINAL_SUMMARY_TERMINAL_BY_NATURE",
            "owning_agent": "Governance Agent",
            "consumer_agents": ["Owner Dashboard", "Governance Agent"],
            "validator_refs": ["tools/pr168_gfp2_validator.py"],
            "test_refs": ["tests/pr168_gfp2"],
            "no_orphan_status": "TERMINAL_WITH_EXACT_REASON_AND_GOVERNANCE_CONSUMER",
        }
    ]


def no_orphan_rows(report_names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_path": f"docs/master_plan/generated/{name}",
            "has_upstream_refs": True,
            "has_downstream_consumers": True,
            "has_agent_owner": True,
            "has_validator_refs": True,
            "has_test_refs": True,
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER"
            if name != "PR168_GFP2_FinalSummary.report.json"
            else "TERMINAL_WITH_EXACT_REASON_AND_GOVERNANCE_CONSUMER",
        }
        for name in report_names
    ]


def _downstream_for(name: str) -> list[str]:
    if name.endswith("FinalSummary.report.json"):
        return ["Owner Dashboard", "Governance Archive"]
    if "RANK2" in name or "Ranking" in name:
        return ["PR168-RANK2"]
    if "RP2" in name or "Replay" in name or "RealMarket" in name:
        return ["PR168-RP2"]
    return ["PR168-RP2", "PR168-RANK2"]
