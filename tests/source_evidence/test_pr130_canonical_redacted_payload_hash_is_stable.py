from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    canonical_redacted_payload_digest,
)


def test_pr130_canonical_redacted_payload_hash_is_stable():
    left = {
        "venue_id": "KALSHI",
        "field_name": "verified_available_cash",
        "redaction_marker": "REDACTED_FIXTURE_VALUE",
    }
    right = {
        "redaction_marker": "REDACTED_FIXTURE_VALUE",
        "field_name": "verified_available_cash",
        "venue_id": "KALSHI",
    }

    assert canonical_redacted_payload_digest(left) == canonical_redacted_payload_digest(right)
