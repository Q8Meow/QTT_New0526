"""Exact PR153R retry target extraction."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from . import constants as c
from . import taxonomy as tx


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def iter_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_objects(child)


def extract_pr153r_targets(pr153_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    targets = [
        dict(item)
        for item in iter_objects(pr153_report)
        if item.get("owner_route") == tx.PR153R_RETRY_CAPTURE
        and item.get("recommended_primary_eligibility_lane")
        == tx.EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET
    ]
    return sorted(
        targets,
        key=lambda item: (
            str(item.get("platform_scope") or ""),
            str(item.get("target_field_path") or ""),
            str(item.get("retrieval_target_id") or ""),
        ),
    )


def platform_counts(targets: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counter = Counter(str(item.get("platform_scope") or "") for item in targets)
    return {key: counter.get(key, 0) for key in sorted(c.EXPECTED_PLATFORM_COUNTS)}


def pr151_targets_by_id(pr151_report: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    queue = pr151_report.get("official_source_retrieval_target_queue")
    if not isinstance(queue, list):
        return {}
    return {
        str(item.get("retrieval_target_id")): dict(item)
        for item in queue
        if isinstance(item, dict) and item.get("retrieval_target_id")
    }


def enrich_targets_from_pr151(
    targets: Iterable[Mapping[str, Any]],
    pr151_report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    index = pr151_targets_by_id(pr151_report)
    enriched: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target.get("retrieval_target_id") or "")
        pr151 = index.get(target_id, {})
        record = dict(target)
        record.update(
            {
                "target_field_id": pr151.get("target_field_id"),
                "target_market_scope": pr151.get("target_market_scope"),
                "target_platform_scope": pr151.get("target_platform_scope"),
                "official_source_class": pr151.get("official_source_class"),
                "source_target_class": pr151.get("source_target_class"),
                "pr150_target_domain": pr151.get("pr150_target_domain"),
                "pr150_target_name": pr151.get("pr150_target_name"),
                "pr150_target_id": pr151.get("pr150_target_id"),
                "revalidation_class": pr151.get("revalidation_class"),
                "conflict_policy_class": pr151.get("conflict_policy_class"),
                "quote_span_requirement": pr151.get("quote_span_requirement"),
                "machine_field_locator_requirement": pr151.get(
                    "machine_field_locator_requirement"
                ),
                "source_locator_requirement": pr151.get("source_locator_requirement"),
            }
        )
        enriched.append(record)
    return enriched


def extraction_failures(targets: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    if len(targets) != c.EXPECTED_TARGET_COUNT:
        failures.append(tx.PR153R_REDO_EXTRACTION_COUNT_BLOCK)
    if platform_counts(targets) != c.EXPECTED_PLATFORM_COUNTS:
        failures.append(tx.PR153R_REDO_EXTRACTION_COUNT_BLOCK)
    for target in targets:
        if target.get("owner_route") != tx.PR153R_RETRY_CAPTURE:
            failures.append(tx.PR153R_REDO_NO_BROADENING_BLOCK)
        if (
            target.get("recommended_primary_eligibility_lane")
            != tx.EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET
        ):
            failures.append(tx.PR153R_REDO_NO_BROADENING_BLOCK)
    return sorted(set(failures))
