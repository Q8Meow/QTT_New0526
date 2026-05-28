from pathlib import Path

from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import constants as c


def test_pr159r_human_readable_summary_exists():
    root = Path(__file__).resolve().parents[3]
    assert (root / c.HUMAN_SUMMARY_PATH).exists()

