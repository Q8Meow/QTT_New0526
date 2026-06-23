from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_agent_memory_has_regime_conditions() -> None:
    assert_rank3_valid()
    assert all(row["regime_condition_id"] for row in rows("agent_memory"))
