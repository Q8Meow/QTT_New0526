from .pr134_runtime_resolver_snapshot_support import assert_malformed, failure_codes, mutable_artifacts


def test_pr134_rejects_historical_dataset_digest_feature_signal_scoring():
    assert_malformed("malformed_historical_dataset_digest_created.v1.fixture.json", "HISTORICAL_DATASET_DIGEST_CREATED")
    assert_malformed("malformed_feature_vector_created.v1.fixture.json", "FEATURE_VECTOR_CREATED")
    assert_malformed("malformed_trading_signal_created.v1.fixture.json", "TRADING_SIGNAL_CREATED")
    payload = mutable_artifacts()
    payload["runtime_resolver_snapshots"][0]["scoring_ranking_arbitration_output_created"] = True
    assert "SCORING_RANKING_ARBITRATION_OUTPUT_CREATED" in failure_codes(payload)
