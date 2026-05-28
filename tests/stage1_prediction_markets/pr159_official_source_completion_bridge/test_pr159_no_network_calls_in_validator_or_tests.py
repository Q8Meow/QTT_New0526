from pathlib import Path

from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import ROOT


def test_pr159_no_network_calls_in_validator_or_tests():
    paths = [ROOT / "tools" / "validate_pr159_official_source_completion_bridge.py"]
    paths.extend((ROOT / "src/qtt/stage1_prediction_markets/pr159_official_source_completion_bridge").glob("*.py"))
    forbidden = ("requests.", "httpx.", "urllib.request", "socket.", "web.run")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), path

