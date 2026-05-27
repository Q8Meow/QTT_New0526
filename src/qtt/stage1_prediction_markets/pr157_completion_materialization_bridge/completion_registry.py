"""Top-level PR157 artifact construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .atomicrows_4183_completion import (
    aggregate_report as atomicrows_aggregate_report,
    build_atomicrow_records,
)
from .input_discovery import load_jsonl_rows, pr154_records
from .models import BuildArtifacts
from .orchestration_preflight import (
    input_consumption_receipts,
    orchestration_alignment_receipt,
    preflight_failures,
)
from .owner_input_request import build_owner_request_packet
from .pr154_completion import (
    aggregate_report as pr154_aggregate_report,
    build_pr154_records,
    count_invariant_receipt,
)


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
        "wall_clock_timestamps_used": False,
        "runtime_git_branch_or_head_used": False,
        "random_values_used": False,
        "local_absolute_paths_used": False,
        "stable_pr154_sort_key": ["target_id"],
        "stable_atomicrows_sort_key": ["row_id_or_row_ref"],
    }


def _atomicrows_shards(records: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    shards: list[dict[str, Any]] = []
    for start in range(0, len(records), c.ATOMICROWS_SHARD_SIZE):
        shard_records = records[start : start + c.ATOMICROWS_SHARD_SIZE]
        shard_index = len(shards) + 1
        shard_id = f"PR157_ATOMICROWS_COMPLETION_SHARD_{shard_index:04d}"
        shard_path = (
            c.ATOMICROWS_SHARD_DIR
            / f"PR157_AtomicRows4183CompletionMaterialization.shard_{shard_index:04d}.json"
        )
        shards.append(
            {
                "shard_id": shard_id,
                "shard_path": shard_path.as_posix(),
                "row_count": len(shard_records),
                "first_row_id": shard_records[0]["row_id_or_row_ref"],
                "last_row_id": shard_records[-1]["row_id_or_row_ref"],
                "records": shard_records,
            }
        )
    return tuple(shards)


def _shard_manifest(shards: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    return [
        {
            "shard_id": shard["shard_id"],
            "shard_path": shard["shard_path"],
            "row_count": shard["row_count"],
            "first_row_id": shard["first_row_id"],
            "last_row_id": shard["last_row_id"],
        }
        for shard in shards
    ]


def build_artifacts(repo_root: Path | str) -> BuildArtifacts:
    root = Path(repo_root).resolve()
    receipts = input_consumption_receipts(root)
    failures = list(preflight_failures(receipts))
    upstream_pr154_records = pr154_records(root)
    pr154_count_receipt = count_invariant_receipt(upstream_pr154_records)
    if not pr154_count_receipt["count_invariants_passed_flag"]:
        failures.append("PR157_BLOCKED_COUNT_INVARIANT_FAILURE")
    exact_rows = load_jsonl_rows(root)
    if len(exact_rows) != c.EXPECTED_ATOMICROWS_TOTAL:
        failures.append("PR157_BLOCKED_COUNT_INVARIANT_FAILURE:ATOMICROWS_4183")

    pr154_bridge_records = build_pr154_records(upstream_pr154_records)
    atomicrow_bridge_records = build_atomicrow_records(exact_rows)
    owner_request_packet = build_owner_request_packet(
        pr154_bridge_records,
        atomicrow_bridge_records,
    )
    atomicrow_shards = _atomicrows_shards(atomicrow_bridge_records)
    shard_manifest = _shard_manifest(atomicrow_shards)
    atomic_report_counts = atomicrows_aggregate_report(atomicrow_bridge_records)
    if not atomic_report_counts["count_reconciliation_passed_flag"]:
        failures.append("PR157_BLOCKED_COUNT_INVARIANT_FAILURE:ATOMICROWS_CLASSIFICATION")
    failures_tuple = tuple(sorted(set(failures)))
    validation = _validation_result(failures_tuple)
    alignment = orchestration_alignment_receipt(receipts)
    common = {
        "pr_id": c.PR_ID,
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "implementation_class": c.IMPLEMENTATION_CLASS,
        "authority_class": c.AUTHORITY_CLASS,
        "input_consumption_receipt": receipts,
        "orchestration_alignment_receipt": alignment,
        "count_invariant_receipt": pr154_count_receipt,
        "determinism_receipt": _determinism_receipt(),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "validation_result": validation,
    }
    pr154_registry = {
        "registry_type": "PR157_PR154_COMPLETION_BRIDGE_REGISTRY",
        **common,
        "records": pr154_bridge_records,
        "record_count": len(pr154_bridge_records),
    }
    pr154_report = {
        "report_type": "PR157_PR154_COMPLETION_BRIDGE_REPORT",
        **common,
        **pr154_aggregate_report(pr154_bridge_records),
        "owner_request_packet_path": c.OWNER_REQUEST_PATH.as_posix(),
        "generated_registry_path": c.PR154_REGISTRY_PATH.as_posix(),
        "generated_report_path": c.PR154_REPORT_PATH.as_posix(),
    }
    atomicrows_registry = {
        "registry_type": "PR157_ATOMICROWS_4183_COMPLETION_MATERIALIZATION_REGISTRY",
        **common,
        "source_requirement_class_counts": atomic_report_counts[
            "source_requirement_class_counts"
        ],
        "records": [],
        "records_are_sharded": True,
        "shards": shard_manifest,
        "record_count": len(atomicrow_bridge_records),
    }
    atomicrows_report = {
        "report_type": "PR157_ATOMICROWS_4183_COMPLETION_MATERIALIZATION_REPORT",
        **common,
        **atomic_report_counts,
        "owner_request_packet_path": c.OWNER_REQUEST_PATH.as_posix(),
        "generated_registry_path": c.ATOMICROWS_REGISTRY_PATH.as_posix(),
        "generated_report_path": c.ATOMICROWS_REPORT_PATH.as_posix(),
        "shards": shard_manifest,
    }
    return BuildArtifacts(
        pr154_registry=pr154_registry,
        pr154_report=pr154_report,
        atomicrows_registry=atomicrows_registry,
        atomicrows_report=atomicrows_report,
        owner_request_packet=owner_request_packet,
        atomicrows_shards=atomicrow_shards,
    )
