"""Canonical QTT agent-role network registry for PR161D."""

from __future__ import annotations

from . import constants as c


def build_agent_role_network_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for index, role in enumerate(c.CANONICAL_QTT_AGENT_ROLES, start=1):
        layer, purpose = c.AGENT_ROLE_LAYER_PURPOSE[role]
        records.append(
            {
                "agent_role_registry_id": f"PR161D-AGENT-ROLE-{index:02d}",
                "assigned_agent_role": role,
                "agent_layer": layer,
                "agent_purpose": purpose,
                "canonical_agent_role_flag": True,
                "autonomous_runtime_agent_claimed_flag": False,
                "no_runtime_agent_claim_flag": True,
                "workflow_consumer_role_flag": True,
            }
        )
    return records


def build_service_layer_records() -> list[dict[str, object]]:
    return [
        {
            "service_layer_domain_id": f"PR161D-QKU-SERVICE-{index:02d}",
            "service_layer_domain": service,
            "agent_layer": "QKU_SERVICE_LAYER",
            "autonomous_runtime_agent_claimed_flag": False,
            "no_runtime_agent_claim_flag": True,
        }
        for index, service in enumerate(c.QKU_SERVICE_LAYER_DOMAINS, start=1)
    ]
