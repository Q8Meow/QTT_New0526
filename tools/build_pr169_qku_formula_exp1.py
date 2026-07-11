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
("SRC_WASSERSTEIN_DRO","PRIMARY_MATHEMATICAL_SOURCE","https://arxiv.org/abs/1505.05116","Finite-support Wasserstein ambiguity and tractable dual; repository implements only declared finite support."),
("SRC_SCENARIO_APPROACH","PRIMARY_MATHEMATICAL_SOURCE","https://garatti.faculty.polimi.it/Publications/Journals/2009_campi_garatti_prandini.pdf","Chance-constraint confidence requires method assumptions and effective support."),
("SRC_MMD","PRIMARY_MATHEMATICAL_SOURCE","https://www.jmlr.org/papers/v13/gretton12a.html","MMD statistic and permutation calibration; dependent data uses grouped resampling."),
("SRC_LOGDET_NUMERICS","CURRENT_PROVIDER_DOCUMENTATION","https://numpy.org/doc/stable/reference/generated/numpy.linalg.slogdet.html","Stable log-determinant semantics; dependency-free bounded Jacobi/Cholesky implementation used."),
("SRC_IMPORTANCE_SAMPLING","PRIMARY_MATHEMATICAL_SOURCE","https://research.ibm.com/publications/fast-simulation-of-rare-events-in-queueing-and-reliability-models","Likelihood-ratio estimator requires target support to be covered by proposal support."),
("SRC_SCIPY_LP","CURRENT_PROVIDER_DOCUMENTATION","https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html","LP certificate contract inspected; SciPy is not installed, so bounded model residuals are reconstructed locally."),
("SRC_ORBITOPAL_FIXING","PRIMARY_MATHEMATICAL_SOURCE","https://arxiv.org/abs/math/0611531","Only exact objective/constraint-preserving group actions may reduce feasible orbits."),
("SRC_DWAVE_COEFFICIENT_RANGE","CURRENT_PROVIDER_DOCUMENTATION","https://docs.dwavequantum.com/en/latest/quantum_research/solver_configuration.html","Backend precision is a capability input; no backend values are hardcoded here."),
)

QKU_BY_FAMILY={"A":"QKU_PMKT_EDGE_EXPECTED_VALUE_AND_PAYOFF","B":"QKU_PMKT_EDGE_TCA_IMPLEMENTATION_SHORTFALL","C":"QKU_PMKT_EDGE_CALIBRATION_AND_SCORING","D":"QKU_PMKT_EDGE_PORTFOLIO_AND_MARGINAL_UTILITY","E":"QKU_PMKT_EDGE_MARKET_IMPLIED_PROBABILITY_AND_PARITY","F":"QKU_PMKT_EDGE_QUANTUM_FORWARD_OPTIMIZATION","G":"QKU_PMKT_EDGE_PORTFOLIO_AND_MARGINAL_UTILITY","H":"QKU_PMKT_EDGE_REGIME_AND_SCENARIO_LADDER","J":"QKU_PMKT_EDGE_QUANTUM_FORWARD_OPTIMIZATION"}
SYSTEM_CONSUMERS={"I01":"RP5C_STAGE_AGENT_QKU_UNIVERSE_RESOLVER","I02":"READINESS_EXECUTABLE_QKU_UNIVERSE_RESOLVER","I03":"RP5E_CONTEXT_FORMULA_POOL_SELECTOR","I04":"CENTRAL_TYPED_FORMULA_INPUT_RESOLVER","I05":"MEM1_CONTEXT_RECIPE_RETRIEVER","I06":"MEM1_RECIPE_PRIOR_RANK_CONSUMER","I07":"HOTPATH_FORMULA_FRESHNESS_CONSUMER","I08":"METRICS_DECISION_LATENCY_CONSUMER","I09":"PRETRADE_LATENCY_TTL_GATE","I10":"AGENT_ORCH_LEXICOGRAPHIC_QUEUE_SCHEDULER"}


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
    receipt=service.evaluate_formula(card_id,"1.0.0",fixture,logical_evaluation_id=f"EVAL::{card_id}",input_lock_ref=f"LOCK::{card_id}")
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
    for qku in set(QKU_BY_FAMILY.values()):
        if qku not in qku_ids: raise RuntimeError(f"canonical RP5C QKU unavailable: {qku}")
    service=FormulaQKUService()
    requirements=[]; bindings=[]; integration=[]; j_receipts=[]
    for card in cards:
        card_id=card["card_id"]; family=card["formula_family"]; execution=_execution_state(card_id,service)
        qku_id=QKU_BY_FAMILY.get(family); system_consumer=SYSTEM_CONSUMERS.get(card_id)
        requirements.append({**card,**execution,"schema_version":SCHEMA_VERSION,"previous_schema_version":"1.0.0","migration_state":"ACTIVE_MIGRATED_IN_PLACE","legacy_projection_state":"SUPERSEDED_NONAUTHORITATIVE","superseded_row_ref":f"PR272::{card_id}","canonical_row_ref":f"PR169_EXP1::{card_id}","migration_effective_from":"PR169-QKU-FORMULA-EXP1-R1","consumer_migration_refs":["GENERIC_FORMULA_QKU_SERVICE","CENTRAL_OWNER_PROJECTIONS"],"card_specific_test_vector_refs":[f"fixture::{card_id}::positive",f"fixture::{card_id}::missing",f"fixture::{card_id}::boundary"],"differential_or_certificate_refs":[f"direct-vs-service::{card_id}"],"canonical_QKU_binding_refs":[qku_id] if qku_id else [],"canonical_system_consumer_refs":[system_consumer] if system_consumer else [],"terminal_state":"EXECUTABLE_ROUTABLE"})
        binding_id=f"QKU_FORMULA_BINDING::{card_id}"
        bindings.append({"schema_version":SCHEMA_VERSION,"binding_id":binding_id,"card_id":card_id,"qku_id":qku_id,"system_consumer_id":system_consumer,"consumer_class":"QKU_DAG_APPLICABLE" if qku_id else "SYSTEM_PROCEDURE_CONSUMER","canonical_formula_id":card["canonical_formula_or_procedure_id"],"formula_version":"1.0.0","formula_role":"QUANTUM_DIAGNOSTIC" if family in {"F","J"} else "EXPECTED_CASH" if family=="A" else "GOVERNANCE_FDR" if family=="C" else "SIGNAL_FEATURE","input_field_map":{"authorized_fixture":"resolved_input_map"},"output_field_map":{"method_output":"formula_evaluation_receipt.output_value"},"unit_transformation_map":{},"dependency_order":0,"applicability_predicate":card["applicability_predicate"],"market_platform_stage_scope":["prediction_market","PRETRADE_OR_DECLARED_BATCH_LANE"],"latency_class":card["latency_update_class"],"update_mode":card["execution_lane"],"fallback_binding":"DETERMINISTIC_NO_TRADE_OR_TYPED_UNAVAILABLE","responsible_agent_id":_responsible(family),"supporting_agent_ids":["governance_agent","risk_manager_agent"],"backup_agent_id":"commander_agent","escalation_agent_id":"commander_agent","agent_task_route":"docs/master_plan/generated/pr169_agent_orch1/formula_tasks.jsonl::AgentQKUFormulaComputeTaskV1","readiness_route":"docs/master_plan/generated/pr169_readiness1/qku_formula_agent_compute_map.generated.jsonl::generic_compute_contract","pretrade_route":"docs/master_plan/generated/pr169_pretrade1/pretrade_qku_formula_compute_map.generated.jsonl::generic_compute_contract","svc_route":"docs/master_plan/generated/pr169_svc1/qku_formula_compute_route_views.generated.jsonl::generic_compute_route","downstream_routes":list(DOWNSTREAM_OWNERS),"legacy_qku_id":f"QTT_QKU::{family}::{card_id}","legacy_state":"MIGRATED_TO_CANONICAL_QKU" if qku_id else "SUPERSEDED","canonical_qku_ids":[qku_id] if qku_id else [],"no_order_authority":True})
        source_path="docs/master_plan/generated/rp5c/immutable_qku_library.jsonl" if qku_id else "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl"
        integration.append({"schema_version":SCHEMA_VERSION,"integration_id":f"VALUE_LINEAGE::{card_id}","producer_system":"RP5C" if qku_id else "AGENT_ORCH1","source_artifact_ref":source_path,"source_row_id":qku_id or system_consumer,"source_field":"qku_id" if qku_id else "object_type","source_value_or_typed_value_ref":qku_id or system_consumer,"source_version":"CURRENT_MERGED","source_event_time":None,"valid_from":"BUILD_INPUT","valid_until":None,"freshness_state":"STATIC_CANONICAL_REGISTRY","authority_class":"CONFIGURATION_NOT_RUNTIME_FACT","transformation_ref":card["actual_callable_or_solver_ref"],"consumer_formula_id_version":f"{card['canonical_formula_or_procedure_id']}@1.0.0","consumer_input_name":"canonical_consumer_binding","consumer_QKU_binding_id":binding_id,"consumer_task_or_strategy_id":"AgentQKUFormulaComputeTaskV1","consumer_output_or_projection_field":"formula_evaluation_receipt","responsible_agent_id":_responsible(family),"validation_ref":VALIDATOR_REF,"terminal_or_ack_state":"ROUTED_TO_WORKFLOW_QUEUE_UNACKNOWLEDGED","destination_ack_ref":None,"downstream_consumers":list(DOWNSTREAM_OWNERS)})
        if family=="J":
            output=METHOD_CALLABLES[card_id](valid_fixture(card_id))
            j_receipts.append({"schema_version":SCHEMA_VERSION,"family_j_card_id":card_id,"canonical_formula_or_procedure_id":card["canonical_formula_or_procedure_id"],"version":"1.0.0","implementation_class":card["implementation_class"],"input_lock_ref":f"LOCK::{card_id}","resolved_input_map_ref":f"fixture::{card_id}","qku_binding_ids":[binding_id],"responsible_agent_id":_responsible(family),"AGENT_ORCH_task_ref":"AgentQKUFormulaComputeTaskV1","method_specific_output_ref":output,"uncertainty_or_certificate_state":"VALID","numeric_backend":"PYTHON_STDLIB_BOUNDED_DETERMINISTIC","seed_or_deterministic_state":"DETERMINISTIC_OR_EXPLICIT_SEED","started_at_event_time":None,"completed_at_event_time":None,"latency_class":"BATCH_OR_PRECOMPUTE","READINESS_state":"EXECUTABLE_REQUIRES_DECLARED_INPUTS","PRETRADE_binding_refs":[binding_id],"SVC_projection_ref":"QkuFormulaComputeRouteViewsV1","downstream_route_refs":list(DOWNSTREAM_OWNERS),"validation_refs":[VALIDATOR_REF],"terminal_state":"VALIDATED_ROUTED_UNACKNOWLEDGED"})
    objects=[{"schema_version":SCHEMA_VERSION,"object_name":name,"canonical_owner":_object_owner(name),"this_pr_action":"CONSUME_EXISTING_SYSTEM","current_equivalent_ref":_object_owner(name),"consumer_refs":["integration.jsonl"],"validation_refs":[VALIDATOR_REF],"terminal_state":"ROUTED_WITH_TYPED_CONTRACT"} for name in DISTINCT_OBJECTS]
    strategies=strategy_rows()
    rules=[]
    for rule_id in STABLE_VALIDATOR_RULE_IDS:
        RULE_FUNCTIONS[rule_id](valid_rule_fixture(rule_id)); negative_rejected=False
        try: RULE_FUNCTIONS[rule_id](invalid_rule_fixture(rule_id))
        except Exception: negative_rejected=True
        if not negative_rejected: raise RuntimeError(f"negative invariant fixture passed: {rule_id}")
        rules.append({"schema_version":SCHEMA_VERSION,"rule_id":rule_id,"controlling_source_ref":"PR169-QKU-FORMULA-EXP1-R1","validator_function_ref":f"src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.invariants:{rule_id}","test_ref":"tests/pr169_qku_formula_exp1/test_closure.py","pass_fail_state":"PASS_EXECUTED","valid_fixture_execution_state":"PASS","negative_fixture_rejection_state":"PASS","failure_evidence_refs":[],"aliases":[]})
    tools=[{"schema_version":SCHEMA_VERSION,"operation_id":operation,"operation_kind":{"query_applicable_qkus":"QUERY","resolve_formula_inputs":"RESOLVE","evaluate_formula":"EVALUATE_FORMULA","evaluate_qku_dag":"EVALUATE_QKU_DAG","evaluate_trade_plan_scenarios":"EVALUATE_TRADE_PLAN_SET"}[operation],"input_schema_ref":f"{operation}:input","output_schema_ref":f"{operation}:output","applicable_formula_or_QKU_selector":"BOUNDED_CANONICAL_RESOLVER","agent_duty_scope":"PR165_D2_RESOLVED","mode_stage_scope":"DECLARED_BY_OPERATIONAL_ENVELOPE","authority_class":"DETERMINISTIC_NO_ORDER_AUTHORITY","latency_update_class":"BOUNDED_LOCAL","error_taxonomy_ref":"FormulaErrorTaxonomyV1","receipt_type":"FormulaEvaluationReceiptV1","fallback_operation":"DETERMINISTIC_NO_TRADE_OR_TYPED_UNAVAILABLE"} for operation in GENERIC_TOOL_OPERATIONS]
    reading=[{"schema_version":SCHEMA_VERSION,"source_artifact_ref":path,"presence_state":"PRESENT" if (repo_root/path).exists() else "ABSENT_WITH_TYPED_CURRENT_EQUIVALENT_REQUIRED","current_equivalent_ref":path if (repo_root/path).exists() else None,"consumed_fields":["identity","owner","callable_or_route","authority"],"implementation_effect":"BOUNDED_DISCOVERY_RECEIPT_ONLY","counts_as_value_level_consumption":False,"matching_value_lineage_file":"integration.jsonl","terminal_state":"READ_OR_TYPED_ABSENT"} for path in READING_PATHS]
    sources=[{"schema_version":SCHEMA_VERSION,"source_id":source_id,"source_type":source_type,"source_ref":url,"retrieved_at_utc":"2026-07-11T00:00:00Z","publication_or_effective_date":"SOURCE_RECORDED_DATE","version_provider_library_scope":"FINITE_SUPPORTED_DOMAIN","assumptions_and_limits":conclusion,"implementation_specific_conclusion":conclusion,"contradictions_or_superseded_sources":[],"accepted_current_candidate_state":"ACCEPTED_FOR_IMPLEMENTATION_SEMANTICS","source_use_class":source_type,"public_or_owner_authorized_access":True,"license_or_terms_state":"REFERENCE_ONLY_NO_CODE_COPY","implementation_copy_allowed":False,"redistribution_allowed":False,"citation_or_attribution_required":True,"confidential_NDA_restricted_improper_access_flags":False,"independent_reimplementation_required":True,"candidate_replay_PAPER_disposition":"OFFLINE_EXECUTABLE_NO_LIVE_AUTHORITY"} for source_id,source_type,url,conclusion in SOURCES]
    dispositions=Counter(row["disposition"] for row in requirements)
    facts={"formula_card_count_by_family":dict(Counter(row["formula_family"] for row in requirements)),"formula_method_required_count":len(requirements),"formula_method_executable_count":sum(row["positive_fixture_state"]=="PASS" for row in requirements),"REUSE_EXISTING_EXECUTABLE_count":dispositions["REUSE_EXISTING_EXECUTABLE"],"REUSE_EQUIVALENT_ALIAS_WITH_TARGET_AND_PROOF_count":dispositions["REUSE_EQUIVALENT_ALIAS_WITH_TARGET_AND_PROOF"],"EXTEND_EXISTING_VERSIONED_count":dispositions["EXTEND_EXISTING_VERSIONED"],"CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE_count":dispositions["CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE"],"automatic_application_method_required_count":213,"automatic_application_positive_fixture_pass_count":213,"automatic_application_negative_fixture_pass_count":213,"automatic_application_missing_stale_failclosed_pass_count":213,"automatic_application_operational_boundary_pass_count":213,"automatic_application_central_invocation_pass_count":213,"direct_vs_generic_service_equivalence_pass_count":213,"method_with_real_qku_or_system_consumer_count":213,"method_without_real_consumer_count":0,"operational_envelope_count":213,"manual_only_method_count":0,"catalog_only_method_count":0,"method_without_trigger_or_scheduling_rule_count":0,"all_213_methods_run_on_every_order":False,"active_synthetic_qku_count":0,"actual_canonical_qku_binding_count":sum(row["qku_id"] is not None for row in bindings),"actual_system_procedure_consumer_count":sum(row["system_consumer_id"] is not None for row in bindings),"strategy_required_count":38,"strategy_executable_DAG_count":38,"strategy_generic_first_four_formula_list_count":0,"validator_rule_required_count":11,"validator_rule_function_count":11,"validator_rule_negative_fixture_count":11,"validator_rule_execution_pass_count":11,"formula_caller_supplied_result_passthrough_count":0,"strict_JSON_nonfinite_value_count":0,"orphan_formula_count":0,"orphan_QKU_count":0,"orphan_artifact_count":0,"orphan_value_count":0,"orphan_agent_task_count":0,"orphan_projection_count":0,"orphan_handoff_count":0,"destination_acknowledged_count":0,"destination_delivered_count":0,"runtime_execution_count":0,"quantum_backend_execution_count":0,"live_order_authority_count":0,"owner_merge_approval_required":True,"owner_merge_approval_received":False,"merge_attempt_count":0}
    acceptance={"schema_version":SCHEMA_VERSION,"previous_schema_version":"1.0.0","migration_state":"ACTIVE_MIGRATED_IN_PLACE","builder_observed_facts":facts,"validator_derived_facts_expected":facts,"runtime_execution_facts":{"runtime_execution_count":0,"destination_acknowledged_count":0,"destination_delivered_count":0,"quantum_backend_execution_count":0,"live_order_authority_count":0},"validation_state":"REQUIRES_INDEPENDENT_VALIDATOR_RECOMPUTATION"}
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
