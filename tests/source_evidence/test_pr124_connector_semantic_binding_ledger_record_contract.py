from __future__ import annotations

import json
from pathlib import Path

from tests.source_evidence.pr124_connector_semantic_binding_support import (
    STAGE1_SURFACES,
    consumed,
)


LEDGER_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_binding_ledger_record.schema.json"
)
MANIFEST_SCHEMA = Path(
    "schemas/source_evidence/pr124_connector_semantic_binding/"
    "stage1_source_to_connector_field_binding_manifest.schema.json"
)
TARGET_MATRIX_SCHEMA = Path(
    "schemas/source_evidence/pr124_connector_semantic_binding/"
    "stage1_connector_semantic_target_field_matrix.schema.json"
)


def test_pr124_ledger_and_manifest_schemas_encode_required_contracts():
    ledger_schema = json.loads(LEDGER_SCHEMA.read_text(encoding="utf-8"))
    manifest_schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    matrix_schema = json.loads(TARGET_MATRIX_SCHEMA.read_text(encoding="utf-8"))

    assert "production_connector_semantic_authority" in ledger_schema["required"]
    assert ledger_schema["properties"]["production_connector_semantic_authority"]["const"] is False
    assert {
        "binding_manifest_record_type",
        "accepted_source_evidence_packet_id",
        "source_locator_required_flag",
        "exact_quote_or_machine_field_locator_required_flag",
        "source_digest_required_flag",
        "extracted_fact_required_flag",
        "applicability_scope_required_flag",
        "conflict_check_required_flag",
        "revalidation_trigger_required_flag",
    }.issubset(set(manifest_schema["required"]))
    assert set(STAGE1_SURFACES).issubset(
        set(matrix_schema["$defs"]["surface_id"]["enum"])
    )


def test_pr124_success_record_has_required_non_production_fields():
    record = consumed()["success_records"][0]

    assert record["connector_semantic_binding_ledger_record_type"] == (
        "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_RECORD"
    )
    assert record["production_connector_semantic_authority"] is False
    assert record["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
    assert record["stale_binding_invalidates_downstream_snapshot_flag"] is True
    assert record["rollback_receipt_required_flag"] is True
    assert record["live_client_import_allowed_flag"] is False
    assert record["network_io_allowed_flag"] is False
    assert record["order_execution_allowed_flag"] is False
    assert record["live_reachability_allowed_flag"] is False
