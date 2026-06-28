from ._helpers import assert_rows_have_contract


def test_owner_enablement_and_live_shadow_are_future_only() -> None:
    enable = assert_rows_have_contract("owner_enable.jsonl")
    live_shadow = assert_rows_have_contract("live_shadow_route.jsonl")

    assert {row["platform"] for row in enable} >= {"KALSHI", "POLYMARKET", "FORECASTEX_IBKR"}
    assert all(row["rp5f_live_reachability_created_flag"] is False for row in enable)
    assert all(row["owner_off_no_live_write_flag"] is True for row in enable)
    assert all(row["rp5f_authority_flag"] is False for row in live_shadow)
    assert all(row["pre_submit_revalidation_required_flag"] is True for row in live_shadow)
    assert {row["future_consumer"] for row in live_shadow} >= {
        "LIVE_DRYRUN",
        "LIVE_PILOT",
        "TRIGGERED_SHADOW_COMPARISON",
        "LAUNCH_GATE",
    }

