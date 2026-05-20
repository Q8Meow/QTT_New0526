import json
from pathlib import Path


SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/credential_readiness")
SCHEMA_FILES = (
    "credential_alias_registry.schema.json",
    "credential_alias_readiness_receipt.schema.json",
    "secret_no_capture_attestation.schema.json",
    "credential_scope_binding.schema.json",
    "credential_readiness_rejection_receipt.schema.json",
    "credential_readiness_downstream_handoff.schema.json",
)


def test_pr131_credential_alias_readiness_schema():
    for filename in SCHEMA_FILES:
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))

        assert schema["additionalProperties"] is False
        assert "schema_version" in schema["required"]
        assert "record_type" in schema["required"]
        assert "created_by" in schema["required"]
        assert "authority_class" in schema["required"]
