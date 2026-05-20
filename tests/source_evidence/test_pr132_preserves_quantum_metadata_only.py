from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_preserves_quantum_metadata_only():
    evidence = support.main_report()["PR132_QUANTUM_METADATA_ONLY_EVIDENCE"]

    for field, expected in policy.QUANTUM_ZERO_AUTHORITY_FLAGS.items():
        assert evidence[field] is expected
    assert evidence["quantum_backend_simulator_optimizer_execution_count"] == 0
    assert evidence["quantum_feature_computation_count"] == 0
    assert evidence["quantum_optimizer_input_count"] == 0
    assert evidence["quantum_trading_signal_count"] == 0
    assert evidence["quantum_advantage_claim_count"] == 0
    assert evidence["quantum_metadata_strings_only"] is True
