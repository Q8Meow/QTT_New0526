"""Deterministic report builder and validator for PR149."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools.ci_branch_context import current_branch_context, is_pr_or_later_branch

from . import constants as c


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(_read_text(path))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _read_required_text(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> str:
    path = root / rel_path
    if not path.exists():
        failures.append(f"{c.REASON_CODES[1]}: {key}: {rel_path.as_posix()}")
        return ""
    try:
        return _read_text(path)
    except OSError as exc:
        failures.append(f"{c.REASON_CODES[2]}: {key}: {rel_path.as_posix()}: {exc}")
        return ""


def _read_required_json(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists():
        failures.append(f"{c.REASON_CODES[1]}: {key}: {rel_path.as_posix()}")
        return {}
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"{c.REASON_CODES[2]}: {key}: {rel_path.as_posix()}: {exc}")
        return {}


def _read_optional_json(root: Path, rel_path: Path, failures: list[str]) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists():
        return {}
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"{c.REASON_CODES[2]}: optional: {rel_path.as_posix()}: {exc}")
        return {}


def _read_optional_text(root: Path, rel_path: Path, failures: list[str]) -> str:
    path = root / rel_path
    if not path.exists():
        return ""
    try:
        return _read_text(path)
    except OSError as exc:
        failures.append(f"{c.REASON_CODES[2]}: optional: {rel_path.as_posix()}: {exc}")
        return ""


def _sorted_strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted(str(value) for value in values if isinstance(value, str))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _path_records(paths: Sequence[Path], present: set[str]) -> list[dict[str, Any]]:
    records = []
    for path in paths:
        path_text = path.as_posix()
        records.append(
            {
                "artifact_path": path_text,
                "consumed": path_text in present,
                "required": True,
            }
        )
    return sorted(records, key=lambda item: item["artifact_path"])


def _optional_path_records(paths: Sequence[Path], present: set[str]) -> list[dict[str, Any]]:
    records = []
    for path in paths:
        path_text = path.as_posix()
        records.append(
            {
                "artifact_path": path_text,
                "consumed": path_text in present,
                "required": False,
            }
        )
    return sorted(records, key=lambda item: item["artifact_path"])


def _crosswalk_payload(root: Path, failures: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    alias_path = root / c.PR136_SECTION_CROSSWALK_ALIAS_PATH
    canonical_path = root / c.PR136_SECTION_CROSSWALK_CANONICAL_PATH
    alias_exists = alias_path.exists()
    canonical_exists = canonical_path.exists()
    selected = c.PR136_SECTION_CROSSWALK_ALIAS_PATH if alias_exists else c.PR136_SECTION_CROSSWALK_CANONICAL_PATH
    if not alias_exists and not canonical_exists:
        failures.append(
            f"{c.REASON_CODES[1]}: pr136_section_crosswalk_or_alias: "
            f"{c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix()}"
        )
        return {}, {
            "alias_used": False,
            "canonical_successor_used": False,
            "created_missing_alias": False,
            "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
            "selected_path": c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix(),
        }
    payload = _read_required_json(root, "pr136_section_crosswalk_or_alias", selected, failures)
    return payload, {
        "alias_used": alias_exists,
        "canonical_successor_used": not alias_exists and canonical_exists,
        "created_missing_alias": False,
        "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
        "selected_path": selected.as_posix(),
    }


def load_static_evidence(repo_root: Path | str) -> tuple[dict[str, Any], list[str]]:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    present: set[str] = set()

    text_inputs = {
        "launch_roadmap": c.ROADMAP_PATH,
        "launch_roadmap_policy": c.ROADMAP_POLICY_PATH,
    }
    json_inputs = {
        "control_plane_roster": c.ROSTER_PATH,
        "control_plane_controller": c.CONTROLLER_PATH,
        "pr136_route_triage": c.PR136_ROUTE_TRIAGE_PATH,
        "pr136_market_index": c.PR136_MARKET_INDEX_PATH,
        "pr136_command_matrix": c.PR136_COMMAND_MATRIX_PATH,
        "pr137r_reconciliation": c.PR137R_REPORT_PATH,
        "pr138_semantic_contract": c.PR138_REPORT_PATH,
        "pr139_row_family_manifest": c.PR139_REPORT_PATH,
        "pr140_field_coverage": c.PR140_REPORT_PATH,
        "pr141_owner_authorization": c.PR141_REPORT_PATH,
        "pr142_handoff_readiness": c.PR142_REPORT_PATH,
    }
    text_payloads: dict[str, str] = {}
    json_payloads: dict[str, dict[str, Any]] = {}

    for key, rel_path in text_inputs.items():
        text_payloads[key] = _read_required_text(root, key, rel_path, failures)
        if text_payloads[key]:
            present.add(rel_path.as_posix())
    for key, rel_path in json_inputs.items():
        json_payloads[key] = _read_required_json(root, key, rel_path, failures)
        if json_payloads[key]:
            present.add(rel_path.as_posix())

    crosswalk, alias_resolution = _crosswalk_payload(root, failures)
    json_payloads["pr136_section_crosswalk_or_alias"] = crosswalk
    if crosswalk:
        present.add(str(alias_resolution["selected_path"]))

    optional_payloads: dict[str, Any] = {}
    for rel_path in (
        c.PR136_AGENT_MAP_PATH,
        c.PR136_SEQUENCE_PATH,
        c.PR136_QUANTUM_MAP_PATH,
        c.PR138_FIELD_INVENTORY_PATH,
        c.PR143_REPORT_PATH,
    ):
        payload = _read_optional_json(root, rel_path, failures)
        optional_payloads[rel_path.as_posix()] = payload
        if payload:
            present.add(rel_path.as_posix())
    source_packet = _read_optional_text(root, c.OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH, failures)
    optional_payloads[c.OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH.as_posix()] = source_packet
    if source_packet:
        present.add(c.OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH.as_posix())

    evidence = {
        "repo_root": root,
        "json_payloads": json_payloads,
        "text_payloads": text_payloads,
        "optional_payloads": optional_payloads,
        "alias_resolution": alias_resolution,
        "present_paths": present,
    }
    return evidence, sorted(set(failures))


def _field_group_by_field(pr140: Mapping[str, Any]) -> dict[str, str]:
    groups: dict[str, str] = {}
    for group in _list(pr140.get("field_group_coverage")):
        if not isinstance(group, Mapping):
            continue
        group_id = str(group.get("field_group_id", "UNRESOLVED"))
        for field_id in _sorted_strings(group.get("required_field_ids")):
            groups[field_id] = group_id
    return groups


def _row_family_source_ids(pr140: Mapping[str, Any]) -> list[str]:
    ids = []
    for row_family in _list(pr140.get("row_family_source_coverage")):
        if isinstance(row_family, Mapping) and isinstance(row_family.get("row_family_source_id"), str):
            ids.append(row_family["row_family_source_id"])
    return sorted(set(ids))


def _market_scope_ids(pr140: Mapping[str, Any]) -> list[str]:
    coverage = _mapping(pr140.get("market_scope_coverage"))
    ids = []
    for scope in _list(coverage.get("market_scopes")):
        if isinstance(scope, Mapping) and isinstance(scope.get("scope_id"), str):
            ids.append(scope["scope_id"])
    return sorted(set(ids))


def _field_ids(pr138: Mapping[str, Any]) -> list[str]:
    contract = _mapping(pr138.get("semantic_contract"))
    field_ids = _sorted_strings(contract.get("field_ids"))
    if field_ids:
        return field_ids
    return _sorted_strings(pr138.get("field_ids"))


def _coverage_by_field(pr140: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    coverage = {}
    for item in _list(pr140.get("field_coverage")):
        if isinstance(item, Mapping) and isinstance(item.get("field_id"), str):
            coverage[item["field_id"]] = item
    return coverage


def _ledger_by_field(pr141: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    ledger = {}
    for item in _list(pr141.get("field_authorization_readiness_ledger")):
        if isinstance(item, Mapping) and isinstance(item.get("field_id"), str):
            ledger[item["field_id"]] = item
    return ledger


def _bridge_classification(
    field_id: str,
    coverage: Mapping[str, Any],
) -> tuple[str, str, list[str]]:
    dependency_class = str(coverage.get("dependency_class", "UNRESOLVED"))
    source_class, state, reasons = c.DEPENDENCY_CLASS_TO_BRIDGE.get(
        dependency_class,
        (
            "UNRESOLVED_PENDING_UPSTREAM_VALUE",
            "UNRESOLVED_PENDING_UPSTREAM",
            ("PR149_PR140_FIELD_COVERAGE_REQUIRED",),
        ),
    )
    reason_codes = list(c.FORCED_FALSE_FIELD_REASON_CODES.get(field_id, reasons))
    if field_id == "row_id":
        source_class = "UPSTREAM_STATIC_REPORT_VALUE"
        state = "IMPLEMENTATION_BRIDGE_READY"
        reason_codes = ["PR149_READY"]
    return source_class, state, sorted(set(reason_codes))


def _resolution_rule(value_source_class: str, state: str) -> str:
    if value_source_class == "SOURCE_EVIDENCE_REQUIRED_EXTERNAL_FACT_VALUE":
        return "WAIT_FOR_ACCEPTED_SOURCE_PACKET"
    if value_source_class == "RUNTIME_RECEIPT_REQUIRED_VALUE":
        return "WAIT_FOR_RUNTIME_OR_RESULT_RECEIPT"
    if value_source_class == "QUANTUM_FORWARD_METADATA_VALUE":
        return "METADATA_ONLY_NO_EXECUTION"
    if state == "CONFIGURATION_READY_WITH_TYPED_LIMITS":
        return "USE_STATIC_UPSTREAM_POLICY_WITH_NO_RUNTIME_AUTHORITY"
    if state == "IMPLEMENTATION_BRIDGE_READY":
        return "USE_STATIC_UPSTREAM_REPORT_METADATA"
    return "WAIT_FOR_TYPED_UPSTREAM_INPUT"


def _consumer_classes(field_id: str, value_source_class: str) -> list[str]:
    classes = {"STATIC_METADATA_CONSUMER_ONLY", "ATOMICROWS_COMPILER_MATERIALIZATION_AGENT_CLASS"}
    if value_source_class == "QUANTUM_FORWARD_METADATA_VALUE" or field_id.startswith("quantum_"):
        classes.add("QUANTUM_OPTIMIZER_METADATA_SURFACE")
    if field_id in {"replay_required_flag", "paper_required_flag", "owner_review_required_flag"}:
        classes.add("REPLAY_PAPER_CANDIDATE_PREPARATION_SURFACE")
    if field_id in {"market_scope", "prediction_market_scope"}:
        classes.add("PARAMETER_STACK_SELECTION_SURFACE")
    return sorted(classes)


def _materialization_items(
    pr138: Mapping[str, Any],
    pr140: Mapping[str, Any],
    pr141: Mapping[str, Any],
) -> list[dict[str, Any]]:
    fields = _field_ids(pr138)
    groups = _field_group_by_field(pr140)
    row_family_ids = _row_family_source_ids(pr140)
    market_scope_ids = _market_scope_ids(pr140)
    coverage = _coverage_by_field(pr140)
    ledger = _ledger_by_field(pr141)
    items = []
    for field_id in fields:
        coverage_item = coverage.get(field_id, {})
        source_class, state, reason_codes = _bridge_classification(field_id, coverage_item)
        items.append(
            {
                "deterministic_resolution_rule": _resolution_rule(source_class, state),
                "downstream_consumer_agent_classes": _consumer_classes(field_id, source_class),
                "evidence_boundary": {
                    "accepted_source_packet_required": (
                        source_class == "SOURCE_EVIDENCE_REQUIRED_EXTERNAL_FACT_VALUE"
                    ),
                    "materialized_value_created": False,
                    "runtime_or_result_receipt_required": (
                        source_class == "RUNTIME_RECEIPT_REQUIRED_VALUE"
                    ),
                    "static_upstream_only": True,
                },
                "future_consumer_notes": [
                    "CONSUME_AS_STATIC_BRIDGE_METADATA",
                    "DO_NOT_TREAT_AS_ROW_VALUE_WRITE",
                ],
                "market_scope": {
                    "scope_ids": market_scope_ids,
                    "scope_status": "USE_MARKET_SURFACE_FOR_EXTERNAL_FACT_LIMITS",
                },
                "materialization_state": state,
                "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
                "quantum_forward_metadata": {
                    "execution_evidence_pending": True,
                    "metadata_only": source_class == "QUANTUM_FORWARD_METADATA_VALUE",
                    "quantum_forward_state": c.QUANTUM_FORWARD_STATE,
                },
                "reason_codes": reason_codes,
                "row_family_ref": {
                    "ref_set_class": "ALL_PR139_ROW_FAMILY_SOURCE_IDS",
                    "row_family_source_ids": row_family_ids,
                    "scope_unresolved": not bool(row_family_ids),
                },
                "semantic_field_ref": {
                    "coverage_status": coverage_item.get("coverage_status", "UNRESOLVED"),
                    "field_group_id": groups.get(field_id, "UNRESOLVED"),
                    "field_id": field_id,
                    "pr141_state": ledger.get(field_id, {}).get(
                        "owner_authorization_readiness_state",
                        "UNRESOLVED",
                    ),
                },
                "semantic_item_id": f"PR149_FIELD_{field_id.upper()}",
                "value_source_class": source_class,
            }
        )
    return sorted(items, key=lambda item: item["semantic_item_id"])


def _agent_surface(agent_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    upstream_agents = {
        str(agent.get("agent_domain_id")): agent
        for agent in _list(agent_map.get("agent_domains"))
        if isinstance(agent, Mapping) and isinstance(agent.get("agent_domain_id"), str)
    }
    candidate_classes = (
        ("atomicrows_agent", "ATOMICROWS_COMPILER_MATERIALIZATION_AGENT_CLASS"),
        ("parameter_stack_agent", "PARAMETER_STACK_SELECTION_SURFACE"),
        ("replay_agent", "REPLAY_PAPER_CANDIDATE_PREPARATION_SURFACE"),
        ("paper_agent", "REPLAY_PAPER_CANDIDATE_PREPARATION_SURFACE"),
        ("dashboard_agent", "OWNER_DASHBOARD_READ_ONLY_CONFIGURATION_SURFACE"),
        ("quantum_optimizer_agent", "QUANTUM_OPTIMIZER_METADATA_SURFACE"),
    )
    rows = []
    for agent_id, surface_class in candidate_classes:
        upstream = upstream_agents.get(agent_id, {})
        rows.append(
            {
                "agent_ref": agent_id,
                "downstream_agent_surface_class": surface_class,
                "materialization_state": (
                    "CONFIGURATION_READY_WITH_TYPED_LIMITS"
                    if upstream
                    else "UNRESOLVED_PENDING_UPSTREAM"
                ),
                "may_consume_pr149_static_metadata": bool(upstream),
                "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
                "reason_codes": ["PR149_READY"] if upstream else ["PR149_AGENT_SURFACE_UNRESOLVED"],
                "surface_authority": {
                    "connector_semantic_authority_granted": False,
                    "external_fact_authority_granted": False,
                    "live_reachability_granted": False,
                    "order_authority_granted": False,
                    "runtime_cash_authority_granted": False,
                },
            }
        )
    return sorted(rows, key=lambda item: item["agent_ref"])


def _market_surface(market_index: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for scope in _list(market_index.get("market_scopes")):
        if not isinstance(scope, Mapping):
            continue
        rows.append(
            {
                "canonical_venue_id": scope.get("canonical_venue_id"),
                "market_scope_id": scope.get("market_scope_id"),
                "materialization_state": "BLOCKED_EXTERNAL_FACT_REQUIRED",
                "missing_source_evidence_classes": _sorted_strings(
                    scope.get("missing_accepted_source_evidence_classes")
                ),
                "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
                "reason_codes": ["PR149_EXTERNAL_FACT_EVIDENCE_REQUIRED"],
                "venue_specific_value_created": False,
            }
        )
    return sorted(rows, key=lambda item: str(item["canonical_venue_id"]))


def _counts_by_state(items: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {state: 0 for state in c.MATERIALIZATION_STATE_VALUES}
    for item in items:
        state = str(item.get("materialization_state"))
        counts[state] = counts.get(state, 0) + 1
    return {key: counts[key] for key in sorted(counts) if counts[key]}


def _build_payload(evidence: Mapping[str, Any]) -> dict[str, Any]:
    payloads = _mapping(evidence["json_payloads"])
    optional = _mapping(evidence["optional_payloads"])
    pr136_route = _mapping(payloads.get("pr136_route_triage"))
    pr136_crosswalk = _mapping(payloads.get("pr136_section_crosswalk_or_alias"))
    pr136_market = _mapping(payloads.get("pr136_market_index"))
    pr136_command = _mapping(payloads.get("pr136_command_matrix"))
    pr137r = _mapping(payloads.get("pr137r_reconciliation"))
    pr138 = _mapping(payloads.get("pr138_semantic_contract"))
    pr139 = _mapping(payloads.get("pr139_row_family_manifest"))
    pr140 = _mapping(payloads.get("pr140_field_coverage"))
    pr141 = _mapping(payloads.get("pr141_owner_authorization"))
    pr142 = _mapping(payloads.get("pr142_handoff_readiness"))
    pr136_agent = _mapping(optional.get(c.PR136_AGENT_MAP_PATH.as_posix()))
    pr136_quantum = _mapping(optional.get(c.PR136_QUANTUM_MAP_PATH.as_posix()))
    pr143 = _mapping(optional.get(c.PR143_REPORT_PATH.as_posix()))
    present = set(evidence["present_paths"])
    materialization_items = _materialization_items(pr138, pr140, pr141)

    return {
        "atomicrows_compatibility_surface": {
            "bridge_to_future_materialization_only": True,
            "bundle_authority_created": False,
            "bundle_mutation_created": False,
            "generated_derivative_report_is_bundle_row_authority": False,
            "pr137r_consumed": bool(pr137r),
            "pr138_consumed": bool(pr138),
            "qtt_integrity_authority_created": False,
            "row_bundle_authority_created": False,
        },
        "authority_class": c.AUTHORITY_CLASS,
        "centralized_no_claim_flags": dict(c.NO_CLAIM_FLAGS),
        "centralized_reason_codes": list(c.REASON_CODES),
        "centralized_state_enums": {
            "downstream_agent_surface_class": list(c.DOWNSTREAM_AGENT_SURFACE_CLASS_VALUES),
            "materialization_state": list(c.MATERIALIZATION_STATE_VALUES),
            "value_source_class": list(c.VALUE_SOURCE_CLASS_VALUES),
        },
        "changed_path_guard_summary": {
            "broad_generated_directory_allowance_created": False,
            "broad_roadmap_allowance_created": False,
            "exact_allowance_candidate_count": len(c.CHANGED_PATH_EXACT_ALLOWANCE_CANDIDATES),
            "pr148_narrow_allowance_preserved": True,
        },
        "deterministic_generation_policy": {
            "array_sorting": "STABLE_IDENTIFIER_ASC",
            "dictionary_key_sorting": "JSON_SORT_KEYS_TRUE",
            "machine_local_paths_allowed": False,
            "random_ids_allowed": False,
            "tracked_timestamp_policy": c.STATIC_TIME,
        },
        "deterministic_materialization_bridge_state": {
            "overall_state": c.READINESS_CLASS,
            "reason_codes": ["PR149_READY"],
            "state_counts": _counts_by_state(materialization_items),
        },
        "downstream_agent_configuration_surface": _agent_surface(pr136_agent),
        "hidden_default_guard": {
            "external_fact_value_created": False,
            "hidden_default_created": False,
            "institutional_parameter_value_invented": False,
            "optimizer_parameter_value_invented": False,
            "venue_fact_value_created": False,
        },
        "market_specific_surface": _market_surface(pr136_market),
        "next_consumer_contract": {
            "consumer_contract_id": "PR149_DOWNSTREAM_STATIC_METADATA_CONTRACT",
            "must_preserve_no_claim_flags": True,
            "must_request_future_evidence_for_blocked_items": True,
            "must_treat_materialization_items_as_bridge_metadata_only": True,
            "next_allowed_state": "FUTURE_SCOPED_CONSUMER_PR_REQUIRED",
        },
        "optional_context_inputs": _optional_path_records(c.OPTIONAL_CONTEXT_ARTIFACT_PATHS, present),
        "orchestration_preflight_receipt": {
            "alias_resolution": dict(evidence["alias_resolution"]),
            "all_required_inputs_consumed": all(
                path.as_posix() in present for path in c.ALLOWED_INPUT_ARTIFACT_PATHS
            ),
            "required_input_keys": list(c.REQUIRED_UPSTREAM_ARTIFACT_KEYS),
        },
        "pr136_alignment_summary": {
            "command_action_count": len(_list(pr136_command.get("actions"))),
            "crosswalk_entry_count": pr136_crosswalk.get("coverage_entry_count"),
            "market_scope_count": pr136_market.get("canonical_venue_count"),
            "route_receipt_type": pr136_route.get("receipt_type"),
            "sequence_authority_class": pr136_route.get("sequence_authority_class"),
        },
        "pr137r_alignment_summary": {
            "row_count_proven": _mapping(pr137r.get("atomicrows_validation_state")).get("row_count_proven"),
            "schema_validated": _mapping(pr137r.get("atomicrows_validation_state")).get("schema_validated"),
            "validation_state": pr137r.get("validation_state"),
        },
        "pr138_semantic_contract_summary": {
            "field_count": len(_field_ids(pr138)),
            "field_group_count": _mapping(pr138.get("semantic_contract")).get("required_field_group_count"),
            "semantic_row_contract_defined": pr138.get("semantic_row_contract_defined_by_pr138"),
            "semantic_values_materialized": pr138.get("semantic_row_values_materialized_by_pr138"),
        },
        "pr140_field_coverage_summary": {
            "field_coverage_count": len(_list(pr140.get("field_coverage"))),
            "semantic_values_materialized": pr140.get("semantic_values_materialized"),
            "validation_marker": pr140.get("validation_marker"),
        },
        "pr141_owner_authorization_summary": {
            "materialization_permission_created": pr141.get("materialization_permission_created"),
            "owner_approval_receipt_created": pr141.get("owner_approval_receipt_created"),
            "summary": dict(_mapping(pr141.get("owner_authorization_readiness_summary"))),
            "validation_marker": pr141.get("validation_marker"),
        },
        "pr142_handoff_readiness_summary": {
            "readiness_state": _mapping(pr142.get("static_handoff_readiness_contract")).get("readiness_state"),
            "validation_marker": pr142.get("validation_marker"),
            "value_materialization_still_blocked": _mapping(pr142.get("atomicrows_compatibility")).get(
                "value_materialization_still_blocked"
            ),
        },
        "pr_id": c.PR_ID,
        "pr_title": c.PR_TITLE,
        "quantum_forward_compatibility_surface": {
            "annealing_compatible_metadata_only": True,
            "ising_compatible_metadata_only": True,
            "qaoa_compatible_metadata_only": True,
            "quantum_applicability_metadata_only": True,
            "quantum_execution_evidence_pending": True,
            "quantum_forward_state": c.QUANTUM_FORWARD_STATE,
            "quantum_live_hot_path_excluded": True,
            "quantum_optimizer_candidate_metadata_only": True,
            "qubo_compatible_metadata_only": True,
            "strongest_classical_comparator_required_metadata_only": True,
            "vqe_compatible_metadata_only": True,
            "upstream_pr143_quantum_state": _mapping(
                pr143.get("quantum_forward_compatibility")
            ).get("quantum_planning_state"),
            "upstream_quantum_evidence_status": pr136_quantum.get("quantum_evidence_status"),
        },
        "readiness_class": c.READINESS_CLASS,
        "replay_paper_live_exclusion_surface": {
            "live_reachability_created": False,
            "order_execution_created": False,
            "paper_execution_created": False,
            "replay_execution_created": False,
            "static_configuration_only": True,
        },
        "report_id": c.REPORT_ID,
        "report_version": c.REPORT_VERSION,
        "semantic_value_materialization_packet": {
            "materialization_items": materialization_items,
            "packet_authority_class": c.AUTHORITY_CLASS,
            "packet_id": "PR149_SEMANTIC_VALUE_MATERIALIZATION_PACKET",
            "packet_readiness_class": c.READINESS_CLASS,
            "packet_version": c.REPORT_VERSION,
            "row_family_scope": {
                "row_family_source_ids": _row_family_source_ids(pr140),
                "source_artifact_ref": c.PR140_REPORT_PATH.as_posix(),
            },
            "semantic_field_scope": {
                "field_ids": _field_ids(pr138),
                "source_artifact_ref": c.PR138_REPORT_PATH.as_posix(),
            },
            "source_artifact_refs": [
                path.as_posix() for path in c.ALLOWED_INPUT_ARTIFACT_PATHS
            ],
        },
        "source_evidence_boundary_surface": {
            "accepted_source_packet_created": False,
            "connector_semantic_authority_created": False,
            "external_fact_value_created": False,
            "owner_source_policy_packet_present": bool(
                optional.get(c.OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH.as_posix())
            ),
            "policy_context_only": True,
            "runtime_cash_receipt_created": False,
        },
        "upstream_artifact_inputs": _path_records(c.ALLOWED_INPUT_ARTIFACT_PATHS, present),
        "validation_summary": {
            "build_report_byte_stable": True,
            "default_validation_mutates_tracked_report": False,
            "explicit_report_write_mode_supported": True,
            "tracked_report_path": c.REPORT_PATH.as_posix(),
        },
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    evidence, failures = load_static_evidence(repo_root)
    if failures:
        raise ValueError("\n".join(failures))
    return _build_payload(evidence)


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _false_flag_failures(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    flags = payload.get("centralized_no_claim_flags")
    if dict(flags if isinstance(flags, Mapping) else {}) != dict(c.NO_CLAIM_FLAGS):
        failures.append("PR149_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED")
    for key, value in _mapping(flags).items():
        if value is not False:
            failures.append(f"PR149_FORBIDDEN_FLAG_TRUE: {key}")
    return failures


def _sidecar_reference_failures(payload: Mapping[str, Any]) -> list[str]:
    compatibility = _mapping(payload.get("atomicrows_compatibility_surface"))
    bundle_authority_fields = (
        "bundle_authority_created",
        "bundle_mutation_created",
        "generated_derivative_report_is_bundle_row_authority",
        "row_bundle_authority_created",
    )
    if any(compatibility.get(field) is not False for field in bundle_authority_fields):
        return ["PR149_NO_BUNDLE_MUTATION_AUTHORITY"]
    if compatibility.get("qtt_integrity_authority_created") is not False:
        return ["PR149_NO_QTT_INTEGRITY_AUTHORITY"]

    forbidden_path = _forbidden_bundle_sidecar_path()
    for key, value in _walk(payload):
        if not _is_path_like_report_field(key):
            continue
        if _contains_forbidden_path(value, forbidden_path):
            return ["PR149_NO_BUNDLE_MUTATION_AUTHORITY"]
    return []


def _forbidden_bundle_sidecar_path() -> str:
    return c.ATOMICROWS_BUNDLE_PATH.with_suffix("." + "sha" + "256").as_posix()


def _is_path_like_report_field(key: str) -> bool:
    return (
        key == "artifact_path"
        or key.endswith("_path")
        or key.endswith("_paths")
        or key.endswith("_ref")
        or key.endswith("_refs")
    )


def _contains_forbidden_path(value: Any, forbidden_path: str) -> bool:
    if isinstance(value, str):
        return value.replace("\\", "/") == forbidden_path
    if isinstance(value, list):
        return any(_contains_forbidden_path(item, forbidden_path) for item in value)
    return False


def validate_report_payload(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    required_top_level = (
        "report_id",
        "report_version",
        "pr_id",
        "pr_title",
        "authority_class",
        "readiness_class",
        "deterministic_generation_policy",
        "upstream_artifact_inputs",
        "optional_context_inputs",
        "orchestration_preflight_receipt",
        "pr136_alignment_summary",
        "pr137r_alignment_summary",
        "pr138_semantic_contract_summary",
        "pr140_field_coverage_summary",
        "pr141_owner_authorization_summary",
        "pr142_handoff_readiness_summary",
        "deterministic_materialization_bridge_state",
        "semantic_value_materialization_packet",
        "downstream_agent_configuration_surface",
        "market_specific_surface",
        "atomicrows_compatibility_surface",
        "quantum_forward_compatibility_surface",
        "replay_paper_live_exclusion_surface",
        "source_evidence_boundary_surface",
        "centralized_reason_codes",
        "centralized_state_enums",
        "centralized_no_claim_flags",
        "hidden_default_guard",
        "changed_path_guard_summary",
        "validation_summary",
        "next_consumer_contract",
    )
    for key in required_top_level:
        if key not in payload:
            failures.append(f"PR149_REQUIRED_REPORT_KEY_MISSING: {key}")
    if payload.get("report_id") != c.REPORT_ID:
        failures.append("PR149_REPORT_ID_MISMATCH")
    if payload.get("report_version") != c.REPORT_VERSION:
        failures.append("PR149_REPORT_VERSION_MISMATCH")
    if payload.get("pr_id") != c.PR_ID:
        failures.append("PR149_PR_ID_MISMATCH")
    if payload.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append("PR149_AUTHORITY_CLASS_MISMATCH")
    if payload.get("readiness_class") != c.READINESS_CLASS:
        failures.append("PR149_READINESS_CLASS_MISMATCH")
    if payload.get("centralized_reason_codes") != list(c.REASON_CODES):
        failures.append("PR149_REASON_CODES_NOT_CONSTANT_ALIGNED")
    enums = _mapping(payload.get("centralized_state_enums"))
    if enums.get("materialization_state") != list(c.MATERIALIZATION_STATE_VALUES):
        failures.append("PR149_MATERIALIZATION_STATES_NOT_CONSTANT_ALIGNED")
    if enums.get("value_source_class") != list(c.VALUE_SOURCE_CLASS_VALUES):
        failures.append("PR149_VALUE_SOURCE_CLASSES_NOT_CONSTANT_ALIGNED")
    if enums.get("downstream_agent_surface_class") != list(c.DOWNSTREAM_AGENT_SURFACE_CLASS_VALUES):
        failures.append("PR149_AGENT_SURFACE_CLASSES_NOT_CONSTANT_ALIGNED")
    failures.extend(_false_flag_failures(payload))
    failures.extend(_sidecar_reference_failures(payload))

    packet = _mapping(payload.get("semantic_value_materialization_packet"))
    items = _list(packet.get("materialization_items"))
    if not items:
        failures.append("PR149_MATERIALIZATION_ITEMS_MISSING")
    item_ids = [str(item.get("semantic_item_id")) for item in items if isinstance(item, Mapping)]
    if item_ids != sorted(item_ids):
        failures.append("PR149_MATERIALIZATION_ITEMS_NOT_SORTED")
    for item in items:
        if not isinstance(item, Mapping):
            failures.append("PR149_MATERIALIZATION_ITEM_NOT_OBJECT")
            continue
        if item.get("value_source_class") not in c.VALUE_SOURCE_CLASS_VALUES:
            failures.append(f"PR149_VALUE_SOURCE_CLASS_INVALID: {item.get('semantic_item_id')}")
        if item.get("materialization_state") not in c.MATERIALIZATION_STATE_VALUES:
            failures.append(f"PR149_MATERIALIZATION_STATE_INVALID: {item.get('semantic_item_id')}")
        if _mapping(item.get("no_claim_flags")) != c.NO_CLAIM_FLAGS:
            failures.append(f"PR149_ITEM_NO_CLAIM_FLAGS_MISMATCH: {item.get('semantic_item_id')}")
        for reason in _list(item.get("reason_codes")):
            if reason not in c.REASON_CODES:
                failures.append(f"PR149_REASON_CODE_INVALID: {reason}")
    for key, value in _mapping(payload.get("hidden_default_guard")).items():
        if value is not False:
            failures.append(f"PR149_NO_HIDDEN_DEFAULTS: {key}")
    for key, value in _mapping(payload.get("replay_paper_live_exclusion_surface")).items():
        if key.endswith("_created") and value is not False:
            failures.append(f"PR149_RUNTIME_AUTHORITY_CREATED: {key}")
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
    return sorted(set(paths))


def _branch_allows_pr149_changed_paths(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        149,
        allow_main=False,
        allow_repair=False,
    )


def _branch_allows_pr150_target_matrix_changed_paths(branch: str) -> bool:
    return is_pr_or_later_branch(
        branch,
        150,
        allow_main=False,
        allow_repair=False,
    )


def _is_pr150_target_matrix_changed_path_for_branch(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized in c.PR150_TARGET_MATRIX_CHANGED_PATHS
        and _branch_allows_pr150_target_matrix_changed_paths(branch)
    )


def _is_pr149_main_write_report_guard_repair_path(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        branch == "repair-pr149-main-write-report-guard"
        and normalized != c.REPORT_PATH.as_posix()
        and normalized in c.CHANGED_PATH_EXACT_ALLOWANCE_CANDIDATES
    )


def _branch_allows_explicit_pr149_tracked_report_write(branch: str) -> bool:
    return branch in {
        c.BRANCH,
        "repair-pr149-main-write-report-guard",
    } or is_pr_or_later_branch(
        branch,
        149,
        allow_main=True,
        allow_repair=False,
    )


def _is_explicit_pr149_tracked_report_write_path_for_branch(
    path: str,
    branch: str,
    tracked_report_write_allowed: bool,
) -> bool:
    normalized = path.replace("\\", "/")
    return (
        tracked_report_write_allowed
        and normalized == c.REPORT_PATH.as_posix()
        and _branch_allows_explicit_pr149_tracked_report_write(branch)
    )


def _is_allowed_pr149_changed_path_for_branch(
    path: str,
    branch: str,
    *,
    tracked_report_write_allowed: bool = False,
) -> bool:
    normalized = path.replace("\\", "/")
    if normalized == ".tmp" or normalized.startswith(".tmp/"):
        return True
    if _is_pr149_main_write_report_guard_repair_path(normalized, branch):
        return True
    if _is_explicit_pr149_tracked_report_write_path_for_branch(
        normalized,
        branch,
        tracked_report_write_allowed,
    ):
        return True
    if _is_pr150_target_matrix_changed_path_for_branch(normalized, branch):
        return True
    return (
        normalized in c.CHANGED_PATH_EXACT_ALLOWANCE_CANDIDATES
        and _branch_allows_pr149_changed_paths(branch)
    )


def _validate_changed_paths(
    repo_root: Path,
    *,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    branch = current_branch_context(repo_root).branch
    failures: list[str] = []
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR149_GIT_STATUS_UNAVAILABLE")
            continue
        normalized = path.replace("\\", "/")
        if not _is_allowed_pr149_changed_path_for_branch(
            normalized,
            branch,
            tracked_report_write_allowed=tracked_report_write_allowed,
        ):
            failures.append(f"PR149_CHANGED_PATH_OUT_OF_SCOPE: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append("PR149_MASTER_PLAN_MUTATION_DETECTED")
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix():
            failures.append("PR149_ATOMICROWS_BUNDLE_MUTATION_DETECTED")
        if normalized.startswith(c.ROW_FAMILY_SOURCE_DIRECTORY.as_posix() + "/"):
            failures.append("PR149_ROW_FAMILY_SOURCE_MUTATION_DETECTED")
        if normalized == _forbidden_bundle_sidecar_path():
            failures.append("PR149_NO_BUNDLE_MUTATION_AUTHORITY")
    return sorted(set(failures))


def validate_repository_artifacts(
    repo_root: Path | str,
    *,
    report_output_path: Path | str | None = None,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    root = Path(repo_root).resolve()
    try:
        expected_report = build_report(root)
        if expected_report != build_report(root):
            return ["PR149_REPORT_NOT_DETERMINISTIC"]
    except ValueError as exc:
        return [line for line in str(exc).splitlines() if line]

    failures = validate_report_payload(expected_report)
    if report_output_path is not None:
        output_path = Path(report_output_path)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_dump(expected_report), encoding="utf-8", newline="\n")

    try:
        actual_report = _read_json(root / c.REPORT_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        actual_report = {}
        failures.append(f"PR149_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}")
    if actual_report and actual_report != expected_report:
        failures.append("PR149_REPORT_STALE_OR_NONDETERMINISTIC")
    if actual_report:
        failures.extend(validate_report_payload(actual_report))

    failures.extend(
        _validate_changed_paths(
            root,
            tracked_report_write_allowed=tracked_report_write_allowed,
        )
    )
    return sorted(set(failures))


def write_report_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    report = build_report(root)
    path = root / c.REPORT_PATH
    serialized_report = json_dump(report)
    serialized_bytes = serialized_report.encode("utf-8")
    if path.exists():
        current_bytes = path.read_bytes()
        if (
            current_bytes == serialized_bytes
            or current_bytes.replace(b"\r\n", b"\n") == serialized_bytes
        ):
            return report
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized_report, encoding="utf-8", newline="\n")
    return report
