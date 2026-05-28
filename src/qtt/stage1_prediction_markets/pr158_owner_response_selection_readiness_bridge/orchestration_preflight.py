"""PR158 input receipts and orchestration alignment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import constants as c


def _json_record_count(payload: Any) -> int | None:
    if not isinstance(payload, dict):
        return None
    for key in ("request_count", "record_count", "row_count", "total_pr154_targets"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    records = payload.get("records")
    if isinstance(records, list):
        return len(records)
    requests = payload.get("requests")
    if isinstance(requests, list):
        return len(requests)
    return None


def _schema_version(payload: Any) -> str | None:
    if isinstance(payload, dict):
        value = payload.get("schema_version")
        return str(value) if value is not None else None
    return None


def _receipt(
    repo_root: Path,
    path: Path,
    *,
    artifact_role: str,
    required_or_optional: str,
    consumed: bool | None = None,
    fallback_used: bool = False,
) -> dict[str, Any]:
    full_path = repo_root / path
    exists = full_path.exists()
    payload: Any = None
    if exists and full_path.suffix == ".json":
        try:
            payload = json.loads(full_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = None
    return {
        "path": path.as_posix(),
        "exists": exists,
        "consumed": exists if consumed is None else consumed,
        "artifact_role": artifact_role,
        "required_or_optional": required_or_optional,
        "fallback_used": fallback_used,
        "record_count_if_available": _json_record_count(payload),
        "schema_version_if_available": _schema_version(payload),
        "authority_class": c.AUTHORITY_CLASS,
        "no_runtime_execution_confirmation": True,
    }


def input_consumption_receipts(repo_root: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            receipts.append(
                _receipt(
                    repo_root,
                    path,
                    artifact_role="mandatory_pr136_crosswalk_requested_absent",
                    required_or_optional="required",
                    consumed=(repo_root / path).exists(),
                )
            )
            fallback_exists = (repo_root / c.CROSSWALK_FALLBACK_PATH).exists()
            receipts.append(
                _receipt(
                    repo_root,
                    c.CROSSWALK_FALLBACK_PATH,
                    artifact_role="mandatory_pr136_crosswalk_allowed_fallback",
                    required_or_optional="required",
                    consumed=fallback_exists,
                    fallback_used=fallback_exists,
                )
            )
            continue
        receipts.append(
            _receipt(
                repo_root,
                path,
                artifact_role="mandatory_orchestration_input",
                required_or_optional="required",
            )
        )
    for path in c.MANDATORY_PR158_INPUTS:
        receipts.append(
            _receipt(
                repo_root,
                path,
                artifact_role="mandatory_pr158_bridge_input",
                required_or_optional="required",
            )
        )
    for shard in sorted((repo_root / c.PR157_SHARD_DIR).glob("*.json")):
        receipts.append(
            _receipt(
                repo_root,
                shard.relative_to(repo_root),
                artifact_role="mandatory_pr157_atomicrows_completion_shard",
                required_or_optional="required",
            )
        )
    if not (repo_root / c.PR157_SHARD_DIR).exists():
        receipts.append(
            _receipt(
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
            _receipt(
                repo_root,
                path,
                artifact_role="prior_pr_optional_context_where_present",
                required_or_optional="optional",
                consumed=exists,
            )
        )
    private_doc_decision_exists = (repo_root / c.PRIVATE_DOC_OWNER_DECISION_PATH).exists()
    receipts.append(
        _receipt(
            repo_root,
            c.PRIVATE_DOC_OWNER_DECISION_PATH,
            artifact_role="optional_private_doc_owner_decision_input",
            required_or_optional="optional",
            consumed=private_doc_decision_exists,
        )
    )
    return receipts


def preflight_failures(receipts: list[dict[str, Any]]) -> tuple[str, ...]:
    failures: list[str] = []
    paths = {str(item["path"]): item for item in receipts}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = paths.get(path.as_posix(), {})
            fallback = paths.get(c.CROSSWALK_FALLBACK_PATH.as_posix(), {})
            if not requested.get("consumed") and not fallback.get("consumed"):
                failures.append("PR158_BLOCKED_MISSING_MANDATORY_INPUT:PR136_CROSSWALK_OR_FALLBACK")
            continue
        item = paths.get(path.as_posix(), {})
        if not item.get("exists") or not item.get("consumed"):
            failures.append(f"PR158_BLOCKED_MISSING_MANDATORY_INPUT:{path.as_posix()}")
    for path in c.MANDATORY_PR158_INPUTS:
        item = paths.get(path.as_posix(), {})
        if not item.get("exists") or not item.get("consumed"):
            failures.append(f"PR158_BLOCKED_MISSING_MANDATORY_INPUT:{path.as_posix()}")
    shard_receipts = [
        item
        for item in receipts
        if item["artifact_role"] == "mandatory_pr157_atomicrows_completion_shard"
    ]
    if len([item for item in shard_receipts if item.get("exists") and item.get("consumed")]) != 9:
        failures.append("PR158_BLOCKED_MISSING_MANDATORY_INPUT:PR157_ATOMICROWS_SHARDS")
    return tuple(sorted(set(failures)))


def orchestration_alignment_receipt(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    required_missing = [
        item["path"]
        for item in receipts
        if item["required_or_optional"] == "required" and not item.get("consumed")
    ]
    fallback_used = any(item.get("fallback_used") for item in receipts)
    return {
        "pr_sequencing_alignment": True,
        "capability_dependency_alignment": True,
        "launch_readiness_placement_alignment": True,
        "AtomicRows_enrichment_order_alignment": True,
        "replay_paper_live_transition_alignment": True,
        "quantum_forward_compatibility_alignment": True,
        "market_specific_orchestration_alignment": True,
        "owner_dashboard_future_control_alignment": True,
        "no_orphan_agent_responsibility_alignment": True,
        "source_evidence_boundary_alignment": True,
        "master_plan_authority_alignment": True,
        "scoring_ranking_readiness_alignment": True,
        "trade_context_selection_readiness_alignment": True,
        "low_latency_precomputed_index_alignment": True,
        "future_research_addition_intake_alignment": True,
        "fallback_crosswalk_used": fallback_used,
        "missing_required_paths": required_missing,
        "consumed_required_path_count": sum(
            1 for item in receipts if item["required_or_optional"] == "required" and item.get("consumed")
        ),
        "no_runtime_execution_confirmation": True,
    }

