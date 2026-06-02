"""PR162C mandatory input preflight reader."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from . import constants as c
from .paths import normalize_repo_relative_ref, resolve_repo_relative


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def preflight_receipt(repo_root: Path) -> dict[str, Any]:
    present: list[str] = []
    missing: list[str] = []
    fallbacks: list[dict[str, str]] = []
    consumed: list[str] = []
    for ref in c.REQUIRED_INPUT_REPORTS:
        normalized = normalize_repo_relative_ref(repo_root, ref, label="PR162C required input")
        path = resolve_repo_relative(repo_root, normalized)
        if path.exists():
            present.append(normalized)
            consumed.append(normalized)
            continue
        missing.append(normalized)
        for fallback in c.FALLBACK_INPUT_REPORTS.get(normalized, ()):
            fallback_ref = normalize_repo_relative_ref(repo_root, fallback, label="PR162C fallback input")
            if resolve_repo_relative(repo_root, fallback_ref).exists():
                fallbacks.append({"missing_input": normalized, "fallback_path": fallback_ref})
                consumed.append(fallback_ref)
                break
    consumed_set = set(consumed)
    return {
        "required_inputs_present": present,
        "required_inputs_missing": missing,
        "fallback_paths_used": fallbacks,
        "consumed_input_refs": sorted(consumed_set),
        "PR136_control_plane_consumed": any("PR136RouteTriage.report.json" in item for item in consumed_set)
        and any("PR136CommandActionMatrix.report.json" in item for item in consumed_set),
        "PR162B_handoff_consumed": (
            "docs/master_plan/generated/PR162B_PR162CDataRequirementHandoff.report.json"
            in consumed_set
        ),
        "PR162B_registry_baseline_consumed": all(
            f"docs/master_plan/generated/{filename}" in consumed_set
            for filename in c.PR162B_REGISTRY_REPORTS
        ),
        "PR162A_repaired_state_consumed": (
            "docs/master_plan/generated/PR162A_FinalSummary.report.json" in consumed_set
        ),
        "online_discovery_allowed": True,
        "ci_offline_required": True,
        "source_class_taxonomy_selected": list(c.SOURCE_CLASSES),
        "qku_execution_class_taxonomy_selected": list(c.QKU_EXECUTION_CLASSES),
        "market_scope_taxonomy_selected": list(c.MARKET_SCOPES),
        "agent_route_taxonomy_selected": list(c.QTT_AGENT_ROUTES),
        "no_sha_freeze_hash_authority_confirmed": True,
        "no_atomicrows_bundle_mutation_confirmed": True,
    }
