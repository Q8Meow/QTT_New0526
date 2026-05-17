from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_atomicrows_lifecycle_cumulative_readiness_gate as gate


REPO_ROOT = Path(".")
SCHEMA = Path(
    "schemas/atomicrows/atomicrows_lifecycle_cumulative_readiness_gate.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_lifecycle_cumulative_readiness_gate_blocked.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsLifecycleCumulativeReadinessGate.report.json"
)
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _upstream_reports() -> dict[str, dict]:
    reports, failures = gate._load_upstream_reports(REPO_ROOT, gate.UPSTREAM_REPORT_PATHS)
    assert failures == []
    return {key: value for key, value in reports.items() if value is not None}


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_declares_cumulative_report_fields_and_canonical_upstreams():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    report_schema = schema["$defs"]["cumulative_readiness_report"]

    assert schema["additionalProperties"] is False
    assert report_schema["required"] == list(gate._empty_report())
    assert report_schema["properties"]["report_type"]["const"] == gate.REPORT_TYPE
    assert fixture["upstream_report_paths"] == [
        gate._normalize_path(path) for path in gate.UPSTREAM_REPORT_PATHS
    ]


def test_fixture_report_is_deterministic_and_has_expected_counts():
    first = gate.build_report(
        repo_root=REPO_ROOT,
        upstream_reports=_upstream_reports(),
    )
    second = gate.build_report(
        repo_root=REPO_ROOT,
        upstream_reports=_upstream_reports(),
    )

    assert first == second
    assert gate.serialize_report(first) == gate.serialize_report(second)
    assert first == json.loads(REPORT.read_text(encoding="utf-8"))
    assert first["upstream_report_count"] == 4
    assert first["upstream_reports_present_count"] == 4
    assert first["upstream_reports_missing_count"] == 0
    assert first["upstream_reports_deterministic_count"] == 4
    assert first["upstream_reports_final_ready_false_count"] == 4
    assert first["upstream_reports_authority_boundary_all_false_count"] == 4
    assert first["total_invalid_claim_count"] == 0
    assert first["optimizer_authority_allowed_total"] == 0
    assert first["runtime_authority_allowed_total"] == 0
    assert first["live_authority_allowed_total"] == 0
    assert first["quantum_backend_authority_allowed_total"] == 0
    assert first["bundle_file_present"] is True
    assert first["bundle_sha_present"] is False
    assert first["cumulative_ready"] is False
    assert first["final_ready"] is False
    assert first["authority_boundary_all_false"] is True


def test_dev_mode_passes_but_final_mode_remains_incomplete():
    dev = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )
    final = gate.validate(
        mode="final",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert dev.failures == ()
    assert final.ok is False
    _assert_failure_contains(final.failures, "final mode incomplete")


def test_false_authority_counts_fail_closed():
    reports = copy.deepcopy(_upstream_reports())
    consumer_report = reports[
        gate._normalize_path(gate.consumer_gate.DEFAULT_REPORT)
    ]
    consumer_report["optimizer_access_allowed_count"] = 1

    report = gate.build_report(repo_root=REPO_ROOT, upstream_reports=reports)
    failures = gate._report_safety_failures(report)

    assert report["optimizer_authority_allowed_total"] == 1
    _assert_failure_contains(failures, "optimizer_authority_allowed_total")


def test_false_final_ready_claim_fails_closed_until_cumulative_coverage_complete():
    reports = copy.deepcopy(_upstream_reports())
    consumer_report = reports[
        gate._normalize_path(gate.consumer_gate.DEFAULT_REPORT)
    ]
    consumer_report["final_ready"] = True

    report = gate.build_report(repo_root=REPO_ROOT, upstream_reports=reports)
    failures = gate._report_safety_failures(report)

    assert report["upstream_reports_final_ready_false_count"] == 3
    assert report["cumulative_ready"] is False
    _assert_failure_contains(failures, "final_ready claims must remain false")


def test_missing_upstream_report_is_a_dev_failure_not_incomplete_success():
    reports: dict[str, dict | None] = copy.deepcopy(_upstream_reports())
    reports[gate._normalize_path(gate.mutation_guard.DEFAULT_REPORT)] = None

    report = gate.build_report(repo_root=REPO_ROOT, upstream_reports=reports)
    failures = gate._report_safety_failures(report)

    assert report["upstream_reports_missing_count"] == 1
    _assert_failure_contains(failures, "upstream reports must be present")


def test_cumulative_gate_does_not_create_atomicrows_bundle_or_hash():
    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()

    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert result.failures == ()
    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
