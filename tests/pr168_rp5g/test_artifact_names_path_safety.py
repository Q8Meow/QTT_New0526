from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.models import all_artifact_filenames
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.path_safety import path_safety_failures
from ._helpers import assert_valid, read_json


def test_artifact_registry_and_paths_are_safe() -> None:
    assert_valid()
    assert not path_safety_failures(all_artifact_filenames())
    registry = read_json("art_reg.json")
    assert registry["artifact_name_registry_count"] == len(all_artifact_filenames())

