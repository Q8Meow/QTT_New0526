"""Feature builder route helpers."""

from __future__ import annotations

from .route_resolver import filter_routes_for_agent


def feature_builder_routes(routes):
    return filter_routes_for_agent(routes, "FEATURE_BUILDER")
