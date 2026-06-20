#!/usr/bin/env python3
"""Report IO helpers for PR168-RANK."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr168_rank_shards"
SHARD_SIZE = 1000

AUTHORITY_BOUNDARY_CODES = [
    "NO_LIVE_ORDER_AUTHORITY",
    "NO_SOURCE_TRUTH_AUTHORITY",
    "NO_CONNECTOR_TRUTH_OR_BINDING",
    "NO_PRIVATE_STATE_OR_CASH",
    "NO_QUANTUM_BACKEND_EXECUTION",
    "NO_QTT_DIGEST_AUTHORITY",
    "NO_ATOMICROWS_DIGEST_AUTHORITY",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    path.write_text(text + "\n", encoding="utf-8")


def read_report(repo_root: Path, filename: str) -> dict[str, Any]:
    path = repo_root / GENERATED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(path)
    return read_json(path)


def read_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    report = read_report(repo_root, filename)
    shard_files = report.get("summary", {}).get("shard_files") or report.get("shard_files") or []
    if not shard_files:
        return list(report.get("records", []))
    rows: list[dict[str, Any]] = []
    for shard_file in shard_files:
        shard_path = repo_root / str(shard_file)
        if not shard_path.exists():
            raise FileNotFoundError(shard_path)
        rows.extend(read_json(shard_path).get("records", []))
    return rows


def base_report(
    report_type: str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    *,
    consumer: str,
    downstream_route: str,
) -> dict[str, Any]:
    return {
        "pr_id": "PR168-RANK",
        "report_type": report_type,
        "producer": "PR168_RANK_EVIDENCE_BACKED_RANKING",
        "consumer": consumer,
        "upstream_source": "PR168-RP computed replay/paper handoff reports",
        "downstream_route": downstream_route,
        "owning_agent": "RankingAgent",
        "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        "materialized_artifact": True,
        "authority_boundary_codes": AUTHORITY_BOUNDARY_CODES,
        "source_truth_authority": False,
        "connector_truth_authority": False,
        "connector_semantic_binding_created": False,
        "live_authority": False,
        "order_authority": False,
        "private_state_read_count": 0,
        "runtime_cash_receipt_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "generated_digest_authority_created": False,
        "qtt_sha_authority_created": False,
        "atomicrows_hash_authority_created": False,
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
    shard: bool | None = None,
) -> None:
    report_type = report_type or Path(filename).stem.upper()
    summary = dict(summary or {})
    _remove_stale_shards(repo_root, filename)
    use_shards = len(records) > SHARD_SIZE if shard is None else shard
    if use_shards:
        shard_files: list[str] = []
        total = max(1, (len(records) + SHARD_SIZE - 1) // SHARD_SIZE)
        for index, start in enumerate(range(0, len(records), SHARD_SIZE), start=1):
            shard_records = records[start : start + SHARD_SIZE]
            shard_name = f"{Path(filename).stem}.part_{index:04d}_of_{total:04d}.report.json"
            shard_files.append((SHARD_DIR / shard_name).as_posix())
            payload = base_report(
                f"{report_type}_SHARD",
                shard_records,
                {
                    "parent_report": filename,
                    "shard_index": index,
                    "shard_count": total,
                    "record_count": len(shard_records),
                },
                consumer=consumer,
                downstream_route=downstream_route,
            )
            write_json(repo_root / SHARD_DIR / shard_name, payload)
        summary.update(
            {
                "record_count": len(records),
                "preview_record_count": min(5, len(records)),
                "records_omitted_for_sharding_flag": len(records) > 5,
                "sharded_flag": True,
                "shard_count": total,
                "shard_files": shard_files,
            }
        )
        root_records = records[:5]
    else:
        summary.update({"record_count": len(records), "sharded_flag": False})
        root_records = records
    payload = base_report(report_type, root_records, summary, consumer=consumer, downstream_route=downstream_route)
    payload["record_count"] = len(records)
    write_json(repo_root / GENERATED_DIR / filename, payload)


def no_orphan_defaults(row: dict[str, Any], filename: str) -> dict[str, Any]:
    normalized = dict(row)
    normalized.setdefault("producer", "PR168_RANK_EVIDENCE_BACKED_RANKING")
    normalized.setdefault("consumer", _consumer_for(filename))
    normalized.setdefault("upstream_source", "PR168_RP_To_PR168_RANK handoff reports")
    normalized.setdefault("downstream_route", _route_for_report(filename))
    normalized.setdefault("owning_agent", "RankingAgent")
    normalized.setdefault("supporting_agents", ["RiskAgent", "ExecutionCostAgent", "GovernanceAgent"])
    normalized.setdefault("downstream_consumers", [_consumer_for(filename)])
    normalized.setdefault("downstream_pr_refs", [_route_for_report(filename)])
    normalized.setdefault("validator_refs", [f"tools/validate_pr168_rank_{_validator_slug(filename)}.py"])
    normalized.setdefault("test_refs", [f"tests/pr168_rank/test_{_validator_slug(filename)}.py"])
    normalized.setdefault("no_orphan_status", "CONNECTED_TO_DECLARED_CONSUMER")
    normalized.setdefault("manual_edit_allowed_flag", False)
    normalized.setdefault("authority_boundary_flags", authority_flags())
    return normalized


def authority_flags() -> dict[str, bool]:
    return {
        "source_truth_authority": False,
        "connector_semantic_binding": False,
        "private_state_required_flag": False,
        "cash_required_flag": False,
        "order_authority_required_flag": False,
        "live_execution_allowed_flag": False,
        "quantum_backend_required_flag": False,
        "quantum_advantage_claim_flag": False,
        "qtt_sha_authority_flag": False,
        "atomicrows_hash_authority_flag": False,
    }


def _remove_stale_shards(repo_root: Path, filename: str) -> None:
    prefix = Path(filename).stem
    shard_dir = repo_root / SHARD_DIR
    if not shard_dir.exists():
        return
    for shard_path in shard_dir.glob(f"{prefix}.part_*.report.json"):
        if shard_path.is_file():
            shard_path.unlink()


def _consumer_for(filename: str) -> str:
    if "_To_PR162E_Q_" in filename or "Quantum" in filename:
        return "QuantumMapperAgent"
    if "_To_PR166_QC_R2_" in filename:
        return "QuantumComparatorAgent"
    if "_To_PR165B_" in filename or "Negative" in filename or "TrueNegative" in filename:
        return "GovernanceAgent"
    if "OwnerDashboard" in filename:
        return "DashboardAgent"
    if "ExecutionRouter" in filename:
        return "OwnerReviewAgent"
    if "Connector" in filename:
        return "ConnectorCandidateAgent"
    if "Registry" in filename:
        return "GovernanceAgent"
    return "RankingAgent"


def _route_for_report(filename: str) -> str:
    if "_To_" in filename:
        return filename.removeprefix("PR168_RANK_To_").removesuffix(".report.json")
    if "Registry" in filename:
        return "central_future_expansion_registry_layer"
    return filename


def _validator_slug(filename: str) -> str:
    stem = Path(filename).stem
    if stem.startswith("PR168_RANK_"):
        stem = stem.removeprefix("PR168_RANK_")
    stem = stem.replace(".report", "")
    return stem.lower()
