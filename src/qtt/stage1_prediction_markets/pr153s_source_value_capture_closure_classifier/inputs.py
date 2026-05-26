"""Read-only upstream input loading for PR153S."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.controlled_official_source_capture_candidate_packets import (
    constants as pr153_constants,
)
from src.qtt.stage1_prediction_markets.official_source_retrieval_target_pack_parameter_defaults import (
    constants as pr151_constants,
)
from src.qtt.stage1_prediction_markets.pr153r_redo_external_source_value_capture_targets import (
    constants as pr153r_constants,
)
from src.qtt.stage1_prediction_markets.source_backed_classical_quantum_parameter_default_target_matrix import (
    constants as pr150_constants,
)


PR136_SECTION_CROSSWALK_REQUESTED_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
)
PR136_SECTION_CROSSWALK_CANONICAL_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)

ORCHESTRATION_ARTIFACT_PATHS = (
    Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
    Path(
        "src/qtt/stage1_prediction_markets/launch_readiness/"
        "day1_launch_readiness_roadmap_policy.py"
    ),
    Path("docs/master_plan/generated/PR136RouteTriage.report.json"),
    PR136_SECTION_CROSSWALK_REQUESTED_PATH,
    PR136_SECTION_CROSSWALK_CANONICAL_PATH,
    Path("docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"),
    Path("docs/master_plan/generated/PR136CommandActionMatrix.report.json"),
    Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"),
    Path("docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"),
)

SOURCE_VALUE_ARTIFACT_PATHS = (
    pr150_constants.REPORT_PATH,
    pr151_constants.REPORT_PATH,
    pr153_constants.REPORT_PATH,
    pr153r_constants.REPORT_PATH,
    Path("tools/validate_controlled_official_source_capture_candidate_packets.py"),
    Path("tools/validate_pr153r_redo_external_source_value_capture_targets.py"),
    Path(
        "src/qtt/stage1_prediction_markets/"
        "pr153r_redo_external_source_value_capture_targets"
    ),
    Path(
        "src/qtt/stage1_prediction_markets/"
        "controlled_official_source_capture_candidate_packets"
    ),
    Path(
        "src/qtt/stage1_prediction_markets/"
        "official_source_retrieval_target_pack_parameter_defaults"
    ),
    Path(
        "src/qtt/stage1_prediction_markets/"
        "source_backed_classical_quantum_parameter_default_target_matrix"
    ),
)


@dataclass(frozen=True)
class UpstreamInputs:
    repo_root: Path
    pr150_report: Mapping[str, Any]
    pr151_report: Mapping[str, Any]
    pr153_report: Mapping[str, Any]
    pr153r_report: Mapping[str, Any]
    pr150_targets_by_id: Mapping[str, Mapping[str, Any]]
    pr151_targets: tuple[Mapping[str, Any], ...]
    pr153_candidates_by_id: Mapping[str, Mapping[str, Any]]
    pr153_owner_queue_by_id: Mapping[str, Mapping[str, Any]]
    pr153r_records_by_id: Mapping[str, Mapping[str, Any]]
    consumed_artifact_receipts: tuple[Mapping[str, Any], ...]
    orchestration_alignment_receipt: Mapping[str, Any]
    reconstruction_failures: tuple[str, ...]


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _artifact_receipt(repo_root: Path, rel_path: Path, role: str) -> dict[str, Any]:
    path = repo_root / rel_path
    exists = path.exists()
    receipt: dict[str, Any] = {
        "artifact_path": rel_path.as_posix(),
        "exists": exists,
        "consumed": exists,
        "role": role,
        "read_mode": "READ_ONLY_CONTEXT",
        "artifact_type": "dir" if exists and path.is_dir() else "file" if exists else "missing",
    }
    if exists and path.is_file() and path.suffix.lower() == ".json":
        try:
            payload = read_json_object(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            receipt["parse_status"] = f"PARSE_ERROR: {exc}"
        else:
            receipt["parse_status"] = "JSON_OBJECT_PARSED"
            for key in (
                "report_id",
                "validator_marker",
                "validation_state",
                "final_status_label",
                "receipt_type",
                "pr_id",
                "report_type",
            ):
                if key in payload:
                    receipt[key] = payload.get(key)
    elif exists:
        receipt["parse_status"] = "TEXT_OR_DIRECTORY_EXISTS"
    else:
        receipt["parse_status"] = "MISSING"
    return receipt


def _artifact_receipts(repo_root: Path) -> tuple[Mapping[str, Any], ...]:
    receipts: list[Mapping[str, Any]] = []
    for rel_path in ORCHESTRATION_ARTIFACT_PATHS:
        receipts.append(_artifact_receipt(repo_root, rel_path, "ORCHESTRATION"))
    for rel_path in SOURCE_VALUE_ARTIFACT_PATHS:
        receipts.append(_artifact_receipt(repo_root, rel_path, "SOURCE_VALUE_INPUT"))
    return tuple(receipts)


def _target_queue(pr151_report: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        item
        for item in _list(pr151_report.get("official_source_retrieval_target_queue"))
        if isinstance(item, Mapping)
    )


def _pr150_targets(pr150_report: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    matrix = _mapping(pr150_report.get("parameter_default_target_matrix"))
    return {
        str(item.get("target_id")): item
        for item in _list(matrix.get("parameter_target_items"))
        if isinstance(item, Mapping) and item.get("target_id")
    }


def _candidate_index(pr153_report: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    return {
        str(item.get("retrieval_target_id")): item
        for item in _list(pr153_report.get("source_capture_candidate_packets"))
        if isinstance(item, Mapping) and item.get("retrieval_target_id")
    }


def _owner_queue_index(pr153_report: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    layer = _mapping(pr153_report.get("owner_blocker_decision_layer"))
    return {
        str(item.get("retrieval_target_id")): item
        for item in _list(layer.get("owner_decision_required_queue"))
        if isinstance(item, Mapping) and item.get("retrieval_target_id")
    }


def _pr153r_index(pr153r_report: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    return {
        str(item.get("retrieval_target_id")): item
        for item in _list(pr153r_report.get("per_target_records"))
        if isinstance(item, Mapping) and item.get("retrieval_target_id")
    }


def _duplicate_values(values: list[str]) -> list[str]:
    counter = Counter(values)
    return sorted(value for value, count in counter.items() if count > 1)


def _orchestration_alignment_receipt(
    repo_root: Path,
    receipts: tuple[Mapping[str, Any], ...],
) -> dict[str, Any]:
    by_path = {str(item.get("artifact_path")): item for item in receipts}
    requested = by_path[PR136_SECTION_CROSSWALK_REQUESTED_PATH.as_posix()]
    canonical = by_path[PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix()]
    return {
        "pr_identity_roster_consumed": by_path[
            "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"
        ]["consumed"],
        "roadmap_execution_state_controller_consumed": by_path[
            "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"
        ]["consumed"],
        "post_pr135_day1_launch_readiness_roadmap_consumed": by_path[
            "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"
        ]["consumed"],
        "day1_launch_readiness_policy_consumed": by_path[
            "src/qtt/stage1_prediction_markets/launch_readiness/"
            "day1_launch_readiness_roadmap_policy.py"
        ]["consumed"],
        "pr136_route_triage_consumed": by_path[
            "docs/master_plan/generated/PR136RouteTriage.report.json"
        ]["consumed"],
        "pr136_section_crosswalk_requested_alias_exists": requested["exists"],
        "pr136_section_crosswalk_requested_alias_consumed": requested["consumed"],
        "pr136_section_crosswalk_canonical_successor_path": (
            PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix()
        ),
        "pr136_section_crosswalk_canonical_successor_consumed": canonical["consumed"],
        "missing_alias_created": False,
        "pr136_market_specific_index_consumed": by_path[
            "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"
        ]["consumed"],
        "pr136_command_action_matrix_consumed": by_path[
            "docs/master_plan/generated/PR136CommandActionMatrix.report.json"
        ]["consumed"],
        "pr137r_atomicrows_reconciliation_consumed": by_path[
            "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
        ]["consumed"],
        "pr138_atomicrows_semantic_contract_consumed": by_path[
            "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"
        ]["consumed"],
        "artifact_identification_uses_global_hashes": False,
        "artifact_identification_uses_paths_status_markers_only": True,
    }


def load_inputs(repo_root: Path | str) -> UpstreamInputs:
    root = Path(repo_root).resolve()
    pr150_report = read_json_object(root / pr150_constants.REPORT_PATH)
    pr151_report = read_json_object(root / pr151_constants.REPORT_PATH)
    pr153_report = read_json_object(root / pr153_constants.REPORT_PATH)
    pr153r_report = read_json_object(root / pr153r_constants.REPORT_PATH)

    pr150_targets_by_id = _pr150_targets(pr150_report)
    pr151_targets = _target_queue(pr151_report)
    pr153_candidates_by_id = _candidate_index(pr153_report)
    pr153_owner_queue_by_id = _owner_queue_index(pr153_report)
    pr153r_records_by_id = _pr153r_index(pr153r_report)
    receipts = _artifact_receipts(root)

    failures: list[str] = []
    pr151_ids = [str(item.get("retrieval_target_id") or "") for item in pr151_targets]
    duplicate_pr151_ids = _duplicate_values(pr151_ids)
    if duplicate_pr151_ids:
        failures.append(
            "PR153S_DUPLICATE_PR151_RETRIEVAL_TARGET_IDS: "
            + ",".join(duplicate_pr151_ids)
        )

    candidate_ids = set(pr153_candidates_by_id)
    owner_queue_ids = set(pr153_owner_queue_by_id)
    pr151_id_set = set(pr151_ids)
    if candidate_ids & owner_queue_ids:
        failures.append(
            "PR153S_PR153_CANDIDATE_AND_OWNER_QUEUE_OVERLAP: "
            + ",".join(sorted(candidate_ids & owner_queue_ids))
        )
    if candidate_ids | owner_queue_ids != pr151_id_set:
        missing = sorted(pr151_id_set - (candidate_ids | owner_queue_ids))
        extra = sorted((candidate_ids | owner_queue_ids) - pr151_id_set)
        failures.append(
            "PR153S_PR153_RECONSTRUCTION_ID_MISMATCH: "
            f"missing={','.join(missing)} extra={','.join(extra)}"
        )

    retry_ids = set(pr153r_records_by_id)
    retry_lane_ids = {
        target_id
        for target_id, row in pr153_owner_queue_by_id.items()
        if row.get("owner_route") == "PR153R_RETRY_CAPTURE"
    }
    if retry_ids != retry_lane_ids:
        failures.append(
            "PR153S_PR153R_RETRY_ID_MISMATCH: "
            f"missing={','.join(sorted(retry_lane_ids - retry_ids))} "
            f"extra={','.join(sorted(retry_ids - retry_lane_ids))}"
        )

    return UpstreamInputs(
        repo_root=root,
        pr150_report=pr150_report,
        pr151_report=pr151_report,
        pr153_report=pr153_report,
        pr153r_report=pr153r_report,
        pr150_targets_by_id=pr150_targets_by_id,
        pr151_targets=pr151_targets,
        pr153_candidates_by_id=pr153_candidates_by_id,
        pr153_owner_queue_by_id=pr153_owner_queue_by_id,
        pr153r_records_by_id=pr153r_records_by_id,
        consumed_artifact_receipts=receipts,
        orchestration_alignment_receipt=_orchestration_alignment_receipt(root, receipts),
        reconstruction_failures=tuple(sorted(set(failures))),
    )
