#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Iterable, Sequence

SUCCESS_MARKER = "STAGE1_CONNECTOR_SEMANTIC_VALUE_CANONICALIZATION_CHECK_OK"
FAILURE_MARKER = "STAGE1_CONNECTOR_SEMANTIC_VALUE_CANONICALIZATION_CHECK_FAILED"

VALIDATION_HOOK = "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_STATIC_AUDIT"
CANONICALIZATION_TYPE = "STAGE1_CONNECTOR_SEMANTIC_VALUE_CANONICALIZATION"
EXPECTED_SYNTHETIC_NOTICE = "SYNTHETIC_PLACEHOLDER_ONLY_NO_REAL_SOURCE_NO_REAL_ACCEPTED_FACT"

VALID_CANONICALIZATION_STATE = "CANONICALIZATION_VALID"
ACCEPTED_SOURCE_ORIGIN = "ACCEPTED_SOURCE_EVIDENCE_EXPORT_RECORD"

CANONICAL_ATOMICROWS_BUNDLE = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_ATOMICROWS_BUNDLE_SHA = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

DEFAULT_FIXTURE = pathlib.Path(
    "tests/fixtures/source_evidence/connector_semantic_binding/"
    "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
)

NO_CLAIM_FLAGS = {
    "accepts_source_facts": False,
    "creates_real_accepted_source_evidence": False,
    "creates_accepted_source_packets": False,
    "populates_connector_semantic_values": False,
    "imports_live_clients": False,
    "creates_network_io": False,
    "creates_runtime_resolver_snapshot": False,
    "executes_replay_or_paper": False,
    "creates_replay_paper_result_packets": False,
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_runtime_cash_claim": False,
    "creates_atomicrows_bundle_or_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

CANONICALIZATION_FIELDS = {
    "stage1_connector_semantic_value_canonicalization_type",
    "semantic_value_canonicalization_record_id",
    "fixture_case",
    "record_authority_class",
    "synthetic_data_notice",
    "accepted_source_evidence_export_record_id",
    "target_field_acceptance_ledger_record_id",
    "source_to_connector_field_binding_record_id",
    "target_field_path",
    "bound_value_original",
    "bound_value_canonical",
    "bound_value_type",
    "bound_value_unit_or_scale",
    "bound_value_scope",
    "bound_value_normalization_rule_id",
    "bound_value_rounding_or_precision_rule_id_when_applicable",
    "semantic_meaning_preservation_key_original",
    "semantic_meaning_preservation_key_canonical",
    "source_value_origin",
    "canonicalization_state",
    "canonicalization_may_convert_representation_but_may_not_change_meaning",
    "canonicalization_requires_accepted_source_evidence_export_record",
    "canonicalization_requires_target_field_acceptance_ledger_record",
    "canonicalization_requires_source_to_connector_field_binding_record",
    "canonicalization_requires_explicit_value_type_unit_scale_and_scope",
    "canonicalization_may_not_invent_fee_tick_rate_limit_settlement_payout_latency_or_order_behavior",
    "canonicalization_may_not_zero_fill_missing_value",
    "canonicalization_may_not_use_owner_policy_value_when_source_packet_required",
    "canonicalization_may_not_use_runtime_observed_value_when_source_packet_required",
    "canonicalization_failure_blocks_binding_packet_creation",
    "canonicalization_changes_meaning_flag",
    "semantic_value_invention_attempt_flag",
    "zero_fill_missing_value_attempt_flag",
    "owner_policy_substitution_attempt_flag",
    "runtime_observed_value_substitution_attempt_flag",
    "candidate_source_evidence_packet_is_accepted_source_evidence_flag",
    "binding_packet_creation_allowed_flag",
    "blocker_codes",
    "receipt_ids",
    "no_claim_flags",
    "validation_hook_ids",
}

REQUIRED_TRUE_RULE_FLAGS = {
    "canonicalization_may_convert_representation_but_may_not_change_meaning",
    "canonicalization_requires_accepted_source_evidence_export_record",
    "canonicalization_requires_target_field_acceptance_ledger_record",
    "canonicalization_requires_source_to_connector_field_binding_record",
    "canonicalization_requires_explicit_value_type_unit_scale_and_scope",
    "canonicalization_may_not_invent_fee_tick_rate_limit_settlement_payout_latency_or_order_behavior",
    "canonicalization_may_not_zero_fill_missing_value",
    "canonicalization_may_not_use_owner_policy_value_when_source_packet_required",
    "canonicalization_may_not_use_runtime_observed_value_when_source_packet_required",
    "canonicalization_failure_blocks_binding_packet_creation",
}

FORBIDDEN_TRUE_FIELDS = set(NO_CLAIM_FLAGS) | {
    "candidate_source_evidence_packet_is_accepted_source_evidence_flag",
    "canonicalization_changes_meaning_flag",
    "accepted_source_fact_created",
    "accepted_source_packet_created",
    "accepted_source_evidence_packet_created",
    "connector_semantic_value_populated",
    "connector_semantic_values_populated",
    "live_client_import_allowed_flag",
    "network_io_allowed_flag",
    "order_execution_allowed_flag",
    "live_reachability_allowed_flag",
    "runtime_resolver_snapshot_creation_allowed_flag",
    "runtime_resolver_snapshot_created",
    "replay_execution_allowed_flag",
    "paper_execution_allowed_flag",
    "replay_paper_result_packet_created",
    "live_order_authority_created",
    "runtime_cash_claim_created",
    "atomicrows_bundle_creation_claimed",
    "atomicrows_hash_creation_claimed",
    "blocker_reduction_claimed",
    "profit_evidence_created",
}

FORBIDDEN_STRING_MARKERS = {
    "OFFICIAL_SOURCE_FACT_ACCEPTED",
    "REAL_ACCEPTED_SOURCE_EVIDENCE_PACKET_CREATED",
    "CONNECTOR_SEMANTIC_VALUE_POPULATED",
    "RUNTIME_RESOLVER_SNAPSHOT_CREATED",
    "REPLAY_RESULT_PACKET_CREATED",
    "PAPER_RESULT_PACKET_CREATED",
    "LIVE_REACHABILITY_CREATED",
    "ORDER_AUTHORITY_CREATED",
    "ATOMICROWS_BUNDLE_CREATED",
    "ATOMICROWS_BUNDLE_HASH_CREATED",
    "BLOCKER_REDUCED",
    "PROFIT_EVIDENCE_CREATED",
}

EXPECTED_STATE_BY_CASE = {
    "VALID_SYNTHETIC_BINDING_NONLIVE_ONLY": VALID_CANONICALIZATION_STATE,
    "BLOCKED_STALE_BINDING": VALID_CANONICALIZATION_STATE,
    "BLOCKED_CONFLICT_BINDING": VALID_CANONICALIZATION_STATE,
    "BLOCKED_TARGET_MISMATCH_BINDING": VALID_CANONICALIZATION_STATE,
    "BLOCKED_SCHEMA_ERROR_BINDING": "BLOCKED_SCHEMA_ERROR",
    "BLOCKED_MISSING_ACCEPTED_SOURCE_EXPORT_RECORD": "BLOCKED_MISSING_ACCEPTED_SOURCE_EXPORT",
    "BLOCKED_MISSING_TARGET_FIELD_ACCEPTANCE_LEDGER_RECORD": "BLOCKED_MISSING_TARGET_FIELD_ACCEPTANCE_LEDGER",
    "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_BINDING_RECORD": "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_BINDING",
    "BLOCKED_ZERO_FILL_INVENTED_MISSING_VALUE_ATTEMPT": "BLOCKED_ZERO_FILL",
    "BLOCKED_OWNER_POLICY_SUBSTITUTION_ATTEMPT": "BLOCKED_OWNER_POLICY_SUBSTITUTION",
    "BLOCKED_RUNTIME_OBSERVED_VALUE_SUBSTITUTION_ATTEMPT": "BLOCKED_RUNTIME_OBSERVED_SUBSTITUTION",
    "BLOCKED_LIVE_CLIENT_NETWORK_ORDER_REACHABILITY_CLAIM_ATTEMPT": VALID_CANONICALIZATION_STATE,
}


def load_json_object(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is not valid JSON: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def require_exact_fields(
    value: dict[str, Any],
    fields: Iterable[str],
    label: str,
) -> list[str]:
    expected = set(fields)
    actual = set(value)
    failures: list[str] = []
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def validate_bool_map(value: Any, expected: dict[str, bool], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    failures = require_exact_fields(value, expected, label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) is not expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def walk(value: Any, path: str = "value"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from walk(item, current)


def missing_reference(value: Any) -> bool:
    return not isinstance(value, str) or not value or value.startswith("MISSING_")


def validate_no_forbidden_claims(value: Any, label: str) -> list[str]:
    failures: list[str] = []
    for path, key, item in walk(value, label):
        if key in FORBIDDEN_TRUE_FIELDS and item is not False:
            failures.append(f"{path} must be false")
        if isinstance(item, str):
            upper = item.upper()
            for marker in sorted(FORBIDDEN_STRING_MARKERS):
                if marker in upper:
                    failures.append(f"{path} contains forbidden claim marker {marker}")
            if "://" in item:
                failures.append(f"{path} must not contain an external locator or URL")
    return failures


def canonical_atomicrows_absence_failures(repo_root: pathlib.Path, label: str) -> list[str]:
    root = repo_root.resolve()
    bundle = root / pathlib.Path(*CANONICAL_ATOMICROWS_BUNDLE.parts)
    bundle_sha = root / pathlib.Path(*CANONICAL_ATOMICROWS_BUNDLE_SHA.parts)
    failures: list[str] = []
    if bundle.exists():
        failures.append(
            f"{label}: canonical AtomicRows bundle must remain absent: "
            f"{CANONICAL_ATOMICROWS_BUNDLE}"
        )
    if bundle_sha.exists():
        failures.append(
            f"{label}: canonical AtomicRows bundle hash must remain absent: "
            f"{CANONICAL_ATOMICROWS_BUNDLE_SHA}"
        )
    return failures


def _validate_scope(record: dict[str, Any], label: str) -> list[str]:
    scope = record.get("bound_value_scope")
    if not isinstance(scope, dict):
        return [f"{label}.bound_value_scope must be an object"]
    failures = require_exact_fields(
        scope,
        {
            "scope_id",
            "scope_authority_class",
            "venue_id",
            "target_field_path",
            "wildcard_scope_allowed",
            "cross_venue_scope_allowed",
        },
        f"{label}.bound_value_scope",
    )
    if scope.get("scope_authority_class") != "SYNTHETIC_SCOPE_ONLY_NOT_EXTERNAL_FACT_AUTHORITY":
        failures.append(f"{label}.bound_value_scope.scope_authority_class must be synthetic")
    if scope.get("target_field_path") != record.get("target_field_path"):
        failures.append(f"{label}.bound_value_scope.target_field_path must match record")
    if scope.get("wildcard_scope_allowed") is not False:
        failures.append(f"{label}.bound_value_scope.wildcard_scope_allowed must be false")
    if scope.get("cross_venue_scope_allowed") is not False:
        failures.append(f"{label}.bound_value_scope.cross_venue_scope_allowed must be false")
    return failures


def validate_canonicalization_record(
    record: dict[str, Any],
    *,
    label: str = "canonicalization record",
) -> list[str]:
    failures = require_exact_fields(record, CANONICALIZATION_FIELDS, label)
    if record.get("stage1_connector_semantic_value_canonicalization_type") != CANONICALIZATION_TYPE:
        failures.append(
            f"{label}.stage1_connector_semantic_value_canonicalization_type must be "
            f"{CANONICALIZATION_TYPE}"
        )
    if record.get("synthetic_data_notice") != EXPECTED_SYNTHETIC_NOTICE:
        failures.append(f"{label}.synthetic_data_notice must mark synthetic non-authority")
    if record.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"{label}.validation_hook_ids must contain only {VALIDATION_HOOK}")
    for field in sorted(REQUIRED_TRUE_RULE_FLAGS):
        if record.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    failures.extend(validate_bool_map(record.get("no_claim_flags"), NO_CLAIM_FLAGS, f"{label}.no_claim_flags"))
    failures.extend(_validate_scope(record, label))
    failures.extend(validate_no_forbidden_claims(record, label))

    if not record.get("bound_value_type"):
        failures.append(f"{label}.bound_value_type must be explicit")
    if not record.get("bound_value_unit_or_scale"):
        failures.append(f"{label}.bound_value_unit_or_scale must be explicit")
    if not isinstance(record.get("bound_value_scope"), dict):
        failures.append(f"{label}.bound_value_scope must be explicit")

    if record.get("semantic_meaning_preservation_key_original") != record.get(
        "semantic_meaning_preservation_key_canonical"
    ):
        failures.append(f"{label} canonicalization may not change semantic meaning")

    fixture_case = record.get("fixture_case")
    expected_state = EXPECTED_STATE_BY_CASE.get(fixture_case)
    if expected_state is None:
        failures.append(f"{label}.fixture_case is not a required PR40 fixture case")
    elif record.get("canonicalization_state") != expected_state:
        failures.append(
            f"{label}.canonicalization_state must be {expected_state} for {fixture_case}"
        )

    state = record.get("canonicalization_state")
    blockers = record.get("blocker_codes")
    if not isinstance(blockers, list):
        failures.append(f"{label}.blocker_codes must be a list")
        blockers = []
    receipts = record.get("receipt_ids")
    if not isinstance(receipts, list) or not receipts:
        failures.append(f"{label}.receipt_ids must be a non-empty list")

    has_missing_link = any(
        missing_reference(record.get(field))
        for field in [
            "accepted_source_evidence_export_record_id",
            "target_field_acceptance_ledger_record_id",
            "source_to_connector_field_binding_record_id",
        ]
    )
    has_source_substitution_or_invention = any(
        record.get(field) is True
        for field in [
            "semantic_value_invention_attempt_flag",
            "zero_fill_missing_value_attempt_flag",
            "owner_policy_substitution_attempt_flag",
            "runtime_observed_value_substitution_attempt_flag",
        ]
    )

    if state == VALID_CANONICALIZATION_STATE:
        if record.get("source_value_origin") != ACCEPTED_SOURCE_ORIGIN:
            failures.append(f"{label}.source_value_origin must be {ACCEPTED_SOURCE_ORIGIN}")
        if has_missing_link:
            failures.append(f"{label} valid canonicalization requires all linkage records")
        if has_source_substitution_or_invention:
            failures.append(f"{label} valid canonicalization cannot contain guessed or substituted values")
        if record.get("binding_packet_creation_allowed_flag") is not True:
            failures.append(f"{label}.binding_packet_creation_allowed_flag must be true when valid")
        if blockers:
            failures.append(f"{label}.blocker_codes must be empty when valid")
    else:
        if record.get("binding_packet_creation_allowed_flag") is not False:
            failures.append(f"{label}.binding_packet_creation_allowed_flag must be false when blocked")
        if not blockers:
            failures.append(f"{label}.blocker_codes must explain blocked canonicalization")

    if record.get("source_value_origin") == "CANDIDATE_SOURCE_EVIDENCE_PACKET_NOT_ACCEPTED":
        if state == VALID_CANONICALIZATION_STATE:
            failures.append(f"{label} candidate source evidence cannot be accepted evidence")
    if record.get("zero_fill_missing_value_attempt_flag") is True and state != "BLOCKED_ZERO_FILL":
        failures.append(f"{label}.canonicalization_state must block zero-fill attempts")
    if record.get("semantic_value_invention_attempt_flag") is True and state not in {
        "BLOCKED_GUESSED_OR_INVENTED_VALUE",
        "BLOCKED_ZERO_FILL",
    }:
        failures.append(f"{label}.canonicalization_state must block invented semantic values")
    if record.get("owner_policy_substitution_attempt_flag") is True and state != (
        "BLOCKED_OWNER_POLICY_SUBSTITUTION"
    ):
        failures.append(f"{label}.canonicalization_state must block owner-policy substitution")
    if record.get("runtime_observed_value_substitution_attempt_flag") is True and state != (
        "BLOCKED_RUNTIME_OBSERVED_SUBSTITUTION"
    ):
        failures.append(f"{label}.canonicalization_state must block runtime-observed substitution")

    return failures


def validate_canonicalization_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    records = fixture.get("semantic_value_canonicalization_records")
    if not isinstance(records, list) or not records:
        return ["fixture.semantic_value_canonicalization_records must be a non-empty list"]
    failures: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            failures.append(f"semantic_value_canonicalization_records[{index}] must be an object")
            continue
        failures.extend(
            validate_canonicalization_record(
                record,
                label=f"semantic_value_canonicalization_records[{index}]",
            )
        )
    failures.extend(canonical_atomicrows_absence_failures(repo_root, "canonicalization fixture"))
    return failures


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    fixture, failures = load_json_object(pathlib.Path(args.fixture))
    if fixture is not None:
        failures.extend(
            validate_canonicalization_fixture(
                fixture,
                repo_root=pathlib.Path(args.repo_root),
            )
        )
    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
