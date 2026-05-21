from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_global_candidate_universe_freeze_claim():
    assert_malformed("malformed_global_candidate_universe_freeze_claim.v1.fixture.json", "GLOBAL_CANDIDATE_UNIVERSE_FREEZE_CLAIM")
    assert_malformed("malformed_future_candidate_addition_blocked.v1.fixture.json", "FUTURE_CANDIDATE_ADDITION_BLOCKED")
