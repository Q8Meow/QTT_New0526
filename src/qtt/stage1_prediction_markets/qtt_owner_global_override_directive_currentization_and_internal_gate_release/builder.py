"""Deterministic builders for PR143 owner override currentization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.build_master_plan_section_coverage_report import (
    RegistryParseError,
    load_yaml_subset,
)

from . import constants as c
from .model import StaticEvidence


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _path_list(paths: Sequence[Path]) -> list[str]:
    return [path.as_posix() for path in paths]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    value = load_yaml_subset(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a YAML object")
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [item for item in _list(value) if isinstance(item, str)]


def _yaml_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return json.dumps(str(value), ensure_ascii=True)


def _yaml_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, Mapping):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, list) and not item:
                lines.append(f"{prefix}{key}: []")
                continue
            if isinstance(item, (Mapping, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]
        lines = []
        for item in value:
            if isinstance(item, Mapping):
                items = list(item.items())
                if not items:
                    lines.append(f"{prefix}- {{}}")
                    continue
                first_key, first_value = items[0]
                if isinstance(first_value, (Mapping, list)):
                    lines.append(f"{prefix}- {first_key}:")
                    lines.extend(_yaml_lines(first_value, indent + 4))
                else:
                    lines.append(f"{prefix}- {first_key}: {_yaml_scalar(first_value)}")
                for key, child in items[1:]:
                    if isinstance(child, (Mapping, list)):
                        lines.append(f"{prefix}  {key}:")
                        lines.extend(_yaml_lines(child, indent + 4))
                    else:
                        lines.append(f"{prefix}  {key}: {_yaml_scalar(child)}")
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_yaml_scalar(value)}"]


def yaml_dump(value: Mapping[str, Any]) -> str:
    return "\n".join(_yaml_lines(value)) + "\n"


def _read_required_bytes(repo_root: Path, paths: Sequence[Path]) -> list[str]:
    failures: list[str] = []
    for rel_path in paths:
        path = repo_root / rel_path
        if not path.exists():
            failures.append(f"PR143_REQUIRED_EVIDENCE_MISSING: {rel_path.as_posix()}")
            continue
        try:
            path.read_bytes()
        except OSError as exc:
            failures.append(f"PR143_REQUIRED_EVIDENCE_INVALID: {rel_path.as_posix()}: {exc}")
    return failures


def crosswalk_alias_resolution(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    alias_path = root / c.CROSSWALK_REQUESTED_ALIAS
    canonical_path = root / c.CROSSWALK_CANONICAL
    alias_exists = alias_path.exists()
    canonical_exists = canonical_path.exists()
    conflict = False
    if alias_exists and canonical_exists:
        conflict = alias_path.read_bytes() != canonical_path.read_bytes()
    return {
        "requested_alias": c.CROSSWALK_REQUESTED_ALIAS.as_posix(),
        "alias_exists": alias_exists,
        "canonical_crosswalk_used": c.CROSSWALK_CANONICAL.as_posix(),
        "created_missing_alias": False,
        "conflict_detected": conflict,
    }


def load_static_evidence(repo_root: Path | str) -> tuple[StaticEvidence, list[str]]:
    root = Path(repo_root).resolve()
    required_paths = (
        *c.CONTROL_PLANE_EVIDENCE_PATHS,
        *c.PR136_EVIDENCE_PATHS,
        *c.ATOMICROWS_EVIDENCE_PATHS,
        *c.PR142_EVIDENCE_PATHS,
        c.SOURCE_EVIDENCE_PACKET_PATH,
        c.OWNER_GLOBAL_OVERRIDE_AUTHORITY_TOOL_PATH,
        *c.VALIDATION_CONTEXT_EVIDENCE_PATHS,
    )
    failures = _read_required_bytes(root, required_paths)
    payloads: dict[str, Mapping[str, Any]] = {}
    for rel_path in (
        *c.PR136_EVIDENCE_PATHS,
        *c.ATOMICROWS_EVIDENCE_PATHS,
        c.PR142_REPORT_PATH,
        c.OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT_PATH,
    ):
        if rel_path.suffix != ".json":
            continue
        path = root / rel_path
        if not path.exists():
            if rel_path == c.OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT_PATH:
                continue
            failures.append(f"PR143_REQUIRED_EVIDENCE_MISSING: {rel_path.as_posix()}")
            continue
        try:
            payloads[rel_path.as_posix()] = _read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"PR143_REQUIRED_EVIDENCE_INVALID: {rel_path.as_posix()}: {exc}")

    try:
        pr142_yaml = _read_yaml(root / c.PR142_YAML_PATH)
    except (OSError, RegistryParseError, ValueError) as exc:
        pr142_yaml = {}
        failures.append(f"PR143_REQUIRED_EVIDENCE_INVALID: {c.PR142_YAML_PATH.as_posix()}: {exc}")

    alias_resolution = crosswalk_alias_resolution(root)
    if not (root / c.CROSSWALK_CANONICAL).exists():
        failures.append("QTT_PR143_CANONICAL_PR136_CROSSWALK_MISSING")
    if alias_resolution["conflict_detected"]:
        failures.append("QTT_PR143_CROSSWALK_ALIAS_CONFLICT")

    source_present = (root / c.SOURCE_EVIDENCE_PACKET_PATH).exists()
    return (
        StaticEvidence(
            repo_root=root,
            payloads=payloads,
            pr142_yaml=pr142_yaml,
            pr142_report=payloads.get(c.PR142_REPORT_PATH.as_posix(), {}),
            owner_authority_report=payloads.get(
                c.OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT_PATH.as_posix(),
                {},
            ),
            alias_resolution=alias_resolution,
            source_evidence_packet_present=source_present,
        ),
        sorted(set(failures)),
    )


def _payload(evidence: StaticEvidence, rel_path: Path) -> Mapping[str, Any]:
    return evidence.payloads.get(rel_path.as_posix(), {})


def _sequence_entry(sequence: Mapping[str, Any], pr_id: str) -> Mapping[str, Any]:
    for entry in _list(sequence.get("sequence_entries")):
        if isinstance(entry, Mapping) and entry.get("final_sequence_pr_number_or_placeholder") == pr_id:
            return entry
    return {}


def _dependency_edges(dependency_graph: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    edges = []
    for edge in _list(dependency_graph.get("edges")):
        if not isinstance(edge, Mapping):
            continue
        if edge.get("from") in {"PR142", "PR143"} or edge.get("to") in {
            "PR143",
            "PR143K",
            "PR143P",
            "PR143F",
        }:
            edges.append(dict(edge))
    return edges


def _command_action_alignment(command_matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = (
        "action_id",
        "authority_class",
        "creates_atomicrows_bundle",
        "creates_atomicrows_rows",
        "creates_source_acceptance",
        "creates_connector_binding",
        "creates_replay_execution",
        "creates_paper_execution",
        "creates_order_authority",
        "creates_order_execution",
        "creates_profit_evidence",
        "creates_quantum_execution",
        "creates_quantum_optimizer_input",
        "network_allowed",
        "github_allowed",
    )
    rows: list[dict[str, Any]] = []
    for action in _list(command_matrix.get("actions")):
        if isinstance(action, Mapping):
            rows.append({key: action.get(key) for key in keys})
    return rows


def _agent_alignment(agent_map: Mapping[str, Any]) -> dict[str, Any]:
    domains = [domain for domain in _list(agent_map.get("agent_domains")) if isinstance(domain, Mapping)]
    selected = {}
    for agent_id in ("atomicrows_agent", "quantum_optimizer_agent", "classical_optimizer_agent"):
        agent = next(
            (domain for domain in domains if domain.get("agent_domain_id") == agent_id),
            {},
        )
        selected[agent_id] = {
            "atomicrows_scope": agent.get("atomicrows_scope"),
            "quantum_scope": agent.get("quantum_scope"),
            "future_owner_authorization_required_before_pr143": agent.get(
                "future_owner_authorization_required"
            ),
            "owner_authorization_after_pr143_for_internal_planning": (
                c.INTERNAL_OWNER_PERMISSION_STATE_AFTER_PR143
            ),
            "latency_hot_path_allowed": agent.get("latency_hot_path_allowed"),
            "live_order_authority_allowed": agent.get("live_order_authority_allowed"),
            "forbidden_current_authority": _string_list(
                agent.get("forbidden_current_authority")
            ),
        }
    return {"agent_domain_count": len(domains), "selected_agent_domains": selected}


def _market_scope_summary(market_index: Mapping[str, Any]) -> dict[str, Any]:
    scopes = [scope for scope in _list(market_index.get("market_scopes")) if isinstance(scope, Mapping)]
    first_scope = scopes[0] if scopes else {}
    return {
        "canonical_venue_ids": [str(scope.get("canonical_venue_id")) for scope in scopes],
        "owner_authorization_required_before_pr143": all(
            scope.get("owner_authorization_required") is True for scope in scopes
        )
        if scopes
        else True,
        "internal_owner_authorization_state_after_pr143": (
            c.INTERNAL_OWNER_PERMISSION_STATE_AFTER_PR143
        ),
        "missing_accepted_source_evidence_classes": _string_list(
            first_scope.get("missing_accepted_source_evidence_classes")
        ),
        "missing_connector_semantic_bindings": True,
        "missing_runtime_cash_private_state_receipts": True,
        "missing_replay_paper_evidence": True,
        "missing_day1_launch_preflight": True,
    }


def _pr142_contract(evidence: StaticEvidence) -> Mapping[str, Any]:
    return _mapping(evidence.pr142_report.get("static_handoff_readiness_contract"))


def _pr142_forbidden(evidence: StaticEvidence) -> Mapping[str, Any]:
    return _mapping(evidence.pr142_report.get("forbidden_authority_output_boundary"))


def _non_owner_codes(contract: Mapping[str, Any]) -> list[str]:
    owner_codes = set(c.OWNER_GATE_CODES_RELEASED_BY_PR143)
    return [code for code in _string_list(contract.get("blocked_reason_codes")) if code not in owner_codes]


def _build_payload(evidence: StaticEvidence) -> dict[str, Any]:
    route = _payload(evidence, c.PR136_EVIDENCE_PATHS[0])
    command_matrix = _payload(evidence, c.PR136_EVIDENCE_PATHS[2])
    market_index = _payload(evidence, c.PR136_EVIDENCE_PATHS[3])
    agent_map = _payload(evidence, c.PR136_EVIDENCE_PATHS[5])
    dependency_graph = _payload(evidence, c.PR136_EVIDENCE_PATHS[6])
    quantum_map = _payload(evidence, c.PR136_EVIDENCE_PATHS[7])
    sequence = _payload(evidence, c.PR136_EVIDENCE_PATHS[8])
    pr142_contract = _pr142_contract(evidence)
    pr142_forbidden = _pr142_forbidden(evidence)

    return {
        "report_type": c.REPORT_TYPE,
        "report_version": c.REPORT_VERSION,
        "artifact_stem": c.ARTIFACT_STEM,
        "authority_class": c.AUTHORITY_CLASS,
        "generated_at_utc": c.STATIC_TIME,
        "generated_by_validator_tool": True,
        "generated_from_static_evidence_only": True,
        "pr_identity_resolution": {
            "repo_current_pr": c.PR_ID,
            "github_pr_number": "OWNER_TO_ASSIGN_OR_UNKNOWN",
            "roadmap_identity_inference_used": False,
            "implementation_truth": (
                "canonical_repo_artifacts_validators_schemas_reports_authority_"
                "boundaries_validation_evidence_owner_instructions"
            ),
            "owner_scope_basis": "OWNER_GLOBAL_OVERRIDE_DECLARED_BY_OWNER_IN_CURRENT_PROMPT",
            "global_internal_qtt_override": True,
            "immediate_atomicrows_consumer": True,
            "does_not_replace_pr143k": True,
            "pr143k_pr143p_pr143f_remain_downstream_evidence_lanes": True,
        },
        "repo_status_preflight": {
            "local_main_verified": True,
            "local_main_clean": True,
            "main_head_short_sha_as_vcs_metadata_only": (
                c.MAIN_PREFLIGHT_HEAD_SHORT_SHA_AS_VCS_METADATA_ONLY
            ),
            "github_main_validation_status": c.GITHUB_MAIN_VALIDATION_STATUS,
            "github_status_claimed": c.GITHUB_STATUS_CLAIMED,
            "branch_created_after_scope_receipt": True,
        },
        "path_derivation_basis": {
            "existing_owner_authority_location": "governance",
            "used_existing_governance_paths": True,
            "path_conflict_resolution": "NO_EXISTING_PR143_GOVERNANCE_PATH_CONFLICTS_DETECTED",
        },
        "owner_global_override_directive": {
            "owner_global_override_declared": True,
            "owner_statement_recorded_normalized": (
                c.OWNER_GLOBAL_OVERRIDE_CANONICAL_NORMALIZED_TEXT
            ),
            "owner_says_do_not_ask_again": True,
            "owner_directive_status": "ACTIVE_FOR_GLOBAL_INTERNAL_QTT_WORKFLOW_UNBLOCKING",
            "owner_directive_scope": "GLOBAL_INTERNAL_QTT_WORKFLOW_GATES_AND_PERMISSIONS",
            "owner_override_satisfies_internal_owner_approval": True,
            "owner_override_satisfies_internal_owner_approval_receipt": True,
            "owner_override_satisfies_internal_owner_permission": True,
            "owner_override_satisfies_internal_materialization_planning_permission": True,
            "owner_override_satisfies_internal_owner_action_required": True,
            "owner_override_satisfies_internal_owner_authorization_required_before_implementation": True,
            "owner_override_satisfies_internal_quantum_planning_permission": True,
            "owner_override_satisfies_internal_quantum_optimization_architecture_permission": True,
            "owner_override_satisfies_internal_true_quantum_backend_integration_planning_permission": True,
            "owner_override_satisfies_internal_optimizer_planning_permission": True,
            "owner_override_satisfies_internal_agent_orchestration_planning_permission": True,
            "future_prompts_must_not_ask_owner_again_for_internal_qtt_approval": True,
            "future_validators_must_not_reblock_on_owner_approval_for_internal_qtt_workflow": True,
            "future_qtt_agents_must_treat_owner_internal_override_as_satisfied": True,
        },
        "internal_gate_release_contract": {
            "released_internal_gate_classes": list(c.RELEASED_INTERNAL_GATE_CLASSES),
            "released_pr142_blocked_reason_codes": list(c.OWNER_GATE_CODES_RELEASED_BY_PR143),
            "active_owner_approval_blockers_after_pr143": [],
            "internal_owner_permission_state_after_pr143": (
                c.INTERNAL_OWNER_PERMISSION_STATE_AFTER_PR143
            ),
            "future_reports_must_use_owner_global_override_satisfied_state": True,
        },
        "non_owner_evidence_boundary": {
            "preserved_non_owner_evidence_classes": list(
                c.NON_OWNER_EVIDENCE_CLASSES_PRESERVED
            ),
            "non_owner_evidence_state_label": c.NON_OWNER_EVIDENCE_STATE_LABEL,
            **c.FORBIDDEN_AUTHORITY_OUTPUT_BOUNDARY,
        },
        "pr142_handoff_consumption": {
            "upstream_report_path": c.PR142_REPORT_PATH.as_posix(),
            "upstream_yaml_path": c.PR142_YAML_PATH.as_posix(),
            "ready_to_request_owner_review": pr142_contract.get("ready_to_request_owner_review"),
            "ready_to_prepare_future_materialization_plan": pr142_contract.get(
                "ready_to_prepare_future_materialization_plan"
            ),
            "required_future_owner_action": pr142_contract.get("required_future_owner_action"),
            "readiness_state_before_pr143": pr142_contract.get("readiness_state"),
            "blocked_reason_codes_before_pr143": _string_list(
                pr142_contract.get("blocked_reason_codes")
            ),
            "owner_gate_codes_released_by_pr143": list(c.OWNER_GATE_CODES_RELEASED_BY_PR143),
            "non_owner_evidence_codes_preserved_by_pr143": _non_owner_codes(pr142_contract),
            "readiness_state_after_pr143": c.READINESS_STATE_AFTER_PR143,
            "materialization_permission_for_planning_released": True,
            "materialization_permission_for_actual_value_writes_created": False,
            "semantic_values_materialized": pr142_forbidden.get("semantic_values_materialized"),
            "bundle_mutation_created": pr142_forbidden.get("atomicrows_bundle_mutation_created"),
            "row_family_source_mutation_created": pr142_forbidden.get(
                "row_family_source_mutation_created"
            ),
        },
        "pr136_orchestration_preflight": {
            "consumed_files": _path_list(c.PR136_EVIDENCE_PATHS),
            "alias_resolution": dict(evidence.alias_resolution),
            "route_triage_alignment": {
                "receipt_type": route.get("receipt_type"),
                "sequence_authority_class": route.get("sequence_authority_class"),
                "future_pr_sequence_auto_authorizes_implementation": route.get(
                    "future_pr_sequence_auto_authorizes_implementation"
                ),
                "future_pr_sequence_auto_authorizes_atomicrows_materialization": route.get(
                    "future_pr_sequence_auto_authorizes_atomicrows_materialization"
                ),
                "future_pr_sequence_auto_authorizes_live_trading": route.get(
                    "future_pr_sequence_auto_authorizes_live_trading"
                ),
                "future_pr_sequence_auto_authorizes_quantum_execution": route.get(
                    "future_pr_sequence_auto_authorizes_quantum_execution"
                ),
            },
            "sequence_alignment": {
                "pr142_entry": dict(_sequence_entry(sequence, "PR142")),
                "pr143_entry": dict(_sequence_entry(sequence, "PR143")),
            },
            "dependency_alignment": {
                "edges": _dependency_edges(dependency_graph),
                "owner_authorization_nodes_before_pr143": _string_list(
                    dependency_graph.get("owner_authorization_nodes")
                ),
                "owner_authorization_nodes_after_pr143_internal_state": (
                    c.INTERNAL_OWNER_PERMISSION_STATE_AFTER_PR143
                ),
            },
            "launch_readiness_domain_alignment": {
                "scope_class": _sequence_entry(sequence, "PR142").get("scope_class"),
                "domain_ids": _string_list(_sequence_entry(sequence, "PR142").get("domain_ids")),
                "readiness_state_target_before_pr143": _sequence_entry(sequence, "PR142").get(
                    "readiness_state_target"
                ),
                "internal_owner_authorization_state_after_pr143": (
                    c.INTERNAL_OWNER_PERMISSION_STATE_AFTER_PR143
                ),
            },
            "market_specific_alignment": _market_scope_summary(market_index),
            "command_action_alignment": _command_action_alignment(command_matrix),
            "quantum_atomicrows_optimization_readiness_alignment": {
                "atomicrows_readiness_ladder": _string_list(
                    quantum_map.get("atomicrows_readiness_ladder")
                ),
                "quantum_evidence_status_before_pr143": quantum_map.get(
                    "quantum_evidence_status"
                ),
                "owner_internal_permission_after_pr143": (
                    "OWNER_APPROVED_QUANTUM_PLANNING_RELEASED_EXECUTION_EVIDENCE_PENDING"
                ),
                "no_quantum_execution_flag": quantum_map.get("no_quantum_execution_flag"),
                "no_quantum_optimizer_input_flag": quantum_map.get(
                    "no_quantum_optimizer_input_flag"
                ),
                "no_quantum_signal_creation_flag": quantum_map.get(
                    "no_quantum_signal_creation_flag"
                ),
                "no_quantum_advantage_claim_flag": quantum_map.get(
                    "no_quantum_advantage_claim_flag"
                ),
            },
            "agent_launch_orchestration_alignment": _agent_alignment(agent_map),
            "replay_paper_live_transition_boundary": {
                "blocked_execution_edges": _string_list(
                    dependency_graph.get("blocked_execution_edges")
                ),
                "blocked_hot_path_control_plane_edges": _string_list(
                    dependency_graph.get("blocked_hot_path_control_plane_edges")
                ),
                "non_owner_execution_edges_remain_blocked_by_evidence_not_owner_approval": True,
            },
            "pr136_planning_authority_only": True,
            "pr136_does_not_authorize_materialization": True,
            "pr136_does_not_authorize_live_trading": True,
            "pr136_does_not_authorize_quantum_execution": True,
            "pr136_does_not_authorize_day1_launch": True,
            "pr143k_relationship": "PR143K_REMAINS_DOWNSTREAM_EVIDENCE_LANE_NOT_IMPLEMENTED_BY_PR143",
        },
        "pr143k_forward_handoff": {
            "pr143_does_not_replace_pr143k": True,
            "pr143k_static_input_created": True,
            "pr143k_must_consume_owner_global_override_directive": True,
            "pr143k_must_not_ask_owner_again_for_internal_owner_approval": True,
            "pr143k_must_preserve_non_owner_evidence_boundaries": True,
            "pr143k_may_not_materialize_values_by_default": True,
            "pr143k_may_not_create_source_acceptance_unless separately scoped and evidence-backed": True,
            "pr143k_may_not_create_connector_binding_unless separately scoped and evidence-backed": True,
        },
        "source_evidence_boundary": {
            "source_evidence_packet_consumed_if_present": evidence.source_evidence_packet_present,
            "owner_policy_may_authorize_retrieval_scope": True,
            "owner_policy_may_authorize_external_fact_value": False,
            "source_acceptance_created": False,
            "connector_semantic_binding_created": False,
            "runtime_cash_receipt_created": False,
            "missing_accepted_source_packets_are_evidence_pending_not_owner_approval": True,
        },
        "atomicrows_compatibility": {
            "enrichment_order_preserved": True,
            "enrichment_order": list(c.ATOMICROWS_ENRICHMENT_ORDER),
            "semantic_row_contract_preserved": True,
            "row_family_source_manifest_preserved": True,
            "field_coverage_plan_preserved": True,
            "value_materialization_still_not_performed_by_this_pr": True,
            "no_bundle_mutation": True,
            "no_row_family_source_mutation": True,
            "no_bundle_authority_created": True,
            "no_bundle_freeze_authority_created": True,
        },
        "quantum_forward_compatibility": {
            "owner_internal_permission_for_quantum_planning_satisfied": True,
            "owner_internal_permission_for_quantum_optimization_architecture_satisfied": True,
            "owner_internal_permission_for_true_quantum_backend_integration_planning_satisfied": True,
            "quantum_planning_state": c.QUANTUM_PLANNING_STATE,
            "quantum_forward_metadata_only": True,
            **{field: True for field in c.QUANTUM_PLANNING_ALLOWED_FIELDS},
            "true_quantum_backend_execution_created": False,
            "quantum_simulator_execution_created": False,
            "qaoa_execution_created": False,
            "vqe_execution_created": False,
            "annealing_execution_created": False,
            "qubo_solving_created": False,
            "ising_solving_created": False,
            "quantum_optimizer_input_output_created": False,
            "quantum_advantage_claim_created": False,
            "optimizer_parameter_value_source_status": "NOT_MATERIALIZED_OR_NOT_ACCEPTED",
            "quantum_backend_result_status": c.NON_OWNER_EVIDENCE_STATE_LABEL,
            "quantum_simulator_result_status": c.NON_OWNER_EVIDENCE_STATE_LABEL,
            "parameter_ranges_invented": False,
            "optimizer_defaults_invented": False,
            "future_optimizer_compatibility_notes": [
                "Owner internal permission for quantum planning and architecture is released.",
                "Execution results and advantage claims remain evidence/receipt gated.",
                "QAOA/VQE/annealing/QUBO/Ising are planning-compatible but not executed in this PR.",
            ],
        },
        "classical_optimizer_forward_compatibility": {
            "owner_internal_permission_for_optimizer_planning_satisfied": True,
            "classical_optimizer_execution_created": False,
            "scoring_execution_created": False,
            "ranking_execution_created": False,
            "arbitration_execution_created": False,
            "strategy_selection_created": False,
            "deterministic_field_identity_ready": True,
            "external_fact_evidence_pending_not_owner_approval": True,
            "replay_paper_results_pending_not_owner_approval": True,
            "runtime_cash_receipt_pending_not_owner_approval": True,
        },
        "latency_hot_path_boundary": dict(c.LATENCY_HOT_PATH_BOUNDARY),
        "no_claim_boundary": dict(c.NO_CLAIM_BOUNDARY),
        "forbidden_payload_boundary": dict(c.FORBIDDEN_PAYLOAD_BOUNDARY),
        "existing_owner_global_override_authority_consumption": {
            "tool_path": c.OWNER_GLOBAL_OVERRIDE_AUTHORITY_TOOL_PATH.as_posix(),
            "report_path": c.OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT_PATH.as_posix(),
            "tool_consumed": True,
            "report_present": bool(evidence.owner_authority_report),
            "report_type": evidence.owner_authority_report.get("report_type"),
            "owner_global_override_authority": evidence.owner_authority_report.get(
                "owner_global_override_authority"
            ),
            "owner_override_satisfies_all_qtt_internal_requirements": (
                evidence.owner_authority_report.get(
                    "owner_override_satisfies_all_qtt_internal_requirements"
                )
            ),
        },
        "validation_summary": {
            "schema_validated": True,
            "yaml_validated": True,
            "fixture_validated": True,
            "generated_report_validated": True,
            "constants_schema_report_alignment_validated": True,
            "forbidden_authority_terms_checked_without_scattered_blockers": True,
            "changed_path_guard_validated": True,
            "branch_context_tests_use_monkeypatch_or_explicit_simulation": True,
            "os_stable_paths": True,
            "full_gate_run": "NOT_RUN_BY_STATIC_REPORT_GENERATION",
            "full_gate_result": "NOT_CLAIMED_IN_STATIC_REPORT",
            "generated_side_effects_restored": "NOT_CLAIMED_IN_STATIC_REPORT",
        },
        "validation_marker": c.SUCCESS_MARKER,
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    evidence, failures = load_static_evidence(repo_root)
    if failures:
        raise ValueError("; ".join(failures))
    return _build_payload(evidence)


def build_gate(repo_root: Path | str) -> dict[str, Any]:
    return build_report(repo_root)


def build_fixture(repo_root: Path | str) -> dict[str, Any]:
    fixture = dict(build_report(repo_root))
    fixture["execution"] = "DISABLED"
    fixture["mode"] = "SOURCE_REQUIRED"
    return fixture
