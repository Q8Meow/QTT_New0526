"""Fail-closed validator for PR159 generated artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping, json_dump, read_json
from .models import ValidationResult
from .report import build_artifacts


def _require(condition: bool, failures: list[str], code: str) -> None:
    if not condition:
        failures.append(code)


def _load_json(root: Path, path: Path, failures: list[str]) -> Mapping[str, Any]:
    full_path = root / path
    if not full_path.exists():
        failures.append(f"PR159_GENERATED_ARTIFACT_MISSING:{path.as_posix()}")
        return {}
    payload = read_json(full_path)
    if not isinstance(payload, dict):
        failures.append(f"PR159_GENERATED_ARTIFACT_NOT_OBJECT:{path.as_posix()}")
        return {}
    return payload


def _placeholder_failures(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, str):
        if value in c.FORBIDDEN_PLACEHOLDER_VALUES or "PLACEHOLDER" in value:
            failures.append(f"PR159_PLACEHOLDER_VALUE:{path}:{value}")
    elif isinstance(value, dict):
        for key, child in value.items():
            failures.extend(_placeholder_failures(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_placeholder_failures(child, f"{path}[{index}]"))
    return failures


def _validate_receipts(report: Mapping[str, Any], failures: list[str]) -> None:
    receipts = [as_mapping(item) for item in as_list(report.get("input_consumption_receipt"))]
    by_path = {str(item.get("path")): item for item in receipts}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = by_path.get(path.as_posix(), {})
            fallback = by_path.get(c.CROSSWALK_FALLBACK_PATH.as_posix(), {})
            _require(
                bool(requested) and (requested.get("consumed") or fallback.get("consumed")),
                failures,
                "PR159_MANDATORY_CROSSWALK_OR_FALLBACK_NOT_CONSUMED",
            )
            continue
        item = by_path.get(path.as_posix(), {})
        _require(
            bool(item and item.get("exists") and item.get("consumed")),
            failures,
            f"PR159_MANDATORY_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    for path in c.MANDATORY_PR159_INPUTS:
        item = by_path.get(path.as_posix(), {})
        _require(
            bool(item and item.get("exists") and item.get("consumed")),
            failures,
            f"PR159_MANDATORY_PR159_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    shard_receipts = [
        item
        for item in receipts
        if item.get("artifact_role") == "mandatory_pr157_atomicrows_completion_shard"
        and item.get("exists")
        and item.get("consumed")
    ]
    _require(len(shard_receipts) == 9, failures, "PR159_PR157_SHARDS_NOT_CONSUMED")


def _validate_counts(master_report: Mapping[str, Any], failures: list[str]) -> None:
    receipt = as_mapping(master_report.get("count_invariant_receipt"))
    _require(receipt.get("pr154_public_source_retry_records") == 34, failures, "PR159_PR154_RETRY_COUNT_NOT_34")
    _require(receipt.get("atomicrows_public_external_source_required") == 315, failures, "PR159_PUBLIC_EXTERNAL_COUNT_NOT_315")
    _require(receipt.get("atomicrows_parameter_range_source_required") == 530, failures, "PR159_PARAMETER_RANGE_COUNT_NOT_530")
    _require(receipt.get("atomicrows_source_required_total") == 845, failures, "PR159_ATOMICROWS_TOTAL_NOT_845")
    _require(receipt.get("total_source_target_records") == 879, failures, "PR159_TOTAL_TARGET_COUNT_NOT_879")
    _require(receipt.get("pr154_retry_processed_count") == 34, failures, "PR159_PR154_PROCESSED_NOT_34")
    _require(receipt.get("atomicrows_source_required_processed_count") == 845, failures, "PR159_ATOMICROWS_PROCESSED_NOT_845")
    _require(receipt.get("count_invariants_passed_flag") is True, failures, "PR159_COUNT_INVARIANTS_FAILED")
    state_counts = as_mapping(receipt.get("target_state_counts"))
    _require(sum(v for v in state_counts.values() if isinstance(v, int)) == 879, failures, "PR159_TARGET_STATE_SUM_NOT_879")
    for state in state_counts:
        _require(state in c.FINAL_TARGET_STATES, failures, f"PR159_BAD_FINAL_STATE:{state}")


def _validate_target_queue(target_registry: Mapping[str, Any], failures: list[str]) -> None:
    records = [as_mapping(item) for item in as_list(target_registry.get("records"))]
    _require(len(records) == 879, failures, "PR159_TARGET_QUEUE_COUNT_NOT_879")
    ids = [str(item.get("target_id")) for item in records]
    _require(len(ids) == len(set(ids)), failures, "PR159_DUPLICATE_TARGET_ID")
    for record in records:
        target_id = str(record.get("target_id"))
        _require(record.get("final_source_target_state") in c.FINAL_TARGET_STATES, failures, f"PR159_BAD_TARGET_STATE:{target_id}")
        _require(record.get("day1_source_priority_tier") in c.CENTRAL_ENUM_VALUE_SETS["day1_source_priority_tier"], failures, f"PR159_BAD_PRIORITY:{target_id}")
        _require(record.get("source_materiality_class") in c.CENTRAL_ENUM_VALUE_SETS["source_materiality_class"], failures, f"PR159_BAD_MATERIALITY:{target_id}")
        _require(record.get("revalidation_class") in c.CENTRAL_ENUM_VALUE_SETS["revalidation_class"], failures, f"PR159_BAD_REVALIDATION:{target_id}")
        _require(bool(record.get("official_source_target_ids")), failures, f"PR159_TARGET_WITHOUT_RETRIEVAL_ENTRY:{target_id}")


def _validate_candidate_packets(
    candidate_registry: Mapping[str, Any],
    accepted_registry: Mapping[str, Any],
    failures: list[str],
) -> None:
    records = [as_mapping(item) for item in as_list(candidate_registry.get("records"))]
    accepted_candidate_ids = {
        str(record.get("candidate_packet_id"))
        for record in [as_mapping(item) for item in as_list(accepted_registry.get("records"))]
    }
    for record in records:
        packet_id = str(record.get("candidate_packet_id"))
        _require(record.get("candidate_is_accepted_fact") is False, failures, f"PR159_CANDIDATE_ACCEPTED_FACT:{packet_id}")
        _require(record.get("official_source_class") in c.CENTRAL_ENUM_VALUE_SETS["official_source_class"], failures, f"PR159_CANDIDATE_BAD_SOURCE_CLASS:{packet_id}")
        _require(record.get("official_source_confidence") in c.CENTRAL_ENUM_VALUE_SETS["official_source_confidence"], failures, f"PR159_CANDIDATE_BAD_CONFIDENCE:{packet_id}")
        locator = as_mapping(record.get("quote_span_or_machine_field_locator"))
        _require(bool(locator.get("quote_span") or locator.get("machine_field_locator")), failures, f"PR159_CANDIDATE_LOCATOR_MISSING:{packet_id}")
        has_extracted_value = record.get("extracted_value_or_range_or_enum_or_null") is not None
        if has_extracted_value:
            _require(packet_id in accepted_candidate_ids, failures, f"PR159_CANDIDATE_VALUE_WITHOUT_ACCEPTANCE:{packet_id}")
            _require(record.get("target_field_scope_match_flag") is True, failures, f"PR159_CANDIDATE_VALUE_SCOPE_MISMATCH:{packet_id}")
            _require(record.get("official_source_confidence") == c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value, failures, f"PR159_CANDIDATE_VALUE_NOT_CONFIRMED:{packet_id}")
            _require(bool(locator.get("locator")), failures, f"PR159_CANDIDATE_VALUE_LOCATOR_MISSING:{packet_id}")
            _require(bool(record.get("extracted_unit_or_basis_or_null")), failures, f"PR159_CANDIDATE_VALUE_UNIT_MISSING:{packet_id}")
            _require(bool(record.get("extracted_scale_or_null")), failures, f"PR159_CANDIDATE_VALUE_SCALE_MISSING:{packet_id}")
            _require(record.get("conflict_clearance_status") == c.ConflictStatus.NO_CONFLICT.value, failures, f"PR159_CANDIDATE_VALUE_CONFLICT_NOT_CLEAR:{packet_id}")
        else:
            _require(packet_id not in accepted_candidate_ids, failures, f"PR159_CANDIDATE_ACCEPTED_WITHOUT_VALUE:{packet_id}")


def _validate_accepted_packets(accepted_registry: Mapping[str, Any], failures: list[str]) -> None:
    records = [as_mapping(item) for item in as_list(accepted_registry.get("records"))]
    for record in records:
        packet_id = str(record.get("accepted_packet_id"))
        _require(record.get("official_source_confidence") == c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value, failures, f"PR159_ACCEPTED_NOT_CONFIRMED:{packet_id}")
        _require(record.get("target_field_scope_match_flag") is True, failures, f"PR159_ACCEPTED_SCOPE_MISMATCH:{packet_id}")
        _require(record.get("locator_valid_flag") is True, failures, f"PR159_ACCEPTED_LOCATOR_INVALID:{packet_id}")
        _require(record.get("conflict_cleared_flag") is True, failures, f"PR159_ACCEPTED_CONFLICT_NOT_CLEAR:{packet_id}")
        _require(record.get("freshness_valid_flag") is True, failures, f"PR159_ACCEPTED_FRESHNESS_INVALID:{packet_id}")
        _require(record.get("unit_scale_canonicalized_flag") is True, failures, f"PR159_ACCEPTED_UNIT_SCALE_INVALID:{packet_id}")
        _require(bool(record.get("target_id_or_row_id")), failures, f"PR159_ACCEPTED_TARGET_MISSING:{packet_id}")
        _require(bool(record.get("source_population")), failures, f"PR159_ACCEPTED_POPULATION_MISSING:{packet_id}")
        _require(bool(record.get("accepted_value_or_range_or_enum")), failures, f"PR159_ACCEPTED_VALUE_MISSING:{packet_id}")
        _require(bool(record.get("canonical_unit_or_basis")), failures, f"PR159_ACCEPTED_UNIT_MISSING:{packet_id}")
        _require(bool(record.get("canonical_scale")), failures, f"PR159_ACCEPTED_SCALE_MISSING:{packet_id}")
        locator = as_mapping(record.get("quote_span_or_machine_field_locator"))
        _require(bool(locator.get("locator") and (locator.get("quote_span") or locator.get("machine_field_locator"))), failures, f"PR159_ACCEPTED_LOCATOR_MISSING:{packet_id}")
        _require(record.get("no_connector_semantic_binding_confirmation") is True, failures, f"PR159_ACCEPTED_CONNECTOR_BINDING:{packet_id}")
        _require(record.get("no_runtime_receipt_confirmation") is True, failures, f"PR159_ACCEPTED_RUNTIME_RECEIPT:{packet_id}")
        _require(record.get("no_live_order_authority_confirmation") is True, failures, f"PR159_ACCEPTED_ORDER_AUTHORITY:{packet_id}")
        _require(record.get("no_profit_evidence_confirmation") is True, failures, f"PR159_ACCEPTED_PROFIT_EVIDENCE:{packet_id}")


def _validate_completion_records(
    pr154_registry: Mapping[str, Any],
    atomic_registry: Mapping[str, Any],
    unresolved_report: Mapping[str, Any],
    failures: list[str],
) -> None:
    pr154_records = [as_mapping(item) for item in as_list(pr154_registry.get("records"))]
    atomic_records = [as_mapping(item) for item in as_list(atomic_registry.get("records"))]
    unresolved = [as_mapping(item) for item in as_list(unresolved_report.get("records"))]
    _require(len(pr154_records) == 34, failures, "PR159_PR154_COMPLETION_COUNT_NOT_34")
    _require(len(atomic_records) == 845, failures, "PR159_ATOMIC_COMPLETION_COUNT_NOT_845")
    accepted_pr154 = 0
    accepted_atomic = 0
    for record in pr154_records:
        target_id = str(record.get("target_id"))
        if record.get("completion_status") == c.SourceTargetState.ACCEPTED_COMPLETED.value:
            accepted_pr154 += 1
            _require(bool(record.get("accepted_source_packet_ref_or_null")), failures, f"PR159_PR154_COMPLETED_WITHOUT_ACCEPTED_PACKET:{target_id}")
            _require(record.get("accepted_value_or_null") is not None, failures, f"PR159_PR154_COMPLETED_WITHOUT_VALUE:{target_id}")
            _require(record.get("quote_span_or_machine_field_locator_or_null") is not None, failures, f"PR159_PR154_COMPLETED_WITHOUT_LOCATOR:{target_id}")
        else:
            _require(record.get("accepted_source_packet_ref_or_null") is None, failures, f"PR159_PR154_UNRESOLVED_HAS_ACCEPTED_PACKET:{target_id}")
            _require(bool(record.get("exact_next_action_if_unresolved")), failures, f"PR159_PR154_NO_NEXT_ACTION:{target_id}")
    for record in atomic_records:
        row_id = str(record.get("row_id"))
        if record.get("completion_status") == c.SourceTargetState.ACCEPTED_COMPLETED.value:
            accepted_atomic += 1
            _require(bool(record.get("accepted_source_packet_ref_or_null")), failures, f"PR159_ATOMIC_COMPLETED_WITHOUT_ACCEPTED_PACKET:{row_id}")
            _require(record.get("accepted_value_or_null") is not None, failures, f"PR159_ATOMIC_COMPLETED_WITHOUT_VALUE:{row_id}")
        else:
            _require(record.get("accepted_value_or_null") is None, failures, f"PR159_ATOMIC_OWNER_OR_FAKE_VALUE:{row_id}")
            _require(record.get("accepted_source_packet_ref_or_null") is None, failures, f"PR159_ATOMIC_UNEXPECTED_ACCEPTED_PACKET:{row_id}")
            _require(bool(record.get("exact_next_action_if_unresolved")), failures, f"PR159_ATOMIC_NO_NEXT_ACTION:{row_id}")
            _require(record.get("completion_status") == c.SourceTargetState.UNRESOLVED_WITH_FILL_PATH.value, failures, f"PR159_ATOMIC_BAD_STATUS:{row_id}")
    _require(
        len(unresolved) == c.EXPECTED_TOTAL_SOURCE_TARGET_RECORDS - accepted_pr154 - accepted_atomic,
        failures,
        "PR159_UNRESOLVED_FILL_PATH_COUNT_NOT_RECONCILED",
    )
    for record in unresolved:
        target_id = str(record.get("target_id_or_row_id"))
        for field in (
            "exact_official_source_needed",
            "exact_steps_to_fill",
            "exact_acceptance_criteria",
            "validator_that_will_unblock",
            "risk_if_unfilled",
        ):
            _require(bool(record.get(field)), failures, f"PR159_UNRESOLVED_MISSING_{field}:{target_id}")
        for flag in ("can_qtt_use_in_replay_flag", "can_qtt_use_in_paper_flag", "can_qtt_use_in_live_flag"):
            _require(record.get(flag) is False, failures, f"PR159_UNRESOLVED_FORBIDDEN_USE:{target_id}:{flag}")


def _validate_attempt_matrix(
    matrix_report: Mapping[str, Any],
    accepted_registry: Mapping[str, Any],
    failures: list[str],
) -> None:
    records = [as_mapping(item) for item in as_list(matrix_report.get("records"))]
    accepted_records = [as_mapping(item) for item in as_list(accepted_registry.get("records"))]
    accepted_ids = {str(record.get("accepted_packet_id")) for record in accepted_records}
    matrix_accepted_ids = {
        str(record.get("accepted_packet_ref_or_null"))
        for record in records
        if record.get("accepted_packet_ref_or_null")
    }
    _require(len(records) == c.EXPECTED_TOTAL_SOURCE_TARGET_RECORDS, failures, "PR159_ATTEMPT_MATRIX_COUNT_NOT_879")
    ids = [str(record.get("target_id_or_row_id")) for record in records]
    _require(len(ids) == len(set(ids)), failures, "PR159_ATTEMPT_MATRIX_DUPLICATE_TARGET")
    _require(matrix_accepted_ids == accepted_ids, failures, "PR159_ATTEMPT_MATRIX_ACCEPTED_IDS_NOT_RECONCILED")
    for record in records:
        target_id = str(record.get("target_id_or_row_id"))
        for field in (
            "target_field_id",
            "source_requirement_class",
            "day1_priority_tier",
            "attempted_source_refs",
            "exact_next_action",
        ):
            _require(field in record, failures, f"PR159_ATTEMPT_MATRIX_MISSING_{field}:{target_id}")
        accepted_ref = record.get("accepted_packet_ref_or_null")
        if record.get("acceptance_possible_flag") is True:
            _require(bool(accepted_ref and accepted_ref in accepted_ids), failures, f"PR159_ATTEMPT_MATRIX_ACCEPTABLE_WITHOUT_ACCEPTED_PACKET:{target_id}")
            for flag in (
                "exact_target_field_match_flag",
                "exact_value_available_flag",
                "exact_unit_scale_available_flag",
                "exact_locator_available_flag",
                "freshness_available_flag",
                "conflict_clearance_possible_flag",
            ):
                _require(record.get(flag) is True, failures, f"PR159_ATTEMPT_MATRIX_FLAG_FALSE:{target_id}:{flag}")
            _require(record.get("acceptance_blocker_reason") is None, failures, f"PR159_ATTEMPT_MATRIX_ACCEPTED_HAS_BLOCKER:{target_id}")
        else:
            _require(accepted_ref is None, failures, f"PR159_ATTEMPT_MATRIX_BLOCKED_HAS_ACCEPTED_PACKET:{target_id}")
            _require(bool(record.get("acceptance_blocker_reason")), failures, f"PR159_ATTEMPT_MATRIX_BLOCKED_NO_REASON:{target_id}")
            _require(bool(record.get("exact_next_action")), failures, f"PR159_ATTEMPT_MATRIX_BLOCKED_NO_NEXT_ACTION:{target_id}")


def _validate_metadata_only(payloads: list[Mapping[str, Any]], failures: list[str]) -> None:
    for payload in payloads:
        for record in as_list(payload.get("records")):
            item = as_mapping(record)
            text = " ".join(str(value) for value in item.values())
            _require("execution_created': True" not in text, failures, "PR159_METADATA_EXECUTION_CREATED_TRUE")
    for payload in payloads:
        no_authority = as_mapping(payload.get("no_authority_confirmation"))
        if no_authority:
            _require(all(value is False for value in no_authority.values()), failures, "PR159_METADATA_NO_AUTHORITY_FLAG_TRUE")


def _validate_currentness(root: Path, failures: list[str]) -> None:
    expected = build_artifacts(root)
    for path_text, payload in expected.payloads.items():
        full_path = root / path_text
        if full_path.exists() and full_path.read_text(encoding="utf-8") != json_dump(payload):
            failures.append(f"PR159_GENERATED_ARTIFACT_NOT_DETERMINISTIC_CURRENT:{path_text}")
    for path_text, payload in expected.markdown_payloads.items():
        full_path = root / path_text
        if full_path.exists() and full_path.read_text(encoding="utf-8") != payload:
            failures.append(f"PR159_MARKDOWN_ARTIFACT_NOT_DETERMINISTIC_CURRENT:{path_text}")


def validate_existing_artifacts(repo_root: Path | str) -> ValidationResult:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    payloads = {path: _load_json(root, path, failures) for path in c.ALL_JSON_ARTIFACT_PATHS}
    if not (root / c.HUMAN_SUMMARY_PATH).exists():
        failures.append(f"PR159_MARKDOWN_ARTIFACT_MISSING:{c.HUMAN_SUMMARY_PATH.as_posix()}")
    if failures:
        return ValidationResult(tuple(sorted(set(failures))))

    master_report = payloads[c.MASTER_REPORT_PATH]
    target_registry = payloads[c.TARGET_QUEUE_REGISTRY_PATH]
    candidate_registry = payloads[c.CANDIDATE_PACKET_REGISTRY_PATH]
    accepted_registry = payloads[c.ACCEPTED_PACKET_REGISTRY_PATH]
    attempt_matrix = payloads[c.SOURCE_ACCEPTANCE_ATTEMPT_MATRIX_PATH]
    pr154_registry = payloads[c.PR154_COMPLETION_REGISTRY_PATH]
    atomic_registry = payloads[c.ATOMICROWS_COMPLETION_REGISTRY_PATH]
    unresolved_report = payloads[c.UNRESOLVED_FILL_PATH_PATH]

    _validate_receipts(master_report, failures)
    _validate_counts(master_report, failures)
    _validate_target_queue(target_registry, failures)
    _validate_candidate_packets(candidate_registry, accepted_registry, failures)
    _validate_accepted_packets(accepted_registry, failures)
    _validate_completion_records(pr154_registry, atomic_registry, unresolved_report, failures)
    _validate_attempt_matrix(attempt_matrix, accepted_registry, failures)
    _validate_metadata_only(
        [
            payloads[c.SELECTION_SOURCE_UPDATE_PATH],
            payloads[c.LOW_LATENCY_SOURCE_UPDATE_PATH],
            payloads[c.TRADE_CONTEXT_SOURCE_UPDATE_PATH],
            payloads[c.SCORING_RANKING_SOURCE_UPDATE_PATH],
            payloads[c.QUANTUM_METADATA_PATH],
        ],
        failures,
    )
    _require(master_report.get("master_plan_consumed_confirmation") is True, failures, "PR159_MASTER_PLAN_NOT_CONSUMED")
    _require(master_report.get("master_plan_not_edited_confirmation") is True, failures, "PR159_MASTER_PLAN_EDITED")
    _require(master_report.get("source_evidence_packet_consumed_confirmation") is True, failures, "PR159_SOURCE_PACKET_NOT_CONSUMED")
    _require(master_report.get("online_official_source_search_performed_confirmation") is True, failures, "PR159_ONLINE_SEARCH_NOT_RECORDED")
    for field in (
        "invented_external_fact_count",
        "invented_numeric_range_count",
        "invented_locator_count",
        "placeholder_value_count",
        "runtime_live_order_profit_authority_count",
        "scoring_ranking_selection_execution_count",
        "optimizer_execution_count",
        "quantum_backend_execution_count",
        "qtt_checksum_freeze_global_digest_authority_count",
        "atomicrows_bundle_checksum_hash_authority_count",
    ):
        _require(master_report.get(field) == 0, failures, f"PR159_MASTER_NONZERO:{field}")
    no_authority = as_mapping(master_report.get("no_authority_confirmation"))
    _require(all(value is False for value in no_authority.values()), failures, "PR159_NO_AUTHORITY_FLAG_TRUE")
    for payload in payloads.values():
        failures.extend(_placeholder_failures(payload))
    _validate_currentness(root, failures)
    return ValidationResult(tuple(sorted(set(failures))))
