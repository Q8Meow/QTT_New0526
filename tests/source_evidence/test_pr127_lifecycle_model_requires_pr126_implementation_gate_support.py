from tests.source_evidence.pr127_execution_lifecycle_support import (
    load_fixture,
    model_records,
)


def test_pr127_lifecycle_model_requires_pr126_implementation_gate_support():
    implementation_fixture = load_fixture("connector_implementation_gate_records.v1.fixture.json")
    implementation_ids = {
        record["connector_implementation_gate_record_id"]
        for record in implementation_fixture["connector_implementation_gate_records"]
    }

    for model in model_records():
        assert model["upstream_connector_implementation_gate_receipt_id"] in implementation_ids
        assert len(model["upstream_connector_semantic_binding_record_ids"]) == 6
        assert len(model["upstream_accepted_source_evidence_packet_ids"]) == 6
