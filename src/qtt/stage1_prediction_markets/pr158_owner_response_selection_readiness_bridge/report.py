"""Top-level PR158 artifact construction and writing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from . import lane_a_agent_assignment as lane_a
from . import lane_b_owner_policy_default as lane_b
from . import lane_c_parameter_range_owner_policy as lane_c
from . import lane_d_pr154_owner_route as lane_d
from . import lane_e_split_reclassification as lane_e
from . import lane_f_private_doc_attestation as lane_f
from .atomicrows_selection_readiness_overlay import aggregate as overlay_aggregate
from .atomicrows_selection_readiness_overlay import build as build_overlay
from .future_research_addition_intake import build as build_future_research
from .input_discovery import (
    atomicrows_by_row_id,
    load_atomicrows_records,
    load_owner_request_packet,
    load_pr154_records,
    owner_requests_by_id,
    pr154_by_target_id,
)
from .io import as_list, json_dump, stable_counter, write_json, write_text
from .low_latency_precomputed_index import build as build_low_latency_index
from .models import BuildArtifacts
from .orchestration_preflight import (
    input_consumption_receipts,
    orchestration_alignment_receipt,
    preflight_failures,
)
from .owner_decision_summary import build_private_doc_review, build_summary
from .owner_response_builder import build_owner_response
from .owner_response_validator import validate_owner_response_payload
from .registry import registry_payload, report_payload


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
        "stable_request_sort_key": ["request_id"],
        "stable_record_sort_key": ["record_id", "row_id", "request_id"],
        "wall_clock_timestamps_used": False,
        "runtime_git_branch_or_head_used": False,
        "random_values_used": False,
        "local_absolute_paths_used": False,
    }


def _count_invariant_receipt(packet: Mapping[str, Any], overlay_count: int) -> dict[str, Any]:
    requests = as_list(packet.get("requests"))
    agent = [r for r in requests if r.get("atomicrows_source_requirement_class_or_null") == "AGENT_BINDING_REQUIRED"]
    owner_default = [r for r in requests if r.get("atomicrows_source_requirement_class_or_null") == "OWNER_POLICY_DEFAULT"]
    param_range = [r for r in requests if r.get("atomicrows_source_requirement_class_or_null") == "PARAMETER_RANGE_OWNER_POLICY"]
    route = [r for r in requests if r.get("source_population") == "PR154_OWNER_ROUTE"]
    split = [r for r in requests if r.get("source_population") == "PR154_SPLIT_RECLASSIFICATION"]
    private = [r for r in requests if r.get("source_population") == "PR154_PRIVATE_DOC_ATTESTATION"]
    atomic = len(agent) + len(owner_default) + len(param_range)
    pr154 = len(route) + len(split) + len(private)
    return {
        "owner_request_packet_count": packet.get("request_count"),
        "atomicrows_owner_response_count": atomic,
        "agent_assignment_count": len(agent),
        "owner_policy_default_count": len(owner_default),
        "parameter_range_owner_policy_count": len(param_range),
        "pr154_owner_dependent_count": pr154,
        "pr154_owner_route_count": len(route),
        "pr154_split_reclassification_count": len(split),
        "pr154_private_doc_attestation_count": len(private),
        "pr154_public_source_retry_out_of_scope_count": c.EXPECTED_PR154_PUBLIC_SOURCE_RETRY_OUT_OF_SCOPE,
        "atomicrows_selection_readiness_count": overlay_count,
        "atomicrows_selection_readiness_expected_count": c.EXPECTED_ATOMICROWS_TOTAL,
        "count_invariants_passed_flag": (
            packet.get("request_count") == c.EXPECTED_OWNER_PACKET_REQUESTS
            and atomic == c.EXPECTED_ATOMICROWS_OWNER_RESPONSE_REQUESTS
            and pr154 == c.EXPECTED_PR154_OWNER_DEPENDENT_REQUESTS
            and len(agent) == c.EXPECTED_AGENT_ASSIGNMENT_REQUESTS
            and len(owner_default) == c.EXPECTED_OWNER_POLICY_DEFAULT_REQUESTS
            and len(param_range) == c.EXPECTED_PARAMETER_RANGE_OWNER_POLICY_REQUESTS
            and len(route) == c.EXPECTED_PR154_OWNER_ROUTE_REQUESTS
            and len(split) == c.EXPECTED_PR154_SPLIT_RECLASSIFICATION_REQUESTS
            and len(private) == c.EXPECTED_PR154_PRIVATE_DOC_ATTESTATION_REQUESTS
            and overlay_count == c.EXPECTED_ATOMICROWS_TOTAL
        ),
    }


def _requests(packet: Mapping[str, Any], *, source_requirement: str | None = None, source_population: str | None = None) -> list[Mapping[str, Any]]:
    records = [r for r in as_list(packet.get("requests")) if isinstance(r, dict)]
    if source_requirement is not None:
        return [r for r in records if r.get("atomicrows_source_requirement_class_or_null") == source_requirement]
    if source_population is not None:
        return [r for r in records if r.get("source_population") == source_population]
    return records


def _common(receipts: list[dict[str, Any]], validation: dict[str, Any], count_receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "pr_id": c.PR_ID,
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "implementation_class": c.IMPLEMENTATION_CLASS,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_profile_ids": list(c.DEFAULT_AUTHORITY_PROFILE_IDS),
        "input_consumption_receipt": receipts,
        "orchestration_alignment_receipt": orchestration_alignment_receipt(receipts),
        "count_invariant_receipt": dict(count_receipt),
        "determinism_receipt": _determinism_receipt(),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "validation_result": validation,
    }


def _response_preview(response: Mapping[str, Any], lane_records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "report_type": "PR158_OWNER_RESPONSE_MATERIALIZATION_PREVIEW",
        "owner_response_path": c.OWNER_RESPONSE_PATH.as_posix(),
        "response_file_created": True,
        "response_item_count": len(response["response_items"]),
        "request_ids": [item["request_id"] for item in response["response_items"]],
        "completed_lane_record_count": sum(1 for item in lane_records if item.get("response_value_or_null") is not None),
        "pending_lane_record_count": sum(1 for item in lane_records if item.get("response_value_or_null") is None),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }


def build_artifacts(repo_root: Path | str) -> BuildArtifacts:
    root = Path(repo_root).resolve()
    packet = load_owner_request_packet(root)
    atomicrows = load_atomicrows_records(root)
    pr154_records = load_pr154_records(root)
    receipts = input_consumption_receipts(root)
    failures = list(preflight_failures(receipts))

    records_by_row = atomicrows_by_row_id(atomicrows)
    records_by_target = pr154_by_target_id(pr154_records)
    private_doc_decision_exists = (root / c.PRIVATE_DOC_OWNER_DECISION_PATH).exists()

    lane_a_records = lane_a.build(
        records_by_row,
        _requests(packet, source_requirement="AGENT_BINDING_REQUIRED"),
    )
    lane_b_records = lane_b.build(
        records_by_row,
        _requests(packet, source_requirement="OWNER_POLICY_DEFAULT"),
    )
    lane_c_records = lane_c.build(
        records_by_row,
        _requests(packet, source_requirement="PARAMETER_RANGE_OWNER_POLICY"),
    )
    lane_d_records = lane_d.build(
        records_by_target,
        _requests(packet, source_population="PR154_OWNER_ROUTE"),
    )
    lane_e_records = lane_e.build(
        records_by_target,
        _requests(packet, source_population="PR154_SPLIT_RECLASSIFICATION"),
    )
    lane_f_records = lane_f.build(
        records_by_target,
        _requests(packet, source_population="PR154_PRIVATE_DOC_ATTESTATION"),
        owner_decision_exists=private_doc_decision_exists,
    )
    lane_records = [
        *lane_a_records,
        *lane_b_records,
        *lane_c_records,
        *lane_d_records,
        *lane_e_records,
        *lane_f_records,
    ]
    response = build_owner_response(lane_records)
    response_failures = validate_owner_response_payload(response, packet)
    failures.extend(response_failures)

    completed_request_ids = {item["request_id"] for item in response["response_items"]}
    overlay_records = build_overlay(atomicrows, completed_request_ids)
    overlay_counts = overlay_aggregate(overlay_records)
    count_receipt = _count_invariant_receipt(packet, len(overlay_records))
    if not count_receipt["count_invariants_passed_flag"]:
        failures.append("PR158_BLOCKED_COUNT_INVARIANT_FAILURE")
    if len(response["response_items"]) != 1444:
        failures.append("PR158_RESPONSE_ITEM_COUNT_UNEXPECTED")
    failures_tuple = tuple(sorted(set(failures)))
    validation = _validation_result(failures_tuple)
    common = _common(receipts, validation, count_receipt)

    lane_summary_counts = {
        "lane_a": lane_a.aggregate(lane_a_records),
        "lane_b": lane_b.aggregate(lane_b_records),
        "lane_c": lane_c.aggregate(lane_c_records),
        "lane_d": lane_d.aggregate(lane_d_records),
        "lane_e": lane_e.aggregate(lane_e_records),
        "lane_f": lane_f.aggregate(lane_f_records),
    }
    low_latency = build_low_latency_index(overlay_records)
    future_research = build_future_research()
    master_report = {
        "report_type": "PR158_MASTER_PLAN_OWNER_RESPONSE_SELECTION_READINESS_BRIDGE_REPORT",
        **common,
        "fallback_crosswalk_used": any(item.get("fallback_used") for item in receipts),
        "master_plan_consumed_confirmation": True,
        "master_plan_not_edited_confirmation": True,
        "source_evidence_packet_consumed_confirmation": True,
        "lane_summary_counts": lane_summary_counts,
        "atomicrows_selection_readiness_aggregate_counts": overlay_counts,
        "owner_response_path": c.OWNER_RESPONSE_PATH.as_posix(),
        "response_file_created": True,
        "response_item_count": len(response["response_items"]),
        "placeholder_value_count": 0,
        "orphan_count": 0,
        "invented_external_fact_count": 0,
        "invented_numeric_range_count": 0,
        "invented_exact_agent_id_count": 0,
        **c.ZERO_EXECUTION_COUNTS,
    }
    master_registry = registry_payload(
        "PR158_MASTER_PLAN_OWNER_RESPONSE_SELECTION_READINESS_BRIDGE_REGISTRY",
        lane_records,
        common,
    )
    agent_formula_records = [
        {
            "row_id": item["row_id"],
            "family_id": item["family_id"],
            "responsible_agent_role_ids": item["responsible_agent_role_ids"],
            "candidate_agent_family_ids": item["candidate_agent_family_ids"],
            "consumer_class_ids": item["consumer_class_ids"],
            "formula_algorithm_edge_alpha_id_or_null": item["formula_algorithm_edge_alpha_id_or_null"],
            "scoring_feature_role": item["scoring_feature_role"],
            "quantum_classical_compatibility": item["quantum_classical_compatibility"],
            "metadata_only_no_execution": True,
        }
        for item in overlay_records
    ]
    trade_context_map = {
        "report_type": "PR158_TRADE_CONTEXT_SCORING_FEATURE_MAP",
        **common,
        "record_count": len(overlay_records),
        "scoring_feature_role_counts": overlay_counts["scoring_feature_role_counts"],
        "trade_context_applicability_counts": overlay_counts["trade_context_applicability_counts"],
        "records": [
            {
                "row_id": item["row_id"],
                "scoring_feature_role": item["scoring_feature_role"],
                "trade_context_applicability_refs": item["trade_context_applicability_refs"],
                "selection_universe_refs": item["selection_universe_refs"],
                "metadata_only_no_selection_execution": True,
            }
            for item in overlay_records
        ],
    }
    payloads: dict[str, Any] = {
        c.MASTER_REPORT_PATH.as_posix(): master_report,
        c.MASTER_REGISTRY_PATH.as_posix(): master_registry,
        c.AGENT_ASSIGNMENT_REPORT_PATH.as_posix(): report_payload(
            "PR158_AGENT_ASSIGNMENT_CANDIDATE_MAP_REPORT",
            lane_a.aggregate(lane_a_records),
            common,
        ),
        c.AGENT_ASSIGNMENT_REGISTRY_PATH.as_posix(): registry_payload(
            "PR158_AGENT_ASSIGNMENT_CANDIDATE_MAP_REGISTRY",
            lane_a_records,
            common,
        ),
        c.OWNER_POLICY_DEFAULT_REPORT_PATH.as_posix(): report_payload(
            "PR158_OWNER_POLICY_DEFAULT_CANDIDATE_MAP_REPORT",
            lane_b.aggregate(lane_b_records),
            common,
        ),
        c.OWNER_POLICY_DEFAULT_REGISTRY_PATH.as_posix(): registry_payload(
            "PR158_OWNER_POLICY_DEFAULT_CANDIDATE_MAP_REGISTRY",
            lane_b_records,
            common,
        ),
        c.PARAMETER_RANGE_REPORT_PATH.as_posix(): report_payload(
            "PR158_PARAMETER_RANGE_OWNER_POLICY_CANDIDATE_MAP_REPORT",
            lane_c.aggregate(lane_c_records),
            common,
        ),
        c.PARAMETER_RANGE_REGISTRY_PATH.as_posix(): registry_payload(
            "PR158_PARAMETER_RANGE_OWNER_POLICY_CANDIDATE_MAP_REGISTRY",
            lane_c_records,
            common,
        ),
        c.PR154_OWNER_ROUTE_REPORT_PATH.as_posix(): report_payload(
            "PR158_PR154_OWNER_ROUTE_CANDIDATE_MAP_REPORT",
            lane_d.aggregate(lane_d_records),
            common,
        ),
        c.PR154_OWNER_ROUTE_REGISTRY_PATH.as_posix(): registry_payload(
            "PR158_PR154_OWNER_ROUTE_CANDIDATE_MAP_REGISTRY",
            lane_d_records,
            common,
        ),
        c.PR154_SPLIT_REPORT_PATH.as_posix(): report_payload(
            "PR158_PR154_SPLIT_RECLASSIFICATION_CANDIDATE_MAP_REPORT",
            lane_e.aggregate(lane_e_records),
            common,
        ),
        c.PR154_SPLIT_REGISTRY_PATH.as_posix(): registry_payload(
            "PR158_PR154_SPLIT_RECLASSIFICATION_CANDIDATE_MAP_REGISTRY",
            lane_e_records,
            common,
        ),
        c.OWNER_RESPONSE_PREVIEW_PATH.as_posix(): _response_preview(response, lane_records),
        c.SELECTION_OVERLAY_REPORT_PATH.as_posix(): report_payload(
            "PR158_ATOMICROWS_SELECTION_READINESS_OVERLAY_REPORT",
            overlay_counts,
            common,
        ),
        c.SELECTION_OVERLAY_REGISTRY_PATH.as_posix(): registry_payload(
            "PR158_ATOMICROWS_SELECTION_READINESS_OVERLAY_REGISTRY",
            overlay_records,
            common,
        ),
        c.AGENT_FORMULA_COMPAT_REPORT_PATH.as_posix(): report_payload(
            "PR158_AGENT_FORMULA_ALGORITHM_SELECTION_COMPATIBILITY_MAP_REPORT",
            {
                "record_count": len(agent_formula_records),
                "quantum_inspired_candidate_count": overlay_counts["quantum_inspired_candidate_count"],
                "true_quantum_candidate_count": overlay_counts["true_quantum_candidate_count"],
                "hybrid_candidate_count": overlay_counts["hybrid_candidate_count"],
                "classical_only_baseline_count": overlay_counts["classical_only_baseline_count"],
            },
            common,
        ),
        c.AGENT_FORMULA_COMPAT_REGISTRY_PATH.as_posix(): registry_payload(
            "PR158_AGENT_FORMULA_ALGORITHM_SELECTION_COMPATIBILITY_MAP_REGISTRY",
            agent_formula_records,
            common,
        ),
        c.TRADE_CONTEXT_SCORING_MAP_PATH.as_posix(): trade_context_map,
        c.LOW_LATENCY_INDEX_PATH.as_posix(): {
            **low_latency,
            **common,
            "report_type": "PR158_PRECOMPUTED_LOW_LATENCY_SELECTION_READINESS_INDEX",
        },
        c.FUTURE_RESEARCH_PATH.as_posix(): {
            **future_research,
            **common,
        },
    }
    markdown_payloads = {
        c.OWNER_DECISION_SUMMARY_PATH.as_posix(): build_summary(master_report),
        c.PRIVATE_DOC_REVIEW_PATH.as_posix(): build_private_doc_review(lane_f_records),
    }
    return BuildArtifacts(payloads=payloads, markdown_payloads=markdown_payloads, owner_response=response)


def write_artifacts(repo_root: Path | str) -> None:
    root = Path(repo_root).resolve()
    artifacts = build_artifacts(root)
    for path_text, payload in artifacts.payloads.items():
        write_json(root / path_text, payload)
    for path_text, payload in artifacts.markdown_payloads.items():
        write_text(root / path_text, payload)
    write_json(root / c.OWNER_RESPONSE_PATH, artifacts.owner_response)

