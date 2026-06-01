"""Map PR162A datasets to PR161F QKUs and run plans."""

from __future__ import annotations

from typing import Any

from . import constants as c


MAPPABLE_MARKETS = {"PREDICTION_MARKET", "MARKET_AGNOSTIC"}
ADAPTER_MECHANICS_SMOKE_LABEL = (
    "ADAPTER_MECHANICS_SMOKE_ONLY_NO_REAL_ARTIFACT_CANDIDATES"
)


def mapping_records(
    pr161f: dict[str, list[dict[str, Any]]],
    datasets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    executor = pr161f["PR161F_ExecutorInputRegistry.report.json"]
    replay = _index(pr161f["PR161F_ReplayRunRequestRegistry.report.json"])
    paper = _index(pr161f["PR161F_PaperRunRequestRegistry.report.json"])
    paired = _index(pr161f["PR161F_PairedReplayPaperRunPlan.report.json"])
    dataset = _kalshi_dataset_profile(datasets)
    records: list[dict[str, Any]] = []
    for index, row in enumerate(executor, start=1):
        qku_id = row["qku_id"]
        market = row.get("market")
        seed_candidate = market in MAPPABLE_MARKETS
        strict_proof = _strict_coverage_proof(row, dataset, seed_candidate=seed_candidate)
        strict_run_capable = all(strict_proof.values())
        dataset_refs = [c.KALSHI_RUN_CAPABLE_DATASET_ID] if seed_candidate else []
        blocker_codes = _coverage_blockers(strict_proof)
        blocker = "NONE" if strict_run_capable else _primary_blocker(seed_candidate, blocker_codes)
        mapping_status = (
            "MAPPED_TO_RUN_CAPABLE_CANDIDATE"
            if strict_run_capable
            else "MAPPED_TO_CANDIDATE_BLOCKED_FROM_RUN"
            if seed_candidate
            else "BLOCKED_UNMAPPABLE_QKU"
        )
        records.append(
            {
                "record_id": f"PR162A-QKU-DATASET-MAP-{index:05d}",
                "created_by_pr": c.PR_ID,
                "authority_class": c.AUTHORITY_CLASS,
                "qku_id": qku_id,
                "qku_bundle_id": row.get("qku_bundle_id_if_available"),
                "scenario_id": row.get("scenario_matrix_id_if_available"),
                "market_bundle_id": row.get("qku_bundle_id_if_available"),
                "market_scope": market,
                "venue_scope": row.get("venue_scope"),
                "pr161f_executor_input_id": row.get("executor_input_id"),
                "pr161f_replay_request_id": replay.get(qku_id, {}).get("replay_run_request_id"),
                "pr161f_paper_request_id": paper.get(qku_id, {}).get("paper_run_request_id"),
                "pr161f_paired_plan_id": paired.get(qku_id, {}).get("paired_run_plan_id"),
                "pr162_adapter_contract_ref": [
                    "PR162_ReplayDataAdapterContract.report.json",
                    "PR162_PaperDataAdapterContract.report.json",
                ],
                "dataset_candidate_ref": dataset_refs[0] if dataset_refs else None,
                "dataset_candidate_refs": dataset_refs,
                "mapping_status": mapping_status,
                "dataset_coverage_state": c.VENUE_SCOPED_RUN_CAPABLE_READY
                if strict_run_capable
                else blocker,
                "seed_candidate_coverage_state": c.DATASET_SEED_CANDIDATE_READY
                if seed_candidate
                else c.RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD,
                "adapter_mechanics_fixture_state": c.ADAPTER_MECHANICS_FIXTURE_READY
                if seed_candidate
                else c.RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD,
                "coverage_blocker_codes": [] if strict_run_capable else blocker_codes,
                "strict_coverage_proof": strict_proof,
                "strict_coverage_proof_status": "PASS" if strict_run_capable else "FAIL_CLOSED",
                "strict_run_capable_coverage_flag": strict_run_capable,
                "strict_row_count_coverage_flag": strict_proof["strict_row_count_coverage_flag"],
                "strict_time_window_coverage_flag": strict_proof["strict_time_window_coverage_flag"],
                "strict_venue_scope_match_flag": strict_proof["strict_venue_scope_match_flag"],
                "strict_qku_scope_match_flag": strict_proof["strict_qku_scope_match_flag"],
                "strict_scenario_scope_match_flag": strict_proof["strict_scenario_scope_match_flag"],
                "seed_candidate_mapping_flag": seed_candidate,
                "adapter_mechanics_fixture_mapping_flag": seed_candidate,
                "run_capable_mapping_flag": strict_run_capable,
                "run_capable_dataset_available_flag": strict_run_capable,
                "replay_lane_eligible_flag": strict_run_capable,
                "paper_lane_eligible_flag": strict_run_capable,
                "adapter_mechanics_smoke_allowed_flag": seed_candidate,
                "adapter_mechanics_smoke_label": ADAPTER_MECHANICS_SMOKE_LABEL
                if seed_candidate
                else None,
                "real_artifact_candidate_creation_allowed_flag": strict_run_capable,
                "dataset_row_count_candidate": dataset["row_count_candidate"],
                "strict_min_row_count_required": c.MIN_STRICT_RUN_CAPABLE_ROW_COUNT,
                "strict_min_time_window_seconds_required": (
                    c.MIN_STRICT_RUN_CAPABLE_TIME_WINDOW_SECONDS
                ),
                "dataset_time_window_seconds": dataset["time_window_seconds"],
                "blocker_code": blocker,
            }
        )
    return records


def pr161f_coverage_records(mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, record in enumerate(mappings, start=1):
        strict = record["strict_run_capable_coverage_flag"]
        seed = record["seed_candidate_mapping_flag"]
        records.append(
            {
                **_copy_common(record, f"PR162A-PR161F-COVERAGE-{index:05d}"),
                "coverage_status": "RUN_PLAN_DATASET_RUN_CAPABLE_MAPPED"
                if strict
                else "RUN_PLAN_DATASET_SEED_OR_MECHANICS_ONLY"
                if seed
                else "RUN_PLAN_DATASET_BLOCKED",
                "dataset_coverage_state": record["dataset_coverage_state"],
                "strict_run_capable_coverage_flag": strict,
                "run_capable_mapping_flag": strict,
                "seed_candidate_mapping_flag": seed,
                "adapter_mechanics_fixture_mapping_flag": record[
                    "adapter_mechanics_fixture_mapping_flag"
                ],
                "adapter_mechanics_smoke_allowed_flag": record[
                    "adapter_mechanics_smoke_allowed_flag"
                ],
                "adapter_mechanics_smoke_label": record["adapter_mechanics_smoke_label"],
                "real_artifact_candidate_creation_allowed_flag": strict,
                "strict_coverage_proof": record["strict_coverage_proof"],
                "coverage_blocker_codes": record["coverage_blocker_codes"],
            }
        )
    return records


def pr162_rerun_readiness_records(mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, record in enumerate(mappings, start=1):
        ready = record["strict_run_capable_coverage_flag"]
        seed = record["seed_candidate_mapping_flag"]
        records.append(
            {
                **_copy_common(record, f"PR162A-PR162-RERUN-READY-{index:05d}"),
                "pr161f_executor_input_ref": record["pr161f_executor_input_id"],
                "pr161f_replay_request_ref": record["pr161f_replay_request_id"],
                "pr161f_paper_request_ref": record["pr161f_paper_request_id"],
                "pr161f_paired_plan_ref": record["pr161f_paired_plan_id"],
                "pr162_adapter_contract_ref": record["pr162_adapter_contract_ref"],
                "run_capable_dataset_available_flag": ready,
                "replay_rerun_ready_flag": ready,
                "paper_rerun_ready_flag": ready,
                "both_lanes_rerun_ready_flag": ready,
                "rerun_readiness_state": c.VENUE_SCOPED_RUN_CAPABLE_READY
                if ready
                else record["dataset_coverage_state"],
                "strict_run_capable_coverage_flag": ready,
                "seed_candidate_mapping_flag": seed,
                "adapter_mechanics_fixture_mapping_flag": record[
                    "adapter_mechanics_fixture_mapping_flag"
                ],
                "adapter_mechanics_smoke_allowed_flag": seed,
                "adapter_mechanics_smoke_label": ADAPTER_MECHANICS_SMOKE_LABEL
                if seed
                else None,
                "real_artifact_candidate_creation_allowed_flag": ready,
                "pr162b_real_artifact_candidate_allowed_flag": ready,
                "pr162r_real_artifact_candidate_allowed_flag": ready,
                "strict_coverage_proof": record["strict_coverage_proof"],
                "coverage_blocker_codes": record["coverage_blocker_codes"],
                "remaining_blocker_code": "NONE" if ready else record["blocker_code"],
                "recommended_next_step": "ROUTE_TO_PR162B_OR_PR162R_RERUN"
                if ready
                else "MORE_DATA_REQUIRED"
                if record["blocker_code"] == c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS
                else "OWNER_MATERIALIZE_MORE_DATASET_COVERAGE",
                "downstream_pr_route": "PR162B_RERUN_PR162_WITH_PR162A_DATASETS"
                if ready
                else "PR162A_DATASET_MAPPING_REPAIR",
                "blocker_code": "PR162A_PR162B_RERUN_READY" if ready else record["blocker_code"],
            }
        )
    return records


def _copy_common(record: dict[str, Any], record_id: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "qku_id": record["qku_id"],
        "qku_bundle_id": record.get("qku_bundle_id"),
        "scenario_id": record.get("scenario_id"),
        "market_bundle_id": record.get("market_bundle_id"),
        "dataset_candidate_refs": record.get("dataset_candidate_refs", []),
        "mapping_status": record["mapping_status"],
        "blocker_code": record["blocker_code"],
    }


def _index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["qku_id"]: record for record in records if isinstance(record.get("qku_id"), str)}


def _kalshi_dataset_profile(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    dataset = next(
        record
        for record in datasets
        if record["dataset_id"] == c.KALSHI_RUN_CAPABLE_DATASET_ID
    )
    return {
        "venue_scope": dataset["venue_scope"],
        "row_count_candidate": int(dataset["row_count_candidate"]),
        "time_window_seconds": int(dataset.get("strict_time_window_coverage_seconds") or 0),
    }


def _strict_coverage_proof(
    row: dict[str, Any],
    dataset: dict[str, Any],
    *,
    seed_candidate: bool,
) -> dict[str, bool]:
    return {
        "strict_dataset_candidate_available_flag": seed_candidate,
        "strict_row_count_coverage_flag": (
            dataset["row_count_candidate"] >= c.MIN_STRICT_RUN_CAPABLE_ROW_COUNT
        ),
        "strict_time_window_coverage_flag": (
            dataset["time_window_seconds"] >= c.MIN_STRICT_RUN_CAPABLE_TIME_WINDOW_SECONDS
        ),
        "strict_venue_scope_match_flag": row.get("venue_scope") == dataset["venue_scope"],
        "strict_qku_scope_match_flag": _explicitly_kalshi_compatible(row),
        "strict_scenario_scope_match_flag": _scenario_is_explicitly_kalshi_covered(row),
    }


def _explicitly_kalshi_compatible(row: dict[str, Any]) -> bool:
    values = [
        row.get("qku_id"),
        row.get("venue_scope"),
        row.get("platform"),
        row.get("dataset_candidate_ref_if_available"),
        *(row.get("input_requirements") or []),
    ]
    return any("KALSHI" in str(value).upper() for value in values if value is not None)


def _scenario_is_explicitly_kalshi_covered(row: dict[str, Any]) -> bool:
    values = [
        row.get("scenario_matrix_id_if_available"),
        row.get("replay_paper_scenario_id_if_available"),
        *(row.get("input_requirements") or []),
    ]
    return any("KALSHI" in str(value).upper() for value in values if value is not None)


def _coverage_blockers(strict_proof: dict[str, bool]) -> list[str]:
    blockers: list[str] = []
    if not strict_proof["strict_row_count_coverage_flag"]:
        blockers.append(c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS)
    if not strict_proof["strict_time_window_coverage_flag"]:
        blockers.append(c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_TIME_WINDOW)
    if not strict_proof["strict_venue_scope_match_flag"]:
        blockers.append(c.RUN_CAPABLE_BLOCKED_VENUE_SCOPE_MISMATCH)
    if not strict_proof["strict_qku_scope_match_flag"]:
        blockers.append(c.RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD)
    if not strict_proof["strict_scenario_scope_match_flag"]:
        blockers.append(c.RUN_CAPABLE_BLOCKED_SCENARIO_SCOPE_TOO_BROAD)
    if not strict_proof["strict_dataset_candidate_available_flag"]:
        blockers.append(c.RUN_CAPABLE_BLOCKED_PR162B_REQUIRES_STRICT_DATASET_COVERAGE)
    return blockers


def _primary_blocker(seed_candidate: bool, blocker_codes: list[str]) -> str:
    if not seed_candidate:
        return c.RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD
    for blocker in (
        c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS,
        c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_TIME_WINDOW,
        c.RUN_CAPABLE_BLOCKED_VENUE_SCOPE_MISMATCH,
        c.RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD,
        c.RUN_CAPABLE_BLOCKED_SCENARIO_SCOPE_TOO_BROAD,
    ):
        if blocker in blocker_codes:
            return blocker
    return c.RUN_CAPABLE_BLOCKED_PR162B_REQUIRES_STRICT_DATASET_COVERAGE
