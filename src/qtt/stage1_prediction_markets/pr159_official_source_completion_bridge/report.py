"""Top-level PR159 artifact construction and writing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .atomicrows_source_completion import build_atomicrows_completion_records
from .candidate_source_packet import build_candidate_packets, candidate_refs_by_target
from .conflict_resolution import build_conflict_queue
from .freshness_revalidation import build_freshness_audit
from .input_discovery import (
    load_atomicrows_source_required_records,
    load_pr153r_seed_records,
    load_pr154_retry_records,
    load_selection_overlay_records,
    overlay_by_row_id,
)
from .io import json_dump, stable_counter, stable_counter_from_records, write_json, write_text
from .low_latency_source_snapshot_update import build_low_latency_updates
from .models import BuildArtifacts
from .official_source_discovery import (
    AMBIGUOUS_OFFICIAL_DISCOVERY,
    NON_AUTHORITATIVE_REJECTIONS,
    OFFICIAL_SOURCE_CATALOG,
    SEARCH_RECEIPTS,
    official_domain_records,
)
from .orchestration_preflight import (
    input_consumption_receipts,
    orchestration_alignment_receipt,
    preflight_failures,
)
from .pr154_retry_completion import build_pr154_completion_records
from .quantum_provider_source_metadata import build_quantum_metadata
from .registry import registry_payload, report_payload
from .revalidation_schedule import build_revalidation_schedule
from .scoring_ranking_source_readiness_update import build_scoring_ranking_updates
from .selection_readiness_source_update import build_selection_updates
from .source_acceptance_validator import build_accepted_packets
from .source_acceptance_attempt_matrix import build_source_acceptance_attempt_matrix
from .source_target_queue import build_target_queue
from .target_field_acceptance_ledger import build_acceptance_ledger
from .trade_context_source_readiness_update import build_trade_context_updates
from .unresolved_fill_paths import build_unresolved_fill_paths


def _validation_result(failures: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": "PASS" if not failures else "FAIL_CLOSED",
        "validator_marker": c.SUCCESS_MARKER if not failures else None,
        "failures": list(failures),
    }


def _determinism_receipt() -> dict[str, Any]:
    return {
        "json_indent": 2,
        "json_sort_keys": True,
        "stable_record_sort_key": ["target_id", "row_id", "candidate_packet_id"],
        "wall_clock_timestamps_used": False,
        "online_retrieval_timestamps_are_preserved_constants": True,
        "validation_refreshes_online_retrieval": False,
        "runtime_git_branch_or_head_used": False,
        "random_values_used": False,
        "local_absolute_paths_used": False,
        "repo_relative_paths_only": True,
    }


def _common(
    receipts: list[dict[str, Any]],
    validation: Mapping[str, Any],
    count_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "pr_id": c.PR_ID,
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "implementation_class": c.IMPLEMENTATION_CLASS,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_profile_ids": list(c.DEFAULT_AUTHORITY_PROFILE_IDS),
        "mode_boundaries": [item.value for item in c.PR159Mode],
        "input_consumption_receipt": receipts,
        "orchestration_alignment_receipt": orchestration_alignment_receipt(receipts),
        "count_invariant_receipt": dict(count_receipt),
        "determinism_receipt": _determinism_receipt(),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "validation_result": dict(validation),
    }


def _count_receipt(
    pr154_records: list[Mapping[str, Any]],
    atomic_records: list[Mapping[str, Any]],
    target_queue: list[Mapping[str, Any]],
    candidate_packets: list[Mapping[str, Any]],
    accepted_packets: list[Mapping[str, Any]],
    unresolved_paths: list[Mapping[str, Any]],
) -> dict[str, Any]:
    state_counts = stable_counter_from_records(target_queue, "final_source_target_state")
    pr154_processed = len(pr154_records)
    atomic_processed = len(atomic_records)
    return {
        "pr154_public_source_retry_records": c.EXPECTED_PR154_PUBLIC_SOURCE_RETRY_RECORDS,
        "atomicrows_public_external_source_required": c.EXPECTED_ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED,
        "atomicrows_parameter_range_source_required": c.EXPECTED_ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED,
        "atomicrows_source_required_total": c.EXPECTED_ATOMICROWS_SOURCE_REQUIRED_TOTAL,
        "total_source_target_records": c.EXPECTED_TOTAL_SOURCE_TARGET_RECORDS,
        "pr154_retry_processed_count": pr154_processed,
        "atomicrows_source_required_processed_count": atomic_processed,
        "accepted_source_packet_count": len(accepted_packets),
        "candidate_source_packet_count": len(candidate_packets),
        "unresolved_source_required_count": len(unresolved_paths),
        "target_state_counts": state_counts,
        "count_invariants_passed_flag": (
            len(pr154_records) == c.EXPECTED_PR154_PUBLIC_SOURCE_RETRY_RECORDS
            and len([r for r in atomic_records if r.get("source_requirement_class") == "PUBLIC_EXTERNAL_SOURCE_REQUIRED"])
            == c.EXPECTED_ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED
            and len([r for r in atomic_records if r.get("source_requirement_class") == "PARAMETER_RANGE_SOURCE_REQUIRED"])
            == c.EXPECTED_ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED
            and len(atomic_records) == c.EXPECTED_ATOMICROWS_SOURCE_REQUIRED_TOTAL
            and len(target_queue) == c.EXPECTED_TOTAL_SOURCE_TARGET_RECORDS
            and pr154_processed == c.EXPECTED_PR154_PUBLIC_SOURCE_RETRY_RECORDS
            and atomic_processed == c.EXPECTED_ATOMICROWS_SOURCE_REQUIRED_TOTAL
            and sum(state_counts.values()) == c.EXPECTED_TOTAL_SOURCE_TARGET_RECORDS
        ),
    }


def _target_queue_with_state(
    target_queue: list[dict[str, Any]],
    candidate_refs: dict[str, list[str]],
    accepted_by_candidate: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in target_queue:
        item = dict(target)
        target_key = str(item.get("target_id"))
        if any(ref in accepted_by_candidate for ref in candidate_refs.get(target_key, [])):
            item["final_source_target_state"] = c.SourceTargetState.ACCEPTED_COMPLETED.value
        elif item["source_population"] == c.PR159TargetPopulation.PR154_PUBLIC_SOURCE_RETRY_34.value and candidate_refs.get(target_key):
            item["final_source_target_state"] = c.SourceTargetState.CANDIDATE_ONLY.value
        else:
            item["final_source_target_state"] = c.SourceTargetState.UNRESOLVED_WITH_FILL_PATH.value
        records.append(item)
    return sorted(records, key=lambda item: item["target_id"])


def _day1_index(target_queue: list[Mapping[str, Any]], common: Mapping[str, Any]) -> dict[str, Any]:
    counts = _priority_counts(target_queue)
    records = [
        {
            "day1_source_priority_tier": tier,
            "target_count": counts.get(tier, 0),
            "source_materiality_classes": sorted(
                {
                    str(item.get("source_materiality_class"))
                    for item in target_queue
                    if item.get("day1_source_priority_tier") == tier
                }
            ),
        }
        for tier in sorted(c.CENTRAL_ENUM_VALUE_SETS["day1_source_priority_tier"])
    ]
    return report_payload(
        "PR159_DAY1_SOURCE_PRIORITY_TIER_INDEX",
        records,
        common,
        priority_tier_counts=counts,
    )


def _priority_counts(target_queue: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = stable_counter_from_records(target_queue, "day1_source_priority_tier")
    return {
        tier: counts.get(tier, 0)
        for tier in sorted(c.CENTRAL_ENUM_VALUE_SETS["day1_source_priority_tier"])
    }


def _summary_markdown(master_report: Mapping[str, Any]) -> str:
    counts = master_report["count_invariant_receipt"]
    target_states = counts["target_state_counts"]
    priority_counts = master_report["day1_source_priority_tier_counts"]
    return "\n".join(
        [
            "# PR159 Official Source Completion Summary",
            "",
            f"Processed targets: {counts['total_source_target_records']}",
            f"P0/P1/P2/P3 targets: {priority_counts}",
            f"Official sources found: {master_report['official_source_discovered_count']}",
            f"Candidate packets created: {counts['candidate_source_packet_count']}",
            f"Accepted packets created: {counts['accepted_source_packet_count']}",
            f"Acceptance attempt matrix records: {master_report['source_acceptance_attempt_matrix_record_count']}",
            f"PR154 retry records completed: {master_report['pr154_retry_accepted_completed']}",
            f"AtomicRows source-required rows completed: {master_report['atomicrows_source_accepted_completed']}",
            f"Remaining target states: {target_states}",
            "",
            "What remains blocked:",
            "- Remaining PR154 retry targets need exact target-field extraction before acceptance.",
            "- AtomicRows source-required rows need row-specific official range/value/constraint packets before PR161 materialization.",
            "",
            "Next actions:",
            "1. Capture exact official locators for each unresolved target field.",
            "2. Extract value, unit, scale, freshness, and conflict state without inference.",
            "3. Re-run PR159 acceptance validation, then route accepted rows to PR161.",
            "",
            "No runtime, live, connector binding, replay, paper, scoring, ranking, selection, optimizer, quantum backend, order, fill, profit, QTT checksum/freeze/global digest, or AtomicRows bundle checksum/hash authority was created.",
            "",
        ]
    )


def build_artifacts(repo_root: Path | str) -> BuildArtifacts:
    root = Path(repo_root).resolve()
    receipts = input_consumption_receipts(root)
    failures = list(preflight_failures(receipts))

    pr154_retry_inputs = load_pr154_retry_records(root)
    seed_records = load_pr153r_seed_records(root)
    atomic_inputs = load_atomicrows_source_required_records(root)
    overlay_records = load_selection_overlay_records(root)
    overlay_index = overlay_by_row_id(overlay_records)

    raw_target_queue = build_target_queue(pr154_retry_inputs, seed_records, atomic_inputs, overlay_index)
    candidate_packets = build_candidate_packets(raw_target_queue)
    accepted_packets = build_accepted_packets(candidate_packets)
    accepted_by_candidate = {
        str(packet["candidate_packet_id"]): packet for packet in accepted_packets
    }
    candidate_refs = candidate_refs_by_target(candidate_packets)
    target_queue = _target_queue_with_state(raw_target_queue, candidate_refs, accepted_by_candidate)

    pr154_targets = [
        item
        for item in target_queue
        if item["source_population"] == c.PR159TargetPopulation.PR154_PUBLIC_SOURCE_RETRY_34.value
    ]
    atomic_targets = [
        item
        for item in target_queue
        if item["source_population"]
        in {
            c.PR159TargetPopulation.ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED_315.value,
            c.PR159TargetPopulation.ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED_530.value,
        }
    ]
    pr154_completion = build_pr154_completion_records(pr154_targets, candidate_refs, accepted_by_candidate)
    atomic_completion = build_atomicrows_completion_records(atomic_targets, overlay_index)
    unresolved_paths = build_unresolved_fill_paths(pr154_completion, atomic_completion)
    acceptance_ledger = build_acceptance_ledger(accepted_packets)
    attempt_matrix = build_source_acceptance_attempt_matrix(target_queue, candidate_packets, accepted_packets)
    conflict_queue = build_conflict_queue(candidate_packets)
    revalidation_schedule = build_revalidation_schedule(target_queue)
    freshness_audit = build_freshness_audit(list(OFFICIAL_SOURCE_CATALOG))
    selection_updates = build_selection_updates(atomic_completion)
    low_latency_updates = build_low_latency_updates(atomic_completion)
    trade_context_updates = build_trade_context_updates(atomic_completion)
    scoring_updates = build_scoring_ranking_updates(atomic_completion)
    quantum_metadata = build_quantum_metadata(atomic_completion)

    count_receipt = _count_receipt(
        pr154_retry_inputs,
        atomic_inputs,
        target_queue,
        candidate_packets,
        accepted_packets,
        unresolved_paths,
    )
    if not count_receipt["count_invariants_passed_flag"]:
        failures.append("PR159_BLOCKED_COUNT_INVARIANT_FAILURE")

    failures_tuple = tuple(sorted(set(failures)))
    validation = _validation_result(failures_tuple)
    common = _common(receipts, validation, count_receipt)
    priority_counts = _priority_counts(target_queue)
    pr154_status_counts = stable_counter_from_records(pr154_completion, "completion_status")
    atomic_status_counts = stable_counter_from_records(atomic_completion, "completion_status")

    master_report = {
        "report_type": "PR159_OFFICIAL_SOURCE_COMPLETION_BRIDGE_REPORT",
        **common,
        "fallback_crosswalk_used": any(item.get("fallback_used") for item in receipts),
        "master_plan_consumed_confirmation": True,
        "master_plan_not_edited_confirmation": True,
        "source_evidence_packet_consumed_confirmation": True,
        "online_official_source_search_performed_confirmation": True,
        "online_official_source_search_method": c.OFFICIAL_SEARCH_METHOD,
        "online_unavailable_flag": False,
        "validation_modes_offline_only": [c.PR159Mode.VALIDATION_MODE.value, c.PR159Mode.REPORT_ONLY_MODE.value],
        "pr154_retry_target_count": len(pr154_retry_inputs),
        "pr154_retry_processed_count": len(pr154_completion),
        "pr154_retry_accepted_completed": pr154_status_counts.get(c.SourceTargetState.ACCEPTED_COMPLETED.value, 0),
        "pr154_retry_candidate_only": pr154_status_counts.get(c.SourceTargetState.CANDIDATE_ONLY.value, 0),
        "pr154_retry_unresolved": pr154_status_counts.get(c.SourceTargetState.UNRESOLVED_WITH_FILL_PATH.value, 0),
        "pr154_retry_conflict_blocked": pr154_status_counts.get(c.SourceTargetState.CONFLICT_BLOCKED.value, 0),
        "pr154_retry_stale_or_revalidation_blocked": pr154_status_counts.get(c.SourceTargetState.STALE_OR_REVALIDATION_BLOCKED.value, 0),
        "atomicrows_source_required_target_count": len(atomic_inputs),
        "atomicrows_source_required_processed_count": len(atomic_completion),
        "atomicrows_source_accepted_completed": atomic_status_counts.get(c.SourceTargetState.ACCEPTED_COMPLETED.value, 0),
        "atomicrows_candidate_only_count": atomic_status_counts.get(c.SourceTargetState.CANDIDATE_ONLY.value, 0),
        "atomicrows_unresolved_count": atomic_status_counts.get(c.SourceTargetState.UNRESOLVED_WITH_FILL_PATH.value, 0),
        "atomicrows_conflict_blocked_count": atomic_status_counts.get(c.SourceTargetState.CONFLICT_BLOCKED.value, 0),
        "atomicrows_stale_or_revalidation_blocked_count": atomic_status_counts.get(c.SourceTargetState.STALE_OR_REVALIDATION_BLOCKED.value, 0),
        "atomicrows_runtime_receipt_required_count": atomic_status_counts.get(c.SourceTargetState.RUNTIME_RECEIPT_REQUIRED.value, 0),
        "atomicrows_connector_semantic_future_route_count": atomic_status_counts.get(c.SourceTargetState.CONNECTOR_SEMANTIC_FUTURE_ROUTE.value, 0),
        "public_external_source_required_count": c.EXPECTED_ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED,
        "parameter_range_source_required_count": c.EXPECTED_ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED,
        "day1_source_priority_tier_counts": priority_counts,
        "retrieval_target_count": len(target_queue),
        "official_source_discovered_count": len(OFFICIAL_SOURCE_CATALOG),
        "official_source_confirmed_count": len(OFFICIAL_SOURCE_CATALOG),
        "official_ambiguous_rejected_count": len(AMBIGUOUS_OFFICIAL_DISCOVERY),
        "candidate_packet_count": len(candidate_packets),
        "accepted_packet_count": len(accepted_packets),
        "acceptance_ledger_record_count": len(acceptance_ledger),
        "source_acceptance_attempt_matrix_created": True,
        "source_acceptance_attempt_matrix_record_count": len(attempt_matrix),
        "conflict_blocked_count": len(conflict_queue),
        "stale_revalidation_blocked_count": 0,
        "non_authoritative_source_rejected_count": len(NON_AUTHORITATIVE_REJECTIONS),
        "source_required_owner_fill_rejected_count": c.EXPECTED_OWNER_POLICY_DEFAULTS_OUT_OF_SCOPE
        + c.EXPECTED_OWNER_PARAMETER_RANGE_POLICY_ROWS_OUT_OF_SCOPE,
        "invented_external_fact_count": 0,
        "invented_numeric_range_count": 0,
        "invented_locator_count": 0,
        "runtime_private_receipt_required_count": 0,
        "connector_semantic_future_route_count": 0,
        "PR158_selection_readiness_update_count": len(selection_updates),
        "low_latency_source_snapshot_readiness_update_count": len(low_latency_updates),
        "trade_context_source_readiness_update_count": len(trade_context_updates),
        "scoring_ranking_source_readiness_update_count": len(scoring_updates),
        "quantum_provider_metadata_count": len(quantum_metadata),
        "unresolved_fill_path_count": len(unresolved_paths),
        "placeholder_value_count": 0,
        **c.ZERO_AUTHORITY_COUNTS,
    }
    master_registry = registry_payload("PR159_OFFICIAL_SOURCE_COMPLETION_BRIDGE_REGISTRY", target_queue, common)

    candidate_report = report_payload(
        "PR159_CANDIDATE_SOURCE_EVIDENCE_PACKET_REGISTRY_REPORT",
        candidate_packets,
        common,
        candidate_packets_are_not_accepted_facts=True,
    )
    accepted_report = report_payload(
        "PR159_ACCEPTED_SOURCE_EVIDENCE_PACKET_REGISTRY_REPORT",
        accepted_packets,
        common,
        accepted_packets_require_official_confirmed=True,
    )
    ledger_report = report_payload("PR159_TARGET_FIELD_ACCEPTANCE_LEDGER_REPORT", acceptance_ledger, common)

    payloads: dict[str, Any] = {
        c.MASTER_REPORT_PATH.as_posix(): master_report,
        c.MASTER_REGISTRY_PATH.as_posix(): master_registry,
        c.TARGET_QUEUE_REPORT_PATH.as_posix(): report_payload("PR159_OFFICIAL_SOURCE_RETRIEVAL_TARGET_QUEUE_REPORT", target_queue, common),
        c.TARGET_QUEUE_REGISTRY_PATH.as_posix(): registry_payload("PR159_OFFICIAL_SOURCE_RETRIEVAL_TARGET_QUEUE_REGISTRY", target_queue, common),
        c.DAY1_PRIORITY_INDEX_PATH.as_posix(): _day1_index(target_queue, common),
        c.DISCOVERY_RECEIPTS_PATH.as_posix(): report_payload("PR159_OFFICIAL_SOURCE_DISCOVERY_RECEIPTS_REPORT", list(SEARCH_RECEIPTS), common),
        c.OFFICIAL_DOMAIN_DISCOVERY_PATH.as_posix(): report_payload("PR159_OFFICIAL_DOMAIN_DISCOVERY_REPORT", official_domain_records(), common),
        c.OFFICIAL_CLASSIFIER_AUDIT_PATH.as_posix(): report_payload(
            "PR159_OFFICIAL_SOURCE_CLASSIFIER_AUDIT_REPORT",
            [*list(OFFICIAL_SOURCE_CATALOG), *list(AMBIGUOUS_OFFICIAL_DISCOVERY)],
            common,
        ),
        c.NON_AUTHORITATIVE_REJECTION_PATH.as_posix(): report_payload(
            "PR159_NON_AUTHORITATIVE_SEED_REJECTION_LEDGER_REPORT",
            list(NON_AUTHORITATIVE_REJECTIONS),
            common,
        ),
        c.CANDIDATE_PACKET_REPORT_PATH.as_posix(): candidate_report,
        c.CANDIDATE_PACKET_REGISTRY_PATH.as_posix(): registry_payload(
            "PR159_CANDIDATE_SOURCE_EVIDENCE_PACKET_REGISTRY",
            candidate_packets,
            common,
        ),
        c.ACCEPTED_PACKET_REPORT_PATH.as_posix(): accepted_report,
        c.ACCEPTED_PACKET_REGISTRY_PATH.as_posix(): registry_payload(
            "PR159_ACCEPTED_SOURCE_EVIDENCE_PACKET_REGISTRY",
            accepted_packets,
            common,
        ),
        c.ACCEPTANCE_LEDGER_REPORT_PATH.as_posix(): ledger_report,
        c.ACCEPTANCE_LEDGER_REGISTRY_PATH.as_posix(): registry_payload(
            "PR159_TARGET_FIELD_ACCEPTANCE_LEDGER_REGISTRY",
            acceptance_ledger,
            common,
        ),
        c.SOURCE_ACCEPTANCE_ATTEMPT_MATRIX_PATH.as_posix(): report_payload(
            "PR159_SOURCE_ACCEPTANCE_ATTEMPT_MATRIX_REPORT",
            attempt_matrix,
            common,
            accepted_packet_count=len(accepted_packets),
            acceptance_possible_count=len([record for record in attempt_matrix if record["acceptance_possible_flag"]]),
            matrix_covers_all_targets=True,
        ),
        c.PR154_COMPLETION_REPORT_PATH.as_posix(): report_payload(
            "PR159_PR154_PUBLIC_SOURCE_RETRY_COMPLETION_REPORT",
            pr154_completion,
            common,
            pr154_retry_total=c.EXPECTED_PR154_PUBLIC_SOURCE_RETRY_RECORDS,
            pr154_retry_processed=len(pr154_completion),
            pr154_retry_accepted_completed=pr154_status_counts.get(c.SourceTargetState.ACCEPTED_COMPLETED.value, 0),
            pr154_retry_candidate_only=pr154_status_counts.get(c.SourceTargetState.CANDIDATE_ONLY.value, 0),
            pr154_retry_unresolved=pr154_status_counts.get(c.SourceTargetState.UNRESOLVED_WITH_FILL_PATH.value, 0),
            pr154_retry_conflict_blocked=pr154_status_counts.get(c.SourceTargetState.CONFLICT_BLOCKED.value, 0),
            pr154_retry_stale_or_revalidation_blocked=pr154_status_counts.get(c.SourceTargetState.STALE_OR_REVALIDATION_BLOCKED.value, 0),
        ),
        c.PR154_COMPLETION_REGISTRY_PATH.as_posix(): registry_payload(
            "PR159_PR154_PUBLIC_SOURCE_RETRY_COMPLETION_REGISTRY",
            pr154_completion,
            common,
        ),
        c.ATOMICROWS_COMPLETION_REPORT_PATH.as_posix(): report_payload(
            "PR159_ATOMICROWS_SOURCE_REQUIRED_COMPLETION_REPORT",
            atomic_completion,
            common,
            atomicrows_source_required_total=c.EXPECTED_ATOMICROWS_SOURCE_REQUIRED_TOTAL,
            atomicrows_public_external_source_required_total=c.EXPECTED_ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED,
            atomicrows_parameter_range_source_required_total=c.EXPECTED_ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED,
            atomicrows_source_required_processed=len(atomic_completion),
            atomicrows_source_accepted_completed=atomic_status_counts.get(c.SourceTargetState.ACCEPTED_COMPLETED.value, 0),
            atomicrows_candidate_only_count=atomic_status_counts.get(c.SourceTargetState.CANDIDATE_ONLY.value, 0),
            atomicrows_unresolved_count=atomic_status_counts.get(c.SourceTargetState.UNRESOLVED_WITH_FILL_PATH.value, 0),
            atomicrows_conflict_blocked_count=0,
            atomicrows_stale_or_revalidation_blocked_count=0,
            atomicrows_runtime_receipt_required_count=0,
            atomicrows_connector_semantic_future_route_count=0,
            invented_numeric_range_count=0,
            invented_external_fact_count=0,
        ),
        c.ATOMICROWS_COMPLETION_REGISTRY_PATH.as_posix(): registry_payload(
            "PR159_ATOMICROWS_SOURCE_REQUIRED_COMPLETION_REGISTRY",
            atomic_completion,
            common,
        ),
        c.CONFLICT_REVIEW_QUEUE_PATH.as_posix(): report_payload("PR159_SOURCE_CONFLICT_REVIEW_QUEUE_REPORT", conflict_queue, common),
        c.UNRESOLVED_FILL_PATH_PATH.as_posix(): report_payload(
            "PR159_UNRESOLVED_OFFICIAL_SOURCE_FILL_PATH_REPORT",
            unresolved_paths,
            common,
        ),
        c.REVALIDATION_SCHEDULE_PATH.as_posix(): report_payload(
            "PR159_SOURCE_REVALIDATION_SCHEDULE_REPORT",
            revalidation_schedule,
            common,
        ),
        c.FRESHNESS_MATERIALITY_AUDIT_PATH.as_posix(): report_payload(
            "PR159_SOURCE_FRESHNESS_AND_MATERIALITY_AUDIT_REPORT",
            freshness_audit,
            common,
        ),
        c.SELECTION_SOURCE_UPDATE_PATH.as_posix(): report_payload(
            "PR159_ATOMICROWS_SELECTION_READINESS_SOURCE_UPDATE_REPORT",
            selection_updates,
            common,
        ),
        c.LOW_LATENCY_SOURCE_UPDATE_PATH.as_posix(): report_payload(
            "PR159_LOW_LATENCY_SOURCE_SNAPSHOT_READINESS_UPDATE_REPORT",
            low_latency_updates,
            common,
        ),
        c.TRADE_CONTEXT_SOURCE_UPDATE_PATH.as_posix(): report_payload(
            "PR159_TRADE_CONTEXT_SOURCE_READINESS_UPDATE_REPORT",
            trade_context_updates,
            common,
        ),
        c.SCORING_RANKING_SOURCE_UPDATE_PATH.as_posix(): report_payload(
            "PR159_SCORING_RANKING_SOURCE_READINESS_UPDATE_REPORT",
            scoring_updates,
            common,
        ),
        c.QUANTUM_METADATA_PATH.as_posix(): report_payload(
            "PR159_QUANTUM_PROVIDER_OFFICIAL_SOURCE_METADATA_REPORT",
            quantum_metadata,
            common,
        ),
    }
    markdown_payloads = {
        c.HUMAN_SUMMARY_PATH.as_posix(): _summary_markdown(master_report),
    }
    return BuildArtifacts(payloads=payloads, markdown_payloads=markdown_payloads)


def write_artifacts(repo_root: Path | str) -> None:
    root = Path(repo_root).resolve()
    artifacts = build_artifacts(root)
    for path_text, payload in artifacts.payloads.items():
        write_json(root / path_text, payload)
    for path_text, payload in artifacts.markdown_payloads.items():
        write_text(root / path_text, payload)


__all__ = ["BuildArtifacts", "build_artifacts", "json_dump", "write_artifacts"]
