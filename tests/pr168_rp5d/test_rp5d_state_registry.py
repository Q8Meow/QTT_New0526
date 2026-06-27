from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import (
    COMPUTABILITY_STATES,
    EXECUTABILITY_STATES,
)

from ._helpers import rows


def test_computability_and_executability_state_registries_are_complete() -> None:
    comp_states = {str(row["state_name"]) for row in rows("rp5d_comp_state_registry.jsonl")}
    exec_states = {str(row["executability_state"]) for row in rows("rp5d_exec_state_registry.jsonl")}

    assert comp_states == set(COMPUTABILITY_STATES)
    assert exec_states == set(EXECUTABILITY_STATES)
    assert not {"UNKNOWN", "TBD", "PLACEHOLDER"} & comp_states
    assert "UNKNOWN" not in exec_states
