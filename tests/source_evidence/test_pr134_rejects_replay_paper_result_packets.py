from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_replay_paper_result_packets():
    assert_malformed("malformed_replay_result_created.v1.fixture.json", "REPLAY_RESULT_CREATED")
    assert_malformed("malformed_paper_result_created.v1.fixture.json", "PAPER_RESULT_CREATED")
