"""Deterministic PR140 AtomicRows semantic coverage plan builder and validator."""

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

from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
    constants as pr152_constants,
)

from . import constants as c


FIXTURE_METADATA = {
    "execution": "DISABLED",
    "mode": "SOURCE_REQUIRED",
}


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _as_posix(path: Path | str) -> str:
    return Path(path).as_posix()


def _path_list(paths: Sequence[Path]) -> list[str]:
    return [path.as_posix() for path in paths]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    return load_yaml_subset(path)


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
    ):
        path = repo_root / rel_path
        key = rel_path.as_posix()
        if not path.exists():
            failures.append(f"PR140_REQUIRED_EVIDENCE_MISSING: {key}")
            continue
        try:
            payloads[key] = _read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"PR140_REQUIRED_EVIDENCE_INVALID: {key}: {exc}")
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


def _dependency_class_for_field(field_id: str) -> str:
    if field_id == "row_id":
        return "EXISTING_ROW_ID_ONLY"
    if field_id in c.AUTHORITY_FLAG_FIELD_IDS:
        return "AUTHORITY_FLAG_FORCED_FALSE"
    if field_id in c.QUANTUM_METADATA_FIELD_IDS:
        return "QUANTUM_METADATA_ONLY"
    if field_id in c.SOURCE_EVIDENCE_FIELD_IDS:
        return "SOURCE_EVIDENCE_PACKET_REQUIRED"
    if field_id in c.RUNTIME_RECEIPT_FIELD_IDS:
        return "FUTURE_RUNTIME_RECEIPT_REQUIRED"
    if field_id in c.REPLAY_PAPER_FIELD_IDS:
        return "FUTURE_REPLAY_PAPER_EVIDENCE_REQUIRED"
    if field_id in c.OWNER_AUTHORIZATION_FIELD_IDS:
        return "OWNER_AUTHORIZATION_REQUIRED"
    if field_id in c.STATIC_POLICY_FIELD_IDS:
        return "STATIC_INTERNAL_POLICY"
    return "STATIC_ENUM_OR_TAXONOMY"


def _future_dependency_class(dependency_class: str) -> str:
    if dependency_class == "SOURCE_EVIDENCE_PACKET_REQUIRED":
        return "ACCEPTED_SOURCE_PACKET_DEPENDENT"
    if dependency_class == "FUTURE_RUNTIME_RECEIPT_REQUIRED":
        return "RUNTIME_RECEIPT_DEPENDENT"
    if dependency_class == "FUTURE_REPLAY_PAPER_EVIDENCE_REQUIRED":
        return "REPLAY_PAPER_EVIDENCE_DEPENDENT"
    if dependency_class in {"OWNER_AUTHORIZATION_REQUIRED", "AUTHORITY_FLAG_FORCED_FALSE"}:
        return "PR141_OR_PR142_OWNER_AUTHORIZATION_DEPENDENT"
    if dependency_class == "QUANTUM_METADATA_ONLY":
        return "QUANTUM_METADATA_STATIC_ONLY"
    return "STATIC_POLICY_ONLY"


def _coverage_status(field_id: str, supported_field_ids: set[str], dependency_class: str) -> str:
    if field_id in supported_field_ids:
        return "PRESENT_EXISTING_ID_ONLY"
    if dependency_class == "AUTHORITY_FLAG_FORCED_FALSE":
        return "BLOCKED_UNTIL_FUTURE_AUTHORIZED_PR"
    return "PLANNED_NOT_MATERIALIZED"


def _field_coverage_records(
    *,
    inventory: Mapping[str, Any],
    pr137r: Mapping[str, Any],
    source_paths: Sequence[str],
) -> list[dict[str, Any]]:
    supported = set(_supported_fields_from_pr137r(pr137r))
    records: list[dict[str, Any]] = []
    for field in _field_records(inventory):
        field_id = str(field.get("field_id"))
        field_group_id = str(field.get("field_group_id"))
        dependency_class = _dependency_class_for_field(field_id)
        coverage_status = _coverage_status(field_id, supported, dependency_class)
        records.append(
            {
                "accepted_source_evidence_required_before_connector_live_use": (
                    dependency_class == "SOURCE_EVIDENCE_PACKET_REQUIRED"
                ),
                "coverage_status": coverage_status,
                "dependency_class": dependency_class,
                "external_fact_authority_created": False,
                "field_group_id": field_group_id,
                "field_id": field_id,
                "field_is_hot_path_input": False,
                "forced_false_no_authority_boundary_until_future_pr": (
                    dependency_class == "AUTHORITY_FLAG_FORCED_FALSE"
                ),
                "future_pr_dependency_class": _future_dependency_class(dependency_class),
                "internal_static_policy_or_taxonomy_field": dependency_class
                in {"STATIC_INTERNAL_POLICY", "STATIC_ENUM_OR_TAXONOMY"},
                "live_use_allowed_created": False,
                "order_authority_created": False,
                "owner_authorization_required_before_materialization": field_id != "row_id",
                "planned_enrichment_locus": list(source_paths),
                "planned_row_family_source_paths": list(source_paths),
                "pr138_inventory_source": c.PR138_INVENTORY_PATH.as_posix(),
                "profit_evidence_created": False,
                "quantum_backend_execution_allowed_created": False,
                "quantum_metadata_only": dependency_class == "QUANTUM_METADATA_ONLY",
                "rationale": c.FIELD_RATIONALE_BY_DEPENDENCY_CLASS[dependency_class],
                "replay_paper_evidence_required_before_value_true": (
                    dependency_class == "FUTURE_REPLAY_PAPER_EVIDENCE_REQUIRED"
                ),
                "required_flag": True,
                "runtime_receipt_required_before_value_true": (
                    dependency_class == "FUTURE_RUNTIME_RECEIPT_REQUIRED"
                ),
                "value_materialization_status": "NOT_MATERIALIZED_BY_PR140",
            }
        )
    return records


def _field_group_coverage_records(
    *, inventory: Mapping[str, Any], field_coverage: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    fields_by_group = _fields_by_group(inventory)
    coverage_ids_by_group: dict[str, list[str]] = {group_id: [] for group_id in fields_by_group}
    for field in field_coverage:
        coverage_ids_by_group.setdefault(str(field.get("field_group_id")), []).append(
            str(field.get("field_id"))
        )
    downstream_by_group = {
        "IDENTITY": "STATIC_POLICY_ONLY",
        "PARAMETER_ALGORITHM_CLASSIFICATION": "STATIC_POLICY_ONLY",
        "AGENT_CONSUMER_BINDING": "STATIC_POLICY_ONLY",
        "MARKET_VENUE_SCOPE": "ACCEPTED_SOURCE_PACKET_DEPENDENT",
        "TRADING_OBJECTIVE_SUPPORT": "REPLAY_PAPER_EVIDENCE_DEPENDENT",
        "REPLAY_PAPER_LIVE_BOUNDARY": "PR141_OR_PR142_OWNER_AUTHORIZATION_DEPENDENT",
        "QUANTUM_COMPATIBILITY": "QUANTUM_METADATA_STATIC_ONLY",
        "SOURCE_PROVENANCE_BOUNDARY": "ACCEPTED_SOURCE_PACKET_DEPENDENT",
    }
    records: list[dict[str, Any]] = []
    for group in _field_group_records(inventory):
        group_id = str(group.get("field_group_id"))
        required_field_ids = list(fields_by_group.get(group_id, []))
        records.append(
            {
                "coverage_plan_complete": True,
                "covered_field_count": len(coverage_ids_by_group.get(group_id, [])),
                "downstream_dependency_class": downstream_by_group.get(
                    group_id, "STATIC_POLICY_ONLY"
                ),
                "field_group_id": group_id,
                "no_authority_created": True,
                "required_field_count": len(required_field_ids),
                "required_field_ids": required_field_ids,
                "semantic_values_materialized": False,
            }
        )
    return records


def _row_family_source_coverage_records(
    *, pr139_manifest: Mapping[str, Any], field_ids: Sequence[str], group_ids: Sequence[str]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for entry in _source_entries(pr139_manifest):
        records.append(
            {
                "future_enrichment_only": True,
                "mutation_allowed_by_pr140": False,
                "planned_field_group_ids": list(group_ids),
                "planned_field_ids": list(field_ids),
                "row_family_source_file_path": str(entry.get("source_file_path")),
                "row_family_source_id": str(entry.get("family_id")),
                "semantic_values_materialized_by_pr140": False,
            }
        )
    return records


def _market_scope_coverage_records(
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
        source_row = _mapping(by_scope.get(scope_id))
        records.append(
            {
                "connector_binding_created": False,
                "external_fact_authority_created": False,
                "field_groups_relevant_to_scope": relevant_group_ids,
                "fields_relevant_to_scope": relevant_fields,
                "future_source_packet_dependency_class": (
                    "ACCEPTED_SOURCE_PACKET_DEPENDENT"
                ),
                "live_use_allowed_created": False,
                "missing_accepted_source_evidence_classes": _string_list(
                    source_row.get("missing_accepted_source_evidence_classes")
                ),
                "scope_id": scope_id,
            }
        )
    return records


def _agent_orchestration_coverage(agent_map: Mapping[str, Any]) -> dict[str, Any]:
    domains: list[dict[str, Any]] = []
    for row in _list(agent_map.get("agent_domains")):
        if not isinstance(row, Mapping):
            continue
        domains.append(
            {
                "agent_domain_id": str(row.get("agent_domain_id")),
                "final_order_submission_authority_created": False,
                "future_owner_authorization_required": bool(
                    row.get("future_owner_authorization_required", True)
                ),
                "latency_hot_path_allowed": False,
                "live_order_authority_allowed": False,
                "may_consume_pr140_plan_as_static_metadata": True,
            }
        )
    return {
        "agent_domain_count": len(domains),
        "agent_domains": domains,
        "current_agent_authority_escalation_created": False,
        "source_evidence_ref": "docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json",
    }


def _first_ref(payload: Mapping[str, Any], key: str, fallback: str) -> str:
    values = _string_list(payload.get(key))
    return values[0] if values else fallback


def _coverage_for_field(field_coverage: Sequence[Mapping[str, Any]], field_id: str) -> dict[str, Any]:
    for field in field_coverage:
        if field.get("field_id") == field_id:
            return {
                "coverage_status": field.get("coverage_status"),
                "dependency_class": field.get("dependency_class"),
                "field_id": field_id,
                "value_materialization_status": field.get("value_materialization_status"),
            }
    return {
        "coverage_status": "MISSING_FROM_PR140_PLAN",
        "dependency_class": "MISSING_FROM_PR140_PLAN",
        "field_id": field_id,
        "value_materialization_status": "MISSING_FROM_PR140_PLAN",
    }


def _quantum_forward_metadata_plan(
    *, quantum_map: Mapping[str, Any], field_coverage: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    quantum_fields = (
        "quantum_applicability_class",
        "classical_only_flag",
        "quantum_inspired_flag",
        "true_quantum_compatible_flag",
        "qubo_compatible_flag",
        "ising_compatible_flag",
        "qaoa_compatible_flag",
        "vqe_compatible_flag",
        "annealing_compatible_flag",
        "quantum_kernel_feature_map_compatible_flag",
        "quantum_backend_execution_allowed_flag",
    )
    plan = {
        f"{field_id}_coverage": _coverage_for_field(field_coverage, field_id)
        for field_id in quantum_fields
    }
    plan.update(
        {
            "future_annealing_schedule_ref": _first_ref(
                quantum_map, "future_annealing_schedule_refs", "FUTURE_ANNEALING_SCHEDULE_REF"
            ),
            "future_backend_provider_class_ref": _first_ref(
                quantum_map, "future_backend_provider_class_refs", "FUTURE_BACKEND_PROVIDER_CLASS_REF"
            ),
            "future_classical_comparator_ref": _first_ref(
                quantum_map, "future_classical_comparator_refs", "FUTURE_CLASSICAL_COMPARATOR_REF"
            ),
            "future_ising_model_ref": _first_ref(
                quantum_map, "future_ising_model_refs", "FUTURE_ISING_MODEL_REF"
            ),
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
            "future_seed_control_ref": _first_ref(
                quantum_map, "future_seed_control_refs", "FUTURE_SEED_CONTROL_REF"
            ),
            "future_shot_budget_ref": _first_ref(
                quantum_map, "future_shot_budget_refs", "FUTURE_SHOT_BUDGET_REF"
            ),
            "future_vqe_ansatz_ref": _first_ref(
                quantum_map, "future_vqe_ansatz_refs", "FUTURE_VQE_ANSATZ_REF"
            ),
            "no_quantum_advantage_claim_flag": True,
            "no_quantum_execution_flag": True,
            "no_quantum_signal_creation_flag": True,
            "quantum_backend_execution_allowed_flag_forced_false": True,
            "quantum_metadata_only": True,
        }
    )
    return plan


def _downstream_handoff_contract(
    *, pr138_report: Mapping[str, Any], quantum_map: Mapping[str, Any]
) -> dict[str, Any]:
    next_required = set(_string_list(pr138_report.get("next_required_prs")))
    supported = ["PR141", "PR142"] if {"PR141", "PR142"}.issubset(next_required) else []
    return {
        "downstream_owner_authorization_required_for_materialization": (
            quantum_map.get("future_owner_authorization_required_for_materialization_flag")
            is True
        ),
        "downstream_scope_not_authorized_by_pr140": list(
            c.DOWNSTREAM_SCOPE_NOT_AUTHORIZED_BY_PR140
        ),
        "no_same_number_identity_inference": True,
        "pr140_creates_downstream_input_for": supported,
    }


def _crosswalk_alias_resolution(repo_root: Path) -> dict[str, Any]:
    alias_exists = (repo_root / c.CROSSWALK_REQUESTED_ALIAS).exists()
    return {
        "alias_exists": alias_exists,
        "canonical_crosswalk_used": c.CROSSWALK_CANONICAL.as_posix(),
        "created_missing_alias": False,
        "requested_alias": c.CROSSWALK_REQUESTED_ALIAS.as_posix(),
    }


def _build_context(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    payloads, failures = _load_required_json_evidence(repo_root)
    pr139_manifest: dict[str, Any] = {}
    try:
        pr139_manifest = _read_yaml(repo_root / c.PR139_MANIFEST_PATH)
    except (OSError, RegistryParseError) as exc:
        failures.append(f"PR140_REQUIRED_EVIDENCE_INVALID: {c.PR139_MANIFEST_PATH.as_posix()}: {exc}")
    return {
        "agent_map": payloads.get(c.PR136_EVIDENCE_PATHS[5].as_posix(), {}),
        "market_index": payloads.get(c.PR136_EVIDENCE_PATHS[3].as_posix(), {}),
        "pr137r": payloads.get(c.PR137R_REPORT_PATH.as_posix(), {}),
        "pr137l": payloads.get(c.PR137L_REPORT_PATH.as_posix(), {}),
        "pr138_inventory": payloads.get(c.PR138_INVENTORY_PATH.as_posix(), {}),
        "pr138_report": payloads.get(c.PR138_REPORT_PATH.as_posix(), {}),
        "pr139_manifest": pr139_manifest,
        "pr139_report": payloads.get(c.PR139_REPORT_PATH.as_posix(), {}),
        "quantum_map": payloads.get(c.PR136_EVIDENCE_PATHS[7].as_posix(), {}),
        "sequence": payloads.get(c.PR136_EVIDENCE_PATHS[8].as_posix(), {}),
        "payloads": payloads,
    }, failures


def build_plan(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    context, _failures = _build_context(root)
    inventory = context["pr138_inventory"]
    pr137r = context["pr137r"]
    pr139_manifest = context["pr139_manifest"]
    field_ids = _field_ids(inventory)
    group_ids = _group_ids(inventory)
    source_paths = _source_paths(pr139_manifest)
    field_coverage = _field_coverage_records(
        inventory=inventory,
        pr137r=pr137r,
        source_paths=source_paths,
    )
    return {
        "agent_orchestration_coverage": _agent_orchestration_coverage(context["agent_map"]),
        "authority_boundaries": dict(c.AUTHORITY_BOUNDARIES),
        "authority_class": c.AUTHORITY_CLASS,
        "coverage_plan_path": c.PLAN_PATH.as_posix(),
        "crosswalk_alias_resolution": _crosswalk_alias_resolution(root),
        "day1_launch_ready": False,
        "deterministic_output": True,
        "downstream_handoff_contract": _downstream_handoff_contract(
            pr138_report=context["pr138_report"],
            quantum_map=context["quantum_map"],
        ),
        "existing_bundle_row_count": c.EXPECTED_BUNDLE_ROW_COUNT,
        "existing_supported_field_ids": _supported_fields_from_pr137r(pr137r),
        "field_coverage": field_coverage,
        "field_group_coverage": _field_group_coverage_records(
            inventory=inventory,
            field_coverage=field_coverage,
        ),
        "final_ready": False,
        "generated_at_utc": c.STATIC_TIME,
        "latency_hot_path_exclusion_matrix": dict(c.LATENCY_HOT_PATH_EXCLUSION_MATRIX),
        "market_scope_coverage": {
            "market_scope_count": len(c.MARKET_SCOPE_IDS),
            "market_scopes": _market_scope_coverage_records(
                inventory=inventory,
                market_index=context["market_index"],
            ),
        },
        "missing_or_planned_field_count": len(
            [field_id for field_id in field_ids if field_id not in set(_supported_fields_from_pr137r(pr137r))]
        ),
        "plan_id": c.PLAN_ID,
        "plan_version": c.PLAN_VERSION,
        "pr_id": c.PR_ID,
        "quantum_forward_metadata_plan": _quantum_forward_metadata_plan(
            quantum_map=context["quantum_map"],
            field_coverage=field_coverage,
        ),
        "report_path": c.REPORT_PATH.as_posix(),
        "required_field_count": c.EXPECTED_REQUIRED_FIELD_COUNT,
        "required_field_group_count": c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT,
        "row_family_source_coverage": _row_family_source_coverage_records(
            pr139_manifest=pr139_manifest,
            field_ids=field_ids,
            group_ids=group_ids,
        ),
        "row_family_source_file_count": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
        "schema_path": c.SCHEMA_PATH.as_posix(),
        "semantic_field_inventory_path": c.PR138_INVENTORY_PATH.as_posix(),
        "semantic_values_materialized": False,
        "source_manifest_entry_count": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
        "source_manifest_path": c.PR139_MANIFEST_PATH.as_posix(),
        "validation_marker": c.SUCCESS_MARKER,
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    plan = build_plan(root)
    return {
        "agent_orchestration_coverage": plan["agent_orchestration_coverage"],
        "atomicrows_bundle_mutated": False,
        "authority_boundaries": dict(c.AUTHORITY_BOUNDARIES),
        "authority_class": c.AUTHORITY_CLASS,
        "branch_context_evidence_consumed": _path_list(c.BRANCH_CONTEXT_EVIDENCE_PATHS),
        "control_plane_evidence_consumed": _path_list(c.CONTROL_PLANE_EVIDENCE_PATHS),
        "coverage_plan_path": c.PLAN_PATH.as_posix(),
        "crosswalk_alias_resolution": plan["crosswalk_alias_resolution"],
        "day1_launch_ready": False,
        "deterministic_output": True,
        "downstream_handoff_contract": plan["downstream_handoff_contract"],
        "existing_bundle_row_count": c.EXPECTED_BUNDLE_ROW_COUNT,
        "existing_supported_field_ids": plan["existing_supported_field_ids"],
        "field_coverage": plan["field_coverage"],
        "field_group_coverage": plan["field_group_coverage"],
        "final_ready": False,
        "generated_at_utc": c.STATIC_TIME,
        "latency_hot_path_exclusion_matrix": dict(c.LATENCY_HOT_PATH_EXCLUSION_MATRIX),
        "market_scope_coverage": plan["market_scope_coverage"],
        "master_plan_mutated": False,
        "missing_or_planned_field_count": plan["missing_or_planned_field_count"],
        "pr136_evidence_consumed": _path_list(c.PR136_EVIDENCE_PATHS),
        "pr137l_evidence_consumed": _path_list(c.PR137L_EVIDENCE_PATHS),
        "pr137r_evidence_consumed": _path_list(c.PR137R_EVIDENCE_PATHS),
        "pr138_evidence_consumed": _path_list(c.PR138_EVIDENCE_PATHS),
        "pr139_evidence_consumed": _path_list(c.PR139_EVIDENCE_PATHS),
        "pr_id": c.PR_ID,
        "quantum_forward_metadata_plan": plan["quantum_forward_metadata_plan"],
        "report_type": c.REPORT_TYPE,
        "required_field_count": c.EXPECTED_REQUIRED_FIELD_COUNT,
        "required_field_group_count": c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT,
        "row_family_source_coverage": plan["row_family_source_coverage"],
        "row_family_source_file_count": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
        "row_family_sources_mutated": False,
        "schema_path": c.SCHEMA_PATH.as_posix(),
        "semantic_field_inventory_path": c.PR138_INVENTORY_PATH.as_posix(),
        "semantic_values_materialized": False,
        "source_manifest_entry_count": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
        "source_manifest_path": c.PR139_MANIFEST_PATH.as_posix(),
        "validation_marker": c.SUCCESS_MARKER,
    }


def build_fixture(repo_root: Path | str) -> dict[str, Any]:
    fixture = build_plan(repo_root)
    fixture.update(FIXTURE_METADATA)
    return fixture


def _false_const_props(names: Sequence[str]) -> dict[str, Any]:
    return {name: {"const": False} for name in names}


def build_json_schema(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    context, _failures = _build_context(root)
    field_ids = _field_ids(context["pr138_inventory"])
    group_ids = _group_ids(context["pr138_inventory"])
    source_paths = _source_paths(context["pr139_manifest"])
    field_entry_required = [
        "field_id",
        "field_group_id",
        "required_flag",
        "pr138_inventory_source",
        "coverage_status",
        "dependency_class",
        "planned_enrichment_locus",
        "planned_row_family_source_paths",
        "value_materialization_status",
        "external_fact_authority_created",
        "live_use_allowed_created",
        "order_authority_created",
        "profit_evidence_created",
        "quantum_backend_execution_allowed_created",
        "field_is_hot_path_input",
        "future_pr_dependency_class",
        "rationale",
        "internal_static_policy_or_taxonomy_field",
        "accepted_source_evidence_required_before_connector_live_use",
        "runtime_receipt_required_before_value_true",
        "replay_paper_evidence_required_before_value_true",
        "owner_authorization_required_before_materialization",
        "forced_false_no_authority_boundary_until_future_pr",
        "quantum_metadata_only",
    ]
    authority_false_props = _false_const_props(tuple(c.AUTHORITY_BOUNDARIES))
    per_field_false_props = _false_const_props(
        (
            "external_fact_authority_created",
            "live_use_allowed_created",
            "order_authority_created",
            "profit_evidence_created",
            "quantum_backend_execution_allowed_created",
            "field_is_hot_path_input",
        )
    )
    latency_props = {
        key: ({"const": value} if isinstance(value, (bool, str)) else {"type": "string"})
        for key, value in c.LATENCY_HOT_PATH_EXCLUSION_MATRIX.items()
    }
    top_properties: dict[str, Any] = {
        "agent_orchestration_coverage": {"$ref": "#/$defs/agent_orchestration_coverage"},
        "authority_boundaries": {"$ref": "#/$defs/authority_boundaries"},
        "authority_class": {"const": c.AUTHORITY_CLASS},
        "coverage_plan_path": {"const": c.PLAN_PATH.as_posix()},
        "crosswalk_alias_resolution": {"$ref": "#/$defs/crosswalk_alias_resolution"},
        "day1_launch_ready": {"const": False},
        "deterministic_output": {"const": True},
        "downstream_handoff_contract": {"$ref": "#/$defs/downstream_handoff_contract"},
        "execution": {"const": FIXTURE_METADATA["execution"]},
        "existing_bundle_row_count": {"const": c.EXPECTED_BUNDLE_ROW_COUNT},
        "existing_supported_field_ids": {"const": ["row_id"]},
        "field_coverage": {
            "items": {"$ref": "#/$defs/field_coverage_entry"},
            "minItems": c.EXPECTED_REQUIRED_FIELD_COUNT,
            "type": "array",
        },
        "field_group_coverage": {
            "items": {"$ref": "#/$defs/field_group_coverage_entry"},
            "minItems": c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT,
            "type": "array",
        },
        "final_ready": {"const": False},
        "generated_at_utc": {"const": c.STATIC_TIME},
        "latency_hot_path_exclusion_matrix": {
            "$ref": "#/$defs/latency_hot_path_exclusion_matrix"
        },
        "market_scope_coverage": {"$ref": "#/$defs/market_scope_coverage"},
        "missing_or_planned_field_count": {"const": c.EXPECTED_REQUIRED_FIELD_COUNT - 1},
        "mode": {"const": FIXTURE_METADATA["mode"]},
        "plan_id": {"const": c.PLAN_ID},
        "plan_version": {"const": c.PLAN_VERSION},
        "pr_id": {"const": c.PR_ID},
        "quantum_forward_metadata_plan": {"$ref": "#/$defs/quantum_forward_metadata_plan"},
        "report_path": {"const": c.REPORT_PATH.as_posix()},
        "required_field_count": {"const": c.EXPECTED_REQUIRED_FIELD_COUNT},
        "required_field_group_count": {"const": c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT},
        "row_family_source_coverage": {
            "items": {"$ref": "#/$defs/row_family_source_coverage_entry"},
            "minItems": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT,
            "type": "array",
        },
        "row_family_source_file_count": {"const": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT},
        "schema_path": {"const": c.SCHEMA_PATH.as_posix()},
        "semantic_field_inventory_path": {"const": c.PR138_INVENTORY_PATH.as_posix()},
        "semantic_values_materialized": {"const": False},
        "source_manifest_entry_count": {"const": c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT},
        "source_manifest_path": {"const": c.PR139_MANIFEST_PATH.as_posix()},
        "validation_marker": {"const": c.SUCCESS_MARKER},
    }
    top_required = [
        key for key in top_properties if key not in set(FIXTURE_METADATA)
    ]
    quantum_properties: dict[str, Any] = {
        f"{field_id}_coverage": {"$ref": "#/$defs/quantum_field_coverage"}
        for field_id in (
            "quantum_applicability_class",
            "classical_only_flag",
            "quantum_inspired_flag",
            "true_quantum_compatible_flag",
            "qubo_compatible_flag",
            "ising_compatible_flag",
            "qaoa_compatible_flag",
            "vqe_compatible_flag",
            "annealing_compatible_flag",
            "quantum_kernel_feature_map_compatible_flag",
            "quantum_backend_execution_allowed_flag",
        )
    }
    quantum_properties.update(
        {
            "future_annealing_schedule_ref": {"type": "string"},
            "future_backend_provider_class_ref": {"type": "string"},
            "future_classical_comparator_ref": {"type": "string"},
            "future_ising_model_ref": {"type": "string"},
            "future_qaoa_depth_p_ref": {"type": "string"},
            "future_qaoa_qubo_constraint_ref": {"type": "string"},
            "future_qubo_penalty_scale_ref": {"type": "string"},
            "future_seed_control_ref": {"type": "string"},
            "future_shot_budget_ref": {"type": "string"},
            "future_vqe_ansatz_ref": {"type": "string"},
            "no_quantum_advantage_claim_flag": {"const": True},
            "no_quantum_execution_flag": {"const": True},
            "no_quantum_signal_creation_flag": {"const": True},
            "quantum_backend_execution_allowed_flag_forced_false": {"const": True},
            "quantum_metadata_only": {"const": True},
        }
    )
    return {
        "$id": "qtt-local-schemas-atomicrows-semantic-field-coverage-enrichment-plan-pr140",
        "$schema": "json-schema-draft-2020-12",
        "additionalProperties": False,
        "description": (
            "Static deterministic PR140 AtomicRows semantic field coverage and enrichment "
            "plan. It creates no row values, source acceptance, connector binding, replay, "
            "paper, live, order, profit, quantum execution, or final readiness authority."
        ),
        "properties": top_properties,
        "required": top_required,
        "title": "PR140 AtomicRows Semantic Field Coverage Enrichment Plan",
        "type": "object",
        "$defs": {
            "agent_domain_entry": {
                "additionalProperties": False,
                "properties": {
                    "agent_domain_id": {"type": "string"},
                    "final_order_submission_authority_created": {"const": False},
                    "future_owner_authorization_required": {"type": "boolean"},
                    "latency_hot_path_allowed": {"const": False},
                    "live_order_authority_allowed": {"const": False},
                    "may_consume_pr140_plan_as_static_metadata": {"const": True},
                },
                "required": [
                    "agent_domain_id",
                    "may_consume_pr140_plan_as_static_metadata",
                    "live_order_authority_allowed",
                    "latency_hot_path_allowed",
                    "final_order_submission_authority_created",
                    "future_owner_authorization_required",
                ],
                "type": "object",
            },
            "agent_orchestration_coverage": {
                "additionalProperties": False,
                "properties": {
                    "agent_domain_count": {"type": "integer"},
                    "agent_domains": {
                        "items": {"$ref": "#/$defs/agent_domain_entry"},
                        "type": "array",
                    },
                    "current_agent_authority_escalation_created": {"const": False},
                    "source_evidence_ref": {"type": "string"},
                },
                "required": [
                    "agent_domain_count",
                    "agent_domains",
                    "current_agent_authority_escalation_created",
                    "source_evidence_ref",
                ],
                "type": "object",
            },
            "authority_boundaries": {
                "additionalProperties": False,
                "properties": authority_false_props,
                "required": list(c.AUTHORITY_BOUNDARIES),
                "type": "object",
            },
            "crosswalk_alias_resolution": {
                "additionalProperties": False,
                "properties": {
                    "alias_exists": {"type": "boolean"},
                    "canonical_crosswalk_used": {"const": c.CROSSWALK_CANONICAL.as_posix()},
                    "created_missing_alias": {"const": False},
                    "requested_alias": {"const": c.CROSSWALK_REQUESTED_ALIAS.as_posix()},
                },
                "required": [
                    "requested_alias",
                    "alias_exists",
                    "canonical_crosswalk_used",
                    "created_missing_alias",
                ],
                "type": "object",
            },
            "downstream_handoff_contract": {
                "additionalProperties": False,
                "properties": {
                    "downstream_owner_authorization_required_for_materialization": {
                        "const": True
                    },
                    "downstream_scope_not_authorized_by_pr140": {
                        "const": list(c.DOWNSTREAM_SCOPE_NOT_AUTHORIZED_BY_PR140)
                    },
                    "no_same_number_identity_inference": {"const": True},
                    "pr140_creates_downstream_input_for": {"const": ["PR141", "PR142"]},
                },
                "required": [
                    "pr140_creates_downstream_input_for",
                    "downstream_scope_not_authorized_by_pr140",
                    "downstream_owner_authorization_required_for_materialization",
                    "no_same_number_identity_inference",
                ],
                "type": "object",
            },
            "field_coverage_entry": {
                "additionalProperties": False,
                "properties": {
                    **per_field_false_props,
                    "accepted_source_evidence_required_before_connector_live_use": {
                        "type": "boolean"
                    },
                    "coverage_status": {"enum": list(c.COVERAGE_STATUS_VALUES)},
                    "dependency_class": {"enum": list(c.DEPENDENCY_CLASS_VALUES)},
                    "field_group_id": {"enum": group_ids},
                    "field_id": {"enum": field_ids},
                    "forced_false_no_authority_boundary_until_future_pr": {
                        "type": "boolean"
                    },
                    "future_pr_dependency_class": {
                        "enum": list(c.FUTURE_PR_DEPENDENCY_CLASS_VALUES)
                    },
                    "internal_static_policy_or_taxonomy_field": {"type": "boolean"},
                    "owner_authorization_required_before_materialization": {
                        "type": "boolean"
                    },
                    "planned_enrichment_locus": {
                        "items": {"enum": source_paths},
                        "type": "array",
                    },
                    "planned_row_family_source_paths": {
                        "items": {"enum": source_paths},
                        "type": "array",
                    },
                    "pr138_inventory_source": {"const": c.PR138_INVENTORY_PATH.as_posix()},
                    "quantum_metadata_only": {"type": "boolean"},
                    "rationale": {"type": "string"},
                    "replay_paper_evidence_required_before_value_true": {
                        "type": "boolean"
                    },
                    "required_flag": {"const": True},
                    "runtime_receipt_required_before_value_true": {"type": "boolean"},
                    "value_materialization_status": {"const": "NOT_MATERIALIZED_BY_PR140"},
                },
                "required": field_entry_required,
                "type": "object",
            },
            "field_group_coverage_entry": {
                "additionalProperties": False,
                "properties": {
                    "coverage_plan_complete": {"const": True},
                    "covered_field_count": {"type": "integer"},
                    "downstream_dependency_class": {
                        "enum": list(c.FUTURE_PR_DEPENDENCY_CLASS_VALUES)
                    },
                    "field_group_id": {"enum": group_ids},
                    "no_authority_created": {"const": True},
                    "required_field_count": {"type": "integer"},
                    "required_field_ids": {"items": {"enum": field_ids}, "type": "array"},
                    "semantic_values_materialized": {"const": False},
                },
                "required": [
                    "field_group_id",
                    "required_field_ids",
                    "required_field_count",
                    "covered_field_count",
                    "coverage_plan_complete",
                    "semantic_values_materialized",
                    "downstream_dependency_class",
                    "no_authority_created",
                ],
                "type": "object",
            },
            "latency_hot_path_exclusion_matrix": {
                "additionalProperties": False,
                "properties": latency_props,
                "required": list(c.LATENCY_HOT_PATH_EXCLUSION_MATRIX),
                "type": "object",
            },
            "market_scope_coverage": {
                "additionalProperties": False,
                "properties": {
                    "market_scope_count": {"const": len(c.MARKET_SCOPE_IDS)},
                    "market_scopes": {
                        "items": {"$ref": "#/$defs/market_scope_entry"},
                        "type": "array",
                    },
                },
                "required": ["market_scope_count", "market_scopes"],
                "type": "object",
            },
            "market_scope_entry": {
                "additionalProperties": False,
                "properties": {
                    "connector_binding_created": {"const": False},
                    "external_fact_authority_created": {"const": False},
                    "field_groups_relevant_to_scope": {
                        "items": {"enum": group_ids},
                        "type": "array",
                    },
                    "fields_relevant_to_scope": {"items": {"enum": field_ids}, "type": "array"},
                    "future_source_packet_dependency_class": {
                        "const": "ACCEPTED_SOURCE_PACKET_DEPENDENT"
                    },
                    "live_use_allowed_created": {"const": False},
                    "missing_accepted_source_evidence_classes": {
                        "items": {"type": "string"},
                        "type": "array",
                    },
                    "scope_id": {"enum": list(c.MARKET_SCOPE_IDS)},
                },
                "required": [
                    "scope_id",
                    "fields_relevant_to_scope",
                    "field_groups_relevant_to_scope",
                    "external_fact_authority_created",
                    "connector_binding_created",
                    "live_use_allowed_created",
                    "future_source_packet_dependency_class",
                    "missing_accepted_source_evidence_classes",
                ],
                "type": "object",
            },
            "quantum_field_coverage": {
                "additionalProperties": False,
                "properties": {
                    "coverage_status": {"enum": list(c.COVERAGE_STATUS_VALUES)},
                    "dependency_class": {"enum": list(c.DEPENDENCY_CLASS_VALUES)},
                    "field_id": {"enum": field_ids},
                    "value_materialization_status": {"const": "NOT_MATERIALIZED_BY_PR140"},
                },
                "required": [
                    "field_id",
                    "coverage_status",
                    "dependency_class",
                    "value_materialization_status",
                ],
                "type": "object",
            },
            "quantum_forward_metadata_plan": {
                "additionalProperties": False,
                "properties": quantum_properties,
                "required": list(quantum_properties),
                "type": "object",
            },
            "row_family_source_coverage_entry": {
                "additionalProperties": False,
                "properties": {
                    "future_enrichment_only": {"const": True},
                    "mutation_allowed_by_pr140": {"const": False},
                    "planned_field_group_ids": {
                        "items": {"enum": group_ids},
                        "type": "array",
                    },
                    "planned_field_ids": {"items": {"enum": field_ids}, "type": "array"},
                    "row_family_source_file_path": {"enum": source_paths},
                    "row_family_source_id": {"type": "string"},
                    "semantic_values_materialized_by_pr140": {"const": False},
                },
                "required": [
                    "row_family_source_file_path",
                    "row_family_source_id",
                    "planned_field_group_ids",
                    "planned_field_ids",
                    "mutation_allowed_by_pr140",
                    "semantic_values_materialized_by_pr140",
                    "future_enrichment_only",
                ],
                "type": "object",
            },
        },
    }


def _canonical_plan_from_file(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        return _read_yaml(repo_root / c.PLAN_PATH), []
    except (OSError, RegistryParseError) as exc:
        return {}, [f"PR140_PLAN_INVALID: {c.PLAN_PATH.as_posix()}: {exc}"]


def _validate_evidence_invariants(context: Mapping[str, Any], repo_root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in (
        *c.CONTROL_PLANE_EVIDENCE_PATHS,
        *c.PR136_EVIDENCE_PATHS,
        *c.PR137L_EVIDENCE_PATHS,
        *c.PR137R_EVIDENCE_PATHS,
        *c.PR138_EVIDENCE_PATHS,
        *c.PR139_EVIDENCE_PATHS,
        *c.BRANCH_CONTEXT_EVIDENCE_PATHS,
    ):
        if not (repo_root / rel_path).exists():
            failures.append(f"PR140_REQUIRED_EVIDENCE_MISSING: {rel_path.as_posix()}")
    if not (repo_root / c.CROSSWALK_CANONICAL).exists():
        failures.append("PR140_CROSSWALK_CANONICAL_MISSING")

    inventory = _mapping(context.get("pr138_inventory"))
    pr138_report = _mapping(context.get("pr138_report"))
    pr137r = _mapping(context.get("pr137r"))
    pr139_report = _mapping(context.get("pr139_report"))
    pr139_manifest = _mapping(context.get("pr139_manifest"))
    quantum_map = _mapping(context.get("quantum_map"))
    sequence = _mapping(context.get("sequence"))
    market_index = _mapping(context.get("market_index"))
    agent_map = _mapping(context.get("agent_map"))

    if inventory.get("required_field_count") != c.EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append("PR140_PR138_REQUIRED_FIELD_COUNT_NOT_59")
    if inventory.get("required_field_group_count") != c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append("PR140_PR138_REQUIRED_FIELD_GROUP_COUNT_NOT_8")
    if pr138_report.get("required_field_count") != c.EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append("PR140_PR138_REQUIRED_FIELD_COUNT_NOT_59")
    if pr138_report.get("required_field_group_count") != c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append("PR140_PR138_REQUIRED_FIELD_GROUP_COUNT_NOT_8")
    if pr138_report.get("semantic_row_values_materialized_by_pr138") is not False:
        failures.append("PR140_PR138_SEMANTIC_VALUES_MATERIALIZED")
    for flag in (
        "final_readiness_claimed_by_pr138",
        "source_acceptance_created_by_pr138",
        "connector_semantic_binding_created_by_pr138",
        "replay_execution_created_by_pr138",
        "paper_execution_created_by_pr138",
        "live_order_authority_created_by_pr138",
        "order_execution_created_by_pr138",
        "profit_evidence_created_by_pr138",
        "quantum_execution_created_by_pr138",
        "quantum_simulator_execution_created_by_pr138",
        "quantum_optimizer_input_created_by_pr138",
        "quantum_optimizer_output_created_by_pr138",
        "quantum_advantage_claimed_by_pr138",
    ):
        if pr138_report.get(flag) is not False:
            failures.append(f"PR140_PR138_FORBIDDEN_AUTHORITY_CREATED: {flag}")

    state = _mapping(pr137r.get("atomicrows_validation_state"))
    inventory_state = _mapping(pr137r.get("atomicrows_artifact_inventory"))
    if state.get("row_count_value") != c.EXPECTED_BUNDLE_ROW_COUNT:
        failures.append("PR140_PR137R_ROW_COUNT_NOT_4183")
    if inventory_state.get("row_family_source_file_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR140_PR137R_ROW_FAMILY_SOURCE_COUNT_NOT_15")
    not_created = _mapping(pr137r.get("not_created_flags"))
    for key, value in not_created.items():
        if value is not False:
            failures.append(f"PR140_PR137R_FORBIDDEN_AUTHORITY_CREATED: {key}")

    source_manifest = _mapping(pr139_manifest.get("row_family_source_manifest"))
    if pr139_report.get("source_manifest_entry_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR140_PR139_SOURCE_MANIFEST_ENTRY_COUNT_NOT_15")
    if pr139_report.get("row_family_source_file_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR140_PR139_ROW_FAMILY_SOURCE_FILE_COUNT_NOT_15")
    if source_manifest.get("manifest_entry_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR140_PR139_SOURCE_MANIFEST_ENTRY_COUNT_NOT_15")
    if source_manifest.get("row_family_source_file_count") != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR140_PR139_ROW_FAMILY_SOURCE_FILE_COUNT_NOT_15")
    for key in (
        "semantic_value_materialization_allowed_flag",
        "final_readiness_created_flag",
        "runtime_live_order_authority_created_flag",
        "source_acceptance_created_flag",
        "connector_semantic_binding_created_flag",
        "replay_paper_execution_created_flag",
        "quantum_backend_execution_created_flag",
        "profit_latency_execution_superiority_claim_created_flag",
    ):
        if pr139_manifest.get(key) is not False:
            failures.append(f"PR140_PR139_FORBIDDEN_AUTHORITY_CREATED: {key}")
    if pr139_report.get("final_ready") is not False:
        failures.append("PR140_PR139_FINAL_READY_CLAIMED")

    if set(_string_list(market_index.get("market_scopes"))) and False:
        failures.append("PR140_UNREACHABLE_MARKET_SCOPE_TYPE_FAILURE")
    market_scope_ids = {
        str(row.get("canonical_venue_id"))
        for row in _list(market_index.get("market_scopes"))
        if isinstance(row, Mapping)
    }
    if market_scope_ids != set(c.MARKET_SCOPE_IDS):
        failures.append("PR140_PR136_MARKET_SCOPE_SET_MISMATCH")
    if agent_map.get("current_agent_authority_escalation_created") is not False:
        failures.append("PR140_PR136_AGENT_AUTHORITY_ESCALATION_CREATED")
    if quantum_map.get("no_quantum_execution_flag") is not True:
        failures.append("PR140_PR136_QUANTUM_NO_EXECUTION_FLAG_MISSING")
    if quantum_map.get("no_quantum_advantage_claim_flag") is not True:
        failures.append("PR140_PR136_QUANTUM_ADVANTAGE_CLAIMED")
    if quantum_map.get("no_quantum_optimizer_input_flag") is not True:
        failures.append("PR140_PR136_QUANTUM_OPTIMIZER_INPUT_CREATED")
    if quantum_map.get("future_owner_authorization_required_for_materialization_flag") is not True:
        failures.append("PR140_PR136_OWNER_AUTHORIZATION_NOT_REQUIRED")
    if sequence.get("future_pr_sequence_auto_authorizes_implementation") is not False:
        failures.append("PR140_PR136_SEQUENCE_AUTO_AUTHORIZES_IMPLEMENTATION")
    if sequence.get("future_pr_sequence_auto_authorizes_live_trading") is not False:
        failures.append("PR140_PR136_SEQUENCE_AUTO_AUTHORIZES_LIVE_TRADING")
    return sorted(set(failures))


def _validate_false_authority_boundaries(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    boundaries = _mapping(payload.get("authority_boundaries"))
    if dict(boundaries) != c.AUTHORITY_BOUNDARIES:
        failures.append("PR140_AUTHORITY_BOUNDARY_REGISTRY_MISMATCH")
    for path, key, item in _walk(payload):
        if key in c.AUTHORITY_BOUNDARIES and item is not False:
            failures.append(f"PR140_AUTHORITY_BOUNDARY_TRUE: {path}")
        if key.endswith("_created") and not key.startswith("no_") and item is True:
            failures.append(f"PR140_AUTHORITY_CREATED_TRUE: {path}")
        if key.endswith("_claimed") and item is True:
            failures.append(f"PR140_AUTHORITY_CLAIMED_TRUE: {path}")
    return failures


def _validate_no_forbidden_integrity_or_sidecar(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk(payload):
        lowered_key = key.lower()
        if lowered_key in c.FORBIDDEN_INTEGRITY_AUTHORITY_KEYS:
            failures.append(f"PR140_QTT_INTEGRITY_AUTHORITY_FORBIDDEN: {path}")
        if any(fragment in lowered_key for fragment in ("_digest", "_hash", "_checksum")):
            failures.append(f"PR140_BUNDLE_SIDECAR_OR_INTEGRITY_FIELD_FORBIDDEN: {path}")
        if isinstance(item, str):
            lowered_value = item.lower()
            for fragment in c.FORBIDDEN_BUNDLE_SIDECAR_FRAGMENTS:
                if fragment.lower() in lowered_value:
                    failures.append(f"PR140_BUNDLE_SIDECAR_REFERENCE_FORBIDDEN: {path}")
            for fragment in c.FORBIDDEN_INTEGRITY_AUTHORITY_KEYS:
                if fragment.lower() in lowered_value:
                    failures.append(f"PR140_QTT_INTEGRITY_AUTHORITY_FORBIDDEN: {path}")
    return failures


def _validate_coverage_model(
    plan: Mapping[str, Any],
    *,
    inventory: Mapping[str, Any],
    pr139_manifest: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    expected_field_ids = _field_ids(inventory)
    expected_group_ids = _group_ids(inventory)
    expected_source_paths = _source_paths(pr139_manifest)
    field_entries = [
        field for field in _list(plan.get("field_coverage")) if isinstance(field, Mapping)
    ]
    field_ids = [str(field.get("field_id")) for field in field_entries]
    if len(field_ids) != c.EXPECTED_REQUIRED_FIELD_COUNT:
        failures.append("PR140_FIELD_COVERAGE_COUNT_NOT_59")
    if len(field_ids) != len(set(field_ids)):
        failures.append("PR140_DUPLICATE_FIELD_COVERAGE")
    missing_fields = sorted(set(expected_field_ids) - set(field_ids))
    unknown_fields = sorted(set(field_ids) - set(expected_field_ids))
    if missing_fields:
        failures.append(f"PR140_REQUIRED_FIELD_MISSING: {','.join(missing_fields)}")
    if unknown_fields:
        failures.append(f"PR140_UNKNOWN_FIELD_ID: {','.join(unknown_fields)}")
    for field in field_entries:
        field_id = str(field.get("field_id"))
        if field.get("field_group_id") not in expected_group_ids:
            failures.append(f"PR140_UNKNOWN_FIELD_GROUP_ID: {field_id}")
        if field.get("required_flag") is not True:
            failures.append(f"PR140_REQUIRED_FLAG_NOT_TRUE: {field_id}")
        if field.get("value_materialization_status") != "NOT_MATERIALIZED_BY_PR140":
            failures.append(f"PR140_SEMANTIC_VALUE_MATERIALIZED: {field_id}")
        for key in (
            "external_fact_authority_created",
            "live_use_allowed_created",
            "order_authority_created",
            "profit_evidence_created",
            "quantum_backend_execution_allowed_created",
            "field_is_hot_path_input",
        ):
            if field.get(key) is not False:
                failures.append(f"PR140_FIELD_AUTHORITY_TRUE: {field_id}.{key}")
        if field.get("planned_row_family_source_paths") != expected_source_paths:
            failures.append(f"PR140_FIELD_SOURCE_LOCI_MISMATCH: {field_id}")
        if field.get("planned_enrichment_locus") != expected_source_paths:
            failures.append(f"PR140_FIELD_SOURCE_LOCI_MISMATCH: {field_id}")
    row_id_entries = [field for field in field_entries if field.get("field_id") == "row_id"]
    if not row_id_entries or row_id_entries[0].get("coverage_status") != "PRESENT_EXISTING_ID_ONLY":
        failures.append("PR140_ROW_ID_NOT_PRESENT_EXISTING_ONLY")
    present_fields = [
        field.get("field_id")
        for field in field_entries
        if field.get("coverage_status") == "PRESENT_EXISTING_ID_ONLY"
    ]
    if present_fields != ["row_id"]:
        failures.append("PR140_PRESENT_EXISTING_FIELDS_NOT_ROW_ID_ONLY")
    if len([field for field in field_entries if field.get("coverage_status") != "PRESENT_EXISTING_ID_ONLY"]) != 58:
        failures.append("PR140_MISSING_OR_PLANNED_FIELD_COUNT_NOT_58")

    group_entries = [
        group for group in _list(plan.get("field_group_coverage")) if isinstance(group, Mapping)
    ]
    group_ids = [str(group.get("field_group_id")) for group in group_entries]
    if set(group_ids) != set(expected_group_ids) or len(group_ids) != c.EXPECTED_REQUIRED_FIELD_GROUP_COUNT:
        failures.append("PR140_FIELD_GROUP_COVERAGE_MISMATCH")
    grouped = _fields_by_group(inventory)
    for group in group_entries:
        group_id = str(group.get("field_group_id"))
        expected_fields = grouped.get(group_id, [])
        if group.get("required_field_ids") != expected_fields:
            failures.append(f"PR140_GROUP_FIELD_IDS_MISMATCH: {group_id}")
        if group.get("required_field_count") != len(expected_fields):
            failures.append(f"PR140_GROUP_FIELD_COUNT_MISMATCH: {group_id}")
        if group.get("covered_field_count") != len(expected_fields):
            failures.append(f"PR140_GROUP_COVERED_FIELD_COUNT_MISMATCH: {group_id}")
        if group.get("semantic_values_materialized") is not False:
            failures.append(f"PR140_GROUP_VALUES_MATERIALIZED: {group_id}")
        if group.get("coverage_plan_complete") is not True:
            failures.append(f"PR140_GROUP_PLAN_INCOMPLETE: {group_id}")
        if group.get("no_authority_created") is not True:
            failures.append(f"PR140_GROUP_AUTHORITY_CREATED: {group_id}")

    source_entries = [
        source
        for source in _list(plan.get("row_family_source_coverage"))
        if isinstance(source, Mapping)
    ]
    source_paths = [str(source.get("row_family_source_file_path")) for source in source_entries]
    if len(source_paths) != c.EXPECTED_ROW_FAMILY_SOURCE_FILE_COUNT:
        failures.append("PR140_ROW_FAMILY_SOURCE_COVERAGE_COUNT_NOT_15")
    if set(source_paths) != set(expected_source_paths):
        failures.append("PR140_UNKNOWN_OR_MISSING_ROW_FAMILY_SOURCE")
    for source in source_entries:
        source_path = str(source.get("row_family_source_file_path"))
        if source.get("mutation_allowed_by_pr140") is not False:
            failures.append(f"PR140_SOURCE_MUTATION_ALLOWED: {source_path}")
        if source.get("semantic_values_materialized_by_pr140") is not False:
            failures.append(f"PR140_SOURCE_VALUES_MATERIALIZED: {source_path}")
        if source.get("future_enrichment_only") is not True:
            failures.append(f"PR140_SOURCE_NOT_FUTURE_ENRICHMENT_ONLY: {source_path}")
        if source.get("planned_field_ids") != expected_field_ids:
            failures.append(f"PR140_SOURCE_FIELD_IDS_MISMATCH: {source_path}")
        if source.get("planned_field_group_ids") != expected_group_ids:
            failures.append(f"PR140_SOURCE_GROUP_IDS_MISMATCH: {source_path}")
    return sorted(set(failures))


def _validate_market_agent_latency_quantum_downstream(plan: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    market = _mapping(plan.get("market_scope_coverage"))
    market_scopes = [
        scope for scope in _list(market.get("market_scopes")) if isinstance(scope, Mapping)
    ]
    scope_ids = [str(scope.get("scope_id")) for scope in market_scopes]
    if set(scope_ids) != set(c.MARKET_SCOPE_IDS) or len(scope_ids) != len(c.MARKET_SCOPE_IDS):
        failures.append("PR140_MARKET_SCOPE_COVERAGE_MISSING")
    for scope in market_scopes:
        for key in (
            "external_fact_authority_created",
            "connector_binding_created",
            "live_use_allowed_created",
        ):
            if scope.get(key) is not False:
                failures.append(f"PR140_MARKET_SCOPE_AUTHORITY_CREATED: {scope.get('scope_id')}.{key}")

    agent = _mapping(plan.get("agent_orchestration_coverage"))
    if agent.get("current_agent_authority_escalation_created") is not False:
        failures.append("PR140_AGENT_AUTHORITY_ESCALATION_CREATED")
    for domain in _list(agent.get("agent_domains")):
        if not isinstance(domain, Mapping):
            failures.append("PR140_AGENT_DOMAIN_MALFORMED")
            continue
        if domain.get("may_consume_pr140_plan_as_static_metadata") is not True:
            failures.append(f"PR140_AGENT_STATIC_METADATA_CONSUMPTION_FALSE: {domain.get('agent_domain_id')}")
        for key in (
            "live_order_authority_allowed",
            "latency_hot_path_allowed",
            "final_order_submission_authority_created",
        ):
            if domain.get(key) is not False:
                failures.append(f"PR140_AGENT_AUTHORITY_CREATED: {domain.get('agent_domain_id')}.{key}")

    latency = _mapping(plan.get("latency_hot_path_exclusion_matrix"))
    if not latency:
        failures.append("PR140_LATENCY_HOT_PATH_EXCLUSION_MATRIX_MISSING")
    for key, expected in c.LATENCY_HOT_PATH_EXCLUSION_MATRIX.items():
        if latency.get(key) != expected:
            failures.append(f"PR140_LATENCY_HOT_PATH_FLAG_MISMATCH: {key}")

    quantum = _mapping(plan.get("quantum_forward_metadata_plan"))
    if not quantum:
        failures.append("PR140_QUANTUM_FORWARD_METADATA_PLAN_MISSING")
    for key in (
        "no_quantum_execution_flag",
        "no_quantum_advantage_claim_flag",
        "no_quantum_signal_creation_flag",
        "quantum_metadata_only",
        "quantum_backend_execution_allowed_flag_forced_false",
    ):
        if quantum.get(key) is not True:
            failures.append(f"PR140_QUANTUM_NO_EXECUTION_FLAG_MISMATCH: {key}")
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
            failures.append(f"PR140_QUANTUM_REFERENCE_MISSING: {key}")

    downstream = _mapping(plan.get("downstream_handoff_contract"))
    if downstream.get("pr140_creates_downstream_input_for") != ["PR141", "PR142"]:
        failures.append("PR140_DOWNSTREAM_HANDOFF_TARGETS_MISMATCH")
    if downstream.get("downstream_scope_not_authorized_by_pr140") != list(
        c.DOWNSTREAM_SCOPE_NOT_AUTHORIZED_BY_PR140
    ):
        failures.append("PR140_DOWNSTREAM_SCOPE_NOT_AUTHORIZED_MISMATCH")
    if downstream.get("downstream_owner_authorization_required_for_materialization") is not True:
        failures.append("PR140_DOWNSTREAM_OWNER_AUTHORIZATION_NOT_REQUIRED")
    if downstream.get("no_same_number_identity_inference") is not True:
        failures.append("PR140_SAME_NUMBER_IDENTITY_INFERENCE_USED")
    return sorted(set(failures))


def validate_plan_payload(
    plan: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    inventory: Mapping[str, Any],
    pr139_manifest: Mapping[str, Any],
) -> list[str]:
    failures = [
        f"PR140_SCHEMA_VALIDATION_FAILED: {failure}"
        for failure in validate_json_schema_subset(dict(plan), dict(schema))
    ]
    expected_identity = {
        "plan_id": c.PLAN_ID,
        "plan_version": c.PLAN_VERSION,
        "pr_id": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "deterministic_output": True,
        "validation_marker": c.SUCCESS_MARKER,
        "semantic_values_materialized": False,
        "final_ready": False,
        "day1_launch_ready": False,
    }
    for key, value in expected_identity.items():
        if plan.get(key) != value:
            failures.append(f"PR140_IDENTITY_OR_BOUNDARY_MISMATCH: {key}")
    failures.extend(_validate_false_authority_boundaries(plan))
    failures.extend(_validate_no_forbidden_integrity_or_sidecar(plan))
    failures.extend(
        _validate_coverage_model(
            plan,
            inventory=inventory,
            pr139_manifest=pr139_manifest,
        )
    )
    failures.extend(_validate_market_agent_latency_quantum_downstream(plan))
    return sorted(set(failures))


def validate_report_payload(report: Mapping[str, Any], expected_report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if dict(report) != dict(expected_report):
        failures.append("PR140_REPORT_STALE_OR_NONDETERMINISTIC")
    for key, value in {
        "report_type": c.REPORT_TYPE,
        "pr_id": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "deterministic_output": True,
        "validation_marker": c.SUCCESS_MARKER,
        "semantic_values_materialized": False,
        "final_ready": False,
        "day1_launch_ready": False,
        "atomicrows_bundle_mutated": False,
        "row_family_sources_mutated": False,
        "master_plan_mutated": False,
    }.items():
        if report.get(key) != value:
            failures.append(f"PR140_REPORT_IDENTITY_OR_BOUNDARY_MISMATCH: {key}")
    failures.extend(_validate_false_authority_boundaries(report))
    failures.extend(_validate_no_forbidden_integrity_or_sidecar(report))
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
        normalized = path.strip().replace("\\", "/")
        if " -> " in normalized:
            normalized = normalized.rsplit(" -> ", 1)[1]
        paths.append(normalized)
    return paths


def _is_ignored_pr140_changed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    tmp_dir, _tmp_glob = c.IGNORED_PR140_CHANGED_PATH_PATTERNS
    return normalized == tmp_dir or normalized.startswith(tmp_dir)


def _branch_allows_pr141_downstream_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 140, allow_repair=False)


def _is_pr141_downstream_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR141_DOWNSTREAM_AUTHORIZATION_GATE_CHANGED_PATHS
        and _branch_allows_pr141_downstream_changed_paths(branch)
    )


def _is_pr142_downstream_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR142_DOWNSTREAM_HANDOFF_READINESS_GATE_CHANGED_PATHS
        and _branch_allows_pr141_downstream_changed_paths(branch)
    )


def _is_pr143_owner_override_currentization_changed_path_for_branch(
    path: str,
    branch: str,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR143_OWNER_GLOBAL_OVERRIDE_CURRENTIZATION_CHANGED_PATHS
        and _branch_allows_pr141_downstream_changed_paths(branch)
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


def _branch_allows_pr152_audit_changed_paths(branch: str) -> bool:
    return is_downstream_roadmap_branch(branch, 147, allow_repair=False)


def _is_pr152_audit_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in pr152_constants.PR152_AUDIT_CHANGED_PATHS
        and _branch_allows_pr152_audit_changed_paths(branch)
    )


def _is_pr141_downstream_changed_path(path: str, repo_root: Path) -> bool:
    branch_context = current_branch_context(repo_root)
    return _is_pr141_downstream_changed_path_for_branch(
        path,
        branch_context.branch,
    ) or _is_pr142_downstream_changed_path_for_branch(
        path,
        branch_context.branch,
    ) or _is_pr143_owner_override_currentization_changed_path_for_branch(
        path,
        branch_context.branch,
    )


def _is_allowed_pr140_changed_path(path: str, repo_root: Path) -> bool:
    normalized = path.replace("\\", "/")
    branch_context = current_branch_context(repo_root)
    return (
        normalized in c.ALLOWED_PR140_CHANGED_PATHS
        or _is_pr141_downstream_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
        or _is_pr142_downstream_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
        or _is_pr143_owner_override_currentization_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
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
        or _is_pr152_audit_changed_path_for_branch(
            normalized,
            branch_context.branch,
        )
    )


def _validate_changed_paths(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR140_GIT_STATUS_UNAVAILABLE")
            continue
        normalized = path.replace("\\", "/")
        if _is_ignored_pr140_changed_path(normalized):
            continue
        if not _is_allowed_pr140_changed_path(normalized, repo_root):
            failures.append(f"PR140_CHANGED_PATH_OUT_OF_SCOPE: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append("PR140_MASTER_PLAN_MUTATION_DETECTED")
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix():
            failures.append("PR140_ATOMICROWS_BUNDLE_MUTATION_DETECTED")
        if normalized.startswith(c.ROW_FAMILY_SOURCE_DIRECTORY.as_posix() + "/"):
            failures.append("PR140_ROW_FAMILY_SOURCE_MUTATION_DETECTED")
        if normalized in {path.as_posix() for path in c.BRANCH_CONTEXT_EVIDENCE_PATHS}:
            failures.append("PR140_BRANCH_CONTEXT_HARDENING_MUTATION_DETECTED")
    return sorted(set(failures))


def validate_repository_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    context, context_failures = _build_context(root)
    failures: list[str] = list(context_failures)
    failures.extend(_validate_evidence_invariants(context, root))

    expected_schema = build_json_schema(root)
    expected_plan = build_plan(root)
    expected_report = build_report(root)
    second_report = build_report(root)
    if expected_report != second_report:
        failures.append("PR140_OUTPUT_NOT_DETERMINISTIC")

    try:
        actual_schema = _read_json(root / c.SCHEMA_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_schema = {}
        failures.append(f"PR140_SCHEMA_INVALID: {c.SCHEMA_PATH.as_posix()}: {exc}")
    if actual_schema and actual_schema != expected_schema:
        failures.append("PR140_SCHEMA_STALE_OR_NONDETERMINISTIC")

    actual_plan, plan_failures = _canonical_plan_from_file(root)
    failures.extend(plan_failures)
    if actual_plan and actual_plan != expected_plan:
        failures.append("PR140_PLAN_STALE_OR_NONDETERMINISTIC")

    try:
        actual_fixture = _read_json(root / c.FIXTURE_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_fixture = {}
        failures.append(f"PR140_FIXTURE_INVALID: {c.FIXTURE_PATH.as_posix()}: {exc}")
    expected_fixture = build_fixture(root)
    if actual_fixture and actual_fixture != expected_fixture:
        failures.append("PR140_FIXTURE_STALE_OR_NONDETERMINISTIC")

    try:
        actual_report = _read_json(root / c.REPORT_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_report = {}
        failures.append(f"PR140_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}")

    if actual_plan:
        failures.extend(
            validate_plan_payload(
                actual_plan,
                expected_schema,
                inventory=context["pr138_inventory"],
                pr139_manifest=context["pr139_manifest"],
            )
        )
    if actual_report:
        failures.extend(validate_report_payload(actual_report, expected_report))
    if actual_fixture:
        failures.extend(
            [
                f"PR140_FIXTURE_SCHEMA_VALIDATION_FAILED: {failure}"
                for failure in validate_json_schema_subset(actual_fixture, expected_schema)
            ]
        )
        failures.extend(_validate_no_forbidden_integrity_or_sidecar(actual_fixture))
    failures.extend(_validate_changed_paths(root))
    return sorted(set(failures))


def write_schema_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    schema = build_json_schema(root)
    _write_text(root / c.SCHEMA_PATH, json_dump(schema))
    return schema


def write_plan_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    plan = build_plan(root)
    _write_text(root / c.PLAN_PATH, yaml_dump(plan))
    return plan


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
        "plan": write_plan_file(repo_root),
        "report": write_report_file(repo_root),
        "fixture": write_fixture_file(repo_root),
    }
