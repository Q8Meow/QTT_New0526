from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder
from tools import validate_atomicrows_lifecycle_consumer_gate as gate


REPO_ROOT = Path(".")
REGISTRY = Path("docs/master_plan/atomic_rows/AtomicRowsParameterLifecycleRegistry.yaml")
LIFECYCLE_REPORT = Path("docs/master_plan/generated/AtomicRowsParameterLifecycleReport.json")
SCHEMA = Path("schemas/atomicrows/atomicrows_lifecycle_consumer_gate.schema.json")
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_lifecycle_consumer_gate_blocked.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/AtomicRowsLifecycleConsumerGate.report.json")
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _registry() -> dict:
    return lifecycle_builder.load_registry(REGISTRY)


def _lifecycle_report() -> dict:
    return json.loads(LIFECYCLE_REPORT.read_text(encoding="utf-8"))


def _entries_by_pattern() -> dict[str, dict]:
    return {entry["row_pattern_id"]: entry for entry in _registry()["entries"]}


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_declares_consumer_classes_statuses_and_report_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    report_schema = schema["$defs"]["lifecycle_gate_report"]

    assert schema["additionalProperties"] is False
    assert schema["$defs"]["consumer_class"]["enum"] == list(gate.CONSUMER_CLASSES)
    assert schema["$defs"]["lifecycle_status"]["enum"] == list(
        lifecycle_builder.LIFECYCLE_STATUSES
    )
    assert report_schema["required"] == list(gate._empty_report())
    assert report_schema["properties"]["report_type"]["const"] == gate.REPORT_TYPE


def test_fixture_report_is_deterministic_and_has_expected_counts():
    first, first_failures = gate.build_report(
        fixture=_fixture(),
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )
    second, second_failures = gate.build_report(
        fixture=_fixture(),
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )

    assert first_failures == []
    assert second_failures == []
    assert first == second
    assert gate.serialize_report(first) == gate.serialize_report(second)
    assert first == json.loads(REPORT.read_text(encoding="utf-8"))
    assert first["attempted_consumer_access_count"] == 23
    assert first["allowed_consumer_access_count"] == 9
    assert first["blocked_consumer_access_count"] == 14
    assert first["invalid_consumer_access_count"] == 0
    assert first["optimizer_access_allowed_count"] == 0
    assert first["runtime_access_allowed_count"] == 0
    assert first["live_access_allowed_count"] == 0
    assert first["quantum_backend_execution_allowed_count"] == 0
    assert first["final_ready"] is False
    assert first["authority_boundary_all_false"] is True


def test_dev_mode_passes_but_final_mode_remains_incomplete():
    dev = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )
    final = gate.validate(
        mode="final",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert dev.failures == ()
    assert final.ok is False
    _assert_failure_contains(final.failures, "final mode incomplete")


def test_gate_status_rules_allow_only_declared_non_active_surfaces():
    entries = _entries_by_pattern()

    assert gate.decide_consumer_access(
        entries["atomicrows_inventory_only_bundle_absent_pattern"],
        "INVENTORY_INDEX",
    ).allowed
    assert not gate.decide_consumer_access(
        entries["atomicrows_inventory_only_bundle_absent_pattern"],
        "OPTIMIZER_SEARCH",
    ).allowed
    assert gate.decide_consumer_access(
        entries["external_microstructure_feature_candidate_pattern"],
        "SOURCE_EVIDENCE_RETRIEVAL",
    ).allowed
    assert not gate.decide_consumer_access(
        entries["external_microstructure_feature_candidate_pattern"],
        "RANGE_VALIDATION",
    ).allowed
    assert gate.decide_consumer_access(
        entries["source_dependent_parameter_value_pattern"],
        "SOURCE_EVIDENCE_RETRIEVAL",
    ).allowed
    assert not gate.decide_consumer_access(
        entries["source_dependent_parameter_value_pattern"],
        "RISK_MODEL_INPUT",
    ).allowed
    assert gate.decide_consumer_access(
        entries["selector_field_static_range_pattern"],
        "RANGE_VALIDATION",
    ).allowed
    assert not gate.decide_consumer_access(
        entries["selector_field_static_range_pattern"],
        "RUNTIME_RESOLVER_INPUT",
    ).allowed
    assert gate.decide_consumer_access(
        entries["edge_parameter_stack_replay_candidate_pattern"],
        "REPLAY_CANDIDATE_SELECTION",
    ).allowed
    assert not gate.decide_consumer_access(
        entries["edge_parameter_stack_replay_candidate_pattern"],
        "OPTIMIZER_SEARCH",
    ).allowed
    assert gate.decide_consumer_access(
        entries["unproven_false_eligibility_claim_pattern"],
        "RESEARCH_TRIAGE",
    ).allowed
    assert not gate.decide_consumer_access(
        entries["negative_or_rejected_row_retirement_pattern"],
        "RESEARCH_TRIAGE",
    ).allowed


def test_unknown_consumer_and_unknown_lifecycle_status_fail_closed():
    fixture = _fixture()
    fixture["attempted_consumer_access"][0]["consumer_class"] = "UNKNOWN_CONSUMER"
    report, failures = gate.build_report(
        fixture=fixture,
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )

    assert report["invalid_consumer_access_count"] == 1
    _assert_failure_contains(failures, "unknown consumer class")

    entry = copy.deepcopy(_registry()["entries"][0])
    entry["lifecycle_status"] = "UNKNOWN_STATUS"
    decision = gate.decide_consumer_access(entry, "INVENTORY_INDEX")

    assert decision.allowed is False
    assert decision.reason == "unknown lifecycle status"


def test_false_allowed_claim_fails_closed_for_active_consumers():
    fixture = _fixture()
    fixture["attempted_consumer_access"][2]["declared_consumer_access_allowed"] = True
    report, failures = gate.build_report(
        fixture=fixture,
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )

    assert report["invalid_consumer_access_count"] == 1
    _assert_failure_contains(failures, "prohibited consumer access")


def test_optimizer_runtime_live_and_quantum_backend_need_explicit_prerequisites():
    base = copy.deepcopy(_registry()["entries"][0])

    optimizer = copy.deepcopy(base)
    optimizer["lifecycle_status"] = "OPTIMIZER_ELIGIBLE"
    assert not gate.decide_consumer_access(optimizer, "OPTIMIZER_SEARCH").allowed
    optimizer["optimizer_eligibility"] = {
        "eligible": True,
        "range_validated": True,
        "source_evidence_accepted": True,
        "evidence_validated": True,
        "promotion_gate_validated": True,
        "receipt_id": "synthetic_optimizer_receipt.json",
        "blocking_reason": "",
    }
    assert gate.decide_consumer_access(optimizer, "OPTIMIZER_DEFAULTS").allowed

    runtime = copy.deepcopy(optimizer)
    runtime["lifecycle_status"] = "RUNTIME_ELIGIBLE"
    runtime["runtime_eligibility"] = {
        "eligible": True,
        "runtime_receipt_id": None,
        "blocking_reason": "missing runtime receipt",
    }
    assert not gate.decide_consumer_access(runtime, "RUNTIME_RESOLVER_INPUT").allowed
    runtime["runtime_eligibility"]["runtime_receipt_id"] = "synthetic_runtime.json"
    assert gate.decide_consumer_access(runtime, "RUNTIME_RESOLVER_INPUT").allowed

    live = copy.deepcopy(runtime)
    live["lifecycle_status"] = "LIVE_ELIGIBLE"
    live["live_eligibility"] = {
        "eligible": True,
        "live_receipt_id": "synthetic_live.json",
        "owner_approval_receipt_id": None,
        "blocking_reason": "missing owner approval",
    }
    assert not gate.decide_consumer_access(live, "LIVE_EXECUTION").allowed
    live["live_eligibility"]["owner_approval_receipt_id"] = "synthetic_owner.json"
    assert gate.decide_consumer_access(live, "LIVE_ORDER_ROUTING").allowed

    quantum = copy.deepcopy(runtime)
    quantum["classical_or_quantum"] = "QUANTUM"
    quantum["source_authority_class"] = "GENERIC_QUANTUM_LABEL"
    quantum["evidence_required"] = ["generic quantum label"]
    assert not gate.decide_consumer_access(
        quantum,
        "QUANTUM_BACKEND_EXECUTION",
    ).allowed


def test_lifecycle_consumer_gate_does_not_create_atomicrows_bundle_or_hash():
    assert not CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()

    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert result.failures == ()
    assert not CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
