from pathlib import Path


def test_pr159r_no_scattered_hardcoded_blocker_no_authority_vocabulary():
    root = Path(__file__).resolve().parents[3]
    constants = (root / "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/constants.py").read_text(encoding="utf-8")
    report = (root / "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/report.py").read_text(encoding="utf-8")
    assert "NO_AUTHORITY_CONFIRMATION" in constants
    assert "NO_AUTHORITY_CONFIRMATION" in report

