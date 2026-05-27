"""Fail-closed validator for PR157 generated artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .completion_registry import build_artifacts
from .io import as_list, as_mapping, json_dump, read_json
from .models import ValidationResult
from .owner_input_validator import validate_owner_response_payload


GENERATED_PATHS = (
    c.PR154_REPORT_PATH,
    c.PR154_REGISTRY_PATH,
    c.ATOMICROWS_REPORT_PATH,
    c.ATOMICROWS_REGISTRY_PATH,
    c.OWNER_REQUEST_PATH,
)


def _load_required_json(repo_root: Path, path: Path, failures: list[str]) -> Mapping[str, Any]:
    full_path = repo_root / path
    if not full_path.exists():
        failures.append(f"PR157_GENERATED_ARTIFACT_MISSING:{path.as_posix()}")
        return {}
    payload = read_json(full_path)
    if not isinstance(payload, Mapping):
        failures.append(f"PR157_GENERATED_ARTIFACT_NOT_OBJECT:{path.as_posix()}")
        return {}
    return payload


def _require(condition: bool, failures: list[str], code: str) -> None:
    if not condition:
        failures.append(code)


def _placeholder_failures(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, str):
        if value in c.FORBIDDEN_PLACEHOLDER_VALUES:
            failures.append(f"PR157_PLACEHOLDER_VALUE:{path}:{value}")
        if "PLACEHOLDER" in value:
            failures.append(f"PR157_PLACEHOLDER_VALUE:{path}:{value}")
    elif isinstance(value, Mapping):
        for key, child in value.items():
            failures.extend(_placeholder_failures(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_placeholder_failures(child, f"{path}[{index}]"))
    return failures


def _validate_input_receipts(report: Mapping[str, Any], failures: list[str]) -> None:
    receipts = [as_mapping(item) for item in as_list(report.get("input_consumption_receipt"))]
    paths = {str(item.get("path")): item for item in receipts}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            fallback = paths.get(c.CROSSWALK_FALLBACK_PATH.as_posix(), {})
            requested = paths.get(path.as_posix(), {})
            _require(
                bool(requested) and (requested.get("exists") or fallback.get("consumed")),
                failures,
                "PR157_MANDATORY_CROSSWALK_OR_FALLBACK_NOT_CONSUMED",
            )
            continue
        receipt = paths.get(path.as_posix())
        _require(
            bool(receipt and receipt.get("exists") and receipt.get("consumed")),
            failures,
            f"PR157_MANDATORY_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    for required in c.PR153_PR156_ARTIFACTS:
        receipt = paths.get(required.as_posix())
        _require(
            bool(receipt and receipt.get("exists") and receipt.get("consumed")),
            failures,
            f"PR157_REQUIRED_BRIDGE_INPUT_NOT_CONSUMED:{required.as_posix()}",
        )


def _validate_pr154(pr154_registry: Mapping[str, Any], pr154_report: Mapping[str, Any], failures: list[str]) -> None:
    records = [as_mapping(item) for item in as_list(pr154_registry.get("records"))]
    _require(len(records) == c.EXPECTED_PR154_TOTAL, failures, "PR157_PR154_COUNT_NOT_342")
    count_receipt = as_mapping(pr154_report.get("count_invariant_receipt"))
    _require(
        count_receipt.get("count_invariants_passed_flag") is True,
        failures,
        "PR157_PR154_COUNT_INVARIANT_FAILED",
    )
    for record in records:
        target_id = str(record.get("target_id"))
        _require(
            record.get("completion_class") in c.CENTRAL_ENUM_VALUE_SETS["completion_class"],
            failures,
            f"PR157_BAD_COMPLETION_CLASS:{target_id}",
        )
        _require(
            record.get("source_population") in c.CENTRAL_ENUM_VALUE_SETS["source_population"],
            failures,
            f"PR157_BAD_SOURCE_POPULATION:{target_id}",
        )
        _require(
            record.get("blocker_class") in c.CENTRAL_ENUM_VALUE_SETS["blocker_class"],
            failures,
            f"PR157_BAD_BLOCKER_CLASS:{target_id}",
        )
        _require(
            bool(record.get("owner_editability_class")),
            failures,
            f"PR157_PR154_OWNER_EDITABILITY_MISSING:{target_id}",
        )
        _require(
            bool(record.get("no_orphan_status")),
            failures,
            f"PR157_PR154_NO_ORPHAN_STATUS_MISSING:{target_id}",
        )
        _require(
            record.get("exact_agent_id_or_null") is None,
            failures,
            f"PR157_EXACT_AGENT_ID_INVENTED:{target_id}",
        )
        if record.get("blocker_class") != c.BlockerClass.NONE.value:
            _require(
                bool(record.get("exact_next_action_if_not_complete")),
                failures,
                f"PR157_PR154_NEXT_ACTION_MISSING:{target_id}",
            )
            _require(
                bool(record.get("fill_plan_refs")),
                failures,
                f"PR157_PR154_FILL_PLAN_MISSING:{target_id}",
            )
        if record.get("source_population") in {
            c.SourcePopulation.PR154_PUBLIC_EXTERNAL_CAPTURED.value,
            c.SourcePopulation.PR154_PUBLIC_EXTERNAL_RETRY.value,
        }:
            _require(
                record.get("external_fact_override_forbidden_flag") is True,
                failures,
                f"PR157_PR154_SOURCE_FACT_OVERRIDE_NOT_FORBIDDEN:{target_id}",
            )


def _validate_atomicrows(registry: Mapping[str, Any], report: Mapping[str, Any], failures: list[str]) -> None:
    records = [as_mapping(item) for item in as_list(registry.get("records"))]
    if not records and registry.get("records_are_sharded") is True:
        records = [as_mapping(item) for item in as_list(registry.get("_loaded_shard_records"))]
    _require(len(records) == c.EXPECTED_ATOMICROWS_TOTAL, failures, "PR157_ATOMICROWS_COUNT_NOT_4183")
    _require(
        report.get("count_reconciliation_passed_flag") is True,
        failures,
        "PR157_ATOMICROWS_COUNT_RECONCILIATION_FAILED",
    )
    _require(report.get("orphan_count") == 0, failures, "PR157_ATOMICROWS_ORPHAN_COUNT_NONZERO")
    _require(
        report.get("placeholder_value_count") == 0,
        failures,
        "PR157_ATOMICROWS_PLACEHOLDER_COUNT_NONZERO",
    )
    source_counts = as_mapping(report.get("source_requirement_class_counts"))
    counted = sum(
        value
        for key, value in source_counts.items()
        if key.endswith("_count") and key != "atomicrows_total_count"
    )
    _require(counted == c.EXPECTED_ATOMICROWS_TOTAL, failures, "PR157_ATOMICROWS_CLASS_COUNTS_NOT_4183")
    seen_ids: set[str] = set()
    for record in records:
        row_id = str(record.get("row_id_or_row_ref"))
        _require(row_id not in seen_ids, failures, f"PR157_DUPLICATE_ATOMICROW:{row_id}")
        seen_ids.add(row_id)
        primary = record.get("source_requirement_class")
        _require(
            primary in c.CENTRAL_ENUM_VALUE_SETS["source_requirement_class"],
            failures,
            f"PR157_BAD_ATOMICROWS_SOURCE_REQUIREMENT:{row_id}",
        )
        _require(
            isinstance(primary, str) and bool(primary),
            failures,
            f"PR157_ATOMICROWS_PRIMARY_CLASS_MISSING:{row_id}",
        )
        _require(
            record.get("owner_editability_class") in c.CENTRAL_ENUM_VALUE_SETS["owner_editability_class"],
            failures,
            f"PR157_ATOMICROWS_OWNER_EDITABILITY_MISSING:{row_id}",
        )
        _require(
            record.get("no_orphan_status") in c.CENTRAL_ENUM_VALUE_SETS["no_orphan_status"],
            failures,
            f"PR157_ATOMICROWS_NO_ORPHAN_STATUS_MISSING:{row_id}",
        )
        _require(
            record.get("exact_agent_id_or_null") is None,
            failures,
            f"PR157_ATOMICROWS_EXACT_AGENT_ID_INVENTED:{row_id}",
        )
        if record.get("blocker_class") != c.BlockerClass.NONE.value:
            plans = [as_mapping(item) for item in as_list(record.get("unresolved_field_fill_plans"))]
            _require(bool(plans), failures, f"PR157_ATOMICROWS_FILL_PLAN_MISSING:{row_id}")
            for plan in plans:
                for field in (
                    "fill_plan_id",
                    "exact_steps_to_fill",
                    "exact_acceptance_criteria",
                    "validator_that_will_unblock",
                ):
                    _require(bool(plan.get(field)), failures, f"PR157_FILL_PLAN_FIELD_MISSING:{row_id}:{field}")
        if record.get("factual_external_value_flag") is True:
            _require(
                record.get("external_fact_override_forbidden_flag") is True,
                failures,
                f"PR157_ATOMICROWS_SOURCE_FACT_OVERRIDE_NOT_FORBIDDEN:{row_id}",
            )
        if record.get("owner_value_change_allowed_flag") is True:
            _require(
                record.get("owner_change_requires_replay_flag") is True
                and record.get("owner_change_requires_paper_flag") is True
                and record.get("owner_change_blocks_live_until_review_flag") is True,
                failures,
                f"PR157_OWNER_EDITABLE_RETEST_FLAGS_MISSING:{row_id}",
            )
            _require(
                record.get("open_orders_unchanged_by_value_change_flag") is True
                and record.get("open_positions_unchanged_by_value_change_flag") is True,
                failures,
                f"PR157_OWNER_EDITABLE_MUTATES_OPEN_STATE:{row_id}",
            )
        no_authority = as_mapping(record.get("no_authority_confirmation"))
        _require(
            all(value is False for value in no_authority.values()),
            failures,
            f"PR157_ATOMICROWS_AUTHORITY_FLAG_TRUE:{row_id}",
        )


def _validate_owner_packet(packet: Mapping[str, Any], failures: list[str]) -> None:
    requests = [as_mapping(item) for item in as_list(packet.get("requests"))]
    _require(packet.get("request_count") == len(requests), failures, "PR157_OWNER_PACKET_COUNT_MISMATCH")
    ids = [str(item.get("request_id")) for item in requests]
    _require(len(ids) == len(set(ids)), failures, "PR157_OWNER_PACKET_DUPLICATE_REQUEST_ID")
    required_fields = {
        "request_id",
        "record_id_or_row_id",
        "target_field_id_or_missing_field_id",
        "source_population",
        "current_blocker_class",
        "exact_owner_question",
        "exact_unblock_condition",
        "exact_steps_to_fill",
        "exact_acceptance_criteria",
        "validator_that_will_unblock",
        "authority_profile_ids",
    }
    for request in requests:
        request_id = str(request.get("request_id"))
        for field in required_fields:
            _require(bool(request.get(field)), failures, f"PR157_OWNER_PACKET_FIELD_MISSING:{request_id}:{field}")
        _require(
            request.get("owner_answer_cannot_create_external_fact_flag") is True,
            failures,
            f"PR157_OWNER_PACKET_EXTERNAL_FACT_BOUNDARY_MISSING:{request_id}",
        )


def _validate_currentness(repo_root: Path, failures: list[str]) -> None:
    expected = build_artifacts(repo_root)
    expected_payloads = {
        c.PR154_REPORT_PATH: expected.pr154_report,
        c.PR154_REGISTRY_PATH: expected.pr154_registry,
        c.ATOMICROWS_REPORT_PATH: expected.atomicrows_report,
        c.ATOMICROWS_REGISTRY_PATH: expected.atomicrows_registry,
        c.OWNER_REQUEST_PATH: expected.owner_request_packet,
    }
    for path, payload in expected_payloads.items():
        full_path = repo_root / path
        if full_path.exists() and full_path.read_text(encoding="utf-8") != json_dump(payload):
            failures.append(f"PR157_GENERATED_ARTIFACT_NOT_DETERMINISTIC_CURRENT:{path.as_posix()}")
    for shard in expected.atomicrows_shards:
        shard_path = Path(str(shard["shard_path"]))
        payload = {
            "registry_type": "PR157_ATOMICROWS_4183_COMPLETION_MATERIALIZATION_SHARD",
            "pr_id": c.PR_ID,
            "semantic_task_id": c.SEMANTIC_TASK_ID,
            "authority_class": c.AUTHORITY_CLASS,
            "shard_id": shard["shard_id"],
            "row_count": shard["row_count"],
            "first_row_id": shard["first_row_id"],
            "last_row_id": shard["last_row_id"],
            "records": shard["records"],
            "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        }
        full_path = repo_root / shard_path
        if full_path.exists() and full_path.read_text(encoding="utf-8") != json_dump(payload):
            failures.append(
                "PR157_GENERATED_ARTIFACT_NOT_DETERMINISTIC_CURRENT:"
                f"{shard_path.as_posix()}"
            )


def validate_existing_artifacts(repo_root: Path | str) -> ValidationResult:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    pr154_report = _load_required_json(root, c.PR154_REPORT_PATH, failures)
    pr154_registry = _load_required_json(root, c.PR154_REGISTRY_PATH, failures)
    atomicrows_report = _load_required_json(root, c.ATOMICROWS_REPORT_PATH, failures)
    atomicrows_registry = _load_required_json(root, c.ATOMICROWS_REGISTRY_PATH, failures)
    owner_packet = _load_required_json(root, c.OWNER_REQUEST_PATH, failures)
    if failures:
        return ValidationResult(tuple(sorted(set(failures))))
    shard_records: list[Mapping[str, Any]] = []
    for shard_ref in as_list(atomicrows_registry.get("shards")):
        shard = as_mapping(shard_ref)
        shard_path = shard.get("shard_path")
        if not shard_path:
            failures.append("PR157_ATOMICROWS_SHARD_PATH_MISSING")
            continue
        payload = _load_required_json(root, Path(str(shard_path)), failures)
        records = [as_mapping(item) for item in as_list(payload.get("records"))]
        if payload:
            _require(
                payload.get("row_count") == len(records),
                failures,
                f"PR157_ATOMICROWS_SHARD_COUNT_MISMATCH:{shard_path}",
            )
            shard_records.extend(records)
    if atomicrows_registry.get("records_are_sharded") is True:
        atomicrows_registry = dict(atomicrows_registry)
        atomicrows_registry["_loaded_shard_records"] = shard_records
    _validate_input_receipts(pr154_report, failures)
    _validate_pr154(pr154_registry, pr154_report, failures)
    _validate_atomicrows(atomicrows_registry, atomicrows_report, failures)
    _validate_owner_packet(owner_packet, failures)
    for payload in (
        pr154_report,
        pr154_registry,
        atomicrows_report,
        atomicrows_registry,
        owner_packet,
    ):
        failures.extend(_placeholder_failures(payload))
        no_authority = as_mapping(payload.get("no_authority_confirmation"))
        _require(
            all(value is False for value in no_authority.values()),
            failures,
            "PR157_REPORT_AUTHORITY_FLAG_TRUE",
        )
    if (root / c.OWNER_RESPONSE_PATH).exists():
        owner_response = read_json(root / c.OWNER_RESPONSE_PATH)
        failures.extend(
            validate_owner_response_payload(as_mapping(owner_response), owner_packet)
        )
    _validate_currentness(root, failures)
    return ValidationResult(tuple(sorted(set(failures))))
