"""Deterministic PR141 AtomicRows semantic materialization owner gate."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools.build_master_plan_section_coverage_report import (
    RegistryParseError,
    load_yaml_subset,
)
from tools.ci_branch_context import (
    current_branch_context,
    is_downstream_roadmap_branch,
)
from tools.validate_master_plan_section_coverage import validate_json_schema_subset

from . import constants as c


FIXTURE_METADATA = {
    "execution": "DISABLED",
    "mode": "SOURCE_REQUIRED",
}


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


def _walk(value: Any, path: str = "$"):
    if isinstance(value, Mapping):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, str(key), item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


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
            if isinstance(item, (Mapping, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
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


def _load_required_json_evidence(repo_root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for rel_path in (
        *c.PR136_EVIDENCE_PATHS,
        *c.PR137L_EVIDENCE_PATHS,
        *c.PR137R_EVIDENCE_PATHS,
        *c.PR138_EVIDENCE_PATHS,
        c.PR139_REPORT_PATH,
        c.PR140_REPORT_PATH,
    ):
        path = repo_root / rel_path
        key = rel_path.as_posix()
        if not path.exists():
            failures.append(f"PR141_REQUIRED_EVIDENCE_MISSING: {key}")
            continue
        try:
            payloads[key] = _read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"PR141_REQUIRED_EVIDENCE_INVALID: {key}: {exc}")
    return payloads, failures


def _field_group_records(inventory: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [group for group in _list(inventory.get("field_groups")) if isinstance(group, Mapping)]


def _field_records(inventory: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [field for field in _list(inventory.get("fields")) if isinstance(field, Mapping)]


def _field_ids(inventory: Mapping[str, Any]) -> list[str]:
    return [str(field.get("field_id")) for field in _field_records(inventory)]


def _group_ids(inventory: Mapping[str, Any]) -> list[str]:
    return [str(group.get("field_group_id")) for group in _field_group_records(inventory)]


def _fields_by_group(inventory: Mapping[str, Any]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {group_id: [] for group_id in _group_ids(inventory)}
    for field in _field_records(inventory):
        grouped.setdefault(str(field.get("field_group_id")), []).append(str(field.get("field_id")))
    return grouped


def _field_group_by_field(inventory: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(field.get("field_id")): str(field.get("field_group_id"))
        for field in _field_records(inventory)
    }


def _source_entries(pr139_manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    source_manifest = _mapping(pr139_manifest.get("row_family_source_manifest"))
    return [
        entry
        for entry in _list(source_manifest.get("row_family_entries"))
        if isinstance(entry, Mapping)
    ]


def _source_paths(pr139_manifest: Mapping[str, Any]) -> list[str]:
    return [str(entry.get("source_file_path")) for entry in _source_entries(pr139_manifest)]


def _supported_fields_from_pr137r(pr137r: Mapping[str, Any]) -> list[str]:
    state = _mapping(pr137r.get("atomicrows_validation_state"))
    audit = _mapping(state.get("row_contract_field_audit"))
    return _string_list(audit.get("supported_fields"))


def _pr140_field_coverage(pr140_plan: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        field
        for field in _list(pr140_plan.get("field_coverage"))
        if isinstance(field, Mapping)
    ]


def _pr140_field_by_id(pr140_plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(field.get("field_id")): field for field in _pr140_field_coverage(pr140_plan)}


def _first_ref(payload: Mapping[str, Any], key: str, fallback: str) -> str:
    values = _string_list(payload.get(key))
    return values[0] if values else fallback


def _crosswalk_alias_resolution(repo_root: Path) -> dict[str, Any]:
    alias_exists = (repo_root / c.CROSSWALK_REQUESTED_ALIAS).exists()
    return {
        "requested_alias": c.CROSSWALK_REQUESTED_ALIAS.as_posix(),
        "alias_exists": alias_exists,
        "canonical_crosswalk_used": c.CROSSWALK_CANONICAL.as_posix(),
        "created_missing_alias": False,
    }


def _build_context(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    payloads, failures = _load_required_json_evidence(repo_root)
    pr139_manifest: dict[str, Any] = {}
    pr140_plan: dict[str, Any] = {}
    try:
        pr139_manifest = _read_yaml(repo_root / c.PR139_MANIFEST_PATH)
    except (OSError, RegistryParseError, ValueError) as exc:
        failures.append(f"PR141_REQUIRED_EVIDENCE_INVALID: {c.PR139_MANIFEST_PATH.as_posix()}: {exc}")
    try:
        pr140_plan = _read_yaml(repo_root / c.PR140_PLAN_PATH)
    except (OSError, RegistryParseError, ValueError) as exc:
        failures.append(f"PR141_REQUIRED_EVIDENCE_INVALID: {c.PR140_PLAN_PATH.as_posix()}: {exc}")
    return {
        "agent_map": payloads.get(c.PR136_EVIDENCE_PATHS[5].as_posix(), {}),
        "dependency_graph": payloads.get(c.PR136_EVIDENCE_PATHS[6].as_posix(), {}),
        "future_cards": payloads.get(c.PR136_EVIDENCE_PATHS[9].as_posix(), {}),
        "market_index": payloads.get(c.PR136_EVIDENCE_PATHS[3].as_posix(), {}),
        "pr137r": payloads.get(c.PR137R_REPORT_PATH.as_posix(), {}),
        "pr137l": payloads.get(c.PR137L_REPORT_PATH.as_posix(), {}),
        "pr138_inventory": payloads.get(c.PR138_INVENTORY_PATH.as_posix(), {}),
        "pr138_report": payloads.get(c.PR138_REPORT_PATH.as_posix(), {}),
        "pr139_manifest": pr139_manifest,
        "pr139_report": payloads.get(c.PR139_REPORT_PATH.as_posix(), {}),
        "pr140_plan": pr140_plan,
        "pr140_report": payloads.get(c.PR140_REPORT_PATH.as_posix(), {}),
        "quantum_map": payloads.get(c.PR136_EVIDENCE_PATHS[7].as_posix(), {}),
        "sequence": payloads.get(c.PR136_EVIDENCE_PATHS[8].as_posix(), {}),
        "payloads": payloads,
    }, failures


def _classification_for_pr140_field(field: Mapping[str, Any]) -> tuple[str, str, str, str]:
    field_id = str(field.get("field_id"))
    dependency_class = str(field.get("dependency_class"))
    readiness, eligibility, downstream, reason = c.FIELD_STATE_BY_PR140_DEPENDENCY_CLASS[
        dependency_class
    ]
    if field_id == "quantum_backend_execution_allowed_flag":
        return (
            "QUANTUM_METADATA_ONLY_NOT_BACKEND_AUTHORIZED",
            "BLOCKED_BY_QUANTUM_BACKEND_EXECUTION_BOUNDARY",
            "QUANTUM_METADATA_STATIC_ONLY",
            "PR141_QUANTUM_BACKEND_EXECUTION_BOUNDARY_FORCED_FALSE",
        )
    return readiness, eligibility, downstream, reason


def _field_ledger_records(
    *, inventory: Mapping[str, Any], pr140_plan: Mapping[str, Any]
) -> list[dict[str, Any]]:
    pr140_by_id = _pr140_field_by_id(pr140_plan)
    records: list[dict[str, Any]] = []
    for field in _field_records(inventory):
        field_id = str(field.get("field_id"))
        pr140_field = pr140_by_id.get(field_id, {})
        dependency_class = str(pr140_field.get("dependency_class"))
        readiness_state, eligibility_state, downstream_class, reason_code = (
            _classification_for_pr140_field(pr140_field)
        )
        is_row_id = field_id == "row_id"
        forced_false = dependency_class == "AUTHORITY_FLAG_FORCED_FALSE"
        quantum_metadata_only = (
            dependency_class == "QUANTUM_METADATA_ONLY"
            or field_id == "quantum_backend_execution_allowed_flag"
            or str(field.get("field_group_id")) == "QUANTUM_COMPATIBILITY"
        )
        source_blocked = dependency_class == "SOURCE_EVIDENCE_PACKET_REQUIRED"
        runtime_blocked = dependency_class == "FUTURE_RUNTIME_RECEIPT_REQUIRED"
        replay_blocked = dependency_class == "FUTURE_REPLAY_PAPER_EVIDENCE_REQUIRED"
        eligible_to_request = (
            eligibility_state == "ELIGIBLE_FOR_FUTURE_OWNER_AUTHORIZED_MATERIALIZATION"
        )
        records.append(
            {
                "field_id": field_id,
                "field_group_id": str(field.get("field_group_id")),
                "pr138_required_flag": True,
                "pr140_coverage_status": str(pr140_field.get("coverage_status")),
                "pr140_dependency_class": dependency_class,
                "pr140_future_pr_dependency_class": str(
                    pr140_field.get("future_pr_dependency_class")
                ),
                "owner_authorization_readiness_state": readiness_state,
                "materialization_eligibility_state": eligibility_state,
                "downstream_dependency_class": downstream_class,
                "planned_enrichment_locus": list(
                    _list(pr140_field.get("planned_enrichment_locus"))
                ),
                "planned_row_family_source_paths": list(
                    _list(pr140_field.get("planned_row_family_source_paths"))
                ),
                "eligibility_to_request_owner_authorization": eligible_to_request,
                "owner_approval_granted_by_pr141": False,
                "materialization_permitted_now": False,
                "owner_authorization_required_before_materialization": not is_row_id,
                "source_evidence_required_before_materialization": source_blocked,
                "accepted_source_packet_required_before_materialization": source_blocked,
                "runtime_receipt_required_before_materialization": runtime_blocked,
                "replay_paper_evidence_required_before_materialization": replay_blocked,
                "forced_false_no_authority_boundary": forced_false,
                "quantum_metadata_only": quantum_metadata_only,
                "quantum_backend_execution_allowed": False,
                "semantic_value_materialized_by_pr141": False,
                "bundle_mutation_allowed_by_pr141": False,
                "row_family_source_mutation_allowed_by_pr141": False,
                "source_acceptance_created_by_pr141": False,
                "connector_binding_created_by_pr141": False,
                "live_use_allowed_by_pr141": False,
                "order_authority_created_by_pr141": False,
                "profit_evidence_created_by_pr141": False,
                "final_readiness_created_by_pr141": False,
                "future_pr142_input_created": not is_row_id,
                "reason_code": reason_code,
                "rationale": c.FIELD_RATIONALE_BY_REASON_CODE[reason_code],
            }
        )
    return records


def _dominant_downstream_class(entries: Sequence[Mapping[str, Any]]) -> str:
    priority = (
        "AUTHORITY_BOUNDARY_FORCED_FALSE",
        "REPLAY_PAPER_EVIDENCE_DEPENDENT",
        "RUNTIME_RECEIPT_DEPENDENT",
        "ACCEPTED_SOURCE_PACKET_DEPENDENT",
        "OWNER_SCOPE_DECISION_DEPENDENT",
        "QUANTUM_METADATA_STATIC_ONLY",
        "PR142_CONSUMABLE_STATIC_AUTHORIZATION_INPUT",
        "STATIC_POLICY_ONLY",
        "EXISTING_ROW_ID_ONLY",
    )
    classes = {str(entry.get("downstream_dependency_class")) for entry in entries}
    for dependency_class in priority:
        if dependency_class in classes:
            return dependency_class
    return "STATIC_POLICY_ONLY"


def _field_group_summary_records(
    *, inventory: Mapping[str, Any], ledger: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    fields_by_group = _fields_by_group(inventory)
    ledger_by_group: dict[str, list[Mapping[str, Any]]] = {
        group_id: [] for group_id in fields_by_group
    }
    for entry in ledger:
        ledger_by_group.setdefault(str(entry.get("field_group_id")), []).append(entry)
    records: list[dict[str, Any]] = []
    for group in _field_group_records(inventory):
        group_id = str(group.get("field_group_id"))
        entries = ledger_by_group.get(group_id, [])
        required_field_ids = fields_by_group.get(group_id, [])
        records.append(
            {
                "field_group_id": group_id,
                "required_field_ids": required_field_ids,
                "required_field_count": len(required_field_ids),
                "field_authorization_count": len(
                    [
                        entry
                        for entry in entries
                        if entry.get("eligibility_to_request_owner_authorization") is True
                    ]
                ),
                "eligible_for_future_materialization_count": len(
                    [
                        entry
                        for entry in entries
                        if entry.get("materialization_eligibility_state")
                        == "ELIGIBLE_FOR_FUTURE_OWNER_AUTHORIZED_MATERIALIZATION"
                    ]
                ),
                "source_evidence_blocked_count": len(
                    [
                        entry
                        for entry in entries
                        if entry.get("source_evidence_required_before_materialization")
                        is True
                    ]
                ),
                "runtime_receipt_blocked_count": len(
                    [
                        entry
                        for entry in entries
                        if entry.get("runtime_receipt_required_before_materialization")
                        is True
                    ]
                ),
                "replay_paper_blocked_count": len(
                    [
                        entry
                        for entry in entries
                        if entry.get("replay_paper_evidence_required_before_materialization")
                        is True
                    ]
                ),
                "forced_false_boundary_count": len(
                    [
                        entry
                        for entry in entries
                        if entry.get("forced_false_no_authority_boundary") is True
                    ]
                ),
                "quantum_metadata_only_count": len(
                    [entry for entry in entries if entry.get("quantum_metadata_only") is True]
                ),
                "no_authority_created": True,
                "semantic_values_materialized": False,
                "group_downstream_dependency_class": _dominant_downstream_class(entries),
            }
        )
    return records


def _row_family_source_summary_records(
    *, pr139_manifest: Mapping[str, Any], ledger: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    eligible_field_ids = [
        str(entry.get("field_id"))
        for entry in ledger
        if entry.get("eligibility_to_request_owner_authorization") is True
    ]
    blocked_field_ids = [
        str(entry.get("field_id"))
        for entry in ledger
        if entry.get("field_id") != "row_id"
        and entry.get("eligibility_to_request_owner_authorization") is not True
    ]
    planned_field_ids = [str(entry.get("field_id")) for entry in ledger]
    records: list[dict[str, Any]] = []
    for source in _source_entries(pr139_manifest):
        records.append(
            {
                "row_family_source_file_path": str(source.get("source_file_path")),
                "row_family_source_id": str(source.get("family_id")),
                "planned_field_ids": planned_field_ids,
                "eligible_field_ids_for_future_materialization": eligible_field_ids,
                "blocked_field_ids": blocked_field_ids,
                "mutation_allowed_by_pr141": False,
                "semantic_values_materialized_by_pr141": False,
                "future_owner_authorization_required": True,
                "future_pr142_input_created": bool(eligible_field_ids),
            }
        )
    return records


def _market_scope_summary_records(
    *, inventory: Mapping[str, Any], market_index: Mapping[str, Any]
) -> list[dict[str, Any]]:
    fields_by_group = _fields_by_group(inventory)
    relevant_group_ids = [
        "MARKET_VENUE_SCOPE",
        "SOURCE_PROVENANCE_BOUNDARY",
        "REPLAY_PAPER_LIVE_BOUNDARY",
    ]
    relevant_fields: list[str] = []
    for group_id in relevant_group_ids:
        relevant_fields.extend(fields_by_group.get(group_id, []))
    market_rows = _list(market_index.get("market_scopes"))
    by_scope = {
        str(row.get("canonical_venue_id")): row
        for row in market_rows
        if isinstance(row, Mapping) and row.get("canonical_venue_id")
    }
    records: list[dict[str, Any]] = []
    for scope_id in c.MARKET_SCOPE_IDS:
        row = _mapping(by_scope.get(scope_id))
        dependency_class = "ACCEPTED_SOURCE_PACKET_DEPENDENT"
        if not _string_list(row.get("missing_accepted_source_evidence_classes")):
            dependency_class = "ACCEPTED_SOURCE_PACKET_DEPENDENT"
        records.append(
            {
                "scope_id": scope_id,
                "field_ids_relevant_to_scope": relevant_fields,
                "owner_authorization_required_before_materialization": True,
                "external_fact_authority_created": False,
                "connector_binding_created": False,
                "live_use_allowed_created": False,
                "future_source_packet_dependency_class": dependency_class,
                "future_pr142_input_created": True,
            }
        )
    return records


def _agent_domain_ids(agent_map: Mapping[str, Any], pr140_plan: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    for row in _list(agent_map.get("agent_domains")):
        if isinstance(row, Mapping) and row.get("agent_domain_id"):
            ids.append(str(row.get("agent_domain_id")))
    pr140_agent = _mapping(pr140_plan.get("agent_orchestration_coverage"))
    for row in _list(pr140_agent.get("agent_domains")):
        if isinstance(row, Mapping) and row.get("agent_domain_id"):
            value = str(row.get("agent_domain_id"))
            if value not in ids:
                ids.append(value)
    return ids


def _agent_orchestration_summary(
    *, agent_map: Mapping[str, Any], pr140_plan: Mapping[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "agent_domain_id": agent_domain_id,
            "may_consume_pr141_gate_as_static_metadata": True,
            "may_materialize_values_by_pr141": False,
            "final_order_submission_authority_created": False,
            "live_order_authority_allowed": False,
            "latency_hot_path_allowed": False,
            "future_owner_authorization_required": True,
            "future_pr142_consumer_scope": "STATIC_AUTHORIZATION_METADATA_ONLY",
        }
        for agent_domain_id in _agent_domain_ids(agent_map, pr140_plan)
    ]


def _quantum_forward_authorization_boundary(quantum_map: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "quantum_metadata_authorization_scope": "STATIC_METADATA_ONLY",
        "no_quantum_execution_flag": True,
        "no_quantum_signal_creation_flag": True,
        "no_quantum_optimizer_input_flag": True,
        "no_quantum_optimizer_output_flag": True,
        "no_quantum_backend_execution_flag": True,
        "no_quantum_simulator_execution_flag": True,
        "no_quantum_advantage_claim_flag": True,
        "quantum_backend_execution_allowed_flag_forced_false": True,
        "future_qaoa_depth_p_ref": _first_ref(
            quantum_map, "future_qaoa_depth_p_refs", "FUTURE_QAOA_DEPTH_P_GRID"
        ),
        "future_qaoa_qubo_constraint_ref": _first_ref(
            quantum_map,
            "future_qaoa_qubo_constraint_refs",
            "FUTURE_QAOA_QUBO_CONSTRAINT_MATRIX",
        ),
        "future_qubo_penalty_scale_ref": _first_ref(
            quantum_map, "future_qubo_penalty_scale_refs", "FUTURE_QUBO_PENALTY_SCALE_GRID"
        ),
        "future_ising_model_ref": _first_ref(
            quantum_map, "future_ising_model_refs", "FUTURE_ISING_MODEL_REF"
        ),
        "future_vqe_ansatz_ref": _first_ref(
            quantum_map, "future_vqe_ansatz_refs", "FUTURE_VQE_ANSATZ_REF"
        ),
        "future_annealing_schedule_ref": _first_ref(
            quantum_map, "future_annealing_schedule_refs", "FUTURE_ANNEALING_SCHEDULE_REF"
        ),
        "future_shot_budget_ref": _first_ref(
            quantum_map, "future_shot_budget_refs", "FUTURE_SHOT_BUDGET_REF"
        ),
        "future_seed_control_ref": _first_ref(
            quantum_map, "future_seed_control_refs", "FUTURE_SEED_CONTROL_REF"
        ),
        "future_backend_provider_class_ref": _first_ref(
            quantum_map, "future_backend_provider_class_refs", "FUTURE_BACKEND_PROVIDER_CLASS_REF"
        ),
        "future_classical_comparator_ref": _first_ref(
            quantum_map, "future_classical_comparator_refs", "FUTURE_CLASSICAL_COMPARATOR_REF"
        ),
    }


def _downstream_handoff_contract() -> dict[str, Any]:
    return {
        "pr141_consumes_downstream_input_from": ["PR140"],
        "pr141_creates_downstream_input_for": ["PR142"],
        "pr141_authorizes_materialization": False,
        "pr141_authorizes_bundle_mutation": False,
        "pr141_authorizes_row_family_source_mutation": False,
        "pr141_authorizes_source_acceptance": False,
        "pr141_authorizes_connector_binding": False,
        "pr141_authorizes_replay_execution": False,
        "pr141_authorizes_paper_execution": False,
        "pr141_authorizes_live_order_authority": False,
        "pr141_authorizes_quantum_backend_execution": False,
        "pr141_authorizes_final_readiness": False,
        "future_owner_authorization_required_for_actual_materialization": True,
        "future_owner_authorization_packet_required": True,
        "no_same_number_identity_inference": True,
    }


def _owner_authorization_readiness_summary(ledger: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "total_required_field_count": c.EXPECTED_REQUIRED_FIELD_COUNT,
        "existing_field_count": len(
            [
                entry
                for entry in ledger
                if entry.get("materialization_eligibility_state")
                == "EXISTING_FIELD_ALREADY_SUPPORTED"
            ]
        ),
        "eligible_to_request_owner_authorization_count": len(
            [
                entry
                for entry in ledger
                if entry.get("eligibility_to_request_owner_authorization") is True
            ]
        ),
        "source_evidence_blocked_count": len(
            [
                entry
                for entry in ledger
                if entry.get("source_evidence_required_before_materialization") is True
            ]
        ),
        "runtime_receipt_blocked_count": len(
            [
                entry
                for entry in ledger
                if entry.get("runtime_receipt_required_before_materialization") is True
            ]
        ),
        "replay_paper_evidence_blocked_count": len(
            [
                entry
                for entry in ledger
                if entry.get("replay_paper_evidence_required_before_materialization")
                is True
            ]
        ),
        "forced_false_authority_boundary_count": len(
            [
                entry
                for entry in ledger
                if entry.get("forced_false_no_authority_boundary") is True
            ]
        ),
        "quantum_metadata_only_count": len(
            [entry for entry in ledger if entry.get("quantum_metadata_only") is True]
        ),
        "owner_approval_granted_by_pr141": False,
        "materialization_permitted_now": False,
        "future_pr142_static_input_field_count": len(
            [entry for entry in ledger if entry.get("future_pr142_input_created") is True]
        ),
    }


def build_gate(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    context, _failures = _build_context(root)
    inventory = context["pr138_inventory"]
    pr137r = context["pr137r"]
    pr139_manifest = context["pr139_manifest"]
    pr140_plan = context["pr140_plan"]
    ledger = _field_ledger_records(inventory=inventory, pr140_plan=pr140_plan)
    return {
        "report_type": c.REPORT_TYPE,
        "gate_id": c.GATE_ID,
        "gate_version": c.GATE_VERSION,
        "pr_id": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "deterministic_output": True,
        "generated_at_utc": c.STATIC_TIME,
        "existing_bundle_row_count": c.EXPECTED_BUNDLE_ROW_COUNT,
        "row_family_source_file_count": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
        "source_manifest_entry_count": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
        "required_field_count": c.EXPECTED_REQUIRED_FIELD_COUNT,
        "required_field_group_count": c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT,
        "existing_supported_field_ids": _supported_fields_from_pr137r(pr137r),
        "pr140_downstream_input_consumed": True,
        "pr140_downstream_owner_authorization_required_for_materialization": True,
        "semantic_values_materialized": False,
        "materialization_permission_created": False,
        "owner_approval_receipt_created": False,
        "final_ready": False,
        "day1_launch_ready": False,
        "validation_marker": c.SUCCESS_MARKER,
        "semantic_field_inventory_path": c.PR138_INVENTORY_PATH.as_posix(),
        "pr140_coverage_plan_path": c.PR140_PLAN_PATH.as_posix(),
        "pr140_coverage_report_path": c.PR140_REPORT_PATH.as_posix(),
        "pr141_authorization_gate_path": c.GATE_PATH.as_posix(),
        "schema_path": c.SCHEMA_PATH.as_posix(),
        "control_plane_evidence_consumed": _path_list(c.CONTROL_PLANE_EVIDENCE_PATHS),
        "pr136_evidence_consumed": _path_list(c.PR136_EVIDENCE_PATHS),
        "pr137l_evidence_consumed": _path_list(c.PR137L_EVIDENCE_PATHS),
        "pr137r_evidence_consumed": _path_list(c.PR137R_EVIDENCE_PATHS),
        "pr138_evidence_consumed": _path_list(c.PR138_EVIDENCE_PATHS),
        "pr139_evidence_consumed": _path_list(c.PR139_EVIDENCE_PATHS),
        "pr140_evidence_consumed": _path_list(c.PR140_EVIDENCE_PATHS),
        "validation_context_evidence_consumed": _path_list(
            c.VALIDATION_CONTEXT_EVIDENCE_PATHS
        ),
        "crosswalk_alias_resolution": _crosswalk_alias_resolution(root),
        "authority_boundaries": dict(c.AUTHORITY_BOUNDARIES),
        "owner_authorization_readiness_summary": _owner_authorization_readiness_summary(
            ledger
        ),
        "field_authorization_readiness_ledger": ledger,
        "field_group_authorization_summary": _field_group_summary_records(
            inventory=inventory,
            ledger=ledger,
        ),
        "row_family_source_authorization_summary": _row_family_source_summary_records(
            pr139_manifest=pr139_manifest,
            ledger=ledger,
        ),
        "market_scope_authorization_summary": _market_scope_summary_records(
            inventory=inventory,
            market_index=context["market_index"],
        ),
        "agent_orchestration_authorization_summary": _agent_orchestration_summary(
            agent_map=context["agent_map"],
            pr140_plan=pr140_plan,
        ),
        "quantum_forward_authorization_boundary": _quantum_forward_authorization_boundary(
            context["quantum_map"]
        ),
        "latency_hot_path_authorization_boundary": dict(
            c.LATENCY_HOT_PATH_AUTHORIZATION_BOUNDARY
        ),
        "downstream_handoff_contract": _downstream_handoff_contract(),
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    return build_gate(repo_root)


def build_fixture(repo_root: Path | str) -> dict[str, Any]:
    fixture = build_gate(repo_root)
    fixture.update(FIXTURE_METADATA)
    return fixture


def _false_const_props(names: Sequence[str]) -> dict[str, Any]:
    return {name: {"const": False} for name in names}


def _true_const_props(names: Sequence[str]) -> dict[str, Any]:
    return {name: {"const": True} for name in names}


def _array_schema(enum_values: Sequence[str] | None = None, *, min_items: int | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "array", "items": {"type": "string"}}
    if enum_values is not None:
        schema["items"] = {"enum": list(enum_values)}
    if min_items is not None:
        schema["minItems"] = min_items
    return schema


def build_json_schema(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    context, _failures = _build_context(root)
    field_ids = _field_ids(context["pr138_inventory"])
    group_ids = _group_ids(context["pr138_inventory"])
    source_paths = _source_paths(context["pr139_manifest"])
    agent_ids = _agent_domain_ids(context["agent_map"], context["pr140_plan"])

    field_entry_required = [
        "field_id",
        "field_group_id",
        "pr138_required_flag",
        "pr140_coverage_status",
        "pr140_dependency_class",
        "pr140_future_pr_dependency_class",
        "owner_authorization_readiness_state",
        "materialization_eligibility_state",
        "downstream_dependency_class",
        "planned_enrichment_locus",
        "planned_row_family_source_paths",
        "eligibility_to_request_owner_authorization",
        "owner_approval_granted_by_pr141",
        "materialization_permitted_now",
        "owner_authorization_required_before_materialization",
        "source_evidence_required_before_materialization",
        "accepted_source_packet_required_before_materialization",
        "runtime_receipt_required_before_materialization",
        "replay_paper_evidence_required_before_materialization",
        "forced_false_no_authority_boundary",
        "quantum_metadata_only",
        "quantum_backend_execution_allowed",
        "semantic_value_materialized_by_pr141",
        "bundle_mutation_allowed_by_pr141",
        "row_family_source_mutation_allowed_by_pr141",
        "source_acceptance_created_by_pr141",
        "connector_binding_created_by_pr141",
        "live_use_allowed_by_pr141",
        "order_authority_created_by_pr141",
        "profit_evidence_created_by_pr141",
        "final_readiness_created_by_pr141",
        "future_pr142_input_created",
        "reason_code",
        "rationale",
    ]
    top_properties: dict[str, Any] = {
        "report_type": {"const": c.REPORT_TYPE},
        "gate_id": {"const": c.GATE_ID},
        "gate_version": {"const": c.GATE_VERSION},
        "pr_id": {"const": c.PR_ID},
        "authority_class": {"const": c.AUTHORITY_CLASS},
        "deterministic_output": {"const": True},
        "generated_at_utc": {"const": c.STATIC_TIME},
        "existing_bundle_row_count": {"const": c.EXPECTED_BUNDLE_ROW_COUNT},
        "row_family_source_file_count": {"const": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT},
        "source_manifest_entry_count": {"const": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT},
        "required_field_count": {"const": c.EXPECTED_REQUIRED_FIELD_COUNT},
        "required_field_group_count": {"const": c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT},
        "existing_supported_field_ids": {"const": ["row_id"]},
        "pr140_downstream_input_consumed": {"const": True},
        "pr140_downstream_owner_authorization_required_for_materialization": {"const": True},
        "semantic_values_materialized": {"const": False},
        "materialization_permission_created": {"const": False},
        "owner_approval_receipt_created": {"const": False},
        "final_ready": {"const": False},
        "day1_launch_ready": {"const": False},
        "validation_marker": {"const": c.SUCCESS_MARKER},
        "semantic_field_inventory_path": {"const": c.PR138_INVENTORY_PATH.as_posix()},
        "pr140_coverage_plan_path": {"const": c.PR140_PLAN_PATH.as_posix()},
        "pr140_coverage_report_path": {"const": c.PR140_REPORT_PATH.as_posix()},
        "pr141_authorization_gate_path": {"const": c.GATE_PATH.as_posix()},
        "schema_path": {"const": c.SCHEMA_PATH.as_posix()},
        "control_plane_evidence_consumed": _array_schema(),
        "pr136_evidence_consumed": _array_schema(),
        "pr137l_evidence_consumed": _array_schema(),
        "pr137r_evidence_consumed": _array_schema(),
        "pr138_evidence_consumed": _array_schema(),
        "pr139_evidence_consumed": _array_schema(),
        "pr140_evidence_consumed": _array_schema(),
        "validation_context_evidence_consumed": _array_schema(),
        "crosswalk_alias_resolution": {"$ref": "#/$defs/crosswalk_alias_resolution"},
        "authority_boundaries": {"$ref": "#/$defs/authority_boundaries"},
        "owner_authorization_readiness_summary": {
            "$ref": "#/$defs/owner_authorization_readiness_summary"
        },
        "field_authorization_readiness_ledger": {
            "items": {"$ref": "#/$defs/field_authorization_readiness_entry"},
            "minItems": c.EXPECTED_REQUIRED_FIELD_COUNT,
            "type": "array",
        },
        "field_group_authorization_summary": {
            "items": {"$ref": "#/$defs/field_group_authorization_entry"},
            "minItems": c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT,
            "type": "array",
        },
        "row_family_source_authorization_summary": {
            "items": {"$ref": "#/$defs/row_family_source_authorization_entry"},
            "minItems": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
            "type": "array",
        },
        "market_scope_authorization_summary": {
            "items": {"$ref": "#/$defs/market_scope_authorization_entry"},
            "minItems": len(c.MARKET_SCOPE_IDS),
            "type": "array",
        },
        "agent_orchestration_authorization_summary": {
            "items": {"$ref": "#/$defs/agent_orchestration_authorization_entry"},
            "type": "array",
        },
        "quantum_forward_authorization_boundary": {
            "$ref": "#/$defs/quantum_forward_authorization_boundary"
        },
        "latency_hot_path_authorization_boundary": {
            "$ref": "#/$defs/latency_hot_path_authorization_boundary"
        },
        "downstream_handoff_contract": {"$ref": "#/$defs/downstream_handoff_contract"},
        "execution": {"const": FIXTURE_METADATA["execution"]},
        "mode": {"const": FIXTURE_METADATA["mode"]},
    }
    top_required = [key for key in top_properties if key not in set(FIXTURE_METADATA)]

    field_entry_props = {
        "field_id": {"enum": field_ids},
        "field_group_id": {"enum": group_ids},
        "pr138_required_flag": {"const": True},
        "pr140_coverage_status": {"enum": list(c.PR140_COVERAGE_STATUS_VALUES)},
        "pr140_dependency_class": {"enum": list(c.PR140_DEPENDENCY_CLASS_VALUES)},
        "pr140_future_pr_dependency_class": {
            "enum": list(c.PR140_FUTURE_PR_DEPENDENCY_CLASS_VALUES)
        },
        "owner_authorization_readiness_state": {
            "enum": list(c.OWNER_AUTHORIZATION_READINESS_STATES)
        },
        "materialization_eligibility_state": {
            "enum": list(c.MATERIALIZATION_ELIGIBILITY_STATES)
        },
        "downstream_dependency_class": {"enum": list(c.DOWNSTREAM_DEPENDENCY_CLASSES)},
        "planned_enrichment_locus": _array_schema(source_paths),
        "planned_row_family_source_paths": _array_schema(source_paths),
        "eligibility_to_request_owner_authorization": {"type": "boolean"},
        "owner_approval_granted_by_pr141": {"const": False},
        "materialization_permitted_now": {"const": False},
        "owner_authorization_required_before_materialization": {"type": "boolean"},
        "source_evidence_required_before_materialization": {"type": "boolean"},
        "accepted_source_packet_required_before_materialization": {"type": "boolean"},
        "runtime_receipt_required_before_materialization": {"type": "boolean"},
        "replay_paper_evidence_required_before_materialization": {"type": "boolean"},
        "forced_false_no_authority_boundary": {"type": "boolean"},
        "quantum_metadata_only": {"type": "boolean"},
        "quantum_backend_execution_allowed": {"const": False},
        "semantic_value_materialized_by_pr141": {"const": False},
        "bundle_mutation_allowed_by_pr141": {"const": False},
        "row_family_source_mutation_allowed_by_pr141": {"const": False},
        "source_acceptance_created_by_pr141": {"const": False},
        "connector_binding_created_by_pr141": {"const": False},
        "live_use_allowed_by_pr141": {"const": False},
        "order_authority_created_by_pr141": {"const": False},
        "profit_evidence_created_by_pr141": {"const": False},
        "final_readiness_created_by_pr141": {"const": False},
        "future_pr142_input_created": {"type": "boolean"},
        "reason_code": {"enum": sorted(c.FIELD_RATIONALE_BY_REASON_CODE)},
        "rationale": {"type": "string"},
    }

    schema = {
        "$id": "qtt-local-schemas-atomicrows-semantic-value-materialization-owner-authorization-gate-pr141",
        "$schema": "json-schema-draft-2020-12",
        "title": "PR141 AtomicRows Semantic Value Materialization Owner Authorization Gate",
        "description": (
            "Static deterministic PR141 AtomicRows owner-authorization-readiness gate. "
            "It creates no row values, source acceptance, connector binding, replay, "
            "paper, live, order, profit, quantum execution, or final readiness authority."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": top_properties,
        "required": top_required,
        "$defs": {
            "authority_boundaries": {
                "type": "object",
                "additionalProperties": False,
                "properties": _false_const_props(tuple(c.AUTHORITY_BOUNDARIES)),
                "required": list(c.AUTHORITY_BOUNDARIES),
            },
            "crosswalk_alias_resolution": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "requested_alias": {"const": c.CROSSWALK_REQUESTED_ALIAS.as_posix()},
                    "alias_exists": {"type": "boolean"},
                    "canonical_crosswalk_used": {"const": c.CROSSWALK_CANONICAL.as_posix()},
                    "created_missing_alias": {"const": False},
                },
                "required": [
                    "requested_alias",
                    "alias_exists",
                    "canonical_crosswalk_used",
                    "created_missing_alias",
                ],
            },
            "owner_authorization_readiness_summary": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "total_required_field_count": {"const": c.EXPECTED_REQUIRED_FIELD_COUNT},
                    "existing_field_count": {"type": "integer"},
                    "eligible_to_request_owner_authorization_count": {"type": "integer"},
                    "source_evidence_blocked_count": {"type": "integer"},
                    "runtime_receipt_blocked_count": {"type": "integer"},
                    "replay_paper_evidence_blocked_count": {"type": "integer"},
                    "forced_false_authority_boundary_count": {"type": "integer"},
                    "quantum_metadata_only_count": {"type": "integer"},
                    "owner_approval_granted_by_pr141": {"const": False},
                    "materialization_permitted_now": {"const": False},
                    "future_pr142_static_input_field_count": {"type": "integer"},
                },
                "required": [
                    "total_required_field_count",
                    "existing_field_count",
                    "eligible_to_request_owner_authorization_count",
                    "source_evidence_blocked_count",
                    "runtime_receipt_blocked_count",
                    "replay_paper_evidence_blocked_count",
                    "forced_false_authority_boundary_count",
                    "quantum_metadata_only_count",
                    "owner_approval_granted_by_pr141",
                    "materialization_permitted_now",
                    "future_pr142_static_input_field_count",
                ],
            },
            "field_authorization_readiness_entry": {
                "type": "object",
                "additionalProperties": False,
                "properties": field_entry_props,
                "required": field_entry_required,
            },
            "field_group_authorization_entry": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "field_group_id": {"enum": group_ids},
                    "required_field_ids": _array_schema(field_ids),
                    "required_field_count": {"type": "integer"},
                    "field_authorization_count": {"type": "integer"},
                    "eligible_for_future_materialization_count": {"type": "integer"},
                    "source_evidence_blocked_count": {"type": "integer"},
                    "runtime_receipt_blocked_count": {"type": "integer"},
                    "replay_paper_blocked_count": {"type": "integer"},
                    "forced_false_boundary_count": {"type": "integer"},
                    "quantum_metadata_only_count": {"type": "integer"},
                    "no_authority_created": {"const": True},
                    "semantic_values_materialized": {"const": False},
                    "group_downstream_dependency_class": {
                        "enum": list(c.DOWNSTREAM_DEPENDENCY_CLASSES)
                    },
                },
                "required": [
                    "field_group_id",
                    "required_field_ids",
                    "required_field_count",
                    "field_authorization_count",
                    "eligible_for_future_materialization_count",
                    "source_evidence_blocked_count",
                    "runtime_receipt_blocked_count",
                    "replay_paper_blocked_count",
                    "forced_false_boundary_count",
                    "quantum_metadata_only_count",
                    "no_authority_created",
                    "semantic_values_materialized",
                    "group_downstream_dependency_class",
                ],
            },
            "row_family_source_authorization_entry": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "row_family_source_file_path": {"enum": source_paths},
                    "row_family_source_id": {"type": "string"},
                    "planned_field_ids": _array_schema(field_ids),
                    "eligible_field_ids_for_future_materialization": _array_schema(field_ids),
                    "blocked_field_ids": _array_schema(field_ids),
                    "mutation_allowed_by_pr141": {"const": False},
                    "semantic_values_materialized_by_pr141": {"const": False},
                    "future_owner_authorization_required": {"const": True},
                    "future_pr142_input_created": {"type": "boolean"},
                },
                "required": [
                    "row_family_source_file_path",
                    "row_family_source_id",
                    "planned_field_ids",
                    "eligible_field_ids_for_future_materialization",
                    "blocked_field_ids",
                    "mutation_allowed_by_pr141",
                    "semantic_values_materialized_by_pr141",
                    "future_owner_authorization_required",
                    "future_pr142_input_created",
                ],
            },
            "market_scope_authorization_entry": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "scope_id": {"enum": list(c.MARKET_SCOPE_IDS)},
                    "field_ids_relevant_to_scope": _array_schema(field_ids),
                    "owner_authorization_required_before_materialization": {"const": True},
                    "external_fact_authority_created": {"const": False},
                    "connector_binding_created": {"const": False},
                    "live_use_allowed_created": {"const": False},
                    "future_source_packet_dependency_class": {
                        "const": "ACCEPTED_SOURCE_PACKET_DEPENDENT"
                    },
                    "future_pr142_input_created": {"const": True},
                },
                "required": [
                    "scope_id",
                    "field_ids_relevant_to_scope",
                    "owner_authorization_required_before_materialization",
                    "external_fact_authority_created",
                    "connector_binding_created",
                    "live_use_allowed_created",
                    "future_source_packet_dependency_class",
                    "future_pr142_input_created",
                ],
            },
            "agent_orchestration_authorization_entry": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "agent_domain_id": {"enum": agent_ids},
                    "may_consume_pr141_gate_as_static_metadata": {"const": True},
                    "may_materialize_values_by_pr141": {"const": False},
                    "final_order_submission_authority_created": {"const": False},
                    "live_order_authority_allowed": {"const": False},
                    "latency_hot_path_allowed": {"const": False},
                    "future_owner_authorization_required": {"const": True},
                    "future_pr142_consumer_scope": {
                        "const": "STATIC_AUTHORIZATION_METADATA_ONLY"
                    },
                },
                "required": [
                    "agent_domain_id",
                    "may_consume_pr141_gate_as_static_metadata",
                    "may_materialize_values_by_pr141",
                    "final_order_submission_authority_created",
                    "live_order_authority_allowed",
                    "latency_hot_path_allowed",
                    "future_owner_authorization_required",
                    "future_pr142_consumer_scope",
                ],
            },
            "quantum_forward_authorization_boundary": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "quantum_metadata_authorization_scope": {"const": "STATIC_METADATA_ONLY"},
                    **_true_const_props(
                        (
                            "no_quantum_execution_flag",
                            "no_quantum_signal_creation_flag",
                            "no_quantum_optimizer_input_flag",
                            "no_quantum_optimizer_output_flag",
                            "no_quantum_backend_execution_flag",
                            "no_quantum_simulator_execution_flag",
                            "no_quantum_advantage_claim_flag",
                            "quantum_backend_execution_allowed_flag_forced_false",
                        )
                    ),
                    "future_qaoa_depth_p_ref": {"type": "string"},
                    "future_qaoa_qubo_constraint_ref": {"type": "string"},
                    "future_qubo_penalty_scale_ref": {"type": "string"},
                    "future_ising_model_ref": {"type": "string"},
                    "future_vqe_ansatz_ref": {"type": "string"},
                    "future_annealing_schedule_ref": {"type": "string"},
                    "future_shot_budget_ref": {"type": "string"},
                    "future_seed_control_ref": {"type": "string"},
                    "future_backend_provider_class_ref": {"type": "string"},
                    "future_classical_comparator_ref": {"type": "string"},
                },
                "required": [
                    "quantum_metadata_authorization_scope",
                    "no_quantum_execution_flag",
                    "no_quantum_signal_creation_flag",
                    "no_quantum_optimizer_input_flag",
                    "no_quantum_optimizer_output_flag",
                    "no_quantum_backend_execution_flag",
                    "no_quantum_simulator_execution_flag",
                    "no_quantum_advantage_claim_flag",
                    "quantum_backend_execution_allowed_flag_forced_false",
                    "future_qaoa_depth_p_ref",
                    "future_qaoa_qubo_constraint_ref",
                    "future_qubo_penalty_scale_ref",
                    "future_ising_model_ref",
                    "future_vqe_ansatz_ref",
                    "future_annealing_schedule_ref",
                    "future_shot_budget_ref",
                    "future_seed_control_ref",
                    "future_backend_provider_class_ref",
                    "future_classical_comparator_ref",
                ],
            },
            "latency_hot_path_authorization_boundary": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    key: ({"const": value} if isinstance(value, bool) else {"const": value})
                    for key, value in c.LATENCY_HOT_PATH_AUTHORIZATION_BOUNDARY.items()
                },
                "required": list(c.LATENCY_HOT_PATH_AUTHORIZATION_BOUNDARY),
            },
            "downstream_handoff_contract": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "pr141_consumes_downstream_input_from": {"const": ["PR140"]},
                    "pr141_creates_downstream_input_for": {"const": ["PR142"]},
                    "pr141_authorizes_materialization": {"const": False},
                    "pr141_authorizes_bundle_mutation": {"const": False},
                    "pr141_authorizes_row_family_source_mutation": {"const": False},
                    "pr141_authorizes_source_acceptance": {"const": False},
                    "pr141_authorizes_connector_binding": {"const": False},
                    "pr141_authorizes_replay_execution": {"const": False},
                    "pr141_authorizes_paper_execution": {"const": False},
                    "pr141_authorizes_live_order_authority": {"const": False},
                    "pr141_authorizes_quantum_backend_execution": {"const": False},
                    "pr141_authorizes_final_readiness": {"const": False},
                    "future_owner_authorization_required_for_actual_materialization": {
                        "const": True
                    },
                    "future_owner_authorization_packet_required": {"const": True},
                    "no_same_number_identity_inference": {"const": True},
                },
                "required": [
                    "pr141_consumes_downstream_input_from",
                    "pr141_creates_downstream_input_for",
                    "pr141_authorizes_materialization",
                    "pr141_authorizes_bundle_mutation",
                    "pr141_authorizes_row_family_source_mutation",
                    "pr141_authorizes_source_acceptance",
                    "pr141_authorizes_connector_binding",
                    "pr141_authorizes_replay_execution",
                    "pr141_authorizes_paper_execution",
                    "pr141_authorizes_live_order_authority",
                    "pr141_authorizes_quantum_backend_execution",
                    "pr141_authorizes_final_readiness",
                    "future_owner_authorization_required_for_actual_materialization",
                    "future_owner_authorization_packet_required",
                    "no_same_number_identity_inference",
                ],
            },
        },
    }
    return schema


def _canonical_gate_from_file(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        return _read_yaml(repo_root / c.GATE_PATH), []
    except (OSError, RegistryParseError, ValueError) as exc:
        return {}, [f"PR141_GATE_INVALID: {c.GATE_PATH.as_posix()}: {exc}"]


def _sequence_edge_exists(graph: Mapping[str, Any], start: str, end: str) -> bool:
    for edge in _list(graph.get("edges")):
        if not isinstance(edge, Mapping):
            continue
        if (
            edge.get("edge_type") == "SEQUENCE_DEPENDS_ON"
            and edge.get("from") == start
            and edge.get("to") == end
        ):
            return True
    return False


def _future_card_by_id(future_cards: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(card.get("future_pr_id")): card
        for card in _list(future_cards.get("cards"))
        if isinstance(card, Mapping) and card.get("future_pr_id")
    }


def _validate_evidence_invariants(context: Mapping[str, Any], repo_root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in (
        *c.CONTROL_PLANE_EVIDENCE_PATHS,
        *c.PR136_EVIDENCE_PATHS,
        *c.PR137L_EVIDENCE_PATHS,
        *c.PR137R_EVIDENCE_PATHS,
        *c.PR138_EVIDENCE_PATHS,
        *c.PR139_EVIDENCE_PATHS,
        *c.PR140_EVIDENCE_PATHS,
        *c.VALIDATION_CONTEXT_EVIDENCE_PATHS,
    ):
        if not (repo_root / rel_path).exists():
            failures.append(f"PR141_REQUIRED_EVIDENCE_MISSING: {rel_path.as_posix()}")
    if not (repo_root / c.CROSSWALK_CANONICAL).exists():
        failures.append("PR141_CROSSWALK_CANONICAL_MISSING")

    sequence = _mapping(context.get("sequence"))
    dependency_graph = _mapping(context.get("dependency_graph"))
    future_cards = _mapping(context.get("future_cards"))
    card_by_id = _future_card_by_id(future_cards)
    quantum_map = _mapping(context.get("quantum_map"))
    pr137r = _mapping(context.get("pr137r"))
    pr138_report = _mapping(context.get("pr138_report"))
    inventory = _mapping(context.get("pr138_inventory"))
    pr139_report = _mapping(context.get("pr139_report"))
    pr139_manifest = _mapping(context.get("pr139_manifest"))
    pr140_report = _mapping(context.get("pr140_report"))
    pr140_plan = _mapping(context.get("pr140_plan"))

    if sequence.get("future_pr_sequence_auto_authorizes_implementation") is not False:
        failures.append("PR141_PR136_SEQUENCE_AUTO_AUTHORIZES_IMPLEMENTATION")
    if sequence.get("future_pr_sequence_auto_authorizes_live_trading") is not False:
        failures.append("PR141_PR136_SEQUENCE_AUTO_AUTHORIZES_LIVE_TRADING")
    owner_gates = set(_string_list(sequence.get("owner_authorization_gates")))
    if not {"PR141", "PR142"}.issubset(owner_gates):
        failures.append("PR141_PR136_OWNER_AUTHORIZATION_GATES_MISSING")
    if not (
        _sequence_edge_exists(dependency_graph, "PR140", "PR141")
        and _sequence_edge_exists(dependency_graph, "PR141", "PR142")
    ):
        failures.append("PR141_PR136_DEPENDENCY_GRAPH_PR140_PR141_PR142_MISSING")
    blocked_edges = set(_string_list(dependency_graph.get("blocked_execution_edges")))
    for blocker in (
        "ATOMICROWS_MATERIALIZATION_BLOCKED_UNTIL_OWNER_AUTHORIZED_FUTURE_PR",
        "LIVE_TRADING_BLOCKED_UNTIL_OWNER_COMMAND",
        "QUANTUM_EXECUTION_BLOCKED_UNTIL_OWNER_AUTHORIZED_FUTURE_PR",
    ):
        if blocker not in blocked_edges:
            failures.append(f"PR141_PR136_BLOCKER_MISSING: {blocker}")
    for pr_id in ("PR141", "PR142"):
        card = _mapping(card_by_id.get(pr_id))
        if card.get("owner_authorization_required") is not True:
            failures.append(f"PR141_PR136_FUTURE_CARD_NOT_OWNER_GATE: {pr_id}")
        if card.get("live_scope") != "OWNER_COMMAND_REQUIRED":
            failures.append(f"PR141_PR136_FUTURE_CARD_LIVE_SCOPE_MISMATCH: {pr_id}")
        must_not_create = set(_string_list(card.get("must_not_create")))
        for forbidden in (
            "creates_live_data",
            "creates_source_acceptance",
            "creates_connector_binding",
            "creates_order_authority",
            "creates_profit_evidence",
            "creates_quantum_execution",
            "creates_day1_live_launch",
        ):
            if forbidden not in must_not_create:
                failures.append(f"PR141_PR136_FUTURE_CARD_MUST_NOT_CREATE_MISSING: {pr_id}.{forbidden}")
    if quantum_map.get("no_quantum_execution_flag") is not True:
        failures.append("PR141_PR136_QUANTUM_EXECUTION_NOT_BLOCKED")
    if quantum_map.get("no_quantum_optimizer_input_flag") is not True:
        failures.append("PR141_PR136_QUANTUM_OPTIMIZER_INPUT_NOT_BLOCKED")
    if quantum_map.get("no_quantum_advantage_claim_flag") is not True:
        failures.append("PR141_PR136_QUANTUM_ADVANTAGE_NOT_BLOCKED")

    state = _mapping(pr137r.get("atomicrows_validation_state"))
    artifact_inventory = _mapping(pr137r.get("atomicrows_artifact_inventory"))
    routing = _mapping(pr137r.get("current_sequence_routing"))
    row_count = state.get("row_count_value") or pr137r.get("expected_atomicrows_row_count")
    if row_count != c.EXPECTED_BUNDLE_ROW_COUNT:
        failures.append("PR141_PR137R_ROW_COUNT_NOT_4183")
    if artifact_inventory.get("row_family_source_file_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR141_PR137R_ROW_FAMILY_SOURCE_COUNT_NOT_15")
    if not {"PR138", "PR139", "PR140", "PR141", "PR142"}.issubset(
        set(_string_list(routing.get("current_sequence_atomicrows_bundle_implementation_slots")))
    ):
        failures.append("PR141_PR137R_SEQUENCE_SLOTS_MISSING")
    if not {"PR137", "PR137L", "PR138", "PR139", "PR140", "PR141"}.issubset(
        set(_string_list(routing.get("active_sequence_observed_prefix")))
    ):
        failures.append("PR141_PR137R_ACTIVE_PREFIX_MISSING")
    supported = _supported_fields_from_pr137r(pr137r)
    if supported != ["row_id"]:
        failures.append("PR141_PR137R_SUPPORTED_FIELDS_NOT_ROW_ID_ONLY")
    forbidden_diff = _mapping(pr137r.get("forbidden_diff_checks"))
    for key, value in forbidden_diff.items():
        if value is not False:
            failures.append(f"PR141_PR137R_FORBIDDEN_DIFF_TRUE: {key}")

    if inventory.get("required_field_count") != c.EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append("PR141_PR138_INVENTORY_REQUIRED_FIELD_COUNT_NOT_59")
    if inventory.get("required_field_group_count") != c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append("PR141_PR138_INVENTORY_REQUIRED_FIELD_GROUP_COUNT_NOT_8")
    if pr138_report.get("required_field_count") != c.EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append("PR141_PR138_REQUIRED_FIELD_COUNT_NOT_59")
    if pr138_report.get("required_field_group_count") != c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append("PR141_PR138_REQUIRED_FIELD_GROUP_COUNT_NOT_8")
    if not {"PR139", "PR140", "PR141", "PR142"}.issubset(
        set(_string_list(pr138_report.get("next_required_prs")))
    ):
        failures.append("PR141_PR138_NEXT_REQUIRED_PRS_MISSING")
    for flag in (
        "semantic_row_values_materialized_by_pr138",
        "source_acceptance_created_by_pr138",
        "connector_semantic_binding_created_by_pr138",
        "replay_execution_created_by_pr138",
        "paper_execution_created_by_pr138",
        "live_order_authority_created_by_pr138",
        "quantum_execution_created_by_pr138",
        "quantum_optimizer_input_created_by_pr138",
        "profit_evidence_created_by_pr138",
    ):
        if pr138_report.get(flag) is not False:
            failures.append(f"PR141_PR138_FORBIDDEN_AUTHORITY_CREATED: {flag}")

    source_manifest = _mapping(pr139_manifest.get("row_family_source_manifest"))
    if pr139_report.get("source_manifest_entry_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR141_PR139_SOURCE_MANIFEST_ENTRY_COUNT_NOT_15")
    if pr139_report.get("row_family_source_file_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR141_PR139_ROW_FAMILY_SOURCE_FILE_COUNT_NOT_15")
    if source_manifest.get("manifest_entry_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR141_PR139_MANIFEST_ENTRY_COUNT_NOT_15")
    if source_manifest.get("row_family_source_file_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR141_PR139_MANIFEST_SOURCE_FILE_COUNT_NOT_15")
    for key in (
        "semantic_value_materialization_allowed_flag",
        "bundle_mutation_allowed_flag",
        "final_readiness_created_flag",
        "source_acceptance_created_flag",
        "connector_semantic_binding_created_flag",
        "replay_paper_execution_created_flag",
        "quantum_backend_execution_created_flag",
        "profit_latency_execution_superiority_claim_created_flag",
    ):
        if pr139_manifest.get(key) is not False:
            failures.append(f"PR141_PR139_FORBIDDEN_AUTHORITY_CREATED: {key}")
    if pr139_report.get("final_ready") is not False:
        failures.append("PR141_PR139_FINAL_READY_CLAIMED")

    if pr140_report.get("required_field_count") != c.EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append("PR141_PR140_REQUIRED_FIELD_COUNT_NOT_59")
    if pr140_report.get("required_field_group_count") != c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append("PR141_PR140_REQUIRED_FIELD_GROUP_COUNT_NOT_8")
    if pr140_report.get("source_manifest_entry_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR141_PR140_SOURCE_MANIFEST_ENTRY_COUNT_NOT_15")
    if pr140_report.get("existing_bundle_row_count") != c.EXPECTED_BUNDLE_ROW_COUNT:
        failures.append("PR141_PR140_BUNDLE_ROW_COUNT_NOT_4183")
    if pr140_report.get("existing_supported_field_ids") != ["row_id"]:
        failures.append("PR141_PR140_SUPPORTED_FIELDS_NOT_ROW_ID_ONLY")
    if pr140_report.get("semantic_values_materialized") is not False:
        failures.append("PR141_PR140_VALUES_MATERIALIZED")
    if pr140_report.get("authority_class") != (
        "STATIC_ATOMICROWS_SEMANTIC_FIELD_COVERAGE_ENRICHMENT_PLAN_ONLY_NOT_VALUE_"
        "MATERIALIZATION_NOT_BUNDLE_MUTATION_NOT_FINAL_READINESS"
    ):
        failures.append("PR141_PR140_AUTHORITY_CLASS_MISMATCH")
    handoff = _mapping(pr140_report.get("downstream_handoff_contract"))
    if handoff.get("pr140_creates_downstream_input_for") != ["PR141", "PR142"]:
        failures.append("PR141_PR140_DOWNSTREAM_TARGETS_MISMATCH")
    if handoff.get("downstream_owner_authorization_required_for_materialization") is not True:
        failures.append("PR141_PR140_OWNER_AUTHORIZATION_NOT_REQUIRED")
    for scope in c.DOWNSTREAM_SCOPE_NOT_AUTHORIZED_BY_PR141:
        if scope not in _string_list(handoff.get("downstream_scope_not_authorized_by_pr140")):
            failures.append(f"PR141_PR140_SCOPE_NOT_AUTHORIZED_MISSING: {scope}")
    if handoff.get("no_same_number_identity_inference") is not True:
        failures.append("PR141_PR140_SAME_NUMBER_IDENTITY_INFERENCE_USED")
    if len(_pr140_field_coverage(pr140_plan)) != c.EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append("PR141_PR140_FIELD_COVERAGE_COUNT_NOT_59")
    return sorted(set(failures))


def _validate_no_forbidden_property_names_or_bundle_reference(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk(payload):
        lowered_key = key.lower()
        for fragment in c.FORBIDDEN_PROPERTY_NAME_FRAGMENTS:
            if fragment in lowered_key:
                failures.append(f"PR141_FORBIDDEN_PROPERTY_NAME: {path}")
        if isinstance(item, str) and c.forbidden_bundle_reference_text() in item:
            failures.append(f"PR141_FORBIDDEN_BUNDLE_REFERENCE: {path}")
    return failures


def _validate_false_authority_boundaries(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    boundaries = _mapping(payload.get("authority_boundaries"))
    if dict(boundaries) != c.AUTHORITY_BOUNDARIES:
        failures.append("PR141_AUTHORITY_BOUNDARY_REGISTRY_MISMATCH")
    allowed_true_created = {"future_pr142_input_created"}
    for path, key, item in _walk(payload):
        if key in c.AUTHORITY_BOUNDARIES and item is not False:
            failures.append(f"PR141_AUTHORITY_BOUNDARY_TRUE: {path}")
        if key.endswith("_created") and key not in allowed_true_created and not key.startswith("no_") and item is True:
            failures.append(f"PR141_AUTHORITY_CREATED_TRUE: {path}")
        if key.endswith("_claimed") and item is True:
            failures.append(f"PR141_AUTHORITY_CLAIMED_TRUE: {path}")
        if key in {
            "owner_approval_granted_by_pr141",
            "materialization_permitted_now",
            "quantum_backend_execution_allowed",
            "semantic_value_materialized_by_pr141",
        } and item is not False:
            failures.append(f"PR141_FIELD_FORBIDDEN_TRUE: {path}")
    return failures


def _validate_field_ledger(
    payload: Mapping[str, Any],
    *,
    inventory: Mapping[str, Any],
    pr140_plan: Mapping[str, Any],
    pr139_manifest: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    expected_field_ids = _field_ids(inventory)
    expected_group_by_field = _field_group_by_field(inventory)
    pr140_by_id = _pr140_field_by_id(pr140_plan)
    expected_source_paths = _source_paths(pr139_manifest)
    entries = [
        entry
        for entry in _list(payload.get("field_authorization_readiness_ledger"))
        if isinstance(entry, Mapping)
    ]
    field_ids = [str(entry.get("field_id")) for entry in entries]
    if len(field_ids) != c.EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append("PR141_FIELD_AUTHORIZATION_COUNT_NOT_59")
    if len(field_ids) != len(set(field_ids)):
        failures.append("PR141_DUPLICATE_FIELD_AUTHORIZATION")
    missing = sorted(set(expected_field_ids) - set(field_ids))
    unknown = sorted(set(field_ids) - set(expected_field_ids))
    if missing:
        failures.append(f"PR141_REQUIRED_FIELD_MISSING: {','.join(missing)}")
    if unknown:
        failures.append(f"PR141_UNKNOWN_FIELD_ID: {','.join(unknown)}")
    for entry in entries:
        field_id = str(entry.get("field_id"))
        expected_group_id = expected_group_by_field.get(field_id)
        if entry.get("field_group_id") != expected_group_id:
            failures.append(f"PR141_FIELD_GROUP_MISMATCH: {field_id}")
        pr140_field = pr140_by_id.get(field_id)
        if not pr140_field:
            failures.append(f"PR141_FIELD_MISSING_PR140_MAPPING: {field_id}")
            continue
        for pr140_key, entry_key in (
            ("coverage_status", "pr140_coverage_status"),
            ("dependency_class", "pr140_dependency_class"),
            ("future_pr_dependency_class", "pr140_future_pr_dependency_class"),
        ):
            if entry.get(entry_key) != pr140_field.get(pr140_key):
                failures.append(f"PR141_FIELD_PR140_MAPPING_MISMATCH: {field_id}.{entry_key}")
        if entry.get("planned_enrichment_locus") != pr140_field.get("planned_enrichment_locus"):
            failures.append(f"PR141_FIELD_PLANNED_LOCUS_MISMATCH: {field_id}")
        if entry.get("planned_row_family_source_paths") != expected_source_paths:
            failures.append(f"PR141_FIELD_SOURCE_PATHS_MISMATCH: {field_id}")
        if entry.get("pr138_required_flag") is not True:
            failures.append(f"PR141_FIELD_REQUIRED_FLAG_NOT_TRUE: {field_id}")
        for key in (
            "owner_approval_granted_by_pr141",
            "materialization_permitted_now",
            "quantum_backend_execution_allowed",
            "semantic_value_materialized_by_pr141",
            "bundle_mutation_allowed_by_pr141",
            "row_family_source_mutation_allowed_by_pr141",
            "source_acceptance_created_by_pr141",
            "connector_binding_created_by_pr141",
            "live_use_allowed_by_pr141",
            "order_authority_created_by_pr141",
            "profit_evidence_created_by_pr141",
            "final_readiness_created_by_pr141",
        ):
            if entry.get(key) is not False:
                failures.append(f"PR141_FIELD_FORBIDDEN_TRUE: {field_id}.{key}")
    row_id_entries = [entry for entry in entries if entry.get("field_id") == "row_id"]
    if not row_id_entries:
        failures.append("PR141_ROW_ID_ENTRY_MISSING")
    else:
        row_id = row_id_entries[0]
        if row_id.get("owner_authorization_readiness_state") != "EXISTING_ROW_ID_ONLY_NO_AUTHORIZATION_NEEDED":
            failures.append("PR141_ROW_ID_READINESS_STATE_MISMATCH")
        if row_id.get("materialization_eligibility_state") != "EXISTING_FIELD_ALREADY_SUPPORTED":
            failures.append("PR141_ROW_ID_MATERIALIZATION_STATE_MISMATCH")
        if row_id.get("downstream_dependency_class") != "EXISTING_ROW_ID_ONLY":
            failures.append("PR141_ROW_ID_DOWNSTREAM_CLASS_MISMATCH")
        if row_id.get("eligibility_to_request_owner_authorization") is not False:
            failures.append("PR141_ROW_ID_OWNER_AUTHORIZATION_ELIGIBLE")
    for field_id in c.FORCED_FALSE_FIELD_IDS:
        entry = next((item for item in entries if item.get("field_id") == field_id), None)
        if not entry:
            failures.append(f"PR141_FORCED_FALSE_FIELD_MISSING: {field_id}")
            continue
        if entry.get("forced_false_no_authority_boundary") is not True:
            failures.append(f"PR141_FORCED_FALSE_FIELD_NOT_FORCED_FALSE: {field_id}")
        if field_id == "quantum_backend_execution_allowed_flag":
            expected_state = "BLOCKED_BY_QUANTUM_BACKEND_EXECUTION_BOUNDARY"
        else:
            expected_state = "BLOCKED_BY_AUTHORITY_BOUNDARY"
        if entry.get("materialization_eligibility_state") != expected_state:
            failures.append(f"PR141_FORCED_FALSE_FIELD_STATE_MISMATCH: {field_id}")
    return sorted(set(failures))


def _validate_group_source_market_agent_sections(
    payload: Mapping[str, Any],
    *,
    inventory: Mapping[str, Any],
    pr139_manifest: Mapping[str, Any],
    agent_map: Mapping[str, Any],
    pr140_plan: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    expected_group_ids = _group_ids(inventory)
    grouped = _fields_by_group(inventory)
    group_entries = [
        entry
        for entry in _list(payload.get("field_group_authorization_summary"))
        if isinstance(entry, Mapping)
    ]
    group_ids = [str(entry.get("field_group_id")) for entry in group_entries]
    if len(group_ids) != c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT or set(group_ids) != set(expected_group_ids):
        failures.append("PR141_FIELD_GROUP_SUMMARY_MISMATCH")
    for entry in group_entries:
        group_id = str(entry.get("field_group_id"))
        if entry.get("required_field_ids") != grouped.get(group_id, []):
            failures.append(f"PR141_GROUP_FIELD_IDS_MISMATCH: {group_id}")
        if entry.get("required_field_count") != len(grouped.get(group_id, [])):
            failures.append(f"PR141_GROUP_FIELD_COUNT_MISMATCH: {group_id}")
        if entry.get("no_authority_created") is not True:
            failures.append(f"PR141_GROUP_AUTHORITY_CREATED: {group_id}")
        if entry.get("semantic_values_materialized") is not False:
            failures.append(f"PR141_GROUP_VALUES_MATERIALIZED: {group_id}")

    expected_source_paths = _source_paths(pr139_manifest)
    source_entries = [
        entry
        for entry in _list(payload.get("row_family_source_authorization_summary"))
        if isinstance(entry, Mapping)
    ]
    source_paths = [str(entry.get("row_family_source_file_path")) for entry in source_entries]
    if len(source_paths) != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT or set(source_paths) != set(expected_source_paths):
        failures.append("PR141_ROW_FAMILY_SOURCE_SUMMARY_MISMATCH")
    for entry in source_entries:
        source_path = str(entry.get("row_family_source_file_path"))
        if entry.get("mutation_allowed_by_pr141") is not False:
            failures.append(f"PR141_ROW_FAMILY_SOURCE_MUTATION_ALLOWED: {source_path}")
        if entry.get("semantic_values_materialized_by_pr141") is not False:
            failures.append(f"PR141_ROW_FAMILY_SOURCE_VALUES_MATERIALIZED: {source_path}")
        if entry.get("future_owner_authorization_required") is not True:
            failures.append(f"PR141_ROW_FAMILY_SOURCE_OWNER_AUTH_NOT_REQUIRED: {source_path}")

    market_entries = [
        entry
        for entry in _list(payload.get("market_scope_authorization_summary"))
        if isinstance(entry, Mapping)
    ]
    scope_ids = [str(entry.get("scope_id")) for entry in market_entries]
    if len(scope_ids) != len(c.MARKET_SCOPE_IDS) or set(scope_ids) != set(c.MARKET_SCOPE_IDS):
        failures.append("PR141_MARKET_SCOPE_SUMMARY_MISMATCH")
    for entry in market_entries:
        for key in (
            "external_fact_authority_created",
            "connector_binding_created",
            "live_use_allowed_created",
        ):
            if entry.get(key) is not False:
                failures.append(f"PR141_MARKET_SCOPE_AUTHORITY_CREATED: {entry.get('scope_id')}.{key}")
        if entry.get("owner_authorization_required_before_materialization") is not True:
            failures.append(f"PR141_MARKET_SCOPE_OWNER_AUTH_NOT_REQUIRED: {entry.get('scope_id')}")

    expected_agent_ids = _agent_domain_ids(agent_map, pr140_plan)
    agent_entries = [
        entry
        for entry in _list(payload.get("agent_orchestration_authorization_summary"))
        if isinstance(entry, Mapping)
    ]
    agent_ids = [str(entry.get("agent_domain_id")) for entry in agent_entries]
    if agent_ids != expected_agent_ids:
        failures.append("PR141_AGENT_DOMAIN_SUMMARY_MISMATCH")
    for entry in agent_entries:
        if entry.get("may_consume_pr141_gate_as_static_metadata") is not True:
            failures.append(f"PR141_AGENT_STATIC_METADATA_FALSE: {entry.get('agent_domain_id')}")
        for key in (
            "may_materialize_values_by_pr141",
            "final_order_submission_authority_created",
            "live_order_authority_allowed",
            "latency_hot_path_allowed",
        ):
            if entry.get(key) is not False:
                failures.append(f"PR141_AGENT_AUTHORITY_CREATED: {entry.get('agent_domain_id')}.{key}")
    return sorted(set(failures))


def _validate_quantum_latency_downstream(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    quantum = _mapping(payload.get("quantum_forward_authorization_boundary"))
    if quantum.get("quantum_metadata_authorization_scope") != "STATIC_METADATA_ONLY":
        failures.append("PR141_QUANTUM_SCOPE_NOT_STATIC_METADATA_ONLY")
    for key in (
        "no_quantum_execution_flag",
        "no_quantum_signal_creation_flag",
        "no_quantum_optimizer_input_flag",
        "no_quantum_optimizer_output_flag",
        "no_quantum_backend_execution_flag",
        "no_quantum_simulator_execution_flag",
        "no_quantum_advantage_claim_flag",
        "quantum_backend_execution_allowed_flag_forced_false",
    ):
        if quantum.get(key) is not True:
            failures.append(f"PR141_QUANTUM_BOUNDARY_FLAG_MISMATCH: {key}")
    for key in (
        "future_qaoa_depth_p_ref",
        "future_qaoa_qubo_constraint_ref",
        "future_qubo_penalty_scale_ref",
        "future_ising_model_ref",
        "future_vqe_ansatz_ref",
        "future_annealing_schedule_ref",
        "future_shot_budget_ref",
        "future_seed_control_ref",
        "future_backend_provider_class_ref",
        "future_classical_comparator_ref",
    ):
        if not quantum.get(key):
            failures.append(f"PR141_QUANTUM_REFERENCE_MISSING: {key}")

    latency = _mapping(payload.get("latency_hot_path_authorization_boundary"))
    if dict(latency) != c.LATENCY_HOT_PATH_AUTHORIZATION_BOUNDARY:
        failures.append("PR141_LATENCY_HOT_PATH_BOUNDARY_MISMATCH")

    handoff = _mapping(payload.get("downstream_handoff_contract"))
    expected = _downstream_handoff_contract()
    if dict(handoff) != expected:
        failures.append("PR141_DOWNSTREAM_HANDOFF_CONTRACT_MISMATCH")
    return sorted(set(failures))


def validate_gate_payload(
    gate: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    inventory: Mapping[str, Any],
    pr139_manifest: Mapping[str, Any],
    pr140_plan: Mapping[str, Any],
    agent_map: Mapping[str, Any],
) -> list[str]:
    failures = [
        f"PR141_SCHEMA_VALIDATION_FAILED: {failure}"
        for failure in validate_json_schema_subset(dict(gate), dict(schema))
    ]
    expected_identity = {
        "report_type": c.REPORT_TYPE,
        "gate_id": c.GATE_ID,
        "gate_version": c.GATE_VERSION,
        "pr_id": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "deterministic_output": True,
        "validation_marker": c.SUCCESS_MARKER,
        "semantic_values_materialized": False,
        "materialization_permission_created": False,
        "owner_approval_receipt_created": False,
        "final_ready": False,
        "day1_launch_ready": False,
    }
    for key, value in expected_identity.items():
        if gate.get(key) != value:
            failures.append(f"PR141_IDENTITY_OR_BOUNDARY_MISMATCH: {key}")
    failures.extend(_validate_false_authority_boundaries(gate))
    failures.extend(_validate_no_forbidden_property_names_or_bundle_reference(gate))
    failures.extend(
        _validate_field_ledger(
            gate,
            inventory=inventory,
            pr140_plan=pr140_plan,
            pr139_manifest=pr139_manifest,
        )
    )
    failures.extend(
        _validate_group_source_market_agent_sections(
            gate,
            inventory=inventory,
            pr139_manifest=pr139_manifest,
            agent_map=agent_map,
            pr140_plan=pr140_plan,
        )
    )
    failures.extend(_validate_quantum_latency_downstream(gate))
    return sorted(set(failures))


def validate_report_payload(report: Mapping[str, Any], expected_report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if dict(report) != dict(expected_report):
        failures.append("PR141_REPORT_STALE_OR_NONDETERMINISTIC")
    failures.extend(_validate_false_authority_boundaries(report))
    failures.extend(_validate_no_forbidden_property_names_or_bundle_reference(report))
    return sorted(set(failures))


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _changed_paths(repo_root: Path) -> list[str]:
    status_rc, status_out, _status_err = _git_stdout(
        repo_root,
        ["status", "--short", "--untracked-files=all"],
    )
    if status_rc != 0:
        return ["<git-status-unavailable>"]
    paths: list[str] = []
    for line in status_out.splitlines():
        if not line.strip():
            continue
        if len(line) > 2 and line[2] == " ":
            path = line[3:]
        elif len(line) > 1 and line[1] == " ":
            path = line[2:]
        else:
            path = line[3:] if len(line) > 3 else line
        paths.append(path.strip().replace("\\", "/"))
    return paths


def _is_ignored_pr141_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    tmp_dir, _tmp_glob = c.IGNORED_PR141_CHANGED_PATH_PATTERNS
    return normalized == tmp_dir or normalized.startswith(tmp_dir)


def _branch_allows_pr138_mainline_context_repair_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(
        branch,
        c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_DOWNSTREAM_AFTER_PR,
        allow_repair=False,
    )


def _is_pr138_mainline_context_repair_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS
        and _branch_allows_pr138_mainline_context_repair_changed_paths(branch)
    )


def _is_pr138_mainline_context_repair_changed_path(path: str, repo_root: Path) -> bool:
    branch_context = current_branch_context(repo_root)
    return _is_pr138_mainline_context_repair_changed_path_for_branch(
        path,
        branch_context.branch,
    )


def _branch_allows_pr140_guard_repair_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 140, allow_repair=False)


def _is_pr140_guard_repair_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR140_GUARD_REPAIR_CHANGED_PATHS
        and _branch_allows_pr140_guard_repair_changed_paths(branch)
    )


def _is_pr140_guard_repair_changed_path(path: str, repo_root: Path) -> bool:
    branch_context = current_branch_context(repo_root)
    return _is_pr140_guard_repair_changed_path_for_branch(path, branch_context.branch)


def _branch_allows_pr142_handoff_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 141, allow_repair=False)


def _is_pr142_handoff_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR142_HANDOFF_READINESS_GATE_CHANGED_PATHS
        and _branch_allows_pr142_handoff_changed_paths(branch)
    )


def _is_pr143_owner_override_currentization_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR143_OWNER_GLOBAL_OVERRIDE_CURRENTIZATION_CHANGED_PATHS
        and _branch_allows_pr142_handoff_changed_paths(branch)
    )


def _branch_allows_pr146_generated_report_nonmutating_validation_repair_changed_paths(
    branch: str,
) -> bool:
    return is_downstream_roadmap_branch(
        branch,
        c.PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_DOWNSTREAM_AFTER_PR,
        allow_repair=False,
    )


def _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized
        in c.PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_CHANGED_PATHS
        and _branch_allows_pr146_generated_report_nonmutating_validation_repair_changed_paths(
            branch
        )
    )


def _branch_allows_pr148_checkpoint_currentization_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(
        branch,
        c.PR148_POST_PR147_VALIDATION_STABLE_CHECKPOINT_CURRENTIZATION_DOWNSTREAM_AFTER_PR,
        allow_repair=False,
    )


def _is_pr148_checkpoint_currentization_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized
        in c.PR148_POST_PR147_VALIDATION_STABLE_CHECKPOINT_CURRENTIZATION_CHANGED_PATHS
        and _branch_allows_pr148_checkpoint_currentization_changed_paths(branch)
    )


def _branch_allows_pr149_implementation_bridge_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 147, allow_repair=False)


def _is_pr149_implementation_bridge_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR149_IMPLEMENTATION_BRIDGE_CHANGED_PATHS
        and _branch_allows_pr149_implementation_bridge_changed_paths(branch)
    )


def _branch_allows_pr150_target_matrix_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 147, allow_repair=False)


def _is_pr150_target_matrix_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR150_TARGET_MATRIX_CHANGED_PATHS
        and _branch_allows_pr150_target_matrix_changed_paths(branch)
    )


def _branch_allows_pr151_retrieval_target_pack_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 147, allow_repair=False)


def _is_pr151_retrieval_target_pack_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS
        and _branch_allows_pr151_retrieval_target_pack_changed_paths(branch)
    )


def _is_pr142_handoff_changed_path(path: str, repo_root: Path) -> bool:
    branch_context = current_branch_context(repo_root)
    return _is_pr142_handoff_changed_path_for_branch(
        path,
        branch_context.branch,
    ) or _is_pr143_owner_override_currentization_changed_path_for_branch(
        path,
        branch_context.branch,
    )


def _is_allowed_pr141_changed_path(path: str, repo_root: Path) -> bool:
    normalized = path.replace("\\", "/")
    branch_context = current_branch_context(repo_root)
    return (
        normalized in c.ALLOWED_PR141_CHANGED_PATHS
        or _is_pr138_mainline_context_repair_changed_path(normalized, repo_root)
        or _is_pr140_guard_repair_changed_path(normalized, repo_root)
        or _is_pr142_handoff_changed_path(normalized, repo_root)
        or _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
        or _is_pr148_checkpoint_currentization_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
        or _is_pr149_implementation_bridge_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
        or _is_pr150_target_matrix_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
        or _is_pr151_retrieval_target_pack_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
    )


def _validate_changed_paths(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR141_GIT_STATUS_UNAVAILABLE")
            continue
        normalized = path.replace("\\", "/")
        if _is_ignored_pr141_changed_path(normalized):
            continue
        if not _is_allowed_pr141_changed_path(normalized, repo_root):
            failures.append(f"PR141_CHANGED_PATH_OUT_OF_SCOPE: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append("PR141_MASTER_PLAN_MUTATION_DETECTED")
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix():
            failures.append("PR141_ATOMICROWS_BUNDLE_MUTATION_DETECTED")
        if normalized.startswith(c.ROW_FAMILY_SOURCE_DIRECTORY.as_posix() + "/"):
            failures.append("PR141_ROW_FAMILY_SOURCE_MUTATION_DETECTED")
    return sorted(set(failures))


def validate_repository_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    context, context_failures = _build_context(root)
    failures: list[str] = list(context_failures)
    failures.extend(_validate_evidence_invariants(context, root))

    expected_schema = build_json_schema(root)
    expected_gate = build_gate(root)
    expected_report = build_report(root)
    second_report = build_report(root)
    if expected_report != second_report:
        failures.append("PR141_OUTPUT_NOT_DETERMINISTIC")

    try:
        actual_schema = _read_json(root / c.SCHEMA_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_schema = {}
        failures.append(f"PR141_SCHEMA_INVALID: {c.SCHEMA_PATH.as_posix()}: {exc}")
    if actual_schema and actual_schema != expected_schema:
        failures.append("PR141_SCHEMA_STALE_OR_NONDETERMINISTIC")
    if actual_schema:
        failures.extend(_validate_no_forbidden_property_names_or_bundle_reference(actual_schema))

    actual_gate, gate_failures = _canonical_gate_from_file(root)
    failures.extend(gate_failures)
    if actual_gate and actual_gate != expected_gate:
        failures.append("PR141_GATE_STALE_OR_NONDETERMINISTIC")

    try:
        actual_fixture = _read_json(root / c.FIXTURE_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_fixture = {}
        failures.append(f"PR141_FIXTURE_INVALID: {c.FIXTURE_PATH.as_posix()}: {exc}")
    expected_fixture = build_fixture(root)
    if actual_fixture and actual_fixture != expected_fixture:
        failures.append("PR141_FIXTURE_STALE_OR_NONDETERMINISTIC")

    try:
        actual_report = _read_json(root / c.REPORT_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_report = {}
        failures.append(f"PR141_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}")

    if actual_gate:
        failures.extend(
            validate_gate_payload(
                actual_gate,
                expected_schema,
                inventory=context["pr138_inventory"],
                pr139_manifest=context["pr139_manifest"],
                pr140_plan=context["pr140_plan"],
                agent_map=context["agent_map"],
            )
        )
    if actual_report:
        failures.extend(validate_report_payload(actual_report, expected_report))
    if actual_fixture:
        fixture_schema_failures = validate_json_schema_subset(actual_fixture, expected_schema)
        failures.extend(
            [
                f"PR141_FIXTURE_SCHEMA_VALIDATION_FAILED: {failure}"
                for failure in fixture_schema_failures
            ]
        )
        failures.extend(_validate_no_forbidden_property_names_or_bundle_reference(actual_fixture))
    failures.extend(_validate_changed_paths(root))
    return sorted(set(failures))


def write_schema_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    schema = build_json_schema(root)
    _write_text(root / c.SCHEMA_PATH, json_dump(schema))
    return schema


def write_gate_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    gate = build_gate(root)
    _write_text(root / c.GATE_PATH, yaml_dump(gate))
    return gate


def write_report_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    report = build_report(root)
    _write_text(root / c.REPORT_PATH, json_dump(report))
    return report


def write_fixture_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    fixture = build_fixture(root)
    _write_text(root / c.FIXTURE_PATH, json_dump(fixture))
    return fixture


def write_all_artifacts(repo_root: Path | str) -> dict[str, Any]:
    return {
        "schema": write_schema_file(repo_root),
        "gate": write_gate_file(repo_root),
        "report": write_report_file(repo_root),
        "fixture": write_fixture_file(repo_root),
    }
