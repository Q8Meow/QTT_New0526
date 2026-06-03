"""Formula/algorithm runtime route helpers."""

from __future__ import annotations

from .route_resolver import filter_routes_for_agent


def formula_algorithm_runtime_routes(routes):
    return filter_routes_for_agent(routes, "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_MODE")
