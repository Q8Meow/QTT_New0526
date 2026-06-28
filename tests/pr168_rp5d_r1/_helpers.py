from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ART_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5d_r1"

FALSE_AUTHORITY_FLAGS = (
    "accepted_source_fact_flag",
    "paper_authority_flag",
    "shadow_authority_flag",
    "live_authority_flag",
    "order_authority_flag",
    "profit_proof_flag",
    "qopt_execution_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "proprietary_claim_flag",
    "qtt_sha_authority_flag",
    "atomicrows_sha_ref_flag",
)


def read_json(name: str) -> dict[str, Any]:
    return json.loads((ART_DIR / name).read_text(encoding="utf-8"))


def read_jsonl(name: str) -> list[dict[str, Any]]:
    path = ART_DIR / name
    if not path.exists():
        raise AssertionError(f"missing generated file: {name}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def assert_common(row: dict[str, Any]) -> None:
    for key in (
        "schema_version",
        "row_id",
        "run_id",
        "created_at_utc",
        "source_pr",
        "upstream_refs",
        "downstream_refs",
        "owner_agent",
        "consumer_agents",
        "validation_refs",
        "execution_authority_ref",
        "blocker_policy_ref",
    ):
        assert row.get(key) not in (None, "", []), key
    assert row["source_pr"] == "PR168-RP5D-R1"


def assert_no_authority(row: dict[str, Any]) -> None:
    for flag in FALSE_AUTHORITY_FLAGS:
        assert row.get(flag) is False, f"{flag}:{row.get('row_id')}"


def all_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in ART_DIR.glob("*.jsonl"):
        rows.extend(read_jsonl(path.name))
    return rows
