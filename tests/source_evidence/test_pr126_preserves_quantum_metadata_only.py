from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    artifacts,
    load_fixture,
)


def test_pr126_preserves_quantum_metadata_only():
    accepted_fixture = load_fixture("accepted_source_evidence_records.v1.fixture.json")
    quantum_records = [
        record
        for record in accepted_fixture["accepted_source_evidence_records"]
        if record.get("quantum_forward_metadata_only") is True
    ]

    assert len(quantum_records) == 1
    assert quantum_records[0]["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"

    report = artifacts()["main_report"]
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["optimizer_execution_count"] == 0
    assert report["quantum_advantage_claim_created"] is False
