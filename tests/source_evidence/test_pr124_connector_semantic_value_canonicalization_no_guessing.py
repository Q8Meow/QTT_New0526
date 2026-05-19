from __future__ import annotations

from src.qtt.source_evidence.connector_semantic_consumer.canonicalize import (
    canonicalize_semantic_payload,
)

from tests.source_evidence.pr124_connector_semantic_binding_support import consumed


def test_pr124_canonicalization_converts_representation_without_changing_meaning():
    record = consumed()["success_records"][0]

    assert record["bound_value_original"] == (
        "{\"fixture_value\": \"TEST_FIXTURE_NOT_EXTERNAL_FACT_VALUE\"}"
    )
    assert record["bound_value_canonical"] == (
        "{\"fixture_value\":\"TEST_FIXTURE_NOT_EXTERNAL_FACT_VALUE\"}"
    )
    assert record["bound_value_original"] != record["bound_value_canonical"]


def test_pr124_canonicalization_rejects_missing_value_unit_scale_or_scope():
    result = canonicalize_semantic_payload(
        None,
        value_type="OBJECT",
        unit_or_scale="TEST_FIXTURE_OBJECT_SCALE",
        scope={
            "scope_id": "PR124_SCOPE",
            "venue_id": "KALSHI",
            "target_field_path": "stage1.kalshi.order_entry.fixture_field",
            "wildcard_scope_allowed": False,
            "cross_venue_scope_allowed": False,
        },
    )
    assert not result.ok
    assert "extracted_fact is required" in " ".join(result.failures)

    result = canonicalize_semantic_payload(
        {"fixture_value": "TEST_FIXTURE_NOT_EXTERNAL_FACT_VALUE"},
        value_type="OBJECT",
        unit_or_scale="",
        scope={},
    )
    assert not result.ok
    joined = " ".join(result.failures)
    assert "bound_value_unit_or_scale is required" in joined
    assert "bound_value_scope is required" in joined
