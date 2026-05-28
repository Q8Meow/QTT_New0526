from pathlib import Path


def test_pr159r_no_network_calls_in_validator_or_tests():
    root = Path(__file__).resolve().parents[3]
    paths = [
        root / "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
        root / "tools/validate_pr159r_source_locator_value_capture.py",
    ]
    forbidden = ("requests.", "urllib.request", "http.client", "websocket", "socket.")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden)

