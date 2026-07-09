from __future__ import annotations

from tools import build_pr169_agent_orch1 as builder
from tools import validate_pr169_agent_orch1 as validator

from .conftest import ARTIFACT_DIR, REPO_ROOT, json_report, jsonl


def test_registry_and_manifest_are_canonical():
    validator.validate(REPO_ROOT, ARTIFACT_DIR)
    registry = jsonl("registry.jsonl")
    manifest = json_report("manifest.json")
    assert registry
    assert manifest["canonical_registry_ref"] == builder.REGISTRY_REF
    assert manifest["baseline_consumed"]["PR269_SVC1_commit"] == "1b2d4da936fd79adfdecc5f503d2fa96ee6798a9"
    assert manifest["phase0_decisions"]["exact_pr"] == "PR169-AGENT-ORCH1"
    assert manifest["phase0_decisions"]["one_registry_builder_validator_resolver"] is True
    assert manifest["phase0_decisions"]["generated_rows_derive_from_registry"] is True
    assert manifest["phase0_decisions"]["paper_shadow_live_order_execution_created"] is False


def test_all_projection_rows_derive_from_registry():
    registry = jsonl("registry.jsonl")
    registry_by_id = {row["row_id"]: row for row in registry}
    assert len(registry_by_id) == len(registry)
    for file_name in builder.JSONL_ARTIFACTS:
        assert "future_" not in file_name.lower()
        assert "_hint" not in file_name.lower()
        assert len(file_name) <= 56
        rows = jsonl(file_name)
        assert rows, file_name
        if file_name == "registry.jsonl":
            continue
        for row in rows:
            source = registry_by_id[row["source_registry_row_id"]]
            assert row["generated_from"] == builder.REGISTRY_REF
            assert row["object_type"] == source["object_type"]
            assert row["object_id"] == source["object_id"]
            assert row["task_ref"] == source["task_ref"]
            assert row["projection_file"] == file_name


def test_required_state_fields_present_on_every_registry_row():
    for row in jsonl("registry.jsonl"):
        assert row["manual_edit_allowed"] is False
        assert row["provider_state"]
        assert row["provider_stage"]
        assert row["freshness_state"]
        assert row["lifecycle_state"]
        assert row["activation_state"]
        assert row["timing_state"]
        assert row["downstream_owner"]
        assert row["authority_state"]
        assert row["queue_state"]
        assert row["task_state"]
        assert row["retry_state"]
        assert row["projection_consumers"]
        assert row["orphan_status"] in {"NOT_ORPHAN", "SCOPED_GAP_ROUTED"}
