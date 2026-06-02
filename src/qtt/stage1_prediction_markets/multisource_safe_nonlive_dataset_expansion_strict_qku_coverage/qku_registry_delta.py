"""PR162C QKU delta registry builders."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .formula_test_vectors import (
    algorithm_delta_records,
    formula_delta_records,
    formula_test_vector_delta_records,
)


def objective_delta_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    objective_names = {
        "correlation_penalized_portfolio_score",
        "multi_objective_weighted_sum",
        "QUBO-to-Ising mapping candidate",
        "constraint_penalty",
    }
    return [
        {
            **_common_delta(record, "objective"),
            "objective_id": record["formula_id"].replace("FORMULA", "OBJECTIVE"),
            "formula_ref": record["formula_id"],
            "objective_family": record["formula_family"],
            "objective_name": record["formula_name"],
        }
        for record in formulas
        if record["formula_name"] in objective_names
    ]


def constraint_delta_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    constraint_names = {
        "liquidity_feasible_dislocation",
        "drawdown_capped_kelly",
        "liquidity_adjusted_size",
        "max_position_by_budget",
        "constraint_penalty",
    }
    return [
        {
            **_common_delta(record, "constraint"),
            "constraint_id": record["formula_id"].replace("FORMULA", "CONSTRAINT"),
            "formula_ref": record["formula_id"],
            "constraint_family": record["formula_family"],
            "constraint_name": record["formula_name"],
        }
        for record in formulas
        if record["formula_name"] in constraint_names
    ]


def parameter_value_delta_records() -> list[dict[str, Any]]:
    return [
        _parameter_record(
            "PR162C-PARAMETER-DELTA-FEE-BUFFER",
            "fee_buffer",
            0.01,
            "fraction",
            "OWNER_APPROVED_FORMULA_OR_VALUE_CANDIDATE",
            "OWNER_PR162C_INTERNAL_APPROVED_CANDIDATE",
        ),
        _parameter_record(
            "PR162C-PARAMETER-DELTA-LIQUIDITY-FRACTION-CAP",
            "liquidity_fraction_cap",
            0.25,
            "fraction",
            "OWNER_APPROVED_FORMULA_OR_VALUE_CANDIDATE",
            "OWNER_PR162C_INTERNAL_APPROVED_CANDIDATE",
        ),
    ]


def parameter_range_scale_delta_records(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "range_scale_id": parameter["parameter_id"].replace("PARAMETER", "RANGE-SCALE"),
            "parameter_ref": parameter["parameter_id"],
            "parameter_name": parameter["parameter_name"],
            "minimum": 0.0,
            "maximum": 1.0,
            "scale": "linear_fraction",
            "source_class": parameter["source_class"],
            "source_locator": parameter["source_locator"],
            "authority_class": c.AUTHORITY_CLASS,
            "candidate_provisional_flag": True,
            "not_live_authority": True,
            "created_by_pr": c.PR_ID,
        }
        for parameter in parameters
    ]


def tradable_value_candidate_delta_records(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "tradable_value_candidate_id": parameter["parameter_id"].replace("PARAMETER", "TRADABLE-VALUE"),
            "parameter_ref": parameter["parameter_id"],
            "value_name": parameter["parameter_name"],
            "value": parameter["value"],
            "unit": parameter["unit"],
            "candidate_use": "REPLAY_PAPER_PARAMETER_CANDIDATE_ONLY",
            "source_class": parameter["source_class"],
            "source_locator": parameter["source_locator"],
            "authority_class": c.AUTHORITY_CLASS,
            "candidate_provisional_flag": True,
            "not_live_authority": True,
            "created_by_pr": c.PR_ID,
        }
        for parameter in parameters
    ]


def solver_mapping_delta_records(formulas: list[dict[str, Any]], algorithms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    algorithm_by_name = {record["algorithm_name"]: record["algorithm_id"] for record in algorithms}
    qubo_formula = next(record for record in formulas if record["formula_name"] == "QUBO-to-Ising mapping candidate")
    penalty_formula = next(record for record in formulas if record["formula_name"] == "constraint_penalty")
    return [
        {
            "solver_mapping_id": "PR162C-SOLVER-MAPPING-DELTA-QUBO-TO-ISING-ASSEMBLY",
            "qku_id_refs": [],
            "formula_refs": [qubo_formula["formula_id"]],
            "algorithm_refs": [algorithm_by_name["qubo_input_assembly_audit"]],
            "objective_refs": [],
            "constraint_refs": [penalty_formula["formula_id"]],
            "compatible_solver_family": "QUBO_TO_ISING_INPUT_ASSEMBLY_ONLY",
            "input_representation": "QUBO_MATRIX_TO_ISING_H_J",
            "implementation_status": "IMPLEMENTED_SOLVER_INPUT_ASSEMBLY_ONLY",
            "source_class": "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE",
            "source_locator": "https://qiskit-community.github.io/qiskit-optimization/",
            "authority_class": c.AUTHORITY_CLASS,
            "candidate_provisional_flag": True,
            "evidence_execution_allowed_flag": False,
            "live_execution_allowed_flag": False,
            "not_live_authority": True,
            "created_by_pr": c.PR_ID,
        },
        {
            "solver_mapping_id": "PR162C-SOLVER-MAPPING-DELTA-QUBO-METADATA-ASSEMBLY",
            "qku_id_refs": [],
            "formula_refs": [penalty_formula["formula_id"]],
            "algorithm_refs": [algorithm_by_name["qubo_input_assembly_audit"]],
            "objective_refs": [],
            "constraint_refs": [penalty_formula["formula_id"]],
            "compatible_solver_family": "QUBO_INPUT_ASSEMBLY_ONLY",
            "input_representation": "QUBO_MATRIX",
            "implementation_status": "IMPLEMENTED_SOLVER_INPUT_ASSEMBLY_ONLY",
            "source_class": "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE",
            "source_locator": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
            "authority_class": c.AUTHORITY_CLASS,
            "candidate_provisional_flag": True,
            "evidence_execution_allowed_flag": False,
            "live_execution_allowed_flag": False,
            "not_live_authority": True,
            "created_by_pr": c.PR_ID,
        },
    ]


def executable_compute_contract_delta_records(
    formulas: list[dict[str, Any]],
    algorithms: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []
    for record in formulas:
        output.append(
            {
                "compute_contract_id": record["formula_id"].replace("FORMULA", "COMPUTE-CONTRACT"),
                "artifact_ref": record["formula_id"],
                "artifact_type": "FORMULA_DELTA",
                "implementation_module": record["implementation_module"],
                "implementation_function": record["implementation_function"],
                "test_vector_refs": record["test_vector_refs"],
                "execution_scope": "LOCAL_DETERMINISTIC_NO_REPLAY_PAPER_RESULT",
                "not_live_authority": True,
                "created_by_pr": c.PR_ID,
            }
        )
    for record in algorithms:
        output.append(
            {
                "compute_contract_id": record["algorithm_id"].replace("ALGORITHM", "COMPUTE-CONTRACT"),
                "artifact_ref": record["algorithm_id"],
                "artifact_type": "ALGORITHM_DELTA",
                "implementation_module": record["implementation_module"],
                "implementation_function": record["implementation_function"],
                "test_vector_refs": record["test_vector_refs"],
                "execution_scope": "LOCAL_DETERMINISTIC_NO_REPLAY_PAPER_RESULT",
                "not_live_authority": True,
                "created_by_pr": c.PR_ID,
            }
        )
    return output


def _parameter_record(
    parameter_id: str,
    name: str,
    value: float,
    unit: str,
    source_class: str,
    source_locator: str,
) -> dict[str, Any]:
    return {
        "parameter_id": parameter_id,
        "parameter_name": name,
        "value": value,
        "unit": unit,
        "source_class": source_class,
        "source_locator": source_locator,
        "source_title": "Owner-approved PR162C internal value candidate",
        "authority_class": c.AUTHORITY_CLASS,
        "candidate_provisional_flag": True,
        "official_truth_flag": False,
        "not_official_truth_if_non_official": True,
        "not_live_authority": True,
        "created_by_pr": c.PR_ID,
    }


def _common_delta(record: dict[str, Any], kind: str) -> dict[str, Any]:
    return {
        f"{kind}_source_formula_ref": record["formula_id"],
        "mathematical_expression": record["mathematical_expression"],
        "plain_english_definition": record["plain_english_definition"],
        "variables": record["variables"],
        "units": record["units"],
        "valid_input_domain": record["valid_input_domain"],
        "invalid_input_conditions": record["invalid_input_conditions"],
        "missing_value_policy": record["missing_value_policy"],
        "normalization_policy": record["normalization_policy"],
        "source_class": record["source_class"],
        "source_locator": record["source_locator"],
        "source_title": record["source_title"],
        "authority_class": c.AUTHORITY_CLASS,
        "candidate_provisional_flag": True,
        "not_live_authority": True,
        "test_vector_refs": record["test_vector_refs"],
        "created_by_pr": c.PR_ID,
    }


def build_delta_bundle() -> dict[str, list[dict[str, Any]]]:
    formulas = formula_delta_records()
    algorithms = algorithm_delta_records()
    parameters = parameter_value_delta_records()
    return {
        "formulas": formulas,
        "formula_tests": formula_test_vector_delta_records(),
        "algorithms": algorithms,
        "algorithm_tests": [],
        "objectives": objective_delta_records(formulas),
        "constraints": constraint_delta_records(formulas),
        "parameters": parameters,
        "ranges": parameter_range_scale_delta_records(parameters),
        "tradable_values": tradable_value_candidate_delta_records(parameters),
        "solver_mappings": solver_mapping_delta_records(formulas, algorithms),
        "compute_contracts": executable_compute_contract_delta_records(formulas, algorithms),
    }
