"""Fail-closed validator for PR155 registry artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools.ci_branch_context import (
    current_branch_context,
    is_explicit_downstream_repair_changed_path,
    is_pr_or_later_branch,
)

from . import constants as c
from .builder import build_outputs
from .io import as_list, json_dump, read_json_object, write_json_file


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _forbidden_bundle_data_path() -> str:
    return c.FORBIDDEN_ATOMICROWS_BUNDLE_STEM + "." + "jsonl"


def _forbidden_bundle_hash_path() -> str:
    return (
        c.FORBIDDEN_ATOMICROWS_BUNDLE_STEM
        + "."
        + "".join(c.ATOMICROWS_BUNDLE_SIDE_CAR_SUFFIX_PARTS)
    )


def _serialized_forbidden_reference_failures(*payloads: Mapping[str, Any]) -> list[str]:
    serialized = "".join(json_dump(payload) for payload in payloads)
    failures: list[str] = []
    if _forbidden_bundle_data_path() in serialized:
        failures.append(c.PR155_FORBIDDEN_ARTIFACT_REFERENCE_CREATED)
    if _forbidden_bundle_hash_path() in serialized:
        failures.append(c.PR155_FORBIDDEN_ARTIFACT_REFERENCE_CREATED)
    return sorted(set(failures))


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _changed_paths(repo_root: Path) -> list[str]:
    status_rc, status_out, _status_err = _git_stdout(
        repo_root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )
    if status_rc != 0:
        return ["<git-status-unavailable>"]
    paths: list[str] = []
    records = [record for record in status_out.split("\0") if record]
    index = 0
    while index < len(records):
        line = records[index]
        if not line.strip():
            index += 1
            continue
        code = line[:2]
        path = line[3:] if len(line) > 3 and line[2] == " " else line[2:].strip()
        paths.append(path.replace("\\", "/"))
        index += 2 if code[:1] in {"R", "C"} or code[1:] in {"R", "C"} else 1
    return sorted(set(paths))


def _branch_allows_pr155_changed_paths(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        155,
        allow_main=False,
        allow_repair=False,
    )


def _is_allowed_changed_path(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized == ".tmp" or normalized.startswith(".tmp/"):
        return True
    if is_explicit_downstream_repair_changed_path(branch, normalized):
        return True
    return normalized in c.CHANGED_PATHS and _branch_allows_pr155_changed_paths(branch)


def _validate_changed_paths(repo_root: Path) -> list[str]:
    branch = current_branch_context(repo_root).branch
    failures: list[str] = []
    sidecar = c.ATOMICROWS_BUNDLE_PATH.with_suffix(
        "." + "".join(c.ATOMICROWS_BUNDLE_SIDE_CAR_SUFFIX_PARTS)
    ).as_posix()
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append(c.PR155_GIT_STATUS_UNAVAILABLE)
            continue
        normalized = path.replace("\\", "/")
        if not _is_allowed_changed_path(normalized, branch):
            failures.append(f"{c.PR155_CHANGED_PATH_OUT_OF_SCOPE}: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append(c.PR155_MASTER_PLAN_MUTATION_DETECTED)
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix() or normalized == sidecar:
            failures.append(c.PR155_ATOMICROWS_BUNDLE_MUTATION_DETECTED)
    return sorted(set(failures))


def _required_top_level_failures(payload: Mapping[str, Any], keys: tuple[str, ...]) -> list[str]:
    return [f"{c.PR155_RECORD_SCHEMA_INVALID}: missing_top_level:{key}" for key in keys if key not in payload]


def _record_schema_failures(record: Mapping[str, Any]) -> list[str]:
    record_id = str(record.get("registry_record_id"))
    failures: list[str] = []
    for field in c.RECORD_REQUIRED_FIELDS:
        if field not in record:
            failures.append(f"{c.PR155_RECORD_SCHEMA_INVALID}: {record_id}: {field}")
    enum_checks = {
        "registry_consumption_state": c.REGISTRY_CONSUMPTION_STATES,
        "agent_assignment_state": c.AGENT_ASSIGNMENT_STATES,
        "default_use_class": c.DEFAULT_USE_CLASSES,
        "atomicrows_compatibility_state": c.ATOMICROWS_COMPATIBILITY_STATES,
        "quantum_forward_compatibility_state": c.QUANTUM_FORWARD_COMPATIBILITY_STATES,
        "optimizer_readiness_hint": c.OPTIMIZER_READINESS_HINTS,
        "latency_path_state": c.LATENCY_PATH_STATES,
    }
    for key, allowed in enum_checks.items():
        if record.get(key) not in allowed:
            failures.append(f"{c.PR155_RECORD_SCHEMA_INVALID}: {record_id}: {key}")
    for field in c.RECORD_ALWAYS_FALSE_FIELDS:
        if record.get(field) is not False:
            failures.append(f"{c.PR155_FORBIDDEN_AUTHORITY_FLAG_TRUE}: {record_id}: {field}")
    if record.get("created_by_pr") != c.PR_ID:
        failures.append(f"{c.PR155_RECORD_SCHEMA_INVALID}: {record_id}: created_by_pr")
    return failures


def _ready_record_failures(record: Mapping[str, Any]) -> list[str]:
    if record.get("agent_consumable_default_ready_flag") is not True:
        return []
    record_id = str(record.get("registry_record_id"))
    failures: list[str] = []
    if record.get("value") is None:
        failures.append(f"{c.PR155_READY_RECORD_VALUE_MISSING}: {record_id}")
    if record.get("source_authority_class") not in c.PR154_ALLOWED_AUTHORITY_CLASSES:
        failures.append(f"{c.PR155_READY_RECORD_AUTHORITY_INVALID}: {record_id}")
    if record.get("source_authority_class") in c.PR154_OFFICIAL_SOURCE_AUTHORITY_CLASSES:
        for field in (
            "source_packet_path_or_null",
            "source_candidate_packet_id_or_null",
            "official_url_or_null",
            "quote_span_or_machine_field_locator_or_null",
        ):
            if not record.get(field):
                failures.append(f"{c.PR155_READY_RECORD_PROVENANCE_MISSING}: {record_id}: {field}")
    if record.get("source_authority_class") in c.PR154_OWNER_INTERNAL_AUTHORITY_CLASSES:
        if not record.get("owner_internal_policy_basis_or_null"):
            failures.append(f"{c.PR155_READY_RECORD_PROVENANCE_MISSING}: {record_id}: owner_internal_policy_basis_or_null")
    if record.get("registry_consumption_state") == c.REGISTRY_READY_NONLIVE_AGENT_ASSIGNMENT_PENDING:
        if record.get("direct_agent_assignment_ready_flag") is not False:
            failures.append(f"{c.PR155_FORBIDDEN_AUTHORITY_FLAG_TRUE}: {record_id}: direct_agent_assignment_ready_flag")
        if record.get("eligible_agent_ids") != []:
            failures.append(f"{c.PR155_RECORD_SCHEMA_INVALID}: {record_id}: eligible_agent_ids")
        if record.get("eligible_agent_basis") != c.ELIGIBLE_AGENT_BASIS_PENDING:
            failures.append(f"{c.PR155_RECORD_SCHEMA_INVALID}: {record_id}: eligible_agent_basis")
    return failures


def _blocked_record_failures(record: Mapping[str, Any]) -> list[str]:
    if record.get("agent_consumable_default_ready_flag") is True:
        return []
    record_id = str(record.get("registry_record_id"))
    completion = _mapping(record.get("blocked_completion_path_if_any"))
    failures: list[str] = []
    for field in c.COMPLETION_PATH_FIELDS:
        value = completion.get(field)
        if field in {"missing_fields", "codex_actionable_completion_steps"}:
            if not as_list(value):
                failures.append(f"{c.PR155_BLOCKED_COMPLETION_PATH_INCOMPLETE}: {record_id}: {field}")
        elif not value:
            failures.append(f"{c.PR155_BLOCKED_COMPLETION_PATH_INCOMPLETE}: {record_id}: {field}")
    if record.get("direct_agent_assignment_ready_flag") is not False:
        failures.append(f"{c.PR155_FORBIDDEN_AUTHORITY_FLAG_TRUE}: {record_id}: direct_agent_assignment_ready_flag")
    if record.get("registry_consumption_state", "").startswith("REGISTRY_DEFAULT_READY"):
        failures.append(f"{c.PR155_RECORD_SCHEMA_INVALID}: {record_id}: blocked_ready_state")
    return failures


def _authority_payload_failures(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    boundary = _mapping(payload.get("non_authority_boundary"))
    for field in c.FORBIDDEN_CREATED_FIELDS:
        if boundary.get(field) is not False:
            failures.append(f"{c.PR155_FORBIDDEN_AUTHORITY_FLAG_TRUE}: {field}")
    for field in c.REPORT_FALSE_AUTHORITY_FIELDS:
        if payload.get(field) is not False and field in payload:
            if field.startswith("atomicrows_"):
                failures.append(c.PR155_ATOMICROWS_BUNDLE_AUTHORITY_CREATED)
            else:
                failures.append(c.PR155_QTT_SHA_AUTHORITY_CREATED)
    for key, value in _walk(payload):
        lowered = key.lower()
        if ("sha_authority" in lowered or "hash_authority" in lowered) and value is not False:
            failures.append(c.PR155_QTT_SHA_AUTHORITY_CREATED)
        if (
            lowered.endswith(("_digest", "_checksum"))
            and key not in c.ALLOWED_SOURCE_EVIDENCE_PROVENANCE_DIGEST_KEYS
            and value not in (False, None)
        ):
            failures.append(c.PR155_QTT_SHA_AUTHORITY_CREATED)
    return sorted(set(failures))


def validate_payloads(
    registry: Mapping[str, Any],
    report: Mapping[str, Any],
    build_failures: Sequence[str] = (),
) -> list[str]:
    failures = list(build_failures)
    failures.extend(_required_top_level_failures(registry, c.REGISTRY_TOP_LEVEL_KEYS))
    failures.extend(_required_top_level_failures(report, c.REPORT_TOP_LEVEL_KEYS))
    if registry.get("registry_type") != c.REGISTRY_TYPE:
        failures.append(c.PR155_RECORD_SCHEMA_INVALID)
    if report.get("report_type") != c.REPORT_TYPE:
        failures.append(c.PR155_RECORD_SCHEMA_INVALID)
    if registry.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append(c.PR155_RECORD_SCHEMA_INVALID)
    if report.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append(c.PR155_RECORD_SCHEMA_INVALID)

    records = [_mapping(record) for record in as_list(registry.get("records"))]
    blocked_records = [_mapping(record) for record in as_list(registry.get("blocked_records"))]
    record_ids = [str(record.get("registry_record_id")) for record in records]
    if record_ids != sorted(record_ids):
        failures.append(c.PR155_RECORD_SCHEMA_INVALID)
    if len(record_ids) != len(set(record_ids)):
        failures.append(c.PR155_PR154_RECORD_ID_DUPLICATE)
    if [str(record.get("registry_record_id")) for record in blocked_records] != sorted(
        str(record.get("registry_record_id")) for record in blocked_records
    ):
        failures.append(c.PR155_RECORD_SCHEMA_INVALID)

    expected_counts = {
        "input_pr154_total_records": c.EXPECTED_INPUT_PR154_TOTAL_RECORDS,
        "agent_consumable_default_ready_count": c.EXPECTED_MATERIALIZED_RECORDS,
        "non_consumable_blocked_count": c.EXPECTED_BLOCKED_RECORDS,
        "official_source_materialized_default_count": (
            c.EXPECTED_OFFICIAL_SOURCE_MATERIALIZED_DEFAULTS
        ),
        "owner_internal_control_plane_default_count": (
            c.EXPECTED_OWNER_INTERNAL_CONTROL_PLANE_DEFAULTS
        ),
        "live_order_ready_count": 0,
        "runtime_ready_count": 0,
        "connector_semantic_bound_count": 0,
        "replay_tested_count": 0,
        "paper_approved_count": 0,
        "quantum_execution_evidence_count": 0,
        "profit_evidence_count": 0,
    }
    counts = _mapping(registry.get("counts"))
    for key, expected_value in expected_counts.items():
        if counts.get(key) != expected_value:
            failures.append(f"{c.PR155_PR154_COUNT_MISMATCH}: registry:{key}")
        if report.get(key) != expected_value:
            failures.append(f"{c.PR155_PR154_COUNT_MISMATCH}: report:{key}")

    if report.get("direct_agent_assignment_ready_count") != 0:
        failures.append(c.PR155_FORBIDDEN_AUTHORITY_FLAG_TRUE)
    if report.get("agent_assignment_pending_count") != c.EXPECTED_MATERIALIZED_RECORDS:
        failures.append(f"{c.PR155_PR154_COUNT_MISMATCH}: agent_assignment_pending_count")

    for record in records:
        failures.extend(_record_schema_failures(record))
        failures.extend(_ready_record_failures(record))
        failures.extend(_blocked_record_failures(record))
    failures.extend(_authority_payload_failures(registry))
    failures.extend(_authority_payload_failures(report))
    failures.extend(_serialized_forbidden_reference_failures(registry, report))

    preflight = _mapping(report.get("control_plane_preflight"))
    required_preflight_flags = (
        "pr_identity_roster_consumed",
        "roadmap_execution_state_consumed",
        "launch_readiness_policy_consumed",
        "route_triage_consumed",
        "section_crosswalk_or_successor_consumed",
        "market_specific_index_consumed",
        "command_action_matrix_consumed",
        "atomicrows_reconciliation_consumed",
        "atomicrows_semantic_contract_consumed",
        "pr155_allowed_to_continue",
    )
    for flag in required_preflight_flags:
        if preflight.get(flag) is not True:
            failures.append(f"{c.PR155_ORCHESTRATION_ARTIFACT_MISSING}: {flag}")
    alias = _mapping(preflight.get("alias_resolution_applied"))
    if not alias.get("alias_exists") and not alias.get("successor_used"):
        failures.append(c.PR155_ORCHESTRATION_CROSSWALK_MISSING)

    serialized = json_dump(registry) + json_dump(report)
    if "C:\\Users\\" in serialized or Path.cwd().as_posix() in serialized:
        failures.append(c.PR155_RECORD_SCHEMA_INVALID)
    branch_rc, branch_out, _branch_err = _git_stdout(Path.cwd(), ["branch", "--show-current"])
    if branch_rc == 0 and branch_out.strip() and branch_out.strip() in serialized:
        failures.append(c.PR155_RECORD_SCHEMA_INVALID)
    return sorted(set(str(failure) for failure in failures if failure))


def validate_repository_artifacts(
    repo_root: Path | str,
    *,
    write_report: bool = False,
    check_only: bool = False,
    strict: bool = False,
) -> list[str]:
    root = Path(repo_root).resolve()
    first = build_outputs(root)
    second = build_outputs(root)
    failures: list[str] = []
    if json_dump(first.registry) != json_dump(second.registry):
        failures.append(c.PR155_REGISTRY_STALE_OR_NONDETERMINISTIC)
    if json_dump(first.report) != json_dump(second.report):
        failures.append(c.PR155_REPORT_STALE_OR_NONDETERMINISTIC)

    if write_report and not check_only:
        write_json_file(root / c.REGISTRY_PATH, first.registry)
        write_json_file(root / c.REPORT_PATH, first.report)

    failures.extend(validate_payloads(first.registry, first.report, first.failures))

    for rel_path, expected, stale_code in (
        (c.REGISTRY_PATH, first.registry, c.PR155_REGISTRY_STALE_OR_NONDETERMINISTIC),
        (c.REPORT_PATH, first.report, c.PR155_REPORT_STALE_OR_NONDETERMINISTIC),
    ):
        try:
            actual = read_json_object(root / rel_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"{stale_code}: {rel_path.as_posix()}: {exc}")
            continue
        if actual != expected:
            failures.append(stale_code)
            failures.extend(validate_payloads(actual, actual if rel_path == c.REPORT_PATH else first.report))

    failures.extend(_validate_changed_paths(root))
    if strict:
        failures.extend(_serialized_forbidden_reference_failures(first.registry, first.report))
    return sorted(set(failures))
