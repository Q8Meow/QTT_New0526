from __future__ import annotations


def test_condition_memory_is_condition_scoped(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_ConditionMemoryApplicationLedger.report.json"]
    assert len(rows) == 3985
    assert all(row["condition_scoped_application_only_flag"] is True for row in rows[:100])
    assert all(row["global_permanent_ban_created"] is False for row in rows[:100])
