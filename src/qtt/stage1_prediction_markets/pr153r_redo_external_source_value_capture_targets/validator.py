"""PR153R redo repository validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from . import accepted_packet
from . import constants as c
from . import extraction
from . import report as report_builder
from . import seed_map
from . import taxonomy as tx


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _accepted_packet_artifact_count(repo_root: Path) -> int:
    directory = repo_root / c.ACCEPTED_PACKET_DIR
    if not directory.exists():
        return 0
    return len(sorted(directory.glob("*.json")))


def validate_report(payload: Mapping[str, Any], repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    pr153 = _read_json(root / c.PR153_REPORT_PATH)
    pr151 = _read_json(root / c.PR151_REPORT_PATH)
    extracted = extraction.extract_pr153r_targets(pr153)
    enriched = extraction.enrich_targets_from_pr151(extracted, pr151)
    owner_inputs = seed_map.load_owner_supplied_inputs(root)
    cross_validation = seed_map.cross_validate_seed_inputs(
        extracted,
        owner_inputs,
        enriched,
    )

    if extraction.extraction_failures(extracted):
        failures.extend(extraction.extraction_failures(extracted))
    if len(extracted) != c.EXPECTED_TARGET_COUNT:
        failures.append(tx.PR153R_REDO_EXTRACTION_COUNT_BLOCK)
    if extraction.platform_counts(extracted) != c.EXPECTED_PLATFORM_COUNTS:
        failures.append(tx.PR153R_REDO_EXTRACTION_COUNT_BLOCK)
    if cross_validation.get("status") != "PASSED":
        failures.append(tx.PR153R_REDO_OWNER_SUPPLIED_SEED_MISMATCH_BLOCK)

    if payload.get("extracted_target_count") != c.EXPECTED_TARGET_COUNT:
        failures.append("PR153R_REDO_REPORT_TARGET_COUNT_MISMATCH")
    if payload.get("platform_counts") != c.EXPECTED_PLATFORM_COUNTS:
        failures.append("PR153R_REDO_REPORT_PLATFORM_COUNTS_MISMATCH")
    for key in (
        "no_broadening_to_342",
        "no_broadening_to_126",
        "no_broadening_to_92",
        "no_top_20_unresolved_list_used_as_target_source",
    ):
        if payload.get(key) is not True:
            failures.append(f"PR153R_REDO_BROADENING_FLAG_FALSE: {key}")

    top_20 = _list(
        _mapping(pr153.get("capture_blocker_category_summary")).get(
            "top_20_unresolved_p0_p1_targets"
        )
    )
    top_20_ids = {
        str(item.get("retrieval_target_id"))
        for item in top_20
        if isinstance(item, Mapping)
    }
    extracted_ids = {str(item.get("retrieval_target_id")) for item in extracted}
    if extracted_ids == top_20_ids or len(extracted_ids) == len(top_20_ids):
        failures.append("PR153R_REDO_TOP_20_USED_AS_TARGET_SOURCE")

    per_target = _list(payload.get("per_target_records"))
    if len(per_target) != c.EXPECTED_TARGET_COUNT:
        failures.append("PR153R_REDO_PER_TARGET_COUNT_MISMATCH")
    expected_ids = {str(item.get("retrieval_target_id")) for item in extracted}
    report_ids = {str(item.get("retrieval_target_id")) for item in per_target}
    if report_ids != expected_ids:
        failures.append("PR153R_REDO_PER_TARGET_IDS_MISMATCH")

    for item in per_target:
        record = _mapping(item)
        if record.get("owner_route") != tx.PR153R_RETRY_CAPTURE:
            failures.append("PR153R_REDO_TARGET_OWNER_ROUTE_MISMATCH")
        if (
            record.get("recommended_primary_eligibility_lane")
            != tx.EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET
        ):
            failures.append("PR153R_REDO_TARGET_LANE_MISMATCH")
        if record.get("seed_url_authority_status") != tx.CANDIDATE_SEED_ONLY_NOT_ACCEPTED_FACT:
            failures.append("PR153R_REDO_SEED_PROMOTED_TO_ACCEPTED_FACT")
        if record.get("acceptance_decision") == tx.ACCEPTED_TARGET_FIELD_SOURCE_PACKET:
            failures.extend(accepted_packet.validate_accepted_packet(record))
        else:
            block_codes = record.get("block_codes")
            if not isinstance(block_codes, list) or not block_codes:
                failures.append("PR153R_REDO_BLOCKED_TARGET_MISSING_BLOCK_CODES")
            else:
                for code in block_codes:
                    if code not in tx.BLOCK_CODES:
                        failures.append(f"PR153R_REDO_UNKNOWN_BLOCK_CODE: {code}")
        failures.extend(accepted_packet.digest_metadata_policy_failures(record))
        if record.get("connector_unlock_eligibility_status") != (
            tx.CONNECTOR_UNLOCK_NOT_CREATED_BY_SOURCE_PACKET
        ):
            failures.append("PR153R_REDO_CONNECTOR_UNLOCK_STATUS_INVALID")

    accepted_count = int(payload.get("accepted_source_packet_count", -1))
    actual_accepted_artifacts = _accepted_packet_artifact_count(root)
    if accepted_count != actual_accepted_artifacts:
        failures.append("PR153R_REDO_ACCEPTED_PACKET_ARTIFACT_COUNT_MISMATCH")
    if accepted_count != sum(
        1
        for item in per_target
        if _mapping(item).get("acceptance_decision")
        == tx.ACCEPTED_TARGET_FIELD_SOURCE_PACKET
    ):
        failures.append("PR153R_REDO_ACCEPTED_PACKET_COUNT_MISMATCH")

    if payload.get("blocked_candidate_count") != c.EXPECTED_TARGET_COUNT - accepted_count:
        failures.append("PR153R_REDO_BLOCKED_CANDIDATE_COUNT_MISMATCH")
    if payload.get("source_packet_digest_metadata_count") != c.EXPECTED_TARGET_COUNT:
        failures.append("PR153R_REDO_DIGEST_METADATA_COUNT_MISMATCH")

    if payload.get("connector_unlock_count") != 0:
        failures.append("PR153R_REDO_CONNECTOR_UNLOCK_CREATED")
    for key in tx.ZERO_AUTHORITY_COUNT_KEYS:
        if payload.get(key) != 0:
            failures.append(f"PR153R_REDO_FORBIDDEN_AUTHORITY_COUNT_NONZERO: {key}")

    taxonomy_module = payload.get("taxonomy_module_path")
    if taxonomy_module != (
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets/taxonomy.py"
    ):
        failures.append("PR153R_REDO_TAXONOMY_MODULE_NOT_CENTRALIZED")
    centralized = _mapping(payload.get("centralized_taxonomy_constants"))
    if set(centralized.get("block_codes", [])) != set(tx.BLOCK_CODES):
        failures.append("PR153R_REDO_TAXONOMY_BLOCK_CODES_MISMATCH")

    if payload.get("final_status_label") not in tx.FINAL_STATUS_LABELS:
        failures.append("PR153R_REDO_FINAL_STATUS_LABEL_INVALID")

    rebuilt = report_builder.build_report(root)
    if report_builder.json_dump(dict(payload)) != report_builder.json_dump(rebuilt):
        failures.append("PR153R_REDO_REPORT_NOT_DETERMINISTIC")
    return sorted(set(failures))


def validate_repository_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    report_path = root / c.REPORT_PATH
    if not report_path.exists():
        return [f"PR153R_REDO_REPORT_MISSING: {c.REPORT_PATH.as_posix()}"]
    try:
        payload = _read_json(report_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"PR153R_REDO_REPORT_INVALID: {exc}"]
    return validate_report(payload, root)
