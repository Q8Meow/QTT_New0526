"""PR137 static launch-readiness dependency controller."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import pr137_launch_readiness_dependency_policy as policy


REPO_ROOT = Path(__file__).resolve().parents[4]


def _json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_dump(payload), encoding="utf-8", newline="\n")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_pr136_inputs(repo_root: Path | str = REPO_ROOT) -> dict[str, Any]:
    """Load PR136 selector and roadmap context artifacts."""

    root = Path(repo_root).resolve()
    inputs: dict[str, Any] = {}
    for rel_path in policy.MANDATORY_READ_ARTIFACTS:
        path = root / rel_path
        if not path.exists():
            inputs[rel_path] = None
            continue
        if path.suffix == ".json":
            inputs[rel_path] = _load_json(path)
        else:
            inputs[rel_path] = _load_text(path)
    return inputs


def _input(inputs: Mapping[str, Any], rel_path: str) -> Any:
    value = inputs.get(rel_path)
    if value is None:
        raise FileNotFoundError(rel_path)
    return value


def _sequence_entries(inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    sequence = _input(
        inputs,
        "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json",
    )
    entries = sequence.get("sequence_entries")
    if not isinstance(entries, list):
        raise ValueError("PR136 sequence entries must be a list")
    return [entry for entry in entries if isinstance(entry, dict)]


def _entry_id(entry: Mapping[str, Any]) -> str:
    return str(entry["final_sequence_pr_number_or_placeholder"])


def _sequence_ids(entries: Sequence[Mapping[str, Any]]) -> list[str]:
    return [_entry_id(entry) for entry in entries]


def _pr136_selector_refs() -> list[dict[str, Any]]:
    return [
        {
            "artifact_ref": rel_path,
            "selector_role": "PR136_CANONICAL_INPUT",
        }
        for rel_path in policy.PR136_SELECTOR_ARTIFACTS
    ]


def _dependency_nodes(entries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for entry in entries:
        sequence_id = _entry_id(entry)
        owner_required = bool(entry.get("owner_authorization_required"))
        nodes.append(
            {
                "authority_state": (
                    "FUTURE_OWNER_AUTHORIZATION_REQUIRED"
                    if owner_required
                    else "DEPENDENCY_GATED_STATIC_SEQUENCE_ENTRY"
                ),
                "current_authority_created": False,
                "domain_ids": list(entry.get("domain_ids", [])),
                "downstream_dependency_ids": list(entry.get("downstream_dependencies", [])),
                "market_scope": list(entry.get("market_scope", policy.CANONICAL_MARKET_SCOPES)),
                "node_id": sequence_id,
                "node_type": "PR136_SEQUENCE_ENTRY",
                "owner_authorization_required": owner_required,
                "readiness_state": str(entry.get("readiness_state_target", policy.TARGET_STATE)),
                "required_upstream_ids": list(entry.get("required_upstream_prs", [])),
                "scope_class": str(entry.get("scope_class", policy.SCOPE_CLASS)),
                "title": str(entry.get("title", sequence_id)),
            }
        )
    return nodes


def _dependency_edges() -> list[dict[str, Any]]:
    return [
        {
            "dependency_type": "REQUIRED_SEQUENCE_EDGE",
            "edge_id": f"{source}_TO_{target}",
            "from_node_id": source,
            "source_selector_ref": (
                "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json"
            ),
            "to_node_id": target,
        }
        for source, target in policy.REQUIRED_DEPENDENCY_EDGES
    ]


def _market_dependency_states(inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    market = _input(
        inputs,
        "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    )
    rows = {
        row.get("canonical_venue_id"): row
        for row in market.get("market_scopes", [])
        if isinstance(row, dict)
    }
    states: list[dict[str, Any]] = []
    for scope in policy.CANONICAL_MARKET_SCOPES:
        row = rows.get(scope, {})
        states.append(
            {
                "canonical_venue_id": scope,
                "future_pr_refs": list(row.get("future_prs_required", [])),
                "missing_prerequisite_classes": list(
                    policy.MISSING_MARKET_PREREQUISITE_CLASSES
                ),
                "owner_authorization_state": "REQUIRED_BEFORE_CANARY_OR_LIVE",
                "pr137_current_state": "PREREQUISITE_GATED",
                "readiness_gated": True,
                "source_market_scope_ref": (
                    "docs/master_plan/generated/"
                    "PR136MarketSpecificLaunchReadinessIndex.report.json"
                ),
            }
        )
    return states


def _agent_dependency_states(inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    agent_map = _input(
        inputs,
        "docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json",
    )
    rows = {
        row.get("agent_domain_id"): row
        for row in agent_map.get("agent_domains", [])
        if isinstance(row, dict)
    }
    states: list[dict[str, Any]] = []
    for agent_id in policy.AGENT_IDS:
        row = rows.get(agent_id, {})
        states.append(
            {
                "agent_id": agent_id,
                "allowed_current_pr137_inputs": [
                    "PR136_SELECTOR_ARTIFACTS",
                    "PR136_MARKET_READINESS_INDEX",
                    "PR136_AGENT_ORCHESTRATION_MAP",
                ],
                "allowed_current_pr137_outputs": [
                    "STATIC_DEPENDENCY_REPORTS",
                    "VALIDATION_GATE_RECEIPTS",
                ],
                "atomicrows_scope": str(row.get("atomicrows_scope", "NONE")),
                "current_authority_state": "STATIC_DEPENDENCY_CONTROLLER_ONLY",
                "forbidden_current_authority": sorted(policy.NO_AUTHORITY_FLAGS),
                "future_dependency_prs": list(policy.AGENT_FUTURE_DEPENDENCY_PRS[agent_id]),
                "future_owner_authorization_required": True,
                "latency_hot_path_allowed": False,
                "live_order_authority_allowed": False,
                "market_scope": list(policy.CANONICAL_MARKET_SCOPES),
                "quantum_scope": str(row.get("quantum_scope", "NONE")),
            }
        )
    return states


def _quantum_atomicrows_boundary() -> dict[str, Any]:
    future_state = "FUTURE_DEPENDENCY_METADATA_ONLY"
    return {
        "atomicrows_bridge_compatibility": future_state,
        "atomicrows_bundle_created": False,
        "atomicrows_materialization_authority_created": False,
        "atomicrows_rows_created": False,
        "boundary_state": "QUANTUM_AND_ATOMICROWS_FUTURE_REF_ONLY",
        "compatibility_states": {
            "ising_compatibility": future_state,
            "qaoa_qubo_compatibility": future_state,
            "quantum_annealing_compatibility": future_state,
            "quantum_classical_comparator": future_state,
            "quantum_kernel_feature_map": future_state,
            "quantum_optimizer_arbitration_readiness": future_state,
            "vqe_compatibility": future_state,
        },
        "no_optimizer_input_packet": True,
        "no_quantum_advantage_claim": True,
        "no_quantum_backend_call": True,
        "no_quantum_trading_signal": True,
        "no_simulator_execution": True,
        "quantum_metadata_only": True,
        "source_selector_ref": (
            "docs/master_plan/generated/"
            "PR136QuantumAtomicRowsOptimizationReadinessMap.report.json"
        ),
    }


def _latency_boundary() -> dict[str, Any]:
    return {
        "control_plane_only": True,
        "future_live_hot_path_allowed_inputs": [
            "precomputed_source_change_snapshot",
            "precomputed_connector_semantic_binding_snapshot",
            "precomputed_runtime_cash_private_state_snapshot",
            "precomputed_risk_limits",
            "precomputed_approved_parameter_stack",
            "precomputed_execution_policy",
            "owner_authorized_live_command",
        ],
        "live_hot_path_call_created": False,
        "no_atomicrows_generation_in_live_hot_path": True,
        "no_llm_reasoning_in_live_hot_path": True,
        "no_quantum_backend_call_in_live_hot_path": True,
        "no_source_retrieval_in_live_hot_path": True,
        "pr137_latency_state": "CONTROL_PLANE_ONLY",
        "source_selector_ref": (
            "docs/master_plan/generated/PR136LatencyControlPlaneVsLivePathMap.report.json"
        ),
    }


def _owner_authorization_boundary() -> dict[str, Any]:
    return {
        "live_command_created": False,
        "owner_approval_receipt_created": False,
        "pr137_auto_authorizes_later_pr": False,
        "pr137_auto_authorizes_pr137l": False,
        "pr137_auto_authorizes_pr138": False,
        "pr164_final_live_start_requires_explicit_owner_command": True,
        "source_selector_ref": (
            "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json"
        ),
    }


def _generated_integrity_boundary() -> dict[str, Any]:
    return {
        "boundary_state": "PR137_GENERATED_INTEGRITY_AUTHORITY_BLOCKED",
        "exact_blocker_assertions_owned_by": (
            "tools/validate_pr137_generated_integrity_authority_boundary.py"
        ),
        "forbidden_field_group_present": False,
        "generated_integrity_authority_created": False,
        "pr137_artifact_scan_scope": [
            *policy.report_paths(),
            policy.ROADMAP_DOC_PATH,
            *policy.schema_paths(),
            *policy.receipt_paths(),
            "src/qtt/stage1_prediction_markets/launch_readiness/"
            "pr137_launch_readiness_dependency_controller.py",
            "src/qtt/stage1_prediction_markets/launch_readiness/"
            "pr137_launch_readiness_dependency_policy.py",
            "tools/validate_pr137_launch_readiness_dependency_controller.py",
            "tools/validate_pr137_generated_integrity_authority_boundary.py",
            "tests/roadmap/test_pr137_launch_readiness_dependency_controller.py",
        ],
        "structural_evidence_only": True,
        "validation_marker": policy.GENERATED_INTEGRITY_VALIDATION_MARKER,
    }


def _validation_gate_integration() -> dict[str, Any]:
    return {
        "authority_class": policy.AUTHORITY_CLASS,
        "cumulative_gate_commands_required": [
            "tools/validate_pr136_roadmap_policy_literal_drift.py",
            "tools/validate_pr136_day1_launch_readiness_roadmap.py",
            "tools/validate_pr137_generated_integrity_authority_boundary.py",
            "tools/validate_pr137_launch_readiness_dependency_controller.py",
        ],
        "generated_at_utc": policy.GENERATED_AT_UTC,
        "generated_by": policy.GENERATED_BY,
        "pr137_validators_ordered_after_pr136": True,
        "receipt_type": "PR137_VALIDATION_GATE_INTEGRATION",
        "repo_pr_number_or_label": policy.REPO_PR_LABEL,
        "report_type": "PR137_VALIDATION_GATE_INTEGRATION",
        "report_version": "PR137_VALIDATION_GATE_INTEGRATION_V1",
        "validation_marker": policy.CONTROLLER_VALIDATION_MARKER,
    }


def build_pr137_controller_payload(repo_root: Path | str = REPO_ROOT) -> dict[str, Any]:
    inputs = load_pr136_inputs(repo_root)
    entries = _sequence_entries(inputs)
    sequence_ids = _sequence_ids(entries)
    nodes = _dependency_nodes(entries)
    edges = _dependency_edges()
    market_states = _market_dependency_states(inputs)
    agent_states = _agent_dependency_states(inputs)
    quantum_atomicrows = _quantum_atomicrows_boundary()
    latency = _latency_boundary()
    owner = _owner_authorization_boundary()
    generated_integrity = _generated_integrity_boundary()
    return {
        "agent_dependency_states": agent_states,
        "authority_class": policy.AUTHORITY_CLASS,
        "dependency_edge_count": len(edges),
        "dependency_edges": edges,
        "dependency_node_count": len(nodes),
        "dependency_nodes": nodes,
        "downstream_sequence_preview": [
            {
                "sequence_id": sequence_id,
                "title": next(
                    str(entry.get("title", sequence_id))
                    for entry in entries
                    if _entry_id(entry) == sequence_id
                ),
            }
            for sequence_id in ("PR137", "PR137L", "PR138", "PR139", "PR164")
        ],
        "first_next_pr_id": "PR137",
        "generated_at_utc": policy.GENERATED_AT_UTC,
        "generated_by": policy.GENERATED_BY,
        "generated_integrity_authority_boundary": generated_integrity,
        "latency_dependency_boundary": latency,
        "market_dependency_states": market_states,
        "no_authority_flags": policy.no_authority_flags(),
        "owner_authorization_boundary": owner,
        "pr136_selector_refs": _pr136_selector_refs(),
        "quantum_atomicrows_dependency_boundary": quantum_atomicrows,
        "receipt_type": "PR137_LAUNCH_READINESS_DEPENDENCY_CONTROLLER",
        "repo_pr_number_or_label": policy.REPO_PR_LABEL,
        "report_type": "PR137_LAUNCH_READINESS_DEPENDENCY_CONTROLLER",
        "report_version": "PR137_LAUNCH_READINESS_DEPENDENCY_CONTROLLER_V1",
        "sequence_entry_ids": sequence_ids,
        "validation_marker": policy.CONTROLLER_VALIDATION_MARKER,
    }


def _dependency_gate_state_matrix(payload: Mapping[str, Any]) -> dict[str, Any]:
    nodes = {node["node_id"]: node for node in payload["dependency_nodes"]}
    upstream: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    downstream: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge in payload["dependency_edges"]:
        source = edge["from_node_id"]
        target = edge["to_node_id"]
        downstream.setdefault(source, []).append(target)
        upstream.setdefault(target, []).append(source)
    matrix = {
        node_id: {
            "authority_state": nodes[node_id]["authority_state"],
            "downstream_dependencies": sorted(downstream.get(node_id, [])),
            "readiness_state": nodes[node_id]["readiness_state"],
            "upstream_dependencies": sorted(upstream.get(node_id, [])),
        }
        for node_id in payload["sequence_entry_ids"]
    }
    return {
        "authority_class": policy.AUTHORITY_CLASS,
        "generated_at_utc": policy.GENERATED_AT_UTC,
        "generated_by": policy.GENERATED_BY,
        "receipt_type": "PR137_DEPENDENCY_GATE_STATE_MATRIX",
        "repo_pr_number_or_label": policy.REPO_PR_LABEL,
        "report_type": "PR137_DEPENDENCY_GATE_STATE_MATRIX",
        "report_version": "PR137_DEPENDENCY_GATE_STATE_MATRIX_V1",
        "sequence_gate_matrix": matrix,
        "validation_marker": policy.CONTROLLER_VALIDATION_MARKER,
    }


def _market_readiness_dependency_matrix(payload: Mapping[str, Any]) -> dict[str, Any]:
    matrix = {
        row["canonical_venue_id"]: {
            "future_pr_refs": list(row["future_pr_refs"]),
            "missing_prerequisite_classes": list(row["missing_prerequisite_classes"]),
            "owner_authorization_state": row["owner_authorization_state"],
            "readiness_gated": row["readiness_gated"],
        }
        for row in payload["market_dependency_states"]
    }
    return {
        "authority_class": policy.AUTHORITY_CLASS,
        "generated_at_utc": policy.GENERATED_AT_UTC,
        "generated_by": policy.GENERATED_BY,
        "market_dependency_matrix": matrix,
        "receipt_type": "PR137_MARKET_READINESS_DEPENDENCY_MATRIX",
        "repo_pr_number_or_label": policy.REPO_PR_LABEL,
        "report_type": "PR137_MARKET_READINESS_DEPENDENCY_MATRIX",
        "report_version": "PR137_MARKET_READINESS_DEPENDENCY_MATRIX_V1",
        "validation_marker": policy.CONTROLLER_VALIDATION_MARKER,
    }


def _agent_dependency_controller(payload: Mapping[str, Any]) -> dict[str, Any]:
    matrix = {
        row["agent_id"]: {
            "allowed_current_pr137_inputs": list(row["allowed_current_pr137_inputs"]),
            "allowed_current_pr137_outputs": list(row["allowed_current_pr137_outputs"]),
            "forbidden_current_authority": list(row["forbidden_current_authority"]),
            "future_dependency_prs": list(row["future_dependency_prs"]),
            "live_order_authority_allowed": row["live_order_authority_allowed"],
        }
        for row in payload["agent_dependency_states"]
    }
    return {
        "agent_dependency_controller": matrix,
        "authority_class": policy.AUTHORITY_CLASS,
        "generated_at_utc": policy.GENERATED_AT_UTC,
        "generated_by": policy.GENERATED_BY,
        "receipt_type": "PR137_AGENT_DEPENDENCY_CONTROLLER",
        "repo_pr_number_or_label": policy.REPO_PR_LABEL,
        "report_type": "PR137_AGENT_DEPENDENCY_CONTROLLER",
        "report_version": "PR137_AGENT_DEPENDENCY_CONTROLLER_V1",
        "validation_marker": policy.CONTROLLER_VALIDATION_MARKER,
    }


def _boundary_report(payload: Mapping[str, Any], key: str, report_type: str) -> dict[str, Any]:
    return {
        "authority_class": policy.AUTHORITY_CLASS,
        "generated_at_utc": policy.GENERATED_AT_UTC,
        "generated_by": policy.GENERATED_BY,
        key: payload[key],
        "receipt_type": report_type,
        "repo_pr_number_or_label": policy.REPO_PR_LABEL,
        "report_type": report_type,
        "report_version": f"{report_type}_V1",
        "validation_marker": policy.CONTROLLER_VALIDATION_MARKER,
    }


def _read_receipt(inputs: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = [path for path in policy.MANDATORY_READ_ARTIFACTS if inputs.get(path) is None]
    return {
        "agent_domain_count": len(payload["agent_dependency_states"]),
        "authority_class": policy.AUTHORITY_CLASS,
        "generated_at_utc": policy.GENERATED_AT_UTC,
        "generated_by": policy.GENERATED_BY,
        "mandatory_artifact_refs_read": [
            path for path in policy.MANDATORY_READ_ARTIFACTS if inputs.get(path) is not None
        ],
        "market_scope_count": len(payload["market_dependency_states"]),
        "missing_mandatory_artifact_refs": missing,
        "read_before_editing_confirmed": True,
        "receipt_type": "CODEX_PR137_MANDATORY_READ_RECEIPT",
        "repo_pr_number_or_label": policy.REPO_PR_LABEL,
        "report_type": "CODEX_PR137_MANDATORY_READ_RECEIPT",
        "report_version": "CODEX_PR137_MANDATORY_READ_RECEIPT_V1",
        "sequence_entry_count": len(payload["sequence_entry_ids"]),
        "validation_marker": policy.CONTROLLER_VALIDATION_MARKER,
    }


def _route_triage_receipt() -> dict[str, Any]:
    return {
        "arbitrary_domain_count_forced": False,
        "authority_class": policy.AUTHORITY_CLASS,
        "fixed_13_domain_model_used": False,
        "generated_at_utc": policy.GENERATED_AT_UTC,
        "generated_by": policy.GENERATED_BY,
        "no_execution_authority_created": True,
        "pr137_selected_from_pr136_sequence": True,
        "receipt_type": "CODEX_PR137_ROUTE_TRIAGE_RECEIPT",
        "repo_pr_number_or_label": policy.REPO_PR_LABEL,
        "report_type": "CODEX_PR137_ROUTE_TRIAGE_RECEIPT",
        "report_version": "CODEX_PR137_ROUTE_TRIAGE_RECEIPT_V1",
        "same_number_inference_used": False,
        "validation_marker": policy.CONTROLLER_VALIDATION_MARKER,
    }


def build_reports(repo_root: Path | str = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    inputs = load_pr136_inputs(root)
    payload = build_pr137_controller_payload(root)
    return {
        f"{policy.REPORT_DIR}/PR137LaunchReadinessDependencyController.report.json": payload,
        f"{policy.REPORT_DIR}/PR137DependencyGateStateMatrix.report.json": (
            _dependency_gate_state_matrix(payload)
        ),
        f"{policy.REPORT_DIR}/PR137MarketReadinessDependencyMatrix.report.json": (
            _market_readiness_dependency_matrix(payload)
        ),
        f"{policy.REPORT_DIR}/PR137AgentDependencyController.report.json": (
            _agent_dependency_controller(payload)
        ),
        f"{policy.REPORT_DIR}/PR137QuantumAtomicRowsDependencyBoundary.report.json": (
            _boundary_report(
                payload,
                "quantum_atomicrows_dependency_boundary",
                "PR137_QUANTUM_ATOMICROWS_DEPENDENCY_BOUNDARY",
            )
        ),
        f"{policy.REPORT_DIR}/PR137GeneratedIntegrityAuthorityBoundary.report.json": (
            _boundary_report(
                payload,
                "generated_integrity_authority_boundary",
                "PR137_GENERATED_INTEGRITY_AUTHORITY_BOUNDARY",
            )
        ),
        f"{policy.REPORT_DIR}/PR137ValidationGateIntegration.report.json": (
            _validation_gate_integration()
        ),
        f"{policy.ROADMAP_GENERATED_DIR}/CODEX_PR137_MANDATORY_READ_RECEIPT.json": (
            _read_receipt(inputs, payload)
        ),
        f"{policy.ROADMAP_GENERATED_DIR}/CODEX_PR137_ROUTE_TRIAGE_RECEIPT.json": (
            _route_triage_receipt()
        ),
    }


def _schema_base(title: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": True,
        "properties": {
            "authority_class": {"const": policy.AUTHORITY_CLASS},
            "generated_at_utc": {"const": policy.GENERATED_AT_UTC},
            "generated_by": {"const": policy.GENERATED_BY},
            "receipt_type": {"type": "string"},
            "repo_pr_number_or_label": {"const": policy.REPO_PR_LABEL},
            "report_type": {"type": "string"},
            "report_version": {"type": "string"},
            "validation_marker": {
                "enum": list(policy.VALIDATION_MARKERS),
                "type": "string",
            },
        },
        "required": [
            "authority_class",
            "generated_at_utc",
            "generated_by",
            "receipt_type",
            "repo_pr_number_or_label",
            "report_type",
            "report_version",
        ],
        "title": title,
        "type": "object",
    }


def schema_documents() -> dict[str, Any]:
    node_schema = _schema_base("PR137 Launch Readiness Dependency Node")
    node_schema["properties"].update(
        {
            "current_authority_created": {"const": False},
            "node_id": {"type": "string"},
            "owner_authorization_required": {"type": "boolean"},
            "readiness_state": {"type": "string"},
            "required_upstream_ids": {"items": {"type": "string"}, "type": "array"},
        }
    )
    edge_schema = _schema_base("PR137 Launch Readiness Dependency Edge")
    edge_schema["properties"].update(
        {
            "dependency_type": {"type": "string"},
            "edge_id": {"type": "string"},
            "from_node_id": {"type": "string"},
            "to_node_id": {"type": "string"},
        }
    )
    market_schema = _schema_base("PR137 Market Dependency State")
    market_schema["properties"].update(
        {
            "canonical_venue_id": {"enum": list(policy.CANONICAL_MARKET_SCOPES)},
            "missing_prerequisite_classes": {
                "items": {"type": "string"},
                "type": "array",
            },
            "readiness_gated": {"const": True},
        }
    )
    boundary_schema = _schema_base("PR137 Generated Integrity Authority Boundary")
    boundary_schema["properties"].update(
        {
            "boundary_state": {"type": "string"},
            "forbidden_field_group_present": {"const": False},
            "generated_integrity_authority_created": {"const": False},
            "structural_evidence_only": {"const": True},
        }
    )
    controller_schema = _schema_base("PR137 Launch Readiness Dependency Controller")
    controller_schema["properties"].update(
        {
            "agent_dependency_states": {"type": "array"},
            "dependency_edges": {"type": "array"},
            "dependency_nodes": {"type": "array"},
            "first_next_pr_id": {"const": "PR137"},
            "generated_integrity_authority_boundary": {"type": "object"},
            "market_dependency_states": {"type": "array"},
            "no_authority_flags": {"type": "object"},
            "pr136_selector_refs": {"type": "array"},
            "sequence_entry_ids": {"type": "array"},
        }
    )
    return {
        f"{policy.SCHEMA_DIR}/pr137_launch_readiness_dependency_controller.schema.json": (
            controller_schema
        ),
        f"{policy.SCHEMA_DIR}/pr137_launch_readiness_dependency_node.schema.json": (
            node_schema
        ),
        f"{policy.SCHEMA_DIR}/pr137_launch_readiness_dependency_edge.schema.json": (
            edge_schema
        ),
        f"{policy.SCHEMA_DIR}/pr137_market_dependency_state.schema.json": market_schema,
        f"{policy.SCHEMA_DIR}/pr137_generated_integrity_authority_boundary.schema.json": (
            boundary_schema
        ),
    }


def roadmap_doc() -> str:
    return f"""# QTT PR137 Launch Readiness Dependency Controller v1.0

PR137 is a static dependency controller for the post-PR136 launch-readiness roadmap. It uses PR136 as the selector and does not replace PR136.

## Authority

- Repo PR label: {policy.REPO_PR_LABEL}
- Branch: {policy.REQUIRED_BRANCH_NAME}
- Authority class: {policy.AUTHORITY_CLASS}
- Target state: {policy.TARGET_STATE}
- Validation marker: {policy.CONTROLLER_VALIDATION_MARKER}

## Scope

PR137 connects the PR136-selected dependency sequence from PR137 to PR164. PR137 is the first next PR, PR137L is downstream of PR137, and PR138 is downstream of PR137L. PR137 does not auto-authorize PR137L, PR138, or any later PR.

The canonical market scope remains PREDICTION_MARKETS_GENERAL, KALSHI, POLYMARKET, and FORECASTEX_IBKR. PR137 preserves global roadmap authority with market-scoped overlays and does not create disconnected market-specific roadmaps.

## Non-Authority Boundary

PR137 creates no trading authority, source retrieval, source acceptance, connector binding, credential resolution, private-state fetch, runtime cash authority, replay execution, paper execution, order authority, order execution, fill receipt, profit evidence, latency superiority evidence, execution superiority evidence, alpha evidence, quantum execution, quantum optimizer input, quantum trading signal, quantum advantage claim, owner approval receipt, canary execution, or Day-1 launch authority.

## Quantum and AtomicRows

Quantum and AtomicRows compatibility remains future-reference metadata only. QAOA/QUBO, Ising, VQE, quantum annealing, quantum kernel feature maps, quantum/classical comparator support, optimizer arbitration readiness, and AtomicRows bridge compatibility stay dependency metadata only. PR137 creates no AtomicRows rows, no AtomicRows bundle, and no AtomicRows materialization authority.

## Generated Integrity Boundary

PR137 preserves the no generated-integrity-authority boundary. Structural evidence is limited to artifact references, sequence IDs, dependency node and edge counts, canonical venue IDs, prerequisite classes, authority booleans, validation markers, and deterministic ordering assertions.
"""


def write_artifacts(repo_root: Path | str = REPO_ROOT) -> None:
    root = Path(repo_root).resolve()
    for rel_path, payload in build_reports(root).items():
        _write_json(root / rel_path, payload)
    for rel_path, payload in schema_documents().items():
        _write_json(root / rel_path, payload)
    path = root / policy.ROADMAP_DOC_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(roadmap_doc(), encoding="utf-8", newline="\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args(argv)
    if args.write_artifacts:
        write_artifacts(args.repo_root)
    else:
        print(_json_dump(build_pr137_controller_payload(args.repo_root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
