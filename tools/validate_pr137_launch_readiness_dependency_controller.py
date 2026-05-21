#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.launch_readiness import (  # noqa: E402
    pr137_launch_readiness_dependency_policy as policy,
)
from tools import validate_pr137_generated_integrity_authority_boundary as boundary


SUCCESS_MARKER = policy.CONTROLLER_VALIDATION_MARKER


@dataclass(frozen=True)
class ValidationFailure:
    code: str
    message: str
    artifact_ref: str


def _failure(code: str, message: str, artifact_ref: str) -> ValidationFailure:
    return ValidationFailure(code, message, artifact_ref)


def _load_object(repo_root: Path, rel_path: str) -> dict[str, Any]:
    payload = json.loads((repo_root / rel_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{rel_path} root must be an object")
    return payload


def _controller(repo_root: Path) -> dict[str, Any]:
    return _load_object(
        repo_root,
        f"{policy.REPORT_DIR}/PR137LaunchReadinessDependencyController.report.json",
    )


def _all_pr137_json_roots(repo_root: Path) -> dict[str, dict[str, Any]]:
    roots: dict[str, dict[str, Any]] = {}
    for rel_path in (*policy.report_paths(), *policy.receipt_paths()):
        roots[rel_path] = _load_object(repo_root, rel_path)
    return roots


def _validate_required_artifacts(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for rel_path in (
        *policy.report_paths(),
        *policy.receipt_paths(),
        *policy.schema_paths(),
        policy.ROADMAP_DOC_PATH,
        "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_policy.py",
        "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_controller.py",
        "tools/validate_pr137_generated_integrity_authority_boundary.py",
        "tools/validate_pr137_launch_readiness_dependency_controller.py",
        "tests/roadmap/test_pr137_launch_readiness_dependency_controller.py",
    ):
        if not (repo_root / rel_path).exists():
            failures.append(
                _failure("PR137_MISSING_ARTIFACT", f"missing {rel_path}", rel_path)
            )
    return failures


def _validate_json_roots(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for rel_path in (*policy.report_paths(), *policy.receipt_paths(), *policy.schema_paths()):
        try:
            _load_object(repo_root, rel_path)
        except Exception as exc:
            failures.append(
                _failure("PR137_JSON_ROOT_INVALID", str(exc), rel_path)
            )
    return failures


def _validate_authority_and_pr136_refs(payload: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if payload.get("authority_class") != policy.AUTHORITY_CLASS:
        failures.append(
            _failure(
                "PR137_AUTHORITY_CLASS_DRIFT",
                "authority class drift",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    refs = {
        row.get("artifact_ref")
        for row in payload.get("pr136_selector_refs", [])
        if isinstance(row, dict)
    }
    missing = set(policy.PR136_SELECTOR_ARTIFACTS) - refs
    if missing:
        failures.append(
            _failure(
                "PR137_MISSING_PR136_SELECTOR_REF",
                f"missing PR136 selector refs {sorted(missing)}",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    return failures


def _graph_has_cycle(nodes: Sequence[str], edges: Sequence[Mapping[str, str]]) -> bool:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        source = edge.get("from_node_id")
        target = edge.get("to_node_id")
        if source in adjacency and target in adjacency:
            adjacency[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for child in adjacency.get(node, []):
            if visit(child):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in nodes)


def _validate_sequence(payload: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    sequence_ids = list(payload.get("sequence_entry_ids", []))
    if sequence_ids != list(policy.CANONICAL_PR136_SEQUENCE_ENTRY_IDS):
        failures.append(
            _failure(
                "PR137_SEQUENCE_DRIFT",
                "PR137 sequence ids do not match PR136 selector order",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    if len(sequence_ids) != len(set(sequence_ids)):
        failures.append(
            _failure(
                "PR137_DUPLICATE_SEQUENCE_NODE",
                "duplicate sequence node",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    if payload.get("first_next_pr_id") != "PR137" or sequence_ids[:1] != ["PR137"]:
        failures.append(
            _failure(
                "PR137_FIRST_NEXT_PR_DRIFT",
                "PR137 must be first next PR after PR136",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    edges = payload.get("dependency_edges", [])
    edge_pairs = {
        (edge.get("from_node_id"), edge.get("to_node_id"))
        for edge in edges
        if isinstance(edge, dict)
    }
    for expected in policy.REQUIRED_DEPENDENCY_EDGES:
        if expected not in edge_pairs:
            failures.append(
                _failure(
                    "PR137_MISSING_SEQUENCE_EDGE",
                    f"missing dependency edge {expected[0]} -> {expected[1]}",
                    "PR137LaunchReadinessDependencyController.report.json",
                )
            )
    if _graph_has_cycle(sequence_ids, edges):
        failures.append(
            _failure(
                "PR137_CYCLIC_SEQUENCE_GRAPH",
                "PR137 to PR164 graph must be acyclic",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    return failures


def _validate_markets(payload: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    states = payload.get("market_dependency_states", [])
    scopes = [
        row.get("canonical_venue_id")
        for row in states
        if isinstance(row, dict)
    ]
    if scopes != list(policy.CANONICAL_MARKET_SCOPES):
        failures.append(
            _failure(
                "PR137_MARKET_SCOPE_DRIFT",
                "canonical market scope order drift",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    for row in states:
        if not isinstance(row, dict):
            continue
        if row.get("readiness_gated") is not True:
            failures.append(
                _failure(
                    "PR137_MARKET_NOT_GATED",
                    f"market not gated: {row.get('canonical_venue_id')}",
                    "PR137LaunchReadinessDependencyController.report.json",
                )
            )
        if set(row.get("missing_prerequisite_classes", [])) != set(
            policy.MISSING_MARKET_PREREQUISITE_CLASSES
        ):
            failures.append(
                _failure(
                    "PR137_MARKET_PREREQUISITE_DRIFT",
                    f"market prerequisite drift: {row.get('canonical_venue_id')}",
                    "PR137LaunchReadinessDependencyController.report.json",
                )
            )
    return failures


def _validate_agents(payload: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    states = payload.get("agent_dependency_states", [])
    agent_ids = [row.get("agent_id") for row in states if isinstance(row, dict)]
    if agent_ids != list(policy.AGENT_IDS):
        failures.append(
            _failure(
                "PR137_AGENT_SCOPE_DRIFT",
                "agent dependency map coverage drift",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    for row in states:
        if not isinstance(row, dict):
            continue
        if row.get("live_order_authority_allowed") is not False:
            failures.append(
                _failure(
                    "PR137_AGENT_AUTHORITY_ESCALATION",
                    f"agent live authority escalated: {row.get('agent_id')}",
                    "PR137LaunchReadinessDependencyController.report.json",
                )
            )
    return failures


def _validate_quantum_atomicrows(payload: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    boundary_payload = payload.get("quantum_atomicrows_dependency_boundary", {})
    expected_true = (
        "quantum_metadata_only",
        "no_quantum_backend_call",
        "no_simulator_execution",
        "no_optimizer_input_packet",
        "no_quantum_trading_signal",
        "no_quantum_advantage_claim",
    )
    expected_false = (
        "atomicrows_rows_created",
        "atomicrows_bundle_created",
        "atomicrows_materialization_authority_created",
    )
    for key in expected_true:
        if boundary_payload.get(key) is not True:
            failures.append(
                _failure(
                    "PR137_QUANTUM_BOUNDARY_DRIFT",
                    f"{key} must be true",
                    "PR137LaunchReadinessDependencyController.report.json",
                )
            )
    for key in expected_false:
        if boundary_payload.get(key) is not False:
            failures.append(
                _failure(
                    "PR137_ATOMICROWS_BOUNDARY_DRIFT",
                    f"{key} must be false",
                    "PR137LaunchReadinessDependencyController.report.json",
                )
            )
    if boundary_payload.get("atomicrows_bridge_compatibility") != (
        "FUTURE_DEPENDENCY_METADATA_ONLY"
    ):
        failures.append(
            _failure(
                "PR137_ATOMICROWS_BOUNDARY_DRIFT",
                "AtomicRows bridge compatibility must remain future metadata only",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    return failures


def _scan_authority_flags(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in policy.NO_AUTHORITY_FLAGS and item is not False:
                failures.append(f"{path}.{key}")
            failures.extend(_scan_authority_flags(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(_scan_authority_flags(item, f"{path}[{index}]"))
    return failures


def _validate_no_authority(payload: Mapping[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    flags = payload.get("no_authority_flags")
    if flags != policy.no_authority_flags():
        failures.append(
            _failure(
                "PR137_NO_AUTHORITY_FLAG_DRIFT",
                "no-authority flags drift",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    for path in _scan_authority_flags(payload):
        failures.append(
            _failure(
                "PR137_AUTHORITY_ESCALATION",
                f"authority flag must remain false: {path}",
                "PR137LaunchReadinessDependencyController.report.json",
            )
        )
    owner = payload.get("owner_authorization_boundary", {})
    expected = {
        "live_command_created": False,
        "owner_approval_receipt_created": False,
        "pr137_auto_authorizes_later_pr": False,
        "pr137_auto_authorizes_pr137l": False,
        "pr137_auto_authorizes_pr138": False,
        "pr164_final_live_start_requires_explicit_owner_command": True,
    }
    for key, value in expected.items():
        if owner.get(key) is not value:
            failures.append(
                _failure(
                    "PR137_OWNER_AUTHORIZATION_BOUNDARY_DRIFT",
                    f"{key} drift",
                    "PR137LaunchReadinessDependencyController.report.json",
                )
            )
    return failures


def _validate_generated_integrity_boundary(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for message in boundary.validate_boundary(repo_root):
        failures.append(
            _failure(
                "PR137_GENERATED_INTEGRITY_AUTHORITY_DRIFT",
                message,
                "tools/validate_pr137_generated_integrity_authority_boundary.py",
            )
        )
    return failures


def _validate_protected_diffs(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for rel_path in policy.PROTECTED_FILE_PATHS:
        completed = subprocess.run(
            ["git", "diff", "--", rel_path],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0 or completed.stdout.strip():
            failures.append(
                _failure("PR137_PROTECTED_FILE_DIFF", rel_path, rel_path)
            )
    for message in boundary.protected_integrity_diff_failures(repo_root):
        failures.append(
            _failure(
                "PR137_PROTECTED_FILE_DIFF",
                message,
                "tools/validate_pr137_generated_integrity_authority_boundary.py",
            )
        )
    return failures


def _validate_gate_integration(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    integration = _load_object(
        repo_root,
        f"{policy.REPORT_DIR}/PR137ValidationGateIntegration.report.json",
    )
    expected = [
        "tools/validate_pr136_roadmap_policy_literal_drift.py",
        "tools/validate_pr136_day1_launch_readiness_roadmap.py",
        "tools/validate_pr137_generated_integrity_authority_boundary.py",
        "tools/validate_pr137_launch_readiness_dependency_controller.py",
    ]
    if integration.get("cumulative_gate_commands_required") != expected:
        failures.append(
            _failure(
                "PR137_GATE_INTEGRATION_DRIFT",
                "PR137 validator order drift",
                "PR137ValidationGateIntegration.report.json",
            )
        )
    return failures


def validate_all(repo_root: Path = _REPO_ROOT) -> list[ValidationFailure]:
    repo_root = repo_root.resolve()
    failures = _validate_required_artifacts(repo_root)
    if failures:
        return failures
    failures.extend(_validate_json_roots(repo_root))
    if failures:
        return failures
    roots = _all_pr137_json_roots(repo_root)
    payload = _controller(repo_root)
    failures.extend(_validate_authority_and_pr136_refs(payload))
    failures.extend(_validate_sequence(payload))
    failures.extend(_validate_markets(payload))
    failures.extend(_validate_agents(payload))
    failures.extend(_validate_quantum_atomicrows(payload))
    failures.extend(_validate_no_authority(payload))
    failures.extend(_validate_generated_integrity_boundary(repo_root))
    failures.extend(_validate_protected_diffs(repo_root))
    failures.extend(_validate_gate_integration(repo_root))
    for rel_path, root in roots.items():
        if root.get("authority_class") != policy.AUTHORITY_CLASS:
            failures.append(
                _failure(
                    "PR137_AUTHORITY_CLASS_DRIFT",
                    "authority class drift in PR137 JSON root",
                    rel_path,
                )
            )
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    args = parser.parse_args(argv)
    failures = validate_all(args.repo_root)
    if failures:
        for failure in failures:
            print(f"{failure.code}: {failure.message} ({failure.artifact_ref})")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
