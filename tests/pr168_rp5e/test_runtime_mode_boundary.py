from ._helpers import by_key, read_jsonl


def test_runtime_mode_boundary_materializes_distinct_master_plan_states() -> None:
    rows = by_key(read_jsonl("mode_boundary.jsonl"), "runtime_state")

    paper = rows["PAPER_MODE"]
    assert paper["simulated_orders"] is True
    assert paper["simulated_fills"] is True
    assert paper["real_exchange_order_state"] is False
    assert paper["order_authority_allowed_in_rp5e_flag"] is False

    live_dry = rows["LIVE_DRYRUN_SUBMIT_DISABLED"]
    assert live_dry["submit_disabled"] is True
    assert live_dry["real_order_submission_allowed"] is False
    assert live_dry["future_pr_consumer"] == "PR170-LIVE-DRYRUN"

    shadow = rows["SHADOW_LIVE_CONCURRENT_COMPARISON"]
    assert shadow["role"] == "LIVE_CONCURRENT_EXECUTION_COMPARISON_LANE"
    assert shadow["requires_live_execution_surface_flag"] is True
    assert shadow["required_before_limited_live_canary"] is False
    assert shadow["pre_live_gate_role_allowed_flag"] is False
    assert shadow["post_live_validation_role_flag"] is True

    canary = rows["LIMITED_LIVE_CANARY"]
    assert canary["owner_approved_tiny_real_orders"] is True
    assert canary["enabled_in_rp5e_flag"] is False
    assert canary["requires_owner_approval_flag"] is True
