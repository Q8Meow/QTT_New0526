"""No-orphan responsible role and consumer-class mapping."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def _roles_from_text(value: str) -> list[str]:
    text = value.upper()
    roles: list[str] = []
    if any(token in text for token in ("SOURCE", "FEE", "TICK", "API", "VENUE")):
        roles.append("SOURCE_EVIDENCE_STEWARD")
    if any(token in text for token in ("EXECUTION", "ORDER", "LATENCY", "CONNECTOR")):
        roles.append("EXECUTION_BOUNDARY_STEWARD")
    if "RISK" in text:
        roles.append("RISK_POLICY_STEWARD")
    if any(token in text for token in ("CAPITAL", "CASH", "EXPOSURE")):
        roles.append("CAPITAL_POLICY_STEWARD")
    if any(token in text for token in ("SCORING", "RANKING", "SIGNAL", "ALPHA")):
        roles.append("SCORING_RESEARCH_STEWARD")
    if any(token in text for token in ("OPTIMIZER", "QUANTUM", "QUBO", "QAOA", "VQE")):
        roles.append("QUANTUM_OPTIMIZER_RESEARCH_STEWARD")
    if any(token in text for token in ("AGENT", "LIFECYCLE", "BINDING")):
        roles.append("AGENT_GOVERNANCE_STEWARD")
    if not roles:
        roles.append("ATOMICROWS_COMPLETION_STEWARD")
    return sorted(dict.fromkeys(roles))


def _consumer_classes(roles: list[str]) -> list[str]:
    classes = ["CONTROL_PLANE_COMPLETION_CONSUMER"]
    if "SOURCE_EVIDENCE_STEWARD" in roles:
        classes.append("SOURCE_EVIDENCE_CONSUMER")
    if "EXECUTION_BOUNDARY_STEWARD" in roles:
        classes.append("EXECUTION_BOUNDARY_CONSUMER")
    if "RISK_POLICY_STEWARD" in roles:
        classes.append("RISK_POLICY_CONSUMER")
    if "CAPITAL_POLICY_STEWARD" in roles:
        classes.append("CAPITAL_POLICY_CONSUMER")
    if "SCORING_RESEARCH_STEWARD" in roles:
        classes.append("SCORING_RANKING_CONSUMER")
    if "QUANTUM_OPTIMIZER_RESEARCH_STEWARD" in roles:
        classes.append("QUANTUM_METADATA_CONSUMER")
    if "AGENT_GOVERNANCE_STEWARD" in roles:
        classes.append("AGENT_BINDING_CONSUMER")
    return sorted(dict.fromkeys(classes))


def for_pr154_record(record: Mapping[str, Any], *, blocked: bool) -> dict[str, Any]:
    basis = " ".join(
        str(record.get(key) or "")
        for key in (
            "parameter_family_or_target_family",
            "target_field_path",
            "platform_scope",
            "pr153s_closure_lane",
        )
    )
    roles = _roles_from_text(basis)
    consumers = _consumer_classes(roles)
    return {
        "responsible_agent_role_ids": roles,
        "applicable_agent_role_ids": roles,
        "candidate_agent_family_ids": [
            str(record.get("parameter_family_or_target_family") or "PR154_TARGET_FAMILY")
        ],
        "consumer_class_ids": consumers,
        "primary_consumer_class": consumers[0],
        "secondary_consumer_classes": consumers[1:],
        "agent_binding_state": (
            c.AgentBindingState.ROLE_BOUND_ONLY.value
            if roles
            else c.AgentBindingState.BLOCKED_NO_RESPONSIBLE_ROLE.value
        ),
        "exact_agent_id_or_null": None,
        "explicit_agent_binding_required_flag": False,
        "agent_binding_source_ref_or_null": (
            "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.registry.json"
        ),
        "owner_agent_assignment_request_id_or_null": None,
        "agent_binding_blocker_class": c.BlockerClass.NONE.value
        if roles
        else c.BlockerClass.BLOCKED_NO_RESPONSIBLE_ROLE.value,
        "agent_binding_future_pr_route": "ELIGIBLE_FOR_AGENT_BINDING_PR163",
        "agent_binding_unblock_steps": [
            "Consume the future exact agent map when it exists.",
            "Verify the exact agent ID is supported by binding evidence.",
            "Regenerate PR157 or the successor binding bridge.",
        ],
        "no_orphan_status": (
            c.NoOrphanStatus.NOT_ORPHAN_ROLE_BOUND.value
            if roles
            else c.NoOrphanStatus.ORPHAN_BLOCKED_NO_RESPONSIBLE_ROUTE.value
        ),
    }


def for_atomicrow(
    row: Mapping[str, Any],
    *,
    source_requirement_class: str,
    owner_assignment_request_id: str | None,
) -> dict[str, Any]:
    family_id = str(row.get("family_id") or row.get("source_file_family_id") or "")
    basis = " ".join(
        str(row.get(key) or "") for key in ("family_id", "family_label", "row_id")
    )
    roles = _roles_from_text(basis)
    consumers = _consumer_classes(roles)
    assignment_required = (
        source_requirement_class == c.AtomicRowsSourceRequirementClass.AGENT_BINDING_REQUIRED.value
    )
    state = (
        c.AgentBindingState.OWNER_AGENT_ASSIGNMENT_REQUIRED.value
        if assignment_required
        else c.AgentBindingState.ROLE_BOUND_ONLY.value
    )
    no_orphan = (
        c.NoOrphanStatus.NOT_ORPHAN_OWNER_ASSIGNMENT_REQUEST_CREATED.value
        if assignment_required
        else c.NoOrphanStatus.NOT_ORPHAN_ROLE_BOUND.value
    )
    return {
        "responsible_agent_role_ids": roles,
        "applicable_agent_role_ids": roles,
        "candidate_agent_family_ids": [family_id],
        "consumer_class_ids": consumers,
        "parameter_owner_role": roles[0],
        "formula_owner_role": "SCORING_RESEARCH_STEWARD"
        if "SCORING_RESEARCH_STEWARD" in roles
        else "ATOMICROWS_COMPLETION_STEWARD",
        "risk_owner_role_if_applicable": "RISK_POLICY_STEWARD"
        if "RISK_POLICY_STEWARD" in roles
        else None,
        "execution_owner_role_if_applicable": "EXECUTION_BOUNDARY_STEWARD"
        if "EXECUTION_BOUNDARY_STEWARD" in roles
        else None,
        "quantum_owner_role_if_applicable": "QUANTUM_OPTIMIZER_RESEARCH_STEWARD"
        if "QUANTUM_OPTIMIZER_RESEARCH_STEWARD" in roles
        else None,
        "research_owner_role_if_applicable": "SCORING_RESEARCH_STEWARD"
        if "SCORING_RESEARCH_STEWARD" in roles
        else None,
        "dashboard_owner_role_if_applicable": "OWNER_DASHBOARD_POLICY_STEWARD",
        "agent_binding_state": state,
        "exact_agent_id_or_null": None,
        "explicit_agent_binding_required_flag": assignment_required,
        "agent_binding_source_ref_or_null": (
            "docs/master_plan/generated/AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json"
        ),
        "owner_agent_assignment_request_id_or_null": owner_assignment_request_id,
        "agent_binding_blocker_class": c.BlockerClass.OWNER_AGENT_ASSIGNMENT_REQUIRED.value
        if assignment_required
        else c.BlockerClass.NONE.value,
        "agent_binding_future_pr_route": "ELIGIBLE_FOR_AGENT_BINDING_PR163",
        "agent_binding_unblock_steps": [
            "Bind the row to an exact agent only after a supported agent map exists.",
            "Preserve the role and consumer-class mapping as the non-orphan fallback.",
            "Validate that binding creates no runtime, live, order, fill, or profit authority.",
        ],
        "no_orphan_status": no_orphan,
    }
