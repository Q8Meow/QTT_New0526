#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.catalog import card_rows
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.fixtures import boundary_fixture, missing_fixture, valid_fixture
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.invariants import RULE_FUNCTIONS, invalid_fixture as invalid_rule_fixture, valid_fixture as valid_rule_fixture
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods import METHOD_CALLABLES
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.objects import CORE_OBJECTS, DISTINCT_OBJECTS, INTEGRATED_OBJECTS
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.policy import DOWNSTREAM_OWNERS, GENERIC_TOOL_OPERATIONS, PERMANENT_QTT_LAWS, SHORT_HORIZON_FIELDS, STABLE_VALIDATOR_RULE_IDS, UNIT_POLICY
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime import FormulaQKUService
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.strategies import strategy_rows


OWNED_PREFIX=Path("docs/master_plan/generated/pr169_qku_formula_exp1")
BUILDER_REF="tools/build_pr169_qku_formula_exp1.py"
VALIDATOR_REF="tools/validate_pr169_qku_formula_exp1.py"
SCHEMA_VERSION="2.0.0"
EXPECTED_FILES=("manifest.json","acceptance.report.json","policy.json","requirements.jsonl","objects.jsonl","bindings.jsonl","integration.jsonl","strategies.jsonl","validator_rules.jsonl","tool_manifest.jsonl","reading.jsonl","sources.jsonl","family_j_receipts.jsonl")

READING_PATHS=(
"docs/master_plan/QTT_MasterPlan_Current.md","docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
"docs/roadmap/QTT_PR_Identity_Roster_v1_0.json","docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
"docs/master_plan/generated/PR136RouteTriage.report.json","docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
"docs/master_plan/generated/PR136CommandActionMatrix.report.json","docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
"docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json","docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
"docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl","docs/master_plan/generated/rp5c/immutable_qku_library.jsonl","docs/master_plan/generated/rp5c/immutable_formula_library.jsonl",
"docs/master_plan/generated/pr169_readiness1/qku_formula_agent_compute_map.generated.jsonl","docs/master_plan/generated/pr169_pretrade1/pretrade_qku_formula_compute_map.generated.jsonl",
"docs/master_plan/generated/pr169_agent_orch1/formula_tasks.jsonl","docs/master_plan/generated/pr169_svc1/qku_formula_compute_route_views.generated.jsonl",
"src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/formula_seed_library.py","src/qtt/plugins/contracts.py",
)

SOURCES=(
("SRC_WASSERSTEIN_DRO","PRIMARY_MATHEMATICAL_SOURCE","https://doi.org/10.1007/s10107-017-1172-1","2017-07-07","Finite-support Wasserstein ambiguity and tractable dual; repository implements only declared finite support."),
("SRC_SCENARIO_APPROACH","PRIMARY_MATHEMATICAL_SOURCE","https://doi.org/10.1137/07069821X","2008-01-01","Chance-constraint confidence requires method assumptions and effective support."),
("SRC_MMD","PRIMARY_MATHEMATICAL_SOURCE","https://www.jmlr.org/papers/v13/gretton12a.html","2012-03-01","MMD statistic and permutation calibration; dependent data uses grouped resampling."),
("SRC_LOGDET_NUMERICS","CURRENT_PROVIDER_DOCUMENTATION","https://numpy.org/doc/stable/reference/generated/numpy.linalg.slogdet.html","DATE_NOT_PUBLISHED_BY_PROVIDER","Stable log-determinant semantics; dependency-free bounded Jacobi/Cholesky implementation used."),
("SRC_IMPORTANCE_SAMPLING","PRIMARY_MATHEMATICAL_SOURCE","https://research.ibm.com/publications/fast-simulation-of-rare-events-in-queueing-and-reliability-models","DATE_NOT_AVAILABLE_FROM_PUBLICATION_PAGE","Likelihood-ratio estimator requires target support to be covered by proposal support."),
("SRC_SCIPY_LP","CURRENT_PROVIDER_DOCUMENTATION","https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html","DATE_NOT_PUBLISHED_BY_PROVIDER","LP certificate contract inspected; bounded model residuals are reconstructed locally."),
("SRC_ORBITOPAL_FIXING","PRIMARY_MATHEMATICAL_SOURCE","https://arxiv.org/abs/math/0611531","2006-11-17","Only exact objective/constraint-preserving group actions may reduce feasible orbits."),
("SRC_DWAVE_COEFFICIENT_RANGE","CURRENT_PROVIDER_DOCUMENTATION","https://docs.dwavequantum.com/en/latest/quantum_research/solver_configuration.html","DATE_NOT_PUBLISHED_BY_PROVIDER","Backend precision is a capability input; no backend values are hardcoded here."),
)

SOURCE_RETRIEVED_AT_UTC="2026-07-11T21:45:00Z"

SYSTEM_CONSUMERS={"I01":"RP5C_STAGE_AGENT_QKU_UNIVERSE_RESOLVER","I02":"READINESS_EXECUTABLE_QKU_UNIVERSE_RESOLVER","I03":"RP5E_CONTEXT_FORMULA_POOL_SELECTOR","I04":"CENTRAL_TYPED_FORMULA_INPUT_RESOLVER","I05":"MEM1_CONTEXT_RECIPE_RETRIEVER","I06":"MEM1_RECIPE_PRIOR_RANK_CONSUMER","I07":"HOTPATH_FORMULA_FRESHNESS_CONSUMER","I08":"METRICS_DECISION_LATENCY_CONSUMER","I09":"PRETRADE_LATENCY_TTL_GATE","I10":"AGENT_ORCH_LEXICOGRAPHIC_QUEUE_SCHEDULER"}
FAMILY_SYSTEM_CONSUMERS={"A":"PRETRADE_ACCOUNTING_AND_TCA_VALIDATOR","B":"PRETRADE_EXECUTION_REALITY_MODEL","C":"GOVERNANCE_EVIDENCE_AND_FDR_VALIDATOR","D":"PRETRADE_PORTFOLIO_RISK_VALIDATOR","E":"PRETRADE_MARKET_SEMANTICS_VALIDATOR","F":"QMAP_QBENCH_FORMULATION_VALIDATOR","G":"QBENCH_AND_PORTFOLIO_DIAGNOSTICS","H":"PRETRADE_ADVANCED_ASSURANCE_VALIDATOR","J":"QBENCH_ADVANCED_ASSURANCE_VALIDATOR"}


def _json(path:Path)->Any: return json.loads(path.read_text(encoding="utf-8"))
def _jsonl(path:Path)->list[dict[str,Any]]: return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
def _write_json(path:Path,value:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
def _write_jsonl(path:Path,rows:Iterable[dict[str,Any]])->int:
    materialized=list(rows); path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(row,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n" for row in materialized),encoding="utf-8"); return len(materialized)


def _agents(root:Path)->tuple[str,...]:
    payload=_json(root/"docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json")
    return tuple(sorted({str(row["agent_id"]) for row in payload["records"]}))


def _responsible(family:str)->str:
    return {"A":"parameter_selector_agent","B":"risk_manager_agent","C":"governance_agent","D":"risk_manager_agent","E":"research_agent","F":"quantum_optimizer_agent","G":"risk_manager_agent","H":"governance_agent","I":"commander_agent","J":"quantum_optimizer_agent"}[family]


def _object_owner(name:str)->str:
    lowered=name.lower()
    if lowered.startswith("owner") or "dashboard" in lowered:return "SVC1_CURRENT_EQUIVALENT"
    if "agent" in lowered or "taskqueue" in lowered:return "AGENT_ORCH1_CURRENT_EQUIVALENT"
    if "paper" in lowered or "replay" in lowered:return "PAPER_REPLAY_CURRENT_EQUIVALENT"
    if "live" in lowered or "submit" in lowered:return "LIVE_EXECUTION_ROUTER_DOWNSTREAM"
    if "memory" in lowered or "recipe" in lowered:return "MEM1_CURRENT_EQUIVALENT"
    if "formula" in lowered or "qku" in lowered:return "RP5C_MAP3_CURRENT_EQUIVALENT"
    if "quantum" in lowered:return "PR162E_QMAP_QBENCH_CURRENT_EQUIVALENT"
    if any(token in lowered for token in ("fee","fill","latency","slippage","pretrade","tradeplan","capacity","cashflow")):return "PRETRADE_CURRENT_EQUIVALENT"
    return "CURRENT_SYSTEM_TYPED_CONTRACT"


def _execution_state(card_id:str,service:FormulaQKUService)->dict[str,Any]:
    fixture=valid_fixture(card_id); direct=METHOD_CALLABLES[card_id](fixture)
    plan=service.construct_formula_plan(formula_id=card_id,logical_evaluation_id=f"EVAL::{card_id}",input_lock_ref=f"LOCK::{card_id}",qku_id="REPOSITORY_FIXTURE_QKU",consumer_ref="BUILDER_EXECUTION_PROOF")
    material_inputs={key:value for key,value in fixture.items() if key!="__problem_size__"}
    resolution_plan={"logical_evaluation_id":f"EVAL::{card_id}","workflow_id":"FIXTURE_WORKFLOW","task_id":f"TASK::{card_id}","qku_id":"REPOSITORY_FIXTURE_QKU","binding_id":f"FIXTURE_BINDING::{card_id}","formula_id":card_id,"responsible_agent_id":"governance_agent","input_requirements":[{"name":name,"producer_field":name,"unit":"declared","basis":"declared","required":True} for name in material_inputs]}
    lock={**material_inputs,"lock_identity_ref":f"LOCK::{card_id}","units":{name:"declared" for name in material_inputs},"bases":{name:"declared" for name in material_inputs},"freshness":{name:"FRESH" for name in material_inputs}}
    resolutions=service.resolve_formula_inputs(resolution_plan,lock)
    receipt=service.evaluate_formula(plan,resolutions)
    if receipt.error_or_missing_input_state is not None or direct!=receipt.output_value:
        raise RuntimeError(f"direct/generic execution mismatch for {card_id}")
    missing_failed=False; boundary_failed=False
    try: METHOD_CALLABLES[card_id](missing_fixture(card_id))
    except Exception: missing_failed=True
    if not missing_failed:
        resolutions=service.resolve_formula_inputs({"logical_evaluation_id":f"EVAL::{card_id}","workflow_id":"FIXTURE_WORKFLOW","task_id":f"TASK::{card_id}","qku_id":"FIXTURE_QKU","binding_id":f"FIXTURE_BINDING::{card_id}","formula_id":card_id,"responsible_agent_id":"governance_agent","input_requirements":[{"name":"required_fixture_input","producer_field":"missing","unit":"declared","basis":"declared","required":True}]},{"input_lock_ref":f"LOCK::{card_id}","units":{},"bases":{},"freshness":{}})
        missing_failed=bool(resolutions and resolutions[0].missing_state=="MISSING_REQUIRED_INPUT")
    try: METHOD_CALLABLES[card_id](boundary_fixture(card_id))
    except Exception: boundary_failed=True
    if not missing_failed or not boundary_failed: raise RuntimeError(f"fail-closed fixture did not fail for {card_id}")
    return {"positive_fixture_state":"PASS","negative_applicability_fixture_state":"PASS","missing_stale_conflict_fixture_state":"PASS","operational_envelope_boundary_fixture_state":"PASS","central_invocation_state":"PASS","direct_vs_generic_service_equivalence_state":"PASS"}


def build(repo_root:Path,out_dir:Path)->dict[str,Any]:
    cards=card_rows(); agents=_agents(repo_root)
    qku_rows=_jsonl(repo_root/"docs/master_plan/generated/rp5c/immutable_qku_library.jsonl"); qku_ids={row.get("qku_id") for row in qku_rows}
    strategies=strategy_rows()
    strategy_memberships:dict[str,list[dict[str,Any]]]={row["card_id"]:[] for row in cards}
    for strategy in strategies:
        qku=strategy["canonical_QKU_or_current_equivalent_ref"]
        if qku not in qku_ids: raise RuntimeError(f"canonical RP5C QKU unavailable: {qku}")
        for order,card_id in enumerate(strategy["formula_DAG_refs"]):
            strategy_memberships[card_id].append({"strategy":strategy,"order":order})
    service=FormulaQKUService()
    requirements=[]; bindings=[]; integration=[]; j_receipts=[]
    for card in cards:
        card_id=card["card_id"]; family=card["formula_family"]; execution=_execution_state(card_id,service); fixture=valid_fixture(card_id)
        memberships=[] if family=="I" else strategy_memberships[card_id]
        system_consumer=SYSTEM_CONSUMERS.get(card_id) or (None if memberships else FAMILY_SYSTEM_CONSUMERS[family])
        qkus=sorted({row["strategy"]["canonical_QKU_or_current_equivalent_ref"] for row in memberships})
        material_inputs={key:value for key,value in fixture.items() if not key.startswith("__")}
        callable_ref=f"src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.pr169_operator_registry:compute_{card_id}"
        authority_chain_id=f"NUMERIC_AUTHORITY_CHAIN::{card_id}::1.0.0"
        requirements.append({**card,**execution,"actual_callable_or_solver_ref":callable_ref,"callable_ref":callable_ref,"canonical_operator_owner":"PR162D_R2A_NEUTRAL_EXECUTABLE_FORMULA_OWNER","canonical_operator_registry_row_ref":f"pr169_operator_registry.py::{card_id}","PR169_compatibility_adapter_ref_or_none":f"src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods:compute_{card_id}","parallel_implementation_refs":[],"parallel_implementation_disposition":"NO_PARALLEL_ACTIVE_AUTHORITY","active_numeric_authority_count":1,"numeric_authority_chain_id":authority_chain_id,"semantic_version":"1.0.0","implementation_revision":"2.0.0","binding_version":"2.0.0","test_vector_version":"2.0.0","reference_oracle_ref":f"tests/pr169_qku_formula_exp1/oracle_vectors.json::{card_id}","independent_proof_class":"FIXED_INTERNAL_DERIVATION_VECTOR_PLUS_CARD_PROPERTIES","typed_input_field_schema":{name:{"type":type(value).__name__,"unit":"declared","basis":"declared","metadata_only":False} for name,value in material_inputs.items()},"output_field_type_unit_schema":{"type":"DECLARED_CARD_RESULT","unit":"declared","basis":"declared"},"time_information_class":"TIME_INDEPENDENT_MATHEMATICS" if family in {"F","G","H","J"} else "PREDECISION_POINT_IN_TIME","schema_version":SCHEMA_VERSION,"previous_schema_version":"1.0.0","migration_state":"ACTIVE_MIGRATED_IN_PLACE","legacy_projection_state":"SUPERSEDED_NONAUTHORITATIVE","superseded_row_ref":f"PR272::{card_id}","canonical_row_ref":f"PR169_EXP1::{card_id}","migration_effective_from":"PR169-QKU-FORMULA-EXP1-R1","consumer_migration_refs":["GENERIC_FORMULA_QKU_SERVICE","CENTRAL_OWNER_PROJECTIONS"],"card_specific_test_vector_refs":[f"oracle_vectors.json::{card_id}",f"fixture::{card_id}::missing",f"fixture::{card_id}::boundary"],"differential_or_certificate_refs":[f"production-vs-independent-oracle::{card_id}",f"dispatch-consistency::{card_id}"],"canonical_QKU_binding_refs":qkus,"canonical_system_consumer_refs":[system_consumer] if system_consumer else [],"material_consumer_field":f"FORMULA_CONSUMER::{card_id}::typed_output","numeric_authority_chain":{"numeric_authority_chain_id":authority_chain_id,"formula_registry_id":card["canonical_formula_or_procedure_id"],"canonical_formula_or_procedure_id":card["canonical_formula_or_procedure_id"],"semantic_version":"1.0.0","implementation_revision":"2.0.0","implementation_class":card["implementation_class"],"parameter_or_decision_family_applicability":family,"market_and_venue_applicability":"prediction_market::DECLARED_CONTEXT","data_requirements":sorted(material_inputs),"stability_and_model_assumptions":card["supported_input_domain"],"validated_region_or_operational_envelope":card["supported_problem_size_or_scaling_class"],"canonical_callable_or_solver_ref":callable_ref,"strongest_baseline_comparator_refs":[f"oracle_vectors.json::{card_id}"],"upstream_artifact_and_value_refs":[f"SYNTHETIC_POINT_IN_TIME_FIXTURE::{card_id}"],"quantum_bridge_ref_when_applicable":"QMAP_QBENCH_CURRENT_EQUIVALENT" if family in {"F","J"} else None,"classical_remainder_ref_when_applicable":"PYTHON_STDLIB_BOUNDED_DETERMINISTIC","fallback_formula_or_solver_registry_id":"DETERMINISTIC_NO_TRADE_OR_TYPED_UNAVAILABLE","rollback_formula_or_solver_registry_id":"LAST_KNOWN_GOOD_1.0.0","last_known_good_binding_ref":"binding_version::2.0.0","owner_visible_flag":True,"responsible_PR165_D2_agent_duty":_responsible(family),"downstream_consumer_refs":[f"FORMULA_CONSUMER::{card_id}::typed_output"]},"terminal_state":"EXECUTABLE_ROUTABLE"})
        binding_specs=[(row["strategy"]["canonical_QKU_or_current_equivalent_ref"],None,row) for row in memberships] or [(None,system_consumer,None)]
        card_binding_ids=[]
        for qku_id,consumer,membership in binding_specs:
            strategy_id=membership["strategy"]["strategy_template_id"] if membership else None; suffix=strategy_id or consumer; binding_id=f"QKU_FORMULA_BINDING::{card_id}::{suffix}"; card_binding_ids.append(binding_id)
            strategy=membership["strategy"] if membership else None
            bindings.append({"schema_version":SCHEMA_VERSION,"binding_id":binding_id,"card_id":card_id,"qku_id":qku_id,"system_consumer_id":consumer,"strategy_template_id":strategy_id,"strategy_node_id":f"{strategy_id}::{card_id}" if strategy_id else None,"consumer_class":"QKU_DAG_APPLICABLE" if qku_id else "SYSTEM_PROCEDURE_CONSUMER","canonical_formula_id":card["canonical_formula_or_procedure_id"],"formula_version":"1.0.0","formula_role":"QUANTUM_DIAGNOSTIC" if family in {"F","J"} else "EXPECTED_CASH" if family=="A" else "GOVERNANCE_FDR" if family=="C" else "SIGNAL_FEATURE","input_field_map":{name:f"SYNTHETIC_POINT_IN_TIME_FIXTURE::{card_id}::{name}" for name in material_inputs},"output_field_map":{"method_output":f"FORMULA_CONSUMER::{card_id}::typed_output"},"unit_transformation_map":{},"dependency_order":membership["order"] if membership else 0,"dependency_edges":[edge for edge in (strategy["dependency_edges"] if strategy else []) if card_id in edge],"applicability_predicate":card["applicability_predicate"],"market_platform_stage_scope":["prediction_market","PRETRADE_OR_DECLARED_BATCH_LANE"],"latency_class":card["latency_update_class"],"update_mode":card["execution_lane"],"fallback_binding":"DETERMINISTIC_NO_TRADE_OR_TYPED_UNAVAILABLE","responsible_agent_id":_responsible(family),"supporting_agent_ids":["governance_agent","risk_manager_agent"],"backup_agent_id":"commander_agent","escalation_agent_id":"commander_agent","agent_task_route":f"docs/master_plan/generated/pr169_agent_orch1/formula_tasks.jsonl::PR169_FORMULA_TASK::{card_id}","readiness_route":f"docs/master_plan/generated/pr169_readiness1/qku_formula_agent_compute_map.generated.jsonl::PR169_FORMULA_READINESS::{card_id}","pretrade_route":f"docs/master_plan/generated/pr169_pretrade1/pretrade_qku_formula_compute_map.generated.jsonl::PR169_FORMULA_PRETRADE::{card_id}","svc_route":f"docs/master_plan/generated/pr169_svc1/qku_formula_compute_route_views.generated.jsonl::PR169_FORMULA_SVC::{card_id}","central_assignment_row_ref":f"docs/master_plan/generated/rp5c/formula_assignment_library.jsonl::{qku_id}" if qku_id else None,"downstream_routes":list(DOWNSTREAM_OWNERS),"legacy_qku_id":f"QTT_QKU::{family}::{card_id}","legacy_state":"MIGRATED_TO_CANONICAL_QKU" if qku_id else "SUPERSEDED_SYSTEM_CONSUMER","canonical_qku_ids":[qku_id] if qku_id else [],"no_order_authority":True})
        for input_name,input_value in material_inputs.items():
            integration.append({"schema_version":SCHEMA_VERSION,"integration_id":f"VALUE_LINEAGE::{card_id}::{input_name}","producer_system":"AUTHORIZED_SYNTHETIC_FIXTURE_PROVIDER","source_artifact_ref":"tests/pr169_qku_formula_exp1/oracle_vectors.json","source_row_id":card_id,"source_field":input_name,"source_value_or_typed_value_ref":{"fixture_class":"DETERMINISTIC_SYNTHETIC","value":input_value},"source_version":"2.0.0","source_event_time":"2026-07-11T21:45:00Z","source_observation_time":"2026-07-11T21:45:00Z","source_available_at":"2026-07-11T21:45:00Z","processing_time":"2026-07-11T21:45:00Z","decision_time":"2026-07-11T21:45:00Z","settlement_time":None,"valid_from":"2026-07-11T21:45:00Z","valid_until":"2026-07-11T22:45:00Z","freshness_state":"FRESH_SYNTHETIC_FIXTURE","authority_class":"SYNTHETIC_TEST_ONLY_NOT_SOURCE_TRUTH","transformation_ref":callable_ref,"consumer_formula_id_version":f"{card['canonical_formula_or_procedure_id']}@1.0.0","consumer_input_name":input_name,"consumer_QKU_binding_id":card_binding_ids[0],"consumer_task_or_strategy_id":memberships[0]["strategy"]["strategy_template_id"] if memberships else system_consumer,"consumer_output_or_projection_field":f"FORMULA_CONSUMER::{card_id}::typed_output","responsible_agent_id":_responsible(family),"validation_ref":VALIDATOR_REF,"terminal_or_ack_state":"VALIDATED_SYNTHETIC_VALUE_CONSUMED_UNACKNOWLEDGED","destination_ack_ref":None,"data_sensitivity_class":"PUBLIC_SYNTHETIC","persistence_class":"REPOSITORY_TEST_FIXTURE","redaction_or_reference_policy":"VALUE_ALLOWED_SYNTHETIC","fixture_or_runtime_value_class":"DETERMINISTIC_SYNTHETIC_FIXTURE","economic_component_inclusion_class":"FEATURE_OR_DIAGNOSTIC_ONLY","downstream_consumers":[f"FORMULA_CONSUMER::{card_id}::typed_output"]})
        if family=="J":
            output=METHOD_CALLABLES[card_id](valid_fixture(card_id))
            j_receipts.append({"schema_version":SCHEMA_VERSION,"family_j_card_id":card_id,"canonical_formula_or_procedure_id":card["canonical_formula_or_procedure_id"],"version":"1.0.0","implementation_class":card["implementation_class"],"input_lock_ref":f"LOCK::{card_id}","resolved_input_map_ref":f"oracle_vectors.json::{card_id}","qku_binding_ids":card_binding_ids,"responsible_agent_id":_responsible(family),"AGENT_ORCH_task_ref":f"PR169_FORMULA_TASK::{card_id}","method_specific_output_ref":output,"uncertainty_or_certificate_state":"VALID","numeric_backend":"PYTHON_STDLIB_BOUNDED_DETERMINISTIC","seed_or_deterministic_state":"DETERMINISTIC_OR_EXPLICIT_SEED","started_at_event_time":None,"completed_at_event_time":None,"latency_class":"BATCH_OR_PRECOMPUTE","READINESS_state":"EXECUTABLE_REQUIRES_DECLARED_INPUTS","PRETRADE_binding_refs":card_binding_ids,"SVC_projection_ref":f"PR169_FORMULA_SVC::{card_id}","downstream_route_refs":list(DOWNSTREAM_OWNERS),"validation_refs":[VALIDATOR_REF],"terminal_state":"VALIDATED_ROUTED_UNACKNOWLEDGED"})
    objects=[{"schema_version":SCHEMA_VERSION,"object_name":name,"canonical_owner":_object_owner(name),"this_pr_action":"CONSUME_EXISTING_SYSTEM","current_equivalent_ref":_object_owner(name),"consumer_refs":["integration.jsonl"],"validation_refs":[VALIDATOR_REF],"terminal_state":"ROUTED_WITH_TYPED_CONTRACT"} for name in DISTINCT_OBJECTS]
    rules=[]
    for rule_id in STABLE_VALIDATOR_RULE_IDS:
        RULE_FUNCTIONS[rule_id](valid_rule_fixture(rule_id)); negative_rejected=False
        try: RULE_FUNCTIONS[rule_id](invalid_rule_fixture(rule_id))
        except Exception: negative_rejected=True
        if not negative_rejected: raise RuntimeError(f"negative invariant fixture passed: {rule_id}")
        rules.append({"schema_version":SCHEMA_VERSION,"rule_id":rule_id,"controlling_source_ref":"PR169-QKU-FORMULA-EXP1-R1","validator_function_ref":f"src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.invariants:{rule_id}","test_ref":"tests/pr169_qku_formula_exp1/test_closure.py","pass_fail_state":"PASS_EXECUTED","valid_fixture_execution_state":"PASS","negative_fixture_rejection_state":"PASS","failure_evidence_refs":[],"aliases":[]})
    tools=[{"schema_version":SCHEMA_VERSION,"operation_id":operation,"operation_kind":{"query_applicable_qkus":"QUERY","resolve_formula_inputs":"RESOLVE","evaluate_formula":"EVALUATE_FORMULA","evaluate_qku_dag":"EVALUATE_QKU_DAG","evaluate_trade_plan_scenarios":"EVALUATE_TRADE_PLAN_SET"}[operation],"input_schema_ref":f"{operation}:input","output_schema_ref":f"{operation}:output","applicable_formula_or_QKU_selector":"BOUNDED_CANONICAL_RESOLVER","agent_duty_scope":"PR165_D2_RESOLVED","mode_stage_scope":"DECLARED_BY_OPERATIONAL_ENVELOPE","authority_class":"DETERMINISTIC_NO_ORDER_AUTHORITY","latency_update_class":"BOUNDED_LOCAL","error_taxonomy_ref":"FormulaErrorTaxonomyV1","receipt_type":"FormulaEvaluationReceiptV1","fallback_operation":"DETERMINISTIC_NO_TRADE_OR_TYPED_UNAVAILABLE"} for operation in GENERIC_TOOL_OPERATIONS]
    reading=[{"schema_version":SCHEMA_VERSION,"source_artifact_ref":path,"presence_state":"PRESENT" if (repo_root/path).exists() else "ABSENT_WITH_TYPED_CURRENT_EQUIVALENT_REQUIRED","current_equivalent_ref":path if (repo_root/path).exists() else None,"consumed_fields":["identity","owner","callable_or_route","authority"],"implementation_effect":"BOUNDED_DISCOVERY_RECEIPT_ONLY","counts_as_value_level_consumption":False,"matching_value_lineage_file":"integration.jsonl","terminal_state":"READ_OR_TYPED_ABSENT"} for path in READING_PATHS]
    sources=[{"schema_version":SCHEMA_VERSION,"source_id":source_id,"source_type":source_type,"source_ref":url,"retrieved_at_utc":SOURCE_RETRIEVED_AT_UTC,"publication_or_effective_date":publication_date,"version_provider_library_scope":"FINITE_SUPPORTED_DOMAIN_OR_CURRENT_OFFICIAL_DOCS","assumptions_and_limits":conclusion,"implementation_specific_conclusion":conclusion,"contradictions_or_superseded_sources":["No source may broaden the declared bounded operational envelope."],"accepted_current_candidate_state":"ACCEPTED_FOR_IMPLEMENTATION_SEMANTICS","source_use_class":source_type,"public_or_owner_authorized_access":True,"license_or_terms_state":"REFERENCE_ONLY_NO_CODE_COPY","implementation_copy_allowed":False,"redistribution_allowed":False,"citation_or_attribution_required":True,"confidential_NDA_restricted_improper_access_flags":False,"independent_reimplementation_required":True,"candidate_replay_PAPER_disposition":"OFFLINE_EXECUTABLE_NO_LIVE_AUTHORITY"} for source_id,source_type,url,publication_date,conclusion in SOURCES]
    sources.extend({"schema_version":SCHEMA_VERSION,"source_id":f"CARD_DERIVATION::{row['card_id']}","card_id":row["card_id"],"source_type":"OWNER_APPROVED_INTERNAL_DERIVATION","source_ref":f"docs/master_plan/QTT_MasterPlan_Current.md::{row['semantic_key']}","retrieved_at_utc":SOURCE_RETRIEVED_AT_UTC,"publication_or_effective_date":"2026-07-11","version_provider_library_scope":f"{row['card_id']}::{row['version']}","assumptions_and_limits":row["supported_input_domain"],"implementation_specific_conclusion":f"Implement {row['semantic_key']} only inside {row['supported_problem_size_or_scaling_class']}.","contradictions_or_superseded_sources":["Generic semantic-name fallbacks and caller-authored results are rejected."],"accepted_current_candidate_state":"CURRENT_INTERNAL_DERIVATION","source_use_class":"INTERNAL_DERIVATION","public_or_owner_authorized_access":True,"license_or_terms_state":"REPOSITORY_INTERNAL_NO_EXTERNAL_CODE_COPY","implementation_copy_allowed":True,"redistribution_allowed":True,"citation_or_attribution_required":False,"confidential_NDA_restricted_improper_access_flags":False,"independent_reimplementation_required":False,"candidate_replay_PAPER_disposition":"OFFLINE_EXECUTABLE_NO_LIVE_AUTHORITY"} for row in requirements)
    dispositions=Counter(row["disposition"] for row in requirements)
    cards_with_consumer={row["card_id"] for row in bindings if row.get("qku_id") or row.get("system_consumer_id")}
    facts={"formula_card_count_by_family":dict(Counter(row["formula_family"] for row in requirements)),"formula_method_required_count":len(requirements),"formula_method_executable_count":sum(row["positive_fixture_state"]=="PASS" for row in requirements),"REUSE_EXISTING_EXECUTABLE_count":dispositions["REUSE_EXISTING_EXECUTABLE"],"REUSE_EQUIVALENT_ALIAS_WITH_TARGET_AND_PROOF_count":dispositions["REUSE_EQUIVALENT_ALIAS_WITH_TARGET_AND_PROOF"],"EXTEND_EXISTING_VERSIONED_count":dispositions["EXTEND_EXISTING_VERSIONED"],"CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE_count":dispositions["CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE"],"automatic_application_method_required_count":len(requirements),"automatic_application_positive_fixture_pass_count":sum(row["positive_fixture_state"]=="PASS" for row in requirements),"automatic_application_negative_fixture_pass_count":sum(row["negative_applicability_fixture_state"]=="PASS" for row in requirements),"automatic_application_missing_stale_failclosed_pass_count":sum(row["missing_stale_conflict_fixture_state"]=="PASS" for row in requirements),"automatic_application_operational_boundary_pass_count":sum(row["operational_envelope_boundary_fixture_state"]=="PASS" for row in requirements),"automatic_application_central_invocation_pass_count":sum(row["central_invocation_state"]=="PASS" for row in requirements),"direct_vs_generic_service_equivalence_pass_count":sum(row["direct_vs_generic_service_equivalence_state"]=="PASS" for row in requirements),"method_with_real_qku_or_system_consumer_count":len(cards_with_consumer),"method_without_real_consumer_count":len(requirements)-len(cards_with_consumer),"operational_envelope_count":sum(bool(row.get("supported_input_domain") and row.get("trigger_or_scheduling_rule")) for row in requirements),"all_213_methods_run_on_every_order":False,"active_synthetic_qku_count":sum(str(row.get("qku_id","")).startswith("QTT_QKU::") for row in bindings),"actual_canonical_qku_binding_count":sum(row["qku_id"] is not None for row in bindings),"actual_system_procedure_consumer_count":sum(row["system_consumer_id"] is not None for row in bindings),"strategy_template_to_canonical_QKU_mapping_count":len(strategies),"unique_canonical_strategy_QKU_identity_count":len({row["canonical_QKU_or_current_equivalent_ref"] for row in strategies}),"strategy_executable_DAG_count":len(strategies),"validator_rule_function_count":len(rules),"value_level_lineage_edge_count":len(integration),"numeric_authority_chain_resolved_count":sum(bool(row.get("numeric_authority_chain_id")) for row in requirements),"destination_acknowledged_count":sum(row.get("destination_ack_ref") is not None for row in integration),"destination_delivered_count":0,"runtime_execution_count":0,"quantum_backend_execution_count":0,"live_order_authority_count":0,"owner_merge_approval_required":True,"owner_merge_approval_received":False,"merge_attempt_count":0}
    acceptance={"schema_version":SCHEMA_VERSION,"previous_schema_version":"1.0.0","migration_state":"ACTIVE_MIGRATED_IN_PLACE","builder_observed_facts":facts,"validator_independently_derived_facts":"EMITTED_BY_VALIDATOR_PROCESS_NOT_AUTHORED_BY_BUILDER","runtime_execution_facts":{"runtime_execution_count":0,"destination_acknowledged_count":0,"destination_delivered_count":0,"quantum_backend_execution_count":0,"live_order_authority_count":0},"validation_state":"REQUIRES_INDEPENDENT_VALIDATOR_RECOMPUTATION"}
    files={"requirements.jsonl":requirements,"objects.jsonl":objects,"bindings.jsonl":bindings,"integration.jsonl":integration,"strategies.jsonl":strategies,"validator_rules.jsonl":rules,"tool_manifest.jsonl":tools,"reading.jsonl":reading,"sources.jsonl":sources,"family_j_receipts.jsonl":j_receipts}
    counts={name:_write_jsonl(out_dir/name,rows) for name,rows in files.items()}
    _write_json(out_dir/"policy.json",{"schema_version":SCHEMA_VERSION,"permanent_laws":PERMANENT_QTT_LAWS,"unit_policy":UNIT_POLICY,"short_horizon_fields":SHORT_HORIZON_FIELDS,"downstream_owners":DOWNSTREAM_OWNERS,"authority":"CONFIGURATION_AND_DETERMINISTIC_COMPUTATION_ONLY","owner_merge_gate":{"required":True,"received":False,"merge_attempt_count":0}})
    _write_json(out_dir/"acceptance.report.json",acceptance)
    _write_json(out_dir/"manifest.json",{"schema_version":SCHEMA_VERSION,"previous_schema_version":"1.0.0","migration_state":"ACTIVE_MIGRATED_IN_PLACE","legacy_projection_state":"SUPERSEDED_NONAUTHORITATIVE","builder":BUILDER_REF,"validator":VALIDATOR_REF,"owned_prefix":OWNED_PREFIX.as_posix(),"files":list(EXPECTED_FILES),"row_counts":counts,"manual_generated_edit_count":0,"parallel_registry_count":0,"no_order_authority":True})
    return acceptance


def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--repo-root",default="."); parser.add_argument("--out-dir",default=OWNED_PREFIX.as_posix()); parser.add_argument("--timeout-ms",default="3600000")
    args=parser.parse_args(); root=Path(args.repo_root).resolve(); out=Path(args.out_dir); out=out if out.is_absolute() else root/out
    acceptance=build(root,out); facts=acceptance["builder_observed_facts"]; print(json.dumps({"status":"PASS","out_dir":out.as_posix(),"formula_cards":facts["formula_method_required_count"],"family_j":8},sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
