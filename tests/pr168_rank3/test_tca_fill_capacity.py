from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_tca_fill_latency_capacity_rows_exist() -> None:
    assert_rank3_valid()
    assert len(rows("tca_rank")) == 35
    assert len(rows("fill_latency_capacity_rank")) == 35
