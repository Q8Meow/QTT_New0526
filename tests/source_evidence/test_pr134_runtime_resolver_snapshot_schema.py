from .pr134_runtime_resolver_snapshot_support import schema
from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor import policy, validator


def test_pr134_runtime_resolver_snapshot_schemas_exist_and_are_closed():
    for file_name, record_type in validator.SCHEMA_FILES.items():
        doc = schema(file_name)
        assert doc["properties"]["record_type"]["const"] == record_type
        assert doc["properties"]["schema_version"]["const"] == policy.SCHEMA_VERSION
        assert doc["properties"]["authority_class"]["const"] == policy.PACKAGE_AUTHORITY_CLASS
        assert doc["additionalProperties"] is False
        assert "record_type" in doc["required"]
        assert "schema_version" in doc["required"]
