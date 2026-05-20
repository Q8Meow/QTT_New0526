from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    validate_redacted_payload_minimized,
)


def test_pr130_rejects_raw_secret_values_or_token_like_payloads():
    failures = validate_redacted_payload_minimized(
        {
            "api_key": "sk_live_1234567890abcdef",
            "bearer_header": "Bearer abcdefghijklmnopqrstuvwxyz",
        }
    )

    assert failures
    assert any("secret-like" in failure for failure in failures)
