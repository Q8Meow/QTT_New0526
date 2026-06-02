"""Compatibility facade for PR162C source discovery."""

from __future__ import annotations

from .source_lanes import source_discovery_records, source_portfolio_records


def discovery_records() -> list[dict[str, object]]:
    return source_discovery_records(source_portfolio_records())
