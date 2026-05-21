from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_venue_scope_mismatch():
    assert_malformed("malformed_scope_mismatch.v1.fixture.json", "VENUE_SCOPE_MISMATCH")
