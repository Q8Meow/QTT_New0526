from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_preserves_quantum_metadata_only():
    main = support.main_report()

    assert main["quantum_backend_execution_count"] == 0
    assert main["quantum_simulator_execution_count"] == 0
    assert main["optimizer_execution_count"] == 0
    assert main["quantum_advantage_claim_created"] is False
    assert main["profit_evidence_created"] is False
