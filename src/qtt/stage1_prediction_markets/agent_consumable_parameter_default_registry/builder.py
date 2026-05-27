"""Build deterministic PR155 registry and report artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .input_discovery import discover_pr154_input
from .io import as_list
from .mapper import map_pr154_record
from .models import BuildOutputs
from .orchestration_preflight import load_control_plane_preflight
from .schema_projection import registry_artifact_schema_projection


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _counter(records: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(key)) for record in records).items()))


def _validation_result(failures: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": "PASS" if not failures else "FAIL_CLOSED",
        "validator_marker": c.SUCCESS_MARKER if not failures else None,
        "failures": list(failures),
    }


def _pr154_count_failures(pr154_payload: Mapping[str, Any]) -> tuple[str, ...]:
    counts = _mapping(pr154_payload.get("materialization_count_summary"))
    expected = {
        "total_pr154_records": c.EXPECTED_INPUT_PR154_TOTAL_RECORDS,
        "materialized_value_count": c.EXPECTED_MATERIALIZED_RECORDS,
        "blocked_count": c.EXPECTED_BLOCKED_RECORDS,
        "accepted_official_source_materialized_count": (
            c.EXPECTED_OFFICIAL_SOURCE_MATERIALIZED_DEFAULTS
        ),
        "owner_internal_materialized_count": (
            c.EXPECTED_OWNER_INTERNAL_CONTROL_PLANE_DEFAULTS
        ),
    }
    failures: list[str] = []
    for key, expected_value in expected.items():
        if counts.get(key) != expected_value:
            failures.append(f"{c.PR155_PR154_COUNT_MISMATCH}: {key}")
    records = as_list(pr154_payload.get("per_target_materialization_records"))
    if len(records) != c.EXPECTED_INPUT_PR154_TOTAL_RECORDS:
        failures.append(f"{c.PR155_PR154_COUNT_MISMATCH}: per_target_materialization_records")
    record_ids = [
        str(_mapping(record).get("pr154_record_id"))
        for record in records
        if isinstance(record, Mapping)
    ]
    duplicates = sorted(key for key, count in Counter(record_ids).items() if count > 1)
    if duplicates:
        failures.append(f"{c.PR155_PR154_RECORD_ID_DUPLICATE}: {','.join(duplicates)}")
    return tuple(sorted(set(failures)))


def _counts(records: list[Mapping[str, Any]], blocked_records: list[Mapping[str, Any]]) -> dict[str, int]:
    ready = [
        record
        for record in records
        if record.get("agent_consumable_default_ready_flag") is True
    ]
    return {
        "input_pr154_total_records": len(records),
        "agent_consumable_default_ready_count": len(ready),
        "direct_agent_assignment_ready_count": sum(
            1 for record in records if record.get("direct_agent_assignment_ready_flag") is True
        ),
        "agent_assignment_pending_count": sum(
            1
            for record in records
            if record.get("agent_assignment_state") == c.AGENT_ASSIGNMENT_PENDING
        ),
        "non_consumable_blocked_count": len(blocked_records),
        "official_source_materialized_default_count": sum(
            1
            for record in ready
            if record.get("default_use_class")
            == c.NONLIVE_OFFICIAL_SOURCE_MATERIALIZED_DEFAULT
        ),
        "owner_internal_control_plane_default_count": sum(
            1
            for record in ready
            if record.get("default_use_class")
            == c.NONLIVE_OWNER_INTERNAL_POLICY_DEFAULT
        ),
        "live_order_ready_count": sum(
            1 for record in records if record.get("live_order_ready_flag") is True
        ),
        "runtime_ready_count": sum(
            1 for record in records if record.get("runtime_ready_flag") is True
        ),
        "connector_semantic_bound_count": sum(
            1
            for record in records
            if record.get("connector_semantic_bound_flag") is True
        ),
        "replay_tested_count": sum(
            1 for record in records if record.get("replay_tested_flag") is True
        ),
        "paper_approved_count": sum(
            1 for record in records if record.get("paper_approved_flag") is True
        ),
        "quantum_execution_evidence_count": sum(
            1
            for record in records
            if record.get("quantum_execution_evidence_flag") is True
        ),
        "profit_evidence_count": sum(
            1 for record in records if record.get("profit_evidence_flag") is True
        ),
    }


def _summary_counts(records: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    return _counter(records, key)


def _blocked_completion_summary(blocked_records: list[Mapping[str, Any]]) -> dict[str, Any]:
    completion_present = {
        field: sum(
            1
            for record in blocked_records
            if _mapping(record.get("blocked_completion_path_if_any")).get(field)
        )
        for field in c.COMPLETION_PATH_FIELDS
    }
    return {
        "blocked_record_count": len(blocked_records),
        "completion_path_field_presence_counts": completion_present,
        "all_blocked_records_have_required_completion_path": all(
            count == len(blocked_records) for count in completion_present.values()
        ),
        "blocked_state_summary": _summary_counts(
            blocked_records,
            "registry_consumption_state",
        ),
    }


def _agent_registry_summary(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "registry_consumption_state_summary": _summary_counts(
            records,
            "registry_consumption_state",
        ),
        "agent_assignment_state_summary": _summary_counts(
            records,
            "agent_assignment_state",
        ),
        "direct_agent_assignment_not_required_for_registry_defaults": True,
        "direct_agent_assignment_invented": False,
        "forbidden_agent_list_invented": False,
    }


def _orchestration_alignment_summary(preflight: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: preflight.get(key)
        for key in (
            "pr_identity_roster_consumed",
            "roadmap_execution_state_consumed",
            "launch_readiness_policy_consumed",
            "route_triage_consumed",
            "section_crosswalk_or_successor_consumed",
            "market_specific_index_consumed",
            "command_action_matrix_consumed",
            "pr155_allowed_to_continue",
            "preflight_block_codes",
        )
    }


def build_outputs(repo_root: Path | str) -> BuildOutputs:
    root = Path(repo_root).resolve()
    preflight_result = load_control_plane_preflight(root)
    discovery = discover_pr154_input(root)
    count_failures = (
        _pr154_count_failures(discovery.payload) if discovery.payload else ()
    )
    failures = tuple(
        sorted(
            set(
                (
                    *preflight_result.failures,
                    *discovery.failures,
                    *count_failures,
                )
            )
        )
    )

    pr154_records = [
        _mapping(record)
        for record in as_list(discovery.payload.get("per_target_materialization_records"))
        if isinstance(record, Mapping)
    ]
    mapped = [
        map_pr154_record(
            record,
            index=index,
            preflight_allowed=not preflight_result.failures,
            payloads=preflight_result.payloads,
        )
        for index, record in enumerate(pr154_records)
    ]
    records = sorted(mapped, key=lambda record: str(record.get("registry_record_id")))
    blocked_records = [
        record
        for record in records
        if record.get("agent_consumable_default_ready_flag") is not True
    ]
    blocked_records = sorted(
        blocked_records,
        key=lambda record: str(record.get("registry_record_id")),
    )
    counts = _counts(records, blocked_records)
    validation_result = _validation_result(failures)
    input_artifact = discovery.input_path.as_posix() if discovery.input_path else None

    registry = {
        "registry_type": c.REGISTRY_TYPE,
        "pr_id": c.PR_ID,
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "input_pr154_artifact": input_artifact,
        "control_plane_preflight": dict(preflight_result.preflight),
        "counts": counts,
        "records": records,
        "blocked_records": blocked_records,
        "non_authority_boundary": dict(c.NON_AUTHORITY_BOUNDARY_FLAGS),
        "schema_projection": registry_artifact_schema_projection(),
        "validation_result": validation_result,
    }
    report = {
        "report_type": c.REPORT_TYPE,
        "pr_id": c.PR_ID,
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "authority_class": c.AUTHORITY_CLASS,
        **counts,
        "qtt_sha_authority_created": False,
        "qtt_generated_sha_created": False,
        "qtt_freeze_checksum_global_digest_authority_created": False,
        "atomicrows_bundle_created": False,
        "atomicrows_bundle_sha_or_hash_authority_created": False,
        "control_plane_preflight": dict(preflight_result.preflight),
        "orchestration_alignment_summary": _orchestration_alignment_summary(
            preflight_result.preflight
        ),
        "market_specific_readiness_summary": {
            "market_scope_summary": _summary_counts(records, "market_scope"),
            "platform_scope_summary": _summary_counts(records, "platform_scope"),
            "future_replay_paper_placement_hint": c.FUTURE_REPLAY_PAPER_PLACEMENT_HINT,
            "future_live_transition_block_reason": (
                c.FUTURE_LIVE_TRANSITION_BLOCK_REASON
            ),
        },
        "atomicrows_compatibility_summary": _summary_counts(
            records,
            "atomicrows_compatibility_state",
        ),
        "quantum_forward_compatibility_summary": {
            "state_summary": _summary_counts(
                records,
                "quantum_forward_compatibility_state",
            ),
            "optimizer_readiness_hint_summary": _summary_counts(
                records,
                "optimizer_readiness_hint",
            ),
            "quantum_execution_created": False,
            "optimizer_backend_execution_created": False,
            "quantum_strategy_tags_inferred": False,
            "missing_quantum_metadata_uses_typed_state": True,
        },
        "agent_registry_summary": _agent_registry_summary(records),
        "blocked_completion_path_summary": _blocked_completion_summary(blocked_records),
        "determinism_metadata_without_runtime_git_volatility": {
            "json_indent": 2,
            "json_sort_keys": True,
            "stable_sort_records_by": "registry_record_id",
            "wall_clock_timestamps_used": False,
            "branch_name_used": False,
            "current_commit_sha_used": False,
            "local_path_used": False,
            "username_used": False,
            "python_hash_used": False,
            "random_uuid_used": False,
        },
        "non_authority_boundary": dict(c.NON_AUTHORITY_BOUNDARY_FLAGS),
        "validation_result": validation_result,
    }
    return BuildOutputs(
        registry=registry,
        report=report,
        input_pr154_artifact=input_artifact,
        failures=failures,
    )
