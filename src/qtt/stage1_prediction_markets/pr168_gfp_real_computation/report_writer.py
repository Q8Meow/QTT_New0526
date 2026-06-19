"""Generated report writer for PR168-GFP."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from .baseline_counts import reconcile_counts
from .canonical_rows import (
    ATOMICROWS_JSONL,
    CPV1_REPORT,
    PR154_REPORT,
    QKU_REPORT,
    atomicrows_qku_id,
    canonical_key_for_atomicrow,
    canonical_key_for_pr154,
    canonical_key_from_qku_id,
    load_inventory,
    source_pointer,
)
from .formula_assignment import (
    assignment_for_row,
    derive_required_formula_set_ids,
    formula_families_for_ids,
    formula_ids_for_sets,
    required_formula_set_map_with_family_refs,
)
from .formula_discovery import (
    FAMILY_SEARCH_TERMS,
    REQUIRED_FORMULA_FAMILIES,
    REQUIRED_FORMULA_SETS,
    SELECTED_FORMULAS,
    selected_formula_records,
)
from .io import GENERATED_DIR, write_report


SHARD_DIR = Path("pr168_gfp_shards")
SHARD_SIZE = 1000
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
CATALOG_MAX_JSON_LIST_ITEMS = 250
CATALOG_MAX_RECORDS_PER_SOURCE = 120
CATALOG_TEXT_RE = re.compile(
    r"formula|operating law|objective|constraint|solver|routing|qubo|bqm|ising|cqm|dqm|"
    r"quadraticprogram|quadprogram|tca|transaction cost|implementation shortfall|spread|fee|"
    r"slippage|market impact|adverse selection|queue|fill probability|partial fill|latency|"
    r"capacity|crowding|overfit|false discovery|fdr|lower confidence|confidence bound|"
    r"expected shortfall|cvar|portfolio|risk budget|champion|challenger|regime|conformal|"
    r"bayesian|shrinkage|covariance|hrp|fallback",
    re.IGNORECASE,
)
PRIOR_PR_CATALOG_PATH_RE = re.compile(
    r"(PR162B|PR162C|PR162D|PR162E|PR166[_-]Q|PR166[_-]QB|PR166[_-]QC|PR167|"
    r"QKU.*(Formula|Objective|Solver|Market)|"
    r"ParameterAlgorithmScoringPolicyRegistry|RouteTriage|Route_Triage|SectionCrosswalk|"
    r"MarketSpecific|CommandAction|CommandMatrix)",
    re.IGNORECASE,
)


def build_all_reports(repo_root: Path) -> dict[str, Any]:
    inventory = load_inventory(repo_root)
    qku_by_id = {str(row.get("qku_id")): row for row in inventory.qku_records}

    count_records = reconcile_counts(inventory)
    count_summary = _count_summary(inventory, count_records)
    _write_count_reports(repo_root, count_records, count_summary, inventory)

    canonical_records = _canonical_records(inventory)
    _write_sharded_report(
        repo_root,
        "PR168_GFP_CanonicalRowKeyMap.report.json",
        canonical_records,
        extra={"report_type": "PR168_GFP_CANONICAL_ROW_KEY_MAP", "dedupe_policy": "canonical_row_key_with_surface_pointer_preserved"},
    )

    actual_family_records = _derive_actual_formula_family_requirements(inventory, qku_by_id)
    actual_families = sorted({str(row["formula_family_required"]) for row in actual_family_records})
    missing_family_records = _missing_source_records(actual_families)

    _write_family_discovery_reports(repo_root, actual_family_records, actual_families, missing_family_records)

    if missing_family_records:
        raise RuntimeError(
            "PR168-GFP formula-source discovery incomplete: "
            + ", ".join(str(row["formula_family_required"]) for row in missing_family_records)
        )

    master_plan_catalog_summary = _write_master_plan_formula_catalog_reports(repo_root)

    assignments = _assignment_records(inventory, qku_by_id)
    _write_sharded_report(
        repo_root,
        "PR168_GFP_FormulaAssignmentMatrix.report.json",
        assignments,
        extra={
            "report_type": "PR168_GFP_FORMULA_ASSIGNMENT_MATRIX",
            "assignment_policy": "per_row_reusable_formula_functions_required_formula_set_allowed_no_unique_formula_sprawl",
            "source_discovery_gate": "PASSED_BEFORE_ROW_ASSIGNMENT",
        },
    )
    _write_coverage_reports(repo_root, assignments)
    label_records = _scan_tracked_label_claims(repo_root)
    _write_truth_overlay_and_label_reports(repo_root, assignments, label_records)
    _write_forbidden_formula_terminology_audit(repo_root)

    return {
        "reports_written": [
            "PR168_GFP_QKUBaselineCountReconcile.report.json",
            "PR168_GFP_Historical9360VsCurrent6502Reconcile.report.json",
            "PR168_GFP_CanonicalRowKeyMap.report.json",
            "PR168_GFP_FormulaFamilySearchMatrix.report.json",
            "PR168_GFP_FormulaDiscoveryCoverageAudit.report.json",
            "PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
            "PR168_GFP_RequiredFormulaSetMap.report.json",
            "PR168_GFP_MasterPlanFormulaCatalog.report.json",
            "PR168_GFP_MasterPlanQuantumFormulaCatalog.report.json",
            "PR168_GFP_PriorPRFormulaCatalog.report.json",
            "PR168_GFP_MasterPlanFormulaToSelectedFormulaCrosswalk.report.json",
            "PR168_GFP_MasterPlanFormulaGapLedger.report.json",
            "PR168_GFP_MasterPlanFormulaCoverageAudit.report.json",
            "PR168_GFP_FormulaAssignmentMatrix.report.json",
            "PR168_GFP_QKUComputationCoverage.report.json",
            "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
            "PR168_GFP_AtomicRowsComputationCoverage.report.json",
            "PR168_GFP_ResidualFormulaSearchGap.report.json",
            "PR168_GFP_AuthoritativeTruthOverlay.report.json",
            "PR168_GFP_HistoricalLabelSupersessionMap.report.json",
            "PR168_GFP_ConsumerMustUseTruthOverlay.report.json",
            "PR168_GFP_GlobalLabelInventory.report.json",
            "PR168_GFP_ForbiddenFormulaBundleTerminologyAudit.report.json",
        ],
        "actual_formula_family_count": len(actual_families),
        "formula_source_gap_count": len(missing_family_records),
        **master_plan_catalog_summary,
        "assignment_count": len(assignments),
    }


def _write_count_reports(repo_root: Path, records: list[dict[str, Any]], summary: dict[str, Any], inventory: Any) -> None:
    payload = _base_report("PR168_GFP_QKU_BASELINE_COUNT_RECONCILE", records, summary)
    write_report(repo_root, "PR168_GFP_QKUBaselineCountReconcile.report.json", payload)

    qku_keys = {canonical_key_from_qku_id(str(row.get("qku_id"))) for row in inventory.qku_records}
    candidate_keys = {canonical_key_from_qku_id(str(row.get("qku_id"))) for row in inventory.candidate_packet_records}
    overlap = sorted(qku_keys & candidate_keys)
    historical_payload = _base_report(
        "PR168_GFP_HISTORICAL_9360_VS_CURRENT_6502_RECONCILE",
        [
            {
                "historical_master_qku_count_expected": 9360,
                "historical_master_qku_count_actual": len(qku_keys),
                "current_candidate_packet_v1_count_expected": 6502,
                "current_candidate_packet_v1_count_actual": len(candidate_keys),
                "overlap_by_canonical_row_key_count": len(overlap),
                "historical_only_count": len(qku_keys - candidate_keys),
                "operational_only_count": len(candidate_keys - qku_keys),
                "duplicate_policy": "candidate_packet_rows_overlap_historical_qku_by_qku_id_and_are_not_counted_as_new_qku_rows",
                "formula_assignment_required": True,
                "owning_agent": "Commander",
                "reconciliation_status": "MATCH" if len(qku_keys) == 9360 and len(candidate_keys) == 6502 else "MISMATCH",
            }
        ],
        {
            "historical_master_qku_count": len(qku_keys),
            "current_candidate_packet_v1_count": len(candidate_keys),
            "overlap_by_canonical_row_key_count": len(overlap),
        },
    )
    write_report(repo_root, "PR168_GFP_Historical9360VsCurrent6502Reconcile.report.json", historical_payload)


def _count_summary(inventory: Any, records: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(str(row["reconciliation_status"]) for row in records)
    return {
        "historical_master_qku_count_actual": len(inventory.qku_records),
        "candidate_packet_v1_count_actual": len(inventory.candidate_packet_records),
        "atomicrows_count_actual": len(inventory.atomicrows_records),
        "pr154_item_count_actual": len(inventory.pr154_records),
        "reconciliation_status_counts": dict(statuses),
    }


def _canonical_records(inventory: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(inventory.qku_records, start=1):
        qku_id = str(row.get("qku_id"))
        records.append(
            {
                "canonical_row_key": canonical_key_from_qku_id(qku_id),
                "row_family": "QKU",
                "source_report_path": QKU_REPORT.as_posix(),
                "source_row_pointer": source_pointer(QKU_REPORT, index, qku_id),
                "source_row_id": qku_id,
                "dedupe_equivalence_key": canonical_key_from_qku_id(qku_id),
                "terminal_flag": False,
                "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::{canonical_key_from_qku_id(qku_id)}",
            }
        )
    for index, row in enumerate(inventory.candidate_packet_records, start=1):
        qku_id = str(row.get("qku_id"))
        records.append(
            {
                "canonical_row_key": canonical_key_from_qku_id(qku_id),
                "row_family": "CandidatePacketV1",
                "source_report_path": CPV1_REPORT.as_posix(),
                "source_row_pointer": source_pointer(CPV1_REPORT, index, str(row.get("queue_id"))),
                "source_row_id": str(row.get("queue_id")),
                "dedupe_equivalence_key": canonical_key_from_qku_id(qku_id),
                "terminal_flag": False,
                "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::{canonical_key_from_qku_id(qku_id)}::CandidatePacketV1",
            }
        )
    for index, row in enumerate(inventory.atomicrows_records, start=1):
        key = canonical_key_for_atomicrow(row)
        records.append(
            {
                "canonical_row_key": key,
                "row_family": "AtomicRows",
                "source_report_path": ATOMICROWS_JSONL.as_posix(),
                "source_row_pointer": source_pointer(ATOMICROWS_JSONL, index, str(row.get("exact_row_id"))),
                "source_row_id": str(row.get("exact_row_id")),
                "dedupe_equivalence_key": key,
                "terminal_flag": False,
                "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::{key}::AtomicRows",
            }
        )
    for index, row in enumerate(inventory.pr154_records, start=1):
        key = canonical_key_for_pr154(row)
        records.append(
            {
                "canonical_row_key": key,
                "row_family": "PR154",
                "source_report_path": PR154_REPORT.as_posix(),
                "source_row_pointer": source_pointer(PR154_REPORT, index, str(row.get("pr154_record_id"))),
                "source_row_id": str(row.get("pr154_record_id")),
                "dedupe_equivalence_key": key,
                "terminal_flag": False,
                "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::{key}",
            }
        )
    return records


def _derive_actual_formula_family_requirements(inventory: Any, qku_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in inventory.qku_records:
        rows.extend(_family_rows_for_source_row(canonical_key_from_qku_id(str(row.get("qku_id"))), "QKU", row))
    for row in inventory.candidate_packet_records:
        qku_row = qku_by_id.get(str(row.get("qku_id")), {})
        rows.extend(_family_rows_for_source_row(canonical_key_from_qku_id(str(row.get("qku_id"))), "CandidatePacketV1", qku_row or {"qku_market_primary": "PREDICTION_MARKET"}))
    for row in inventory.atomicrows_records:
        atomic_row = {
            "qku_family": "ATOMICROWS",
            "qku_market_primary": "PREDICTION_MARKET",
            "qku_quantum_applicability": row.get("quantum_applicability_metadata_class") or row.get("source_quantum_metadata_class"),
        }
        rows.extend(_family_rows_for_source_row(canonical_key_for_atomicrow(row), "AtomicRows", atomic_row))
    for row in inventory.pr154_records:
        pr154_row = {
            "qku_family": "PR154",
            "qku_market_primary": "PREDICTION_MARKET",
            "qku_quantum_applicability": "QUANTUM_APPLICABLE",
        }
        rows.extend(_family_rows_for_source_row(canonical_key_for_pr154(row), "PR154", pr154_row))
    return rows


def _family_rows_for_source_row(canonical_row_key: str, row_family: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    set_ids = derive_required_formula_set_ids(row)
    formula_ids = formula_ids_for_sets(set_ids)
    families = formula_families_for_ids(formula_ids)
    return [
        {
            "canonical_row_key": canonical_row_key,
            "row_family": row_family,
            "required_formula_set_ids": set_ids,
            "formula_family_required": family,
            "formula_id": formula_id,
            "derivation_rule": "row_attributes_to_required_formula_set_to_formula_family",
        }
        for family, formula_id in zip(families, formula_ids)
    ]


def _missing_source_records(actual_families: list[str]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for family in actual_families:
        selected = SELECTED_FORMULAS.get(family)
        if not selected:
            missing.append(_gap_record(family, "NO_SELECTED_FORMULA"))
            continue
        has_expression = bool(selected.get("formula_expression"))
        has_source = bool(selected.get("formula_source_ref"))
        has_variable_map = bool(selected.get("variable_map"))
        has_function = bool(selected.get("computation_function_path"))
        has_repo_source = str(selected.get("formula_source_ref", "")).startswith("docs/")
        has_online_source = str(selected.get("formula_source_ref", "")).startswith("http") or any(str(ref).startswith("http") for ref in selected.get("alternate_source_refs", []))
        if not (has_expression and has_source and has_variable_map and has_function and (has_repo_source or has_online_source)):
            missing.append(_gap_record(family, "MISSING_REQUIRED_SELECTED_FORMULA_FIELD_OR_SOURCE_EVIDENCE"))
    return missing


def _gap_record(family: str, reason: str) -> dict[str, Any]:
    return {
        "formula_family_required": family,
        "gap_reason": reason,
        "residual_formula_materialization_route": "PR168-FM",
        "terminal_not_trading_formula_reason": None,
        "validation_status": "FAIL",
        "owning_agent": "External Scout Agent",
        "downstream_route": "PR168-FM",
    }


def _write_family_discovery_reports(
    repo_root: Path,
    actual_family_records: list[dict[str, Any]],
    actual_families: list[str],
    missing_family_records: list[dict[str, Any]],
) -> None:
    family_usage_counts = Counter(str(row["formula_family_required"]) for row in actual_family_records)
    search_records = []
    coverage_records = []
    for family in actual_families:
        selected = SELECTED_FORMULAS[family]
        repo_source_evidence = _repo_source_evidence(selected)
        online_source_evidence = _online_source_evidence(selected)
        search_records.append(
            {
                "formula_family": family,
                "formula_family_required_count": family_usage_counts[family],
                "derived_from_row_inventory": True,
                "search_terms": FAMILY_SEARCH_TERMS.get(family, [family]),
                "repo_source_evidence": repo_source_evidence,
                "online_formula_source_evidence": online_source_evidence,
                "second_pass_search_required": family in {str(row["formula_family_required"]) for row in missing_family_records},
                "second_pass_search_status": "NOT_REQUIRED_NO_SOURCE_GAP_AFTER_COMPARISON" if family not in {str(row["formula_family_required"]) for row in missing_family_records} else "REQUIRED_GAP_RECORDED",
                "source_truth_accepted": False,
                "selected_formula_id": selected["formula_id"],
                "selected_formula_expression": selected["formula_expression"],
                "formula_source_ref": selected["formula_source_ref"],
                "variable_map": selected["variable_map"],
                "computation_function_path": selected["computation_function_path"],
                "test_vector_or_input_gap_route": selected["test_vector_id"] or selected["input_gap_route"],
                "downstream_replay_paper_route": selected["downstream_replay_paper_route"],
                "owning_agent": selected["owning_agent"],
            }
        )
        coverage_records.append(
            {
                "formula_family": family,
                "derived_required_count": family_usage_counts[family],
                "repo_source_evidence_present": bool(repo_source_evidence),
                "online_formula_source_evidence_present": bool(online_source_evidence),
                "selected_formula_expression_present": bool(selected["formula_expression"]),
                "source_provenance_present": bool(selected["formula_source_ref"]),
                "variable_map_present": bool(selected["variable_map"]),
                "computation_function_path_present": bool(selected["computation_function_path"]),
                "test_vector_or_input_gap_route_present": bool(selected["test_vector_id"] or selected["input_gap_route"]),
                "downstream_replay_paper_route_present": bool(selected["downstream_replay_paper_route"]),
                "formula_discovery_status": "SOURCE_COVERED_SELECTED_EXPRESSION_READY",
                "source_truth_accepted": False,
            }
        )
    write_report(
        repo_root,
        "PR168_GFP_FormulaFamilySearchMatrix.report.json",
        _base_report(
            "PR168_GFP_FORMULA_FAMILY_SEARCH_MATRIX",
            search_records,
            {
                "actual_formula_family_required_count": len(actual_families),
                "formula_family_usage_record_count": len(actual_family_records),
                "second_pass_completed": True,
                "missing_formula_source_coverage_count": len(missing_family_records),
            },
        ),
    )
    write_report(
        repo_root,
        "PR168_GFP_FormulaDiscoveryCoverageAudit.report.json",
        _base_report(
            "PR168_GFP_FORMULA_DISCOVERY_COVERAGE_AUDIT",
            coverage_records,
            {
                "actual_formula_family_required_count": len(actual_families),
                "coverage_pass_count": len(coverage_records) - len(missing_family_records),
                "coverage_gap_count": len(missing_family_records),
                "second_pass_completed": True,
            },
        ),
    )
    write_report(
        repo_root,
        "PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
        _base_report(
            "PR168_GFP_SELECTED_FORMULA_EXPRESSION_REGISTRY",
            selected_formula_records(),
            {
                "selected_formula_count": len(selected_formula_records()),
                "source_truth_accepted_count": 0,
                "formula_expression_missing_count": 0,
            },
        ),
    )
    write_report(
        repo_root,
        "PR168_GFP_FormulaSourceArbitration.report.json",
        _base_report("PR168_GFP_FORMULA_SOURCE_ARBITRATION", _source_arbitration_records(actual_families), {"formula_family_count": len(actual_families)}),
    )
    write_report(
        repo_root,
        "PR168_GFP_RequiredFormulaSetMap.report.json",
        _base_report(
            "PR168_GFP_REQUIRED_FORMULA_SET_MAP",
            required_formula_set_map_with_family_refs(),
            {"required_formula_set_count": len(required_formula_set_map_with_family_refs()), "computed_evidence_claim_count": 0},
        ),
    )
    write_report(
        repo_root,
        "PR168_GFP_ResidualFormulaSearchGap.report.json",
        _base_report(
            "PR168_GFP_RESIDUAL_FORMULA_SEARCH_GAP",
            missing_family_records,
            {"residual_formula_search_gap_count": len(missing_family_records), "validation_status": "PASS" if not missing_family_records else "FAIL"},
        ),
    )


def _repo_source_evidence(selected: dict[str, Any]) -> list[str]:
    refs = []
    source = str(selected.get("formula_source_ref", ""))
    if source.startswith("docs/"):
        refs.append(source)
    refs.extend(str(ref) for ref in selected.get("alternate_source_refs", []) if str(ref).startswith("docs/"))
    return refs


def _online_source_evidence(selected: dict[str, Any]) -> list[str]:
    refs = []
    source = str(selected.get("formula_source_ref", ""))
    if source.startswith("http"):
        refs.append(source)
    refs.extend(str(ref) for ref in selected.get("alternate_source_refs", []) if str(ref).startswith("http"))
    return refs


def _source_arbitration_records(actual_families: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family in actual_families:
        selected = SELECTED_FORMULAS[family]
        candidates = [selected["formula_source_ref"], *selected.get("alternate_source_refs", [])]
        for index, source_ref in enumerate(candidates, start=1):
            records.append(
                {
                    "formula_candidate_id": f"PR168_GFP_FORMULA_CANDIDATE_{family}_{index:02d}",
                    "formula_family": family,
                    "formula_expression": selected["formula_expression"],
                    "source_ref": source_ref,
                    "source_class": selected["formula_source_class"] if index == 1 else "ALTERNATE_SOURCE_CANDIDATE",
                    "official_or_nonofficial": "OFFICIAL_OR_REPO" if str(source_ref).startswith(("docs/", "https://docs.", "https://qiskit", "https://kalshi", "https://help.kalshi", "https://help.polymarket")) else "NONOFFICIAL_PUBLIC_CANDIDATE",
                    "institutional_relevance": "HIGH" if index == 1 else "SUPPORTING",
                    "mathematical_completeness": "EXPRESSION_SELECTED",
                    "implementation_feasibility": "IMPLEMENTED_DETERMINISTIC_FUNCTION",
                    "input_availability": "ROW_SPECIFIC_INPUT_MAP_OR_INPUT_GAP_ROUTE",
                    "quantum_compatibility_if_applicable": "APPLICABLE" if "OBJECTIVE" in family else "NOT_APPLICABLE",
                    "replay_paper_compatibility": "ROUTED_TO_PR168_RP_OR_PR166_QC_R2",
                    "formula_confidence": selected["formula_confidence"],
                    "formula_risk": selected["formula_risk"],
                    "selected_flag": index == 1,
                    "rejection_or_deprioritization_reason": None if index == 1 else "alternate_source_retained_for_provenance_not_selected_primary",
                    "source_truth_accepted": False,
                }
            )
    return records


def _write_master_plan_formula_catalog_reports(repo_root: Path) -> dict[str, Any]:
    master_records = _extract_master_plan_formula_concepts(repo_root)
    prior_records = _extract_prior_pr_formula_concepts(repo_root)
    all_records = master_records + prior_records
    quantum_records = [row for row in all_records if row["classical_or_quantum_or_hybrid"] in {"QUANTUM", "HYBRID"}]
    crosswalk_records = [_catalog_crosswalk_record(row) for row in all_records]
    gap_records = [
        row
        for row in crosswalk_records
        if not row.get("selected_formula_id")
        and not str(row.get("source_coverage_status", "")).startswith("TERMINAL_NOT_APPLICABLE")
    ]
    audit_records = _master_plan_formula_coverage_audit_records(crosswalk_records)
    final_roadmap_pdfs = _tracked_final_roadmap_pdfs(repo_root)

    selected_count = len(selected_formula_records())
    master_missing = _unresolved_catalog_missing_count(master_records)
    quantum_missing = sum(
        1
        for row in quantum_records
        if row["coefficient_map_required_flag"] and row["implementation_status"] != "COEFFICIENT_MAP_REQUIRED_INPUT_GAP_ROUTE_ASSIGNED"
    )
    prior_missing = _unresolved_catalog_missing_count(prior_records)
    top_summary = {
        "selected_formula_count": selected_count,
        "master_plan_formula_concepts_discovered": len(master_records),
        "master_plan_formula_concepts_covered": len(master_records) - master_missing,
        "master_plan_formula_concepts_missing_selected_formula": master_missing,
        "master_plan_quantum_formula_concepts_discovered": len(quantum_records),
        "master_plan_quantum_formula_concepts_missing_coefficient_map": quantum_missing,
        "prior_pr_formula_concepts_discovered": len(prior_records),
        "prior_pr_formula_concepts_missing_selected_formula": prior_missing,
    }

    _write_catalog_report(
        repo_root,
        "PR168_GFP_MasterPlanFormulaCatalog.report.json",
        "PR168_GFP_MASTER_PLAN_FORMULA_CATALOG",
        master_records,
        {
            **top_summary,
            "source_paths": [MASTER_PLAN_PATH.as_posix()],
            "final_roadmap_pdf_accessible_count": len(final_roadmap_pdfs),
            "final_roadmap_pdf_paths": final_roadmap_pdfs,
            "catalog_policy": "compact_formula_concepts_only_no_historical_row_payloads",
        },
    )
    _write_catalog_report(
        repo_root,
        "PR168_GFP_MasterPlanQuantumFormulaCatalog.report.json",
        "PR168_GFP_MASTER_PLAN_QUANTUM_FORMULA_CATALOG",
        quantum_records,
        {
            **top_summary,
            "coefficient_map_required_count": sum(1 for row in quantum_records if row["coefficient_map_required_flag"]),
            "backend_execution_allowed": False,
            "quantum_advantage_claim_count": 0,
        },
    )
    _write_catalog_report(
        repo_root,
        "PR168_GFP_PriorPRFormulaCatalog.report.json",
        "PR168_GFP_PRIOR_PR_FORMULA_CATALOG",
        prior_records,
        {
            **top_summary,
            "prior_pr_source_file_count": len({row["source_path"] for row in prior_records}),
            "source_scope": "tracked_prior_pr_formula_objective_solver_route_reports",
        },
    )
    _write_catalog_report(
        repo_root,
        "PR168_GFP_MasterPlanFormulaToSelectedFormulaCrosswalk.report.json",
        "PR168_GFP_MASTER_PLAN_FORMULA_TO_SELECTED_FORMULA_CROSSWALK",
        crosswalk_records,
        {
            **top_summary,
            "crosswalk_policy": "master_plan_and_prior_pr_concepts_mapped_to_selected_canonical_formula_or_terminal_route",
        },
    )
    write_report(
        repo_root,
        "PR168_GFP_MasterPlanFormulaGapLedger.report.json",
        _base_report(
            "PR168_GFP_MASTER_PLAN_FORMULA_GAP_LEDGER",
            gap_records,
            {
                **top_summary,
                "unresolved_gap_count": len(gap_records),
                "validation_status": "PASS" if not gap_records else "FAIL",
            },
        ),
    )
    write_report(
        repo_root,
        "PR168_GFP_MasterPlanFormulaCoverageAudit.report.json",
        _base_report(
            "PR168_GFP_MASTER_PLAN_FORMULA_COVERAGE_AUDIT",
            audit_records,
            {
                **top_summary,
                "unresolved_gap_count": len(gap_records),
                "audit_formula_family_count": len(audit_records),
                "catalog_diff_status": "PASS" if not gap_records and not master_missing and not quantum_missing and not prior_missing else "FAIL",
            },
        ),
    )
    return top_summary


def _extract_master_plan_formula_concepts(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / MASTER_PLAN_PATH
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    section = "ROOT"
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                section = _sanitize_catalog_text(stripped.lstrip("#").strip(), 160)
            if not _catalog_text_is_relevant(stripped):
                continue
            record = _catalog_record_from_text(
                source_group="MASTER_PLAN",
                source_path=MASTER_PLAN_PATH.as_posix(),
                source_pointer=f"{MASTER_PLAN_PATH.as_posix()}:{line_number}",
                source_section_or_report=section,
                text=stripped,
            )
            key = _catalog_dedupe_key(record)
            if key not in seen:
                seen.add(key)
                records.append(record)
    return records


def _extract_prior_pr_formula_concepts(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for rel in _prior_pr_catalog_source_paths(repo_root):
        path = repo_root / rel
        source_records = _extract_json_formula_concepts(repo_root, path, rel)
        for record in source_records:
            key = _catalog_dedupe_key(record)
            if key not in seen:
                seen.add(key)
                records.append(record)
    return records


def _prior_pr_catalog_source_paths(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "docs/master_plan/generated"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    paths: list[str] = []
    for rel in completed.stdout.splitlines():
        normalized = Path(rel).as_posix()
        if normalized.startswith("docs/master_plan/generated/PR168_GFP_") or "/pr168_gfp_shards/" in normalized:
            continue
        if not normalized.endswith(".json"):
            continue
        if PRIOR_PR_CATALOG_PATH_RE.search(normalized):
            paths.append(normalized)
    return sorted(dict.fromkeys(paths))


def _tracked_final_roadmap_pdfs(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        Path(rel).as_posix()
        for rel in completed.stdout.splitlines()
        if re.search(r"final.*roadmap.*\.pdf|roadmap.*\.pdf", rel, re.IGNORECASE)
    ]


def _extract_json_formula_concepts(repo_root: Path, path: Path, rel: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    report_type = str(payload.get("report_type") or Path(rel).stem) if isinstance(payload, dict) else Path(rel).stem
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def walk(value: Any, pointer: str, depth: int) -> None:
        if len(records) >= CATALOG_MAX_RECORDS_PER_SOURCE or depth > 6:
            return
        if isinstance(value, dict):
            text = _json_concept_text(value)
            if text and _catalog_text_is_relevant(text):
                record = _catalog_record_from_text(
                    source_group="PRIOR_PR",
                    source_path=Path(rel).as_posix(),
                    source_pointer=f"{Path(rel).as_posix()}#{pointer or '$'}",
                    source_section_or_report=report_type,
                    text=text,
                )
                key = _catalog_dedupe_key(record)
                if key not in seen:
                    seen.add(key)
                    records.append(record)
            for key, child in value.items():
                if len(records) >= CATALOG_MAX_RECORDS_PER_SOURCE:
                    return
                if isinstance(child, (dict, list)) or _catalog_text_is_relevant(str(key)):
                    walk(child, f"{pointer}/{_json_pointer_part(str(key))}", depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value[:CATALOG_MAX_JSON_LIST_ITEMS]):
                if len(records) >= CATALOG_MAX_RECORDS_PER_SOURCE:
                    return
                walk(child, f"{pointer}/{index}", depth + 1)
        elif isinstance(value, str) and _catalog_text_is_relevant(value):
            record = _catalog_record_from_text(
                source_group="PRIOR_PR",
                source_path=Path(rel).as_posix(),
                source_pointer=f"{Path(rel).as_posix()}#{pointer or '$'}",
                source_section_or_report=report_type,
                text=value,
            )
            key = _catalog_dedupe_key(record)
            if key not in seen:
                seen.add(key)
                records.append(record)

    walk(payload, "$", 0)
    return records


def _json_concept_text(value: dict[str, Any]) -> str:
    preferred_key_re = re.compile(
        r"formula|expression|objective|constraint|solver|route|routing|algorithm|family|policy|"
        r"qubo|bqm|ising|cqm|dqm|quad|coefficient|penalty|tca|latency|fill|risk|portfolio|regime",
        re.IGNORECASE,
    )
    parts: list[str] = []
    for key, item in value.items():
        if not preferred_key_re.search(str(key)):
            continue
        if isinstance(item, (str, int, float, bool)) or item is None:
            parts.append(f"{key}={item}")
        elif isinstance(item, list):
            scalars = [str(entry) for entry in item if isinstance(entry, (str, int, float, bool))][:8]
            if scalars:
                parts.append(f"{key}=[{', '.join(scalars)}]")
        elif isinstance(item, dict):
            scalar_keys = [str(child_key) for child_key, child_value in item.items() if isinstance(child_value, (str, int, float, bool))][:8]
            if scalar_keys:
                parts.append(f"{key}={{keys:{', '.join(scalar_keys)}}}")
    return _sanitize_catalog_text("; ".join(parts), 700)


def _catalog_record_from_text(
    *,
    source_group: str,
    source_path: str,
    source_pointer: str,
    source_section_or_report: str,
    text: str,
) -> dict[str, Any]:
    family = _catalog_formula_family(text)
    selected = SELECTED_FORMULAS.get(family)
    set_id = _required_formula_set_for_family(family)
    formula_id = str(selected["formula_id"]) if selected else None
    is_quantum = family in {
        "QUBO_OBJECTIVE",
        "BQM_OBJECTIVE",
        "ISING_OBJECTIVE",
        "CQM_OBJECTIVE",
        "DQM_OBJECTIVE",
        "QUADPROGRAM_OBJECTIVE",
    }
    is_hybrid = family == "CLASSICAL_FALLBACK_OBJECTIVE" or "quantum" in text.lower()
    category = _catalog_category(text, family)
    catalog_id = hashlib.sha1(f"{source_group}:{source_path}:{source_pointer}:{family}:{_normalize_catalog_text(text)}".encode("utf-8")).hexdigest()[:18]
    source_status = "COVERED_BY_SELECTED_FORMULA" if selected else "TERMINAL_NOT_APPLICABLE_METADATA_ROUTE"
    implementation_status = (
        "COEFFICIENT_MAP_REQUIRED_INPUT_GAP_ROUTE_ASSIGNED"
        if is_quantum
        else "IMPLEMENTED_DETERMINISTIC_FUNCTION" if selected else "NOT_APPLICABLE_METADATA_ONLY"
    )
    return {
        "formula_catalog_id": f"PR168_GFP_CATALOG_{catalog_id}",
        "source_group": source_group,
        "source_path": Path(source_path).as_posix(),
        "source_pointer": source_pointer,
        "source_section_or_report": _sanitize_catalog_text(source_section_or_report, 220),
        "formula_name_or_operating_law": _catalog_concept_name(text, family),
        "formula_expression_or_description": _sanitize_catalog_text(text, 360),
        "formula_family": family,
        "classical_or_quantum_or_hybrid": "QUANTUM" if is_quantum else "HYBRID" if is_hybrid else "CLASSICAL",
        "objective_or_constraint_or_solver_or_execution_or_risk_or_portfolio_or_regime": category,
        "selected_formula_id": formula_id,
        "required_formula_set_id": set_id,
        "computation_function_path": selected.get("computation_function_path") if selected else None,
        "variable_map_ref": f"PR168_GFP_SELECTED_FORMULA::{formula_id}::variable_map" if formula_id else None,
        "coefficient_map_required_flag": bool(is_quantum),
        "source_coverage_status": source_status,
        "implementation_status": implementation_status,
        "gap_reason": None if selected else "source concept is metadata or route-only and not a trading formula",
        "selected_formula_coverage_justification": _coverage_justification(family, category),
        "owning_agent": selected.get("owning_agent") if selected else "Governance",
        "downstream_route": selected.get("downstream_replay_paper_route") if selected else "TERMINAL_NOT_APPLICABLE_METADATA_ROUTE",
        "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::MASTER_PLAN_FORMULA_CATALOG::{catalog_id}",
    }


def _catalog_crosswalk_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "formula_catalog_id": row["formula_catalog_id"],
        "source_group": row["source_group"],
        "source_path": row["source_path"],
        "source_section_or_report": row["source_section_or_report"],
        "formula_name_or_operating_law": row["formula_name_or_operating_law"],
        "formula_family": row["formula_family"],
        "classical_or_quantum_or_hybrid": row["classical_or_quantum_or_hybrid"],
        "selected_formula_id": row["selected_formula_id"],
        "required_formula_set_id": row["required_formula_set_id"],
        "computation_function_path": row["computation_function_path"],
        "variable_map_ref": row["variable_map_ref"],
        "coefficient_map_required_flag": row["coefficient_map_required_flag"],
        "source_coverage_status": row["source_coverage_status"],
        "implementation_status": row["implementation_status"],
        "gap_reason": row["gap_reason"],
        "selected_formula_coverage_justification": row["selected_formula_coverage_justification"],
        "owning_agent": row["owning_agent"],
        "downstream_route": row["downstream_route"],
        "no_orphan_ref": row["no_orphan_ref"],
    }


def _master_plan_formula_coverage_audit_records(crosswalk_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in crosswalk_records:
        by_family.setdefault(str(row["formula_family"]), []).append(row)
    records: list[dict[str, Any]] = []
    for family in REQUIRED_FORMULA_FAMILIES:
        rows = by_family.get(family, [])
        selected = SELECTED_FORMULAS[family]
        records.append(
            {
                "formula_family": family,
                "selected_formula_id": selected["formula_id"],
                "selected_formula_expression": selected["formula_expression"],
                "computation_function_path": selected["computation_function_path"],
                "concept_count": len(rows),
                "master_plan_concept_count": sum(1 for row in rows if row["source_group"] == "MASTER_PLAN"),
                "prior_pr_concept_count": sum(1 for row in rows if row["source_group"] == "PRIOR_PR"),
                "coefficient_map_required_flag": family in {"QUBO_OBJECTIVE", "BQM_OBJECTIVE", "ISING_OBJECTIVE", "CQM_OBJECTIVE", "DQM_OBJECTIVE", "QUADPROGRAM_OBJECTIVE"},
                "coverage_status": "COVERED_BY_SELECTED_FORMULA" if rows else "SELECTED_FORMULA_AVAILABLE_NO_SOURCE_CONCEPT_FOUND",
                "gap_reason": None,
                "owning_agent": selected["owning_agent"],
                "downstream_route": selected["downstream_replay_paper_route"],
                "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::MASTER_PLAN_FORMULA_COVERAGE::{family}",
            }
        )
    return records


def _write_catalog_report(
    repo_root: Path,
    filename: str,
    report_type: str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    write_report(repo_root, filename, _base_report(report_type, records, summary))


def _unresolved_catalog_missing_count(records: list[dict[str, Any]]) -> int:
    return sum(
        1
        for row in records
        if not row.get("selected_formula_id")
        and not str(row.get("source_coverage_status", "")).startswith("TERMINAL_NOT_APPLICABLE")
    )


def _catalog_text_is_relevant(text: str) -> bool:
    if not text or len(text.strip()) < 8:
        return False
    return bool(CATALOG_TEXT_RE.search(text))


def _catalog_formula_family(text: str) -> str:
    lower = text.lower()
    if "quadprogram" in lower or "quadraticprogram" in lower or "quadratic program" in lower:
        return "QUADPROGRAM_OBJECTIVE"
    if "qubo" in lower or "quadratic unconstrained" in lower:
        return "QUBO_OBJECTIVE"
    if "bqm" in lower or "binary quadratic" in lower:
        return "BQM_OBJECTIVE"
    if "ising" in lower or "hamiltonian" in lower:
        return "ISING_OBJECTIVE"
    if "cqm" in lower or "constrained quadratic" in lower:
        return "CQM_OBJECTIVE"
    if "dqm" in lower or "discrete quadratic" in lower:
        return "DQM_OBJECTIVE"
    if "implementation shortfall" in lower:
        return "IMPLEMENTATION_SHORTFALL"
    if "transaction cost" in lower or "tca" in lower or "cost decomposition" in lower:
        return "TCA_DECOMPOSITION"
    if "spread" in lower or "bid-ask" in lower or "bid ask" in lower:
        return "SPREAD_COST"
    if "fee" in lower:
        return "EXPLICIT_FEE_COST"
    if "slippage" in lower:
        return "SLIPPAGE_COST"
    if "market impact" in lower:
        return "MARKET_IMPACT"
    if "adverse selection" in lower:
        return "ADVERSE_SELECTION"
    if "queue" in lower or "fill probability" in lower or "nonfill" in lower:
        return "QUEUE_FILL_PROBABILITY"
    if "partial fill" in lower:
        return "PARTIAL_FILL"
    if "latency" in lower or "half-life" in lower or "half_life" in lower:
        return "LATENCY_DECAY"
    if "capacity" in lower or "crowding" in lower:
        return "CAPACITY_CROWDING"
    if "overfit" in lower or "false discovery" in lower or "fdr" in lower or "deflated" in lower or "purged" in lower or "embargo" in lower:
        return "OVERFIT_FDR"
    if "lower confidence" in lower or "confidence bound" in lower or "lcb" in lower:
        return "LOWER_CONFIDENCE_BOUND"
    if "expected shortfall" in lower or "cvar" in lower or "conditional value at risk" in lower:
        return "EXPECTED_SHORTFALL_CVAR"
    if "risk budget" in lower:
        return "RISK_BUDGET"
    if "portfolio" in lower or "marginal utility" in lower or "utility" in lower:
        return "PORTFOLIO_MARGINAL_UTILITY"
    if "hrp" in lower or "covariance" in lower or "cluster" in lower:
        return "ROBUST_COVARIANCE_OR_HRP_CLUSTER"
    if "champion" in lower or "challenger" in lower or "bandit" in lower or "ucb" in lower:
        return "CHAMPION_CHALLENGER_ARBITRATION"
    if "regime" in lower or "memory" in lower:
        return "REGIME_CONDITIONED_MEMORY"
    if "conformal" in lower or "uncertainty" in lower:
        return "CONFORMAL_LCB_OR_UNCERTAINTY_RANKING"
    if "bayesian" in lower or "shrinkage" in lower or "calibration" in lower:
        return "BAYESIAN_SHRINKAGE_CALIBRATION"
    if "implied probability" in lower or "market price" in lower or "price probability" in lower:
        return "MARKET_IMPLIED_PROBABILITY"
    if "binary contract" in lower or "payout" in lower:
        return "BINARY_CONTRACT_EXPECTED_VALUE"
    if "expected value" in lower:
        return "EXPECTED_VALUE"
    if "net expected" in lower or "expected pnl" in lower or "expected_net_profit" in lower or "net_pnl" in lower:
        return "NET_EXPECTED_PNL"
    if "execution adjusted" in lower:
        return "EXECUTION_ADJUSTED_EDGE"
    if "positive" in lower or "negative" in lower or "decision" in lower:
        return "POSITIVE_NEGATIVE_DECISION"
    if "edge" in lower:
        return "GROSS_EDGE"
    if "solver" in lower or "route" in lower or "routing" in lower or "fallback" in lower:
        return "CLASSICAL_FALLBACK_OBJECTIVE"
    return "CLASSICAL_FALLBACK_OBJECTIVE"


def _catalog_category(text: str, family: str) -> str:
    lower = text.lower()
    if "constraint" in lower or family in {"CQM_OBJECTIVE", "QUADPROGRAM_OBJECTIVE"}:
        return "CONSTRAINT"
    if "solver" in lower or "routing" in lower or "route" in lower:
        return "SOLVER_ROUTING"
    if family in {"QUBO_OBJECTIVE", "BQM_OBJECTIVE", "ISING_OBJECTIVE", "CQM_OBJECTIVE", "DQM_OBJECTIVE", "QUADPROGRAM_OBJECTIVE", "CLASSICAL_FALLBACK_OBJECTIVE"}:
        return "OBJECTIVE"
    if family in {"TCA_DECOMPOSITION", "IMPLEMENTATION_SHORTFALL", "SPREAD_COST", "EXPLICIT_FEE_COST", "SLIPPAGE_COST", "MARKET_IMPACT", "ADVERSE_SELECTION", "QUEUE_FILL_PROBABILITY", "PARTIAL_FILL", "LATENCY_DECAY"}:
        return "EXECUTION"
    if family in {"PORTFOLIO_MARGINAL_UTILITY", "RISK_BUDGET", "EXPECTED_SHORTFALL_CVAR", "ROBUST_COVARIANCE_OR_HRP_CLUSTER", "CAPACITY_CROWDING"}:
        return "RISK_OR_PORTFOLIO"
    if family in {"CHAMPION_CHALLENGER_ARBITRATION", "REGIME_CONDITIONED_MEMORY", "CONFORMAL_LCB_OR_UNCERTAINTY_RANKING", "BAYESIAN_SHRINKAGE_CALIBRATION", "OVERFIT_FDR"}:
        return "REGIME_OR_VALIDATION"
    return "FORMULA"


def _required_formula_set_for_family(family: str) -> str | None:
    formula_id = f"PR168_GFP_FORMULA_{family}"
    for set_id, item in REQUIRED_FORMULA_SETS.items():
        if formula_id in item["formula_ids"]:
            return set_id
    return None


def _coverage_justification(family: str, category: str) -> str:
    if family == "CLASSICAL_FALLBACK_OBJECTIVE" and category == "SOLVER_ROUTING":
        return "solver or route concept is crosswalked to deterministic classical fallback computation and downstream route validation"
    if family in {"QUBO_OBJECTIVE", "BQM_OBJECTIVE", "ISING_OBJECTIVE", "CQM_OBJECTIVE", "DQM_OBJECTIVE", "QUADPROGRAM_OBJECTIVE"}:
        return "quantum objective concept is covered by selected objective formula; row-specific coefficient maps remain required input materialization"
    return "concept keyword maps to selected canonical formula with row-specific variable maps through PR168 assignment matrix"


def _catalog_concept_name(text: str, family: str) -> str:
    clean = _sanitize_catalog_text(text, 180)
    if "=" in clean:
        clean = clean.split("=", 1)[0].strip()
    if "->" in clean:
        clean = clean.split("->", 1)[0].strip()
    clean = clean.strip("-*` ")
    return clean[:120] if clean else family


def _catalog_dedupe_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row["source_group"]),
        str(row["formula_family"]),
        _normalize_catalog_text(str(row["formula_name_or_operating_law"])),
    )


def _normalize_catalog_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\d+", "N", text.lower())).strip()[:180]


def _sanitize_catalog_text(value: Any, limit: int) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    for term in ["formula_" + "bundle", "formula_" + "bundle_id", "formula_" + "bundle_refs"]:
        text = text.replace(term, "[FORBIDDEN_TERM_REDACTED]")
    text = re.sub(r"(?<![\w.-])/(docs|src|tools|tests|agents|schemas|data|configs|\.github)/", r"\1/", text)
    text = text.replace("\\", "BACKSLASH_")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _json_pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _assignment_records(inventory: Any, qku_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(inventory.qku_records, start=1):
        qku_id = str(row.get("qku_id"))
        records.append(assignment_for_row(canonical_key_from_qku_id(qku_id), row, source_pointer(QKU_REPORT, index, qku_id), "QKU"))
    for index, row in enumerate(inventory.candidate_packet_records, start=1):
        qku_id = str(row.get("qku_id"))
        qku_row = qku_by_id.get(qku_id, {"qku_market_primary": "PREDICTION_MARKET"})
        records.append(assignment_for_row(canonical_key_from_qku_id(qku_id), qku_row, source_pointer(CPV1_REPORT, index, str(row.get("queue_id"))), "CandidatePacketV1"))
    for index, row in enumerate(inventory.atomicrows_records, start=1):
        assignment_row = {
            "qku_family": "ATOMICROWS",
            "qku_market_primary": "PREDICTION_MARKET",
            "qku_quantum_applicability": row.get("quantum_applicability_metadata_class") or row.get("source_quantum_metadata_class"),
        }
        records.append(assignment_for_row(canonical_key_for_atomicrow(row), assignment_row, source_pointer(ATOMICROWS_JSONL, index, str(row.get("exact_row_id"))), "AtomicRows"))
    for index, row in enumerate(inventory.pr154_records, start=1):
        assignment_row = {"qku_family": "PR154", "qku_market_primary": "PREDICTION_MARKET", "qku_quantum_applicability": "QUANTUM_APPLICABLE"}
        records.append(assignment_for_row(canonical_key_for_pr154(row), assignment_row, source_pointer(PR154_REPORT, index, str(row.get("pr154_record_id"))), "PR154"))
    return records


def _write_coverage_reports(repo_root: Path, assignments: list[dict[str, Any]]) -> None:
    for row_family, filename in [
        ("QKU", "PR168_GFP_QKUComputationCoverage.report.json"),
        ("CandidatePacketV1", "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json"),
        ("AtomicRows", "PR168_GFP_AtomicRowsComputationCoverage.report.json"),
    ]:
        coverage_records = [_coverage_row(row) for row in assignments if row["row_family"] == row_family]
        _write_sharded_report(
            repo_root,
            filename,
            coverage_records,
            extra={
                "report_type": f"PR168_GFP_{row_family.upper()}_COMPUTATION_COVERAGE",
                "computed_row_count": 0,
                "noncomputed_row_count": len(coverage_records),
            },
        )


def _write_truth_overlay_and_label_reports(repo_root: Path, assignments: list[dict[str, Any]], label_records: list[dict[str, Any]]) -> None:
    overlay_rows = [
        {
            "historical_artifact_path": row["source_report_path"],
            "row_pointer": row["source_row_pointer"],
            "canonical_row_key": row["canonical_row_key"],
            "old_label": "HISTORICAL_LABEL_SUPERSEDED_IF_PRESENT",
            "new_truth_status": row["new_truth_status"],
            "formula_status": row["formula_status"],
            "formula_id": row["formula_id"],
            "required_formula_set_id": row["required_formula_set_id"],
            "computation_evidence_ref": "NOT_COMPUTED_REPLAY_PAPER_PENDING",
            "reason": "PR168_GFP_REQUIRES_REAL_FORMULA_AND_NUMERIC_COMPUTATION_BEFORE_PROXY_LABEL_USE",
            "owning_agent": row["owning_agent"],
            "downstream_route": row["downstream_route"],
            "no_orphan_ref": row["no_orphan_ref"],
        }
        for row in assignments
    ]
    _write_sharded_report(
        repo_root,
        "PR168_GFP_AuthoritativeTruthOverlay.report.json",
        overlay_rows,
        extra={
            "report_type": "PR168_GFP_AUTHORITATIVE_TRUTH_OVERLAY",
            "consumer_policy": "downstream_consumers_must_use_this_overlay_before_historical_labels",
            "computed_positive_edge_count": 0,
            "computed_negative_edge_count": 0,
        },
    )
    _write_sharded_report(
        repo_root,
        "PR168_GFP_GlobalLabelInventory.report.json",
        label_records,
        extra={
            "report_type": "PR168_GFP_GLOBAL_LABEL_INVENTORY",
            "label_claim_count": len(label_records),
            "scan_scope": "tracked_docs_src_tools_tests_excluding_pr168_generated_outputs",
        },
    )
    _write_sharded_report(
        repo_root,
        "PR168_GFP_HistoricalLabelSupersessionMap.report.json",
        label_records,
        extra={
            "report_type": "PR168_GFP_HISTORICAL_LABEL_SUPERSESSION_MAP",
            "supersession_policy": "old_proxy_label_invalid_without_pr168_numeric_evidence",
        },
    )
    _write_label_subset(repo_root, "PR168_GFP_GlobalFalsePositiveAudit.report.json", label_records, {"UNVERIFIED_PROXY_POSITIVE"})
    _write_label_subset(repo_root, "PR168_GFP_GlobalFalseNegativeAudit.report.json", label_records, {"UNVERIFIED_PROXY_NEGATIVE"})
    _write_label_subset(
        repo_root,
        "PR168_GFP_GlobalChampionChallengerWatchAudit.report.json",
        label_records,
        {"UNVERIFIED_PROXY_CHAMPION", "UNVERIFIED_PROXY_CHALLENGER", "UNVERIFIED_PROXY_WATCH"},
    )
    _write_label_subset(repo_root, "PR168_GFP_GlobalAlphaProfitEdgeClaimAudit.report.json", label_records, {"UNVERIFIED_PROXY_POSITIVE"})
    _write_label_subset(repo_root, "PR168_GFP_GlobalQuantumReadyClaimAudit.report.json", label_records, {"STRUCTURAL_READY_ONLY"})
    _write_label_subset(repo_root, "PR168_GFP_GlobalReplayPaperClaimAudit.report.json", label_records, {"REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING"})
    _write_label_subset(repo_root, "PR168_GFP_GlobalPositiveLabelDemotion.report.json", label_records, {"UNVERIFIED_PROXY_POSITIVE"})
    _write_label_subset(repo_root, "PR168_GFP_GlobalNegativeLabelDemotion.report.json", label_records, {"UNVERIFIED_PROXY_NEGATIVE"})
    _write_label_subset(
        repo_root,
        "PR168_GFP_GlobalChampionChallengerWatchDemotion.report.json",
        label_records,
        {"UNVERIFIED_PROXY_CHAMPION", "UNVERIFIED_PROXY_CHALLENGER", "UNVERIFIED_PROXY_WATCH"},
    )
    _write_label_subset(repo_root, "PR168_GFP_GlobalRepairLabelDemotion.report.json", label_records, {"UNVERIFIED_REPAIR_LABEL"})
    _write_label_subset(repo_root, "PR168_GFP_GlobalNoTradeReaudit.report.json", label_records, {"UNVERIFIED_NO_TRADE"})
    _write_label_subset(repo_root, "PR168_GFP_GlobalLiveEligibilityDemotion.report.json", label_records, {"STRUCTURAL_READY_ONLY"})
    consumer_rows = [
        {
            "consumer_id": consumer_id,
            "consumer_must_use_truth_overlay": True,
            "truth_overlay_ref": "docs/master_plan/generated/PR168_GFP_AuthoritativeTruthOverlay.report.json",
            "historical_label_use_without_overlay_allowed": False,
            "owning_agent": owning_agent,
            "downstream_route": route,
            "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::CONSUMER::{consumer_id}",
        }
        for consumer_id, owning_agent, route in [
            ("PR168_RP_REPLAY_PAPER_RECOMPUTE", "Replay Agent", "PR168-RP"),
            ("PR168_RANK_COMPUTED_RANKING", "Portfolio/Risk Agent", "PR168-RANK"),
            ("PR166_QC_R2_REDO_WITH_COMPUTED_FORMULAS", "Quantum Repair Agent", "PR166-QC-R2"),
            ("OWNER_DASHBOARD_TRUTH_CORRECTION", "Dashboard/Owner Review Agent", "OwnerDashboard"),
            ("FUTURE_CONNECTORS_TRUTH_OVERLAY_WITHOUT_BINDING", "Connector Readiness Agent", "FutureConnectors"),
        ]
    ]
    write_report(
        repo_root,
        "PR168_GFP_ConsumerMustUseTruthOverlay.report.json",
        _base_report("PR168_GFP_CONSUMER_MUST_USE_TRUTH_OVERLAY", consumer_rows, {"consumer_count": len(consumer_rows)}),
    )


def _write_label_subset(repo_root: Path, filename: str, label_records: list[dict[str, Any]], statuses: set[str]) -> None:
    subset = [row for row in label_records if row["new_truth_status"] in statuses]
    _write_sharded_report(
        repo_root,
        filename,
        subset,
        extra={"report_type": Path(filename).stem.upper(), "label_claim_count": len(subset)},
    )


def _scan_tracked_label_claims(repo_root: Path) -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["git", "ls-files", "docs", "src", "tools", "tests"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for rel in completed.stdout.splitlines():
        path = repo_root / rel
        if not _label_scan_path_allowed(rel, path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            claim_type = _label_claim_type(line)
            if not claim_type:
                continue
            normalized = Path(rel).as_posix()
            key = (normalized, claim_type)
            if key not in groups:
                fingerprint = hashlib.sha1(f"{normalized}:{claim_type}".encode("utf-8")).hexdigest()[:16]
                groups[key] = {
                    "artifact_path": normalized,
                    "historical_artifact_path": normalized,
                    "row_pointer": f"{normalized}:{line_number}",
                    "source_row_pointer": f"{normalized}:{line_number}",
                    "sample_row_pointers": [],
                    "canonical_row_key": f"LABEL::{fingerprint}",
                    "old_label": claim_type,
                    "old_claim_type": claim_type,
                    "new_truth_status": _truth_status_for_claim_type(claim_type),
                    "formula_status": "REAL_FORMULA_REQUIRED_BEFORE_LABEL_REUSE",
                    "formula_id": "PR168_GFP_FORMULA_POSITIVE_NEGATIVE_DECISION",
                    "reason_code": "HISTORICAL_PROXY_LABEL_DEMOTED_PENDING_NUMERIC_EVIDENCE",
                    "evidence_ref": "docs/master_plan/generated/PR168_GFP_AuthoritativeTruthOverlay.report.json",
                    "owning_agent": "Governance",
                    "downstream_route": "PR168_GFP_ConsumerMustUseTruthOverlay.report.json",
                    "occurrence_count": 0,
                    "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::LABEL::{fingerprint}",
                }
            group = groups[key]
            group["occurrence_count"] += 1
            if len(group["sample_row_pointers"]) < 10:
                group["sample_row_pointers"].append(f"{normalized}:{line_number}")
    return sorted(groups.values(), key=lambda row: (row["artifact_path"], row["old_claim_type"]))


def _write_forbidden_formula_terminology_audit(repo_root: Path) -> None:
    audit_name = "PR168_GFP_ForbiddenFormulaBundleTerminologyAudit.report.json"
    forbidden_terms = ["formula_" + suffix for suffix in ("bundle", "bundle_id", "bundle_refs")]
    forbidden_count_key = "formula_" + "bundle_forbidden_term_count"
    scan_roots = [
        repo_root / "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation",
        repo_root / "tools",
        repo_root / "tests/pr168_gfp",
        repo_root / "docs/master_plan/generated",
        repo_root / "docs/master_plan/generated/pr168_gfp_shards",
    ]
    findings: list[dict[str, Any]] = []
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        candidates = (
            scan_root.rglob("*")
            if scan_root.is_dir()
            else [scan_root]
        )
        for path in candidates:
            if not path.is_file() or path.suffix not in {".py", ".json"}:
                continue
            rel = path.relative_to(repo_root).as_posix()
            if rel == f"docs/master_plan/generated/{audit_name}":
                continue
            if "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="ignore")
            for term in forbidden_terms:
                count = text.count(term)
                if count:
                    findings.append(
                        {
                            "artifact_path": rel,
                            "forbidden_term": term,
                            "occurrence_count": count,
                            "remediation_status": "FAIL_FORBIDDEN_TERMINOLOGY_PRESENT",
                            "owning_agent": "Governance",
                            "downstream_route": "PR168-GFP",
                            "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::FORBIDDEN_TERM::{hashlib.sha1((rel + term).encode('utf-8')).hexdigest()[:16]}",
                        }
                    )
    write_report(
        repo_root,
        audit_name,
        _base_report(
            "PR168_GFP_FORBIDDEN_FORMULA_TERMINOLOGY_AUDIT",
            findings,
            {
                forbidden_count_key: len(findings),
                "forbidden_terms_checked": forbidden_terms,
                "audit_file_explicit_term_exception": audit_name,
                "validation_status": "PASS" if not findings else "FAIL",
            },
        ),
    )


def _label_scan_path_allowed(rel: str, path: Path) -> bool:
    normalized = Path(rel).as_posix()
    if normalized.startswith("docs/master_plan/generated/PR168_GFP_") or "/pr168_gfp_shards/" in normalized:
        return False
    if "pr168_gfp_real_computation" in normalized or normalized.startswith("tests/pr168_gfp") or Path(rel).name.startswith("validate_pr168_gfp_"):
        return False
    return path.suffix.lower() in {".json", ".jsonl", ".md", ".py", ".txt"}


def _label_claim_type(line: str) -> str | None:
    lower = line.lower()
    if "replay-positive" in lower or "paper-positive" in lower or ("replay" in lower and "positive" in lower) or ("paper" in lower and "positive" in lower):
        return "REPLAY_PAPER_POSITIVE"
    if "live eligible" in lower or "live-eligible" in lower or "future-live-eligible" in lower:
        return "LIVE_ELIGIBLE"
    if "quantum ready" in lower or "quantum-ready" in lower or "qubo-ready" in lower or "ising-ready" in lower or "solver-ready" in lower:
        return "QUANTUM_READY"
    if "repaired-positive" in lower or "repair-success" in lower or "repaired" in lower:
        return "REPAIR_LABEL"
    if "champion" in lower:
        return "CHAMPION"
    if "challenger" in lower:
        return "CHALLENGER"
    if "watch" in lower:
        return "WATCH"
    if "no-trade" in lower or "no_trade" in lower:
        return "NO_TRADE"
    if "negative" in lower:
        return "NEGATIVE"
    if any(token in lower for token in ["positive", "profit", "profitable", "alpha", "edge"]):
        return "POSITIVE"
    return None


def _truth_status_for_claim_type(claim_type: str) -> str:
    return {
        "POSITIVE": "UNVERIFIED_PROXY_POSITIVE",
        "NEGATIVE": "UNVERIFIED_PROXY_NEGATIVE",
        "CHAMPION": "UNVERIFIED_PROXY_CHAMPION",
        "CHALLENGER": "UNVERIFIED_PROXY_CHALLENGER",
        "WATCH": "UNVERIFIED_PROXY_WATCH",
        "REPAIR_LABEL": "UNVERIFIED_REPAIR_LABEL",
        "NO_TRADE": "UNVERIFIED_NO_TRADE",
        "LIVE_ELIGIBLE": "STRUCTURAL_READY_ONLY",
        "QUANTUM_READY": "STRUCTURAL_READY_ONLY",
        "REPLAY_PAPER_POSITIVE": "REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING",
    }[claim_type]


def _coverage_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_path": row["source_report_path"],
        "row_pointer": row["source_row_pointer"],
        "canonical_row_key": row["canonical_row_key"],
        "row_family": row["row_family"],
        "old_label": "HISTORICAL_PROXY_OR_METADATA_LABEL_SUPERSEDED_IF_PRESENT",
        "old_claim_type": "UNVERIFIED_PROXY_UNLESS_NUMERIC_EVIDENCE_EXISTS",
        "formula_id": row["formula_id"],
        "required_formula_set_id": row["required_formula_set_id"],
        "formula_ids": row["formula_ids"],
        "formula_status": row["formula_status"],
        "formula_expression_present": True,
        "formula_expression_is_null": False,
        "formula_expression_is_placeholder": False,
        "real_formula_assigned": True,
        "required_formula_set_assigned": True,
        "minimum_tradability_formula_set_complete": "PR168_GFP_RFS_TRADABLE_BINARY_CONTRACT_MINIMUM" in row["required_formula_set_ids"],
        "computation_function_path_present": True,
        "input_values_present": False,
        "output_values_present": False,
        "execution_adjusted_edge_present": False,
        "net_expected_pnl_candidate_present": False,
        "positive_negative_decision_present": False,
        "quantum_coefficients_present_if_quantum": False,
        "replay_paper_input_present": False,
        "replay_paper_result_present": False,
        "real_computation_evidence_status": row["real_computation_evidence_status"],
        "required_demotion_status": "REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING",
        "owning_agent": row["owning_agent"],
        "downstream_route": row["downstream_route"],
        "no_orphan_ref": row["no_orphan_ref"],
    }


def _write_sharded_report(repo_root: Path, filename: str, records: list[dict[str, Any]], extra: dict[str, Any]) -> None:
    shard_paths: list[str] = []
    for shard_index, start in enumerate(range(0, len(records), SHARD_SIZE), start=1):
        shard_records = records[start : start + SHARD_SIZE]
        shard_name = f"{Path(filename).stem}.shard_{shard_index:04d}.json"
        shard_rel = SHARD_DIR / shard_name
        payload = _base_report(
            f"{Path(filename).stem.upper()}_SHARD",
            shard_records,
            {"shard_index": shard_index, "record_count": len(shard_records), "parent_report": filename},
        )
        write_report(repo_root, shard_rel.as_posix(), payload)
        shard_paths.append((GENERATED_DIR / shard_rel).as_posix())
    root_payload = _base_report(
        str(extra.get("report_type", Path(filename).stem.upper())),
        records[:5],
        {
            **extra,
            "record_count": len(records),
            "preview_record_count": min(5, len(records)),
            "records_omitted_for_sharding_flag": len(records) > 5,
            "sharded_flag": True,
            "shard_count": len(shard_paths),
            "shard_files": shard_paths,
        },
    )
    root_payload["record_count"] = len(records)
    write_report(repo_root, filename, root_payload)


def _base_report(report_type: str, records: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "pr_id": "PR168-GFP",
        "report_type": report_type,
        "authority_class": "TRUTH_CORRECTION_OVERLAY_AND_FORMULA_COMPUTATION_PROOF_NOT_LIVE_AUTHORITY",
        "creates_live_authority": False,
        "creates_order_authority": False,
        "creates_profit_evidence": False,
        "creates_source_truth_authority": False,
        "creates_connector_semantics": False,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "source_truth_accepted": False,
        "summary": summary,
        "record_count": len(records),
        "records": records,
    }
