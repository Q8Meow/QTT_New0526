from .pr161a_test_support import records, summary


def test_pr161a_replay_paper_queue_is_preparatory_only():
    queue = records("replay_queue")
    assert len(queue) == 4525
    assert summary()["replay_paper_queue_count"] == 4525
    assert all(record["profit_validation_tag"] == "PROFIT_NOT_TESTED" for record in queue[:100])
    assert all(record["live_use_allowed_flag"] is False for record in queue[:100])

