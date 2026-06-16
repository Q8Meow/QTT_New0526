from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import final_summary, assert_reports_for_test


def test_pr165_d3_pr152_pr208_routing_contract():
    assert_reports_for_test(__file__)
    summary = final_summary()
    assert summary["pr152_currentization_status"].startswith("REQUIRED")
    assert "PR165_D3" in summary["pr208_routing_status"]
    assert summary["timeout_ms"] == 3600000
