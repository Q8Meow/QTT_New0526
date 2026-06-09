"""Central agent duty contracts for PR165-C."""

from __future__ import annotations

from .central_vocab import AGENT_IDS


def agent_contracts() -> tuple[dict[str, object], ...]:
    contracts = {
        "scoring_agent": (
            "PRODUCER",
            "rank and explain PR165 score components",
            "approve live use; validate its own score quality",
            "governance_agent",
        ),
        "memory_agent": (
            "PRODUCER",
            "overlay condition-scoped PR165-B memory",
            "execute orders; globally ban combinations without structural evidence",
            "risk_agent",
        ),
        "risk_agent": (
            "INDEPENDENT_CHALLENGER",
            "challenge, demote, and route based on risk",
            "fabricate score evidence",
            "governance_agent",
        ),
        "tca_agent": (
            "VALIDATOR",
            "measure cost drag and execution-cost degradation",
            "create profit evidence",
            "repair_agent",
        ),
        "latency_agent": (
            "VALIDATOR",
            "assign control-plane, retest, and future hot-path lanes",
            "place orders",
            "repair_agent",
        ),
        "liquidity_agent": (
            "VALIDATOR",
            "assign liquidity fragility and market-depth caveats",
            "bind connector truth",
            "repair_agent",
        ),
        "quantum_mapper_advisory_agent": (
            "REVIEWER",
            "map formulation and comparator needs",
            "run a backend or claim advantage",
            "repair_agent",
        ),
        "replay_agent": (
            "CONSUMER",
            "consume memory and queue replay retests",
            "fake result packets",
            "commander_agent",
        ),
        "paper_agent": (
            "CONSUMER",
            "consume memory and queue paper retests",
            "use live write credentials",
            "commander_agent",
        ),
        "repair_agent": (
            "REPAIR_OWNER",
            "create repair and retest handoffs",
            "fake repaired outputs",
            "commander_agent",
        ),
        "dashboard_agent": (
            "DASHBOARD_VIEWER",
            "render queues and owner-review surfaces",
            "authorize live use",
            "governance_agent",
        ),
        "governance_agent": (
            "INDEPENDENT_CHALLENGER",
            "challenge workflow state and audit coverage",
            "create proven-value or live authority",
            "commander_agent",
        ),
        "commander_agent": (
            "COMMANDER_COORDINATOR",
            "coordinate tasks and stuck-state recovery",
            "self-grant live authority",
            "governance_agent",
        ),
    }
    rows: list[dict[str, object]] = []
    for agent_id in AGENT_IDS:
        role, primary, forbidden, fallback = contracts[agent_id]
        rows.append(
            {
                "agent_id": agent_id,
                "agent_role_class": role,
                "primary_duties": [primary],
                "secondary_duties": ["consume PR165-C lineage and receipts"],
                "forbidden_duties": [forbidden],
                "fallback_agent": fallback,
                "escalation_agent": "commander_agent" if agent_id != "commander_agent" else "governance_agent",
            }
        )
    return tuple(rows)
