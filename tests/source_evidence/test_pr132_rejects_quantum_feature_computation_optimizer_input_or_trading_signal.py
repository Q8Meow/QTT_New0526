from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_rejects_quantum_feature_computation_optimizer_input_or_trading_signal():
    value = support.cloned_artifacts()
    event = value["adapter_report"]["canonical_market_data_ingest_events"][0]
    event["quantum_feature_computation_created"] = True
    event["quantum_optimizer_input_created"] = True
    event["quantum_trading_signal_created"] = True

    failures = support.validation_failures(value)

    assert any("quantum_feature_computation_created" in failure for failure in failures)
    assert any("quantum_optimizer_input_created" in failure for failure in failures)
    assert any("quantum_trading_signal_created" in failure for failure in failures)
