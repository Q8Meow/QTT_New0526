"""Artifact name registry construction for RP5E compact outputs."""

from __future__ import annotations

from typing import Iterable

from .models import all_artifact_filenames, schema_name
from .path_safety import path_safety_record


LOGICAL_NAMES = {
    "art_reg.json": "StackArtifactNameRegistryV1",
    "ctx_univ.jsonl": "ContextCandidateUniverseSelectorV1",
    "ctx_pools.jsonl": "ContextFormulaPoolSelectorV1",
    "qku_guard.jsonl": "QKUComputabilityGuardLedgerV1",
    "tmp_previews.jsonl": "StackCandidatePreviewV1 temporary preview dump",
    "topk.jsonl": "StackCandidatePreviewV1 retained top-K previews",
    "features.jsonl": "StackFeatureVectorLedgerV1",
    "edge_feats.jsonl": "EdgeCaptureFeatureLedgerV1",
    "exec_prev.jsonl": "ExecutionAdjustedStackPreviewLedgerV1",
    "q_obj.jsonl": "StackQuantumStructuralReadinessLedgerV1",
    "unlock_pri.jsonl": "ExecutableUnlockPriorityLedgerV1",
    "mode_boundary.jsonl": "RuntimeModeBoundaryLedgerV1",
    "exec_auth.report.json": "RP5E execution authority boundary report",
    "run_receipt.report.json": "StackGeneratorRunReceiptV1",
}


def artifact_family(filename: str) -> str:
    if filename.endswith(".manifest.json"):
        return "manifest"
    if filename.endswith(".report.json"):
        return "summary_report"
    if filename in {"art_reg.json"}:
        return "artifact_registry"
    if filename.startswith("to_") or filename in {"downstream.jsonl", "future.report.json", "re_handoff.report.json"}:
        return "future_handoff"
    if filename in {"artifact_io.jsonl", "file_route.jsonl", "dag.jsonl", "lineage.jsonl", "val_lineage.jsonl"}:
        return "routing_lineage"
    if filename.startswith("q_") or filename == "classic.jsonl":
        return "quantum_classical_structure"
    if filename in {"unlock_pri.jsonl", "gap_rank.jsonl", "triage52.jsonl", "queue_dedupe.jsonl"}:
        return "unlock_plan"
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
                "abbreviation_explanation": "RP5E compact filename mapped by art_reg.json to the logical artifact contract.",
                "primary_consumer_agent_refs": ["GovernanceAgent", "RP5EValidator", "ArtifactRouteAgent"],
                "future_consumer_pr_refs": ["RP5F", "RP5G", "RANK4", "QOPT1", "VS2", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "LIVE-DRYRUN", "TRIGGERED-SHADOW-COMPARISON"],
            }
        )
    return rows
