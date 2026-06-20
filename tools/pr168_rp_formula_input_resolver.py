#!/usr/bin/env python3
"""Resolve repo-local numeric input candidates for PR168-RP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.pr168_rp_report_writer import GENERATED_DIR, read_records, read_report


PR165_D2_INPUT_REPORTS = {
    "probability": "PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json",
    "microstructure": "PR165_D2_MicrostructureFeatureLedger.report.json",
    "tca": "PR165_D2_TCADecompositionSelectionLedger.report.json",
    "ranking": "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json",
}

PR165_D2_AGENT_REPORTS = {
    "roster": "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "duty_crosswalk": "PR165_D2_AgentDutySourceCrosswalk.report.json",
}


def load_numeric_input_maps(repo_root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    maps: dict[str, dict[str, dict[str, Any]]] = {}
    for lane, filename in PR165_D2_INPUT_REPORTS.items():
        path = repo_root / GENERATED_DIR / filename
        if not path.exists():
            maps[lane] = {}
            continue
        rows = read_records(repo_root, filename)
        maps[lane] = {
            str(row.get("qku_id")): row
            for row in rows
            if row.get("qku_id") and str(row.get("qku_id")) != "NOT_APPLICABLE_FOR_THIS_ROW_TERMINAL_BY_NATURE"
        }
    return maps


def load_agent_source_status(repo_root: Path) -> dict[str, Any]:
    status: dict[str, Any] = {"exact_artifacts_found": [], "missing_artifacts": [], "agent_ids": []}
    for lane, filename in PR165_D2_AGENT_REPORTS.items():
        path = repo_root / GENERATED_DIR / filename
        if not path.exists():
            status["missing_artifacts"].append(filename)
            continue
        status["exact_artifacts_found"].append(filename)
        report = read_report(repo_root, filename)
        rows = list(report.get("records", []))
        status[f"{lane}_record_count"] = report.get("record_count", len(rows))
        status["agent_ids"].extend(str(row.get("agent_id")) for row in rows if row.get("agent_id"))
    status["agent_ids"] = sorted(set(status["agent_ids"]))
    status["agent_duty_source_resolved"] = not status["missing_artifacts"]
    return status


def qku_id_from_assignment(row: dict[str, Any]) -> str | None:
    key = str(row.get("canonical_row_key") or "")
    if key.startswith("QKU::"):
        return key.split("QKU::", 1)[1]
    pointer = str(row.get("source_row_pointer") or row.get("row_pointer") or "")
    if ":QKU-" in pointer:
        return "QKU-" + pointer.split(":QKU-", 1)[1]
    return None


def resolve_row_input(row: dict[str, Any], input_maps: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    qku_id = qku_id_from_assignment(row)
    missing_lanes: list[str] = []
    resolved: dict[str, Any] = {"qku_id": qku_id}
    for lane in ("probability", "microstructure", "tca", "ranking"):
        lane_row = input_maps.get(lane, {}).get(str(qku_id))
        if lane_row is None:
            missing_lanes.append(lane)
        else:
            resolved[lane] = lane_row
    resolved["missing_lanes"] = missing_lanes
    resolved["complete"] = not missing_lanes and qku_id is not None
    return resolved


def missing_variables_for_input_gap(row: dict[str, Any], resolved: dict[str, Any]) -> list[str]:
    base = [
        "market_price",
        "predicted_probability",
        "market_implied_probability",
        "bid",
        "ask",
        "quantity",
        "fee_rate",
        "spread_cost",
        "slippage_cost",
        "fill_probability",
        "latency_ms",
        "capacity_limit",
        "overfit_fdr_penalty",
    ]
    lane_to_fields = {
        "probability": ["predicted_probability", "market_implied_probability", "market_price"],
        "microstructure": ["bid", "ask", "quantity", "fill_probability", "latency_ms", "capacity_limit"],
        "tca": ["fee_rate", "spread_cost", "slippage_cost"],
        "ranking": ["overfit_fdr_penalty", "portfolio_marginal_utility"],
    }
    missing: list[str] = []
    for lane in resolved.get("missing_lanes", []):
        missing.extend(lane_to_fields.get(str(lane), []))
    return sorted(set(missing or base))
