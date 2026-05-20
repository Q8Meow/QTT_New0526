import json
from pathlib import Path


SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/private_state_receipts")
SCHEMA_FILES = {
    "private_state_read_request.schema.json": "private_state_read_request_id",
    "private_state_read_receipt.schema.json": "private_state_read_receipt_id",
    "account_wallet_balance_receipt.schema.json": "account_wallet_balance_receipt_id",
    "private_state_redaction_attestation.schema.json": "redaction_attestation_id",
    "private_state_no_secret_capture_attestation.schema.json": "no_secret_capture_attestation_id",
    "private_state_read_rejection_receipt.schema.json": "private_state_read_rejection_receipt_id",
    "private_state_to_runtime_cash_linkage_receipt.schema.json": (
        "private_state_to_runtime_cash_linkage_receipt_id"
    ),
    "private_state_downstream_handoff.schema.json": "private_state_downstream_handoff_id",
}


def test_pr130_private_state_read_receipt_schema_surface_exists():
    for filename, required_id in SCHEMA_FILES.items():
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))

        assert schema["additionalProperties"] is True
        assert required_id in schema["required"]
        assert schema["properties"]["fixture_authority_class"]["const"] == (
            "TEST_FIXTURE_NOT_EXTERNAL_FACT"
        )
