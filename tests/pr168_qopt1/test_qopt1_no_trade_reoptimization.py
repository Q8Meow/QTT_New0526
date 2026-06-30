from ._helpers import rows


def test_no_trade_next_action_ladder_exists() -> None:
    for filename in (
        "var_tune_frontier.jsonl",
        "stack_chall_frontier.jsonl",
        "venue_side_rotate.jsonl",
        "adapter_source_refresh.jsonl",
        "next_target_rotate.jsonl",
        "retest_queue.jsonl",
        "notrade_not_terminal.jsonl",
    ):
        row = rows(filename)[0]
        assert row["terminal_dead_end_flag"] is False
        assert row["paper_order_intent_created_flag"] is False
