from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_quantum_ready_market_data_contract_fields_present():
    evidence = support.main_report()["PR132_QUANTUM_READY_MARKET_DATA_CONTRACT_EVIDENCE"]

    assert evidence["quantum_ready_market_data_contract_count"] >= 4
    for field in policy.QUANTUM_FORWARD_METADATA_FIELDS:
        assert field in evidence
    for record in support.all_contract_records():
        for field in policy.QUANTUM_FORWARD_METADATA_FIELDS:
            assert field in record
