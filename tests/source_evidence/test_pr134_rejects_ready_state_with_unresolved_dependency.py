from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_ready_state_with_unresolved_dependency():
    assert_malformed("malformed_ready_with_unresolved_dependency.v1.fixture.json", "READY_WITH_UNRESOLVED_DEPENDENCY")
