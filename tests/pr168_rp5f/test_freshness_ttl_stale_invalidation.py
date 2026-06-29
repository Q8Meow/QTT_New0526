from ._helpers import assert_rows_have_contract


def test_freshness_ttl_and_stale_rules_force_recomputation() -> None:
    fresh = assert_rows_have_contract("fresh_policy.jsonl")
    ttl = assert_rows_have_contract("ttl_policy.jsonl")
    stale = assert_rows_have_contract("stale_rules.jsonl")

    assert all(row["source_change_event_trigger_revalidation_required_flag"] for row in fresh)
    assert all(row["unknown_state_blocks_new_or_increased_exposure_flag"] for row in fresh)
    assert all(row["snapshot_ttl_ms"] == 2500 for row in ttl)
    assert all(row["must_recompute_after_ttl_flag"] for row in ttl)
    assert all(row["must_recompute_before_submit"] for row in stale)
    assert all(row["stale_if_kill_switch_or_owner_gate_changes"] for row in stale)

