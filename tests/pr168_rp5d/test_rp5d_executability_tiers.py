from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import EXECUTABILITY_STATES

from ._helpers import rows


def test_executability_tiers_have_exact_current_states_and_adapter_routes() -> None:
    tiers = rows("rp5d_exec_tiers.jsonl")

    assert tiers
    for row in tiers:
        assert row["executability_state"] in EXECUTABILITY_STATES
        assert row["executability_state"] != "UNKNOWN"
        if row["schedulable_after_adapter_flag"]:
            assert row["blocking_adapter_family_refs"]
            assert row["adapter_queue_refs"]
