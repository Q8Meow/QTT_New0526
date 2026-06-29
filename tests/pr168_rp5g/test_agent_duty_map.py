from ._helpers import assert_rows_have_contract


def test_agent_duty_consumes_pr165d2() -> None:
    rows = assert_rows_have_contract("agent_duty_map.jsonl")
    assert any(row["pr165_d2_consumed_flag"] is True for row in rows)

