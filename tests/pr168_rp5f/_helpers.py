from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
ART_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5f"

AUTHORITY_FALSE_FIELDS = (
    "paper_authority_flag",
    "paper_submit_authority_flag",
    "shadow_authority_flag",
    "live_authority_flag",
    "order_authority_flag",
    "connector_write_flag",
    "private_state_fetch_flag",
    "cash_account_read_flag",
    "profit_proof_flag",
    "qopt_execution_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "proprietary_claim_flag",
    "qtt_sha_authority_flag",
    "atomicrows_sha_ref_flag",
    "metadata_is_proof_flag",
    "fixed_trade_instruction_flag",
    "non_expiring_trade_plan_flag",
    "stale_candidate_authority_flag",
    "formula_mutation_flag",
    "formula_deletion_flag",
    "qku_mutation_flag",
    "qku_deletion_flag",
    "global_ban_flag",
)

COMMON_FIELDS = (
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
    "connector_refs_or_future_connector_status",
    "provenance_tier",
)


def read_json(name: str) -> dict:
    return json.loads((ART_DIR / name).read_text(encoding="utf-8"))


def read_jsonl(name: str) -> list[dict]:
    path = ART_DIR / name
    assert path.exists(), name
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


@lru_cache(maxsize=1)
def assert_valid() -> dict:
    from src.qtt.stage1_prediction_markets.pr168_rp5f_dynamic_targets.validator import (
        run_validation,
    )

    result = run_validation()
    assert result["validation"] == "PR168_RP5F_DYNAMIC_TARGETS_OK"
    return result


def assert_nonempty_jsonl(name: str) -> list[dict]:
    assert_valid()
    rows = read_jsonl(name)
    assert rows, name
    return rows


def assert_common_contract(row: dict) -> None:
    missing = [field for field in COMMON_FIELDS if field not in row]
    assert not missing, missing
    assert row["source_pr"] == "PR168-RP5F"
    assert row["upstream_refs"]
    assert row["downstream_refs"]
    assert row["consumer_agents"]
    assert row["validation_refs"]
    assert row["execution_authority_ref"].startswith("RP5F_EXEC_AUTH::")
    assert row["blocker_policy_ref"].startswith("RP5F_BLOCKER_POLICY::")


def assert_no_authority(row: dict) -> None:
    for field in AUTHORITY_FALSE_FIELDS:
        if field in row:
            assert row[field] is False, (field, row.get("row_id"), row[field])


def assert_rows_have_contract(name: str) -> list[dict]:
    rows = assert_nonempty_jsonl(name)
    for row in rows:
        assert_common_contract(row)
        assert_no_authority(row)
    return rows


def all_jsonl_rows() -> Iterable[tuple[str, dict]]:
    assert_valid()
    for path in sorted(ART_DIR.glob("*.jsonl")):
        for row in read_jsonl(path.name):
            yield path.name, row

