"""PR162A quantum-forward dataset feature readiness bridge."""

from __future__ import annotations

from typing import Any

from . import constants as c


def quantum_dataset_feature_records(
    qch_records: list[dict[str, Any]],
    mapping_by_qku: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(qch_records, start=1):
        qku_id = row["qku_id"]
        mapping = mapping_by_qku.get(qku_id, {})
        run_capable = bool(mapping.get("strict_run_capable_coverage_flag"))
        seed_candidate = bool(mapping.get("seed_candidate_mapping_flag"))
        blocked = not run_capable and not seed_candidate
        records.append(
            {
                "record_id": f"PR162A-QUANTUM-DATASET-FEATURE-{index:05d}",
                "created_by_pr": c.PR_ID,
                "authority_class": c.AUTHORITY_CLASS,
                "qku_id": qku_id,
                "pr162_quantum_readiness_ref": f"PR162-QUANTUM-READINESS-{index:05d}",
                "encoding_blueprint_ref": f"PR162-QUANTUM-ENCODING-{index:05d}",
                "backend_fit_ref": f"PR162-QUANTUM-BACKEND-FIT-{index:05d}",
                "comparator_blueprint_ref": f"PR162-QUANTUM-COMPARATOR-{index:05d}",
                "replay_paper_work_order_ref": f"PR162-QUANTUM-WORK-ORDER-{index:05d}",
                "dataset_candidate_refs": mapping.get("dataset_candidate_refs", []),
                "feature_family_candidates": list(c.QUANTUM_FEATURE_FAMILIES),
                "quantum_feature_materialization_status": (
                    "QUANTUM_DATASET_FEATURE_RUN_CAPABLE_READY"
                    if run_capable
                    else "FEATURE_SEED_CANDIDATE_ONLY"
                    if seed_candidate
                    else "QUANTUM_DATASET_FEATURE_BLOCKED_NO_SAFE_DATA"
                ),
                "classical_baseline_dataset_required_flag": True,
                "hybrid_comparator_dataset_required_flag": True,
                "run_capable_dataset_available_flag": run_capable,
                "seed_candidate_dataset_available_flag": seed_candidate,
                "feature_seed_candidate_only_flag": seed_candidate,
                "strict_run_capable_feature_coverage_flag": run_capable,
                "future_live_precomputed_snapshot_dataset_candidate_flag": run_capable,
                "live_hot_path_admissibility": "PRECOMPUTED_SNAPSHOT_ONLY"
                if run_capable
                else "FORBIDDEN_UNTIL_FUTURE_OWNER_GATE",
                "quantum_backend_execution_created_flag": False,
                "quantum_simulator_execution_created_flag": False,
                "optimizer_execution_created_flag": False,
                "coverage_blocker_codes": mapping.get("coverage_blocker_codes", []),
                "blocker_code": _quantum_blocker(
                    run_capable=run_capable,
                    seed_candidate=seed_candidate,
                    mapping=mapping,
                ),
            }
        )
    return records


def quantum_feature_work_order_records(
    feature_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162A-QUANTUM-FEATURE-WORK-ORDER-{index:05d}",
            "created_by_pr": c.PR_ID,
            "authority_class": c.AUTHORITY_CLASS,
            "qku_id": record["qku_id"],
            "dataset_candidate_refs": record["dataset_candidate_refs"],
            "feature_family_candidates": record["feature_family_candidates"],
            "work_order_status": "READY_FOR_PR162B_PR162R_REAL_RERUN_INPUT"
            if record["run_capable_dataset_available_flag"]
            else "FEATURE_SEED_CANDIDATE_ONLY_MORE_DATA_REQUIRED"
            if record["feature_seed_candidate_only_flag"]
            else "BLOCKED_NO_SAFE_DATA",
            "execute_quantum_backend_flag": False,
            "execute_quantum_simulator_flag": False,
            "execute_optimizer_flag": False,
            "real_artifact_candidate_creation_allowed_flag": record[
                "run_capable_dataset_available_flag"
            ],
            "feature_seed_candidate_only_flag": record["feature_seed_candidate_only_flag"],
            "blocker_code": record["blocker_code"],
        }
        for index, record in enumerate(feature_records, start=1)
    ]


def _quantum_blocker(
    *,
    run_capable: bool,
    seed_candidate: bool,
    mapping: dict[str, Any],
) -> str:
    if run_capable:
        return "NONE"
    if seed_candidate:
        return mapping.get("blocker_code") or c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS
    return mapping.get("blocker_code") or "QUANTUM_BLOCKED_NO_SAFE_DATA"
