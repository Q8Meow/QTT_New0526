from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_atomicrows_bundle_sha_row_materialization_or_4183_completion():
    for field, value in (("atomicrows_bundle_created", True), ("atomicrows_sha_created", True), ("atomicrows_row_records_created_count", 1), ("atomicrows_4183_completion_claim_created", True)):
        built = support.cloned_artifacts()
        built["atomicrows_compatibility_records"][0][field] = value
        assert any(field in failure for failure in support.validation_failures(built))
