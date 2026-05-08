import json
from pathlib import Path


SCHEMA_PATH = Path("schemas/source_evidence/source_evidence.schema.json")


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_source_evidence_schema_exposes_required_static_surfaces():
    schema = _schema()
    defs = schema["$defs"]

    required_surfaces = {
        "candidate_source_packet",
        "accepted_source_packet",
        "target_field_ledger_record",
        "conflict_metadata",
        "materiality_metadata",
        "revalidation_metadata",
        "no_claim_flags",
        "source_packet_marker_checks",
    }

    assert required_surfaces.issubset(defs)
    assert schema["properties"]["mode"]["const"] == "SOURCE_REQUIRED"
    assert schema["properties"]["execution"]["const"] == "DISABLED"
    assert (
        schema["properties"]["schema_authority_class"]["const"]
        == "STATIC_SCHEMA_CONTRACT_ONLY_NOT_EXTERNAL_FACT_AUTHORITY"
    )


def test_candidate_and_accepted_packet_fields_are_target_field_specific():
    defs = _schema()["$defs"]
    candidate_required = set(defs["candidate_source_packet"]["required"])
    accepted_required = set(defs["accepted_source_packet"]["required"])
    ledger_required = set(defs["target_field_ledger_record"]["required"])

    assert {
        "source_target_id",
        "venue_id",
        "target_semantic_family",
        "target_field_paths",
        "source_locator_status",
        "expected_capture_type",
        "conflict_metadata",
        "materiality_metadata",
        "revalidation_metadata",
        "no_claim_flags",
    }.issubset(candidate_required)

    assert {
        "candidate_packet_id",
        "acceptance_decision_packet_id",
        "retrieval_manifest_id",
        "raw_capture_digest_sha256",
        "canonical_text_digest_sha256",
        "quote_span_or_machine_field_locator",
        "extracted_fact_payload",
        "target_field_paths_authorized",
        "acceptance_state",
        "no_claim_flags",
    }.issubset(accepted_required)

    assert {
        "accepted_source_packet_id",
        "accepted_source_packet_digest_sha256",
        "target_field_path",
        "target_semantic_family",
        "applicability_scope_digest",
        "accepted_fact_payload_digest_sha256",
        "ledger_record_state",
        "connector_semantic_binding_allowed_flag",
        "blocked_reason_when_not_bindable",
    }.issubset(ledger_required)


def test_no_claim_flags_block_runtime_authority_and_examples_are_synthetic():
    schema = _schema()
    defs = schema["$defs"]
    no_claim_properties = defs["no_claim_flags"]["properties"]

    blocked_authority_fields = {
        "external_fact_authority",
        "source_retrieval_authority",
        "source_acceptance_execution_authority",
        "accepted_packet_creation_authority",
        "connector_binding_authority",
        "runtime_authority",
        "runtime_cash_fetch_authority",
        "private_state_fetch_authority",
        "order_execution_authority",
        "replay_paper_live_execution_authority",
        "network_io_authority",
        "sha_freeze_authority",
        "profit_claim_authority",
    }

    assert blocked_authority_fields == set(no_claim_properties)
    assert all(no_claim_properties[field]["const"] is False for field in blocked_authority_fields)
    assert (
        defs["candidate_source_packet"]["properties"][
            "candidate_packet_may_unlock_connector_semantics"
        ]["const"]
        is False
    )
    assert (
        defs["target_field_ledger_record"]["properties"][
            "connector_semantic_binding_allowed_flag"
        ]["const"]
        is False
    )
    for flag in [
        "no_connector_semantic_population_flag",
        "no_live_reachability_flag",
        "no_order_execution_flag",
        "no_runtime_cash_claim_flag",
        "no_blocker_reduction_or_profit_claim_flag",
    ]:
        assert defs["accepted_source_packet"]["properties"][flag]["const"] is True

    assert schema["examples"]
    assert all(
        example["example_authority_class"]
        == "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT"
        for example in schema["examples"]
    )
    assert all(
        value is False
        for example in schema["examples"]
        for value in example["no_claim_flags"].values()
    )


def test_target_field_paths_disallow_wildcards_and_unknown_venue_scope():
    defs = _schema()["$defs"]

    assert defs["target_field_path"]["not"]["pattern"] == "\\*"
    assert "*" not in defs["venue_id"]["enum"]
    assert "UNKNOWN" not in defs["venue_id"]["enum"]
