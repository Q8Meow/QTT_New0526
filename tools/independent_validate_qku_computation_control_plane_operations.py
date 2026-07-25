#!/usr/bin/env python3
"""Independent operations-boundary validation without production imports."""

from __future__ import annotations

import ast
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
FORBIDDEN_IMPORT_ROOTS = {
    "asyncio",
    "multiprocessing",
    "requests",
    "socket",
    "sqlite3",
    "subprocess",
    "threading",
}
FORBIDDEN_CALL_NAMES = {
    "connect",
    "create_connection",
    "listen",
    "Popen",
    "run",
    "serve_forever",
    "start",
}
SUCCESS_MARKER = "QKU_OPERATIONS_INDEPENDENTLY_VALIDATED"


def main() -> int:
    failures: list[str] = []
    parsed: dict[str, ast.Module] = {}
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parsed[path.name] = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{path.name}: runtime import {sorted(roots)}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{path.name}: runtime import {root}")
            elif isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                if name in FORBIDDEN_CALL_NAMES:
                    failures.append(f"{path.name}: runtime call {name}")
    models = parsed.get("models.py")
    required_contracts = {
        "ComputationExecutionReceiptV1",
        "ConfigurationEnvelopeV1",
        "ContractFieldV1",
        "HealthEnvelopeV1",
        "OperationFailureEnvelopeV1",
        "OperationRequestEnvelopeV1",
        "OperationResponseEnvelopeV1",
        "SupervisionEnvelopeV1",
        "FallbackEnvelopeV1",
        "FormulaRuntimeSnapshotV1",
        "TransactionEnvelopeV1",
    }
    found_contracts = {
        node.name
        for node in (models.body if models else ())
        if isinstance(node, ast.ClassDef)
    }
    if not required_contracts <= found_contracts:
        failures.append("operations data-contract envelope is incomplete")
    validation = parsed.get("validation.py")
    operation_rows: list[tuple[str, str, str, str, str]] = []
    operation_constructor: ast.Call | None = None
    for node in validation.body if validation else ():
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "TRANCHE_A_OPERATION_CONTRACTS"
                for target in node.targets
            )
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "tuple"
            and node.value.args
            and isinstance(node.value.args[0], ast.GeneratorExp)
            and isinstance(node.value.args[0].generators[0].iter, ast.Tuple)
        ):
            generator = node.value.args[0]
            if isinstance(generator.elt, ast.Call):
                operation_constructor = generator.elt
            for row in generator.generators[0].iter.elts:
                if (
                    not isinstance(row, ast.Tuple)
                    or len(row.elts) != 5
                    or any(
                        not isinstance(value, ast.Constant)
                        or not isinstance(value.value, str)
                        or not value.value
                        for value in row.elts[:4]
                    )
                    or not isinstance(row.elts[4], ast.Attribute)
                    or not isinstance(row.elts[4].value, ast.Name)
                    or row.elts[4].value.id != "ReasonCode"
                ):
                    failures.append("operation-contract row is not a typed exact tuple")
                    continue
                operation_rows.append(
                    (
                        *(value.value for value in row.elts[:4]),
                        row.elts[4].attr,
                    )
                )
    operation_count = len(operation_rows)
    if operation_count != 15:
        failures.append(
            f"operation-contract denominator={operation_count}, expected=15"
        )
    elif any(
        len({row[index] for row in operation_rows}) != 15
        for index in range(4)
    ):
        failures.append("operation contracts have an identity or schema collision")
    if operation_constructor is None:
        failures.append("operation-contract constructor is missing")
    else:
        keyword_values = {
            keyword.arg: keyword.value
            for keyword in operation_constructor.keywords
            if keyword.arg is not None
        }
        keyword_names = set(keyword_values)
        if (
            not isinstance(operation_constructor.func, ast.Name)
            or operation_constructor.func.id != "OperationContractV1"
            or len(operation_constructor.args) != 4
            or keyword_names
            != {
                "request_fields",
                "response_fields",
                "failure_reason_codes",
            }
        ):
            failures.append(
                "operation contracts do not use complete data-only typed schemas"
            )
        else:
            def field_names(value: ast.expr) -> tuple[str, ...]:
                if not isinstance(value, ast.Tuple):
                    return ()
                names: list[str] = []
                for item in value.elts:
                    if (
                        not isinstance(item, ast.Call)
                        or not isinstance(item.func, ast.Name)
                        or item.func.id != "ContractFieldV1"
                        or len(item.args) != 2
                        or not isinstance(item.args[0], ast.Constant)
                        or not isinstance(item.args[0].value, str)
                    ):
                        return ()
                    names.append(item.args[0].value)
                return tuple(names)

            if field_names(keyword_values["request_fields"]) != (
                "request_id",
                "contract_version",
                "payload_json",
            ):
                failures.append("operation request schema fields are not exact")
            if field_names(keyword_values["response_fields"]) != (
                "request_id",
                "result_json",
            ):
                failures.append("operation response schema fields are not exact")
            failure_reasons = keyword_values["failure_reason_codes"]
            if (
                not isinstance(failure_reasons, ast.Tuple)
                or len(failure_reasons.elts) != 1
                or not isinstance(failure_reasons.elts[0], ast.Name)
                or failure_reasons.elts[0].id != "failure_reason"
            ):
                failures.append("operation failure schema is not reason-allowlisted")
    forbidden_files = {
        "runtime.py",
        "service.py",
        "supervision.py",
        "backup.py",
        "database.py",
    }
    if forbidden_files & {path.name for path in PACKAGE.glob("*.py")}:
        failures.append("a later-tranche runtime module exists")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"{SUCCESS_MARKER} closure_controls=4 operation_contracts=15")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
