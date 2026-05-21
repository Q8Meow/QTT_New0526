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
    day1_launch_readiness_roadmap as roadmap,
)
from src.qtt.stage1_prediction_markets.launch_readiness import (  # noqa: E402
    day1_launch_readiness_roadmap_policy as policy,
)

COVERAGE_STRUCTURAL_METADATA_FIELDS = (
    "coverage_report_ref",
    "coverage_report_value_source",
    "master_plan_section_count",
    "coverage_entry_count",
    "report_type",
    "report_version",
    "deterministic_output",
    "generated_by",
    "generated_at_utc",
    "registry_entry_count",
    "parser_visible_section_count",
    "required_structural_keys_present",
    "required_structural_keys_missing",
)

FORBIDDEN_PR136_DIGEST_AUTHORITY_KEYS = {
    "atomicrows_bundle_sha_path",
    "atomicrows_sha_created_flag",
    "creates_atomicrows_sha",
    "coverage_report_digest_sha256",
    "file_digests_or_sizes",
    "sha256",
}

FORBIDDEN_PR136_DIGEST_AUTHORITY_TEXT = {
    "ATOMICROWS_BUNDLE_SHA_PATH",
    "AtomicRows SHA",
    "AtomicRows.bundle.sha256",
    "SHA/freeze",
    "atomicrows_bundle_sha_path",
    "atomicrows_sha_created_flag",
    "coverage_report_digest_sha256",
    "creates_atomicrows_sha",
    "file_digests_or_sizes",
    "hashlib",
    "sha256",
    "sha256_file",
}


@dataclass(frozen=True)
class ValidationFailure:
    code: str
    message: str
    artifact_ref: str


def _failure(code: str, message: str, artifact_ref: str) -> ValidationFailure:
    return ValidationFailure(code, message, artifact_ref)


def _load(repo_root: Path, rel_path: str) -> Any:
    return json.loads((repo_root / rel_path).read_text(encoding="utf-8"))


def _load_report(repo_root: Path, name: str) -> dict[str, Any]:
    value = _load(repo_root, f"docs/master_plan/generated/{name}")
    if not isinstance(value, dict):
        raise ValueError(f"{name} root must be object")
    return value


def _all_reports(repo_root: Path) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for rel_path in policy.PR136_REPORT_PATHS:
        path = repo_root / rel_path
        if not path.exists():
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            reports[Path(rel_path).name] = value
    return reports


def _scan_forbidden_pr136_digest_authority_keys(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}"
            if key in FORBIDDEN_PR136_DIGEST_AUTHORITY_KEYS or any(
                term in key for term in FORBIDDEN_PR136_DIGEST_AUTHORITY_TEXT
            ):
                failures.append(next_path)
            failures.extend(_scan_forbidden_pr136_digest_authority_keys(item, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(
                _scan_forbidden_pr136_digest_authority_keys(item, f"{path}[{index}]")
            )
    elif isinstance(value, str):
        for term in FORBIDDEN_PR136_DIGEST_AUTHORITY_TEXT:
            if term in value:
                failures.append(path)
                break
    return failures


def _validate_required_files(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for rel_path in (
        *policy.PR136_REPORT_PATHS,
        *policy.PR136_ROADMAP_RECEIPT_PATHS,
        *policy.PR136_SCHEMA_PATHS,
        "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
        "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_Index_v1_0.json",
        policy.POLICY_MODULE_PATH,
        policy.ROADMAP_MODULE_PATH,
    ):
        if not (repo_root / rel_path).exists():
            failures.append(
                _failure(
                    "BLOCKED_MISSING_PR136_ARTIFACT",
                    f"missing {rel_path}",
                    rel_path,
                )
            )
    return failures


def _validate_pr135_currentization(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    receipt = _load_report(repo_root, "PR135GitHubAuditCurrentization.report.json")
    for field, expected in roadmap.PR135_OWNER_VERIFIED_FIELDS.items():
        if receipt.get(field) != expected:
            failures.append(
                _failure(
                    "BLOCKED_MISSING_PR135_CURRENTIZATION",
                    f"PR135 field {field} expected {expected!r}",
                    "PR135GitHubAuditCurrentization.report.json",
                )
            )
    required = {
        "receipt_type": "PR135_GITHUB_AUDIT_CURRENTIZATION_RECEIPT",
        "owner_verified_source": True,
        "codex_network_access_used": False,
        "gh_command_used_by_codex": False,
        "currentized_in_identity_roster": True,
        "missing_owner_verified_fields": [],
        "placeholder_values_detected": [],
        "stop_if_missing_required_fields": True,
    }
    for field, expected in required.items():
        if receipt.get(field) != expected:
            failures.append(
                _failure(
                    "BLOCKED_MISSING_PR135_CURRENTIZATION",
                    f"PR135 currentization field {field} expected {expected!r}",
                    "PR135GitHubAuditCurrentization.report.json",
                )
            )
    roster = _load(repo_root, "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
    entries = roster.get("entries", [])
    if not any(
        isinstance(entry, dict)
        and entry.get("roster_entry_id") == "PR135_REPO_CANONICAL_SELF_ENTRY"
        and entry.get("github_pr_mergeCommit_oid")
        == roadmap.PR135_OWNER_VERIFIED_FIELDS["mergeCommit_full"]
        for entry in entries
    ):
        failures.append(
            _failure(
                "BLOCKED_MISSING_PR135_CURRENTIZATION",
                "PR135 roster self-entry missing or not currentized",
                "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
            )
        )
    return failures


def _validate_route_read_path(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    route = _load_report(repo_root, "PR136RouteTriage.report.json")
    if route.get("same_number_inference_used") is not False:
        failures.append(
            _failure(
                "BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE",
                "same_number_inference_used must be false",
                "PR136RouteTriage.report.json",
            )
        )
    if route.get("currentization_first_subtask_completed") is not True:
        failures.append(
            _failure(
                "BLOCKED_MISSING_PR135_CURRENTIZATION",
                "PR135 currentization must complete before PR136 mapping",
                "PR136RouteTriage.report.json",
            )
        )
    if route.get("sequence_authority_class") != policy.SEQUENCE_AUTHORITY:
        failures.append(
            _failure(
                "BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE",
                "route authority class drift",
                "PR136RouteTriage.report.json",
            )
        )
    read = _load_report(repo_root, "PR136ReadReceipt.report.json")
    if read.get("missing_files") != [] or read.get("read_before_editing_confirmed") is not True:
        failures.append(
            _failure(
                "BLOCKED_MISSING_READ_INPUT",
                "read receipt missing files or confirmation",
                "PR136ReadReceipt.report.json",
            )
        )
    meta = roadmap.coverage_metadata(repo_root)
    for field in COVERAGE_STRUCTURAL_METADATA_FIELDS:
        expected = meta[field]
        if read.get(field) != expected:
            failures.append(
                _failure(
                    "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                    f"read receipt coverage field {field} drift",
                    "PR136ReadReceipt.report.json",
                )
            )
    if read.get("required_structural_keys_missing") != []:
        failures.append(
            _failure(
                "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                "read receipt coverage report structural keys missing",
                "PR136ReadReceipt.report.json",
            )
        )
    file_sizes = read.get("file_sizes_and_line_counts")
    if not isinstance(file_sizes, dict) or not file_sizes:
        failures.append(
            _failure(
                "BLOCKED_MISSING_READ_INPUT",
                "read receipt must record file sizes and line counts",
                "PR136ReadReceipt.report.json",
            )
        )
    path = _load_report(repo_root, "PR136PathDecision.report.json")
    if path.get("safe_canonical_path_inferred") is not True:
        failures.append(
            _failure(
                "BLOCKED_PATH_DECISION",
                "safe canonical path was not inferred",
                "PR136PathDecision.report.json",
            )
        )
    return failures


def _validate_policy(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    manifest = _load_report(repo_root, "PR136PolicyManifest.report.json")
    expected = policy.policy_manifest_payload()
    keys = (
        "validator_marker",
        "sequence_authority_classes",
        "classification_labels",
        "evidence_classes",
        "readiness_state_classes",
        "readiness_domain_taxonomy_rules",
        "canonical_venues",
        "future_pr_scope_classes",
        "future_pr_number_status",
        "domain_types",
        "no_authority_flags",
        "block_code_refs",
    )
    for key in keys:
        if manifest.get(key) != expected.get(key):
            failures.append(
                _failure(
                    "BLOCKED_SCATTERED_POLICY_LITERAL_DRIFT",
                    f"policy manifest drift at {key}",
                    "PR136PolicyManifest.report.json",
                )
            )
    for rel_path in policy.PR136_SCHEMA_PATHS:
        try:
            _load(repo_root, rel_path)
        except Exception as exc:
            failures.append(
                _failure(
                    "BLOCKED_SCATTERED_POLICY_LITERAL_DRIFT",
                    f"schema load failed: {exc}",
                    rel_path,
                )
            )
    try:
        from tools import validate_pr136_roadmap_policy_literal_drift as drift

        drift_failures = drift.validate_policy_literal_drift(repo_root=repo_root)
        failures.extend(
            _failure(
                "BLOCKED_SCATTERED_POLICY_LITERAL_DRIFT",
                item,
                "PR136PolicyLiteralDrift.report.json",
            )
            for item in drift_failures
        )
    except Exception as exc:
        failures.append(
            _failure(
                "BLOCKED_SCATTERED_POLICY_LITERAL_DRIFT",
                str(exc),
                "tools/validate_pr136_roadmap_policy_literal_drift.py",
            )
        )
    return failures


def _validate_domain_mapping(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    domain_map = _load_report(repo_root, "PR136MasterPlanCoverageToReadinessDomainMap.report.json")
    taxonomy = _load_report(repo_root, "PR136ReadinessDomainTaxonomy.report.json")
    meta = roadmap.coverage_metadata(repo_root)
    if domain_map.get("master_plan_section_count") != meta["master_plan_section_count"]:
        failures.append(
            _failure(
                "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                "master plan section count does not match coverage report",
                "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
            )
        )
    if domain_map.get("coverage_entry_count") != meta["coverage_entry_count"]:
        failures.append(
            _failure(
                "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                "coverage entry count does not match coverage report",
                "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
            )
        )
    for field in COVERAGE_STRUCTURAL_METADATA_FIELDS:
        if domain_map.get(field) != meta[field]:
            failures.append(
                _failure(
                    "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                    f"domain map coverage structural field {field} drift",
                    "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
                )
            )
    evidence_summary = taxonomy.get("domain_evidence_summary")
    if not isinstance(evidence_summary, dict):
        failures.append(
            _failure(
                "BLOCKED_EVIDENCELESS_CLASSIFICATION",
                "taxonomy missing domain_evidence_summary",
                "PR136ReadinessDomainTaxonomy.report.json",
            )
        )
    else:
        for field in COVERAGE_STRUCTURAL_METADATA_FIELDS:
            if evidence_summary.get(field) != meta[field]:
                failures.append(
                    _failure(
                        "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                        f"taxonomy coverage structural field {field} drift",
                        "PR136ReadinessDomainTaxonomy.report.json",
                    )
                )
    for artifact_name, payload in (
        ("PR136MasterPlanCoverageToReadinessDomainMap.report.json", domain_map),
        ("PR136ReadinessDomainTaxonomy.report.json", taxonomy),
    ):
        if payload.get("arbitrary_domain_count_forced") is not False:
            failures.append(
                _failure(
                    "BLOCKED_ARBITRARY_DOMAIN_COUNT_FORCED",
                    "arbitrary domain count forced",
                    artifact_name,
                )
            )
        if payload.get("fixed_13_domain_model_used") is not False:
            failures.append(
                _failure(
                    "BLOCKED_FIXED_13_DOMAIN_MODEL_USED",
                    "fixed 13 domain model used",
                    artifact_name,
                )
            )
    records = domain_map.get("domain_records", [])
    if domain_map.get("readiness_domain_count") != len(records):
        failures.append(
            _failure(
                "BLOCKED_ARBITRARY_DOMAIN_COUNT_FORCED",
                "readiness_domain_count must equal generated domain record count",
                "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
            )
        )
    if domain_map.get("readiness_domain_count") == 13:
        failures.append(
            _failure(
                "BLOCKED_FIXED_13_DOMAIN_MODEL_USED",
                "readiness_domain_count cannot be 13",
                "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
            )
        )
    if domain_map.get("unmapped_entries") != []:
        failures.append(
            _failure(
                "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                "coverage entries are unmapped",
                "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
            )
        )
    for record in records:
        if not record.get("evidence_basis"):
            failures.append(
                _failure(
                    "BLOCKED_EVIDENCELESS_CLASSIFICATION",
                    f"domain lacks evidence basis: {record.get('domain_id')}",
                    "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
                )
            )
        if not record.get("future_pr_candidates"):
            failures.append(
                _failure(
                    "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                    f"domain lacks future PR candidates: {record.get('domain_id')}",
                    "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
                )
            )
    if taxonomy.get("readiness_domain_count") != domain_map.get("readiness_domain_count"):
        failures.append(
            _failure(
                "BLOCKED_ARBITRARY_DOMAIN_COUNT_FORCED",
                "taxonomy count does not match domain map count",
                "PR136ReadinessDomainTaxonomy.report.json",
            )
        )
    return failures


def _validate_classification_sequence(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    classification = _load_report(repo_root, "PR136ProvisionalPR137ToPR164Classification.report.json")
    records = classification.get("classification_records", [])
    numbers = {record.get("provisional_pr_number") for record in records}
    expected_numbers = set(range(137, 165))
    if numbers != expected_numbers:
        failures.append(
            _failure(
                "BLOCKED_PROVISIONAL_PR_WITHOUT_CLASSIFICATION",
                "PR137-PR164 classification set is incomplete",
                "PR136ProvisionalPR137ToPR164Classification.report.json",
            )
        )
    for record in records:
        if record.get("classification") not in policy.CLASSIFICATION_LABELS:
            failures.append(
                _failure(
                    "BLOCKED_PROVISIONAL_PR_WITHOUT_CLASSIFICATION",
                    f"invalid classification {record.get('classification')}",
                    "PR136ProvisionalPR137ToPR164Classification.report.json",
                )
            )
        if not record.get("evidence_basis"):
            failures.append(
                _failure(
                    "BLOCKED_EVIDENCELESS_CLASSIFICATION",
                    f"classification lacks evidence {record.get('provisional_pr_number')}",
                    "PR136ProvisionalPR137ToPR164Classification.report.json",
                )
            )
    sequence = _load_report(repo_root, "PR136PostPR135RoadmapSequence.report.json")
    seen: set[str] = set()
    domain_map = _load_report(repo_root, "PR136MasterPlanCoverageToReadinessDomainMap.report.json")
    all_domain_ids = {record["domain_id"] for record in domain_map["domain_records"]}
    sequence_domain_ids: set[str] = set()
    for entry in sequence.get("sequence_entries", []):
        seq_id = entry.get("final_sequence_pr_number_or_placeholder")
        if seq_id in seen:
            failures.append(
                _failure(
                    "BLOCKED_DUPLICATE_FUTURE_PR_NUMBER",
                    f"duplicate sequence id {seq_id}",
                    "PR136PostPR135RoadmapSequence.report.json",
                )
            )
        seen.add(seq_id)
        sequence_domain_ids.update(entry.get("domain_ids", []))
        required_fields = (
            "required_upstream_prs",
            "downstream_dependencies",
            "domain_ids",
            "validation_marker",
            "allowed_artifacts",
            "forbidden_artifacts",
            "owner_authorization_required",
            "current_authority_created",
        )
        for field in required_fields:
            if field not in entry:
                failures.append(
                    _failure(
                        "BLOCKED_PROVISIONAL_PR_WITHOUT_CLASSIFICATION",
                        f"sequence entry missing {field}",
                        "PR136PostPR135RoadmapSequence.report.json",
                    )
                )
        if entry.get("validation_marker") != policy.VALIDATOR_MARKER:
            failures.append(
                _failure(
                    "BLOCKED_PROVISIONAL_PR_WITHOUT_CLASSIFICATION",
                    "sequence validation marker drift",
                    "PR136PostPR135RoadmapSequence.report.json",
                )
            )
        if entry.get("current_authority_created") is not False:
            failures.append(
                _failure(
                    "BLOCKED_LIVE_DATA_OR_RUNTIME_AUTHORITY_ATTEMPT",
                    "sequence entry creates current authority",
                    "PR136PostPR135RoadmapSequence.report.json",
                )
            )
    missing_domains = all_domain_ids - sequence_domain_ids
    if missing_domains:
        failures.append(
            _failure(
                "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                f"sequence misses domains {sorted(missing_domains)}",
                "PR136PostPR135RoadmapSequence.report.json",
            )
        )
    cards = _load_report(repo_root, "PR136FuturePRCardRegistry.report.json")
    for card in cards.get("cards", []):
        if not card.get("definition_of_done"):
            failures.append(
                _failure(
                    "BLOCKED_PROVISIONAL_PR_WITHOUT_CLASSIFICATION",
                    f"future PR card lacks definition_of_done {card.get('future_pr_id')}",
                    "PR136FuturePRCardRegistry.report.json",
                )
            )
    return failures


def _graph_has_cycle(nodes: Sequence[str], edges: Sequence[Mapping[str, str]]) -> bool:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        source = edge.get("from")
        target = edge.get("to")
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


def _validate_graph_market_quantum_agent_latency(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    graph = _load_report(repo_root, "PR136LaunchReadinessDependencyGraph.report.json")
    node_ids = [node.get("node_id") for node in graph.get("nodes", []) if isinstance(node, dict)]
    if _graph_has_cycle([str(node) for node in node_ids], graph.get("edges", [])):
        failures.append(
            _failure(
                "BLOCKED_CYCLIC_DEPENDENCY_GRAPH",
                "dependency graph has cycle",
                "PR136LaunchReadinessDependencyGraph.report.json",
            )
        )
    domain_map = _load_report(repo_root, "PR136MasterPlanCoverageToReadinessDomainMap.report.json")
    missing_domains = [
        record["domain_id"]
        for record in domain_map["domain_records"]
        if record["domain_id"] not in node_ids
    ]
    if missing_domains:
        failures.append(
            _failure(
                "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                f"graph misses domain nodes {missing_domains}",
                "PR136LaunchReadinessDependencyGraph.report.json",
            )
        )
    for venue in policy.CANONICAL_VENUES:
        if venue not in node_ids:
            failures.append(
                _failure(
                    "BLOCKED_MISSING_MARKET_SPECIFIC_READINESS_ROUTE",
                    f"graph misses market scope {venue}",
                    "PR136LaunchReadinessDependencyGraph.report.json",
                )
            )
    market = _load_report(repo_root, "PR136MarketSpecificLaunchReadinessIndex.report.json")
    scopes = [row.get("canonical_venue_id") for row in market.get("market_scopes", [])]
    if tuple(scopes) != policy.CANONICAL_VENUES:
        failures.append(
            _failure(
                "BLOCKED_MISSING_MARKET_SPECIFIC_READINESS_ROUTE",
                "market-specific index must contain exactly four canonical scopes",
                "PR136MarketSpecificLaunchReadinessIndex.report.json",
            )
        )
    if any(scope in policy.FORBIDDEN_FORECASTEX_ALIASES for scope in scopes):
        failures.append(
            _failure(
                "BLOCKED_MISSING_MARKET_SPECIFIC_READINESS_ROUTE",
                "noncanonical ForecastEx/IBKR scope used",
                "PR136MarketSpecificLaunchReadinessIndex.report.json",
            )
        )
    quantum = _load_report(repo_root, "PR136QuantumAtomicRowsOptimizationReadinessMap.report.json")
    for field in (
        "no_quantum_execution_flag",
        "no_quantum_optimizer_input_flag",
        "no_quantum_signal_creation_flag",
        "no_quantum_advantage_claim_flag",
    ):
        if quantum.get(field) is not True:
            failures.append(
                _failure(
                    "BLOCKED_QUANTUM_EXECUTION_OR_ADVANTAGE_CLAIM_ATTEMPT",
                    f"{field} must be true",
                    "PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
                )
            )
    for field in (
        "atomicrows_bundle_created_flag",
        "atomicrows_bundle_edited_flag",
        "atomicrows_rows_created_flag",
        "atomicrows_materialization_authority_created_flag",
    ):
        if quantum.get(field) is not False:
            failures.append(
                _failure(
                    "BLOCKED_ATOMICROWS_BUNDLE_ROW_MATERIALIZATION_ATTEMPT",
                    f"{field} must be false",
                    "PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
                )
            )
    if (
        quantum.get("atomicrows_bundle_integrity_authority_status")
        != "OWNER_DISABLED_NO_QTT_SHA"
    ):
        failures.append(
            _failure(
                "BLOCKED_ATOMICROWS_BUNDLE_ROW_MATERIALIZATION_ATTEMPT",
                "AtomicRows bundle integrity authority must remain owner-disabled",
                "PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
            )
        )
    agents = _load_report(repo_root, "PR136AgentLaunchOrchestrationMap.report.json")
    for agent in agents.get("agent_domains", []):
        if agent.get("latency_hot_path_allowed") is not False or agent.get("live_order_authority_allowed") is not False:
            failures.append(
                _failure(
                    "BLOCKED_AGENT_AUTHORITY_ESCALATION",
                    f"agent authority escalates {agent.get('agent_domain_id')}",
                    "PR136AgentLaunchOrchestrationMap.report.json",
                )
            )
    latency = _load_report(repo_root, "PR136LatencyControlPlaneVsLivePathMap.report.json")
    forbidden = set(latency.get("live_hot_path_forbidden_current_and_future_runtime_calls", []))
    required_forbidden = {
        "document retrieval",
        "source acceptance",
        "LLM reasoning",
        "roadmap compilation",
        "master-plan parsing",
        "replay execution",
        "paper execution",
        "dashboard dependency",
        "quantum backend call",
        "AtomicRows generation",
    }
    if not required_forbidden.issubset(forbidden):
        failures.append(
            _failure(
                "BLOCKED_LIVE_HOT_PATH_CONTROL_PLANE_CALL",
                "live hot path does not block all control-plane calls",
                "PR136LatencyControlPlaneVsLivePathMap.report.json",
            )
        )
    if latency.get("current_pr136_hot_path_authority_created") is not False:
        failures.append(
            _failure(
                "BLOCKED_LIVE_HOT_PATH_CONTROL_PLANE_CALL",
                "PR136 created hot-path authority",
                "PR136LatencyControlPlaneVsLivePathMap.report.json",
            )
        )
    return failures


def _scan_forbidden_flags(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in policy.NO_AUTHORITY_FLAGS and item is not False:
                failures.append(f"{path}.{key} must remain false")
            failures.extend(_scan_forbidden_flags(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            failures.extend(_scan_forbidden_flags(item, f"{path}[{index}]"))
    return failures


def _validate_authority_boundaries(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for name, report in _all_reports(repo_root).items():
        for message in _scan_forbidden_flags(report):
            failures.append(
                _failure(
                    "BLOCKED_LIVE_DATA_OR_RUNTIME_AUTHORITY_ATTEMPT",
                    message,
                    name,
                )
            )
    day1 = _load_report(repo_root, "PR136PostPR135RoadmapSequence.report.json")
    official = [
        entry
        for entry in day1.get("sequence_entries", [])
        if entry.get("final_sequence_pr_number_or_placeholder") == "PR164"
    ]
    if not official or official[0].get("readiness_state_target") != "OFFICIAL_DAY1_LIVE_TRADING_STARTED_OWNER_AUTHORIZED_ONLY":
        failures.append(
            _failure(
                "BLOCKED_DAY1_LAUNCH_EXECUTION_ATTEMPT",
                "Day-1 launch terminal node must remain owner-authorized only",
                "PR136PostPR135RoadmapSequence.report.json",
            )
        )
    return failures


def _validate_no_pr136_digest_authority(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    json_paths = (
        *policy.PR136_REPORT_PATHS,
        *policy.PR136_ROADMAP_RECEIPT_PATHS,
        *policy.PR136_SCHEMA_PATHS,
        "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_Index_v1_0.json",
    )
    for rel_path in json_paths:
        path = repo_root / rel_path
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(
                _failure(
                    "BLOCKED_SCATTERED_POLICY_LITERAL_DRIFT",
                    f"JSON load failed while checking digest authority: {exc}",
                    rel_path,
                )
            )
            continue
        for field_path in _scan_forbidden_pr136_digest_authority_keys(payload):
            failures.append(
                _failure(
                    "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                    f"PR136 digest authority field is forbidden: {field_path}",
                    rel_path,
                )
            )
    text_paths = ("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",)
    for rel_path in text_paths:
        text = (repo_root / rel_path).read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_PR136_DIGEST_AUTHORITY_TEXT:
            if forbidden in text:
                failures.append(
                    _failure(
                        "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
                        f"PR136 digest authority text is forbidden: {forbidden}",
                        rel_path,
                    )
                )
    return failures


def _validate_protected_diffs(repo_root: Path) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    protected = (
        ("docs/master_plan/QTT_MasterPlan_Current.md", "BLOCKED_MASTER_PLAN_EDIT_ATTEMPT"),
        (roadmap.ATOMICROWS_BUNDLE_PATH.as_posix(), "BLOCKED_ATOMICROWS_BUNDLE_ROW_MATERIALIZATION_ATTEMPT"),
        (
            "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
            "BLOCKED_ATOMICROWS_BUNDLE_ROW_MATERIALIZATION_ATTEMPT",
        ),
    )
    for rel_path, block_code in protected:
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
                _failure(block_code, f"protected artifact diff: {rel_path}", rel_path)
            )
    return failures


def validate_all(repo_root: Path = _REPO_ROOT) -> list[ValidationFailure]:
    repo_root = repo_root.resolve()
    failures = _validate_required_files(repo_root)
    if failures:
        return failures
    failures.extend(_validate_pr135_currentization(repo_root))
    failures.extend(_validate_route_read_path(repo_root))
    failures.extend(_validate_policy(repo_root))
    failures.extend(_validate_domain_mapping(repo_root))
    failures.extend(_validate_classification_sequence(repo_root))
    failures.extend(_validate_graph_market_quantum_agent_latency(repo_root))
    failures.extend(_validate_authority_boundaries(repo_root))
    failures.extend(_validate_no_pr136_digest_authority(repo_root))
    failures.extend(_validate_protected_diffs(repo_root))
    return failures


def marker_for_failures(failures: Sequence[ValidationFailure]) -> str:
    return policy.VALIDATOR_MARKER if not failures else ""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.write_artifacts:
        roadmap.write_artifacts(repo_root)
    failures = validate_all(repo_root)
    if failures:
        for failure in failures:
            print(f"{failure.code}: {failure.message} ({failure.artifact_ref})")
        return 1
    print(policy.VALIDATOR_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
