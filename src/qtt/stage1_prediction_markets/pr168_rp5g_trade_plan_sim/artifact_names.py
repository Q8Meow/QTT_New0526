"""Artifact registry construction for PR168-RP5G compact outputs."""

from __future__ import annotations

from typing import Iterable

from .models import all_artifact_filenames, schema_name
from .path_safety import path_safety_record

LOGICAL_NAMES = {
    "trade_candidate.jsonl": "TradePlanCandidateV1",
    "sim_run.jsonl": "TradePlanSimulationRunV1",
    "exec_pnl.jsonl": "ExecutionAdjustedPnLV1",
    "owner_q1_edge.jsonl": "OwnerQuestion1EdgeAnswerV1",
    "owner_q2_route.jsonl": "OwnerQuestion2RouteAnswerV1",
    "owner_q3_auto_path.jsonl": "OwnerQuestion3AutomationAnswerV1",
    "qstruct_problem.jsonl": "QuantumStructuralProblemV1",
    "run_receipt.report.json": "RP5GRunReceiptV1",
}


def artifact_family(filename: str) -> str:
    if filename.endswith(".manifest.json"):
        return "manifest"
    if filename.endswith(".report.json"):
        return "summary_report"
    if filename.endswith(".md"):
        return "pull_request_body"
    if filename == "art_reg.json":
        return "artifact_registry"
    if filename.startswith("owner_q"):
        return "owner_question_proof"
    if filename.startswith("q_") or filename.startswith("qstruct") or filename.startswith("qobj"):
        return "quantum_structural_readiness"
    if filename in {"value_route.jsonl", "row_route.jsonl", "info_route.jsonl", "user_route.jsonl", "conn_route.jsonl", "handoff_route.jsonl", "dag.jsonl"}:
        return "value_level_no_orphan_route"
    if filename in {"order_auto_path.jsonl", "live_shadow_handoff.jsonl", "auth_block.jsonl", "authority_block.jsonl", "order_ready_prev.jsonl"}:
        return "order_automation_non_authority_handoff"
    if filename in {"exec_pnl.jsonl", "tca_decomp.jsonl", "fill_latency_cap.jsonl", "scenario_ladder.jsonl", "notrade_cmp.jsonl", "overfit_fdr.jsonl", "port_marg_util.jsonl"}:
        return "execution_adjusted_numeric_evidence"
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
                "abbreviation_explanation": "RP5G compact filename mapped by art_reg.json to the replay/paper trade-plan simulation contract.",
                "primary_consumer_agent_refs": ["GovernanceAgent", "TradePlanSimulationAgent", "RiskAgent", "RP5GValidator"],
                "future_consumer_pr_refs": ["RANK4", "QOPT1", "VS2", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "PR170-LIVE-DRYRUN", "PR171-LIVE-PILOT", "PR172-LAUNCH"],
            }
        )
    return rows

