"""Fail-closed validator for PR156 registry and report artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from tools.ci_branch_context import (
    current_branch_context,
    is_explicit_downstream_repair_changed_path,
    is_pr_or_later_branch,
)

from . import constants as c
from .builder import build_outputs
from .io import as_list, as_mapping, json_dump, read_json_object, write_json_file


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


def _string_tokens(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _string_tokens(item)
    elif isinstance(value, list):
        for item in value:
            yield from _string_tokens(item)
    elif isinstance(value, str):
        yield value


def _branch_name_reference_present(branch: str, *payloads: Mapping[str, Any]) -> bool:
    if not branch:
        return False
    branch_reference = re.compile(
        rf"(?<![A-Za-z0-9_-]){re.escape(branch)}(?![A-Za-z0-9_-])"
    )
    return any(
        branch_reference.search(token)
        for payload in payloads
        for token in _string_tokens(payload)
    )


def _forbidden_bundle_data_path() -> str:
    return (
        ".".join(c.FORBIDDEN_ATOMICROWS_BUNDLE_STEM_PARTS)
        + "."
        + c.FORBIDDEN_ATOMICROWS_BUNDLE_DATA_SUFFIX
    )


def _forbidden_bundle_hash_path() -> str:
    return (
        ".".join(c.FORBIDDEN_ATOMICROWS_BUNDLE_STEM_PARTS)
        + "."
        + "".join(c.FORBIDDEN_ATOMICROWS_BUNDLE_HASH_SUFFIX_PARTS)
    )


def _serialized_forbidden_reference_failures(*payloads: Mapping[str, Any]) -> list[str]:
    serialized = "".join(json_dump(payload) for payload in payloads)
    failures: list[str] = []
    if _forbidden_bundle_data_path() in serialized:
        failures.append(c.PR156_FORBIDDEN_ARTIFACT_REFERENCE_CREATED)
    if _forbidden_bundle_hash_path() in serialized:
        failures.append(c.PR156_FORBIDDEN_ARTIFACT_REFERENCE_CREATED)
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


def _branch_allows_pr156_changed_paths(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        156,
        allow_main=False,
        allow_repair=False,
    )


def _is_allowed_changed_path(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized == ".tmp" or normalized.startswith(".tmp/"):
        return True
    if is_explicit_downstream_repair_changed_path(branch, normalized):
        return True
    return normalized in c.CHANGED_PATHS and _branch_allows_pr156_changed_paths(branch)


def _validate_changed_paths(repo_root: Path) -> list[str]:
    branch = current_branch_context(repo_root).branch
    failures: list[str] = []
    sidecar = c.ATOMICROWS_BUNDLE_PATH.with_suffix(
        "." + "".join(c.FORBIDDEN_ATOMICROWS_BUNDLE_HASH_SUFFIX_PARTS)
    ).as_posix()
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append(c.PR156_GIT_STATUS_UNAVAILABLE)
            continue
        normalized = path.replace("\\", "/")
        if not _is_allowed_changed_path(normalized, branch):
            failures.append(f"{c.PR156_CHANGED_PATH_OUT_OF_SCOPE}: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append(c.PR156_MASTER_PLAN_MUTATION_DETECTED)
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix() or normalized == sidecar:
            failures.append(c.PR156_ATOMICROWS_BUNDLE_MUTATION_DETECTED)
    return sorted(set(failures))


def _required_top_level_failures(payload: Mapping[str, Any], keys: tuple[str, ...]) -> list[str]:
    return [
        f"{c.PR156_RECORD_SCHEMA_INVALID}: missing_top_level:{key}"
        for key in keys
        if key not in payload
    ]


def _enum_failure(
    record: Mapping[str, Any],
    record_id: str,
    field: str,
    allowed: tuple[str, ...],
) -> str | None:
    if record.get(field) not in allowed:
        return f"{c.PR156_RECORD_SCHEMA_INVALID}: {record_id}: {field}"
    return None


def _record_schema_failures(record: Mapping[str, Any]) -> list[str]:
    record_id = str(record.get("pr156_record_id"))
    failures: list[str] = []
    for field in c.RECORD_REQUIRED_FIELDS:
        if field not in record:
            failures.append(f"{c.PR156_RECORD_SCHEMA_INVALID}: {record_id}: {field}")
    enum_checks = {
        "record_kind": c.RECORD_KIND_VALUES,
        "population_lane": c.POPULATION_LANE_VALUES,
        "agent_binding_state": c.AGENT_BINDING_STATE_VALUES,
        "candidate_instance_state": c.CANDIDATE_INSTANCE_STATE_VALUES,
        "candidate_research_intake_state": c.SOURCE_EVIDENCE_REQUIREMENT_STATE_VALUES,
        "applicability_class": c.CLASSICAL_QUANTUM_HYBRID_APPLICABILITY_VALUES,
        "owner_strategy_priority_state": c.OWNER_STRATEGY_PRIORITY_STATE_VALUES,
        "atomicrows_ingestion_state": c.ATOMICROWS_INGESTION_STATE_VALUES,
        "scoring_ranking_readiness_state": c.SCORING_RANKING_READINESS_STATE_VALUES,
        "optimizer_routing_hint": c.OPTIMIZER_ROUTING_HINT_VALUES,
        "replay_paper_routing_hint": c.REPLAY_PAPER_ROUTING_HINT_VALUES,
    }
    for field, allowed in enum_checks.items():
        failure = _enum_failure(record, record_id, field, allowed)
        if failure:
            failures.append(failure)
    template_type = record.get("template_type")
    if template_type is not None and template_type not in c.UNIVERSAL_INTAKE_TEMPLATE_TYPE_VALUES:
        failures.append(f"{c.PR156_RECORD_SCHEMA_INVALID}: {record_id}: template_type")
    if record.get("created_by_pr") != c.PR_ID:
        failures.append(f"{c.PR156_RECORD_SCHEMA_INVALID}: {record_id}: created_by_pr")
    for field in c.RECORD_ALWAYS_FALSE_FIELDS:
        boundary = _mapping(record.get("non_authority_boundary"))
        if record.get(field) is not False:
            failures.append(f"{c.PR156_FORBIDDEN_AUTHORITY_FLAG_TRUE}: {record_id}: {field}")
        if boundary.get(field) is not False:
            failures.append(f"{c.PR156_FORBIDDEN_AUTHORITY_FLAG_TRUE}: {record_id}: {field}")
    return failures


def _blocked_record_failures(record: Mapping[str, Any]) -> list[str]:
    if record.get("record_kind") != c.PR154_BLOCKED_INGESTION_RECORD:
        return []
    record_id = str(record.get("pr156_record_id"))
    failures: list[str] = []
    if record.get("agent_binding_state") != c.BINDING_PENDING_PR154_COMPLETION:
        failures.append(f"{c.PR156_BLOCKED_RECORD_CONSUMABLE}: {record_id}")
    if record.get("bound_agent_ids") or record.get("bound_agent_roles") or record.get(
        "bound_consumer_classes"
    ):
        failures.append(f"{c.PR156_BLOCKED_RECORD_CONSUMABLE}: {record_id}")
    completion = _mapping(record.get("blocked_completion_path_ref_or_inline"))
    for field in c.COMPLETION_PATH_FIELDS:
        value = completion.get(field)
        if field in {"missing_fields", "codex_actionable_completion_steps"}:
            if not as_list(value):
                failures.append(f"{c.PR156_RECORD_SCHEMA_INVALID}: {record_id}: {field}")
        elif not value:
            failures.append(f"{c.PR156_RECORD_SCHEMA_INVALID}: {record_id}: {field}")
    return failures


def _template_record_failures(record: Mapping[str, Any]) -> list[str]:
    if record.get("record_kind") != c.FUTURE_INTAKE_TEMPLATE_RECORD:
        return []
    record_id = str(record.get("pr156_record_id"))
    failures: list[str] = []
    if record.get("candidate_instance_state") != c.TEMPLATE_ONLY_NO_CANDIDATE_INSTANCE:
        failures.append(f"{c.PR156_TEMPLATE_RECORD_CONSUMABLE}: {record_id}")
    if record.get("bound_agent_ids") or record.get("bound_agent_roles") or record.get(
        "bound_consumer_classes"
    ):
        failures.append(f"{c.PR156_TEMPLATE_RECORD_CONSUMABLE}: {record_id}")
    if record.get("template_type") not in c.UNIVERSAL_INTAKE_TEMPLATE_TYPE_VALUES:
        failures.append(f"{c.PR156_RECORD_SCHEMA_INVALID}: {record_id}: template_type")
    return failures


def _authority_payload_failures(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    boundary = _mapping(payload.get("non_authority_boundary"))
    for field in c.RECORD_ALWAYS_FALSE_FIELDS:
        if boundary.get(field) is not False and field in boundary:
            failures.append(f"{c.PR156_FORBIDDEN_AUTHORITY_FLAG_TRUE}: {field}")
    for field in c.REPORT_FALSE_AUTHORITY_FIELDS:
        if field in payload and payload.get(field) is not False:
            if field.startswith("atomicrows_"):
                failures.append(c.PR156_ATOMICROWS_BUNDLE_AUTHORITY_CREATED)
            else:
                failures.append(c.PR156_QTT_SHA_AUTHORITY_CREATED)
    for key, value in _walk(payload):
        lowered = key.lower()
        if (
            ("sha_authority" in lowered or "hash_authority" in lowered)
            and value is not False
        ):
            failures.append(c.PR156_QTT_SHA_AUTHORITY_CREATED)
        if lowered.endswith(("_digest", "_checksum")) and value not in (False, None):
            failures.append(c.PR156_QTT_SHA_AUTHORITY_CREATED)
    return sorted(set(failures))


def _count_failures(
    registry: Mapping[str, Any],
    report: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    counts = _mapping(registry.get("counts"))
    expected = {
        "input_pr155_total_records": c.EXPECTED_INPUT_PR155_TOTAL_RECORDS,
        "input_pr155_ready_default_count": c.EXPECTED_INPUT_PR155_READY_DEFAULT_COUNT,
        "input_pr155_blocked_count": c.EXPECTED_INPUT_PR155_BLOCKED_COUNT,
        "pr156_binding_record_count": c.EXPECTED_INPUT_PR155_READY_DEFAULT_COUNT,
        "pr154_blocked_ingestion_lane_count": c.EXPECTED_PR154_BLOCKED_COUNT,
        "atomicrows_universe_ingestion_lane_count": 1,
        "future_classical_intake_template_count": len(c.CLASSICAL_TEMPLATE_TYPES),
        "future_quantum_intake_template_count": len(c.QUANTUM_TEMPLATE_TYPES),
        "future_hybrid_intake_template_count": len(c.HYBRID_TEMPLATE_TYPES),
        **{field: 0 for field in c.REPORT_ZERO_COUNT_FIELDS},
    }
    for key, expected_value in expected.items():
        if counts.get(key) != expected_value:
            failures.append(f"{c.PR156_PR155_COUNT_MISMATCH}: registry:{key}")
        if report.get(key) != expected_value:
            failures.append(f"{c.PR156_PR155_COUNT_MISMATCH}: report:{key}")
    count_state = report.get("atomicrows_universe_count_state")
    confirmed_count = report.get("atomicrows_universe_confirmed_count")
    if count_state not in {
        c.ATOMICROWS_UNIVERSE_COUNT_CONFIRMED,
        c.ATOMICROWS_UNIVERSE_COUNT_UNCONFIRMED,
    }:
        failures.append(
            f"{c.PR156_RECORD_SCHEMA_INVALID}: atomicrows_universe_count_state"
        )
    if count_state == c.ATOMICROWS_UNIVERSE_COUNT_CONFIRMED:
        if confirmed_count != c.EXPECTED_ATOMICROWS_UNIVERSE_COUNT:
            failures.append(
                f"{c.PR156_PR155_COUNT_MISMATCH}: atomicrows_universe_confirmed_count"
            )
    if count_state == c.ATOMICROWS_UNIVERSE_COUNT_UNCONFIRMED and confirmed_count is not None:
        failures.append(
            f"{c.PR156_RECORD_SCHEMA_INVALID}: atomicrows_universe_confirmed_count"
        )
    for key in (
        "explicit_agent_bound_count",
        "explicit_role_bound_count",
        "explicit_consumer_class_bound_count",
        "binding_pending_count",
    ):
        if counts.get(key) != report.get(key):
            failures.append(f"{c.PR156_PR155_COUNT_MISMATCH}: report:{key}")
    if report.get("binding_pending_count") != c.EXPECTED_INPUT_PR155_READY_DEFAULT_COUNT:
        failures.append(f"{c.PR156_PR155_COUNT_MISMATCH}: binding_pending_count")
    return failures


def _preflight_failures(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    preflight = _mapping(report.get("control_plane_preflight"))
    required_preflight_flags = (
        "pr_identity_roster_consumed",
        "roadmap_execution_state_consumed",
        "launch_readiness_roadmap_consumed",
        "launch_readiness_policy_consumed",
        "route_triage_consumed",
        "section_crosswalk_or_successor_consumed",
        "market_specific_index_consumed",
        "command_action_matrix_consumed",
        "atomicrows_reconciliation_consumed",
        "atomicrows_semantic_contract_consumed",
        "pr156_allowed_to_continue",
    )
    for flag in required_preflight_flags:
        if preflight.get(flag) is not True:
            failures.append(f"{c.PR156_ORCHESTRATION_ARTIFACT_MISSING}: {flag}")
    alias = _mapping(preflight.get("alias_resolution_applied"))
    if not alias.get("alias_exists") and not alias.get("successor_used"):
        failures.append(c.PR156_ORCHESTRATION_CROSSWALK_MISSING)
    return failures


def _schema_projection_failures(registry: Mapping[str, Any]) -> list[str]:
    projection = _mapping(registry.get("schema_projection"))
    record_schema = _mapping(
        _mapping(_mapping(projection.get("properties")).get("records")).get("items")
    )
    properties = _mapping(record_schema.get("properties"))
    checks = {
        "population_lane": c.POPULATION_LANE_VALUES,
        "agent_binding_state": c.AGENT_BINDING_STATE_VALUES,
        "candidate_instance_state": c.CANDIDATE_INSTANCE_STATE_VALUES,
        "atomicrows_ingestion_state": c.ATOMICROWS_INGESTION_STATE_VALUES,
        "optimizer_routing_hint": c.OPTIMIZER_ROUTING_HINT_VALUES,
    }
    failures: list[str] = []
    for key, expected in checks.items():
        if _mapping(properties.get(key)).get("enum") != list(expected):
            failures.append(f"{c.PR156_CENTRALIZED_VOCABULARY_DRIFT}: {key}")
    return failures


def validate_payloads(
    registry: Mapping[str, Any],
    report: Mapping[str, Any],
    build_failures: Sequence[str] = (),
    *,
    repo_root: Path | None = None,
) -> list[str]:
    failures = list(build_failures)
    failures.extend(_required_top_level_failures(registry, c.REGISTRY_TOP_LEVEL_KEYS))
    failures.extend(_required_top_level_failures(report, c.REPORT_KEYS))
    if registry.get("registry_type") != c.REGISTRY_TYPE:
        failures.append(c.PR156_RECORD_SCHEMA_INVALID)
    if report.get("report_type") != c.REPORT_TYPE:
        failures.append(c.PR156_RECORD_SCHEMA_INVALID)
    if registry.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append(c.PR156_RECORD_SCHEMA_INVALID)
    if report.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append(c.PR156_RECORD_SCHEMA_INVALID)

    records = [_mapping(record) for record in as_list(registry.get("records"))]
    blocked_records = [_mapping(record) for record in as_list(registry.get("blocked_records"))]
    record_ids = [str(record.get("pr156_record_id")) for record in records]
    if record_ids != sorted(record_ids):
        failures.append(c.PR156_RECORD_SCHEMA_INVALID)
    if len(record_ids) != len(set(record_ids)):
        failures.append(c.PR156_RECORD_ID_DUPLICATE)
    if [str(record.get("pr156_record_id")) for record in blocked_records] != sorted(
        str(record.get("pr156_record_id")) for record in blocked_records
    ):
        failures.append(c.PR156_RECORD_SCHEMA_INVALID)

    failures.extend(_count_failures(registry, report))
    for field in c.REPORT_FALSE_AUTHORITY_FIELDS:
        if report.get(field) is not False:
            failures.append(f"{c.PR156_FORBIDDEN_AUTHORITY_FLAG_TRUE}: {field}")
    for record in records:
        failures.extend(_record_schema_failures(record))
        failures.extend(_blocked_record_failures(record))
        failures.extend(_template_record_failures(record))
    failures.extend(_authority_payload_failures(registry))
    failures.extend(_authority_payload_failures(report))
    failures.extend(_serialized_forbidden_reference_failures(registry, report))
    failures.extend(_preflight_failures(report))
    failures.extend(_schema_projection_failures(registry))

    serialized = json_dump(registry) + json_dump(report)
    root = (repo_root or Path.cwd()).resolve()
    if "C:\\Users\\" in serialized or root.as_posix() in serialized:
        failures.append(c.PR156_RECORD_SCHEMA_INVALID)
    branch_rc, branch_out, _branch_err = _git_stdout(root, ["branch", "--show-current"])
    if branch_rc == 0 and _branch_name_reference_present(
        branch_out.strip(),
        registry,
        report,
    ):
        failures.append(c.PR156_RECORD_SCHEMA_INVALID)
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
        failures.append(c.PR156_REGISTRY_STALE_OR_NONDETERMINISTIC)
    if json_dump(first.report) != json_dump(second.report):
        failures.append(c.PR156_REPORT_STALE_OR_NONDETERMINISTIC)

    if write_report and not check_only:
        write_json_file(root / c.REGISTRY_PATH, first.registry)
        write_json_file(root / c.REPORT_PATH, first.report)

    failures.extend(
        validate_payloads(
            first.registry,
            first.report,
            first.failures,
            repo_root=root,
        )
    )

    for rel_path, expected, stale_code in (
        (c.REGISTRY_PATH, first.registry, c.PR156_REGISTRY_STALE_OR_NONDETERMINISTIC),
        (c.REPORT_PATH, first.report, c.PR156_REPORT_STALE_OR_NONDETERMINISTIC),
    ):
        path = root / rel_path
        try:
            actual = read_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"{stale_code}: {rel_path.as_posix()}: {exc}")
            continue
        if actual != expected:
            failures.append(stale_code)
        if path.read_text(encoding="utf-8") != json_dump(actual):
            failures.append(stale_code)

    failures.extend(_validate_changed_paths(root))
    if strict:
        failures.extend(_serialized_forbidden_reference_failures(first.registry, first.report))
    return sorted(set(failures))
