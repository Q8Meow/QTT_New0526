from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.build_pr168_map3 import REPORTS, build_summary


GENERATED_ROOT = Path("docs/master_plan/generated")
ALLOWED_STATES = {
    "MATERIALIZED_FORMULA_PLUGIN_CONTRACT",
    "SEMANTIC_FORMULA_CANDIDATE_REQUIRES_EXPRESSION_REPAIR",
    "SOURCE_EVIDENCE_REVIEW_REQUIRED",
    "DATA1B_DATA_ACQUISITION_REPAIR_REQUIRED",
    "REJECTED_WITH_REASON",
}
ONLINE_REQUIRED_FIELDS = {
    "scout_row_id",
    "source_url",
    "source_title",
    "source_tier",
    "retrieved_at_utc",
    "query_family",
    "useful_formula_or_input_found_flag",
    "formula_family_candidate",
    "candidate_expression_or_semantic_definition",
    "required_inputs_candidate",
    "data_family_requirements",
    "unit_requirements",
    "candidate_only_flag",
    "accepted_truth_flag",
    "source_evidence_review_route",
    "RP2_or_RANK2_route_if_computable",
    "rejected_flag",
    "reject_reason_if_any",
}


def _read_report(name: str) -> dict[str, Any]:
    path = GENERATED_ROOT / name
    if not path.exists():
        raise AssertionError(f"missing required MAP3 report: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _records(report: dict[str, Any]) -> list[dict[str, Any]]:
    records = report.get("records")
    if not isinstance(records, list) or not records:
        raise AssertionError(f"report has no non-placeholder records: {report.get('physical_filename')}")
    return records


def read_rows_by_name() -> dict[str, list[dict[str, Any]]]:
    return {
        key: _records(_read_report(physical))
        for key, (_, physical) in REPORTS.items()
    }


def validate_required_reports(rows_by_name: dict[str, list[dict[str, Any]]]) -> None:
    for key, rows in rows_by_name.items():
        if not rows:
            raise AssertionError(f"{key} report is empty")


def validate_online_rows(rows_by_name: dict[str, list[dict[str, Any]]]) -> None:
    for row in rows_by_name["online"]:
        missing = sorted(field for field in ONLINE_REQUIRED_FIELDS if field not in row)
        if missing:
            raise AssertionError(f"{row.get('scout_row_id')} missing fields: {missing}")
        if row["candidate_only_flag"] is not True:
            raise AssertionError(f"{row['scout_row_id']} lacks candidate-only authority")
        if row["accepted_truth_flag"] is not False:
            raise AssertionError(f"{row['scout_row_id']} accepts source truth")
        if not row["source_url"] or not row["source_tier"] or not row["formula_family_candidate"]:
            raise AssertionError(f"{row['scout_row_id']} is a source note without required routing fields")
        if row["useful_formula_or_input_found_flag"] and row["materialization_path"] not in ALLOWED_STATES:
            raise AssertionError(f"{row['scout_row_id']} has invalid materialization path")
        if row["rejected_flag"] and not row["reject_reason_if_any"]:
            raise AssertionError(f"{row['scout_row_id']} rejected without reason")
        if not row["required_inputs_candidate"] and not row.get("missing_input_reason"):
            raise AssertionError(f"{row['scout_row_id']} lacks required inputs or exact missing reason")
        if row.get("no_orphan_status") != "NO_ORPHAN_LINKED":
            raise AssertionError(f"{row['scout_row_id']} has no-orphan violation")


def validate_authority(rows_by_name: dict[str, list[dict[str, Any]]]) -> None:
    all_rows = [row for rows in rows_by_name.values() for row in rows]
    forbidden_truthy = [
        "accepted_truth_flag",
        "source_truth_acceptance_created_flag",
        "champion_allowed_flag",
        "live_candidate_allowed_flag",
        "live_authority_created_flag",
        "profit_evidence_created_flag",
        "connector_semantic_binding_created_flag",
        "private_state_access_created_flag",
        "cash_access_created_flag",
        "order_authority_created_flag",
        "quantum_backend_execution_flag",
        "quantum_advantage_claim_flag",
        "qtt_sha_or_atomicrows_hash_authority_flag",
    ]
    for row in all_rows:
        for field in forbidden_truthy:
            if row.get(field) is True:
                raise AssertionError(f"forbidden authority field {field} in {row}")
        if row.get("authority_class") in {"REAL_POSITIVE", "REAL_NEGATIVE", "CHAMPION", "LIVE_CANDIDATE"}:
            raise AssertionError(f"forbidden authority class in {row}")


def validate_minimum_counts(rows_by_name: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary = build_summary(rows_by_name)
    checks = {
        "online_scout_row_count": summary["online_scout_row_count"] >= 30,
        "distinct_source_url_count": summary["distinct_source_url_count"] >= 10,
        "query_family_count": summary["query_family_count"] >= 8,
        "mandatory_family_total": (
            summary["mandatory_formula_family_covered_count"]
            + summary["mandatory_formula_family_gap_routed_count"]
            >= 12
        ),
        "useful_formula_or_input_found_count": summary["useful_formula_or_input_found_count"] > 0,
        "materialized_or_semantic": (
            summary["materialized_formula_candidate_count"]
            + summary["semantic_formula_repair_route_count"]
            > 0
        ),
        "contract_or_semantic": (
            summary["formula_plugin_contract_count"]
            + summary["semantic_formula_repair_route_count"]
            > 0
        ),
        "handoff_total": (
            summary["rp2_handoff_count"]
            + summary["rank2_handoff_count"]
            + summary["source_evidence_review_route_count"]
            + summary["data1b_repair_route_count"]
            > 0
        ),
        "no_orphan_violation_count": summary["no_orphan_violation_count"] == 0,
        "source_truth_acceptance_created_count": summary["source_truth_acceptance_created_count"] == 0,
        "real_positive_count": summary["real_positive_count"] == 0,
        "real_negative_count": summary["real_negative_count"] == 0,
        "champion_allowed_count": summary["champion_allowed_count"] == 0,
        "live_candidate_allowed_count": summary["live_candidate_allowed_count"] == 0,
    }
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise AssertionError(f"MAP3 online scouting counts below minimum: {failures}; summary={summary}")
    return summary


def validate_pr168_map3() -> dict[str, Any]:
    rows_by_name = read_rows_by_name()
    validate_required_reports(rows_by_name)
    validate_online_rows(rows_by_name)
    validate_authority(rows_by_name)
    return validate_minimum_counts(rows_by_name)
