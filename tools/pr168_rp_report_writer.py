#!/usr/bin/env python3
"""Report IO helpers for PR168-RP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr168_rp_shards"
SHARD_SIZE = 1000


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_report(repo_root: Path, filename: str) -> dict[str, Any]:
    path = repo_root / GENERATED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(path)
    return read_json(path)


def read_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    report = read_report(repo_root, filename)
    shard_files = report.get("summary", {}).get("shard_files") or report.get("shard_files") or report.get("shard_paths") or []
    if not shard_files:
        return list(report.get("records", []))
    rows: list[dict[str, Any]] = []
    for shard_file in shard_files:
        shard_path = repo_root / str(shard_file)
        if not shard_path.exists():
            raise FileNotFoundError(shard_path)
        rows.extend(read_json(shard_path).get("records", []))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False)
    path.write_text(text + "\n", encoding="utf-8")


def base_report(
    report_type: str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    *,
    consumer: str,
    downstream_route: str,
) -> dict[str, Any]:
    return {
        "pr_id": "PR168-RP",
        "report_type": report_type,
        "producer": "PR168_RP_FORMULA_BASED_REPLAY_PAPER_RECOMPUTE",
        "consumer": consumer,
        "upstream_source": "PR168-GFP truth overlay plus repo replay-paper evidence candidates",
        "downstream_route": downstream_route,
        "owning_agent": "Replay Paper Recompute Agent",
        "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        "authority_boundary_codes": [
            "NO_LIVE_ORDER_AUTHORITY",
            "NO_SOURCE_TRUTH_AUTHORITY",
            "NO_CONNECTOR_TRUTH_OR_BINDING",
            "NO_PRIVATE_STATE_OR_CASH",
            "NO_QUANTUM_BACKEND_EXECUTION",
            "NO_LLM_HOT_PATH_AUTHORITY",
            "NO_QTT_DIGEST_AUTHORITY",
            "NO_ATOMICROWS_DIGEST_AUTHORITY",
        ],
        "source_truth_authority": False,
        "connector_truth_authority": False,
        "connector_semantic_binding_created": False,
        "live_authority": False,
        "order_authority": False,
        "private_state_read_count": 0,
        "runtime_cash_receipt_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "llm_hot_path_authority": False,
        "generated_digest_authority_created": False,
        "summary": summary,
        "record_count": len(records),
        "records": records,
    }


def write_report(
    repo_root: Path,
    filename: str,
    records: list[dict[str, Any]],
    *,
    report_type: str | None = None,
    summary: dict[str, Any] | None = None,
    consumer: str = "PR168-RANK",
    downstream_route: str = "PR168-RANK",
    shard: bool = False,
) -> None:
    report_type = report_type or Path(filename).stem.upper()
    summary = dict(summary or {})
    _remove_stale_shards(repo_root, filename)
    if shard:
        shard_files: list[str] = []
        for index, start in enumerate(range(0, len(records), SHARD_SIZE), start=1):
            shard_records = records[start : start + SHARD_SIZE]
            shard_name = f"{Path(filename).stem}.part_{index:04d}_of_{{total}}.report.json"
            shard_files.append(shard_name)
            payload = base_report(
                f"{report_type}_SHARD",
                shard_records,
                {"parent_report": filename, "shard_index": index, "record_count": len(shard_records)},
                consumer=consumer,
                downstream_route=downstream_route,
            )
            write_json(repo_root / SHARD_DIR / shard_name, payload)
        total = len(shard_files)
        resolved_files: list[str] = []
        for index, old_name in enumerate(shard_files, start=1):
            new_name = old_name.replace("{total}", f"{total:04d}")
            old_path = repo_root / SHARD_DIR / old_name
            new_path = repo_root / SHARD_DIR / new_name
            if old_path != new_path:
                old_path.replace(new_path)
            resolved_files.append((SHARD_DIR / new_name).as_posix())
        summary.update(
            {
                "record_count": len(records),
                "preview_record_count": min(5, len(records)),
                "records_omitted_for_sharding_flag": len(records) > 5,
                "sharded_flag": True,
                "shard_count": total,
                "shard_files": resolved_files,
            }
        )
        root_records = records[:5]
    else:
        summary.update({"record_count": len(records), "sharded_flag": False})
        root_records = records
    payload = base_report(report_type, root_records, summary, consumer=consumer, downstream_route=downstream_route)
    payload["record_count"] = len(records)
    write_json(repo_root / GENERATED_DIR / filename, payload)


def _remove_stale_shards(repo_root: Path, filename: str) -> None:
    prefix = Path(filename).stem
    shard_dir = repo_root / SHARD_DIR
    if not shard_dir.exists():
        return
    for shard_path in shard_dir.glob(f"{prefix}.part_*.report.json"):
        if shard_path.is_file():
            shard_path.unlink()


def pointer_row(
    source: dict[str, Any],
    *,
    report_ref: str,
    result_ref: str,
    evidence_tier: str,
    computed_status: str,
    downstream_route: str,
) -> dict[str, Any]:
    return {
        "canonical_row_key": source.get("canonical_row_key"),
        "qku_id": source.get("qku_id"),
        "row_family": source.get("row_family"),
        "upstream_report": source.get("upstream_report") or source.get("upstream_file_ref"),
        "upstream_row_ref": source.get("upstream_row_ref"),
        "formula_id": source.get("formula_id"),
        "required_formula_set_id": source.get("required_formula_set_id"),
        "input_ref": source.get("input_ref"),
        "output_ref": source.get("output_ref"),
        "result_ref": result_ref,
        "evidence_tier": evidence_tier,
        "computed_status": computed_status,
        "edge_attribution_ref": source.get("edge_attribution_ref"),
        "negative_recovery_ref": source.get("negative_recovery_ref"),
        "owning_agent": source.get("owning_agent", "Replay Paper Recompute Agent"),
        "supporting_agents": source.get("supporting_agents", ["Risk Manager Agent", "Governance Agent"]),
        "downstream_agent": source.get("downstream_agent", "Ranking Agent"),
        "downstream_pr": source.get("downstream_pr", "PR168-RANK"),
        "connector_candidate_route": source.get("connector_candidate_route"),
        "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
        "downstream_route": downstream_route,
        "dashboard_visibility": True,
        "commander_visibility": True,
        "governance_visibility": True,
        "producer": "PR168_RP_FORMULA_BASED_REPLAY_PAPER_RECOMPUTE",
        "consumer": report_ref,
        "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
    }
