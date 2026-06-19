"""Focused validators for PR168-GFP generated proof reports."""

from __future__ import annotations

import importlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

GENERATED_DIR = Path("docs/master_plan/generated")
COMPUTED_STATUSES = {"COMPUTED_POSITIVE_EDGE", "COMPUTED_NEGATIVE_EDGE", "COMPUTED_NEUTRAL_OR_ZERO_EDGE"}
MAX_PR168_SHARD_FILES = 250
MAX_COMPACT_REPORT_RECORDS = 25000
REQUIRED_FORMULA_FIELDS = (
    "formula_id",
    "formula_family",
    "formula_expression",
    "formula_source_ref",
    "formula_source_class",
    "computation_function_path",
    "computation_function_name",
    "variable_map",
    "input_schema",
    "output_schema",
)
HIGH_RISK_FORMULA_IDS = (
    "PR168_GFP_FORMULA_CHAMPION_CHALLENGER_ARBITRATION",
    "PR168_GFP_FORMULA_ROBUST_COVARIANCE_OR_HRP_CLUSTER",
    "PR168_GFP_FORMULA_SLIPPAGE_COST",
    "PR168_GFP_FORMULA_SPREAD_COST",
    "PR168_GFP_FORMULA_BINARY_CONTRACT_EXPECTED_VALUE",
    "PR168_GFP_FORMULA_MARKET_IMPLIED_PROBABILITY",
    "PR168_GFP_FORMULA_OVERFIT_FDR",
    "PR168_GFP_FORMULA_PARTIAL_FILL",
    "PR168_GFP_FORMULA_CLASSICAL_FALLBACK_OBJECTIVE",
    "PR168_GFP_FORMULA_QUBO_OBJECTIVE",
    "PR168_GFP_FORMULA_BQM_OBJECTIVE",
    "PR168_GFP_FORMULA_ISING_OBJECTIVE",
    "PR168_GFP_FORMULA_CQM_OBJECTIVE",
    "PR168_GFP_FORMULA_DQM_OBJECTIVE",
    "PR168_GFP_FORMULA_QUADPROGRAM_OBJECTIVE",
)
EXPECTED_HIGH_RISK_FUNCTIONS = {
    "PR168_GFP_FORMULA_CHAMPION_CHALLENGER_ARBITRATION": "champion_challenger_score",
    "PR168_GFP_FORMULA_ROBUST_COVARIANCE_OR_HRP_CLUSTER": "robust_covariance_or_hrp_cluster",
    "PR168_GFP_FORMULA_SLIPPAGE_COST": "slippage_cost",
    "PR168_GFP_FORMULA_SPREAD_COST": "spread_cost",
    "PR168_GFP_FORMULA_BINARY_CONTRACT_EXPECTED_VALUE": "binary_contract_expected_value",
    "PR168_GFP_FORMULA_MARKET_IMPLIED_PROBABILITY": "market_implied_probability",
    "PR168_GFP_FORMULA_OVERFIT_FDR": "overfit_fdr_penalty",
    "PR168_GFP_FORMULA_PARTIAL_FILL": "partial_fill_penalty",
    "PR168_GFP_FORMULA_CLASSICAL_FALLBACK_OBJECTIVE": "compute_classical_fallback_solution",
    "PR168_GFP_FORMULA_QUBO_OBJECTIVE": "build_qubo_objective",
    "PR168_GFP_FORMULA_BQM_OBJECTIVE": "build_bqm_objective",
    "PR168_GFP_FORMULA_ISING_OBJECTIVE": "build_ising_objective",
    "PR168_GFP_FORMULA_CQM_OBJECTIVE": "build_cqm_objective",
    "PR168_GFP_FORMULA_DQM_OBJECTIVE": "build_dqm_objective",
    "PR168_GFP_FORMULA_QUADPROGRAM_OBJECTIVE": "build_quadprogram_objective",
}


class ValidationError(RuntimeError):
    pass


def run_validation(repo_root: Path, mode: str) -> None:
    if mode == "baseline_count_reconcile":
        validate_baseline_counts(repo_root)
    elif mode == "formula_assignment_coverage":
        validate_formula_assignment_coverage(repo_root)
    elif mode == "real_formula_computation":
        validate_real_formula_computation(repo_root)
    elif mode == "qku_computation_coverage":
        validate_coverage_report(repo_root, "PR168_GFP_QKUComputationCoverage.report.json", 9360, "QKU")
    elif mode == "candidate_packet_v1_coverage":
        validate_coverage_report(repo_root, "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json", 6502, "CandidatePacketV1")
    elif mode == "atomicrows_computation_coverage":
        validate_coverage_report(repo_root, "PR168_GFP_AtomicRowsComputationCoverage.report.json", 4183, "AtomicRows")
    elif mode == "formula_source_arbitration":
        validate_formula_source_coverage(repo_root)
    elif mode == "formula_registry_integrity":
        validate_formula_registry_integrity(repo_root)
    elif mode == "master_plan_formula_catalog_diff":
        validate_master_plan_formula_catalog_diff(repo_root)
    elif mode == "minimum_tradability_formula_set":
        validate_required_formula_sets(repo_root)
    elif mode == "forbidden_bundle_terminology":
        validate_forbidden_formula_terms(repo_root)
    elif mode == "report_compactness":
        validate_report_compactness(repo_root)
    elif mode == "no_fake_positive_negative_labels":
        validate_no_fake_computed_labels(repo_root)
    elif mode == "quantum_objective_coefficients":
        validate_quantum_formula_registry(repo_root)
    elif mode == "metadata_placeholder_demotions":
        validate_no_metadata_only_computed_rows(repo_root)
    elif mode == "truth_overlay_required":
        validate_truth_overlay_required(repo_root)
    elif mode == "authority_boundaries":
        validate_authority_boundaries(repo_root)
    elif mode == "no_orphan_lineage":
        validate_no_orphan_refs(repo_root)
    else:
        raise ValidationError(f"unknown PR168-GFP validation mode: {mode}")


def validate_baseline_counts(repo_root: Path) -> None:
    count_report = _read_report(repo_root, "PR168_GFP_QKUBaselineCountReconcile.report.json")
    records = count_report["records"]
    by_name = {row["count_name"]: row for row in records}
    _expect(by_name["historical_master_qku_count"]["actual_repo_count"] == 9360, "historical master QKU count mismatch")
    _expect(by_name["residual_qku_count"]["actual_repo_count"] == 4835, "residual QKU count mismatch")
    _expect(by_name["atomicrows_count"]["actual_repo_count"] == 4183, "AtomicRows count mismatch")
    _expect(by_name["pr154_item_count"]["actual_repo_count"] == 342, "PR154 item count mismatch")
    _expect(by_name["current_candidate_packet_v1_count"]["actual_repo_count"] == 6502, "CandidatePacketV1 count mismatch")
    _expect(by_name["historical_equation"]["actual_repo_count"] == 9360, "historical equation mismatch")
    historical = _read_report(repo_root, "PR168_GFP_Historical9360VsCurrent6502Reconcile.report.json")["records"][0]
    _expect(historical["overlap_by_canonical_row_key_count"] == 6502, "operational candidate overlap mismatch")
    _expect(historical["operational_only_count"] == 0, "CandidatePacketV1 row outside historical QKU baseline")


def validate_formula_assignment_coverage(repo_root: Path) -> None:
    registry = _formula_registry(repo_root)
    required_sets = _required_formula_sets(repo_root)
    assignments = _read_sharded_records(repo_root, "PR168_GFP_FormulaAssignmentMatrix.report.json")
    _expect(len(assignments) == 20387, f"formula assignment row count mismatch: {len(assignments)}")
    family_report = _read_report(repo_root, "PR168_GFP_FormulaDiscoveryCoverageAudit.report.json")
    _expect(family_report["summary"]["coverage_gap_count"] == 0, "formula discovery coverage gap exists")

    for row in assignments:
        _validate_assignment_row(row, registry, required_sets)


def validate_real_formula_computation(repo_root: Path) -> None:
    registry = _formula_registry(repo_root)
    for formula_id, row in registry.items():
        _expect(row.get("formula_expression"), f"{formula_id} missing formula_expression")
        _expect(row.get("formula_source_ref"), f"{formula_id} missing formula_source_ref")
        _expect(row.get("variable_map"), f"{formula_id} missing variable_map")
        _expect(row.get("computation_function_path"), f"{formula_id} missing computation_function_path")
        _expect(Path(row["computation_function_path"]).exists(), f"{formula_id} computation function path does not exist")
    for filename in [
        "PR168_GFP_QKUComputationCoverage.report.json",
        "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
        "PR168_GFP_AtomicRowsComputationCoverage.report.json",
    ]:
        for row in _read_sharded_records(repo_root, filename):
            _validate_computation_row(row)


def validate_coverage_report(repo_root: Path, filename: str, expected_count: int, row_family: str) -> None:
    report = _read_report(repo_root, filename)
    _expect(report["record_count"] == expected_count, f"{filename} record_count mismatch")
    rows = _read_sharded_records(repo_root, filename)
    _expect(len(rows) == expected_count, f"{filename} shard row count mismatch")
    for row in rows:
        _expect(row["row_family"] == row_family, f"{filename} wrong row family")
        _expect(row.get("canonical_row_key"), f"{filename} row missing canonical_row_key")
        _expect(row.get("formula_id") or row.get("required_formula_set_id"), f"{filename} row missing formula assignment")
        _expect(row.get("no_orphan_ref"), f"{filename} row missing no_orphan_ref")
        _validate_computation_row(row)


def validate_formula_source_coverage(repo_root: Path) -> None:
    search = _read_report(repo_root, "PR168_GFP_FormulaFamilySearchMatrix.report.json")
    coverage = _read_report(repo_root, "PR168_GFP_FormulaDiscoveryCoverageAudit.report.json")
    arbitration = _read_report(repo_root, "PR168_GFP_FormulaSourceArbitration.report.json")
    _expect(search["summary"]["second_pass_completed"] is True, "second formula-source pass not recorded")
    _expect(search["summary"]["missing_formula_source_coverage_count"] == 0, "formula source coverage gap exists")
    _expect(coverage["summary"]["coverage_gap_count"] == 0, "coverage audit gap exists")
    selected_by_family = {row["formula_family"] for row in arbitration["records"] if row.get("selected_flag")}
    actual_families = {row["formula_family"] for row in search["records"]}
    _expect(actual_families == selected_by_family, "source arbitration missing selected formula family")
    for row in search["records"]:
        _expect(row["repo_source_evidence"] or row["online_formula_source_evidence"], f"{row['formula_family']} lacks source evidence")
        _expect(row["selected_formula_expression"], f"{row['formula_family']} lacks selected expression")
        _expect(row["formula_source_ref"], f"{row['formula_family']} lacks source ref")
        _expect(row["variable_map"], f"{row['formula_family']} lacks variable map")
        _expect(row["computation_function_path"], f"{row['formula_family']} lacks computation function path")


def audit_formula_registry_integrity(repo_root: Path) -> dict[str, Any]:
    report_path = repo_root / GENERATED_DIR / "PR168_GFP_SelectedFormulaExpressionRegistry.report.json"
    invalid_json_count = 0
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        invalid_json_count = 1
        report = {"records": []}

    records = report.get("records", [])
    malformed_formula_ids: set[str] = set()
    missing_required_fields: dict[str, list[str]] = {}
    truncated_or_missing_schema_count = 0
    variable_schema_mismatch_count = 0
    function_name_mismatch_count = 0
    high_risk_issues: list[str] = []

    formula_ids: list[str] = []
    for index, row in enumerate(records):
        formula_id = f"__malformed_row_{index}"
        if not isinstance(row, dict):
            malformed_formula_ids.add(formula_id)
            continue
        formula_id = str(row.get("formula_id") or formula_id)
        formula_ids.append(formula_id)

        missing_fields = [field for field in REQUIRED_FORMULA_FIELDS if not row.get(field)]
        if missing_fields:
            missing_required_fields[formula_id] = missing_fields
            malformed_formula_ids.add(formula_id)

        variable_map = row.get("variable_map")
        input_schema = row.get("input_schema")
        output_schema = row.get("output_schema")
        if not isinstance(variable_map, dict) or not variable_map or not isinstance(input_schema, dict) or not input_schema or not isinstance(output_schema, dict) or not output_schema:
            truncated_or_missing_schema_count += 1
            malformed_formula_ids.add(formula_id)
        elif set(variable_map) != set(input_schema):
            variable_schema_mismatch_count += 1
            malformed_formula_ids.add(formula_id)

        try:
            _resolve_formula_callable(repo_root, row)
        except ValidationError:
            function_name_mismatch_count += 1
            malformed_formula_ids.add(formula_id)

        if formula_id in HIGH_RISK_FORMULA_IDS:
            row_issues = _high_risk_formula_issues(row)
            if row_issues:
                high_risk_issues.extend(row_issues)
                malformed_formula_ids.add(formula_id)

    duplicate_formula_id_count = sum(count - 1 for count in Counter(formula_ids).values() if count > 1)
    fallback_lazy_catch_all_count = _fallback_lazy_catch_all_count(repo_root)
    partial_fill_ratio_used_as_penalty_count = _partial_fill_ratio_used_as_penalty_count(records)
    required_set_computed_evidence_count = _required_set_computed_evidence_count(repo_root)
    binary_ev_unit_contract_status = _binary_ev_unit_contract_status(records)

    malformed_count = len(malformed_formula_ids) + invalid_json_count
    status = "PASS"
    if (
        malformed_count
        or duplicate_formula_id_count
        or variable_schema_mismatch_count
        or function_name_mismatch_count
        or high_risk_issues
        or fallback_lazy_catch_all_count
        or partial_fill_ratio_used_as_penalty_count
        or required_set_computed_evidence_count
        or binary_ev_unit_contract_status != "PASS_NET_PROFIT_EXCLUDING_RETURNED_STAKE"
    ):
        status = "FAIL"

    return {
        "formula_registry_integrity_status": status,
        "selected_formula_count": len(records) if isinstance(records, list) else 0,
        "malformed_formula_row_count": malformed_count,
        "formula_ids_missing_required_fields": sorted(missing_required_fields),
        "missing_required_field_details": missing_required_fields,
        "duplicate_formula_id_count": duplicate_formula_id_count,
        "formula_rows_with_invalid_json_count": invalid_json_count,
        "formula_rows_with_truncated_or_missing_schema_count": truncated_or_missing_schema_count,
        "high_risk_formula_issue_count": len(high_risk_issues),
        "high_risk_formula_issues": sorted(high_risk_issues),
        "function_name_mismatch_count": function_name_mismatch_count,
        "formula_variable_schema_mismatch_count": variable_schema_mismatch_count,
        "fallback_lazy_catch_all_count": fallback_lazy_catch_all_count,
        "partial_fill_ratio_used_as_penalty_count": partial_fill_ratio_used_as_penalty_count,
        "required_formula_set_computed_evidence_count": required_set_computed_evidence_count,
        "binary_ev_unit_contract_status": binary_ev_unit_contract_status,
    }


def validate_formula_registry_integrity(repo_root: Path) -> None:
    audit = audit_formula_registry_integrity(repo_root)
    _expect(audit["formula_registry_integrity_status"] == "PASS", json.dumps(audit, sort_keys=True))
    validate_forbidden_formula_terms(repo_root)


def validate_required_formula_sets(repo_root: Path) -> None:
    registry = _formula_registry(repo_root)
    for set_id, row in _required_formula_sets(repo_root).items():
        formula_ids = row.get("formula_ids", [])
        _expect(formula_ids, f"{set_id} lacks formula_id entries")
        _expect(row.get("required_formula_set_is_computed_evidence") is False, f"{set_id} treated as computed evidence")
        expression_refs = row.get("formula_expression_refs", [])
        _expect(len(expression_refs) == len(formula_ids), f"{set_id} formula_expression_refs count mismatch")
        for formula_id in formula_ids:
            _expect(formula_id in registry, f"{set_id} references unknown formula_id {formula_id}")
            _expect(registry[formula_id].get("formula_expression"), f"{formula_id} lacks formula_expression")


def validate_forbidden_formula_terms(repo_root: Path) -> None:
    forbidden = tuple("formula_" + suffix for suffix in ("bundle", "bundle_id", "bundle_refs"))
    audit_name = "PR168_GFP_ForbiddenFormulaBundleTerminologyAudit.report.json"
    forbidden_count_key = "formula_" + "bundle_forbidden_term_count"
    audit = _read_report(repo_root, audit_name)
    _expect(
        audit.get("summary", {}).get(forbidden_count_key) == 0,
        f"{audit_name} recorded forbidden terminology outside audit",
    )
    paths = [
        *Path(repo_root, "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation").rglob("*"),
        *Path(repo_root, "tools").glob("validate_pr168_gfp_*.py"),
        Path(repo_root, "tools/build_pr168_gfp_global_formula_discovery_real_computation.py"),
        *Path(repo_root, "tests/pr168_gfp").glob("*.py"),
        *Path(repo_root, "docs/master_plan/generated").glob("PR168_GFP_*.report.json"),
        *Path(repo_root, "docs/master_plan/generated/pr168_gfp_shards").glob("*.json"),
    ]
    for path in paths:
        if path.name == audit_name:
            continue
        if path.is_file() and path.suffix in {".py", ".json"} and "__pycache__" not in path.parts:
            text = path.read_text(encoding="utf-8")
            for term in forbidden:
                _expect(term not in text, f"forbidden term {term} found in {path}")


def validate_report_compactness(repo_root: Path) -> None:
    pr168_shards = list(Path(repo_root, "docs/master_plan/generated/pr168_gfp_shards").glob("PR168_GFP_*.json"))
    _expect(len(pr168_shards) <= MAX_PR168_SHARD_FILES, f"PR168-GFP shard output exploded: {len(pr168_shards)} files")
    for path in Path(repo_root, "docs/master_plan/generated").glob("PR168_GFP_*.report.json"):
        report = json.loads(path.read_text(encoding="utf-8"))
        _expect(report.get("record_count", 0) <= MAX_COMPACT_REPORT_RECORDS, f"{path.name} record_count exceeds compact limit")
        shard_count = int(report.get("summary", {}).get("shard_count", 0))
        _expect(shard_count <= MAX_PR168_SHARD_FILES, f"{path.name} shard_count exceeds compact limit")
    for filename in [
        "PR168_GFP_CanonicalRowKeyMap.report.json",
        "PR168_GFP_FormulaAssignmentMatrix.report.json",
        "PR168_GFP_QKUComputationCoverage.report.json",
        "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
        "PR168_GFP_AtomicRowsComputationCoverage.report.json",
        "PR168_GFP_AuthoritativeTruthOverlay.report.json",
        "PR168_GFP_GlobalLabelInventory.report.json",
        "PR168_GFP_HistoricalLabelSupersessionMap.report.json",
    ]:
        report = _read_report(repo_root, filename)
        _expect(report["summary"]["sharded_flag"] is True, f"{filename} not sharded")
        _expect(len(report["records"]) <= 5, f"{filename} root repeats too many rows")
        _expect(report["summary"]["record_count"] == report["record_count"], f"{filename} count mismatch")


def validate_no_fake_computed_labels(repo_root: Path) -> None:
    for filename in [
        "PR168_GFP_QKUComputationCoverage.report.json",
        "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
        "PR168_GFP_AtomicRowsComputationCoverage.report.json",
    ]:
        for row in _read_sharded_records(repo_root, filename):
            status = str(row.get("new_truth_status") or row.get("required_demotion_status") or "")
            _expect(status not in COMPUTED_STATUSES, f"{filename} has computed status without numeric evidence")
            old_label = str(row.get("old_label", "")).lower()
            if any(token in old_label for token in ["positive", "negative", "champion", "challenger", "watch", "profit", "alpha"]):
                _expect("proxy" in old_label or "superseded" in old_label, f"{filename} old proxy label not demoted")


def validate_quantum_formula_registry(repo_root: Path) -> None:
    registry = _formula_registry(repo_root)
    for formula_id in [
        "PR168_GFP_FORMULA_QUBO_OBJECTIVE",
        "PR168_GFP_FORMULA_BQM_OBJECTIVE",
        "PR168_GFP_FORMULA_ISING_OBJECTIVE",
        "PR168_GFP_FORMULA_CQM_OBJECTIVE",
        "PR168_GFP_FORMULA_DQM_OBJECTIVE",
        "PR168_GFP_FORMULA_QUADPROGRAM_OBJECTIVE",
    ]:
        row = registry[formula_id]
        expression = str(row["formula_expression"])
        _expect("coefficient" in json.dumps(row).lower() or "sum" in expression, f"{formula_id} lacks coefficient/objective expression")
        _expect(row["computation_function_path"].endswith("quantum_objectives.py"), f"{formula_id} wrong computation path")
    fallback = registry["PR168_GFP_FORMULA_CLASSICAL_FALLBACK_OBJECTIVE"]
    _expect("argmin_solution" in str(fallback["formula_expression"]), "classical fallback formula lacks deterministic objective expression")
    _expect(fallback["computation_function_path"].endswith("quantum_objectives.py"), "classical fallback wrong computation path")


def validate_no_metadata_only_computed_rows(repo_root: Path) -> None:
    for filename in [
        "PR168_GFP_QKUComputationCoverage.report.json",
        "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
        "PR168_GFP_AtomicRowsComputationCoverage.report.json",
    ]:
        for row in _read_sharded_records(repo_root, filename):
            _expect(row.get("real_formula_assigned") is True, f"{filename} metadata-only row not formula assigned")
            _expect(row.get("real_computation_evidence_status") != "METADATA_ONLY_COMPUTED", f"{filename} metadata-only computed row")


def validate_truth_overlay_required(repo_root: Path) -> None:
    overlay = _read_report(repo_root, "PR168_GFP_AuthoritativeTruthOverlay.report.json")
    _expect(overlay["record_count"] == 20387, "truth overlay does not cover every assigned row surface")
    _expect(overlay["summary"]["consumer_policy"] == "downstream_consumers_must_use_this_overlay_before_historical_labels", "truth overlay consumer policy missing")
    for row in _read_sharded_records(repo_root, "PR168_GFP_AuthoritativeTruthOverlay.report.json"):
        _expect(row.get("canonical_row_key"), "truth overlay row missing canonical key")
        _expect(row.get("new_truth_status") not in COMPUTED_STATUSES, "truth overlay computed status without evidence")
        _expect(row.get("formula_id"), "truth overlay row missing formula_id")
        _expect(row.get("required_formula_set_id"), "truth overlay row missing required formula set")
        _expect(row.get("no_orphan_ref"), "truth overlay row missing no_orphan_ref")
    consumers = _read_report(repo_root, "PR168_GFP_ConsumerMustUseTruthOverlay.report.json")
    _expect(consumers["record_count"] >= 5, "consumer truth overlay route count too low")
    for row in consumers["records"]:
        _expect(row["consumer_must_use_truth_overlay"] is True, "consumer can bypass truth overlay")
        _expect(row["historical_label_use_without_overlay_allowed"] is False, "consumer historical label bypass allowed")


def validate_authority_boundaries(repo_root: Path) -> None:
    for path in Path(repo_root, "docs/master_plan/generated").glob("PR168_GFP_*.report.json"):
        report = json.loads(path.read_text(encoding="utf-8"))
        for field in [
            "creates_live_authority",
            "creates_order_authority",
            "creates_profit_evidence",
            "creates_source_truth_authority",
            "creates_connector_semantics",
            "source_truth_accepted",
        ]:
            _expect(report.get(field) is False, f"{path.name} has forbidden authority field {field}")
        _expect(report.get("quantum_backend_execution_count") == 0, f"{path.name} quantum backend execution count nonzero")
        _expect(report.get("quantum_advantage_claim_count") == 0, f"{path.name} quantum advantage claim count nonzero")


def validate_no_orphan_refs(repo_root: Path) -> None:
    for filename in [
        "PR168_GFP_FormulaAssignmentMatrix.report.json",
        "PR168_GFP_QKUComputationCoverage.report.json",
        "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
        "PR168_GFP_AtomicRowsComputationCoverage.report.json",
    ]:
        for row in _read_sharded_records(repo_root, filename):
            _expect(row.get("no_orphan_ref"), f"{filename} row missing no_orphan_ref")


def validate_master_plan_formula_catalog_diff(repo_root: Path) -> None:
    required_reports = [
        "PR168_GFP_MasterPlanFormulaCatalog.report.json",
        "PR168_GFP_MasterPlanQuantumFormulaCatalog.report.json",
        "PR168_GFP_PriorPRFormulaCatalog.report.json",
        "PR168_GFP_MasterPlanFormulaToSelectedFormulaCrosswalk.report.json",
        "PR168_GFP_MasterPlanFormulaGapLedger.report.json",
        "PR168_GFP_MasterPlanFormulaCoverageAudit.report.json",
    ]
    reports = {name: _read_report(repo_root, name) for name in required_reports}
    coverage_summary = reports["PR168_GFP_MasterPlanFormulaCoverageAudit.report.json"]["summary"]
    _expect(coverage_summary["selected_formula_count"] == 35, "selected formula count changed")
    _expect(coverage_summary["master_plan_formula_concepts_discovered"] > 0, "no master plan formula concepts discovered")
    _expect(coverage_summary["master_plan_formula_concepts_covered"] > 0, "no master plan formula concepts covered")
    _expect(
        coverage_summary["master_plan_formula_concepts_missing_selected_formula"] == 0,
        "master plan formula concept missing selected formula without terminal route",
    )
    _expect(
        coverage_summary["master_plan_quantum_formula_concepts_discovered"] > 0,
        "no master plan quantum formula concepts discovered",
    )
    _expect(
        coverage_summary["master_plan_quantum_formula_concepts_missing_coefficient_map"] == 0,
        "master plan quantum formula concept missing coefficient-map route",
    )
    _expect(coverage_summary["prior_pr_formula_concepts_discovered"] > 0, "no prior PR formula concepts discovered")
    _expect(
        coverage_summary["prior_pr_formula_concepts_missing_selected_formula"] == 0,
        "prior PR formula concept missing selected formula without terminal route",
    )
    _expect(coverage_summary["catalog_diff_status"] == "PASS", "master plan formula catalog diff did not pass")

    gap_report = reports["PR168_GFP_MasterPlanFormulaGapLedger.report.json"]
    _expect(gap_report["summary"]["unresolved_gap_count"] == 0, "master plan formula gap ledger has unresolved gaps")
    _expect(gap_report["record_count"] == 0, "master plan formula gap ledger records unresolved gaps")

    registry = _formula_registry(repo_root)
    required_sets = _required_formula_sets(repo_root)
    crosswalk = _read_records_allow_shards(repo_root, "PR168_GFP_MasterPlanFormulaToSelectedFormulaCrosswalk.report.json")
    _expect(crosswalk, "master plan formula crosswalk is empty")
    for row in crosswalk:
        for field in [
            "formula_catalog_id",
            "source_path",
            "source_section_or_report",
            "formula_name_or_operating_law",
            "formula_family",
            "classical_or_quantum_or_hybrid",
            "selected_formula_id",
            "required_formula_set_id",
            "computation_function_path",
            "variable_map_ref",
            "coefficient_map_required_flag",
            "source_coverage_status",
            "implementation_status",
            "owning_agent",
            "downstream_route",
            "no_orphan_ref",
        ]:
            _expect(field in row, f"crosswalk row missing {field}")
        formula_id = str(row["selected_formula_id"])
        _expect(formula_id in registry, f"crosswalk references unknown formula {formula_id}")
        _expect(row["required_formula_set_id"] in required_sets, f"crosswalk references unknown required formula set {row['required_formula_set_id']}")
        _expect(row["computation_function_path"] == registry[formula_id]["computation_function_path"], f"{formula_id} computation path mismatch")
        _expect(row["variable_map_ref"], f"{formula_id} variable map ref missing")
        if row["coefficient_map_required_flag"]:
            _expect(
                row["implementation_status"] == "COEFFICIENT_MAP_REQUIRED_INPUT_GAP_ROUTE_ASSIGNED",
                f"{formula_id} coefficient-map route missing",
            )

    for filename in [
        "PR168_GFP_MasterPlanFormulaCatalog.report.json",
        "PR168_GFP_MasterPlanQuantumFormulaCatalog.report.json",
        "PR168_GFP_PriorPRFormulaCatalog.report.json",
    ]:
        for row in _read_records_allow_shards(repo_root, filename):
            _expect(row.get("selected_formula_id") or row.get("gap_reason"), f"{filename} row lacks formula or terminal reason")
            _expect(row.get("source_coverage_status"), f"{filename} row lacks source coverage status")


def _resolve_formula_callable(repo_root: Path, row: dict[str, Any]) -> Any:
    function_path = Path(str(row.get("computation_function_path", "")))
    full_path = repo_root / function_path
    _expect(full_path.exists(), f"{row.get('formula_id')} computation path missing: {function_path}")
    module_name = ".".join(function_path.with_suffix("").parts)
    function_name = str(row.get("computation_function_name", ""))
    module = importlib.import_module(module_name)
    function = getattr(module, function_name, None)
    _expect(callable(function), f"{row.get('formula_id')} computation function not callable: {function_name}")
    return function


def _high_risk_formula_issues(row: dict[str, Any]) -> list[str]:
    formula_id = str(row.get("formula_id"))
    issues: list[str] = []
    expected_function = EXPECTED_HIGH_RISK_FUNCTIONS.get(formula_id)
    if expected_function and row.get("computation_function_name") != expected_function:
        issues.append(f"{formula_id}:function_name_expected_{expected_function}")

    text = json.dumps(row, sort_keys=True).lower()
    expression = str(row.get("formula_expression", "")).lower()
    variable_map = row.get("variable_map") if isinstance(row.get("variable_map"), dict) else {}
    output_schema = row.get("output_schema") if isinstance(row.get("output_schema"), dict) else {}

    if formula_id == "PR168_GFP_FORMULA_CHAMPION_CHALLENGER_ARBITRATION":
        if row.get("computation_function_name") == "deflated_score_proxy":
            issues.append(f"{formula_id}:must_not_point_to_deflated_score_proxy")
        if "sqrt(log(total_trials)" not in expression:
            issues.append(f"{formula_id}:ucb_expression_missing")

    if formula_id == "PR168_GFP_FORMULA_OVERFIT_FDR":
        if "penalty" not in text or "proxy" not in text:
            issues.append(f"{formula_id}:must_be_labeled_penalty_proxy")

    if formula_id == "PR168_GFP_FORMULA_PARTIAL_FILL":
        if "partial_fill_penalty" not in output_schema or "1 -" not in expression:
            issues.append(f"{formula_id}:must_convert_fill_ratio_to_penalty")
        if row.get("computation_function_name") == "partial_fill":
            issues.append(f"{formula_id}:ratio_function_used_as_penalty")

    if formula_id == "PR168_GFP_FORMULA_SPREAD_COST":
        if "side_price" in expression and "side_price" not in variable_map:
            issues.append(f"{formula_id}:side_price_unmapped")
        if "side" not in variable_map:
            issues.append(f"{formula_id}:side_derivation_missing")

    if formula_id == "PR168_GFP_FORMULA_BINARY_CONTRACT_EXPECTED_VALUE":
        if _binary_ev_unit_contract_status([row]) != "PASS_NET_PROFIT_EXCLUDING_RETURNED_STAKE":
            issues.append(f"{formula_id}:payout_unit_contract_missing")

    if formula_id == "PR168_GFP_FORMULA_CLASSICAL_FALLBACK_OBJECTIVE":
        if row.get("computation_function_name") != "compute_classical_fallback_solution":
            issues.append(f"{formula_id}:fallback_function_mismatch")
        if "fallback" not in text or "argmin_solution" not in expression:
            issues.append(f"{formula_id}:fallback_only_contract_missing")

    if formula_id in {
        "PR168_GFP_FORMULA_QUBO_OBJECTIVE",
        "PR168_GFP_FORMULA_BQM_OBJECTIVE",
        "PR168_GFP_FORMULA_CQM_OBJECTIVE",
        "PR168_GFP_FORMULA_QUADPROGRAM_OBJECTIVE",
    }:
        for key in ("linear_coefficients", "quadratic_coefficients"):
            if key not in variable_map:
                issues.append(f"{formula_id}:{key}_missing")

    if formula_id == "PR168_GFP_FORMULA_ISING_OBJECTIVE":
        for key in ("h_coefficients", "j_coefficients", "spin_map"):
            if key not in variable_map:
                issues.append(f"{formula_id}:{key}_missing")

    if formula_id == "PR168_GFP_FORMULA_DQM_OBJECTIVE":
        for key in ("linear_case_coefficients", "quadratic_case_coefficients", "discrete_variable_map"):
            if key not in variable_map:
                issues.append(f"{formula_id}:{key}_missing")

    if formula_id == "PR168_GFP_FORMULA_ROBUST_COVARIANCE_OR_HRP_CLUSTER":
        if row.get("computation_function_name") != "robust_covariance_or_hrp_cluster":
            issues.append(f"{formula_id}:robust_covariance_function_mismatch")
        for key in ("sample_covariance", "target_covariance", "shrinkage", "cluster_var_left", "cluster_var_right"):
            if key not in variable_map:
                issues.append(f"{formula_id}:{key}_missing")

    return issues


def _fallback_lazy_catch_all_count(repo_root: Path) -> int:
    count = 0
    fallback_id = "PR168_GFP_FORMULA_CLASSICAL_FALLBACK_OBJECTIVE"
    for filename in [
        "PR168_GFP_MasterPlanFormulaCatalog.report.json",
        "PR168_GFP_PriorPRFormulaCatalog.report.json",
    ]:
        for row in _read_records_allow_shards(repo_root, filename):
            if row.get("selected_formula_id") != fallback_id:
                continue
            text = " ".join(
                str(row.get(field) or "").lower()
                for field in ("gap_reason", "selected_formula_coverage_justification")
            )
            if "no better formula" in text or "unresolved" in text or "missing selected formula" in text:
                count += 1
    return count


def _partial_fill_ratio_used_as_penalty_count(records: list[Any]) -> int:
    for row in records:
        if not isinstance(row, dict) or row.get("formula_id") != "PR168_GFP_FORMULA_PARTIAL_FILL":
            continue
        output_schema = row.get("output_schema") if isinstance(row.get("output_schema"), dict) else {}
        if row.get("computation_function_name") == "partial_fill" or "partial_fill_ratio" in output_schema:
            return 1
    return 0


def _required_set_computed_evidence_count(repo_root: Path) -> int:
    try:
        required_sets = _required_formula_sets(repo_root)
    except ValidationError:
        return 1
    return sum(1 for row in required_sets.values() if row.get("required_formula_set_is_computed_evidence") is not False)


def _binary_ev_unit_contract_status(records: list[Any]) -> str:
    for row in records:
        if not isinstance(row, dict) or row.get("formula_id") != "PR168_GFP_FORMULA_BINARY_CONTRACT_EXPECTED_VALUE":
            continue
        unit_contract = str(row.get("unit_contract", "")).lower()
        expression = str(row.get("formula_expression", "")).lower()
        if "net_profit" in unit_contract and "excluding_returned_stake" in unit_contract and "net profit" in expression:
            return "PASS_NET_PROFIT_EXCLUDING_RETURNED_STAKE"
        return "FAIL_BINARY_EV_UNIT_CONTRACT_AMBIGUOUS"
    return "FAIL_BINARY_EV_FORMULA_MISSING"


def _validate_assignment_row(row: dict[str, Any], registry: dict[str, dict[str, Any]], required_sets: dict[str, dict[str, Any]]) -> None:
    _expect(row.get("canonical_row_key"), "assignment row missing canonical_row_key")
    _expect(row.get("formula_id") or row.get("required_formula_set_id"), f"{row.get('canonical_row_key')} missing formula assignment")
    _expect(row.get("formula_ids"), f"{row.get('canonical_row_key')} missing formula_ids")
    _expect(row.get("required_formula_set_id") in required_sets, f"{row.get('canonical_row_key')} unknown required formula set")
    _expect(set(row["formula_ids"]).issubset(registry), f"{row.get('canonical_row_key')} unknown formula_id")
    _expect(row["formula_expression_ref_count"] == len(row["formula_ids"]), f"{row.get('canonical_row_key')} expression ref count mismatch")
    _expect(row["formula_source_ref_count"] == len(row["formula_ids"]), f"{row.get('canonical_row_key')} source ref count mismatch")
    _expect(row["variable_map_ref_count"] == len(row["formula_ids"]), f"{row.get('canonical_row_key')} variable map ref count mismatch")
    _expect(row["computation_function_path_ref_count"] == len(row["formula_ids"]), f"{row.get('canonical_row_key')} function path ref count mismatch")
    _expect(row.get("formula_status"), f"{row.get('canonical_row_key')} missing formula_status")
    _expect(row.get("owning_agent"), f"{row.get('canonical_row_key')} missing owning_agent")
    _expect(row.get("downstream_route"), f"{row.get('canonical_row_key')} missing downstream_route")
    _expect(row.get("no_orphan_ref"), f"{row.get('canonical_row_key')} missing no_orphan_ref")


def _validate_computation_row(row: dict[str, Any]) -> None:
    status = str(row.get("new_truth_status") or row.get("required_demotion_status") or "")
    if status in COMPUTED_STATUSES:
        for field in [
            "input_values_present",
            "output_values_present",
            "execution_adjusted_edge_present",
            "net_expected_pnl_candidate_present",
            "positive_negative_decision_present",
        ]:
            _expect(row.get(field) is True, f"{row.get('canonical_row_key')} computed row missing {field}")
    else:
        _expect(row.get("input_values_present") is False, f"{row.get('canonical_row_key')} noncomputed row has input values flag")
        _expect(row.get("output_values_present") is False, f"{row.get('canonical_row_key')} noncomputed row has output values flag")


def _formula_registry(repo_root: Path) -> dict[str, dict[str, Any]]:
    report = _read_report(repo_root, "PR168_GFP_SelectedFormulaExpressionRegistry.report.json")
    return {str(row["formula_id"]): row for row in report["records"]}


def _required_formula_sets(repo_root: Path) -> dict[str, dict[str, Any]]:
    report = _read_report(repo_root, "PR168_GFP_RequiredFormulaSetMap.report.json")
    return {str(row["required_formula_set_id"]): row for row in report["records"]}


def _read_report(repo_root: Path, filename: str) -> dict[str, Any]:
    path = repo_root / GENERATED_DIR / filename
    _expect(path.exists(), f"missing report {filename}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_sharded_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    report = _read_report(repo_root, filename)
    shard_files = report.get("summary", {}).get("shard_files", [])
    _expect(shard_files, f"{filename} missing shard_files")
    records: list[dict[str, Any]] = []
    for shard_file in shard_files:
        shard_path = repo_root / shard_file
        _expect(shard_path.exists(), f"missing shard {shard_file}")
        shard = json.loads(shard_path.read_text(encoding="utf-8"))
        records.extend(shard["records"])
    return records


def _read_records_allow_shards(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    report = _read_report(repo_root, filename)
    if report.get("summary", {}).get("shard_files"):
        return _read_sharded_records(repo_root, filename)
    return list(report.get("records", []))


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)
