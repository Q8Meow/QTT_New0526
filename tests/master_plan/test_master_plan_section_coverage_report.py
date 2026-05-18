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


def test_route_map_extension_is_static_and_controller_referenced():
    report = _report()
    route_map = report["route_map"]
    route_summary = report["route_map_summary"]

    assert route_map["repo_canonical_pr_label"] == "PR119"
    assert route_map["roadmap_pr_label"] == "PR #102"
    assert route_map["semantic_task_id"] == "ROADMAP-MASTER-PLAN-COVERAGE-TRIAGE-I"
    assert route_summary["artifact_family_decision"] == (
        "EXISTING_MASTER_PLAN_SECTION_COVERAGE_FAMILY_EXTENDED"
    )
    assert route_summary["route_entry_count"] == len(route_map["route_entries"])
    assert route_summary["unresolved_default_count"] == 1
    assert route_summary["quantum_forward_route_count"] == 1
    assert route_summary["optimizer_arbitration_route_count"] == 1
    assert route_summary["latency_cost_route_count"] == 1
    assert route_summary["old_coverage_ledger_reintroduction_flag"] is False
    assert route_summary["master_plan_mutation_count"] == 0
    assert route_summary["runtime_authority_created"] is False
    assert route_summary["live_authority_created"] is False
    assert route_summary["source_fact_acceptance_created"] is False
    assert route_summary["connector_semantic_binding_created"] is False
    assert route_summary["replay_paper_result_created"] is False
    assert route_summary["order_authority_created"] is False
    assert route_summary["profit_evidence_created"] is False
    assert route_summary["latency_superiority_evidence_created"] is False
    assert (
        route_summary["quantum_backend_simulator_optimizer_execution_created"]
        is False
    )

    route_classes = route_summary["count_by_route_class"]
    assert route_classes["UNRESOLVED_DEFAULT_ROUTE"] == 1
    assert route_classes["QUANTUM_FORWARD_OPTIMIZATION_ROUTE"] == 1
    assert route_classes["OPTIMIZER_ARBITRATION_ROUTE"] == 1
    assert route_classes["LATENCY_COST_ROUTE"] == 1


def test_pr120_crosswalk_covers_every_section_and_keeps_authority_static():
    report = _report()
    rows = report["roadmap_crosswalk"]["rows"]
    summary = report["roadmap_crosswalk_summary"]

    assert report["pr120_scope_summary"]["repo_canonical_pr_label"] == "PR120"
    assert report["pr120_scope_summary"]["roadmap_pr_label"] == "PR #103"
    assert report["pr120_scope_summary"]["blueprint_pr_label"] == "PR #103"
    assert summary["section_manifest_parser_visible_section_count"] == len(rows)
    assert summary["section_manifest_parser_visible_section_count"] == len(
        report["section_coverage"]
    )
    assert summary["all_section_crosswalk_row_count"] == len(rows)
    assert summary["missing_section_count"] == 0
    assert summary["duplicate_section_count"] == 0
    assert summary["ordering_matches_section_manifest"] is True
    assert summary["master_plan_mutation_count"] == 0
    assert summary["runtime_authority_created"] is False
    assert summary["live_authority_created"] is False
    assert summary["market_launch_authority_created"] is False

    first_row = rows[0]
    assert first_row["document_order_index"] == 1
    assert first_row["section_id"] == report["section_coverage"][0]["owner_section_id"]
    assert first_row["no_master_plan_text_mutation_flag"] is True
    assert first_row["no_old_coverage_ledger_flag"] is True
    assert first_row["no_market_launch_authority_created_flag"] is True


def test_pr119_exact_routes_are_preserved_inside_pr120_crosswalk():
    report = _report()
    rows = {row["section_id"]: row for row in report["roadmap_crosswalk"]["rows"]}

    for entry in report["route_map"]["route_entries"]:
        row = rows[entry["section_id"]]
        assert row["current_route_class"] == entry["current_route_class"]
        assert row["route_confidence_class"] == "EXACT_PR119_ROUTE_ENTRY"
        assert entry["downstream_consumer_reference"] in row[
            "downstream_consumer_references"
        ]
        assert entry["controller_state_reference"] in {
            item["controller_entry_reference"]
            for item in row["controller_state_references"]
        }


def test_market_specific_section_index_is_derived_and_non_launch_authority():
    report = _report()
    market_index = report["market_specific_section_index"]
    summary = report["market_specific_section_index_summary"]

    assert market_index["authority_class"] == (
        "STATIC_MARKET_SECTION_INDEX_NOT_MARKET_LAUNCH_AUTHORITY"
    )
    assert summary["market_specific_index_count"] == len(market_index["markets"])
    assert summary["prediction_market_section_counts"]["KALSHI"] >= 1
    assert summary["prediction_market_section_counts"]["POLYMARKET"] >= 1
    assert summary["prediction_market_section_counts"]["FORECASTEX_IBKR"] >= 1
    assert summary["market_launch_authority_created"] is False
    assert summary["stage2_launch_authority_created"] is False
    assert summary["next_market_selected"] is False
    for market in market_index["markets"]:
        assert market["no_market_launch_authority_created_flag"] is True
        assert market["no_external_market_fact_created_flag"] is True


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
