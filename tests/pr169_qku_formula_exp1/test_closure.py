from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.catalog import CARD_NAMES
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.fixtures import boundary_fixture, valid_fixture
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.invariants import RULE_FUNCTIONS, invalid_fixture as invalid_rule_fixture, valid_fixture as valid_rule_fixture
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods import METHOD_CALLABLES
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime import FormulaQKUService, _topological_order
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.strategies import strategy_rows


ROOT=Path(__file__).resolve().parents[2]


def _evaluate_through_service(service: FormulaQKUService, card_id: str, fixture: dict) -> object:
    material={key:value for key,value in fixture.items() if key!="__problem_size__"}
    plan=service.construct_formula_plan(formula_id=card_id,logical_evaluation_id=f"E::{card_id}",input_lock_ref=f"L::{card_id}",qku_id="FIXTURE_QKU",consumer_ref="TEST")
    resolution_plan={"logical_evaluation_id":f"E::{card_id}","workflow_id":"W","task_id":"T","qku_id":"FIXTURE_QKU","binding_id":f"B::{card_id}","formula_id":card_id,"responsible_agent_id":"governance_agent","input_requirements":[{"name":name,"producer_field":name,"unit":"declared","basis":"declared"} for name in material]}
    lock={**material,"units":{name:"declared" for name in material},"bases":{name:"declared" for name in material},"freshness":{name:"FRESH" for name in material}}
    return service.evaluate_formula(plan,service.resolve_formula_inputs(resolution_plan,lock)).output_value


@pytest.mark.parametrize("card_id",[card_id for card_id,_ in CARD_NAMES])
def test_every_method_executes_direct_and_generic_and_has_boundary(card_id: str) -> None:
    fixture=valid_fixture(card_id); direct=METHOD_CALLABLES[card_id](fixture)
    assert _evaluate_through_service(FormulaQKUService(),card_id,fixture)==direct
    with pytest.raises(Exception,match="UNSUPPORTED_OPERATIONAL_ENVELOPE"):
        METHOD_CALLABLES[card_id](boundary_fixture(card_id))


def test_38_strategy_dags_are_distinct_acyclic_and_executable() -> None:
    rows=strategy_rows()
    assert len(rows)==38 and len({tuple(row["formula_DAG_refs"]) for row in rows})==38
    for row in rows:
        assert _topological_order(row["formula_DAG_refs"],[tuple(edge) for edge in row["dependency_edges"]])
        assert row["input_maps"] and row["output_maps"] and row["fallback_path"] and row["no_trade_comparator_ref"]=="A25"
        for card_id in row["formula_DAG_refs"]:
            METHOD_CALLABLES[card_id](valid_fixture(card_id))


def test_11_invariants_execute_and_reject_negative_fixtures() -> None:
    assert len(RULE_FUNCTIONS)==11
    for rule_id,function in RULE_FUNCTIONS.items():
        assert function(valid_rule_fixture(rule_id))
        with pytest.raises(Exception,match="INVARIANT_VIOLATION"):
            function(invalid_rule_fixture(rule_id))


def test_complete_champion_gate_and_no_trade_precedence() -> None:
    service=FormulaQKUService(); scenarios=[{"scenario_id":"s","probability":1.0}]
    required=("input_lock","formula_dag","accounting","original_model","net_cash_lcb","no_trade_margin","tca","fill","latency_ttl","capacity","portfolio_tail_risk","calibration_scenarios","overfit_fdr","agent_no_orphan")
    receipts=[{"gate_id":key,"owner":f"CANONICAL_OWNER::{key}","version":"1.0.0","input_lock_ref":"lock","validation_state":"VALID","freshness_state":"FRESH","passed":True} for key in required]
    valid={"candidate_id":"candidate","input_lock_ref":"lock","scenario_net_cash":{"s":2},"risk_reserve":0,"gate_receipts":receipts}
    no_trade={"candidate_id":"NO_TRADE","scenario_net_cash":{"s":0},"risk_reserve":0,"comparator_receipt":{"owner":"CANONICAL_OWNER::no_trade","validation_state":"VALID"}}
    assert service.evaluate_trade_plan_scenarios([valid],scenarios,no_trade)["eligibility_state"]=="CHAMPION_ELIGIBLE"
    invalid={**valid,"gate_receipts":[{**row,"passed":False} if row["gate_id"]=="tca" else row for row in receipts]}
    assert service.evaluate_trade_plan_scenarios([invalid],scenarios,no_trade)["eligibility_state"]=="DETERMINISTIC_NO_TRADE"


def test_real_mutation_regressions_reject_actual_temporary_copies() -> None:
    result=subprocess.run([sys.executable,str(ROOT/"tools/validate_pr169_qku_formula_exp1.py"),"--repo-root",str(ROOT),"--skip-determinism"],cwd=ROOT,text=True,capture_output=True,check=False)
    assert result.returncode==0,result.stdout+result.stderr
    payload=json.loads(result.stdout)
    assert payload["defect_injection_case_count"]>=18
    assert payload["validator_independently_derived_facts"]["real_temporary_mutation_case_count"]>=18


def test_generated_surface_is_single_strict_migrated_plane() -> None:
    root=ROOT/"docs/master_plan/generated/pr169_qku_formula_exp1"
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"]=="2.0.0" and len(manifest["files"])==13
    bindings=[json.loads(line) for line in (root/"bindings.jsonl").read_text(encoding="utf-8").splitlines()]
    assert not any(str(row.get("qku_id","")).startswith("QTT_QKU::") for row in bindings)
    assert all(row.get("qku_id") or row.get("system_consumer_id") for row in bindings)
    receipt=json.loads(next(line for line in (root/"family_j_receipts.jsonl").read_text(encoding="utf-8").splitlines() if '"J07"' in line))
    assert math.isfinite(float(receipt["method_specific_output_ref"]["maximum_objective_distortion_bound"]))
    assert receipt["method_specific_output_ref"]["decision_margin_to_two_bound_ratio"]!="Infinity"


def test_thirteen_formula_definition_currentizations() -> None:
    with pytest.raises(Exception): METHOD_CALLABLES["A32"]({"own_fee_equivalent":0,"total_fee_equivalent":0,"rebate_pool":1})
    c25=METHOD_CALLABLES["C25"]({"previous_mean":1,"previous_second_moment":2,"return_value":3,"eta":0.25})
    assert c25["innovation_a"]==2 and c25["updated_mean"]==pytest.approx(1.5)
    f03=METHOD_CALLABLES["F03"]({"linear":[1,2],"quadratic_upper":{"0,1":3},"offset":4})
    assert f03["coefficient_convention"]=="LINEAR_PLUS_STRICT_UPPER_TRIANGULAR"
    f06=METHOD_CALLABLES["F06"]({"linear":[2],"quadratic_upper":{},"offset":5,"scale":2,"centering_constant":1})
    assert f06["linear_scaled"]==[1] and f06["inverse_map"]=={"scale":2.0,"centering_constant":1.0}
    with pytest.raises(Exception): METHOD_CALLABLES["F21"]({"bitstrings":[[1,0]]})
    assert METHOD_CALLABLES["F24"]({"objective_candidate":3,"objective_classical_champion":2,"objective_sense":"MINIMIZE"})["suboptimality_gap"]==1
    assert METHOD_CALLABLES["F24"]({"objective_candidate":3,"objective_classical_champion":2,"objective_sense":"MAXIMIZE"})["improvement_gap"]==1
    assert METHOD_CALLABLES["F40"]({"sample_chain_broken":[[True,False],[False,False]]})["observed_sample_chain_pairs"]==4
    with pytest.raises(Exception): METHOD_CALLABLES["G09"]({"valid_runs":0,"successful_valid_runs":0})
    with pytest.raises(Exception): METHOD_CALLABLES["G14"]({"frontier":[[1,1]],"candidate":[2,2],"reference_point":[3,3],"objective_senses":["MAXIMIZE","MAXIMIZE"]})
    with pytest.raises(Exception): METHOD_CALLABLES["H11"]({"features":[]})
    i04=METHOD_CALLABLES["I04"]({"requirements":[]})
    assert i04["coverage"]==1 and i04["coverage_state"]=="NO_REQUIRED_INPUTS"
    with pytest.raises(Exception): METHOD_CALLABLES["I05"]({"fields":[{"kind":"numeric","left":1,"right":1,"range":1,"weight":0,"valid":True}]})
    with pytest.raises(Exception): METHOD_CALLABLES["I07"]({"reference_time":1,"windows":[{"valid_from":1,"valid_until":1}]})
