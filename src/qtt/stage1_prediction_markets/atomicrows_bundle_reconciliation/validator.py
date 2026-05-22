"""Fail-closed validator for PR137R AtomicRows reconciliation artifacts."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .model import ValidationOutcome


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _bool_at(report: Mapping[str, Any], section: str, key: str) -> bool | None:
    value = report.get(section)
    if not isinstance(value, Mapping):
        return None
    item = value.get(key)
    return item if isinstance(item, bool) else None


def _validate_environment(repo_root: Path) -> list[str]:
    failures: list[str] = []
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if branch.returncode != 0 or branch.stdout.strip() != c.BRANCH:
        failures.append(c.REASON_BASELINE_BRANCH_MISMATCH)
    head = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if head.returncode != 0 or not head.stdout.strip().startswith(c.BASE_HEAD_PREFIX):
        failures.append(c.REASON_BASELINE_HEAD_MISMATCH)
    return failures


def _validate_required_context(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("pr136_selector_artifacts_missing"):
        failures.append(c.REASON_PR136_SELECTOR_REQUIRED)
    if report.get("pr137_dependency_controller_artifacts_missing"):
        failures.append(c.REASON_PR137_DEPENDENCY_CONTROLLER_REQUIRED)
    if report.get("crosswalk_context_artifacts_missing"):
        failures.append(c.REASON_CROSSWALK_CONTEXT_REQUIRED)
    return failures


def _validate_bundle_truth(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    inventory = report.get("atomicrows_artifact_inventory", {})
    state = report.get("atomicrows_validation_state", {})
    if not isinstance(inventory, Mapping) or not isinstance(state, Mapping):
        return [c.REASON_FALSE_COMPLETION_FORBIDDEN]

    bundle_found = inventory.get("functional_bundle_artifact_found") is True
    status = state.get("functional_bundle_status")
    row_count = state.get("row_count_value")
    row_count_proven = state.get("row_count_proven") is True
    schema_validated = state.get("schema_validated") is True
    agent_ready = state.get("functional_bundle_ready_for_agent_consumption") is True

    if status not in c.ATOMICROWS_FUNCTIONAL_BUNDLE_STATUSES:
        failures.append(c.REASON_FALSE_COMPLETION_FORBIDDEN)
    if not bundle_found and status == c.STATUS_PRESENT_AND_STATICALLY_VALIDATED:
        failures.append(c.REASON_FALSE_COMPLETION_FORBIDDEN)
    if status == c.STATUS_PRESENT_AND_STATICALLY_VALIDATED:
        if row_count != c.EXPECTED_ROW_COUNT or not row_count_proven:
            failures.append(c.REASON_4183_ROWS_NOT_PROVEN)
        if not schema_validated:
            failures.append(c.REASON_ROW_SCHEMA_NOT_PROVEN)
    if row_count == c.EXPECTED_ROW_COUNT and not row_count_proven and status == c.STATUS_PRESENT_AND_STATICALLY_VALIDATED:
        failures.append(c.REASON_4183_ROWS_NOT_PROVEN)
    if schema_validated and not inventory.get("bundle_validator_found"):
        failures.append(c.REASON_VALIDATOR_MISSING)
    if agent_ready:
        if not inventory.get("agent_read_only_consumer_found"):
            failures.append(c.REASON_AGENT_CONSUMER_MISSING)
        if status != c.STATUS_PRESENT_AND_STATICALLY_VALIDATED:
            failures.append(c.REASON_FALSE_COMPLETION_FORBIDDEN)
    for key in (
        "day1_live_trading_ready",
        "profit_evidence_created",
        "quantum_advantage_evidence_created",
    ):
        if state.get(key) is not False:
            failures.append(c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN)
    return failures


def _validate_legacy(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    legacy = report.get("legacy_roadmap_reconciliation", {})
    if not isinstance(legacy, Mapping):
        return [c.REASON_LEGACY_LABEL_ONLY]
    if legacy.get("old_pr_labels_used_as_completion_proof") is not False:
        failures.append(c.REASON_LEGACY_LABEL_ONLY)
    records = legacy.get("records", [])
    if not isinstance(records, list):
        return failures + [c.REASON_LEGACY_LABEL_ONLY]
    for record in records:
        if not isinstance(record, Mapping):
            failures.append(c.REASON_LEGACY_LABEL_ONLY)
            continue
        found = record.get("repo_artifacts_found")
        supported = record.get("completion_claim_supported_by_artifacts")
        if supported is True and (not isinstance(found, list) or not found):
            failures.append(c.REASON_LEGACY_LABEL_ONLY)
        if record.get("old_label") in {"PR100", "PR101"} and supported is True:
            failures.append(c.REASON_FALSE_COMPLETION_FORBIDDEN)
    return failures


def _validate_sequence(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    routing = report.get("current_sequence_routing", {})
    if not isinstance(routing, Mapping):
        return [c.REASON_SEQUENCE_INSERTION_OWNER_REVIEW]
    observed = routing.get("active_sequence_observed_prefix")
    if not isinstance(observed, list) or observed[:3] != ["PR137", "PR137L", "PR138"]:
        if observed[:4] != ["PR137", c.PR_ID, "PR137L", "PR138"]:
            failures.append(c.REASON_SEQUENCE_INSERTION_OWNER_REVIEW)
    inserted = routing.get("repair_checkpoint_inserted_before_pr137l") is True
    if inserted and observed[:4] != ["PR137", c.PR_ID, "PR137L", "PR138"]:
        failures.append(c.REASON_SEQUENCE_INSERTION_OWNER_REVIEW)
    if routing.get("pr137l_preserved_as_latency_boundary_only") is not True:
        failures.append(c.REASON_SEQUENCE_INSERTION_OWNER_REVIEW)
    if routing.get("pr138_preserved_downstream_of_pr137l") is not True:
        failures.append(c.REASON_SEQUENCE_INSERTION_OWNER_REVIEW)
    if routing.get("current_sequence_atomicrows_bundle_implementation_slot_found") is not True:
        failures.append(c.REASON_SEQUENCE_SLOT_NOT_FOUND)
    return failures


def _validate_quantum_and_market(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("market_scopes") != list(c.CANONICAL_MARKET_SCOPES):
        failures.append(c.REASON_FORECASTEX_ALIAS_FORBIDDEN)
    values = [item for _path, _key, item in _walk(report) if isinstance(item, str)]
    forbidden_exact = set(c.FORBIDDEN_THIRD_VENUE_ALIASES)
    if any(value in forbidden_exact for value in values):
        failures.append(c.REASON_FORECASTEX_ALIAS_FORBIDDEN)
    if report.get("one_global_roadmap_preserved") is not True:
        failures.append(c.REASON_MARKET_ROADMAP_FORK_FORBIDDEN)
    quantum = report.get("quantum_forward_compatibility_audit", {})
    if not isinstance(quantum, Mapping):
        return failures + [c.REASON_QUANTUM_EXECUTION_FORBIDDEN]
    for key in (
        "quantum_execution_created",
        "quantum_optimizer_input_created",
        "quantum_trading_signal_created",
        "quantum_advantage_claim_created",
        "quantum_numeric_defaults_invented",
        "quantum_backend_names_invented",
        "quantum_provider_capabilities_invented",
    ):
        if quantum.get(key) is not False:
            failures.append(c.REASON_QUANTUM_EXECUTION_FORBIDDEN)
    return failures


def _validate_forbidden_authority(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for section_name in ("not_created_flags", "forbidden_diff_checks", "no_qtt_sha_summary"):
        section = report.get(section_name)
        if not isinstance(section, Mapping):
            failures.append(c.REASON_FALSE_COMPLETION_FORBIDDEN)
            continue
        for key, value in section.items():
            if value is not False:
                if key.startswith("atomicrows_") or "bundle" in key or "row" in key or "builder" in key:
                    failures.append(c.REASON_BUNDLE_GENERATION_FORBIDDEN)
                elif "source" in key:
                    failures.append(c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN)
                elif "quantum" in key:
                    failures.append(c.REASON_QUANTUM_EXECUTION_FORBIDDEN)
                elif "sha" in key or "digest" in key or "checksum" in key or "integrity" in key:
                    failures.append(c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY)
                else:
                    failures.append(c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN)
    return failures


def _validate_no_forbidden_keys_or_text(report: Mapping[str, Any], repo_root: Path | None) -> list[str]:
    failures: list[str] = []
    forbidden_key = c.FORBIDDEN_GENERATED_INTEGRITY_KEY
    for path, key, _item in _walk(report):
        if key == forbidden_key:
            failures.append(c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY)
        if ("side" + "car") in key.lower() and _item is not False:
            failures.append(c.REASON_SHA_SIDECAR_REFERENCE_FORBIDDEN)
    text = _json_text(report)
    if re.search(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:", text):
        failures.append(c.REASON_IDEMPOTENCY_FAILURE)
    if repo_root is not None:
        for rel_path in c.PR137R_CREATED_PATHS:
            path = repo_root / rel_path
            if not path.exists() or path.is_dir():
                continue
            artifact_text = path.read_text(encoding="utf-8", errors="ignore")
            if f'"{forbidden_key}"' in artifact_text:
                failures.append(c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY)
    return failures


def success_receipts_for_report(report: Mapping[str, Any]) -> tuple[str, ...]:
    receipts = list(c.SUCCESS_RECEIPTS)
    state = report.get("atomicrows_validation_state", {})
    routing = report.get("current_sequence_routing", {})
    if isinstance(state, Mapping) and state.get("functional_bundle_status") == c.STATUS_PRESENT_AND_STATICALLY_VALIDATED:
        receipts.extend([c.RECEIPT_BUNDLE_VALID, c.RECEIPT_ROWS_PROVEN])
    else:
        receipts.extend([c.RECEIPT_BUNDLE_MISSING, c.RECEIPT_ROWS_NOT_PROVEN])
    if isinstance(routing, Mapping) and routing.get("owner_sequence_assignment_required") is True:
        receipts.append(c.RECEIPT_OWNER_SEQUENCE_ASSIGNMENT)
    return tuple(receipts)


def validate_report_payload(
    report: Mapping[str, Any],
    *,
    repo_root: Path | str | None = None,
    enforce_environment: bool = False,
) -> ValidationOutcome:
    root = Path(repo_root).resolve() if repo_root is not None else None
    failures: list[str] = []
    if report.get("report_type") != c.REPORT_TYPE:
        failures.append(c.REASON_FALSE_COMPLETION_FORBIDDEN)
    if report.get("generated_at_utc") != c.STATIC_TIME:
        failures.append(c.REASON_IDEMPOTENCY_FAILURE)
    if report.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append(c.REASON_FALSE_COMPLETION_FORBIDDEN)
    if report.get("structural_evidence_only") is not True:
        failures.append(c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY)
    if enforce_environment and root is not None:
        failures.extend(_validate_environment(root))
    failures.extend(_validate_required_context(report))
    failures.extend(_validate_bundle_truth(report))
    failures.extend(_validate_legacy(report))
    failures.extend(_validate_sequence(report))
    failures.extend(_validate_quantum_and_market(report))
    failures.extend(_validate_forbidden_authority(report))
    failures.extend(_validate_no_forbidden_keys_or_text(report, root))
    unique_failures = tuple(sorted(set(failures)))
    return ValidationOutcome(
        ok=not unique_failures,
        failures=unique_failures,
        receipts=success_receipts_for_report(report) if not unique_failures else (),
    )
