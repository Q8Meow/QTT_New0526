"""Shared QKU, agent, and replay/paper route helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json, records_from_payload


FALLBACK_QKU_REFS = (
    "QKU-ATOMICROW-AR_EXACT_001_SIGNAL_FEATURES_000001",
    "QKU-ATOMICROW-AR_EXACT_001_SIGNAL_FEATURES_000002",
    "QKU-ATOMICROW-AR_EXACT_001_SIGNAL_FEATURES_000003",
    "PR162D_R1_EXTERNAL_FORMULA_DATA_QUANTUM_QKU_BACKLOG",
)


def load_qku_refs(repo_root: Path, limit: int = 48) -> list[str]:
    candidates: list[str] = []
    for ref in (
        "docs/master_plan/generated/PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json",
        "docs/master_plan/generated/PR161C_QKUCanonicalRegistry.report.json",
    ):
        path = repo_root / ref
        if not path.exists():
            continue
        payload = read_json(path)
        rows = records_from_payload(payload)
        if not rows and isinstance(payload, dict):
            rows = [item for item in payload.get("preview_records", []) if isinstance(item, dict)]
        for row in rows:
            qku = row.get("qku_id") or row.get("qku_ref") or row.get("canonical_qku_id")
            if isinstance(qku, str) and qku not in candidates:
                candidates.append(qku)
                if len(candidates) >= limit:
                    return candidates
    return list(FALLBACK_QKU_REFS)


def qku_refs_for_index(qku_pool: list[str], index: int) -> list[str]:
    if not qku_pool:
        return [FALLBACK_QKU_REFS[-1]]
    return [qku_pool[index % len(qku_pool)]]


def common_agent_refs(include_quantum: bool = False) -> list[str]:
    refs = list(c.REQUIRED_AGENT_ROUTES)
    if include_quantum and c.QUANTUM_HARNESS_ROUTE not in refs:
        refs.append(c.QUANTUM_HARNESS_ROUTE)
    return refs


def replay_route_refs(candidate_id: str) -> list[str]:
    return [c.REPLAY_PAPER_ROUTE, f"PR162D_R1_REPLAY_PAPER_ROUTE::{candidate_id}"]


def downstream_bridge(candidate_id: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
        "pr162r_handoff_ref": f"PR162D_R1_PR162R_HANDOFF::{candidate_id}",
        "pr163_future_result_consumer_ref": f"PR162D_R1_PR163_FUTURE_CONSUMER::{candidate_id}",
        "pr164_future_review_ref": f"PR162D_R1_PR164_FUTURE_REVIEW::{candidate_id}",
        "pr165_future_scoring_ref": f"PR162D_R1_PR165_FUTURE_SCORING::{candidate_id}",
    }
