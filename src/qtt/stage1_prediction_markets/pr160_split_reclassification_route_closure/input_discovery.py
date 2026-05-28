"""Input loading and target parsing for PR160."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping, read_json


VENUE_MARKERS = ("FORECASTEX_IBKR", "KALSHI", "POLYMARKET")


def _load_json(root: Path, rel_path: Path) -> Mapping[str, Any]:
    path = root / rel_path
    if not path.exists():
        return {}
    payload = read_json(path)
    return as_mapping(payload)


def _records(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [as_mapping(item) for item in as_list(payload.get("records"))]


def load_split_records(root: Path) -> list[Mapping[str, Any]]:
    payload = _load_json(root, c.PR158_SPLIT_REGISTRY_PATH)
    return sorted(_records(payload), key=lambda item: str(item.get("PR154_target_id")))


def load_pr157_pr154_records(root: Path) -> list[Mapping[str, Any]]:
    payload = _load_json(root, c.PR157_PR154_REGISTRY_PATH)
    return sorted(_records(payload), key=lambda item: str(item.get("target_id")))


def pr157_by_target_id(records: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(record.get("target_id")): record for record in records}


def load_pr150_items(root: Path) -> list[Mapping[str, Any]]:
    payload = _load_json(root, c.PR150_TARGET_MATRIX_PATH)
    matrix = as_mapping(payload.get("parameter_default_target_matrix"))
    return [
        as_mapping(item)
        for item in as_list(matrix.get("parameter_target_items"))
        if isinstance(item, Mapping)
    ]


def load_pr159_accepted_packets(root: Path) -> list[Mapping[str, Any]]:
    return _records(_load_json(root, c.PR159_ACCEPTED_PACKET_REGISTRY_PATH))


def load_pr159_unresolved_fill_paths(root: Path) -> list[Mapping[str, Any]]:
    return _records(_load_json(root, c.PR159_UNRESOLVED_FILL_PATH_PATH))


def accepted_packet_by_exact_target(
    records: list[Mapping[str, Any]],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    return {
        (str(record.get("target_id_or_row_id")), str(record.get("target_field_id"))): record
        for record in records
    }


def unresolved_path_by_exact_target(
    records: list[Mapping[str, Any]],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    return {
        (str(record.get("target_id_or_row_id")), str(record.get("target_field_id"))): record
        for record in records
    }


def target_venue(target_id: str) -> str:
    for marker in VENUE_MARKERS:
        if marker in target_id:
            return marker
    return "PREDICTION_MARKETS_GENERAL"


def pr150_item_for_target(
    target_id: str,
    pr150_items: list[Mapping[str, Any]],
) -> Mapping[str, Any]:
    for item in pr150_items:
        domain = str(item.get("target_domain") or "")
        name = str(item.get("target_name") or "")
        if domain and domain in target_id and name.upper() in target_id:
            return item
    return {}


def target_field_id_from_pr150(item: Mapping[str, Any]) -> str:
    source_field = str(item.get("source_target_field_class") or "")
    if ":" in source_field:
        return source_field.split(":")[-1]
    return str(item.get("target_name") or item.get("target_domain") or "target_field")


def requested_value_type(item: Mapping[str, Any]) -> str:
    return str(item.get("evidence_requirement_class") or "ROUTE_METADATA_ONLY")


def requested_unit_or_basis(item: Mapping[str, Any]) -> str:
    return str(item.get("source_target_field_class") or "route_metadata_basis")


def requested_scale(item: Mapping[str, Any]) -> str:
    return str(item.get("order_use_eligibility") or "nonlive_metadata_only")


def source_record(
    split_record: Mapping[str, Any],
    pr157_record: Mapping[str, Any],
    pr150_item: Mapping[str, Any],
    accepted_packet: Mapping[str, Any] | None,
    unresolved_path: Mapping[str, Any] | None,
) -> dict[str, Any]:
    target_id = str(split_record.get("PR154_target_id"))
    request_id = str(split_record.get("request_id"))
    target_field_id = target_field_id_from_pr150(pr150_item)
    fill_plan_refs = as_list(pr157_record.get("fill_plan_refs"))
    first_fill_plan = as_mapping(fill_plan_refs[0]) if fill_plan_refs else {}
    venue = target_venue(target_id)
    return {
        "request_id_or_record_id": request_id,
        "PR154_target_id": target_id,
        "current_source_population": split_record.get("current_source_population"),
        "current_blocker_class": split_record.get("current_blocker_class"),
        "target_field_id": target_field_id,
        "requested_value_name": pr150_item.get("target_name"),
        "requested_value_type": requested_value_type(pr150_item),
        "requested_unit_or_basis": requested_unit_or_basis(pr150_item),
        "requested_scale": requested_scale(pr150_item),
        "platform_scope": "PREDICTION_MARKETS_GENERAL",
        "venue_scope": venue,
        "market_scope": "PREDICTION_MARKETS_GENERAL",
        "strategy_scope": "STATIC_RECLASSIFICATION_ROUTE_CLOSURE_ONLY",
        "current_future_route_if_any": split_record.get("future_route"),
        "PR157_fill_path_ref": first_fill_plan.get("fill_plan_id"),
        "PR158_candidate_reclassification_ref": request_id,
        "PR159_source_attempt_ref_or_null": None,
        "PR159_accepted_packet_ref_or_null": (
            accepted_packet.get("accepted_packet_id") if accepted_packet else None
        ),
        "PR159_unresolved_fill_path_ref_or_null": (
            unresolved_path.get("target_id_or_row_id") if unresolved_path else None
        ),
        "pr150_target_id_or_null": pr150_item.get("target_id"),
        "pr150_target_domain_or_null": pr150_item.get("target_domain"),
        "pr150_target_family_id_or_null": pr150_item.get("target_family_id"),
        "pr150_evidence_requirement_class_or_null": pr150_item.get("evidence_requirement_class"),
        "pr150_value_authority_class_or_null": pr150_item.get("value_authority_class"),
        "pr150_default_target_state_or_null": pr150_item.get("default_target_state"),
        "pr150_order_use_eligibility_or_null": pr150_item.get("order_use_eligibility"),
        "pr150_downstream_consumer_classes_or_null": list(
            as_list(pr150_item.get("downstream_consumer_classes"))
        ),
    }


def build_source_records(root: Path) -> list[dict[str, Any]]:
    split_records = load_split_records(root)
    pr157_index = pr157_by_target_id(load_pr157_pr154_records(root))
    pr150_items = load_pr150_items(root)
    accepted_index = accepted_packet_by_exact_target(load_pr159_accepted_packets(root))
    unresolved_index = unresolved_path_by_exact_target(load_pr159_unresolved_fill_paths(root))
    output: list[dict[str, Any]] = []
    for split_record in split_records:
        target_id = str(split_record.get("PR154_target_id"))
        pr150_item = pr150_item_for_target(target_id, pr150_items)
        field_id = target_field_id_from_pr150(pr150_item)
        exact_key = (target_id, field_id)
        output.append(
            source_record(
                split_record,
                pr157_index.get(target_id, {}),
                pr150_item,
                accepted_index.get(exact_key),
                unresolved_index.get(exact_key),
            )
        )
    return sorted(output, key=lambda item: item["PR154_target_id"])
