#!/usr/bin/env python3
"""Independent static validation of Tranche-B model-risk closure."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "qku_computation_control_plane"
)
EXPECTED_CLOSURES = {
    f"ST12-CLOSURE::ST11-MODEL-RISK::{index:03d}"
    for index in range(1, 9)
}
EXPECTED_MATH_IDS = {
    *(f"MATH-{index:02d}" for index in range(1, 26)),
    "MATH-36",
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
}
SUCCESS_MARKER = "QKU_MODEL_RISK_INDEPENDENTLY_VALIDATED"


def _literal_assignment(tree: ast.Module, name: str) -> object | None:
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets
                if isinstance(node, ast.Assign)
                else (node.target,)
            )
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in targets
            ):
                value = node.value
                if value is None:
                    return None
                try:
                    return ast.literal_eval(value)
                except (TypeError, ValueError):
                    return None
    return None


def _json_assignment(tree: ast.Module, name: str) -> object | None:
    raw = _literal_assignment(tree, name)
    if not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _implementation_function_names(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("compute_math_")
    }


def _expected_function_name(math_id: str) -> str:
    return f"compute_math_{int(math_id.split('-')[1]):02d}_"


def main() -> int:
    failures: list[str] = []
    trees: dict[str, ast.Module] = {}
    for name in (
        "validation.py",
        "specification.py",
        "oracle_contracts.py",
        "implementation_registry.py",
    ):
        path = PACKAGE / name
        try:
            trees[name] = ast.parse(
                path.read_text(encoding="utf-8"),
                filename=str(path),
            )
        except (OSError, SyntaxError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

    payload = _json_assignment(
        trees["validation.py"],
        "_TRANCHE_B_MACHINE_ROWS_JSON",
    )
    closure_rows = (
        payload.get("closure_rows")
        if isinstance(payload, dict)
        else None
    )
    selected = [
        row
        for row in closure_rows or []
        if isinstance(row, dict) and row.get("domain") == "model_risk"
    ]
    if {str(row.get("closure_id")) for row in selected} != EXPECTED_CLOSURES:
        failures.append("the eight exact certified model-risk closures differ")
    for row in selected:
        implementation = row.get("implementation_specification")
        if (
            row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_CLOSURE_SPECIFICATION"
            or not isinstance(implementation, dict)
            or implementation.get("runtime_effect_authorized")
            or implementation.get("open_research_questions") != []
            or not implementation.get("canonical_owner")
            or not implementation.get("independent_validator_owner")
            or not implementation.get("failure_behavior")
            or not implementation.get("fallback")
        ):
            failures.append(
                f"{row.get('closure_id')}: nonterminal model-risk contract"
            )

    math_rows = _json_assignment(
        trees["specification.py"],
        "_TRANCHE_B_MATH_SPECIFICATION_ROWS_JSON",
    )
    if not isinstance(math_rows, list) or {
        str(row.get("math_spec_id"))
        for row in math_rows
        if isinstance(row, dict)
    } != EXPECTED_MATH_IDS:
        failures.append("the exact 30 Tranche-B math specifications differ")
    else:
        required_fields = {
            "math_spec_id",
            "inputs",
            "output",
            "input_shapes",
            "output_shape",
            "unit_and_basis_contract",
            "assumptions",
            "boundary_behavior",
            "missing_stale_invalid_nonfinite_behavior",
            "precision_and_rounding_policy",
            "specification_version",
            "deterministic_seed_policy",
            "source_identity_refs",
            "registered_classical_fallback",
            "mandatory_comparator_or_reconciliation",
        }
        for row in math_rows:
            missing = {
                name
                for name in required_fields
                if name not in row
            }
            if (
                missing
                or row.get("research_completeness_state")
                != "COMPLETE_TERMINAL_MATH_SPECIFICATION"
                or row.get("semantic_status")
                != "COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION"
                or row.get("specification_gap_count") != 0
                or row.get("codex_online_research_allowed")
                or row.get("live_order_authority")
                or row.get("qpu_execution_allowed")
                or row.get("profit_or_advantage_claim_allowed")
            ):
                failures.append(
                    f"{row.get('math_spec_id')}: incomplete math-risk contract"
                )

    oracle_rows = _json_assignment(
        trees["oracle_contracts.py"],
        "_TRANCHE_B_ORACLE_ROWS_JSON",
    )
    vector_rows = _json_assignment(
        trees["oracle_contracts.py"],
        "_TRANCHE_B_GOLDEN_VECTOR_ROWS_JSON",
    )
    if not isinstance(oracle_rows, list) or len(oracle_rows) != 30:
        failures.append("the exact 30 independent oracle rows differ")
        oracle_rows = []
    if not isinstance(vector_rows, list) or len(vector_rows) != 30:
        failures.append("the exact 30 golden-vector rows differ")
        vector_rows = []
    if {
        str(row.get("math_spec_ref"))
        for row in oracle_rows
        if isinstance(row, dict)
    } != EXPECTED_MATH_IDS:
        failures.append("oracle math identities differ")
    if {
        str(row.get("math_spec_ref"))
        for row in vector_rows
        if isinstance(row, dict)
    } != EXPECTED_MATH_IDS:
        failures.append("golden-vector math identities differ")
    for row in oracle_rows:
        if (
            row.get("production_implementation_import_allowed")
            or row.get("primary_validator_expected_value_import_allowed")
            or row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_EXECUTABLE_ORACLE_SPECIFICATION"
            or not row.get("independence_proof")
            or not row.get("independent_algorithm_steps")
            or not row.get("mutation_targets_required")
        ):
            failures.append(
                f"{row.get('oracle_id')}: oracle independence is incomplete"
            )
    for row in vector_rows:
        if (
            row.get("production_implementation_import_allowed")
            or row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_GOLDEN_VECTOR_OR_STRUCTURAL_INVARIANT"
            or not row.get("comparison_policy")
            or "inputs" not in row
            or "expected" not in row
        ):
            failures.append(
                f"{row.get('vector_id')}: golden-vector independence is incomplete"
            )

    implementation_tree = trees["implementation_registry.py"]
    function_names = _implementation_function_names(implementation_tree)
    for math_id in EXPECTED_MATH_IDS:
        prefix = _expected_function_name(math_id)
        if not any(name.startswith(prefix) for name in function_names):
            failures.append(f"{math_id}: registered callable is absent")
    imports = {
        node.module or ""
        for node in ast.walk(implementation_tree)
        if isinstance(node, ast.ImportFrom)
    }
    if any(module.endswith("oracle_contracts") for module in imports):
        failures.append("production imports oracle expected-value material")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} closure_rows={len(EXPECTED_CLOSURES)} "
        f"math_oracle_vector_rows={len(EXPECTED_MATH_IDS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
