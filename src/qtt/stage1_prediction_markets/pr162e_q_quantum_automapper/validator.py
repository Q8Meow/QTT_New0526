"""Validate PR162E-Q generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import FORBIDDEN_AUTHORITY_FLAGS, ZERO_AUTHORITY_KEYS
from .io import read_json, records_from_report_payload
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_companion_alignment_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_manifest_consistency_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_directory_entries_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_schema_records_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_schema_session_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import finite_float
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import is_finite_json_number_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import is_nonnegative_json_integer_v1
from .report_writer import schema_filename


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    schema_check = _report_schema_session_v1(repo_root, c, read_json, profile="MAPPER", schema_name=schema_filename)
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"MISSING_REPORT::{filename}")
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = _report_schema_records_v1(repo_root, payload, read_json, schema_check, filename)
    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))
    _validate_schemas(repo_root, payloads, failures)
    _validate_payload_contracts(payloads, records, failures)
    try:
        _report_manifest_consistency_v1(
            payloads, records, c.REPORT_FILENAMES,
            "PR162E_Q_ReportManifest.report.json", c.GENERATED_DIR, c.SCHEMA_DIR,
            style="ROOT_REFERENCE", schema_refs=None,
        )
    except SerializationSafetyError as exc:
        failures.append(str(exc))
    _validate_inputs(repo_root, records, failures)
    _validate_mapping_rows(records, failures)
    _validate_budget(records, failures)
    _validate_source_and_upstream(records, failures)
    _validate_recipe_contracts(records, failures)
    _validate_interpret_back_and_proofs(records, failures)
    _validate_mapping_projection_consistency_v1(records, failures)
    _validate_risk_execution_and_units(records, failures)
    _validate_routes_and_agents(records, failures)
    _validate_crosswalk_and_artifacts(records, failures)
    _validate_summary(records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(ok=not failures, failures=tuple(failures))


def _validate_schemas(repo_root: Path, payloads: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in payloads.items():
        schema_ref = payload.get("schema_ref")
        if not schema_ref:
            failures.append(f"MISSING_SCHEMA_REF::{filename}")
            continue
        if not (repo_root / c.SCHEMA_DIR / str(schema_ref)).exists():
            failures.append(f"MISSING_SCHEMA_FILE::{filename}::{schema_ref}")


def _validate_payload_contracts(
    payloads: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in payloads.items():
        if payload.get("roadmap_pr_id") != c.PR_ID:
            failures.append(f"BAD_ROADMAP_PR::{filename}")
        if payload.get("created_by_pr") != c.PR_ID:
            failures.append(f"BAD_CREATED_BY_PR::{filename}")
        if not is_nonnegative_json_integer_v1(payload.get("record_count")) or payload.get("record_count") != len(records[filename]):
            failures.append(f"BAD_RECORD_COUNT::{filename}")
        for key in ZERO_AUTHORITY_KEYS:
            if (not is_nonnegative_json_integer_v1(payload.get(key, 0)) or payload.get(key, 0) != 0):
                failures.append(f"PAYLOAD_FORBIDDEN_AUTHORITY_COUNT::{filename}::{key}")
        if filename in c.ROW_REPORTS and not payload.get("sharded_flag"):
            failures.append(f"ROW_REPORT_NOT_SHARDED::{filename}")


def _validate_inputs(repo_root: Path, records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    lineage_primary = None
    observed_input_counts: dict[str, int] = {}
    for filename in c.STRICT_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"MISSING_INPUT_REPORT::{filename}")
            continue
        payload = read_json(path)
        expanded = records_from_report_payload(repo_root, payload)
        observed_input_counts[filename] = len(expanded)
        if filename == 'PR166_QC_To_PR162E_Q.report.json':
            lineage_primary = expanded
        if filename in c.EXPECTED_559_INPUTS and len(expanded) != 559:
            failures.append(f"INPUT_COUNT_DRIFT::{filename}::{len(expanded)}")
    input_rows = records["PR162E_Q_InputConsumption.report.json"]
    if len(input_rows) != len(c.STRICT_INPUT_REPORTS):
        failures.append("INPUT_CONSUMPTION_ROW_COUNT_MISMATCH")
    for row in input_rows:
        if not row.get("record_count_matches_expected_flag"):
            failures.append(f"INPUT_EXPECTED_COUNT_FAIL::{row.get('source_report_ref')}")
        for flag in ("no_source_truth_acceptance_flag", "no_connector_binding_flag", "no_profit_evidence_flag", "no_backend_execution_flag"):
            if row.get(flag) is not True:
                failures.append(f"INPUT_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")

    observed_rows: set[str] = set()
    count_ledger_valid = True
    for row in input_rows:
        name = row.get("source_report_ref")
        actual = row.get("expanded_record_count")
        expected = row.get("expected_record_count")
        if type(name) is not str or name not in observed_input_counts or name in observed_rows:
            count_ledger_valid = False
            continue
        observed_rows.add(name)
        declared_expected = 559 if name in c.EXPECTED_559_INPUTS else observed_input_counts[name]
        if (
            type(actual) is not int or actual < 0 or actual != observed_input_counts[name]
            or type(expected) is not int or expected != declared_expected
            or row.get("record_count_matches_expected_flag") is not (actual == expected)
        ):
            count_ledger_valid = False
    if observed_rows != set(c.STRICT_INPUT_REPORTS) or not count_ledger_valid:
        failures.append("INPUT_CONSUMPTION_COUNT_MISMATCH")

    try:
        _report_companion_alignment_v1(
            lineage_primary, {name: records[name] for name in c.ROW_REPORTS}
        )
    except SerializationSafetyError:
        failures.append("INPUT_CANDIDATE_LINEAGE_MISMATCH")


def _validate_mapping_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    required = {
        "row_id",
        "source_pr",
        "upstream_pr166_qc_row_ref",
        "upstream_pr166_qb_row_ref",
        "upstream_pr166_q_row_ref",
        "qku_id",
        "qku_family",
        "formula_id",
        "algorithm_id",
        "parameter_stack_id",
        "execution_route_id",
        "market_scope",
        "stage1_prediction_market_flag",
        "future_market_portability_flag",
        "automapper_disposition",
        "mapping_quality_grade",
        "model_family_selected",
        "secondary_model_families",
        "formula_family_id",
        "objective_family_id",
        "canonical_objective_signature",
        "qubo_mappable_flag",
        "bqm_mappable_flag",
        "ising_mappable_flag",
        "cqm_mappable_flag",
        "dqm_mappable_flag",
        "quadratic_program_mappable_flag",
        "hybrid_mapping_flag",
        "objective_direction",
        "objective_terms",
        "objective_linear_terms",
        "objective_quadratic_terms",
        "decision_variables",
        "variable_domains",
        "constraints",
        "penalty_terms",
        "coefficient_scaling_status",
        "coefficient_dynamic_range",
        "unit_normalization_ref",
        "solution_interpret_back_ref",
        "test_vector_ref",
        "proof_vector_ref",
        "mapping_quality_score",
        "mapping_confidence_score",
        "edge_attribution_ref",
        "report_consumer_crosswalk_ref",
        "upstream_report_use_ref",
        "downstream_pr166_qc_retest_route_ref",
        "downstream_pr167_route_ref",
        "downstream_pr162e_route_ref",
        "downstream_pr162f_route_ref",
        "downstream_owner_dashboard_route_ref",
        "downstream_cloud_switchboard_route_ref",
        "downstream_future_connector_route_ref",
        "owning_agent_id",
        "reviewer_agent_id",
        "challenger_agent_id",
        "upstream_refs",
        "downstream_refs",
        "validation_refs",
        "no_orphan_proof_ref",
        "deterministic_sort_key",
    }
    for filename in c.ROW_REPORTS:
        rows = records[filename]
        if len(rows) != 559:
            failures.append(f"ROW_REPORT_COUNT_NOT_559::{filename}::{len(rows)}")
            continue
        seen: set[str] = set()
        for row in rows:
            row_id = str(row.get("row_id"))
            if row_id in seen:
                failures.append(f"DUPLICATE_ROW_ID::{filename}::{row_id}")
            seen.add(row_id)
            for key in required:
                if key not in row:
                    failures.append(f"REQUIRED_FIELD_MISSING::{filename}::{row_id}::{key}")
            disposition = row.get("automapper_disposition")
            if disposition not in c.AUTOMAPPER_DISPOSITIONS:
                failures.append(f"BAD_AUTOMAPPER_DISPOSITION::{filename}::{row_id}::{disposition}")
            if disposition in c.FORBIDDEN_AUTOMAPPER_DISPOSITIONS:
                failures.append(f"FORBIDDEN_AUTOMAPPER_DISPOSITION::{filename}::{row_id}::{disposition}")
            grade = row.get("mapping_quality_grade")
            if grade not in c.MAPPING_QUALITY_GRADES:
                failures.append(f"BAD_MAPPING_QUALITY_GRADE::{filename}::{row_id}::{grade}")
            if row.get("classical_fallback_available") is not True:
                failures.append(f"CLASSICAL_FALLBACK_MISSING::{filename}::{row_id}")
            if row.get("hot_path_allowed_flag") is not False:
                failures.append(f"HOT_PATH_ALLOWED::{filename}::{row_id}")
            if row.get("future_live_candidate_flag") is not False:
                failures.append(f"FUTURE_LIVE_CANDIDATE_TRUE::{filename}::{row_id}")
            _validate_authority(row, failures, filename, row_id)


def _validate_authority(row: dict[str, Any], failures: list[str], filename: str, row_id: str) -> None:
    for key in ZERO_AUTHORITY_KEYS:
        if (not is_nonnegative_json_integer_v1(row.get(key, 0)) or row.get(key, 0) != 0):
            failures.append(f"ROW_FORBIDDEN_AUTHORITY_COUNT::{filename}::{row_id}::{key}")
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        if row.get(flag) is not False:
            failures.append(f"ROW_FORBIDDEN_AUTHORITY_FLAG::{filename}::{row_id}::{flag}")
    if row.get("no_live_authority_flag") is not True:
        failures.append(f"NO_LIVE_AUTHORITY_FLAG_MISSING::{filename}::{row_id}")
    if row.get("profit_evidence_flag") is not False:
        failures.append(f"PROFIT_EVIDENCE_FLAG_TRUE::{filename}::{row_id}")


def _validate_budget(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    budget = records["PR162E_Q_MapBudget.report.json"][0]
    subset = [row for row in records["PR162E_Q_MapEligibility.report.json"] if row.get("actual_deep_mapping_subset_flag")]
    if len(subset) != budget.get("actual_deep_mapping_subset_size"):
        failures.append("DEEP_MAPPING_SUBSET_SIZE_MISMATCH")
    if len(subset) > c.MAP_CAPS["max_deep_mapping_rows_default_ci"]:
        failures.append("DEEP_MAPPING_SUBSET_CAP_EXCEEDED")
    for key, cap in c.MAP_CAPS.items():
        if budget.get(key) != cap:
            failures.append(f"MAP_CAP_VALUE_MISMATCH::{key}")
    per_family: dict[str, int] = {}
    for row in subset:
        family = str(row.get("model_family_selected"))
        per_family[family] = per_family.get(family, 0) + 1
    for family, count in per_family.items():
        if count > c.MAP_CAPS["max_rows_per_model_family_default_ci"]:
            failures.append(f"DEEP_MAPPING_FAMILY_CAP_EXCEEDED::{family}::{count}")
    if [row["deterministic_sort_key"] for row in subset] != sorted(row["deterministic_sort_key"] for row in subset):
        failures.append("DEEP_MAPPING_SUBSET_SORT_NOT_DETERMINISTIC")
    if budget.get("no_unbounded_mapping_execution_flag") is not True:
        failures.append("MAP_BUDGET_UNBOUNDED_FLAG_MISSING")


def _validate_source_and_upstream(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    sources = records["PR162E_Q_SourceMapParams.report.json"]
    if not any(row.get("official_flag") for row in sources):
        failures.append("SOURCE_MAP_OFFICIAL_SOURCE_MISSING")
    if not any(row.get("non_official_flag") for row in sources):
        failures.append("SOURCE_MAP_NON_OFFICIAL_SOURCE_MISSING")
    for row in sources:
        for key in (
            "mapping_parameters_extracted_count",
            "model_family_patterns_extracted_count",
            "penalty_patterns_extracted_count",
            "encoding_patterns_extracted_count",
            "coefficient_scaling_patterns_extracted_count",
            "interpret_back_patterns_extracted_count",
            "proof_vector_patterns_extracted_count",
            "repair_strategy_parameters_extracted_count",
            "benchmark_retest_parameters_extracted_count",
            "future_market_portability_notes_count",
            "candidate_values_extracted_count",
        ):
            if not isinstance(row.get(key), int) or row[key] < 0:
                failures.append(f"SOURCE_COUNT_BAD::{row.get('row_id')}::{key}")
        if int(row.get("candidate_values_extracted_count", 0)) <= 0 and not row.get("rejected_reason"):
            failures.append(f"SOURCE_CANDIDATE_VALUES_MISSING::{row.get('row_id')}")
        for flag in ("no_source_truth_acceptance_flag", "no_connector_binding_flag", "no_profit_evidence_flag", "no_backend_execution_flag"):
            if row.get(flag) is not True:
                failures.append(f"SOURCE_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")
    upstream = records["PR162E_Q_UpstreamReportUse.report.json"]
    if len(upstream) != len(c.STRICT_INPUT_REPORTS):
        failures.append("UPSTREAM_REPORT_USE_COUNT_MISMATCH")
    for row in upstream:
        if row.get("consumed_by_pr162e_q_flag") is not True and not row.get("terminal_reason"):
            failures.append(f"UPSTREAM_NOT_CONSUMED_OR_TERMINAL::{row.get('row_id')}")
        if not row.get("fields_used"):
            failures.append(f"UPSTREAM_FIELDS_USED_MISSING::{row.get('row_id')}")


def _validate_recipe_contracts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    recipe_reports = (
        "PR162E_Q_QUBORecipe.report.json",
        "PR162E_Q_BQMRecipe.report.json",
        "PR162E_Q_IsingRecipe.report.json",
        "PR162E_Q_CQMRecipe.report.json",
        "PR162E_Q_DQMRecipe.report.json",
        "PR162E_Q_QuadProgramRecipe.report.json",
        "PR162E_Q_HybridRecipe.report.json",
    )
    for filename in recipe_reports:
        for row in records[filename]:
            payload = row.get("recipe_payload") or {}
            if not payload:
                failures.append(f"RECIPE_PAYLOAD_MISSING::{filename}::{row.get('row_id')}")
            if not row.get("objective_terms") or not row.get("decision_variables"):
                failures.append(f"RECIPE_LABEL_ONLY::{filename}::{row.get('row_id')}")
            if row.get("automapper_disposition") in c.FORBIDDEN_AUTOMAPPER_DISPOSITIONS:
                failures.append(f"RECIPE_FORBIDDEN_DISPOSITION::{filename}::{row.get('row_id')}")
            if not row.get("solution_interpret_back_ref") or not row.get("proof_vector_ref"):
                failures.append(f"RECIPE_INTERPRET_OR_PROOF_MISSING::{filename}::{row.get('row_id')}")
    for row in records["PR162E_Q_HybridRecipe.report.json"]:
        if row.get("classical_fallback_available") is not True:
            failures.append(f"HYBRID_CLASSICAL_FALLBACK_MISSING::{row.get('row_id')}")
        if row.get("quantum_backend_execution_flag") is not False:
            failures.append(f"HYBRID_BACKEND_EXECUTED::{row.get('row_id')}")


def _validate_interpret_back_and_proofs(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR162E_Q_SolutionInterpretBack.report.json"]:
        for key in (
            "encoded_variable_name",
            "original_variable_name",
            "original_qku_field",
            "original_formula_field",
            "original_parameter_field",
            "original_execution_route_field",
            "encoded_domain",
            "original_domain",
            "transform_type",
            "reverse_transform_rule",
            "feasibility_check_rule",
            "downstream_agent_consumer",
            "test_vector_ref",
            "proof_vector_ref",
        ):
            if row.get(key) in {None, ""}:
                failures.append(f"INTERPRET_FIELD_MISSING::{row.get('row_id')}::{key}")
        if row.get("lost_information_flag") is not False and not row.get("lost_information_reason"):
            failures.append(f"INTERPRET_LOST_INFO_REASON_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_MapProof.report.json"]:
        if row.get("proof_status") not in {
            "PROOF_VECTOR_COMPUTED_DETERMINISTIC_NO_SOLVER",
            "STRUCTURAL_PROOF_VECTOR_COMPUTED_NO_SOLVER",
        }:
            failures.append(f"PROOF_STATUS_BAD::{row.get('row_id')}::{row.get('proof_status')}")
        objective_delta = finite_float(
            row.get("objective_delta"),
            field_name=f"objective_delta:{row.get('row_id')}",
        )
        if abs(objective_delta) > 1e-9:
            failures.append(f"PROOF_OBJECTIVE_DELTA_NONZERO::{row.get('row_id')}")
        if row.get("interpret_back_match_flag") is not True:
            failures.append(f"PROOF_INTERPRET_BACK_FAIL::{row.get('row_id')}")
    for row in records["PR162E_Q_TestVectors.report.json"]:
        if row.get("test_status") != "PASS_DETERMINISTIC_NO_SOLVER":
            failures.append(f"TEST_VECTOR_STATUS_BAD::{row.get('row_id')}")


    # Independent witness/model reconstruction: no writer or forward compiler call.
    from fractions import Fraction
    for row in records["PR162E_Q_MapProof.report.json"]:
        try:
            def scalar(value):
                if not is_finite_json_number_v1(value):
                    raise ValueError("invalid finite decoded model scalar")
                return Fraction(value)

            def put(target, key, value):
                target[key] = target.get(key, Fraction(0)) + value

            def polynomial(linear, quadratic, delimiter):
                if type(linear) is not dict or type(quadratic) is not dict:
                    raise ValueError("invalid coefficient objects")
                result = {}
                for name, value in linear.items():
                    if type(name) is not str or not name.strip() or name not in bits:
                        raise ValueError("unknown objective variable")
                    put(result, (name, name), scalar(value))
                for pair, value in quadratic.items():
                    if type(pair) is not str or len(pair.split(delimiter)) != 2:
                        raise ValueError("invalid coefficient pair")
                    left, right = pair.split(delimiter)
                    if left not in bits or right not in bits:
                        raise ValueError("unknown objective pair variable")
                    put(result, tuple(sorted((left, right))), scalar(value))
                return result

            def agrees(left, right, left_constant=Fraction(0), right_constant=Fraction(0)):
                # L1 bound certifies the maximum error over every binary assignment,
                # not only whichever terms happen to be active in this witness.
                bound = abs(left_constant - right_constant)
                for key in left.keys() | right.keys():
                    bound += abs(left.get(key, Fraction(0)) - right.get(key, Fraction(0)))
                return bound <= Fraction(1, 1_000_000_000)

            bits = row["encoded_variable_assignment"]
            if type(bits) is not dict or any(type(k) is not str or not k.strip() or type(v) is not int or v not in (0, 1) for k, v in bits.items()):
                raise ValueError("nonbinary or incomplete assignment")
            constraints = row["constraints"]
            if type(constraints) is not list:
                raise ValueError("constraint list missing")
            names = set()
            for constraint in constraints:
                if type(constraint) is not dict or set(constraint) != {"name", "linear", "sense", "rhs"}:
                    raise ValueError("unsupported constraint")
                name = constraint["name"]
                if type(name) is not str or not name.strip() or name in names or type(constraint["linear"]) is not dict:
                    raise ValueError("constraint identity")
                names.add(name)
                lhs = Fraction(0)
                for variable, coefficient in constraint["linear"].items():
                    if variable not in bits:
                        raise ValueError("unassigned constraint variable")
                    lhs += scalar(coefficient) * bits[variable]
                rhs, sense = scalar(constraint["rhs"]), constraint["sense"]
                if type(sense) is not str or sense not in ("GE", "LE", "EQ"):
                    raise ValueError("unknown sense")
                ok = (lhs >= rhs - Fraction(1, 1_000_000_000)) if sense == "GE" else (lhs <= rhs + Fraction(1, 1_000_000_000)) if sense == "LE" else (abs(lhs - rhs) <= Fraction(1, 1_000_000_000))
                if not ok:
                    raise ValueError("infeasible witness")
            original = polynomial(row["objective_linear_terms"], row["objective_quadratic_terms"], "*")
            original_envelope = row["objective_terms"]
            if type(original_envelope) is not dict or not agrees(original, polynomial(original_envelope["linear"], original_envelope["quadratic"], "*")):
                raise ValueError("objective envelope mismatch")
            offset = scalar(original_envelope["offset"])
            recipes = row["recipe_payload"]
            q, b, s = recipes["qubo"], recipes["bqm"], recipes["ising"]
            if q["objective_sense"] != "minimize_energy" or b["vartype"] != "BINARY" or s["vartype"] != "SPIN" or s["binary_to_spin_rule"] != "x=(s+1)/2":
                raise ValueError("objective/domain basis")
            qpoly = polynomial({}, q["Q"], ",")
            bpoly = polynomial(b["linear"], b["quadratic"], "*")
            required = {key: -value for key, value in original.items()}
            full_names = ("x_select", "x_precompute", "x_retest", "x_owner_review", "x_size_0", "x_size_1", "x_size_2", "case_retest", "case_skip", "case_precompute", "case_owner_review")
            if tuple(bits) != full_names and set(bits) != set(full_names):
                raise ValueError("complete native variable domain missing")
            encoding = recipes["constraint_encoding"]
            if encoding["method"] != "SOURCE_BOUND_BINARY_VIOLATION_SQUARES_NO_SLACK" or encoding["variables"] != list(full_names) or type(encoding["additional_binary_variables"]) is not int or encoding["additional_binary_variables"] != 0 or encoding["original_model_check_required"] is not True:
                raise ValueError("encoding contract mismatch")
            native_forms = {
                "select_requires_one_route": ({"x_select": 1, "x_precompute": -1}, "GE", (0,)),
                "owner_review_for_negative_or_repair": ({"x_owner_review": 1, "x_retest": 1}, "GE", (0, 1)),
                "bounded_candidate_size": ({"x_size_0": 1, "x_size_1": 2, "x_size_2": 4}, "LE", (7,)),
                "dqm_case_one_hot": ({"case_skip": 1, "case_precompute": 1, "case_retest": 1, "case_owner_review": 1}, "EQ", (1,)),
                "structural_sparse_route": ({"x_precompute": 1}, "GE", (1,)),
                "capacity_guard": ({"x_select": 1, "x_owner_review": 1}, "LE", (2,)),
            }
            if not {"select_requires_one_route", "owner_review_for_negative_or_repair", "bounded_candidate_size"} <= names:
                raise ValueError("native constraint roster incomplete")
            family = recipes["selected_family"]
            if family not in ("QUBO", "BQM", "Ising", "CQM", "DQM", "QuadraticProgram"):
                raise ValueError("model family")
            # Bind the existing outer report declarations to the actual native model.
            # Reconstruct these source-defined domains locally: never ask the writer
            # under test to certify its own schema or variable interpretation.
            def same_domain(actual, expected):
                if type(actual) is not type(expected):
                    return False
                if type(expected) is dict:
                    return actual.keys() == expected.keys() and all(same_domain(actual[k], value) for k, value in expected.items())
                if type(expected) is list:
                    return len(actual) == len(expected) and all(same_domain(a, b) for a, b in zip(actual, expected))
                return actual == expected
            original_fields = (
                "candidate_selected_flag", "quantum_precompute_route_flag",
                "replay_paper_retest_route_flag", "owner_dashboard_review_flag",
                "order_size_bit_0", "order_size_bit_1", "order_size_bit_2",
                "execution_route_case", "execution_route_case", "execution_route_case", "execution_route_case",
            )
            declared_variables = []
            for variable, original_field in zip(full_names, original_fields):
                declaration = {"name": variable, "type": "binary", "original_field": original_field}
                if variable.startswith("case_"):
                    declaration["case_value"] = variable.removeprefix("case_")
                declared_variables.append(declaration)
            declared_domains = {
                "binary": {name: [0, 1] for name in full_names},
                "integer": {"candidate_size": [0, 7]},
                "spin": {name.replace("x_", "s_"): [-1, 1] for name in full_names},
                "discrete": {"route_case": ["skip", "precompute", "retest", "owner_review"]},
                "selected_family_native": family,
                "integer_is_derived": True,
                "route_case_requires_one_hot_constraint": True,
                "route_bits_preserved_when_not_one_hot": True,
            }
            if type(row.get("model_family_selected")) is not str or row["model_family_selected"] != family:
                raise ValueError("outer model-family mismatch")
            if not same_domain(row.get("decision_variables"), declared_variables):
                raise ValueError("outer variable-declaration mismatch")
            if not same_domain(row.get("variable_domains"), declared_domains):
                raise ValueError("outer variable-domain mismatch")
            for native_name in ("cqm", "quadratic_program"):
                if not same_domain(recipes[native_name].get("variables"), declared_variables):
                    raise ValueError("native variable interpretation mismatch")
            structural = recipes["hybrid"]["structural_only_flag"]
            if type(structural) is not bool or ("dqm_case_one_hot" in names) != (family == "DQM") or ("structural_sparse_route" in names) != structural:
                raise ValueError("constraint branch mismatch")
            if type(row.get("still_negative_after_costs_flag")) is not bool:
                raise ValueError("negative-branch predicate unavailable")
            negative_constraint = next(item for item in constraints if item["name"] == "owner_review_for_negative_or_repair")
            if type(negative_constraint["rhs"]) is not int or negative_constraint["rhs"] != int(row["still_negative_after_costs_flag"]):
                raise ValueError("negative-branch predicate mismatch")
            penalty_poly, penalty_constant = {}, Fraction(0)
            from itertools import combinations, product
            for constraint in constraints:
                shape, sense, allowed = native_forms[constraint["name"]]
                if constraint["linear"] != shape or any(type(value) is not int for value in constraint["linear"].values()) or type(constraint["rhs"]) is not int or constraint["rhs"] not in allowed or constraint["sense"] != sense:
                    raise ValueError("unreviewed native constraint change")
                variables = tuple(shape)
                def loss(active):
                    lhs = sum(coefficient for name, coefficient in shape.items() if name in active)
                    residual = lhs - constraint["rhs"]
                    violation = max(0, -residual) if sense == "GE" else max(0, residual) if sense == "LE" else abs(residual)
                    return Fraction(violation * violation)
                constant = loss(set())
                singles = {name: loss({name}) - constant for name in variables}
                pairs = {tuple(sorted((left, right))): loss({left, right}) - constant - singles[left] - singles[right] for left, right in combinations(variables, 2)}
                # Independent Boolean interpolation; verify no higher-order loss.
                for values in product((0, 1), repeat=len(variables)):
                    assignment = dict(zip(variables, values))
                    interpolated = constant + sum(singles[name]*assignment[name] for name in variables) + sum(value*assignment[a]*assignment[b] for (a, b), value in pairs.items())
                    if interpolated != loss({name for name, value in assignment.items() if value}):
                        raise ValueError("constraint needs unsupported higher-order encoding")
                penalty_constant += constant
                for name, value in singles.items():
                    put(penalty_poly, (name, name), value)
                for pair, value in pairs.items():
                    put(penalty_poly, pair, value)
            weight = scalar(q["penalty_weight"])
            span = sum(abs(value) for value in original.values())
            if weight <= span:
                raise ValueError("penalty cannot prove feasibility separation")
            for key, value in penalty_poly.items():
                put(required, key, weight*value)
            required_offset = offset + weight*penalty_constant
            if encoding["original_constraints"] != constraints or scalar(encoding["penalty_weight"]) != weight or scalar(encoding["objective_energy_offset"]) != offset:
                raise ValueError("encoding input binding mismatch")
            if not agrees(polynomial({}, encoding["penalty_polynomial"], ","), penalty_poly, scalar(encoding["penalty_constant"]), penalty_constant):
                raise ValueError("penalty declaration mismatch")
            if scalar(encoding["objective_span_upper_bound"]) < span:
                raise ValueError("understated objective variation")
            qoffset, boffset = scalar(q["offset"]), scalar(b["offset"])
            if not agrees(qpoly, required, qoffset, required_offset) or not agrees(bpoly, qpoly, boffset, qoffset):
                raise ValueError("full binary polynomial mismatch")
            # Invert s=2*x-1, independently of the writer's forward transform.
            reverse = {}
            for name in bits:
                spin = name.replace("x_", "s_")
                if spin in reverse:
                    raise ValueError("spin name collision")
                reverse[spin] = name
            recovered, recovered_constant = {}, scalar(s["offset"])
            if type(s["h"]) is not dict or type(s["J"]) is not dict:
                raise ValueError("Ising coefficient objects")
            for spin, raw in s["h"].items():
                name, value = reverse[spin], scalar(raw)
                put(recovered, (name, name), 2 * value)
                recovered_constant -= value
            for pair, raw in s["J"].items():
                if type(pair) is not str or len(pair.split(",")) != 2:
                    raise ValueError("Ising pair")
                left, right = (reverse[name] for name in pair.split(","))
                value = scalar(raw)
                if left == right:
                    recovered_constant += value
                else:
                    put(recovered, tuple(sorted((left, right))), 4 * value)
                    put(recovered, (left, left), -2 * value)
                    put(recovered, (right, right), -2 * value)
                    recovered_constant += value
            if not agrees(recovered, qpoly, recovered_constant, qoffset):
                raise ValueError("Ising polynomial mismatch")
            q_error = abs(qoffset-required_offset) + sum(abs(qpoly.get(key, Fraction(0))-required.get(key, Fraction(0))) for key in qpoly.keys() | required.keys())
            spin_error = abs(recovered_constant-qoffset) + sum(abs(recovered.get(key, Fraction(0))-qpoly.get(key, Fraction(0))) for key in recovered.keys() | qpoly.keys())
            if weight-span <= 2*(q_error+spin_error):
                raise ValueError("numerical error removes feasibility separation")
            # Recompute the reported spin-coordinate error certificate independently.
            ideal_h = {name.replace("x_", "s_"): qpoly.get((name,name), Fraction(0))/2 + sum(value/4 for pair,value in qpoly.items() if pair[0]!=pair[1] and name in pair) for name in full_names}
            ideal_j = {",".join(sorted((a.replace("x_","s_"),b.replace("x_","s_")))): value/4 for (a,b),value in qpoly.items() if a!=b}
            ideal_constant = qoffset + sum(value/(2 if a==b else 4) for (a,b),value in qpoly.items())
            reported_minimum = q_error + abs(scalar(s["offset"])-ideal_constant)
            reported_minimum += sum(abs(scalar(s["h"].get(name,0))-value) for name,value in ideal_h.items())
            reported_minimum += sum(abs(scalar(s["J"].get(pair,0))-value) for pair,value in ideal_j.items())
            if not reported_minimum <= scalar(encoding["uniform_export_error_bound"]) <= Fraction(1, 1000000000):
                raise ValueError("invalid or understated export error bound")
            for label in ("cqm", "quadratic_program"):
                model = recipes[label]
                variables = model["variables"]
                if type(variables) is not list or [item["name"] for item in variables] != list(full_names) or any(item.get("type") != "binary" for item in variables):
                    raise ValueError("incomplete constrained-model domains")
                model_sense = "minimize" if label == "cqm" else "maximize"
                model_constant = offset if label == "cqm" else Fraction(0)
                model_poly = {key: -value for key, value in original.items()} if label == "cqm" else original
                if model["constraints"] != constraints or model["objective"]["sense"] != model_sense or scalar(model["objective"]["offset"]) != model_constant:
                    raise ValueError("constrained-model objective or constraint mismatch")
                if not agrees(polynomial(model["objective"]["linear"], model["objective"]["quadratic"], "*"), model_poly):
                    raise ValueError("constrained-model utility mismatch")
            dqm = recipes["dqm"]
            if dqm["native_encoding"] != "TWO_CASE_PER_ORIGINAL_BINARY_VARIABLE" or set(dqm["variables"]) != set(full_names) or any(type(cases) is not list or len(cases)!=2 or any(type(value) is not int for value in cases) or cases != [0, 1] for cases in dqm["variables"].values()):
                raise ValueError("DQM case domains")
            if set(dqm["linear_biases"]) != set(full_names) or set(dqm["quadratic_biases"]) != set(b["quadratic"]):
                raise ValueError("DQM bias roster mismatch")
            d_linear, d_pairs = {}, {}
            for name, values in dqm["linear_biases"].items():
                if type(values) is not list or len(values)!=2 or scalar(values[0])!=0:
                    raise ValueError("DQM linear bias shape")
                d_linear[name] = values[1]
            for pair, matrix in dqm["quadratic_biases"].items():
                if type(matrix) is not list or len(matrix)!=2 or any(type(values) is not list or len(values)!=2 for values in matrix) or any(scalar(matrix[i][j])!=0 for i,j in ((0,0),(0,1),(1,0))):
                    raise ValueError("DQM pair bias shape")
                d_pairs[pair] = matrix[1][1]
            if not agrees(polynomial(d_linear, d_pairs, "*"), qpoly, scalar(dqm["offset"]), qoffset):
                raise ValueError("DQM polynomial mismatch")
            u = sum((v * bits[a] * bits[b] for (a, b), v in original.items()), Fraction(0))
            energy = qoffset + sum((v * bits[a] * bits[b] for (a, b), v in qpoly.items()), Fraction(0))
            for key, expected in (("original_objective_value", u), ("encoded_objective_value", offset - energy), ("encoded_energy_value", energy), ("bqm_energy_value", energy), ("ising_energy_value", energy)):
                if abs(scalar(row[key]) - expected) > Fraction(1, 1_000_000_000):
                    raise ValueError("claimed objective/energy mismatch")
            if row["constraint_satisfaction_original"] != "SATISFIED" or row["constraint_satisfaction_encoded"] != "SATISFIED" or row["feasibility_match_flag"] is not True or scalar(row["penalty_value"]) != 0:
                raise ValueError("feasibility claims mismatch")
            if row["proof_scope"] != "CONSTRAINED_BINARY_ENERGY_AND_FEASIBLE_WITNESS" or q["constraint_penalties_embedded"] is not True or q["original_model_constraint_check_required"] is not True:
                raise ValueError("proof scope or constraint handling misrepresented")
            decoded = row["original_variable_assignment"]
            for name, field in (("x_select", "select_candidate"), ("x_precompute", "quantum_precompute_route"), ("x_retest", "replay_paper_retest_route"), ("x_owner_review", "owner_review_route")):
                if type(decoded[field]) is not bool or decoded[field] != bool(bits[name]):
                    raise ValueError("route interpret-back mismatch")
            if decoded["route_bits"] != {name: bits["case_"+name] for name in ("skip", "precompute", "retest", "owner_review")} or any(type(value) is not int for value in decoded["route_bits"].values()):
                raise ValueError("route-bit interpret-back mismatch")
            size = bits["x_size_0"] + 2 * bits["x_size_1"] + 4 * bits["x_size_2"]
            cases = [name for name in ("skip", "precompute", "retest", "owner_review") if bits["case_" + name] == 1]
            if type(decoded["candidate_size"]) is not int or decoded["candidate_size"] != size:
                raise ValueError("size interpret-back mismatch")
            if "dqm_case_one_hot" in names and len(cases) != 1:
                raise ValueError("original one-hot constraint violated")
            expected_case = cases[0] if len(cases) == 1 else None
            if type(decoded["route_case"]) is not type(expected_case) or decoded["route_case"] != expected_case:
                raise ValueError("case interpret-back mismatch")
        except (KeyError, TypeError, ValueError, ArithmeticError):
            failures.append(f"PROOF_MODEL_WITNESS_INVALID::{row.get('row_id')}")


def _validate_risk_execution_and_units(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR162E_Q_UnitNorm.report.json"]:
        for key in (
            "probability_unit",
            "YES_NO_side",
            "price_unit",
            "edge_unit",
            "TCA_unit",
            "latency_unit",
            "fill_probability_unit",
            "order_size_unit",
            "expected_value_unit",
            "normalized_expected_net_profit_per_order_candidate",
        ):
            if row.get(key) in {None, ""}:
                failures.append(f"UNIT_FIELD_MISSING::{row.get('row_id')}::{key}")
        if row.get("YES_NO_side") not in {"YES", "NO"}:
            failures.append(f"UNIT_YES_NO_SIDE_BAD::{row.get('row_id')}")
    for row in records["PR162E_Q_TCAMapImpact.report.json"]:
        for key in (
            "explicit_fee_component",
            "bid_ask_spread_component",
            "slippage_component",
            "impact_component",
            "latency_component",
            "no_fill_opportunity_cost_component",
            "settlement_finality_component",
            "market_state_mismatch_component",
            "model_vs_execution_gap_component",
            "mapping_to_replay_translation_penalty",
            "mapping_to_paper_translation_penalty",
            "mapping_to_simulator_translation_penalty",
            "total_tca_estimate",
        ):
            if not is_finite_json_number_v1(row.get(key)):
                failures.append(f"TCA_FIELD_MISSING::{row.get('row_id')}::{key}")
        if not row.get("tca_reason_codes"):
            failures.append(f"TCA_REASON_CODES_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_OverfitFDRMapRisk.report.json"]:
        for key in (
            "trial_family_id",
            "near_duplicate_mapping_cluster_id",
            "effective_independent_trial_count",
            "family_wise_selection_pressure",
            "false_discovery_penalty",
            "deflated_score_proxy",
            "probability_of_backtest_overfitting_proxy",
            "mapping_instability_penalty",
            "replay_instability_penalty",
            "paper_instability_penalty",
            "replay_paper_divergence_penalty",
            "rank_stability_score",
            "repeated_test_inflation_penalty",
            "holdout_walk_forward_eligibility_flag",
            "cpcv_purged_walk_forward_route_flag",
        ):
            if row.get(key) in {None, ""}:
                failures.append(f"OVERFIT_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR162E_Q_MapSensitivityStress.report.json"]:
        if not row.get("stress_test_result"):
            failures.append(f"STRESS_RESULT_MISSING::{row.get('row_id')}")
        if row.get("paper_champion_flag") or row.get("paper_challenger_flag"):
            if row.get("mapping_robustness_score") in {None, ""}:
                failures.append(f"CHAMPION_CHALLENGER_STRESS_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_EdgeAttribution.report.json"]:
        for key in (
            "baseline_expected_net_profit_per_order_candidate",
            "mapped_expected_net_profit_per_order_candidate",
            "expected_value_delta_candidate",
            "TCA_delta_candidate",
            "latency_delta_candidate",
            "fill_probability_delta_candidate",
            "queue_risk_delta_candidate",
            "capacity_delta_candidate",
            "crowding_delta_candidate",
            "overfit_delta_candidate",
            "marginal_utility_delta_candidate",
            "quantum_precompute_delta_candidate",
            "classical_fallback_delta_candidate",
        ):
            if not is_finite_json_number_v1(row.get(key)):
                failures.append(f"EDGE_FIELD_MISSING::{row.get('row_id')}::{key}")
        if row.get("not_profit_evidence_flag") is not True:
            failures.append(f"EDGE_PROFIT_EVIDENCE_FLAG_BAD::{row.get('row_id')}")


def _validate_routes_and_agents(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR162E_Q_StillNegativeMapRepair.report.json"]:
        if row.get("still_negative_after_costs_flag") and not row.get("repair_family"):
            failures.append(f"REPAIR_FAMILY_MISSING::{row.get('row_id')}")
        if row.get("not_profit_evidence_flag") is not True or row.get("no_live_authority_flag") is not True:
            failures.append(f"REPAIR_AUTHORITY_FLAG_BAD::{row.get('row_id')}")
    for row in records["PR162E_Q_OpenTradeSimMap.report.json"]:
        if row.get("hot_path_allowed_flag") is not False or row.get("no_live_authority_flag") is not True:
            failures.append(f"OPEN_TRADE_AUTHORITY_BAD::{row.get('row_id')}")
    for row in records["PR162E_Q_OwnerDashboardMapReview.report.json"]:
        if row.get("dashboard_ui_implemented_flag") not in {None, False}:
            failures.append(f"DASHBOARD_UI_CLAIMED::{row.get('row_id')}")
        if not row.get("future_dashboard_pr_ref"):
            failures.append(f"DASHBOARD_FUTURE_PR_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_ConnectorRouteReady.report.json"]:
        for flag in ("no_current_connector_binding_flag", "no_source_truth_acceptance_flag", "no_private_state_fetch_flag"):
            if row.get(flag) is not True:
                failures.append(f"CONNECTOR_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")
        if not row.get("downstream_connector_pr_ref"):
            failures.append(f"CONNECTOR_DOWNSTREAM_PR_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_MarketPortability.report.json"]:
        if row.get("stage1_prediction_market_flag") is not True or row.get("future_market_portability_flag") is not True:
            failures.append(f"MARKET_PORTABILITY_FLAG_BAD::{row.get('row_id')}")
        if row.get("no_current_connector_binding_flag") is not True or row.get("no_live_authority_flag") is not True:
            failures.append(f"MARKET_AUTHORITY_BAD::{row.get('row_id')}")
    for row in records["PR162E_Q_AgentWorkOrders.report.json"]:
        for key in (
            "work_order_id",
            "owning_agent_id",
            "agent_duty_ref",
            "source_artifact_ref",
            "source_row_ref",
            "task_type",
            "task_priority",
            "expected_input_refs",
            "expected_output_refs",
            "downstream_agent_refs",
            "downstream_pr_refs",
            "expected_agent_output_artifact",
        ):
            if not row.get(key):
                failures.append(f"AGENT_WORK_ORDER_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR162E_Q_AgentDAG.report.json"]:
        for key in ("dag_node_id", "upstream_pr_refs", "upstream_row_refs", "mapping_recipe_route", "replay_route", "open_trade_simulator_route", "connector_readiness_route", "no_orphan_proof"):
            if not row.get(key):
                failures.append(f"AGENT_DAG_FIELD_MISSING::{row.get('row_id')}::{key}")
    for filename in (
        "PR162E_Q_To_PR166_QC_Retest.report.json",
        "PR162E_Q_To_PR167.report.json",
        "PR162E_Q_To_PR162E.report.json",
        "PR162E_Q_To_PR162F.report.json",
        "PR162E_Q_To_OwnerDashboard.report.json",
        "PR162E_Q_To_CloudSwitchboard.report.json",
        "PR162E_Q_To_FutureConnectors.report.json",
    ):
        for row in records[filename]:
            for key in ("handoff_id", "source_mapping_row_ref", "model_family_selected", "objective_map_ref", "variable_encoding_ref", "solution_interpret_back_ref", "proof_vector_ref"):
                if not row.get(key):
                    failures.append(f"HANDOFF_FIELD_MISSING::{filename}::{row.get('row_id')}::{key}")
            if row.get("no_live_authority_flag") is not True:
                failures.append(f"HANDOFF_LIVE_AUTHORITY::{filename}::{row.get('row_id')}")


def _validate_crosswalk_and_artifacts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    crosswalk = records["PR162E_Q_ReportConsumerCrosswalk.report.json"]
    mapped = {row.get("report_path") for row in crosswalk}
    for filename in c.REPORT_FILENAMES:
        if f"docs/master_plan/generated/{filename}" not in mapped:
            failures.append(f"CROSSWALK_REPORT_NOT_MAPPED::{filename}")
    for filename in c.STRICT_INPUT_REPORTS:
        if f"docs/master_plan/generated/{filename}" not in mapped:
            failures.append(f"CROSSWALK_INPUT_NOT_MAPPED::{filename}")
    for row in crosswalk:
        if not row.get("owning_agent_id"):
            failures.append(f"CROSSWALK_OWNER_MISSING::{row.get('row_id')}")
        if not row.get("consuming_agent_ids") and not row.get("terminal_flag"):
            failures.append(f"CROSSWALK_CONSUMER_MISSING::{row.get('row_id')}")
    artifacts = records["PR162E_Q_ArtifactMap.report.json"]
    if not artifacts:
        failures.append("ARTIFACT_MAP_EMPTY")
    for row in artifacts:
        if not row.get("artifact_path"):
            failures.append(f"ARTIFACT_PATH_MISSING::{row.get('row_id')}")
        if not row.get("consumed_by_module"):
            failures.append(f"ARTIFACT_CONSUMER_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_NoOrphanProof.report.json"]:
        if row.get("no_orphan_status") != "NO_ORPHAN":
            failures.append(f"NO_ORPHAN_STATUS_FAIL::{row.get('row_id')}")
        if not row.get("artifact_refs_checked"):
            failures.append(f"NO_ORPHAN_REFS_MISSING::{row.get('row_id')}")
    # Independent reconstruction: do not call the writer or its crosswalk factory.
    expected_counts = {
        f"docs/master_plan/generated/{name}": len(records[name])
        for name in c.REPORT_FILENAMES
    }
    input_counts: dict[str, int] = {}
    counts_valid = True
    for row in records["PR162E_Q_InputConsumption.report.json"]:
        name = row.get("source_report_ref")
        value = row.get("expanded_record_count")
        if (
            type(name) is not str or name not in c.STRICT_INPUT_REPORTS
            or name in input_counts or type(value) is not int or value < 0
        ):
            counts_valid = False
            continue
        input_counts[name] = value
    if set(input_counts) != set(c.STRICT_INPUT_REPORTS):
        counts_valid = False
    expected_counts.update({f"docs/master_plan/generated/{name}": value for name, value in input_counts.items()})
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    for row in crosswalk:
        path = row.get("report_path")
        identity = row.get("row_id")
        value = row.get("record_count")
        if (
            type(path) is not str or path not in expected_counts or path in seen_paths
            or type(identity) is not str or not identity.strip() or identity in seen_ids
            or type(value) is not int or value < 0 or value != expected_counts.get(path)
        ):
            counts_valid = False
        if type(path) is str:
            seen_paths.add(path)
        if type(identity) is str:
            seen_ids.add(identity)
    if seen_paths != set(expected_counts) or not counts_valid:
        failures.append("CROSSWALK_COUNT_OR_COVERAGE_MISMATCH")


def _validate_summary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR162E_Q_FinalSummary.report.json"][0]
    if summary.get("consumed_pr162e_q_handoff_rows") != 559:
        failures.append("SUMMARY_HANDOFF_COUNT_NOT_559")
    if summary.get("deep_mapping_subset_count", 0) > c.MAP_CAPS["max_deep_mapping_rows_default_ci"]:
        failures.append("SUMMARY_DEEP_SUBSET_CAP_EXCEEDED")
    if summary.get("forbidden_authority_counts_all_zero_flag") is not True:
        failures.append("SUMMARY_AUTHORITY_NOT_ZERO")
    if summary.get("dashboard_ui_implemented_flag") is not False:
        failures.append("SUMMARY_DASHBOARD_UI_CLAIMED")
    for key in (
        "cloud_backend_execution_count",
        "credential_access_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "profit_evidence_count",
        "live_order_authority_count",
        "live_promotion_claim_count",
        "source_truth_acceptance_count",
        "connector_semantic_binding_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "qtt_sha_authority_count",
        "atomicrows_bundle_hash_authority_count",
    ):
        if (not is_nonnegative_json_integer_v1(summary.get(key, 0)) or summary.get(key, 0) != 0):
            failures.append(f"SUMMARY_FORBIDDEN_COUNT_NONZERO::{key}")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    from fnmatch import fnmatch
    for path in _report_directory_entries_v1(repo_root / c.GENERATED_DIR):
        if not fnmatch(path.name, "PR162E_Q_*"):
            continue
        name = path.name.lower()
        if any(token in name for token in ("sha256", "checksum", "freeze", "global_digest")):
            failures.append(f"FORBIDDEN_DIGEST_ARTIFACT::{path.name}")

def _validate_mapping_projection_consistency_v1(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    """Bind every current row-report projection to the independently checked proof.

    This is not source-generation acceptance. Reuse the existing packet/context
    alignment owner, do not reread reports, and do not invoke a writer as oracle.
    All-empty input is allowed here; the outer original row-count gate owns
    required population. A missing or mismatched sibling is not all-empty.
    """
    import math
    import json

    def identical(left, right):
        if type(left) is not type(right):
            return False
        if type(left) is dict:
            return left.keys() == right.keys() and all(identical(left[key], right[key]) for key in left)
        if type(left) is list:
            return len(left) == len(right) and all(identical(a, b) for a, b in zip(left, right))
        if type(left) is float:
            return math.isfinite(left) and math.isfinite(right) and left == right
        return type(left) in (str, int, bool, type(None)) and left == right

    proof_name = "PR162E_Q_MapProof.report.json"
    interpret_name = "PR162E_Q_SolutionInterpretBack.report.json"
    test_name = "PR162E_Q_TestVectors.report.json"
    try:
        proof_rows = records[proof_name]
        companion_names = tuple(name for name in c.ROW_REPORTS if name != proof_name)
        if proof_name not in c.ROW_REPORTS or interpret_name not in companion_names or test_name not in companion_names or len(c.ROW_REPORTS) != len(set(c.ROW_REPORTS)):
            raise ValueError("invalid projection report roster")
        aligned = _report_companion_alignment_v1(
            proof_rows, {name: records[name] for name in companion_names},
        )
        # Equality here is stricter than numerical closeness: projections of
        # one producer value must not introduce independent conversion/rounding.
        shared = (
            "recipe_payload", "constraints", "objective_terms",
            "objective_linear_terms", "objective_quadratic_terms",
            "model_family_selected", "decision_variables", "variable_domains",
            "encoded_variable_assignment", "original_variable_assignment",
            "original_objective_value", "encoded_objective_value", "objective_delta",
            "encoded_energy_value", "bqm_energy_value", "ising_energy_value",
            "penalty_value", "constraint_satisfaction_original",
            "constraint_satisfaction_encoded", "feasibility_match_flag",
            "interpret_back_match_flag", "proof_scope", "proof_status",
            "proof_vector_id", "mapping_row_ref", "source_mapping_row_ref",
            "proof_vector_ref", "test_vector_ref",
            "canonical_variable_signature", "canonical_constraint_signature",
            "constraint_native_flag", "slack_variable_plan",
            "coefficient_scaling_status", "discrete_case_handling",
        )
        cases = ["case_skip", "case_precompute", "case_retest", "case_owner_review"]
        expected_entries = [
            {"encoded_variable_name": "x_select", "original_variable_name": "select_candidate", "transform_type": "identity", "output_type": "boolean"},
            {"encoded_variable_name": "x_precompute", "original_variable_name": "quantum_precompute_route", "transform_type": "identity", "output_type": "boolean"},
            {"encoded_variable_name": "s_select", "original_variable_name": "select_candidate", "transform_type": "spin_conversion", "reverse_transform_rule": "x=(s+1)/2", "output_type": "boolean"},
            {"encoded_variable_name": "case_retest", "original_variable_name": "route_bits.retest", "transform_type": "identity", "output_type": "integer_0_or_1"},
            {"encoded_variable_name": "x_retest", "original_variable_name": "replay_paper_retest_route", "transform_type": "identity", "output_type": "boolean"},
            {"encoded_variable_name": "x_owner_review", "original_variable_name": "owner_review_route", "transform_type": "identity", "output_type": "boolean"},
            {"encoded_variables": ["x_size_0", "x_size_1", "x_size_2"], "original_variable_name": "candidate_size", "transform_type": "binary_expansion", "weights": [1, 2, 4], "output_domain": [0, 7]},
            {"encoded_variables": cases, "original_variable_name": "route_bits", "transform_type": "identity", "case_names": ["skip", "precompute", "retest", "owner_review"]},
            {"encoded_variables": cases, "original_variable_name": "route_case", "transform_type": "unique_active_or_null", "requires_one_hot_only_when": "dqm_case_one_hot"},
        ]
        labels = ("x_select", "x_precompute", "x_retest", "x_owner_review", "x_size_0", "x_size_1", "x_size_2", "case_retest", "case_skip", "case_precompute", "case_owner_review")
        expected_spin = {name.replace("x_", "s_"): name for name in labels}
        expected_interpret = {
            "encoded_variable_name": "x_select", "original_variable_name": "select_candidate",
            "original_qku_field": "qku_id", "original_formula_field": "formula_id",
            "original_parameter_field": "parameter_stack_id", "original_execution_route_field": "execution_route_id",
            "encoded_domain": "{0,1}", "original_domain": "NONLIVE_SELECT_OR_SKIP_DECISION", "transform_type": "identity",
            "reverse_transform_rule": "select_candidate = bool(x_select); first convert every spin with x=(s+1)/2; candidate_size=x_size_0+2*x_size_1+4*x_size_2; preserve all route_bits; route_case is the unique active case or null; execution_route_id is unchanged",
            "feasibility_check_rule": "complete exact-domain sample; all original constraints satisfied; one-hot only when dqm_case_one_hot is present; never use argmax to repair an infeasible or ambiguous sample",
            "lost_information_flag": False, "lost_information_reason": "", "downstream_agent_consumer": "Replay Agent",
            "interpret_back_entries": expected_entries, "spin_to_binary_variables": expected_spin,
        }
        # A business-reference identifier cannot name two distinct packets in
        # the same invocation, even if every sibling repeats the collision.
        reference_owners = {key: set() for key in ("proof_vector_id", "mapping_row_ref", "test_vector_ref")}
        for index, proof in enumerate(proof_rows):
            interpret, test = aligned[interpret_name][index], aligned[test_name][index]
            for name in companion_names:
                sibling = aligned[name][index]
                if any(key not in proof or key not in sibling or not identical(proof[key], sibling[key]) for key in shared):
                    raise ValueError("projected model or witness differs")
            expected_descriptions = {
                "canonical_variable_signature": ",".join(item["name"] for item in proof["decision_variables"]),
                "canonical_constraint_signature": json.dumps(proof["constraints"], sort_keys=True, separators=(",", ":")),
                "constraint_native_flag": proof["model_family_selected"] in {"CQM", "QuadraticProgram"},
                "slack_variable_plan": "NO_ADDITIONAL_SLACK_FOR_SELECTED_SOURCE_BOUND_BINARY_CONSTRAINTS",
                "coefficient_scaling_status": "UNSCALED_MODEL_COEFFICIENTS_WITH_SOURCE_MAXIMUM_MAGNITUDE_PROXY",
                "discrete_case_handling": "TWO_CASE_PER_ORIGINAL_BINARY_VARIABLE;ONE_HOT_ONLY_WHEN_ORIGINAL_CONSTRAINT_REQUIRES",
            }
            if any(not identical(proof[key], value) for key, value in expected_descriptions.items()):
                raise ValueError("outer model description contradicts compiled representation")
            for key in ("proof_vector_id", "mapping_row_ref", "source_mapping_row_ref", "proof_vector_ref", "test_vector_ref"):
                if type(proof[key]) is not str or not proof[key].strip():
                    raise ValueError("invalid linked identity")
            for key, observed in reference_owners.items():
                if proof[key] in observed:
                    raise ValueError("business reference aliases distinct packets")
                observed.add(proof[key])
            if proof["source_mapping_row_ref"] != proof["mapping_row_ref"] or proof["proof_vector_ref"] != proof["proof_vector_id"]:
                raise ValueError("mapping/proof link mismatch")
            if type(test.get("test_vector_id")) is not str or test["test_vector_id"] != proof["test_vector_ref"]:
                raise ValueError("test identity mismatch")
            for key, value in expected_interpret.items():
                if key not in interpret or not identical(interpret[key], value):
                    raise ValueError("interpretation differs from original inverse contract")
            for target, origin in (("expected_original_objective_value", "original_objective_value"), ("expected_encoded_objective_value", "encoded_objective_value")):
                if target not in test or not identical(test[target], proof[origin]):
                    raise ValueError("expected value is detached from verified witness")
            if test.get("expected_feasibility_status") != "FEASIBLE" or test.get("test_status") != "PASS_DETERMINISTIC_NO_SOLVER":
                raise ValueError("test projection status mismatch")
    except (KeyError, TypeError, ValueError, ArithmeticError, SerializationSafetyError):
        failures.append("MAPPING_PROJECTION_MISMATCH")
