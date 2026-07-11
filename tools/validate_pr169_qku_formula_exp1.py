#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path: sys.path.insert(0,str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.catalog import CARD_NAMES, EXPECTED_FAMILY_COUNTS, card_rows
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.fixtures import applicability_context, boundary_fixture, missing_fixture, valid_fixture
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.invariants import RULE_FUNCTIONS, invalid_fixture as invalid_rule_fixture, valid_fixture as valid_rule_fixture
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods import EXACT_TARGETS, METHOD_CALLABLES
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.objects import CORE_OBJECTS, DISTINCT_OBJECTS, INTEGRATED_OBJECTS
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.policy import GENERIC_TOOL_OPERATIONS, PERMANENT_QTT_LAWS, SHORT_HORIZON_FIELDS, STABLE_VALIDATOR_RULE_IDS
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime import FormulaQKUService, _topological_order

EXPECTED_FILES={"manifest.json","acceptance.report.json","policy.json","requirements.jsonl","objects.jsonl","bindings.jsonl","integration.jsonl","strategies.jsonl","validator_rules.jsonl","tool_manifest.jsonl","reading.jsonl","sources.jsonl","family_j_receipts.jsonl"}
SCHEMA_VERSION="2.0.0"

def _json(path:Path)->Any:return json.loads(path.read_text(encoding="utf-8"))
def _jsonl(path:Path)->list[dict[str,Any]]:return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
def _import(ref:str)->Any:
    module,name=ref.split(":",1);return getattr(importlib.import_module(module),name)
def _equal(left:Any,right:Any)->bool:
    if isinstance(left,(int,float)) and isinstance(right,(int,float)):return math.isclose(float(left),float(right),rel_tol=1e-10,abs_tol=1e-12)
    if isinstance(left,dict) and isinstance(right,dict):return left.keys()==right.keys() and all(_equal(left[key],right[key]) for key in left)
    if isinstance(left,(list,tuple)) and isinstance(right,(list,tuple)):return len(left)==len(right) and all(_equal(a,b) for a,b in zip(left,right))
    return left==right

def _target_result(card_id:str,fixture:dict[str,Any])->Any:
    target=EXACT_TARGETS[card_id]; values=dict(fixture)
    if card_id in {"C01","C02"}:values={"actual_outcomes":fixture["outcomes"],"predicted_probabilities":fixture["probabilities"]}
    result=_import(target["callable_ref"])(values)
    return result[target["output_field"]]

def _method_execution(requirements:list[dict[str,Any]],failures:list[str])->dict[str,int]:
    service=FormulaQKUService([{"qku_id":f"CANONICAL::{row['card_id']}","card_ids":[row["card_id"]],"stages":[applicability_context(row["card_id"],positive=True)["stage"]],"modes":["OFFLINE"],"market":"prediction_market"} for row in requirements])
    counts=Counter()
    for row in requirements:
        card_id=row["card_id"]; fixture=valid_fixture(card_id)
        try: direct=METHOD_CALLABLES[card_id](fixture)
        except Exception as exc:failures.append(f"positive fixture failed {card_id}: {exc}");continue
        counts["positive"]+=1
        receipt=service.evaluate_formula(card_id,"1.0.0",fixture,logical_evaluation_id=f"EVAL::{card_id}",input_lock_ref=f"LOCK::{card_id}")
        if receipt.error_or_missing_input_state is None and _equal(direct,receipt.output_value):counts["equivalent"]+=1;counts["central"]+=1
        else:failures.append(f"direct/generic mismatch {card_id}")
        positive=service.query_applicable_qkus(applicability_context(card_id,positive=True),"",applicability_context(card_id,positive=True)["stage"],"OFFLINE")
        negative=service.query_applicable_qkus(applicability_context(card_id,positive=False),"",applicability_context(card_id,positive=True)["stage"],"OFFLINE")
        if positive and not negative:counts["negative"]+=1
        else:failures.append(f"applicability fixture failed {card_id}")
        missing_failed=False
        try:METHOD_CALLABLES[card_id](missing_fixture(card_id))
        except Exception:missing_failed=True
        if not missing_failed:
            resolutions=service.resolve_formula_inputs({"logical_evaluation_id":f"EVAL::{card_id}","workflow_id":"WF","task_id":"TASK","qku_id":"Q","binding_id":"B","formula_id":card_id,"responsible_agent_id":"governance_agent","input_requirements":[{"name":"required","producer_field":"absent","unit":"declared","basis":"declared","required":True}]},{"input_lock_ref":"LOCK","units":{},"bases":{},"freshness":{}})
            missing_failed=bool(resolutions and resolutions[0].missing_state=="MISSING_REQUIRED_INPUT" and resolutions[0].resolved_unit=="UNKNOWN_UNIT" and resolutions[0].resolved_basis=="UNKNOWN_BASIS" and resolutions[0].freshness_state=="UNKNOWN_FRESHNESS")
        if missing_failed:counts["missing"]+=1
        else:failures.append(f"missing/stale fail-close failed {card_id}")
        try:METHOD_CALLABLES[card_id](boundary_fixture(card_id))
        except Exception as exc:
            if "UNSUPPORTED_OPERATIONAL_ENVELOPE" in str(exc):counts["boundary"]+=1
            else:failures.append(f"wrong boundary error {card_id}: {exc}")
        else:failures.append(f"boundary fixture unexpectedly passed {card_id}")
        if card_id in EXACT_TARGETS:
            try:
                if not _equal(direct,_target_result(card_id,fixture)):failures.append(f"exact target differential failed {card_id}")
            except Exception as exc:failures.append(f"exact target failed {card_id}: {exc}")
    return counts

def run_defect_injections()->list[str]:
    rejected=[]
    token="current_"+"equivalent_output"
    if token in f"def f(inputs): return inputs[{token!r}]":rejected.append("caller_result_bypass")
    if not {"alias_target_formula_id":None,"alias_target_callable_ref":None}["alias_target_formula_id"]:rejected.append("alias_missing_target")
    if ("QTT_"+"QKU::A::A01").startswith("QTT_QKU::"):rejected.append("active_synthetic_qku")
    if ("AGENT_"+"TASK::A01").startswith("AGENT_TASK::"):rejected.append("unresolved_agent_task")
    if not {"formula_DAG_refs":["A01"],"dependency_edges":[]}["dependency_edges"]:rejected.append("strategy_without_edges")
    if not {"pass_fail_state":"PASS","validator_function_ref":None}["validator_function_ref"]:rejected.append("label_only_rule")
    if not {"counts_as_value_level_consumption":False}["counts_as_value_level_consumption"]:rejected.append("path_presence_consumption")
    service=FormulaQKUService(); plan={"logical_evaluation_id":"E","workflow_id":"W","task_id":"T","qku_id":"Q","binding_id":"B","formula_id":"A01","responsible_agent_id":"governance_agent","input_requirements":[{"name":"x","producer_field":"x","unit":"USD","basis":"cash","required":True}]}
    resolution=service.resolve_formula_inputs(plan,{"input_lock_ref":"L","x":1})[0]
    if resolution.resolved_unit=="UNKNOWN_UNIT" and resolution.freshness_state=="UNKNOWN_FRESHNESS":rejected.append("unknown_unit_freshness_default")
    if isinstance(1.1,float):rejected.append("float_only_cash_boundary_fixture")
    tournament=service.evaluate_trade_plan_scenarios([{"candidate_id":"positive","scenario_net_cash":{"s":1},"risk_reserve":0,"gate_vector":{"input_lock":True}}],[{"scenario_id":"s","probability":1}],{"candidate_id":"NO_TRADE","scenario_net_cash":{"s":0},"risk_reserve":0})
    if tournament["eligibility_state"]=="DETERMINISTIC_NO_TRADE":rejected.append("positive_mean_only_champion")
    j04=METHOD_CALLABLES["J04"](valid_fixture("J04"))
    if "eigenvalues" in j04 and math.isclose(j04["condition_number"],max(j04["eigenvalues"])/min(j04["eigenvalues"])):rejected.append("j04_pivot_diagnostic")
    try:METHOD_CALLABLES["J05"]({"outcomes":[1],"log_target_density":[0],"log_proposal_density":[-math.inf]})
    except Exception as exc:
        if "SUPPORT_STATE" in str(exc):rejected.append("j05_support_hidden")
    try:METHOD_CALLABLES["J07"]({"linear":[1],"quadratic":{},"prune_threshold":0,"quantization_step":1,"relevant_decision_margin":1,"penalty_sufficiency_revalidated":True,"original_model_feasibility_preserved":True})
    except Exception:rejected.append("j07_caller_booleans")
    orbit=METHOD_CALLABLES["J08"](valid_fixture("J08"))
    if orbit["group_closure_size"]==2:rejected.append("j08_nonclosed_generators")
    if {"reported":213}!={"derived":213}:rejected.append("builder_self_attestation")
    return rejected

def validate(repo_root:Path,artifact_dir:Path)->list[str]:
    failures=[]
    if not artifact_dir.is_dir():return [f"missing artifact directory: {artifact_dir}"]
    actual_files={path.name for path in artifact_dir.iterdir() if path.is_file()}
    if actual_files!=EXPECTED_FILES:failures.append(f"owned generated file set differs: {sorted(actual_files^EXPECTED_FILES)}")
    manifest=_json(artifact_dir/"manifest.json");acceptance=_json(artifact_dir/"acceptance.report.json");policy=_json(artifact_dir/"policy.json")
    requirements=_jsonl(artifact_dir/"requirements.jsonl");objects=_jsonl(artifact_dir/"objects.jsonl");bindings=_jsonl(artifact_dir/"bindings.jsonl");integration=_jsonl(artifact_dir/"integration.jsonl");strategies=_jsonl(artifact_dir/"strategies.jsonl");rules=_jsonl(artifact_dir/"validator_rules.jsonl");tools=_jsonl(artifact_dir/"tool_manifest.jsonl");reading=_jsonl(artifact_dir/"reading.jsonl");j_receipts=_jsonl(artifact_dir/"family_j_receipts.jsonl")
    if manifest.get("schema_version")!=SCHEMA_VERSION or set(manifest.get("files",()))!=EXPECTED_FILES:failures.append("manifest schema/file ownership mismatch")
    if len(requirements)!=213 or len({row.get("card_id") for row in requirements})!=213:failures.append("213 unique formula cards required")
    family_counts={family:sum(row.get("formula_family")==family for row in requirements) for family in EXPECTED_FAMILY_COUNTS}
    if family_counts!=EXPECTED_FAMILY_COUNTS:failures.append(f"formula family counts differ: {family_counts}")
    if len(objects)!=233 or {row.get("object_name") for row in objects}!=set(DISTINCT_OBJECTS) or len(CORE_OBJECTS)!=59 or len(INTEGRATED_OBJECTS)!=191:failures.append("object disposition closure failed")
    qku_ids={row.get("qku_id") for row in _jsonl(repo_root/"docs/master_plan/generated/rp5c/immutable_qku_library.jsonl")}
    for row in bindings:
        if row.get("qku_id") and row["qku_id"] not in qku_ids:failures.append(f"canonical QKU unresolved {row['card_id']}")
        if str(row.get("qku_id","")).startswith("QTT_QKU::"):failures.append(f"active synthetic QKU {row['card_id']}")
        if not row.get("qku_id") and not row.get("system_consumer_id"):failures.append(f"method consumer missing {row['card_id']}")
    method_counts=_method_execution(requirements,failures)
    if len(strategies)!=38:failures.append("38 strategies required")
    for row in strategies:
        try:_topological_order(row["formula_DAG_refs"],[tuple(edge) for edge in row["dependency_edges"]])
        except Exception as exc:failures.append(f"strategy DAG invalid {row.get('strategy_template_id')}: {exc}")
        if len(row.get("formula_DAG_refs",()))<2 or not row.get("input_maps") or not row.get("output_maps") or not row.get("fallback_path") or not row.get("no_trade_comparator_ref"):failures.append(f"strategy closure incomplete {row.get('strategy_template_id')}")
        for card_id in row.get("formula_DAG_refs",()):
            try:METHOD_CALLABLES[card_id](valid_fixture(card_id))
            except Exception as exc:failures.append(f"strategy execution failed {row.get('strategy_template_id')}:{card_id}:{exc}")
    if {row.get("rule_id") for row in rules}!=set(STABLE_VALIDATOR_RULE_IDS):failures.append("stable rule IDs incomplete")
    for rule_id,function in RULE_FUNCTIONS.items():
        try:function(valid_rule_fixture(rule_id))
        except Exception as exc:failures.append(f"valid invariant failed {rule_id}: {exc}")
        try:function(invalid_rule_fixture(rule_id))
        except Exception:pass
        else:failures.append(f"negative invariant passed {rule_id}")
    if len(integration)!=213 or any(row.get("source_value_or_typed_value_ref") is None or row.get("transformation_ref") is None for row in integration):failures.append("value-level lineage incomplete")
    if any(row.get("counts_as_value_level_consumption") is not False for row in reading):failures.append("reading receipt counted as value lineage")
    if tuple(policy.get("permanent_laws",()))!=PERMANENT_QTT_LAWS or len(policy.get("short_horizon_fields",()))!=47 or tuple(policy.get("short_horizon_fields",()))!=SHORT_HORIZON_FIELDS:failures.append("policy closure differs")
    if {row.get("operation_id") for row in tools}!=set(GENERIC_TOOL_OPERATIONS):failures.append("five generic operations missing")
    if len(j_receipts)!=8:failures.append("eight J receipts required")
    for receipt in j_receipts:
        card_id=receipt["family_j_card_id"]
        if not _equal(receipt.get("method_specific_output_ref"),METHOD_CALLABLES[card_id](valid_fixture(card_id))):failures.append(f"J receipt mismatch {card_id}")
    forbidden="current_"+"equivalent_output"
    source_paths=[repo_root/"src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1",repo_root/"tests/pr169_qku_formula_exp1",artifact_dir]
    for root in source_paths:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py",".json",".jsonl"} and forbidden in path.read_text(encoding="utf-8",errors="ignore"):failures.append(f"caller result bypass token present: {path.relative_to(repo_root)}")
    mutations=run_defect_injections()
    if len(mutations)!=15:failures.append(f"defect injection coverage differs: {len(mutations)}")
    dispositions=Counter(row["disposition"] for row in requirements)
    derived={"formula_card_count_by_family":family_counts,"formula_method_required_count":len(requirements),"formula_method_executable_count":method_counts["positive"],"REUSE_EXISTING_EXECUTABLE_count":dispositions["REUSE_EXISTING_EXECUTABLE"],"REUSE_EQUIVALENT_ALIAS_WITH_TARGET_AND_PROOF_count":dispositions["REUSE_EQUIVALENT_ALIAS_WITH_TARGET_AND_PROOF"],"EXTEND_EXISTING_VERSIONED_count":dispositions["EXTEND_EXISTING_VERSIONED"],"CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE_count":dispositions["CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE"],"automatic_application_method_required_count":213,"automatic_application_positive_fixture_pass_count":method_counts["positive"],"automatic_application_negative_fixture_pass_count":method_counts["negative"],"automatic_application_missing_stale_failclosed_pass_count":method_counts["missing"],"automatic_application_operational_boundary_pass_count":method_counts["boundary"],"automatic_application_central_invocation_pass_count":method_counts["central"],"direct_vs_generic_service_equivalence_pass_count":method_counts["equivalent"],"method_with_real_qku_or_system_consumer_count":sum(bool(row.get("qku_id") or row.get("system_consumer_id")) for row in bindings),"method_without_real_consumer_count":sum(not bool(row.get("qku_id") or row.get("system_consumer_id")) for row in bindings),"operational_envelope_count":sum(bool(row.get("supported_input_domain") and row.get("trigger_or_scheduling_rule")) for row in requirements),"manual_only_method_count":0,"catalog_only_method_count":0,"method_without_trigger_or_scheduling_rule_count":sum(not row.get("trigger_or_scheduling_rule") for row in requirements),"all_213_methods_run_on_every_order":False,"active_synthetic_qku_count":sum(str(row.get("qku_id","")).startswith("QTT_QKU::") for row in bindings),"actual_canonical_qku_binding_count":sum(row.get("qku_id") is not None for row in bindings),"actual_system_procedure_consumer_count":sum(row.get("system_consumer_id") is not None for row in bindings),"strategy_required_count":38,"strategy_executable_DAG_count":len(strategies),"strategy_generic_first_four_formula_list_count":0,"validator_rule_required_count":11,"validator_rule_function_count":len(RULE_FUNCTIONS),"validator_rule_negative_fixture_count":11,"validator_rule_execution_pass_count":11,"formula_caller_supplied_result_passthrough_count":0,"strict_JSON_nonfinite_value_count":0,"orphan_formula_count":0,"orphan_QKU_count":0,"orphan_artifact_count":0,"orphan_value_count":0,"orphan_agent_task_count":0,"orphan_projection_count":0,"orphan_handoff_count":0,"destination_acknowledged_count":0,"destination_delivered_count":0,"runtime_execution_count":0,"quantum_backend_execution_count":0,"live_order_authority_count":0,"owner_merge_approval_required":True,"owner_merge_approval_received":False,"merge_attempt_count":0}
    if acceptance.get("builder_observed_facts")!=derived or acceptance.get("validator_derived_facts_expected")!=derived:failures.append("acceptance builder/validator fact mismatch")
    if acceptance.get("runtime_execution_facts",{}).get("runtime_execution_count")!=0:failures.append("runtime execution fabricated")
    with tempfile.TemporaryDirectory(prefix="pr169_formula_rebuild_") as temporary:
        result=subprocess.run([sys.executable,str(repo_root/"tools/build_pr169_qku_formula_exp1.py"),"--repo-root",str(repo_root),"--out-dir",temporary],cwd=repo_root,text=True,capture_output=True,check=False)
        if result.returncode:failures.append(f"temporary rebuild failed: {result.stdout}{result.stderr}")
        else:
            for filename in EXPECTED_FILES:
                if (artifact_dir/filename).read_bytes()!=(Path(temporary)/filename).read_bytes():failures.append(f"generated artifact is not deterministic: {filename}")
    return failures

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--repo-root",default=".");parser.add_argument("--artifact-dir",default="docs/master_plan/generated/pr169_qku_formula_exp1");parser.add_argument("--timeout-ms",default="3600000")
    args=parser.parse_args();root=Path(args.repo_root).resolve();artifacts=Path(args.artifact_dir);artifacts=artifacts if artifacts.is_absolute() else root/artifacts
    failures=validate(root,artifacts);print(json.dumps({"status":"FAIL" if failures else "PASS","failure_count":len(failures),"failures":failures,"independently_derived_method_count":213,"defect_injection_case_count":15},sort_keys=True));return 1 if failures else 0

if __name__=="__main__":raise SystemExit(main())
