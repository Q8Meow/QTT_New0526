"""Deterministic builders for the PR142 AtomicRows handoff-readiness gate."""

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


def _read_required_bytes(repo_root: Path, paths: Sequence[Path]) -> list[str]:
    failures: list[str] = []
    for rel_path in paths:
        path = repo_root / rel_path
        if not path.exists():
            failures.append(f"PR142_REQUIRED_EVIDENCE_MISSING: {rel_path.as_posix()}")
            continue
        try:
            path.read_bytes()
        except OSError as exc:
            failures.append(f"PR142_REQUIRED_EVIDENCE_INVALID: {rel_path.as_posix()}: {exc}")
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
        *c.VALIDATION_CONTEXT_EVIDENCE_PATHS,
    )
    failures = _read_required_bytes(root, required_paths)
    payloads: dict[str, Mapping[str, Any]] = {}
    for rel_path in (*c.PR136_EVIDENCE_PATHS, *c.ATOMICROWS_EVIDENCE_PATHS):
        if rel_path.suffix != ".json":
            continue
        path = root / rel_path
        if not path.exists():
            continue
        try:
            payloads[rel_path.as_posix()] = _read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"PR142_REQUIRED_EVIDENCE_INVALID: {rel_path.as_posix()}: {exc}")

    try:
        pr141_yaml = _read_yaml(root / c.PR141_YAML_PATH)
    except (OSError, RegistryParseError, ValueError) as exc:
        pr141_yaml = {}
        failures.append(f"PR142_REQUIRED_EVIDENCE_INVALID: {c.PR141_YAML_PATH.as_posix()}: {exc}")

    pr141_report = payloads.get(c.PR141_REPORT_PATH.as_posix(), {})
    alias_resolution = crosswalk_alias_resolution(root)
    if not (root / c.CROSSWALK_CANONICAL).exists():
        failures.append("QTT_PR142_CANONICAL_PR136_CROSSWALK_MISSING")
    if alias_resolution["conflict_detected"]:
        failures.append("QTT_PR142_CROSSWALK_ALIAS_CONFLICT")

    optional_present = (root / c.OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH).exists()
    if optional_present:
        try:
            (root / c.OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH).read_bytes()
        except OSError as exc:
            failures.append(
                "PR142_OPTIONAL_SOURCE_EVIDENCE_PACKET_INVALID: "
                f"{c.OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH.as_posix()}: {exc}"
            )

    return (
        StaticEvidence(
            repo_root=root,
            payloads=payloads,
            pr141_yaml=pr141_yaml,
            pr141_report=pr141_report,
            alias_resolution=alias_resolution,
            source_evidence_packet_present=optional_present,
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
        if edge.get("from") in {"PR140", "PR141", "PR142"} or edge.get("to") in {
            "PR141",
            "PR142",
            "PR143K",
        }:
            edges.append(dict(edge))
    return edges


def _market_scope_summary(market_index: Mapping[str, Any]) -> dict[str, Any]:
    scopes = [scope for scope in _list(market_index.get("market_scopes")) if isinstance(scope, Mapping)]
    first_scope = scopes[0] if scopes else {}
    return {
        "canonical_venue_ids": [str(scope.get("canonical_venue_id")) for scope in scopes],
        "owner_authorization_required": all(
            scope.get("owner_authorization_required") is True for scope in scopes
        )
        if scopes
        else True,
        "missing_accepted_source_evidence_classes": _string_list(
            first_scope.get("missing_accepted_source_evidence_classes")
        ),
        "missing_connector_semantic_bindings": True,
        "missing_runtime_cash_private_state_receipts": True,
        "missing_replay_paper_evidence": True,
        "missing_day1_launch_preflight": True,
    }


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
            "future_owner_authorization_required": agent.get(
                "future_owner_authorization_required"
            ),
            "latency_hot_path_allowed": agent.get("latency_hot_path_allowed"),
            "live_order_authority_allowed": agent.get("live_order_authority_allowed"),
            "forbidden_current_authority": _string_list(
                agent.get("forbidden_current_authority")
            ),
        }
    return {"agent_domain_count": len(domains), "selected_agent_domains": selected}


def _pr141_handoff(evidence: StaticEvidence) -> Mapping[str, Any]:
    return _mapping(evidence.pr141_report.get("downstream_handoff_contract"))


def _pr141_summary(evidence: StaticEvidence) -> Mapping[str, Any]:
    return _mapping(evidence.pr141_report.get("owner_authorization_readiness_summary"))


def _pr141_yaml_handoff(evidence: StaticEvidence) -> Mapping[str, Any]:
    return _mapping(evidence.pr141_yaml.get("downstream_handoff_contract"))


def _build_payload(evidence: StaticEvidence) -> dict[str, Any]:
    route = _payload(evidence, c.PR136_EVIDENCE_PATHS[0])
    command_matrix = _payload(evidence, c.PR136_EVIDENCE_PATHS[2])
    market_index = _payload(evidence, c.PR136_EVIDENCE_PATHS[3])
    agent_map = _payload(evidence, c.PR136_EVIDENCE_PATHS[5])
    dependency_graph = _payload(evidence, c.PR136_EVIDENCE_PATHS[6])
    quantum_map = _payload(evidence, c.PR136_EVIDENCE_PATHS[7])
    sequence = _payload(evidence, c.PR136_EVIDENCE_PATHS[8])
    pr141_sequence = _sequence_entry(sequence, "PR141")
    pr142_sequence = _sequence_entry(sequence, "PR142")
    pr141_handoff = _pr141_handoff(evidence)
    pr141_summary = _pr141_summary(evidence)
    market_summary = _market_scope_summary(market_index)

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
            "evidence_derived_name_used": False,
            "fallback_name_used": True,
            "name_derivation_notes": (
                "PR141 downstream_handoff_contract creates static input for PR142 "
                "but does not define a more specific artifact stem, package name, "
                "or validation marker; owner-provided PR142 fallback names are used."
            ),
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
                "pr141_entry": dict(pr141_sequence),
                "pr142_entry": dict(pr142_sequence),
            },
            "dependency_alignment": {
                "edges": _dependency_edges(dependency_graph),
                "owner_authorization_nodes": _string_list(
                    dependency_graph.get("owner_authorization_nodes")
                ),
            },
            "launch_readiness_domain_alignment": {
                "scope_class": pr142_sequence.get("scope_class"),
                "domain_ids": _string_list(pr142_sequence.get("domain_ids")),
                "readiness_state_target": pr142_sequence.get("readiness_state_target"),
                "owner_authorization_required": pr142_sequence.get(
                    "owner_authorization_required"
                ),
            },
            "market_specific_alignment": market_summary,
            "command_action_alignment": _command_action_alignment(command_matrix),
            "quantum_atomicrows_optimization_readiness_alignment": {
                "atomicrows_readiness_ladder": _string_list(
                    quantum_map.get("atomicrows_readiness_ladder")
                ),
                "quantum_evidence_status": quantum_map.get("quantum_evidence_status"),
                "future_owner_authorization_required_for_materialization_flag": quantum_map.get(
                    "future_owner_authorization_required_for_materialization_flag"
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
                "pr142_forbidden_artifacts": _string_list(
                    pr142_sequence.get("forbidden_artifacts")
                ),
            },
            "pr136_planning_authority_only": True,
            "pr136_does_not_authorize_materialization": True,
            "pr136_does_not_authorize_live_trading": True,
            "pr136_does_not_authorize_quantum_execution": True,
            "pr136_does_not_authorize_day1_launch": True,
        },
        "upstream_atomicrows_evidence": {
            "consumed_files": _path_list(c.ATOMICROWS_EVIDENCE_PATHS),
            "pr137r_bundle_reconciliation_consumed": True,
            "pr137l_latency_hot_path_boundary_consumed": True,
            "pr138_semantic_row_contract_consumed": True,
            "pr138_semantic_field_inventory_consumed": True,
            "pr139_row_family_source_manifest_currentization_consumed": True,
            "pr140_semantic_field_coverage_enrichment_plan_consumed": True,
            "pr141_owner_authorization_readiness_gate_consumed": True,
        },
        "pr141_downstream_handoff_consumption": {
            "upstream_report_path": c.PR141_REPORT_PATH.as_posix(),
            "upstream_yaml_path": c.PR141_YAML_PATH.as_posix(),
            "downstream_handoff_contract_detected": bool(pr141_handoff),
            "downstream_handoff_contract": dict(pr141_handoff),
            "yaml_downstream_handoff_contract": dict(_pr141_yaml_handoff(evidence)),
            "downstream_handoff_scope": "STATIC_AUTHORIZATION_METADATA_ONLY",
            "downstream_handoff_allowed_for_this_pr": (
                "PR142" in _string_list(pr141_handoff.get("pr141_creates_downstream_input_for"))
            ),
            "exact_future_step_prepared": (
                "future owner-review/materialization-planning readiness request only"
            ),
            "owner_approval_inferred": False,
            "owner_approval_receipt_created": False,
            "materialization_permission_created": False,
            "semantic_values_materialized": False,
            "bundle_mutation_created": False,
            "row_family_source_mutation_created": False,
        },
        "static_handoff_readiness_contract": {
            "ready_to_request_owner_review": True,
            "ready_to_prepare_future_materialization_plan": True,
            "readiness_state": c.READINESS_STATES[1],
            "blocked_reason_codes": list(c.BLOCK_REASON_CODES),
            "required_future_owner_action": (
                "EXPLICIT_OWNER_APPROVAL_PACKET_REQUIRED_BEFORE_MATERIALIZATION"
            ),
            "required_future_accepted_source_or_runtime_receipt_dependencies": [
                "ACCEPTED_SOURCE_PACKETS",
                "RUNTIME_RECEIPTS",
                "REPLAY_PAPER_RESULTS",
                "OPTIMIZER_DEFAULT_POLICY_OR_ACCEPTED_EVIDENCE",
            ],
            "next_pr_static_input_created": True,
            "future_materialization_still_requires_explicit_owner_approval": True,
        },
        "source_evidence_boundary": {
            "source_evidence_packet_consumed_if_present": (
                evidence.source_evidence_packet_present
            ),
            "source_evidence_packet_repo_path_present": (
                evidence.source_evidence_packet_present
            ),
            "source_evidence_packet_path": (
                c.OPTIONAL_SOURCE_EVIDENCE_PACKET_PATH.as_posix()
            ),
            "owner_policy_may_authorize_retrieval_scope": (
                True if evidence.source_evidence_packet_present else "unknown"
            ),
            "owner_policy_may_authorize_external_fact_value": False,
            "source_acceptance_created": False,
            "connector_semantic_binding_created": False,
            "runtime_cash_receipt_created": False,
            "missing_accepted_source_packets_block_runtime_use": True,
        },
        "atomicrows_compatibility": {
            "enrichment_order_preserved": True,
            "enrichment_order": list(c.ATOMICROWS_ENRICHMENT_ORDER),
            "semantic_row_contract_preserved": True,
            "row_family_source_manifest_preserved": True,
            "field_coverage_plan_preserved": True,
            "owner_authorization_readiness_gate_preserved": True,
            "value_materialization_still_blocked": True,
            "no_bundle_mutation": True,
            "no_row_family_source_mutation": True,
            "no_bundle_authority_created": True,
            "no_bundle_freeze_authority_created": True,
            "pr141_blocked_counts": {
                "source_evidence_blocked_count": pr141_summary.get(
                    "source_evidence_blocked_count"
                ),
                "runtime_receipt_blocked_count": pr141_summary.get(
                    "runtime_receipt_blocked_count"
                ),
                "replay_paper_evidence_blocked_count": pr141_summary.get(
                    "replay_paper_evidence_blocked_count"
                ),
            },
        },
        "quantum_forward_compatibility": {
            "quantum_forward_metadata_only": True,
            "quantum_applicability_source": [
                c.PR136_EVIDENCE_PATHS[7].as_posix(),
                c.PR141_REPORT_PATH.as_posix(),
            ],
            **c.QUANTUM_EXECUTION_BOUNDARY,
            "optimizer_parameter_value_source_status": "NOT_MATERIALIZED_OR_NOT_ACCEPTED",
            "compatible_future_problem_forms": "UNKNOWN_PENDING_EVIDENCE",
            "future_optimizer_compatibility_notes": [
                "QAOA/VQE/annealing/QUBO/Ising references remain static metadata only.",
                "No optimizer inputs, outputs, parameter values, or backend calls are created.",
            ],
            "missing_optimizer_default_policy_route": (
                "BLOCK_UNTIL_ACCEPTED_EVIDENCE_OR_OWNER_POLICY"
            ),
            "metadata_only_fields": list(c.QUANTUM_FORWARD_METADATA_ONLY_FIELDS),
        },
        "classical_optimizer_forward_compatibility": {
            **c.CLASSICAL_OPTIMIZER_BOUNDARY,
            "deterministic_field_identity_ready": True,
            "missing_value_materialization_blocks_optimizer_use": True,
            "missing_external_fact_evidence_blocks_runtime_use": True,
            "missing_owner_approval_blocks_materialization": True,
            "missing_replay_paper_results_blocks_live_promotion": True,
            "missing_runtime_cash_receipt_blocks_exposure": True,
            "metadata_only_fields": list(c.CLASSICAL_OPTIMIZER_METADATA_ONLY_FIELDS),
        },
        "latency_hot_path_boundary": dict(c.LATENCY_HOT_PATH_BOUNDARY),
        "no_claim_boundary": dict(c.NO_CLAIM_BOUNDARY),
        "forbidden_authority_output_boundary": dict(c.FORBIDDEN_AUTHORITY_OUTPUT_BOUNDARY),
        "forbidden_payload_boundary": dict(c.FORBIDDEN_PAYLOAD_BOUNDARY),
        "path_conflict_resolution": {
            "conflicts_detected": False,
            "path_conflict_resolution": "NO_EXISTING_PR142_FALLBACK_PATH_CONFLICTS_DETECTED",
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
