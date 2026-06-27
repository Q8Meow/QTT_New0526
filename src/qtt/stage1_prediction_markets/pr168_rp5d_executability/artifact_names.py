"""Artifact name registry construction for PR168-RP5D."""

from __future__ import annotations

from typing import Iterable

from .models import (
    BLOCKER_POLICY_REF,
    COMPACT_NAME_SEMANTICS,
    EXECUTION_AUTHORITY_REF,
    OLD_TO_COMPACT_NAME,
    all_artifact_filenames,
)
from .path_safety import path_safety_record


def abbreviation_explanation(filename: str) -> str:
    if "qobj" in filename:
        return "qobj abbreviates quantum objective; canonical compact RP5D artifact name."
    if "compat" in filename:
        return "compat abbreviates compatibility; canonical compact RP5D artifact name."
    if "rank" in filename:
        return "rank abbreviates execution-adjusted ranking readiness; canonical compact RP5D artifact name."
    if "fb" in filename:
        return "fb abbreviates fallback; canonical compact RP5D artifact name."
    if "var" in filename:
        return "var abbreviates future trade variable contract readiness; canonical compact RP5D artifact name."
    return "rp5d prefix identifies PR168-RP5D; filename is the canonical compact artifact name."


def full_semantic_name(filename: str) -> str:
    if filename in COMPACT_NAME_SEMANTICS:
        return COMPACT_NAME_SEMANTICS[filename]
    if filename.endswith(".manifest.json"):
        base = filename.replace(".manifest.json", ".jsonl")
        return f"Manifest for {COMPACT_NAME_SEMANTICS.get(base, base)}"
    return filename.replace("_", " ").replace(".jsonl", "").replace(".json", "").replace(".report", "")


def old_long_name_for(filename: str) -> str | None:
    for old_name, compact in OLD_TO_COMPACT_NAME.items():
        if compact == filename:
            return old_name
    return None


def artifact_family(filename: str) -> str:
    if filename.endswith(".manifest.json"):
        return "manifest"
    if "queue" in filename:
        return "adapter_queue"
    if "readiness" in filename:
        return "readiness_ledger"
    if "handoff" in filename:
        return "future_handoff"
    if "registry" in filename:
        return "central_registry"
    if "coverage" in filename:
        return "coverage_ledger"
    if "quantum" in filename or "qobj" in filename:
        return "quantum_readiness"
    if filename.endswith(".report.json"):
        return "report"
    return "ledger"


def schema_contract_ref(filename: str) -> str:
    stem = filename.replace(".manifest", "").replace(".report", "").replace(".jsonl", "").replace(".json", "")
    return "".join(part.capitalize() for part in stem.split("_") if part) + "V1"


def build_artifact_name_entries(filenames: Iterable[str] | None = None) -> list[dict[str, object]]:
    names = tuple(dict.fromkeys(filenames or all_artifact_filenames()))
    rows: list[dict[str, object]] = []
    for filename in sorted(names, key=lambda item: (item.casefold(), item)):
        safety = path_safety_record(filename)
        rows.append(
            {
                **safety,
                "artifact_family": artifact_family(filename),
                "full_semantic_name": full_semantic_name(filename),
                "schema_contract_ref": schema_contract_ref(filename),
                "producer_agent": "ArtifactNameAgent" if filename == "rp5d_artifact_name_registry.json" else "RP5DGeneratedArtifactProducer",
                "primary_consumer_agent_refs": ["GovernanceAgent", "PathSafetyAgent", "RP5DValidator"],
                "future_consumer_pr_refs": ["RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "LIVE-DRYRUN"],
                "old_long_name_if_applicable": old_long_name_for(filename),
                "abbreviation_explanation": abbreviation_explanation(filename),
                "execution_authority_ref": EXECUTION_AUTHORITY_REF,
                "blocker_policy_ref": BLOCKER_POLICY_REF,
            }
        )
    return rows
