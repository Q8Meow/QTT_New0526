"""Deterministic query API for PR168-MEM1 generated artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .models import GENERATED_DIR, read_jsonl, stable_json


def _artifact_dir(path: str | Path | None = None) -> Path:
    directory = Path(path) if path is not None else GENERATED_DIR
    return directory


def _rows(artifact_dir: str | Path | None, filename: str) -> list[dict[str, Any]]:
    return read_jsonl(_artifact_dir(artifact_dir) / filename)


def _similarity(context_signature: str, row: dict[str, Any]) -> float:
    key = str(row.get("market_context_key", ""))
    if not context_signature or context_signature == "sample":
        return 1.0
    if context_signature == key or context_signature in key:
        return 1.0
    tokens = set(context_signature.split("|"))
    row_tokens = set(key.split("|"))
    if not tokens or not row_tokens:
        return 0.5
    return len(tokens & row_tokens) / len(tokens | row_tokens)


def get_top_recipes_for_context(context_signature: str, top_k: int = 5, artifact_dir: str | Path | None = None) -> list[dict[str, Any]]:
    recipes = _rows(artifact_dir, "winning_recipe.jsonl")
    scored = [
        {
            "recipe_id": recipe["recipe_id"],
            "source_trade_plan_candidate_id": recipe.get("source_trade_plan_candidate_id"),
            "similarity_score": f"{_similarity(context_signature, recipe):.6f}",
            "prior_state": "PENDING_REPLAY_PAPER_REVALIDATION",
            "replay_paper_revalidation_required": True,
            "current_profit_proof_flag": False,
            "live_authority_flag": False,
            "order_authority_flag": False,
        }
        for recipe in recipes
    ]
    return sorted(scored, key=lambda row: (-float(row["similarity_score"]), row["recipe_id"]))[:top_k]


def get_recipe_prior(recipe_id: str, context_signature: str = "sample", artifact_dir: str | Path | None = None) -> dict[str, Any]:
    scores = _rows(artifact_dir, "recipe_prior_score.jsonl")
    recipes = _rows(artifact_dir, "winning_recipe.jsonl")
    recipe = next((row for row in recipes if row.get("recipe_id") == recipe_id), None)
    prior = next((row for row in scores if row.get("recipe_id") == recipe_id), None)
    if not recipe or not prior:
        return {"recipe_id": recipe_id, "state": "NOT_FOUND_FAIL_CLOSED", "authority_created_flag": False}
    return {
        "recipe_id": recipe_id,
        "context_similarity_score": f"{_similarity(context_signature, recipe):.6f}",
        "recipe_prior_score": prior.get("recipe_prior_score"),
        "state": "PENDING_REPLAY_PAPER_REVALIDATION",
        "replay_paper_revalidation_required": True,
        "current_profit_proof_flag": False,
        "live_authority_flag": False,
        "order_authority_flag": False,
    }


def _record_outcome(kind: str, recipe_id: str, outcome_ref: str | None) -> dict[str, Any]:
    if not outcome_ref:
        return {
            "recipe_id": recipe_id,
            "outcome_kind": kind,
            "state": "PENDING_RECEIPT_FAIL_CLOSED",
            "authority_created_flag": False,
            "paper_submit_authority_created_flag": False,
            "live_authority_created_flag": False,
        }
    return {
        "recipe_id": recipe_id,
        "outcome_kind": kind,
        "outcome_ref": outcome_ref,
        "state": "RECEIPT_REF_ACCEPTED_FOR_DOWNSTREAM_VALIDATION_ONLY",
        "authority_created_flag": False,
        "current_profit_proof_flag": False,
    }


def record_replay_outcome(recipe_id: str, outcome_ref: str | None = None, artifact_dir: str | Path | None = None) -> dict[str, Any]:
    return _record_outcome("replay", recipe_id, outcome_ref)


def record_paper_outcome(recipe_id: str, outcome_ref: str | None = None, artifact_dir: str | Path | None = None) -> dict[str, Any]:
    return _record_outcome("paper", recipe_id, outcome_ref)


def record_live_canary_outcome(recipe_id: str, outcome_ref: str | None = None, artifact_dir: str | Path | None = None) -> dict[str, Any]:
    return _record_outcome("live_canary", recipe_id, outcome_ref)


def mark_recipe_stale(recipe_id: str, reason: str, artifact_dir: str | Path | None = None) -> dict[str, Any]:
    return {
        "recipe_id": recipe_id,
        "reason": reason,
        "memory_status": "STALE_PENDING_REVALIDATION",
        "recipe_priority_downshift": True,
        "current_profit_proof_flag": False,
        "live_canary_blocked": True,
    }


def cooldown_recipe_for_context(recipe_id: str, context_key: str, artifact_dir: str | Path | None = None) -> dict[str, Any]:
    return {
        "recipe_id": recipe_id,
        "context_key": context_key,
        "cooldown_scope_key": context_key,
        "cooldown_state": "CONTEXT_SCOPED_COOLDOWN_ACTIVE",
        "global_formula_ban_flag": False,
        "global_qku_ban_flag": False,
    }


def get_failure_memories_for_context(context_signature: str, top_k: int = 5, artifact_dir: str | Path | None = None) -> list[dict[str, Any]]:
    failures = _rows(artifact_dir, "failure_memory.jsonl")
    scored = [
        {
            "failure_memory_id": row["failure_memory_id"],
            "source_recipe_or_candidate_id": row.get("source_recipe_or_candidate_id"),
            "similarity_score": f"{_similarity(context_signature, row):.6f}",
            "similar_context_only_flag": True,
            "global_formula_ban_flag": False,
            "global_qku_ban_flag": False,
        }
        for row in failures
    ]
    return sorted(scored, key=lambda row: (-float(row["similarity_score"]), row["failure_memory_id"]))[:top_k]


def get_quantum_structures_for_context(context_signature: str, top_k: int = 5, artifact_dir: str | Path | None = None) -> list[dict[str, Any]]:
    qrows = _rows(artifact_dir, "qmemory_registry.jsonl")
    return [
        {
            "qmemory_id": row["qmemory_id"],
            "recipe_id": row.get("recipe_id"),
            "quantum_objective_id": row.get("quantum_objective_id"),
            "qopt1_reuse_candidate_flag": row.get("qopt1_reuse_candidate_flag"),
            "backend_execution_created_flag": False,
            "quantum_advantage_claim_flag": False,
            "current_profit_proof_flag": False,
        }
        for row in qrows[:top_k]
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--artifact-dir", default=str(GENERATED_DIR))
    parser.add_argument("--context-fixture", default="sample")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    artifact_dir = Path(args.artifact_dir)
    if not artifact_dir.is_absolute():
        artifact_dir = Path(args.repo_root) / artifact_dir
    payload = {
        "context_fixture": args.context_fixture,
        "top_recipes": get_top_recipes_for_context(args.context_fixture, args.top_k, artifact_dir),
        "failure_memories": get_failure_memories_for_context(args.context_fixture, args.top_k, artifact_dir),
        "quantum_structures": get_quantum_structures_for_context(args.context_fixture, args.top_k, artifact_dir),
        "authority_state": "NON_AUTHORITY_PENDING_REPLAY_PAPER_REVALIDATION",
    }
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path(args.repo_root) / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(stable_json(payload), encoding="utf-8")
    print(f"PR168-MEM1 query demo written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
