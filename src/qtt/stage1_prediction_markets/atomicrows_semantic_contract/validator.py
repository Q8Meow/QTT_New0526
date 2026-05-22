"""Fail-closed validator for PR138 AtomicRows semantic row-contract artifacts."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from tools import ci_branch_context

from . import constants as c
from .fixtures import build_fixture_collection
from .model import ValidationOutcome
from .report import build_index, build_report, evidence_snapshot
from .schema import build_contract, build_json_schema


def _walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, str(key), item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _string_values(value: Any) -> list[str]:
    return [item for _path, _key, item in _walk(value) if isinstance(item, str)]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _validate_environment(report: Mapping[str, Any], repo_root: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    receipts: list[str] = []
    if (
        report.get("owner_verified_baseline_receipt_consumed") is True
        and report.get("sandbox_bootstrap_fallback_used") is True
    ):
        receipts.append(c.PR138_REASON_SANDBOX_BOOTSTRAP_FALLBACK_USED)
        return failures, receipts

    branch_rc, branch, _branch_err = _git_stdout(repo_root, ["branch", "--show-current"])
    ci_merge_ref = ci_branch_context.github_actions_pull_request_detached_context_active(
        branch_returncode=branch_rc,
        branch=branch,
    )
    if ci_merge_ref:
        receipts.append(c.PR138_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY)
        return failures, receipts
    if ci_branch_context.github_actions_main_push_context_active():
        receipts.append(c.PR138_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY)
        return failures, receipts
    if branch_rc != 0 or branch != c.BRANCH:
        failures.append(c.PR138_REASON_BRANCH_MISMATCH)

    base_rc, _base_out, _base_err = _git_stdout(
        repo_root,
        ["cat-file", "-e", f"{c.BASELINE_CHECKPOINT}^{{commit}}"],
    )
    ancestor_rc, _ancestor_out, _ancestor_err = _git_stdout(
        repo_root,
        ["merge-base", "--is-ancestor", c.BASELINE_CHECKPOINT, "HEAD"],
    )
    if base_rc != 0 or ancestor_rc != 0:
        failures.append(c.PR138_REASON_LOCAL_BASELINE_NOT_DESCENDANT)
    return failures, receipts


def _expected_group_fields() -> dict[str, tuple[str, ...]]:
    return {group_id: tuple(fields) for group_id, fields in c.REQUIRED_FIELDS_BY_GROUP}


def _validate_no_forbidden_alias_values(payload: Mapping[str, Any]) -> list[str]:
    forbidden = set(c.FORBIDDEN_ALIASES)
    return (
        [c.PR138_REASON_FORBIDDEN_VENUE_ALIAS]
        if any(value in forbidden for value in _string_values(payload))
        else []
    )


def _validate_reason_codes_are_centralized(payload: Mapping[str, Any]) -> list[str]:
    allowed = set(c.REASON_CODES)
    failures: list[str] = []
    for _path, key, item in _walk(payload):
        if key == "validator_reason_codes" and isinstance(item, list):
            for reason_code in item:
                if reason_code not in allowed:
                    failures.append(c.PR138_REASON_REASON_CODE_NOT_CENTRALIZED)
        if key == "expected_reason_codes" and isinstance(item, list):
            for reason_code in item:
                if reason_code not in allowed:
                    failures.append(c.PR138_REASON_REASON_CODE_NOT_CENTRALIZED)
    return failures


def validate_contract_payload(contract: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if contract.get("pr_id") != c.PR_ID or contract.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
    if contract.get("baseline_checkpoint") != c.BASELINE_CHECKPOINT:
        failures.append(c.PR138_REASON_OLDER_BASELINE_CHECKPOINT_REFERENCE_FORBIDDEN)
    if contract.get("required_field_group_count") != c.REQUIRED_FIELD_GROUP_COUNT:
        failures.append(c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING)
    if contract.get("required_field_count") != c.REQUIRED_FIELD_COUNT:
        failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)
    if contract.get("semantic_row_values_materialized_by_pr138") is not False:
        failures.append(c.PR138_REASON_BUNDLE_MUTATION_FORBIDDEN)
    if contract.get("canonical_stage1_market_scopes") != list(c.CANONICAL_STAGE1_MARKET_SCOPES):
        failures.append(c.PR138_REASON_FORBIDDEN_VENUE_ALIAS)

    groups = contract.get("field_groups", [])
    if not isinstance(groups, list):
        return failures + [c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING]
    group_ids = [group.get("field_group_id") for group in groups if isinstance(group, Mapping)]
    if len(group_ids) != len(set(group_ids)):
        failures.append(c.PR138_REASON_FIELD_GROUP_DUPLICATE)
    for expected_group_id in c.REQUIRED_FIELD_GROUP_IDS:
        if group_ids.count(expected_group_id) != 1:
            failures.append(c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING)
    if len(group_ids) != c.REQUIRED_FIELD_GROUP_COUNT:
        failures.append(c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING)
    expected_fields_by_group = _expected_group_fields()
    for group in groups:
        if not isinstance(group, Mapping):
            failures.append(c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING)
            continue
        group_id = str(group.get("field_group_id"))
        expected_fields = expected_fields_by_group.get(group_id)
        fields = tuple(group.get("fields", [])) if isinstance(group.get("fields"), list) else ()
        if expected_fields is None or fields != expected_fields:
            failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)

    fields = contract.get("fields", [])
    if not isinstance(fields, list):
        return failures + [c.PR138_REASON_REQUIRED_FIELD_MISSING]
    field_ids = [field.get("field_id") for field in fields if isinstance(field, Mapping)]
    if len(field_ids) != len(set(field_ids)):
        failures.append(c.PR138_REASON_FIELD_DUPLICATE)
    if len(field_ids) != c.REQUIRED_FIELD_COUNT:
        failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)
    for expected_field in c.REQUIRED_FIELD_IDS:
        if field_ids.count(expected_field) != 1:
            failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)

    expected_group_by_field = {
        field: group_id for group_id, fields_for_group in c.REQUIRED_FIELDS_BY_GROUP for field in fields_for_group
    }
    for field in fields:
        if not isinstance(field, Mapping):
            failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)
            continue
        field_id = str(field.get("field_id"))
        if field.get("canonical_name") != field_id:
            failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)
        if field.get("field_group_id") != expected_group_by_field.get(field_id):
            failures.append(c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING)
        if not field.get("authority_boundary"):
            failures.append(c.PR138_REASON_FIELD_WITHOUT_AUTHORITY_BOUNDARY)
        if field.get("future_enrichment_phase") not in c.FUTURE_PR_PHASE_VALUES:
            failures.append(c.PR138_REASON_FUTURE_PHASE_MISSING)
        for trace_key, reason in (
            ("route_triage_trace", c.PR138_REASON_FIELD_WITHOUT_CROSSWALK_TRACE),
            (
                "full_master_plan_section_crosswalk_trace",
                c.PR138_REASON_FIELD_WITHOUT_CROSSWALK_TRACE,
            ),
            (
                "market_specific_section_index_trace",
                c.PR138_REASON_FIELD_WITHOUT_MARKET_INDEX_TRACE,
            ),
            (
                "command_action_matrix_trace",
                c.PR138_REASON_FIELD_WITHOUT_COMMAND_MATRIX_TRACE,
            ),
        ):
            trace = _mapping(field.get(trace_key))
            if trace.get("trace_state") != "TRACE_CONSUMED_READ_ONLY":
                failures.append(reason)
        for false_field in (
            "populated_by_pr138",
            "atomicrows_bundle_mutation_required_in_pr138",
            "row_family_source_mutation_required_in_pr138",
            "live_authority_created_by_field",
            "order_authority_created_by_field",
            "profit_evidence_created_by_field",
            "quantum_execution_created_by_field",
            "source_acceptance_created_by_field",
            "connector_semantic_binding_created_by_field",
            "runtime_cash_authority_created_by_field",
            "scoring_ranking_arbitration_created_by_field",
            "trading_signal_created_by_field",
            "hot_path_dependency_created_by_field",
        ):
            if field.get(false_field) is not False:
                failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
        if field.get("allowed_market_scopes") != list(c.CANONICAL_STAGE1_MARKET_SCOPES):
            failures.append(c.PR138_REASON_FORBIDDEN_VENUE_ALIAS)
        if field.get("canonical_venue_scope_values") != list(c.CANONICAL_STAGE1_MARKET_SCOPES):
            failures.append(c.PR138_REASON_FORBIDDEN_VENUE_ALIAS)
        if field.get("allowed_placeholder_states") != list(c.ALLOWED_PLACEHOLDER_STATES):
            failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
    failures.extend(_validate_reason_codes_are_centralized(contract))
    failures.extend(_validate_no_forbidden_alias_values(contract))
    return sorted(set(failures))


def _reason_for_report_claim(field: str) -> str:
    if "final_readiness" in field:
        return c.PR138_REASON_FINAL_READINESS_NOT_CREATED
    if "day1_live" in field or "live_order" in field:
        return c.PR138_REASON_DAY1_LIVE_READINESS_NOT_CREATED
    if "order" in field:
        return c.PR138_REASON_ORDER_AUTHORITY_FORBIDDEN
    if "profit" in field:
        return c.PR138_REASON_PROFIT_EVIDENCE_FORBIDDEN
    if "source_retrieval" in field:
        return c.PR138_REASON_SOURCE_RETRIEVAL_FORBIDDEN
    if "source_acceptance" in field:
        return c.PR138_REASON_SOURCE_ACCEPTANCE_FORBIDDEN
    if "connector" in field:
        return c.PR138_REASON_CONNECTOR_SEMANTIC_BINDING_FORBIDDEN
    if "runtime_cash" in field:
        return c.PR138_REASON_RUNTIME_CASH_AUTHORITY_FORBIDDEN
    if "replay" in field:
        return c.PR138_REASON_REPLAY_EXECUTION_FORBIDDEN
    if "paper" in field:
        return c.PR138_REASON_PAPER_EXECUTION_FORBIDDEN
    if "scoring" in field or "ranking" in field or "arbitration" in field:
        return c.PR138_REASON_SCORING_RANKING_ARBITRATION_FORBIDDEN
    if "trading_signal" in field:
        return c.PR138_REASON_TRADING_SIGNAL_FORBIDDEN
    if "quantum_simulator" in field:
        return c.PR138_REASON_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN
    if "quantum_optimizer" in field:
        return c.PR138_REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN
    if "quantum_advantage" in field:
        return c.PR138_REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN
    if "quantum" in field:
        return c.PR138_REASON_QUANTUM_EXECUTION_FORBIDDEN
    if "bundle_mutated" in field:
        return c.PR138_REASON_BUNDLE_MUTATION_FORBIDDEN
    if "row_family" in field:
        return c.PR138_REASON_ROW_FAMILY_SOURCE_MUTATION_FORBIDDEN
    if "bundle_builder" in field:
        return c.PR138_REASON_BUILDER_MUTATION_FORBIDDEN
    if "cryptographic" in field:
        return c.PR138_REASON_QTT_GENERATED_CRYPTOGRAPHIC_AUTHORITY_FORBIDDEN
    return c.PR138_REASON_REPORT_CLAIM_FORBIDDEN


def _validate_contract_default_flag_values(report: Mapping[str, Any]) -> list[str]:
    defaults = _mapping(report.get("contract_level_default_flag_values"))
    failures: list[str] = []
    expected_reason = {
        "live_use_allowed_flag": c.PR138_REASON_LIVE_USE_FLAG_TRUE_FORBIDDEN,
        "order_authority_created_flag": c.PR138_REASON_ORDER_AUTHORITY_FLAG_TRUE_FORBIDDEN,
        "profit_evidence_created_flag": c.PR138_REASON_PROFIT_EVIDENCE_FLAG_TRUE_FORBIDDEN,
        "quantum_backend_execution_allowed_flag": (
            c.PR138_REASON_QUANTUM_BACKEND_EXECUTION_FLAG_TRUE_FORBIDDEN
        ),
        "external_fact_authority_flag": (
            c.PR138_REASON_EXTERNAL_FACT_AUTHORITY_TRUE_FORBIDDEN_WITHOUT_ACCEPTED_SOURCE_PACKET
        ),
    }
    for field in c.CONTRACT_DEFAULT_FALSE_FLAG_FIELDS:
        if defaults.get(field) is not False:
            failures.append(expected_reason[field])
    return failures


def _validate_no_cryptographic_authority_keys(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for _path, key, item in _walk(payload):
        key_lower = key.lower()
        if key_lower == "baseline_checkpoint":
            continue
        if "cryptographic" in key_lower and item is not False:
            failures.append(c.PR138_REASON_QTT_GENERATED_CRYPTOGRAPHIC_AUTHORITY_FORBIDDEN)
        if key_lower.endswith(("_digest", "_checksum")) or key_lower.endswith("_hash"):
            failures.append(c.PR138_REASON_QTT_GENERATED_CRYPTOGRAPHIC_AUTHORITY_FORBIDDEN)
    return failures


def validate_report_payload(
    report: Mapping[str, Any],
    *,
    repo_root: Path | str | None = None,
    enforce_environment: bool = False,
    enforce_protected_diff: bool = False,
) -> ValidationOutcome:
    root = Path(repo_root).resolve() if repo_root is not None else None
    failures: list[str] = []
    receipts: list[str] = []
    if report.get("report_type") != c.REPORT_TYPE:
        failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
    if report.get("pr_id") != c.PR_ID:
        failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
    if report.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
    if report.get("baseline_checkpoint") != c.BASELINE_CHECKPOINT:
        failures.append(c.PR138_REASON_OLDER_BASELINE_CHECKPOINT_REFERENCE_FORBIDDEN)
    if report.get("generated_at_utc") != c.STATIC_TIME:
        failures.append(c.PR138_REASON_IDEMPOTENCY_FAILURE)
    if report.get("owner_verified_baseline_receipt_consumed") is True and report.get(
        "sandbox_bootstrap_fallback_used"
    ) is not True:
        failures.append(c.PR138_REASON_SANDBOX_BOOTSTRAP_FALLBACK_USED)
    if report.get("required_field_group_count") != c.REQUIRED_FIELD_GROUP_COUNT:
        failures.append(c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING)
    if report.get("required_field_count") != c.REQUIRED_FIELD_COUNT:
        failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)
    if report.get("atomicrows_bundle_detected_from_existing_repo_evidence") is not True:
        failures.append(c.PR138_REASON_BUNDLE_MUTATION_FORBIDDEN)
    if report.get("atomicrows_row_count_from_existing_evidence") != c.EXPECTED_ATOMICROWS_ROW_COUNT:
        failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)
    if report.get("current_bundle_basic_schema_validation_status") != (
        c.CURRENT_BUNDLE_BASIC_SCHEMA_VALIDATION_STATUS_PASSED
    ):
        failures.append(c.PR138_REASON_REQUIRED_FIELD_MISSING)
    for evidence_flag, reason in (
        ("pr137r_evidence_consumed_read_only", c.PR138_REASON_PR137R_EVIDENCE_MISSING),
        ("pr137l_evidence_consumed_read_only", c.PR138_REASON_PR137L_EVIDENCE_MISSING),
        (
            "route_triage_evidence_consumed_read_only",
            c.PR138_REASON_ROUTE_TRIAGE_EVIDENCE_MISSING,
        ),
        (
            "full_master_plan_section_crosswalk_consumed_read_only",
            c.PR138_REASON_SECTION_CROSSWALK_EVIDENCE_MISSING,
        ),
        (
            "market_specific_section_indexes_consumed_read_only",
            c.PR138_REASON_MARKET_INDEX_EVIDENCE_MISSING,
        ),
        (
            "command_action_matrix_consumed_read_only",
            c.PR138_REASON_COMMAND_ACTION_MATRIX_EVIDENCE_MISSING,
        ),
    ):
        if report.get(evidence_flag) is not True:
            failures.append(reason)
    if report.get("semantic_row_contract_defined_by_pr138") is not True:
        failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
    if report.get("semantic_row_values_materialized_by_pr138") is not False:
        failures.append(c.PR138_REASON_BUNDLE_MUTATION_FORBIDDEN)
    if report.get("next_required_prs") != c.NEXT_REQUIRED_PRS:
        failures.append(c.PR138_REASON_FUTURE_PHASE_MISSING)
    if "FORECASTEX_IBKR" not in _string_values(report):
        failures.append(c.PR138_REASON_FORBIDDEN_VENUE_ALIAS)

    for flag in c.REPORT_NO_CLAIM_FLAG_NAMES:
        if report.get(flag) is not False:
            failures.append(_reason_for_report_claim(flag))
    if report.get("new_atomicrows_bundle_sidecar_reference_created_by_pr138") is not False:
        failures.append(c.PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN)
    failures.extend(_validate_contract_default_flag_values(report))
    failures.extend(_validate_no_forbidden_alias_values(report))
    failures.extend(_validate_no_cryptographic_authority_keys(report))
    if enforce_environment and root is not None:
        environment_failures, environment_receipts = _validate_environment(report, root)
        failures.extend(environment_failures)
        receipts.extend(environment_receipts)
    if enforce_protected_diff and root is not None:
        failures.extend(_protected_diff_failures(root))
        failures.extend(_artifact_reference_failures(root))
    unique_failures = tuple(sorted(set(failures)))
    return ValidationOutcome(
        ok=not unique_failures,
        failures=unique_failures,
        receipts=(tuple(c.SUCCESS_RECEIPTS) + tuple(receipts) if not unique_failures else ()),
    )


def _reason_for_changed_path(path: str) -> str | None:
    normalized = path.replace("\\", "/")
    if normalized == "docs/master_plan/QTT_MasterPlan_Current.md":
        return c.PR138_REASON_MASTER_PLAN_EDIT_FORBIDDEN
    if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix():
        return c.PR138_REASON_BUNDLE_MUTATION_FORBIDDEN
    if normalized.startswith("docs/master_plan/atomic_rows/pr98_row_family_sources/"):
        return c.PR138_REASON_ROW_FAMILY_SOURCE_MUTATION_FORBIDDEN
    if normalized.startswith("docs/master_plan/atomic_rows/exact_row_sources/"):
        return c.PR138_REASON_ROW_FAMILY_SOURCE_MUTATION_FORBIDDEN
    if normalized in c.BUNDLE_BUILDER_PATHS:
        return c.PR138_REASON_BUILDER_MUTATION_FORBIDDEN
    lowered = normalized.lower()
    if "atomicrows.bundle." in lowered or "atomicrows_bundle_forbidden_sidecar" in lowered:
        return c.PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN
    return None


def _protected_diff_failures_for_paths(paths: Sequence[str]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        reason = _reason_for_changed_path(path)
        if reason is not None:
            failures.append(reason)
    return sorted(set(failures))


def _protected_diff_failures(repo_root: Path) -> list[str]:
    paths: list[str] = []
    diff_rc, diff_out, _diff_err = _git_stdout(repo_root, ["diff", "--name-only"])
    if diff_rc != 0:
        return [c.PR138_REASON_REPORT_CLAIM_FORBIDDEN]
    if diff_out:
        paths.extend(line.strip() for line in diff_out.splitlines() if line.strip())
    status_rc, status_out, _status_err = _git_stdout(repo_root, ["status", "--short"])
    if status_rc != 0:
        return [c.PR138_REASON_REPORT_CLAIM_FORBIDDEN]
    for line in status_out.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:].strip().replace("\\", "/"))
    return _protected_diff_failures_for_paths(paths)


def _artifact_reference_failures(repo_root: Path) -> list[str]:
    failures: list[str] = []
    tracked_existing_paths = {
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/run_validation_gates.py",
    }
    for rel_path in c.PR138_CREATED_OR_UPDATED_PATHS:
        path = repo_root / rel_path
        if not path.exists() or path.is_dir():
            continue
        if rel_path in tracked_existing_paths:
            diff_rc, diff_out, _diff_err = _git_stdout(
                repo_root,
                ["diff", "--unified=0", "--", rel_path],
            )
            if diff_rc == 0:
                added_lines = [
                    line
                    for line in diff_out.splitlines()
                    if line.startswith("+") and not line.startswith("+++")
                ]
                if any(
                    re.search(r"AtomicRows\.bundle\.(?!jsonl\b)", line)
                    for line in added_lines
                ):
                    failures.append(
                        c.PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN
                    )
                continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"AtomicRows\.bundle\.(?!jsonl\b)", text):
            failures.append(c.PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN)
    return sorted(set(failures))


def _find_field(contract: dict[str, Any], field_id: str) -> dict[str, Any]:
    for field in contract.get("fields", []):
        if isinstance(field, dict) and field.get("field_id") == field_id:
            return field
    raise KeyError(field_id)


def _find_group(contract: dict[str, Any], field_group_id: str) -> dict[str, Any]:
    for group in contract.get("field_groups", []):
        if isinstance(group, dict) and group.get("field_group_id") == field_group_id:
            return group
    raise KeyError(field_group_id)


def _apply_fixture_mutation(
    *,
    contract: Mapping[str, Any],
    report: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    payload_type = str(fixture.get("payload_type"))
    mutation = _mapping(fixture.get("mutation"))
    operation = str(mutation.get("operation", ""))
    if payload_type == "contract":
        payload = deepcopy(dict(contract))
        if operation == "remove_field":
            payload["fields"] = [
                field for field in payload["fields"] if field.get("field_id") != mutation.get("field_id")
            ]
        elif operation == "remove_field_group":
            payload["field_groups"] = [
                group
                for group in payload["field_groups"]
                if group.get("field_group_id") != mutation.get("field_group_id")
            ]
        elif operation == "duplicate_field":
            payload["fields"].append(deepcopy(_find_field(payload, str(mutation["field_id"]))))
        elif operation == "duplicate_field_group":
            payload["field_groups"].append(
                deepcopy(_find_group(payload, str(mutation["field_group_id"])))
            )
        elif operation == "append_accepted_market_scope":
            field = _find_field(payload, str(mutation["field_id"]))
            field["allowed_market_scopes"].append(str(mutation["accepted_value"]))
        elif operation == "append_reason_code":
            field = _find_field(payload, str(mutation["field_id"]))
            field["validator_reason_codes"].append(str(mutation["reason_code"]))
        elif operation == "remove_field_key":
            field = _find_field(payload, str(mutation["field_id"]))
            field.pop(str(mutation["key"]), None)
        elif operation == "set_trace_state":
            field = _find_field(payload, str(mutation["field_id"]))
            trace = field[str(mutation["trace_key"])]
            trace["trace_state"] = str(mutation["trace_state"])
        return payload_type, payload
    if payload_type == "report":
        payload = deepcopy(dict(report))
        if operation == "set_default_flag":
            payload["contract_level_default_flag_values"][str(mutation["field"])] = mutation.get("value")
        elif operation == "set_report_flag":
            payload[str(mutation["field"])] = mutation.get("value")
        elif operation == "add_report_key":
            payload[str(mutation["key"])] = mutation.get("value")
        return payload_type, payload
    if payload_type == "protected_diff":
        return payload_type, dict(mutation)
    return payload_type, {}


def validate_fixture_collection(
    fixture_collection: Mapping[str, Any],
    *,
    valid_contract: Mapping[str, Any],
    valid_report: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    fixtures = fixture_collection.get("fixtures", [])
    if not isinstance(fixtures, list):
        return [c.PR138_REASON_SEMANTIC_CONTRACT_ONLY]
    for fixture in fixtures:
        if not isinstance(fixture, Mapping):
            failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
            continue
        if fixture.get("fixture_polarity") not in c.FIXTURE_POLARITY_VALUES:
            failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
            continue
        payload_type, payload = _apply_fixture_mutation(
            contract=valid_contract,
            report=valid_report,
            fixture=fixture,
        )
        if payload_type == "contract":
            fixture_failures = validate_contract_payload(payload)
        elif payload_type == "report":
            fixture_failures = list(validate_report_payload(payload).failures)
        elif payload_type == "protected_diff":
            if payload.get("operation") == "simulate_changed_path":
                fixture_failures = _protected_diff_failures_for_paths([str(payload.get("path"))])
            elif payload.get("operation") == "simulate_forbidden_sidecar_reference":
                fixture_failures = [
                    c.PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN
                ]
            else:
                fixture_failures = [c.PR138_REASON_REPORT_CLAIM_FORBIDDEN]
        else:
            fixture_failures = [c.PR138_REASON_SEMANTIC_CONTRACT_ONLY]
        expected = set(fixture.get("expected_reason_codes", []))
        if fixture.get("fixture_polarity") == "VALID_POSITIVE":
            if fixture_failures:
                failures.extend(fixture_failures)
        elif not expected.issubset(set(fixture_failures)):
            failures.append(c.PR138_REASON_SEMANTIC_CONTRACT_ONLY)
    failures.extend(_validate_reason_codes_are_centralized(fixture_collection))
    return sorted(set(failures))


def validate_repository_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    evidence = evidence_snapshot(root)
    expected_contract = build_contract(evidence)
    expected_report = build_report(root)
    expected_index = build_index(expected_report)
    expected_schema = build_json_schema()
    expected_fixture = build_fixture_collection()
    artifact_expectations = (
        (root / c.INVENTORY_PATH, expected_contract),
        (root / c.REPORT_PATH, expected_report),
        (root / c.INDEX_PATH, expected_index),
        (root / c.SCHEMA_PATH, expected_schema),
        (root / c.FIXTURE_PATH, expected_fixture),
    )
    for path, expected in artifact_expectations:
        if not path.exists():
            failures.append(c.PR138_REASON_IDEMPOTENCY_FAILURE)
            continue
        try:
            actual = _load_json(path)
        except (OSError, json.JSONDecodeError, ValueError):
            failures.append(c.PR138_REASON_IDEMPOTENCY_FAILURE)
            continue
        if actual != expected:
            failures.append(c.PR138_REASON_IDEMPOTENCY_FAILURE)
    failures.extend(validate_contract_payload(expected_contract))
    failures.extend(
        validate_fixture_collection(
            expected_fixture,
            valid_contract=expected_contract,
            valid_report=expected_report,
        )
    )
    return sorted(set(failures))
