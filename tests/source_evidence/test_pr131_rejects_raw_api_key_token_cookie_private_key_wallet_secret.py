from src.qtt.stage1_prediction_markets.credential_readiness.alias import secret_like_findings


def test_pr131_rejects_raw_api_key_token_cookie_private_key_wallet_secret():
    findings = secret_like_findings(
        {
            "api_key": "UNREDACTED_SECRET_VALUE_RAW_API_KEY",
            "bearer_header": "UNREDACTED_SECRET_VALUE_BEARER_TOKEN",
            "session_cookie": "UNREDACTED_SECRET_VALUE_SESSION_COOKIE",
            "private_key": "UNREDACTED_SECRET_VALUE_PRIVATE_KEY",
            "wallet_secret": "UNREDACTED_SECRET_VALUE_WALLET_SECRET",
        }
    )

    assert findings
    assert len(findings) >= 5
