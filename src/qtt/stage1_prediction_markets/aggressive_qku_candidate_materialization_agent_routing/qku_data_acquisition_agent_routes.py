"""QKU data acquisition route helpers."""

from __future__ import annotations

from .route_resolver import filter_routes_for_agent


def qku_data_acquisition_routes(routes):
    return filter_routes_for_agent(routes, "QKU_DATA_ACQUISITION_AGENT")
