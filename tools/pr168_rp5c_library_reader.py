#!/usr/bin/env python3
"""Read-only query surface for PR168-RP5C QKU/formula library rows."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Iterable

from tools.pr168_rp5c_config import (
    AGENT_ACCESS_POLICY_VERSION,
    APPLICABILITY_MATRIX_VERSION,
    LIBRARY_VERSION,
    REPO_ROOT,
    ROW_SHARDS,
    STAGE1_PROFILE_ID,
    STAGE_PROFILE_VERSION,
)


class LibraryVersionMismatchError(ValueError):
    """Raised when a caller requests incompatible RP5C surface versions."""


def _root(repo_root: str | Path | None = None) -> Path:
    return Path(repo_root).resolve() if repo_root is not None else REPO_ROOT


def _shard_path(key: str, repo_root: str | Path | None = None) -> Path:
    return _root(repo_root) / "docs" / "master_plan" / "generated" / "rp5c" / ROW_SHARDS[key]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _stable_identity_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("identity_row_id") or ""),
        str(row.get("qku_id") or ""),
        str(row.get("formula_id") or ""),
    )


def _stable_ref_key(ref: str) -> tuple[str, str]:
    return (ref.casefold(), ref)


def _check_versions(expected_versions: dict[str, str] | None) -> None:
    if not expected_versions:
        return
    actual_versions = {
        "library_version": LIBRARY_VERSION,
        "applicability_matrix_version": APPLICABILITY_MATRIX_VERSION,
        "stage_profile_version": STAGE_PROFILE_VERSION,
        "agent_access_policy_version": AGENT_ACCESS_POLICY_VERSION,
    }
    mismatches = {
        key: {"expected": expected, "actual": actual_versions.get(key)}
        for key, expected in expected_versions.items()
        if actual_versions.get(key) != expected
    }
    if mismatches:
        raise LibraryVersionMismatchError(f"RP5C library version mismatch: {mismatches}")


def load_library(
    repo_root: str | Path | None = None,
    *,
    expected_versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Load the RP5C central surfaces without reading raw RP5A/RP5B inputs."""

    _check_versions(expected_versions)
    keys = (
        "immutable_qku_library",
        "immutable_formula_library",
        "immutable_qku_formula_library",
        "qku_market_applicability_matrix",
        "market_stage_activation_profile_registry",
        "agent_qku_access_policy_registry",
        "stage_computation_universe_view",
        "agent_computation_universe_view",
        "stage_agent_qku_universe_resolver",
        "library_query_receipts",
    )
    loaded = {key: sorted(_read_jsonl(_shard_path(key, repo_root)), key=_stable_identity_key) for key in keys}
    return {
        **loaded,
        "versions": {
            "library_version": LIBRARY_VERSION,
            "applicability_matrix_version": APPLICABILITY_MATRIX_VERSION,
            "stage_profile_version": STAGE_PROFILE_VERSION,
            "agent_access_policy_version": AGENT_ACCESS_POLICY_VERSION,
        },
        "loaded_surface_paths": [
            str(Path("docs") / "master_plan" / "generated" / "rp5c" / ROW_SHARDS[key]).replace("\\", "/")
            for key in keys
        ],
        "raw_legacy_surface_paths_read": [],
    }


def list_qkus(library: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = library if library is not None else load_library()
    return [dict(row) for row in sorted(data["immutable_qku_library"], key=_stable_identity_key)]


def list_formulas(library: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = library if library is not None else load_library()
    return [dict(row) for row in sorted(data["immutable_formula_library"], key=_stable_identity_key)]


def get_qku(qku_id: str, library: dict[str, Any] | None = None) -> dict[str, Any] | None:
    data = library if library is not None else load_library()
    for row in sorted(data["immutable_qku_library"], key=_stable_identity_key):
        if row.get("qku_id") == qku_id:
            return dict(row)
    return None


def get_formula(formula_id: str, library: dict[str, Any] | None = None) -> dict[str, Any] | None:
    data = library if library is not None else load_library()
    for row in sorted(data["immutable_formula_library"], key=_stable_identity_key):
        if row.get("formula_id") == formula_id:
            return dict(row)
    return None


def _stage_market_allowed(matrix_row: dict[str, Any], stage_profile: dict[str, Any]) -> bool:
    if matrix_row.get("applicability_mode") == "CROSS_MARKET_SHARED":
        return bool(stage_profile.get("include_cross_market_shared"))
    if matrix_row.get("applicability_mode") == "MARKET_SPECIFIC":
        return bool(set(matrix_row.get("market_family_refs", [])) & set(stage_profile.get("enabled_market_family_refs", [])))
    return False


def _policy_allows_identity(
    policy: dict[str, Any],
    identity: dict[str, Any],
    matrix_row: dict[str, Any],
    platform_id: str,
    access_mode: str,
) -> bool:
    return (
        identity.get("ontology_category") in set(policy.get("allowed_ontology_categories", []))
        and identity.get("formula_family") in set(policy.get("allowed_formula_family_refs", []))
        and identity.get("qku_family") in set(policy.get("allowed_qku_family_refs", []))
        and bool(set(matrix_row.get("market_family_refs", [])) & set(policy.get("allowed_market_family_refs", [])))
        and platform_id in set(policy.get("allowed_platform_refs", []))
        and access_mode in set(policy.get("allowed_access_modes", []))
    )


def _find_stage_profile(data: dict[str, Any], stage_profile_id: str) -> dict[str, Any]:
    for row in data["market_stage_activation_profile_registry"]:
        if row.get("profile_id") == stage_profile_id:
            return row
    raise KeyError(f"Unknown RP5C stage profile: {stage_profile_id}")


def _find_agent_policy(data: dict[str, Any], agent_id: str) -> dict[str, Any]:
    for row in data["agent_qku_access_policy_registry"]:
        if row.get("agent_id") == agent_id:
            return row
    raise KeyError(f"Unknown RP5C agent policy: {agent_id}")


def query_ids(
    stage_profile_id: str,
    agent_id: str,
    platform_id: str,
    ontology_roles: Iterable[str] | None = None,
    formula_families: Iterable[str] | None = None,
    access_mode: str | None = None,
    library: dict[str, Any] | None = None,
) -> list[str]:
    data = library if library is not None else load_library()
    stage_profile = _find_stage_profile(data, stage_profile_id)
    policy = _find_agent_policy(data, agent_id)
    ontology_filter = set(ontology_roles or [])
    family_filter = set(formula_families or [])
    matrix_by_identity = {row["identity_row_id"]: row for row in data["qku_market_applicability_matrix"]}
    result: list[str] = []
    for identity in sorted(data["immutable_qku_formula_library"], key=_stable_identity_key):
        matrix_row = matrix_by_identity.get(identity["identity_row_id"])
        if not matrix_row:
            continue
        resolved_access_mode = matrix_row.get("stage_access_mode_by_profile", {}).get(stage_profile_id)
        if resolved_access_mode is None:
            continue
        if access_mode is not None and resolved_access_mode != access_mode:
            continue
        if ontology_filter and identity.get("ontology_category") not in ontology_filter:
            continue
        if family_filter and identity.get("formula_family") not in family_filter:
            continue
        if not _stage_market_allowed(matrix_row, stage_profile):
            continue
        if platform_id not in set(matrix_row.get("platform_refs", [])):
            continue
        if resolved_access_mode not in set(stage_profile.get("access_modes", [])):
            continue
        if not _policy_allows_identity(policy, identity, matrix_row, platform_id, resolved_access_mode):
            continue
        result.append(identity["identity_row_id"])
    return sorted(result, key=_stable_ref_key)


def resolve_stage_agent_universe(
    stage_profile_id: str,
    agent_id: str,
    platform_id: str,
    library: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = library if library is not None else load_library()
    resolved_refs = query_ids(stage_profile_id, agent_id, platform_id, library=data)
    matrix_by_identity = {row["identity_row_id"]: row for row in data["qku_market_applicability_matrix"]}
    default_refs = [
        ref
        for ref in resolved_refs
        if matrix_by_identity[ref]["stage_access_mode_by_profile"][stage_profile_id] == "DEFAULT_COMPUTE"
    ]
    on_demand_refs = [
        ref
        for ref in resolved_refs
        if matrix_by_identity[ref]["stage_access_mode_by_profile"][stage_profile_id] == "AVAILABLE_ON_DEMAND"
    ]
    blocked_count = max(len(data["immutable_qku_formula_library"]) - len(resolved_refs), 0)
    return {
        "query_receipt_id": f"RP5C_READER_RECEIPT_{stage_profile_id}_{agent_id}_{platform_id}",
        "agent_id": agent_id,
        "stage_profile_id": stage_profile_id,
        "platform_id": platform_id,
        "library_version": LIBRARY_VERSION,
        "applicability_matrix_version": APPLICABILITY_MATRIX_VERSION,
        "access_policy_version": AGENT_ACCESS_POLICY_VERSION,
        "requested_filters": {
            "ontology_roles": None,
            "formula_families": None,
            "access_mode": None,
        },
        "resolved_identity_count": len(resolved_refs),
        "default_compute_count": len(default_refs),
        "available_on_demand_count": len(on_demand_refs),
        "blocked_count": blocked_count,
        "blocker_codes": [] if resolved_refs else ["NO_AGENT_STAGE_PLATFORM_MATCH"],
        "result_identity_refs": resolved_refs,
    }


def load_rows(identity_ids: Iterable[str], library: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = library if library is not None else load_library()
    requested = set(identity_ids)
    rows = [row for row in data["immutable_qku_formula_library"] if row.get("identity_row_id") in requested]
    return [dict(row) for row in sorted(rows, key=_stable_identity_key)]


__all__ = [
    "LibraryVersionMismatchError",
    "STAGE1_PROFILE_ID",
    "get_formula",
    "get_qku",
    "list_formulas",
    "list_qkus",
    "load_library",
    "load_rows",
    "query_ids",
    "resolve_stage_agent_universe",
]
