"""Replay/paper result analyzer input prep route helpers."""

from __future__ import annotations

from .route_resolver import filter_routes_for_agent


def replay_paper_result_analyzer_input_prep_routes(routes):
    return filter_routes_for_agent(routes, "REPLAY_PAPER_RESULT_ANALYZER_INPUT_PREP")
