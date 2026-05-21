from .pr134_runtime_resolver_snapshot_support import artifacts, summary


def test_pr134_atomicrows_compatibility_metadata_only():
    payload = artifacts()
    assert len(payload["atomicrows_pre_bridge_compatibility"]) == 4
    counts = summary(payload)
    assert counts["atomicrows_bundle_created_count"] == 0
    assert counts["atomicrows_sha_created_count"] == 0
    assert counts["atomicrows_row_records_created_count"] == 0
    assert counts["atomicrows_4183_completion_claim_created_count"] == 0
