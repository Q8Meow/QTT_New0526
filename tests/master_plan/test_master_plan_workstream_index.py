import json
from pathlib import Path

import pytest

from tools import build_master_plan_workstream_index as builder


MASTER_PLAN = Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

EXPECTED_WORKSTREAM_IDS = {
    "source_evidence_acceptance_registry",
    "connector_capability_registry",
    "runtime_orchestration_skeleton",
    "replay_paper_execution_graph",
    "venue_abstraction_layer",
    "order_intent_execution_router_scaffolding",
    "atomicrows_parameter_bundle_validation_later",
}


@pytest.fixture(scope="module")
def index() -> dict:
    return builder.build_master_plan_workstream_index(MASTER_PLAN)


@pytest.fixture(scope="module")
def records(index: dict) -> dict[str, dict]:
    return {
        record["workstream_id"]: record
        for record in index["workstreams"]
    }


def test_workstream_index_builds_from_current_master_plan(index):
    assert index["index_name"] == "ImplementationWorkstreamIndex"
    assert index["deterministic_output"] is True
    assert index["authority"]["authority_class"] == (
        "NON_AUTHORITATIVE_DERIVED_IMPLEMENTATION_INDEX"
    )
    assert index["workstream_count"] == len(index["workstreams"])


def test_workstream_index_output_is_deterministic():
    first = builder.build_master_plan_workstream_index(MASTER_PLAN)
    second = builder.build_master_plan_workstream_index(MASTER_PLAN)

    assert first == second
    assert json.dumps(first, indent=2, sort_keys=True) == json.dumps(
        second,
        indent=2,
        sort_keys=True,
    )


def test_workstream_index_contains_all_required_ids_and_fields(index, records):
    assert set(records) == EXPECTED_WORKSTREAM_IDS
    assert index["required_workstream_fields"] == list(
        builder.REQUIRED_WORKSTREAM_FIELDS
    )

    for record in records.values():
        assert set(builder.REQUIRED_WORKSTREAM_FIELDS) <= set(record)
        assert record["master_plan_anchor_terms"]


def test_atomicrows_parameter_bundle_workstream_is_later_not_immediate(records):
    atomicrows = records["atomicrows_parameter_bundle_validation_later"]

    assert "later" in atomicrows["status"]
    assert "immediate" not in atomicrows["status"]
    assert atomicrows["implementation_phase_order"] > max(
        record["implementation_phase_order"]
        for workstream_id, record in records.items()
        if workstream_id != "atomicrows_parameter_bundle_validation_later"
    )


def test_workstream_order_preserves_source_connector_runtime_replay_venue_order(records):
    order = {
        workstream_id: record["implementation_phase_order"]
        for workstream_id, record in records.items()
    }

    assert (
        order["source_evidence_acceptance_registry"]
        < order["connector_capability_registry"]
        < order["runtime_orchestration_skeleton"]
        < order["replay_paper_execution_graph"]
        < order["venue_abstraction_layer"]
        < order["order_intent_execution_router_scaffolding"]
    )


def test_workstreams_create_no_runtime_order_or_profit_authority(records):
    for record in records.values():
        assert record["creates_runtime_trading_authority"] is False
        assert record["creates_order_execution_authority"] is False
        assert record["creates_profit_claim"] is False


def test_missing_anchor_terms_fail_closed(tmp_path):
    omitted_anchor = builder.WORKSTREAM_DEFINITIONS[0].master_plan_anchor_terms[0]
    synthetic_master_plan = "\n".join(
        term
        for definition in builder.WORKSTREAM_DEFINITIONS
        for term in definition.master_plan_anchor_terms
        if term != omitted_anchor
    )
    path = tmp_path / "QTT_MasterPlan_Current.md"
    path.write_text(synthetic_master_plan, encoding="utf-8")

    with pytest.raises(builder.AnchorValidationError) as exc_info:
        builder.build_master_plan_workstream_index(path)

    message = str(exc_info.value)
    assert "master plan workstream index anchor validation failed" in message
    assert "source_evidence_acceptance_registry" in message
    assert omitted_anchor in message


def test_json_output_is_parseable_and_structure_is_stable(tmp_path, index):
    output = tmp_path / "ImplementationWorkstreamIndex.json"

    builder.write_index(index, output)
    parsed = json.loads(output.read_text(encoding="utf-8"))

    assert isinstance(parsed, dict)
    assert isinstance(parsed["authority"], dict)
    assert isinstance(parsed["workstreams"], list)
    assert all(isinstance(record, dict) for record in parsed["workstreams"])
    assert parsed["workstream_count"] == len(parsed["workstreams"])
    assert parsed["required_workstream_fields"] == list(
        builder.REQUIRED_WORKSTREAM_FIELDS
    )
