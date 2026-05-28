"""Top-level PR160 artifact construction and writing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import agent_responsibility_update
from . import backlog_delta
from . import candidate_route_matrix
from . import connector_runtime_future_route
from . import constants as c
from . import formula_derived_route
from . import low_latency_readiness_update
from . import owner_decision_packet
from . import owner_policy_route
from . import pr159r_source_requeue
from . import pr161_atomicrows_materialization_route
from . import pr163_agent_binding_route
from . import private_doc_route
from . import quantum_classical_compatibility_update
from . import scoring_ranking_readiness_update
from . import selection_readiness_update
from . import trade_context_readiness_update
from .basis_reconciliation import build_basis_audit
from .final_route_decision import build_final_decisions
from .input_discovery import build_source_records
from .io import json_dump, read_json, stable_counter_from_records, write_json, write_text
from .models import BuildArtifacts
from .orchestration_preflight import (
    input_consumption_receipts,
    orchestration_alignment_receipt,
    preflight_failures,
)
from .registry import registry_payload, report_payload
from .route_arbitration import build_arbitration_audit
from .route_collision_audit import build_route_collision_audit


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
        "stable_record_sort_key": ["PR154_target_id", "request_id_or_record_id"],
        "wall_clock_timestamps_used": False,
        "runtime_git_branch_or_head_used": False,
        "random_values_used": False,
        "local_absolute_paths_used": False,
        "repo_relative_paths_only": True,
        "validation_refreshes_online_context": False,
    }


def _count_receipt(decisions: list[Mapping[str, Any]]) -> dict[str, Any]:
    route_counts = stable_counter_from_records(decisions, "final_route_class")
    source_count = route_counts.get(
        c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value,
        0,
    )
    pr161_count = source_count + route_counts.get(
        c.ReclassificationFinalRouteClass.ATOMICROWS_SOURCE_VALUE_MATERIALIZATION_ROUTE_PR161.value,
        0,
    )
    connector_runtime_count = route_counts.get(
        c.ReclassificationFinalRouteClass.CONNECTOR_SEMANTIC_FUTURE_ROUTE.value,
        0,
    ) + route_counts.get(c.ReclassificationFinalRouteClass.RUNTIME_RECEIPT_FUTURE_ROUTE.value, 0)
    formula_derived_count = route_counts.get(
        c.ReclassificationFinalRouteClass.FORMULA_ONLY_DERIVED_ROUTE.value,
        0,
    ) + route_counts.get(
        c.ReclassificationFinalRouteClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS_ROUTE.value,
        0,
    )
    one_route_count = sum(1 for item in decisions if item.get("one_final_route_flag") is True)
    generic_remaining = sum(
        1
        for item in decisions
        if item.get("generic_split_reclassification_state_remaining_flag") is True
    )
    return {
        "pr154_split_reclassification_input_count": c.EXPECTED_SPLIT_RECLASSIFICATION_RECORDS,
        "split_records_processed_count": len(decisions),
        "final_route_decision_count": len(decisions),
        "one_final_route_per_record_count": one_route_count,
        "generic_split_blocker_remaining_count": generic_remaining,
        "routed_to_PR159R_count": source_count,
        "routed_to_PR161_count": pr161_count,
        "routed_to_PR163_count": route_counts.get(
            c.ReclassificationFinalRouteClass.EXACT_AGENT_BINDING_ROUTE_PR163.value,
            0,
        ),
        "routed_to_owner_policy_count": route_counts.get(
            c.ReclassificationFinalRouteClass.OWNER_INTERNAL_POLICY_ROUTE.value,
            0,
        ),
        "routed_to_owner_route_metadata_count": route_counts.get(
            c.ReclassificationFinalRouteClass.OWNER_ROUTE_METADATA_ROUTE.value,
            0,
        ),
        "routed_to_private_doc_attestation_count": route_counts.get(
            c.ReclassificationFinalRouteClass.PRIVATE_DOC_ATTESTATION_ROUTE.value,
            0,
        ),
        "routed_to_formula_or_generated_derivative_count": formula_derived_count,
        "routed_to_quantum_metadata_only_count": route_counts.get(
            c.ReclassificationFinalRouteClass.QUANTUM_CLASSICAL_METADATA_ONLY_ROUTE.value,
            0,
        ),
        "routed_to_connector_semantic_future_count": route_counts.get(
            c.ReclassificationFinalRouteClass.CONNECTOR_SEMANTIC_FUTURE_ROUTE.value,
            0,
        ),
        "routed_to_runtime_receipt_future_count": route_counts.get(
            c.ReclassificationFinalRouteClass.RUNTIME_RECEIPT_FUTURE_ROUTE.value,
            0,
        ),
        "routed_to_connector_runtime_future_count": connector_runtime_count,
        "routed_to_scoring_ranking_metadata_count": route_counts.get(
            c.ReclassificationFinalRouteClass.SCORING_RANKING_METADATA_ROUTE.value,
            0,
        ),
        "routed_to_replay_paper_future_count": route_counts.get(
            c.ReclassificationFinalRouteClass.REPLAY_PAPER_EVALUATION_FUTURE_ROUTE.value,
            0,
        ),
        "still_owner_choice_required_count": route_counts.get(
            c.ReclassificationFinalRouteClass.OWNER_CLASSIFICATION_DECISION_REQUIRED_WITH_CHOICES.value,
            0,
        ),
        "still_blocked_invalid_or_unsupported_count": route_counts.get(
            c.ReclassificationFinalRouteClass.INVALID_OR_UNSUPPORTED_WITH_FILL_PATH.value,
            0,
        ),
        "orphan_route_count": 0,
        "total_pr154_universe_count": c.EXPECTED_PR154_UNIVERSE_COUNT,
        "total_atomicrows_universe_count": c.EXPECTED_ATOMICROWS_UNIVERSE_COUNT,
        "pr159_unresolved_source_target_count_unchanged_by_PR160": c.EXPECTED_PR159_UNRESOLVED_SOURCE_TARGET_COUNT,
        "post_PR160_backlog_delta_summary": "33 generic split/reclassification blockers closed into typed downstream routes.",
        "route_counts": route_counts,
        "count_invariants_passed_flag": (
            len(decisions) == c.EXPECTED_SPLIT_RECLASSIFICATION_RECORDS
            and one_route_count == c.EXPECTED_SPLIT_RECLASSIFICATION_RECORDS
            and generic_remaining == 0
            and sum(route_counts.values()) == c.EXPECTED_SPLIT_RECLASSIFICATION_RECORDS
        ),
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
        "route_closure_doctrine_ids": list(c.ROUTE_CLOSURE_DOCTRINE_IDS),
        "central_enum_value_sets": dict(c.CENTRAL_ENUM_VALUE_SETS),
        "input_consumption_receipt": receipts,
        "orchestration_alignment_receipt": orchestration_alignment_receipt(receipts),
        "count_invariant_receipt": dict(count_receipt),
        "determinism_receipt": _determinism_receipt(),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "validation_result": dict(validation),
    }


def _route_update_summary(
    *,
    pr159r_records: list[Mapping[str, Any]],
    pr161_records: list[Mapping[str, Any]],
    pr163_records: list[Mapping[str, Any]],
    private_doc_records: list[Mapping[str, Any]],
    owner_policy_records: list[Mapping[str, Any]],
    connector_runtime_records: list[Mapping[str, Any]],
    formula_derived_records: list[Mapping[str, Any]],
) -> dict[str, int]:
    return {
        "pr159r_source_requeue_count": len(pr159r_records),
        "pr161_materialization_route_count": len(pr161_records),
        "pr163_agent_binding_route_count": len(pr163_records),
        "private_doc_attestation_route_count": len(private_doc_records),
        "owner_policy_route_count": len(owner_policy_records),
        "connector_runtime_future_route_count": len(connector_runtime_records),
        "formula_derived_route_count": len(formula_derived_records),
    }


def _summary_markdown(master_report: Mapping[str, Any], decisions: list[Mapping[str, Any]]) -> str:
    counts = master_report["count_invariant_receipt"]
    lines = [
        "# PR160 Split/Reclassification Route Closure Summary",
        "",
        f"Input split/reclassification records: {counts['pr154_split_reclassification_input_count']}",
        f"Processed records: {counts['split_records_processed_count']}",
        f"Final route decisions: {counts['final_route_decision_count']}",
        f"Generic split blockers remaining: {counts['generic_split_blocker_remaining_count']}",
        "",
        "Final route counts:",
    ]
    for route, count in sorted(counts["route_counts"].items()):
        lines.append(f"- {route}: {count}")
    lines.extend(
        [
            "",
            "Per-record route closure:",
        ]
    )
    for item in decisions:
        lines.append(
            f"- {item['PR154_target_id']}: {item['final_route_class']} -> {item['exact_next_action']}"
        )
    lines.extend(
        [
            "",
            "Post-PR160 backlog delta:",
            "- 3 source-required records are requeued to PR159R and then PR161/PR162 after accepted evidence exists.",
            "- 12 optimizer metadata records route to future optimizer/replay/paper evaluation.",
            "- 12 quantum/classical records are closed as metadata-only.",
            "- 3 VQE tolerance records route to future PR169 runtime/quantum evidence gates.",
            "- 3 scoring/ranking metadata records route to PR164 and later replay/paper gates.",
            "",
            "No runtime, live, connector binding, replay, paper, scoring, ranking, selection, optimizer, quantum backend, order, fill, profit, QTT checksum/freeze/global digest, or AtomicRows bundle checksum/hash authority was created.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_existing_count(root: Path, rel_path: Path) -> int | None:
    path = root / rel_path
    if not path.exists() or path.suffix != ".json":
        return None
    payload = read_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("record_count"), int):
        return int(payload["record_count"])
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return len(payload["records"])
    return None


def build_artifacts(repo_root: Path | str) -> BuildArtifacts:
    root = Path(repo_root).resolve()
    receipts = input_consumption_receipts(root)
    failures = list(preflight_failures(receipts))
    source_records = build_source_records(root)
    matrix_records = candidate_route_matrix.build_candidate_route_matrix(source_records)
    decisions = build_final_decisions(source_records, matrix_records)
    count_receipt = _count_receipt(decisions)
    if not count_receipt["count_invariants_passed_flag"]:
        failures.append("PR160_BLOCKED_COUNT_INVARIANT_FAILURE")
    if _load_existing_count(root, c.PR157_PR154_REGISTRY_PATH) != c.EXPECTED_PR154_UNIVERSE_COUNT:
        failures.append("PR160_PR154_UNIVERSE_COUNT_CHANGED")
    if _load_existing_count(root, c.PR158_SELECTION_OVERLAY_REGISTRY_PATH) != c.EXPECTED_ATOMICROWS_UNIVERSE_COUNT:
        failures.append("PR160_ATOMICROWS_UNIVERSE_COUNT_CHANGED")

    failures_tuple = tuple(sorted(set(failures)))
    validation = _validation_result(failures_tuple)
    common = _common(receipts, validation, count_receipt)

    basis_records = build_basis_audit(matrix_records)
    collision_records = build_route_collision_audit(matrix_records)
    arbitration_records = build_arbitration_audit(matrix_records)
    pr159r_records = pr159r_source_requeue.build(decisions)
    pr161_records = pr161_atomicrows_materialization_route.build(decisions)
    pr163_records = pr163_agent_binding_route.build(decisions)
    private_doc_records = private_doc_route.build(decisions)
    owner_policy_records = owner_policy_route.build(decisions)
    connector_runtime_records = connector_runtime_future_route.build(decisions)
    formula_derived_records = formula_derived_route.build(decisions)
    selection_records = selection_readiness_update.build(decisions)
    trade_context_records = trade_context_readiness_update.build(decisions)
    low_latency_records = low_latency_readiness_update.build(decisions)
    quantum_records = quantum_classical_compatibility_update.build(decisions)
    agent_records = agent_responsibility_update.build(decisions)
    scoring_records = scoring_ranking_readiness_update.build(decisions)
    backlog = backlog_delta.build(decisions)
    owner_packet = owner_decision_packet.build(decisions)

    route_update_summary = _route_update_summary(
        pr159r_records=pr159r_records,
        pr161_records=pr161_records,
        pr163_records=pr163_records,
        private_doc_records=private_doc_records,
        owner_policy_records=owner_policy_records,
        connector_runtime_records=connector_runtime_records,
        formula_derived_records=formula_derived_records,
    )
    master_report = {
        "report_type": "PR160_PR154_SPLIT_RECLASSIFICATION_ROUTE_CLOSURE_REPORT",
        **common,
        "fallback_crosswalk_used": any(item.get("fallback_used") for item in receipts),
        "master_plan_consumed_confirmation": True,
        "master_plan_not_edited_confirmation": True,
        "source_evidence_packet_consumed_confirmation": True,
        "online_classification_context_used": False,
        "official_online_docs_used_for_classification_routing_count": 0,
        "official_online_docs_used_as_accepted_source_value_authority_count": 0,
        "official_online_docs_not_accepted_value_authority_confirmation": True,
        "route_update_summary": route_update_summary,
        "selection_readiness_update_count": len(selection_records),
        "trade_context_readiness_update_count": len(trade_context_records),
        "low_latency_readiness_update_count": len(low_latency_records),
        "scoring_ranking_readiness_update_count": len(scoring_records),
        "agent_responsibility_update_count": len(agent_records),
        "quantum_classical_compatibility_update_count": len(quantum_records),
        "owner_choice_packet_created_count": 1 if owner_packet["decision_required_count"] else 0,
        "placeholder_value_count": 0,
        **c.ZERO_EXECUTION_COUNTS,
        "records": decisions,
        "record_count": len(decisions),
    }

    payloads: dict[str, Any] = {
        c.MASTER_REPORT_PATH.as_posix(): master_report,
        c.MASTER_REGISTRY_PATH.as_posix(): registry_payload(
            "PR160_PR154_SPLIT_RECLASSIFICATION_ROUTE_CLOSURE_REGISTRY",
            decisions,
            common,
        ),
        c.DECISION_LEDGER_REPORT_PATH.as_posix(): report_payload(
            "PR160_RECLASSIFICATION_DECISION_LEDGER_REPORT",
            decisions,
            common,
        ),
        c.DECISION_LEDGER_REGISTRY_PATH.as_posix(): registry_payload(
            "PR160_RECLASSIFICATION_DECISION_LEDGER_REGISTRY",
            decisions,
            common,
        ),
        c.CANDIDATE_ROUTE_MATRIX_PATH.as_posix(): report_payload(
            "PR160_RECLASSIFICATION_CANDIDATE_ROUTE_MATRIX_REPORT",
            matrix_records,
            common,
        ),
        c.BASIS_AUDIT_PATH.as_posix(): report_payload(
            "PR160_RECLASSIFICATION_BASIS_AUDIT_REPORT",
            basis_records,
            common,
        ),
        c.ROUTE_COLLISION_AUDIT_PATH.as_posix(): report_payload(
            "PR160_ROUTE_COLLISION_AUDIT_REPORT",
            collision_records,
            common,
            unresolved_collision_count=sum(
                1 for item in collision_records if item["unresolved_collision_blocked_flag"]
            ),
        ),
        c.ARBITRATION_AUDIT_PATH.as_posix(): report_payload(
            "PR160_DETERMINISTIC_ROUTE_ARBITRATION_AUDIT_REPORT",
            arbitration_records,
            common,
        ),
        c.PR159R_SOURCE_REQUEUE_PATH.as_posix(): report_payload(
            "PR160_PR159R_SOURCE_TARGET_REQUEUE_REPORT",
            pr159r_records,
            common,
        ),
        c.PR161_MATERIALIZATION_ROUTE_PATH.as_posix(): report_payload(
            "PR160_PR161_ATOMICROWS_MATERIALIZATION_ROUTE_UPDATE_REPORT",
            pr161_records,
            common,
        ),
        c.PR163_AGENT_BINDING_ROUTE_PATH.as_posix(): report_payload(
            "PR160_PR163_AGENT_BINDING_ROUTE_UPDATE_REPORT",
            pr163_records,
            common,
        ),
        c.PRIVATE_DOC_ROUTE_PATH.as_posix(): report_payload(
            "PR160_PRIVATE_DOC_ATTESTATION_ROUTE_UPDATE_REPORT",
            private_doc_records,
            common,
        ),
        c.OWNER_POLICY_ROUTE_PATH.as_posix(): report_payload(
            "PR160_OWNER_POLICY_ROUTE_UPDATE_REPORT",
            owner_policy_records,
            common,
        ),
        c.CONNECTOR_RUNTIME_ROUTE_PATH.as_posix(): report_payload(
            "PR160_CONNECTOR_RUNTIME_FUTURE_ROUTE_UPDATE_REPORT",
            connector_runtime_records,
            common,
        ),
        c.FORMULA_DERIVED_ROUTE_PATH.as_posix(): report_payload(
            "PR160_FORMULA_DERIVED_ROUTE_UPDATE_REPORT",
            formula_derived_records,
            common,
        ),
        c.SELECTION_UPDATE_PATH.as_posix(): report_payload(
            "PR160_ATOMICROWS_SELECTION_READINESS_RECLASSIFICATION_UPDATE_REPORT",
            selection_records,
            common,
        ),
        c.TRADE_CONTEXT_UPDATE_PATH.as_posix(): report_payload(
            "PR160_TRADE_CONTEXT_RECLASSIFICATION_READINESS_UPDATE_REPORT",
            trade_context_records,
            common,
        ),
        c.LOW_LATENCY_UPDATE_PATH.as_posix(): report_payload(
            "PR160_LOW_LATENCY_RECLASSIFICATION_READINESS_UPDATE_REPORT",
            low_latency_records,
            common,
        ),
        c.QUANTUM_COMPAT_UPDATE_PATH.as_posix(): report_payload(
            "PR160_QUANTUM_CLASSICAL_RECLASSIFICATION_COMPATIBILITY_UPDATE_REPORT",
            quantum_records,
            common,
        ),
        c.AGENT_RESPONSIBILITY_UPDATE_PATH.as_posix(): report_payload(
            "PR160_AGENT_RESPONSIBILITY_RECLASSIFICATION_UPDATE_REPORT",
            agent_records,
            common,
        ),
        c.SCORING_RANKING_UPDATE_PATH.as_posix(): report_payload(
            "PR160_SCORING_RANKING_RECLASSIFICATION_READINESS_UPDATE_REPORT",
            scoring_records,
            common,
        ),
        c.BACKLOG_DELTA_PATH.as_posix(): {
            "report_type": "PR160_POST_RECLASSIFICATION_BACKLOG_DELTA_REPORT",
            **common,
            **backlog,
        },
        c.OWNER_DECISION_PACKET_PATH.as_posix(): {
            **owner_packet,
            **common,
        },
    }
    markdown_payloads = {
        c.HUMAN_SUMMARY_PATH.as_posix(): _summary_markdown(master_report, decisions)
    }
    return BuildArtifacts(payloads=payloads, markdown_payloads=markdown_payloads)


def write_artifacts(repo_root: Path | str) -> None:
    root = Path(repo_root).resolve()
    artifacts = build_artifacts(root)
    for rel_path, payload in artifacts.payloads.items():
        write_json(root / rel_path, payload)
    for rel_path, payload in artifacts.markdown_payloads.items():
        write_text(root / rel_path, payload)


def build_artifacts_json(repo_root: Path | str) -> str:
    return json_dump(build_artifacts(repo_root).payloads)
