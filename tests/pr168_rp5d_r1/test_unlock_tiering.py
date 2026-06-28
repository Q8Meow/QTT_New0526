from ._helpers import read_json


def test_tier_c_used_after_tier_a_b_exhaustion() -> None:
    run = read_json("run_receipt.report.json")
    assert run["tier_a_rows_seen"] == 0
    assert run["tier_b_rows_seen"] == 0
    assert run["tier_c_rows_seen"] > 0
