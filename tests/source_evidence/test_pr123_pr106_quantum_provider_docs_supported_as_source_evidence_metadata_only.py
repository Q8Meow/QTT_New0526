from ._pr123_acceptance_helpers import execute, set_text_digests, valid_candidate


def test_quantum_provider_docs_supported_as_source_evidence_metadata_only():
    candidate = valid_candidate()
    candidate["candidate_source_evidence_packet_id"] = (
        "PR123_FIXTURE_CANDIDATE_QUANTUM_PROVIDER_DOC_METADATA_ONLY"
    )
    candidate["venue_id"] = "PREDICTION_MARKETS_GENERAL"
    candidate["platform_scope"] = "PREDICTION_MARKETS_GENERAL"
    candidate["retrieval_target_id"] = "PR123_FIXTURE_RETRIEVAL_TARGET_QUANTUM_PROVIDER_DOC"
    candidate["source_target_id"] = "PR123_FIXTURE_SOURCE_TARGET_QUANTUM_PROVIDER_DOC"
    candidate["source_authority_class"] = "OFFICIAL_PROVIDER_DOCS"
    candidate["source_locator"] = (
        "TEST_FIXTURE_NOT_EXTERNAL_FACT:QUANTUM_PROVIDER_DOC_METADATA_PLACEHOLDER"
    )
    candidate["target_section_id"] = "source_evidence.quantum.provider_metadata"
    candidate["target_field_path"] = (
        "stage1.prediction_markets_general.quantum_provider.fixture_metadata"
    )
    candidate["target_field_paths_authorized"] = [candidate["target_field_path"]]
    candidate["applicability_scope"] = {
        "scope_id": "PR123_FIXTURE_SCOPE_QUANTUM_PROVIDER_DOC",
        "venue_id": "PREDICTION_MARKETS_GENERAL",
        "platform_scope": "PREDICTION_MARKETS_GENERAL",
        "target_field_paths": [candidate["target_field_path"]],
        "wildcard_scope_allowed": False,
        "cross_venue_scope_allowed": False,
    }
    set_text_digests(
        candidate,
        "TEST_FIXTURE_NOT_EXTERNAL_FACT quantum provider capability metadata source evidence.",
        "TEST_FIXTURE_NOT_EXTERNAL_FACT quantum provider capability metadata canonical text.",
    )

    result = execute(candidate)

    assert result.decision_receipt["decision"] == "ACCEPTED"
    assert result.decision_receipt["quantum_backend_execution_count"] == 0
    assert result.accepted_packet is not None
    assert result.accepted_ledger_record is not None
    assert result.accepted_packet["source_authority_class"] == "OFFICIAL_PROVIDER_DOCS"
    assert result.accepted_packet["production_external_fact_authority"] is False
    assert result.accepted_ledger_record["quantum_backend_execution_allowed_flag"] is False
