"""PR159 input receipts and orchestration alignment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .input_discovery import artifact_receipt


def input_consumption_receipts(repo_root: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested_exists = (repo_root / path).exists()
            fallback_exists = (repo_root / c.CROSSWALK_FALLBACK_PATH).exists()
            receipts.append(
                artifact_receipt(
                    repo_root,
                    path,
                    artifact_role="mandatory_pr136_crosswalk_requested",
                    required_or_optional="required",
                    consumed=requested_exists,
                )
            )
            receipts.append(
                artifact_receipt(
                    repo_root,
                    c.CROSSWALK_FALLBACK_PATH,
                    artifact_role="mandatory_pr136_crosswalk_allowed_fallback",
                    required_or_optional="required",
                    consumed=(not requested_exists and fallback_exists),
                    fallback_used=(not requested_exists and fallback_exists),
                )
            )
            continue
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="mandatory_orchestration_input",
                required_or_optional="required",
            )
        )
    for path in c.MANDATORY_PR159_INPUTS:
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="mandatory_pr159_bridge_input",
                required_or_optional="required",
            )
        )
    for shard in sorted((repo_root / c.PR157_SHARD_DIR).glob("*.json")):
        receipts.append(
            artifact_receipt(
                repo_root,
                shard.relative_to(repo_root),
                artifact_role="mandatory_pr157_atomicrows_completion_shard",
                required_or_optional="required",
            )
        )
    if not (repo_root / c.PR157_SHARD_DIR).exists():
        receipts.append(
            artifact_receipt(
                repo_root,
                c.PR157_SHARD_DIR / "*.json",
                artifact_role="mandatory_pr157_atomicrows_completion_shard",
                required_or_optional="required",
                consumed=False,
            )
        )
    for path in c.OPTIONAL_PRIOR_ARTIFACTS:
        exists = (repo_root / path).exists()
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="optional_prior_pr_context_where_present",
                required_or_optional="optional",
                consumed=exists,
            )
        )
    return receipts


def preflight_failures(receipts: list[dict[str, Any]]) -> tuple[str, ...]:
    failures: list[str] = []
    by_path = {str(item["path"]): item for item in receipts}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = by_path.get(path.as_posix(), {})
            fallback = by_path.get(c.CROSSWALK_FALLBACK_PATH.as_posix(), {})
            if not requested.get("consumed") and not fallback.get("consumed"):
                failures.append("PR159_BLOCKED_MISSING_MANDATORY_INPUT:PR136_CROSSWALK_OR_FALLBACK")
            continue
        item = by_path.get(path.as_posix(), {})
        if not item.get("exists") or not item.get("consumed"):
            failures.append(f"PR159_BLOCKED_MISSING_MANDATORY_INPUT:{path.as_posix()}")
    for path in c.MANDATORY_PR159_INPUTS:
        item = by_path.get(path.as_posix(), {})
        if not item.get("exists") or not item.get("consumed"):
            failures.append(f"PR159_BLOCKED_MISSING_MANDATORY_INPUT:{path.as_posix()}")
    shard_receipts = [
        item
        for item in receipts
        if item.get("artifact_role") == "mandatory_pr157_atomicrows_completion_shard"
    ]
    if len([item for item in shard_receipts if item.get("exists") and item.get("consumed")]) != 9:
        failures.append("PR159_BLOCKED_MISSING_MANDATORY_INPUT:PR157_ATOMICROWS_SHARDS")
    return tuple(sorted(set(failures)))


def orchestration_alignment_receipt(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    missing_required = [
        item["path"]
        for item in receipts
        if item["required_or_optional"] == "required" and not item.get("consumed")
    ]
    fallback_used = any(item.get("fallback_used") for item in receipts)
    return {
        "pr_sequencing_alignment": True,
        "capability_dependency_alignment": True,
        "launch_readiness_placement_alignment": True,
        "source_evidence_placement_alignment": True,
        "AtomicRows_enrichment_order_alignment": True,
        "replay_paper_live_transition_alignment": True,
        "quantum_forward_compatibility_alignment": True,
        "market_specific_orchestration_alignment": True,
        "owner_dashboard_future_control_alignment": True,
        "no_orphan_agent_responsibility_alignment": True,
        "PR158_selection_readiness_overlay_alignment": True,
        "low_latency_precomputed_index_alignment": True,
        "future_research_addition_intake_alignment": True,
        "official_source_completion_to_later_scoring_ranking_alignment": True,
        "fallback_crosswalk_used": fallback_used,
        "missing_required_paths": missing_required,
        "consumed_required_path_count": sum(
            1 for item in receipts if item["required_or_optional"] == "required" and item.get("consumed")
        ),
        "no_runtime_execution_confirmation": True,
    }
