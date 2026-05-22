"""Deterministic PR138 semantic row-contract report builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import constants as c
from .schema import build_contract, json_dump, write_inventory_file, write_schema_file


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _existing(root: Path, paths: Sequence[str]) -> list[str]:
    return [path for path in paths if (root / path).exists()]


def _missing(root: Path, paths: Sequence[str]) -> list[str]:
    return [path for path in paths if not (root / path).exists()]


def _glob(root: Path, pattern: str) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.glob(pattern))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _route_triage_trace(root: Path, found: Sequence[str]) -> dict[str, Any]:
    if not found:
        return {
            "reason_code": c.PR138_REASON_ROUTE_TRIAGE_EVIDENCE_MISSING,
            "trace_state": "TRACE_BLOCKED",
        }
    report = _load_json(root / found[0])
    return {
        "artifact_paths": list(found),
        "receipt_type": report.get("receipt_type"),
        "repo_pr_number": report.get("repo_pr_number"),
        "route_resolution_basis": report.get("route_resolution_basis"),
        "sequence_authority_class": report.get("sequence_authority_class"),
        "trace_state": "TRACE_CONSUMED_READ_ONLY",
    }


def _section_crosswalk(root: Path, found: Sequence[str]) -> dict[str, Any]:
    if not found:
        return {
            "artifacts": [],
            "by_section_id": {},
            "trace_state": "TRACE_BLOCKED",
        }
    path = root / "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json"
    report = _load_json(path)
    rows = [row for row in _list(report.get("rows")) if isinstance(row, dict)]
    by_section = {str(row.get("section_id")): row for row in rows}
    return {
        "artifacts": list(found),
        "by_section_id": by_section,
        "receipt_type": report.get("receipt_type"),
        "trace_state": "TRACE_CONSUMED_READ_ONLY",
    }


def _market_specific_trace(root: Path, found: Sequence[str]) -> dict[str, Any]:
    if not found:
        return {
            "reason_code": c.PR138_REASON_MARKET_INDEX_EVIDENCE_MISSING,
            "trace_state": "TRACE_BLOCKED",
        }
    market_scope_ids: list[str] = []
    canonical_venue_ids: list[str] = []
    for rel_path in (
        "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
        "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    ):
        path = root / rel_path
        if not path.exists():
            continue
        report = _load_json(path)
        for row in _list(report.get("market_scopes")):
            if not isinstance(row, dict):
                continue
            venue = row.get("canonical_venue_id")
            scope_id = row.get("market_scope_id")
            if isinstance(venue, str) and venue not in canonical_venue_ids:
                canonical_venue_ids.append(venue)
            if isinstance(scope_id, str) and scope_id not in market_scope_ids:
                market_scope_ids.append(scope_id)
    return {
        "artifact_paths": list(found),
        "canonical_venue_ids": canonical_venue_ids,
        "market_scope_ids": market_scope_ids,
        "trace_state": "TRACE_CONSUMED_READ_ONLY",
    }


def _command_action_trace(root: Path, found: Sequence[str]) -> dict[str, Any]:
    if not found:
        return {
            "reason_code": c.PR138_REASON_COMMAND_ACTION_MATRIX_EVIDENCE_MISSING,
            "trace_state": "TRACE_BLOCKED",
        }
    action_ids: list[str] = []
    preferred = {
        "CREATE_SCHEMAS_WITH_POLICY_REFS",
        "CREATE_FIXTURES",
        "CREATE_VALIDATOR",
        "CREATE_GENERATED_REPORTS",
        "ADD_FOCUSED_TESTS",
        "RUN_VALIDATIONS",
        "run_validation_gates",
    }
    for rel_path in (
        "docs/master_plan/generated/PR135CommandActionMatrix.report.json",
        "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    ):
        path = root / rel_path
        if not path.exists():
            continue
        report = _load_json(path)
        for row in _list(report.get("actions")):
            if not isinstance(row, dict):
                continue
            action_id = row.get("action_id")
            if isinstance(action_id, str) and action_id in preferred:
                action_ids.append(action_id)
    return {
        "action_ids": sorted(set(action_ids)),
        "artifact_paths": list(found),
        "trace_state": "TRACE_CONSUMED_READ_ONLY",
    }


def evidence_snapshot(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    pr137r_path = root / c.PR137R_REPORT_PATH
    pr137l_path = root / c.PR137L_REPORT_PATH
    pr137r_report = _load_json(pr137r_path) if pr137r_path.exists() else {}
    pr137l_report = _load_json(pr137l_path) if pr137l_path.exists() else {}

    pr137r_inventory = _mapping(pr137r_report.get("atomicrows_artifact_inventory"))
    pr137r_state = _mapping(pr137r_report.get("atomicrows_validation_state"))
    pr137r_field_audit = _mapping(pr137r_state.get("row_contract_field_audit"))
    pr137l_snapshot = _mapping(pr137l_report.get("pr137r_static_evidence_snapshot"))

    route_found = _existing(root, c.ROUTE_TRIAGE_ARTIFACTS)
    section_found = _existing(root, c.SECTION_CROSSWALK_ARTIFACTS)
    market_found = _existing(root, c.MARKET_INDEX_ARTIFACTS)
    command_found = _existing(root, c.COMMAND_ACTION_MATRIX_ARTIFACTS)
    roadmap_found = _existing(root, c.ROADMAP_SAFE_ARCHITECTURE_ARTIFACTS)

    row_family_sources = _glob(root, c.ROW_FAMILY_SOURCE_GLOB)
    exact_sources = _glob(root, c.EXACT_ROW_SOURCE_GLOB)

    section_trace = _section_crosswalk(root, section_found)
    return {
        "atomicrows_bundle_exists": (root / c.ATOMICROWS_BUNDLE_PATH).exists(),
        "atomicrows_bundle_path": c.ATOMICROWS_BUNDLE_PATH.as_posix(),
        "atomicrows_row_count_from_bundle_file": (
            sum(1 for _line in (root / c.ATOMICROWS_BUNDLE_PATH).open("r", encoding="utf-8"))
            if (root / c.ATOMICROWS_BUNDLE_PATH).exists()
            else None
        ),
        "bundle_builder_paths_found": _existing(root, c.BUNDLE_BUILDER_PATHS),
        "command_action_matrix_artifacts_found": command_found,
        "command_action_matrix_artifacts_missing": _missing(
            root, c.COMMAND_ACTION_MATRIX_ARTIFACTS
        ),
        "command_action_matrix_trace": _command_action_trace(root, command_found),
        "current_bundle_basic_schema_validation_status": (
            c.CURRENT_BUNDLE_BASIC_SCHEMA_VALIDATION_STATUS_PASSED
            if pr137r_state.get("schema_validated") is True
            else c.CURRENT_BUNDLE_BASIC_SCHEMA_VALIDATION_STATUS_UNKNOWN
        ),
        "exact_row_source_file_count": len(exact_sources),
        "exact_row_source_files_found": exact_sources,
        "market_specific_section_index_artifacts_found": market_found,
        "market_specific_section_index_artifacts_missing": _missing(
            root, c.MARKET_INDEX_ARTIFACTS
        ),
        "market_specific_section_index_trace": _market_specific_trace(root, market_found),
        "pr137l_evidence_consumed_read_only": bool(pr137l_report),
        "pr137l_evidence_paths_found": [
            path.as_posix()
            for path in (c.PR137L_REPORT_PATH, c.PR137L_INDEX_PATH)
            if (root / path).exists()
        ],
        "pr137l_snapshot_semantic_complete": (
            pr137l_snapshot.get("atomicrows_semantic_row_contract_complete")
        ),
        "pr137r_evidence_consumed_read_only": bool(pr137r_report),
        "pr137r_evidence_paths_found": [
            path.as_posix()
            for path in (c.PR137R_REPORT_PATH, c.PR137R_INDEX_PATH)
            if (root / path).exists()
        ],
        "pr137r_report_type": pr137r_report.get("report_type"),
        "pr137r_semantic_missing_field_count": len(
            _list(pr137r_field_audit.get("missing_fields"))
        ),
        "pr137r_semantic_missing_fields_sample": [
            str(item) for item in _list(pr137r_field_audit.get("missing_fields"))[:12]
        ],
        "pr137r_state": {
            "functional_bundle_artifact_found": pr137r_inventory.get(
                "functional_bundle_artifact_found"
            ),
            "functional_bundle_status": pr137r_state.get("functional_bundle_status"),
            "row_count_proven": pr137r_state.get("row_count_proven"),
            "row_count_value": pr137r_state.get("row_count_value"),
            "schema_validated": pr137r_state.get("schema_validated"),
            "readiness_gate_found": pr137r_state.get("readiness_gate_found"),
            "day1_live_trading_ready": pr137r_state.get("day1_live_trading_ready"),
            "profit_evidence_created": pr137r_state.get("profit_evidence_created"),
            "quantum_advantage_evidence_created": pr137r_state.get(
                "quantum_advantage_evidence_created"
            ),
        },
        "roadmap_safe_architecture_artifacts_found": roadmap_found,
        "route_triage_artifacts_found": route_found,
        "route_triage_artifacts_missing": _missing(root, c.ROUTE_TRIAGE_ARTIFACTS),
        "route_triage_trace": _route_triage_trace(root, route_found),
        "row_family_source_file_count": len(row_family_sources),
        "row_family_source_files_found": row_family_sources,
        "section_crosswalk_artifacts": section_trace["artifacts"],
        "section_crosswalk_artifacts_found": section_found,
        "section_crosswalk_artifacts_missing": _missing(root, c.SECTION_CROSSWALK_ARTIFACTS),
        "section_crosswalk_by_section_id": section_trace["by_section_id"],
    }


def _report_no_claim_flags() -> dict[str, bool]:
    return {name: False for name in c.REPORT_NO_CLAIM_FLAG_NAMES}


def build_report(
    repo_root: Path | str,
    *,
    owner_verified_baseline_receipt_consumed: bool = False,
    sandbox_bootstrap_fallback_used: bool = False,
) -> dict[str, Any]:
    evidence = evidence_snapshot(repo_root)
    contract = build_contract(evidence)
    no_claim_flags = _report_no_claim_flags()
    row_count_proven = evidence["pr137r_state"].get("row_count_proven") is True
    row_count_value = evidence["pr137r_state"].get("row_count_value")
    report = {
        "atomicrows_bundle_detected_from_existing_repo_evidence": evidence[
            "atomicrows_bundle_exists"
        ],
        "atomicrows_bundle_evidence_path": evidence["atomicrows_bundle_path"],
        "atomicrows_row_count_from_existing_evidence": (
            row_count_value if row_count_proven else None
        ),
        "authority_class": c.AUTHORITY_CLASS,
        "baseline_checkpoint": c.BASELINE_CHECKPOINT,
        "command_action_matrix_consumed_read_only": bool(
            evidence["command_action_matrix_artifacts_found"]
        ),
        "command_action_matrix_evidence_paths": evidence[
            "command_action_matrix_artifacts_found"
        ],
        "contract_level_default_flag_values": {
            field: False for field in c.CONTRACT_DEFAULT_FALSE_FLAG_FIELDS
        },
        "current_bundle_basic_schema_validation_status": evidence[
            "current_bundle_basic_schema_validation_status"
        ],
        "day1_live_readiness_claimed_by_pr138": False,
        "final_readiness_claimed_by_pr138": False,
        "full_master_plan_section_crosswalk_consumed_read_only": bool(
            evidence["section_crosswalk_artifacts_found"]
        ),
        "full_master_plan_section_crosswalk_evidence_paths": evidence[
            "section_crosswalk_artifacts_found"
        ],
        "generated_at_utc": c.STATIC_TIME,
        "generated_by": (
            "src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.report"
        ),
        "hot_path_forbidden_dependencies": list(c.HOT_PATH_FORBIDDEN_DEPENDENCIES),
        "market_specific_section_indexes_consumed_read_only": bool(
            evidence["market_specific_section_index_artifacts_found"]
        ),
        "market_specific_section_index_evidence_paths": evidence[
            "market_specific_section_index_artifacts_found"
        ],
        "new_atomicrows_bundle_sidecar_reference_created_by_pr138": False,
        "next_required_prs": list(c.NEXT_REQUIRED_PRS),
        "owner_verified_baseline_receipt_consumed": owner_verified_baseline_receipt_consumed,
        "pr137l_evidence_consumed_read_only": evidence["pr137l_evidence_consumed_read_only"],
        "pr137l_evidence_paths": evidence["pr137l_evidence_paths_found"],
        "pr137r_evidence_consumed_read_only": evidence["pr137r_evidence_consumed_read_only"],
        "pr137r_evidence_paths": evidence["pr137r_evidence_paths_found"],
        "pr_id": c.PR_ID,
        "report_type": c.REPORT_TYPE,
        "required_field_count": c.REQUIRED_FIELD_COUNT,
        "required_field_group_count": c.REQUIRED_FIELD_GROUP_COUNT,
        "route_triage_evidence_consumed_read_only": bool(
            evidence["route_triage_artifacts_found"]
        ),
        "route_triage_evidence_paths": evidence["route_triage_artifacts_found"],
        "sandbox_bootstrap_fallback_used": sandbox_bootstrap_fallback_used,
        "schema_path": c.SCHEMA_PATH.as_posix(),
        "semantic_contract": {
            "canonical_stage1_market_scopes": list(c.CANONICAL_STAGE1_MARKET_SCOPES),
            "field_group_ids": list(c.REQUIRED_FIELD_GROUP_IDS),
            "field_ids": list(c.REQUIRED_FIELD_IDS),
            "field_inventory_path": c.INVENTORY_PATH.as_posix(),
            "forbidden_aliases_enforced_from_constants": True,
            "required_field_count": contract["required_field_count"],
            "required_field_group_count": contract["required_field_group_count"],
        },
        "semantic_incompleteness_evidence": {
            "pr137l_snapshot_semantic_complete": evidence[
                "pr137l_snapshot_semantic_complete"
            ],
            "pr137r_missing_field_count": evidence["pr137r_semantic_missing_field_count"],
            "pr137r_missing_fields_sample": evidence[
                "pr137r_semantic_missing_fields_sample"
            ],
        },
        "semantic_row_contract_defined_by_pr138": True,
        "semantic_row_values_materialized_by_pr138": False,
        "validation_state": "STATIC_SEMANTIC_CONTRACT_DEFINED_NOT_FINAL_READY",
        **no_claim_flags,
    }
    return report


def build_index(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "authority_class": c.AUTHORITY_CLASS,
        "baseline_checkpoint": c.BASELINE_CHECKPOINT,
        "field_inventory_ref": c.INVENTORY_PATH.as_posix(),
        "gate_tool": c.GATE_TOOL_PATH,
        "index_type": c.INDEX_TYPE,
        "next_required_prs": list(c.NEXT_REQUIRED_PRS),
        "pr_id": c.PR_ID,
        "report_ref": c.REPORT_PATH.as_posix(),
        "schema_ref": c.SCHEMA_PATH.as_posix(),
        "validation_receipts": list(c.SUCCESS_RECEIPTS),
    }


def write_report_files(
    repo_root: Path | str,
    *,
    owner_verified_baseline_receipt_consumed: bool = False,
    sandbox_bootstrap_fallback_used: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    evidence = evidence_snapshot(root)
    contract = build_contract(evidence)
    schema = write_schema_file(root)
    write_inventory_file(root, contract)
    report = build_report(
        root,
        owner_verified_baseline_receipt_consumed=owner_verified_baseline_receipt_consumed,
        sandbox_bootstrap_fallback_used=sandbox_bootstrap_fallback_used,
    )
    index = build_index(report)
    report_path = root / c.REPORT_PATH
    index_path = root / c.INDEX_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json_dump(report), encoding="utf-8", newline="\n")
    index_path.write_text(json_dump(index), encoding="utf-8", newline="\n")
    return {"contract": contract, "index": index, "report": report, "schema": schema}

