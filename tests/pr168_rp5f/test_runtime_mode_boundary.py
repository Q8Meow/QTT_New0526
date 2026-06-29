from ._helpers import assert_rows_have_contract


def test_runtime_mode_boundary_preserves_stage1_laws() -> None:
    rows = assert_rows_have_contract("mode_bound.jsonl")
    by_mode = {row["runtime_mode"]: row for row in rows}

    assert by_mode["REPLAY_MODE"]["stage1_replay_and_paper_results_must_remain_separate_flag"] is True
    assert by_mode["SHADOW_LIVE_CONCURRENT_COMPARISON"]["stage1_shadow_mode_execution_enabled_flag"] is False
    assert by_mode["LIVE_DRYRUN_SUBMIT_DISABLED"]["submit_disabled_required_flag"] is True
    assert by_mode["LIVE_DRYRUN_SUBMIT_DISABLED"]["order_authority_flag"] is False
