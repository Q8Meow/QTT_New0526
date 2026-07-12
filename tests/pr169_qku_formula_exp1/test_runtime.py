from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime import EconomicComponentLedgerEntryV1, EconomicComponentLedgerV1, FormulaQKUService


class _FakeResolver:
    def __init__(self) -> None:
        self.rows=({"qku_id":"QKU-B"},{"qku_id":"QKU-A"})

    def query(self, context, agent_duty, stage, mode):
        del context,agent_duty,stage,mode
        return self.rows


def test_bounded_query_input_resolution_and_stable_retry_identity() -> None:
    service=FormulaQKUService(_FakeResolver())
    rows=service.query_applicable_qkus({"market":"synthetic","query_limit":1},"risk","PRETRADE","SHADOW")
    assert [row["qku_id"] for row in rows]==["QKU-A"]
    resolution_plan={"logical_evaluation_id":"eval-1","workflow_id":"wf","task_id":"task","qku_id":"QKU-A","binding_id":"bind","formula_id":"C01","responsible_agent_id":"risk_manager_agent","input_requirements":[{"name":"probabilities","unit":"probability","basis":"calibrated_binary","producer_field":"p"},{"name":"outcomes","unit":"binary","basis":"observed","producer_field":"y"}]}
    resolved=service.resolve_formula_inputs(resolution_plan,{"input_lock_ref":"lock","p":[0.5],"y":[1],"units":{"p":"probability","y":"binary"},"bases":{"p":"calibrated_binary","y":"observed"},"freshness":{"p":"FRESH","y":"FRESH"}})
    assert all(row.missing_state is None and row.conflict_state is None for row in resolved)
    plan=service.construct_formula_plan(formula_id="C01",logical_evaluation_id="eval-1",input_lock_ref="lock",qku_id="QKU-A",consumer_ref="TEST")
    first=service.evaluate_formula(plan,resolved,attempt_number=1)
    retry=service.evaluate_formula(plan,resolved,attempt_number=2)
    assert first.logical_evaluation_id==retry.logical_evaluation_id
    assert first.output_value==retry.output_value==pytest.approx(0.25)
    with ThreadPoolExecutor(max_workers=8) as pool:
        concurrent=list(pool.map(lambda attempt:service.evaluate_formula(plan,resolved,attempt_number=attempt),range(3,19)))
    assert all(receipt is first for receipt in concurrent)


def test_dag_cycle_fails_and_trade_scenarios_keep_no_trade() -> None:
    service=FormulaQKUService()
    with pytest.raises(Exception,match="CYCLE"):
        service.evaluate_qku_dag("Q",[{"formula_id":"A01","dependency_edges":[["A01","A02"]]},{"formula_id":"A02","dependency_edges":[["A02","A01"]]}],{"logical_evaluation_id":"eval","input_lock_ref":"lock"})
    result=service.evaluate_trade_plan_scenarios([{"candidate_id":"maker","input_lock_ref":"lock","scenario_net_cash":{"s":-1},"risk_reserve":0,"gate_receipts":[]}], [{"scenario_id":"s","probability":1}], {"candidate_id":"NO_TRADE","scenario_net_cash":{"s":0},"risk_reserve":0,"comparator_receipt":{"owner":"CANONICAL_OWNER::no_trade","validation_state":"VALID"}})
    assert result["eligibility_state"]=="DETERMINISTIC_NO_TRADE"
    assert result["authority_state"]=="CANDIDATE_ONLY_NO_ORDER_AUTHORITY"


def test_unit_conflict_and_missing_critical_input_are_typed() -> None:
    service=FormulaQKUService(); plan={"logical_evaluation_id":"e","workflow_id":"w","task_id":"t","qku_id":"q","binding_id":"b","formula_id":"A06","responsible_agent_id":"parameter_selector_agent","input_requirements":[{"name":"cash","unit":"USD","producer_field":"cash"},{"name":"seconds","unit":"seconds","producer_field":"seconds"}]}
    rows=service.resolve_formula_inputs(plan,{"input_lock_ref":"lock","cash":1,"units":{"cash":"EUR"}})
    assert rows[0].conflict_state=="UNIT_MISMATCH"
    assert rows[1].missing_state=="MISSING_REQUIRED_INPUT"


def test_clean_process_production_composition_root() -> None:
    root=Path(__file__).resolve().parents[2]
    code=r'''
from qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime import FormulaQKUService
service=FormulaQKUService()
qku="QKU_PMKT_EDGE_EXPECTED_VALUE_AND_PAYOFF_019"
assert service.query_applicable_qkus({"qku_ids":[qku],"market":"prediction_market"},"risk_manager_agent","PRETRADE","OFFLINE")
bindings=[
 {"formula_id":"A03","version":"1.0.0","binding_id":"B::A03","input_map":{"probabilities":"A03::probabilities","branch_net_cash":"A03::branch_net_cash"},"input_units":{"probabilities":"declared","branch_net_cash":"declared"},"input_bases":{"probabilities":"declared","branch_net_cash":"declared"},"dependency_edges":[["A03","A05"]],"output_field":"expected_cash"},
 {"formula_id":"A05","version":"1.0.0","binding_id":"B::A05","input_map":{"estimator_samples":"A05::estimator_samples","lower_quantile":"A05::lower_quantile","upper_quantile":"A05::upper_quantile","confidence_method":"A05::confidence_method"},"input_units":{"estimator_samples":"declared","lower_quantile":"declared","upper_quantile":"declared","confidence_method":"declared"},"input_bases":{"estimator_samples":"declared","lower_quantile":"declared","upper_quantile":"declared","confidence_method":"declared"},"dependency_edges":[["A03","A05"]],"output_field":"cash_lcb"},
]
lock={"logical_evaluation_id":"CLEAN","input_lock_ref":"LOCK","lock_identity_ref":"LOCK","workflow_id":"CLEAN_PROCESS","A03::probabilities":[0.5,0.5],"A03::branch_net_cash":[-1,2],"A05::estimator_samples":[-1,0,1,2,3],"A05::lower_quantile":0.2,"A05::upper_quantile":0.8,"A05::confidence_method":"DEPENDENCE_AWARE_BOOTSTRAP"}
keys=[key for key in lock if "::" in key]; lock["units"]={key:"declared" for key in keys}; lock["bases"]={key:"declared" for key in keys}; lock["freshness"]={key:"TIME_INDEPENDENT_MATHEMATICS" for key in keys}
receipts=service.evaluate_qku_dag(qku,bindings,lock)
assert len(receipts)==2 and all(row.error_or_missing_input_state is None for row in receipts)
assert receipts[-1].output_value is not None
'''
    env={**os.environ,"PYTHONPATH":os.pathsep.join([str(root/"src"),str(root)])}
    with tempfile.TemporaryDirectory(prefix="qtt_clean_process_") as temporary:
        result=subprocess.run([sys.executable,"-c",code],cwd=temporary,env=env,text=True,capture_output=True,check=False)
        assert result.returncode==0,result.stdout+result.stderr


def test_point_in_time_leakage_and_snapshot_controls_fail_closed() -> None:
    service=FormulaQKUService(); plan={"logical_evaluation_id":"pit","workflow_id":"wf","task_id":"task","qku_id":"q","binding_id":"b","formula_id":"A03","responsible_agent_id":"risk_manager_agent","input_requirements":[{"name":"probabilities","producer_field":"p","unit":"declared","basis":"declared","time_information_class":"PREDECISION_POINT_IN_TIME","leakage_control_required":True}]}
    base={"p":[0.5,0.5],"units":{"p":"declared"},"bases":{"p":"declared"},"freshness":{"p":"FRESH"},"source_event_times":{"p":"2026-01-01T00:00:00Z"},"source_available_times":{"p":"2026-01-01T00:00:02Z"},"input_lock_time":"2026-01-01T00:00:03Z","decision_time":"2026-01-01T00:00:04Z","purge_ref":"PURGE","embargo_ref":"EMBARGO","split_ref":"SPLIT","snapshot_coherence_state":"COHERENT"}
    assert service.resolve_formula_inputs(plan,base)[0].conflict_state is None
    future={**base,"source_available_times":{"p":"2026-01-01T00:00:05Z"}}
    assert service.resolve_formula_inputs(plan,future)[0].conflict_state=="POINT_IN_TIME_VIOLATION"
    no_leakage={key:value for key,value in base.items() if key not in {"purge_ref","embargo_ref","split_ref"}}
    assert service.resolve_formula_inputs(plan,no_leakage)[0].conflict_state=="MISSING_LEAKAGE_CONTROL"
    incoherent={**base,"snapshot_coherence_state":"OUT_OF_SEQUENCE"}
    assert service.resolve_formula_inputs(plan,incoherent)[0].conflict_state=="SNAPSHOT_COHERENCE_FAILURE"


def test_economic_component_ledger_allows_attribution_but_rejects_rededuction() -> None:
    ledger=EconomicComponentLedgerV1()
    cash=EconomicComponentLedgerEntryV1("LOCK","FILL-1","fee","EMBEDDED_IN_EXECUTABLE_FILL_CASH",Decimal("1.25"),"FILL_RECEIPT::fee")
    attribution=EconomicComponentLedgerEntryV1("LOCK","FILL-1","fee","TCA_ATTRIBUTION_ONLY",Decimal("1.25"),"TCA_RECEIPT::fee")
    assert ledger.register(cash)==cash and ledger.register(attribution)==attribution
    with pytest.raises(Exception,match="DUPLICATE_ECONOMIC_COMPONENT_INCLUSION"):
        ledger.register(EconomicComponentLedgerEntryV1("LOCK","FILL-1","fee","EXPLICIT_LEDGER_CASH_COST",Decimal("1.25"),"LEDGER::fee"))
