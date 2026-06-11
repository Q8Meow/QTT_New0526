"""Report sharding helpers for PR166-S."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import authority_absence_confirmation, authority_boundary_record, authority_zero_counts
from .central_vocab import (
    AUTHORITY_CLASS,
    DEFAULT_NO_ORPHAN_STATUS,
    DOWNSTREAM_PR_ROUTES,
    PR_ID,
    TERMINAL_NO_ORPHAN_STATUS,
    UPSTREAM_PR_REFS,
    VALIDATION_STATUS,
)
from .json_io import json_text, read_json, records_from_payload

ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024
DEFAULT_SHARD_ROW_TARGET = 1000

VOCAB_REFS = (
    "src/qtt/stage1_prediction_markets/pr166_s_replay_paper_scenario_retest_execution/central_vocab.py",
    "src/qtt/stage1_prediction_markets/pr166_s_replay_paper_scenario_retest_execution/authority_policy.py",
)

TERMINAL_REPORTS = frozenset(
    {
        "PR166_S_OptionalReplayPaperInputMissingReceipt.report.json",
        "PR166_S_AuthorityBoundaryAudit.report.json",
        "PR166_S_OrphanArtifactAudit.report.json",
        "PR166_S_TerminalArtifactReceiptRegistry.report.json",
        "PR166_S_FinalSummary.report.json",
    }
)


def encoded_json_size(payload: Any, *, compact: bool = False) -> int:
    return len(json_text(payload, compact=compact).encode("utf-8"))


def shard_rows(rows: list[dict[str, Any]], shard_size: int = DEFAULT_SHARD_ROW_TARGET) -> list[list[dict[str, Any]]]:
    if not rows:
        return []
    return [rows[index : index + shard_size] for index in range(0, len(rows), shard_size)]


def terminal_status(filename: str) -> tuple[bool, str | None]:
    if filename not in TERMINAL_REPORTS:
        return False, None
    return True, (
        "Terminal-by-nature PR166-S receipt or audit; it records bounded replay/paper-only "
        "state and routes inspection to governance/commander without creating live authority."
    )


def _base_payload(
    *,
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    report_name: str | None = None,
) -> dict[str, Any]:
    terminal_flag, terminal_reason = terminal_status(filename)
    normalized_filename = p.normalize_repo_ref(p.GENERATED_DIR / filename)
    payload = {
        "artifact_id": filename.replace(".report.json", "").upper(),
        "artifact_path": normalized_filename,
        "artifact_type": "PR166_S_ROOT_REPORT",
        "report_id": filename.replace(".report.json", "").upper(),
        "report_name": report_name or filename.replace(".report.json", ""),
        "pr_id": PR_ID,
        "report_filename": filename,
        "created_by_pr": PR_ID,
        "authority_class": AUTHORITY_CLASS,
        "authority_policy_module_ref": (
            "src.qtt.stage1_prediction_markets.pr166_s_replay_paper_scenario_retest_execution."
            "authority_policy"
        ),
        "authority_boundary": authority_boundary_record(),
        "authority_boundary_ref": authority_boundary_record()["authority_boundary_ref"],
        "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
        "validation_status": VALIDATION_STATUS,
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(UPSTREAM_PR_REFS),
        "upstream_artifact_refs": source_inputs,
        "downstream_pr_refs": list(DOWNSTREAM_PR_ROUTES),
        "downstream_artifact_refs": [
            "score_memory_refresh_PR",
            "PR166-Q",
            "PR167",
            "PR171/PR172",
        ],
        "downstream_agent_consumers": [
            "scoring_agent",
            "memory_agent",
            "tca_agent",
            "latency_agent",
            "liquidity_agent",
            "risk_agent",
            "replay_agent",
            "paper_agent",
            "repair_agent",
            "dashboard_agent",
            "governance_agent",
            "commander_agent",
        ],
        "owning_agent": "replay_agent",
        "reviewer_or_challenger_agent": "governance_agent",
        "validator_ref": "tools/validate_pr166_s_replay_paper_scenario_retest_execution.py",
        "manifest_ref": "PR166_S_ReportManifest.report.json",
        "vocab_refs": list(VOCAB_REFS),
        "no_orphan_status": TERMINAL_NO_ORPHAN_STATUS if terminal_flag else DEFAULT_NO_ORPHAN_STATUS,
        "terminal_status_flag": terminal_flag,
        "terminal_status_reason": terminal_reason,
        "record_count": len(records),
        "total_row_count": len(records),
        "sharded_flag": False,
        "shard_count": 0,
        "shard_manifest_refs": [],
        "records": records,
        **authority_zero_counts(),
    }
    return payload


def build_root_payload(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _base_payload(filename=filename, records=records, source_inputs=source_inputs)
    payload["aggregate_counts"] = aggregate_counts(records)
    payload["authority_counts"] = authority_zero_counts()
    payload["authority_absence_confirmation"] = authority_absence_confirmation()
    if extra:
        payload.update(extra)
    return payload


def build_sharded_payloads(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    report_name = filename.replace(".report.json", "")
    chunks = shard_rows(records)
    shard_payloads: dict[str, dict[str, Any]] = {}
    shard_files: list[str] = []
    shard_counts: list[int] = []
    shard_refs: list[dict[str, Any]] = []
    shard_count = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        shard_name = f"{report_name}.part_{index:04d}_of_{shard_count:04d}.report.json"
        rel_path = p.normalize_repo_ref(p.SHARD_DIR / shard_name)
        shard_payload = _base_payload(
            filename=shard_name,
            records=chunk,
            source_inputs=source_inputs,
            report_name=report_name,
        )
        shard_payload.update(
            {
                "artifact_path": rel_path,
                "artifact_type": "PR166_S_SHARD_REPORT",
                "parent_report_filename": filename,
                "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
                "part_ref": f"PR166_S_PART::{index:04d}",
                "part_index": index,
                "part_count": shard_count,
                "shard_index": index,
                "shard_count": shard_count,
                "record_count": len(chunk),
                "total_record_count": len(records),
                "total_row_count": len(records),
                "records_canonical_part_flag": True,
                "aggregate_counts": aggregate_counts(chunk),
                "authority_counts": authority_zero_counts(),
            }
        )
        shard_payloads[rel_path] = shard_payload
        shard_files.append(rel_path)
        shard_counts.append(len(chunk))
        shard_refs.append(
            {
                "part_ref": shard_payload["part_ref"],
                "shard_path": rel_path,
                "shard_index": index,
                "row_count": len(chunk),
                "estimated_shard_size_bytes": encoded_json_size(shard_payload, compact=True),
                "below_25_mib_limit": encoded_json_size(shard_payload, compact=True) <= SHARD_LIMIT_BYTES,
            }
        )
    compact_payload = _base_payload(filename=filename, records=[], source_inputs=source_inputs, report_name=report_name)
    compact_payload.update(
        {
            "record_count": len(records),
            "total_record_count": len(records),
            "total_row_count": len(records),
            "sharded_flag": True,
            "shard_count": shard_count,
            "shard_files": shard_files,
            "shard_paths": shard_files,
            "shard_manifest_refs": shard_refs,
            "shard_record_counts": shard_counts,
            "largest_shard_record_count": max(shard_counts) if shard_counts else 0,
            "records_omitted_for_sharding_flag": True,
            "full_records_only_in_shards_flag": True,
            "canonical_records_location": p.normalize_repo_ref(p.SHARD_DIR),
            "aggregate_counts": aggregate_counts(records),
            "authority_counts": authority_zero_counts(),
            "authority_absence_confirmation": authority_absence_confirmation(),
        }
    )
    return compact_payload, shard_payloads


def load_report_records(repo_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_path in payload.get("shard_files") or []:
        rows.extend(records_from_payload(read_json(p.resolve_repo_relative(repo_root, shard_path))))
    return rows


def aggregate_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counter = Counter()
    candidates: set[str] = set()
    batches: set[str] = set()
    orders: set[str] = set()
    for row in rows:
        if row.get("candidate_packet_id"):
            candidates.add(str(row["candidate_packet_id"]))
        if row.get("batch_id"):
            batches.add(str(row["batch_id"]))
        if row.get("order_intent_id"):
            orders.add(str(row["order_intent_id"]))
        for key, value in row.items():
            if key.endswith("_status") or key in {
                "run_status",
                "execution_classification",
                "post_cost_classification",
                "fill_status",
                "no_orphan_status",
                "dominant_failure_driver",
                "recommended_next_state",
            }:
                status_counter[f"{key}={value}"] += 1
    return {
        "row_count": len(rows),
        "candidate_packet_count": len(candidates),
        "batch_count": len(batches),
        "order_intent_count": len(orders),
        "status_counts": {key: status_counter[key] for key in sorted(status_counter)},
    }


def file_size_summary(repo_root: Path, report_filenames: tuple[str, ...]) -> dict[str, Any]:
    root_sizes = []
    shard_sizes = []
    for filename in report_filenames:
        root_path = repo_root / p.GENERATED_DIR / filename
        if root_path.exists():
            root_sizes.append(root_path.stat().st_size)
            payload = read_json(root_path)
            for shard_path in payload.get("shard_files") or []:
                resolved = p.resolve_repo_relative(repo_root, shard_path)
                if resolved.exists():
                    shard_sizes.append(resolved.stat().st_size)
    return {
        "root_report_count": len(root_sizes),
        "shard_report_count": len(shard_sizes),
        "largest_root_report_size_bytes": max(root_sizes) if root_sizes else 0,
        "largest_shard_report_size_bytes": max(shard_sizes) if shard_sizes else 0,
        "root_reports_below_10_mib": all(size <= ROOT_REPORT_LIMIT_BYTES for size in root_sizes),
        "shard_reports_below_25_mib": all(size <= SHARD_LIMIT_BYTES for size in shard_sizes),
    }
