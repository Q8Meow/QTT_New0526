from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_stale_or_conflict_dependency_ready_claim():
    assert_malformed("malformed_stale_dependency_ready_claim.v1.fixture.json", "STALE_DEPENDENCY_READY_CLAIM")
    assert_malformed("malformed_conflict_dependency_ready_claim.v1.fixture.json", "CONFLICT_DEPENDENCY_READY_CLAIM")
