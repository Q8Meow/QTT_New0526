"""Load PR162D-R1 routed candidates without rebuilding upstream artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class LoadedInputs:
    pr162d_r1_summary: dict[str, Any]
    pr162d_summary: dict[str, Any]
    candidates: list[dict[str, Any]]
    qku_routes: dict[str, dict[str, Any]]
    agent_routes: dict[str, dict[str, Any]]
    replay_paper_routes: dict[str, dict[str, Any]]
    test_vectors: dict[str, dict[str, Any]]
    quantum_problem_records: dict[str, dict[str, Any]]
    pr162d_replay_router_records: list[dict[str, Any]]
    pr162d_trace_records: list[dict[str, Any]]
    replay_contract: dict[str, Any]
    paper_contract: dict[str, Any]


def load_inputs(repo_root: Path) -> LoadedInputs:
    def payload(name: str) -> dict[str, Any]:
        return read_json(repo_root / c.GENERATED_DIR / name)

    pr162d_r1_summary = payload("PR162D_R1_FinalSummary.report.json")
    pr162d_summary = payload("PR162D_FinalSummary.report.json")
    candidates = records_from_payload(payload("PR162D_R1_ComputableCandidateRegistry.report.json"))
    qku_routes = _by_candidate(records_from_payload(payload("PR162D_R1_QKUExternalCandidateMappingMatrix.report.json")))
    agent_routes = _by_candidate(records_from_payload(payload("PR162D_R1_AgentExternalCandidateRouteMatrix.report.json")))
    replay_paper_routes = _by_candidate(records_from_payload(payload("PR162D_R1_ReplayPaperExternalCandidateQueue.report.json")))
    test_vectors = _by_candidate(records_from_payload(payload("PR162D_R1_TestVectorExpansionRegistry.report.json")))
    quantum_problem_records = _by_candidate(
        records_from_payload(payload("PR162D_R1_QuantumProblemFormulationRegistry.report.json"))
    )
    router_payload = payload("PR162D_ReplayPaperCandidateRouterQueue.report.json")
    trace_payload = payload("PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json")
    pr162d_replay_router_records = _records_or_count_placeholders(router_payload, "PR162D_ROUTER_ROLLUP")
    pr162d_trace_records = _records_or_count_placeholders(trace_payload, "PR162D_TRACE_ROLLUP")
    replay_contract = payload("PR162_ReplayDataAdapterContract.report.json")
    paper_contract = payload("PR162_PaperDataAdapterContract.report.json")
    return LoadedInputs(
        pr162d_r1_summary=pr162d_r1_summary,
        pr162d_summary=pr162d_summary,
        candidates=candidates,
        qku_routes=qku_routes,
        agent_routes=agent_routes,
        replay_paper_routes=replay_paper_routes,
        test_vectors=test_vectors,
        quantum_problem_records=quantum_problem_records,
        pr162d_replay_router_records=pr162d_replay_router_records,
        pr162d_trace_records=pr162d_trace_records,
        replay_contract=replay_contract,
        paper_contract=paper_contract,
    )


def _by_candidate(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(record.get("candidate_id") or record.get("quantum_candidate_id")): record
        for record in records
        if record.get("candidate_id") or record.get("quantum_candidate_id")
    }


def _records_or_count_placeholders(payload: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    records = records_from_payload(payload)
    if records:
        return records
    count = int(payload.get("record_count") or payload.get("total_record_count") or 0)
    return [
        {
            "record_id": f"{prefix}_{index:04d}",
            "rollup_placeholder_from_record_count": True,
            "route_status": "ROLLED_UP_FROM_SHARDED_PR162D_REPORT",
        }
        for index in range(1, count + 1)
    ]


def candidate_id(record: dict[str, Any]) -> str:
    return str(
        record.get("candidate_id")
        or record.get("formula_id")
        or record.get("algorithm_id")
        or record.get("parameter_id")
        or record.get("dataset_candidate_id")
        or record.get("quantum_candidate_id")
    )


def candidate_type(record: dict[str, Any]) -> str:
    if record.get("formula_id"):
        return "FORMULA"
    if record.get("algorithm_id"):
        return "ALGORITHM"
    if record.get("parameter_id"):
        return "PARAMETER"
    if record.get("dataset_candidate_id"):
        return "DATASET"
    if record.get("quantum_candidate_id"):
        return "QUANTUM"
    return "UNKNOWN"


def agent_refs(record: dict[str, Any]) -> list[str]:
    refs = record.get("agent_refs") or record.get("agent_route_refs") or []
    return [str(ref) for ref in refs]


def route_refs(record: dict[str, Any]) -> list[str]:
    return [str(ref) for ref in (record.get("replay_paper_route_refs") or [])]


def source_tier(record: dict[str, Any]) -> str:
    return str(record.get("source_tier") or "UNKNOWN_SOURCE_TIER")
