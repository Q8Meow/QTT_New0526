"""Callable import resolver for PR162R smoke readiness."""

from __future__ import annotations

import importlib
from typing import Any, Callable


def import_callable(callable_ref: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    module_name, attr_name = callable_ref.split(":", 1)
    module = importlib.import_module(module_name)
    obj = getattr(module, attr_name)
    if not callable(obj):
        raise TypeError(f"callable_ref is not callable: {callable_ref}")
    return obj


def build_callable_import_rows(
    formulations: list[dict[str, Any]],
    comparators: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, formulation in enumerate(formulations, start=1):
        callable_ref = str(formulation.get("callable_ref") or "")
        status, error = _try_import(callable_ref)
        rows.append(
            {
                "callable_import_audit_id": f"PR162R_CALLABLE_IMPORT::{index:04d}",
                "callable_family": _callable_family(formulation.get("formulation_type")),
                "formulation_ref": formulation.get("formulation_id"),
                "callable_ref": callable_ref,
                "import_status": status,
                "import_error": error,
                "exact_fill_action_ref": None if status == "CALLABLE_IMPORT_PASSED" else f"PR162R_CALLABLE_IMPORT_FILL::{index:04d}",
                "live_order_authority": False,
                "validation_status": "PASS" if status == "CALLABLE_IMPORT_PASSED" else "FILL_REQUIRED_WITH_EXACT_REASON",
            }
        )
    offset = len(rows)
    for index, comparator in enumerate(comparators, start=1):
        callable_ref = str(comparator.get("callable_ref") or "")
        status, error = _try_import(callable_ref)
        rows.append(
            {
                "callable_import_audit_id": f"PR162R_CALLABLE_IMPORT::{offset + index:04d}",
                "callable_family": "CLASSICAL_COMPARATOR",
                "formulation_ref": comparator.get("classical_comparator_id"),
                "callable_ref": callable_ref,
                "import_status": status,
                "import_error": error,
                "exact_fill_action_ref": None if status == "CALLABLE_IMPORT_PASSED" else f"PR162R_COMPARATOR_IMPORT_FILL::{index:04d}",
                "live_order_authority": False,
                "validation_status": "PASS" if status == "CALLABLE_IMPORT_PASSED" else "FILL_REQUIRED_WITH_EXACT_REASON",
            }
        )
    return rows


def _try_import(callable_ref: str) -> tuple[str, str | None]:
    if not callable_ref:
        return "CALLABLE_IMPORT_SKIPPED_WITH_EXACT_REASON", "missing callable_ref"
    try:
        import_callable(callable_ref)
    except Exception as exc:  # pragma: no cover - validator reports the exact failure
        return "CALLABLE_IMPORT_FAILED", str(exc)
    return "CALLABLE_IMPORT_PASSED", None


def _callable_family(formulation_type: Any) -> str:
    if formulation_type in {"FORMULA", "FEATURE"}:
        return "FORMULA"
    if formulation_type == "ALGORITHM":
        return "ALGORITHM"
    if formulation_type == "QUANTUM_FORMULATION":
        return "QUANTUM_SHAPE_BUILDER"
    if formulation_type == "PARAMETER_PACK":
        return "PARAMETER_PACK"
    return "UNKNOWN_CALLABLE_FAMILY"
