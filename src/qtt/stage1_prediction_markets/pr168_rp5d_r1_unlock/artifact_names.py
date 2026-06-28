"""Artifact registry construction for RP5D-R1 compact overlay outputs."""

from __future__ import annotations

from typing import Iterable

from .models import all_artifact_filenames, schema_name
from .path_safety import path_safety_record


LOGICAL_NAMES = {
    "art_reg.json": "RP5D_R1_ArtifactNameRegistryV1",
    "exec_now_proof.jsonl": "ReplayPaperExecutableNowProofV1",
    "tier_overlay.jsonl": "TierOverlayDeltaLedgerV1",
    "count_integrity.jsonl": "CountIntegrityAuditLedgerV1",
    "contract_matrix.jsonl": "ContractCompletenessMatrixV1",
    "calc_smoke.jsonl": "CalculationSmokeTestLedgerV1",
    "edge_profit_map.jsonl": "EdgeProfitContributionMapV1",
    "run_receipt.report.json": "RP5D_R1_RunReceiptV1",
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
    if filename.startswith("q_") or filename == "classic_exec.jsonl":
        return "quantum_classical_carry"
    if filename in {"unlock_select.jsonl", "unlock_plan.jsonl", "contract_patch.jsonl"}:
        return "execution_contract_completion"
    if filename in {"promote.jsonl", "nonpromote.jsonl", "tier_delta.jsonl", "tier_overlay.jsonl"}:
        return "overlay_delta"
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
                "abbreviation_explanation": "RP5D-R1 compact filename mapped by art_reg.json to the overlay artifact contract.",
                "primary_consumer_agent_refs": ["GovernanceAgent", "ExecutabilityAgent", "RP5D_R1Validator"],
                "future_consumer_pr_refs": ["RP5F", "RP5G", "RANK4", "QOPT1", "VS2", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "PR170-LIVE-DRYRUN", "TRIGGERED-SHADOW-COMPARISON"],
            }
        )
    return rows
