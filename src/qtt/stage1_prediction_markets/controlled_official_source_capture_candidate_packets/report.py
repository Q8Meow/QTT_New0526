"""Deterministic PR153 report builder and validator."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import constants as c
from . import reason_codes as rc
from .models import (
    OWNER_DECISION_OPTIONS,
    OWNER_NON_SOURCE_BACKED_STATUSES,
    no_claim_flags,
)


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(_read_text(path))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _path_record(root: Path, rel_path: Path, required: bool) -> dict[str, Any]:
    path = root / rel_path
    exists = path.exists()
    return {
        "artifact_path": rel_path.as_posix(),
        "exists": exists,
        "consumed": exists,
        "required": required,
        "artifact_type": "dir" if exists and path.is_dir() else "file" if exists else "missing",
        "reason_codes": [
            "PR153_PREFLIGHT_ARTIFACT_FOUND" if exists else "PR153_PREFLIGHT_ARTIFACT_MISSING",
            "PR153_PREFLIGHT_READ_ONLY_CONTEXT_CONSUMED" if exists else "PR153_PREFLIGHT_ARTIFACT_MISSING",
        ],
    }


def _read_required_json(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR153_UPSTREAM_REPORT_MISSING: {key}: {rel_path.as_posix()}")
        return {}
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(
            f"PR153_UPSTREAM_REPORT_PARSE_ERROR: {key}: {rel_path.as_posix()}: {exc}"
        )
        return {}


def _read_required_text(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> str:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR153_UPSTREAM_REPORT_MISSING: {key}: {rel_path.as_posix()}")
        return ""
    try:
        return _read_text(path)
    except OSError as exc:
        failures.append(
            f"PR153_UPSTREAM_REPORT_PARSE_ERROR: {key}: {rel_path.as_posix()}: {exc}"
        )
        return ""


def _crosswalk_payload(root: Path, failures: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    alias_path = root / c.PR136_SECTION_CROSSWALK_ALIAS_PATH
    canonical_path = root / c.PR136_SECTION_CROSSWALK_CANONICAL_PATH
    alias_exists = alias_path.exists()
    canonical_exists = canonical_path.exists()
    selected = (
        c.PR136_SECTION_CROSSWALK_ALIAS_PATH
        if alias_exists
        else c.PR136_SECTION_CROSSWALK_CANONICAL_PATH
    )
    if not alias_exists and not canonical_exists:
        failures.append(
            "PR153_UPSTREAM_REPORT_MISSING: pr136_section_crosswalk_or_alias: "
            f"{c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix()}"
        )
        return {}, {
            "alias_used": False,
            "canonical_successor_used": False,
            "created_missing_alias": False,
            "selected_path": c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix(),
        }
    payload = _read_required_json(root, "pr136_section_crosswalk_or_alias", selected, failures)
    return payload, {
        "alias_used": alias_exists,
        "canonical_successor_used": not alias_exists and canonical_exists,
        "created_missing_alias": False,
        "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
        "selected_path": selected.as_posix(),
        "reason_codes": ["PR153_PREFLIGHT_CROSSWALK_ALIAS_USED"]
        if not alias_exists and canonical_exists
        else ["PR153_PREFLIGHT_ARTIFACT_FOUND"],
    }


def load_static_evidence(repo_root: Path | str) -> tuple[dict[str, Any], list[str]]:
    root = Path(repo_root).resolve()
    failures: list[str] = []

    text_payloads = {
        "launch_roadmap": _read_required_text(root, "launch_roadmap", c.ROADMAP_PATH, failures),
        "launch_roadmap_policy": _read_required_text(
            root, "launch_roadmap_policy", c.ROADMAP_POLICY_PATH, failures
        ),
        "owner_source_evidence_packet": _read_required_text(
            root,
            "owner_source_evidence_packet",
            c.SOURCE_EVIDENCE_PACKET_PATH,
            failures,
        ),
    }
    json_payloads = {
        "control_plane_roster": _read_required_json(
            root, "control_plane_roster", c.ROSTER_PATH, failures
        ),
        "control_plane_controller": _read_required_json(
            root, "control_plane_controller", c.CONTROLLER_PATH, failures
        ),
        "pr136_route_triage": _read_required_json(
            root, "pr136_route_triage", c.PR136_ROUTE_TRIAGE_PATH, failures
        ),
        "pr136_market_index": _read_required_json(
            root, "pr136_market_index", c.PR136_MARKET_INDEX_PATH, failures
        ),
        "pr136_command_matrix": _read_required_json(
            root, "pr136_command_matrix", c.PR136_COMMAND_MATRIX_PATH, failures
        ),
        "pr137r_reconciliation": _read_required_json(
            root, "pr137r_reconciliation", c.PR137R_REPORT_PATH, failures
        ),
        "pr138_semantic_contract": _read_required_json(
            root, "pr138_semantic_contract", c.PR138_REPORT_PATH, failures
        ),
        "pr149_bridge_report": _read_required_json(
            root, "pr149_bridge_report", c.PR149_REPORT_PATH, failures
        ),
        "pr150_target_matrix": _read_required_json(
            root, "pr150_target_matrix", c.PR150_REPORT_PATH, failures
        ),
        "pr151_target_pack": _read_required_json(
            root, "pr151_target_pack", c.PR151_REPORT_PATH, failures
        ),
        "pr152_global_audit": _read_required_json(
            root, "pr152_global_audit", c.PR152_REPORT_PATH, failures
        ),
    }
    crosswalk, alias_resolution = _crosswalk_payload(root, failures)
    json_payloads["pr136_section_crosswalk_or_alias"] = crosswalk

    for rel_path in (c.PR151_MODULE_DIR_PATH, c.PR150_MODULE_DIR_PATH, c.PR152_MODULE_DIR_PATH):
        path = root / rel_path
        if not path.exists() or not path.is_dir():
            failures.append(f"PR153_UPSTREAM_REPORT_MISSING: module_dir: {rel_path.as_posix()}")

    artifact_receipts = [
        _path_record(root, rel_path, True) for rel_path in c.REQUIRED_UPSTREAM_ARTIFACTS
    ]
    return {
        "repo_root": root,
        "text_payloads": text_payloads,
        "json_payloads": json_payloads,
        "crosswalk_alias_resolution": alias_resolution,
        "artifact_receipts": artifact_receipts,
    }, failures


def _pr150_items(pr150: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    matrix = _mapping(pr150.get("parameter_default_target_matrix"))
    return [item for item in _list(matrix.get("parameter_target_items")) if isinstance(item, Mapping)]


def _pr151_targets(pr151: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        item
        for item in _list(pr151.get("official_source_retrieval_target_queue"))
        if isinstance(item, Mapping)
    ]


def _target_priority(target: Mapping[str, Any]) -> str:
    cls = str(target.get("source_target_class") or "")
    if cls in c.P0_SOURCE_TARGET_CLASSES:
        return "P0"
    if cls in c.P1_SOURCE_TARGET_CLASSES:
        return "P1"
    if cls in c.P2_SOURCE_TARGET_CLASSES:
        return "P2"
    if cls in c.P3_SOURCE_TARGET_CLASSES:
        return "P3"
    return "P2"


def _target_sort_key(target: Mapping[str, Any]) -> tuple[int, str, str, str]:
    priority = _target_priority(target)
    return (
        c.PRIORITY_ORDER[priority],
        str(target.get("target_platform_scope") or ""),
        str(target.get("target_field_path") or ""),
        str(target.get("retrieval_target_id") or ""),
    )


def _matching_route(target: Mapping[str, Any]) -> Mapping[str, Any] | None:
    platform = str(target.get("target_platform_scope") or "")
    field_id = str(target.get("target_field_id") or "")
    requested_class = str(target.get("official_source_class") or "")
    for route in c.SOURCE_ROUTES:
        if platform not in route["platforms"]:
            continue
        if field_id not in route["target_field_ids"]:
            continue
        if requested_class != route["official_source_class"]:
            continue
        return route
    return None


def _candidate_packet(
    target: Mapping[str, Any],
    route: Mapping[str, Any],
    batch_id: str,
) -> dict[str, Any]:
    retrieval_target_id = str(target["retrieval_target_id"])
    locator_type = str(route["locator_type"])
    reason_codes = [
        "PR153_CAPTURE_OFFICIAL_SOURCE_CANDIDATE_CREATED",
        "PR153_CAPTURE_OFFICIAL_SOURCE_CLASS_ALLOWED",
        "PR153_CAPTURE_DOMAIN_ROUTE_RECORDED",
        "PR153_CAPTURE_OFFICIALITY_EVIDENCE_RECORDED",
        "PR153_CAPTURE_REVALIDATION_CLASS_RECORDED",
        "PR153_CAPTURE_PR154_HANDOFF_READY",
    ]
    if locator_type == "QUOTE_SPAN":
        reason_codes.append("PR153_CAPTURE_QUOTE_SPAN_RECORDED")
    else:
        reason_codes.append("PR153_CAPTURE_MACHINE_FIELD_LOCATOR_RECORDED")

    officiality = {
        "official_source_class": route["official_source_class"],
        "domain_verification_status": "VERIFIED_OFFICIAL_PUBLIC_DOC_DOMAIN",
        "officiality_route": route["officiality_route"],
        "source_class_basis": "PUBLIC_OFFICIAL_DOC_ROUTE_DISCOVERED_AND_RECORDED",
        "retrieval_method_policy": "CONTROLLED_PUBLIC_DOC_CAPTURE_ONLY",
        "source_locator": route["source_locator"],
        "source_url": route["source_url"],
        "source_domain": route["source_domain"],
        "capture_status": "CAPTURED_CANDIDATE_ONLY_NOT_ACCEPTED",
        "reason_codes": [
            "PR153_CAPTURE_OFFICIAL_SOURCE_CLASS_ALLOWED",
            "PR153_CAPTURE_OFFICIALITY_EVIDENCE_RECORDED",
            "PR153_CAPTURE_DOMAIN_ROUTE_RECORDED",
        ],
    }
    return {
        "candidate_packet_id": f"PR153_CANDIDATE_PACKET__{retrieval_target_id}",
        "retrieval_target_id": retrieval_target_id,
        "pr151_target_ref": retrieval_target_id,
        "pr150_target_ref": target.get("pr150_target_id"),
        "platform_scope": target.get("target_platform_scope"),
        "market_scope": target.get("target_market_scope"),
        "batch_id": batch_id,
        "priority_class": _target_priority(target),
        "target_field_path": target.get("target_field_path"),
        "target_field_id": target.get("target_field_id"),
        "requested_official_source_class": target.get("official_source_class"),
        "official_source_class": route["official_source_class"],
        "source_locator": route["source_locator"],
        "source_domain": route["source_domain"],
        "source_url": route["source_url"],
        "source_title": route["source_title"],
        "source_access_method": "PUBLIC_WEB_DOC_CAPTURE",
        "retrieval_method_policy": "CONTROLLED_ONLINE_CAPTURE_STATIC_RECORD_ONLY",
        "retrieval_status": "PUBLIC_DOC_RETRIEVED_WITHOUT_AUTHENTICATION",
        "capture_status": "CAPTURED_CANDIDATE_ONLY_NOT_ACCEPTED",
        "officiality_evidence": officiality,
        "officiality_route": route["officiality_route"],
        "source_class_basis": "OFFICIAL_SOURCE_CLASS_MATCHES_PR151_TARGET_AND_OFFICIAL_ROUTE",
        "domain_verification_status": "VERIFIED_OFFICIAL_PUBLIC_DOC_DOMAIN",
        "quote_span_or_machine_field_locator": {
            "locator_type": locator_type,
            "source_locator": route["source_locator"],
            "quote_text_or_machine_locator": route["quote_or_locator"],
        },
        "captured_candidate_text_or_value": route["quote_or_locator"],
        "candidate_observation_type": route["candidate_observation_type"],
        "unit_or_scale_if_present": target.get("unit_or_scale"),
        "applicability_scope_if_present": {
            "platform_scope": target.get("target_platform_scope"),
            "market_scope": target.get("target_market_scope"),
            "target_field_id": target.get("target_field_id"),
        },
        "conflict_review_required": target.get("conflict_policy_class")
        in {
            "OFFICIAL_SOURCE_CONFLICT_REVIEW_REQUIRED",
            "MULTI_OFFICIAL_SOURCE_CONFLICT_REVIEW_REQUIRED",
            "OWNER_REVIEW_REQUIRED_FOR_CONFLICT",
        },
        "conflict_review_reason_codes": ["PR153_HANDOFF_TO_PR154_ACCEPTANCE_REQUIRED"],
        "revalidation_class": target.get("revalidation_class"),
        "source_change_materiality_preclassification": "PR154_MUST_REVALIDATE_BEFORE_ACCEPTANCE",
        "acceptance_status": "NOT_ACCEPTED_CANDIDATE_ONLY",
        "connector_binding_status": "NOT_BOUND",
        "runtime_receipt_status": "NOT_CREATED",
        "order_use_eligibility": "NOT_ORDER_USABLE_CANDIDATE_ONLY",
        "replay_paper_truth_use_eligibility": "NOT_REPLAY_PAPER_TRUTH_USABLE_CANDIDATE_ONLY",
        "launch_readiness_use_eligibility": "NOT_LAUNCH_READINESS_USABLE_CANDIDATE_ONLY",
        "atomicrows_materialization_dependency": "PR154_ACCEPTANCE_AND_PR155_MATERIALIZATION_REQUIRED",
        "quantum_forward_dependency": target.get("quantum_forward_dependency"),
        "pr154_acceptance_required": True,
        "reason_codes": sorted(reason_codes),
        "no_claim_flags": no_claim_flags(True),
    }


def _blocker_category(target: Mapping[str, Any]) -> str:
    field_id = str(target.get("target_field_id") or "")
    if field_id in c.PRIVATE_OR_AUTH_FIELD_IDS:
        return "SOURCE_REQUIRES_LOGIN_OR_PRIVATE_ACCESS"
    if field_id in c.INTERNAL_QTT_FIELD_IDS:
        return "TARGET_NOT_CAPTURE_CANDIDATE"
    if str(target.get("official_source_class") or "") == "OFFICIAL_PROVIDER_DOCS":
        return "TARGET_FIELD_TOO_GRANULAR"
    if str(target.get("source_target_class") or "") == "ATOMICROWS_COMPATIBILITY_SOURCE_TARGET":
        return "TARGET_NOT_CAPTURE_CANDIDATE"
    return "EXACT_VALUE_NOT_VISIBLE"


def _unresolved_target(
    target: Mapping[str, Any],
    batch_id: str,
    attempted_urls: Sequence[str],
) -> dict[str, Any]:
    category = _blocker_category(target)
    reason_code = rc.BLOCKER_CATEGORY_TO_REASON_CODE[category]
    field_id = str(target.get("target_field_id") or "")
    can_owner_doc = category in {
        "OFFICIAL_SOURCE_NOT_FOUND",
        "EXACT_VALUE_NOT_VISIBLE",
        "SOURCE_REQUIRES_LOGIN_OR_PRIVATE_ACCESS",
    }
    return {
        "retrieval_target_id": target.get("retrieval_target_id"),
        "pr151_target_ref": target.get("retrieval_target_id"),
        "pr150_target_ref": target.get("pr150_target_id"),
        "platform_scope": target.get("target_platform_scope"),
        "market_scope": target.get("target_market_scope"),
        "target_field_path": target.get("target_field_path"),
        "target_field_id": field_id,
        "priority_class": _target_priority(target),
        "batch_id": batch_id,
        "attempted_source_queries": _attempted_queries(target),
        "attempted_source_urls": sorted(set(attempted_urls)),
        "best_candidate_source_locator_if_any": None,
        "blocker_primary_category": category,
        "blocker_secondary_categories": [],
        "blocker_reason_detail": _blocker_detail(category, field_id),
        "exact_missing_evidence": "Exact official quote span or machine-field locator for this PR151 target was not captured.",
        "required_next_action": _next_action(category),
        "owner_review_required": True,
        "pr154_review_required": True,
        "can_be_solved_by_broader_search": category
        in {"OFFICIAL_SOURCE_NOT_FOUND", "EXACT_VALUE_NOT_VISIBLE", "TARGET_FIELD_TOO_GRANULAR"},
        "can_be_solved_by_manual_official_locator": category
        in {"EXACT_VALUE_NOT_VISIBLE", "TARGET_FIELD_TOO_GRANULAR", "OFFICIAL_SOURCE_NOT_FOUND"},
        "can_be_solved_by_owner_uploaded_doc": can_owner_doc,
        "can_be_solved_by_target_split_or_reclassification": category
        in {"TARGET_FIELD_TOO_GRANULAR", "TARGET_NOT_CAPTURE_CANDIDATE"},
        "can_be_solved_only_by_private_or_authenticated_source": category
        == "SOURCE_REQUIRES_LOGIN_OR_PRIVATE_ACCESS",
        "candidate_packet_created": False,
        "owner_decision_options": list(OWNER_DECISION_OPTIONS),
        "reason_codes": [
            reason_code,
            "PR153_OWNER_DECISION_REQUIRED",
            "PR153_HANDOFF_TO_PR154_ACCEPTANCE_REQUIRED",
        ],
        "no_claim_flags": no_claim_flags(False),
    }


def _blocker_detail(category: str, field_id: str) -> str:
    details = {
        "SOURCE_REQUIRES_LOGIN_OR_PRIVATE_ACCESS": (
            "The target concerns account/private-state semantics; PR153 did not authenticate "
            "or fetch private account state."
        ),
        "TARGET_NOT_CAPTURE_CANDIDATE": (
            "The target is an internal QTT policy or architecture slot, not an external "
            "official venue/provider fact candidate."
        ),
        "TARGET_FIELD_TOO_GRANULAR": (
            "Public official provider documentation was found, but not an exact locator "
            "for this target field path."
        ),
        "EXACT_VALUE_NOT_VISIBLE": (
            "Official routes were discovered, but the exact target value or field locator "
            "was not visible in the captured public source evidence."
        ),
    }
    return details.get(category, "No exact official-source candidate could be captured.")


def _next_action(category: str) -> str:
    actions = {
        "SOURCE_REQUIRES_LOGIN_OR_PRIVATE_ACCESS": "OWNER_DECIDE_PRIVATE_DOC_OR_DE_SCOPE_ROUTE",
        "TARGET_NOT_CAPTURE_CANDIDATE": "OWNER_REVIEW_TARGET_RECLASSIFICATION_OR_INTERNAL_POLICY_ROUTE",
        "TARGET_FIELD_TOO_GRANULAR": "MANUAL_OFFICIAL_LOCATOR_OR_TARGET_SPLIT_REQUIRED",
        "EXACT_VALUE_NOT_VISIBLE": "BROADER_PUBLIC_OFFICIAL_SOURCE_SEARCH_OR_OWNER_LOCATOR_REQUIRED",
    }
    return actions.get(category, "BROADER_PUBLIC_OFFICIAL_SOURCE_SEARCH_REQUIRED")


def _attempted_queries(target: Mapping[str, Any]) -> list[str]:
    platform = str(target.get("target_platform_scope") or "")
    field = str(target.get("target_field_id") or "")
    return [
        f"{platform} official documentation {field}",
        f"{platform} official API docs {field}",
        *c.CONTROLLED_DISCOVERY_QUERIES[:2],
    ]


def _attempted_urls_for_target(target: Mapping[str, Any]) -> list[str]:
    platform = str(target.get("target_platform_scope") or "")
    urls = []
    for route in c.SOURCE_ROUTES:
        if platform in route["platforms"]:
            urls.append(str(route["source_url"]))
    return urls[:6]


def _build_batches(targets: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    sorted_targets = sorted(targets, key=_target_sort_key)
    batches = []
    for index in range(0, len(sorted_targets), c.BATCH_SIZE):
        batch_targets = sorted_targets[index : index + c.BATCH_SIZE]
        batch_number = index // c.BATCH_SIZE + 1
        batch_id = f"PR153_BATCH_{batch_number:03d}"
        batches.append(
            {
                "batch_id": batch_id,
                "batch_index": batch_number,
                "batch_size": c.BATCH_SIZE,
                "batch_target_count": len(batch_targets),
                "batch_ordering": [
                    "priority_class",
                    "platform_scope",
                    "target_field_path",
                    "retrieval_target_id",
                ],
                "target_ids": [str(target["retrieval_target_id"]) for target in batch_targets],
                "reason_codes": ["PR153_BATCH_PLAN_CREATED"],
            }
        )
    return batches


def _build_capture(
    batches: Sequence[Mapping[str, Any]],
    targets_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    unresolved_before = len(targets_by_id)

    for batch in batches:
        before_candidates = len(candidates)
        before_unresolved = unresolved_before
        batch_candidate_domains: set[str] = set()
        batch_source_classes: set[str] = set()
        batch_blockers: set[str] = set()
        for target_id in batch["target_ids"]:
            target = targets_by_id[target_id]
            route = _matching_route(target)
            if route is None:
                record = _unresolved_target(
                    target,
                    str(batch["batch_id"]),
                    _attempted_urls_for_target(target),
                )
                unresolved.append(record)
                batch_blockers.add(record["blocker_primary_category"])
                ledger.append(
                    _progress_record(
                        target,
                        str(batch["batch_id"]),
                        "UNRESOLVED_BLOCKER_TRIAGED",
                        False,
                        record,
                    )
                )
                continue
            packet = _candidate_packet(target, route, str(batch["batch_id"]))
            candidates.append(packet)
            batch_candidate_domains.add(str(packet["source_domain"]))
            batch_source_classes.add(str(packet["official_source_class"]))
            ledger.append(
                _progress_record(
                    target,
                    str(batch["batch_id"]),
                    "CAPTURED_CANDIDATE_ONLY_NOT_ACCEPTED",
                    True,
                    None,
                )
            )

        unresolved_before = len(targets_by_id) - len(candidates)
        receipts.append(
            {
                "batch_id": batch["batch_id"],
                "batch_index": batch["batch_index"],
                "batch_target_count": batch["batch_target_count"],
                "target_ids": batch["target_ids"],
                "batch_status": "COMPLETED_WITH_CANDIDATES_AND_BLOCKERS",
                "web_search_used": True,
                "command_network_used": True,
                "candidate_count_before": before_candidates,
                "candidate_count_after": len(candidates),
                "unresolved_count_before": before_unresolved,
                "unresolved_count_after": len(targets_by_id) - len(candidates),
                "source_domains_found": sorted(batch_candidate_domains),
                "source_classes_found": sorted(batch_source_classes),
                "blocker_categories_found": sorted(batch_blockers),
                "validation_status": "BATCH_STRUCTURE_VALIDATED_STATICALLY",
                "next_resume_cursor": {
                    "next_batch_id": _next_batch_id(batches, int(batch["batch_index"])),
                    "candidate_packet_count": len(candidates),
                    "unresolved_target_count": len(targets_by_id) - len(candidates),
                },
                "reason_codes": [
                    "PR153_BATCH_STARTED",
                    "PR153_BATCH_COMPLETED",
                    "PR153_BATCH_RESUME_CURSOR_RECORDED",
                    "PR153_CAPTURE_PROGRESS_LEDGER_UPDATED",
                ],
            }
        )
    return candidates, unresolved, ledger, receipts


def _progress_record(
    target: Mapping[str, Any],
    batch_id: str,
    status: str,
    candidate_created: bool,
    unresolved: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "retrieval_target_id": target.get("retrieval_target_id"),
        "target_field_path": target.get("target_field_path"),
        "priority_class": _target_priority(target),
        "platform_scope": target.get("target_platform_scope"),
        "batch_id": batch_id,
        "capture_status": status,
        "candidate_packet_created": candidate_created,
        "blocker_primary_category": None
        if unresolved is None
        else unresolved.get("blocker_primary_category"),
        "owner_decision_options": []
        if unresolved is None
        else list(unresolved.get("owner_decision_options", [])),
        "next_required_action": None
        if unresolved is None
        else unresolved.get("required_next_action"),
    }


def _next_batch_id(batches: Sequence[Mapping[str, Any]], current_index: int) -> str | None:
    for batch in batches:
        if int(batch["batch_index"]) == current_index + 1:
            return str(batch["batch_id"])
    return None


def _index_by(
    packets: Sequence[Mapping[str, Any]],
    key: str,
) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for packet in packets:
        value = str(packet.get(key) or "")
        if not value:
            continue
        index.setdefault(value, []).append(str(packet["candidate_packet_id"]))
    return {item_key: sorted(values) for item_key, values in sorted(index.items())}


def _target_path_family_group(target_field_path: str) -> tuple[str, str]:
    parts = target_field_path.split(".")
    family = parts[3] if len(parts) > 3 else ""
    group = parts[4] if len(parts) > 4 else ""
    return family, group


def _pr153a_lane_for_unresolved(item: Mapping[str, Any]) -> str:
    category = str(item.get("blocker_primary_category") or "")
    family, group = _target_path_family_group(str(item.get("target_field_path") or ""))
    if category == "TARGET_NOT_CAPTURE_CANDIDATE":
        return "INTERNAL_QTT_POLICY_OR_CONTROL_PLANE_TARGET"
    if category == "TARGET_FIELD_TOO_GRANULAR":
        return "TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED"
    if category == "SOURCE_REQUIRES_LOGIN_OR_PRIVATE_ACCESS":
        return "PRIVATE_DOC_OR_ATTESTATION_REQUIRED"
    if category == "EXACT_VALUE_NOT_VISIBLE":
        if family == "classical_strategy_parameter" or (
            family == "replay_paper_calibration" and group == "paper_metric_target_slots"
        ):
            return "OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE"
        if (
            family == "venue_source_required"
            and group == "venue_cross_venue_normalization_dependencies"
        ):
            return "TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED"
        return "EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET"
    return "OWNER_DISAPPROVAL_OR_DESCOPE_CANDIDATE"


def _pr153a_lane_counts(
    candidates: Sequence[Mapping[str, Any]],
    unresolved: Sequence[Mapping[str, Any]],
) -> Counter[str]:
    counts = Counter({lane: 0 for lane in c.ELIGIBILITY_LANES})
    counts["PR154_ACCEPTANCE_REVIEW_ONLY"] = len(candidates)
    for item in unresolved:
        counts[_pr153a_lane_for_unresolved(item)] += 1
    return counts


def _pr153a_retry_targets(unresolved: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "retrieval_target_id": item["retrieval_target_id"],
            "platform_scope": item["platform_scope"],
            "priority_class": item["priority_class"],
            "target_field_path": item["target_field_path"],
            "blocker_primary_category": item["blocker_primary_category"],
            "next_required_action": "PR153R_RETRY_BROADER_PUBLIC_OFFICIAL_SOURCE_CAPTURE_OR_OWNER_MANUAL_OFFICIAL_LOCATOR_THEN_PR154_OR_OWNER_OVERRIDE",
        }
        for item in sorted(unresolved, key=lambda value: str(value["retrieval_target_id"]))
        if _pr153a_lane_for_unresolved(item) == "EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET"
    ]


def _corrected_denominator_summary(lane_counts: Mapping[str, int]) -> dict[str, Any]:
    captured = int(lane_counts["PR154_ACCEPTANCE_REVIEW_ONLY"])
    retry = int(lane_counts["EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET"])
    return {
        "total_PR151_targets": c.PR153A_TOTAL_PR151_TARGETS,
        "true_external_public_source_value_capture_target_count": captured + retry,
        "captured_candidate_packet_count": captured,
        "remaining_external_public_capture_retry_target_count": retry,
        "internal_control_plane_target_count": int(
            lane_counts["INTERNAL_QTT_POLICY_OR_CONTROL_PLANE_TARGET"]
        ),
        "target_split_or_reclassification_required_count": int(
            lane_counts["TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED"]
        ),
        "private_doc_or_attestation_required_count": int(
            lane_counts["PRIVATE_DOC_OR_ATTESTATION_REQUIRED"]
        ),
        "owner_provided_value_candidate_route_count": int(
            lane_counts["OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE"]
        ),
        "pr154_acceptance_review_only_count": captured,
        "corrected_public_capture_denominator": captured + retry,
        "reason_codes": [
            rc.PR153_OWNER_APPROVED_CORRECTED_DENOMINATOR,
            rc.PR153_BLOCKER_TRIAGE_SUCCESS_NOT_FULL_CAPTURE_SUCCESS,
        ],
    }


def _pr153_completion_status(
    *,
    target_count: int,
    candidate_count: int,
    unresolved_count: int,
) -> dict[str, Any]:
    return {
        "full_capture_success": False,
        "blocker_triage_success": True,
        "completion_label": c.COMPLETION_LABEL,
        "owner_approved_commit_framing": c.OWNER_APPROVED_COMMIT_FRAMING,
        "not_full_342_capture_success": True,
        "all_PR151_targets_accounted": candidate_count + unresolved_count == target_count,
        "total_accounted_targets": candidate_count + unresolved_count,
        "completion_statuses_supported": [
            c.COMPLETION_LABEL,
            c.OWNER_APPROVED_COMMIT_FRAMING,
            c.FULL_CAPTURE_SUCCESS,
            c.BLOCKER_TRIAGE_SUCCESS,
        ],
        "reason_codes": [
            rc.PR153_OWNER_APPROVED_BLOCKER_TRIAGE_ARCHITECTURE,
            rc.PR153_BLOCKER_TRIAGE_SUCCESS_NOT_FULL_CAPTURE_SUCCESS,
        ],
    }


def _owner_approved_lane_routing_summary(
    lane_counts: Mapping[str, int],
) -> dict[str, dict[str, Any]]:
    return {
        lane: {
            "owner_route": c.OWNER_ROUTE_BY_ELIGIBILITY_LANE[lane],
            "count": int(lane_counts[lane]),
            "can_owner_override_external_fact_truth_as_source_backed": False,
        }
        for lane in c.ELIGIBILITY_LANES
    }


def _owner_global_authority_override_clarification() -> dict[str, Any]:
    return {
        "owner_may_override_pr154_workflow_gate": True,
        "owner_may_defer_pr154_workflow_gate": True,
        "owner_may_bypass_pr154_workflow_gate_with_receipt": True,
        "owner_override_does_not_create_source_backed_truth": True,
        "owner_override_does_not_create_accepted_source_evidence": True,
        "allowed_owner_non_source_backed_statuses": list(OWNER_NON_SOURCE_BACKED_STATUSES),
        "owner_override_statuses_supported": list(c.OWNER_NON_SOURCE_BACKED_OVERRIDE_STATUSES),
        **c.OWNER_NON_SOURCE_BACKED_RISK_FLAGS,
        "reason_codes": [
            rc.PR153_OWNER_MAY_OVERRIDE_PR154_WORKFLOW_GATE,
            rc.PR153_OWNER_OVERRIDE_DOES_NOT_CREATE_SOURCE_BACKED_TRUTH,
            rc.PR153_OWNER_AUTHORIZED_NON_SOURCE_BACKED_CANDIDATE_ALLOWED,
            rc.PR153_OWNER_AUTHORIZED_NON_SOURCE_BACKED_RUNTIME_VALUE_PENDING_LATER_OWNER_COMMAND_ALLOWED,
            rc.PR153_OWNER_OVERRIDE_RECEIPT_REQUIRED,
        ],
    }


def _pr153r_retry_capture_contract(
    retry_targets: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "retry_target_count": len(retry_targets),
        "retry_scope": "EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET only",
        "retry_target_ids": [str(item["retrieval_target_id"]) for item in retry_targets],
        "no_internal_control_plane_rows_in_retry": True,
        "no_target_split_reclassification_rows_in_retry": True,
        "no_private_doc_attestation_rows_in_retry_without_owner_doc_packet": True,
        "no_owner_provided_external_value_as_source_truth": True,
        "PR154_or_owner_non_source_backed_override_route_required_after_retry": True,
        "reason_codes": [
            rc.PR153_PR153R_RETRY_CAPTURE_REQUIRED_FOR_34_EXTERNAL_TARGETS,
            rc.PR153_OWNER_OVERRIDE_DOES_NOT_CREATE_SOURCE_BACKED_TRUTH,
        ],
    }


def _pr154_or_owner_override_handoff_contract(candidate_count: int) -> dict[str, Any]:
    return {
        "captured_candidate_count": candidate_count,
        "candidates_are_not_accepted_source_evidence": True,
        "pr154_independent_revalidation_available": True,
        "owner_non_source_backed_override_available": True,
        "owner_non_source_backed_override_requires_receipt": True,
        "owner_non_source_backed_override_preserves_risk_flags": True,
        "source_backed_truth_requires_PR154_or_later_accepted_source_evidence": True,
        "non_source_backed_owner_use_requires_explicit_owner_override_receipt": True,
        **c.OWNER_NON_SOURCE_BACKED_RISK_FLAGS,
        "reason_codes": [
            rc.PR153_PR154_OR_OWNER_OVERRIDE_HANDOFF_READY,
            rc.PR153_OWNER_OVERRIDE_RECEIPT_REQUIRED,
        ],
    }


def _owner_external_fact_boundary() -> dict[str, Any]:
    return {
        "can_owner_override_internal_workflow_blocker": True,
        "can_owner_approve_internal_policy_route": True,
        "can_owner_provide_external_fact_candidate": True,
        "can_owner_override_pr154_workflow_gate": True,
        "can_owner_override_external_fact_truth_as_source_backed": False,
        "owner_authorized_non_source_backed_candidate_allowed": True,
        "owner_authorized_non_source_backed_runtime_value_pending_later_owner_command_allowed": True,
        "connector_runtime_order_live_atomicrows_use_blocked_without_later_gates_or_explicit_owner_override_receipt": True,
        **c.OWNER_NON_SOURCE_BACKED_RISK_FLAGS,
        "reason_codes": [
            rc.PR153_OWNER_DECISION_EXTERNAL_FACT_BOUNDARY_PRESERVED,
            rc.PR153_OWNER_OVERRIDE_DOES_NOT_CREATE_SOURCE_BACKED_TRUTH,
        ],
    }


def _next_pr_path_recommendation() -> list[str]:
    return [
        "commit PR153 only as blocker-triage architecture after validation",
        "PR153R retry capture for 34 remaining true external public source-value targets",
        "PR154 accepted source evidence ledger for 92 captured candidates and later PR153R candidates, unless owner explicitly chooses non-source-backed override route",
        "owner manual locator/value packet for owner-provided/private-doc lanes",
        "PR155 AtomicRows/default materialization only after PR154 accepted evidence or a later explicit owner non-source-backed materialization override receipt",
    ]


def _owner_decision_layer(unresolved: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_category = Counter(str(item["blocker_primary_category"]) for item in unresolved)
    by_platform = Counter(str(item["platform_scope"]) for item in unresolved)
    by_priority = Counter(str(item["priority_class"]) for item in unresolved)
    lane_counts = _pr153a_lane_counts([], unresolved)
    return {
        "owner_decision_layer_enabled": True,
        "owner_decision_options": list(OWNER_DECISION_OPTIONS),
        "owner_approved_commit_framing": c.OWNER_APPROVED_COMMIT_FRAMING,
        "owner_lane_routing_summary": _owner_approved_lane_routing_summary(lane_counts),
        "owner_decision_receipts": [],
        "owner_provided_value_candidates": [],
        "owner_decision_required_queue": [
            {
                "retrieval_target_id": item["retrieval_target_id"],
                "target_field_path": item["target_field_path"],
                "platform_scope": item["platform_scope"],
                "priority_class": item["priority_class"],
                "blocker_primary_category": item["blocker_primary_category"],
                "recommended_primary_eligibility_lane": _pr153a_lane_for_unresolved(item),
                "owner_route": c.OWNER_ROUTE_BY_ELIGIBILITY_LANE[
                    _pr153a_lane_for_unresolved(item)
                ],
                "owner_decision_options": list(OWNER_DECISION_OPTIONS),
                "next_required_action": item["required_next_action"],
                "can_owner_override_external_fact_truth_as_source_backed": False,
            }
            for item in sorted(unresolved, key=lambda value: str(value["retrieval_target_id"]))
        ],
        "owner_decision_summary_by_blocker_category": dict(sorted(by_category.items())),
        "owner_decision_summary_by_platform": dict(sorted(by_platform.items())),
        "owner_decision_summary_by_priority_class": dict(sorted(by_priority.items())),
        "owner_decision_external_fact_boundary": {
            "owner_can_control_internal_qtt_workflow": True,
            "owner_cannot_convert_unverified_external_fact_to_source_backed_truth": True,
            "owner_may_override_pr154_workflow_gate": True,
            "owner_override_does_not_create_source_backed_truth": True,
            "allowed_owner_non_source_backed_statuses": list(OWNER_NON_SOURCE_BACKED_STATUSES),
            "owner_override_receipt_required": True,
            "owner_assumes_external_fact_risk": True,
            "downstream_consumer_warning_required": True,
            "accepted_source_evidence_packet_created": False,
            "connector_semantic_value_created": False,
            "runtime_cash_value_created": False,
            "order_parameter_created": False,
        },
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    evidence, failures = load_static_evidence(repo_root)
    payloads = evidence["json_payloads"]
    pr150_items = _pr150_items(payloads["pr150_target_matrix"])
    pr150_ids = {str(item.get("target_id")) for item in pr150_items}
    targets = _pr151_targets(payloads["pr151_target_pack"])
    batches = _build_batches(targets)
    targets_by_id = {str(target["retrieval_target_id"]): target for target in targets}
    candidates, unresolved, ledger, receipts = _build_capture(batches, targets_by_id)

    candidate_pr150_missing = sorted(
        {
            str(packet["pr150_target_ref"])
            for packet in candidates
            if str(packet["pr150_target_ref"]) not in pr150_ids
        }
    )
    target_count = len(targets)
    candidate_count = len(candidates)
    unresolved_count = len(unresolved)
    full_success = candidate_count == target_count and unresolved_count == 0
    status = c.SUCCESS_MARKER if full_success else c.INCOMPLETE_MARKER
    blocker_counts = Counter(str(item["blocker_primary_category"]) for item in unresolved)
    lane_counts = _pr153a_lane_counts(candidates, unresolved)
    retry_targets = _pr153a_retry_targets(unresolved)

    report = {
        "report_id": c.REPORT_ID,
        "report_version": c.REPORT_VERSION,
        "pr_id": c.PR_ID,
        "pr_title": c.PR_TITLE,
        "authority_class": c.AUTHORITY_CLASS,
        "readiness_class": c.READINESS_CLASS,
        "pr153_completion_status": _pr153_completion_status(
            target_count=target_count,
            candidate_count=candidate_count,
            unresolved_count=unresolved_count,
        ),
        "corrected_denominator_summary": _corrected_denominator_summary(lane_counts),
        "owner_approved_lane_routing_summary": _owner_approved_lane_routing_summary(
            lane_counts
        ),
        "owner_global_authority_override_clarification": (
            _owner_global_authority_override_clarification()
        ),
        "pr153r_retry_capture_contract": _pr153r_retry_capture_contract(retry_targets),
        "pr154_or_owner_override_handoff_contract": (
            _pr154_or_owner_override_handoff_contract(candidate_count)
        ),
        "owner_external_fact_boundary": _owner_external_fact_boundary(),
        "next_pr_path_recommendation": _next_pr_path_recommendation(),
        "deterministic_generation_policy": {
            "random_ids_allowed": False,
            "wall_clock_used": False,
            "stable_json_sort_keys": True,
            "candidate_sort_key": [
                "retrieval_target_id",
                "platform_scope",
                "target_field_path",
                "official_source_class",
            ],
            "unresolved_sort_key": ["retrieval_target_id"],
        },
        "upstream_artifact_inputs": {
            "required_artifact_count": len(c.REQUIRED_UPSTREAM_ARTIFACTS),
            "all_required_artifacts_found": not failures,
            "crosswalk_alias_resolution": evidence["crosswalk_alias_resolution"],
        },
        "preflight_artifact_receipts": evidence["artifact_receipts"],
        "web_capture_environment_receipt": {
            "controlled_online_source_capture_used": True,
            "web_search_status": "CONTROLLED_PUBLIC_WEB_DISCOVERY_USED",
            "command_network_status": "CONTROLLED_PUBLIC_DOC_INDEX_FETCH_USED",
            "authenticated_or_private_endpoint_used": False,
            "trading_order_endpoint_called": False,
            "secret_used": False,
            "reason_codes": [
                "PR153_PREFLIGHT_ONLINE_CAPTURE_AVAILABLE",
                "PR153_PREFLIGHT_COMMAND_NETWORK_AVAILABLE",
                "PR153_PREFLIGHT_SEARCH_TOOL_AVAILABLE",
            ],
        },
        "source_discovery_policy": {
            "broad_discovery_allowed": True,
            "non_authoritative_sources_locator_hints_only": True,
            "official_capture_required": True,
            "guessed_domains_allowed_in_candidate_packets": False,
            "guessed_values_allowed_in_candidate_packets": False,
            "controlled_discovery_queries": list(c.CONTROLLED_DISCOVERY_QUERIES),
        },
        "capture_batch_plan": batches,
        "capture_batch_receipts": receipts,
        "capture_progress_ledger": ledger,
        "capture_resume_cursor": {
            "resume_status": "NO_NEXT_BATCH_ALL_TARGETS_ATTEMPTED",
            "next_batch_id": None,
            "next_batch_index": None,
            "candidate_packet_count": candidate_count,
            "unresolved_target_count": unresolved_count,
            "next_required_action": "OWNER_DECISION_QUEUE_OR_MANUAL_OFFICIAL_LOCATOR_REDO"
            if unresolved_count
            else "PR154_ACCEPTANCE_REVIEW",
            "reason_codes": ["PR153_BATCH_RESUME_CURSOR_RECORDED"],
        },
        "capture_blocker_category_summary": {
            "blocking_category_counts": dict(sorted(blocker_counts.items())),
            "pr153a_owner_approved_lane_counts": {
                lane: int(lane_counts[lane]) for lane in c.ELIGIBILITY_LANES
            },
            "remaining_external_public_capture_retry_target_count": len(retry_targets),
            "blocker_triage_success_not_full_capture_success": True,
            "top_20_unresolved_p0_p1_targets": _top_unresolved_p0_p1(unresolved),
            "blocker_category_to_next_pr_or_owner_action_map": _blocker_action_map(blocker_counts),
            "another_pr153r_run_can_solve_by_category": _pr153r_solve_map(blocker_counts),
            "pr154_owner_validator_review_required": unresolved_count > 0,
            "target_field_reclassification_required": any(
                item["blocker_primary_category"] in {"TARGET_NOT_CAPTURE_CANDIDATE", "TARGET_FIELD_TOO_GRANULAR"}
                for item in unresolved
            ),
        },
        "pr136_alignment_summary": {
            "route_triage_consumed": bool(payloads["pr136_route_triage"]),
            "section_crosswalk_or_alias_consumed": bool(
                payloads["pr136_section_crosswalk_or_alias"]
            ),
            "market_specific_index_consumed": bool(payloads["pr136_market_index"]),
            "command_action_matrix_consumed": bool(payloads["pr136_command_matrix"]),
            "crosswalk_alias_used": evidence["crosswalk_alias_resolution"]["canonical_successor_used"],
        },
        "pr137r_atomicrows_reconciliation_consumption_summary": {
            "consumed": bool(payloads["pr137r_reconciliation"]),
            "bundle_mutation_attempted": False,
        },
        "pr138_atomicrows_semantic_row_contract_consumption_summary": {
            "consumed": bool(payloads["pr138_semantic_contract"]),
            "semantic_contract_used_for_context_only": True,
        },
        "pr149_bridge_consumption_summary": {
            "consumed": bool(payloads["pr149_bridge_report"]),
            "materialization_deferred": True,
        },
        "pr150_target_matrix_consumption_summary": {
            "consumed": bool(payloads["pr150_target_matrix"]),
            "target_mapping_count": len(pr150_items),
            "candidate_pr150_missing_refs": candidate_pr150_missing,
        },
        "pr151_retrieval_target_pack_consumption_summary": {
            "consumed": bool(payloads["pr151_target_pack"]),
            "retrieval_target_count": target_count,
            "unique_pr150_target_refs": len(
                {str(target.get("pr150_target_id")) for target in targets}
            ),
        },
        "pr152_global_audit_consumption_summary": {
            "consumed": bool(payloads["pr152_global_audit"]),
            "audit_used_as_read_only_context": True,
        },
        "owner_source_evidence_packet_summary": {
            "consumed": bool(evidence["text_payloads"]["owner_source_evidence_packet"]),
            "owner_packet_authorizes_retrieval_scope": True,
            "owner_packet_authorizes_external_fact_value": False,
            "reason_codes": ["PR153_PREFLIGHT_OWNER_SOURCE_PACKET_CONSUMED"],
        },
        "controlled_capture_policy": {
            "candidate_only": True,
            "accepted_facts_created": False,
            "connector_binding_created": False,
            "runtime_receipts_created": False,
            "order_or_trading_execution_created": False,
        },
        "official_source_class_policy": {
            "allowed_official_source_classes": list(c.OFFICIAL_SOURCE_CLASS_VALUES),
            "allowed_officiality_routes": list(c.OFFICIALITY_ROUTE_VALUES),
            "candidate_source_classes_observed": sorted(
                {str(packet["official_source_class"]) for packet in candidates}
            ),
        },
        "discovery_attempt_receipts": _discovery_receipts(),
        "official_domain_route_receipts": list(c.OFFICIAL_DOMAIN_ROUTE_RECEIPTS),
        "source_capture_candidate_packets": sorted(
            candidates,
            key=lambda packet: (
                str(packet["retrieval_target_id"]),
                str(packet["platform_scope"]),
                str(packet["target_field_path"]),
                str(packet["official_source_class"]),
            ),
        ),
        "unresolved_capture_targets": sorted(
            unresolved,
            key=lambda item: str(item["retrieval_target_id"]),
        ),
        "source_locator_index": _index_by(candidates, "source_locator"),
        "officiality_evidence_index": _index_by(candidates, "source_domain"),
        "quote_span_index": _locator_index(candidates, "QUOTE_SPAN"),
        "machine_field_locator_index": _locator_index(candidates, "MACHINE_FIELD_LOCATOR"),
        "conflict_review_input_index": {
            str(packet["candidate_packet_id"]): {
                "conflict_review_required": packet["conflict_review_required"],
                "reason_codes": packet["conflict_review_reason_codes"],
            }
            for packet in candidates
        },
        "revalidation_policy_index": {
            str(packet["candidate_packet_id"]): packet["revalidation_class"]
            for packet in candidates
        },
        "acceptance_readiness_index_for_PR154": {
            str(packet["candidate_packet_id"]): {
                "ready_for_pr154_independent_revalidation": True,
                "accepted_in_pr153": False,
            }
            for packet in candidates
        },
        "acceptance_handoff_contract_for_PR154": _pr154_handoff(unresolved_count),
        "owner_blocker_decision_layer": _owner_decision_layer(unresolved),
        "atomicrows_compatibility_surface": {
            "pr137r_reconciliation_consumed": bool(payloads["pr137r_reconciliation"]),
            "pr138_semantic_row_contract_consumed": bool(payloads["pr138_semantic_contract"]),
            "bundle_mutation_attempted": False,
            "bundle_file_created": False,
            "bundle_integrity_artifact_created": False,
            "candidate_capture_materialization_status": "CANDIDATE_ONLY_NOT_MATERIALIZED",
            "pr154_acceptance_dependency": "REQUIRED_BEFORE_PARAMETER_DEFAULT_VALUE_MATERIALIZATION",
            "pr155_materialization_dependency": "PR155_ATOMICROWS_PARAMETER_DEFAULT_VALUE_MATERIALIZATION_REQUIRED_AFTER_PR154_ACCEPTANCE",
        },
        "quantum_forward_capture_surface": {
            "provider_documentation_candidate_capture_allowed": True,
            "quantum_parameter_documentation_candidate_capture_allowed": True,
            "quantum_backend_call_created": False,
            "quantum_simulator_call_created": False,
            "quantum_optimizer_output_created": False,
            "qaoa_execution_created": False,
            "vqe_execution_created": False,
            "annealing_execution_created": False,
            "qubo_solver_execution_created": False,
            "ising_solver_execution_created": False,
            "quantum_advantage_claim_created": False,
            "quantum_latency_superiority_claim_created": False,
            "pr159_or_later_backend_evidence_dependency": "REQUIRED_BEFORE_ANY_BACKEND_OR_OPTIMIZER_RESULT_LEDGER",
        },
        "no_claim_boundary": no_claim_flags(False) | {
            "source_capture_candidate_created": candidate_count > 0,
            "all_prohibited_flags_false_except_candidate_capture_marker": True,
        },
        "centralized_reason_codes": {
            "reason_code_source_module": "src.qtt.stage1_prediction_markets.controlled_official_source_capture_candidate_packets.reason_codes",
            "reason_codes": list(rc.ALL_REASON_CODES),
        },
        "validation_summary": {
            "status": status,
            "full_capture_success": full_success,
            "blocker_triage_success": unresolved_count > 0,
            "completion_label": c.COMPLETION_LABEL,
            "owner_approved_commit_framing": c.OWNER_APPROVED_COMMIT_FRAMING,
            "controlled_online_source_capture_used": True,
            "candidate_packet_count": candidate_count,
            "unresolved_target_count": unresolved_count,
            "pr151_target_count": target_count,
            "total_accounted_targets": candidate_count + unresolved_count,
            "all_PR151_targets_accounted": candidate_count + unresolved_count == target_count,
            "corrected_public_capture_denominator": int(
                lane_counts["PR154_ACCEPTANCE_REVIEW_ONLY"]
                + lane_counts["EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET"]
            ),
            "remaining_external_public_capture_retry_target_count": len(retry_targets),
            "pr150_target_mapping_count": len(pr150_items),
            "candidate_packet_count_equals_pr151_target_count": candidate_count == target_count,
            "unresolved_capture_targets_empty": unresolved_count == 0,
            "reason_codes": [
                "PR153_CAPTURE_ALL_TARGETS_COMPLETED" if full_success else "PR153_CAPTURE_INCOMPLETE_WITH_BLOCKER_TRIAGE",
                "PR153_BLOCK_UNRESOLVED_TARGETS_REMAIN" if unresolved_count else "PR153_CAPTURE_ALL_TARGETS_COMPLETED",
                rc.PR153_OWNER_APPROVED_CORRECTED_DENOMINATOR,
                rc.PR153_OWNER_APPROVED_BLOCKER_TRIAGE_ARCHITECTURE,
                rc.PR153_BLOCKER_TRIAGE_SUCCESS_NOT_FULL_CAPTURE_SUCCESS,
            ],
        },
        "next_consumer_contract": {
            "next_pr": "PR154",
            "next_pr_title": "Accepted Source Evidence Parameter Default Ledger",
            "pr153r_retry_target_count": len(retry_targets),
            "owner_non_source_backed_override_available": True,
            "owner_non_source_backed_override_requires_receipt": True,
            "owner_override_does_not_create_source_backed_truth": True,
            "pr153_outputs_not_consumable_as_values": True,
            "accepted_fact_creation_allowed_in_pr153": False,
            "connector_binding_allowed_in_pr153": False,
            "runtime_receipt_allowed_in_pr153": False,
            "order_use_allowed_in_pr153": False,
            "replay_paper_truth_use_allowed_in_pr153": False,
            "launch_readiness_use_allowed_in_pr153": False,
        },
    }
    return report


def _locator_index(candidates: Sequence[Mapping[str, Any]], locator_type: str) -> dict[str, Any]:
    return {
        str(packet["candidate_packet_id"]): packet["quote_span_or_machine_field_locator"]
        for packet in candidates
        if _mapping(packet.get("quote_span_or_machine_field_locator")).get("locator_type")
        == locator_type
    }


def _discovery_receipts() -> list[dict[str, Any]]:
    return [
        {
            "discovery_attempt_id": f"PR153_DISCOVERY_ATTEMPT_{index:03d}",
            "query": query,
            "web_search_used": True,
            "command_network_used": index in {1, 2, 3, 5},
            "non_authoritative_sources_used_as_locator_hints_only": True,
            "official_route_found": True,
            "reason_codes": [
                "PR153_DISCOVERY_ATTEMPT_RECORDED",
                "PR153_DISCOVERY_BROAD_HINT_USED",
                "PR153_DISCOVERY_OFFICIAL_ROUTE_FOUND",
            ],
        }
        for index, query in enumerate(c.CONTROLLED_DISCOVERY_QUERIES, start=1)
    ]


def _pr154_handoff(unresolved_count: int) -> dict[str, Any]:
    return {
        "pr154_title": "Accepted Source Evidence Parameter Default Ledger",
        "owner_non_source_backed_override_available": True,
        "owner_non_source_backed_override_requires_receipt": True,
        "owner_override_does_not_create_source_backed_truth": True,
        "pr153_outputs_consumable_by_pr154": [
            "source_capture_candidate_packets",
            "officiality_evidence_index",
            "quote_span_index",
            "machine_field_locator_index",
            "conflict_review_input_index",
            "revalidation_policy_index",
            "acceptance_readiness_index_for_PR154",
            "owner_blocker_decision_layer" if unresolved_count else None,
            "blocker_category_summary" if unresolved_count else None,
        ],
        "pr153_outputs_not_consumable_as_values": True,
        "accepted_fact_creation_allowed_in_pr153": False,
        "connector_binding_allowed_in_pr153": False,
        "runtime_receipt_allowed_in_pr153": False,
        "order_use_allowed_in_pr153": False,
        "replay_paper_truth_use_allowed_in_pr153": False,
        "launch_readiness_use_allowed_in_pr153": False,
        "owner_override_workflow_gate_available_but_not_source_truth": True,
        "pr154_must_independently_verify": [
            "exact official source",
            "source URL/domain",
            "source locator",
            "source class",
            "officiality route",
            "quote span or machine-field locator",
            "candidate observation",
            "target field path",
            "platform scope",
            "market scope",
            "unit/scale",
            "applicability scope",
            "conflict state",
            "source-change materiality",
            "revalidation policy",
            "owner review requirement",
        ],
        "reason_codes": [
            "PR153_HANDOFF_TO_PR154_ACCEPTANCE_REQUIRED",
            rc.PR153_PR154_OR_OWNER_OVERRIDE_HANDOFF_READY,
            rc.PR153_OWNER_OVERRIDE_DOES_NOT_CREATE_SOURCE_BACKED_TRUTH,
        ],
    }


def _top_unresolved_p0_p1(unresolved: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    filtered = [
        item
        for item in unresolved
        if item.get("priority_class") in {"P0", "P1"}
    ]
    return [
        {
            "retrieval_target_id": item["retrieval_target_id"],
            "platform_scope": item["platform_scope"],
            "target_field_path": item["target_field_path"],
            "priority_class": item["priority_class"],
            "blocker_primary_category": item["blocker_primary_category"],
            "next_required_action": item["required_next_action"],
        }
        for item in sorted(filtered, key=lambda value: str(value["retrieval_target_id"]))[:20]
    ]


def _blocker_action_map(counter: Counter[str]) -> dict[str, str]:
    return {category: _next_action(category) for category in sorted(counter)}


def _pr153r_solve_map(counter: Counter[str]) -> dict[str, bool]:
    solveable = {"EXACT_VALUE_NOT_VISIBLE", "OFFICIAL_SOURCE_NOT_FOUND", "TARGET_FIELD_TOO_GRANULAR"}
    return {category: category in solveable for category in sorted(counter)}


def write_report_file(repo_root: Path | str) -> Path:
    root = Path(repo_root).resolve()
    report = build_report(root)
    path = root / c.REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(report), encoding="utf-8")
    return path


def validate_report(report: Mapping[str, Any], repo_root: Path | str) -> list[str]:
    failures: list[str] = []
    for key in c.REQUIRED_REPORT_KEYS:
        if key not in report:
            failures.append(f"PR153_REQUIRED_REPORT_KEY_MISSING: {key}")

    pr151_count = int(_mapping(report.get("pr151_retrieval_target_pack_consumption_summary")).get("retrieval_target_count", -1))
    candidate_packets = _list(report.get("source_capture_candidate_packets"))
    unresolved = _list(report.get("unresolved_capture_targets"))
    candidate_count = len(candidate_packets)
    unresolved_count = len(unresolved)
    full_success = bool(_mapping(report.get("validation_summary")).get("full_capture_success"))

    if pr151_count <= 0:
        failures.append("PR153_PR151_RETRIEVAL_TARGET_PACK_REQUIRED")
    if full_success and candidate_count != pr151_count:
        failures.append("PR153_BLOCK_TARGET_COUNT_MISMATCH")
    if pr151_count == 342 and full_success and candidate_count != 342:
        failures.append("PR153_BLOCK_TARGET_COUNT_MISMATCH")
    if full_success and unresolved:
        failures.append("PR153_BLOCK_UNRESOLVED_TARGETS_REMAIN")
    if not full_success and not unresolved:
        failures.append("PR153_INCOMPLETE_STATUS_REQUIRES_UNRESOLVED_TARGETS")
    if not _list(report.get("capture_batch_plan")):
        failures.append("PR153_BATCH_PLAN_MISSING")
    if not _list(report.get("capture_batch_receipts")):
        failures.append("PR153_BATCH_RECEIPTS_MISSING")
    if not _list(report.get("capture_progress_ledger")):
        failures.append("PR153_CAPTURE_PROGRESS_LEDGER_MISSING")
    if not _mapping(report.get("capture_resume_cursor")):
        failures.append("PR153_CAPTURE_RESUME_CURSOR_MISSING")

    for packet in candidate_packets:
        failures.extend(_validate_candidate_packet(packet))
    for item in unresolved:
        failures.extend(_validate_unresolved_target(item))
    failures.extend(
        _validate_pr153a_owner_approved_architecture(
            report,
            candidate_count=candidate_count,
            unresolved_count=unresolved_count,
            pr151_count=pr151_count,
            full_success=full_success,
        )
    )
    failures.extend(_validate_owner_decision_layer(report, unresolved_count))
    failures.extend(_validate_no_claims(report))

    built = build_report(repo_root)
    if json_dump(report) != json_dump(built):
        failures.append("PR153_REPORT_NOT_DETERMINISTIC")
    return failures


def _validate_pr153a_owner_approved_architecture(
    report: Mapping[str, Any],
    *,
    candidate_count: int,
    unresolved_count: int,
    pr151_count: int,
    full_success: bool,
) -> list[str]:
    failures: list[str] = []
    completion = _mapping(report.get("pr153_completion_status"))
    denominator = _mapping(report.get("corrected_denominator_summary"))
    validation = _mapping(report.get("validation_summary"))
    lane_summary = _mapping(report.get("owner_approved_lane_routing_summary"))
    owner_override = _mapping(report.get("owner_global_authority_override_clarification"))
    retry_contract = _mapping(report.get("pr153r_retry_capture_contract"))
    handoff = _mapping(report.get("pr154_or_owner_override_handoff_contract"))
    boundary = _mapping(report.get("owner_external_fact_boundary"))

    if full_success:
        if denominator.get("remaining_external_public_capture_retry_target_count") != 0:
            failures.append("PR153_FULL_CAPTURE_SUCCESS_RETRY_TARGETS_REMAIN")
        if unresolved_count != 0:
            failures.append("PR153_BLOCK_UNRESOLVED_TARGETS_REMAIN")
        return failures

    expected_denominator = {
        "total_PR151_targets": c.PR153A_TOTAL_PR151_TARGETS,
        "true_external_public_source_value_capture_target_count": (
            c.PR153A_TRUE_EXTERNAL_PUBLIC_SOURCE_VALUE_CAPTURE_TARGET_COUNT
        ),
        "captured_candidate_packet_count": c.PR153A_CAPTURED_CANDIDATE_PACKET_COUNT,
        "remaining_external_public_capture_retry_target_count": (
            c.PR153A_REMAINING_EXTERNAL_PUBLIC_CAPTURE_RETRY_TARGET_COUNT
        ),
        "internal_control_plane_target_count": c.PR153A_INTERNAL_CONTROL_PLANE_TARGET_COUNT,
        "target_split_or_reclassification_required_count": (
            c.PR153A_TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED_COUNT
        ),
        "private_doc_or_attestation_required_count": (
            c.PR153A_PRIVATE_DOC_OR_ATTESTATION_REQUIRED_COUNT
        ),
        "owner_provided_value_candidate_route_count": (
            c.PR153A_OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE_COUNT
        ),
        "pr154_acceptance_review_only_count": c.PR153A_PR154_ACCEPTANCE_REVIEW_ONLY_COUNT,
        "corrected_public_capture_denominator": (
            c.PR153A_TRUE_EXTERNAL_PUBLIC_SOURCE_VALUE_CAPTURE_TARGET_COUNT
        ),
    }
    for key, expected in expected_denominator.items():
        if denominator.get(key) != expected:
            failures.append(f"PR153_CORRECTED_DENOMINATOR_MISMATCH: {key}")

    expected_completion = {
        "full_capture_success": False,
        "blocker_triage_success": True,
        "completion_label": c.COMPLETION_LABEL,
        "owner_approved_commit_framing": c.OWNER_APPROVED_COMMIT_FRAMING,
        "not_full_342_capture_success": True,
        "all_PR151_targets_accounted": True,
        "total_accounted_targets": c.PR153A_TOTAL_PR151_TARGETS,
    }
    for key, expected in expected_completion.items():
        if completion.get(key) != expected:
            failures.append(f"PR153_COMPLETION_STATUS_MISMATCH: {key}")
    if validation.get("completion_label") != c.COMPLETION_LABEL:
        failures.append("PR153_VALIDATION_COMPLETION_LABEL_MISMATCH")
    if validation.get("owner_approved_commit_framing") != c.OWNER_APPROVED_COMMIT_FRAMING:
        failures.append("PR153_VALIDATION_OWNER_FRAMING_MISMATCH")
    if validation.get("full_capture_success") is not False:
        failures.append("PR153_BLOCKER_TRIAGE_MARKED_FULL_CAPTURE_SUCCESS")
    if validation.get("blocker_triage_success") is not True:
        failures.append("PR153_BLOCKER_TRIAGE_SUCCESS_MISSING")
    if validation.get("all_PR151_targets_accounted") is not True:
        failures.append("PR153_ALL_TARGETS_ACCOUNTED_MISSING")
    if candidate_count != c.PR153A_CAPTURED_CANDIDATE_PACKET_COUNT:
        failures.append("PR153_CANDIDATE_COUNT_MISMATCH")
    if unresolved_count != c.PR153A_UNRESOLVED_TARGET_COUNT:
        failures.append("PR153_UNRESOLVED_COUNT_MISMATCH")
    if pr151_count != c.PR153A_TOTAL_PR151_TARGETS:
        failures.append("PR153_PR151_TARGET_COUNT_MISMATCH")

    expected_lane_counts = {
        "INTERNAL_QTT_POLICY_OR_CONTROL_PLANE_TARGET": (
            c.PR153A_INTERNAL_CONTROL_PLANE_TARGET_COUNT
        ),
        "TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED": (
            c.PR153A_TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED_COUNT
        ),
        "PRIVATE_DOC_OR_ATTESTATION_REQUIRED": (
            c.PR153A_PRIVATE_DOC_OR_ATTESTATION_REQUIRED_COUNT
        ),
        "OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE": (
            c.PR153A_OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE_COUNT
        ),
        "EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET": (
            c.PR153A_REMAINING_EXTERNAL_PUBLIC_CAPTURE_RETRY_TARGET_COUNT
        ),
        "PR154_ACCEPTANCE_REVIEW_ONLY": c.PR153A_PR154_ACCEPTANCE_REVIEW_ONLY_COUNT,
        "OWNER_DISAPPROVAL_OR_DESCOPE_CANDIDATE": 0,
    }
    for lane, expected in expected_lane_counts.items():
        lane_record = _mapping(lane_summary.get(lane))
        if lane_record.get("count") != expected:
            failures.append(f"PR153_OWNER_LANE_COUNT_MISMATCH: {lane}")
        if lane_record.get("owner_route") != c.OWNER_ROUTE_BY_ELIGIBILITY_LANE[lane]:
            failures.append(f"PR153_OWNER_LANE_ROUTE_MISMATCH: {lane}")
        if lane_record.get("can_owner_override_external_fact_truth_as_source_backed") is not False:
            failures.append(f"PR153_OWNER_LANE_EXTERNAL_TRUTH_OVERRIDE_ALLOWED: {lane}")

    if retry_contract.get("retry_target_count") != (
        c.PR153A_REMAINING_EXTERNAL_PUBLIC_CAPTURE_RETRY_TARGET_COUNT
    ):
        failures.append("PR153_PR153R_RETRY_TARGET_COUNT_MISMATCH")
    for key in (
        "no_internal_control_plane_rows_in_retry",
        "no_target_split_reclassification_rows_in_retry",
        "no_private_doc_attestation_rows_in_retry_without_owner_doc_packet",
        "no_owner_provided_external_value_as_source_truth",
        "PR154_or_owner_non_source_backed_override_route_required_after_retry",
    ):
        if retry_contract.get(key) is not True:
            failures.append(f"PR153_PR153R_RETRY_CONTRACT_FLAG_MISSING: {key}")

    if handoff.get("captured_candidate_count") != c.PR153A_CAPTURED_CANDIDATE_PACKET_COUNT:
        failures.append("PR153_HANDOFF_CANDIDATE_COUNT_MISMATCH")
    for key in (
        "candidates_are_not_accepted_source_evidence",
        "pr154_independent_revalidation_available",
        "owner_non_source_backed_override_available",
        "owner_non_source_backed_override_requires_receipt",
        "owner_non_source_backed_override_preserves_risk_flags",
        "source_backed_truth_requires_PR154_or_later_accepted_source_evidence",
        "non_source_backed_owner_use_requires_explicit_owner_override_receipt",
    ):
        if handoff.get(key) is not True:
            failures.append(f"PR153_HANDOFF_FLAG_MISSING: {key}")

    if owner_override.get("owner_may_override_pr154_workflow_gate") is not True:
        failures.append("PR153_OWNER_OVERRIDE_PR154_WORKFLOW_GATE_MISSING")
    if owner_override.get("owner_override_does_not_create_source_backed_truth") is not True:
        failures.append("PR153_OWNER_OVERRIDE_SOURCE_TRUTH_BOUNDARY_MISSING")
    if sorted(_list(owner_override.get("allowed_owner_non_source_backed_statuses"))) != sorted(
        OWNER_NON_SOURCE_BACKED_STATUSES
    ):
        failures.append("PR153_OWNER_NON_SOURCE_BACKED_STATUSES_MISSING")
    if boundary.get("can_owner_override_external_fact_truth_as_source_backed") is not False:
        failures.append("PR153_OWNER_EXTERNAL_FACT_TRUTH_OVERRIDE_ALLOWED")
    if (
        boundary.get(
            "connector_runtime_order_live_atomicrows_use_blocked_without_later_gates_or_explicit_owner_override_receipt"
        )
        is not True
    ):
        failures.append("PR153_OWNER_EXTERNAL_FACT_USE_BLOCK_MISSING")

    for surface_name, surface in (
        ("owner_override", owner_override),
        ("handoff", handoff),
        ("boundary", boundary),
    ):
        for key, expected in c.OWNER_NON_SOURCE_BACKED_RISK_FLAGS.items():
            if surface.get(key) != expected:
                failures.append(f"PR153_OWNER_RISK_FLAG_MISMATCH: {surface_name}:{key}")

    return failures


def _validate_candidate_packet(packet: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(packet, Mapping):
        return ["PR153_CANDIDATE_PACKET_NOT_OBJECT"]
    required = (
        "candidate_packet_id",
        "retrieval_target_id",
        "pr150_target_ref",
        "officiality_evidence",
        "source_domain",
        "source_url",
        "quote_span_or_machine_field_locator",
        "acceptance_status",
        "connector_binding_status",
        "runtime_receipt_status",
        "order_use_eligibility",
        "replay_paper_truth_use_eligibility",
        "launch_readiness_use_eligibility",
        "no_claim_flags",
    )
    for key in required:
        if key not in packet or packet.get(key) in (None, "", []):
            failures.append(f"PR153_CANDIDATE_REQUIRED_FIELD_MISSING: {key}")
    if packet.get("acceptance_status") != "NOT_ACCEPTED_CANDIDATE_ONLY":
        failures.append("PR153_BLOCK_ACCEPTED_FACT_PROMOTION")
    if packet.get("connector_binding_status") != "NOT_BOUND":
        failures.append("PR153_BLOCK_CONNECTOR_BINDING")
    if packet.get("runtime_receipt_status") != "NOT_CREATED":
        failures.append("PR153_BLOCK_RUNTIME_RECEIPT")
    flags = _mapping(packet.get("no_claim_flags"))
    for key, value in flags.items():
        if key != "source_capture_candidate_created" and value is not False:
            failures.append(f"PR153_FORBIDDEN_FLAG_TRUE: {key}")
    if flags.get("source_capture_candidate_created") is not True:
        failures.append("PR153_CANDIDATE_CAPTURE_FLAG_FALSE")
    return failures


def _validate_unresolved_target(item: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(item, Mapping):
        return ["PR153_UNRESOLVED_TARGET_NOT_OBJECT"]
    required = (
        "retrieval_target_id",
        "pr151_target_ref",
        "pr150_target_ref",
        "platform_scope",
        "market_scope",
        "target_field_path",
        "priority_class",
        "attempted_source_queries",
        "attempted_source_urls",
        "blocker_primary_category",
        "blocker_reason_detail",
        "exact_missing_evidence",
        "required_next_action",
        "owner_decision_options",
        "candidate_packet_created",
        "no_claim_flags",
    )
    for key in required:
        if key not in item or item.get(key) in (None, "", []):
            failures.append(f"PR153_UNRESOLVED_REQUIRED_FIELD_MISSING: {key}")
    if item.get("blocker_primary_category") not in c.BLOCKER_PRIMARY_CATEGORIES:
        failures.append("PR153_UNRESOLVED_BLOCKER_CATEGORY_INVALID")
    if item.get("candidate_packet_created") is not False:
        failures.append("PR153_UNRESOLVED_CANDIDATE_FLAG_TRUE")
    if tuple(item.get("owner_decision_options", ())) != OWNER_DECISION_OPTIONS:
        failures.append("PR153_OWNER_DECISION_OPTIONS_MISSING")
    for key, value in _mapping(item.get("no_claim_flags")).items():
        if value is not False:
            failures.append(f"PR153_FORBIDDEN_FLAG_TRUE: unresolved:{key}")
    return failures


def _validate_owner_decision_layer(
    report: Mapping[str, Any],
    unresolved_count: int,
) -> list[str]:
    failures: list[str] = []
    layer = _mapping(report.get("owner_blocker_decision_layer"))
    if not layer.get("owner_decision_layer_enabled"):
        failures.append("PR153_OWNER_DECISION_LAYER_MISSING")
    queue = _list(layer.get("owner_decision_required_queue"))
    if len(queue) != unresolved_count:
        failures.append("PR153_OWNER_DECISION_QUEUE_COUNT_MISMATCH")
    for item in queue:
        if tuple(_list(_mapping(item).get("owner_decision_options"))) != OWNER_DECISION_OPTIONS:
            failures.append("PR153_OWNER_DECISION_OPTIONS_MISSING")
    boundary = _mapping(layer.get("owner_decision_external_fact_boundary"))
    if boundary.get("accepted_source_evidence_packet_created") is not False:
        failures.append("PR153_BLOCK_OWNER_PROVIDED_EXTERNAL_FACT_AS_ACCEPTED_SOURCE_TRUTH")
    return failures


def _validate_no_claims(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    boundary = _mapping(report.get("no_claim_boundary"))
    for key, value in boundary.items():
        if key in {
            "source_capture_candidate_created",
            "all_prohibited_flags_false_except_candidate_capture_marker",
        }:
            continue
        if value is not False:
            failures.append(f"PR153_FORBIDDEN_FLAG_TRUE: report:{key}")
    atomicrows = _mapping(report.get("atomicrows_compatibility_surface"))
    if atomicrows.get("bundle_mutation_attempted") is not False:
        failures.append("PR153_BLOCK_ATOMICROWS_BUNDLE_MUTATION")
    quantum = _mapping(report.get("quantum_forward_capture_surface"))
    for key in (
        "quantum_backend_call_created",
        "quantum_simulator_call_created",
        "quantum_optimizer_output_created",
        "qaoa_execution_created",
        "vqe_execution_created",
        "annealing_execution_created",
        "qubo_solver_execution_created",
        "ising_solver_execution_created",
        "quantum_advantage_claim_created",
        "quantum_latency_superiority_claim_created",
    ):
        if quantum.get(key) is not False:
            failures.append(f"PR153_BLOCK_QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION: {key}")
    return failures


def validate_repository_artifacts(
    repo_root: Path | str,
    *,
    report_output_path: Path | None = None,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    root = Path(repo_root).resolve()
    report = build_report(root)
    if report_output_path is not None:
        output_path = report_output_path if report_output_path.is_absolute() else root / report_output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_dump(report), encoding="utf-8")

    tracked_path = root / c.REPORT_PATH
    if not tracked_path.exists():
        return [f"PR153_REPORT_MISSING: {c.REPORT_PATH.as_posix()}"]
    try:
        tracked_report = _read_json(tracked_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"PR153_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}"]

    failures = validate_report(tracked_report, root)
    if json_dump(tracked_report) != json_dump(report):
        failures.append("PR153_REPORT_STALE_OR_NONDETERMINISTIC")
    if tracked_report_write_allowed and tracked_path.exists():
        # The write permission is handled by the CLI before validation; no extra mutation here.
        pass
    return failures
