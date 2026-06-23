from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_hurdle_gates_block_no_trade_dominated_top_seeds() -> None:
    assert_rank3_valid()
    assert all(row["hurdle_gate_pass_flag"] is False for row in rows("hurdle_gate"))
