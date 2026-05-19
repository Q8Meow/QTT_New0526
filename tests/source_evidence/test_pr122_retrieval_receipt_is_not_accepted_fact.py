from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from src.qtt.source_evidence.retrieval import controller


RECEIPT_SCHEMA = Path(
    "schemas/source_evidence/retrieval/candidate_source_retrieval_receipt.schema.json"
)
SOURCE_PACKET_SCHEMA = Path("schemas/source_evidence/source_evidence.schema.json")


def _base_receipt() -> dict:
    digest = hashlib.sha256(b"synthetic fixture content").hexdigest()
    return {
        "accepted_fact_authority_flag": False,
        "canonicalization_policy_id": "PR122_CANONICAL_JSON_SHA256_V1",
        "canonicalized_content_digest": digest,
        "connector_semantic_unlock_allowed_flag": False,
        "fetch_or_capture_metadata": {"mode": "synthetic"},
        "fetch_or_capture_mode": "FIXTURE_ONLY",
        "fixture_id": "SYNTHETIC_PR122_FIXTURE",
        "next_required_gate": "ACCEPTED_SOURCE_EVIDENCE_PACKET_REQUIRED_FOR_TARGET_FIELD",
        "order_authority_allowed_flag": False,
        "private_doc_access_rights_state": "NOT_PRIVATE_DOCUMENT",
        "profit_evidence_allowed_flag": False,
        "quantum_backend_execution_allowed_flag": False,
        "quote_span_locator": {
            "quote_span_locator_id": "SYNTHETIC_QUOTE_SPAN",
            "quote_digest_sha256": digest,
        },
        "redaction_applied_flag": False,
        "retrieval_receipt_id": "SYNTHETIC_CANDIDATE_RECEIPT",
        "retrieval_target_id": "SYNTHETIC_TARGET",
        "runtime_live_use_allowed_flag": False,
        "secret_like_value_detected_flag": False,
        "source_authority_state": "CANDIDATE_RETRIEVAL_ONLY_NOT_ACCEPTED_FACT",
        "source_class": "OFFICIAL_API_DOCS",
        "source_locator": {"locator_type": "FIXTURE_ONLY"},
    }


def test_candidate_receipt_schema_forces_no_authority_flags():
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    props = schema["properties"]

    for field in controller.FORCED_FALSE_AUTHORITY_FLAGS:
        assert props[field]["const"] is False
        assert field in schema["required"]
    assert props["source_authority_state"]["const"] == (
        "CANDIDATE_RETRIEVAL_ONLY_NOT_ACCEPTED_FACT"
    )
    assert props["next_required_gate"]["const"] == (
        "ACCEPTED_SOURCE_EVIDENCE_PACKET_REQUIRED_FOR_TARGET_FIELD"
    )


def test_candidate_receipt_validator_blocks_accepted_fact_or_connector_unlock():
    receipt = _base_receipt()
    assert controller.validate_candidate_receipt_record(receipt) == []

    mutated = copy.deepcopy(receipt)
    mutated["accepted_fact_authority_flag"] = True
    mutated["connector_semantic_unlock_allowed_flag"] = True
    failures = controller.validate_candidate_receipt_record(mutated)
    assert any("accepted_fact_authority_flag" in failure for failure in failures)
    assert any("connector_semantic_unlock_allowed_flag" in failure for failure in failures)


def test_candidate_packet_schema_does_not_unlock_connector_semantics():
    schema = json.loads(SOURCE_PACKET_SCHEMA.read_text(encoding="utf-8"))
    candidate = schema["$defs"]["candidate_source_packet"]

    assert candidate["properties"]["candidate_packet_may_unlock_connector_semantics"][
        "const"
    ] is False


def test_quote_span_or_machine_field_locator_required_for_candidate_capture():
    receipt = _base_receipt()
    receipt.pop("quote_span_locator")

    failures = controller.validate_candidate_receipt_record(receipt)

    assert any("quote_span_locator or machine_field_locator" in failure for failure in failures)
