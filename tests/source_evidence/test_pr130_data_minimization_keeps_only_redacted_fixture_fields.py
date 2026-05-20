from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    validate_redacted_payload_minimized,
)
from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_data_minimization_keeps_only_redacted_fixture_fields():
    for payload in support.redacted_payloads_by_receipt().values():
        assert validate_redacted_payload_minimized(payload) == []

    assert all("redacted_payload" not in receipt for receipt in support.read_receipts())
    assert all("raw_payload" not in receipt for receipt in support.read_receipts())
