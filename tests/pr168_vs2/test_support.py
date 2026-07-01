from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_vs2"


def read_jsonl(name: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (ARTIFACT_DIR / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_json(name: str) -> dict[str, Any]:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def packet_ids() -> set[str]:
    return {row["paper_intent_candidate_id"] for row in read_jsonl("paper_intent_candidate.jsonl")}


AUTHORITY_FALSE_FIELDS = (
    "paper_order_intent_created_flag",
    "paper_submit_authority_created_flag",
    "paper_execution_created_flag",
    "live_authority_created_flag",
    "connector_write_created_flag",
    "private_state_read_created_flag",
    "cash_account_read_created_flag",
    "true_quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "profit_guarantee_flag",
    "owner_dashboard_runtime_created_flag",
    "telegram_bot_runtime_created_flag",
    "llm_runtime_created_by_vs2_flag",
    "qTT_SHA_authority_created_flag",
    "atomicrows_hash_authority_created_flag",
)
