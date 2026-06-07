"""Computability disposition materializer."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields
from .central_reason_codes import COMPUTABILITY_DISPOSITIONS, require_enum
from .deterministic_ids import plain_ref


def disposition_for(identity: dict[str, Any]) -> str:
    if identity["candidate_id"]:
        return "COMPUTABLE_WITH_CANDIDATE_VALUES_FOR_REPLAY_PAPER"
    if identity["activation_state"] == "DORMANT_NON_STAGE1_MARKET":
        return "DORMANT_NON_STAGE1_BUT_COMPUTABLE"
    if identity["market_scope"] == "UNKNOWN_MARKET_SCOPE_OWNER_REVIEW":
        return "COMPUTABLE_AFTER_MARKET_SCOPE_REPAIR"
    return "COMPUTABLE_AFTER_EXACT_MISSING_VALUE_FILL"


def build_computability_rows(
    identity_rows: list[dict[str, Any]],
    formula_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    formula_by_qku = {row["qku_id"]: row for row in formula_rows}
    rows: list[dict[str, Any]] = []
    for index, identity in enumerate(identity_rows, 1):
        disposition = require_enum(disposition_for(identity), COMPUTABILITY_DISPOSITIONS, "computability_disposition")
        formula = formula_by_qku[identity["qku_id"]]
        missing = disposition in {
            "COMPUTABLE_AFTER_EXACT_MISSING_VALUE_FILL",
            "COMPUTABLE_AFTER_FORMULA_FAMILY_EXPANSION",
            "COMPUTABLE_AFTER_MARKET_SCOPE_REPAIR",
        }
        rows.append(
            {
                "computability_materialization_ref": plain_ref("COMPUTABILITY", index),
                "qku_id": identity["qku_id"],
                "candidate_id": identity["candidate_id"],
                "evidence_id": identity["evidence_id"],
                "canonical_identity_status": identity["canonical_identity_status"],
                "market_scope": identity["market_scope"],
                "activation_state": identity["activation_state"],
                "computability_disposition": disposition,
                "computability_reason": _reason(disposition),
                "qku_formula_id": formula["qku_formula_id"],
                "formula_name": formula["formula_name"],
                "formula_expression": formula["formula_expression"],
                "objective_expression": formula["objective_expression"],
                "input_fields": formula["input_fields"],
                "output_fields": formula["output_fields"],
                "parameter_fields": formula["parameter_fields"],
                "parameter_domain": formula["parameter_domain"],
                "algorithm_family": formula["algorithm_family"],
                "solver_family": formula["solver_family"],
                "event_contract_assumptions": formula["event_contract_assumptions"],
                "expected_net_profit_candidate_formula": formula["expected_net_profit_candidate_formula"],
                "execution_cost_component_refs": [
                    f"PR164_EXEC_COST::{index:06d}::exchange_fee_cost",
                    f"PR164_EXEC_COST::{index:06d}::spread_crossing_cost",
                    f"PR164_EXEC_COST::{index:06d}::slippage_cost",
                    f"PR164_EXEC_COST::{index:06d}::latency_adverse_selection_cost",
                    f"PR164_EXEC_COST::{index:06d}::queue_position_or_fill_probability_cost",
                    f"PR164_EXEC_COST::{index:06d}::cancel_replace_cost",
                    f"PR164_EXEC_COST::{index:06d}::capital_lock_cost",
                    f"PR164_EXEC_COST::{index:06d}::settlement_delay_cost",
                    f"PR164_EXEC_COST::{index:06d}::operational_error_penalty",
                    f"PR164_EXEC_COST::{index:06d}::market_lifecycle_penalty",
                    f"PR164_EXEC_COST::{index:06d}::stale_data_penalty",
                ],
                "latency_cost_formula": formula["latency_cost_formula"],
                "risk_penalty_formula": formula["risk_penalty_formula"],
                "test_vector_ref": formula["test_vector_ref"],
                "expected_test_vector_output": formula["expected_test_vector_output"],
                "replay_adapter_consumer": formula["replay_adapter_consumer"],
                "paper_adapter_consumer": formula["paper_adapter_consumer"],
                "pr165_scoring_consumer": formula["pr165_scoring_consumer"],
                "downstream_agent_consumers": formula["downstream_agent_consumers"],
                "missing_field_fill_task_ref": f"PR164_MISSING_FILL::{index:06d}" if missing else "",
                "replay_paper_materialization_route": (
                    "REPLAY_PAPER_ROUTE_READY_WITH_CANDIDATE_VALUES"
                    if identity["candidate_id"]
                    else "REPLAY_PAPER_ROUTE_AFTER_EXACT_FILL"
                ),
                "pr165_scoring_readiness_route": (
                    "ROUTE_TO_PR165_SCORING"
                    if identity["candidate_id"]
                    else "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR"
                ),
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows


def _reason(disposition: str) -> str:
    return {
        "COMPUTABLE_WITH_CANDIDATE_VALUES_FOR_REPLAY_PAPER": "Current CandidatePacketV1 row has formula/objective/input/output/test-vector materialization; source values remain candidate values for replay/paper only.",
        "COMPUTABLE_AFTER_EXACT_MISSING_VALUE_FILL": "Historical QKU needs exact CandidatePacketV1 fill before replay/paper materialization.",
        "COMPUTABLE_AFTER_MARKET_SCOPE_REPAIR": "Market scope must be repaired before formula family route can be consumed.",
        "DORMANT_NON_STAGE1_BUT_COMPUTABLE": "Non-Stage-1 market QKU remains dormant and is retained with a computable control-plane route.",
    }.get(disposition, "Central PR164 disposition with exact downstream route.")
