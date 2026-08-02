"""Data-only independent-oracle and golden-vector contract materialization."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import json
from types import MappingProxyType
from typing import Mapping
import zlib

from .errors import ContractValidationError, ReasonCode
from .models import GoldenVectorV1, OracleContractV1


@dataclass(frozen=True, slots=True)
class OraclePackEntryV1:
    oracle: OracleContractV1
    vector: GoldenVectorV1
    oracle_row_json: str
    vector_row_json: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.oracle, OracleContractV1)
            or not isinstance(self.vector, GoldenVectorV1)
            or self.oracle.math_spec_id != self.vector.math_spec_id
            or self.oracle.oracle_id != self.vector.oracle_id
        ):
            raise ContractValidationError(
                ReasonCode.ORACLE_NOT_INDEPENDENT,
                "oracle and golden-vector lineage do not match",
            )
        for name in ("oracle_row_json", "vector_row_json"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.ORACLE_NOT_INDEPENDENT,
                    f"{name} must be nonempty canonical JSON",
                )
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ContractValidationError(
                    ReasonCode.ORACLE_NOT_INDEPENDENT,
                    f"{name} is not valid JSON",
                ) from exc
            if not isinstance(parsed, dict):
                raise ContractValidationError(
                    ReasonCode.ORACLE_NOT_INDEPENDENT,
                    f"{name} must encode an object",
                )


_ORACLE_ROWS_JSON = r'''
[
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_DECIMAL",
  "expected_value_or_invariant": {
    "p_market": "0.42"
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-01",
  "math_spec_ref": "MATH-01",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-01",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "ABS_TOL_1E-15",
  "expected_value_or_invariant": {
    "edge_probability": "0.06"
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-02",
  "math_spec_ref": "MATH-02",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-02",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_DECIMAL",
  "expected_value_or_invariant": {
    "mid": "0.43"
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-03",
  "math_spec_ref": "MATH-03",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-03",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_DECIMAL",
  "expected_value_or_invariant": {
    "spread": "0.02"
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-04",
  "math_spec_ref": "MATH-04",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-04",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT",
  "expected_value_or_invariant": {
    "relative_spread": "0.04651162790697674418604651162790698"
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-05",
  "math_spec_ref": "MATH-05",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-05",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_DECIMAL",
  "expected_value_or_invariant": {
    "expected_net_cash": "0.14"
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-06",
  "math_spec_ref": "MATH-06",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-06",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_DECIMAL",
  "expected_value_or_invariant": {
    "expected_net_cash": "0.17"
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-07",
  "math_spec_ref": "MATH-07",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-07",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_DECIMAL",
  "expected_value_or_invariant": {
    "brier_score": "0.09"
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-08",
  "math_spec_ref": "MATH-08",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-08",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "ABS_TOL_1E-15",
  "expected_value_or_invariant": {
    "log_loss": 0.35667494393873245
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-09",
  "math_spec_ref": "MATH-09",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-09",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "ABS_TOL_1E-15",
  "expected_value_or_invariant": {
    "ece": 0.25
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-10",
  "math_spec_ref": "MATH-10",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-10",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "ABS_TOL_1E-12",
  "expected_value_or_invariant": {
    "lower": 0.49015684672072335,
    "upper": 0.9433190520193067
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-11",
  "math_spec_ref": "MATH-11",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-11",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_ORDER_AND_INDEX_SET",
  "expected_value_or_invariant": {
    "largest_rank": 2,
    "rejected_original_indices": [
      0,
      1
    ]
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-12",
  "math_spec_ref": "MATH-12",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT",
  "oracle_id": "ORACLE::MATH-12",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_ORDER_AND_INDEX_SET",
  "expected_value_or_invariant": {
    "largest_rank": 2,
    "rejected_original_indices": [
      0,
      1
    ]
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-13",
  "math_spec_ref": "MATH-13",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT",
  "oracle_id": "ORACLE::MATH-13",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "BOOLEAN_INVARIANTS",
  "expected_value_or_invariant": {
    "interval_contains_sample_mean": true,
    "same_seed_reproducible": true
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-14",
  "math_spec_ref": "MATH-14",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT",
  "oracle_id": "ORACLE::MATH-14",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "ABS_TOL_1E-15",
  "expected_value_or_invariant": {
    "p_value": 1.0,
    "reject": false
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-15",
  "math_spec_ref": "MATH-15",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT",
  "oracle_id": "ORACLE::MATH-15",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "ABS_TOL_1E-15",
  "expected_value_or_invariant": {
    "energy": 4.6
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-46",
  "math_spec_ref": "MATH-46",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE",
  "oracle_id": "ORACLE::MATH-46",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "ENUMERATION_INVARIANT",
  "expected_value_or_invariant": {
    "all_binary_assignments_energy_equal_after_ising_transform": true,
    "assignment_count": 4
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-47",
  "math_spec_ref": "MATH-47",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT",
  "oracle_id": "ORACLE::MATH-47",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "BRUTE_FORCE_ENUMERATION",
  "expected_value_or_invariant": {
    "all_returned_solutions_feasible": true,
    "optimal_objective": 1
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-48",
  "math_spec_ref": "MATH-48",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT",
  "oracle_id": "ORACLE::MATH-48",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
},
{
  "codex_online_research_allowed": false,
  "codex_research_required": false,
  "comparison_policy": "EXACT_DISCRETE_ENUMERATION",
  "expected_value_or_invariant": {
    "minimum_energy_assignment": {
      "a": "A0",
      "b": "B0"
    },
    "one_case_per_variable": true
  },
  "independence_proof": "ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE",
  "independent_algorithm_steps": [
    "Parse the golden-vector inputs without importing the production implementation.",
    "Apply the independently stated formula, enumeration, resampling, or invariant procedure.",
    "Compare every declared output using the vector comparison policy.",
    "Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."
  ],
  "input_fixture_ref": "GOLDEN::MATH-49",
  "math_spec_ref": "MATH-49",
  "mutation_targets_required": [
    "FORMULA_OR_PROCEDURE",
    "DOMAIN_GUARD",
    "PRECISION_OR_TOLERANCE",
    "SOURCE_OR_UNIT_BINDING"
  ],
  "oracle_class": "INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT",
  "oracle_id": "ORACLE::MATH-49",
  "oracle_version": "1.1R1",
  "primary_validator_expected_value_import_allowed": false,
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION",
  "specification_gap_count": 0
}
]
'''

_GOLDEN_VECTOR_ROWS_JSON = r'''
[
{
  "comparison_policy": "EXACT_DECIMAL",
  "expected": {
    "p_market": "0.42"
  },
  "inputs": {
    "contract_price": "0.42",
    "payout_per_winning_contract": "1.00"
  },
  "math_spec_ref": "MATH-01",
  "oracle_ref": "ORACLE::MATH-01",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-01",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "ABS_TOL_1E-15",
  "expected": {
    "edge_probability": "0.06"
  },
  "inputs": {
    "calibrated_model_probability": "0.58",
    "market_implied_probability": "0.52"
  },
  "math_spec_ref": "MATH-02",
  "oracle_ref": "ORACLE::MATH-02",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-02",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "EXACT_DECIMAL",
  "expected": {
    "mid": "0.43"
  },
  "inputs": {
    "best_ask": "0.44",
    "best_bid": "0.42"
  },
  "math_spec_ref": "MATH-03",
  "oracle_ref": "ORACLE::MATH-03",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-03",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "EXACT_DECIMAL",
  "expected": {
    "spread": "0.02"
  },
  "inputs": {
    "best_ask": "0.44",
    "best_bid": "0.42"
  },
  "math_spec_ref": "MATH-04",
  "oracle_ref": "ORACLE::MATH-04",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-04",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT",
  "expected": {
    "relative_spread": "0.04651162790697674418604651162790698"
  },
  "inputs": {
    "best_ask": "0.44",
    "best_bid": "0.42"
  },
  "math_spec_ref": "MATH-05",
  "oracle_ref": "ORACLE::MATH-05",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-05",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "EXACT_DECIMAL",
  "expected": {
    "expected_net_cash": "0.14"
  },
  "inputs": {
    "acquisition_cost": "0",
    "expected_impact": "0",
    "expected_slippage": "0",
    "fees": "0.01",
    "lose_cash": "-0.45",
    "p": "0.60",
    "quantity": "1",
    "win_cash": "0.55"
  },
  "math_spec_ref": "MATH-06",
  "oracle_ref": "ORACLE::MATH-06",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-06",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "EXACT_DECIMAL",
  "expected": {
    "expected_net_cash": "0.17"
  },
  "inputs": {
    "acquisition_cost": "0.02",
    "expected_impact": "0",
    "expected_slippage": "0",
    "fees": "0",
    "payoffs": [
      "1.0",
      "-0.2",
      "0.1"
    ],
    "probabilities": [
      "0.2",
      "0.3",
      "0.5"
    ],
    "quantity": "1"
  },
  "math_spec_ref": "MATH-07",
  "oracle_ref": "ORACLE::MATH-07",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-07",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "EXACT_DECIMAL",
  "expected": {
    "brier_score": "0.09"
  },
  "inputs": {
    "p": "0.70",
    "y": 1
  },
  "math_spec_ref": "MATH-08",
  "oracle_ref": "ORACLE::MATH-08",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-08",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "ABS_TOL_1E-15",
  "expected": {
    "log_loss": 0.35667494393873245
  },
  "inputs": {
    "clip_epsilon": 1e-15,
    "p": 0.7,
    "y": 1
  },
  "math_spec_ref": "MATH-09",
  "oracle_ref": "ORACLE::MATH-09",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-09",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "ABS_TOL_1E-15",
  "expected": {
    "ece": 0.25
  },
  "inputs": {
    "bins": [
      {
        "count": 2,
        "empirical_frequency": 0.5,
        "mean_confidence": 0.8
      },
      {
        "count": 2,
        "empirical_frequency": 0.5,
        "mean_confidence": 0.3
      }
    ]
  },
  "math_spec_ref": "MATH-10",
  "oracle_ref": "ORACLE::MATH-10",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-10",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "ABS_TOL_1E-12",
  "expected": {
    "lower": 0.49016247153664183,
    "upper": 0.9433178485456247
  },
  "inputs": {
    "successes": 8,
    "trials": 10,
    "confidence": 0.95
  },
  "math_spec_ref": "MATH-11",
  "oracle_ref": "ORACLE::MATH-11",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-11",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "EXACT_ORDER_AND_INDEX_SET",
  "expected": {
    "largest_rank": 2,
    "rejected_original_indices": [
      0,
      1
    ]
  },
  "inputs": {
    "p_values": [
      0.001,
      0.01,
      0.04,
      0.2
    ],
    "q": 0.05
  },
  "math_spec_ref": "MATH-12",
  "oracle_ref": "ORACLE::MATH-12",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": 1201,
  "vector_id": "GOLDEN::MATH-12",
  "vector_kind": "STRUCTURAL_INVARIANT"
},
{
  "comparison_policy": "EXACT_ORDER_AND_INDEX_SET",
  "expected": {
    "largest_rank": 2,
    "rejected_original_indices": [
      0,
      1
    ]
  },
  "inputs": {
    "p_values": [
      0.001,
      0.01,
      0.04,
      0.2
    ],
    "q": 0.05
  },
  "math_spec_ref": "MATH-13",
  "oracle_ref": "ORACLE::MATH-13",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": 1301,
  "vector_id": "GOLDEN::MATH-13",
  "vector_kind": "STRUCTURAL_INVARIANT"
},
{
  "comparison_policy": "BOOLEAN_INVARIANTS",
  "expected": {
    "interval_contains_sample_mean": true,
    "same_seed_reproducible": true
  },
  "inputs": {
    "expected_block_length": 2,
    "replicates": 64,
    "seed": 1401,
    "series": [
      1,
      2,
      3,
      4,
      5
    ]
  },
  "math_spec_ref": "MATH-14",
  "oracle_ref": "ORACLE::MATH-14",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": 1401,
  "vector_id": "GOLDEN::MATH-14",
  "vector_kind": "STRUCTURAL_INVARIANT"
},
{
  "comparison_policy": "ABS_TOL_1E-15",
  "expected": {
    "p_value": 0.0,
    "reject": true
  },
  "inputs": {
    "loss_differentials": [
      [
        1
      ],
      [
        1
      ],
      [
        1
      ],
      [
        1
      ]
    ],
    "replicates": 64,
    "seed": 1501
  },
  "math_spec_ref": "MATH-15",
  "oracle_ref": "ORACLE::MATH-15",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": 1501,
  "vector_id": "GOLDEN::MATH-15",
  "vector_kind": "STRUCTURAL_INVARIANT"
},
{
  "comparison_policy": "ABS_TOL_1E-15",
  "expected": {
    "energy": 4.6
  },
  "inputs": {
    "diagonal": [
      1,
      2,
      3
    ],
    "offset": 0.1,
    "upper_terms": [
      {
        "i": 0,
        "j": 2,
        "value": 0.5
      }
    ],
    "x": [
      1,
      0,
      1
    ]
  },
  "math_spec_ref": "MATH-46",
  "oracle_ref": "ORACLE::MATH-46",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": null,
  "vector_id": "GOLDEN::MATH-46",
  "vector_kind": "NUMERIC_GOLDEN"
},
{
  "comparison_policy": "ENUMERATION_INVARIANT",
  "expected": {
    "all_binary_assignments_energy_equal_after_ising_transform": true,
    "assignment_count": 4
  },
  "inputs": {
    "qubo": {
      "diagonal": [
        1,
        2
      ],
      "offset": 0.1,
      "upper_terms": [
        {
          "i": 0,
          "j": 1,
          "value": 0.5
        }
      ]
    }
  },
  "math_spec_ref": "MATH-47",
  "oracle_ref": "ORACLE::MATH-47",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": 4701,
  "vector_id": "GOLDEN::MATH-47",
  "vector_kind": "STRUCTURAL_INVARIANT"
},
{
  "comparison_policy": "BRUTE_FORCE_ENUMERATION",
  "expected": {
    "all_returned_solutions_feasible": true,
    "optimal_objective": 1
  },
  "inputs": {
    "constraints": [
      "x+y<=1"
    ],
    "domains": {
      "x": "BINARY",
      "y": "BINARY"
    },
    "objective": "maximize x+y"
  },
  "math_spec_ref": "MATH-48",
  "oracle_ref": "ORACLE::MATH-48",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": 4801,
  "vector_id": "GOLDEN::MATH-48",
  "vector_kind": "STRUCTURAL_INVARIANT"
},
{
  "comparison_policy": "EXACT_DISCRETE_ENUMERATION",
  "expected": {
    "minimum_energy_assignment": {
      "a": "A0",
      "b": "B0"
    },
    "one_case_per_variable": true
  },
  "inputs": {
    "discrete_variables": {
      "a": [
        "A0",
        "A1"
      ],
      "b": [
        "B0",
        "B1"
      ]
    },
    "linear_biases": {
      "A0": 0,
      "A1": 1,
      "B0": 0,
      "B1": 1
    },
    "pairwise_biases": {}
  },
  "math_spec_ref": "MATH-49",
  "oracle_ref": "ORACLE::MATH-49",
  "precision_context": "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE",
  "production_implementation_import_allowed": false,
  "research_completeness_state": "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT",
  "seed": 4901,
  "vector_id": "GOLDEN::MATH-49",
  "vector_kind": "STRUCTURAL_INVARIANT"
}
]
'''


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _oracle(row: object) -> OracleContractV1:
    if not isinstance(row, dict):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT, "oracle row must be an object"
        )
    for field_name in (
        "codex_online_research_allowed",
        "codex_research_required",
        "production_implementation_import_allowed",
        "primary_validator_expected_value_import_allowed",
    ):
        if type(row[field_name]) is not bool:
            raise ContractValidationError(
                ReasonCode.ORACLE_NOT_INDEPENDENT,
                f"{field_name} must be a boolean",
            )
    if (
        row["codex_online_research_allowed"]
        or row["codex_research_required"]
        or row["production_implementation_import_allowed"]
        or row["primary_validator_expected_value_import_allowed"]
        or row.get("specification_gap_count") != 0
        or row.get("research_completeness_state")
        != "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION"
        or not isinstance(row.get("independence_proof"), str)
        or not row["independence_proof"]
        or not isinstance(row.get("mutation_targets_required"), list)
        or not row["mutation_targets_required"]
    ):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "oracle row is not terminal, independent, and effect-free",
        )
    return OracleContractV1(
        oracle_id=str(row["oracle_id"]),
        math_spec_id=str(row["math_spec_ref"]),
        oracle_version=str(row["oracle_version"]),
        comparison_policy=str(row["comparison_policy"]),
        expected_value_json=_canonical(row["expected_value_or_invariant"]),
        independent_algorithm_steps=tuple(
            str(value) for value in row["independent_algorithm_steps"]
        ),
        production_import_allowed=row[
            "production_implementation_import_allowed"
        ],
        primary_validator_import_allowed=row[
            "primary_validator_expected_value_import_allowed"
        ],
    )


def _vector(row: object) -> GoldenVectorV1:
    if not isinstance(row, dict):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT, "golden-vector row must be an object"
        )
    if type(row["production_implementation_import_allowed"]) is not bool:
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "golden-vector production import flag must be a boolean",
        )
    if (
        row["production_implementation_import_allowed"]
        or row.get("research_completeness_state")
        != "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT"
        or row.get("precision_context")
        != "DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE"
    ):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "golden-vector row is not terminal and independently usable",
        )
    seed = row["seed"]
    if seed is not None and (
        isinstance(seed, bool) or not isinstance(seed, int)
    ):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "golden-vector seed must be an integer when declared",
        )
    return GoldenVectorV1(
        vector_id=str(row["vector_id"]),
        math_spec_id=str(row["math_spec_ref"]),
        oracle_id=str(row["oracle_ref"]),
        vector_kind=str(row["vector_kind"]),
        comparison_policy=str(row["comparison_policy"]),
        inputs_json=_canonical(row["inputs"]),
        expected_json=_canonical(row["expected"]),
        seed=seed,
        production_import_allowed=row[
            "production_implementation_import_allowed"
        ],
    )


def _load_pack() -> tuple[OraclePackEntryV1, ...]:
    oracle_rows = json.loads(_ORACLE_ROWS_JSON)
    vector_rows = json.loads(_GOLDEN_VECTOR_ROWS_JSON)
    if not isinstance(oracle_rows, list) or not isinstance(vector_rows, list):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "oracle materialization must contain typed row lists",
        )
    oracle_contracts = tuple(_oracle(row) for row in oracle_rows)
    vector_contracts = tuple(_vector(row) for row in vector_rows)
    oracles = {
        contract.math_spec_id: (contract, row)
        for contract, row in zip(oracle_contracts, oracle_rows, strict=True)
    }
    vectors = {
        contract.math_spec_id: (contract, row)
        for contract, row in zip(vector_contracts, vector_rows, strict=True)
    }
    if (
        len(oracles) != 19
        or len(vectors) != 19
        or set(oracles) != set(vectors)
    ):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "oracle pack must contain 19 aligned oracle/vector pairs",
        )
    expected_math_ids = (
        *(f"MATH-{index:02d}" for index in range(1, 16)),
        "MATH-46",
        "MATH-47",
        "MATH-48",
        "MATH-49",
    )
    if set(oracles) != set(expected_math_ids) or any(
        oracle.oracle_id != f"ORACLE::{math_id}"
        or oracle.oracle_version != "1.1R1"
        or vector.vector_id != f"GOLDEN::{math_id}"
        or vector.oracle_id != oracle.oracle_id
        or vector.comparison_policy != oracle.comparison_policy
        for math_id in expected_math_ids
        for oracle, vector in (
            (oracles[math_id][0], vectors[math_id][0]),
        )
    ):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "oracle/vector identities or versions do not match the 19-row registry",
        )
    return tuple(
        OraclePackEntryV1(
            oracle=oracles[math_id][0],
            vector=vectors[math_id][0],
            oracle_row_json=_canonical(oracles[math_id][1]),
            vector_row_json=_canonical(vectors[math_id][1]),
        )
        for math_id in sorted(
            oracles,
            key=lambda value: int(value.split("-")[1]),
        )
    )


ORACLE_PACK = _load_pack()
ORACLE_BY_MATH_ID: Mapping[str, OracleContractV1] = MappingProxyType(
    {entry.oracle.math_spec_id: entry.oracle for entry in ORACLE_PACK}
)
GOLDEN_VECTOR_BY_MATH_ID: Mapping[str, GoldenVectorV1] = MappingProxyType(
    {entry.vector.math_spec_id: entry.vector for entry in ORACLE_PACK}
)


def get_oracle(math_spec_id: str) -> OracleContractV1:
    if not isinstance(math_spec_id, str) or not math_spec_id:
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "oracle math identity must be nonempty text",
        )
    try:
        return ORACLE_BY_MATH_ID[math_spec_id]
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            f"no independent oracle for {math_spec_id}",
        ) from exc


def get_golden_vector(math_spec_id: str) -> GoldenVectorV1:
    if not isinstance(math_spec_id, str) or not math_spec_id:
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "golden-vector math identity must be nonempty text",
        )
    try:
        return GOLDEN_VECTOR_BY_MATH_ID[math_spec_id]
    except KeyError as exc:
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            f"no golden vector for {math_spec_id}",
        ) from exc


# BEGIN GENERATED ST12B V3.4 OWNER-FROZEN DATA
_ST12B_ORACLE_CONTRACTS_JSON = (
    '[{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["contract_price","payout_per_winning_contract"],"math_spec_id":"MATH-01","module_path":"independent_oracle_reference/economics_microstructure.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-01::V3_4","output_schema_ref":"MATH-01::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["R'
    'AW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["calibrated_model_probability","market_implied_probability","calibration_state"],"math_spec_id":"MATH-02","module_path":"independent_oracle_reference/economics_microstructure.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-02::V3_4","output_schema_ref":"MATH-02::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATI'
    'ON"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"math_spec_id":"MATH-03","module_path":"independent_oracle_reference/economics_microstructure.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-03::V3_4","output_schema_ref":"MATH-03::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODU'
    'CTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"math_spec_id":"MATH-04","module_path":"independent_oracle_reference/economics_microstructure.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-04::V3_4","output_schema_ref":"MATH-04::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTE'
    'S_FROM_RAW_DECLARED_INPUTS"],"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"math_spec_id":"MATH-05","module_path":"independent_oracle_reference/economics_microstructure.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-05::V3_4","output_schema_ref":"MATH-05::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["p_win","p_void","fill_'
    'probability","entry_trade_cashflow_total","win_terminal_cashflow_total","lose_terminal_cashflow_total","void_terminal_cashflow_total","no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total","cashflow_basis"],"math_spec_id":"MATH-06","module_path":"independent_oracle_reference/economics_microstructure.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-06::V3_4","output_schema_ref":"MATH-06::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable'
    '_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["outcome_ids","outcome_probabilities","outcome_terminal_cashflow_totals","probability_simplex_tolerance","fill_probability","entry_trade_cashflow_total","no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total","cashflow_basis"],"math_spec_id":"MATH-07","module_path":"independent_oracle_reference/economics_microstructure.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-07::V3_4","output_schema_ref":"MATH-07::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_T'
    'YPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["probability_rows","outcome_indices"],"math_spec_id":"MATH-08","module_path":"independent_oracle_reference/scoring_statistics.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-08::V3_4","output_schema_ref":"MATH-08::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"N'
    'OT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["probability_rows","outcome_indices","clip_epsilon"],"math_spec_id":"MATH-09","module_path":"independent_oracle_reference/scoring_statistics.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-09::V3_4","output_schema_ref":"MATH-09::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispa'
    'tcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["probabilities","outcomes","bin_policy","bin_count"],"math_spec_id":"MATH-10","module_path":"independent_oracle_reference/scoring_statistics.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-10::V3_4","output_schema_ref":"MATH-10::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLAR'
    'ED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["successes","trials","confidence"],"math_spec_id":"MATH-11","module_path":"independent_oracle_reference/scoring_statistics.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-11::V3_4","output_schema_ref":"MATH-11::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_'
    'PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["p_values","q"],"math_spec_id":"MATH-12","module_path":"independent_oracle_reference/scoring_statistics.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-12::V3_4","output_schema_ref":"MATH-12::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["p_values","q"],"m'
    'ath_spec_id":"MATH-13","module_path":"independent_oracle_reference/scoring_statistics.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-13::V3_4","output_schema_ref":"MATH-13::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["series","expected_block_length","seed","replicates","confidence","interval_method"],"math_spec_id":"MATH-14","module_path":"independent_oracle_refere'
    'nce/scoring_statistics.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-14::V3_4","output_schema_ref":"MATH-14::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["loss_differentials","sign_convention","seed","replicates","expected_block_length","alpha"],"math_spec_id":"MATH-15","module_path":"independent_oracle_reference/model_risk_validation.py","oracle_class":"ANALYTIC_O'
    'R_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-15::V3_4","output_schema_ref":"MATH-15::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_15","secondary_route_state":"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["loss_differentials","sign_convention","seed","replicates","expected_block_length","alpha","recenter_variant"],"math_spec_id":"MATH-16","module_path":"independent_oracle_reference/model_risk_validation.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-16::V3_4","output_schema_'
    'ref":"MATH-16::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_16","secondary_route_state":"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["estimated_sharpe","reference_sharpe","independent_equivalent_observations","sample_skewness","sample_non_excess_kurtosis"],"math_spec_id":"MATH-17","module_path":"independent_oracle_reference/model_risk_validation.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-17::V3_4","output_schema_ref":"MATH-17::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route'
    '_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["complete_material_trial_sharpes","effective_independent_trial_count","candidate_estimated_sharpe","candidate_independent_equivalent_observations","candidate_sample_skewness","candidate_sample_non_excess_kurtosis"],"math_spec_id":"MATH-18","module_path":"independent_oracle_reference/model_risk_validation.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-18::V3_4","output_schema_ref":"MATH-18'
    '::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_18","secondary_route_state":"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["performance_matrix","strategy_ids","S"],"math_spec_id":"MATH-19","module_path":"independent_oracle_reference/model_risk_validation.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-19::V3_4","output_schema_ref":"MATH-19::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_19","secondary_route_state":'
    '"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["sample_intervals","folds","embargo_duration"],"math_spec_id":"MATH-20","module_path":"independent_oracle_reference/model_risk_validation.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-20::V3_4","output_schema_ref":"MATH-20::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_20","secondary_route_state":"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["'
    'RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["sample_intervals","N_groups","k_test_groups","embargo_duration","aggregation_rule"],"math_spec_id":"MATH-21","module_path":"independent_oracle_reference/model_risk_validation.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-21::V3_4","output_schema_ref":"MATH-21::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_21","secondary_route_state":"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO'
    '_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["logged_rows"],"math_spec_id":"MATH-22","module_path":"independent_oracle_reference/off_policy.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-22::V3_4","output_schema_ref":"MATH-22::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["logged_rows"],"math_spec_'
    'id":"MATH-23","module_path":"independent_oracle_reference/off_policy.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-23::V3_4","output_schema_ref":"MATH-23::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["weights","rewards"],"math_spec_id":"MATH-24","module_path":"independent_oracle_reference/off_policy.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PR'
    'OCEDURE","oracle_id":"ORACLE::MATH-24::V3_4","output_schema_ref":"MATH-24::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["logged_rows","tau_grid","outer_fold_count","reward_lower_bound","reward_upper_bound"],"math_spec_id":"MATH-25","module_path":"independent_oracle_reference/off_policy.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-25::V3_4","output_schema_ref":"MAT'
    'H-25::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_25","secondary_route_state":"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["RAW_DECLARED_INPUT_EXECUTION","GOLDEN_BOUNDARY_NEGATIVE_MUTATION"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["yes_bids","no_bids","payout","book_sequence","expected_sequence","book_state","price_ranges"],"math_spec_id":"MATH-36","module_path":"independent_oracle_reference/economics_microstructure.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-36::V3_4","output_schema_ref":"MATH-36::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_RE'
    'ASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["DIRECT_ASSIGNMENT_ENERGY","EXHAUSTIVE_BINARY_ENUMERATION_N_LE_12","FULL_SYMMETRIC_TO_CANONICAL_ADAPTER"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["representation","diagonal","upper_terms","full_symmetric_matrix","constant","binary_assignment"],"math_spec_id":"MATH-46","module_path":"independent_oracle_reference/quantum_models.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-46::V3_4","output_schema_ref":"MATH-46::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_AN'
    'ALYTIC_OR_EXACT_REFERENCE_PLUS_METAMORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["IMMUTABLE_RAW_QUBO_CANONICALIZATION_ADAPTER","EXHAUSTIVE_QUBO_ISING_PARITY_N_LE_12"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["representation","diagonal","upper_terms","full_symmetric_matrix","constant","binary_assignment"],"math_spec_id":"MATH-47","module_path":"independent_oracle_reference/quantum_models.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-47::V3_4","output_schema_ref":"MATH-47::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"NOT_APPLICABLE_WITH_TYPED_REASON: PRIMARY_ANALYTIC_OR_EXACT_REFERENCE_PLUS_METAM'
    'ORPHIC_ROUTE_SUFFICIENT","secondary_route_state":"NOT_APPLICABLE_WITH_TYPED_REASON","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["FINITE_CQM_ENUMERATION_MAX_4096","ORIGINAL_MODEL_FEASIBILITY","EXPLICIT_ENUMERATION_VALUES_VALIDATION","CONVERSION_PENALTY_ADEQUACY"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["model","assignment"],"math_spec_id":"MATH-48","module_path":"independent_oracle_reference/quantum_models.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-48::V3_4","output_schema_ref":"MATH-48::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_48","secondary_route_state":"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_'
    'ORACLE_V3_4"},{"dispatcher_path":"independent_oracle_reference/dispatcher.py","executable_capabilities":["FINITE_DQM_CARTESIAN_ENUMERATION_MAX_4096","NATIVE_CASE_LABEL_INTERPRET_BACK"],"independence_controls":["NO_QTT_PRODUCTION_IMPORT","NO_PRODUCTION_RESULT_READ","NO_EVAL_EXEC","STANDARD_LIBRARY_ONLY","EXECUTES_FROM_RAW_DECLARED_INPUTS"],"input_keys":["model","assignment"],"math_spec_id":"MATH-49","module_path":"independent_oracle_reference/quantum_models.py","oracle_class":"ANALYTIC_OR_BRUTE_FORCE_OR_SEEDED_REFERENCE_PROCEDURE","oracle_id":"ORACLE::MATH-49::V3_4","output_schema_ref":"MATH-49::OUTPUT","output_schema_version":"ST12B_OUTPUT_V3_4","secondary_route_ref":"independent_oracle_reference/secondary_routes.py::check_math_49","secondary_route_state":"EXECUTABLE","terminal_state":"EXECUTABLE_INDEPENDENT_ORACLE_V3_4"}]'
)

_ST12B_VECTOR_PACK_JSON = (
    '[{"case_type":"GOLDEN","expected":"0.47","expected_exception":null,"input_keys":["contract_price","payout_per_winning_contract"],"inputs":{"contract_price":"0.47","payout_per_winning_contract":"1"},"math_spec_id":"MATH-01","vector_id":"VECTOR::MATH-01::GOLDEN"},{"case_type":"BOUNDARY","expected":"0","expected_exception":null,"input_keys":["contract_price","payout_per_winning_contract"],"inputs":{"contract_price":"0","payout_per_winning_contract":"1"},"math_spec_id":"MATH-01","vector_id":"VECTOR::MATH-01::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"require 0 <= contract_price <= positive payout","input_keys":["contract_price","payout_per_winning_contract"],"inputs":{"contract_price":"0.5","payout_per_winning_contract":"0"},"math_spec_id":"MATH-01","vector_id":"VECTOR::MATH-01::NEGATIVE"},{"case_type":"GOLDEN","expected":0.13,"expected_exception":null,"input_keys":["calibrated_model_probability","market_implied_probabi'
    'lity","calibration_state"],"inputs":{"calibrated_model_probability":0.61,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.48},"math_spec_id":"MATH-02","vector_id":"VECTOR::MATH-02::GOLDEN"},{"case_type":"BOUNDARY","expected":0.0,"expected_exception":null,"input_keys":["calibrated_model_probability","market_implied_probability","calibration_state"],"inputs":{"calibrated_model_probability":0.5,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.5},"math_spec_id":"MATH-02","vector_id":"VECTOR::MATH-02::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"calibration_state is not eligible","input_keys":["calibrated_model_probability","market_implied_probability","calibration_state"],"inputs":{"calibrated_model_probability":0.61,"calibration_state":"UNCALIBRATED","market_implied_probability":0.48},"math_spec_id":"MATH-02","vector_id":"VECTOR::MATH-02::NEGATIVE"},'
    '{"case_type":"GOLDEN","expected":"0.48","expected_exception":null,"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0.50","best_bid":"0.46","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-03","vector_id":"VECTOR::MATH-03::GOLDEN"},{"case_type":"BOUNDARY","expected":"0.5","expected_exception":null,"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0.5","best_bid":"0.5","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-03","vector_id":"VECTOR::MATH-03::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"snapshot is stale, gapped, or invalid","input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0.50","best_bid":"0.46","payout":"1'
    '","same_instrument_snapshot":true,"snapshot_state":"SEQUENCE_GAP"},"math_spec_id":"MATH-03","vector_id":"VECTOR::MATH-03::NEGATIVE"},{"case_type":"GOLDEN","expected":"0.04","expected_exception":null,"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0.50","best_bid":"0.46","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-04","vector_id":"VECTOR::MATH-04::GOLDEN"},{"case_type":"BOUNDARY","expected":"0","expected_exception":null,"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0.5","best_bid":"0.5","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-04","vector_id":"VECTOR::MATH-04::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"invalid uncrossed book","input_keys":["best_bid","best_'
    'ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0.5","best_bid":"0.6","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-04","vector_id":"VECTOR::MATH-04::NEGATIVE"},{"case_type":"GOLDEN","expected":{"relative_spread_bps":"833.3333333333333333333333333333333","relative_spread_ratio":"0.08333333333333333333333333333333333"},"expected_exception":null,"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0.50","best_bid":"0.46","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-05","vector_id":"VECTOR::MATH-05::GOLDEN"},{"case_type":"BOUNDARY","expected":{"relative_spread_bps":"20000","relative_spread_ratio":"2"},"expected_exception":null,"input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0.02","best_bid":"0","payout":"1","'
    'same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-05","vector_id":"VECTOR::MATH-05::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"midpoint must be positive","input_keys":["best_bid","best_ask","payout","same_instrument_snapshot","snapshot_state"],"inputs":{"best_ask":"0","best_bid":"0","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-05","vector_id":"VECTOR::MATH-05::NEGATIVE"},{"case_type":"GOLDEN","expected":{"expected_net_cash":"1.248","expected_net_cash_if_filled":"1.56","expected_terminal_cashflow":"6.47","p_lose":"0.3"},"expected_exception":null,"input_keys":["p_win","p_void","fill_probability","entry_trade_cashflow_total","win_terminal_cashflow_total","lose_terminal_cashflow_total","void_terminal_cashflow_total","no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_re'
    'bate_total","exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total","cashflow_basis"],"inputs":{"builder_fee_total":"0","capital_time_cost_reserve_total":"0.01","cashflow_basis":"SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE","entry_trade_cashflow_total":"-4.7","exit_slippage_reserve_total":"0.05","expected_rebate_total":"0","fill_probability":"0.8","latency_adverse_selection_reserve_total":"0.03","lose_terminal_cashflow_total":"0","market_impact_reserve_total":"0.02","no_fill_cashflow_total":"0","other_fee_total":"0","p_void":"0.1","p_win":"0.6","platform_fee_total":"0.1","void_terminal_cashflow_total":"4.7","win_terminal_cashflow_total":"10"},"invariant_assertions":["p_win + p_lose + p_void = 1","p_lose = 1 - p_win - p_void"],"math_spec_id":"MATH-06","vector_id":"VECTOR::MATH-06::GOLDEN"},{"case_type":"BOUNDARY","expected":{"expected_net_cash":"-0.02","expected_net_cash_if_filled":"1.56",'
    '"expected_terminal_cashflow":"6.47","p_lose":"0.3"},"expected_exception":null,"input_keys":["p_win","p_void","fill_probability","entry_trade_cashflow_total","win_terminal_cashflow_total","lose_terminal_cashflow_total","void_terminal_cashflow_total","no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total","cashflow_basis"],"inputs":{"builder_fee_total":"0","capital_time_cost_reserve_total":"0.01","cashflow_basis":"SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE","entry_trade_cashflow_total":"-4.7","exit_slippage_reserve_total":"0.05","expected_rebate_total":"0","fill_probability":"0","latency_adverse_selection_reserve_total":"0.03","lose_terminal_cashflow_total":"0","market_impact_reserve_total":"0.02","no_fill_cashflow_total":"-0.02","other_fee_total":"0","p_void":"0.1","p_win":"0.6","pl'
    'atform_fee_total":"0.1","void_terminal_cashflow_total":"4.7","win_terminal_cashflow_total":"10"},"math_spec_id":"MATH-06","vector_id":"VECTOR::MATH-06::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"p_win + p_void must not exceed one","input_keys":["p_win","p_void","fill_probability","entry_trade_cashflow_total","win_terminal_cashflow_total","lose_terminal_cashflow_total","void_terminal_cashflow_total","no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total","cashflow_basis"],"inputs":{"builder_fee_total":"0","capital_time_cost_reserve_total":"0.01","cashflow_basis":"SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE","entry_trade_cashflow_total":"-4.7","exit_slippage_reserve_total":"0.05","expected_rebate_total":"0","fill_p'
    'robability":"0.8","latency_adverse_selection_reserve_total":"0.03","lose_terminal_cashflow_total":"0","market_impact_reserve_total":"0.02","no_fill_cashflow_total":"0","other_fee_total":"0","p_void":"0.2","p_win":"0.9","platform_fee_total":"0.1","void_terminal_cashflow_total":"4.7","win_terminal_cashflow_total":"10"},"math_spec_id":"MATH-06","vector_id":"VECTOR::MATH-06::NEGATIVE"},{"case_type":"GOLDEN","expected":{"expected_net_cash":"-0.999","expected_net_cash_if_filled":"-1.11","expected_terminal_cashflow":"2.1","normalization_applied":false,"normalized_probabilities":["0.2","0.3","0.5"],"original_probability_sum":"1","outcome_ids":["A","B","C"]},"expected_exception":null,"input_keys":["outcome_ids","outcome_probabilities","outcome_terminal_cashflow_totals","probability_simplex_tolerance","fill_probability","entry_trade_cashflow_total","no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total","market_imp'
    'act_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total","cashflow_basis"],"inputs":{"builder_fee_total":"0.02","capital_time_cost_reserve_total":"0.01","cashflow_basis":"SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE","entry_trade_cashflow_total":"-3","exit_slippage_reserve_total":"0.03","expected_rebate_total":"0.01","fill_probability":"0.9","latency_adverse_selection_reserve_total":"0.04","market_impact_reserve_total":"0.02","no_fill_cashflow_total":"0","other_fee_total":"0","outcome_ids":["A","B","C"],"outcome_probabilities":["0.2","0.3","0.5"],"outcome_terminal_cashflow_totals":["10","2","-1"],"platform_fee_total":"0.1","probability_simplex_tolerance":"0.000000000001"},"math_spec_id":"MATH-07","vector_id":"VECTOR::MATH-07::GOLDEN"},{"case_type":"BOUNDARY","expected":{"expected_net_cash":"-0.99899999999928","expected_net_cash_if_filled":"-1.1099999999992","expected_terminal_cashflow":"2.1000000000008","normalization_applied":fal'
    'se,"normalized_probabilities":["0.2000000000001","0.2999999999999","0.5"],"original_probability_sum":"1","outcome_ids":["A","B","C"]},"expected_exception":null,"input_keys":["outcome_ids","outcome_probabilities","outcome_terminal_cashflow_totals","probability_simplex_tolerance","fill_probability","entry_trade_cashflow_total","no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total","cashflow_basis"],"inputs":{"builder_fee_total":"0.02","capital_time_cost_reserve_total":"0.01","cashflow_basis":"SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE","entry_trade_cashflow_total":"-3","exit_slippage_reserve_total":"0.03","expected_rebate_total":"0.01","fill_probability":"0.9","latency_adverse_selection_reserve_total":"0.04","market_impact_reserve_total":"0.02","no_fill_cashflow_total":"0","other_fe'
    'e_total":"0","outcome_ids":["A","B","C"],"outcome_probabilities":["0.2000000000001","0.2999999999999","0.5"],"outcome_terminal_cashflow_totals":["10","2","-1"],"platform_fee_total":"0.1","probability_simplex_tolerance":"0.000000000001"},"math_spec_id":"MATH-07","vector_id":"VECTOR::MATH-07::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"outcome vectors must be aligned","input_keys":["outcome_ids","outcome_probabilities","outcome_terminal_cashflow_totals","probability_simplex_tolerance","fill_probability","entry_trade_cashflow_total","no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total","cashflow_basis"],"inputs":{"builder_fee_total":"0.02","capital_time_cost_reserve_total":"0.01","cashflow_basis":"SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_E'
    'VENT_INCLUDED_EXACTLY_ONCE","entry_trade_cashflow_total":"-3","exit_slippage_reserve_total":"0.03","expected_rebate_total":"0.01","fill_probability":"0.9","latency_adverse_selection_reserve_total":"0.04","market_impact_reserve_total":"0.02","no_fill_cashflow_total":"0","other_fee_total":"0","outcome_ids":["A","B","C"],"outcome_probabilities":["0.2","0.3","0.5"],"outcome_terminal_cashflow_totals":["1","2"],"platform_fee_total":"0.1","probability_simplex_tolerance":"0.000000000001"},"math_spec_id":"MATH-07","vector_id":"VECTOR::MATH-07::NEGATIVE"},{"case_type":"GOLDEN","expected":{"mean_brier_score":0.13,"per_observation":[0.18,0.08]},"expected_exception":null,"input_keys":["probability_rows","outcome_indices"],"inputs":{"outcome_indices":[0,1],"probability_rows":[[0.7,0.3],[0.2,0.8]]},"math_spec_id":"MATH-08","vector_id":"VECTOR::MATH-08::GOLDEN"},{"case_type":"BOUNDARY","expected":{"mean_brier_score":0.0,"per_observation":[0.0,0.0]},"expected_exception":null,"input_keys":["probability_'
    'rows","outcome_indices"],"inputs":{"outcome_indices":[0,1],"probability_rows":[[1.0,0.0],[0.0,1.0]]},"math_spec_id":"MATH-08","vector_id":"VECTOR::MATH-08::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"probability row must sum to one","input_keys":["probability_rows","outcome_indices"],"inputs":{"outcome_indices":[0],"probability_rows":[[0.8,0.3]]},"math_spec_id":"MATH-08","vector_id":"VECTOR::MATH-08::NEGATIVE"},{"case_type":"GOLDEN","expected":{"mean_log_loss":0.289909247626471,"per_observation":[0.356674943938732,0.22314355131421]},"expected_exception":null,"input_keys":["probability_rows","outcome_indices","clip_epsilon"],"inputs":{"clip_epsilon":1e-06,"outcome_indices":[0,1],"probability_rows":[[0.7,0.3],[0.2,0.8]]},"math_spec_id":"MATH-09","vector_id":"VECTOR::MATH-09::GOLDEN"},{"case_type":"BOUNDARY","expected":{"mean_log_loss":1.00000050002909e-06,"per_observation":[1.00000050002909e-06,1.00000050002909e-06]},"'
    'expected_exception":null,"input_keys":["probability_rows","outcome_indices","clip_epsilon"],"inputs":{"clip_epsilon":1e-06,"outcome_indices":[0,1],"probability_rows":[[1.0,0.0],[0.0,1.0]]},"math_spec_id":"MATH-09","vector_id":"VECTOR::MATH-09::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"clip_epsilon must be in (0,0.5)","input_keys":["probability_rows","outcome_indices","clip_epsilon"],"inputs":{"clip_epsilon":0,"outcome_indices":[0,1],"probability_rows":[[0.7,0.3],[0.2,0.8]]},"math_spec_id":"MATH-09","vector_id":"VECTOR::MATH-09::NEGATIVE"},{"case_type":"GOLDEN","expected":{"bin_policy":"EQUAL_WIDTH","bins":[{"absolute_gap":0.05,"bin_index":0,"count":2,"empirical_frequency":0.0,"left":0.0,"mean_confidence":0.05,"right":0.2,"right_inclusive":false},{"absolute_gap":0.8,"bin_index":1,"count":1,"empirical_frequency":1.0,"left":0.2,"mean_confidence":0.2,"right":0.4,"right_inclusive":false},{"absolute_gap":0.4,"bin_index":'
    '2,"count":1,"empirical_frequency":0.0,"left":0.4,"mean_confidence":0.4,"right":0.6,"right_inclusive":false},{"absolute_gap":0.4,"bin_index":3,"count":1,"empirical_frequency":1.0,"left":0.6,"mean_confidence":0.6,"right":0.8,"right_inclusive":false},{"absolute_gap":0.05,"bin_index":4,"count":2,"empirical_frequency":1.0,"left":0.8,"mean_confidence":0.95,"right":1.0,"right_inclusive":true}],"effective_edges":[0.0,0.2,0.4,0.6,0.8,1.0],"expected_calibration_error":0.257142857142857,"requested_bin_count":5},"expected_exception":null,"input_keys":["probabilities","outcomes","bin_policy","bin_count"],"inputs":{"bin_count":5,"bin_policy":"EQUAL_WIDTH","outcomes":[0,0,1,0,1,1,1],"probabilities":[0,0.1,0.2,0.4,0.6,0.9,1.0]},"math_spec_id":"MATH-10","vector_id":"VECTOR::MATH-10::GOLDEN"},{"case_type":"BOUNDARY","expected":{"bin_policy":"EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES","bins":[{"absolute_gap":0.5,"bin_index":0,"count":2,"empirical_frequency":0.5,"left":0.0,"mean_confidence":0.0,"right":0.'
    '333333333333333,"right_inclusive":false},{"absolute_gap":0.0,"bin_index":1,"count":2,"empirical_frequency":0.5,"left":0.333333333333333,"mean_confidence":0.5,"right":0.666666666666667,"right_inclusive":false},{"absolute_gap":0.0,"bin_index":2,"count":2,"empirical_frequency":1.0,"left":0.666666666666667,"mean_confidence":1.0,"right":1.0,"right_inclusive":true}],"effective_edges":[0.0,0.333333333333333,0.666666666666667,1.0],"expected_calibration_error":0.166666666666667,"requested_bin_count":3},"expected_exception":null,"input_keys":["probabilities","outcomes","bin_policy","bin_count"],"inputs":{"bin_count":3,"bin_policy":"EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES","outcomes":[0,1,0,1,1,1],"probabilities":[0,0,0.5,0.5,1,1]},"math_spec_id":"MATH-10","vector_id":"VECTOR::MATH-10::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"probabilities and outcomes must be aligned nonempty lists","input_keys":["probabilities","outcomes'
    '","bin_policy","bin_count"],"inputs":{"bin_count":2,"bin_policy":"EQUAL_WIDTH","outcomes":[1],"probabilities":[0.1,0.2]},"math_spec_id":"MATH-10","vector_id":"VECTOR::MATH-10::NEGATIVE"},{"case_type":"GOLDEN","expected":{"lower":0.396778147461145,"upper":0.892208732593699},"expected_exception":null,"input_keys":["successes","trials","confidence"],"inputs":{"confidence":0.95,"successes":7,"trials":10},"math_spec_id":"MATH-11","vector_id":"VECTOR::MATH-11::GOLDEN"},{"case_type":"BOUNDARY","expected":{"lower":2.77555756156289e-17,"upper":0.277532799862889},"expected_exception":null,"input_keys":["successes","trials","confidence"],"inputs":{"confidence":0.95,"successes":0,"trials":10},"math_spec_id":"MATH-11","vector_id":"VECTOR::MATH-11::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"require integer trials>0 and 0<=successes<=trials","input_keys":["successes","trials","confidence"],"inputs":{"confidence":0.95,"successes":0'
    ',"trials":0},"math_spec_id":"MATH-11","vector_id":"VECTOR::MATH-11::NEGATIVE"},{"case_type":"GOLDEN","expected":{"adjusted_p_values":[0.004,0.04,0.04,0.2],"correction":1.0,"largest_rank":3,"rejected_original_indices":[0,1,2]},"expected_exception":null,"input_keys":["p_values","q"],"inputs":{"p_values":[0.001,0.02,0.03,0.2],"q":0.05},"math_spec_id":"MATH-12","vector_id":"VECTOR::MATH-12::GOLDEN"},{"case_type":"BOUNDARY","expected":{"adjusted_p_values":[0.02,0.02,0.0533333333333333,0.2],"correction":1.0,"largest_rank":2,"rejected_original_indices":[0,1]},"expected_exception":null,"input_keys":["p_values","q"],"inputs":{"p_values":[0.01,0.01,0.04,0.2],"q":0.05},"math_spec_id":"MATH-12","vector_id":"VECTOR::MATH-12::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"q must be in (0,1)","input_keys":["p_values","q"],"inputs":{"p_values":[0.01],"q":1.0},"math_spec_id":"MATH-12","vector_id":"VECTOR::MATH-12::NEGATIVE"},{"case_type'
    '":"GOLDEN","expected":{"adjusted_p_values":[0.00833333333333333,0.0833333333333333,0.0833333333333333,0.416666666666667],"correction":2.08333333333333,"largest_rank":1,"rejected_original_indices":[0]},"expected_exception":null,"input_keys":["p_values","q"],"inputs":{"p_values":[0.001,0.02,0.03,0.2],"q":0.05},"math_spec_id":"MATH-13","vector_id":"VECTOR::MATH-13::GOLDEN"},{"case_type":"BOUNDARY","expected":{"adjusted_p_values":[0.0416666666666667,0.0416666666666667,0.111111111111111,0.416666666666667],"correction":2.08333333333333,"largest_rank":2,"rejected_original_indices":[0,1]},"expected_exception":null,"input_keys":["p_values","q"],"inputs":{"p_values":[0.01,0.01,0.04,0.2],"q":0.05},"math_spec_id":"MATH-13","vector_id":"VECTOR::MATH-13::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"q must be in (0,1)","input_keys":["p_values","q"],"inputs":{"p_values":[0.01],"q":0.0},"math_spec_id":"MATH-13","vector_id":"VECTOR::MA'
    'TH-13::NEGATIVE"},{"case_type":"GOLDEN","expected":{"bootstrap_distribution":[2.33333333333333,2.41666666666667,2.41666666666667,2.41666666666667,2.83333333333333,2.25,1.91666666666667,2.41666666666667,2.0,1.41666666666667,2.83333333333333,2.91666666666667,2.33333333333333,2.0,2.41666666666667,2.33333333333333,2.58333333333333,2.33333333333333,2.08333333333333,2.83333333333333,2.58333333333333,1.91666666666667,2.16666666666667,3.16666666666667,2.66666666666667,2.0,1.75,2.25,2.33333333333333,2.33333333333333,2.58333333333333,2.5,1.75,2.25,2.25,2.08333333333333,2.75,2.25,2.66666666666667,2.91666666666667,2.5,2.91666666666667,2.08333333333333,1.83333333333333,3.08333333333333,2.75,2.16666666666667,1.75,2.91666666666667,1.66666666666667,2.33333333333333,2.16666666666667,2.08333333333333,2.33333333333333,2.33333333333333,2.41666666666667,2.58333333333333,2.41666666666667,2.08333333333333,2.5,2.33333333333333,2.33333333333333,2.08333333333333,2.83333333333333],"expected_block_length":2.0,"in'
    'terval_method":"PERCENTILE_TYPE7","lower":1.75,"replicates":64,"sample_mean":2.33333333333333,"seed":17,"upper":2.91666666666667},"expected_exception":null,"input_keys":["series","expected_block_length","seed","replicates","confidence","interval_method"],"inputs":{"confidence":0.9,"expected_block_length":2,"interval_method":"PERCENTILE_TYPE7","replicates":64,"seed":17,"series":[1,2,1.5,3,2.5,4]},"math_spec_id":"MATH-14","vector_id":"VECTOR::MATH-14::GOLDEN"},{"case_type":"BOUNDARY","expected":{"bootstrap_distribution":[2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0,2.0],"expected_block_length":1.0,"interval_method":"PERCENTILE_TYPE7","lower":2.0,"replicates":16,"sample_mean":2.0,"seed":1,"upper":2.0},"expected_exception":null,"input_keys":["series","expected_block_length","seed","replicates","confidence","interval_method"],"inputs":{"confidence":0.8,"expected_block_length":1,"interval_method":"PERCENTILE_TYPE7","replicates":16,"seed":1,"series":[2,2,2,2]},"math_spec_id":"M'
    'ATH-14","vector_id":"VECTOR::MATH-14::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"replicates must be an integer >= 1","input_keys":["series","expected_block_length","seed","replicates","confidence","interval_method"],"inputs":{"confidence":0.9,"expected_block_length":2,"interval_method":"PERCENTILE_TYPE7","replicates":0,"seed":17,"series":[1,2,1.5,3,2.5,4]},"math_spec_id":"MATH-14","vector_id":"VECTOR::MATH-14::NEGATIVE"},{"case_type":"GOLDEN","expected":{"candidate_means":[0.141666666666667,0.0625,-0.120833333333333],"p_value":0.0153846153846154,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":true,"simulated_statistics":[0.0,0.0,0.0,0.0144337567297407,0.043301270189222,0.0288675134594813,0.0721687836487032,0.0577350269189626,0.0144337567297406,0.0433012701892219,0.0721687836487032,0.0,0.0144337567297406,0.0721687836487032,0.158771324027147,0.0288675134594813,0.0,0.057735026918'
    '9626,0.0577350269189626,0.043301270189222,0.0577350269189626,0.0,0.043301270189222,0.101036297108185,0.0288675134594813,0.0288675134594813,0.0577350269189626,0.0288675134594813,0.0,0.0288675134594813,0.0,0.0,0.043301270189222,0.0144337567297406,0.0721687836487032,0.0,0.101036297108185,0.0144337567297407,0.0288675134594813,0.0,0.0144337567297406,0.043301270189222,0.0866025403784439,0.0288675134594813,0.0577350269189626,0.0288675134594813,0.0288675134594813,0.0288675134594813,0.129903810567666,0.0,0.0,0.0144337567297406,0.0577350269189627,0.0,0.0433012701892219,0.101036297108184,0.0577350269189626,0.0288675134594813,0.0,0.0866025403784438,0.0,0.0,0.0577350269189627,0.101036297108185],"statistic":0.490747728811182},"expected_exception":null,"input_keys":["loss_differentials","sign_convention","seed","replicates","expected_block_length","alpha"],"inputs":{"alpha":0.05,"expected_block_length":2,"loss_differentials":[[0.2,0.1,-0.1],[0.1,0.0,-0.2],[0.3,0.2,-0.1],[0.0,0.1,-0.1],[0.2,-0.1,-0.2]'
    ',[0.1,0.0,-0.1],[0.25,0.15,-0.05],[0.05,0.1,-0.15],[0.2,0.05,-0.1],[0.1,0.1,-0.2],[0.15,0.0,-0.05],[0.05,0.05,-0.1]],"replicates":64,"seed":11,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"math_spec_id":"MATH-15","vector_id":"VECTOR::MATH-15::GOLDEN"},{"case_type":"BOUNDARY","expected":{"candidate_means":[0.0,0.0],"p_value":1.0,"recenter_policy":"CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN","reject":false,"simulated_statistics":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"statistic":0.0},"expected_exception":null,"input_keys":["loss_differentials","sign_convention","seed","replicates","expected_block_length","alpha"],"inputs":{"alpha":0.05,"expected_block_length":1,"loss_differentials":[[0,0],[0,0],[0,0]],"replicates":16,"seed":1,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"math_spec_id":"MATH-15","vector_id":"VECTOR::MATH-15::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_'
    'exception":"ValueError","expected_message_contains":"explicit benchmark sign convention is required","input_keys":["loss_differentials","sign_convention","seed","replicates","expected_block_length","alpha"],"inputs":{"alpha":0.05,"expected_block_length":2,"loss_differentials":[[0.2,0.1,-0.1],[0.1,0.0,-0.2],[0.3,0.2,-0.1],[0.0,0.1,-0.1],[0.2,-0.1,-0.2],[0.1,0.0,-0.1],[0.25,0.15,-0.05],[0.05,0.1,-0.15],[0.2,0.05,-0.1],[0.1,0.1,-0.2],[0.15,0.0,-0.05],[0.05,0.05,-0.1]],"replicates":64,"seed":11,"sign_convention":"AMBIGUOUS"},"math_spec_id":"MATH-15","vector_id":"VECTOR::MATH-15::NEGATIVE"},{"case_type":"GOLDEN","expected":{"candidate_means":[0.141666666666667,0.0625,-0.120833333333333],"consistent_valid_columns":[true,true,false],"long_run_variances":[0.00334752400716146,0.0040634028116862,0.00154127756754557],"p_value":0.0153846153846154,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":true,"simulated_statistics":[0.0,0.0,0.0,0.249469542829409,0.748408628488224,0.49893908'
    '5658816,1.13215124182565,0.905720993460521,0.22643024836513,0.67929074509539,1.24734771414704,0.0,0.22643024836513,1.13215124182565,2.49073273201643,0.498939085658816,0.0,0.905720993460521,0.452860496730261,0.0,0.748408628488224,0.0,0.748408628488224,1.58501173855591,0.498939085658816,0.0,0.905720993460521,0.452860496730261,0.0,0.452860496730261,0.0,0.0,0.748408628488224,0.22643024836513,1.13215124182565,0.0,1.58501173855591,0.249469542829409,0.498939085658816,0.0,0.22643024836513,0.0,0.249469542829409,0.0,0.905720993460521,0.498939085658816,0.452860496730261,0.452860496730261,2.24522588546467,0.0,0.0,0.0,0.997878171317633,0.0,0.67929074509539,1.74628679980585,0.90572099346052,0.452860496730261,0.0,1.49681725697645,0.0,0.0,0.997878171317633,0.0],"statistic":8.48196445619987},"expected_exception":null,"input_keys":["loss_differentials","sign_convention","seed","replicates","expected_block_length","alpha","recenter_variant"],"inputs":{"alpha":0.05,"expected_block_length":2,"loss_differen'
    'tials":[[0.2,0.1,-0.1],[0.1,0.0,-0.2],[0.3,0.2,-0.1],[0.0,0.1,-0.1],[0.2,-0.1,-0.2],[0.1,0.0,-0.1],[0.25,0.15,-0.05],[0.05,0.1,-0.15],[0.2,0.05,-0.1],[0.1,0.1,-0.2],[0.15,0.0,-0.05],[0.05,0.05,-0.1]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":64,"seed":11,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"math_spec_id":"MATH-16","vector_id":"VECTOR::MATH-16::GOLDEN"},{"case_type":"BOUNDARY","expected":{"candidate_means":[0.125,-0.15],"consistent_valid_columns":[true,false],"long_run_variances":[0.003125,0.0025],"p_value":0.0588235294117647,"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","reject":true,"simulated_statistics":[0.0,0.0,0.0,2.23606797749979,0.0,0.0,1.78885438199983,0.0,1.78885438199983,0.447213595499958,0.0,0.0,0.894427190999917,0.0,0.894427190999917,0.894427190999917],"statistic":4.47213595499958},"expected_exception":null,"input_keys":["loss_differentials","sign_convention","seed","replicates","expected_block_l'
    'ength","alpha","recenter_variant"],"inputs":{"alpha":0.1,"expected_block_length":1,"loss_differentials":[[0.1,-0.1],[0.2,-0.2],[0.05,-0.1],[0.15,-0.2]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":16,"seed":2,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"math_spec_id":"MATH-16","vector_id":"VECTOR::MATH-16::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"candidate 0 has positive mean and zero long-run variance","input_keys":["loss_differentials","sign_convention","seed","replicates","expected_block_length","alpha","recenter_variant"],"inputs":{"alpha":0.05,"expected_block_length":2,"loss_differentials":[[1,0],[1,0],[1,0],[1,0]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":64,"seed":11,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"math_spec_id":"MATH-16","vector_id":"VECTOR::MATH-16::NEGATIVE"},{"case_type":"GOL'
    'DEN","expected":{"probabilistic_sharpe_ratio":0.999996045369034,"z_score":4.46762547885953},"expected_exception":null,"input_keys":["estimated_sharpe","reference_sharpe","independent_equivalent_observations","sample_skewness","sample_non_excess_kurtosis"],"inputs":{"estimated_sharpe":0.8,"independent_equivalent_observations":100,"reference_sharpe":0.3,"sample_non_excess_kurtosis":3.0,"sample_skewness":0.1},"math_spec_id":"MATH-17","vector_id":"VECTOR::MATH-17::GOLDEN"},{"case_type":"BOUNDARY","expected":{"probabilistic_sharpe_ratio":0.5,"z_score":0.0},"expected_exception":null,"input_keys":["estimated_sharpe","reference_sharpe","independent_equivalent_observations","sample_skewness","sample_non_excess_kurtosis"],"inputs":{"estimated_sharpe":0.3,"independent_equivalent_observations":50,"reference_sharpe":0.3,"sample_non_excess_kurtosis":3,"sample_skewness":0},"math_spec_id":"MATH-17","vector_id":"VECTOR::MATH-17::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"V'
    'alueError","expected_message_contains":"independent_equivalent_observations must be an integer >= 2","input_keys":["estimated_sharpe","reference_sharpe","independent_equivalent_observations","sample_skewness","sample_non_excess_kurtosis"],"inputs":{"estimated_sharpe":0.8,"independent_equivalent_observations":1,"reference_sharpe":0.3,"sample_non_excess_kurtosis":3.0,"sample_skewness":0.1},"math_spec_id":"MATH-17","vector_id":"VECTOR::MATH-17::NEGATIVE"},{"case_type":"GOLDEN","expected":{"deflated_sharpe_ratio":0.92585163242918,"expected_maximum_sharpe_threshold":0.345901298241941,"trial_mean_sharpe":0.23,"trial_sharpe_variance":0.0145},"expected_exception":null,"input_keys":["complete_material_trial_sharpes","effective_independent_trial_count","candidate_estimated_sharpe","candidate_independent_equivalent_observations","candidate_sample_skewness","candidate_sample_non_excess_kurtosis"],"inputs":{"candidate_estimated_sharpe":0.5,"candidate_independent_equivalent_observations":100,"candid'
    'ate_sample_non_excess_kurtosis":3.0,"candidate_sample_skewness":0.0,"complete_material_trial_sharpes":[0.1,0.2,0.3,0.4,0.15],"effective_independent_trial_count":3.5},"math_spec_id":"MATH-18","vector_id":"VECTOR::MATH-18::GOLDEN"},{"case_type":"BOUNDARY","expected":{"deflated_sharpe_ratio":0.62886677916101,"expected_maximum_sharpe_threshold":0.251975534428059,"trial_mean_sharpe":0.2,"trial_sharpe_variance":0.01},"expected_exception":null,"input_keys":["complete_material_trial_sharpes","effective_independent_trial_count","candidate_estimated_sharpe","candidate_independent_equivalent_observations","candidate_sample_skewness","candidate_sample_non_excess_kurtosis"],"inputs":{"candidate_estimated_sharpe":0.3,"candidate_independent_equivalent_observations":50,"candidate_sample_non_excess_kurtosis":3,"candidate_sample_skewness":0,"complete_material_trial_sharpes":[0.1,0.2,0.3],"effective_independent_trial_count":2.0},"math_spec_id":"MATH-18","vector_id":"VECTOR::MATH-18::BOUNDARY"},{"case_typ'
    'e":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"effective independent trial count must be in (1, material trial count]","input_keys":["complete_material_trial_sharpes","effective_independent_trial_count","candidate_estimated_sharpe","candidate_independent_equivalent_observations","candidate_sample_skewness","candidate_sample_non_excess_kurtosis"],"inputs":{"candidate_estimated_sharpe":0.5,"candidate_independent_equivalent_observations":100,"candidate_sample_non_excess_kurtosis":3.0,"candidate_sample_skewness":0.0,"complete_material_trial_sharpes":[0.1,0.2,0.3,0.4,0.15],"effective_independent_trial_count":1.0},"math_spec_id":"MATH-18","vector_id":"VECTOR::MATH-18::NEGATIVE"},{"case_type":"GOLDEN","expected":{"S":4,"logits":[0.0,1.09861228866811,1.09861228866811,1.09861228866811,1.09861228866811,0.0],"probability_of_backtest_overfitting":0.333333333333333,"split_count":6,"splits":[{"is_winner_strategy_id":"S-A","logit":0.0,"oos_midrank_worst_1'
    '_best_n":2.0,"relative_rank":0.5,"train_groups":[0,1]},{"is_winner_strategy_id":"S-B","logit":1.09861228866811,"oos_midrank_worst_1_best_n":3.0,"relative_rank":0.75,"train_groups":[0,2]},{"is_winner_strategy_id":"S-B","logit":1.09861228866811,"oos_midrank_worst_1_best_n":3.0,"relative_rank":0.75,"train_groups":[0,3]},{"is_winner_strategy_id":"S-B","logit":1.09861228866811,"oos_midrank_worst_1_best_n":3.0,"relative_rank":0.75,"train_groups":[1,2]},{"is_winner_strategy_id":"S-B","logit":1.09861228866811,"oos_midrank_worst_1_best_n":3.0,"relative_rank":0.75,"train_groups":[1,3]},{"is_winner_strategy_id":"S-B","logit":0.0,"oos_midrank_worst_1_best_n":2.0,"relative_rank":0.5,"train_groups":[2,3]}]},"expected_exception":null,"input_keys":["performance_matrix","strategy_ids","S"],"inputs":{"S":4,"performance_matrix":[[1.0,0.5,0.2],[1.1,0.4,0.3],[0.9,0.6,0.1],[1.2,0.3,0.4],[0.4,1.0,0.2],[0.3,1.1,0.1],[0.5,0.9,0.3],[0.2,1.2,0.4]],"strategy_ids":["S-A","S-B","S-C"]},"math_spec_id":"MATH-19","vec'
    'tor_id":"VECTOR::MATH-19::GOLDEN"},{"case_type":"BOUNDARY","expected":{"S":4,"logits":[0.0,1.09861228866811,1.09861228866811,1.09861228866811,1.09861228866811,0.0],"probability_of_backtest_overfitting":0.333333333333333,"split_count":6,"splits":[{"is_winner_strategy_id":"S-A","logit":0.0,"oos_midrank_worst_1_best_n":2.0,"relative_rank":0.5,"train_groups":[0,1]},{"is_winner_strategy_id":"S-B","logit":1.09861228866811,"oos_midrank_worst_1_best_n":3.0,"relative_rank":0.75,"train_groups":[0,2]},{"is_winner_strategy_id":"S-B","logit":1.09861228866811,"oos_midrank_worst_1_best_n":3.0,"relative_rank":0.75,"train_groups":[0,3]},{"is_winner_strategy_id":"S-B","logit":1.09861228866811,"oos_midrank_worst_1_best_n":3.0,"relative_rank":0.75,"train_groups":[1,2]},{"is_winner_strategy_id":"S-B","logit":1.09861228866811,"oos_midrank_worst_1_best_n":3.0,"relative_rank":0.75,"train_groups":[1,3]},{"is_winner_strategy_id":"S-B","logit":0.0,"oos_midrank_worst_1_best_n":2.0,"relative_rank":0.5,"train_group'
    's":[2,3]}]},"expected_exception":null,"input_keys":["performance_matrix","strategy_ids","S"],"inputs":{"S":4,"performance_matrix":[[1.0,0.5,0.2],[1.1,0.4,0.3],[0.9,0.6,0.1],[1.2,0.3,0.4],[0.4,1.0,0.2],[0.3,1.1,0.1],[0.5,0.9,0.3],[0.2,1.2,0.4]],"strategy_ids":["S-A","S-B","S-C"]},"math_spec_id":"MATH-19","vector_id":"VECTOR::MATH-19::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"S must be even","input_keys":["performance_matrix","strategy_ids","S"],"inputs":{"S":3,"performance_matrix":[[1.0,0.5,0.2],[1.1,0.4,0.3],[0.9,0.6,0.1],[1.2,0.3,0.4],[0.4,1.0,0.2],[0.3,1.1,0.1],[0.5,0.9,0.3],[0.2,1.2,0.4]],"strategy_ids":["S-A","S-B","S-C"]},"math_spec_id":"MATH-19","vector_id":"VECTOR::MATH-19::NEGATIVE"},{"case_type":"GOLDEN","expected":{"embargo_basis":"TIME_DURATION_AFTER_MERGED_TEST_INTERVAL","folds":[{"embargoed_sample_ids":["s3"],"fold_id":0,"merged_test_intervals":[[0.0,4.0]],"purged_sample_ids":[],"test_sample_ids":["s0"'
    ',"s1","s2"],"train_sample_ids":["s4","s5","s6","s7"]},{"embargoed_sample_ids":["s6"],"fold_id":1,"merged_test_intervals":[[4.0,9.0]],"purged_sample_ids":[],"test_sample_ids":["s3","s4","s5"],"train_sample_ids":["s0","s1","s2","s7"]},{"embargoed_sample_ids":[],"fold_id":2,"merged_test_intervals":[[9.0,12.0]],"purged_sample_ids":[],"test_sample_ids":["s6","s7"],"train_sample_ids":["s0","s1","s2","s3","s4","s5"]}],"interval_semantics":"HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE","ordered_sample_ids":["s0","s1","s2","s3","s4","s5","s6","s7"]},"expected_exception":null,"input_keys":["sample_intervals","folds","embargo_duration"],"inputs":{"embargo_duration":1.0,"folds":3,"sample_intervals":[{"end":2,"sample_id":"s0","start":0},{"end":3,"sample_id":"s1","start":1},{"end":4,"sample_id":"s2","start":3},{"end":6,"sample_id":"s3","start":4},{"end":7,"sample_id":"s4","start":6},{"end":9,"sample_id":"s5","start":7},{"end":10,"sample_id":"s6","start":9},{"end":12,"sample_id":"s7","start":10}]},"math_s'
    'pec_id":"MATH-20","vector_id":"VECTOR::MATH-20::GOLDEN"},{"case_type":"BOUNDARY","expected":{"embargo_basis":"TIME_DURATION_AFTER_MERGED_TEST_INTERVAL","folds":[{"embargoed_sample_ids":[],"fold_id":0,"merged_test_intervals":[[0.0,2.0]],"purged_sample_ids":[],"test_sample_ids":["a","b"],"train_sample_ids":["c","d"]},{"embargoed_sample_ids":[],"fold_id":1,"merged_test_intervals":[[2.0,4.0]],"purged_sample_ids":[],"test_sample_ids":["c","d"],"train_sample_ids":["a","b"]}],"interval_semantics":"HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE","ordered_sample_ids":["a","b","c","d"]},"expected_exception":null,"input_keys":["sample_intervals","folds","embargo_duration"],"inputs":{"embargo_duration":0,"folds":2,"sample_intervals":[{"end":1,"sample_id":"a","start":0},{"end":2,"sample_id":"b","start":1},{"end":3,"sample_id":"c","start":2},{"end":4,"sample_id":"d","start":3}]},"math_spec_id":"MATH-20","vector_id":"VECTOR::MATH-20::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"V'
    'alueError","expected_message_contains":"intervals use half-open [start,end) semantics and require start<end","input_keys":["sample_intervals","folds","embargo_duration"],"inputs":{"embargo_duration":0,"folds":2,"sample_intervals":[{"end":1,"sample_id":"x","start":1}]},"math_spec_id":"MATH-20","vector_id":"VECTOR::MATH-20::NEGATIVE"},{"case_type":"GOLDEN","expected":{"N_groups":4,"aggregation_rule":"ALL_PATHS_NO_CHERRY_PICKING","expected_path_count":3,"k_test_groups":2,"path_count":3,"paths":[{"path_id":0,"split_ids":[0,5],"test_group_partition":[[0,1],[2,3]]},{"path_id":1,"split_ids":[1,4],"test_group_partition":[[0,2],[1,3]]},{"path_id":2,"split_ids":[2,3],"test_group_partition":[[0,3],[1,2]]}],"split_count":6,"splits":[{"embargoed_sample_ids":["s4"],"merged_test_intervals":[[0.0,6.0]],"purged_sample_ids":[],"split_id":0,"test_groups":[0,1],"test_sample_ids":["s0","s1","s2","s3"],"train_sample_ids":["s5","s6","s7"]},{"embargoed_sample_ids":["s2","s6"],"merged_test_intervals":[[0.0,3.0'
    '],[6.0,9.0]],"purged_sample_ids":[],"split_id":1,"test_groups":[0,2],"test_sample_ids":["s0","s1","s4","s5"],"train_sample_ids":["s3","s7"]},{"embargoed_sample_ids":["s2"],"merged_test_intervals":[[0.0,3.0],[9.0,12.0]],"purged_sample_ids":[],"split_id":2,"test_groups":[0,3],"test_sample_ids":["s0","s1","s6","s7"],"train_sample_ids":["s3","s4","s5"]},{"embargoed_sample_ids":["s6"],"merged_test_intervals":[[3.0,9.0]],"purged_sample_ids":[],"split_id":3,"test_groups":[1,2],"test_sample_ids":["s2","s3","s4","s5"],"train_sample_ids":["s0","s1","s7"]},{"embargoed_sample_ids":["s4"],"merged_test_intervals":[[3.0,6.0],[9.0,12.0]],"purged_sample_ids":[],"split_id":4,"test_groups":[1,3],"test_sample_ids":["s2","s3","s6","s7"],"train_sample_ids":["s0","s1","s5"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[6.0,12.0]],"purged_sample_ids":[],"split_id":5,"test_groups":[2,3],"test_sample_ids":["s4","s5","s6","s7"],"train_sample_ids":["s0","s1","s2","s3"]}]},"expected_exception":null,"input_'
    'keys":["sample_intervals","N_groups","k_test_groups","embargo_duration","aggregation_rule"],"inputs":{"N_groups":4,"aggregation_rule":"ALL_PATHS_NO_CHERRY_PICKING","embargo_duration":0.5,"k_test_groups":2,"sample_intervals":[{"end":2,"sample_id":"s0","start":0},{"end":3,"sample_id":"s1","start":1},{"end":4,"sample_id":"s2","start":3},{"end":6,"sample_id":"s3","start":4},{"end":7,"sample_id":"s4","start":6},{"end":9,"sample_id":"s5","start":7},{"end":10,"sample_id":"s6","start":9},{"end":12,"sample_id":"s7","start":10}]},"math_spec_id":"MATH-21","vector_id":"VECTOR::MATH-21::GOLDEN"},{"case_type":"BOUNDARY","expected":{"N_groups":4,"aggregation_rule":"ALL_PATHS_NO_CHERRY_PICKING","expected_path_count":3,"k_test_groups":2,"path_count":3,"paths":[{"path_id":0,"split_ids":[0,5],"test_group_partition":[[0,1],[2,3]]},{"path_id":1,"split_ids":[1,4],"test_group_partition":[[0,2],[1,3]]},{"path_id":2,"split_ids":[2,3],"test_group_partition":[[0,3],[1,2]]}],"split_count":6,"splits":[{"embargoed_'
    'sample_ids":[],"merged_test_intervals":[[0.0,0.5],[1.0,1.5]],"purged_sample_ids":[],"split_id":0,"test_groups":[0,1],"test_sample_ids":["s0","s1"],"train_sample_ids":["s2","s3"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[0.0,0.5],[2.0,2.5]],"purged_sample_ids":[],"split_id":1,"test_groups":[0,2],"test_sample_ids":["s0","s2"],"train_sample_ids":["s1","s3"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[0.0,0.5],[3.0,3.5]],"purged_sample_ids":[],"split_id":2,"test_groups":[0,3],"test_sample_ids":["s0","s3"],"train_sample_ids":["s1","s2"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[1.0,1.5],[2.0,2.5]],"purged_sample_ids":[],"split_id":3,"test_groups":[1,2],"test_sample_ids":["s1","s2"],"train_sample_ids":["s0","s3"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[1.0,1.5],[3.0,3.5]],"purged_sample_ids":[],"split_id":4,"test_groups":[1,3],"test_sample_ids":["s1","s3"],"train_sample_ids":["s0","s2"]},{"embargoed_sample_ids":[],"merged_test_intervals":[[2.0,'
    '2.5],[3.0,3.5]],"purged_sample_ids":[],"split_id":5,"test_groups":[2,3],"test_sample_ids":["s2","s3"],"train_sample_ids":["s0","s1"]}]},"expected_exception":null,"input_keys":["sample_intervals","N_groups","k_test_groups","embargo_duration","aggregation_rule"],"inputs":{"N_groups":4,"aggregation_rule":"ALL_PATHS_NO_CHERRY_PICKING","embargo_duration":0,"k_test_groups":2,"sample_intervals":[{"end":0.5,"sample_id":"s0","start":0},{"end":1.5,"sample_id":"s1","start":1},{"end":2.5,"sample_id":"s2","start":2},{"end":3.5,"sample_id":"s3","start":3}]},"math_spec_id":"MATH-21","vector_id":"VECTOR::MATH-21::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"frozen CPCV path assembly requires k_test_groups to divide N_groups","input_keys":["sample_intervals","N_groups","k_test_groups","embargo_duration","aggregation_rule"],"inputs":{"N_groups":3,"aggregation_rule":"ALL_PATHS_NO_CHERRY_PICKING","embargo_duration":0.5,"k_test_groups":2,'
    '"sample_intervals":[{"end":2,"sample_id":"s0","start":0},{"end":3,"sample_id":"s1","start":1},{"end":4,"sample_id":"s2","start":3},{"end":6,"sample_id":"s3","start":4},{"end":7,"sample_id":"s4","start":6},{"end":9,"sample_id":"s5","start":7},{"end":10,"sample_id":"s6","start":9},{"end":12,"sample_id":"s7","start":10}]},"math_spec_id":"MATH-21","vector_id":"VECTOR::MATH-21::NEGATIVE"},{"case_type":"GOLDEN","expected":{"clipping_applied":false,"doubly_robust_estimate":0.491904761904762,"effective_sample_size":3.96575132090709,"importance_weights":[0.833333333333333,0.6,3.0,1.5,0.714285714285714,0.571428571428572],"row_values":[1.05,0.36,1.2,-0.29,0.614285714285714,0.0171428571428571]},"expected_exception":null,"input_keys":["logged_rows"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},'
    '{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id":"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_'
    'reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}]},"math_spec_id":"MATH-22","vector_id":"VECTOR::MATH-22::GOLDEN"},{"case_type":"BOUNDARY","expected":{"clipping_applied":false,"doubly_robust_estimate":0.491904761904762,"effective_sample_size":3.96575132090709,"importance_weights":[0.833333333333333,0.6,3.0,1.5,0.714285714285714,0.571428571428572],"row_values":[1.05,0.36,1.2,-0.29,0.614285714285714,0.0171428571428571]},"expected_exception":null,"input_keys":["logged_rows"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_i'
    'd":"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}]},"math_spec_id":"MATH-22","vector_id":'
    '"VECTOR::MATH-22::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"target support must be contained in behavior support","input_keys":["logged_rows"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[1,0],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0,1]}]},"math_spec_id":"MATH-22","vector_id":"VECTOR::MATH-22::NEGATIVE"},{"case_type":"GOLDEN","expected":{"clipping_applied":false,"effective_sample_size":3.96575132090709,"importance_weights":[0.833333333333333,0.6,3.0,1.5,0.714285714285714,0.571428571428572],"inverse_propensity_score_estimate":0.757936507936508,"row_values":[0.833333333333333,0.0,3.0,0.0,0.714285714285714,0.0]},"expected_exception":null,"input_keys":["logged_rows"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_'
    'fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id":"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":'
    '1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}]},"math_spec_id":"MATH-23","vector_id":"VECTOR::MATH-23::GOLDEN"},{"case_type":"BOUNDARY","expected":{"clipping_applied":false,"effective_sample_size":3.96575132090709,"importance_weights":[0.833333333333333,0.6,3.0,1.5,0.714285714285714,0.571428571428572],"inverse_propensity_score_estimate":0.757936507936508,"row_values":[0.833333333333333,0.0,3.0,0.0,0.714285714285714,0.0]},"expected_exception":null,"input_keys":["logged_rows"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabil'
    'ities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id":"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":'
    '[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}]},"math_spec_id":"MATH-23","vector_id":"VECTOR::MATH-23::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"reward-model prediction must be cross-fitted","input_keys":["logged_rows"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":false,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]}]},"math_spec_id":"MATH-23","vector_id":"VECTOR::MATH-23::NEGATIVE"},{"case_type":"GOLDEN","expected":{"effective_sample_size":2.33333333333333,"self_normalized_ips_estimate":0.357142857142857,"weight_sum":3.5},"expected_exception":null,"input_keys":["weights","rewards"],"inputs":{"rewards":[1.0,0.0,0.5],"weights":[1.0,2.0,0.5]},"math_spec_id":"MATH-24","vector_id":"VECTOR::MATH-24::G'
    'OLDEN"},{"case_type":"BOUNDARY","expected":{"effective_sample_size":2.0,"self_normalized_ips_estimate":0.5,"weight_sum":2.0},"expected_exception":null,"input_keys":["weights","rewards"],"inputs":{"rewards":[0,1],"weights":[1,1]},"math_spec_id":"MATH-24","vector_id":"VECTOR::MATH-24::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"weights must be nonnegative with positive total","input_keys":["weights","rewards"],"inputs":{"rewards":[1,0],"weights":[0,0]},"math_spec_id":"MATH-24","vector_id":"VECTOR::MATH-24::NEGATIVE"},{"case_type":"GOLDEN","expected":{"clipping_applied":false,"held_out_row_values":[1.05,-0.29,0.36,0.614285714285714,0.6,0.0171428571428571],"outer_fold_results":[{"criteria":[{"bias_upper_bound":1.0,"estimated_mse_upper_bound":1.0028,"tau":0.0,"variance_of_mean":0.0028},{"bias_upper_bound":0.6,"estimated_mse_upper_bound":0.379506632653061,"tau":1.0,"variance_of_mean":0.0195066326530612},{"bias_upper_bound"'
    ':0.15,"estimated_mse_upper_bound":0.0420066326530612,"tau":2.0,"variance_of_mean":0.0195066326530612},{"bias_upper_bound":0.0,"estimated_mse_upper_bound":0.0622209183673469,"tau":"INF","variance_of_mean":0.0622209183673469}],"held_out_row_values":[1.05,-0.29],"outer_fold":0,"selected_tau":2.0},{"criteria":[{"bias_upper_bound":1.0,"estimated_mse_upper_bound":1.00278958333333,"tau":0.0,"variance_of_mean":0.00278958333333333},{"bias_upper_bound":0.575,"estimated_mse_upper_bound":0.375892474489796,"tau":1.0,"variance_of_mean":0.0452674744897959},{"bias_upper_bound":0.15,"estimated_mse_upper_bound":0.11189693877551,"tau":2.0,"variance_of_mean":0.0893969387755102},{"bias_upper_bound":0.0,"estimated_mse_upper_bound":0.137468367346939,"tau":"INF","variance_of_mean":0.137468367346939}],"held_out_row_values":[0.36,0.614285714285714],"outer_fold":1,"selected_tau":2.0},{"criteria":[{"bias_upper_bound":1.0,"estimated_mse_upper_bound":1.00095625,"tau":0.0,"variance_of_mean":0.000956250000000001},{"b'
    'ias_upper_bound":0.575,"estimated_mse_upper_bound":0.353802338435374,"tau":1.0,"variance_of_mean":0.0231773384353742},{"bias_upper_bound":0.0,"estimated_mse_upper_bound":0.0784675170068027,"tau":2.0,"variance_of_mean":0.0784675170068027},{"bias_upper_bound":0.0,"estimated_mse_upper_bound":0.0784675170068027,"tau":"INF","variance_of_mean":0.0784675170068027}],"held_out_row_values":[0.6,0.0171428571428571],"outer_fold":2,"selected_tau":2.0}],"selection_rule":"MIN_ESTIMATED_MSE_UPPER_BOUND_THEN_SMALLEST_TAU","switch_ope_estimate":0.391904761904762},"expected_exception":null,"input_keys":["logged_rows","tau_grid","outer_fold_count","reward_lower_bound","reward_upper_bound"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction"'
    ':true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id":"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index'
    '":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}],"outer_fold_count":3,"reward_lower_bound":0.0,"reward_upper_bound":1.0,"tau_grid":[0.0,1.0,2.0,"INF"]},"math_spec_id":"MATH-25","vector_id":"VECTOR::MATH-25::GOLDEN"},{"case_type":"BOUNDARY","expected":{"clipping_applied":false,"held_out_row_values":[1.05,-0.29,0.36,0.614285714285714,0.6,0.0171428571428571],"outer_fold_results":[{"criteria":[{"bias_upper_bound":1.0,"estimated_mse_upper_bound":1.0028,"tau":0.0,"variance_of_mean":0.0028},{"bias_upper_bound":0.6,"estimated_mse_upper_bound":0.379506632653061,"tau":1.0,"variance_of_mean":0.0195066326530612},{"bias_upper_bound":0.15,"estimated_mse_upper_bound":0.0420066326530612,"tau":2.0,"variance_of_mean":0.0195066326530612},{"bias_upper_bound":0.0,"estimated_mse_upper_bound":0.0622209183673469,"tau":"INF","variance_of_mean":0.0622209183673469}],"held_out_row_values":[1.05,-0.29],"outer_fold":0,"selected_tau":2.0},{"criteria":[{"bias_upper_bound":1.0,"estimated_mse_up'
    'per_bound":1.00278958333333,"tau":0.0,"variance_of_mean":0.00278958333333333},{"bias_upper_bound":0.575,"estimated_mse_upper_bound":0.375892474489796,"tau":1.0,"variance_of_mean":0.0452674744897959},{"bias_upper_bound":0.15,"estimated_mse_upper_bound":0.11189693877551,"tau":2.0,"variance_of_mean":0.0893969387755102},{"bias_upper_bound":0.0,"estimated_mse_upper_bound":0.137468367346939,"tau":"INF","variance_of_mean":0.137468367346939}],"held_out_row_values":[0.36,0.614285714285714],"outer_fold":1,"selected_tau":2.0},{"criteria":[{"bias_upper_bound":1.0,"estimated_mse_upper_bound":1.00095625,"tau":0.0,"variance_of_mean":0.000956250000000001},{"bias_upper_bound":0.575,"estimated_mse_upper_bound":0.353802338435374,"tau":1.0,"variance_of_mean":0.0231773384353742},{"bias_upper_bound":0.0,"estimated_mse_upper_bound":0.0784675170068027,"tau":2.0,"variance_of_mean":0.0784675170068027},{"bias_upper_bound":0.0,"estimated_mse_upper_bound":0.0784675170068027,"tau":"INF","variance_of_mean":0.0784675'
    '170068027}],"held_out_row_values":[0.6,0.0171428571428571],"outer_fold":2,"selected_tau":2.0}],"selection_rule":"MIN_ESTIMATED_MSE_UPPER_BOUND_THEN_SMALLEST_TAU","switch_ope_estimate":0.391904761904762},"expected_exception":null,"input_keys":["logged_rows","tau_grid","outer_fold_count","reward_lower_bound","reward_upper_bound"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id":"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","t'
    'arget_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}],"outer_fold_count":3,"reward_lower_bound":0.0,"reward_upper_bound":1.0,"tau_grid":[0.0,1.0,2.0,"INF"]},"math_spec_id":"MATH-25","vector_id":"VECTOR::MATH-25::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"tau_'
    'grid must be unique and ascending","input_keys":["logged_rows","tau_grid","outer_fold_count","reward_lower_bound","reward_upper_bound"],"inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id":"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_inde'
    'x":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}],"outer_fold_count":3,"reward_lower_bound":0.0,"reward_upper_bound":1.0,"tau_grid":[2,1]},"math_spec_id":"MATH-25","vector_id":"VECTOR::MATH-25::NEGATIVE"},{"case_type":"GOLDEN","expected":{"best_no_bid":"0.52","best_yes_bid":"0.45","book_sequence":5,"derived_no_ask":"0.55","derived_yes_ask":"0.48"},"expected_exception":null,"input_keys":["yes_bids","no_bids","payout","book_sequence","expected_sequence","book_state","price_ranges"],"inputs":{"book_sequence":5,"book_s'
    'tate":"CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS","expected_sequence":5,"no_bids":["0.50","0.52"],"payout":"1","price_ranges":[{"maximum":"0.99","minimum":"0.01","step":"0.01"}],"yes_bids":["0.40","0.45"]},"math_spec_id":"MATH-36","vector_id":"VECTOR::MATH-36::GOLDEN"},{"case_type":"BOUNDARY","expected":{"best_no_bid":"0.52","best_yes_bid":"0.45","book_sequence":5,"derived_no_ask":"0.55","derived_yes_ask":"0.48"},"expected_exception":null,"input_keys":["yes_bids","no_bids","payout","book_sequence","expected_sequence","book_state","price_ranges"],"inputs":{"book_sequence":5,"book_state":"CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS","expected_sequence":5,"no_bids":["0.50","0.52"],"payout":"1","price_ranges":[{"maximum":"0.99","minimum":"0.01","step":"0.01"}],"yes_bids":["0.40","0.45"]},"math_spec_id":"MATH-36","vector_id":"VECTOR::MATH-36::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"sequence mismatch requires snapshot resync'
    'hronization","input_keys":["yes_bids","no_bids","payout","book_sequence","expected_sequence","book_state","price_ranges"],"inputs":{"book_sequence":5,"book_state":"CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS","expected_sequence":4,"no_bids":["0.50","0.52"],"payout":"1","price_ranges":[{"maximum":"0.99","minimum":"0.01","step":"0.01"}],"yes_bids":["0.40","0.45"]},"math_spec_id":"MATH-36","vector_id":"VECTOR::MATH-36::NEGATIVE"},{"case_type":"GOLDEN","expected":{"binary_assignment":[1,0],"canonical_qubo":{"constant":0.5,"diagonal":[1.0,-2.0],"representation":"CANONICAL_UPPER_TRIANGULAR","schema_version":"CANONICAL_QUBO_MODEL_V1","upper_terms":[{"i":0,"j":1,"value":3.0}],"variable_count":2},"energy":1.5,"exhaustive_assignments":[{"binary_assignment":[0,0],"energy":0.5},{"binary_assignment":[0,1],"energy":-1.5},{"binary_assignment":[1,0],"energy":1.5},{"binary_assignment":[1,1],"energy":2.5}]},"expected_exception":null,"input_keys":["representation","diagonal","upper_terms","full_symmetric_mat'
    'rix","constant","binary_assignment"],"inputs":{"binary_assignment":[1,0],"constant":0.5,"diagonal":[1.0,-2.0],"full_symmetric_matrix":[],"representation":"CANONICAL_UPPER_TRIANGULAR","upper_terms":[{"i":0,"j":1,"value":3.0}]},"math_spec_id":"MATH-46","vector_id":"VECTOR::MATH-46::GOLDEN"},{"case_type":"BOUNDARY","expected":{"binary_assignment":[1],"canonical_qubo":{"constant":-1.0,"diagonal":[2.0],"representation":"CANONICAL_UPPER_TRIANGULAR","schema_version":"CANONICAL_QUBO_MODEL_V1","upper_terms":[],"variable_count":1},"energy":1.0,"exhaustive_assignments":[{"binary_assignment":[0],"energy":-1.0},{"binary_assignment":[1],"energy":1.0}]},"expected_exception":null,"input_keys":["representation","diagonal","upper_terms","full_symmetric_matrix","constant","binary_assignment"],"inputs":{"binary_assignment":[1],"constant":-1.0,"diagonal":[2.0],"full_symmetric_matrix":[],"representation":"CANONICAL_UPPER_TRIANGULAR","upper_terms":[]},"math_spec_id":"MATH-46","vector_id":"VECTOR::MATH-46::BO'
    'UNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"duplicate upper-triangular interaction","input_keys":["representation","diagonal","upper_terms","full_symmetric_matrix","constant","binary_assignment"],"inputs":{"binary_assignment":[0,1],"constant":0,"diagonal":[1,2],"full_symmetric_matrix":[],"representation":"CANONICAL_UPPER_TRIANGULAR","upper_terms":[{"i":0,"j":1,"value":1},{"i":0,"j":1,"value":2}]},"math_spec_id":"MATH-46","vector_id":"VECTOR::MATH-46::NEGATIVE"},{"case_type":"GOLDEN","expected":{"binary_assignment":[1,0],"binary_to_spin_convention":"x_i=(1-s_i)/2; s=+1 maps to x=0 and s=-1 maps to x=1","couplers_J":[{"i":0,"j":1,"value":0.75}],"exhaustive_parity_rows":[{"binary_assignment":[0,0],"ising_energy":0.5,"qubo_energy":0.5,"spin_assignment":[1,1]},{"binary_assignment":[0,1],"ising_energy":-1.5,"qubo_energy":-1.5,"spin_assignment":[1,-1]},{"binary_assignment":[1,0],"ising_energy":1.5,"qubo_energy":1.5,"spin_assi'
    'gnment":[-1,1]},{"binary_assignment":[1,1],"ising_energy":2.5,"qubo_energy":2.5,"spin_assignment":[-1,-1]}],"ising_energy":1.5,"linear_fields_h":[-1.25,0.25],"offset":0.75,"qubo_energy":1.5,"spin_assignment":[-1,1]},"expected_exception":null,"input_keys":["representation","diagonal","upper_terms","full_symmetric_matrix","constant","binary_assignment"],"inputs":{"binary_assignment":[1,0],"constant":0.5,"diagonal":[1.0,-2.0],"full_symmetric_matrix":[],"representation":"CANONICAL_UPPER_TRIANGULAR","upper_terms":[{"i":0,"j":1,"value":3.0}]},"math_spec_id":"MATH-47","vector_id":"VECTOR::MATH-47::GOLDEN"},{"case_type":"BOUNDARY","expected":{"binary_assignment":[1],"binary_to_spin_convention":"x_i=(1-s_i)/2; s=+1 maps to x=0 and s=-1 maps to x=1","couplers_J":[],"exhaustive_parity_rows":[{"binary_assignment":[0],"ising_energy":-1.0,"qubo_energy":-1.0,"spin_assignment":[1]},{"binary_assignment":[1],"ising_energy":1.0,"qubo_energy":1.0,"spin_assignment":[-1]}],"ising_energy":1.0,"linear_fields_'
    'h":[-1.0],"offset":0.0,"qubo_energy":1.0,"spin_assignment":[-1]},"expected_exception":null,"input_keys":["representation","diagonal","upper_terms","full_symmetric_matrix","constant","binary_assignment"],"inputs":{"binary_assignment":[1],"constant":-1.0,"diagonal":[2.0],"full_symmetric_matrix":[],"representation":"CANONICAL_UPPER_TRIANGULAR","upper_terms":[]},"math_spec_id":"MATH-47","vector_id":"VECTOR::MATH-47::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"binary_assignment must contain one binary integer per variable","input_keys":["representation","diagonal","upper_terms","full_symmetric_matrix","constant","binary_assignment"],"inputs":{"binary_assignment":[2],"constant":0,"diagonal":[1],"full_symmetric_matrix":[],"representation":"CANONICAL_UPPER_TRIANGULAR","upper_terms":[]},"math_spec_id":"MATH-47","vector_id":"VECTOR::MATH-47::NEGATIVE"},{"case_type":"GOLDEN","expected":{"assignment":{"x":1.0,"y":2.0},"constrain'
    't_evaluations":[{"hard":true,"id":"demand","lhs":3.0,"rhs":1.0,"sense":"GE","soft_penalty_weight":0.0,"violation":0.0},{"hard":false,"id":"soft_inventory","lhs":2.0,"rhs":1.0,"sense":"LE","soft_penalty_weight":2.0,"violation":1.0}],"conversion_penalty_adequacy":{"converted_best_assignment":{"x":1.0,"y":0.0},"matches_native_feasible_optimum":true,"penalty":100.0,"state":"ADEQUATE_FOR_EXACT_ENUMERATED_FIXTURE"},"interpret_back_state":"EXACT_ORIGINAL_VARIABLE_LABELS_AND_UNITS_PRESERVED","objective_sense":"MINIMIZE","original_model_feasible":true,"penalized_objective":13.0,"raw_objective":11.0,"schema_version":"QTT_CQM_GRAMMAR_V1","small_exact_solution":{"assignment":{"x":1.0,"y":0.0},"enumerated_assignment_count":6,"feasible_assignment_count":5,"penalized_objective":1.0,"raw_objective":1.0,"state":"EXACT_FEASIBLE_OPTIMUM"},"soft_penalty":2.0},"expected_exception":null,"input_keys":["model","assignment"],"inputs":{"assignment":{"x":1,"y":2},"model":{"constraints":[{"constant":0,"hard":true'
    ',"id":"demand","linear":{"x":1,"y":1},"quadratic":[],"rhs":1,"sense":"GE","soft_penalty_weight":0},{"constant":0,"hard":false,"id":"soft_inventory","linear":{"y":1},"quadratic":[],"rhs":1,"sense":"LE","soft_penalty_weight":2}],"conversion_penalty_candidate":100.0,"feasibility_tolerance":1e-12,"objective_constant":0,"objective_linear":{"x":1,"y":2},"objective_quadratic":[{"coefficient":3,"u":"x","v":"y"}],"objective_sense":"MINIMIZE","schema_version":"QTT_CQM_GRAMMAR_V1","variables":[{"enumeration_values":[0,1],"id":"x","lower":0,"type":"BINARY","unit":"binary","upper":1},{"enumeration_values":[0,1,2],"id":"y","lower":0,"type":"INTEGER","unit":"units","upper":2}]}},"math_spec_id":"MATH-48","vector_id":"VECTOR::MATH-48::GOLDEN"},{"case_type":"BOUNDARY","expected":{"assignment":{"x":0.0,"y":0.0},"constraint_evaluations":[{"hard":true,"id":"demand","lhs":0.0,"rhs":1.0,"sense":"GE","soft_penalty_weight":0.0,"violation":1.0},{"hard":false,"id":"soft_inventory","lhs":0.0,"rhs":1.0,"sense":"LE'
    '","soft_penalty_weight":2.0,"violation":0.0}],"conversion_penalty_adequacy":{"converted_best_assignment":{"x":1.0,"y":0.0},"matches_native_feasible_optimum":true,"penalty":100.0,"state":"ADEQUATE_FOR_EXACT_ENUMERATED_FIXTURE"},"interpret_back_state":"EXACT_ORIGINAL_VARIABLE_LABELS_AND_UNITS_PRESERVED","objective_sense":"MINIMIZE","original_model_feasible":false,"penalized_objective":0.0,"raw_objective":0.0,"schema_version":"QTT_CQM_GRAMMAR_V1","small_exact_solution":{"assignment":{"x":1.0,"y":0.0},"enumerated_assignment_count":6,"feasible_assignment_count":5,"penalized_objective":1.0,"raw_objective":1.0,"state":"EXACT_FEASIBLE_OPTIMUM"},"soft_penalty":0.0},"expected_exception":null,"input_keys":["model","assignment"],"inputs":{"assignment":{"x":0,"y":0},"model":{"constraints":[{"constant":0,"hard":true,"id":"demand","linear":{"x":1,"y":1},"quadratic":[],"rhs":1,"sense":"GE","soft_penalty_weight":0},{"constant":0,"hard":false,"id":"soft_inventory","linear":{"y":1},"quadratic":[],"rhs":1'
    ',"sense":"LE","soft_penalty_weight":2}],"conversion_penalty_candidate":100.0,"feasibility_tolerance":1e-12,"objective_constant":0,"objective_linear":{"x":1,"y":2},"objective_quadratic":[{"coefficient":3,"u":"x","v":"y"}],"objective_sense":"MINIMIZE","schema_version":"QTT_CQM_GRAMMAR_V1","variables":[{"enumeration_values":[0,1],"id":"x","lower":0,"type":"BINARY","unit":"binary","upper":1},{"enumeration_values":[0,1,2],"id":"y","lower":0,"type":"INTEGER","unit":"units","upper":2}]}},"math_spec_id":"MATH-48","vector_id":"VECTOR::MATH-48::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"assignment must provide every variable exactly once","input_keys":["model","assignment"],"inputs":{"assignment":{"x":1},"model":{"constraints":[{"constant":0,"hard":true,"id":"demand","linear":{"x":1,"y":1},"quadratic":[],"rhs":1,"sense":"GE","soft_penalty_weight":0},{"constant":0,"hard":false,"id":"soft_inventory","linear":{"y":1},"quadratic"'
    ':[],"rhs":1,"sense":"LE","soft_penalty_weight":2}],"conversion_penalty_candidate":100.0,"feasibility_tolerance":1e-12,"objective_constant":0,"objective_linear":{"x":1,"y":2},"objective_quadratic":[{"coefficient":3,"u":"x","v":"y"}],"objective_sense":"MINIMIZE","schema_version":"QTT_CQM_GRAMMAR_V1","variables":[{"enumeration_values":[0,1],"id":"x","lower":0,"type":"BINARY","unit":"binary","upper":1},{"enumeration_values":[0,1,2],"id":"y","lower":0,"type":"INTEGER","unit":"units","upper":2}]}},"math_spec_id":"MATH-48","vector_id":"VECTOR::MATH-48::NEGATIVE"},{"case_type":"GOLDEN","expected":{"assignment":{"A":"a1","B":"b1"},"energy":-1.5,"exhaustive_assignments":[{"assignment":{"A":"a0","B":"b0"},"energy":0.5},{"assignment":{"A":"a0","B":"b1"},"energy":-0.5},{"assignment":{"A":"a0","B":"b2"},"energy":2.5},{"assignment":{"A":"a1","B":"b0"},"energy":1.5},{"assignment":{"A":"a1","B":"b1"},"energy":-1.5},{"assignment":{"A":"a1","B":"b2"},"energy":3.5}],"interpret_back_state":"EXACT_ORDERED_V'
    'ARIABLE_AND_CASE_LABELS_PRESERVED","one_hot_expansion_applied":false,"schema_version":"QTT_DQM_GRAMMAR_V1"},"expected_exception":null,"input_keys":["model","assignment"],"inputs":{"assignment":{"A":"a1","B":"b1"},"model":{"constant":0.5,"linear_biases":[{"bias":0,"case":"a0","variable":"A"},{"bias":1,"case":"a1","variable":"A"},{"bias":0,"case":"b0","variable":"B"},{"bias":-1,"case":"b1","variable":"B"},{"bias":2,"case":"b2","variable":"B"}],"pairwise_biases":[{"bias":-2,"case_u":"a1","case_v":"b1","u":"A","v":"B"}],"schema_version":"QTT_DQM_GRAMMAR_V1","variables":[{"cases":["a0","a1"],"id":"A"},{"cases":["b0","b1","b2"],"id":"B"}]}},"math_spec_id":"MATH-49","vector_id":"VECTOR::MATH-49::GOLDEN"},{"case_type":"BOUNDARY","expected":{"assignment":{"A":"a0","B":"b2"},"energy":2.5,"exhaustive_assignments":[{"assignment":{"A":"a0","B":"b0"},"energy":0.5},{"assignment":{"A":"a0","B":"b1"},"energy":-0.5},{"assignment":{"A":"a0","B":"b2"},"energy":2.5},{"assignment":{"A":"a1","B":"b0"},"energ'
    'y":1.5},{"assignment":{"A":"a1","B":"b1"},"energy":-1.5},{"assignment":{"A":"a1","B":"b2"},"energy":3.5}],"interpret_back_state":"EXACT_ORDERED_VARIABLE_AND_CASE_LABELS_PRESERVED","one_hot_expansion_applied":false,"schema_version":"QTT_DQM_GRAMMAR_V1"},"expected_exception":null,"input_keys":["model","assignment"],"inputs":{"assignment":{"A":"a0","B":"b2"},"model":{"constant":0.5,"linear_biases":[{"bias":0,"case":"a0","variable":"A"},{"bias":1,"case":"a1","variable":"A"},{"bias":0,"case":"b0","variable":"B"},{"bias":-1,"case":"b1","variable":"B"},{"bias":2,"case":"b2","variable":"B"}],"pairwise_biases":[{"bias":-2,"case_u":"a1","case_v":"b1","u":"A","v":"B"}],"schema_version":"QTT_DQM_GRAMMAR_V1","variables":[{"cases":["a0","a1"],"id":"A"},{"cases":["b0","b1","b2"],"id":"B"}]}},"math_spec_id":"MATH-49","vector_id":"VECTOR::MATH-49::BOUNDARY"},{"case_type":"NEGATIVE","expected":null,"expected_exception":"ValueError","expected_message_contains":"assignment must select one known case per v'
    'ariable","input_keys":["model","assignment"],"inputs":{"assignment":{"A":"unknown","B":"b1"},"model":{"constant":0.5,"linear_biases":[{"bias":0,"case":"a0","variable":"A"},{"bias":1,"case":"a1","variable":"A"},{"bias":0,"case":"b0","variable":"B"},{"bias":-1,"case":"b1","variable":"B"},{"bias":2,"case":"b2","variable":"B"}],"pairwise_biases":[{"bias":-2,"case_u":"a1","case_v":"b1","u":"A","v":"B"}],"schema_version":"QTT_DQM_GRAMMAR_V1","variables":[{"cases":["a0","a1"],"id":"A"},{"cases":["b0","b1","b2"],"id":"B"}]}},"math_spec_id":"MATH-49","vector_id":"VECTOR::MATH-49::NEGATIVE"}]'
)

_ST12B_PROPERTY_PACK_JSON = (
    '[{"base_inputs":{"contract_price":"0.47","payout_per_winning_contract":"1"},"math_spec_id":"MATH-01","mutation":{"path":["contract_price"],"replacement":"0.52"},"property_id":"POSITIVE_COMMON_SCALE_INVARIANCE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-01"},{"base_inputs":{"calibrated_model_probability":0.61,"calibration_state":"CALIBRATED_FOR_DECLARED_CONTEXT","market_implied_probability":0.48},"math_spec_id":"MATH-02","mutation":{"path":["calibrated_model_probability"],"replacement":0.66},"property_id":"AFFINE_EDGE_SENSITIVITY","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-02"},{"base_inputs":{"best_ask":"0.50","best_bid":"0.46","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-03","mutation":{"path":["best_ask"],"replacement":"0.54"},"prope'
    'rty_id":"MIDPOINT_BOUNDS_AND_SYMMETRY","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-03"},{"base_inputs":{"best_ask":"0.50","best_bid":"0.46","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-04","mutation":{"path":["best_ask"],"replacement":"0.54"},"property_id":"NONNEGATIVE_AND_TRANSLATION_INVARIANCE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-04"},{"base_inputs":{"best_ask":"0.50","best_bid":"0.46","payout":"1","same_instrument_snapshot":true,"snapshot_state":"CURRENT_CONTIGUOUS_BOOK"},"math_spec_id":"MATH-05","mutation":{"path":["best_ask"],"replacement":"0.54"},"property_id":"POSITIVE_SCALE_INVARIANCE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-'
    '05"},{"base_inputs":{"builder_fee_total":"0","capital_time_cost_reserve_total":"0.01","cashflow_basis":"SIGNED_TOTAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE","entry_trade_cashflow_total":"-4.7","exit_slippage_reserve_total":"0.05","expected_rebate_total":"0","fill_probability":"0.8","latency_adverse_selection_reserve_total":"0.03","lose_terminal_cashflow_total":"0","market_impact_reserve_total":"0.02","no_fill_cashflow_total":"0","other_fee_total":"0","p_void":"0.1","p_win":"0.6","platform_fee_total":"0.1","void_terminal_cashflow_total":"4.7","win_terminal_cashflow_total":"10"},"math_spec_id":"MATH-06","mutation":{"path":["win_terminal_cashflow_total"],"replacement":"11"},"property_id":"CASHFLOW_CONSERVATION_AND_FILL_MIXTURE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-06"},{"base_inputs":{"builder_fee_total":"0.02","capital_time_cost_reserve_total":"0.01","cashflow_basis":"SIGNED_TO'
    'TAL_ACCOUNT_CASHFLOW_EACH_EVENT_INCLUDED_EXACTLY_ONCE","entry_trade_cashflow_total":"-3","exit_slippage_reserve_total":"0.03","expected_rebate_total":"0.01","fill_probability":"0.9","latency_adverse_selection_reserve_total":"0.04","market_impact_reserve_total":"0.02","no_fill_cashflow_total":"0","other_fee_total":"0","outcome_ids":["A","B","C"],"outcome_probabilities":["0.2","0.3","0.5"],"outcome_terminal_cashflow_totals":["10","2","-1"],"platform_fee_total":"0.1","probability_simplex_tolerance":"0.000000000001"},"math_spec_id":"MATH-07","mutation":{"path":["outcome_terminal_cashflow_totals",0],"replacement":"11"},"property_id":"ALIGNED_OUTCOME_PERMUTATION_INVARIANCE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-07"},{"base_inputs":{"outcome_indices":[0,1],"probability_rows":[[0.7,0.3],[0.2,0.8]]},"math_spec_id":"MATH-08","mutation":{"companion_mutations":[[["probability_rows",0,1],0.4]],"path"'
    ':["probability_rows",0,0],"replacement":0.6},"property_id":"PERFECT_FORECAST_ZERO","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-08"},{"base_inputs":{"clip_epsilon":1e-06,"outcome_indices":[0,1],"probability_rows":[[0.7,0.3],[0.2,0.8]]},"math_spec_id":"MATH-09","mutation":{"companion_mutations":[[["probability_rows",0,1],0.4]],"path":["probability_rows",0,0],"replacement":0.6},"property_id":"REALIZED_CLASS_PROBABILITY_MONOTONICITY","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-09"},{"base_inputs":{"bin_count":5,"bin_policy":"EQUAL_WIDTH","outcomes":[0,0,1,0,1,1,1],"probabilities":[0,0.1,0.2,0.4,0.6,0.9,1.0]},"math_spec_id":"MATH-10","mutation":{"path":["outcomes",2],"replacement":0},"property_id":"EXACT_BIN_COVERAGE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPE'
    'RTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-10"},{"base_inputs":{"confidence":0.95,"successes":7,"trials":10},"math_spec_id":"MATH-11","mutation":{"path":["successes"],"replacement":8},"property_id":"ORDERED_UNIT_INTERVAL_BOUNDS","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-11"},{"base_inputs":{"p_values":[0.001,0.02,0.03,0.2],"q":0.05},"math_spec_id":"MATH-12","mutation":{"path":["p_values",3],"replacement":0.04},"property_id":"SORTED_ADJUSTED_P_MONOTONICITY","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-12"},{"base_inputs":{"p_values":[0.001,0.02,0.03,0.2],"q":0.05},"math_spec_id":"MATH-13","mutation":{"path":["p_values",3],"replacement":0.04},"property_id":"BY_NOT_LESS_CONSERVATIVE_THAN_BH","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_T'
    'EST","test_id":"PROPERTY::MATH-13"},{"base_inputs":{"confidence":0.9,"expected_block_length":2,"interval_method":"PERCENTILE_TYPE7","replicates":64,"seed":17,"series":[1,2,1.5,3,2.5,4]},"math_spec_id":"MATH-14","mutation":{"path":["series",0],"replacement":1.125},"property_id":"STATIONARY_BOOTSTRAP_TRANSLATION_EQUIVARIANCE_WITH_FIXED_INDEX_STREAM","property_parameters":{"translation_constant":7.25},"required_outcome":"ADDING_CONSTANT_C_TO_EVERY_SERIES_VALUE_SHIFTS_SAMPLE_MEAN_LOWER_UPPER_AND_EVERY_BOOTSTRAP_REPLICATE_BY_EXACTLY_C_WITH_IDENTICAL_SEED_AND_INDICES","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-14"},{"base_inputs":{"alpha":0.05,"expected_block_length":2,"loss_differentials":[[0.2,0.1,-0.1],[0.1,0.0,-0.2],[0.3,0.2,-0.1],[0.0,0.1,-0.1],[0.2,-0.1,-0.2],[0.1,0.0,-0.1],[0.25,0.15,-0.05],[0.05,0.1,-0.15],[0.2,0.05,-0.1],[0.1,0.1,-0.2],[0.15,0.0,-0.05],[0.05,0.05,-0.1]],"replicates":64,"seed":11,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDAT'
    'E_LOSS_POSITIVE_IS_BETTER"},"math_spec_id":"MATH-15","mutation":{"path":["loss_differentials",0,0],"replacement":0.5},"property_id":"COMPLETE_MATRIX_COMMON_RESAMPLE_AND_ZERO_CASE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-15"},{"base_inputs":{"alpha":0.05,"expected_block_length":2,"loss_differentials":[[0.2,0.1,-0.1],[0.1,0.0,-0.2],[0.3,0.2,-0.1],[0.0,0.1,-0.1],[0.2,-0.1,-0.2],[0.1,0.0,-0.1],[0.25,0.15,-0.05],[0.05,0.1,-0.15],[0.2,0.05,-0.1],[0.1,0.1,-0.2],[0.15,0.0,-0.05],[0.05,0.05,-0.1]],"recenter_variant":"HANSEN_CONSISTENT_LOG_LOG_THRESHOLD","replicates":64,"seed":11,"sign_convention":"BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"},"math_spec_id":"MATH-16","mutation":{"path":["loss_differentials",0,0],"replacement":0.5},"property_id":"CONSISTENT_RECENTER_AND_FINITE_P_VALUE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATIO'
    'N_TEST","test_id":"PROPERTY::MATH-16"},{"base_inputs":{"estimated_sharpe":0.8,"independent_equivalent_observations":100,"reference_sharpe":0.3,"sample_non_excess_kurtosis":3.0,"sample_skewness":0.1},"math_spec_id":"MATH-17","mutation":{"path":["estimated_sharpe"],"replacement":0.9},"property_id":"EQUAL_REFERENCE_GIVES_HALF","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-17"},{"base_inputs":{"candidate_estimated_sharpe":0.5,"candidate_independent_equivalent_observations":100,"candidate_sample_non_excess_kurtosis":3.0,"candidate_sample_skewness":0.0,"complete_material_trial_sharpes":[0.1,0.2,0.3,0.4,0.15],"effective_independent_trial_count":3.5},"math_spec_id":"MATH-18","mutation":{"path":["candidate_estimated_sharpe"],"replacement":0.6},"property_id":"COMPLETE_TRIAL_THRESHOLD_SENSITIVITY","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST'
    '","test_id":"PROPERTY::MATH-18"},{"base_inputs":{"S":4,"performance_matrix":[[1.0,0.5,0.2],[1.1,0.4,0.3],[0.9,0.6,0.1],[1.2,0.3,0.4],[0.4,1.0,0.2],[0.3,1.1,0.1],[0.5,0.9,0.3],[0.2,1.2,0.4]],"strategy_ids":["S-A","S-B","S-C"]},"math_spec_id":"MATH-19","mutation":{"path":["performance_matrix",0,0],"replacement":2.0},"property_id":"COMPLETE_SPLIT_COUNT_AND_UNIT_PBO","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-19"},{"base_inputs":{"embargo_duration":1.0,"folds":3,"sample_intervals":[{"end":2,"sample_id":"s0","start":0},{"end":3,"sample_id":"s1","start":1},{"end":4,"sample_id":"s2","start":3},{"end":6,"sample_id":"s3","start":4},{"end":7,"sample_id":"s4","start":6},{"end":9,"sample_id":"s5","start":7},{"end":10,"sample_id":"s6","start":9},{"end":12,"sample_id":"s7","start":10}]},"math_spec_id":"MATH-20","mutation":{"path":["embargo_duration"],"replacement":2.0},"property_id":"NO_TRAIN_TEST_OVERLAP_'
    'AFTER_PURGE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-20"},{"base_inputs":{"N_groups":4,"aggregation_rule":"ALL_PATHS_NO_CHERRY_PICKING","embargo_duration":0.5,"k_test_groups":2,"sample_intervals":[{"end":2,"sample_id":"s0","start":0},{"end":3,"sample_id":"s1","start":1},{"end":4,"sample_id":"s2","start":3},{"end":6,"sample_id":"s3","start":4},{"end":7,"sample_id":"s4","start":6},{"end":9,"sample_id":"s5","start":7},{"end":10,"sample_id":"s6","start":9},{"end":12,"sample_id":"s7","start":10}]},"math_spec_id":"MATH-21","mutation":{"path":["embargo_duration"],"replacement":1.5},"property_id":"EXACT_SPLIT_AND_PATH_COVERAGE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-21"},{"base_inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model'
    '_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id":"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","'
    'target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}]},"math_spec_id":"MATH-22","mutation":{"path":["logged_rows",0,"reward"],"replacement":0.5},"property_id":"DR_RAW_ROW_SENSITIVITY_AND_SUPPORT","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-22"},{"base_inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id":"r1",'
    '"target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}]},"math_spec_id":"MATH-23","mutation":{"path":['
    '"logged_rows",0,"reward"],"replacement":0.5},"property_id":"IPS_ON_POLICY_REDUCTION","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-23"},{"base_inputs":{"rewards":[1.0,0.0,0.5],"weights":[1.0,2.0,0.5]},"math_spec_id":"MATH-24","mutation":{"path":["rewards",0],"replacement":0.5},"property_id":"COMMON_WEIGHT_SCALE_INVARIANCE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-24"},{"base_inputs":{"logged_rows":[{"behavior_action_probabilities":[0.6,0.4],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.4,0.7],"fold_id":0,"logged_action_index":0,"reward":1.0,"row_id":"r0","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.5,0.5],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.6,0.2],"fold_id":1,"logged_action_index":1,"reward":0.0,"row_id"'
    ':"r1","target_action_probabilities":[0.7,0.3]},{"behavior_action_probabilities":[0.8,0.2],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.3,0.8],"fold_id":2,"logged_action_index":1,"reward":1.0,"row_id":"r2","target_action_probabilities":[0.4,0.6]},{"behavior_action_probabilities":[0.4,0.6],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.5,0.4],"fold_id":0,"logged_action_index":0,"reward":0.0,"row_id":"r3","target_action_probabilities":[0.6,0.4]},{"behavior_action_probabilities":[0.7,0.3],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.7,0.1],"fold_id":1,"logged_action_index":0,"reward":1.0,"row_id":"r4","target_action_probabilities":[0.5,0.5]},{"behavior_action_probabilities":[0.3,0.7],"cross_fitted_prediction":true,"cross_fitted_reward_model_predictions":[0.2,0.6],"fold_id":2,"logged_action_index":1,"reward":0.0,"row_id":"r5","target_action_probabilities":[0.6,0.4]}],"outer_fold_count":3,"reward_lower_bound'
    '":0.0,"reward_upper_bound":1.0,"tau_grid":[0.0,1.0,2.0,"INF"]},"math_spec_id":"MATH-25","mutation":{"path":["logged_rows",0,"reward"],"replacement":0.5},"property_id":"TRAIN_ONLY_TAU_SELECTION_AND_HELD_OUT_COVERAGE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-25"},{"base_inputs":{"book_sequence":5,"book_state":"CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS","expected_sequence":5,"no_bids":["0.50","0.52"],"payout":"1","price_ranges":[{"maximum":"0.99","minimum":"0.01","step":"0.01"}],"yes_bids":["0.40","0.45"]},"math_spec_id":"MATH-36","mutation":{"path":["yes_bids",1],"replacement":"0.46"},"property_id":"COMPLEMENT_AND_DYNAMIC_GRID_SEQUENCE","required_outcome":"OUTPUT_CHANGES_OR_TYPED_REJECTION","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-36"},{"base_inputs":{"binary_assignment":[1,0],"constant":0.5,"diagonal":[1.0,-2.0],"full_symmetric_matrix":[],"representati'
    'on":"CANONICAL_UPPER_TRIANGULAR","upper_terms":[{"i":0,"j":1,"value":3.0}]},"math_spec_id":"MATH-46","mutation":{"path":["diagonal",0],"replacement":2.0},"property_id":"EXHAUSTIVE_BINARY_ENUMERATION_MATCHES_DIRECT_ENERGY","required_outcome":"ENUMERATION_COMPLETE_AND_MUTATED_COEFFICIENT_CHANGES_AT_LEAST_ONE_ENERGY","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-46"},{"base_inputs":{"binary_assignment":[1,0],"constant":0.5,"diagonal":[1.0,-2.0],"full_symmetric_matrix":[],"representation":"CANONICAL_UPPER_TRIANGULAR","upper_terms":[{"i":0,"j":1,"value":3.0}]},"math_spec_id":"MATH-47","mutation":{"path":["diagonal",0],"replacement":2.0},"property_id":"EXHAUSTIVE_QUBO_ISING_ENERGY_PARITY_VIA_IMMUTABLE_RAW_FIELD_ADAPTER","required_outcome":"RAW_FIELD_ADAPTER_CANONICALIZES_ONCE_AND_EVERY_ENUMERATED_QUBO_ENERGY_EQUALS_ISING_ENERGY; MATERIAL_COEFFICIENT_MUTATION_CHANGES_LEDGER","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH'
    '-47"},{"base_inputs":{"assignment":{"x":1,"y":2},"model":{"constraints":[{"constant":0,"hard":true,"id":"demand","linear":{"x":1,"y":1},"quadratic":[],"rhs":1,"sense":"GE","soft_penalty_weight":0},{"constant":0,"hard":false,"id":"soft_inventory","linear":{"y":1},"quadratic":[],"rhs":1,"sense":"LE","soft_penalty_weight":2}],"conversion_penalty_candidate":100.0,"feasibility_tolerance":1e-12,"objective_constant":0,"objective_linear":{"x":1,"y":2},"objective_quadratic":[{"coefficient":3,"u":"x","v":"y"}],"objective_sense":"MINIMIZE","schema_version":"QTT_CQM_GRAMMAR_V1","variables":[{"enumeration_values":[0,1],"id":"x","lower":0,"type":"BINARY","unit":"binary","upper":1},{"enumeration_values":[0,1,2],"id":"y","lower":0,"type":"INTEGER","unit":"units","upper":2}]}},"math_spec_id":"MATH-48","mutation":{"path":["assignment","y"],"replacement":1},"property_id":"FINITE_ENUMERATION_FEASIBILITY_INTERPRET_BACK_AND_PENALTY_ADEQUACY","required_outcome":"EXACT_FEASIBLE_OPTIMUM_AND_CONVERSION_PENALTY_'
    'MATCH_NATIVE_OPTIMUM","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-48"},{"base_inputs":{"assignment":{"A":"a1","B":"b1"},"model":{"constant":0.5,"linear_biases":[{"bias":0,"case":"a0","variable":"A"},{"bias":1,"case":"a1","variable":"A"},{"bias":0,"case":"b0","variable":"B"},{"bias":-1,"case":"b1","variable":"B"},{"bias":2,"case":"b2","variable":"B"}],"pairwise_biases":[{"bias":-2,"case_u":"a1","case_v":"b1","u":"A","v":"B"}],"schema_version":"QTT_DQM_GRAMMAR_V1","variables":[{"cases":["a0","a1"],"id":"A"},{"cases":["b0","b1","b2"],"id":"B"}]}},"math_spec_id":"MATH-49","mutation":{"path":["assignment","B"],"replacement":"b2"},"property_id":"CARTESIAN_EXACT_ENUMERATION_NATIVE_CASE_LABELS_NO_ONE_HOT","required_outcome":"ENUMERATION_CARDINALITY_EQUALS_CASE_PRODUCT_AND_MUTATION_CHANGES_ENERGY","terminal_state":"EXECUTABLE_PROPERTY_AND_MUTATION_TEST","test_id":"PROPERTY::MATH-49"}]'
)
# END GENERATED ST12B V3.4 OWNER-FROZEN DATA


@dataclass(frozen=True, slots=True)
class TrancheBVectorV1:
    vector_id: str
    math_spec_id: str
    case_type: str
    input_keys: tuple[str, ...]
    inputs: Mapping[str, object]
    expected: object
    expected_exception: str | None

    def __post_init__(self) -> None:
        if (
            not self.vector_id
            or not self.math_spec_id
            or self.case_type not in {"GOLDEN", "BOUNDARY", "NEGATIVE"}
            or not self.input_keys
            or set(self.inputs) != set(self.input_keys)
            or (
                self.case_type == "NEGATIVE"
                and self.expected_exception != "ValueError"
            )
            or (
                self.case_type != "NEGATIVE"
                and self.expected_exception is not None
            )
        ):
            raise ContractValidationError(
                ReasonCode.ORACLE_NOT_INDEPENDENT,
                "v3.4 vector identity, keys, or expected exception is invalid",
            )


@dataclass(frozen=True, slots=True)
class TrancheBPropertyTestV1:
    test_id: str
    math_spec_id: str
    property_id: str
    base_inputs: Mapping[str, object]
    mutation: Mapping[str, object]
    required_outcome: str
    terminal_state: str


def _freeze_oracle_value(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze_oracle_value(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_oracle_value(item) for item in value)
    return value


_TRANCHE_A_ORACLE_PACK = ORACLE_PACK
TRANCHE_A_ORACLE_BY_MATH_ID = ORACLE_BY_MATH_ID
TRANCHE_A_GOLDEN_VECTOR_BY_MATH_ID = GOLDEN_VECTOR_BY_MATH_ID

_ST12B_VECTOR_ROWS = tuple(json.loads(_ST12B_VECTOR_PACK_JSON))
_ST12B_VECTORS = tuple(
    TrancheBVectorV1(
        vector_id=str(row["vector_id"]),
        math_spec_id=str(row["math_spec_id"]),
        case_type=str(row["case_type"]),
        input_keys=tuple(str(value) for value in row["input_keys"]),
        inputs=_freeze_oracle_value(row["inputs"]),
        expected=_freeze_oracle_value(row["expected"]),
        expected_exception=(
            None
            if row["expected_exception"] is None
            else str(row["expected_exception"])
        ),
    )
    for row in _ST12B_VECTOR_ROWS
)
ST12B_VECTOR_PACK: Mapping[str, TrancheBVectorV1] = MappingProxyType(
    {row.vector_id: row for row in _ST12B_VECTORS}
)
ST12B_VECTORS_BY_MATH_ID: Mapping[
    str, tuple[TrancheBVectorV1, ...]
] = MappingProxyType(
    {
        math_spec_id: tuple(
            row for row in _ST12B_VECTORS if row.math_spec_id == math_spec_id
        )
        for math_spec_id in dict.fromkeys(
            row.math_spec_id for row in _ST12B_VECTORS
        )
    }
)
_ST12B_PROPERTY_ROWS = tuple(json.loads(_ST12B_PROPERTY_PACK_JSON))
_ST12B_PROPERTIES = tuple(
    TrancheBPropertyTestV1(
        test_id=str(row["test_id"]),
        math_spec_id=str(row["math_spec_id"]),
        property_id=str(row["property_id"]),
        base_inputs=_freeze_oracle_value(row["base_inputs"]),
        mutation=_freeze_oracle_value(row["mutation"]),
        required_outcome=str(row["required_outcome"]),
        terminal_state=str(row["terminal_state"]),
    )
    for row in _ST12B_PROPERTY_ROWS
)
ST12B_PROPERTY_TESTS: Mapping[str, TrancheBPropertyTestV1] = MappingProxyType(
    {row.math_spec_id: row for row in _ST12B_PROPERTIES}
)

_ST12B_GOLDEN_ROWS = {
    row.math_spec_id: row
    for row in _ST12B_VECTORS
    if row.case_type == "GOLDEN"
}
_ST12B_ORACLE_ROWS = tuple(json.loads(_ST12B_ORACLE_CONTRACTS_JSON))


def _st12b_oracle(row: object) -> OracleContractV1:
    if not isinstance(row, dict):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "v3.4 oracle row must be an object",
        )
    math_spec_id = str(row["math_spec_id"])
    golden = _ST12B_GOLDEN_ROWS[math_spec_id]
    return OracleContractV1(
        oracle_id=str(row["oracle_id"]),
        math_spec_id=math_spec_id,
        oracle_version="V3_4",
        comparison_policy="CANONICAL_STRUCTURE_WITH_DECLARED_NUMERIC_TOLERANCE",
        expected_value_json=json.dumps(
            _ST12B_VECTOR_ROWS[
                next(
                    index
                    for index, vector in enumerate(_ST12B_VECTOR_ROWS)
                    if vector["vector_id"] == golden.vector_id
                )
            ]["expected"],
            sort_keys=True,
            separators=(",", ":"),
        ),
        independent_algorithm_steps=(
            f"Execute raw declared inputs through {row['dispatcher_path']}.",
            f"Use the independent standard-library module {row['module_path']}.",
            "Do not import or read any QTT production result.",
            "Compare golden, boundary, negative, property, and mutation behavior.",
        ),
        production_import_allowed=False,
        primary_validator_import_allowed=False,
    )


_ST12B_ORACLES = tuple(_st12b_oracle(row) for row in _ST12B_ORACLE_ROWS)


def _st12b_golden_vector(
    oracle: OracleContractV1,
) -> GoldenVectorV1:
    vector = _ST12B_GOLDEN_ROWS[oracle.math_spec_id]
    raw = next(
        row for row in _ST12B_VECTOR_ROWS if row["vector_id"] == vector.vector_id
    )
    seed_value = raw["inputs"].get("seed")
    return GoldenVectorV1(
        vector_id=vector.vector_id,
        math_spec_id=vector.math_spec_id,
        oracle_id=oracle.oracle_id,
        vector_kind="GOLDEN",
        comparison_policy="CANONICAL_STRUCTURE_WITH_DECLARED_NUMERIC_TOLERANCE",
        inputs_json=json.dumps(
            raw["inputs"], sort_keys=True, separators=(",", ":")
        ),
        expected_json=json.dumps(
            raw["expected"], sort_keys=True, separators=(",", ":")
        ),
        seed=(
            seed_value
            if isinstance(seed_value, int) and not isinstance(seed_value, bool)
            else None
        ),
        production_import_allowed=False,
    )


_ST12B_ORACLE_PACK_ENTRIES = tuple(
    OraclePackEntryV1(
        oracle=oracle,
        vector=_st12b_golden_vector(oracle),
        oracle_row_json=json.dumps(
            next(
                row
                for row in _ST12B_ORACLE_ROWS
                if row["math_spec_id"] == oracle.math_spec_id
            ),
            sort_keys=True,
            separators=(",", ":"),
        ),
        vector_row_json=json.dumps(
            next(
                row
                for row in _ST12B_VECTOR_ROWS
                if row["vector_id"]
                == _ST12B_GOLDEN_ROWS[oracle.math_spec_id].vector_id
            ),
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    for oracle in _ST12B_ORACLES
)
ORACLE_PACK = _ST12B_ORACLE_PACK_ENTRIES
ORACLE_BY_MATH_ID = MappingProxyType(
    {entry.oracle.math_spec_id: entry.oracle for entry in ORACLE_PACK}
)
GOLDEN_VECTOR_BY_MATH_ID = MappingProxyType(
    {entry.vector.math_spec_id: entry.vector for entry in ORACLE_PACK}
)
if (
    len(ORACLE_PACK) != 30
    or len(ORACLE_BY_MATH_ID) != 30
    or len(GOLDEN_VECTOR_BY_MATH_ID) != 30
    or len(ST12B_VECTOR_PACK) != 90
    or len(ST12B_VECTORS_BY_MATH_ID) != 30
    or any(len(rows) != 3 for rows in ST12B_VECTORS_BY_MATH_ID.values())
    or len(ST12B_PROPERTY_TESTS) != 30
):
    raise ContractValidationError(
        ReasonCode.ORACLE_NOT_INDEPENDENT,
        "v3.4 oracle closure requires 30 oracles, 90 vectors, and 30 properties",
    )


# Exact frozen Tranche-C oracle/vector payloads are a data-only compatibility
# overlay; predecessor ORACLE_BY_MATH_ID remains its exact 30-row view.
_ST12C_ORACLE_ARCHIVE_B85 = 'c-rlqTXWht6vyB9Q+WK084Mw9coVirJTW#a+iBCzj>Z^~cx!Cdm$YoB-+hk^Nl3Ev!mzW{JueAZN79kbIlunv`0`neL|(@8Sj>2qhfyN<G8cu&@5D?Ud{(1uCO+{jP2yB=*%0Q@Ef13<`zQ_OVN!_J#_FLt7k^c8{-k}e4D-0iQohWRI9jO#l?*-ZyEfOUruWsBDn2bmRDv6KVNwZjhR5k0bPCf_IwJ03b<k<+{Vy#wPG@2%;71xsce88`<GG9&HsurM8q^FJ<-{>LeLJCsPfgCK7uY^0aNP4<21h(PA&mIczUCw5j%7zPFnr5(xKG$Q_3Hs9%o-DR&98`UnFM-r)1@AFT%Q}nwzqp3u1VEx=StY8n=FsZ+XXL5u`JZVdvy}#g;2^{q1<E%7-@H~>MU2{bXk>!@)4}Fs#M~|GK09JH?=9OaaKiToTaiM5epbRlwaF0Az3byRc*F4H5@6xM9h?VmM^L#Y$+nG79y{^wG@a|2qVD+Ev24)v(<8{NX)8S$f1ooZbA`vB3~&p5hd_#rhtRstWp*C{%zLq7-nT1W;q5Ee?qIWh>N104ctmZtDZ55XDubo(s`W5B^;~Zmlmh>Fl9WIW-w|Y7T{PMLDH=h*_swHY$y1--m|v)hun4e$mj8=5?qG_lo@gE+9q`dgE8?hwC*YRvIxstUO=90EVf#z^@j2?%x^?lY~}EKb>y;fU=t3}e@HLrW4dEvIs7~z%!IEKMh(l8nE-Z>*_08-kanIMFoVjYfn)i6XgQ|koJ+4a6$jf|Kys+iKqnM_I6h=9F?`wQ!aBd;k7F}BqKvKw-gJ*=59z<X*i9>hu7HJsiQd+k4h_pZUWECI*8vD2aQs>At&{IXl|N=7f0~86Iy?YDMl=x+Gf@=0&P#B|aK{sy`jq>WjV*`Rux4rmJ{j6_v+8R0pnR>7We{0m;JS<*z$#i#dlN2U=t=^j^QCp9ta`drVFmS_$A524h%`f*A<cf6W}dHi4b2D`^!KfI)YSBL=LqTMxOFYPl|@SlGcMr6?|}tHD|wbxc~nQZ;8B(5LIUKydhN1Hjb2&WnEDs4DL3~k<ooUO|0d$raWx^FV`6_Bj2{GKJ)eV%<vNI+cDJLVqC*Dm!@yTN8ThJs419%(?kK^9@($64XgfUGnk?@wscm0t`dR<9G0N^9jbXxTR@R8rQQIK^_XFVTodA5@JOI8%ZFi*TLUo65L%1CtZcSEqBUrwyLSk!cp|?4S*J`5ftI9Zu%QZ7QrzrQ3h<g$7Y$p-Vnn%PllzYcTEL3^OG-TT0nbu^L2Ss}6zOnpwQqOgdSI_<6r7ID9RtLRyr={M1LQRMK+k=0-&My9~TN=f`dP%71j*MEU>yT^6wZn6*$+`~0a!E#TqK+^vVAsT>SDJA}SYs64LvsN%EMeRPRUXoCZyM@5X{a}khB~Ue<0Ka<J!BiQ?eJ`CveLURbj`bPnLmQkY})M>&$f6An<{V<FU~_Q?#IRMPA+zv$Hgvcz9UB%ia&%LLhkU8YqI#8PzKS~EIGs&mRD2pQ3*Ci0v6y_I0Mg%vi@faRUZOzPayVo0<qUTAofu89Urw&=pomTYlr6=3cX_&dNp$T=7bO3z%hY4-*H=;5ImfhBIh}*W(FlzqqN)abYyI0^Hcx>#PfC(hzQcXKzgzhq$kY-=?MzN=Fkp>CGrq?cz7N*T3EXFwY&+0`r5he4&iR!5vAV!Vr6t54TgaQiNT&){6xxgNSsT`JZ{K5`F<!b!VduCa3R;Uq4P9M;aIUvVXf2NTxqdo{Swx-ndCW`mRqJZ$NP9%6DhqPrTaT6-ESVH`>0xfT~h8IxE8|CjQ?FOcRF}37GaDq{?B0ii%90c`x(XXw?Up}^)^dC!{S5zkcqy00@6wpFB(oxP_!Z^_u}Nv$N%@5_xS%FzRct&BN}Q$WF9i_@XTxUGqH*7U09mS;5_NjbuW)!8G@HKB@VY7xINq=j_-ZPgDN0G({%~MB$0@h<<?|nUag}t4X5%UWicRjD*yit<8`?H(qP4*_&Ag`TrMSxlTTN?X01#YX^i?3S-THwcfNn1ca-lR7_tDc12eCC!n|<VkAMAGnqOrtzFOs%<RYq6Bqx&d@Z@Z=N_F2j@Mrun@c_dUn>gB)4o{J7pETzD<wNs4P7?lCB}<}ySnera7m7&S4~aWpchGCz>kfMOE|+7*7ivBP90Km}fJ4pqQuF--Zos1W'
_ST12C_VECTOR_ARCHIVE_B85 = 'c-rloZFAZ<5Xax&$M9<>;|Cm)ymO3uWsX44flhm!jz$=9(ZtxUB$Lw2efL|*(15YskPu1>GnomoR<gAF^B-xwdC)?_1RYZ{LQ@iogrSrXPS});w95xAOeQI2lqWGtlZb{h?NW2EZcxA1L8gCVI-0JLuPOA*?a7pCm&U2-{HJR)PBX#fRUCfFD5rwLFk!-lGSRg#V~oTC;ZU_qag-6T|74sxx^de0tZOm3M>HNMY=V^u4@nHuNu-q=w%G3+`dQE~Wyuf^X+*_L-V0_^W^IFYv&{N4%pUG|i#V(dF*1f#U%UOcC)OFPH(@x8$oz6IaJ`OydHL83{tIETYN@dxUtzUc%lF#XZU@;76!Zq&7JBP;-XQ<I-$lIuL2Jhi{1$rC>A8LBTR(8Sp05T=Mp-^_I!Plk0e|7ep9ursMNx7ueLuz#C%Ptshgo=wWaJ_uNK80K96Ax0hu6D)*YW#4>ifZUy9+b=v)5_CEZ+NGA7%nSH~nDX^#=j8wY%@#pzU`1FcD7VP2wzybZrg_g$r8Ve|i1$);k)@_U_=?58B@RJ{maoDM-!9px^SfP6?9^1;d-ZX?Z8!APD?!zx|KjIx$a;ItEvrhBI-SF#2uDVMj{$m(p$zdA*kZ0R{ez?*`sm`0)3j4U^a+k$*fqLj(N}uGdF%hZXp{BT+O%W0r>!j3L^Fwjziz5hxjr;Io$Vdrx8T<p4vcGu5d)!p-^!HxFEgn$OgsVpw0KL)9E?AWBD4wx<Qn-D|-j`Zz)g2Nf=}pau&gG|3`C(})tL>>L^IF)Rv|qXfRA{0@aUU4pBeg7bO`&JSEK&i6qt>R8!8F^)9tQd7=%uPK>$RDR=ZRZ1oV#}E^dv3P;cJg)c=MhmV9hGRYlCEx67(sT+F!Es3P!5h^GT+}0Qao~b-u@8b$0?GzDazttOYI5;9YEqZ62_a6}rG09sh^bGjxtl1x#qz+}baX9BIM0uzx~W^bU3mnxjoP59<^$FTwf>);D5(hjCMlD{hU4W={1ZUf`V+tSj5q{Vz>1@-J@saNV9f)6>dn1Kk5-5O^`HFT1&}Q~`R49V4h0u10iXc^g{;JA5r&k}`7X}MSt4O33Jq3%Czt~jXiUgFU!{aTm5$D0*oms`A<E)0jUqWCwNFgMEn%vK&#!#RFu<)guBIA-(~-Q-)!<|0F4DH@$+8YydaQjokUWLI4K(OT=&!1M*6y{BLvK7<98k?QxhsRF(SSiFbd)Akz5o<xL0sNyKbHi%o&@{AwaVTHt*YQ<19>_U^;5LP-hs9t7kuTk-k~e$H8=QJOyv`T@L0gN21~MdMB{%ILzZKxh|1<6fr0^2Y+uzR87P^h=igb7Jz4HENUAw15=-BGm3%bn`Dh%t;xx9QIAu`0?1j*aDB3`&j-0)M4mEbALsxG1FF&|J9*|TeNE3Vq7~u(UBIZmDaSYe^GCL<wZ6uGSE7t3XDKkl-O#UyKD*7DbM;exo4tr{W^T7-ltVq~m<b~Pd4MsV3PCa(cfy<k-HF>LI?L|7b6F92}R*G3LF4tAV*nAhbJ^r2FpZ_h$uCx22Wt=E4$l)-*%Ofc30%nA-H8dK9O27nIgOtNiEd@HN;!HeCGVz$8kOQq)HLPkD>We?^120jw&-USP`3zz<sTn*n^?Lg9N(IGNJy^cmeFXZZ__7v9bjWfifU5~j1^kAJbtc;d%gAzxIF-?rUtTZ;1DWdvGZe!>kbQtG2ZwJsG@Kztlw?>Muc#Eq6M_;pQfW{X-GwnYnZPAkp!&(w9o;snU;fmWqT0WE(X!n%%sR5x%Tr5-tI(%XfL>M}@DqsJK;@21Zm4YA;&1Ewr|)m1<y#lDl>a;{<il3l(TH-v=rGHRSm8fyie>TEYBp7F-Per@DOac5%2`j$R{#HvU0)w-A9%I3y%*KiKZ0(Pit8hmzuGSD31!>=1N4Q8?E'


def _decode_st12c_rows(payload: str) -> tuple[dict[str, object], ...]:
    text = zlib.decompress(base64.b85decode(payload.encode("ascii"))).decode("utf-8-sig")
    return tuple(json.loads(line) for line in text.splitlines() if line.strip())


_ST12C_ORACLE_ROWS = _decode_st12c_rows(_ST12C_ORACLE_ARCHIVE_B85)
_ST12C_VECTOR_ROWS = _decode_st12c_rows(_ST12C_VECTOR_ARCHIVE_B85)


def _st12c_oracle(row: Mapping[str, object]) -> OracleContractV1:
    return OracleContractV1(
        oracle_id=str(row["oracle_id"]),
        math_spec_id=str(row["math_spec_ref"]),
        oracle_version=str(row["oracle_version"]),
        comparison_policy=str(row["comparison_policy"]),
        expected_value_json=json.dumps(row["expected_value_or_invariant"], sort_keys=True, separators=(",", ":")),
        independent_algorithm_steps=tuple(str(value) for value in row["independent_algorithm_steps"]),
        production_import_allowed=False,
        primary_validator_import_allowed=False,
    )


def _st12c_vector(row: Mapping[str, object], oracle: OracleContractV1) -> GoldenVectorV1:
    seed = row["seed"]
    return GoldenVectorV1(
        vector_id=str(row["vector_id"]),
        math_spec_id=str(row["math_spec_ref"]),
        oracle_id=oracle.oracle_id,
        vector_kind=str(row["vector_kind"]),
        comparison_policy=str(row["comparison_policy"]),
        inputs_json=json.dumps(row["inputs"], sort_keys=True, separators=(",", ":")),
        expected_json=json.dumps(row["expected"], sort_keys=True, separators=(",", ":")),
        seed=seed if isinstance(seed, int) and not isinstance(seed, bool) else None,
        production_import_allowed=False,
    )


_ST12C_ORACLES = tuple(_st12c_oracle(row) for row in _ST12C_ORACLE_ROWS)
_ST12C_ORACLE_BY_ID = {row.math_spec_id: row for row in _ST12C_ORACLES}
ST12C_ORACLE_PACK = tuple(
    OraclePackEntryV1(
        oracle=oracle,
        vector=_st12c_vector(
            next(row for row in _ST12C_VECTOR_ROWS if row["math_spec_ref"] == oracle.math_spec_id),
            oracle,
        ),
        oracle_row_json=json.dumps(
            next(row for row in _ST12C_ORACLE_ROWS if row["math_spec_ref"] == oracle.math_spec_id),
            sort_keys=True,
            separators=(",", ":"),
        ),
        vector_row_json=json.dumps(
            next(row for row in _ST12C_VECTOR_ROWS if row["math_spec_ref"] == oracle.math_spec_id),
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    for oracle in _ST12C_ORACLES
)
ST12C_ORACLE_BY_MATH_ID: Mapping[str, OracleContractV1] = MappingProxyType(
    {entry.oracle.math_spec_id: entry.oracle for entry in ST12C_ORACLE_PACK}
)
ST12C_GOLDEN_VECTOR_BY_MATH_ID: Mapping[str, GoldenVectorV1] = MappingProxyType(
    {entry.vector.math_spec_id: entry.vector for entry in ST12C_ORACLE_PACK}
)
ST12C_CUMULATIVE_ORACLE_BY_MATH_ID: Mapping[str, OracleContractV1] = MappingProxyType(
    {**ORACLE_BY_MATH_ID, **ST12C_ORACLE_BY_MATH_ID}
)
ST12C_CUMULATIVE_GOLDEN_VECTOR_BY_MATH_ID: Mapping[str, GoldenVectorV1] = MappingProxyType(
    {**GOLDEN_VECTOR_BY_MATH_ID, **ST12C_GOLDEN_VECTOR_BY_MATH_ID}
)

if (
    len(ST12C_ORACLE_PACK) != 13
    or len(ST12C_ORACLE_BY_MATH_ID) != 13
    or len(ST12C_GOLDEN_VECTOR_BY_MATH_ID) != 13
    or tuple(ST12C_ORACLE_BY_MATH_ID) != tuple(f"MATH-{number}" for number in range(26, 39))
    or len(ST12C_CUMULATIVE_ORACLE_BY_MATH_ID) != 42
    or any(entry.oracle.production_import_allowed or entry.vector.production_import_allowed for entry in ST12C_ORACLE_PACK)
):
    raise ContractValidationError(ReasonCode.ORACLE_NOT_INDEPENDENT, "Tranche-C independent oracle/vector closure must be exact 13/13/13")
