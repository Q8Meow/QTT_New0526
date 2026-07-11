from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.catalog import CARD_NAMES
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.fixtures import boundary_fixture, valid_fixture
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.invariants import RULE_FUNCTIONS, invalid_fixture as invalid_rule_fixture, valid_fixture as valid_rule_fixture
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods import METHOD_CALLABLES
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime import FormulaQKUService, _topological_order
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.strategies import strategy_rows
from tools.validate_pr169_qku_formula_exp1 import run_defect_injections


ROOT=Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("card_id",[card_id for card_id,_ in CARD_NAMES])
def test_every_method_executes_direct_and_generic_and_has_boundary(card_id: str) -> None:
    fixture=valid_fixture(card_id); direct=METHOD_CALLABLES[card_id](fixture)
    receipt=FormulaQKUService().evaluate_formula(card_id,"1.0.0",fixture,logical_evaluation_id=f"E::{card_id}",input_lock_ref=f"L::{card_id}")
    assert receipt.error_or_missing_input_state is None
    assert receipt.output_value==direct
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
    valid={"candidate_id":"candidate","scenario_net_cash":{"s":2},"risk_reserve":0,"gate_vector":{key:True for key in required}}
    no_trade={"candidate_id":"NO_TRADE","scenario_net_cash":{"s":0},"risk_reserve":0}
    assert service.evaluate_trade_plan_scenarios([valid],scenarios,no_trade)["eligibility_state"]=="CHAMPION_ELIGIBLE"
    invalid={**valid,"gate_vector":{**valid["gate_vector"],"tca":False}}
    assert service.evaluate_trade_plan_scenarios([invalid],scenarios,no_trade)["eligibility_state"]=="DETERMINISTIC_NO_TRADE"


def test_mutation_regressions_reject_all_15_baseline_defects() -> None:
    rejected=run_defect_injections()
    assert len(rejected)==15 and len(set(rejected))==15


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
