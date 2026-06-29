from ._helpers import assert_rows_have_contract


def test_targets_are_dynamic_snapshot_conditioned_candidates() -> None:
    rows = assert_rows_have_contract("targets.jsonl")

    assert all(row["candidate_status"] == "DYNAMIC_TRADE_TARGET_CANDIDATE" for row in rows)
    assert all(row["snapshot_id"] for row in rows)
    assert all(row["asof_timestamp_utc"] for row in rows)
    assert all(row["eligible_stack_preview_refs"] for row in rows)
    assert all(row["eligible_executable_now_refs"] for row in rows)
    assert all(row["fixed_trade_instruction_flag"] is False for row in rows)

