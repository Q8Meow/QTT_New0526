from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class CanonicalizationResult:
    ok: bool
    original_text: str
    canonical_text: str
    meaning_preservation_key: str
    failures: tuple[str, ...]


def _stable_json(value: Any, *, sort_keys: bool) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=sort_keys,
        separators=(",", ":") if sort_keys else None,
    )


def _meaning_key(value: Any) -> str:
    payload = _stable_json(value, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _scope_failures(scope: Any) -> list[str]:
    if not isinstance(scope, Mapping) or not scope:
        return ["bound_value_scope is required before canonicalization"]
    failures: list[str] = []
    for field in (
        "scope_id",
        "venue_id",
        "target_field_path",
        "wildcard_scope_allowed",
        "cross_venue_scope_allowed",
    ):
        if field not in scope:
            failures.append(f"bound_value_scope.{field} is required")
    if scope.get("wildcard_scope_allowed") is not False:
        failures.append("bound_value_scope.wildcard_scope_allowed must be false")
    if scope.get("cross_venue_scope_allowed") is not False:
        failures.append("bound_value_scope.cross_venue_scope_allowed must be false")
    return failures


def canonicalize_semantic_payload(
    semantic_payload: Any,
    *,
    value_type: str | None,
    unit_or_scale: str | None,
    scope: Mapping[str, Any] | None,
) -> CanonicalizationResult:
    """Canonicalize representation only after source-backed metadata is explicit."""

    failures: list[str] = []
    if semantic_payload is None:
        failures.append("accepted source-evidence export extracted_fact is required")
    if not value_type:
        failures.append("bound_value_type is required before canonicalization")
    if not unit_or_scale:
        failures.append("bound_value_unit_or_scale is required before canonicalization")
    failures.extend(_scope_failures(scope))
    if failures:
        return CanonicalizationResult(False, "", "", "", tuple(failures))

    original_text = _stable_json(semantic_payload, sort_keys=False)
    canonical_text = _stable_json(semantic_payload, sort_keys=True)
    meaning_key = _meaning_key(semantic_payload)
    return CanonicalizationResult(
        True,
        original_text,
        canonical_text,
        meaning_key,
        (),
    )
