"""Dictionary-coded compact shard records for PR161E."""

from __future__ import annotations

import json
from typing import Any

from . import constants as c


COMPACT_RECORD_VERSION = "PR161E_COMPACT_CANONICAL_RECORD_V1"
SHARED_DICTIONARY_VERSION = "PR161E_SHARED_DICTIONARY_V1"

COMPACTED_REPORT_FILENAMES = frozenset(
    {
        "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json",
        "PR161E_QKUBundleResultLedger.report.json",
        "PR161E_QKUReplayPaperProfitabilityLedger.report.json",
        "PR161E_QKUScenarioResultAttribution.report.json",
        "PR161E_QKUResultBackedRankingUpdateCandidates.report.json",
        "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json",
        "PR161E_QuantumClassicalHybridOutcomeComparison.report.json",
        "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json",
        "PR161E_ResultConfidenceGate.report.json",
        "PR161E_OwnerReviewResultPromotionQueue.report.json",
        "PR161E_AgentOutcomeTaskQueue.report.json",
        "PR161E_QKUGraphTraceabilityBridge.report.json",
    }
)

ROUTE_FIELDS = (
    "pr161c_registry_ref",
    "pr161c_graph_ref",
    "downstream_workflow_routes",
    "downstream_process_routes",
    "downstream_future_pr_routes",
    "downstream_owner_review_route",
    "downstream_future_live_gate_route",
)
AGENT_ROUTE_FIELDS = ("downstream_agent_roles",)
QKU_TRACE_FIELDS = (
    "qku_graph_node_id",
    "upstream_pr161a_or_pr161b_origin_if_available",
    "pr161d_score_ref_if_available",
    "pr161d_category_ranking_ref_if_available",
    "atomicrows_ref_if_available",
    "pr154_ref_if_available",
    "unmappable_reason_if_any",
    "result_backed_ranking_slot_id",
    "pre_result_quality_score",
    "pr161d_bundle_ref_if_available",
    "pr161d_scenario_matrix_ref_if_available",
    "pr161d_replay_paper_scenario_ref_if_available",
)
RECORD_TRACE_FIELDS = (
    "pr161d_bundle_ref_if_available",
    "pr161d_scenario_matrix_ref_if_available",
    "pr161d_replay_paper_scenario_ref_if_available",
    "pr161d_agent_task_ref_if_available",
    "pr161d_owner_review_ref_if_available",
)
AUTHORITY_BOUNDARY_FIELDS = (
    "no_live_authority_created_flag",
    "no_profit_guarantee_created_flag",
    "no_live_profit_evidence_created_flag",
    "no_profit_evidence_created_without_validated_result_packet_flag",
    "no_optimizer_execution_created_flag",
    "no_quantum_backend_execution_created_flag",
    "no_quantum_simulator_execution_created_flag",
    "no_qtt_sha_authority_created_flag",
    "no_qtt_generated_sha_authority_created_flag",
    "no_qtt_freeze_checksum_global_digest_authority_created_flag",
    "no_atomicrows_bundle_sha_authority_created_flag",
    "no_atomicrows_bundle_hash_freeze_authority_created_flag",
)
POLICY_FIELDS = (
    "owner_review_required_flag",
    "replay_paper_required_flag",
    "future_live_gate_required_flag",
    "result_packet_required_flag",
    "canonical_agent_role_not_runtime_agent_claim_flag",
    "promotion_allowed_flag",
    "active_ranking_mutation_created_flag",
    "future_positive_pattern_flag",
    "future_negative_pattern_flag",
)
COMPATIBILITY_POLICY_FIELDS = (
    "owner_review_route",
    "result_packet_id_if_available",
    "no_atomicrows_final_bundle_created_flag",
    "no_atomicrows_bundle_jsonl_created_flag",
    "no_atomicrows_bundle_sha_reference_created_flag",
    "no_atomicrows_bundle_hash_sha_freeze_authority_created_flag",
)
QCH_POLICY_FIELDS = (
    "quantum_applicability_class",
    "quantum_route_id_if_available",
    "classical_baseline_route_id_if_available",
    "hybrid_arbitration_route_id_if_available",
    "optimizer_family_id_if_available",
    "qaoa_metadata_candidate_if_available",
    "vqe_metadata_candidate_if_available",
    "annealing_metadata_candidate_if_available",
    "qubo_metadata_candidate_if_available",
    "ising_metadata_candidate_if_available",
    "replay_result_packet_id_if_available",
    "paper_result_packet_id_if_available",
    "no_quantum_backend_execution_flag",
    "no_quantum_simulator_execution_flag",
    "no_optimizer_execution_flag",
    "no_quantum_advantage_claim_flag",
    "no_latency_superiority_claim_without_validated_result_packet_flag",
)
RESULT_DETAIL_FIELDS = (
    "bundle_result_state",
    "replay_paper_evidence_class",
    "result_evidence_weight",
    "result_backed_score",
    "promotion_blocker",
    "scenario_learning_state",
    "ranking_update_state",
    "future_pattern_update_state",
    "comparison_state",
    "compatibility_state",
    "owner_review_state",
    "agent_task_state",
)
CONFIDENCE_STATE_FIELDS = (
    "sample_size_class",
    "confidence_class",
    "drawdown_class",
    "slippage_cost_class",
    "latency_percentile_class",
    "time_to_expiry_class",
    "liquidity_class",
    "regime_class",
    "calibration_quality_class",
    "brier_score_candidate_class",
    "log_loss_candidate_class",
    "result_consistency_class",
    "replay_paper_divergence_class",
    "quantum_classical_hybrid_divergence_class",
)
NUMERIC_FIELDS = tuple(c.RESULT_NUMERIC_FIELDS) + tuple(
    f"future_{field}" for field in c.RESULT_NUMERIC_FIELDS
)
DERIVED_OR_CANONICAL_FIELDS = (
    "record_id",
    "outcome_capture_record_id",
    "profitability_ledger_id",
    "scenario_result_attribution_id",
    "ranking_update_candidate_id",
    "future_profitability_pattern_record_id",
    "qku_id",
    "qku_ids",
    "qku_bundle_id",
    "qku_bundle_id_if_available",
    "scenario_matrix_id",
    "scenario_matrix_id_if_available",
    "replay_paper_scenario_id",
    "assigned_agent_role",
    "source_task_id",
    "owner_review_source_record_id",
    "atomicrow_id_if_available",
    "pr154_target_id_if_available",
    "compatibility_source_class",
)

GROUPED_FIELDS = frozenset(
    ROUTE_FIELDS
    + AGENT_ROUTE_FIELDS
    + QKU_TRACE_FIELDS
    + RECORD_TRACE_FIELDS
    + AUTHORITY_BOUNDARY_FIELDS
    + POLICY_FIELDS
    + COMPATIBILITY_POLICY_FIELDS
    + QCH_POLICY_FIELDS
    + RESULT_DETAIL_FIELDS
    + CONFIDENCE_STATE_FIELDS
    + NUMERIC_FIELDS
    + DERIVED_OR_CANONICAL_FIELDS
    + ("result_state", "validation_state", "evidence_state", "profitability_label")
)
DEFAULTABLE_COMPACT_FIELDS = (
    "schema_ref",
    "result_state_ref",
    "validation_state_ref",
    "evidence_state_ref",
    "profitability_label_ref",
    "policy_ref",
    "authority_boundary_ref",
    "owner_authority_ref",
    "route_ref",
    "agent_route_ref",
    "compatibility_policy_ref",
    "qch_policy_ref",
    "numeric_state_ref",
    "result_detail_ref",
    "confidence_state_ref",
    "field_group_ref",
)
QKU_TRACE_INDEX_FIELDS = (
    "upstream_origin_ref",
    "pre_result_quality_score",
    "pr161d_bundle_ref_if_available",
    "pr161d_scenario_matrix_ref_if_available",
    "pr161d_replay_paper_scenario_ref_if_available",
)


def build_shared_dictionary(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    builder = _DictionaryBuilder()
    for filename in sorted(COMPACTED_REPORT_FILENAMES):
        payload = payloads.get(filename)
        if not payload:
            continue
        schema_ref = c.REPORT_SCHEMA_REFS.get(filename)
        if schema_ref:
            builder.intern("schema_refs", "S", schema_ref)
        for record in payload.get("records") or []:
            if not isinstance(record, dict):
                continue
            builder.ingest_record(filename, record)
    return builder.as_dictionary()


def compact_records_for_report(
    records: list[dict[str, Any]],
    filename: str,
    schema_ref: str | None,
    shared_dictionary: dict[str, Any],
) -> list[dict[str, Any]]:
    if filename not in COMPACTED_REPORT_FILENAMES:
        return records
    indexes = _dictionary_indexes(shared_dictionary)
    schema_ref_id = _ref_for(indexes, "schema_refs", schema_ref)
    return [
        _compact_record(record, filename, schema_ref_id, shared_dictionary, indexes)
        for record in records
    ]


def hoist_compact_record_defaults(
    records: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not records:
        return {}, []
    defaults: dict[str, Any] = {}
    for field in DEFAULTABLE_COMPACT_FIELDS:
        first = records[0].get(field)
        if first is None:
            continue
        if all(record.get(field) == first for record in records):
            defaults[field] = first
    if not defaults:
        return {}, records
    compacted = [
        {field: value for field, value in record.items() if field not in defaults}
        for record in records
    ]
    return defaults, compacted


def expand_payload_records(
    payload: dict[str, Any],
    shared_dictionary: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    records = payload.get("records") or []
    if not payload.get("compact_records_flag"):
        return [record for record in records if isinstance(record, dict)]
    if shared_dictionary is None:
        raise ValueError("compact PR161E shard requires shared dictionary")
    filename = str(payload.get("parent_report_filename") or payload.get("report_filename") or "")
    defaults = dict(payload.get("compact_record_defaults") or {})
    defaults["compact_record_version"] = payload.get("compact_record_version")
    return [
        expand_compact_record({**defaults, **record}, filename, shared_dictionary)
        for record in records
        if isinstance(record, dict)
    ]


def expand_compact_record(
    record: dict[str, Any],
    filename: str,
    shared_dictionary: dict[str, Any],
) -> dict[str, Any]:
    if record.get("compact_record_version") != COMPACT_RECORD_VERSION:
        return dict(record)

    expanded: dict[str, Any] = {"record_id": record["record_id"]}
    qku_id = record.get("qku_id")
    if qku_id is not None:
        expanded["qku_id"] = qku_id
        expanded["qku_ids"] = list(record.get("qku_ids") or [qku_id])
        expanded.update(_qku_trace_for_qku(shared_dictionary, str(qku_id)))
    elif record.get("qku_ids") is not None:
        expanded["qku_ids"] = list(record["qku_ids"])

    _resolve_state_refs(expanded, record, shared_dictionary)
    _merge_ref_group(expanded, record, shared_dictionary, "policy_ref", "policy_flag_groups")
    _merge_ref_group(expanded, record, shared_dictionary, "authority_boundary_ref", "authority_boundary_groups")
    _merge_ref_group(expanded, record, shared_dictionary, "owner_authority_ref", "owner_authority_groups")
    _merge_ref_group(expanded, record, shared_dictionary, "route_ref", "route_groups")
    _merge_ref_group(expanded, record, shared_dictionary, "agent_route_ref", "agent_route_groups")
    _merge_ref_group(
        expanded,
        record,
        shared_dictionary,
        "compatibility_policy_ref",
        "compatibility_policy_groups",
    )
    _merge_ref_group(expanded, record, shared_dictionary, "qch_policy_ref", "qch_policy_groups")
    _merge_ref_group(expanded, record, shared_dictionary, "numeric_state_ref", "numeric_state_groups")
    _merge_ref_group(expanded, record, shared_dictionary, "result_detail_ref", "result_detail_groups")
    _merge_ref_group(
        expanded,
        record,
        shared_dictionary,
        "confidence_state_ref",
        "confidence_state_groups",
    )
    _merge_ref_group(expanded, record, shared_dictionary, "field_group_ref", "field_groups")

    _restore_direct_identity_fields(expanded, record, filename)
    _restore_record_trace_fields(expanded, record, filename)
    return expanded


def _restore_direct_identity_fields(
    expanded: dict[str, Any],
    record: dict[str, Any],
    filename: str,
) -> None:
    record_id = str(record["record_id"])
    qku_id = record.get("qku_id")
    bundle_id = record.get("qku_bundle_id_if_available") or expanded.get(
        "pr161d_bundle_ref_if_available"
    )
    scenario_id = record.get("scenario_matrix_id_if_available") or expanded.get(
        "pr161d_scenario_matrix_ref_if_available"
    )
    replay_scenario_id = record.get("replay_paper_scenario_id_if_available") or expanded.get(
        "pr161d_replay_paper_scenario_ref_if_available"
    )

    if filename == "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json":
        expanded["outcome_capture_record_id"] = record_id
        expanded["replay_paper_scenario_id"] = replay_scenario_id
        expanded["qku_bundle_id"] = bundle_id
        expanded["scenario_matrix_id"] = scenario_id
    elif filename == "PR161E_QKUBundleResultLedger.report.json":
        expanded["qku_bundle_id"] = bundle_id
    elif filename == "PR161E_QKUReplayPaperProfitabilityLedger.report.json":
        expanded["profitability_ledger_id"] = record_id
        expanded["result_backed_ranking_slot_id"] = _result_slot_id(qku_id)
    elif filename == "PR161E_QKUScenarioResultAttribution.report.json":
        expanded["scenario_result_attribution_id"] = record_id
        expanded["scenario_matrix_id"] = scenario_id
        expanded["qku_bundle_id"] = bundle_id
    elif filename == "PR161E_QKUResultBackedRankingUpdateCandidates.report.json":
        expanded["ranking_update_candidate_id"] = record_id
        expanded["result_backed_ranking_slot_id"] = _result_slot_id(qku_id)
    elif filename == "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json":
        expanded["future_profitability_pattern_record_id"] = record.get(
            "future_profitability_pattern_record_id"
        )
    elif filename == "PR161E_QuantumClassicalHybridOutcomeComparison.report.json":
        expanded["qku_bundle_id_if_available"] = bundle_id
    elif filename == "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json":
        expanded["compatibility_source_class"] = _compatibility_source_class(record)
        expanded["atomicrow_id_if_available"] = record.get("atomicrow_id_if_available")
        expanded["pr154_target_id_if_available"] = record.get("pr154_target_id_if_available")
        expanded["qku_bundle_id_if_available"] = bundle_id
        expanded["scenario_matrix_id_if_available"] = scenario_id
    elif filename == "PR161E_ResultConfidenceGate.report.json":
        expanded["replay_paper_scenario_id"] = replay_scenario_id
    elif filename == "PR161E_OwnerReviewResultPromotionQueue.report.json":
        expanded["owner_review_source_record_id"] = record_id.replace(
            "PR161E-OWNER-RESULT-PROMOTION",
            "PR161D-OWNER-REVIEW",
        )
    elif filename == "PR161E_AgentOutcomeTaskQueue.report.json":
        role = record.get("agent_role_if_applicable")
        expanded["assigned_agent_role"] = role
        expanded["source_task_id"] = _source_task_id(qku_id, role)


def _restore_record_trace_fields(
    expanded: dict[str, Any],
    record: dict[str, Any],
    filename: str,
) -> None:
    bundle_id = record.get("qku_bundle_id_if_available") or expanded.get(
        "pr161d_bundle_ref_if_available"
    )
    scenario_id = record.get("scenario_matrix_id_if_available") or expanded.get(
        "pr161d_scenario_matrix_ref_if_available"
    )
    replay_scenario_id = record.get("replay_paper_scenario_id_if_available") or expanded.get(
        "pr161d_replay_paper_scenario_ref_if_available"
    )
    role = record.get("agent_role_if_applicable")
    expanded["pr161d_bundle_ref_if_available"] = bundle_id
    expanded["pr161d_scenario_matrix_ref_if_available"] = scenario_id
    expanded["pr161d_replay_paper_scenario_ref_if_available"] = replay_scenario_id
    expanded["pr161d_agent_task_ref_if_available"] = (
        _source_task_id(record.get("qku_id"), role)
        if filename == "PR161E_AgentOutcomeTaskQueue.report.json"
        else None
    )
    expanded["pr161d_owner_review_ref_if_available"] = (
        expanded.get("owner_review_source_record_id")
        if filename == "PR161E_OwnerReviewResultPromotionQueue.report.json"
        else None
    )


def _compact_record(
    record: dict[str, Any],
    filename: str,
    schema_ref_id: str | None,
    shared_dictionary: dict[str, Any],
    indexes: dict[str, dict[str, str]],
) -> dict[str, Any]:
    compact: dict[str, Any] = {
        "record_id": record["record_id"],
    }
    if schema_ref_id is not None:
        compact["schema_ref"] = schema_ref_id
    _copy_identity_fields(compact, record, shared_dictionary)
    _copy_state_refs(compact, record, indexes)
    _copy_group_ref(compact, record, indexes, "policy_ref", "policy_flag_groups", POLICY_FIELDS)
    _copy_group_ref(
        compact,
        record,
        indexes,
        "authority_boundary_ref",
        "authority_boundary_groups",
        AUTHORITY_BOUNDARY_FIELDS,
    )
    _copy_group_ref(compact, record, indexes, "owner_authority_ref", "owner_authority_groups", ())
    _copy_group_ref(compact, record, indexes, "route_ref", "route_groups", ROUTE_FIELDS)
    _copy_group_ref(
        compact,
        record,
        indexes,
        "agent_route_ref",
        "agent_route_groups",
        AGENT_ROUTE_FIELDS,
    )
    _copy_group_ref(
        compact,
        record,
        indexes,
        "compatibility_policy_ref",
        "compatibility_policy_groups",
        COMPATIBILITY_POLICY_FIELDS,
    )
    _copy_group_ref(compact, record, indexes, "qch_policy_ref", "qch_policy_groups", QCH_POLICY_FIELDS)
    _copy_group_ref(
        compact,
        record,
        indexes,
        "numeric_state_ref",
        "numeric_state_groups",
        NUMERIC_FIELDS,
    )
    _copy_group_ref(
        compact,
        record,
        indexes,
        "result_detail_ref",
        "result_detail_groups",
        RESULT_DETAIL_FIELDS,
    )
    _copy_group_ref(
        compact,
        record,
        indexes,
        "confidence_state_ref",
        "confidence_state_groups",
        CONFIDENCE_STATE_FIELDS,
    )
    field_group = _field_group(record, _remaining_field_names(record))
    if field_group:
        compact["field_group_ref"] = _ref_for(indexes, "field_groups", field_group)
    _validate_compact_record_resolves(compact, shared_dictionary)
    return compact


def _copy_identity_fields(
    compact: dict[str, Any],
    record: dict[str, Any],
    shared_dictionary: dict[str, Any],
) -> None:
    qku_id = record.get("qku_id")
    qku_ids = record.get("qku_ids")
    if qku_id is not None:
        compact["qku_id"] = qku_id
    if isinstance(qku_ids, list) and (not qku_id or qku_ids != [qku_id]):
        compact["qku_ids"] = qku_ids
    bundle_id = (
        record.get("qku_bundle_id_if_available")
        or record.get("qku_bundle_id")
        or record.get("pr161d_bundle_ref_if_available")
    )
    scenario_id = (
        record.get("scenario_matrix_id_if_available")
        or record.get("scenario_matrix_id")
        or record.get("pr161d_scenario_matrix_ref_if_available")
    )
    replay_scenario_id = (
        record.get("replay_paper_scenario_id")
        or record.get("replay_paper_scenario_id_if_available")
        or record.get("pr161d_replay_paper_scenario_ref_if_available")
    )
    trace_defaults = (
        _qku_trace_for_qku(shared_dictionary, str(qku_id))
        if qku_id is not None
        else {}
    )
    single_qku_record = _single_qku_record(record)
    if (
        bundle_id is not None
        and (not single_qku_record or trace_defaults.get("pr161d_bundle_ref_if_available") != bundle_id)
    ):
        compact["qku_bundle_id_if_available"] = bundle_id
    if (
        scenario_id is not None
        and (
            not single_qku_record
            or trace_defaults.get("pr161d_scenario_matrix_ref_if_available") != scenario_id
        )
    ):
        compact["scenario_matrix_id_if_available"] = scenario_id
    if (
        replay_scenario_id is not None
        and (
            not single_qku_record
            or trace_defaults.get("pr161d_replay_paper_scenario_ref_if_available")
            != replay_scenario_id
        )
    ):
        compact["replay_paper_scenario_id_if_available"] = replay_scenario_id
    role = record.get("assigned_agent_role")
    if role is not None:
        compact["agent_role_if_applicable"] = role
    atomicrow_id = record.get("atomicrow_id_if_available")
    pr154_target_id = record.get("pr154_target_id_if_available")
    if atomicrow_id is not None:
        compact["atomicrow_id_if_available"] = atomicrow_id
    if pr154_target_id is not None:
        compact["pr154_target_id_if_available"] = pr154_target_id
    if "future_profitability_pattern_record_id" in record:
        compact["future_profitability_pattern_record_id"] = record[
            "future_profitability_pattern_record_id"
        ]


def _copy_state_refs(
    compact: dict[str, Any],
    record: dict[str, Any],
    indexes: dict[str, dict[str, str]],
) -> None:
    state_fields = (
        ("result_state", "result_state_ref", "result_states"),
        ("validation_state", "validation_state_ref", "validation_states"),
        ("evidence_state", "evidence_state_ref", "evidence_states"),
        ("profitability_label", "profitability_label_ref", "profitability_labels"),
    )
    for source_field, compact_field, table_name in state_fields:
        if source_field in record:
            compact[compact_field] = _ref_for(indexes, table_name, record[source_field])


def _copy_group_ref(
    compact: dict[str, Any],
    record: dict[str, Any],
    indexes: dict[str, dict[str, str]],
    compact_field: str,
    table_name: str,
    fields: tuple[str, ...],
) -> None:
    group = _field_group(record, fields)
    if group:
        compact[compact_field] = _ref_for(indexes, table_name, group)


def _resolve_state_refs(
    expanded: dict[str, Any],
    record: dict[str, Any],
    shared_dictionary: dict[str, Any],
) -> None:
    state_fields = (
        ("result_state_ref", "result_states", "result_state"),
        ("validation_state_ref", "validation_states", "validation_state"),
        ("evidence_state_ref", "evidence_states", "evidence_state"),
        ("profitability_label_ref", "profitability_labels", "profitability_label"),
    )
    for compact_field, table_name, expanded_field in state_fields:
        ref = record.get(compact_field)
        if ref is not None:
            expanded[expanded_field] = _dict_value(shared_dictionary, table_name, ref)


def _merge_ref_group(
    expanded: dict[str, Any],
    record: dict[str, Any],
    shared_dictionary: dict[str, Any],
    compact_field: str,
    table_name: str,
) -> None:
    ref = record.get(compact_field)
    if ref is None:
        return
    value = _dict_value(shared_dictionary, table_name, ref)
    if not isinstance(value, dict):
        raise ValueError(f"PR161E compact dictionary ref is not an object: {table_name}:{ref}")
    expanded.update(value)


def _validate_compact_record_resolves(
    compact: dict[str, Any],
    shared_dictionary: dict[str, Any],
) -> None:
    if compact.get("schema_ref") is not None:
        _dict_value(shared_dictionary, "schema_refs", compact["schema_ref"])
    for compact_field, table_name in (
        ("result_state_ref", "result_states"),
        ("validation_state_ref", "validation_states"),
        ("evidence_state_ref", "evidence_states"),
        ("profitability_label_ref", "profitability_labels"),
        ("policy_ref", "policy_flag_groups"),
        ("authority_boundary_ref", "authority_boundary_groups"),
        ("owner_authority_ref", "owner_authority_groups"),
        ("route_ref", "route_groups"),
        ("agent_route_ref", "agent_route_groups"),
        ("compatibility_policy_ref", "compatibility_policy_groups"),
        ("qch_policy_ref", "qch_policy_groups"),
        ("numeric_state_ref", "numeric_state_groups"),
        ("result_detail_ref", "result_detail_groups"),
        ("confidence_state_ref", "confidence_state_groups"),
        ("field_group_ref", "field_groups"),
    ):
        ref = compact.get(compact_field)
        if ref is not None:
            _dict_value(shared_dictionary, table_name, ref)
    qku_id = compact.get("qku_id")
    if qku_id is not None and qku_id not in shared_dictionary.get("qku_trace_index", {}):
        raise ValueError(f"PR161E compact record qku_id missing from trace index: {qku_id}")


def _remaining_field_names(record: dict[str, Any]) -> tuple[str, ...]:
    return tuple(field for field in sorted(record) if field not in GROUPED_FIELDS)


def _field_group(record: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: record[field] for field in fields if field in record}


def _source_task_id(qku_id: Any, role: Any) -> str | None:
    if qku_id is None or role is None:
        return None
    return f"PR161D-TASK-{qku_id}-{role}"


def _result_slot_id(qku_id: Any) -> str | None:
    if qku_id is None:
        return None
    return f"PR161D-RESULT-SLOT-{qku_id}"


def _single_qku_record(record: dict[str, Any]) -> bool:
    qku_id = record.get("qku_id")
    qku_ids = record.get("qku_ids")
    return qku_id is not None and (not isinstance(qku_ids, list) or qku_ids == [qku_id])


def _compatibility_source_class(record: dict[str, Any]) -> str | None:
    if record.get("atomicrow_id_if_available") is not None:
        return "ATOMICROWS"
    if record.get("pr154_target_id_if_available") is not None:
        return "PR154"
    return None


def _qku_trace_for_qku(shared_dictionary: dict[str, Any], qku_id: str) -> dict[str, Any]:
    trace_index = shared_dictionary.get("qku_trace_index", {})
    if qku_id not in trace_index:
        raise ValueError(f"missing PR161E compact qku trace index: {qku_id}")
    trace_row = trace_index[qku_id]
    if isinstance(trace_row, dict):
        return trace_row
    if not isinstance(trace_row, list):
        raise ValueError(f"invalid PR161E qku trace row: {qku_id}")
    fields = shared_dictionary.get("qku_trace_index_fields")
    if not isinstance(fields, list) or len(fields) != len(trace_row):
        raise ValueError("PR161E qku trace index fields mismatch")
    compact = dict(zip(fields, trace_row))
    upstream_ref = compact.get("upstream_origin_ref")
    upstream_origin = _dict_value(
        shared_dictionary,
        "qku_upstream_origin_refs",
        upstream_ref,
    )
    return {
        "atomicrows_ref_if_available": qku_id if qku_id.startswith("QKU-ATOMICROW-") else None,
        "pr154_ref_if_available": qku_id if qku_id.startswith("QKU-PR154-") else None,
        "pr161d_category_ranking_ref_if_available": None,
        "pr161d_score_ref_if_available": f"PR161D-QSCORE-{qku_id}",
        "pre_result_quality_score": compact.get("pre_result_quality_score"),
        "qku_graph_node_id": f"QKUNODE-{qku_id}",
        "result_backed_ranking_slot_id": f"PR161D-RESULT-SLOT-{qku_id}",
        "unmappable_reason_if_any": None,
        "upstream_pr161a_or_pr161b_origin_if_available": upstream_origin,
        "pr161d_bundle_ref_if_available": compact.get("pr161d_bundle_ref_if_available"),
        "pr161d_scenario_matrix_ref_if_available": compact.get(
            "pr161d_scenario_matrix_ref_if_available"
        ),
        "pr161d_replay_paper_scenario_ref_if_available": compact.get(
            "pr161d_replay_paper_scenario_ref_if_available"
        ),
    }


def _dict_value(shared_dictionary: dict[str, Any], table_name: str, ref: str) -> Any:
    table = shared_dictionary.get(table_name)
    if not isinstance(table, dict) or ref not in table:
        raise ValueError(f"unresolved PR161E compact dictionary ref: {table_name}:{ref}")
    return table[ref]


def _dictionary_indexes(shared_dictionary: dict[str, Any]) -> dict[str, dict[str, str]]:
    indexes: dict[str, dict[str, str]] = {}
    for table_name, table in shared_dictionary.items():
        if not isinstance(table, dict) or table_name == "qku_trace_index":
            continue
        indexes[table_name] = {_canonical(value): ref for ref, value in table.items()}
    return indexes


def _ref_for(indexes: dict[str, dict[str, str]], table_name: str, value: Any) -> str:
    ref = indexes.get(table_name, {}).get(_canonical(value))
    if ref is None:
        raise ValueError(f"missing PR161E compact dictionary entry: {table_name}:{value!r}")
    return ref


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


class _DictionaryBuilder:
    def __init__(self) -> None:
        self.tables: dict[str, dict[str, Any]] = {
            "schema_refs": {},
            "result_states": {},
            "validation_states": {},
            "evidence_states": {},
            "profitability_labels": {},
            "policy_flag_groups": {},
            "authority_boundary_groups": {},
            "owner_authority_groups": {},
            "route_groups": {},
            "agent_route_groups": {},
            "compatibility_policy_groups": {},
            "qch_policy_groups": {},
            "numeric_state_groups": {},
            "result_detail_groups": {},
            "confidence_state_groups": {},
            "field_groups": {},
            "qku_upstream_origin_refs": {},
        }
        self.reverse: dict[str, dict[str, str]] = {name: {} for name in self.tables}
        self.qku_trace_index: dict[str, dict[str, Any]] = {}

    def ingest_record(self, filename: str, record: dict[str, Any]) -> None:
        del filename
        self._ingest_states(record)
        self.intern_group("policy_flag_groups", "P", _field_group(record, POLICY_FIELDS))
        self.intern_group(
            "authority_boundary_groups",
            "A",
            _field_group(record, AUTHORITY_BOUNDARY_FIELDS),
        )
        self.intern_group("owner_authority_groups", "O", {})
        self.intern_group("route_groups", "R", _field_group(record, ROUTE_FIELDS))
        self.intern_group("agent_route_groups", "AR", _field_group(record, AGENT_ROUTE_FIELDS))
        self.intern_group(
            "compatibility_policy_groups",
            "CP",
            _field_group(record, COMPATIBILITY_POLICY_FIELDS),
        )
        self.intern_group("qch_policy_groups", "QCH", _field_group(record, QCH_POLICY_FIELDS))
        self.intern_group("numeric_state_groups", "N", _field_group(record, NUMERIC_FIELDS))
        self.intern_group(
            "result_detail_groups",
            "RD",
            _field_group(record, RESULT_DETAIL_FIELDS),
        )
        self.intern_group(
            "confidence_state_groups",
            "CF",
            _field_group(record, CONFIDENCE_STATE_FIELDS),
        )
        self.intern_group("field_groups", "F", _field_group(record, _remaining_field_names(record)))
        self._ingest_qku_trace(record)

    def _ingest_states(self, record: dict[str, Any]) -> None:
        for field, table_name, prefix in (
            ("result_state", "result_states", "RS"),
            ("validation_state", "validation_states", "VS"),
            ("evidence_state", "evidence_states", "ES"),
            ("profitability_label", "profitability_labels", "PL"),
        ):
            if field in record:
                self.intern(table_name, prefix, record[field])

    def _ingest_qku_trace(self, record: dict[str, Any]) -> None:
        qku_id = record.get("qku_id")
        if qku_id is None:
            return
        trace = self.qku_trace_index.setdefault(str(qku_id), {})
        for field in QKU_TRACE_FIELDS:
            if field not in record:
                continue
            if field in RECORD_TRACE_FIELDS and not _single_qku_record(record):
                continue
            value = record[field]
            if field not in trace or trace[field] is None:
                trace[field] = value
            elif trace[field] != value and value is not None:
                raise ValueError(
                    f"conflicting PR161E qku trace value for {qku_id}:{field}"
                )

    def intern_group(self, table_name: str, prefix: str, group: dict[str, Any]) -> str | None:
        if not group:
            return None
        return self.intern(table_name, prefix, group)

    def intern(self, table_name: str, prefix: str, value: Any) -> str:
        canonical = _canonical(value)
        existing = self.reverse[table_name].get(canonical)
        if existing is not None:
            return existing
        ref = f"{prefix}{len(self.tables[table_name]) + 1}"
        self.tables[table_name][ref] = value
        self.reverse[table_name][canonical] = ref
        return ref

    def as_dictionary(self) -> dict[str, Any]:
        compact_qku_trace_index = self._compact_qku_trace_index()
        return {
            "dictionary_version": SHARED_DICTIONARY_VERSION,
            "compact_record_version": COMPACT_RECORD_VERSION,
            "compacted_report_filenames": sorted(COMPACTED_REPORT_FILENAMES),
            "schema_refs": self.tables["schema_refs"],
            "result_states": self.tables["result_states"],
            "validation_states": self.tables["validation_states"],
            "evidence_states": self.tables["evidence_states"],
            "profitability_labels": self.tables["profitability_labels"],
            "policy_flag_groups": self.tables["policy_flag_groups"],
            "authority_boundary_groups": self.tables["authority_boundary_groups"],
            "owner_authority_groups": self.tables["owner_authority_groups"],
            "route_groups": self.tables["route_groups"],
            "agent_route_groups": self.tables["agent_route_groups"],
            "compatibility_policy_groups": self.tables["compatibility_policy_groups"],
            "qch_policy_groups": self.tables["qch_policy_groups"],
            "numeric_state_groups": self.tables["numeric_state_groups"],
            "result_detail_groups": self.tables["result_detail_groups"],
            "confidence_state_groups": self.tables["confidence_state_groups"],
            "field_groups": self.tables["field_groups"],
            "qku_upstream_origin_refs": self.tables["qku_upstream_origin_refs"],
            "qku_trace_index_fields": list(QKU_TRACE_INDEX_FIELDS),
            "qku_trace_index": compact_qku_trace_index,
            "qku_trace_index_count": len(compact_qku_trace_index),
            "no_binary_compression_flag": True,
            "external_storage_used_flag": False,
            "qtt_sha_or_checksum_authority_created_flag": False,
            "atomicrows_bundle_sha_hash_freeze_authority_created_flag": False,
        }

    def _compact_qku_trace_index(self) -> dict[str, list[Any]]:
        compact: dict[str, list[Any]] = {}
        for qku_id, trace in sorted(self.qku_trace_index.items()):
            upstream_ref = self.intern(
                "qku_upstream_origin_refs",
                "U",
                trace.get("upstream_pr161a_or_pr161b_origin_if_available"),
            )
            compact[qku_id] = [
                upstream_ref,
                trace.get("pre_result_quality_score"),
                trace.get("pr161d_bundle_ref_if_available"),
                trace.get("pr161d_scenario_matrix_ref_if_available"),
                trace.get("pr161d_replay_paper_scenario_ref_if_available"),
            ]
        return compact
