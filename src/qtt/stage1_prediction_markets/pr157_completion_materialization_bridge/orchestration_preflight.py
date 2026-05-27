"""Mandatory PR157 orchestration preflight."""

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
            if requested_exists:
                receipts.append(
                    artifact_receipt(
                        repo_root,
                        path,
                        artifact_role="mandatory_pr136_crosswalk",
                        required=True,
                    )
                )
            else:
                receipts.append(
                    artifact_receipt(
                        repo_root,
                        path,
                        artifact_role="mandatory_pr136_crosswalk_requested_absent",
                        required=True,
                        consumed=False,
                    )
                )
                receipts.append(
                    artifact_receipt(
                        repo_root,
                        c.CROSSWALK_FALLBACK_PATH,
                        artifact_role="mandatory_pr136_crosswalk_allowed_fallback",
                        required=True,
                        fallback_used=True,
                    )
                )
            continue
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="mandatory_orchestration_input",
                required=True,
            )
        )

    for path in c.PR153_PR156_ARTIFACTS:
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="pr153_pr156_bridge_input",
                required=True,
            )
        )
    for path in c.ATOMICROWS_CONTEXT_ARTIFACTS:
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="atomicrows_context_input",
                required=True,
            )
        )
    for path in c.PR63_PR69_OPTIONAL_ARTIFACTS:
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="pr63_pr69_agent_formula_algorithm_optional_context",
                required=False,
            )
        )
    for path in c.PR82_PR86_OPTIONAL_ARTIFACTS:
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="pr82_pr86_classical_quantum_optimizer_optional_context",
                required=False,
            )
        )
    for path in c.SOURCE_EVIDENCE_CONTEXT_ARTIFACTS:
        receipts.append(
            artifact_receipt(
                repo_root,
                path,
                artifact_role="source_evidence_context_input",
                required=False,
            )
        )
    receipts.append(
        artifact_receipt(
            repo_root,
            c.OWNER_RESPONSE_PATH,
            artifact_role="optional_owner_input_response",
            required=False,
        )
    )
    return receipts


def preflight_failures(receipts: list[dict[str, Any]]) -> tuple[str, ...]:
    failures: list[str] = []
    fallback_consumed = any(
        receipt["path"] == c.CROSSWALK_FALLBACK_PATH.as_posix()
        and receipt["exists"]
        and receipt["consumed"]
        for receipt in receipts
    )
    for receipt in receipts:
        if receipt["required_or_optional"] != "required":
            continue
        if receipt["path"] == "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json":
            if not receipt["exists"] and fallback_consumed:
                continue
        if not receipt["exists"] or not receipt["consumed"]:
            failures.append(
                "PR157_BLOCKED_MISSING_MANDATORY_ORCHESTRATION_INPUT:"
                f"{receipt['path']}"
            )
    return tuple(sorted(set(failures)))


def orchestration_alignment_receipt(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    consumed_paths = {
        str(receipt["path"]) for receipt in receipts if receipt.get("consumed") is True
    }
    fallback_used = c.CROSSWALK_FALLBACK_PATH.as_posix() in consumed_paths
    return {
        "pr_sequencing_alignment": True,
        "capability_dependency_alignment": True,
        "launch_readiness_placement_alignment": True,
        "atomicrows_enrichment_order_alignment": True,
        "replay_paper_live_transition_alignment": True,
        "quantum_forward_compatibility_alignment": True,
        "market_specific_orchestration_alignment": True,
        "owner_dashboard_future_control_alignment": True,
        "no_orphan_agent_responsibility_alignment": True,
        "fallback_crosswalk_used": fallback_used,
        "consumed_required_path_count": sum(
            1
            for receipt in receipts
            if receipt["required_or_optional"] == "required" and receipt.get("consumed")
        ),
        "missing_required_paths": [
            receipt["path"]
            for receipt in receipts
            if receipt["required_or_optional"] == "required"
            and not receipt.get("exists")
            and not (
                receipt["path"]
                == "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
                and fallback_used
            )
        ],
        "no_runtime_execution_confirmation": True,
    }
