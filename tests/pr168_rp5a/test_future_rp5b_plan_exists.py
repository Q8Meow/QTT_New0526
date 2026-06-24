from tests.pr168_rp5a._helpers import delete_rows, load_rows


def test_future_rp5b_plan_exists() -> None:
    rows = load_rows("future_rp5b_plan_rows")
    assert rows
    assert len(rows) == len(delete_rows())
