#!/usr/bin/env python3
"""Latency budget helpers for PR168-RP."""

from __future__ import annotations

from typing import Any


def latency_budget_row(candidate: dict[str, Any]) -> dict[str, Any]:
    expected = int(candidate["expected_latency"])
    budget = int(candidate["latency_budget_ms"])
    return {
        "latency_budget_ref": candidate["latency_budget_ref"],
        "candidate_id": candidate["candidate_id"],
        "expected_latency_ms": expected,
        "latency_budget_ms": budget,
        "latency_budget_pass_fail": expected <= budget,
        "latency_repair_route": "PR168_RP_HotPathPrecomputeCandidateSeed.report.json" if expected > budget else "PR168_RP_LatencyBudgetResults.report.json",
        "producer": "PR168_RP_LATENCY_BUDGET",
        "consumer": "PR168_RANK",
        "upstream_source": candidate["candidate_id"],
        "downstream_route": "PR168_RP_LatencyBudgetResults.report.json",
        "owning_agent": "Latency Agent",
        "no_orphan_status": "CONNECTED_TO_LATENCY_CONSUMER",
    }
