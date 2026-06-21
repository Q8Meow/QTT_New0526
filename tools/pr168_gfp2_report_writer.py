#!/usr/bin/env python3
"""Report IO helpers for PR168-GFP2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.pr168_gfp2_constants import (
    AUTHORITY_CLASS,
    CONNECTED,
    CREATED_BY_TOOL,
    GENERATED_DIR,
    NO_AUTHORITY_FLAGS,
    PR_ID,
    REPORT_VERSION,
    SHARD_DIR,
    SHARD_SIZE,
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def read_report(repo_root: Path, filename: str) -> dict[str, Any]:
    path = repo_root / GENERATED_DIR / filename
    if not path.exists():
        raise FileNotFoundError(path)
    return read_json(path)


def read_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    report = read_report(repo_root, filename)
    shard_files = (
        report.get("summary", {}).get("shard_files")
        or report.get("shard_files")
        or report.get("shard_paths")
        or []
    )
    if shard_files:
        rows: list[dict[str, Any]] = []
        for shard_file in shard_files:
            shard_path = repo_root / str(shard_file)
            if not shard_path.exists():
                raise FileNotFoundError(shard_path)
            rows.extend(read_json(shard_path).get("records", []))
        return rows
    for key in ("records", "accepted_ledger_records", "per_target_materialization_records"):
        if isinstance(report.get(key), list):
            return list(report[key])
    return []


def base_report(
    report_id: str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    *,
    upstream_input_refs: list[str] | None = None,
    numeric_evidence_refs: list[str] | None = None,
    data_provenance_refs: list[str] | None = None,
    owning_agent: str = "Governance Agent",
    downstream_consumers: list[str] | None = None,
    downstream_pr_refs: list[str] | None = None,
    validator_refs: list[str] | None = None,
    test_refs: list[str] | None = None,
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
    authority_class: str = AUTHORITY_CLASS,
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "pr_id": PR_ID,
        "created_by_tool": CREATED_BY_TOOL,
        "upstream_input_refs": upstream_input_refs or [],
        "numeric_evidence_refs": numeric_evidence_refs or [],
        "data_provenance_refs": data_provenance_refs or [],
        "owning_agent": owning_agent,
        "downstream_consumers": downstream_consumers or ["PR168-RP2", "PR168-RANK2"],
        "downstream_pr_refs": downstream_pr_refs or ["PR168-RP2", "PR168-RANK2"],
        "validator_refs": validator_refs or ["tools/pr168_gfp2_validator.py"],
        "test_refs": test_refs or ["tests/pr168_gfp2"],
        "no_orphan_status": CONNECTED,
        "terminal_by_nature_flag": terminal_by_nature_flag,
        "terminal_reason_code": terminal_reason_code,
        "authority_class": authority_class,
        **NO_AUTHORITY_FLAGS,
        "summary": summary,
        "record_count": len(records),
        "records": records,
    }


def write_report(
    repo_root: Path,
    filename: str,
    records: list[dict[str, Any]],
    *,
    summary: dict[str, Any] | None = None,
    upstream_input_refs: list[str] | None = None,
    numeric_evidence_refs: list[str] | None = None,
    data_provenance_refs: list[str] | None = None,
    owning_agent: str = "Governance Agent",
    downstream_consumers: list[str] | None = None,
    downstream_pr_refs: list[str] | None = None,
    validator_refs: list[str] | None = None,
    test_refs: list[str] | None = None,
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
    authority_class: str = AUTHORITY_CLASS,
    shard: bool | None = None,
) -> Path:
    report_id = Path(filename).stem.replace(".report", "").upper()
    summary_payload = dict(summary or {})
    _remove_stale_shards(repo_root, filename)
    should_shard = len(records) > SHARD_SIZE if shard is None else shard
    root_records = records
    if should_shard:
        shard_files: list[str] = []
        total = (len(records) + SHARD_SIZE - 1) // SHARD_SIZE
        for index, start in enumerate(range(0, len(records), SHARD_SIZE), start=1):
            shard_name = f"{Path(filename).stem}.part_{index:04d}_of_{total:04d}.report.json"
            shard_rel = SHARD_DIR / shard_name
            shard_records = records[start : start + SHARD_SIZE]
            shard_payload = base_report(
                f"{report_id}_SHARD_{index:04d}",
                shard_records,
                {
                    "parent_report": filename,
                    "shard_index": index,
                    "shard_count": total,
                    "record_count": len(shard_records),
                },
                upstream_input_refs=upstream_input_refs,
                numeric_evidence_refs=numeric_evidence_refs,
                data_provenance_refs=data_provenance_refs,
                owning_agent=owning_agent,
                downstream_consumers=downstream_consumers,
                downstream_pr_refs=downstream_pr_refs,
                validator_refs=validator_refs,
                test_refs=test_refs,
                terminal_by_nature_flag=False,
                terminal_reason_code=None,
                authority_class=authority_class,
            )
            write_json(repo_root / shard_rel, shard_payload)
            shard_files.append(shard_rel.as_posix())
        summary_payload.update(
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
        summary_payload.update(
            {
                "record_count": len(records),
                "sharded_flag": False,
                "records_omitted_for_sharding_flag": False,
            }
        )
    payload = base_report(
        report_id,
        root_records,
        summary_payload,
        upstream_input_refs=upstream_input_refs,
        numeric_evidence_refs=numeric_evidence_refs,
        data_provenance_refs=data_provenance_refs,
        owning_agent=owning_agent,
        downstream_consumers=downstream_consumers,
        downstream_pr_refs=downstream_pr_refs,
        validator_refs=validator_refs,
        test_refs=test_refs,
        terminal_by_nature_flag=terminal_by_nature_flag,
        terminal_reason_code=terminal_reason_code,
        authority_class=authority_class,
    )
    payload["record_count"] = len(records)
    output_path = repo_root / GENERATED_DIR / filename
    write_json(output_path, payload)
    return output_path


def _remove_stale_shards(repo_root: Path, filename: str) -> None:
    shard_dir = repo_root / SHARD_DIR
    if not shard_dir.exists():
        return
    prefix = Path(filename).stem
    for path in shard_dir.glob(f"{prefix}.part_*.report.json"):
        if path.is_file():
            path.unlink()
