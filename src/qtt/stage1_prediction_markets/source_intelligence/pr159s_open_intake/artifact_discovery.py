"""Deterministic artifact discovery for PR159S preflight."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json, record_count, schema_version


def _safe_read_json(path: Path) -> Any:
    if not path.exists() or path.suffix != ".json":
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def artifact_receipt(root: Path, rel_path: Path, role: str, required: bool, fallback: bool = False) -> dict[str, Any]:
    full_path = root / rel_path
    payload = _safe_read_json(full_path)
    exists = full_path.exists()
    return {
        "path": rel_path.as_posix(),
        "exists": exists,
        "consumed": exists,
        "artifact_role": role,
        "required_or_optional": "required" if required else "optional",
        "fallback_used": fallback,
        "record_count_if_available": record_count(payload),
        "schema_version_if_available": schema_version(payload),
        "authority_class": c.AUTHORITY_CLASS,
        "no_runtime_execution_confirmation": True,
    }


def _glob_receipts(root: Path, pattern: str, role: str) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in sorted(root.glob(pattern)):
        if path.is_file():
            receipts.append(artifact_receipt(root, path.relative_to(root), role, False))
    return receipts


def input_consumption_receipts(root: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = artifact_receipt(root, path, "mandatory_pr136_crosswalk_requested", True)
            fallback_used = not requested["exists"] and (root / c.CROSSWALK_FALLBACK_PATH).exists()
            receipts.append(requested)
            receipts.append(
                artifact_receipt(
                    root,
                    c.CROSSWALK_FALLBACK_PATH,
                    "mandatory_pr136_crosswalk_allowed_fallback",
                    True,
                    fallback_used,
                )
            )
            continue
        receipts.append(artifact_receipt(root, path, "mandatory_orchestration_input", True))
    for path in c.MANDATORY_CONTEXT_INPUTS:
        receipts.append(artifact_receipt(root, path, "mandatory_pr159s_context_input", True))
    if (root / c.PR157_SHARD_DIR).exists():
        receipts.extend(
            artifact_receipt(root, shard.relative_to(root), "mandatory_pr157_atomicrows_completion_shard", True)
            for shard in sorted((root / c.PR157_SHARD_DIR).glob("*.json"))
        )
    receipts.extend(_glob_receipts(root, "docs/master_plan/generated/PR157*.*", "discovered_pr157_artifact"))
    receipts.extend(_glob_receipts(root, "docs/master_plan/generated/PR158*.*", "discovered_pr158_artifact"))
    receipts.extend(_glob_receipts(root, "docs/master_plan/generated/PR159*.*", "discovered_pr159_family_artifact"))
    receipts.extend(_glob_receipts(root, "docs/master_plan/generated/PR160*.*", "discovered_pr160_artifact"))
    receipts.extend(_glob_receipts(root, "docs/master_plan/generated/*PR82*.*", "discovered_pr82_pr86_quantum_artifact"))
    receipts.extend(_glob_receipts(root, "docs/master_plan/generated/*PR86*.*", "discovered_pr82_pr86_quantum_artifact"))
    return receipts


def selected_artifact_paths(receipts: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(item.get("path"))
            for item in receipts
            if item.get("consumed") and item.get("path")
        }
    )


def fallback_crosswalk_path_used(receipts: list[dict[str, Any]]) -> str | None:
    for item in receipts:
        if item.get("artifact_role") == "mandatory_pr136_crosswalk_allowed_fallback" and item.get("fallback_used"):
            return str(item.get("path"))
    return None

