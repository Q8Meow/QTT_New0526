from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

from src.qtt.stage1_prediction_markets.launch_readiness import (
    pr137_launch_readiness_dependency_controller as controller,
)
from src.qtt.stage1_prediction_markets.launch_readiness import (
    pr137_launch_readiness_dependency_policy as policy,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_ATOMICROWS_INTEGRITY_ARTIFACT_PATH = (
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)
FORBIDDEN_GENERATED_INTEGRITY_AUTHORITY_TERMS = (
    "AtomicRows.bundle.sha256",
    "atomicrows_bundle_sha_path",
    "ATOMICROWS_BUNDLE_SHA_PATH",
    "coverage_report_digest_sha256",
    "file_digests_or_sizes",
    "sha256_file",
    "hashlib",
    "sha256",
)


def _load_json(rel_path: str) -> dict[str, Any]:
    payload = json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _payload() -> dict[str, Any]:
    return _load_json(
        "docs/master_plan/generated/PR137LaunchReadinessDependencyController.report.json"
    )


def _run_validator(rel_path: str) -> str:
    completed = subprocess.run(
        [sys.executable, rel_path],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed.stdout.strip()


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
        for child in adjacency[node]:
            if visit(child):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in nodes)


def _string_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_string_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_string_values(item))
        return values
    if isinstance(value, str):
        return [value]
    return []


def test_pr137_artifacts_exist() -> None:
    for rel_path in (
        *policy.report_paths(),
        *policy.receipt_paths(),
        *policy.schema_paths(),
        policy.ROADMAP_DOC_PATH,
        "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_policy.py",
        "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_controller.py",
        "tools/validate_pr137_generated_integrity_authority_boundary.py",
        "tools/validate_pr137_launch_readiness_dependency_controller.py",
    ):
        assert (REPO_ROOT / rel_path).exists(), rel_path


def test_pr137_validators_emit_exact_markers() -> None:
    assert (
        _run_validator("tools/validate_pr137_generated_integrity_authority_boundary.py")
        == policy.GENERATED_INTEGRITY_VALIDATION_MARKER
    )
    assert (
        _run_validator("tools/validate_pr137_launch_readiness_dependency_controller.py")
        == policy.CONTROLLER_VALIDATION_MARKER
    )


def test_pr137_sequence_and_downstream_ordering() -> None:
    payload = _payload()
    sequence = payload["sequence_entry_ids"]
    assert sequence == list(policy.CANONICAL_PR136_SEQUENCE_ENTRY_IDS)
    assert payload["first_next_pr_id"] == "PR137"
    assert sequence[:3] == ["PR137", "PR137L", "PR138"]
    edge_pairs = {
        (edge["from_node_id"], edge["to_node_id"])
        for edge in payload["dependency_edges"]
    }
    assert ("PR137", "PR137L") in edge_pairs
    assert ("PR137L", "PR138") in edge_pairs
    assert ("PR138", "PR139") in edge_pairs
    assert not _graph_has_cycle(sequence, payload["dependency_edges"])


def test_pr137_no_authority_flags_remain_false() -> None:
    payload = _payload()
    assert payload["no_authority_flags"] == policy.no_authority_flags()
    assert all(value is False for value in payload["no_authority_flags"].values())
    for key in (
        "creates_source_retrieval",
        "creates_source_acceptance",
        "creates_connector_binding",
        "creates_replay_execution",
        "creates_paper_execution",
        "creates_order_authority",
        "creates_order_execution",
        "creates_profit_evidence",
        "creates_quantum_execution",
        "creates_quantum_optimizer_input",
        "creates_day1_live_launch",
    ):
        assert payload["no_authority_flags"][key] is False


def test_pr137_market_scopes_and_prerequisites_are_preserved() -> None:
    payload = _payload()
    states = payload["market_dependency_states"]
    assert [row["canonical_venue_id"] for row in states] == list(
        policy.CANONICAL_MARKET_SCOPES
    )
    for row in states:
        assert row["readiness_gated"] is True
        assert set(row["missing_prerequisite_classes"]) == set(
            policy.MISSING_MARKET_PREREQUISITE_CLASSES
        )


def test_pr137_forbidden_forecastex_aliases_absent_as_exact_values() -> None:
    forbidden = set(policy.FORBIDDEN_FORECASTEX_ALIASES)
    for rel_path in (*policy.report_paths(), *policy.receipt_paths()):
        values = set(_string_values(_load_json(rel_path)))
        assert not (values & forbidden), rel_path


def test_pr137_agent_dependency_map_covers_expected_agents() -> None:
    payload = _payload()
    assert [row["agent_id"] for row in payload["agent_dependency_states"]] == list(
        policy.AGENT_IDS
    )
    for row in payload["agent_dependency_states"]:
        assert row["live_order_authority_allowed"] is False
        assert row["latency_hot_path_allowed"] is False


def test_pr137_quantum_atomicrows_boundary_is_future_metadata_only() -> None:
    boundary = _payload()["quantum_atomicrows_dependency_boundary"]
    assert boundary["quantum_metadata_only"] is True
    assert boundary["no_quantum_backend_call"] is True
    assert boundary["no_simulator_execution"] is True
    assert boundary["no_optimizer_input_packet"] is True
    assert boundary["no_quantum_trading_signal"] is True
    assert boundary["no_quantum_advantage_claim"] is True
    assert boundary["atomicrows_bridge_compatibility"] == (
        "FUTURE_DEPENDENCY_METADATA_ONLY"
    )
    assert boundary["atomicrows_rows_created"] is False
    assert boundary["atomicrows_bundle_created"] is False
    assert boundary["atomicrows_materialization_authority_created"] is False
    assert set(boundary["compatibility_states"].values()) == {
        "FUTURE_DEPENDENCY_METADATA_ONLY"
    }


def test_pr137_does_not_auto_authorize_downstream_or_live_trading() -> None:
    owner = _payload()["owner_authorization_boundary"]
    assert owner["pr137_auto_authorizes_pr137l"] is False
    assert owner["pr137_auto_authorizes_pr138"] is False
    assert owner["pr137_auto_authorizes_later_pr"] is False
    assert owner["owner_approval_receipt_created"] is False
    assert owner["live_command_created"] is False
    assert owner["pr164_final_live_start_requires_explicit_owner_command"] is True


def test_pr137_generated_artifacts_do_not_contain_generated_integrity_authority() -> None:
    disallowed_scan_paths = (
        *policy.report_paths(),
        *policy.receipt_paths(),
        *policy.schema_paths(),
        policy.ROADMAP_DOC_PATH,
        "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_policy.py",
        "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_controller.py",
        "tools/validate_pr137_launch_readiness_dependency_controller.py",
    )
    for rel_path in disallowed_scan_paths:
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8", errors="ignore")
        hits = [
            term
            for term in FORBIDDEN_GENERATED_INTEGRITY_AUTHORITY_TERMS
            if term in text
        ]
        assert hits == [], f"{rel_path}: {hits}"


def test_pr137_protected_artifacts_have_no_diff() -> None:
    for rel_path in (
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        LEGACY_ATOMICROWS_INTEGRITY_ARTIFACT_PATH,
    ):
        completed = subprocess.run(
            ["git", "diff", "--", rel_path],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert completed.returncode == 0
        assert completed.stdout.strip() == ""


def test_pr137_reports_are_deterministic_and_idempotent() -> None:
    first = controller.build_reports(REPO_ROOT)
    second = controller.build_reports(REPO_ROOT)
    assert first == second

    artifact_paths = (
        *policy.report_paths(),
        *policy.receipt_paths(),
        *policy.schema_paths(),
        policy.ROADMAP_DOC_PATH,
    )
    before_bytes = {
        rel_path: (REPO_ROOT / rel_path).read_bytes()
        for rel_path in artifact_paths
    }
    before = {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in (*policy.report_paths(), *policy.receipt_paths())
    }
    try:
        controller.write_artifacts(REPO_ROOT)
        after_first_write = {
            rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
            for rel_path in (*policy.report_paths(), *policy.receipt_paths())
        }
        controller.write_artifacts(REPO_ROOT)
        after_second_write = {
            rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
            for rel_path in (*policy.report_paths(), *policy.receipt_paths())
        }
    finally:
        for rel_path, content in before_bytes.items():
            (REPO_ROOT / rel_path).write_bytes(content)
    assert before == after_first_write == after_second_write
