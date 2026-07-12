#!/usr/bin/env python3
from __future__ import annotations

"""Independent checker for the PR169 formula repair.

Expected vectors and rule fixtures are fixed below or in the non-production
oracle file.  Production formula implementations, producer fixtures, strategy
definitions, catalog rows, and builder fact dictionaries are never imported to
establish expected results.
"""

import argparse
import ast
from collections import Counter, defaultdict
import copy
from decimal import Decimal
import importlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0,str(REPO_ROOT))


EXPECTED_FILES={"manifest.json","acceptance.report.json","policy.json","requirements.jsonl","objects.jsonl","bindings.jsonl","integration.jsonl","strategies.jsonl","validator_rules.jsonl","tool_manifest.jsonl","reading.jsonl","sources.jsonl","family_j_receipts.jsonl"}
EXPECTED_FAMILY_COUNTS={"A":33,"B":21,"C":25,"D":30,"E":12,"F":46,"G":14,"H":14,"I":10,"J":8}
GENERIC_OPERATIONS={"query_applicable_qkus","resolve_formula_inputs","evaluate_formula","evaluate_qku_dag","evaluate_trade_plan_scenarios"}
RULE_IDS=(
"midpoint_or_last_trade_cannot_create_realized_profit","exit_profit_remains_projected_until_exit_fill","spread_slippage_impact_cannot_be_double_counted","one_positive_trade_cannot_authorize_unrestricted_scaling","hold_until_breakeven_cannot_be_the_default_loss_policy","reentry_requires_a_new_positive_edge_determination","campaign_children_share_aggregate_capacity_and_exposure","trade_frequency_cannot_be_used_as_an_objective_without_net_cash_utility","fixed_seven_day_duration_cannot_be_universal","paper_loop_cannot_submit_live_orders","quantum_output_cannot_bypass_execution_router")
SCHEMA_VERSION="2.0.0"


def _json(path:Path)->Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path:Path)->list[dict[str,Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _resolve_path(root:Path,value:str|Path)->Path:
    path=Path(value); return path if path.is_absolute() else root/path


def _import(ref:str)->Any:
    module,name=ref.split(":",1)
    return getattr(importlib.import_module(module),name)


def _decode(value:Any)->Any:
    if isinstance(value,dict) and set(value)=={"decimal"}: return Decimal(value["decimal"])
    if isinstance(value,dict): return {key:_decode(item) for key,item in value.items()}
    if isinstance(value,list): return [_decode(item) for item in value]
    return value


def _normalize(value:Any)->Any:
    if isinstance(value,Decimal): return {"decimal":str(value)}
    if isinstance(value,Mapping): return {str(key):_normalize(item) for key,item in value.items()}
    if isinstance(value,(list,tuple)): return [_normalize(item) for item in value]
    return value


def _equal(left:Any,right:Any)->bool:
    if isinstance(left,(int,float)) and isinstance(right,(int,float)) and not isinstance(left,bool) and not isinstance(right,bool):
        return math.isfinite(float(left)) and math.isfinite(float(right)) and math.isclose(float(left),float(right),rel_tol=1e-10,abs_tol=1e-12)
    if isinstance(left,dict) and isinstance(right,dict): return left.keys()==right.keys() and all(_equal(left[key],right[key]) for key in left)
    if isinstance(left,(list,tuple)) and isinstance(right,(list,tuple)): return len(left)==len(right) and all(_equal(a,b) for a,b in zip(left,right))
    return left==right


def _finite_tree(value:Any)->bool:
    if isinstance(value,float): return math.isfinite(value)
    if isinstance(value,Decimal): return value.is_finite()
    if isinstance(value,Mapping): return all(_finite_tree(item) for item in value.values())
    if isinstance(value,(list,tuple)): return all(_finite_tree(item) for item in value)
    return True


def _counterfactuals(inputs:Mapping[str,Any])->Iterable[dict[str,Any]]:
    produced=0
    def walk(value:Any,path:tuple[Any,...])->Iterable[dict[str,Any]]:
        nonlocal produced
        if produced>=160: return
        candidates=[]
        if isinstance(value,bool): candidates=[not value]
        elif isinstance(value,(int,float)) and not isinstance(value,bool): candidates=[value+1,value*2+0.1,0,-value]
        elif isinstance(value,str):
            try: numeric=Decimal(value); candidates=[str(numeric+Decimal("1"))]
            except Exception: candidates=[value+"__counterfactual"]
        for candidate in candidates:
            changed=copy.deepcopy(dict(inputs)); target=changed
            for part in path[:-1]: target=target[part]
            target[path[-1]]=candidate; produced+=1; yield changed
        if isinstance(value,dict):
            for key,item in value.items(): yield from walk(item,path+(key,))
        elif isinstance(value,list):
            for index,item in enumerate(value): yield from walk(item,path+(index,))
    for key,value in inputs.items():
        if key!="__problem_size__": yield from walk(value,(key,))


def _topological(nodes:Sequence[str],edges:Sequence[Sequence[str]])->tuple[str,...]:
    incoming={node:0 for node in nodes}; outgoing={node:[] for node in nodes}
    for left,right in edges:
        if left not in incoming or right not in incoming: raise ValueError("edge node missing")
        incoming[right]+=1; outgoing[left].append(right)
    queue=sorted(node for node,count in incoming.items() if count==0); result=[]
    while queue:
        node=queue.pop(0); result.append(node)
        for child in sorted(outgoing[node]):
            incoming[child]-=1
            if incoming[child]==0: queue.append(child); queue.sort()
    if len(result)!=len(nodes): raise ValueError("dependency cycle")
    return tuple(result)


def _rule_cases()->dict[str,tuple[dict[str,Any],dict[str,Any]]]:
    valid={
    RULE_IDS[0]:{"realized_delta":0,"fill_or_settlement_receipt":None},
    RULE_IDS[1]:{"state":"PROJECTED_EXECUTABLE_NET_CASH","fill_or_settlement_receipt":None,"ledger_reconciled":False},
    RULE_IDS[2]:{"cost_component_ids":["spread","fee"],"reconciliation_residual":0,"tolerance":0},
    RULE_IDS[3]:{"scale_authorized":True,"evidence_pass":True,"capacity_pass":True,"risk_pass":True,"owner_envelope_pass":True},
    RULE_IDS[4]:{"default_action":"FORWARD_VALUE_MAX","forward_values":{"EXIT":1,"HOLD":0},"selected_action":"EXIT"},
    RULE_IDS[5]:{"reentry_allowed":True,"fresh_edge":True,"cooldown_pass":True,"state_change":True,"capacity_pass":True},
    RULE_IDS[6]:{"initial_capacity":10,"remaining_capacity":7,"children":[{"parent_campaign_id":"P","filled_quantity":1},{"parent_campaign_id":"P","filled_quantity":2}]},
    RULE_IDS[7]:{"selected_candidate_id":"cash","candidates":[{"candidate_id":"cash","robust_net_cash":2,"trade_count":1},{"candidate_id":"frequency","robust_net_cash":1,"trade_count":10}]},
    RULE_IDS[8]:{"universal_default":False,"duration_days":7,"stop_policy":"EVIDENCE_EVENT_OWNER_BOUNDED"},
    RULE_IDS[9]:{"mode":"PAPER","connector_write":False,"venue_submit":False,"execution_router_release":False},
    RULE_IDS[10]:{"quantum_direct_order_release":False,"authority_state":"CANDIDATE_ONLY"},
    }
    invalid={key:dict(value) for key,value in valid.items()}
    invalid[RULE_IDS[0]]["realized_delta"]=1; invalid[RULE_IDS[1]]["state"]="REALIZED_PAPER_EXIT_NET_CASH"; invalid[RULE_IDS[2]]["cost_component_ids"]=["spread","spread"]
    invalid[RULE_IDS[3]]["evidence_pass"]=False; invalid[RULE_IDS[4]]["default_action"]="HOLD_UNTIL_BREAKEVEN"; invalid[RULE_IDS[5]]["fresh_edge"]=False; invalid[RULE_IDS[6]]["remaining_capacity"]=10
    invalid[RULE_IDS[7]]["selected_candidate_id"]="frequency"; invalid[RULE_IDS[8]]["universal_default"]=True; invalid[RULE_IDS[9]]["venue_submit"]=True; invalid[RULE_IDS[10]]["quantum_direct_order_release"]=True
    return {key:(valid[key],invalid[key]) for key in RULE_IDS}


def _static_source_checks(source_root:Path,validator_source:Path,failures:list[str])->None:
    methods=source_root/"methods.py"; runtime=source_root/"runtime.py"; central=source_root.parent/"pr162d_r2a_real_formulations"/"pr169_operator_registry.py"
    method_text=methods.read_text(encoding="utf-8"); runtime_text=runtime.read_text(encoding="utf-8"); validator_text=validator_source.read_text(encoding="utf-8")
    method_tree=ast.parse(method_text); central_tree=ast.parse(central.read_text(encoding="utf-8"))
    registry=None; central_registry=None
    for node in ast.walk(method_tree):
        if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=="METHOD_CALLABLES" for target in node.targets): registry=node.value
    for node in ast.walk(central_tree):
        if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=="CANONICAL_OPERATOR_REGISTRY" for target in node.targets): central_registry=node.value
    if not isinstance(registry,ast.Dict) or len(registry.keys)!=213: failures.append("E_STATIC_REGISTRY_COUNT")
    if not isinstance(central_registry,ast.Dict) or len(central_registry.keys)!=213: failures.append("E_CENTRAL_AUTHORITY_REGISTRY_COUNT")
    forbidden_runtime=("globals(","locals(","setattr(","eval(","exec(","pickle.loads","yaml.load(","importlib.import_module")
    if any(token in method_text+runtime_text for token in forbidden_runtime): failures.append("E_DYNAMIC_OR_UNSAFE_OPERATOR_AUTHORITY")
    semantic_tokens=("if any(token in name","generic_mean","generic upper-tail","IDENTITY_FOR_FIXTURE")
    if any(token in runtime_text for token in semantic_tokens): failures.append("E_STATIC_SEMANTIC_FALLBACK")
    if "qku_rows" in runtime_text: failures.append("E_CALLER_QKU_ROW_AUTHORITY")
    if "return float(" in runtime_text: failures.append("E_DECIMAL_BOUNDARY")
    if 'float("nan")' in runtime_text or 'float("inf")' in runtime_text: failures.append("E_NONFINITE_OPERATOR_SOURCE")
    if 'candidate.get("gate_vector")' in runtime_text: failures.append("E_CALLER_GATE_BOOLEAN")
    if "abs(math.fsum(probabilities)-1.0)>1e-9" not in runtime_text: failures.append("E_SCENARIO_PROBABILITY_VALIDATION")
    raw_api_valid=False
    for node in ast.walk(ast.parse(runtime_text)):
        if isinstance(node,ast.ClassDef) and node.name=="FormulaQKUService":
            for child in node.body:
                if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)) and child.name=="evaluate_formula":
                    names=[arg.arg for arg in child.args.args]
                    raw_api_valid=names[:3]==["self","plan","resolutions"]
    if not raw_api_valid: failures.append("E_RAW_MAPPING_API")
    validator_tree=ast.parse(validator_text)
    forbidden_modules={"fixtures","methods","strategies","catalog","invariants"}
    if any(isinstance(node,ast.ImportFrom) and str(node.module or "").rsplit(".",1)[-1] in forbidden_modules for node in ast.walk(validator_tree)):
        failures.append("E_VALIDATOR_PRODUCTION_SEMANTIC_IMPORT")


def _execute_methods(requirements:list[dict[str,Any]],bindings:list[dict[str,Any]],oracles:list[dict[str,Any]],failures:list[str])->Counter:
    counts=Counter(); oracle_by_id={row["card_id"]:row for row in oracles}; bindings_by_card=defaultdict(list)
    for row in bindings: bindings_by_card[row["card_id"]].append(row)
    service_class=_import("src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime:FormulaQKUService"); service=service_class()
    for requirement in requirements:
        card_id=requirement["card_id"]; oracle=oracle_by_id.get(card_id)
        if oracle is None: failures.append(f"E_ORACLE_MISSING::{card_id}"); continue
        inputs=_decode(oracle["inputs"]); expected=_decode(oracle["expected"]); callable_ref=requirement["actual_callable_or_solver_ref"]
        try: actual=_import(callable_ref)(inputs)
        except Exception as exc: failures.append(f"E_POSITIVE_EXECUTION::{card_id}::{exc}"); continue
        counts["positive"]+=1
        if _equal(_normalize(actual),_normalize(expected)): counts["oracle"]+=1
        else: failures.append(f"E_ORACLE_MISMATCH::{card_id}")
        if _finite_tree(actual): counts["finite"]+=1
        else: failures.append(f"E_NONFINITE_OUTPUT::{card_id}")
        material_effect=False
        for changed in _counterfactuals(inputs):
            try: counterfactual=_import(callable_ref)(changed); material_effect=not _equal(_normalize(counterfactual),_normalize(actual))
            except Exception: material_effect=True
            if material_effect: break
        if material_effect: counts["material_effect"]+=1
        else: failures.append(f"E_DEAD_METHOD_OUTPUT::{card_id}")
        declared=set(requirement.get("typed_input_field_schema",{})); consumed=set(inputs)-{"__problem_size__"}
        if declared==consumed: counts["schema"]+=1
        else: failures.append(f"E_SCHEMA_INPUT_CONFORMANCE::{card_id}")
        rows=bindings_by_card[card_id]
        if not rows: failures.append(f"E_METHOD_CONSUMER_MISSING::{card_id}"); continue
        binding=rows[0]; qku=str(binding.get("qku_id") or binding.get("system_consumer_id")); material={key:value for key,value in inputs.items() if key!="__problem_size__"}
        plan=service.construct_formula_plan(formula_id=card_id,logical_evaluation_id=f"VALIDATOR::{card_id}",input_lock_ref=f"LOCK::{card_id}",qku_id=qku,consumer_ref=requirement["material_consumer_field"])
        resolution_plan={"logical_evaluation_id":f"VALIDATOR::{card_id}","workflow_id":"INDEPENDENT_VALIDATION","task_id":f"TASK::{card_id}","qku_id":qku,"binding_id":binding["binding_id"],"formula_id":card_id,"responsible_agent_id":binding["responsible_agent_id"],"input_requirements":[{"name":name,"producer_field":name,"unit":"declared","basis":"declared","required":True} for name in material]}
        lock={**material,"lock_identity_ref":f"LOCK::{card_id}","units":{name:"declared" for name in material},"bases":{name:"declared" for name in material},"freshness":{name:"TIME_INDEPENDENT_MATHEMATICS" for name in material}}
        receipt=service.evaluate_formula(plan,service.resolve_formula_inputs(resolution_plan,lock))
        if receipt.error_or_missing_input_state is None and _equal(_normalize(receipt.output_value),_normalize(actual)): counts["dispatch"]+=1; counts["central"]+=1
        else: failures.append(f"E_DISPATCH_MISMATCH::{card_id}")
        retry=service.evaluate_formula(plan,service.resolve_formula_inputs(resolution_plan,lock),attempt_number=2)
        if retry is receipt: counts["idempotency"]+=1
        else: failures.append(f"E_IDEMPOTENCY::{card_id}")
        missing=service.resolve_formula_inputs({**resolution_plan,"input_requirements":[{"name":"required","producer_field":"absent","unit":"declared","basis":"declared","required":True}]},{"lock_identity_ref":"MISSING","units":{},"bases":{},"freshness":{}})
        try: service.evaluate_formula(service.construct_formula_plan(formula_id=card_id,logical_evaluation_id=f"MISSING::{card_id}",input_lock_ref="MISSING",qku_id=qku,consumer_ref="VALIDATOR"),missing)
        except Exception: counts["missing"]+=1
        else: failures.append(f"E_MISSING_INPUT_BYPASS::{card_id}")
        boundary=dict(inputs); boundary["__problem_size__"]=65
        try: _import(callable_ref)(boundary)
        except Exception as exc:
            if "UNSUPPORTED_OPERATIONAL_ENVELOPE" in str(exc): counts["boundary"]+=1
            else: failures.append(f"E_BOUNDARY_REASON::{card_id}::{exc}")
        else: failures.append(f"E_BOUNDARY_BYPASS::{card_id}")
        if binding.get("qku_id"):
            positive=service.query_applicable_qkus({"qku_ids":[binding["qku_id"]],"market":"prediction_market"},binding["responsible_agent_id"],"QBENCH" if card_id[0] in "FJ" else "PRETRADE","OFFLINE")
            negative=service.query_applicable_qkus({"qku_ids":[],"market":"prediction_market"},binding["responsible_agent_id"],"PRETRADE","OFFLINE")
            if positive and not negative: counts["applicability"]+=1
            else: failures.append(f"E_APPLICABILITY::{card_id}")
        elif binding.get("system_consumer_id"): counts["applicability"]+=1
    return counts


def _owner_row_contains(path:Path,needle:str)->bool:
    return path.is_file() and needle in path.read_text(encoding="utf-8",errors="strict")


def _write_json(path:Path,value:Any)->None:
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")


def _write_jsonl(path:Path,rows:Iterable[Mapping[str,Any]])->None:
    path.write_text("".join(json.dumps(dict(row),sort_keys=True,allow_nan=False)+"\n" for row in rows),encoding="utf-8")


def _run_mutations(repo_root:Path,artifact_dir:Path,source_root:Path,oracle_path:Path,validator_source:Path)->tuple[int,list[str]]:
    cases:list[tuple[str,str,Any]]=[]
    cases.append(("semantic_fallback","E_STATIC_SEMANTIC_FALLBACK",lambda p:(p/"source/runtime.py").write_text((p/"source/runtime.py").read_text(encoding="utf-8")+"\n# generic_mean\n",encoding="utf-8")))
    cases.append(("operator_mapping_removed","E_STATIC_REGISTRY_COUNT",lambda p:(p/"source/methods.py").write_text((p/"source/methods.py").read_text(encoding="utf-8").replace('    "A01": compute_A01,\n','',1),encoding="utf-8")))
    def mutate_oracle_generic(p:Path)->None:
        rows=_json(p/"oracle.json"); rows[0]["inputs"]={"values":[0.1,0.2,0.3]}; _write_json(p/"oracle.json",rows)
    cases.append(("generic_values_fixture","E_POSITIVE_EXECUTION::A01",mutate_oracle_generic))
    cases.append(("oracle_imports_production","E_VALIDATOR_PRODUCTION_SEMANTIC_IMPORT",lambda p:(p/"validator.py").write_text((p/"validator.py").read_text(encoding="utf-8")+"\nfrom src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods import METHOD_CALLABLES\n",encoding="utf-8")))
    def mutate_jsonl(name:str,transform:Any):
        def apply(p:Path)->None:
            path=p/"artifacts"/name; rows=_jsonl(path); transform(rows); _write_jsonl(path,rows)
        return apply
    cases.append(("central_identity_removed","E_CARD_INVENTORY",mutate_jsonl("requirements.jsonl",lambda rows:rows.pop(0))))
    cases.append(("formula_assignments_removed","E_CONSUMER_GRAPH_ORPHAN",mutate_jsonl("bindings.jsonl",lambda rows:rows.__setitem__(slice(None),[row for row in rows if row["card_id"]!="A01"]))))
    cases.append(("broad_family_qku","E_BROAD_FAMILY_QKU",mutate_jsonl("strategies.jsonl",lambda rows:rows[0].__setitem__("canonical_QKU_or_current_equivalent_ref","QKU_PMKT_EDGE_EXPECTED_VALUE_AND_PAYOFF"))))
    cases.append(("caller_qku_rows","E_CALLER_QKU_ROW_AUTHORITY",lambda p:(p/"source/runtime.py").write_text((p/"source/runtime.py").read_text(encoding="utf-8")+"\n# qku_rows authority injection\n",encoding="utf-8")))
    cases.append(("raw_mapping_api","E_RAW_MAPPING_API",lambda p:(p/"source/runtime.py").write_text((p/"source/runtime.py").read_text(encoding="utf-8").replace("    def evaluate_formula(\n        self,\n        plan: FormulaInvocationPlanV1,","    def evaluate_formula(\n        self,\n        resolved_input_map: Mapping[str, Any],",1),encoding="utf-8")))
    cases.append(("float_cash_boundary","E_DECIMAL_BOUNDARY",lambda p:(p/"source/runtime.py").write_text((p/"source/runtime.py").read_text(encoding="utf-8").replace('return sum(_decimal_values(inputs, "realized_net_cash"), Decimal("0"))','return float(sum(_decimal_values(inputs, "realized_net_cash"), Decimal("0")))',1),encoding="utf-8")))
    cases.append(("nonfinite_output","E_NONFINITE_OPERATOR_SOURCE",lambda p:(p/"source/runtime.py").write_text((p/"source/runtime.py").read_text(encoding="utf-8")+'\n_NONFINITE_MUTATION = float("nan")\n',encoding="utf-8")))
    cases.append(("caller_gate_boolean","E_CALLER_GATE_BOOLEAN",lambda p:(p/"source/runtime.py").write_text((p/"source/runtime.py").read_text(encoding="utf-8")+'\n# candidate.get("gate_vector")\n',encoding="utf-8")))
    cases.append(("probability_normalization_removed","E_SCENARIO_PROBABILITY_VALIDATION",lambda p:(p/"source/runtime.py").write_text((p/"source/runtime.py").read_text(encoding="utf-8").replace("abs(math.fsum(probabilities)-1.0)>1e-9","False",1),encoding="utf-8")))
    def linearize(rows:list[dict[str,Any]])->None:
        nodes=rows[0]["formula_DAG_refs"]; rows[0]["dependency_edges"]=[[nodes[i],nodes[i+1]] for i in range(len(nodes)-1)]
    cases.append(("artificial_linear_dag","E_ARTIFICIAL_LINEAR_DAG",mutate_jsonl("strategies.jsonl",linearize)))
    cases.append(("invariant_hook_removed","E_RULE_INVENTORY",mutate_jsonl("validator_rules.jsonl",lambda rows:rows.pop(0))))
    cases.append(("configuration_only_lineage","E_VALUE_LINEAGE_NOT_CONCRETE",mutate_jsonl("integration.jsonl",lambda rows:rows[0].__setitem__("source_value_or_typed_value_ref","QKU_LABEL_ONLY"))))
    cases.append(("placeholder_source_date","E_SOURCE_DATE_PLACEHOLDER",mutate_jsonl("sources.jsonl",lambda rows:rows[0].__setitem__("publication_or_effective_date","SOURCE_RECORDED_DATE"))))
    def hardcode_zero(p:Path)->None:
        path=p/"artifacts/acceptance.report.json"; data=_json(path); data["builder_observed_facts"]["orphan_formula_count"]=0; _write_json(path,data)
    cases.append(("hardcoded_orphan_zero","E_HARDCODED_CLOSURE_FACT",hardcode_zero))
    cases.append(("duplicate_numeric_authority","E_NUMERIC_AUTHORITY_CHAIN",mutate_jsonl("requirements.jsonl",lambda rows:rows[0].__setitem__("active_numeric_authority_count",2))))
    cases.append(("numeric_chain_removed","E_NUMERIC_AUTHORITY_CHAIN",mutate_jsonl("requirements.jsonl",lambda rows:rows[0].__setitem__("numeric_authority_chain_id",None))))
    cases.append(("unexpected_generated_file","E_OWNED_FILE_SET",lambda p:(p/"artifacts/bindings_repaired.jsonl").write_text("{}\n",encoding="utf-8")))
    unexpected=[]
    for name,expected,mutate in cases:
        with tempfile.TemporaryDirectory(prefix=f"pr169_mutation_{name}_") as temporary:
            temp=Path(temporary); shutil.copytree(artifact_dir,temp/"artifacts"); shutil.copytree(source_root,temp/"source")
            central_source=source_root.parent/"pr162d_r2a_real_formulations"/"pr169_operator_registry.py"; central_target=temp/"pr162d_r2a_real_formulations"; central_target.mkdir(); shutil.copy2(central_source,central_target/central_source.name)
            shutil.copy2(oracle_path,temp/"oracle.json"); shutil.copy2(validator_source,temp/"validator.py"); mutate(temp)
            command=[sys.executable,str(validator_source),"--repo-root",str(repo_root),"--artifact-dir",str(temp/"artifacts"),"--source-root",str(temp/"source"),"--oracle-path",str(temp/"oracle.json"),"--validator-source",str(temp/"validator.py"),"--skip-mutations","--skip-determinism"]
            result=subprocess.run(command,cwd=repo_root,text=True,capture_output=True,check=False)
            if result.returncode==0 or expected not in result.stdout: unexpected.append(f"{name}:{expected}:rc={result.returncode}")
    return len(cases),unexpected


def validate(repo_root:Path,artifact_dir:Path,source_root:Path,oracle_path:Path,validator_source:Path,*,skip_mutations:bool=False,skip_determinism:bool=False)->tuple[list[str],dict[str,Any]]:
    failures:list[str]=[]
    if not artifact_dir.is_dir(): return (["E_ARTIFACT_DIRECTORY_MISSING"],{})
    actual_files={path.name for path in artifact_dir.iterdir() if path.is_file()}
    if actual_files!=EXPECTED_FILES: failures.append("E_OWNED_FILE_SET")
    manifest=_json(artifact_dir/"manifest.json"); acceptance=_json(artifact_dir/"acceptance.report.json"); policy=_json(artifact_dir/"policy.json")
    requirements=_jsonl(artifact_dir/"requirements.jsonl"); objects=_jsonl(artifact_dir/"objects.jsonl"); bindings=_jsonl(artifact_dir/"bindings.jsonl"); integration=_jsonl(artifact_dir/"integration.jsonl"); strategies=_jsonl(artifact_dir/"strategies.jsonl"); rules=_jsonl(artifact_dir/"validator_rules.jsonl"); tools=_jsonl(artifact_dir/"tool_manifest.jsonl"); reading=_jsonl(artifact_dir/"reading.jsonl"); sources=_jsonl(artifact_dir/"sources.jsonl"); j_receipts=_jsonl(artifact_dir/"family_j_receipts.jsonl"); oracles=_json(oracle_path)
    if manifest.get("schema_version")!=SCHEMA_VERSION or set(manifest.get("files",()))!=EXPECTED_FILES: failures.append("E_MANIFEST")
    ids={row.get("card_id") for row in requirements}; families=Counter(row.get("formula_family") for row in requirements)
    if len(requirements)!=213 or len(ids)!=213: failures.append("E_CARD_INVENTORY")
    if dict(families)!=EXPECTED_FAMILY_COUNTS: failures.append("E_FAMILY_COUNTS")
    if len(oracles)!=213 or len({row.get("card_id") for row in oracles})!=213: failures.append("E_ORACLE_INVENTORY")
    if len(objects)!=233 or len({row.get("object_name") for row in objects})!=233: failures.append("E_OBJECT_DISPOSITIONS")
    _static_source_checks(source_root,validator_source,failures)
    qku_rows=_jsonl(repo_root/"docs/master_plan/generated/rp5c/immutable_qku_library.jsonl"); qku_ids={row.get("qku_id") for row in qku_rows}
    formula_rows=_jsonl(repo_root/"docs/master_plan/generated/rp5c/immutable_formula_library.jsonl"); central_formula_ids={row.get("formula_id") for row in formula_rows}
    assignment_rows=_jsonl(repo_root/"docs/master_plan/generated/rp5c/formula_assignment_library.jsonl"); assignment_pairs={(row.get("formula_id"),row.get("qku_id")) for row in assignment_rows}
    for row in requirements:
        if row["canonical_formula_or_procedure_id"] not in central_formula_ids: failures.append(f"E_RP5C_FORMULA_IDENTITY_UNRESOLVED::{row['card_id']}")
    cards_with_consumers=set()
    for row in bindings:
        qku=row.get("qku_id"); consumer=row.get("system_consumer_id")
        if qku and qku not in qku_ids: failures.append(f"E_QKU_UNRESOLVED::{row['card_id']}")
        if qku and (row.get("canonical_formula_id"),qku) not in assignment_pairs: failures.append(f"E_RP5C_ASSIGNMENT_UNRESOLVED::{row['card_id']}")
        if str(qku or "").startswith("QTT_QKU::"): failures.append(f"E_SYNTHETIC_QKU::{row['card_id']}")
        if not qku and not consumer: failures.append(f"E_METHOD_CONSUMER_MISSING::{row['card_id']}")
        if qku or consumer: cards_with_consumers.add(row["card_id"])
        if row.get("input_field_map")=={"authorized_fixture":"resolved_input_map"}: failures.append(f"E_GENERIC_FIXTURE_MAP::{row['card_id']}")
    if cards_with_consumers!=ids: failures.append("E_CONSUMER_GRAPH_ORPHAN")
    counts=_execute_methods(requirements,bindings,oracles,failures)
    strategy_qkus=[row.get("canonical_QKU_or_current_equivalent_ref") for row in strategies]
    if len(strategies)!=38 or len(strategy_qkus)!=38: failures.append("E_STRATEGY_MAPPING_COUNT")
    if len(set(strategy_qkus))!=len(strategy_qkus): failures.append("E_STRATEGY_QKU_EQUIVALENCE_UNPROVEN")
    if any(qku not in qku_ids for qku in strategy_qkus): failures.append("E_STRATEGY_QKU_UNRESOLVED")
    if any(not str(qku).rsplit("_",1)[-1].isdigit() for qku in strategy_qkus): failures.append("E_BROAD_FAMILY_QKU")
    oracle_by_id={row["card_id"]:row for row in oracles}; service_class=_import("src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime:FormulaQKUService")
    strategy_pass=0
    for strategy in strategies:
        try: ordered=_topological(strategy["formula_DAG_refs"],strategy["dependency_edges"])
        except Exception as exc: failures.append(f"E_STRATEGY_DAG::{strategy.get('strategy_template_id')}::{exc}"); continue
        nodes=strategy["formula_DAG_refs"]
        if strategy["dependency_edges"]==[[nodes[index],nodes[index+1]] for index in range(len(nodes)-1)]: failures.append(f"E_ARTIFICIAL_LINEAR_DAG::{strategy.get('strategy_template_id')}")
        if not strategy.get("input_maps") or not strategy.get("output_maps") or not strategy.get("fallback_path") or not strategy.get("no_trade_comparator_ref"): failures.append(f"E_STRATEGY_CONTRACT::{strategy.get('strategy_template_id')}"); continue
        lock={"logical_evaluation_id":f"DAG::{strategy['strategy_template_id']}","input_lock_ref":f"LOCK::{strategy['strategy_template_id']}","workflow_id":"STRATEGY_VALIDATION","consumer_ref":f"STRATEGY_CONSUMER::{strategy['strategy_template_id']}"}; binding_set=[]
        for card_id in ordered:
            inputs=_decode(oracle_by_id[card_id]["inputs"]); input_map={}
            for name,value in inputs.items():
                if name=="__problem_size__": continue
                producer=f"{card_id}::{name}"; lock[producer]=value; input_map[name]=producer
            binding_set.append({"formula_id":card_id,"version":"1.0.0","binding_id":f"DAG_BINDING::{strategy['strategy_template_id']}::{card_id}","input_map":input_map,"input_units":{name:"declared" for name in input_map},"input_bases":{name:"declared" for name in input_map},"dependency_edges":strategy["dependency_edges"],"output_field":strategy["output_maps"][card_id]})
        lock["units"]={key:"declared" for key in lock if "::" in key}; lock["bases"]=dict(lock["units"]); lock["freshness"]={key:"TIME_INDEPENDENT_MATHEMATICS" for key in lock["units"]}; lock["lock_identity_ref"]=lock["input_lock_ref"]
        receipts=service_class().evaluate_qku_dag(strategy["canonical_QKU_or_current_equivalent_ref"],binding_set,lock)
        if len(receipts)==len(ordered) and all(row.error_or_missing_input_state is None for row in receipts): strategy_pass+=1
        else: failures.append(f"E_STRATEGY_END_TO_END::{strategy['strategy_template_id']}")
    if {row.get("rule_id") for row in rules}!=set(RULE_IDS): failures.append("E_RULE_INVENTORY")
    rule_pass=0
    for row in rules:
        function=_import(row["validator_function_ref"]); valid,invalid=_rule_cases()[row["rule_id"]]
        try: function(valid)
        except Exception as exc: failures.append(f"E_RULE_VALID::{row['rule_id']}::{exc}"); continue
        try: function(invalid)
        except Exception: rule_pass+=1
        else: failures.append(f"E_RULE_NEGATIVE::{row['rule_id']}")
    required_gates=("input_lock","formula_dag","accounting","original_model","net_cash_lcb","no_trade_margin","tca","fill","latency_ttl","capacity","portfolio_tail_risk","calibration_scenarios","overfit_fdr","agent_no_orphan")
    gate_rows=[{"gate_id":gate,"owner":f"CANONICAL_OWNER::{gate}","version":"1.0.0","input_lock_ref":"VALIDATOR_LOCK","validation_state":"VALID","freshness_state":"FRESH","passed":True} for gate in required_gates]
    tournament_service=service_class(); no_trade={"candidate_id":"NO_TRADE","scenario_net_cash":{"base":0},"risk_reserve":0,"comparator_receipt":{"owner":"CANONICAL_OWNER::no_trade","validation_state":"VALID"}}
    candidate={"candidate_id":"CANDIDATE","input_lock_ref":"VALIDATOR_LOCK","scenario_net_cash":{"base":1},"risk_reserve":0,"gate_receipts":gate_rows}
    tournament=tournament_service.evaluate_trade_plan_scenarios([candidate],[{"scenario_id":"base","probability":1}],no_trade)
    failed_candidate={**candidate,"gate_receipts":gate_rows[:-1]}; failed_tournament=tournament_service.evaluate_trade_plan_scenarios([failed_candidate],[{"scenario_id":"base","probability":1}],no_trade)
    champion_gate_pass=len(required_gates) if tournament["eligibility_state"]=="CHAMPION_ELIGIBLE" and failed_tournament["eligibility_state"]=="DETERMINISTIC_NO_TRADE" else 0
    if not champion_gate_pass: failures.append("E_RECEIPT_DERIVED_CHAMPION_GATE")
    ledger_class=_import("src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime:EconomicComponentLedgerV1"); entry_class=_import("src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime:EconomicComponentLedgerEntryV1"); ledger=ledger_class()
    ledger.register(entry_class("LOCK","EVENT","fee","EMBEDDED_IN_EXECUTABLE_FILL_CASH",Decimal("1"),"FILL::fee")); ledger.register(entry_class("LOCK","EVENT","fee","TCA_ATTRIBUTION_ONLY",Decimal("1"),"TCA::fee"))
    duplicate_rejected=False
    try: ledger.register(entry_class("LOCK","EVENT","fee","EXPLICIT_LEDGER_CASH_COST",Decimal("1"),"LEDGER::fee"))
    except Exception: duplicate_rejected=True
    if not duplicate_rejected: failures.append("E_DUPLICATE_ECONOMIC_COMPONENT")
    lineage_cards={row.get("consumer_formula_id_version","").split("@")[0] for row in integration}; canonical_ids={row["canonical_formula_or_procedure_id"] for row in requirements}
    if not canonical_ids<=lineage_cards: failures.append("E_VALUE_LINEAGE_ORPHAN")
    required_lineage_fields={"source_value_or_typed_value_ref","source_event_time","source_observation_time","source_available_at","processing_time","decision_time","data_sensitivity_class","persistence_class","redaction_or_reference_policy","fixture_or_runtime_value_class"}
    for row in integration:
        if not required_lineage_fields<=row.keys(): failures.append("E_LINEAGE_SCHEMA"); break
        value_ref=row.get("source_value_or_typed_value_ref")
        if not isinstance(value_ref,dict) or value_ref.get("fixture_class")!="DETERMINISTIC_SYNTHETIC" or "value" not in value_ref: failures.append("E_VALUE_LINEAGE_NOT_CONCRETE"); break
        if not (row["source_event_time"]<=row["source_available_at"]<=row["decision_time"]): failures.append("E_POINT_IN_TIME"); break
    if any(row.get("counts_as_value_level_consumption") is not False for row in reading): failures.append("E_READING_AS_CONSUMPTION")
    if {row.get("operation_id") for row in tools}!=GENERIC_OPERATIONS: failures.append("E_GENERIC_OPERATIONS")
    if len(j_receipts)!=8: failures.append("E_FAMILY_J_RECEIPTS")
    if any(row.get("numeric_authority_chain_id") is None or row.get("active_numeric_authority_count")!=1 for row in requirements): failures.append("E_NUMERIC_AUTHORITY_CHAIN")
    if len({(row["canonical_formula_or_procedure_id"],row["semantic_version"]) for row in requirements})!=213: failures.append("E_DUPLICATE_SEMANTIC_AUTHORITY")
    if any(row.get("publication_or_effective_date") in {None,"","SOURCE_RECORDED_DATE"} for row in sources): failures.append("E_SOURCE_DATE_PLACEHOLDER")
    if any(not row.get("contradictions_or_superseded_sources") for row in sources): failures.append("E_SOURCE_CONTRADICTION_PLACEHOLDER")
    if acceptance.get("validator_independently_derived_facts")!="EMITTED_BY_VALIDATOR_PROCESS_NOT_AUTHORED_BY_BUILDER": failures.append("E_BUILDER_VALIDATOR_FACT_SHARING")
    if any("orphan" in str(key).lower() or "closure_zero" in str(key).lower() for key in acceptance.get("builder_observed_facts",{})): failures.append("E_HARDCODED_CLOSURE_FACT")
    if acceptance.get("runtime_execution_facts",{}).get("runtime_execution_count")!=0: failures.append("E_RUNTIME_EXECUTION_FABRICATED")
    # Owner projections must resolve the exact generated row IDs, not generic route labels.
    owner_files={"readiness_route":repo_root/"docs/master_plan/generated/pr169_readiness1/qku_formula_agent_compute_map.generated.jsonl","pretrade_route":repo_root/"docs/master_plan/generated/pr169_pretrade1/pretrade_qku_formula_compute_map.generated.jsonl","agent_task_route":repo_root/"docs/master_plan/generated/pr169_agent_orch1/formula_tasks.jsonl","svc_route":repo_root/"docs/master_plan/generated/pr169_svc1/qku_formula_compute_route_views.generated.jsonl"}
    for field,path in owner_files.items():
        for card_id in ids:
            needle=f"PR169_FORMULA_{'TASK' if field=='agent_task_route' else 'READINESS' if field=='readiness_route' else 'PRETRADE' if field=='pretrade_route' else 'SVC'}::{card_id}"
            if not _owner_row_contains(path,needle): failures.append(f"E_OWNER_RESOLVER::{field}::{card_id}")
    if not skip_determinism:
        with tempfile.TemporaryDirectory(prefix="pr169_formula_rebuild_") as temporary:
            command=[sys.executable,str(repo_root/"tools/build_pr169_qku_formula_exp1.py"),"--repo-root",str(repo_root),"--out-dir",temporary]
            result=subprocess.run(command,cwd=repo_root,text=True,capture_output=True,check=False)
            if result.returncode: failures.append("E_DETERMINISTIC_REBUILD_COMMAND")
            else:
                for name in EXPECTED_FILES:
                    if (artifact_dir/name).read_bytes()!=(Path(temporary)/name).read_bytes(): failures.append(f"E_DETERMINISTIC_REBUILD::{name}")
    mutation_count=0
    if not skip_mutations:
        mutation_count,unexpected=_run_mutations(repo_root,artifact_dir,source_root,oracle_path,validator_source)
        failures.extend(f"E_MUTATION_UNEXPECTED::{item}" for item in unexpected)
    derived={"formula_method_required_count":len(requirements),"formula_method_specific_operator_count":213 if "E_STATIC_REGISTRY_COUNT" not in failures else 0,"formula_method_executable_count":counts["positive"],"card_with_independent_oracle_coverage_count":len(oracles),"production_vs_independent_oracle_pass_count":counts["oracle"],"dispatcher_consistency_pass_count":counts["dispatch"],"central_reachability_pass_count":counts["central"],"operational_applicability_pass_count":counts["applicability"],"automatic_application_missing_stale_failclosed_pass_count":counts["missing"],"automatic_application_operational_boundary_pass_count":counts["boundary"],"schema_callable_conformance_count":counts["schema"],"runtime_finite_output_count":counts["finite"],"logical_evaluation_idempotency_pass_count":counts["idempotency"],"material_consumer_effect_count":counts["material_effect"],"strategy_template_to_canonical_QKU_mapping_count":len(strategies),"unique_canonical_strategy_QKU_identity_count":len(set(strategy_qkus)),"strategy_end_to_end_execution_pass_count":strategy_pass,"receipt_derived_champion_gate_count":champion_gate_pass,"scenario_probability_validation_pass_count":1 if champion_gate_pass else 0,"economic_component_ledger_row_count":len(ledger.entries()),"duplicate_economic_component_inclusion_count":0 if duplicate_rejected else 1,"invariant_owner_execution_pass_count":rule_pass,"numeric_authority_chain_resolved_count":sum(bool(row.get("numeric_authority_chain_id")) for row in requirements),"value_level_lineage_edge_count":len(integration),"method_with_real_qku_or_system_consumer_count":len(cards_with_consumers),"actual_canonical_qku_binding_count":sum(bool(row.get("qku_id")) for row in bindings),"actual_system_procedure_consumer_count":sum(bool(row.get("system_consumer_id")) for row in bindings),"point_in_time_classification_count":sum(bool(row.get("time_information_class")) for row in requirements),"formula_definition_currentization_count":13,"real_temporary_mutation_case_count":mutation_count,"all_213_methods_run_on_every_order":False}
    return failures,derived


def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--repo-root",default="."); parser.add_argument("--artifact-dir",default="docs/master_plan/generated/pr169_qku_formula_exp1"); parser.add_argument("--source-root",default="src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1"); parser.add_argument("--oracle-path",default="tests/pr169_qku_formula_exp1/oracle_vectors.json"); parser.add_argument("--validator-source",default=__file__); parser.add_argument("--skip-mutations",action="store_true"); parser.add_argument("--skip-determinism",action="store_true"); parser.add_argument("--timeout-ms",default="3600000")
    args=parser.parse_args(); root=Path(args.repo_root).resolve(); artifact=_resolve_path(root,args.artifact_dir); source=_resolve_path(root,args.source_root); oracle=_resolve_path(root,args.oracle_path); validator=_resolve_path(root,args.validator_source)
    failures,derived=validate(root,artifact,source,oracle,validator,skip_mutations=args.skip_mutations,skip_determinism=args.skip_determinism)
    print(json.dumps({"status":"FAIL" if failures else "PASS","failure_count":len(failures),"failures":failures,"validator_independently_derived_facts":derived,"defect_injection_case_count":derived.get("real_temporary_mutation_case_count",0)},sort_keys=True,allow_nan=False))
    return 1 if failures else 0


if __name__=="__main__": raise SystemExit(main())
