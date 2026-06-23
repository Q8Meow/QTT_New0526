from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_agent_dag_no_orphan_owners_consumers() -> None:
    assert_recovery1_valid()
    assert all(row["owning_agent"] and row["consumer_agents"] for row in rows("work_item"))
