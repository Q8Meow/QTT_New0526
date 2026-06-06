"""Generic paper adapter interface."""

from __future__ import annotations

from typing import Protocol, Any


class PaperAdapter(Protocol):
    venue_scope: str

    def normalize_paper_market_state(self, binding: dict[str, Any]) -> dict[str, Any]:
        ...

    def create_paper_decision_intent(self, candidate_row: dict[str, Any], qku_route: dict[str, Any], market_state: dict[str, Any], risk_policy: dict[str, Any]) -> dict[str, Any]:
        ...

    def create_paper_order_intent(self, decision_intent: dict[str, Any], market_state: dict[str, Any], risk_policy: dict[str, Any]) -> dict[str, Any]:
        ...

    def run_pretrade_checks(self, intent_or_decision: dict[str, Any], paper_portfolio: dict[str, Any], market_state: dict[str, Any], cost_model: dict[str, Any]) -> dict[str, Any]:
        ...

    def simulate_order_state_transitions(self, intent: dict[str, Any], market_state: dict[str, Any], latency_model: dict[str, Any], fill_model: dict[str, Any]) -> list[dict[str, Any]]:
        ...

    def apply_paper_fill_events(self, portfolio: dict[str, Any], fill_events: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    def emit_paper_capture_events(self, *records: dict[str, Any]) -> list[dict[str, Any]]:
        ...

    def emit_downstream_handoff(self, capture_bundle: dict[str, Any]) -> dict[str, Any]:
        ...


def capability_row(index: int, venue_scope: str, features: list[str], source_slots: list[str]) -> dict[str, Any]:
    return {
        "venue_adapter_capability_ref": f"PR163_VENUE_ADAPTER_CAPABILITY::{index:03d}",
        "venue_scope": venue_scope,
        "generic_interface_implemented": True,
        "supported_features": features,
        "candidate_source_slots": source_slots,
        "paper_execution_is_simulated": True,
        "live_connector_activation": False,
        "order_submission_allowed": False,
        "source_acceptance_created": False,
        "private_state_fetch_allowed": False,
        "llm_hot_path_allowed": False,
        "validation_status": "PASS",
        "live_order_authority": False,
    }
