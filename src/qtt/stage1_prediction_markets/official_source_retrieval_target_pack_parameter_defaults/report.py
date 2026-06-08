"""Deterministic PR151 report builder and validator."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from tools.ci_branch_context import (
    current_branch_context,
    is_explicit_downstream_repair_changed_path,
    is_pr_or_later_branch,
    is_validation_infrastructure_changed_path,
)

from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
    constants as pr152_constants,
)

from . import constants as c


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


def _read_required_text(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> str:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR151_UPSTREAM_REPORT_MISSING: {key}: {rel_path.as_posix()}")
        return ""
    try:
        return _read_text(path)
    except OSError as exc:
        failures.append(
            f"PR151_UPSTREAM_REPORT_PARSE_ERROR: {key}: {rel_path.as_posix()}: {exc}"
        )
        return ""


def _read_required_json(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR151_UPSTREAM_REPORT_MISSING: {key}: {rel_path.as_posix()}")
        return {}
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(
            f"PR151_UPSTREAM_REPORT_PARSE_ERROR: {key}: {rel_path.as_posix()}: {exc}"
        )
        return {}


def _read_optional_payload(root: Path, rel_path: Path, failures: list[str]) -> Any:
    path = root / rel_path
    if not path.exists():
        return None
    if path.is_dir():
        return {"directory_file_names": sorted(child.name for child in path.iterdir())}
    if path.suffix == ".json":
        try:
            return _read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            failures.append(
                f"PR151_UPSTREAM_REPORT_PARSE_ERROR: optional: {rel_path.as_posix()}: {exc}"
            )
            return {}
    try:
        text = _read_text(path)
    except OSError as exc:
        failures.append(
            f"PR151_UPSTREAM_REPORT_PARSE_ERROR: optional: {rel_path.as_posix()}: {exc}"
        )
        return {}
    return {"line_count": len(text.splitlines()), "present": True}


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
            "PR151_UPSTREAM_REPORT_MISSING: pr136_section_crosswalk_or_alias: "
            f"{c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix()}"
        )
        return {}, {
            "alias_used": False,
            "canonical_successor_used": False,
            "created_missing_alias": False,
            "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
            "selected_path": c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix(),
        }
    payload = _read_required_json(root, "pr136_section_crosswalk_or_alias", selected, failures)
    return payload, {
        "alias_used": alias_exists,
        "canonical_successor_used": not alias_exists and canonical_exists,
        "created_missing_alias": False,
        "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
        "selected_path": selected.as_posix(),
    }


def _path_records(paths: Sequence[Path], present: set[str], required: bool) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "artifact_path": path.as_posix(),
                "consumed": path.as_posix() in present,
                "required": required,
            }
            for path in paths
        ),
        key=lambda item: item["artifact_path"],
    )


def _extract_assignment_values(text: str, key: str) -> list[str]:
    pattern = rf"^{re.escape(key)}\s*=\s*([A-Z0-9_]+(?:__[A-Z0-9_]+)*)\s*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return []
    return [part for part in match.group(1).split("__") if part]


def _extract_owner_source_policy(source_packet: str) -> dict[str, Any]:
    official = _extract_assignment_values(source_packet, "allowed_official_source_classes")
    blocked = _extract_assignment_values(source_packet, "non_authoritative_source_classes")
    domain_unset = (
        "official_domain_allowlist = OWNER_UNSET_PENDING_RETRIEVAL_DISCOVERY"
        in source_packet
        or "official_domain_allowlist_owner_unset_pending_retrieval_discovery = true"
        in source_packet
    )
    platform_scope_present = {
        platform: f"{platform}_retrieval_scope =" in source_packet
        for platform in c.VENUE_SCOPES
    }
    return {
        "allowed_official_source_classes": sorted(official),
        "domain_routes_owner_unset": domain_unset,
        "non_authoritative_source_classes": sorted(blocked),
        "platform_scope_present": platform_scope_present,
        "source_class_extraction_success": sorted(official) == sorted(c.OFFICIAL_SOURCE_CLASS_VALUES),
    }


def load_static_evidence(repo_root: Path | str) -> tuple[dict[str, Any], list[str]]:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    present: set[str] = set()

    text_payloads = {
        "launch_roadmap": _read_required_text(root, "launch_roadmap", c.ROADMAP_PATH, failures),
        "launch_roadmap_policy": _read_required_text(
            root,
            "launch_roadmap_policy",
            c.ROADMAP_POLICY_PATH,
            failures,
        ),
        "owner_source_evidence_packet": _read_required_text(
            root,
            "owner_source_evidence_packet",
            c.SOURCE_EVIDENCE_PACKET_PATH,
            failures,
        ),
    }
    for rel_path, text in (
        (c.ROADMAP_PATH, text_payloads["launch_roadmap"]),
        (c.ROADMAP_POLICY_PATH, text_payloads["launch_roadmap_policy"]),
        (c.SOURCE_EVIDENCE_PACKET_PATH, text_payloads["owner_source_evidence_packet"]),
    ):
        if text:
            present.add(rel_path.as_posix())

    json_payloads = {
        "control_plane_roster": _read_required_json(root, "control_plane_roster", c.ROSTER_PATH, failures),
        "control_plane_controller": _read_required_json(
            root,
            "control_plane_controller",
            c.CONTROLLER_PATH,
            failures,
        ),
        "pr136_route_triage": _read_required_json(
            root,
            "pr136_route_triage",
            c.PR136_ROUTE_TRIAGE_PATH,
            failures,
        ),
        "pr136_market_index": _read_required_json(
            root,
            "pr136_market_index",
            c.PR136_MARKET_INDEX_PATH,
            failures,
        ),
        "pr136_command_matrix": _read_required_json(
            root,
            "pr136_command_matrix",
            c.PR136_COMMAND_MATRIX_PATH,
            failures,
        ),
        "pr137r_reconciliation": _read_required_json(
            root,
            "pr137r_reconciliation",
            c.PR137R_REPORT_PATH,
            failures,
        ),
        "pr138_semantic_contract": _read_required_json(
            root,
            "pr138_semantic_contract",
            c.PR138_REPORT_PATH,
            failures,
        ),
        "pr149_bridge_report": _read_required_json(
            root,
            "pr149_bridge_report",
            c.PR149_REPORT_PATH,
            failures,
        ),
        "pr150_target_matrix": _read_required_json(
            root,
            "pr150_target_matrix",
            c.PR150_REPORT_PATH,
            failures,
        ),
    }
    json_path_by_key = {
        "control_plane_roster": c.ROSTER_PATH,
        "control_plane_controller": c.CONTROLLER_PATH,
        "pr136_route_triage": c.PR136_ROUTE_TRIAGE_PATH,
        "pr136_market_index": c.PR136_MARKET_INDEX_PATH,
        "pr136_command_matrix": c.PR136_COMMAND_MATRIX_PATH,
        "pr137r_reconciliation": c.PR137R_REPORT_PATH,
        "pr138_semantic_contract": c.PR138_REPORT_PATH,
        "pr149_bridge_report": c.PR149_REPORT_PATH,
        "pr150_target_matrix": c.PR150_REPORT_PATH,
    }
    for key, rel_path in json_path_by_key.items():
        if json_payloads[key]:
            present.add(rel_path.as_posix())

    crosswalk, alias_resolution = _crosswalk_payload(root, failures)
    json_payloads["pr136_section_crosswalk_or_alias"] = crosswalk
    if crosswalk:
        present.add(str(alias_resolution["selected_path"]))

    optional_payloads: dict[str, Any] = {}
    for rel_path in c.OPTIONAL_CONTEXT_ARTIFACTS:
        path = root / rel_path
        payload = _read_optional_payload(root, rel_path, failures)
        optional_payloads[rel_path.as_posix()] = payload
        if path.exists():
            present.add(rel_path.as_posix())

    if not text_payloads["owner_source_evidence_packet"]:
        failures.append(
            "PR151_OWNER_SOURCE_PACKET_REQUIRED: "
            f"{c.SOURCE_EVIDENCE_PACKET_PATH.as_posix()}"
        )
    owner_policy = _extract_owner_source_policy(text_payloads["owner_source_evidence_packet"])
    if not owner_policy["source_class_extraction_success"]:
        failures.append("PR151_OWNER_SOURCE_PACKET_REQUIRED: official_source_classes")

    return {
        "alias_resolution": alias_resolution,
        "json_payloads": json_payloads,
        "optional_payloads": optional_payloads,
        "owner_source_policy": owner_policy,
        "present_paths": present,
        "repo_root": root,
        "text_payloads": text_payloads,
    }, sorted(set(failures))


def _stable_token(*parts: str) -> str:
    raw = "_".join(str(part) for part in parts if part)
    return re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").upper()


def _target_field_id(item: Mapping[str, Any]) -> str:
    source_field = str(item.get("source_target_field_class") or "")
    if ":" in source_field:
        return source_field.split(":")[-1]
    return str(item.get("target_name") or item.get("target_domain") or "target_field")


def _platforms_for_item(item: Mapping[str, Any]) -> list[str]:
    scope = [str(value) for value in _list(item.get("market_scope"))]
    venues = [value for value in scope if value in c.VENUE_SCOPES]
    if venues:
        return sorted(set(venues))
    if "PREDICTION_MARKETS_GENERAL" in scope or not scope:
        return list(c.VENUE_SCOPES)
    return sorted(set(scope))


def _source_required_target_ids(pr150: Mapping[str, Any]) -> set[str]:
    explicit = {
        str(value)
        for value in _list(pr150.get("venue_source_required_targets"))
        if isinstance(value, str)
    }
    matrix = _mapping(pr150.get("parameter_default_target_matrix"))
    items = [
        item
        for item in _list(matrix.get("parameter_target_items"))
        if isinstance(item, Mapping)
    ]
    for item in items:
        target_id = str(item.get("target_id"))
        source_field = item.get("source_target_field_class")
        if item.get("value_authority_class") == "SOURCE_EVIDENCE_REQUIRED_VALUE":
            explicit.add(target_id)
        if item.get("default_target_state") in {
            "TARGET_DEFINED_VALUE_PENDING_SOURCE_EVIDENCE",
            "TARGET_BLOCKED_NO_SOURCE_AUTHORITY",
        }:
            explicit.add(target_id)
        if item.get("evidence_requirement_class") in {
            "OFFICIAL_SOURCE_EVIDENCE_REQUIRED",
            "ACCEPTED_SOURCE_EVIDENCE_REQUIRED",
        }:
            explicit.add(target_id)
        if source_field and item.get("value_authority_class") != "ACCEPTED_SOURCE_EVIDENCE_VALUE":
            explicit.add(target_id)
    return explicit


def _source_target_class(item: Mapping[str, Any]) -> str:
    domain = str(item.get("target_domain") or "")
    family = str(item.get("target_family_id") or "")
    name = str(item.get("target_name") or "")
    if domain in {"VENUE_FEE_RULES", "FEE_SETTLEMENT_COST_TARGET_FIELDS"}:
        return "FEE_RULE_SOURCE_TARGET"
    if domain in {"VENUE_TICK_RULES", "TICK_SIZE_TARGET_FIELDS"}:
        return "TICK_RULE_SOURCE_TARGET"
    if domain == "VENUE_PAYOUT_RULES":
        return "PAYOUT_RULE_SOURCE_TARGET"
    if domain in {"VENUE_SETTLEMENT_RULES", "VENUE_CASHFLOW_PNL_SEMANTICS"}:
        return "SETTLEMENT_RULE_SOURCE_TARGET"
    if domain == "VENUE_SDK_BEHAVIOR":
        return "SDK_BEHAVIOR_SOURCE_TARGET"
    if domain in {"VENUE_RATE_LIMITS", "RATE_LIMIT_TARGET_FIELDS"}:
        return "RATE_LIMIT_SOURCE_TARGET"
    if domain == "VENUE_ACCOUNT_PRIVATE_STATE_SEMANTICS" or "BALANCE" in domain:
        return "ACCOUNT_PRIVATE_STATE_SOURCE_TARGET"
    if domain == "VENUE_MARKET_DATA_SEMANTICS" or "MARKET_DATA" in domain:
        return "MARKET_DATA_SOURCE_TARGET"
    if "ORDERBOOK" in domain:
        if "SEQUENCING" in domain:
            return "ORDERBOOK_EVENT_SEQUENCE_SOURCE_TARGET"
        return "ORDERBOOK_FIELD_SOURCE_TARGET"
    if domain == "VENUE_EXECUTION_LIFECYCLE":
        return "EXECUTION_LIFECYCLE_SOURCE_TARGET"
    if domain == "VENUE_FILL_INTEGRITY":
        return "FILL_INTEGRITY_SOURCE_TARGET"
    if domain == "VENUE_LATENCY_COMPONENT_SEMANTICS" or "LATENCY" in domain:
        return "LATENCY_COMPONENT_SOURCE_TARGET"
    if domain == "VENUE_RECONCILIATION_SEMANTICS":
        return "RECONCILIATION_SOURCE_TARGET"
    if domain == "VENUE_CROSS_VENUE_NORMALIZATION_DEPENDENCIES":
        return "CROSS_VENUE_NORMALIZATION_SOURCE_TARGET"
    if domain == "VENUE_ORDER_FIELDS" or "ORDER" in domain or "PRICE" in domain:
        return "ORDER_FIELD_SOURCE_TARGET"
    if family == "RISK_CAPITAL_CONTROL":
        return "RISK_CAPITAL_SOURCE_TARGET"
    if family == "OPTIMIZER_PARAMETER" or "OPTIMIZER" in domain:
        return "OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET"
    if family == "QUANTUM_PARAMETER" or name.startswith(("qaoa", "vqe", "quantum")):
        return "QUANTUM_PROVIDER_DOC_SOURCE_TARGET"
    if family == "ATOMICROWS_COMPATIBILITY":
        return "ATOMICROWS_COMPATIBILITY_SOURCE_TARGET"
    if family == "CLASSICAL_STRATEGY_PARAMETER":
        return "CLASSICAL_STRATEGY_OFFICIAL_SEMANTICS_SOURCE_TARGET"
    if "STATUS" in domain:
        return "MARKET_STATUS_SOURCE_TARGET"
    if "EVENT" in domain:
        return "EVENT_LIFECYCLE_SOURCE_TARGET"
    return "VENUE_API_SOURCE_TARGET"


def _official_source_class(item: Mapping[str, Any], source_target_class: str) -> str:
    domain = str(item.get("target_domain") or "")
    if source_target_class in {"FEE_RULE_SOURCE_TARGET", "TICK_RULE_SOURCE_TARGET", "SETTLEMENT_RULE_SOURCE_TARGET"}:
        return "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS"
    if source_target_class == "PAYOUT_RULE_SOURCE_TARGET":
        return "OFFICIAL_RULEBOOKS"
    if source_target_class == "SDK_BEHAVIOR_SOURCE_TARGET":
        return "OFFICIAL_SDK_DOCS"
    if source_target_class in {"OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET", "QUANTUM_PROVIDER_DOC_SOURCE_TARGET"}:
        return "OFFICIAL_PROVIDER_DOCS"
    if source_target_class == "CLASSICAL_STRATEGY_OFFICIAL_SEMANTICS_SOURCE_TARGET":
        return "OFFICIAL_VENUE_DOCS"
    if "RULE" in domain:
        return "OFFICIAL_RULEBOOKS"
    return "OFFICIAL_API_DOCS"


def _downstream_consumer(item: Mapping[str, Any], source_target_class: str) -> str:
    family = str(item.get("target_family_id") or "")
    if family == "OPTIMIZER_PARAMETER":
        return "OPTIMIZER_PLANNING_METADATA_CONSUMER"
    if family == "QUANTUM_PARAMETER":
        return "QUANTUM_PLANNING_METADATA_CONSUMER"
    if family == "ATOMICROWS_COMPATIBILITY":
        return "ATOMICROWS_COMPATIBILITY_METADATA_CONSUMER"
    if family == "RISK_CAPITAL_CONTROL":
        return "RISK_CAPITAL_CONTROL_METADATA_CONSUMER"
    if source_target_class in {
        "ORDER_FIELD_SOURCE_TARGET",
        "EXECUTION_LIFECYCLE_SOURCE_TARGET",
        "LATENCY_COMPONENT_SOURCE_TARGET",
    }:
        return "EXECUTION_PLANNING_METADATA_CONSUMER"
    return "VENUE_SOURCE_EVIDENCE_TARGETING_CONSUMER"


def _revalidation_class(source_target_class: str) -> str:
    if source_target_class in {
        "OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET",
        "QUANTUM_PROVIDER_DOC_SOURCE_TARGET",
    }:
        return "PROVIDER_DOCS_EVENT_TRIGGERED"
    if source_target_class in {
        "FEE_RULE_SOURCE_TARGET",
        "TICK_RULE_SOURCE_TARGET",
        "SETTLEMENT_RULE_SOURCE_TARGET",
        "ACCOUNT_PRIVATE_STATE_SOURCE_TARGET",
        "EXECUTION_LIFECYCLE_SOURCE_TARGET",
        "FILL_INTEGRITY_SOURCE_TARGET",
        "LATENCY_COMPONENT_SOURCE_TARGET",
    }:
        return "LIVE_CRITICAL_P1D_AND_EVENT_TRIGGERED"
    return "LOW_RISK_P7D_AND_EVENT_TRIGGERED"


def _catalog_record(source_target_class: str) -> dict[str, Any]:
    source_class = "OFFICIAL_PROVIDER_DOCS"
    if source_target_class in {
        "FEE_RULE_SOURCE_TARGET",
        "TICK_RULE_SOURCE_TARGET",
        "SETTLEMENT_RULE_SOURCE_TARGET",
    }:
        source_class = "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS"
    elif source_target_class == "SDK_BEHAVIOR_SOURCE_TARGET":
        source_class = "OFFICIAL_SDK_DOCS"
    elif source_target_class == "PAYOUT_RULE_SOURCE_TARGET":
        source_class = "OFFICIAL_RULEBOOKS"
    elif source_target_class not in {
        "OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET",
        "QUANTUM_PROVIDER_DOC_SOURCE_TARGET",
    }:
        source_class = "OFFICIAL_API_DOCS"
    return {
        "acceptance_handoff_class": "FUTURE_PR153_ACCEPTANCE_REVIEW_REQUIRED",
        "conflict_policy_class": "MULTI_OFFICIAL_SOURCE_CONFLICT_REVIEW_REQUIRED",
        "future_capture_requirement": "CAPTURE_REQUIRES_FUTURE_PR",
        "official_source_class": source_class,
        "quote_span_requirement": "QUOTE_SPAN_REQUIRED",
        "revalidation_class": _revalidation_class(source_target_class),
        "source_locator_requirement": "QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR_REQUIRED",
        "source_target_class": source_target_class,
    }


def _queue_item(item: Mapping[str, Any], platform: str, owner_policy: Mapping[str, Any]) -> dict[str, Any]:
    source_target_class = _source_target_class(item)
    source_class = _official_source_class(item, source_target_class)
    target_field_id = _target_field_id(item)
    domain_slot = f"PR151_DOMAIN_SLOT__{platform}__{source_class}"
    target_path = ".".join(
        [
            "pr151",
            "target_fields",
            platform.lower(),
            str(item.get("target_family_id")).lower(),
            str(item.get("target_domain")).lower(),
            target_field_id.lower(),
        ]
    )
    target_id = str(item.get("target_id"))
    route_state = (
        "DOMAIN_ROUTE_PENDING_OWNER_APPROVAL"
        if owner_policy.get("domain_routes_owner_unset") is True
        else "DOMAIN_ROUTE_REQUIRED_FOR_FUTURE_RETRIEVAL"
    )
    reason_codes = sorted(
        {
            "PR151_ACCEPTANCE_HANDOFF_REQUIRED",
            "PR151_CONFLICT_POLICY_REQUIRED",
            "PR151_DOMAIN_ROUTE_PENDING_OWNER_APPROVAL",
            "PR151_NOT_RETRIEVED_TARGET_ONLY",
            "PR151_NO_BUNDLE_MUTATION_AUTHORITY",
            "PR151_NO_CONNECTOR_VALUE",
            "PR151_NO_DOMAIN_INVENTION",
            "PR151_NO_FACT_ACCEPTANCE",
            "PR151_NO_NETWORK_EXECUTION",
            "PR151_NO_ORDER_AUTHORITY",
            "PR151_NO_QTT_INTEGRITY_AUTHORITY",
            "PR151_NO_RUNTIME_RECEIPT",
            "PR151_NO_VALUE_INVENTION",
            "PR151_OFFICIAL_SOURCE_CLASS_READY",
            "PR151_QUOTE_OR_MACHINE_LOCATOR_REQUIRED",
            "PR151_READY",
            "PR151_REVALIDATION_POLICY_REQUIRED",
            "PR151_SOURCE_LOCATOR_REQUIRED",
            "PR151_SOURCE_REQUIRED_TARGET_FOUND",
        }
    )
    quantum_dependency = (
        c.QUANTUM_FORWARD_STATE
        if source_target_class == "QUANTUM_PROVIDER_DOC_SOURCE_TARGET"
        else None
    )
    return {
        "accepted_value_state": "NOT_ACCEPTED_TARGET_ONLY",
        "acceptance_handoff_class": "FUTURE_PR153_ACCEPTANCE_REVIEW_REQUIRED",
        "atomicrows_materialization_dependency": {
            "no_bundle_mutation_dependency": True,
            "pr137r_reference_required": True,
            "pr138_semantic_field_reference_required": True,
            "pr149_materialization_reference_required": True,
        },
        "conflict_policy_class": "MULTI_OFFICIAL_SOURCE_CONFLICT_REVIEW_REQUIRED",
        "connector_unlock_dependency": {
            "accepted_value_required_before_unlock": True,
            "connector_value_created": False,
        },
        "downstream_acceptance_target": f"PR153_TARGET_FIELD_ACCEPTANCE::{target_field_id}",
        "future_capture_requirement": "CAPTURE_REQUIRES_FUTURE_PR",
        "machine_field_locator_requirement": "MACHINE_FIELD_LOCATOR_REQUIRED",
        "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
        "official_source_class": source_class,
        "official_source_domain_slot": domain_slot,
        "order_use_eligibility": "NOT_ORDER_USABLE_RETRIEVAL_TARGET_ONLY",
        "owner_approved_domain_route": None,
        "owner_domain_route_state": route_state,
        "pr150_target_domain": str(item.get("target_domain")),
        "pr150_target_id": target_id,
        "pr150_target_name": str(item.get("target_name")),
        "quantum_forward_dependency": quantum_dependency,
        "queue_state": "TARGET_DECLARED_DOMAIN_SLOT_PENDING_OWNER_APPROVAL",
        "quote_span_requirement": "QUOTE_SPAN_REQUIRED",
        "reason_codes": reason_codes,
        "retrieval_method_policy": "FUTURE_RETRIEVAL_PR_REQUIRED",
        "retrieval_target_id": "PR151_" + _stable_token(target_id, platform, source_class, target_field_id),
        "revalidation_class": _revalidation_class(source_target_class),
        "source_locator_requirement": "QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR_REQUIRED",
        "source_target_class": source_target_class,
        "target_field_id": target_field_id,
        "target_field_path": target_path,
        "target_market_scope": platform,
        "target_platform_scope": platform,
        "value_capture_state": "BLOCKED_PENDING_DOMAIN_ROUTE",
    }


def _build_queue(pr150: Mapping[str, Any], owner_policy: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    matrix = _mapping(pr150.get("parameter_default_target_matrix"))
    raw_items = [
        item
        for item in _list(matrix.get("parameter_target_items"))
        if isinstance(item, Mapping)
    ]
    eligible_ids = _source_required_target_ids(pr150)
    queue: list[dict[str, Any]] = []
    for item in raw_items:
        if str(item.get("target_id")) not in eligible_ids:
            continue
        for platform in _platforms_for_item(item):
            queue.append(_queue_item(item, platform, owner_policy))
    return sorted(queue, key=lambda row: row["retrieval_target_id"]), sorted(eligible_ids)


def _counter(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _index(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for row in rows:
        result.setdefault(str(row.get(key)), []).append(str(row.get("retrieval_target_id")))
    return {name: sorted(values) for name, values in sorted(result.items())}


def _build_payload(evidence: Mapping[str, Any]) -> dict[str, Any]:
    present = set(evidence["present_paths"])
    json_payloads = _mapping(evidence["json_payloads"])
    pr136_route = _mapping(json_payloads.get("pr136_route_triage"))
    pr136_market = _mapping(json_payloads.get("pr136_market_index"))
    pr136_command = _mapping(json_payloads.get("pr136_command_matrix"))
    pr137r = _mapping(json_payloads.get("pr137r_reconciliation"))
    pr138 = _mapping(json_payloads.get("pr138_semantic_contract"))
    pr149 = _mapping(json_payloads.get("pr149_bridge_report"))
    pr150 = _mapping(json_payloads.get("pr150_target_matrix"))
    owner_policy = _mapping(evidence.get("owner_source_policy"))
    queue, eligible_ids = _build_queue(pr150, owner_policy)
    excluded: list[dict[str, Any]] = []
    covered_ids = sorted({row["pr150_target_id"] for row in queue})
    catalog = sorted(
        (
            _catalog_record(source_target_class)
            for source_target_class in {row["source_target_class"] for row in queue}
        ),
        key=lambda row: row["source_target_class"],
    )
    platform_index = {
        platform: sorted(
            row["retrieval_target_id"]
            for row in queue
            if row["target_platform_scope"] == platform
        )
        for platform in c.VENUE_SCOPES
    }
    return {
        "acceptance_handoff_index": _index(queue, "acceptance_handoff_class"),
        "atomicrows_compatibility_surface": {
            "bundle_mutation_required": False,
            "future_materialization_dependency_target_count": len(queue),
            "pr137r_reference_present": bool(pr137r),
            "pr138_reference_present": bool(pr138),
            "pr149_reference_present": bool(pr149),
        },
        "authority_class": c.AUTHORITY_CLASS,
        "centralized_reason_codes": list(c.REASON_CODES),
        "centralized_state_enums": {
            "accepted_value_state": list(c.ACCEPTED_VALUE_STATE_VALUES),
            "acceptance_handoff_class": list(c.ACCEPTANCE_HANDOFF_CLASS_VALUES),
            "conflict_policy_class": list(c.CONFLICT_POLICY_CLASS_VALUES),
            "domain_route_state": list(c.DOMAIN_ROUTE_STATE_VALUES),
            "downstream_consumer_class": list(c.DOWNSTREAM_CONSUMER_CLASS_VALUES),
            "locator_requirement_class": list(c.LOCATOR_REQUIREMENT_CLASS_VALUES),
            "official_source_class": list(c.OFFICIAL_SOURCE_CLASS_VALUES),
            "order_use_eligibility": list(c.ORDER_USE_ELIGIBILITY_VALUES),
            "retrieval_method_policy": list(c.RETRIEVAL_METHOD_POLICY_VALUES),
            "revalidation_class": list(c.REVALIDATION_CLASS_VALUES),
            "source_target_class": list(c.SOURCE_TARGET_CLASS_VALUES),
            "target_queue_state": list(c.TARGET_QUEUE_STATE_VALUES),
            "value_capture_state": list(c.VALUE_CAPTURE_STATE_VALUES),
        },
        "conflict_policy_index": _index(queue, "conflict_policy_class"),
        "deterministic_generation_policy": {
            "array_sort_key": "retrieval_target_id",
            "dictionary_keys_sorted": True,
            "local_paths_excluded": True,
            "stable_id_parts": [
                "pr150_target_id",
                "target_platform_scope",
                "official_source_class",
                "target_field_id",
            ],
            "wall_clock_time_used": False,
        },
        "future_pr152_capture_handoff_contract": {
            "accepted_value_state_required_before_pr153": "NOT_ACCEPTED_TARGET_ONLY",
            "handoff_input_queue": "official_source_retrieval_target_queue",
            "required_locator_classes": sorted(set(row["source_locator_requirement"] for row in queue)),
            "value_capture_state": "CAPTURE_REQUIRES_FUTURE_PR",
        },
        "future_pr153_acceptance_handoff_contract": {
            "accepted_value_state_before_pr153": "NOT_ACCEPTED_TARGET_ONLY",
            "conflict_review_required": True,
            "downstream_acceptance_targets": sorted(
                set(row["downstream_acceptance_target"] for row in queue)
            ),
        },
        "intentionally_excluded_pr150_source_targets": excluded,
        "network_code_absence_summary": {
            "network_retrieval_executed": False,
            "pr151_added_files_structural_scan_required": True,
            "retrieval_capable_code_created": False,
        },
        "next_consumer_contract": {
            "consumer": "PR152_OFFICIAL_SOURCE_CAPTURE_TARGET_CONSUMER",
            "input_queue_key": "official_source_retrieval_target_queue",
            "must_preserve_no_claim_flags": True,
            "must_use_symbolic_domain_slots_until_route_approval": True,
        },
        "no_claim_boundary": dict(c.NO_CLAIM_FLAGS),
        "official_source_retrieval_target_queue": queue,
        "optional_context_inputs": _path_records(c.OPTIONAL_CONTEXT_ARTIFACTS, present, False),
        "orchestration_preflight_receipt": {
            "alias_resolution": evidence["alias_resolution"],
            "all_required_inputs_consumed": all(path.as_posix() in present for path in c.REQUIRED_UPSTREAM_ARTIFACTS),
            "owner_source_packet_consumed": c.SOURCE_EVIDENCE_PACKET_PATH.as_posix() in present,
            "pr149_bridge_consumed": bool(pr149),
            "pr150_target_matrix_consumed": bool(pr150),
        },
        "owner_source_evidence_packet_summary": {
            "allowed_official_source_classes": owner_policy.get("allowed_official_source_classes", []),
            "domain_routes_owner_unset": owner_policy.get("domain_routes_owner_unset"),
            "non_authoritative_source_classes": owner_policy.get("non_authoritative_source_classes", []),
            "platform_scope_present": owner_policy.get("platform_scope_present", {}),
        },
        "platform_source_target_index": platform_index,
        "pr136_alignment_summary": {
            "command_action_count": len(_list(pr136_command.get("actions"))),
            "market_scope_count": len(_list(pr136_market.get("market_scopes"))),
            "route_receipt_type": pr136_route.get("receipt_type"),
            "section_crosswalk_alias_resolution": evidence["alias_resolution"],
        },
        "pr137r_alignment_summary": {
            "report_id": pr137r.get("report_id"),
            "row_count_proven": _mapping(pr137r.get("atomicrows_validation_state")).get(
                "row_count_proven"
            ),
        },
        "pr138_semantic_contract_summary": {
            "field_count": pr138.get("required_field_count"),
            "report_id": pr138.get("report_id"),
        },
        "pr149_bridge_consumption_summary": {
            "report_id": pr149.get("report_id"),
            "semantic_item_count": _mapping(pr149.get("implementation_bridge_summary")).get(
                "semantic_item_count"
            ),
        },
        "pr150_parameter_target_matrix_consumption_summary": {
            "eligible_pr150_target_count": len(eligible_ids),
            "parameter_target_item_count": _mapping(
                pr150.get("parameter_default_target_matrix")
            ).get("target_count"),
            "report_id": pr150.get("report_id"),
            "source_required_authority_count": len(
                [
                    item
                    for item in _list(
                        _mapping(pr150.get("parameter_default_target_matrix")).get(
                            "parameter_target_items"
                        )
                    )
                    if isinstance(item, Mapping)
                    and item.get("value_authority_class") == "SOURCE_EVIDENCE_REQUIRED_VALUE"
                ]
            ),
        },
        "pr150_source_target_coverage_summary": {
            "covered_pr150_target_ids": covered_ids,
            "eligible_pr150_target_count": len(eligible_ids),
            "eligible_pr150_target_ids": eligible_ids,
            "queue_item_count": len(queue),
            "queue_item_count_by_official_source_class": _counter(queue, "official_source_class"),
            "queue_item_count_by_platform": _counter(queue, "target_platform_scope"),
            "queue_item_count_by_source_target_class": _counter(queue, "source_target_class"),
            "typed_exclusion_count": len(excluded),
        },
        "pr_id": c.PR_ID,
        "pr_title": c.PR_TITLE,
        "quantum_forward_source_target_surface": {
            "provider_documentation_target_count": len(
                [
                    row
                    for row in queue
                    if row["source_target_class"] == "QUANTUM_PROVIDER_DOC_SOURCE_TARGET"
                ]
            ),
            "quantum_forward_state": c.QUANTUM_FORWARD_STATE,
            "quantum_output_created": False,
        },
        "readiness_class": c.READINESS_CLASS,
        "report_id": c.REPORT_ID,
        "report_version": c.REPORT_VERSION,
        "revalidation_policy_index": _index(queue, "revalidation_class"),
        "source_authority_boundary_summary": {
            "authoritative_source_classes": owner_policy.get("allowed_official_source_classes", []),
            "non_authoritative_source_classes_blocked": owner_policy.get(
                "non_authoritative_source_classes",
                [],
            ),
            "official_domain_invented": False,
            "official_value_invented": False,
        },
        "source_class_extraction_receipt": {
            "extracted_from_owner_packet": True,
            "extracted_official_source_classes": owner_policy.get(
                "allowed_official_source_classes",
                [],
            ),
            "matches_constant_surface": owner_policy.get("source_class_extraction_success"),
        },
        "source_locator_requirement_index": _index(queue, "source_locator_requirement"),
        "source_retrieval_target_class_catalog": catalog,
        "target_field_path_index": _index(queue, "target_field_path"),
        "upstream_artifact_inputs": _path_records(c.REQUIRED_UPSTREAM_ARTIFACTS, present, True),
        "validation_summary": {
            "build_report_byte_stable": True,
            "default_validation_mutates_tracked_report": False,
            "explicit_report_write_mode_supported": True,
            "normal_full_gate_integration_is_non_mutating": True,
            "tracked_report_path": c.REPORT_PATH.as_posix(),
        },
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    evidence, failures = load_static_evidence(repo_root)
    if failures:
        raise ValueError("\n".join(failures))
    return _build_payload(evidence)


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _is_path_like_key(key: str) -> bool:
    return (
        key == "artifact_path"
        or key.endswith("_path")
        or key.endswith("_paths")
        or key.endswith("_ref")
        or key.endswith("_refs")
    )


def _forbidden_bundle_sidecar_path() -> str:
    return c.ATOMICROWS_BUNDLE_PATH.with_suffix("." + "sha" + "256").as_posix()


def _contains_exact(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return value.replace("\\", "/") == needle
    if isinstance(value, list):
        return any(_contains_exact(item, needle) for item in value)
    return False


def _path_and_authority_failures(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    forbidden_sidecar = _forbidden_bundle_sidecar_path()
    for key, value in _walk(payload):
        lowered = key.lower()
        if lowered.endswith(("_" + "di" + "gest", "_" + "check" + "sum", "_hash")):
            failures.append("PR151_QTT_INTEGRITY_AUTHORITY_DETECTED")
        if "integrity_authority" in lowered and value is not False:
            failures.append("PR151_QTT_INTEGRITY_AUTHORITY_DETECTED")
        if _is_path_like_key(key) and _contains_exact(value, forbidden_sidecar):
            failures.append("PR151_ATOMICROWS_SIDECAR_REFERENCE_DETECTED")
        if isinstance(value, str) and re.search(r"[A-Za-z]:[\\/]", value):
            failures.append("PR151_LOCAL_PATH_FORBIDDEN")
    return sorted(set(failures))


def _false_flag_failures(payload: Mapping[str, Any]) -> list[str]:
    flags = _mapping(payload.get("no_claim_boundary"))
    failures: list[str] = []
    if dict(flags) != c.NO_CLAIM_FLAGS:
        failures.append("PR151_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED")
    for key, value in flags.items():
        if value is not False:
            failures.append(f"PR151_FORBIDDEN_FLAG_TRUE: {key}")
    return failures


def _url_like(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in ("://", "www.", ".com", "/api/", "/docs/"))


def _value_creation_failures(row: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    key_to_failure = {
        "accepted_value": "PR151_ACCEPTED_VALUE_CREATED",
        "captured_value": "PR151_CAPTURED_VALUE_CREATED",
        "connector_semantic_value": "PR151_CONNECTOR_VALUE_CREATED",
        "external_fact_value": "PR151_CAPTURED_VALUE_CREATED",
        "optimizer_output_value": "PR151_QUANTUM_OUTPUT_VALUE_CREATED",
        "quantum_output_value": "PR151_QUANTUM_OUTPUT_VALUE_CREATED",
        "replay_paper_result_value": "PR151_REPLAY_PAPER_RESULT_VALUE_CREATED",
        "runtime_receipt_value": "PR151_RUNTIME_RECEIPT_VALUE_CREATED",
    }
    for key, failure in key_to_failure.items():
        if key in row and row.get(key) not in (None, False, "", [], {}):
            failures.append(failure)
    if row.get("order_use_eligibility") == "ORDER_USABLE":
        failures.append("PR151_ORDER_USABLE_CREATED")
    return failures


def _validate_queue_item(row: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    row_id = str(row.get("retrieval_target_id") or "missing_id")
    for key in c.QUEUE_ITEM_REQUIRED_FIELDS:
        if key not in row:
            failures.append(f"PR151_QUEUE_ITEM_SCHEMA_INVALID: {row_id}: {key}")
    enum_checks = {
        "accepted_value_state": c.ACCEPTED_VALUE_STATE_VALUES,
        "acceptance_handoff_class": c.ACCEPTANCE_HANDOFF_CLASS_VALUES,
        "conflict_policy_class": c.CONFLICT_POLICY_CLASS_VALUES,
        "official_source_class": c.OFFICIAL_SOURCE_CLASS_VALUES,
        "order_use_eligibility": c.ORDER_USE_ELIGIBILITY_VALUES,
        "owner_domain_route_state": c.DOMAIN_ROUTE_STATE_VALUES,
        "queue_state": c.TARGET_QUEUE_STATE_VALUES,
        "retrieval_method_policy": c.RETRIEVAL_METHOD_POLICY_VALUES,
        "revalidation_class": c.REVALIDATION_CLASS_VALUES,
        "source_locator_requirement": c.LOCATOR_REQUIREMENT_CLASS_VALUES,
        "value_capture_state": c.VALUE_CAPTURE_STATE_VALUES,
    }
    for key, allowed in enum_checks.items():
        if row.get(key) not in allowed:
            failures.append(f"PR151_QUEUE_ENUM_INVALID: {row_id}: {key}")
    if row.get("source_target_class") not in c.SOURCE_TARGET_CLASS_VALUES:
        failures.append(f"PR151_QUEUE_ENUM_INVALID: {row_id}: source_target_class")
    if row.get("official_source_class") in c.NON_AUTHORITATIVE_SOURCE_CLASS_VALUES:
        failures.append("PR151_NON_AUTHORITATIVE_SOURCE_CLASS_BLOCKED")
    for reason in _list(row.get("reason_codes")):
        if reason not in c.REASON_CODES:
            failures.append(f"PR151_REASON_CODE_INVALID: {reason}")
    if _mapping(row.get("no_claim_flags")) != c.NO_CLAIM_FLAGS:
        failures.append(f"PR151_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED: {row_id}")
    if row.get("owner_approved_domain_route") is not None:
        failures.append("PR151_DOMAIN_ROUTE_INVENTED")
    for key in ("official_source_domain_slot", "owner_approved_domain_route", "target_field_path"):
        value = row.get(key)
        if isinstance(value, str) and _url_like(value):
            failures.append("PR151_NO_DOMAIN_INVENTION")
    if str(row.get("official_source_domain_slot", "")).startswith("PR151_DOMAIN_SLOT__") is False:
        failures.append(f"PR151_QUEUE_ITEM_SCHEMA_INVALID: {row_id}: official_source_domain_slot")
    if row.get("accepted_value_state") not in {
        "NOT_ACCEPTED_TARGET_ONLY",
        "ACCEPTANCE_REQUIRES_FUTURE_PR",
        "ACCEPTANCE_BLOCKED_PENDING_CAPTURE",
        "ACCEPTANCE_BLOCKED_PENDING_CONFLICT_REVIEW",
        "ACCEPTANCE_BLOCKED_PENDING_OWNER_REVIEW",
    }:
        failures.append("PR151_ACCEPTED_VALUE_CREATED")
    if row.get("value_capture_state") not in c.VALUE_CAPTURE_STATE_VALUES:
        failures.append("PR151_CAPTURED_VALUE_CREATED")
    failures.extend(_value_creation_failures(row))
    return failures


def _coverage_failures(payload: Mapping[str, Any]) -> list[str]:
    coverage = _mapping(payload.get("pr150_source_target_coverage_summary"))
    eligible = set(str(value) for value in _list(coverage.get("eligible_pr150_target_ids")))
    queue = [
        row
        for row in _list(payload.get("official_source_retrieval_target_queue"))
        if isinstance(row, Mapping)
    ]
    queued = {str(row.get("pr150_target_id")) for row in queue}
    excluded = {
        str(row.get("pr150_target_id"))
        for row in _list(payload.get("intentionally_excluded_pr150_source_targets"))
        if isinstance(row, Mapping)
    }
    missing = eligible - queued - excluded
    if missing:
        return [f"PR151_PR150_SOURCE_TARGET_COVERAGE_REQUIRED: {target_id}" for target_id in sorted(missing)]
    return []


def validate_report_payload(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    required_top_level = (
        "report_id",
        "report_version",
        "pr_id",
        "pr_title",
        "authority_class",
        "readiness_class",
        "deterministic_generation_policy",
        "upstream_artifact_inputs",
        "optional_context_inputs",
        "orchestration_preflight_receipt",
        "pr136_alignment_summary",
        "pr137r_alignment_summary",
        "pr138_semantic_contract_summary",
        "pr149_bridge_consumption_summary",
        "pr150_parameter_target_matrix_consumption_summary",
        "owner_source_evidence_packet_summary",
        "source_class_extraction_receipt",
        "source_authority_boundary_summary",
        "source_retrieval_target_class_catalog",
        "official_source_retrieval_target_queue",
        "intentionally_excluded_pr150_source_targets",
        "pr150_source_target_coverage_summary",
        "platform_source_target_index",
        "target_field_path_index",
        "source_locator_requirement_index",
        "conflict_policy_index",
        "revalidation_policy_index",
        "acceptance_handoff_index",
        "future_pr152_capture_handoff_contract",
        "future_pr153_acceptance_handoff_contract",
        "atomicrows_compatibility_surface",
        "quantum_forward_source_target_surface",
        "network_code_absence_summary",
        "no_claim_boundary",
        "centralized_reason_codes",
        "validation_summary",
        "next_consumer_contract",
    )
    for key in required_top_level:
        if key not in payload:
            failures.append(f"PR151_REQUIRED_REPORT_KEY_MISSING: {key}")
    if payload.get("report_id") != c.REPORT_ID:
        failures.append("PR151_REPORT_ID_MISMATCH")
    if payload.get("report_version") != c.REPORT_VERSION:
        failures.append("PR151_REPORT_VERSION_MISMATCH")
    if payload.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append("PR151_AUTHORITY_CLASS_MISMATCH")
    if payload.get("readiness_class") != c.READINESS_CLASS:
        failures.append("PR151_READINESS_CLASS_MISMATCH")
    if payload.get("centralized_reason_codes") != list(c.REASON_CODES):
        failures.append("PR151_ENUMS_NOT_CONSTANT_ALIGNED")
    expected_enums = {
        "accepted_value_state": list(c.ACCEPTED_VALUE_STATE_VALUES),
        "acceptance_handoff_class": list(c.ACCEPTANCE_HANDOFF_CLASS_VALUES),
        "conflict_policy_class": list(c.CONFLICT_POLICY_CLASS_VALUES),
        "domain_route_state": list(c.DOMAIN_ROUTE_STATE_VALUES),
        "downstream_consumer_class": list(c.DOWNSTREAM_CONSUMER_CLASS_VALUES),
        "locator_requirement_class": list(c.LOCATOR_REQUIREMENT_CLASS_VALUES),
        "official_source_class": list(c.OFFICIAL_SOURCE_CLASS_VALUES),
        "order_use_eligibility": list(c.ORDER_USE_ELIGIBILITY_VALUES),
        "retrieval_method_policy": list(c.RETRIEVAL_METHOD_POLICY_VALUES),
        "revalidation_class": list(c.REVALIDATION_CLASS_VALUES),
        "source_target_class": list(c.SOURCE_TARGET_CLASS_VALUES),
        "target_queue_state": list(c.TARGET_QUEUE_STATE_VALUES),
        "value_capture_state": list(c.VALUE_CAPTURE_STATE_VALUES),
    }
    if _mapping(payload.get("centralized_state_enums")) != expected_enums:
        failures.append("PR151_ENUMS_NOT_CONSTANT_ALIGNED")
    failures.extend(_false_flag_failures(payload))
    failures.extend(_path_and_authority_failures(payload))

    preflight = _mapping(payload.get("orchestration_preflight_receipt"))
    if preflight.get("all_required_inputs_consumed") is not True:
        failures.append("PR151_PR136_ORCHESTRATION_REQUIRED")
    if preflight.get("owner_source_packet_consumed") is not True:
        failures.append("PR151_OWNER_SOURCE_PACKET_REQUIRED")
    if preflight.get("pr149_bridge_consumed") is not True:
        failures.append("PR151_PR149_BRIDGE_REQUIRED")
    if preflight.get("pr150_target_matrix_consumed") is not True:
        failures.append("PR151_PR150_TARGET_MATRIX_REQUIRED")
    if _mapping(payload.get("pr136_alignment_summary")).get("route_receipt_type") != (
        "PR136_ROUTE_TRIAGE_RECEIPT"
    ):
        failures.append("PR151_PR136_ORCHESTRATION_REQUIRED")
    if _mapping(payload.get("pr137r_alignment_summary")).get("row_count_proven") is not True:
        failures.append("PR151_PR137R_RECONCILIATION_REQUIRED")
    if _mapping(payload.get("pr138_semantic_contract_summary")).get("field_count") != 59:
        failures.append("PR151_PR138_SEMANTIC_CONTRACT_REQUIRED")
    if not _mapping(payload.get("pr149_bridge_consumption_summary")).get("report_id"):
        failures.append("PR151_PR149_BRIDGE_REQUIRED")
    if not _mapping(payload.get("pr150_parameter_target_matrix_consumption_summary")).get("report_id"):
        failures.append("PR151_PR150_TARGET_MATRIX_REQUIRED")
    if _mapping(payload.get("source_class_extraction_receipt")).get("matches_constant_surface") is not True:
        failures.append("PR151_OWNER_SOURCE_PACKET_REQUIRED")

    queue = [
        row
        for row in _list(payload.get("official_source_retrieval_target_queue"))
        if isinstance(row, Mapping)
    ]
    if not queue:
        failures.append("PR151_QUEUE_ITEMS_MISSING")
    ids = [str(row.get("retrieval_target_id")) for row in queue]
    if ids != sorted(ids):
        failures.append("PR151_QUEUE_ITEMS_NOT_SORTED")
    if len(ids) != len(set(ids)):
        failures.append("PR151_QUEUE_ITEM_DUPLICATE")
    for row in queue:
        failures.extend(_validate_queue_item(row))
    failures.extend(_coverage_failures(payload))

    coverage = _mapping(payload.get("pr150_source_target_coverage_summary"))
    if coverage.get("queue_item_count") != len(queue):
        failures.append("PR151_PR150_SOURCE_TARGET_COVERAGE_REQUIRED")
    if coverage.get("typed_exclusion_count") != len(
        _list(payload.get("intentionally_excluded_pr150_source_targets"))
    ):
        failures.append("PR151_PR150_SOURCE_TARGET_COVERAGE_REQUIRED")
    return sorted(set(failures))


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _changed_paths(repo_root: Path) -> list[str]:
    status_rc, status_out, _status_err = _git_stdout(
        repo_root,
        ["status", "--short", "--untracked-files=all"],
    )
    if status_rc != 0:
        return ["<git-status-unavailable>"]
    paths: list[str] = []
    for line in status_out.splitlines():
        if not line.strip():
            continue
        if len(line) > 2 and line[2] == " ":
            path = line[3:]
        elif len(line) > 1 and line[1] == " ":
            path = line[2:]
        else:
            path = line[3:] if len(line) > 3 else line
        normalized = path.strip().replace("\\", "/")
        if " -> " in normalized:
            normalized = normalized.rsplit(" -> ", 1)[1]
        paths.append(normalized)
    return sorted(set(paths))


def _branch_allows_pr151_changed_paths(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        151,
        allow_main=False,
        allow_repair=False,
    )


def _branch_allows_explicit_pr151_tracked_report_write(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        151,
        allow_main=True,
        allow_repair=False,
    )


def _branch_allows_pr152_audit_changed_paths(branch: str) -> bool:
    return is_pr_or_later_branch(
        branch,
        152,
        allow_main=False,
        allow_repair=False,
    )


def _is_pr152_audit_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in pr152_constants.PR152_AUDIT_CHANGED_PATHS
        and _branch_allows_pr152_audit_changed_paths(branch)
    )


def _is_allowed_pr151_changed_path_for_branch(
    path: str,
    branch: str,
    *,
    tracked_report_write_allowed: bool = False,
) -> bool:
    normalized = path.replace("\\", "/")
    if normalized == ".tmp" or normalized.startswith(".tmp/"):
        return True
    if (
        tracked_report_write_allowed
        and normalized == c.REPORT_PATH.as_posix()
        and _branch_allows_explicit_pr151_tracked_report_write(branch)
    ):
        return True
    if _is_pr152_audit_changed_path_for_branch(normalized, branch):
        return True
    if is_explicit_downstream_repair_changed_path(branch, normalized):
        return True
    if is_validation_infrastructure_changed_path(branch, normalized):
        return True
    return normalized in c.EXACT_CHANGED_PATH_CANDIDATES and _branch_allows_pr151_changed_paths(
        branch
    )


def _validate_changed_paths(
    repo_root: Path,
    *,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    branch = current_branch_context(repo_root).branch
    failures: list[str] = []
    sidecar_path = _forbidden_bundle_sidecar_path()
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR151_GIT_STATUS_UNAVAILABLE")
            continue
        normalized = path.replace("\\", "/")
        if not _is_allowed_pr151_changed_path_for_branch(
            normalized,
            branch,
            tracked_report_write_allowed=tracked_report_write_allowed,
        ):
            failures.append(f"PR151_CHANGED_PATH_OUT_OF_SCOPE: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append("PR151_MASTER_PLAN_MUTATION_DETECTED")
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix():
            failures.append("PR151_ATOMICROWS_BUNDLE_MUTATION_DETECTED")
        if normalized == sidecar_path:
            failures.append("PR151_ATOMICROWS_SIDECAR_REFERENCE_DETECTED")
    return sorted(set(failures))


def _pr151_file_paths(root: Path) -> list[Path]:
    return [
        root / "src/qtt/stage1_prediction_markets/official_source_retrieval_target_pack_parameter_defaults/__init__.py",
        root / "src/qtt/stage1_prediction_markets/official_source_retrieval_target_pack_parameter_defaults/constants.py",
        root / "src/qtt/stage1_prediction_markets/official_source_retrieval_target_pack_parameter_defaults/report.py",
        root / "src/qtt/stage1_prediction_markets/official_source_retrieval_target_pack_parameter_defaults/validator.py",
        root / "tools/validate_official_source_retrieval_target_pack_parameter_defaults.py",
        root / "tests/source_evidence/test_official_source_retrieval_target_pack_parameter_defaults.py",
    ]


def _network_surface_failures(root: Path) -> list[str]:
    failures: list[str] = []
    blocked_imports = {"aiohttp", "ftplib", "httpx", "requests", "socket", "urllib", "webbrowser"}
    blocked_commands = {
        "cu" + "rl ",
        "wg" + "et ",
        "Invoke-" + "WebRequest",
        "Invoke-" + "RestMethod",
        "Start-" + "BitsTransfer",
    }
    for path in _pr151_file_paths(root):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            failures.append(f"PR151_NETWORK_SURFACE_DETECTED: {path.relative_to(root).as_posix()}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in blocked_imports:
                        failures.append("PR151_NETWORK_SURFACE_DETECTED")
            elif isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")[0]
                if module in blocked_imports:
                    failures.append("PR151_NETWORK_SURFACE_DETECTED")
        if path.name == "constants.py":
            continue
        for token in blocked_commands:
            if token in text:
                failures.append("PR151_NETWORK_SURFACE_DETECTED")
    return sorted(set(failures))


def validate_repository_artifacts(
    repo_root: Path | str,
    *,
    report_output_path: Path | str | None = None,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    root = Path(repo_root).resolve()
    try:
        expected_report = build_report(root)
        if expected_report != build_report(root):
            return ["PR151_REPORT_NOT_DETERMINISTIC"]
    except ValueError as exc:
        return [line for line in str(exc).splitlines() if line]

    failures = validate_report_payload(expected_report)
    if report_output_path is not None:
        output_path = Path(report_output_path)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_dump(expected_report), encoding="utf-8", newline="\n")

    try:
        actual_report = _read_json(root / c.REPORT_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_report = {}
        failures.append(f"PR151_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}")
    if actual_report and actual_report != expected_report:
        failures.append("PR151_REPORT_STALE_OR_NONDETERMINISTIC")
    if actual_report:
        failures.extend(validate_report_payload(actual_report))

    failures.extend(_network_surface_failures(root))
    failures.extend(
        _validate_changed_paths(
            root,
            tracked_report_write_allowed=tracked_report_write_allowed,
        )
    )
    return sorted(set(failures))


def write_report_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    report = build_report(root)
    path = root / c.REPORT_PATH
    serialized_report = json_dump(report)
    serialized_bytes = serialized_report.encode("utf-8")
    if path.exists():
        current_bytes = path.read_bytes()
        if (
            current_bytes == serialized_bytes
            or current_bytes.replace(b"\r\n", b"\n") == serialized_bytes
        ):
            return report
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized_report, encoding="utf-8", newline="\n")
    return report
