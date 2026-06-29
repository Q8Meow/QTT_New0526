from ._helpers import assert_rows_have_contract


def test_trade_plan_seeds_are_snapshot_conditioned_inputs_only() -> None:
    rows = assert_rows_have_contract("trade_seed.jsonl")

    assert all(row["snapshot_id"] for row in rows)
    assert all(row["asof_timestamp_utc"] for row in rows)
    assert all(row["formula_stack_preview_refs"] for row in rows)
    assert all(row["qku_refs"] for row in rows)
    assert all(row["formula_refs"] for row in rows)
    assert all(row["freshness_policy_ref"] for row in rows)
    assert all(row["ttl_policy_ref"] for row in rows)
    assert all(row["stale_invalidation_ref"] for row in rows)
    assert all(row["pre_submit_revalidation_ref"] for row in rows)
    assert all(row["future_rp5g_required_flag"] is True for row in rows)
    assert all(row["rp5f_final_trade_plan_flag"] is False for row in rows)

