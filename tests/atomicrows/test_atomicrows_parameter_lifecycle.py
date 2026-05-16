from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import build_atomicrows_parameter_lifecycle_report as builder
from tools import validate_atomicrows_parameter_lifecycle as validator


REPO_ROOT = Path(".")
REGISTRY = Path("docs/master_plan/atomic_rows/AtomicRowsParameterLifecycleRegistry.yaml")
SCHEMA = Path("schemas/atomicrows/atomicrows_parameter_lifecycle_registry.schema.json")
REPORT = Path("docs/master_plan/generated/AtomicRowsParameterLifecycleReport.json")
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _registry() -> dict:
    return builder.load_registry(REGISTRY)


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_lifecycle_schema_declares_required_statuses_and_entry_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    statuses = schema["$defs"]["lifecycle_status"]["enum"]
    entry_required = set(schema["$defs"]["lifecycle_entry"]["required"])

    assert statuses == list(builder.LIFECYCLE_STATUSES)
    assert set(builder.ENTRY_FIELDS) <= entry_required
    assert schema["additionalProperties"] is False


def test_registry_shape_and_entries_validate():
    registry = _registry()

    assert validator.validate_registry_shape(registry) == []
    assert validator.validate_registry_entries(registry["entries"]) == []
    assert registry["registry_name"] == builder.REGISTRY_NAME
    assert registry["lifecycle_statuses"] == list(builder.LIFECYCLE_STATUSES)
    assert all(
        entry["optimizer_eligibility"]["eligible"] is False
        for entry in registry["entries"]
    )
    assert all(
        entry["runtime_eligibility"]["eligible"] is False
        for entry in registry["entries"]
    )
    assert all(entry["live_eligibility"]["eligible"] is False for entry in registry["entries"])


def test_report_is_deterministic_and_has_expected_safety_counts():
    first = builder.build_report(repo_root=REPO_ROOT, registry_path=REGISTRY)
    second = builder.build_report(repo_root=REPO_ROOT, registry_path=REGISTRY)

    assert first == second
    assert builder.serialize_report(first) == builder.serialize_report(second)
    assert first == json.loads(REPORT.read_text(encoding="utf-8"))
    assert first["deterministic_output"] is True
    assert first["generated_at_utc"] == builder.DETERMINISTIC_GENERATED_AT
    assert first["registry_entry_count"] == 8
    assert first["parameter_family_count"] == 8
    assert first["classical_entry_count"] == 6
    assert first["quantum_entry_count"] == 2
    assert first["optimizer_eligible_count"] == 0
    assert first["runtime_eligible_count"] == 0
    assert first["live_eligible_count"] == 0
    assert first["invalid_eligibility_claim_count"] == 0
    assert first["final_ready"] is False
    assert first["authority_boundary_all_false"] is True


def test_dev_mode_passes_but_final_mode_remains_incomplete():
    dev = validator.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        report_path=REPORT,
    )
    final = validator.validate(
        mode="final",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        report_path=REPORT,
    )

    assert dev.failures == ()
    assert final.ok is False
    _assert_failure_contains(final.failures, "final mode incomplete")


def test_optimizer_eligibility_fails_without_range_source_evidence_and_promotion_gate():
    entry = copy.deepcopy(_registry()["entries"][0])
    entry["lifecycle_status"] = "OPTIMIZER_ELIGIBLE"
    entry["optimizer_eligibility"]["eligible"] = True

    failures = builder.invalid_eligibility_claims([entry])

    _assert_failure_contains(failures, "range_validated")
    _assert_failure_contains(failures, "source_evidence_accepted")
    _assert_failure_contains(failures, "evidence_validated")
    _assert_failure_contains(failures, "promotion_gate_validated")


def test_runtime_and_live_eligibility_require_receipts_and_prior_gates():
    runtime_entry = copy.deepcopy(_registry()["entries"][0])
    runtime_entry["lifecycle_status"] = "RUNTIME_ELIGIBLE"
    runtime_entry["runtime_eligibility"]["eligible"] = True

    runtime_failures = builder.invalid_eligibility_claims([runtime_entry])

    _assert_failure_contains(runtime_failures, "optimizer gate")
    _assert_failure_contains(runtime_failures, "runtime receipt")

    live_entry = copy.deepcopy(runtime_entry)
    live_entry["lifecycle_status"] = "LIVE_ELIGIBLE"
    live_entry["live_eligibility"]["eligible"] = True

    live_failures = builder.invalid_eligibility_claims([live_entry])

    _assert_failure_contains(live_failures, "runtime receipt")
    _assert_failure_contains(live_failures, "live receipt")
    _assert_failure_contains(live_failures, "owner approval receipt")


def test_quarantined_and_retired_entries_require_reasons():
    quarantined = copy.deepcopy(_registry()["entries"][6])
    quarantined["quarantine_reason"] = None
    retired = copy.deepcopy(_registry()["entries"][7])
    retired["retirement_reason"] = None

    failures = validator.validate_registry_entries([quarantined, retired])

    _assert_failure_contains(failures, "quarantine_reason is required")
    _assert_failure_contains(failures, "retirement_reason is required")


def test_parameter_lifecycle_validation_does_not_create_atomicrows_bundle_or_hash():
    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()

    result = validator.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        report_path=REPORT,
    )

    assert result.failures == ()
    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
