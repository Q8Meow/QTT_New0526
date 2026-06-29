from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.models import all_artifact_filenames
from ._helpers import assert_rows_have_contract


def test_artifact_io_covers_every_file() -> None:
    rows = assert_rows_have_contract("artifact_io.jsonl")
    assert {row["file_path"].split("/")[-1] for row in rows} == set(all_artifact_filenames())

