from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import ROOT


def test_pr159_human_readable_source_completion_summary_exists():
    path = ROOT / c.HUMAN_SUMMARY_PATH
    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "Processed targets: 879" in text

