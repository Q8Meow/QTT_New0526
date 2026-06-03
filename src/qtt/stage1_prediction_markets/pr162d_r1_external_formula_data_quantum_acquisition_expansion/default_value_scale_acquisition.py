"""Default value and scale acquisition facade."""

from __future__ import annotations

from typing import Any


def default_value_scale_records(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **record,
            "default_value_scale_candidate_flag": True,
            "range_default_scale_complete_flag": True,
        }
        for record in parameters
    ]
