from __future__ import annotations

import pytest

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime import FormulaQKUService


def test_bounded_query_input_resolution_and_stable_retry_identity() -> None:
    service=FormulaQKUService([{"qku_id":"QKU-B","agent_duties":["risk"],"stages":["PRETRADE"],"modes":["SHADOW"],"market":"synthetic"},{"qku_id":"QKU-A","agent_duties":["risk"],"stages":["PRETRADE"],"modes":["SHADOW"],"market":"synthetic"}])
    rows=service.query_applicable_qkus({"market":"synthetic","query_limit":1},"risk","PRETRADE","SHADOW")
    assert [row["qku_id"] for row in rows]==["QKU-A"]
    plan={"logical_evaluation_id":"eval-1","workflow_id":"wf","task_id":"task","qku_id":"QKU-A","binding_id":"bind","formula_id":"C01","responsible_agent_id":"risk_manager_agent","input_requirements":[{"name":"probabilities","unit":"probability","basis":"calibrated_binary","producer_field":"p"}]}
    resolved=service.resolve_formula_inputs(plan,{"input_lock_ref":"lock","p":[0.5],"units":{"p":"probability"},"bases":{"p":"calibrated_binary"},"freshness":{"p":"FRESH"}})
    assert resolved[0].missing_state is None and resolved[0].conflict_state is None
    first=service.evaluate_formula("C01","1.0.0",{"probabilities":[0.5],"outcomes":[1]},logical_evaluation_id="eval-1",input_lock_ref="lock",attempt_number=1)
    retry=service.evaluate_formula("C01","1.0.0",{"probabilities":[0.5],"outcomes":[1]},logical_evaluation_id="eval-1",input_lock_ref="lock",attempt_number=2)
    assert first.logical_evaluation_id==retry.logical_evaluation_id
    assert first.output_value==retry.output_value==pytest.approx(0.25)


def test_dag_cycle_fails_and_trade_scenarios_keep_no_trade() -> None:
    service=FormulaQKUService()
    with pytest.raises(Exception,match="CYCLE"):
        service.evaluate_qku_dag("Q",[{"formula_id":"A01","dependency_edges":[["A01","A02"]]},{"formula_id":"A02","dependency_edges":[["A02","A01"]]}],{"logical_evaluation_id":"eval","input_lock_ref":"lock"})
    result=service.evaluate_trade_plan_scenarios([{"candidate_id":"maker","scenario_net_cash":{"s":-1},"risk_reserve":0}], [{"scenario_id":"s","probability":1}], {"candidate_id":"NO_TRADE","scenario_net_cash":{"s":0},"risk_reserve":0})
    assert result["eligibility_state"]=="DETERMINISTIC_NO_TRADE"
    assert result["authority_state"]=="CANDIDATE_ONLY_NO_ORDER_AUTHORITY"


def test_unit_conflict_and_missing_critical_input_are_typed() -> None:
    service=FormulaQKUService(); plan={"logical_evaluation_id":"e","workflow_id":"w","task_id":"t","qku_id":"q","binding_id":"b","formula_id":"A06","responsible_agent_id":"parameter_selector_agent","input_requirements":[{"name":"cash","unit":"USD","producer_field":"cash"},{"name":"seconds","unit":"seconds","producer_field":"seconds"}]}
    rows=service.resolve_formula_inputs(plan,{"input_lock_ref":"lock","cash":1,"units":{"cash":"EUR"}})
    assert rows[0].conflict_state=="UNIT_MISMATCH"
    assert rows[1].missing_state=="MISSING_REQUIRED_INPUT"
