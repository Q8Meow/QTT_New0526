from pathlib import Path

from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import ROOT, atomic_records


def test_pr157_owner_response_absent_does_not_fabricate_values():
    assert not (ROOT / c.OWNER_RESPONSE_PATH).exists()
    blocked_owner = [
        record
        for record in atomic_records()
        if record["owner_input_required_flag"] is True
    ]
    assert blocked_owner
    assert all(record["value_materialization_status"] == "BLOCKED_WITH_TYPED_FILL_PLAN" for record in blocked_owner)
