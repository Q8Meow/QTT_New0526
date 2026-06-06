"""Lightweight PR163 contract constants."""

from __future__ import annotations


CONTRACT_SCHEMA_VERSIONS = {
    "adapter_input": "PaperAdapterInputV1",
    "decision_intent": "PaperDecisionIntentV1",
    "order_intent": "PaperOrderIntentV1",
    "pretrade_receipt": "PaperPreTradeCheckReceiptV1",
    "risk_policy_receipt": "PaperRiskPolicyReceiptV1",
    "state_transition": "PaperOrderStateTransitionV1",
    "fill_event": "PaperSyntheticFillEventV1",
    "ledger_snapshot": "PaperPortfolioLedgerSnapshotV1",
    "cash_reservation": "PaperCashReservationReceiptV1",
    "execution_cost": "PaperExecutionCostReceiptV1",
    "latency_slippage": "PaperLatencySlippageReceiptV1",
    "capture_event": "PaperCaptureEventV1",
    "run_plan": "PaperAdapterRunPlanV1",
    "capture_bundle": "PaperAdapterCaptureBundleV1",
    "qku_handoff": "PaperQKUPrioritizationFeatureHandoffV1",
    "llm_handoff": "PaperLLMFutureHandoffExclusionReceiptV1",
}


UPSTREAM_REQUIRED_REF_FAMILIES = (
    "CandidatePacketV1",
    "PR162R-B row binding resolution",
    "PR162R-B paper binding fanout",
    "PR162R-B paper market state binding",
    "PR162R-B paper synthetic fill model",
    "PR162R-B paper portfolio state fixture",
    "PR162R-B paper execution cost model",
    "PR162R-B fee/slippage/latency binding",
    "PR162R-B QKU formula algorithm routing",
)


DOWNSTREAM_AGENT_ROUTES = (
    "QKU Compute Engine",
    "Formula/Algorithm Runtime candidate lane",
    "Feature Builder",
    "Parameter Stack Agent",
    "Replay/Paper Candidate Router",
    "Paper Adapter",
    "Paper OMS",
    "Paper EMS / Fill Simulator",
    "Paper Portfolio Ledger",
    "Paper Capture/Provenance",
    "Risk Manager",
    "Capital Allocation",
    "Quantum Advisory / Quantum Mapping Agent",
    "PR163-B paired replay+paper executor",
    "PR164 Review/Provenance",
    "PR165 Scoring/Ranking",
    "PR166 LLM Review/Research lane",
    "PR162E Plugin Intake",
)
