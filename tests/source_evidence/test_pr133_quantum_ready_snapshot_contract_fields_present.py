from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_quantum_ready_snapshot_contract_fields_present():
    for record in support.all_records():
        for field in policy.QUANTUM_FORWARD_SNAPSHOT_METADATA_FIELDS:
            assert field in record
        assert record["quantum_ready_snapshot_contract"] is True
