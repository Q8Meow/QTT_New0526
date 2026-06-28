"""Artifact registry construction for PR168-RP5F compact outputs."""

from __future__ import annotations

from typing import Iterable

from .models import all_artifact_filenames, schema_name
from .path_safety import path_safety_record

LOGICAL_NAMES = {
    "art_reg.json": "RP5FArtifactNameRegistryV1",
    "snap_ctx.jsonl": "MarketSnapshotContextV1",
    "targets.jsonl": "DynamicTradeTargetV1",
    "var_grid.jsonl": "EphemeralOrderVariableGridV1",
    "trade_seed.jsonl": "SnapshotConditionedTradePlanSeedV1",
    "edge_capture_map.jsonl": "OwnerEdgeCaptureMapV1",
    "run_receipt.report.json": "RP5FRunReceiptV1",
}


def artifact_family(filename: str) -> str:
    if filename.endswith(".manifest.json"):
        return "manifest"
    if filename.endswith(".report.json"):
        return "summary_report"
    if filename == "art_reg.json":
        return "artifact_registry"
    if filename.startswith("to_") or filename in {"downstream.jsonl", "future.report.json"}:
        return "future_handoff"
    if filename in {"artifact_io.jsonl", "file_route.jsonl", "dag.jsonl", "lineage.jsonl", "val_lineage.jsonl"}:
        return "routing_lineage"
    if filename.startswith("q_") or filename == "classic_fallback.jsonl":
        return "quantum_classical_structure"
    if filename in {"stale_rules.jsonl", "snapshot_reval.jsonl", "pre_submit_reval.jsonl", "no_stale_candidate.jsonl"}:
        return "freshness_revalidation"
    if filename in {"pm_edge_hints.jsonl", "yes_no_parity.jsonl", "cross_venue_hints.jsonl", "orderbook_imbalance.jsonl", "liquidity_decay.jsonl", "event_news_hints.jsonl"}:
        return "prediction_market_edge_inputs"
    if filename in {"tca_inputs.jsonl", "fill_inputs.jsonl", "queue_fill_inputs.jsonl", "adverse_select.jsonl", "lat_inputs.jsonl", "capacity_inputs.jsonl", "cash_settle_inputs.jsonl"}:
        return "execution_realism_inputs"
    return "ledger"


def full_semantic_name(filename: str) -> str:
    if filename in LOGICAL_NAMES:
        return LOGICAL_NAMES[filename]
    if filename.endswith(".manifest.json"):
        return f"Manifest for {filename.replace('.manifest.json', '.jsonl')}"
    return filename.replace("_", " ").replace(".jsonl", "").replace(".json", "").replace(".report", "")


def build_artifact_name_entries(filenames: Iterable[str] | None = None) -> list[dict[str, object]]:
    names = tuple(dict.fromkeys(filenames or all_artifact_filenames()))
    rows: list[dict[str, object]] = []
    for filename in sorted(names, key=lambda item: (item.casefold(), item)):
        rows.append(
            {
                **path_safety_record(filename),
                "short_file": filename,
                "logical_name": full_semantic_name(filename),
                "full_semantic_name": full_semantic_name(filename),
                "artifact_family": artifact_family(filename),
                "schema_contract_ref": schema_name(filename),
                "abbreviation_explanation": "RP5F compact filename mapped by art_reg.json to the dynamic target/grid artifact contract.",
                "primary_consumer_agent_refs": ["GovernanceAgent", "TradeTargetScoutAgent", "OrderVariableAgent", "RP5FValidator"],
                "future_consumer_pr_refs": ["RP5G", "RANK4", "QOPT1", "VS2", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "PR170-LIVE-DRYRUN", "PR171-LIVE-PILOT", "TRIGGERED-SHADOW-COMPARISON"],
            }
        )
    return rows
