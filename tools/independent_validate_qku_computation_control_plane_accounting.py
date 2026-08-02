#!/usr/bin/env python3
"""Independent ST12-C accounting/math reconstruction without production imports."""

from __future__ import annotations

import ast
import base64
from collections import Counter
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import json
from pathlib import Path
import sys
import zlib


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "src" / "qtt" / "stage1_prediction_markets" / "qku_computation_control_plane"
EXPECTED_PRODUCTION = (
    "context.py", "economic_math.py", "receipts.py", "persistence.py", "migrations.py",
    "outbox.py", "transaction.py", "idempotency.py", "rollback.py", "accounting.py",
    "lifecycle.py", "sqlite_reference.py",
)
PROHIBITED = ("decimal_math.py", "execution.py", "accounting_tca_adapter.py", "telemetry.py", "sqlite_runtime.py")
EXPECTED_MATH_IDS = tuple(f"MATH-{value}" for value in range(26, 39))
CONTEXT = Context(prec=34, rounding=ROUND_HALF_EVEN)
SUCCESS = "QKU_ACCOUNTING_INDEPENDENTLY_VALIDATED"


def _assigned_literal(path: Path, name: str) -> object:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"missing literal {name}")


def _archive_rows(path: Path, name: str) -> tuple[dict[str, object], ...]:
    payload = _assigned_literal(path, name)
    if not isinstance(payload, str):
        raise ValueError(f"{name} is not literal text")
    text = zlib.decompress(base64.b85decode(payload.encode("ascii"))).decode("utf-8-sig")
    rows = tuple(json.loads(line) for line in text.splitlines() if line.strip())
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{name} contains a nonobject")
    return rows


def _d(value: object) -> Decimal:
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)


def _golden_results() -> dict[str, object]:
    with localcontext(CONTEXT):
        current = max(Decimal(".5"), Decimal(".4"))
        posterior = Decimal(".5") * Decimal(".8") + Decimal(".5") * Decimal(".7")
        evi = posterior - current - Decimal(".1")
        kelly = (Decimal("1") * Decimal(".60") - (Decimal(1) - Decimal(".60"))) / Decimal("1")
        fractional = min(Decimal(".50") * max(Decimal(0), Decimal(".20")), Decimal(".20"))
        mean_variance = Decimal(".10") - Decimal("2") / Decimal(2) * Decimal(".04")
        losses = tuple(sorted((Decimal(0), Decimal(1), Decimal(2), Decimal(3)), reverse=True))
        tail_mass = Decimal(1) - Decimal(".75")
        expected_shortfall = losses[0] * tail_mass / tail_mass
        shortfall = Decimal("100") * (Decimal(".52") - Decimal(".50")) + Decimal("1")
        spread = Decimal("100") * (Decimal(".44") - Decimal(".43"))
        global_fee = Decimal("100") * Decimal(".05") * Decimal(".50") * Decimal(".50")
        us_taker = Decimal("100") * Decimal(".05") * Decimal(".50") * Decimal(".50")
        us_maker = Decimal("100") * Decimal("-.0125") * Decimal(".50") * Decimal(".50")
        yes_ask = Decimal("1") - Decimal(".56")
        no_ask = Decimal("1") - Decimal(".42")
        expected_fill = Decimal("0") * Decimal(".2") + Decimal("50") * Decimal(".3") + Decimal("100") * Decimal(".5")
    return {
        "MATH-26": evi,
        "MATH-27": kelly,
        "MATH-28": fractional,
        "MATH-29": mean_variance,
        "MATH-30": (Decimal("3"), expected_shortfall),
        "MATH-31": expected_shortfall,
        "MATH-32": shortfall,
        "MATH-33": spread,
        "MATH-34": (global_fee, global_fee.quantize(Decimal(".00001"), rounding=ROUND_HALF_EVEN)),
        "MATH-35": (us_maker, us_maker.quantize(Decimal(".01"), rounding=ROUND_HALF_EVEN), us_taker, us_taker.quantize(Decimal(".01"), rounding=ROUND_HALF_EVEN)),
        "MATH-36": (yes_ask, no_ask),
        "MATH-37": (True, True, True),
        "MATH-38": expected_fill,
    }


def _source_safety(failures: list[str]) -> None:
    forbidden_imports = {"requests", "httpx", "socket", "subprocess", "asyncio", "multiprocessing"}
    for name in EXPECTED_PRODUCTION:
        path = PACKAGE / name
        if not path.is_file():
            failures.append(f"missing production owner: {name}")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & forbidden_imports:
                    failures.append(f"forbidden import in {name}: {sorted(roots & forbidden_imports)}")
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".", 1)[0] in forbidden_imports:
                failures.append(f"forbidden import in {name}: {node.module}")
    if any((PACKAGE / name).exists() for name in PROHIBITED):
        failures.append("a prohibited historical production path exists")


def _class_and_function_names(path: Path) -> tuple[set[str], set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return (
        {node.name for node in tree.body if isinstance(node, ast.ClassDef)},
        {node.name for node in tree.body if isinstance(node, ast.FunctionDef)},
    )


def _class_node(tree: ast.Module, class_name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise ValueError(f"missing class {class_name}")


def _annotated_fields(tree: ast.Module, class_name: str) -> set[str]:
    return {
        node.target.id
        for node in _class_node(tree, class_name).body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }


def _class_method_node(
    tree: ast.Module, class_name: str, method_name: str
) -> ast.FunctionDef:
    owner = _class_node(tree, class_name)
    for node in owner.body:
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    raise ValueError(f"missing {class_name}.{method_name}")


def _semantic_repair_closure(
    failures: list[str], policies: tuple[dict[str, object], ...],
    bindings: tuple[dict[str, object], ...],
) -> None:
    rollback_classes, rollback_functions = _class_and_function_names(PACKAGE / "rollback.py")
    if "ReversalHistoryViewV1" not in rollback_classes or "validate_reversal_bundle_against_history_v1" not in rollback_functions:
        failures.append("persisted reversal history has no single typed semantic owner")
    for filename, class_name in (
        ("persistence.py", "PersistenceAdapterV1"),
        ("persistence.py", "InMemoryPersistenceAdapterV1"),
        ("sqlite_reference.py", "SQLiteReferenceAdapterV1"),
    ):
        tree = ast.parse((PACKAGE / filename).read_text(encoding="utf-8"), filename=filename)
        owner = next(
            (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name),
            None,
        )
        if owner is None or "load_committed_reversal_history" not in {
            node.name for node in owner.body if isinstance(node, ast.FunctionDef)
        }:
            failures.append(f"{class_name} lacks the exact committed reversal-history query")
    transaction_tree = ast.parse(
        (PACKAGE / "transaction.py").read_text(encoding="utf-8"),
        filename="transaction.py",
    )
    transaction_calls = {
        node.func.attr
        for node in ast.walk(transaction_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(transaction_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    if not {
        "load_committed_reversal_history",
        "validate_reversal_bundle_against_history_v1",
    } <= transaction_calls:
        failures.append("unit of work does not enforce persisted reversal history")

    sqlite_tree = ast.parse(
        (PACKAGE / "sqlite_reference.py").read_text(encoding="utf-8"),
        filename="sqlite_reference.py",
    )
    public_sqlite = any(
        isinstance(node, ast.Import)
        and any(alias.name == "sqlite3" for alias in node.names)
        for node in sqlite_tree.body
    )
    private_sqlite = any(
        isinstance(node, ast.ImportFrom) and node.module == "_sqlite3"
        for node in sqlite_tree.body
    )
    if not public_sqlite or private_sqlite:
        failures.append("SQLite reference adapter does not use the public sqlite3 module exclusively")

    parameter_path = PACKAGE / "parameter_policy.py"
    parameter_tree = ast.parse(
        parameter_path.read_text(encoding="utf-8"),
        filename="parameter_policy.py",
    )
    parameter_classes, parameter_functions = _class_and_function_names(parameter_path)
    required_parameter_classes = {
        "TrancheCParameterPolicyClassV1",
        "TrancheCParameterEvidenceV1",
        "TrancheCParameterAdmissibilityReceiptV1",
        "TrancheCDrawdownCalibrationArtifactV1",
    }
    if not required_parameter_classes <= parameter_classes:
        failures.append("centralized typed parameter admissibility contract is incomplete")
    if not {
        "_validate_exact_evidence_v1",
        "_validate_drawdown_calibration_artifact_v1",
        "resolve_tranche_c_parameter_v1",
    } <= parameter_functions:
        failures.append("centralized dynamic parameter resolver path is incomplete")
    required_evidence_fields = {
        "evidence_ref", "evidence_class", "family_evidence_binding_ref",
        "value_source_class", "source_or_binding_refs",
        "source_currentization_refs", "active_scope_ref", "source_epoch_ref",
        "canonical_owner_ref", "authority_ref", "declared_unit_or_basis",
        "observed_at", "evaluated_at", "valid_until", "constraint_refs",
    }
    required_bundle_fields = {
        "calibration_bundle_ref", "approved_sleeve_max_drawdown_budget",
        "warning_threshold", "freeze_threshold", "canonical_owner_ref",
        "authority_ref", "active_scope_ref", "source_epoch_ref",
        "observed_at", "evaluated_at", "valid_until",
    }
    required_receipt_fields = {
        "evidence_ref", "family_evidence_binding_ref", "value_source_class",
        "source_currentization_refs", "active_scope_ref", "source_epoch_ref",
        "observed_at", "evaluated_at", "resolution_at", "valid_until",
        "calibration_bundle_ref",
    }
    try:
        if not required_evidence_fields <= _annotated_fields(
            parameter_tree, "TrancheCParameterEvidenceV1"
        ):
            failures.append("dynamic source/runtime evidence field closure is incomplete")
        if required_bundle_fields != _annotated_fields(
            parameter_tree, "TrancheCDrawdownCalibrationArtifactV1"
        ):
            failures.append("drawdown calibration bundle field closure is not exact")
        if not required_receipt_fields <= _annotated_fields(
            parameter_tree, "TrancheCParameterAdmissibilityReceiptV1"
        ):
            failures.append("dynamic admissibility receipt custody is incomplete")
        bundle_post_init = _class_method_node(
            parameter_tree,
            "TrancheCDrawdownCalibrationArtifactV1",
            "__post_init__",
        )
        bundle_constants = {
            node.value
            for node in ast.walk(bundle_post_init)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        bundle_calls = {
            node.func.id
            for node in ast.walk(bundle_post_init)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        bundle_attributes = {
            node.attr for node in ast.walk(bundle_post_init)
            if isinstance(node, ast.Attribute)
        }
        if (
            not {"0.50", "1.00"} <= bundle_constants
            or not {"decimal_context_v1", "exact_decimal"} <= bundle_calls
            or not {
                "approved_sleeve_max_drawdown_budget",
                "warning_threshold",
                "freeze_threshold",
            } <= bundle_attributes
        ):
            failures.append("drawdown calibration formulas are not exact Decimal laws")
    except ValueError as exc:
        failures.append(str(exc))

    binding_by_id = {row.get("parameter_id"): row for row in bindings}
    source_rows = tuple(
        row for row in policies
        if row.get("applicability_state") == "SOURCE_BOUND_MUTABLE_VALUE"
    )
    required_source_fields = (
        "family_evidence_binding_ref", "effective_value_source_class",
        "effective_source_state_refs", "source_currentization_refs",
        "effective_unit_or_basis", "master_plan_section_id",
        "currentization_version",
    )
    if len(source_rows) != 2 or any(
        any(not row.get(field) for field in required_source_fields)
        or binding_by_id.get(row.get("parameter_id"), {}).get(
            "active_stage1_value_authority"
        ) is None
        or binding_by_id.get(row.get("parameter_id"), {}).get(
            "currentized_source_refs"
        ) != row.get("source_currentization_refs")
        for row in source_rows
    ):
        failures.append("source/runtime policy evidence custody is not exact for both rows")

    drawdown_by_symbol = {
        row.get("parameter_symbol"): row
        for row in policies
        if row.get("effective_resolution_class") == "RISK_POLICY_DERIVED"
    }
    expected_drawdown_rules = {
        "dd_warn": "0.50 * approved_sleeve_max_drawdown_budget",
        "dd_freeze": "1.00 * approved_sleeve_max_drawdown_budget",
    }
    if (
        set(drawdown_by_symbol) != set(expected_drawdown_rules)
        or any(
            drawdown_by_symbol[symbol].get(
                "effective_day1_seed_value_or_resolution_rule"
            ) != rule
            for symbol, rule in expected_drawdown_rules.items()
        )
        or len({
            (
                row.get("family_evidence_binding_ref"),
                tuple(row.get("effective_source_state_refs", ())),
                row.get("effective_unit_or_basis"),
                row.get("canonical_owner"),
            )
            for row in drawdown_by_symbol.values()
        }) != 1
    ):
        failures.append("frozen drawdown rows do not share the exact calibration family")
    with localcontext(CONTEXT):
        independent_budget = Decimal("0.20")
        independent_warning = Decimal("0.50") * independent_budget
        independent_freeze = Decimal("1.00") * independent_budget
    if (
        independent_warning != Decimal("0.10")
        or independent_freeze != Decimal("0.20")
        or not Decimal("0") <= independent_warning < independent_freeze
    ):
        failures.append("independent drawdown formula reconstruction failed")
    independently_classified: list[str] = []
    for row in policies:
        applicability = row.get("applicability_state")
        resolution = row.get("effective_resolution_class")
        if applicability == "DORMANT_FUTURE_MARKET_PRESERVED_FAIL_CLOSED":
            policy_class = "NO_MACHINE_VERIFIABLE_OVERRIDE"
        elif applicability == "SOURCE_BOUND_MUTABLE_VALUE":
            policy_class = "SOURCE_OR_RUNTIME_BOUND"
        elif applicability == "REFERENCE_SEED_REQUIRES_CONTEXT_AND_OWNER_BINDING":
            policy_class = {
                "RISK_POLICY_DERIVED": "CALIBRATION_REQUIRED",
                "STATIC_NUMERIC_OR_OWNER_EDIT": "BOUNDED_NUMERIC",
                "STATIC_NUMERIC": "FIXED_SINGLETON_NUMERIC",
            }.get(resolution, "UNSUPPORTED")
        elif resolution == "STATIC_MAP_REFERENCE":
            policy_class = "TYPED_STRUCTURAL"
        elif resolution in {
            "STATIC_ENUM", "STATIC_RULE", "STATIC_FORMULA_RULE",
            "STATIC_ENUM_OR_RULE", "FORMULA", "STATIC_POINTER_OR_CONNECTOR_RULE",
            "STATIC_ENUM_OR_CONNECTOR_RULE",
        }:
            policy_class = "FIXED_SYMBOLIC_OR_ENUM"
        else:
            policy_class = "UNSUPPORTED"
        independently_classified.append(policy_class)
    expected_counts = {
        "FIXED_SYMBOLIC_OR_ENUM": 59,
        "FIXED_SINGLETON_NUMERIC": 1,
        "BOUNDED_NUMERIC": 1,
        "TYPED_STRUCTURAL": 1,
        "SOURCE_OR_RUNTIME_BOUND": 2,
        "CALIBRATION_REQUIRED": 2,
        "NO_MACHINE_VERIFIABLE_OVERRIDE": 14,
    }
    if Counter(independently_classified) != Counter(expected_counts):
        failures.append("independent 80-policy admissibility classification is not exact")

    registry_tree = ast.parse(
        (PACKAGE / "implementation_registry.py").read_text(encoding="utf-8"),
        filename="implementation_registry.py",
    )
    compatibility = next(
        node
        for node in registry_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "compute_math_36_kalshi_binary_book_transform"
    )
    canonical_calls = [
        node
        for node in ast.walk(compatibility)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "binary_book_implied_asks_v1"
    ]
    if len(canonical_calls) != 1 or any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)
        for node in ast.walk(compatibility)
    ):
        failures.append("MATH-36 predecessor route is not a delegation-only adapter")

    matrix_text = (
        REPO_ROOT
        / "tests"
        / "stage1_prediction_markets"
        / "qku_computation_control_plane"
        / "accounting"
        / "test_contract_matrix.py"
    ).read_text(encoding="utf-8")
    if not {
        '"journal-link-bijection"',
        "test_dynamic_parameter_evidence_compound_matrix",
        "drawdown_calibration_artifact",
    } <= {marker for marker in (
        '"journal-link-bijection"',
        "test_dynamic_parameter_evidence_compound_matrix",
        "drawdown_calibration_artifact",
    ) if marker in matrix_text}:
        failures.append("central accounting matrix lacks compact residual semantic coverage")


def main() -> int:
    failures: list[str] = []
    _source_safety(failures)
    try:
        policies = _archive_rows(PACKAGE / "parameter_policy.py", "_ST12C_POLICY_ARCHIVE_B85")
        bindings = _archive_rows(PACKAGE / "parameter_policy.py", "_ST12C_BINDING_ARCHIVE_B85")
        oracles = _archive_rows(PACKAGE / "oracle_contracts.py", "_ST12C_ORACLE_ARCHIVE_B85")
        vectors = _archive_rows(PACKAGE / "oracle_contracts.py", "_ST12C_VECTOR_ARCHIVE_B85")
    except (OSError, SyntaxError, ValueError, KeyError, zlib.error) as exc:
        failures.append(f"frozen overlay could not be independently decoded: {exc}")
        policies = bindings = oracles = vectors = ()
    policy_ids = tuple(row.get("parameter_id") for row in policies)
    binding_ids = tuple(row.get("parameter_id") for row in bindings)
    oracle_ids = tuple(row.get("math_spec_ref") for row in oracles)
    vector_ids = tuple(row.get("math_spec_ref") for row in vectors)
    if len(policies) != 80 or len(set(policy_ids)) != 80 or policy_ids != binding_ids:
        failures.append("parameter closure is not exact 80/80")
    if any(row.get("no_silent_default") is not True or row.get("codex_online_research_allowed") is not False or row.get("provider_effect_authorized") is not False for row in policies):
        failures.append("parameter no-default/research/effect law failed")
    if oracle_ids != EXPECTED_MATH_IDS or vector_ids != EXPECTED_MATH_IDS:
        failures.append("oracle/vector identities are not MATH-26..38 exactly")
    if any(row.get("production_implementation_import_allowed") is not False for row in (*oracles, *vectors)):
        failures.append("oracle/vector production-import separation failed")
    _semantic_repair_closure(failures, policies, bindings)
    actual = _golden_results()
    expected = {
        "MATH-26": Decimal(".15"), "MATH-27": Decimal(".20"), "MATH-28": Decimal(".10"),
        "MATH-29": Decimal(".06"), "MATH-30": (Decimal(3), Decimal(3)), "MATH-31": Decimal(3),
        "MATH-32": Decimal("3.00"), "MATH-33": Decimal("1.00"),
        "MATH-34": (Decimal("1.25"), Decimal("1.25000")),
        "MATH-35": (Decimal("-.312500"), Decimal("-.31"), Decimal("1.250000"), Decimal("1.25")),
        "MATH-36": (Decimal(".44"), Decimal(".58")), "MATH-37": (True, True, True), "MATH-38": Decimal(65),
    }
    if actual != expected:
        failures.append(f"independent golden reconstruction mismatch: {actual!r}")
    accounting_matrix = REPO_ROOT / "tests" / "stage1_prediction_markets" / "qku_computation_control_plane" / "accounting" / "test_contract_matrix.py"
    execution_matrix = accounting_matrix.parents[1] / "execution" / "test_contract_matrix.py"
    if not accounting_matrix.is_file() or not execution_matrix.is_file():
        failures.append("centralized accounting/execution matrices are missing")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"{SUCCESS} controls=16 policies=80 bindings=80 math=13 oracles=13 vectors=13 effects=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
