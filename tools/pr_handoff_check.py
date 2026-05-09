#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any, Sequence

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from qtt.core.testing.gate_result import (  # noqa: E402
    CANONICAL_ATOMICROWS_BUNDLE,
    CANONICAL_ATOMICROWS_BUNDLE_SHA,
    STATIC_AUTHORITY_FLAGS,
    canonical_atomicrows_absence_failures,
    canonical_atomicrows_presence,
    require_exact_fields,
    static_metadata,
    true_claim_failures,
    write_json,
)

SUCCESS_MARKER = "PR_HANDOFF_CHECK_OK"
FAILURE_MARKER = "PR_HANDOFF_CHECK_FAILED"

PACKET_TYPE = "FIRST_CODING_PR_HANDOFF_PACKET"
PACKET_VERSION = "PR37_FIRST_CODING_PR_HANDOFF_PACKET_V1"
VALIDATION_HOOK = "PR_HANDOFF_CHECK_STATIC_AUDIT"

ROOT_FIELDS = {
    "packet_type",
    "packet_version",
    "status",
    "metadata",
    "handoff_scope",
    "not_created_claims",
    "remaining_blockers",
    "generated_derivative_and_atomicrows_status",
    "forbidden_authority_claims",
    "summary_no_authority",
    "validation_hook_ids",
}

METADATA_FIELDS = set(STATIC_AUTHORITY_FLAGS) | {
    "generated_by",
    "generated_at_utc",
    "authority_class",
}

HANDOFF_SCOPE = {
    "phase": "first-coding-runbook",
    "pr_title": "Add QTT cumulative test gate and PR handoff checker",
    "master_plan_mapping": (
        "0X.4O QTT cumulative test gate, local gate command matrix, "
        "and first-coding PR handoff Codex task packet"
    ),
    "authority_class": "STATIC_REPORT_ONLY_NOT_TRADING_AUTHORITY",
    "pr_handoff_creates_authority": False,
}

NOT_CREATED_CLAIMS = {
    "source_fact_acceptance": "NOT_CREATED",
    "connector_semantics": "NOT_CREATED",
    "runtime_resolver_snapshots": "NOT_CREATED",
    "replay_paper_results": "NOT_CREATED",
    "live_reachability": "NOT_CREATED",
    "runtime_cash_or_usable_cash_receipts": "NOT_CREATED",
    "atomicrows_bundle_hash_or_4183_rows": "NOT_CREATED",
    "blocker_reduction": "NOT_CREATED",
    "profit_evidence": "NOT_CREATED",
}

REMAINING_BLOCKER_IDS = [
    "source_fact_acceptance",
    "connector_semantics",
    "runtime_resolver_snapshots",
    "replay_paper_results",
    "live_reachability",
    "runtime_cash_or_usable_cash_receipts",
    "atomicrows_bundle_hash_or_4183_rows",
    "blocker_reduction",
    "profit_evidence",
]

BLOCKER_FIELDS = {
    "blocker_id",
    "status",
    "reduced_by_this_packet",
    "authority_created",
}

ATOMICROWS_STATUS_FIELDS = {
    "generated_derivative_status",
    "atomicrows_bundle_path",
    "atomicrows_bundle_present",
    "atomicrows_bundle_sha_path",
    "atomicrows_bundle_sha_present",
    "atomicrows_row_count_status",
    "bootstrap_status_explicit",
    "creates_completion_authority",
}

FORBIDDEN_AUTHORITY_CLAIMS = {
    "freeze_or_sha_authority": False,
    "source_fact_acceptance": False,
    "connector_semantics": False,
    "exact_contract_event_market_selection": False,
    "runtime_resolver_snapshot": False,
    "replay_paper_execution_or_result_packets": False,
    "dual_result_review_decision": False,
    "limited_live_canary_or_live_arbitrage": False,
    "live_reachability": False,
    "runtime_cash_or_usable_cash_receipt": False,
    "dashboard_live_mutation": False,
    "atomicrows_bundle_hash_or_4183_rows": False,
    "blocker_reduction": False,
    "profit_evidence": False,
}

SUMMARY_NO_AUTHORITY = {
    "pr_handoff_creates_authority": False,
    "creates_source_fact_acceptance": False,
    "creates_connector_semantics": False,
    "creates_runtime_resolver_snapshot": False,
    "executes_replay_or_paper": False,
    "creates_live_reachability": False,
    "creates_runtime_cash_or_usable_cash": False,
    "creates_atomicrows_bundle_or_4183_rows": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

FORBIDDEN_TRUE_FIELDS = set(STATIC_AUTHORITY_FLAGS) | set(FORBIDDEN_AUTHORITY_CLAIMS) | set(
    SUMMARY_NO_AUTHORITY
) | {
    "pr_handoff_creates_authority",
    "reduced_by_this_packet",
    "authority_created",
    "atomicrows_bundle_present",
    "atomicrows_bundle_sha_present",
    "creates_completion_authority",
}


def _static_flag_failures(value: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    for field, expected in sorted(STATIC_AUTHORITY_FLAGS.items()):
        if value.get(field) is not expected:
            failures.append(f"{label}.{field} must be {expected}")
    return failures


def _remaining_blockers() -> list[dict[str, Any]]:
    return [
        {
            "blocker_id": blocker_id,
            "status": "REMAINING_BLOCKER",
            "reduced_by_this_packet": False,
            "authority_created": False,
        }
        for blocker_id in REMAINING_BLOCKER_IDS
    ]


def build_packet(*, repo_root: pathlib.Path) -> dict[str, Any]:
    bundle_present, sha_present = canonical_atomicrows_presence(repo_root)
    return {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "status": "PASS",
        "metadata": static_metadata("tools/pr_handoff_check.py"),
        "handoff_scope": dict(HANDOFF_SCOPE),
        "not_created_claims": dict(NOT_CREATED_CLAIMS),
        "remaining_blockers": _remaining_blockers(),
        "generated_derivative_and_atomicrows_status": {
            "generated_derivative_status": "STATIC_BOOTSTRAP_ABSENT_NO_COMPLETION_AUTHORITY",
            "atomicrows_bundle_path": str(CANONICAL_ATOMICROWS_BUNDLE),
            "atomicrows_bundle_present": bundle_present,
            "atomicrows_bundle_sha_path": str(CANONICAL_ATOMICROWS_BUNDLE_SHA),
            "atomicrows_bundle_sha_present": sha_present,
            "atomicrows_row_count_status": "NOT_CREATED_UNBOUND",
            "bootstrap_status_explicit": True,
            "creates_completion_authority": False,
        },
        "forbidden_authority_claims": dict(FORBIDDEN_AUTHORITY_CLAIMS),
        "summary_no_authority": dict(SUMMARY_NO_AUTHORITY),
        "validation_hook_ids": [VALIDATION_HOOK],
    }


def _validate_not_created_claims(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["not_created_claims must be an object"]
    failures = require_exact_fields(value, NOT_CREATED_CLAIMS, "not_created_claims")
    for field, expected in sorted(NOT_CREATED_CLAIMS.items()):
        if value.get(field) != expected:
            failures.append(f"not_created_claims.{field} must be {expected}")
    return failures


def _validate_remaining_blockers(value: Any) -> list[str]:
    if not isinstance(value, list):
        return ["remaining_blockers must be a list"]
    failures: list[str] = []
    actual_ids = [item.get("blocker_id") for item in value if isinstance(item, dict)]
    if actual_ids != REMAINING_BLOCKER_IDS:
        failures.append("remaining_blockers must explicitly preserve all required blocker ids")
    for index, item in enumerate(value):
        label = f"remaining_blockers[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(require_exact_fields(item, BLOCKER_FIELDS, label))
        if item.get("status") != "REMAINING_BLOCKER":
            failures.append(f"{label}.status must be REMAINING_BLOCKER")
        if item.get("reduced_by_this_packet") is not False:
            failures.append(f"{label}.reduced_by_this_packet must be false")
        if item.get("authority_created") is not False:
            failures.append(f"{label}.authority_created must be false")
    return failures


def _validate_atomicrows_status(value: Any, repo_root: pathlib.Path) -> list[str]:
    if not isinstance(value, dict):
        return ["generated_derivative_and_atomicrows_status must be an object"]
    failures = require_exact_fields(
        value,
        ATOMICROWS_STATUS_FIELDS,
        "generated_derivative_and_atomicrows_status",
    )
    if value.get("generated_derivative_status") != (
        "STATIC_BOOTSTRAP_ABSENT_NO_COMPLETION_AUTHORITY"
    ):
        failures.append(
            "generated_derivative_and_atomicrows_status.generated_derivative_status "
            "must be STATIC_BOOTSTRAP_ABSENT_NO_COMPLETION_AUTHORITY"
        )
    bundle_present, sha_present = canonical_atomicrows_presence(repo_root)
    if value.get("atomicrows_bundle_present") is not bundle_present:
        failures.append(
            "generated_derivative_and_atomicrows_status.atomicrows_bundle_present "
            f"must match filesystem presence {bundle_present}"
        )
    if value.get("atomicrows_bundle_sha_present") is not sha_present:
        failures.append(
            "generated_derivative_and_atomicrows_status.atomicrows_bundle_sha_present "
            f"must match filesystem presence {sha_present}"
        )
    if value.get("atomicrows_row_count_status") != "NOT_CREATED_UNBOUND":
        failures.append(
            "generated_derivative_and_atomicrows_status.atomicrows_row_count_status "
            "must be NOT_CREATED_UNBOUND"
        )
    if value.get("bootstrap_status_explicit") is not True:
        failures.append(
            "generated_derivative_and_atomicrows_status.bootstrap_status_explicit must be true"
        )
    if value.get("creates_completion_authority") is not False:
        failures.append(
            "generated_derivative_and_atomicrows_status.creates_completion_authority must be false"
        )
    return failures


def _validate_false_map(
    value: Any,
    expected: dict[str, bool],
    label: str,
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    failures = require_exact_fields(value, expected, label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) is not expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def validate_packet(packet: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures = require_exact_fields(packet, ROOT_FIELDS, "pr handoff packet")
    if packet.get("packet_type") != PACKET_TYPE:
        failures.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        failures.append(f"packet_version must be {PACKET_VERSION}")
    if packet.get("status") != "PASS":
        failures.append("status must be PASS")

    metadata = packet.get("metadata")
    if not isinstance(metadata, dict):
        failures.append("metadata must be an object")
    else:
        failures.extend(require_exact_fields(metadata, METADATA_FIELDS, "metadata"))
        failures.extend(_static_flag_failures(metadata, "metadata"))
        if metadata.get("authority_class") != "STATIC_REPORT_ONLY_NOT_TRADING_AUTHORITY":
            failures.append("metadata.authority_class must be static report only")

    handoff_scope = packet.get("handoff_scope")
    if not isinstance(handoff_scope, dict):
        failures.append("handoff_scope must be an object")
    else:
        failures.extend(require_exact_fields(handoff_scope, HANDOFF_SCOPE, "handoff_scope"))
        for field, expected in sorted(HANDOFF_SCOPE.items()):
            if handoff_scope.get(field) != expected:
                failures.append(f"handoff_scope.{field} must be {expected}")

    failures.extend(_validate_not_created_claims(packet.get("not_created_claims")))
    failures.extend(_validate_remaining_blockers(packet.get("remaining_blockers")))
    failures.extend(
        _validate_atomicrows_status(
            packet.get("generated_derivative_and_atomicrows_status"),
            repo_root,
        )
    )
    failures.extend(
        _validate_false_map(
            packet.get("forbidden_authority_claims"),
            FORBIDDEN_AUTHORITY_CLAIMS,
            "forbidden_authority_claims",
        )
    )
    failures.extend(
        _validate_false_map(
            packet.get("summary_no_authority"),
            SUMMARY_NO_AUTHORITY,
            "summary_no_authority",
        )
    )
    failures.extend(
        true_claim_failures(
            packet,
            forbidden_true_fields=FORBIDDEN_TRUE_FIELDS,
            label="pr handoff packet",
        )
    )
    failures.extend(
        canonical_atomicrows_absence_failures(
            repo_root,
            label="pr handoff packet",
        )
    )
    if packet.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    packet = build_packet(repo_root=repo_root)
    failures = validate_packet(packet, repo_root=repo_root)
    write_json(repo_root / pathlib.Path(args.out), packet)

    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
