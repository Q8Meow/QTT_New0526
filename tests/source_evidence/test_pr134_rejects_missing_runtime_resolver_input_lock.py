from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_missing_runtime_resolver_input_lock():
    assert_malformed("malformed_missing_runtime_resolver_input_lock.v1.fixture.json", "MISSING_RUNTIME_RESOLVER_INPUT_LOCK")
