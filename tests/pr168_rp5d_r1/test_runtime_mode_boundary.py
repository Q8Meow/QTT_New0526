from ._helpers import read_jsonl


def test_runtime_boundaries_are_distinct_and_non_authority() -> None:
    rows = {row["runtime_mode"]: row for row in read_jsonl("mode_bound.jsonl")}
    assert {"REPLAY_MODE", "PAPER_MODE", "LIVE_DRY_RUN", "SHADOW_MODE", "LIMITED_LIVE_CANARY", "LIVE_MODE"} <= set(rows)
    assert rows["LIVE_DRY_RUN"]["submit_disabled_flag"] is True
    assert rows["SHADOW_MODE"]["post_live_validation_only_flag"] is True
    assert all(row["order_authority_flag"] is False for row in rows.values())
