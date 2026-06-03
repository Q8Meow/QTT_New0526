"""Formula compute engine route helpers."""

from __future__ import annotations

from .route_resolver import filter_routes_for_agent


def formula_compute_engine_routes(routes):
    return filter_routes_for_agent(routes, "QKU_FORMULA_COMPUTE_ENGINE")
