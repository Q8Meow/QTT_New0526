from .pr134_runtime_resolver_snapshot_support import artifacts
from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor import policy


def test_pr134_quantum_ready_runtime_resolver_contract_fields_present():
    for snapshot in artifacts()["runtime_resolver_snapshots"]:
        for field_name in policy.QUANTUM_FORWARD_RUNTIME_RESOLVER_METADATA_FIELDS:
            assert field_name in snapshot
        assert snapshot["quantum_ready_runtime_resolver_snapshot_contract"] is True
