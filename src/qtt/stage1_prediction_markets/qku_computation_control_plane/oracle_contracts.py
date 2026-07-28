"""Data-only independent-oracle and golden-vector contract materialization."""

from __future__ import annotations

from dataclasses import dataclass
import json
from types import MappingProxyType
from typing import Mapping

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


@dataclass(frozen=True, slots=True)
class TrancheBOracleCoverageRowV1:
    """Exact certified B row custody without creating a second oracle owner."""

    math_spec_id: str
    oracle_id: str
    vector_id: str
    oracle_row_json: str
    vector_row_json: str

    def __post_init__(self) -> None:
        for name in (
            "math_spec_id",
            "oracle_id",
            "vector_id",
            "oracle_row_json",
            "vector_row_json",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.ORACLE_NOT_INDEPENDENT,
                    f"Tranche-B coverage {name} is required",
                )
        oracle_row = json.loads(self.oracle_row_json)
        vector_row = json.loads(self.vector_row_json)
        if (
            not isinstance(oracle_row, dict)
            or not isinstance(vector_row, dict)
            or oracle_row.get("math_spec_ref") != self.math_spec_id
            or vector_row.get("math_spec_ref") != self.math_spec_id
            or oracle_row.get("oracle_id") != self.oracle_id
            or vector_row.get("oracle_ref") != self.oracle_id
            or vector_row.get("vector_id") != self.vector_id
        ):
            raise ContractValidationError(
                ReasonCode.ORACLE_NOT_INDEPENDENT,
                "Tranche-B oracle/vector coverage lineage is inconsistent",
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

_TRANCHE_B_ORACLE_ROWS_JSON = r'''
[{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_DECIMAL","expected_value_or_invariant":{"p_market":"0.42"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-01","math_spec_ref":"MATH-01","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-01","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-15","expected_value_or_invariant":{"edge_probability":"0.06"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-02","math_spec_ref":"MATH-02","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-02","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_DECIMAL","expected_value_or_invariant":{"mid":"0.43"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-03","math_spec_ref":"MATH-03","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-03","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_DECIMAL","expected_value_or_invariant":{"spread":"0.02"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-04","math_spec_ref":"MATH-04","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-04","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT","expected_value_or_invariant":{"relative_spread":"0.04651162790697674418604651162790698"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-05","math_spec_ref":"MATH-05","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-05","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_DECIMAL","expected_value_or_invariant":{"expected_net_cash":"0.14"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-06","math_spec_ref":"MATH-06","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-06","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_DECIMAL","expected_value_or_invariant":{"expected_net_cash":"0.17"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-07","math_spec_ref":"MATH-07","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-07","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_DECIMAL","expected_value_or_invariant":{"brier_score":"0.09"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-08","math_spec_ref":"MATH-08","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-08","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-15","expected_value_or_invariant":{"log_loss":0.35667494393873245},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-09","math_spec_ref":"MATH-09","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-09","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-15","expected_value_or_invariant":{"ece":0.25},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-10","math_spec_ref":"MATH-10","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-10","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-12","expected_value_or_invariant":{"lower":0.49015684672072335,"upper":0.9433190520193067},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-11","math_spec_ref":"MATH-11","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-11","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_ORDER_AND_INDEX_SET","expected_value_or_invariant":{"largest_rank":2,"rejected_original_indices":[0,1]},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-12","math_spec_ref":"MATH-12","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-12","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_ORDER_AND_INDEX_SET","expected_value_or_invariant":{"largest_rank":2,"rejected_original_indices":[0,1]},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-13","math_spec_ref":"MATH-13","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-13","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"BOOLEAN_INVARIANTS","expected_value_or_invariant":{"interval_contains_sample_mean":true,"same_seed_reproducible":true},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-14","math_spec_ref":"MATH-14","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-14","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-15","expected_value_or_invariant":{"p_value":1.0,"reject":false},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-15","math_spec_ref":"MATH-15","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-15","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-15","expected_value_or_invariant":{"p_value":1.0,"reject":false},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-16","math_spec_ref":"MATH-16","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-16","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-12","expected_value_or_invariant":{"psr":0.9999986367476719,"z_score":4.69041575982343},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-17","math_spec_ref":"MATH-17","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-17","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"BOOLEAN_INVARIANTS","expected_value_or_invariant":{"bounded_0_1":true,"dsr_monotone_nonincreasing_with_trial_count":true},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-18","math_spec_ref":"MATH-18","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-18","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-15","expected_value_or_invariant":{"bounded_0_1":true,"pbo":0.5},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-19","math_spec_ref":"MATH-19","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-19","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_INDEX_SET","expected_value_or_invariant":{"embargo_respected":true,"no_interval_overlap":true,"training_indices":[2,3]},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-20","math_spec_ref":"MATH-20","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-20","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_COUNT_AND_BOOLEAN","expected_value_or_invariant":{"every_split_purged_and_embargoed":true,"no_post_hoc_path_selection":true,"split_count":6},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-21","math_spec_ref":"MATH-21","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-21","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-12","expected_value_or_invariant":{"dr_estimate":0.74},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-22","math_spec_ref":"MATH-22","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-22","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-15","expected_value_or_invariant":{"ips":0.8},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-23","math_spec_ref":"MATH-23","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-23","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-12_NOT_EXACT_BINARY_FLOAT_EQUALITY","expected_value_or_invariant":{"snips":0.8},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-24","math_spec_ref":"MATH-24","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-24","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_INDEX_SET","expected_value_or_invariant":{"deterministic_selection":true,"direct_model_indices":[1],"importance_corrected_indices":[0]},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-25","math_spec_ref":"MATH-25","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-25","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_DECIMAL","expected_value_or_invariant":{"no_implied_ask":"0.58","yes_implied_ask":"0.44"},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-36","math_spec_ref":"MATH-36","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-36","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ABS_TOL_1E-15","expected_value_or_invariant":{"energy":4.6},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-46","math_spec_ref":"MATH-46","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_EXACT_OR_HIGH_PRECISION_REFERENCE","oracle_id":"ORACLE::MATH-46","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"ENUMERATION_INVARIANT","expected_value_or_invariant":{"all_binary_assignments_energy_equal_after_ising_transform":true,"assignment_count":4},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-47","math_spec_ref":"MATH-47","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-47","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"BRUTE_FORCE_ENUMERATION","expected_value_or_invariant":{"all_returned_solutions_feasible":true,"optimal_objective":1},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-48","math_spec_ref":"MATH-48","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-48","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0},{"codex_online_research_allowed":false,"codex_research_required":false,"comparison_policy":"EXACT_DISCRETE_ENUMERATION","expected_value_or_invariant":{"minimum_energy_assignment":{"a":"A0","b":"B0"},"one_case_per_variable":true},"independence_proof":"ORACLE_PROCEDURE_AND_EXPECTED_RESULT_ARE_STORED_SEPARATELY_FROM_PRODUCTION_TARGET_AND_PRIMARY_VALIDATOR_DOES_NOT_CALL_PRODUCTION_CODE","independent_algorithm_steps":["Parse the golden-vector inputs without importing the production implementation.","Apply the independently stated formula, enumeration, resampling, or invariant procedure.","Compare every declared output using the vector comparison policy.","Reject missing, stale, invalid, nonfinite, unit-incompatible, or semantically inconsistent inputs."],"input_fixture_ref":"GOLDEN::MATH-49","math_spec_ref":"MATH-49","mutation_targets_required":["FORMULA_OR_PROCEDURE","DOMAIN_GUARD","PRECISION_OR_TOLERANCE","SOURCE_OR_UNIT_BINDING"],"oracle_class":"INDEPENDENT_BRUTE_FORCE_OR_PROPERTY_INVARIANT","oracle_id":"ORACLE::MATH-49","oracle_version":"1.1R1","primary_validator_expected_value_import_allowed":false,"production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION","specification_gap_count":0}]
'''

_TRANCHE_B_GOLDEN_VECTOR_ROWS_JSON = r'''
[{"comparison_policy":"EXACT_DECIMAL","expected":{"p_market":"0.42"},"inputs":{"contract_price":"0.42","payout_per_winning_contract":"1.00"},"math_spec_ref":"MATH-01","oracle_ref":"ORACLE::MATH-01","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-01","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"ABS_TOL_1E-15","expected":{"edge_probability":"0.06"},"inputs":{"calibrated_model_probability":"0.58","market_implied_probability":"0.52"},"math_spec_ref":"MATH-02","oracle_ref":"ORACLE::MATH-02","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-02","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"EXACT_DECIMAL","expected":{"mid":"0.43"},"inputs":{"best_ask":"0.44","best_bid":"0.42"},"math_spec_ref":"MATH-03","oracle_ref":"ORACLE::MATH-03","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-03","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"EXACT_DECIMAL","expected":{"spread":"0.02"},"inputs":{"best_ask":"0.44","best_bid":"0.42"},"math_spec_ref":"MATH-04","oracle_ref":"ORACLE::MATH-04","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-04","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT","expected":{"relative_spread":"0.04651162790697674418604651162790698"},"inputs":{"best_ask":"0.44","best_bid":"0.42"},"math_spec_ref":"MATH-05","oracle_ref":"ORACLE::MATH-05","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-05","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"EXACT_DECIMAL","expected":{"expected_net_cash":"0.14"},"inputs":{"acquisition_cost":"0","expected_impact":"0","expected_slippage":"0","fees":"0.01","lose_cash":"-0.45","p":"0.60","quantity":"1","win_cash":"0.55"},"math_spec_ref":"MATH-06","oracle_ref":"ORACLE::MATH-06","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-06","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"EXACT_DECIMAL","expected":{"expected_net_cash":"0.17"},"inputs":{"acquisition_cost":"0.02","expected_impact":"0","expected_slippage":"0","fees":"0","payoffs":["1.0","-0.2","0.1"],"probabilities":["0.2","0.3","0.5"],"quantity":"1"},"math_spec_ref":"MATH-07","oracle_ref":"ORACLE::MATH-07","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-07","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"EXACT_DECIMAL","expected":{"brier_score":"0.09"},"inputs":{"outcome":1,"probability":"0.70"},"math_spec_ref":"MATH-08","oracle_ref":"ORACLE::MATH-08","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-08","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"ABS_TOL_1E-15","expected":{"log_loss":0.35667494393873245},"inputs":{"clip_epsilon":1e-15,"outcome":1,"probability":0.7},"math_spec_ref":"MATH-09","oracle_ref":"ORACLE::MATH-09","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-09","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"ABS_TOL_1E-15","expected":{"ece":0.25},"inputs":{"bins":[{"count":2,"empirical_frequency":0.5,"mean_confidence":0.8},{"count":2,"empirical_frequency":0.5,"mean_confidence":0.3}]},"math_spec_ref":"MATH-10","oracle_ref":"ORACLE::MATH-10","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-10","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"ABS_TOL_1E-12","expected":{"lower":0.49015684672072335,"upper":0.9433190520193067},"inputs":{"successes":8,"trials":10,"z":1.96},"math_spec_ref":"MATH-11","oracle_ref":"ORACLE::MATH-11","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-11","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"EXACT_ORDER_AND_INDEX_SET","expected":{"largest_rank":2,"rejected_original_indices":[0,1]},"inputs":{"p_values":[0.001,0.01,0.04,0.2],"q":0.05},"math_spec_ref":"MATH-12","oracle_ref":"ORACLE::MATH-12","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":1201,"vector_id":"GOLDEN::MATH-12","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"EXACT_ORDER_AND_INDEX_SET","expected":{"largest_rank":2,"rejected_original_indices":[0,1]},"inputs":{"p_values":[0.001,0.01,0.04,0.2],"q":0.05},"math_spec_ref":"MATH-13","oracle_ref":"ORACLE::MATH-13","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":1301,"vector_id":"GOLDEN::MATH-13","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"BOOLEAN_INVARIANTS","expected":{"interval_contains_sample_mean":true,"same_seed_reproducible":true},"inputs":{"mean_block_length":2,"replicates":64,"seed":1401,"series":[1,2,3,4,5]},"math_spec_ref":"MATH-14","oracle_ref":"ORACLE::MATH-14","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":1401,"vector_id":"GOLDEN::MATH-14","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"ABS_TOL_1E-15","expected":{"p_value":1.0,"reject":false},"inputs":{"differentials":[[0,0,0,0],[0,0,0,0]],"replicates":64,"seed":1501},"math_spec_ref":"MATH-15","oracle_ref":"ORACLE::MATH-15","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":1501,"vector_id":"GOLDEN::MATH-15","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"ABS_TOL_1E-15","expected":{"p_value":1.0,"reject":false},"inputs":{"differentials":[[0,0,0,0],[0,0,0,0]],"replicates":64,"seed":1601},"math_spec_ref":"MATH-16","oracle_ref":"ORACLE::MATH-16","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":1601,"vector_id":"GOLDEN::MATH-16","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"ABS_TOL_1E-12","expected":{"psr":0.9999986367476719,"z_score":4.69041575982343},"inputs":{"kurtosis":3.0,"n":100,"sharpe_hat":0.5,"sharpe_ref":0.0,"skewness":0.0},"math_spec_ref":"MATH-17","oracle_ref":"ORACLE::MATH-17","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-17","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"BOOLEAN_INVARIANTS","expected":{"bounded_0_1":true,"dsr_monotone_nonincreasing_with_trial_count":true},"inputs":{"observed_sharpe":1.0,"other_moments_fixed":true,"trial_counts":[1,10,100]},"math_spec_ref":"MATH-18","oracle_ref":"ORACLE::MATH-18","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":1801,"vector_id":"GOLDEN::MATH-18","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"ABS_TOL_1E-15","expected":{"bounded_0_1":true,"pbo":0.5},"inputs":{"split_oos_relative_ranks":[0.25,0.75,0.4,0.9]},"math_spec_ref":"MATH-19","oracle_ref":"ORACLE::MATH-19","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":1901,"vector_id":"GOLDEN::MATH-19","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"EXACT_INDEX_SET","expected":{"embargo_respected":true,"no_interval_overlap":true,"training_indices":[2,3]},"inputs":{"embargo":1,"intervals":[[0,3],[1,4],[5,6],[7,9]],"test_indices":[1]},"math_spec_ref":"MATH-20","oracle_ref":"ORACLE::MATH-20","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":2001,"vector_id":"GOLDEN::MATH-20","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"EXACT_COUNT_AND_BOOLEAN","expected":{"every_split_purged_and_embargoed":true,"no_post_hoc_path_selection":true,"split_count":6},"inputs":{"groups":4,"test_groups_per_split":2},"math_spec_ref":"MATH-21","oracle_ref":"ORACLE::MATH-21","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":2101,"vector_id":"GOLDEN::MATH-21","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"ABS_TOL_1E-12","expected":{"dr_estimate":0.74},"inputs":{"samples":[{"mu_logged":0.5,"pi_logged":0.8,"pi_q_sum":0.5,"q_logged":0.6,"reward":1.0},{"mu_logged":0.5,"pi_logged":0.2,"pi_q_sum":0.5,"q_logged":0.4,"reward":0.0}]},"math_spec_ref":"MATH-22","oracle_ref":"ORACLE::MATH-22","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-22","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"ABS_TOL_1E-15","expected":{"ips":0.8},"inputs":{"rewards":[1.0,0.0],"weights":[1.6,0.4]},"math_spec_ref":"MATH-23","oracle_ref":"ORACLE::MATH-23","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-23","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"ABS_TOL_1E-12_NOT_EXACT_BINARY_FLOAT_EQUALITY","expected":{"snips":0.8},"inputs":{"rewards":[1.0,0.0],"weights":[1.6,0.4]},"math_spec_ref":"MATH-24","oracle_ref":"ORACLE::MATH-24","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-24","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"EXACT_INDEX_SET","expected":{"deterministic_selection":true,"direct_model_indices":[1],"importance_corrected_indices":[0]},"inputs":{"direct_estimates":[0.6,0.4],"rewards":[1.0,0.0],"tau":1.0,"weights":[0.5,3.0]},"math_spec_ref":"MATH-25","oracle_ref":"ORACLE::MATH-25","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":2501,"vector_id":"GOLDEN::MATH-25","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"EXACT_DECIMAL","expected":{"no_implied_ask":"0.58","yes_implied_ask":"0.44"},"inputs":{"no_best_bid":"0.56","payout":"1.00","yes_best_bid":"0.42"},"math_spec_ref":"MATH-36","oracle_ref":"ORACLE::MATH-36","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-36","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"ABS_TOL_1E-15","expected":{"energy":4.6},"inputs":{"diagonal":[1,2,3],"offset":0.1,"upper_terms":[{"i":0,"j":2,"value":0.5}],"x":[1,0,1]},"math_spec_ref":"MATH-46","oracle_ref":"ORACLE::MATH-46","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":null,"vector_id":"GOLDEN::MATH-46","vector_kind":"NUMERIC_GOLDEN"},{"comparison_policy":"ENUMERATION_INVARIANT","expected":{"all_binary_assignments_energy_equal_after_ising_transform":true,"assignment_count":4},"inputs":{"qubo":{"diagonal":[1,2],"offset":0.1,"upper_terms":[{"i":0,"j":1,"value":0.5}]}},"math_spec_ref":"MATH-47","oracle_ref":"ORACLE::MATH-47","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":4701,"vector_id":"GOLDEN::MATH-47","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"BRUTE_FORCE_ENUMERATION","expected":{"all_returned_solutions_feasible":true,"optimal_objective":1},"inputs":{"constraints":["x+y<=1"],"domains":{"x":"BINARY","y":"BINARY"},"objective":"maximize x+y"},"math_spec_ref":"MATH-48","oracle_ref":"ORACLE::MATH-48","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":4801,"vector_id":"GOLDEN::MATH-48","vector_kind":"STRUCTURAL_INVARIANT"},{"comparison_policy":"EXACT_DISCRETE_ENUMERATION","expected":{"minimum_energy_assignment":{"a":"A0","b":"B0"},"one_case_per_variable":true},"inputs":{"discrete_variables":{"a":["A0","A1"],"b":["B0","B1"]},"linear_biases":{"A0":0,"A1":1,"B0":0,"B1":1},"pairwise_biases":{}},"math_spec_ref":"MATH-49","oracle_ref":"ORACLE::MATH-49","precision_context":"DECIMAL_34_ROUND_HALF_EVEN_OR_DECLARED_FLOAT_TOLERANCE","production_implementation_import_allowed":false,"research_completeness_state":"COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT","seed":4901,"vector_id":"GOLDEN::MATH-49","vector_kind":"STRUCTURAL_INVARIANT"}]
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


def _load_pack(
    oracle_rows_json: str,
    vector_rows_json: str,
    *,
    expected_math_ids: tuple[str, ...],
) -> tuple[OraclePackEntryV1, ...]:
    oracle_rows = json.loads(oracle_rows_json)
    vector_rows = json.loads(vector_rows_json)
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
        len(oracles) != len(expected_math_ids)
        or len(vectors) != len(expected_math_ids)
        or set(oracles) != set(vectors)
    ):
        raise ContractValidationError(
            ReasonCode.ORACLE_NOT_INDEPENDENT,
            "oracle pack must contain the exact aligned oracle/vector roster",
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
            "oracle/vector identities or versions do not match the roster",
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


TRANCHE_A_ORACLE_MATH_IDS = (
    *(f"MATH-{index:02d}" for index in range(1, 16)),
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
TRANCHE_B_ORACLE_MATH_IDS = (
    *(f"MATH-{index:02d}" for index in range(1, 26)),
    "MATH-36",
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
TRANCHE_A_ORACLE_PACK = _load_pack(
    _ORACLE_ROWS_JSON,
    _GOLDEN_VECTOR_ROWS_JSON,
    expected_math_ids=TRANCHE_A_ORACLE_MATH_IDS,
)
_TRANCHE_B_CERTIFIED_PACK = _load_pack(
    _TRANCHE_B_ORACLE_ROWS_JSON,
    _TRANCHE_B_GOLDEN_VECTOR_ROWS_JSON,
    expected_math_ids=TRANCHE_B_ORACLE_MATH_IDS,
)
_TRANCHE_B_NEW_MATH_IDS = tuple(
    math_id
    for math_id in TRANCHE_B_ORACLE_MATH_IDS
    if math_id not in TRANCHE_A_ORACLE_MATH_IDS
)
ORACLE_PACK = TRANCHE_A_ORACLE_PACK + tuple(
    entry
    for entry in _TRANCHE_B_CERTIFIED_PACK
    if entry.oracle.math_spec_id in _TRANCHE_B_NEW_MATH_IDS
)
if (
    len(TRANCHE_A_ORACLE_PACK) != 19
    or len(_TRANCHE_B_CERTIFIED_PACK) != 30
    or len(ORACLE_PACK) != 30
    or len({entry.oracle.math_spec_id for entry in ORACLE_PACK}) != 30
):
    raise ContractValidationError(
        ReasonCode.ORACLE_NOT_INDEPENDENT,
        "A/B oracle packs must preserve A and form a 30-identity union",
    )
TRANCHE_B_ORACLE_COVERAGE_ROWS = tuple(
    TrancheBOracleCoverageRowV1(
        math_spec_id=entry.oracle.math_spec_id,
        oracle_id=entry.oracle.oracle_id,
        vector_id=entry.vector.vector_id,
        oracle_row_json=entry.oracle_row_json,
        vector_row_json=entry.vector_row_json,
    )
    for entry in _TRANCHE_B_CERTIFIED_PACK
)
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
