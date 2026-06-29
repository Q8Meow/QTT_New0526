from ._helpers import assert_rows_have_contract


def test_pre_submit_revalidation_required_for_all_future_consumers() -> None:
    rows = assert_rows_have_contract("pre_submit_reval.jsonl")

    required_flags = (
        "required_before_paper_intent_flag",
        "required_before_live_dryrun_intent_flag",
        "required_before_shadow_input_flag",
        "required_before_limited_live_canary_flag",
        "required_before_live_order_flag",
        "latest_snapshot_required_flag",
        "risk_gate_required_flag",
        "source_freshness_required_flag",
        "market_data_truth_required_flag",
        "owner_or_risk_gate_required_for_live_flag",
    )
    for row in rows:
        assert all(row[flag] is True for flag in required_flags)

