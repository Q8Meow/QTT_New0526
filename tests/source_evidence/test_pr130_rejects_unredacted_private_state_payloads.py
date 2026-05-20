from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    validate_redacted_payload_minimized,
)


def test_pr130_rejects_unredacted_private_state_payloads():
    failures = validate_redacted_payload_minimized(
        {"raw_balance": "UNREDACTED_PRIVATE_STATE_VALUE"}
    )

    assert failures
    assert any("unredacted private-state" in failure for failure in failures)
