"""Parameter stack route helpers."""

from __future__ import annotations


def parameter_stack_agent_routes(routes):
    return [
        record for record in routes
        if "PARAMETER_STACK_AGENT" in record.get("agent_path_refs", [])
    ]
