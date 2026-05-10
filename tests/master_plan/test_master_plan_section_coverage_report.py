from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import build_master_plan_section_coverage_report as builder
from tools import validate_master_plan_section_coverage as validator


REPO_ROOT = Path(".")
MASTER_PLAN = Path("docs/master_plan/QTT_MasterPlan_Current.md")
REGISTRY = Path("docs/master_plan/completion/QTTSectionCoverageRegistry.yaml")
SCHEMA = Path("schemas/master_plan/master_plan_section_coverage_report.schema.json")
REPORT = Path("docs/master_plan/generated/MasterPlanSectionCoverageReport.json")


def _report() -> dict:
    return builder.build_report(
        repo_root=REPO_ROOT,
        master_plan=MASTER_PLAN,
        registry_path=REGISTRY,
    )


def _entries() -> list[dict]:
    return builder.load_registry(REGISTRY)["entries"]


def test_section_coverage_report_is_generated_deterministically():
    first = _report()
    second = _report()

    assert first == second
    assert builder.serialize_report(first) == builder.serialize_report(second)
    assert first["deterministic_output"] is True
    assert first["generated_at_utc"] == builder.DETERMINISTIC_GENERATED_AT


def test_generated_report_covers_every_parser_visible_section():
    report = _report()
    summary = report["coverage_summary"]

    assert summary["parser_visible_section_count"] == len(report["section_coverage"])
    assert summary["parser_visible_section_count"] > 3000
    assert summary["blocked_or_future_entries_routed"] is True
    assert summary["authority_boundary_all_false"] is True

    first_section = report["section_coverage"][0]
    assert first_section["parser_visible"] is True
    assert first_section["capability_id"]
    assert {
        "codable",
        "policy_only",
        "static_contract_only",
        "source_evidence_dependent",
        "runtime_receipt_dependent",
        "owner_approval_dependent",
    } <= set(first_section)


def test_generated_report_schema_validates():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert validator.validate_json_schema_subset(report, schema) == []


def test_removed_implementation_ledger_system_is_not_referenced():
    failures = validator.validate_no_removed_ledger_references(
        repo_root=REPO_ROOT.resolve(),
        registry_path=REGISTRY,
        schema_path=SCHEMA,
        report_path=REPORT,
    )

    assert failures == []


def test_blocked_and_future_items_require_route_or_unblock_condition():
    assert validator.validate_blocked_future_routing(_entries()) == []

    entry = copy.deepcopy(_entries()[0])
    entry["capability_id"] = "synthetic_idle_blocked_item"
    entry["current_status"] = "BLOCKED_SOURCE_EVIDENCE"
    entry["research_route"] = ""
    entry["unblock_condition"] = ""
    entry["required_receipts"] = []
    entry["quarantine_reason"] = ""
    entry["retirement_reason"] = ""
    entry["static_safety_stub"] = ""

    failures = validator.validate_blocked_future_routing([entry])

    assert failures
    assert "synthetic_idle_blocked_item" in failures[0]


def test_complete_verified_without_required_files_tests_reports_fails():
    entry = copy.deepcopy(_entries()[0])
    entry["capability_id"] = "synthetic_false_complete"
    entry["current_status"] = "COMPLETE_VERIFIED"
    entry["required_files"] = ["docs/master_plan/generated/does_not_exist.json"]
    entry["required_tests"] = []
    entry["required_reports"] = []

    failures = validator.validate_complete_verified_evidence(
        [entry],
        repo_root=REPO_ROOT.resolve(),
    )

    assert any("COMPLETE_VERIFIED missing required_files path" in item for item in failures)
    assert any("COMPLETE_VERIFIED requires required_tests" in item for item in failures)
    assert any("COMPLETE_VERIFIED requires required_reports" in item for item in failures)


def test_authority_claims_fail_without_validated_receipts():
    for field in validator.REQUIRED_AUTHORITY_BOUNDARY_FIELDS:
        entry = copy.deepcopy(_entries()[0])
        entry["capability_id"] = f"synthetic_authority_{field}"
        entry["authority_boundary"][field] = True

        failures = validator.validate_registry_entries([entry])

        assert any(field in item for item in failures)
        assert any("without validated receipt evidence" in item for item in failures)


def test_final_mode_exists_and_reports_incomplete():
    result = validator.validate(
        mode="final",
        repo_root=REPO_ROOT,
        master_plan=MASTER_PLAN,
        registry_path=REGISTRY,
        report_path=REPORT,
        schema_path=SCHEMA,
    )

    assert result.ok is False
    assert any("final mode incomplete status remains" in item for item in result.failures)


def test_dev_mode_validates_generated_report_and_blocks_pr_tracking_keys():
    result = validator.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        master_plan=MASTER_PLAN,
        registry_path=REGISTRY,
        report_path=REPORT,
        schema_path=SCHEMA,
    )

    assert result.failures == ()
    assert validator.validate_no_pr_tracking_keys(result.report) == []
