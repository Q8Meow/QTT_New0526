"""RP5D executability overlay access for RP5E."""

from __future__ import annotations

from .models import REPO_ROOT, read_json, read_jsonl


def rp5d_run_receipt() -> dict[str, object]:
    return read_json(REPO_ROOT / "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json")


def exec_tiers() -> list[dict[str, object]]:
    return read_jsonl(REPO_ROOT / "docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl")


def schedulable_after_adapter_rows() -> list[dict[str, object]]:
    return [row for row in exec_tiers() if row.get("schedulable_after_adapter_flag") is True]
