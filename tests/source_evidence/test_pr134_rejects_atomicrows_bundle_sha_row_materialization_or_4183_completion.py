from .pr134_runtime_resolver_snapshot_support import assert_malformed, failure_codes, mutable_artifacts


def test_pr134_rejects_atomicrows_bundle_sha_row_materialization_or_4183_completion():
    assert_malformed("malformed_atomicrows_bundle_created.v1.fixture.json", "ATOMICROWS_BUNDLE_CREATED")
    assert_malformed("malformed_atomicrows_row_records_created.v1.fixture.json", "ATOMICROWS_ROW_RECORDS_CREATED")
    assert_malformed("malformed_atomicrows_4183_completion_claim.v1.fixture.json", "ATOMICROWS_4183_COMPLETION_CLAIM_CREATED")
    payload = mutable_artifacts()
    payload["atomicrows_pre_bridge_compatibility"][0]["atomicrows_sha_created"] = True
    assert "ATOMICROWS_SHA_CREATED" in failure_codes(payload)
