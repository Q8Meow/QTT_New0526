"""PR160 input-consumption and orchestration-alignment receipts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import as_list, as_mapping, read_json


def _record_count_if_available(path: Path) -> int | None:
    if not path.exists() or path.is_dir():
        return None
    if path.suffix != ".json":
        return None
    try:
        payload = read_json(path)
    except Exception:
        return None
    mapping = as_mapping(payload)
    if isinstance(mapping.get("records"), list):
        return len(as_list(mapping.get("records")))
    if isinstance(mapping.get("requests"), list):
        return len(as_list(mapping.get("requests")))
    if isinstance(mapping.get("response_items"), list):
        return len(as_list(mapping.get("response_items")))
    if isinstance(mapping.get("parameter_target_items"), list):
        return len(as_list(mapping.get("parameter_target_items")))
    matrix = as_mapping(mapping.get("parameter_default_target_matrix"))
    if isinstance(matrix.get("parameter_target_items"), list):
        return len(as_list(matrix.get("parameter_target_items")))
    if isinstance(mapping.get("record_count"), int):
        return int(mapping["record_count"])
    return None


def _schema_version_if_available(path: Path) -> str | None:
    if not path.exists() or path.is_dir() or path.suffix != ".json":
        return None
    try:
        payload = as_mapping(read_json(path))
    except Exception:
        return None
    for key in ("schema_version", "report_version", "version"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def _receipt(
    root: Path,
    rel_path: Path,
    *,
    role: str,
    required: bool,
    fallback_used: bool = False,
    consumed_override: bool | None = None,
) -> dict[str, Any]:
    path = root / rel_path
    exists = path.exists()
    consumed = bool(exists) if consumed_override is None else consumed_override
    return {
        "path": rel_path.as_posix(),
        "exists": exists,
        "consumed": consumed,
        "artifact_role": role,
        "required_or_optional": "required" if required else "optional",
        "fallback_used": fallback_used,
        "record_count_if_available": _record_count_if_available(path),
        "schema_version_if_available": _schema_version_if_available(path),
        "authority_class": c.AUTHORITY_CLASS,
        "no_runtime_execution_confirmation": True,
    }


def input_consumption_receipts(root: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    fallback_exists = (root / c.CROSSWALK_FALLBACK_PATH).exists()
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested_exists = (root / path).exists()
            receipts.append(
                _receipt(
                    root,
                    path,
                    role="mandatory_pr136_section_crosswalk_requested",
                    required=True,
                    fallback_used=fallback_exists and not requested_exists,
                    consumed_override=requested_exists,
                )
            )
            if fallback_exists and not requested_exists:
                receipts.append(
                    _receipt(
                        root,
                        c.CROSSWALK_FALLBACK_PATH,
                        role="mandatory_pr136_section_crosswalk_fallback",
                        required=True,
                        fallback_used=True,
                    )
                )
            continue
        receipts.append(
            _receipt(root, path, role="mandatory_orchestration_input", required=True)
        )
    for path in c.MANDATORY_PR160_INPUTS:
        receipts.append(_receipt(root, path, role="mandatory_pr160_input", required=True))
    shard_dir = root / c.PR157_SHARD_DIR
    for shard_path in sorted(shard_dir.glob("*.json")) if shard_dir.exists() else []:
        receipts.append(
            _receipt(
                root,
                shard_path.relative_to(root),
                role="mandatory_pr157_atomicrows_completion_shard",
                required=True,
            )
        )
    for path in c.OPTIONAL_PRIOR_ARTIFACTS:
        receipts.append(_receipt(root, path, role="optional_prior_context_artifact", required=False))
    return sorted(receipts, key=lambda item: item["path"])


def preflight_failures(receipts: list[dict[str, Any]]) -> tuple[str, ...]:
    failures: list[str] = []
    by_path = {str(item["path"]): item for item in receipts}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = by_path.get(path.as_posix(), {})
            fallback = by_path.get(c.CROSSWALK_FALLBACK_PATH.as_posix(), {})
            if not (requested.get("consumed") or fallback.get("consumed")):
                failures.append("PR160_BLOCKED_MISSING_MANDATORY_INPUT:CROSSWALK_OR_FALLBACK")
            continue
        item = by_path.get(path.as_posix(), {})
        if not (item.get("exists") and item.get("consumed")):
            failures.append(f"PR160_BLOCKED_MISSING_MANDATORY_INPUT:{path.as_posix()}")
    for path in c.MANDATORY_PR160_INPUTS:
        item = by_path.get(path.as_posix(), {})
        if not (item.get("exists") and item.get("consumed")):
            failures.append(f"PR160_BLOCKED_MISSING_MANDATORY_INPUT:{path.as_posix()}")
    shard_count = sum(
        1
        for item in receipts
        if item.get("artifact_role") == "mandatory_pr157_atomicrows_completion_shard"
        and item.get("exists")
        and item.get("consumed")
    )
    if shard_count != 9:
        failures.append("PR160_BLOCKED_MISSING_MANDATORY_INPUT:PR157_SHARDS")
    return tuple(sorted(set(failures)))


def orchestration_alignment_receipt(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    consumed_paths = {str(item["path"]) for item in receipts if item.get("consumed")}
    fallback_used = any(item.get("fallback_used") for item in receipts)
    return {
        "PR_sequencing_alignment": "PR160 follows PR159 and bridges PR154 split/reclassification records to PR159R/PR161/PR163/PR164-plus routes.",
        "capability_dependency_alignment": "Routes depend on accepted source evidence, owner/internal authority, agent binding, replay/paper, or quantum/runtime gates only as metadata.",
        "launch_readiness_placement_alignment": "Day-1 launch remains blocked until future source, materialization, exact-agent, scoring, replay/paper, connector/runtime, and owner gates pass.",
        "source_evidence_placement_alignment": c.PR159_ACCEPTED_PACKET_REGISTRY_PATH.as_posix() in consumed_paths,
        "AtomicRows_enrichment_order_alignment": "PR160 creates route updates only; PR161/PR162 own later materialization and final audit.",
        "replay_paper_live_transition_alignment": "PR160 creates no replay, paper, live, order, fill, or profit authority.",
        "quantum_forward_compatibility_alignment": "Quantum records are metadata-only or future-gated; no backend evidence is created.",
        "market_specific_orchestration_alignment": c.MANDATORY_ORCHESTRATION_INPUTS[6].as_posix() in consumed_paths,
        "owner_dashboard_future_control_alignment": "Owner/internal policy remains owner-editable and live-blocked until replay/paper and owner review.",
        "no_orphan_agent_responsibility_alignment": "Every record includes a required actor and future route; exact agent IDs remain deferred to PR163 when needed.",
        "PR158_selection_readiness_overlay_alignment": c.PR158_SELECTION_OVERLAY_REGISTRY_PATH.as_posix() in consumed_paths,
        "PR159_accepted_unresolved_source_route_alignment": c.PR159_UNRESOLVED_FILL_PATH_PATH.as_posix() in consumed_paths,
        "low_latency_precomputed_index_alignment": c.PR158_LOW_LATENCY_INDEX_PATH.as_posix() in consumed_paths,
        "future_research_addition_intake_alignment": True,
        "PR159R_readiness_alignment": True,
        "PR161_PR162_AtomicRows_materialization_audit_readiness_alignment": True,
        "PR163_exact_agent_binding_readiness_alignment": True,
        "fallback_crosswalk_used": fallback_used,
    }
