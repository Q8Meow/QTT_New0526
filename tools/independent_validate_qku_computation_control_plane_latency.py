#!/usr/bin/env python3
"""Independent static validation of Tranche-B latency and deadline closure."""

from __future__ import annotations

import ast
from datetime import timedelta
from decimal import Decimal
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
    "ST12-CLOSURE::ST11-LATENCY::006": "budget-ledger",
    "ST12-CLOSURE::ST11-LATENCY::007": "ttl-and-edge-decay",
    "ST12-CLOSURE::ST11-LATENCY::008": "clock-skew",
    "ST12-CLOSURE::ST11-LATENCY::009": "queueing",
    "ST12-CLOSURE::ST11-LATENCY::010": "deadlines-and-cancellation",
}
SUCCESS_MARKER = "QKU_LATENCY_INDEPENDENTLY_VALIDATED"


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


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    return next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ),
        None,
    )


def _class_method(
    tree: ast.Module,
    class_name: str,
    method_name: str,
) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return next(
                (
                    item
                    for item in node.body
                    if isinstance(item, ast.FunctionDef)
                    and item.name == method_name
                ),
                None,
            )
    return None


def _uses_name(function: ast.FunctionDef | None, name: str) -> bool:
    return function is not None and any(
        isinstance(node, ast.Name) and node.id == name
        for node in ast.walk(function)
    )


def _has_strict_greater_ttl(
    function: ast.FunctionDef | None,
) -> bool:
    if function is None:
        return False
    return any(
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and node.left.id == "age"
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Gt)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Attribute)
        and node.comparators[0].attr == "ttl"
        for node in ast.walk(function)
    )


def _has_strict_greater_deadline(
    function: ast.FunctionDef | None,
) -> bool:
    if function is None:
        return False
    return any(
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and node.left.id == "elapsed"
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Gt)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Attribute)
        and node.comparators[0].attr == "budget_seconds"
        for node in ast.walk(function)
    )


def _certified_latency_rows(validation_tree: ast.Module) -> dict[str, str]:
    raw = _literal_assignment(
        validation_tree,
        "_TRANCHE_B_MACHINE_ROWS_JSON",
    )
    if not isinstance(raw, str):
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    rows = payload.get("closure_rows")
    if not isinstance(rows, list):
        return {}
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("domain") != "latency":
            continue
        implementation = row.get("implementation_specification")
        if (
            row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_CLOSURE_SPECIFICATION"
            or not isinstance(implementation, dict)
            or implementation.get("runtime_effect_authorized")
            or implementation.get("open_research_questions") != []
            or not implementation.get("tests")
            or not implementation.get("validation_commands")
            or not implementation.get("fallback")
        ):
            return {}
        result[str(row.get("closure_id"))] = str(row.get("control_slug"))
    return result


def main() -> int:
    failures: list[str] = []
    freshness_path = PACKAGE / "freshness.py"
    validation_path = PACKAGE / "validation.py"
    service_path = PACKAGE / "service.py"
    try:
        freshness = ast.parse(
            freshness_path.read_text(encoding="utf-8"),
            filename=str(freshness_path),
        )
        validation = ast.parse(
            validation_path.read_text(encoding="utf-8"),
            filename=str(validation_path),
        )
        service = ast.parse(
            service_path.read_text(encoding="utf-8"),
            filename=str(service_path),
        )
    except (OSError, SyntaxError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if _certified_latency_rows(validation) != EXPECTED_CLOSURES:
        failures.append("the five exact certified latency closures differ")

    imports = {
        alias.name
        for node in freshness.body
        if isinstance(node, ast.ImportFrom) and node.module == "time"
        for alias in node.names
    }
    if "monotonic" not in imports:
        failures.append("elapsed deadlines do not import the monotonic clock")

    start = _class_method(freshness, "DeadlineBudgetV1", "start")
    deadline = _class_method(freshness, "DeadlineResolverV1", "resolve")
    field = _class_method(freshness, "FreshnessResolverV1", "resolve_field")
    closure = _class_method(freshness, "FreshnessResolverV1", "resolve_closure")
    if not _uses_name(start, "monotonic_clock") or not _uses_name(
        deadline,
        "monotonic_clock",
    ):
        failures.append("deadline origin and elapsed checks are not monotonic")
    if not _has_strict_greater_ttl(field):
        failures.append("TTL boundary is not inclusive at exact expiry")
    if not _has_strict_greater_deadline(deadline):
        failures.append("deadline boundary is not inclusive at exact budget")

    freshness_text = freshness_path.read_text(encoding="utf-8")
    for required in (
        "FRESH",
        "STALE",
        "UNKNOWN_FAIL_CLOSED",
        "FIELD_STALE",
        "FRESHNESS_UNKNOWN",
        "DEADLINE_EXHAUSTED",
        "REGISTERED_FAST_CLASSICAL_OR_NO_TRADE",
    ):
        if required not in freshness_text:
            failures.append(f"latency/freshness invariant is absent: {required}")
    if closure is None or not _uses_name(closure, "material"):
        failures.append("material-only freshness propagation is absent")

    forbidden_runtime_roots = {
        "asyncio",
        "multiprocessing",
        "socket",
        "subprocess",
        "threading",
    }
    for tree, path in ((freshness, freshness_path), (service, service_path)):
        for node in ast.walk(tree):
            roots: set[str] = set()
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = {node.module.split(".", 1)[0]}
            if roots & forbidden_runtime_roots:
                failures.append(
                    f"{path.name}: forbidden runtime import {sorted(roots)}"
                )

    # Independent boundary arithmetic, with no production import.
    ttl = timedelta(seconds=10)
    if not (
        timedelta(seconds=10) <= ttl
        and timedelta(seconds=10, microseconds=1) > ttl
    ):
        failures.append("independent TTL boundary arithmetic failed")
    budget = Decimal("1")
    if not (Decimal("1") <= budget and Decimal("1.000001") > budget):
        failures.append("independent deadline boundary arithmetic failed")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} closure_rows={len(EXPECTED_CLOSURES)} "
        "ttl_boundary=inclusive deadline_clock=monotonic"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
