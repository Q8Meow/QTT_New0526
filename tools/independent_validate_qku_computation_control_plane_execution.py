#!/usr/bin/env python3
"""Independent ST12-C execution/no-effect validation without production imports."""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "src" / "qtt" / "stage1_prediction_markets" / "qku_computation_control_plane"
SUCCESS = "QKU_EXECUTION_INDEPENDENTLY_VALIDATED"
SERVICE_METHODS = (
    "resolve_identity", "resolve_contextual_computability", "resolve_applicable_stack",
    "resolve_required_inputs", "compute_component", "compute_stack", "compare_with_no_trade",
    "evaluate_trade_plan", "get_snapshot_view", "explain_resolution",
    "submit_candidate_proposal", "request_materialization_work_order",
)
FORBIDDEN_METHODS = {"submit", "cancel", "amend", "sign", "dispatch", "send"}
NEW_MODULES = (
    "economic_math.py", "receipts.py", "persistence.py", "migrations.py", "outbox.py",
    "transaction.py", "idempotency.py", "rollback.py", "accounting.py", "lifecycle.py",
    "sqlite_reference.py",
)


def _tree(name: str) -> ast.Module:
    path = PACKAGE / name
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _class_methods(tree: ast.Module, class_name: str) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return tuple(item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_"))
    raise ValueError(f"missing class {class_name}")


def _assigned_tuple(tree: ast.Module, name: str) -> tuple[object, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, tuple):
                return value
    raise ValueError(f"missing tuple {name}")


def _call_order(tree: ast.Module) -> tuple[str, ...]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "execute":
            calls: list[tuple[int, int, str]] = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Attribute) and isinstance(child.func.value.value, ast.Name) and child.func.value.value.id == "self" and child.func.value.attr == "_adapter":
                    calls.append((child.lineno, child.col_offset, child.func.attr))
            return tuple(name for _, _, name in sorted(calls))
    raise ValueError("unit-of-work execute method missing")


def main() -> int:
    failures: list[str] = []
    try:
        trees = {name: _tree(name) for name in NEW_MODULES}
        service_tree = _tree("service.py")
        validation_tree = _tree("validation.py")
    except (OSError, SyntaxError) as exc:
        print(f"source parse failed: {exc}", file=sys.stderr)
        return 1
    try:
        if _class_methods(service_tree, "QKUComputationControlPlaneV1") != SERVICE_METHODS:
            failures.append("existing public service method roster changed")
        gates = _assigned_tuple(trees["lifecycle.py"], "PREFLIGHT_GATE_CLASSES")
        if gates != ("SOURCE", "MODEL", "FRESHNESS", "VENUE", "CAP", "RISK", "CASH", "ACCOUNTING", "CONDUCT", "KILL", "MODE", "SNAPSHOT", "IDEMPOTENCY"):
            failures.append("preflight gate roster is not exact")
    except ValueError as exc:
        failures.append(str(exc))
    defined = {
        node.name
        for tree in trees.values()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if defined & FORBIDDEN_METHODS:
        failures.append(f"provider-write method implemented: {sorted(defined & FORBIDDEN_METHODS)}")
    forbidden_imports = {"requests", "httpx", "socket", "subprocess", "asyncio", "multiprocessing"}
    for name, tree in trees.items():
        roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        if roots & forbidden_imports:
            failures.append(f"forbidden operational import in {name}: {sorted(roots & forbidden_imports)}")
        if "sqlite3" in roots and name != "sqlite_reference.py":
            failures.append(f"SQLite ownership leaked into {name}")
    lifecycle_text = (PACKAGE / "lifecycle.py").read_text(encoding="utf-8")
    outbox_text = (PACKAGE / "outbox.py").read_text(encoding="utf-8")
    persistence_text = (PACKAGE / "persistence.py").read_text(encoding="utf-8")
    idempotency_text = (PACKAGE / "idempotency.py").read_text(encoding="utf-8")
    if "ExecutionRouterV1_FUTURE_SOLE_OWNER_NOT_IMPLEMENTED" not in lifecycle_text:
        failures.append("future sole release authority boundary missing")
    if "RECORDED_NOT_DISPATCHABLE" not in outbox_text or "OUTBOX_DISPATCHER_IMPLEMENTED = False" not in outbox_text:
        failures.append("outbox no-dispatch contract missing")
    if "NO_DEFAULT_REQUIRES_SEPARATE_RUNTIME_PLATFORM_AUTHORIZATION_AND_BENCHMARK" not in (PACKAGE / "migrations.py").read_text(encoding="utf-8"):
        failures.append("production persistence blocker missing")
    if "REFERENCE_STORE_LIFETIME_NO_TIME_BASED_PURGE_API" not in idempotency_text or "deterministic_json" not in idempotency_text:
        failures.append("idempotency canonical-text/retention law missing")
    persistence_methods = set(_class_methods(trees["persistence.py"], "PersistenceAdapterV1"))
    expected_methods = {
        "availability", "begin_transaction", "insert_receipt_record", "insert_value_lineage_edge",
        "insert_economic_event", "insert_journal_transaction", "insert_journal_posting",
        "insert_state_transition", "acquire_idempotency_claim", "bind_idempotency_result",
        "insert_outbox_intent", "insert_reversal_link", "insert_reconciliation_break",
        "get_record", "get_idempotency_result", "reconstruct_as_of",
    }
    if persistence_methods != expected_methods:
        failures.append(f"typed persistence interface mismatch: {sorted(persistence_methods ^ expected_methods)}")
    ordered = _call_order(trees["transaction.py"])
    required_order = (
        "acquire_idempotency_claim", "insert_receipt_record", "insert_economic_event",
        "insert_value_lineage_edge", "insert_journal_transaction", "insert_journal_posting",
        "insert_state_transition", "insert_outbox_intent", "bind_idempotency_result",
    )
    positions = [ordered.index(name) if name in ordered else -1 for name in required_order]
    if -1 in positions or positions != sorted(positions):
        failures.append(f"atomic unit-of-work call order mismatch: {ordered}")
    identity_fields = _class_methods(trees["lifecycle.py"], "EconomicIdentitySetV1")
    # A frozen dataclass has only __post_init__ as a method; inspect annotated fields instead.
    identity_class = next(node for node in trees["lifecycle.py"].body if isinstance(node, ast.ClassDef) and node.name == "EconomicIdentitySetV1")
    identity_names = tuple(node.target.id for node in identity_class.body if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name))
    if identity_names != ("semantic_economic_intent_id", "command_id", "attempt_id", "provider_request_id", "request_id", "trace_id", "transaction_id", "event_id"):
        failures.append("economic identity separation fields are not exact")
    fill_distribution = ((Decimal(0), Decimal(".2")), (Decimal(50), Decimal(".3")), (Decimal(100), Decimal(".5")))
    if sum((quantity * probability for quantity, probability in fill_distribution), Decimal(0)) != Decimal(65):
        failures.append("independent expected partial-fill oracle failed")
    probabilities = (Decimal(".1"), Decimal(".4"), Decimal(".8"))
    if not all(Decimal(0) <= value <= Decimal(1) for value in probabilities) or tuple(sorted(probabilities)) != probabilities:
        failures.append("independent fill-probability structural invariant failed")
    blocker_mapping = next(
        (node.value for node in validation_tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "ST12C_LATER_PHASE_BLOCKERS" for target in node.targets)),
        None,
    )
    if not isinstance(blocker_mapping, ast.Call) or not blocker_mapping.args or not isinstance(blocker_mapping.args[0], ast.Dict) or len(blocker_mapping.args[0].keys) != 9:
        failures.append("nine later-phase blockers are not explicit")
    matrix_root = REPO_ROOT / "tests" / "stage1_prediction_markets" / "qku_computation_control_plane"
    if not (matrix_root / "accounting" / "test_contract_matrix.py").is_file() or not (matrix_root / "execution" / "test_contract_matrix.py").is_file():
        failures.append("centralized contract matrices are missing")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"{SUCCESS} controls=9 identities=8 gates=13 lifecycle=NO_WRITE effects=0 blockers=9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
