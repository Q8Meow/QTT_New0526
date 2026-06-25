#!/usr/bin/env python3
"""Active artifact registry builder for PR168-RP5B."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.pr168_rp5b_config import REPO_ROOT, generated_ref, normalize_repo_path


def _path_exists(path: str) -> bool:
    return (REPO_ROOT / path).exists()


def _prefix_exists(prefix: str) -> bool:
    normalized = prefix.rstrip("/**").rstrip("/")
    return (REPO_ROOT / normalized).exists()


def _no_orphan_status(path: str) -> str:
    if path.startswith("docs/master_plan/generated/PR168_RP5B_") or path.startswith("docs/master_plan/generated/rp5b/"):
        return "RP5B_OUTPUT_WRITTEN_BY_BUILDER"
    if path.endswith("/**"):
        return "PREFIX_EXISTS" if _prefix_exists(path) else "MISSING_PREFIX_EXACT_GAP"
    return "PATH_EXISTS" if _path_exists(path) else "MISSING_EXACT_GAP"


def _row(
    rows: list[dict[str, Any]],
    *,
    artifact_path: str,
    artifact_family: str,
    artifact_role: str,
    active_status: str,
    allowed_consumers: list[str],
    forbidden_consumers: list[str],
    replacement_artifact_refs: list[str],
    upstream_refs: list[str],
    downstream_refs: list[str],
    owning_agent_refs: list[str],
    validator_refs: list[str],
) -> None:
    rows.append(
        {
            "artifact_id": f"RP5B_ACTIVE_ARTIFACT_{len(rows) + 1:05d}",
            "artifact_path": normalize_repo_path(artifact_path),
            "artifact_family": artifact_family,
            "artifact_role": artifact_role,
            "active_status": active_status,
            "allowed_consumers": allowed_consumers,
            "forbidden_consumers": forbidden_consumers,
            "replacement_artifact_refs": replacement_artifact_refs,
            "upstream_refs": upstream_refs,
            "downstream_refs": downstream_refs,
            "owning_agent_refs": owning_agent_refs,
            "validator_refs": validator_refs,
            "no_orphan_status": _no_orphan_status(normalize_repo_path(artifact_path)),
        }
    )


def _existing_glob(pattern: str, *, limit: int = 8) -> list[str]:
    matches = sorted(generated_ref(path) for path in REPO_ROOT.glob(pattern))
    return matches[:limit]


def build_active_registry_rows(
    verification_rows: list[dict[str, Any]],
    semantic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base_forbidden = ["TRADING_DECISION_DIRECT", "RAW_LEGACY_REPORT_DECISION_AUTHORITY"]
    rp5a_inputs = [
        "docs/master_plan/generated/PR168_RP5A_FinalSummary.report.json",
        "docs/master_plan/generated/PR168_RP5A_DeleteEligibilityDraft.report.json",
        "docs/master_plan/generated/PR168_RP5A_ConsumerGraph.report.json",
        "docs/master_plan/generated/PR168_RP5A_ValidationDependencyGraph.report.json",
        "docs/master_plan/generated/PR168_RP5A_QKUFormulaIdentityDependency.report.json",
        "docs/master_plan/generated/PR168_RP5A_IdentityCustodyGraph.report.json",
        "docs/master_plan/generated/PR168_RP5A_NoDeletionProof.report.json",
        "docs/master_plan/generated/PR168_RP5A_FutureRP5BPlan.report.json",
        "docs/master_plan/generated/rp5a/delete_eligibility_rows.jsonl",
        "docs/master_plan/generated/rp5a/identity_custody_rows.jsonl",
    ]
    for path in rp5a_inputs:
        _row(
            rows,
            artifact_path=path,
            artifact_family="RP5A_AUDIT_INPUT",
            artifact_role="Historical audit evidence for RP5B/RP5C/RP5D routing",
            active_status="ACTIVE_TRANSITIONAL",
            allowed_consumers=["PR168_RP5B", "PR168_RP5C", "PR168_RP5D"],
            forbidden_consumers=base_forbidden,
            replacement_artifact_refs=["docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json"],
            upstream_refs=["PR168_RP5A"],
            downstream_refs=["PR168_RP5B", "PR168_RP5C", "PR168_RP5D"],
            owning_agent_refs=["QTT_ARCHITECTURE_CLEANUP_AGENT"],
            validator_refs=["tools/validate_pr168_rp5b_active_registry_safe_cleanup.py"],
        )

    for path in (
        "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
        "docs/master_plan/generated/PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json",
    ):
        _row(
            rows,
            artifact_path=path,
            artifact_family="AGENT_ROUTE_CROSSWALK",
            artifact_role="Active agent duty and QKU/formula route preservation source",
            active_status="ACTIVE_CANONICAL",
            allowed_consumers=["ActiveArtifactRegistryV1", "PR168_RP5C", "PR168_RP5D", "PR168_RP5E"],
            forbidden_consumers=base_forbidden,
            replacement_artifact_refs=[],
            upstream_refs=["PR165_D2"],
            downstream_refs=["PR168_RP5B", "PR168_RP5C", "PR168_RP5D", "PR168_RP5E"],
            owning_agent_refs=["AGENT_ROUTE_PRESERVATION"],
            validator_refs=["tools/validate_pr168_rp5b_active_registry_safe_cleanup.py"],
        )

    for path in (
        "tools/run_validation_gates.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
    ):
        _row(
            rows,
            artifact_path=path,
            artifact_family="VALIDATION_INFRASTRUCTURE",
            artifact_role="Active validation and no-raw-legacy enforcement",
            active_status="ACTIVE_CANONICAL",
            allowed_consumers=["CI", "QTT_VALIDATORS", "ActiveArtifactRegistryV1"],
            forbidden_consumers=base_forbidden,
            replacement_artifact_refs=[],
            upstream_refs=["PR168_RP5B"],
            downstream_refs=["QTT_VALIDATION_GATES", "FUTURE_QTT_AGENTS"],
            owning_agent_refs=["VALIDATION_AGENT"],
            validator_refs=["tools/validate_validation_scope_registry.py", "tools/validate_validation_inventory.py"],
        )

    for path in (
        "docs/master_plan/generated/PR161C_QKUCanonicalRegistry.report.json",
        "docs/master_plan/generated/PR161C_QKUFormulaAlgorithmAssimilation.report.json",
        "docs/master_plan/generated/map3/formula_contract_rows.jsonl",
        "docs/master_plan/generated/map3/formula_ontology_rows.jsonl",
        "docs/master_plan/generated/map3/formula_materialization_rows.jsonl",
        "docs/master_plan/generated/map3/quantum_objective_rows.jsonl",
    ):
        if _path_exists(path):
            _row(
                rows,
                artifact_path=path,
                artifact_family="QKU_FORMULA_IDENTITY_SOURCE",
                artifact_role="Preserved input for future immutable QKU/formula library reclaim",
                active_status="ACTIVE_TRANSITIONAL",
                allowed_consumers=["ActiveArtifactRegistryV1", "PR168_RP5C"],
                forbidden_consumers=base_forbidden + ["GLOBAL_FORMULA_BAN_AUTHORITY"],
                replacement_artifact_refs=["PR168_RP5C_IMMUTABLE_QKU_FORMULA_LIBRARY"],
                upstream_refs=["PR161C", "PR168_MAP3"],
                downstream_refs=["PR168_RP5C"],
                owning_agent_refs=["QKU_FORMULA_LIBRARY_RECLAIM_AGENT"],
                validator_refs=["tools/validate_pr168_rp5b_active_registry_safe_cleanup.py"],
            )

    for path in (
        "docs/master_plan/generated/pr168_data1_snapshots/**",
        "docs/master_plan/generated/pr168_data1a_audit/**",
        "docs/master_plan/generated/pr168_gfp2r_candidate_compute/**",
        "docs/master_plan/generated/rp2p/**",
        "docs/master_plan/generated/rp3/**",
    ):
        if _prefix_exists(path):
            _row(
                rows,
                artifact_path=path,
                artifact_family="FUTURE_REPLAY_PAPER_CONTEXT",
                artifact_role="Existing generated evidence context routed through active registry",
                active_status="ACTIVE_TRANSITIONAL",
                allowed_consumers=["ActiveArtifactRegistryV1", "PR168_RP5C", "PR168_RP5D"],
                forbidden_consumers=base_forbidden,
                replacement_artifact_refs=["PR168_RP5D_EXECUTABILITY_TIERS"],
                upstream_refs=["PR168_DATA1", "PR168_DATA1A", "PR168_GFP2R", "PR168_RP2", "PR168_RP3"],
                downstream_refs=["PR168_RP5C", "PR168_RP5D"],
                owning_agent_refs=["REPLAY_PAPER_CONTEXT_AGENT"],
                validator_refs=["tools/validate_pr168_rp5b_active_registry_safe_cleanup.py"],
            )

    for path in _existing_glob("docs/master_plan/generated/PR168_RP5B_*.report.json", limit=3):
        _row(
            rows,
            artifact_path=path,
            artifact_family="RP5B_ACTIVE_CONTROL_OUTPUT",
            artifact_role="RP5B registry, supersession, and cleanup proof output",
            active_status="ACTIVE_CANONICAL",
            allowed_consumers=["FUTURE_QTT_AGENTS", "PR168_RP5C", "PR168_RP5D", "PR168_RP5E"],
            forbidden_consumers=["RAW_LEGACY_REPORT_DECISION_AUTHORITY"],
            replacement_artifact_refs=[],
            upstream_refs=["PR168_RP5A", "PR168_RP5B"],
            downstream_refs=["PR168_RP5C", "PR168_RP5D", "PR168_RP5E"],
            owning_agent_refs=["QTT_ARCHITECTURE_CLEANUP_AGENT"],
            validator_refs=["tools/validate_pr168_rp5b_active_registry_safe_cleanup.py"],
        )

    for verification in verification_rows:
        if verification.get("final_action") == "ARCHIVE_NO_VALIDATION_SCAN_NOW":
            _row(
                rows,
                artifact_path=str(verification["file_path"]),
                artifact_family="LEGACY_ARCHIVED_BY_REGISTRY",
                artifact_role="Archived by RP5B registry classification; not direct decision authority",
                active_status="LEGACY_ARCHIVED",
                allowed_consumers=["LegacySemanticSupersessionV1"],
                forbidden_consumers=base_forbidden,
                replacement_artifact_refs=["docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json"],
                upstream_refs=["PR168_RP5A", "PR168_RP5B"],
                downstream_refs=["LegacySemanticSupersessionV1"],
                owning_agent_refs=["QTT_ARCHITECTURE_CLEANUP_AGENT"],
                validator_refs=["tools/validate_pr168_rp5b_active_registry_safe_cleanup.py"],
            )

    if semantic_rows:
        _row(
            rows,
            artifact_path="docs/master_plan/generated/PR168_RP5B_LegacySemanticSupersession.report.json",
            artifact_family="LEGACY_SEMANTIC_SUPERSESSION",
            artifact_role="Canonical interpretation bridge for stale legacy labels",
            active_status="ACTIVE_CANONICAL",
            allowed_consumers=["FUTURE_QTT_AGENTS", "PR168_RP5C", "PR168_RP5D", "PR168_RP5E"],
            forbidden_consumers=["GLOBAL_FORMULA_BAN_AUTHORITY", "RAW_LEGACY_REPORT_DECISION_AUTHORITY"],
            replacement_artifact_refs=[],
            upstream_refs=["PR168_RP5A_WrongConceptTermIndex"],
            downstream_refs=["FUTURE_QTT_AGENTS"],
            owning_agent_refs=["QTT_ARCHITECTURE_CLEANUP_AGENT"],
            validator_refs=["tools/validate_pr168_rp5b_active_registry_safe_cleanup.py"],
        )

    return rows
