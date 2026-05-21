from .pr134_runtime_resolver_snapshot_support import artifacts, failure_codes, summary


def test_pr134_runtime_resolver_integrity_is_deterministic_and_canonical_ordered():
    payload = artifacts()
    assert not failure_codes(payload)
    sort_keys = [snapshot["canonical_sort_key"] for snapshot in payload["runtime_resolver_snapshots"]]
    assert sort_keys == sorted(sort_keys)
    assert all(value == 0 for key, value in summary(payload).items() if key.endswith("_count"))
