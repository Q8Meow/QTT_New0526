"""Optional replay/paper input receipts for PR166-S."""

from __future__ import annotations

from typing import Any

from .central_vocab import TERMINAL_NO_ORPHAN_STATUS
from .deterministic_ids import stable_ref
from .input_consumption import InputDiscovery, row_contract


def receipt_id(group: str) -> str:
    return stable_ref("PR166_S_OPTIONAL_INPUT_RECEIPT", group)


def build_optional_input_missing_receipts(discovery: InputDiscovery) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in sorted(discovery.optional_missing):
        missing = list(discovery.optional_missing[group])
        if not missing:
            continue
        row_id = receipt_id(group)
        rows.append(
            {
                "optional_replay_paper_input_receipt_id": row_id,
                "optional_input_group": group,
                "missing_artifact_refs": missing,
                "receipt_status": "MISSING_MARKET_DATA_OR_FIXTURE_ROUTE_CREATED",
                "bounded_execution_route": _bounded_route(group),
                "safe_fallback_mode": _safe_fallback_mode(group),
                "why_not_blocking_pr166_s": (
                    "PR166-S can produce deterministic bounded fixture replay/paper outcomes "
                    "while routing richer repo-local data needs to dataset completion."
                ),
                "terminal_status_flag": True,
                "terminal_status_reason": (
                    "Receipt is terminal for PR166-S because it records missing optional context "
                    "without granting source-truth, connector, or live-order authority."
                ),
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref=",".join(missing),
                    source_row_ref=group,
                    computed_by_module="optional_input_receipts",
                    owning_agent="governance_agent",
                    consuming_agent="commander_agent",
                    downstream_action_type="dataset completion or bounded replay route receipt",
                    downstream_pr_route="DATASET_COMPLETION_ROUTE",
                    downstream_artifact_route="PR166_S_OptionalReplayPaperInputMissingReceipt.report.json",
                    no_orphan_status=TERMINAL_NO_ORPHAN_STATUS,
                ),
            }
        )
    return rows


def _bounded_route(group: str) -> str:
    if "historical" in group:
        return "DATA_REQUIRED_WITH_REPLAY_FIXTURE_ROUTE"
    if "paper" in group:
        return "PAPER_EXECUTABLE_WITH_SIMULATED_ADAPTER"
    if "quantum" in group:
        return "QUANTUM_ADVISORY_ONLY_NO_BACKEND"
    return "REPLAY_EXECUTABLE_WITH_FIXTURE_DATA"


def _safe_fallback_mode(group: str) -> str:
    if "paper" in group:
        return "SIMULATED_ADAPTER_ONLY"
    if "quantum" in group:
        return "ADVISORY_PASSTHROUGH_ONLY"
    return "BOUNDED_SYNTHETIC_FIXTURE_ONLY"
