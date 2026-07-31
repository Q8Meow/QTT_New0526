#!/usr/bin/env python3
"""Independently validate v3.4 oracle separation and high-risk routes."""

from __future__ import annotations

import ast
from collections import Counter
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
ORACLES = PACKAGE / "oracle_contracts.py"
SUCCESS_MARKER = "QKU_MODEL_RISK_INDEPENDENTLY_VALIDATED"
EXPECTED_MATH_IDS = (
    *(f"MATH-{value:02d}" for value in range(1, 26)),
    "MATH-36",
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
EXPECTED_HIGH_RISK_IDS = (
    "MATH-15",
    "MATH-16",
    "MATH-18",
    "MATH-19",
    "MATH-20",
    "MATH-21",
    "MATH-25",
    "MATH-48",
    "MATH-49",
)
REQUIRED_INDEPENDENCE_CONTROLS = {
    "NO_QTT_PRODUCTION_IMPORT",
    "NO_PRODUCTION_RESULT_READ",
    "NO_EVAL_EXEC",
    "STANDARD_LIBRARY_ONLY",
    "EXECUTES_FROM_RAW_DECLARED_INPUTS",
}


def _literal(tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise ValueError(f"missing literal {name}")


def main() -> int:
    failures: list[str] = []
    try:
        oracle_tree = ast.parse(
            ORACLES.read_text(encoding="utf-8"),
            filename=str(ORACLES),
        )
        oracle_rows = json.loads(
            _literal(oracle_tree, "_ST12B_ORACLE_CONTRACTS_JSON")
        )
        vectors = json.loads(_literal(oracle_tree, "_ST12B_VECTOR_PACK_JSON"))
        properties = json.loads(
            _literal(oracle_tree, "_ST12B_PROPERTY_PACK_JSON")
        )
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        print(f"model-risk literals could not be reconstructed: {exc}", file=sys.stderr)
        return 1
    if any(
        not isinstance(rows, list)
        or any(not isinstance(row, dict) for row in rows)
        for rows in (oracle_rows, vectors, properties)
    ):
        failures.append("oracle/vector/property literals must be arrays of objects")
        oracle_rows = []
        vectors = []
        properties = []
    if (
        tuple(str(row.get("math_spec_id")) for row in oracle_rows)
        != EXPECTED_MATH_IDS
        or len(vectors) != 90
        or Counter(str(row.get("math_spec_id")) for row in vectors)
        != {math_id: 3 for math_id in EXPECTED_MATH_IDS}
        or tuple(str(row.get("math_spec_id")) for row in properties)
        != EXPECTED_MATH_IDS
    ):
        failures.append("oracle/vector/property closure is not exact 30/90/30")
    high_risk_ids = tuple(
        str(row.get("math_spec_id"))
        for row in oracle_rows
        if row.get("secondary_route_state") == "EXECUTABLE"
    )
    if high_risk_ids != EXPECTED_HIGH_RISK_IDS:
        failures.append("high-risk secondary-route identities are not exact")
    by_id = {
        str(row.get("math_spec_id")): row
        for row in oracle_rows
        if isinstance(row, dict)
    }
    for math_id in EXPECTED_MATH_IDS:
        row = by_id.get(math_id, {})
        if set(row.get("independence_controls", ())) != (
            REQUIRED_INDEPENDENCE_CONTROLS
        ):
            failures.append(f"{math_id}: independent-oracle controls differ")
        if math_id in EXPECTED_HIGH_RISK_IDS:
            expected_ref = (
                "independent_oracle_reference/secondary_routes.py::"
                f"check_{math_id.lower().replace('-', '_')}"
            )
            if row.get("secondary_route_ref") != expected_ref:
                failures.append(f"{math_id}: secondary route reference differs")
        elif row.get("secondary_route_state") != (
            "NOT_APPLICABLE_WITH_TYPED_REASON"
        ):
            failures.append(f"{math_id}: unexpected secondary route")
    for path in PACKAGE.glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{path.name}: {exc}")
            continue
        if path.name == "oracle_contracts.py":
            continue
        for node in ast.walk(tree):
            module = (
                node.module
                if isinstance(node, ast.ImportFrom)
                else ""
            )
            names = (
                tuple(alias.name for alias in node.names)
                if isinstance(node, ast.Import)
                else ()
            )
            if (
                "independent_oracle_reference" in module
                or any(
                    "independent_oracle_reference" in name for name in names
                )
            ):
                failures.append(
                    f"{path.name}: production imports package oracle code"
                )
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} oracles=30 vectors=90 properties=30 "
        f"secondary_routes={len(EXPECTED_HIGH_RISK_IDS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
