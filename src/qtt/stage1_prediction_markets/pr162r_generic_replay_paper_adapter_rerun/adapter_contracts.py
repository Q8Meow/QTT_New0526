"""Replay/paper adapter contract helpers for PR162R."""

from __future__ import annotations

from typing import Any


REPLAY_REQUIRED_BINDINGS = ("historical_replay_market_data_binding",)
PAPER_REQUIRED_BINDINGS = ("paper_current_or_simulated_market_state_binding",)


def contract_refs() -> dict[str, list[str]]:
    return {
        "replay": [
            "docs/master_plan/generated/PR162_ReplayDataAdapterContract.report.json",
            "docs/master_plan/generated/PR161F_ReplayRunRequestRegistry.report.json",
        ],
        "paper": [
            "docs/master_plan/generated/PR162_PaperDataAdapterContract.report.json",
            "docs/master_plan/generated/PR161F_PaperRunRequestRegistry.report.json",
        ],
        "paired": [
            "docs/master_plan/generated/PR161F_PairedReplayPaperRunPlan.report.json",
            "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
        ],
    }


def adapter_contract_payload() -> dict[str, Any]:
    return {
        "replay_required_bindings": list(REPLAY_REQUIRED_BINDINGS),
        "paper_required_bindings": list(PAPER_REQUIRED_BINDINGS),
        "result_packet_boundary_ref": "docs/master_plan/generated/PR161F_ResultPacketEmissionEligibilityGate.report.json",
        "no_result_packet_created": True,
        "live_order_authority": False,
    }
