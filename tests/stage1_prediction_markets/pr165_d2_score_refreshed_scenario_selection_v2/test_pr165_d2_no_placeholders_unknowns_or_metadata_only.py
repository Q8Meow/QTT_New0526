from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2.enums import (
    FORBIDDEN_STATUS_VALUES,
)


def _flatten(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _flatten(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten(item)


def test_no_forbidden_status_tokens_in_generated_rows(pr165_d2_records):
    forbidden = set(FORBIDDEN_STATUS_VALUES)
    for rows in pr165_d2_records.values():
        for row in rows:
            assert not (set(_flatten(row)) & forbidden)
