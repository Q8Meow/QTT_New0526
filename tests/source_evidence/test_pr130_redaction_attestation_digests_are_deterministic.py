from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    canonical_redacted_payload_digest,
)
from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_redaction_attestation_digests_are_deterministic():
    payloads = support.redacted_payloads_by_receipt()
    attestations = {
        record["private_state_read_receipt_id"]: record
        for record in support.redaction_attestations()
    }

    for receipt_id, payload in payloads.items():
        digest = canonical_redacted_payload_digest(payload)
        assert digest == canonical_redacted_payload_digest(payload)
        assert attestations[receipt_id]["canonicalized_redacted_payload_digest"] == digest
