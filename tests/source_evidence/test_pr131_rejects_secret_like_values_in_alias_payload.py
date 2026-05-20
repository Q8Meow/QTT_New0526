from src.qtt.stage1_prediction_markets.credential_readiness.alias import (
    validate_alias_registry_records,
)
from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_rejects_secret_like_values_in_alias_payload():
    records = [dict(record) for record in support.alias_records()]
    records[0]["alias_placeholder_value"] = "UNREDACTED_SECRET_VALUE_RAW_API_KEY"

    failures = validate_alias_registry_records(records)

    assert any("secret-like payload" in failure for failure in failures)
