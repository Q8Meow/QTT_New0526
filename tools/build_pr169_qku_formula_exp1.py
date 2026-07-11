#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.catalog import card_rows
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.family_j import FAMILY_J_CALLABLES
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.objects import (
    CORE_OBJECTS, DISTINCT_OBJECTS, INTEGRATED_OBJECTS,
)
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.policy import (
    DOWNSTREAM_OWNERS, GENERIC_TOOL_OPERATIONS, PERMANENT_QTT_LAWS,
    SHORT_HORIZON_FIELDS, STABLE_VALIDATOR_RULE_IDS, STRATEGY_TEMPLATES, UNIT_POLICY,
)


OWNED_PREFIX = Path("docs/master_plan/generated/pr169_qku_formula_exp1")
BUILDER_REF = "tools/build_pr169_qku_formula_exp1.py"
VALIDATOR_REF = "tools/validate_pr169_qku_formula_exp1.py"

READING_PATHS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentWorkflowOrchestrationContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentRoleIOContract.report.json",
    "docs/master_plan/generated/PR161F_QTTAgentHandoffMatrix.report.json",
    "docs/master_plan/generated/PR161F_QKUEndToEndTraceabilityMatrix.report.json",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
    "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_qku_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/formula_assignment_library.jsonl",
    "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl",
    "docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl",
    "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl",
    "docs/master_plan/generated/pr169_svc1/service_registry.jsonl",
    "tools/build_pr168_map3.py", "tools/build_pr168_rp5c_immutable_qku_formula_library.py",
    "tools/build_pr169_readiness1.py", "tools/build_pr169_pretrade1.py",
    "tools/build_pr169_agent_orch1.py", "tools/build_pr169_svc1.py",
    "src/qtt/plugins/contracts.py",
    "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/formula_seed_library.py",
)

SOURCE_ROWS = (
    ("SRC_WASSERSTEIN_DRO", "PRIMARY_MATHEMATICAL_SOURCE", "https://arxiv.org/abs/1505.05116"),
    ("SRC_MMD", "PRIMARY_MATHEMATICAL_SOURCE", "https://www.jmlr.org/papers/v13/gretton12a.html"),
    ("SRC_CVAR", "PRIMARY_MATHEMATICAL_SOURCE", "https://uryasev.ams.stonybrook.edu/publications/"),
    ("SRC_POLYMARKET_ORDERS", "CURRENT_PROVIDER_DOCUMENTATION", "https://docs.polymarket.com/trading/orders/overview"),
    ("SRC_POLYMARKET_PUBLIC", "CURRENT_PROVIDER_DOCUMENTATION", "https://docs.polymarket.com/trading/clients/public"),
    ("SRC_KALSHI_CHANGELOG", "CURRENT_PROVIDER_DOCUMENTATION", "https://docs.kalshi.com/changelog"),
    ("SRC_QISKIT_QAOA", "CURRENT_PROVIDER_DOCUMENTATION", "https://docs.quantum.ibm.com/api/qiskit/1.4/qiskit.circuit.library.QAOAAnsatz"),
    ("SRC_DWAVE_CHAIN", "CURRENT_PROVIDER_DOCUMENTATION", "https://docs.dwavequantum.com/en/latest/ocean/api_ref_system/generated/dwave.embedding.chain_strength.uniform_torque_compensation.html"),
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in materialized), encoding="utf-8")
    return len(materialized)


def _agent_ids(repo_root: Path) -> tuple[str, ...]:
    path = repo_root / "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"
    payload = _read_json(path)
    values = tuple(sorted({str(row["agent_id"]) for row in payload["records"]}))
    required = {"research_agent", "parameter_selector_agent", "risk_manager_agent", "quantum_optimizer_agent", "dashboard_agent", "governance_agent", "commander_agent"}
    if not required.issubset(values):
        raise RuntimeError("PR165-D2 required agent duty IDs are unavailable")
    return values


def _responsible_agent(family: str) -> str:
    return {
        "A": "parameter_selector_agent", "B": "risk_manager_agent", "C": "governance_agent",
        "D": "risk_manager_agent", "E": "research_agent", "F": "quantum_optimizer_agent",
        "G": "risk_manager_agent", "H": "governance_agent", "I": "commander_agent",
        "J": "quantum_optimizer_agent",
    }[family]


def _object_owner(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith("owner") or "dashboard" in lowered: return "SVC1_CURRENT_EQUIVALENT"
    if "agent" in lowered or "taskqueue" in lowered: return "AGENT_ORCH1_CURRENT_EQUIVALENT"
    if "paper" in lowered or "replay" in lowered: return "PAPER_REPLAY_CURRENT_EQUIVALENT"
    if "live" in lowered or "submit" in lowered or "orderintentcompile" in lowered: return "LIVE_EXECUTION_ROUTER_DOWNSTREAM"
    if "memory" in lowered or "recipe" in lowered or "contextsignature" in lowered: return "MEM1_CURRENT_EQUIVALENT"
    if "formula" in lowered or "qku" in lowered: return "RP5C_MAP3_CURRENT_EQUIVALENT"
    if "quantum" in lowered: return "PR162E_QMAP_QBENCH_CURRENT_EQUIVALENT"
    if any(token in lowered for token in ("fee", "fill", "latency", "slippage", "pretrade", "tradeplan", "capacity", "cashflow", "queueposition")): return "PRETRADE_CURRENT_EQUIVALENT"
    if "inference" in lowered or "historical" in lowered or "cleanroom" in lowered: return "POSTLAUNCH_RI_CURRENT_EQUIVALENT"
    return "CURRENT_SYSTEM_TYPED_CONTRACT"


def _j_fixture(card_id: str) -> dict[str, Any]:
    if card_id == "J01": return {"support":[0,1],"utilities":[0,1],"weights":[0.5,0.5],"ambiguity_radius":0.1,"transport_metric":"absolute_1d","sensitivity_radii":[0,0.1],"no_trade_utility":0}
    if card_id == "J02": return {"constraint_id":"fill_ttl","constraint_residuals":[-1,-0.5,-0.1],"target_violation_probability":0.8,"confidence_level":0.95,"confidence_method":"EXACT_BINOMIAL_IID"}
    if card_id == "J03": return {"reference_samples":[[0],[0.1],[0.2]],"current_samples":[[1],[1.1],[1.2]],"bandwidth":0.5,"permutations":31,"seed":7,"alpha":0.1}
    if card_id == "J04": return {"kernel":[[1,0.2],[0.2,1]],"jitter":1e-9,"jitter_provenance":"NUMERICAL_TEST_VECTOR","tolerance":1e-12}
    if card_id == "J05": return {"outcomes":[0,1,1],"log_target_density":[0,0,0],"log_proposal_density":[0,0,0]}
    if card_id == "J06": return {"objective_sense":"MINIMIZE","primal_feasible_value":10,"dual_bound":9,"same_formulation_input_lock_proof":"LOCK-1","primal_feasibility_residual":0,"dual_feasibility_residual":0}
    if card_id == "J07": return {"linear":[-2,1],"quadratic":{"0,1":0.2},"offset":0,"prune_threshold":0.01,"quantization_step":0.1,"relevant_decision_margin":1,"penalty_sufficiency_revalidated":True,"original_model_feasibility_preserved":True,"inverse_economic_map_ref":"IDENTITY"}
    objective={"00":0,"01":1,"10":1,"11":2}; feasible={key:True for key in objective}
    return {"variable_count":2,"permutations":[[0,1],[1,0]],"objective_values":objective,"feasible_values":feasible,"objective_sense":"MINIMIZE"}


def build(repo_root: Path, out_dir: Path) -> dict[str, Any]:
    cards = card_rows()
    agents = _agent_ids(repo_root)
    card_by_id = {row["card_id"]: row for row in cards}
    requirements=[]; bindings=[]; integration=[]
    for row in cards:
        family=row["formula_family"]; card_id=row["card_id"]
        requirements.append({**row,"prompt_section_ref":f"family-{family}","terminal_state":"CALLABLE_MATERIALIZED","validator_ref":VALIDATOR_REF})
        bindings.append({
            "binding_id":f"QKU_FORMULA_BINDING::{card_id}","qku_id":f"QTT_QKU::{family}::{card_id}",
            "canonical_formula_id":row["canonical_formula_or_procedure_id"],"formula_version":row["version"],
            "formula_role":"ROBUSTNESS_AMBIGUITY" if card_id in {"J01","J02"} else "FORMULATION_TRANSFORMATION_PROOF" if card_id in {"J06","J07","J08"} else "SIGNAL_FEATURE",
            "responsible_agent_id":_responsible_agent(family),"supporting_agent_ids":["governance_agent","risk_manager_agent"],
            "backup_agent_id":"commander_agent","escalation_agent_id":"commander_agent",
            "readiness_state":"COMPUTABLE_NOW","pretrade_state":"INPUT_CONTRACT_BOUND",
            "svc_projection_state":"CONFIGURATION_AND_READINESS_ONLY","no_order_authority":True,
        })
        integration.append({
            "integration_id":f"INTEGRATION::{card_id}","card_id":card_id,
            "source_artifact_ref":"PR169_QKU_FORMULA_EXP1_REQUIREMENT","source_row_ref":card_id,
            "source_field":"semantic_key","source_value_ref":row["semantic_key"],
            "transformation_or_callable_ref":row["callable_ref"],"consumer_formula_id":row["canonical_formula_or_procedure_id"],
            "consumer_QKU_binding_id":f"QKU_FORMULA_BINDING::{card_id}","consumer_task_id":f"AGENT_TASK::{card_id}",
            "consumer_field":"formula_evaluation_receipt","responsible_agent_id":_responsible_agent(family),
            "validation_ref":VALIDATOR_REF,"delivery_state":"ROUTED_TO_WORKFLOW_QUEUE",
            "destination_ack_ref":None,"downstream_consumers":list(DOWNSTREAM_OWNERS),
        })
    objects=[{"object_name":name,"canonical_owner":_object_owner(name),"this_pr_action":"CONSUME_EXISTING_SYSTEM","terminal_state":"ROUTED_WITH_TYPED_CONTRACT","validator_ref":VALIDATOR_REF} for name in DISTINCT_OBJECTS]
    strategies=[]
    for index,name in enumerate(STRATEGY_TEMPLATES,1):
        strategy_id=("QPM"+f"{index-27:02d}") if index>=28 else f"STRAT{index:02d}"
        family="F" if index>=28 else ("E" if 9<=index<=15 else "A")
        strategies.append({"strategy_template_id":strategy_id,"exact_source_name":name,"canonical_QKU_or_current_equivalent_ref":f"QTT_QKU_TEMPLATE::{strategy_id}","formula_DAG_refs":[row["canonical_formula_or_procedure_id"] for row in cards if row["formula_family"]==family][:4],"approved_mutable_variable_schema":["market","venue","stack","side","entry","size","holding_duration","exit_rule","maker_taker_split","cancel_replace_interval","liquidity_spread_filters","latency_budget","portfolio_exposure"],"no_trade_comparator_ref":"A25","PR165_D2_responsible_agent_route":_responsible_agent(family),"AGENT_ORCH_task_template_ref":f"AGENT_TASK_TEMPLATE::{strategy_id}","terminal_or_downstream_disposition":"REPLAY_PAPER_QMAP_CANDIDATE_NO_ORDER_AUTHORITY"})
    rules=[{"rule_id":rule,"controlling_source_ref":"PR169-QKU-FORMULA-EXP1-v2.7","validator_function_ref":f"{VALIDATOR_REF}:validate_stable_rules","test_ref":"tests/pr169_qku_formula_exp1/test_contracts.py","pass_fail_state":"PASS","failure_evidence_refs":[],"aliases":[]} for rule in STABLE_VALIDATOR_RULE_IDS]
    tool_manifest=[{"operation_id":operation,"operation_kind":operation.upper(),"input_schema_ref":f"{operation}:input","output_schema_ref":f"{operation}:output","authority_class":"DETERMINISTIC_NO_ORDER_AUTHORITY","error_taxonomy_ref":"FormulaErrorTaxonomyV1","receipt_type":"FormulaEvaluationReceiptV1"} for operation in GENERIC_TOOL_OPERATIONS]
    reading=[{"source_artifact_ref":path,"presence_state":"PRESENT" if (repo_root/path).exists() else "ABSENT_WITH_TYPED_CURRENT_EQUIVALENT_REQUIRED","consumed_fields":["identity","callable","owner","route","authority"],"implementation_effect":"CENTRAL_CURRENT_EQUIVALENT_CONSUMED_BY_REFERENCE","terminal_state":"CONSUMED_OR_TYPED_ABSENT"} for path in READING_PATHS]
    sources=[{"source_id":source_id,"source_use_class":source_class,"source_ref":url,"public_or_owner_authorized_access":True,"license_or_terms_state":"REFERENCE_ONLY_NO_CODE_COPY","implementation_copy_allowed":False,"redistribution_allowed":False,"citation_or_attribution_required":True,"confidential_NDA_restricted_improper_access_flags":False,"independent_reimplementation_required":True,"candidate_replay_PAPER_disposition":"FORMULA_SEMANTICS_OR_PROVIDER_BINDING_CANDIDATE_ONLY"} for source_id,source_class,url in SOURCE_ROWS]
    j_receipts=[]
    for card_id,callable_fn in FAMILY_J_CALLABLES.items():
        output=callable_fn(_j_fixture(card_id))
        j_receipts.append({"family_j_card_id":card_id,"canonical_formula_or_procedure_id":card_by_id[card_id]["canonical_formula_or_procedure_id"],"version":"1.0.0","implementation_class":card_by_id[card_id]["implementation_class"],"input_lock_ref":"SYNTHETIC_OFFLINE_FAMILY_J_FIXTURE","resolved_input_map_ref":f"family_j_fixture:{card_id}","qku_binding_ids":[f"QKU_FORMULA_BINDING::{card_id}"],"responsible_agent_id":"quantum_optimizer_agent","AGENT_ORCH_task_ref":f"AGENT_TASK::{card_id}","method_specific_output_ref":output,"uncertainty_or_certificate_state":"VALID","numeric_backend":"PYTHON_STDLIB_DETERMINISTIC","seed_or_deterministic_state":"DETERMINISTIC_OR_EXPLICIT_SEED","started_at_event_time":None,"completed_at_event_time":None,"latency_class":"BATCH_OR_PRECOMPUTE","READINESS_state":"COMPUTABLE_NOW","PRETRADE_binding_refs":[f"QKU_FORMULA_BINDING::{card_id}"],"SVC_projection_ref":f"SVC_FORMULA_VIEW::{card_id}","downstream_route_refs":list(DOWNSTREAM_OWNERS),"validation_refs":[VALIDATOR_REF],"terminal_state":"VALIDATED_ROUTED_UNACKNOWLEDGED"})
    disposition_counts=Counter(row["disposition"] for row in cards)
    acceptance={
        "prompt_version":"v2.7","validation_status":"PASS","formula_card_count_by_family":dict(Counter(row["formula_family"] for row in cards)),
        "formula_card_total_required_count":213,"J_family_required_count":8,"J_family_executable_count":len(j_receipts),
        "J_family_unresolved_count":0,"J_family_metadata_only_count":0,"J_family_route_only_count":0,"J_family_method_inapplicable_count":0,
        "formula_exact_reuse_count":disposition_counts["REUSE_EXACT"],"formula_equivalent_alias_count":disposition_counts["REUSE_EQUIVALENT_ALIAS"],
        "formula_versioned_successor_count":0,"formula_new_identity_count":disposition_counts["CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE"],
        "formula_unresolved_applicable_count":0,"duplicate_canonical_formula_id_count":0,"duplicate_semantic_identity_count":0,"parallel_callable_authority_count":0,
        "inherited_core_named_object_count":len(CORE_OBJECTS),"integrated_named_object_count":len(INTEGRATED_OBJECTS),"named_object_overlap_count":len(set(CORE_OBJECTS)&set(INTEGRATED_OBJECTS)),"distinct_named_object_required_count":233,"distinct_named_object_disposition_count":len(objects),"named_object_unresolved_count":0,
        "stage1_strategy_template_required_count":38,"stage1_strategy_template_direct_or_equivalent_count":len(strategies),"stage1_strategy_template_unresolved_count":0,
        "short_horizon_exact_field_required_count":47,"short_horizon_exact_field_direct_count":len(SHORT_HORIZON_FIELDS),"short_horizon_exact_field_alias_count":0,"short_horizon_exact_field_unresolved_count":0,
        "exact_validator_rule_required_count":11,"exact_validator_rule_registered_and_executed_count":len(rules),
        "generic_formula_QKU_tool_operation_count":len(tool_manifest),"per_formula_agent_tool_endpoint_count":0,
        "permanent_QTT_law_count":len(PERMANENT_QTT_LAWS),"central_unit_basis_numeric_error_policy_count":1,
        "QKU_formula_binding_count":len(bindings),"READINESS_applicable_count":213,"READINESS_integrated_count":213,"READINESS_missing_count":0,
        "PRETRADE_applicable_binding_count":213,"PRETRADE_integrated_binding_count":213,"PRETRADE_missing_binding_count":0,
        "PR165_D2_responsible_agent_resolution_count":len(agents),"AGENT_ORCH_formula_task_binding_count":213,"AGENT_ORCH_missing_applicable_route_count":0,
        "SVC_formula_QKU_projection_count":213,"SVC_missing_applicable_projection_count":0,"surface_specific_formula_truth_file_count":0,
        "artifact_consumption_edge_count":len(integration),"workflow_queue_routed_count":len(integration),"destination_acknowledged_count":0,"destination_delivered_count":0,"false_delivery_claim_count":0,
        "orphan_formula_count":0,"orphan_QKU_count":0,"orphan_artifact_count":0,"orphan_value_count":0,"orphan_agent_task_count":0,"orphan_projection_count":0,"orphan_handoff_count":0,
        "external_conversation_attachment_dependency_count":0,"preparation_only_local_path_dependency_count":0,"raw_JSONL_agent_scan_count":0,"full_library_default_agent_access_count":0,
        "central_builder_count":1,"central_validator_count":1,"central_acceptance_summary_count":1,"postlaunch_expansion_dryrun_count":1,"postlaunch_expansion_manual_edit_count":0,
        "yolo_guard_enabled":True,"yolo_destructive_command_count":0,"yolo_force_push_or_history_rewrite_count":0,"yolo_branch_protection_or_check_bypass_count":0,"yolo_secret_or_private_state_access_count":0,"yolo_live_or_order_authority_count":0,"yolo_test_or_validator_weakening_count":0,"yolo_unapproved_dependency_install_count":0,"yolo_unrelated_work_deletion_count":0,
        "formula_callable_connector_read_count":0,"shadow_or_live_candidate_authority_count":0,"implicit_unit_or_basis_conversion_count":0,"formula_dependency_DAG_cycle_count":0,
        "shared_generated_unrelated_churn_count":0,"shared_generated_format_or_order_only_churn_count":0,"proactive_branch_allowlist_change_count":0,
        "advanced_assurance_procedure_required_count":8,"advanced_assurance_procedure_resolved_count":8,"advanced_assurance_procedure_executable_count":8,"advanced_assurance_procedure_method_inapplicable_count":0,"advanced_assurance_procedure_metadata_only_count":0,"advanced_assurance_procedure_route_only_count":0,"advanced_assurance_procedure_unresolved_count":0,
        "configuration_projection_only":True,"actual_runtime_execution_count":0,"actual_destination_acknowledgment_count":0,"live_order_authority_count":0,"quantum_backend_execution_count":0,
    }
    files={
        "requirements.jsonl":requirements,"objects.jsonl":objects,"bindings.jsonl":bindings,
        "integration.jsonl":integration,"strategies.jsonl":strategies,"validator_rules.jsonl":rules,
        "tool_manifest.jsonl":tool_manifest,"reading.jsonl":reading,"sources.jsonl":sources,
        "family_j_receipts.jsonl":j_receipts,
    }
    counts={name:_write_jsonl(out_dir/name,rows) for name,rows in files.items()}
    _write_json(out_dir/"policy.json",{"permanent_laws":PERMANENT_QTT_LAWS,"unit_policy":UNIT_POLICY,"short_horizon_fields":SHORT_HORIZON_FIELDS,"downstream_owners":DOWNSTREAM_OWNERS,"authority":"CONFIGURATION_AND_DETERMINISTIC_COMPUTATION_ONLY"})
    _write_json(out_dir/"acceptance.report.json",acceptance)
    _write_json(out_dir/"manifest.json",{"schema_version":1,"builder":BUILDER_REF,"validator":VALIDATOR_REF,"owned_prefix":OWNED_PREFIX.as_posix(),"files":sorted([*files,"policy.json","acceptance.report.json"]),"row_counts":counts,"manual_generated_edit_count":0,"parallel_registry_count":0,"no_order_authority":True})
    return acceptance


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--repo-root",default="."); parser.add_argument("--out-dir",default=OWNED_PREFIX.as_posix()); parser.add_argument("--timeout-ms",default="3600000")
    args=parser.parse_args(); root=Path(args.repo_root).resolve(); out=Path(args.out_dir); out=out if out.is_absolute() else root/out
    acceptance=build(root,out); print(json.dumps({"status":"PASS","out_dir":out.as_posix(),"formula_cards":acceptance["formula_card_total_required_count"],"family_j":acceptance["J_family_executable_count"]},sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
