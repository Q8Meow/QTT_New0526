#!/usr/bin/env python3
"""Report and shard IO for PR168-RP3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from tools.pr168_rp3_config import (
    CREATED_AT_UTC,
    GENERATED_ROOT,
    REPORT_ALIASES,
    REPORT_VERSION,
    SHARD_ROOT,
    TOOL_NAME,
    generated_ref,
    report_path,
    route_defaults,
    shard_path,
)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_report_file(filename: str) -> dict[str, Any]:
    return read_json(GENERATED_ROOT / filename)


def load_report(report_id: str) -> dict[str, Any]:
    return read_json(report_path(report_id))


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    materialized = [dict(row) for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in materialized:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n")
    return materialized


def row_ref(row: Mapping[str, Any]) -> str:
    for key in (
        "formula_id",
        "input_lock_id",
        "market_instantiation_id",
        "formula_exec_receipt_id",
        "replay_row_id",
        "paper_row_id",
        "tca_row_id",
        "scenario_id",
        "rank2_evidence_row_id",
        "stack_id",
        "negative_recovery_id",
        "quantum_stack_row_id",
        "operator_action_id",
        "row_id",
    ):
        value = row.get(key)
        if value:
            return str(value)
    return "unidentified_row"


def write_shard(key: str, rows: Iterable[Mapping[str, Any]], *, logical_family_id: str) -> dict[str, Any]:
    path = shard_path(key)
    materialized = write_jsonl(path, rows)
    manifest_path = path.with_suffix(".manifest.json")
    manifest = {
        "manifest_id": f"{logical_family_id}_Manifest",
        "logical_shard_family_id": logical_family_id,
        "physical_filename": generated_ref(manifest_path),
        "shard_path": generated_ref(path),
        "row_count": len(materialized),
        "row_refs": [row_ref(row) for row in materialized],
        "short_physical_shard_root": generated_ref(SHARD_ROOT),
        **route_defaults(
            "agent",
            upstream_refs=[logical_family_id],
            row_shard_refs=[generated_ref(path)],
            authority_class="REPLAY_PAPER_CANDIDATE_NON_PROOF",
        ),
    }
    write_json(manifest_path, manifest)
    return manifest


def report_payload(
    report_id: str,
    records: Any,
    *,
    route_key: str = "agent",
    upstream_refs: list[str] | None = None,
    map3_refs: list[str] | None = None,
    rp2_refs: list[str] | None = None,
    gfp2r_refs: list[str] | None = None,
    data1a_refs: list[str] | None = None,
    data1_refs: list[str] | None = None,
    formula_refs: list[str] | None = None,
    formula_contract_refs: list[str] | None = None,
    qku_refs: list[str] | None = None,
    order_intent_refs: list[str] | None = None,
    replay_refs: list[str] | None = None,
    paper_refs: list[str] | None = None,
    scenario_refs: list[str] | None = None,
    tca_refs: list[str] | None = None,
    no_trade_refs: list[str] | None = None,
    quantum_refs: list[str] | None = None,
    computed_from_refs: list[str] | None = None,
    row_shard_refs: list[str] | None = None,
    numeric_evidence_refs: list[str] | None = None,
    market_instantiation_refs: list[str] | None = None,
    stack_refs: list[str] | None = None,
    contribution_refs: list[str] | None = None,
    recovery_refs: list[str] | None = None,
    formula_quality_refs: list[str] | None = None,
    authority_class: str = "REPLAY_PAPER_CANDIDATE_NON_PROOF",
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
    repair_route_if_gap: str | None = None,
) -> dict[str, Any]:
    physical = REPORT_ALIASES[report_id]
    return {
        "logical_report_id": report_id,
        "physical_filename": physical,
        "alias_registry_ref": "docs/master_plan/generated/PR168_RP3_FileAliases.report.json",
        "path_audit_ref": "docs/master_plan/generated/PR168_RP3_PathAudit.report.json",
        "report_version": REPORT_VERSION,
        "created_by_tool": TOOL_NAME,
        "created_at_utc": CREATED_AT_UTC,
        "records": records,
        **route_defaults(
            route_key,
            upstream_refs=upstream_refs,
            map3_refs=map3_refs,
            rp2_refs=rp2_refs,
            gfp2r_refs=gfp2r_refs,
            data1a_refs=data1a_refs,
            data1_refs=data1_refs,
            formula_refs=formula_refs,
            formula_contract_refs=formula_contract_refs,
            qku_refs=qku_refs,
            order_intent_refs=order_intent_refs,
            replay_refs=replay_refs,
            paper_refs=paper_refs,
            scenario_refs=scenario_refs,
            tca_refs=tca_refs,
            no_trade_refs=no_trade_refs,
            quantum_refs=quantum_refs,
            computed_from_refs=computed_from_refs,
            row_shard_refs=row_shard_refs,
            numeric_evidence_refs=numeric_evidence_refs,
            market_instantiation_refs=market_instantiation_refs,
            stack_refs=stack_refs,
            contribution_refs=contribution_refs,
            recovery_refs=recovery_refs,
            formula_quality_refs=formula_quality_refs,
            authority_class=authority_class,
            terminal_by_nature_flag=terminal_by_nature_flag,
            terminal_reason_code=terminal_reason_code,
            repair_route_if_gap=repair_route_if_gap,
        ),
    }


def write_report(report_id: str, records: Any, **kwargs: Any) -> dict[str, Any]:
    payload = report_payload(report_id, records, **kwargs)
    write_json(report_path(report_id), payload)
    return payload


def report_records(report_id: str) -> Any:
    return load_report(report_id)["records"]
