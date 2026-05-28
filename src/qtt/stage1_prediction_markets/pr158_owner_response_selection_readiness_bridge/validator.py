"""Fail-closed validator for PR158 generated artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping, json_dump, read_json
from .models import ValidationResult
from .owner_response_validator import validate_owner_response_payload
from .report import build_artifacts


def _require(condition: bool, failures: list[str], code: str) -> None:
    if not condition:
        failures.append(code)


def _load_json(root: Path, path: Path, failures: list[str]) -> Mapping[str, Any]:
    full_path = root / path
    if not full_path.exists():
        failures.append(f"PR158_GENERATED_ARTIFACT_MISSING:{path.as_posix()}")
        return {}
    payload = read_json(full_path)
    if not isinstance(payload, dict):
        failures.append(f"PR158_GENERATED_ARTIFACT_NOT_OBJECT:{path.as_posix()}")
        return {}
    return payload


def _placeholder_failures(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, str):
        if value in c.FORBIDDEN_PLACEHOLDER_VALUES or "PLACEHOLDER" in value:
            failures.append(f"PR158_PLACEHOLDER_VALUE:{path}:{value}")
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
                "PR158_MANDATORY_CROSSWALK_OR_FALLBACK_NOT_CONSUMED",
            )
            continue
        item = by_path.get(path.as_posix(), {})
        _require(
            bool(item and item.get("exists") and item.get("consumed")),
            failures,
            f"PR158_MANDATORY_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    for path in c.MANDATORY_PR158_INPUTS:
        item = by_path.get(path.as_posix(), {})
        _require(
            bool(item and item.get("exists") and item.get("consumed")),
            failures,
            f"PR158_MANDATORY_PR158_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    shard_receipts = [
        item
        for item in receipts
        if item.get("artifact_role") == "mandatory_pr157_atomicrows_completion_shard"
        and item.get("exists")
        and item.get("consumed")
    ]
    _require(len(shard_receipts) == 9, failures, "PR158_PR157_SHARDS_NOT_CONSUMED")


def _validate_lane_records(master_registry: Mapping[str, Any], failures: list[str]) -> None:
    records = [as_mapping(item) for item in as_list(master_registry.get("records"))]
    _require(len(records) == c.EXPECTED_OWNER_PACKET_REQUESTS, failures, "PR158_OWNER_LANE_RECORD_COUNT_NOT_1483")
    request_ids = [str(item.get("request_id")) for item in records]
    _require(len(request_ids) == len(set(request_ids)), failures, "PR158_DUPLICATE_LANE_REQUEST_ID")
    for record in records:
        request_id = str(record.get("request_id"))
        _require(record.get("lane") in c.CENTRAL_ENUM_VALUE_SETS["lane"], failures, f"PR158_BAD_LANE:{request_id}")
        _require(
            record.get("completion_decision_class") in c.CENTRAL_ENUM_VALUE_SETS["completion_decision_class"],
            failures,
            f"PR158_BAD_COMPLETION_DECISION:{request_id}",
        )
        if record.get("exact_agent_id_or_null") is not None:
            failures.append(f"PR158_EXACT_AGENT_ID_INVENTED:{request_id}")
        if record.get("actual_numeric_range_available") is True:
            failures.append(f"PR158_NUMERIC_RANGE_INVENTED:{request_id}")
        if record.get("factual_external_value_flag") is True:
            failures.append(f"PR158_EXTERNAL_FACT_OWNER_FILLED:{request_id}")
        if record.get("lane") == c.PR158Lane.LANE_F_PR154_PRIVATE_DOC_ATTESTATION.value:
            _require(
                record.get("response_value_or_null") is None,
                failures,
                f"PR158_PRIVATE_DOC_COMPLETED_WITHOUT_ATTESTATION:{request_id}",
            )
            _require(
                record.get("raw_secret_capture_forbidden_flag") is True,
                failures,
                f"PR158_PRIVATE_DOC_RAW_SECRET_NOT_FORBIDDEN:{request_id}",
            )


def _validate_overlay(overlay_registry: Mapping[str, Any], overlay_report: Mapping[str, Any], failures: list[str]) -> None:
    records = [as_mapping(item) for item in as_list(overlay_registry.get("records"))]
    _require(len(records) == c.EXPECTED_ATOMICROWS_TOTAL, failures, "PR158_OVERLAY_COUNT_NOT_4183")
    row_ids = [str(item.get("row_id")) for item in records]
    _require(len(row_ids) == len(set(row_ids)), failures, "PR158_OVERLAY_DUPLICATE_ROW_ID")
    _require(
        overlay_report.get("atomicrows_selection_readiness_total_count") == c.EXPECTED_ATOMICROWS_TOTAL,
        failures,
        "PR158_OVERLAY_REPORT_COUNT_NOT_4183",
    )
    for record in records:
        row_id = str(record.get("row_id"))
        _require(record.get("blocker_class") in c.CENTRAL_ENUM_VALUE_SETS["blocker_class"], failures, f"PR158_OVERLAY_BAD_BLOCKER:{row_id}")
        _require(
            record.get("scoring_feature_role") in c.CENTRAL_ENUM_VALUE_SETS["scoring_feature_role"],
            failures,
            f"PR158_OVERLAY_BAD_SCORING_ROLE:{row_id}",
        )
        _require(
            record.get("latency_path_class") in c.CENTRAL_ENUM_VALUE_SETS["latency_path_class"],
            failures,
            f"PR158_OVERLAY_BAD_LATENCY_PATH:{row_id}",
        )
        for flag in (
            "quantum_backend_execution_allowed_flag",
            "optimizer_execution_allowed_flag",
            "scoring_execution_allowed_flag",
            "live_order_authority_allowed_flag",
        ):
            _require(record.get(flag) is False, failures, f"PR158_OVERLAY_FORBIDDEN_EXECUTION:{row_id}:{flag}")
        _require(record.get("exact_agent_id_or_null") is None, failures, f"PR158_OVERLAY_EXACT_AGENT_ID_INVENTED:{row_id}")
    for field in (
        "live_order_authority_allowed_count",
        "scoring_execution_allowed_count",
        "optimizer_execution_allowed_count",
        "quantum_backend_execution_allowed_count",
    ):
        _require(overlay_report.get(field) == 0, failures, f"PR158_OVERLAY_NONZERO:{field}")


def _validate_response(root: Path, packet: Mapping[str, Any], failures: list[str]) -> None:
    response_path = root / c.OWNER_RESPONSE_PATH
    _require(response_path.exists(), failures, "PR158_OWNER_RESPONSE_FILE_NOT_CREATED")
    if not response_path.exists():
        return
    response = as_mapping(read_json(response_path))
    failures.extend(validate_owner_response_payload(response, packet))
    items = [as_mapping(item) for item in as_list(response.get("response_items"))]
    _require(len(items) == 1444, failures, "PR158_OWNER_RESPONSE_ITEM_COUNT_NOT_1444")
    request_ids = {
        str(item.get("request_id"))
        for item in as_list(packet.get("requests"))
        if item.get("request_id")
    }
    for item in items:
        request_id = str(item.get("request_id"))
        _require(request_id in request_ids, failures, f"PR158_OWNER_RESPONSE_UNKNOWN_REQUEST:{request_id}")
        _require(item.get("claims_external_fact") is False, failures, f"PR158_RESPONSE_EXTERNAL_FACT:{request_id}")
        for flag in c.NO_AUTHORITY_CONFIRMATION:
            response_flag = {
                "runtime_execution_created": "creates_runtime_authority",
                "live_execution_created": "creates_live_authority",
                "replay_execution_created": "creates_replay_authority",
                "paper_execution_created": "creates_paper_authority",
                "scoring_execution_created": "creates_scoring_execution",
                "optimizer_execution_created": "creates_optimizer_execution",
                "quantum_backend_execution_created": "creates_quantum_backend_execution",
                "order_authority_created": "creates_order_fill_profit_authority",
                "qtt_checksum_freeze_global_digest_authority_created": "creates_qtt_checksum_freeze_global_digest_authority",
                "atomicrows_bundle_checksum_hash_authority_created": "creates_atomicrows_bundle_checksum_hash_authority",
            }.get(flag)
            if response_flag and item.get(response_flag) is True:
                failures.append(f"PR158_RESPONSE_FORBIDDEN_AUTHORITY:{request_id}:{response_flag}")


def _validate_currentness(root: Path, failures: list[str]) -> None:
    expected = build_artifacts(root)
    for path_text, payload in expected.payloads.items():
        full_path = root / path_text
        if full_path.exists() and full_path.read_text(encoding="utf-8") != json_dump(payload):
            failures.append(f"PR158_GENERATED_ARTIFACT_NOT_DETERMINISTIC_CURRENT:{path_text}")
    for path_text, payload in expected.markdown_payloads.items():
        full_path = root / path_text
        if full_path.exists() and full_path.read_text(encoding="utf-8") != payload:
            failures.append(f"PR158_MARKDOWN_ARTIFACT_NOT_DETERMINISTIC_CURRENT:{path_text}")
    response_path = root / c.OWNER_RESPONSE_PATH
    if response_path.exists() and response_path.read_text(encoding="utf-8") != json_dump(expected.owner_response):
        failures.append(f"PR158_OWNER_RESPONSE_NOT_DETERMINISTIC_CURRENT:{c.OWNER_RESPONSE_PATH.as_posix()}")


def validate_existing_artifacts(repo_root: Path | str) -> ValidationResult:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    master_report = _load_json(root, c.MASTER_REPORT_PATH, failures)
    master_registry = _load_json(root, c.MASTER_REGISTRY_PATH, failures)
    overlay_report = _load_json(root, c.SELECTION_OVERLAY_REPORT_PATH, failures)
    overlay_registry = _load_json(root, c.SELECTION_OVERLAY_REGISTRY_PATH, failures)
    packet = _load_json(root, c.OWNER_REQUEST_PATH, failures)
    for path in c.ALL_JSON_ARTIFACT_PATHS:
        _load_json(root, path, failures)
    for path in (c.OWNER_DECISION_SUMMARY_PATH, c.PRIVATE_DOC_REVIEW_PATH):
        if not (root / path).exists():
            failures.append(f"PR158_MARKDOWN_ARTIFACT_MISSING:{path.as_posix()}")
    if failures:
        return ValidationResult(tuple(sorted(set(failures))))
    _validate_receipts(master_report, failures)
    count_receipt = as_mapping(master_report.get("count_invariant_receipt"))
    _require(
        count_receipt.get("count_invariants_passed_flag") is True,
        failures,
        "PR158_COUNT_INVARIANTS_FAILED",
    )
    _validate_lane_records(master_registry, failures)
    _validate_overlay(overlay_registry, overlay_report, failures)
    _validate_response(root, packet, failures)
    _require(master_report.get("placeholder_value_count") == 0, failures, "PR158_PLACEHOLDER_COUNT_NONZERO")
    _require(master_report.get("orphan_count") == 0, failures, "PR158_ORPHAN_COUNT_NONZERO")
    _require(master_report.get("invented_external_fact_count") == 0, failures, "PR158_INVENTED_EXTERNAL_FACT_COUNT_NONZERO")
    _require(master_report.get("invented_numeric_range_count") == 0, failures, "PR158_INVENTED_NUMERIC_RANGE_COUNT_NONZERO")
    _require(master_report.get("invented_exact_agent_id_count") == 0, failures, "PR158_INVENTED_EXACT_AGENT_ID_COUNT_NONZERO")
    no_authority = as_mapping(master_report.get("no_authority_confirmation"))
    _require(all(value is False for value in no_authority.values()), failures, "PR158_NO_AUTHORITY_FLAG_TRUE")
    for payload in (master_report, master_registry, overlay_report, overlay_registry):
        failures.extend(_placeholder_failures(payload))
    _validate_currentness(root, failures)
    return ValidationResult(tuple(sorted(set(failures))))

