from __future__ import annotations

from tests.source_evidence.pr125_revalidation_scheduler_support import (
    inputs,
    materiality_by_event,
    report_and_failures,
)


def test_pr125_quantum_provider_docs_are_metadata_only_no_backend_or_optimizer_execution():
    accepted_records = inputs()["accepted_source_evidence_records"][
        "accepted_source_evidence_records"
    ]
    quantum_record = next(
        record
        for record in accepted_records
        if record["accepted_source_evidence_packet_id"]
        == "PR125_PACKET_QUANTUM_PROVIDER_DOC_METADATA"
    )
    event = materiality_by_event("EVENT_UNKNOWN_MATERIALITY_QUANTUM_DOC")
    report, failures = report_and_failures()

    assert failures == []
    assert quantum_record["quantum_provider_docs_metadata_only"] is True
    assert event["materiality_class"] == "CONNECTOR_BLOCKING"
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["optimizer_execution_count"] == 0
    assert report["quantum_advantage_claim_created"] is False
