"""Build deterministic PR156 registry and report artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .agent_binding import load_agent_binding_context
from .atomicrows_ingestion import (
    atomicrows_universe_state,
    build_atomicrows_universe_record,
)
from .input_discovery import (
    artifact_summary,
    discover_pr154_report,
    discover_pr155_registry,
    discover_pr155_report,
    load_optional_artifacts,
)
from .intake_templates import build_universal_intake_templates
from .io import as_list, as_mapping
from .models import BuildOutputs
from .orchestration_preflight import load_control_plane_preflight
from .population_router import (
    build_pr154_blocked_ingestion_record,
    build_pr155_ready_binding_record,
)
from .schema_projection import registry_artifact_schema_projection


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _counter(records: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(key)) for record in records).items()))


def _counter_values(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _validation_result(failures: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": "PASS" if not failures else "FAIL_CLOSED",
        "validator_marker": c.SUCCESS_MARKER if not failures else None,
        "failures": list(failures),
    }


def _pr155_count_failures(
    registry_payload: Mapping[str, Any],
    report_payload: Mapping[str, Any],
) -> tuple[str, ...]:
    records = [_mapping(record) for record in as_list(registry_payload.get("records"))]
    ready = [
        record
        for record in records
        if record.get("agent_consumable_default_ready_flag") is True
    ]
    blocked = [
        record
        for record in records
        if record.get("agent_consumable_default_ready_flag") is not True
    ]
    expected = {
        "total_records": (len(records), c.EXPECTED_INPUT_PR155_TOTAL_RECORDS),
        "ready_records": (len(ready), c.EXPECTED_INPUT_PR155_READY_DEFAULT_COUNT),
        "blocked_records": (len(blocked), c.EXPECTED_INPUT_PR155_BLOCKED_COUNT),
        "report_ready_records": (
            report_payload.get("agent_consumable_default_ready_count"),
            c.EXPECTED_INPUT_PR155_READY_DEFAULT_COUNT,
        ),
        "report_blocked_records": (
            report_payload.get("non_consumable_blocked_count"),
            c.EXPECTED_INPUT_PR155_BLOCKED_COUNT,
        ),
    }
    failures = [
        f"{c.PR156_PR155_COUNT_MISMATCH}: {key}"
        for key, (actual, expected_value) in expected.items()
        if actual != expected_value
    ]
    return tuple(sorted(set(failures)))


def _pr154_count_failures(pr154_payload: Mapping[str, Any]) -> tuple[str, ...]:
    counts = as_mapping(pr154_payload.get("materialization_count_summary"))
    failures = []
    if counts.get("blocked_count") != c.EXPECTED_PR154_BLOCKED_COUNT:
        failures.append(f"{c.PR156_PR154_COUNT_MISMATCH}: blocked_count")
    if counts.get("total_pr154_records") != c.EXPECTED_INPUT_PR155_TOTAL_RECORDS:
        failures.append(f"{c.PR156_PR154_COUNT_MISMATCH}: total_pr154_records")
    return tuple(sorted(set(failures)))


def _required_input_summaries(
    pr155_registry_path: Path | None,
    pr155_registry: Mapping[str, Any],
    pr155_report_path: Path | None,
    pr155_report: Mapping[str, Any],
    pr154_path: Path | None,
    pr154_report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        artifact_summary(
            key="pr155_registry",
            rel_path=pr155_registry_path or c.PR155_REGISTRY_PATH,
            payload=pr155_registry,
            required=True,
            consumed=pr155_registry_path is not None,
        ),
        artifact_summary(
            key="pr155_report",
            rel_path=pr155_report_path or c.PR155_REPORT_PATH,
            payload=pr155_report,
            required=True,
            consumed=pr155_report_path is not None,
        ),
        artifact_summary(
            key="pr154_materialization_report",
            rel_path=pr154_path or c.PR154_REPORT_PATH,
            payload=pr154_report,
            required=True,
            consumed=pr154_path is not None,
        ),
    ]


def _counts(
    binding_records: list[Mapping[str, Any]],
    blocked_ingestion_records: list[Mapping[str, Any]],
    atomicrows_record: Mapping[str, Any],
    template_records: list[Mapping[str, Any]],
    pr155_records: list[Mapping[str, Any]],
) -> dict[str, int | bool | None | str]:
    all_records = [*binding_records, *blocked_ingestion_records, atomicrows_record, *template_records]
    return {
        "input_pr155_total_records": len(pr155_records),
        "input_pr155_ready_default_count": len(binding_records),
        "input_pr155_blocked_count": len(blocked_ingestion_records),
        "pr156_binding_record_count": len(binding_records),
        "explicit_agent_bound_count": sum(
            1
            for record in binding_records
            if record.get("agent_binding_state") == c.AGENT_BOUND_NONLIVE_EXPLICIT
        ),
        "explicit_role_bound_count": sum(
            1
            for record in binding_records
            if record.get("agent_binding_state") == c.ROLE_BOUND_NONLIVE_EXPLICIT
        ),
        "explicit_consumer_class_bound_count": sum(
            1
            for record in binding_records
            if record.get("agent_binding_state")
            == c.CONSUMER_CLASS_BOUND_NONLIVE_EXPLICIT
        ),
        "binding_pending_count": sum(
            1
            for record in binding_records
            if record.get("agent_binding_state")
            == c.BINDING_PENDING_EXPLICIT_AGENT_MAP_MISSING
        ),
        "pr154_blocked_ingestion_lane_count": len(blocked_ingestion_records),
        "atomicrows_universe_ingestion_lane_count": 1,
        "atomicrows_universe_confirmed_count": (
            atomicrows_record["atomicrows_reconciliation_refs"][0]["row_count_value"]
        ),
        "atomicrows_universe_count_state": atomicrows_record["atomicrows_ingestion_state"],
        "future_classical_intake_template_count": sum(
            1 for record in template_records if record.get("template_type") in c.CLASSICAL_TEMPLATE_TYPES
        ),
        "future_quantum_intake_template_count": sum(
            1 for record in template_records if record.get("template_type") in c.QUANTUM_TEMPLATE_TYPES
        ),
        "future_hybrid_intake_template_count": sum(
            1 for record in template_records if record.get("template_type") in c.HYBRID_TEMPLATE_TYPES
        ),
        **{
            count_field: sum(
                1
                for record in all_records
                if record.get(count_field.removesuffix("_count") + "_flag") is True
            )
            for count_field in c.REPORT_ZERO_COUNT_FIELDS
            if count_field
            not in {
                "scoring_executed_as_trade_selection_count",
                "quantum_execution_evidence_count",
            }
        },
        "scoring_executed_as_trade_selection_count": sum(
            1
            for record in all_records
            if record.get("scoring_executed_as_trade_selection_flag") is True
        ),
        "quantum_execution_evidence_count": sum(
            1
            for record in all_records
            if record.get("quantum_execution_evidence_flag") is True
        ),
    }


def _blocked_completion_summary(
    blocked_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    completion_present = {
        field: sum(
            1
            for record in blocked_records
            if as_mapping(record.get("blocked_completion_path_ref_or_inline")).get(field)
        )
        for field in c.COMPLETION_PATH_FIELDS
    }
    return {
        "blocked_record_count": len(blocked_records),
        "completion_path_field_presence_counts": completion_present,
        "all_blocked_records_have_required_completion_path": all(
            count == len(blocked_records) for count in completion_present.values()
        ),
        "required_next_task_summary": _counter_values(
            [
                str(
                    as_mapping(record.get("blocked_completion_path_ref_or_inline")).get(
                        "required_next_task"
                    )
                )
                for record in blocked_records
            ]
        ),
    }


def _market_summary(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "market_scope_summary": _counter(records, "market_scope"),
        "platform_scope_summary": _counter(records, "platform_scope"),
        "launch_readiness_domain_summary": _counter(records, "launch_readiness_domain"),
        "route_triage_domain_summary": _counter(records, "route_triage_domain"),
        "live_transition_created": False,
        "connector_unlock_created": False,
    }


def _agent_binding_summary(
    records: list[Mapping[str, Any]],
    binding_context_paths: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "agent_binding_state_summary": _counter(records, "agent_binding_state"),
        "explicit_binding_artifacts_consumed": list(binding_context_paths),
        "semantic_similarity_binding_used": False,
        "agent_name_matching_binding_used": False,
        "live_authority_created_by_binding": False,
    }


def _static_artifact_paths(optional_paths: tuple[Mapping[str, Any], ...], keys: tuple[str, ...]) -> list[str]:
    return sorted(
        str(item["artifact_path"])
        for item in optional_paths
        if item.get("artifact_key") in keys and item.get("consumed") is True
    )


def build_outputs(repo_root: Path | str) -> BuildOutputs:
    root = Path(repo_root).resolve()
    preflight_result = load_control_plane_preflight(root)
    pr155_registry_discovery = discover_pr155_registry(root)
    pr155_report_discovery = discover_pr155_report(root)
    pr154_discovery = discover_pr154_report(root)
    optional = load_optional_artifacts(root)
    binding_context = load_agent_binding_context(optional)

    count_failures = (
        _pr155_count_failures(
            pr155_registry_discovery.payload,
            pr155_report_discovery.payload,
        )
        if pr155_registry_discovery.payload and pr155_report_discovery.payload
        else ()
    )
    pr154_failures = (
        _pr154_count_failures(pr154_discovery.payload) if pr154_discovery.payload else ()
    )
    failures = tuple(
        sorted(
            set(
                (
                    *preflight_result.failures,
                    *pr155_registry_discovery.failures,
                    *pr155_report_discovery.failures,
                    *pr154_discovery.failures,
                    *optional.failures,
                    *count_failures,
                    *pr154_failures,
                )
            )
        )
    )

    pr155_records = [
        _mapping(record)
        for record in as_list(pr155_registry_discovery.payload.get("records"))
        if isinstance(record, Mapping)
    ]
    pr155_ready = [
        record
        for record in pr155_records
        if record.get("agent_consumable_default_ready_flag") is True
    ]
    pr155_blocked = [
        record
        for record in pr155_records
        if record.get("agent_consumable_default_ready_flag") is not True
    ]
    pr155_authority_class = str(
        pr155_registry_discovery.payload.get("authority_class") or c.PR155_REGISTRY_TYPE
    )

    binding_records = sorted(
        (
            build_pr155_ready_binding_record(
                record,
                binding_context=binding_context,
                pr155_authority_class=pr155_authority_class,
            )
            for record in pr155_ready
        ),
        key=lambda record: str(record["pr156_record_id"]),
    )
    blocked_ingestion_records = sorted(
        (
            build_pr154_blocked_ingestion_record(
                record,
                pr155_authority_class=pr155_authority_class,
            )
            for record in pr155_blocked
        ),
        key=lambda record: str(record["pr156_record_id"]),
    )
    atomicrows_state = atomicrows_universe_state(
        preflight_result.payloads.get("pr137r_atomicrows_reconciliation", {}),
        optional,
    )
    atomicrows_record = build_atomicrows_universe_record(atomicrows_state)
    template_records = build_universal_intake_templates()
    all_records = sorted(
        [*binding_records, *blocked_ingestion_records, atomicrows_record, *template_records],
        key=lambda record: str(record["pr156_record_id"]),
    )
    counts = _counts(
        binding_records,
        blocked_ingestion_records,
        atomicrows_record,
        template_records,
        pr155_records,
    )
    validation_result = _validation_result(failures)
    required_artifacts = _required_input_summaries(
        pr155_registry_discovery.input_path,
        pr155_registry_discovery.payload,
        pr155_report_discovery.input_path,
        pr155_report_discovery.payload,
        pr154_discovery.input_path,
        pr154_discovery.payload,
    )
    preflight_artifacts = list(
        as_list(preflight_result.preflight.get("required_input_artifacts"))
    )
    input_artifacts = {
        "required": sorted(
            [*required_artifacts, *preflight_artifacts],
            key=lambda item: str(item["artifact_path"]),
        ),
        "optional_consumed": list(optional.consumed_artifacts),
        "optional_missing": list(optional.missing_artifacts),
    }

    registry = {
        "registry_type": c.REGISTRY_TYPE,
        "pr_id": c.PR_ID,
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "input_artifacts": input_artifacts,
        "control_plane_preflight": dict(preflight_result.preflight),
        "counts": counts,
        "population_lanes": _counter(all_records, "population_lane"),
        "agent_binding_records": binding_records,
        "missing_record_ingestion_lanes": blocked_ingestion_records,
        "atomicrows_universe_ingestion_summary": atomicrows_record,
        "universal_intake_templates": template_records,
        "records": all_records,
        "blocked_records": blocked_ingestion_records,
        "non_authority_boundary": dict(c.NON_AUTHORITY_BOUNDARY),
        "schema_projection": registry_artifact_schema_projection(),
        "validation_result": validation_result,
    }

    static_paths = _static_artifact_paths(
        optional.consumed_artifacts,
        c.SCORING_OPTIMIZER_STATIC_KEYS,
    )
    atomicrows_paths = _static_artifact_paths(
        optional.consumed_artifacts,
        c.ATOMICROWS_OPTIONAL_KEYS,
    )
    future_source_paths = _static_artifact_paths(
        optional.consumed_artifacts,
        c.FUTURE_CANDIDATE_SOURCE_KEYS,
    )
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
        "orchestration_alignment_summary": {
            key: preflight_result.preflight.get(key)
            for key in (
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
                "preflight_block_codes",
                "alias_resolution_applied",
            )
        },
        "market_specific_readiness_summary": _market_summary(all_records),
        "agent_binding_summary": _agent_binding_summary(
            binding_records,
            binding_context.consumed_artifact_paths,
        ),
        "missing_record_ingestion_summary": {
            "pr154_blocked_ingestion_lane_count": len(blocked_ingestion_records),
            "blocked_records_materialized_by_pr156": 0,
            "blocked_records_made_consumable_by_pr156": 0,
            "completion_path_summary": _blocked_completion_summary(
                blocked_ingestion_records
            ),
        },
        "atomicrows_ingestion_summary": {
            "atomicrows_universe_ingestion_lane_count": 1,
            "atomicrows_universe_confirmed_count": counts[
                "atomicrows_universe_confirmed_count"
            ],
            "atomicrows_universe_count_state": counts["atomicrows_universe_count_state"],
            "atomicrows_source_artifacts_consumed": list(
                atomicrows_state.source_artifact_paths
            ),
            "atomicrows_optional_universe_artifacts_consumed": atomicrows_paths,
            "atomicrows_bundle_created": False,
            "atomicrows_bundle_hash_authority_created": False,
            "atomicrows_rows_materialized_by_pr156": 0,
        },
        "universal_classical_quantum_intake_summary": {
            "template_record_count": len(template_records),
            "future_classical_intake_template_count": counts[
                "future_classical_intake_template_count"
            ],
            "future_quantum_intake_template_count": counts[
                "future_quantum_intake_template_count"
            ],
            "future_hybrid_intake_template_count": counts[
                "future_hybrid_intake_template_count"
            ],
            "future_candidate_source_artifacts_consumed": future_source_paths,
            "candidate_instances_accepted_by_pr156": 0,
            "classical_formulas_are_first_class": True,
            "quantum_templates_are_challenger_lanes_only": True,
            "unknown_research_candidate_template_blocks_without_source_evidence": True,
        },
        "scoring_ranking_future_routing_summary": {
            "static_foundation_artifacts_consumed": static_paths,
            "scoring_ranking_executed_as_trade_selection": False,
            "live_selection_created": False,
            "future_routing_hints_only": True,
        },
        "optimizer_replay_paper_future_routing_summary": {
            "static_foundation_artifacts_consumed": static_paths,
            "optimizer_executed": False,
            "quantum_backend_executed": False,
            "replay_executed": False,
            "paper_executed": False,
            "future_routing_hints_only": True,
        },
        "blocked_completion_path_summary": _blocked_completion_summary(
            blocked_ingestion_records
        ),
        "determinism_metadata_without_runtime_git_volatility": {
            "json_indent": 2,
            "json_sort_keys": True,
            "stable_sort_records_by": c.DETERMINISTIC_SORT_KEYS["records"],
            "stable_sort_blocked_records_by": c.DETERMINISTIC_SORT_KEYS[
                "blocked_records"
            ],
            "wall_clock_timestamps_used": False,
            "branch_name_used": False,
            "current_commit_sha_used": False,
            "local_path_used": False,
            "username_used": False,
            "python_hash_used": False,
            "random_uuid_used": False,
        },
        "validation_result": validation_result,
    }
    return BuildOutputs(registry=registry, report=report, failures=failures)
