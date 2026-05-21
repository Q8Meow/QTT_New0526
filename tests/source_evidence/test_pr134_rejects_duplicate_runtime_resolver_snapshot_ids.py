from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_duplicate_runtime_resolver_snapshot_ids():
    assert_malformed("malformed_duplicate_runtime_resolver_snapshot_id.v1.fixture.json", "DUPLICATE_RUNTIME_RESOLVER_SNAPSHOT_ID")
