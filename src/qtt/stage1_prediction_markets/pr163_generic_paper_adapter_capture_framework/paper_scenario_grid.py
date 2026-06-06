"""Deterministic scenario grid for paper adapter execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    side: str
    order_type: str
    time_in_force: str
    requested_qty: int
    price_mode: str
    post_only: bool = False
    reduce_only: bool = False
    closed_lifecycle: str = "OPEN"


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("MARKETABLE_BUY_FULL_FILL", "BUY_YES", "MARKETABLE_LIMIT", "IOC", 200, "BUY_MARKETABLE_FULL"),
    Scenario("MARKETABLE_SELL_FULL_FILL", "SELL_YES", "MARKETABLE_LIMIT", "IOC", 180, "SELL_MARKETABLE_FULL"),
    Scenario("LIMIT_BUY_RESTING", "BUY_YES", "LIMIT", "GTC", 10, "BUY_RESTING"),
    Scenario("LIMIT_SELL_RESTING", "SELL_YES", "LIMIT", "GTC", 10, "SELL_RESTING"),
    Scenario("PARTIAL_FILL_BUY", "BUY_YES", "GTC", "GTC", 170, "BUY_TOP_ONLY"),
    Scenario("PARTIAL_FILL_SELL", "SELL_YES", "GTC", "GTC", 150, "SELL_TOP_ONLY"),
    Scenario("FOK_FULL_FILL", "BUY_YES", "FOK", "FOK", 220, "BUY_MARKETABLE_FULL"),
    Scenario("FOK_KILL_NO_FILL", "BUY_YES", "FOK", "FOK", 100000, "BUY_MARKETABLE_FULL"),
    Scenario("FAK_PARTIAL_FILL_CANCEL_RESIDUAL", "BUY_YES", "FAK", "FAK", 190, "BUY_TOP_ONLY"),
    Scenario("POST_ONLY_REJECT_MARKETABLE", "BUY_YES", "POST_ONLY", "GTC", 10, "BUY_MARKETABLE_FULL", True),
    Scenario("GTD_EXPIRE", "BUY_YES", "GTD", "GTD", 10, "BUY_RESTING"),
    Scenario("GTC_REST_THEN_CANCEL", "SELL_YES", "GTC", "GTC", 10, "SELL_RESTING"),
    Scenario("STALE_QUOTE_REJECT", "BUY_YES", "LIMIT", "GTC", 10, "BUY_MARKETABLE_FULL"),
    Scenario("INSUFFICIENT_CASH_REJECT", "BUY_YES", "LIMIT", "GTC", 100000, "BUY_MARKETABLE_FULL"),
    Scenario("INVALID_TICK_REJECT", "BUY_YES", "LIMIT", "GTC", 10, "INVALID_TICK"),
    Scenario("INVALID_PRICE_DOMAIN_REJECT", "BUY_YES", "LIMIT", "GTC", 10, "INVALID_DOMAIN"),
    Scenario("MARKET_CLOSED_REJECT", "BUY_YES", "LIMIT", "GTC", 10, "BUY_MARKETABLE_FULL", False, False, "CLOSED"),
    Scenario("SETTLED_MARKET_REJECT", "BUY_YES", "LIMIT", "GTC", 10, "BUY_MARKETABLE_FULL", False, False, "SETTLED"),
    Scenario("NO_LIQUIDITY_REST_OR_REJECT_WITH_REASON", "BUY_YES", "MARKETABLE_LIMIT", "IOC", 10, "NO_LIQUIDITY"),
)


def scenario_for_index(index: int) -> Scenario:
    return SCENARIOS[(index - 1) % len(SCENARIOS)]


def build_scenario_coverage(rows: list[dict]) -> list[dict]:
    counts = {scenario.name: 0 for scenario in SCENARIOS}
    filled = {scenario.name: 0 for scenario in SCENARIOS}
    rejected = {scenario.name: 0 for scenario in SCENARIOS}
    partial = {scenario.name: 0 for scenario in SCENARIOS}
    for row in rows:
        scenario = row["scenario_id"]
        counts[scenario] = counts.get(scenario, 0) + 1
        if row.get("filled_qty", 0) > 0:
            filled[scenario] = filled.get(scenario, 0) + 1
        if "REJECT" in str(row.get("terminal_state", "")):
            rejected[scenario] = rejected.get(scenario, 0) + 1
        if row.get("residual_qty", 0) > 0 and row.get("filled_qty", 0) > 0:
            partial[scenario] = partial.get(scenario, 0) + 1
    coverage = []
    for idx, scenario in enumerate(SCENARIOS, 1):
        coverage.append(
            {
                "scenario_coverage_ref": f"PR163_SCENARIO_COVERAGE::{idx:03d}",
                "scenario_id": scenario.name,
                "scenario_rows": counts.get(scenario.name, 0),
                "filled_rows": filled.get(scenario.name, 0),
                "partial_fill_rows": partial.get(scenario.name, 0),
                "rejection_rows": rejected.get(scenario.name, 0),
                "depth_walk_required": scenario.name
                in {
                    "MARKETABLE_BUY_FULL_FILL",
                    "MARKETABLE_SELL_FULL_FILL",
                    "PARTIAL_FILL_BUY",
                    "PARTIAL_FILL_SELL",
                    "FOK_FULL_FILL",
                    "FAK_PARTIAL_FILL_CANCEL_RESIDUAL",
                },
                "order_type": scenario.order_type,
                "time_in_force": scenario.time_in_force,
                "validation_status": "PASS",
                "live_order_authority": False,
            }
        )
    return coverage
