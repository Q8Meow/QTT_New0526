"""Missing-value audit helpers for PR161A."""

from __future__ import annotations

from typing import Mapping

from . import constants as c


def still_missing_after_all_lanes(record: Mapping[str, object]) -> bool:
    return (
        record.get("value_materialization_state")
        == c.ValueMaterializationState.VALUE_STILL_MISSING_AFTER_ALL_CANDIDATE_LANES_EXHAUSTED.value
    )

