"""VS1 generated evidence access for RP5E."""

from __future__ import annotations

from .models import REPO_ROOT, read_json, read_jsonl


def vs1_run_receipt() -> dict[str, object]:
    return read_json(REPO_ROOT / "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json")


def temporary_stack_candidates() -> list[dict[str, object]]:
    return read_jsonl(REPO_ROOT / "docs/master_plan/generated/pr168_vs1/temporary_stack_candidate_receipts.jsonl")
