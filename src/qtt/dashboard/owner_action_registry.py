"""Central owner action grammar for PR169-DASH1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ACTION_DEFINITIONS: dict[str, dict[str, Any]] = {
    "ACK_OWNER_PACKET": {
        "label": "Acknowledge packet",
        "semantics": "Audit acknowledgement only; does not approve risk, source truth, paper, shadow, or live action.",
        "confirmation_class": "ACK_ONLY",
    },
    "REQUEST_OWNER_REVIEW": {
        "label": "Request owner review",
        "semantics": "Create audited owner review task in the decision queue.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_RISK_REVIEW": {
        "label": "Request risk review",
        "semantics": "Route to risk/pretrade review without risk-pass authority.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_KILL_SWITCH_REVIEW": {
        "label": "Request kill-switch review",
        "semantics": "Route to governed kill-switch review without direct execution control.",
        "confirmation_class": "CRITICAL_CONFIRMATION",
    },
    "REQUEST_SOURCE_CAPTURE": {
        "label": "Request source capture",
        "semantics": "Route a source candidate into evidence capture without accepting source truth.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_SOURCE_VALIDATION": {
        "label": "Request source validation",
        "semantics": "Request source-evidence validation without ledger acceptance authority.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "SUBMIT_RESEARCH_CANDIDATE": {
        "label": "Submit research candidate",
        "semantics": "Create audited research candidate intake and route to source/LLM/QKU providers.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_LLM_RESEARCH_EXTRACTION": {
        "label": "Request research extraction",
        "semantics": "Route to bounded LLM extraction without source-truth or order authority.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_FORMULA_EXTRACTION": {
        "label": "Request formula extraction",
        "semantics": "Route extracted formulas to computability review; no formula truth by assertion.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_QKU_MATERIALIZATION": {
        "label": "Request QKU materialization",
        "semantics": "Route useful research into QKU candidate materialization provider.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_QKU_COMPUTABILITY_REVIEW": {
        "label": "Request QKU computability review",
        "semantics": "Route QKU/formula/candidate computability gaps to READINESS1/PRETRADE1.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_QSTRUCT_MAPPING_REVIEW": {
        "label": "Request qstruct mapping review",
        "semantics": "Route quantum structural mapping review to QMAP1 without backend execution.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_REPLAY_TEST": {
        "label": "Request replay test",
        "semantics": "Request replay provider work; DASH1 does not execute replay.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_PAPER_TEST": {
        "label": "Request paper test",
        "semantics": "Request paper-loop provider work; DASH1 does not submit paper orders.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_VARIABLE_OPTIMIZATION": {
        "label": "Request variable optimization",
        "semantics": "Route mutable trade-plan variables to optimization providers; formulas/QKUs remain immutable.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_QOPT_REVIEW": {
        "label": "Request QOPT review",
        "semantics": "Route advisory optimization review to QOPT/QMAP providers.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_MEMORY_REVALIDATION": {
        "label": "Request memory revalidation",
        "semantics": "Route to condition-scoped memory revalidation; memory is not current proof.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_NO_TRADE_REOPTIMIZATION_REVIEW": {
        "label": "Request no-trade reoptimization",
        "semantics": "Route no-trade comparator to retest/rotation review rather than terminal closure.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_LIVE_CANARY_REVIEW": {
        "label": "Request live-canary review",
        "semantics": "Create owner review route for later live-pilot stages without order release.",
        "confirmation_class": "CRITICAL_CONFIRMATION",
    },
    "REQUEST_ALLOWLIST_REVIEW": {
        "label": "Request allowlist review",
        "semantics": "Route allowlist/rollback review to ALLOW1 without live promotion authority.",
        "confirmation_class": "CRITICAL_CONFIRMATION",
    },
    "REQUEST_TELEGRAM_MIRROR": {
        "label": "Request Telegram mirror",
        "semantics": "Route mirror contract to TG1 without bot runtime, webhook, polling, or token access.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "REQUEST_AGENT_TASK": {
        "label": "Request agent task",
        "semantics": "Route audited owner request to AGENT-ORCH1 without expanding agent permissions.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "PROMOTE_TO_REPLAY_REQUEST": {
        "label": "Request replay promotion",
        "semantics": "Promotion request only; provider evidence still required.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "PROMOTE_TO_PAPER_REQUEST": {
        "label": "Request paper promotion",
        "semantics": "Promotion request only; no paper submit authority.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "PROMOTE_TO_LIVE_REVIEW_REQUEST": {
        "label": "Request live review",
        "semantics": "Owner review route only; execution router gates remain required.",
        "confirmation_class": "CRITICAL_CONFIRMATION",
    },
    "ROLLBACK_FORMULA_VERSION_REQUEST": {
        "label": "Request formula rollback review",
        "semantics": "Route rollback review to ALLOW1 without mutating QKUs/formulas in DASH1.",
        "confirmation_class": "CRITICAL_CONFIRMATION",
    },
    "SUBMIT_OPEN_TRADE_URL_REQUEST": {
        "label": "Submit open trade URL",
        "semantics": "Source/target intake request; no source truth and no order authority.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "SIMULATE_COMBINATIONS_REQUEST": {
        "label": "Request combination simulation",
        "semantics": "Route to simulation provider; no runtime execution in DASH1.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "RUN_FORMULA_TEST_VECTOR_REQUEST": {
        "label": "Request formula test vector",
        "semantics": "Request test-vector provider work; no accepted formula truth by itself.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "RUN_REPLAY_CANDIDATE_REQUEST": {
        "label": "Request candidate replay",
        "semantics": "Request replay provider work only.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "RUN_PAPER_CANDIDATE_REQUEST": {
        "label": "Request candidate paper test",
        "semantics": "Request paper provider work only; no submit authority.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "ADD_FORMULA_REQUEST": {
        "label": "Add formula request",
        "semantics": "Route formula intake to PLUGIN1/computability workflow.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "ADD_ALGORITHM_REQUEST": {
        "label": "Add algorithm request",
        "semantics": "Route algorithm intake to PLUGIN1 without runtime enablement.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "ADD_QUANTUM_FORMULATION_REQUEST": {
        "label": "Add quantum formulation request",
        "semantics": "Route quantum formulation intake to QMAP1 without backend execution.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
    "ADD_SOURCE_REQUEST": {
        "label": "Add source request",
        "semantics": "Route source candidate intake without direct acceptance.",
        "confirmation_class": "OWNER_REVIEW_REQUIRED",
    },
}


@dataclass(frozen=True)
class OwnerActionRegistry:
    actions: dict[str, dict[str, Any]]

    @classmethod
    def default(cls) -> "OwnerActionRegistry":
        return cls(ACTION_DEFINITIONS)

    def get(self, action_code: str) -> dict[str, Any]:
        return self.actions[action_code]
